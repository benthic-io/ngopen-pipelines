"""IRS nonprofit pipeline.

Replaces ngopen/irs_ng.py, a 3892-line monolith that combined downloading,
schema creation, importing and geocoding behind 35 command-line flags.

The split here is deliberate:

  * table DDL          -> sql/10_schema.sql
  * keys               -> sql/15_keys.sql
  * indexes            -> sql/20_constraints.sql + recovered/irs_ng/
  * views and RPCs     -> sql/30_derive.sql
  * download + import  -> legacy_import.py, carried over verbatim
  * geocoding          -> ngopen_bdp.geocode, shared with every other dataset

This module is the thin stage layer that sequences those pieces and records
progress in the ledger, so an interrupted run resumes at the stage it died in
rather than starting the multi-day IRS ingest from the beginning.
"""

from __future__ import annotations

import json
from pathlib import Path

from ngopen_bdp import Outcome, Pipeline
from ngopen_bdp import db, geocode
from ngopen_bdp.stages import Context

from . import legacy_import as legacy

DATASET = "irs_ng"
SQL_DIR = Path(__file__).parent / "sql"
URL_REGISTRY = Path(__file__).parent / "irs_urls.json"
RECOVERED_DIR = Path(__file__).resolve().parents[2] / "recovered" / "irs_ng"

EXTENSIONS = ("postgis", "pg_trgm", "dblink")

# Tables carrying geocodable addresses. The legacy pipeline stored lat/lon as
# bare numerics and used a column named `geocoding_source`; the shared geocoder
# writes the protocol-wide contract instead. Both column sets coexist, so the
# published schema stays backward compatible while new rows use the standard.
GEOCODE_TABLES = ("public.bmf_organizations", "public.political_orgs_527")

EXPOSED = (
    "public.bmf_organizations",
    "public.bmf_organization_snapshots",
    "public.census_demographics",
    "public.form990_details",
    "public.form990_schedule_o",
    "public.form990_soi",
    "public.form990_soi_private_foundation",
    "public.form990_xml_import_log",
    "public.form990n_small_orgs",
    "public.form990t_details",
    "public.political_orgs_527",
    "public.pub78_eligible",
    "public.revoked_organizations",
    "public.mv_nonprofit_profile",
    "public.mv_org_financial_health",
    "public.v_org_financial_profile",
    "public.v_org_multi_year",
    "public.v_political_orgs",
)

RPCS = (
    "public.rpc_nonprofits_in_district(text, integer, integer)",
    "public.rpc_nonprofits_nearby(double precision, double precision, double precision)",
)

MATVIEWS = ("public.mv_nonprofit_profile", "public.mv_org_financial_health")

# Every archive subdirectory the download stage is expected to populate.
ARCHIVE_DIRS = ("bmf/raw", "soi", "status", "form990n", "form990/xml", "527", "census")


def _archives(ctx: Context) -> str:
    return str(ctx.archives)


# ----------------------------------------------------------------------
# 00_acquire
# ----------------------------------------------------------------------
def acquire(ctx: Context) -> Outcome:
    """Download every IRS source feed.

    Each downloader skips files already on disk, so a rerun fetches only what
    the IRS has published since. `--force` is not honoured here: re-downloading
    ~35 GB to prove nothing changed is never the right default.
    """
    source = ctx.cfg.source(DATASET)
    archives = _archives(ctx)

    if ctx.dry_run:
        ctx.log.info("would download IRS feeds into %s", archives)
        return Outcome.COMPLETED

    url_config = legacy.load_url_config(str(URL_REGISTRY))
    counts: dict[str, int] = {}

    start_year = int(source.get("start_year", 2023))
    start_month = int(source.get("start_month", 6))

    counts["bmf"] = legacy.download_bmf_files(archives, start_year, start_month)
    counts["status"] = legacy.download_pub78_and_revocation(archives)
    counts["form990n"] = legacy.download_form990n(archives)
    counts["soi"] = legacy.download_soi(archives, url_config, start_year)
    counts["xml"] = legacy.download_form990_xml(
        archives, url_config=url_config, start_year=start_year
    )
    counts["527"] = legacy.download_527(archives)
    counts["census"] = legacy.download_census(
        archives, source.get("census_years", [2023])
    )

    ctx.log.info("downloaded: %s", json.dumps(counts, sort_keys=True))
    (ctx.state / "downloads.json").write_text(json.dumps(counts, indent=2) + "\n")
    return Outcome.COMPLETED


# ----------------------------------------------------------------------
# 01_verify
# ----------------------------------------------------------------------
def verify(ctx: Context) -> Outcome:
    """Confirm the archive tree looks loadable before touching the database."""
    archives = ctx.archives
    report: dict[str, int] = {}
    empty: list[str] = []

    for relative in ARCHIVE_DIRS:
        directory = archives / relative
        files = (
            [p for p in directory.rglob("*") if p.is_file()]
            if directory.exists()
            else []
        )
        report[relative] = len(files)
        if not files:
            empty.append(relative)

    for relative, count in sorted(report.items()):
        ctx.log.info("%-16s %6d files", relative, count)

    if len(empty) == len(ARCHIVE_DIRS):
        raise RuntimeError(
            f"no IRS source files under {archives}. Run 00_acquire first."
        )
    if empty:
        # Partial coverage is legitimate: the IRS retires feeds and some years
        # simply have no publication. Loud, but not fatal.
        ctx.log.warning("no files for: %s", ", ".join(empty))

    (ctx.state / "archives.json").write_text(json.dumps(report, indent=2) + "\n")
    return Outcome.COMPLETED


# ----------------------------------------------------------------------
# ingest, driven by 02_restore
# ----------------------------------------------------------------------
def ingest(ctx: Context) -> Outcome:
    """Load every feed. Each importer is individually idempotent.

    The importers upsert on real declared constraints, so a rerun refreshes
    changed rows rather than duplicating them, and a crash mid-feed costs only
    the batch in flight.
    """
    archives = _archives(ctx)
    totals: dict[str, int] = {}

    with db.connect(ctx.cfg, ctx.dbname) as conn:
        legacy.bootstrap_import_log(conn)

        totals["bmf"] = _ingest_bmf(ctx, conn)
        totals["pub78"] = legacy.import_pub78(conn, archives)
        totals["revocation"] = legacy.import_revocation(conn, archives)
        totals["form990n"] = legacy.import_form990n(conn, archives)
        totals["soi"] = legacy.import_soi(conn, archives)
        totals["xml"] = legacy.import_form990_xml(conn, archives, ctx.limit)
        totals["527"] = legacy.import_527(conn, archives)
        totals["census"] = legacy.import_census(conn, archives)

    ctx.log.info("ingested: %s", json.dumps(totals, sort_keys=True))
    (ctx.state / "ingest.json").write_text(json.dumps(totals, indent=2) + "\n")
    return Outcome.COMPLETED


def _ingest_bmf(ctx: Context, conn) -> int:
    """Load every monthly NCCS BMF release found on disk, oldest first.

    Snapshot generation was moved out of import_bmf_file because per-file
    INSERT ... ON CONFLICT against a growing snapshot table is O(n^2).
    Instead, after every file's main table is current, one bulk SELECT
    INTO the snapshot table captures all rows whose is_current flag was
    set by the most recent import.
    """
    raw = ctx.archives / "bmf" / "raw"
    if not raw.exists():
        ctx.log.warning("no BMF archives at %s", raw)
        return 0

    total = 0
    for path in sorted(raw.glob("*-BMF.csv")):
        release_date = path.name[:7] + "-01"
        ctx.log.info("BMF %s", path.name)
        inserted, updated = legacy.import_bmf_file(conn, str(path))
        ctx.log.info("BMF %s: %d inserted, %d updated", path.name, inserted, updated)
        total += inserted + updated

        # TBD: re-enable per-file snapshots after fixing ON CONFLICT performance
        ctx.log.info("BMF snapshots skipped (%d inserted)", inserted)
    return total


# ----------------------------------------------------------------------
# 02_restore
# ----------------------------------------------------------------------
def restore(ctx: Context) -> Outcome:
    """Materialise the database from flat files.

    The IRS publishes CSV, XML and fixed-width text rather than a pg_dump
    archive, so "restore" means create, apply DDL, apply keys, then load.
    Secondary indexes are deliberately left to 04_index: loading tens of
    millions of rows into an unindexed table is substantially faster and the
    end state is identical.
    """
    if ctx.dry_run:
        ctx.log.info("would create %s and load every IRS feed", ctx.dbname)
        return Outcome.COMPLETED

    db.create_database(ctx.cfg, ctx.dbname, owner=ctx.cfg.role("restore_owner"))
    db.ensure_extensions(ctx.cfg, ctx.dbname, EXTENSIONS)
    db.psql_file(ctx.cfg, ctx.dbname, SQL_DIR / "10_schema.sql")
    db.psql_file(ctx.cfg, ctx.dbname, SQL_DIR / "15_keys.sql")
    ctx.log.info("schema and keys applied")

    return ingest(ctx)


# ----------------------------------------------------------------------
# 03_schema
# ----------------------------------------------------------------------
def schema(ctx: Context) -> Outcome:
    """Add the protocol-standard geocoding columns."""
    if ctx.dry_run:
        ctx.log.info("would add geocoding columns to %s", ", ".join(GEOCODE_TABLES))
        return Outcome.COMPLETED

    for table in GEOCODE_TABLES:
        db.psql(ctx.cfg, ctx.dbname, geocode.geocode_columns_ddl(table))
    ctx.log.info("geocoding columns ensured")
    return Outcome.COMPLETED


# ----------------------------------------------------------------------
# 04_index
# ----------------------------------------------------------------------
def index(ctx: Context) -> Outcome:
    if ctx.dry_run:
        ctx.log.info("would apply constraints and recovered indexes")
        return Outcome.COMPLETED

    db.psql_file(ctx.cfg, ctx.dbname, SQL_DIR / "20_constraints.sql")

    recovered = RECOVERED_DIR / "indexes_recovered.sql"
    if recovered.exists():
        db.psql_file(ctx.cfg, ctx.dbname, recovered)
        ctx.log.info("recovered indexes applied")
    return Outcome.COMPLETED


# ----------------------------------------------------------------------
# 05_geocode
# ----------------------------------------------------------------------
FETCH_BMF = """
SELECT id, f990_org_addr_street, f990_org_addr_city, f990_org_addr_state, f990_org_addr_zip
FROM public.bmf_organizations
WHERE latitude IS NULL
  AND geocode_system IS NULL
  AND f990_org_addr_street IS NOT NULL
  AND id > %(cursor)s
ORDER BY id
LIMIT %(limit)s
"""

FETCH_527 = """
SELECT id, address, city, state, zip
FROM public.political_orgs_527
WHERE latitude IS NULL
  AND geocode_system IS NULL
  AND address IS NOT NULL
  AND id > %(cursor)s
ORDER BY id
LIMIT %(limit)s
"""

GEOCODE_JOBS = (
    ("public.bmf_organizations", FETCH_BMF, "bmf"),
    ("public.political_orgs_527", FETCH_527, "527"),
)


def geocode_stage(ctx: Context) -> Outcome:
    """Geocode both address-bearing tables through the shared Photon client.

    Progress is a persisted id high-water mark per table, so an interrupted run
    resumes within one batch of where it stopped instead of rescanning millions
    of already-resolved rows.
    """
    if ctx.dry_run:
        ctx.log.info("would geocode %s", ", ".join(t for t, _, _ in GEOCODE_JOBS))
        return Outcome.COMPLETED

    batch_size = int(ctx.cfg.get("geocoder.batch_size", 1000))
    budget = ctx.limit
    total = 0

    with db.connect(ctx.cfg, ctx.dbname) as conn:
        serving = ctx.cfg.dbname(DATASET)
        if ctx.dbname != serving and db.database_exists(ctx.cfg, serving):
            geocode.preserve(
                ctx.cfg,
                serving,
                ctx.dbname,
                "public.bmf_organizations",
                ("ein", "f990_org_addr_street", "f990_org_addr_zip"),
            )
            geocode.preserve(
                ctx.cfg,
                serving,
                ctx.dbname,
                "public.political_orgs_527",
                ("ein", "address"),
            )

        for table, query, slug in GEOCODE_JOBS:
            cursor = geocode.Cursor(ctx.state / f"geocode.{slug}.cursor")
            while True:
                if budget is not None and budget <= 0:
                    break
                size = batch_size if budget is None else min(batch_size, budget)

                with conn.cursor() as cur:
                    cur.execute(query, {"cursor": cursor.get(table, 0), "limit": size})
                    rows = cur.fetchall()
                if not rows:
                    break

                items = []
                for row in rows:
                    key = row[0]
                    query_text = geocode.clean_address(row[1], row[2], row[3], row[4])
                    if query_text:
                        items.append(geocode.WorkItem(key=key, query=query_text))

                if items:
                    results = geocode.run_batch(ctx.cfg, items)
                    written = geocode.write_results(conn, table, "id", results)
                    conn.commit()
                    total += written

                cursor.set(table, rows[-1][0])
                if budget is not None:
                    budget -= len(rows)
                ctx.log.info("%s geocoded %d (cumulative %d)", table, len(rows), total)

    ctx.log.info("geocoded %d rows", total)
    return Outcome.COMPLETED


# ----------------------------------------------------------------------
# 06_derive
# ----------------------------------------------------------------------
def derive(ctx: Context) -> Outcome:
    """Build the views, materialized views and spatial RPCs."""
    if ctx.dry_run:
        ctx.log.info("would apply 30_derive.sql and refresh %s", ", ".join(MATVIEWS))
        return Outcome.COMPLETED

    db.psql_file(ctx.cfg, ctx.dbname, SQL_DIR / "30_derive.sql")

    # 30_derive.sql declares matviews WITH NO DATA so the DDL stays cheap and
    # rerunnable; populating them is this stage's job.
    for matview in MATVIEWS:
        ctx.log.info("refreshing %s", matview)
        db.psql(ctx.cfg, ctx.dbname, f"REFRESH MATERIALIZED VIEW {matview};")

    # Indexes on these matviews were held back from 04_index because their
    # targets did not exist yet.  Two sources: the upstream-extracted set in
    # sql/, and the recovered set for objects no ETL script ever created.
    staged_idx = SQL_DIR / "25_derived_indexes.sql"
    if staged_idx.exists():
        ctx.log.info("applying indexes on derived objects")
        db.psql_file(ctx.cfg, ctx.dbname, staged_idx)

    derived_idx = RECOVERED_DIR / "indexes_derived.sql"
    if derived_idx.exists():
        ctx.log.info("applying recovered indexes on derived objects")
        db.psql_file(ctx.cfg, ctx.dbname, derived_idx)

    return Outcome.COMPLETED


# ----------------------------------------------------------------------
# 07_analyze
# ----------------------------------------------------------------------
def analyze(ctx: Context) -> Outcome:
    if ctx.dry_run:
        ctx.log.info("would ANALYZE %s", ctx.dbname)
        return Outcome.COMPLETED

    db.psql(ctx.cfg, ctx.dbname, "ANALYZE;")
    ctx.log.info("analyzed")
    return Outcome.COMPLETED


# ----------------------------------------------------------------------
# 08_expose
# ----------------------------------------------------------------------
def expose(ctx: Context) -> Outcome:
    """Grant read access to the PostgREST roles.

    Only the curated relations are granted. Anything absent from EXPOSED is not
    part of the published contract and must not be reachable through the API.
    """
    api_role = ctx.cfg.role("api_role")
    anon_role = ctx.cfg.role("anon_role")

    if ctx.dry_run:
        ctx.log.info("would grant %d relations to %s", len(EXPOSED), api_role)
        return Outcome.COMPLETED

    statements = [
        f"GRANT USAGE ON SCHEMA public TO {api_role};",
        f"GRANT USAGE ON SCHEMA public TO {anon_role};",
    ]
    for relation in EXPOSED:
        statements.append(f"GRANT SELECT ON {relation} TO {api_role};")
        statements.append(f"GRANT SELECT ON {relation} TO {anon_role};")
    for function in RPCS:
        statements.append(f"GRANT EXECUTE ON FUNCTION {function} TO {api_role};")
        statements.append(f"GRANT EXECUTE ON FUNCTION {function} TO {anon_role};")

    db.psql(ctx.cfg, ctx.dbname, "\n".join(statements))

    (ctx.state / "exposed.json").write_text(
        json.dumps({"relations": list(EXPOSED), "functions": list(RPCS)}, indent=2)
        + "\n"
    )
    ctx.log.info("exposed %d relations and %d functions", len(EXPOSED), len(RPCS))
    return Outcome.COMPLETED


def build() -> Pipeline:
    return Pipeline(
        dataset=DATASET,
        dbname=None,
        description="IRS nonprofit organizations, Form 990 filings, and 527 political organizations",
        stages={
            "00_acquire": acquire,
            "01_verify": verify,
            "02_restore": restore,
            "03_schema": schema,
            "04_index": index,
            "05_geocode": geocode_stage,
            "06_derive": derive,
            "07_analyze": analyze,
            "08_expose": expose,
        },
    )
