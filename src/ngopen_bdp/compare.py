"""Structural and content comparison between two databases.

Migration verification has two halves that answer different questions, and
conflating them would make the whole exercise useless.

**Structural comparison is a gate.** Relations, columns, types, nullability,
indexes, constraints, functions and grants must match exactly. Every
difference is either a bug in the new pipeline or an undocumented change made
by hand in production that was never written back to the ETL source. Both are
findings worth acting on; neither is acceptable to wave through. This mode
found the ``_staging_*`` CASCADE bug and the ``fiscal_year::text`` cast during
the usaspending validation run.

**Content comparison is advisory.** The live databases are stale: they were
built against older upstream vintages. A freshly built database pulls current
data, so row counts *will* differ, and differing is the correct outcome. This
mode records the honest delta so the audit report says what changed and by how
much, without pretending a growing dataset is a regression.

**Snapshot** captures the structure of relations that are about to be removed,
so a deletion remains auditable after the fact.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable

from . import db
from .config import Config

# ----------------------------------------------------------------------------
# introspection queries
#
# Each returns a stable, ordered projection so two databases can be compared
# by simple set arithmetic rather than by parsing DDL text.
# ----------------------------------------------------------------------------

RELATIONS_SQL = """
SELECT n.nspname, c.relname, c.relkind
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = ANY($SCHEMAS$)
  AND c.relkind IN ('r', 'p', 'v', 'm', 'f')
  AND c.relname NOT IN (
      'spatial_ref_sys', 'geometry_columns', 'geography_columns',
      'raster_columns', 'raster_overviews',
      'pg_stat_statements', 'pg_stat_statements_info'
  )
ORDER BY 1, 2
"""

COLUMNS_SQL = """
SELECT n.nspname, c.relname, a.attname,
       format_type(a.atttypid, a.atttypmod),
       CASE WHEN a.attnotnull THEN 'NOT NULL' ELSE 'NULL' END
FROM pg_attribute a
JOIN pg_class c ON c.oid = a.attrelid
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = ANY($SCHEMAS$)
  AND c.relkind IN ('r', 'p', 'v', 'm', 'f')
  AND a.attnum > 0
  AND NOT a.attisdropped
ORDER BY 1, 2, a.attnum
"""

INDEXES_SQL = """
SELECT schemaname, tablename, indexname, indexdef
FROM pg_indexes
WHERE schemaname = ANY($SCHEMAS$)
  AND tablename <> 'spatial_ref_sys'
ORDER BY 1, 2, 3
"""

CONSTRAINTS_SQL = """
SELECT n.nspname, c.relname, con.conname, pg_get_constraintdef(con.oid)
FROM pg_constraint con
JOIN pg_class c ON c.oid = con.conrelid
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = ANY($SCHEMAS$)
ORDER BY 1, 2, 3
"""

FUNCTIONS_SQL = """
SELECT n.nspname, p.proname, pg_get_function_identity_arguments(p.oid)
FROM pg_proc p
JOIN pg_namespace n ON n.oid = p.pronamespace
WHERE n.nspname = ANY($SCHEMAS$)
  AND p.proname NOT LIKE 'st\\_%'
  AND p.proname NOT LIKE '\\_st\\_%'
  AND p.proname NOT LIKE 'postgis%'
  AND p.proname NOT LIKE 'geometry%'
  AND p.proname NOT LIKE 'geography%'
  AND p.proname NOT LIKE 'box%'
  AND p.proname NOT LIKE 'raster%'
ORDER BY 1, 2, 3
"""

GRANTS_SQL = """
SELECT table_schema, table_name, grantee, privilege_type
FROM information_schema.role_table_grants
WHERE table_schema = ANY($SCHEMAS$)
  AND grantee <> 'PUBLIC'
ORDER BY 1, 2, 3, 4
"""

COUNTS_SQL = """
SELECT n.nspname, c.relname, c.reltuples::bigint
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = ANY($SCHEMAS$)
  AND c.relkind IN ('r', 'p', 'm')
  AND c.relname NOT IN ('spatial_ref_sys')
ORDER BY 1, 2
"""

GEOMETRY_SQL = """
SELECT f_table_schema, f_table_name, f_geometry_column, srid, type
FROM geometry_columns
WHERE f_table_schema = ANY($SCHEMAS$)
ORDER BY 1, 2, 3
"""

# Aspects checked by --structural. Order is deliberate: relation-level
# differences are reported before column-level ones, so the report reads
# from coarse to fine.
STRUCTURAL_ASPECTS = (
    ("relations", RELATIONS_SQL, 2),
    ("columns", COLUMNS_SQL, 3),
    ("indexes", INDEXES_SQL, 3),
    ("constraints", CONSTRAINTS_SQL, 3),
    ("functions", FUNCTIONS_SQL, 3),
    ("grants", GRANTS_SQL, 4),
)


def _schemas_literal(schemas: Iterable[str]) -> str:
    joined = ", ".join("'" + s.replace("'", "''") + "'" for s in schemas)
    return f"ARRAY[{joined}]"


def _query(
    cfg: Config, dbname: str, sql: str, schemas: Iterable[str]
) -> list[list[str]]:
    return db.psql(cfg, dbname, sql.replace("$SCHEMAS$", _schemas_literal(schemas)))


def _key(row: list[str], key_len: int) -> str:
    return ".".join(row[:key_len])


def _value(row: list[str], key_len: int) -> str:
    return " | ".join(row[key_len:])


# ----------------------------------------------------------------------------
# results
# ----------------------------------------------------------------------------


@dataclass
class AspectDiff:
    """Differences found in one structural aspect."""

    aspect: str
    only_left: list[str] = field(default_factory=list)
    only_right: list[str] = field(default_factory=list)
    changed: list[tuple[str, str, str]] = field(default_factory=list)

    @property
    def clean(self) -> bool:
        return not (self.only_left or self.only_right or self.changed)

    @property
    def count(self) -> int:
        return len(self.only_left) + len(self.only_right) + len(self.changed)


@dataclass
class CountDelta:
    """Row-count movement for one relation. Advisory, never a gate."""

    relation: str
    left: int | None
    right: int | None

    @property
    def delta(self) -> int | None:
        if self.left is None or self.right is None:
            return None
        return self.right - self.left

    @property
    def pct(self) -> float | None:
        if self.left is None or self.right is None or self.left == 0:
            return None
        return (self.right - self.left) / self.left * 100.0


@dataclass
class Comparison:
    left: str
    right: str
    schemas: tuple[str, ...]
    structural: list[AspectDiff] = field(default_factory=list)
    counts: list[CountDelta] = field(default_factory=list)
    geometry: AspectDiff | None = None
    generated_at: str = ""

    @property
    def structurally_clean(self) -> bool:
        return all(d.clean for d in self.structural) and (
            self.geometry is None or self.geometry.clean
        )


# ----------------------------------------------------------------------------
# comparison
# ----------------------------------------------------------------------------


def compare_aspect(
    cfg: Config,
    left: str,
    right: str,
    aspect: str,
    sql: str,
    key_len: int,
    schemas: Iterable[str],
) -> AspectDiff:
    """Compare one aspect between two databases."""
    schemas = tuple(schemas)
    left_rows = {
        _key(r, key_len): _value(r, key_len) for r in _query(cfg, left, sql, schemas)
    }
    right_rows = {
        _key(r, key_len): _value(r, key_len) for r in _query(cfg, right, sql, schemas)
    }

    diff = AspectDiff(aspect=aspect)
    for key in sorted(set(left_rows) - set(right_rows)):
        diff.only_left.append(key)
    for key in sorted(set(right_rows) - set(left_rows)):
        diff.only_right.append(key)
    for key in sorted(set(left_rows) & set(right_rows)):
        if left_rows[key] != right_rows[key]:
            diff.changed.append((key, left_rows[key], right_rows[key]))
    return diff


def compare_structural(
    cfg: Config, left: str, right: str, schemas: Iterable[str]
) -> list[AspectDiff]:
    schemas = tuple(schemas)
    return [
        compare_aspect(cfg, left, right, aspect, sql, key_len, schemas)
        for aspect, sql, key_len in STRUCTURAL_ASPECTS
    ]


def compare_geometry(
    cfg: Config, left: str, right: str, schemas: Iterable[str]
) -> AspectDiff:
    """Compare geometry column SRIDs and types.

    Kept separate from the generic column comparison because an SRID change is
    a silent, high-consequence break: queries keep working and return wrong
    answers.
    """
    return compare_aspect(cfg, left, right, "geometry", GEOMETRY_SQL, 3, schemas)


def compare_counts(
    cfg: Config, left: str, right: str, schemas: Iterable[str]
) -> list[CountDelta]:
    """Compare row-count estimates. Advisory only.

    Uses ``reltuples`` rather than ``COUNT(*)``: an exact count on
    ``rpt.transaction_search`` takes longer than the entire rest of the
    comparison and would make the tool unusable on the datasets that most need
    it. ``reltuples`` is -1 when a relation has never been analysed, which is
    reported as unknown rather than as zero.
    """
    schemas = tuple(schemas)

    def load(dbname: str) -> dict[str, int | None]:
        out: dict[str, int | None] = {}
        for row in _query(cfg, dbname, COUNTS_SQL, schemas):
            value = int(row[2])
            out[f"{row[0]}.{row[1]}"] = None if value < 0 else value
        return out

    left_counts = load(left)
    right_counts = load(right)

    deltas = []
    for relation in sorted(set(left_counts) | set(right_counts)):
        deltas.append(
            CountDelta(
                relation=relation,
                left=left_counts.get(relation),
                right=right_counts.get(relation),
            )
        )
    return deltas


def compare(
    cfg: Config,
    left: str,
    right: str,
    schemas: Iterable[str],
    *,
    structural: bool = True,
    content: bool = True,
) -> Comparison:
    schemas = tuple(schemas)
    result = Comparison(
        left=left,
        right=right,
        schemas=schemas,
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
    if structural:
        result.structural = compare_structural(cfg, left, right, schemas)
        result.geometry = compare_geometry(cfg, left, right, schemas)
    if content:
        result.counts = compare_counts(cfg, left, right, schemas)
    return result


# ----------------------------------------------------------------------------
# snapshot
# ----------------------------------------------------------------------------


def snapshot(cfg: Config, dbname: str, schemas: Iterable[str]) -> dict[str, Any]:
    """Capture full structure of a database as JSON.

    Written before a destructive change so the removal stays auditable once
    the objects no longer exist.
    """
    schemas = tuple(schemas)
    out: dict[str, Any] = {
        "database": dbname,
        "schemas": list(schemas),
        "captured_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    for aspect, sql, _ in STRUCTURAL_ASPECTS:
        out[aspect] = _query(cfg, dbname, sql, schemas)
    out["geometry"] = _query(cfg, dbname, GEOMETRY_SQL, schemas)
    out["counts"] = _query(cfg, dbname, COUNTS_SQL, schemas)
    return out


# ----------------------------------------------------------------------------
# reporting
# ----------------------------------------------------------------------------


def _fmt_int(value: int | None) -> str:
    return "unknown" if value is None else f"{value:,}"


def render_markdown(result: Comparison, *, title: str = "") -> str:
    """Render a comparison as a committable markdown audit report."""
    lines: list[str] = []
    heading = title or f"Comparison: `{result.left}` vs `{result.right}`"
    lines.append(f"# {heading}")
    lines.append("")
    lines.append(f"Generated {result.generated_at}")
    lines.append("")
    lines.append("| | |")
    lines.append("|---|---|")
    lines.append(f"| Reference (left) | `{result.left}` |")
    lines.append(f"| Candidate (right) | `{result.right}` |")
    lines.append(f"| Schemas | {', '.join('`' + s + '`' for s in result.schemas)} |")
    lines.append("")

    if result.structural:
        verdict = "PASS" if result.structurally_clean else "FAIL"
        lines.append("## Structural comparison")
        lines.append("")
        lines.append(
            "Structural equivalence is a gate. Every difference below is either a "
            "defect in the candidate pipeline or a change made by hand in the "
            "reference database that was never written back to source."
        )
        lines.append("")
        lines.append(f"**Verdict: {verdict}**")
        lines.append("")
        lines.append("| Aspect | Only in reference | Only in candidate | Changed |")
        lines.append("|---|---:|---:|---:|")
        aspects = list(result.structural)
        if result.geometry is not None:
            aspects.append(result.geometry)
        for diff in aspects:
            lines.append(
                f"| {diff.aspect} | {len(diff.only_left)} | "
                f"{len(diff.only_right)} | {len(diff.changed)} |"
            )
        lines.append("")

        for diff in aspects:
            if diff.clean:
                continue
            lines.append(f"### {diff.aspect}")
            lines.append("")
            if diff.only_left:
                lines.append(f"**Only in `{result.left}`** ({len(diff.only_left)})")
                lines.append("")
                for key in diff.only_left:
                    lines.append(f"- `{key}`")
                lines.append("")
            if diff.only_right:
                lines.append(f"**Only in `{result.right}`** ({len(diff.only_right)})")
                lines.append("")
                for key in diff.only_right:
                    lines.append(f"- `{key}`")
                lines.append("")
            if diff.changed:
                lines.append(f"**Changed** ({len(diff.changed)})")
                lines.append("")
                for key, left_value, right_value in diff.changed:
                    lines.append(f"- `{key}`")
                    lines.append(f"  - reference: `{left_value}`")
                    lines.append(f"  - candidate: `{right_value}`")
                lines.append("")

    if result.counts:
        lines.append("## Content comparison")
        lines.append("")
        lines.append(
            "Row counts are advisory, never a gate. The reference database was "
            "built against an older upstream vintage; the candidate pulls current "
            "data. Differences are expected and are recorded here as the honest "
            "delta rather than treated as regressions. Counts are `reltuples` "
            "estimates, reported as unknown where a relation has never been "
            "analysed."
        )
        lines.append("")
        lines.append("| Relation | Reference | Candidate | Delta | Change |")
        lines.append("|---|---:|---:|---:|---:|")
        for delta in result.counts:
            pct = "" if delta.pct is None else f"{delta.pct:+.1f}%"
            change = "" if delta.delta is None else f"{delta.delta:+,}"
            lines.append(
                f"| `{delta.relation}` | {_fmt_int(delta.left)} | "
                f"{_fmt_int(delta.right)} | {change} | {pct} |"
            )
        lines.append("")

    return "\n".join(lines) + "\n"


def render_json(result: Comparison) -> str:
    payload = {
        "left": result.left,
        "right": result.right,
        "schemas": list(result.schemas),
        "generated_at": result.generated_at,
        "structurally_clean": result.structurally_clean,
        "structural": [
            {
                "aspect": d.aspect,
                "only_left": d.only_left,
                "only_right": d.only_right,
                "changed": [
                    {"key": k, "left": lv, "right": rv} for k, lv, rv in d.changed
                ],
            }
            for d in (
                result.structural + ([result.geometry] if result.geometry else [])
            )
        ],
        "counts": [
            {
                "relation": c.relation,
                "left": c.left,
                "right": c.right,
                "delta": c.delta,
            }
            for c in result.counts
        ],
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"
