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
    db.transfer_relation(
        cfg, candidate_db, serving, relation, target_schema=STAGING_SCHEMA
    )

    set_state(
        cfg,
        serving,
        dataset,
        relation,
        "building",
        candidate_db=candidate_db,
        relkind=kind,
    )
    logger.info("%s staged as %s", relation, staged)
    return RelationState(relation, "building", candidate_db, None, kind, {})


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

    # One transaction. Readers either see the old relation for the whole of
    # their statement or the new one; there is no window where the name is
    # unresolvable.
    sql = (
        "BEGIN;\n"
        f"ALTER {alter} IF EXISTS {schema}.{name} RENAME TO {legacy};\n"
        f"ALTER {alter} {STAGING_SCHEMA}.{name} SET SCHEMA {schema};\n"
        "COMMIT;"
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

    sql = (
        "BEGIN;\n"
        f"ALTER {alter} {schema}.{name} SET SCHEMA {STAGING_SCHEMA};\n"
        f"ALTER {alter} {schema}.{legacy} RENAME TO {name};\n"
        "COMMIT;"
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

    dropped: list[tuple[str, str]] = []
    for state in targets:
        alter = _ALTER.get(state.relkind or "r", "TABLE")
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
