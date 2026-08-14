"""Relation-at-a-time live migration from a legacy serving database to a
pipeline-built candidate.

The unit of migration is a *relation*, not a row range. That choice is forced by
Postgres: DELETE marks rows dead but returns nothing to the filesystem, and
reclaiming that space needs VACUUM FULL, which transiently wants a second copy
of the table. DROP TABLE returns the space immediately. So a migration that is
meant to free disk as it proceeds has to move whole relations.

Serving continues throughout because the cutover is a rename inside a single
transaction:

    BEGIN;
      ALTER ... public.all_entities  RENAME TO all_entities__bdp_legacy;
      ALTER ... bdp_next.all_entities SET SCHEMA public;
    COMMIT;

PostgREST resolves relations per query, so in-flight statements finish against
the old relation and the next one lands on the new. No restart, no dropped
connection, no nginx change.

Every relation carries a state, and the process is stoppable at any of them:

    legacy     untouched, serving from the original
    building   candidate copy present in the staging schema
    verified   candidate passed structural comparison
    swapped    serving from the candidate, legacy retained
    reclaimed  legacy dropped, space returned

Rollback is available until reclaim. That is the property that makes this
acceptable to run against a live host.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable, Sequence

from . import compare as cmp
from . import db
from .config import Config
from .log import get

logger = get("migrate")

STAGING_SCHEMA = "bdp_next"
LEGACY_SUFFIX = "__bdp_legacy"

STATES = ("legacy", "building", "verified", "swapped", "reclaimed")

STATE_DDL = """
CREATE SCHEMA IF NOT EXISTS bdp_meta;

CREATE TABLE IF NOT EXISTS bdp_meta.migration_state (
    dataset       TEXT NOT NULL,
    relation      TEXT NOT NULL,
    state         TEXT NOT NULL CHECK (state IN
                    ('legacy','building','verified','swapped','reclaimed')),
    candidate_db  TEXT,
    legacy_name   TEXT,
    relkind       TEXT,
    built_at      TIMESTAMPTZ,
    verified_at   TIMESTAMPTZ,
    swapped_at    TIMESTAMPTZ,
    reclaimed_at  TIMESTAMPTZ,
    detail        JSONB NOT NULL DEFAULT '{}'::jsonb,
    PRIMARY KEY (dataset, relation)
);
"""

# Postgres spells the rename differently per relation kind, and getting it wrong
# is an error rather than a silent no-op, so the mapping is explicit.
_ALTER = {
    "r": "TABLE",
    "p": "TABLE",
    "v": "VIEW",
    "m": "MATERIALIZED VIEW",
    "f": "FOREIGN TABLE",
}


@dataclass
class RelationState:
    relation: str
    state: str
    candidate_db: str | None
    legacy_name: str | None
    relkind: str | None
    detail: dict[str, Any]

    @property
    def rollbackable(self) -> bool:
        return self.state == "swapped" and bool(self.legacy_name)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _split(relation: str) -> tuple[str, str]:
    if "." in relation:
        schema, _, name = relation.rpartition(".")
        return schema, name
    return "public", relation


def ensure(cfg: Config, dbname: str) -> None:
    """Create the migration bookkeeping table in the serving database."""
    db.psql(cfg, dbname, STATE_DDL, tuples_only=False)


def exposed_relations(dataset: str) -> tuple[str, ...]:
    """The curated relations a dataset publishes.

    Read from the pipeline module rather than from the live catalog: the
    published contract is what the pipeline declares, and anything else in the
    serving database is either upstream lineage or accumulated debris. Migrating
    debris would be migrating the wrong thing.
    """
    import importlib

    module = importlib.import_module(f"pipelines.{dataset}.pipeline")
    return tuple(getattr(module, "EXPOSED", ()))


def load_states(cfg: Config, dbname: str, dataset: str) -> dict[str, RelationState]:
    rows = db.psql(
        cfg,
        dbname,
        "SELECT relation, state, coalesce(candidate_db,''), coalesce(legacy_name,''), "
        f"coalesce(relkind,''), detail::text FROM bdp_meta.migration_state "
        f"WHERE dataset = {db.quote_literal(dataset)} ORDER BY relation",
    )
    out: dict[str, RelationState] = {}
    for row in rows:
        if len(row) < 6:
            continue
        relation, state, candidate, legacy, relkind, detail = row[:6]
        try:
            parsed = json.loads(detail) if detail else {}
        except json.JSONDecodeError:
            parsed = {}
        out[relation] = RelationState(
            relation=relation,
            state=state,
            candidate_db=candidate or None,
            legacy_name=legacy or None,
            relkind=relkind or None,
            detail=parsed,
        )
    return out


def set_state(
    cfg: Config,
    dbname: str,
    dataset: str,
    relation: str,
    state: str,
    **fields: Any,
) -> None:
    if state not in STATES:
        raise ValueError(f"unknown migration state: {state}")

    columns = ["dataset", "relation", "state"]
    values = [
        db.quote_literal(dataset),
        db.quote_literal(relation),
        db.quote_literal(state),
    ]

    stamp = {
        "building": "built_at",
        "verified": "verified_at",
        "swapped": "swapped_at",
        "reclaimed": "reclaimed_at",
    }.get(state)
    if stamp:
        columns.append(stamp)
        values.append("now()")

    for key, value in fields.items():
        if value is None:
            continue
        columns.append(key)
        if key == "detail":
            values.append(f"{db.quote_literal(json.dumps(value))}::jsonb")
        else:
            values.append(db.quote_literal(str(value)))

    updates = ", ".join(
        f"{c} = EXCLUDED.{c}" for c in columns if c not in ("dataset", "relation")
    )
    sql = (
        f"INSERT INTO bdp_meta.migration_state ({', '.join(columns)}) "
        f"VALUES ({', '.join(values)}) "
        f"ON CONFLICT (dataset, relation) DO UPDATE SET {updates}"
    )
    db.psql(cfg, dbname, sql, tuples_only=False)


def plan(
    cfg: Config, dataset: str, *, serving_db: str | None = None
) -> list[RelationState]:
    """Current migration state of every relation the dataset publishes."""
    serving = serving_db or cfg.dbname(dataset)
    ensure(cfg, serving)
    known = load_states(cfg, serving, dataset)

    out: list[RelationState] = []
    for relation in exposed_relations(dataset):
        if relation in known:
            out.append(known[relation])
        else:
            out.append(
                RelationState(
                    relation=relation,
                    state="legacy",
                    candidate_db=None,
                    legacy_name=None,
                    relkind=db.relation_kind(cfg, serving, relation),
                    detail={},
                )
            )
    return out


def build(
    cfg: Config,
    dataset: str,
    relation: str,
    candidate_db: str,
    *,
    serving_db: str | None = None,
    defer_foreign_keys: bool = False,
) -> RelationState:
    """Carry a candidate relation into the serving database's staging schema.

    The candidate is copied verbatim rather than rebuilt in place. That matters
    for provenance: the bytes that were structurally compared are the bytes that
    end up serving, with nothing regenerated in between.
    """
    serving = serving_db or cfg.dbname(dataset)
    ensure(cfg, serving)

    kind = db.relation_kind(cfg, candidate_db, relation)
    if kind is None:
        raise RuntimeError(
            f"{relation} does not exist in candidate database {candidate_db}"
        )

    _, name = _split(relation)
    staged = f"{STAGING_SCHEMA}.{name}"

    # A matview arrives from pg_dump as a matview definition; a table arrives as
    # data. Either way it lands in the staging schema, never touching the
    # relation currently being served.
    db.psql(
        cfg,
        serving,
        f"DROP {_ALTER.get(kind, 'TABLE')} IF EXISTS {staged} CASCADE",
        tuples_only=False,
    )
    logger.info("transferring %s from %s", relation, candidate_db)
    deferred = db.transfer_relation(
        cfg,
        candidate_db,
        serving,
        relation,
        target_schema=STAGING_SCHEMA,
        defer_foreign_keys=defer_foreign_keys,
    )

    # Held-back foreign keys ride along in the state row so the swap can apply
    # them once every relation they reference has landed. Recording them here
    # rather than in memory means a crash between build and swap does not lose
    # them.
    detail: dict[str, Any] = {}
    if deferred:
        detail["deferred_foreign_keys"] = deferred
        logger.info("%s: %d foreign key(s) deferred", relation, len(deferred))

    set_state(
        cfg,
        serving,
        dataset,
        relation,
        "building",
        candidate_db=candidate_db,
        relkind=kind,
        detail=detail,
    )
    logger.info("%s staged as %s", relation, staged)
    return RelationState(relation, "building", candidate_db, None, kind, detail)


def verify(
    cfg: Config,
    dataset: str,
    relation: str,
    candidate_db: str,
    *,
    serving_db: str | None = None,
) -> tuple[bool, cmp.Comparison]:
    """Structurally compare the staged candidate against what is serving.

    Content is deliberately not a gate. Every serving database here is stale,
    and a pipeline run pulls current upstream data, so row counts are expected
    to move. Structure is the thing that must not move: a column that changed
    type or an index that vanished is a defect or an unrecorded hand-change,
    and either way it needs a human decision before anything is swapped.
    """
    serving = serving_db or cfg.dbname(dataset)
    result = cmp.compare(cfg, serving, candidate_db, ["public"], content=True)

    if result.structurally_clean:
        set_state(
            cfg, serving, dataset, relation, "verified", candidate_db=candidate_db
        )
    return result.structurally_clean, result


def _rename_dependents(schema: str, target: str, suffix: str) -> str:
    """Rename a relation's indexes, constraints, and owned sequences.

    ``ALTER TABLE ... RENAME`` renames only the relation. Its indexes,
    constraints, and owned sequences keep their original names, so the
    incoming copy -- which carries identically named ones -- collides on
    ``SET SCHEMA``. Renaming them out of the way first is what makes the
    cutover possible.

    Emitted as a catalogue-driven DO block rather than generated statements
    so it stays correct for any relation without a round trip to discover
    what exists.
    """
    return f"""
DO $$
DECLARE
    r record;
    ref regclass := '{schema}.{target}'::regclass;
    suffix text := '{suffix}';
BEGIN
    FOR r IN SELECT conname FROM pg_constraint WHERE conrelid = ref
    LOOP
        EXECUTE format(
            'ALTER TABLE %s RENAME CONSTRAINT %I TO %I',
            ref, r.conname, left(r.conname, 63 - length(suffix)) || suffix
        );
    END LOOP;

    FOR r IN
        SELECT c.relname
        FROM pg_index i
        JOIN pg_class c ON c.oid = i.indexrelid
        WHERE i.indrelid = ref
          AND NOT EXISTS (
              SELECT 1 FROM pg_constraint x WHERE x.conindid = i.indexrelid
          )
    LOOP
        EXECUTE format(
            'ALTER INDEX {schema}.%I RENAME TO %I',
            r.relname, left(r.relname, 63 - length(suffix)) || suffix
        );
    END LOOP;

    FOR r IN
        SELECT s.relname
        FROM pg_class s
        JOIN pg_depend d ON d.objid = s.oid
        WHERE s.relkind = 'S' AND d.refobjid = ref AND d.deptype = 'a'
    LOOP
        EXECUTE format(
            'ALTER SEQUENCE {schema}.%I RENAME TO %I',
            r.relname, left(r.relname, 63 - length(suffix)) || suffix
        );
    END LOOP;
END $$;
"""


def _strip_suffix(schema: str, target: str, suffix: str) -> str:
    """Undo :func:`_rename_dependents` so a rolled-back relation looks untouched."""
    return f"""
DO $$
DECLARE
    r record;
    ref regclass := '{schema}.{target}'::regclass;
    suffix text := '{suffix}';
BEGIN
    FOR r IN
        SELECT conname FROM pg_constraint
        WHERE conrelid = ref AND conname LIKE '%' || suffix
    LOOP
        EXECUTE format(
            'ALTER TABLE %s RENAME CONSTRAINT %I TO %I',
            ref, r.conname, left(r.conname, length(r.conname) - length(suffix))
        );
    END LOOP;

    FOR r IN
        SELECT c.relname
        FROM pg_index i
        JOIN pg_class c ON c.oid = i.indexrelid
        WHERE i.indrelid = ref
          AND c.relname LIKE '%' || suffix
          AND NOT EXISTS (
              SELECT 1 FROM pg_constraint x WHERE x.conindid = i.indexrelid
          )
    LOOP
        EXECUTE format(
            'ALTER INDEX {schema}.%I RENAME TO %I',
            r.relname, left(r.relname, length(r.relname) - length(suffix))
        );
    END LOOP;

    FOR r IN
        SELECT s.relname
        FROM pg_class s
        JOIN pg_depend d ON d.objid = s.oid
        WHERE s.relkind = 'S' AND d.refobjid = ref AND d.deptype = 'a'
          AND s.relname LIKE '%' || suffix
    LOOP
        EXECUTE format(
            'ALTER SEQUENCE {schema}.%I RENAME TO %I',
            r.relname, left(r.relname, length(r.relname) - length(suffix))
        );
    END LOOP;
END $$;
"""


def _move_owned_sequences(from_schema: str, to_schema: str, target: str) -> str:
    """Follow a relation's owned sequences into its new schema.

    ``SET SCHEMA`` moves the relation but leaves its sequences behind, which
    would leave the column default pointing across a schema boundary at a
    staging area that later gets dropped.

    The relation is looked up in either schema because this runs after the move
    on the way in and before it on the way out; ``to_regclass`` returns NULL
    rather than raising when a name does not resolve, so the two lookups can be
    tried in order without a failure in between.
    """
    return f"""
DO $$
DECLARE
    r record;
    ref regclass := COALESCE(
        to_regclass('{to_schema}.{target}'),
        to_regclass('{from_schema}.{target}')
    );
BEGIN
    IF ref IS NULL THEN
        RETURN;
    END IF;
    FOR r IN
        SELECT s.relname
        FROM pg_class s
        JOIN pg_namespace n ON n.oid = s.relnamespace
        JOIN pg_depend d ON d.objid = s.oid
        WHERE s.relkind = 'S'
          AND n.nspname = '{from_schema}'
          AND d.refobjid = ref
          AND d.deptype = 'a'
    LOOP
        EXECUTE format(
            'ALTER SEQUENCE {from_schema}.%I SET SCHEMA {to_schema}', r.relname
        );
    END LOOP;
END $$;
"""


def _copy_grants(schema: str, target: str, legacy: str) -> str:
    """Carry the legacy relation's grants onto its replacement.

    ``pg_dump --no-privileges`` deliberately omits grants, so a transferred
    relation arrives owned by the superuser and readable by nobody else. Swapping
    it in without this step revokes the endpoint: PostgREST keeps serving, but
    every request returns ``permission denied for table``. Reading the grants off
    the relation being retired rather than from configuration means the
    replacement inherits exactly what was there, including any grant made by hand
    over the years that no pipeline knows about.

    Grants are read from ``pg_class.relacl`` rather than
    ``information_schema.role_table_grants`` because the information schema only
    reports tables and views. Materialised views are absent from it entirely, so
    reading from there silently drops every grant on a matview and the endpoint
    disappears from the API rather than merely erroring.
    """
    return f"""
DO $$
DECLARE
    ref regclass := to_regclass('{schema}.{legacy}');
    r record;
BEGIN
    IF ref IS NULL THEN
        RETURN;
    END IF;
    FOR r IN
        SELECT pg_get_userbyid(a.grantee) AS grantee_name,
               a.privilege_type
        FROM pg_class c,
             LATERAL aclexplode(coalesce(c.relacl, '{{}}'::aclitem[])) a
        WHERE c.oid = ref
    LOOP
        IF r.grantee_name IS NULL OR r.grantee_name = current_user THEN
            CONTINUE;
        END IF;
        EXECUTE format(
            'GRANT %s ON {schema}.{target} TO %I', r.privilege_type, r.grantee_name
        );
    END LOOP;
END $$;
"""


FK_CLUSTER_SQL = """
SELECT n1.nspname || '.' || c1.relname,
       n2.nspname || '.' || c2.relname
FROM pg_constraint k
JOIN pg_class c1 ON c1.oid = k.conrelid
JOIN pg_namespace n1 ON n1.oid = c1.relnamespace
JOIN pg_class c2 ON c2.oid = k.confrelid
JOIN pg_namespace n2 ON n2.oid = c2.relnamespace
WHERE k.contype = 'f'
  AND n1.nspname = 'public'
  AND n2.nspname = 'public'
"""


def fk_clusters(cfg: Config, dbname: str) -> list[set[str]]:
    """Group relations that are joined by foreign keys.

    ``ALTER TABLE ... RENAME`` preserves the OID, so a foreign key follows the
    relation it points at rather than the name. Swapping a parent on its own
    therefore leaves every child still referencing the renamed legacy copy, and
    reclaim would either fail or cascade the child constraints away. Relations
    tied together by a foreign key have to cut over in the same transaction.
    """
    edges = db.psql(cfg, dbname, FK_CLUSTER_SQL)
    parent: dict[str, str] = {}

    def find(node: str) -> str:
        parent.setdefault(node, node)
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for row in edges:
        if len(row) == 2 and row[0] and row[1]:
            union(row[0], row[1])

    groups: dict[str, set[str]] = {}
    for node in parent:
        groups.setdefault(find(node), set()).add(node)
    return [g for g in groups.values() if len(g) > 1]


def cluster_for(cfg: Config, dbname: str, relation: str) -> set[str]:
    """Return every relation that must swap alongside this one."""
    for group in fk_clusters(cfg, dbname):
        if relation in group:
            return group
    return {relation}


def _populate_staged(cfg: Config, serving: str, name: str, kind: str) -> None:
    """Materialise a staged matview before it is swapped in.

    pg_dump carries a materialised view across as a definition, not as data, so
    a staged matview arrives empty. Refreshing it here rather than after the
    swap means the relation is already populated at the moment it becomes the
    served one -- there is no window in which the endpoint answers with an
    empty result set.

    The definition still points at the base relations in the serving schema, so
    this must run after those have been swapped. In practice that ordering is
    natural: a matview depends on its inputs, and the inputs migrate first.
    """
    if kind != "m":
        return
    logger.info("refreshing staged %s.%s before swap", STAGING_SCHEMA, name)
    db.psql(
        cfg,
        serving,
        f"REFRESH MATERIALIZED VIEW {STAGING_SCHEMA}.{name}",
        tuples_only=False,
    )


def swap(
    cfg: Config,
    dataset: str,
    relation: str,
    *,
    serving_db: str | None = None,
    force: bool = False,
) -> RelationState:
    """Cut over to the staged candidate in a single transaction."""
    serving = serving_db or cfg.dbname(dataset)
    states = load_states(cfg, serving, dataset)
    current = states.get(relation)

    if current is None or current.state not in ("building", "verified"):
        raise RuntimeError(
            f"{relation} is in state "
            f"{current.state if current else 'legacy'}; nothing staged to swap"
        )
    if current.state != "verified" and not force:
        raise RuntimeError(
            f"{relation} has not passed structural comparison; "
            "run verify first, or pass force to override"
        )

    schema, name = _split(relation)
    kind = current.relkind or db.relation_kind(cfg, serving, relation) or "r"
    alter = _ALTER.get(kind, "TABLE")
    legacy = f"{name}{LEGACY_SUFFIX}"

    _populate_staged(cfg, serving, name, kind)

    # One transaction. Readers either see the old relation for the whole of
    # their statement or the new one; there is no window where the name is
    # unresolvable.
    sql = (
        "BEGIN;\n"
        + _rename_dependents(schema, name, LEGACY_SUFFIX)
        + f"ALTER {alter} IF EXISTS {schema}.{name} RENAME TO {legacy};\n"
        + f"ALTER {alter} {STAGING_SCHEMA}.{name} SET SCHEMA {schema};\n"
        + _move_owned_sequences(STAGING_SCHEMA, schema, name)
        + _copy_grants(schema, name, legacy)
        + "COMMIT;"
    )
    db.psql(cfg, serving, sql, tuples_only=False)

    set_state(
        cfg,
        serving,
        dataset,
        relation,
        "swapped",
        legacy_name=f"{schema}.{legacy}",
        relkind=kind,
    )
    logger.info("%s swapped; legacy retained as %s.%s", relation, schema, legacy)
    return RelationState(
        relation, "swapped", current.candidate_db, f"{schema}.{legacy}", kind, {}
    )


def swap_cluster(
    cfg: Config,
    dataset: str,
    relations: Sequence[str],
    *,
    serving_db: str | None = None,
    force: bool = False,
) -> list[RelationState]:
    """Cut over a set of foreign-key-linked relations in one transaction.

    Individually swapping relations joined by foreign keys leaves the graph
    inconsistent, because a foreign key tracks the OID of the relation it points
    at and follows it through the rename. Doing the whole cluster inside a single
    transaction means the constraints land pointing at the new relations, and any
    failure rolls the entire group back rather than stranding half of it.
    """
    serving = serving_db or cfg.dbname(dataset)
    states = load_states(cfg, serving, dataset)
    ordered = sorted(relations)

    staged: list[tuple[str, str, str, str, str]] = []
    for rel in ordered:
        current = states.get(rel)
        if current is None or current.state not in ("building", "verified"):
            raise RuntimeError(
                f"{rel} is in state "
                f"{current.state if current else 'legacy'}; nothing staged to swap"
            )
        if current.state != "verified" and not force:
            raise RuntimeError(
                f"{rel} has not passed structural comparison; "
                "run verify first, or pass force to override"
            )
        schema, name = _split(rel)
        kind = current.relkind or db.relation_kind(cfg, serving, rel) or "r"
        staged.append((rel, schema, name, kind, _ALTER.get(kind, "TABLE")))

    # Populate any staged matviews before the transaction opens, for the same
    # reason as the single-relation path: a matview must not become the served
    # relation while still empty.
    for _, _, name, kind, _ in staged:
        _populate_staged(cfg, serving, name, kind)

    parts = ["BEGIN;\n"]
    # Rename every legacy relation and its dependents aside first, so that no
    # incoming relation collides with a name still held by the outgoing set.
    for _, schema, name, _, alter in staged:
        parts.append(_rename_dependents(schema, name, LEGACY_SUFFIX))
        parts.append(
            f"ALTER {alter} IF EXISTS {schema}.{name} "
            f"RENAME TO {name}{LEGACY_SUFFIX};\n"
        )
    # Only then move the candidates in, by which point every name is free.
    for _, schema, name, _, alter in staged:
        parts.append(f"ALTER {alter} {STAGING_SCHEMA}.{name} SET SCHEMA {schema};\n")
        parts.append(_move_owned_sequences(STAGING_SCHEMA, schema, name))
        parts.append(_copy_grants(schema, name, f"{name}{LEGACY_SUFFIX}"))

    # Foreign keys held back during staging are applied last, inside the same
    # transaction. By this point every relation in the cluster is in place, so
    # each reference resolves against the incoming data rather than the
    # outgoing copy it was dumped beside.
    for rel, _, _, _, _ in staged:
        for statement in states[rel].detail.get("deferred_foreign_keys", []):
            text = statement.strip()
            parts.append(text if text.endswith(";") else f"{text};")
            parts.append("\n")

    parts.append("COMMIT;")

    db.psql(cfg, serving, "".join(parts), tuples_only=False)

    results: list[RelationState] = []
    for rel, schema, name, kind, _ in staged:
        legacy = f"{schema}.{name}{LEGACY_SUFFIX}"
        set_state(
            cfg, serving, dataset, rel, "swapped", legacy_name=legacy, relkind=kind
        )
        results.append(
            RelationState(rel, "swapped", states[rel].candidate_db, legacy, kind, {})
        )
    logger.info(
        "swapped %d relations as one cluster: %s",
        len(results),
        ", ".join(r.relation for r in results),
    )
    return results


def rollback(
    cfg: Config, dataset: str, relation: str, *, serving_db: str | None = None
) -> RelationState:
    """Put the legacy relation back. Available until the legacy copy is dropped."""
    serving = serving_db or cfg.dbname(dataset)
    states = load_states(cfg, serving, dataset)
    current = states.get(relation)

    if current is None or not current.rollbackable:
        raise RuntimeError(
            f"{relation} cannot be rolled back from state "
            f"{current.state if current else 'legacy'}"
        )

    schema, name = _split(relation)
    kind = current.relkind or "r"
    alter = _ALTER.get(kind, "TABLE")
    legacy = f"{name}{LEGACY_SUFFIX}"

    # Exact reverse of the swap: move the candidate back to staging with its
    # sequences, restore the legacy name, then strip the suffix off the
    # dependents so the relation is indistinguishable from its pre-swap self.
    sql = (
        "BEGIN;\n"
        + _move_owned_sequences(schema, STAGING_SCHEMA, name)
        + f"ALTER {alter} {schema}.{name} SET SCHEMA {STAGING_SCHEMA};\n"
        + f"ALTER {alter} {schema}.{legacy} RENAME TO {name};\n"
        + _strip_suffix(schema, name, LEGACY_SUFFIX)
        + "COMMIT;"
    )
    db.psql(cfg, serving, sql, tuples_only=False)

    set_state(
        cfg, serving, dataset, relation, "building", candidate_db=current.candidate_db
    )
    logger.info("%s rolled back to the legacy relation", relation)
    return RelationState(relation, "building", current.candidate_db, None, kind, {})


def reclaim(
    cfg: Config,
    dataset: str,
    *,
    serving_db: str | None = None,
    relations: Sequence[str] | None = None,
) -> list[tuple[str, str]]:
    """Drop retained legacy relations. This is the point of no return."""
    serving = serving_db or cfg.dbname(dataset)
    states = load_states(cfg, serving, dataset)

    targets = [
        s
        for s in states.values()
        if s.state == "swapped"
        and s.legacy_name
        and (not relations or s.relation in relations)
    ]

    # Drop derived objects before the tables they read. A legacy matview whose
    # definition still binds to a legacy table would otherwise be carried off by
    # that table's CASCADE, and if the matview had not itself been swapped yet
    # the served copy disappears with it. Ordering by relkind puts matviews and
    # views ahead of tables.
    order = {"m": 0, "v": 1, "f": 2, "r": 3, "p": 3}
    targets.sort(key=lambda s: order.get(s.relkind or "r", 3))

    dropped: list[tuple[str, str]] = []
    for state in targets:
        alter = _ALTER.get(state.relkind or "r", "TABLE")

        # A prior partial reclaim may have already dropped this legacy copy
        # (a CASCADE can carry a relation the loop has not reached yet).
        # to_regclass returns NULL instead of raising, so already-gone
        # relations are simply marked reclaimed.
        gone = db.scalar(
            cfg,
            serving,
            f"SELECT to_regclass({db.quote_literal(state.legacy_name or '')}) IS NULL",
        )
        if gone == "t":
            logger.info("%s already gone; marking reclaimed", state.legacy_name)
            set_state(cfg, serving, dataset, state.relation, "reclaimed")
            dropped.append((state.relation, state.legacy_name or ""))
            continue

        # CASCADE is necessary -- a retired relation still owns its constraints
        # and sequences -- but it must not reach anything currently serving.
        collateral = db.psql(
            cfg,
            serving,
            f"""
            SELECT DISTINCT dn.nspname || '.' || dc.relname
            FROM pg_depend d
            JOIN pg_rewrite w ON w.oid = d.objid
            JOIN pg_class dc ON dc.oid = w.ev_class
            JOIN pg_namespace dn ON dn.oid = dc.relnamespace
            WHERE d.refobjid = {db.quote_literal(state.legacy_name or "")}::regclass
              AND dc.relname NOT LIKE '%{LEGACY_SUFFIX}'
              AND dc.oid <> {db.quote_literal(state.legacy_name or "")}::regclass
            """,
        )
        blocking = [row[0] for row in collateral if row and row[0]]
        if blocking:
            raise RuntimeError(
                f"refusing to drop {state.legacy_name}: still serving "
                f"{', '.join(blocking)}. Migrate those first."
            )

        db.psql(
            cfg,
            serving,
            f"DROP {alter} IF EXISTS {state.legacy_name} CASCADE",
            tuples_only=False,
        )
        set_state(cfg, serving, dataset, state.relation, "reclaimed")
        logger.info("dropped %s", state.legacy_name)
        dropped.append((state.relation, state.legacy_name or ""))
    return dropped


def render_plan(dataset: str, states: Iterable[RelationState]) -> str:
    rows = list(states)
    lines = [
        f"# Migration plan: {dataset}",
        "",
        f"Generated {_now()}",
        "",
        "| relation | state | candidate | legacy retained |",
        "|---|---|---|---|",
    ]
    for state in rows:
        lines.append(
            f"| `{state.relation}` | {state.state} | "
            f"{state.candidate_db or '—'} | {state.legacy_name or '—'} |"
        )

    counts: dict[str, int] = {}
    for state in rows:
        counts[state.state] = counts.get(state.state, 0) + 1
    lines += [
        "",
        "Summary: " + ", ".join(f"{v} {k}" for k, v in sorted(counts.items())),
    ]
    return "\n".join(lines) + "\n"
