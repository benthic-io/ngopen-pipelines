"""USAspending pipeline.

Runs from scratch against an empty server: resolves the current archive from
the USAspending bulk-download API, downloads it (resumable), restores it in
two phases, applies benthic's own schema/index/geocode/derivation layers, and
exposes the curated relations to PostgREST.

Rerunning fetches a newer archive if one has been published; every stage is
recorded in bdp_meta.run_ledger so a crash resumes where it stopped.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import zipfile
from pathlib import Path

from ngopen_bdp import Outcome, Pipeline
from ngopen_bdp import db, fetch, geocode
from ngopen_bdp.stages import Context

DATASET = "usaspending"
CURSOR_KEY = "recipient_lookup"
SQL_DIR = Path(__file__).parent / "sql"
RECOVERED_DIR = Path(__file__).resolve().parents[2] / "recovered" / "usaspending"

EXTENSIONS = (
    "postgis",
    "pg_trgm",
    "dblink",
    "hstore",
    "intarray",
    "pg_prewarm",
    "pg_stat_statements",
    "postgres_fdw",
)

# Curated relations exposed through PostgREST. Everything else in the database
# is lineage, not contract. See the BDP manifest for the authoritative list.
EXPOSED = (
    "public.all_entities",
    "public.prime_awards",
    "public.subawards",
    "public.entity_awards",
    "public.recipient_geocode_index",
    "public.mv_entity_spending_summary",
    "public.mv_district_spending",
    "public.mv_covid_spending",
    "public.uei_crosswalk",
)

# Recovered materialized views declared WITH NO DATA in recovered/*.sql; the
# derive stage creates them and populates them here, mirroring irs_ng.
MATVIEWS = (
    "public.mv_entity_spending_summary",
    "public.mv_district_spending",
    "public.mv_covid_spending",
)


def _archive_name(ctx: Context) -> str:
    return f"{DATASET}-{ctx.variant}.zip"


def _dump_dir(ctx: Context) -> Path:
    return ctx.work / "dump"


# ---------------------------------------------------------------- 00_acquire


def acquire(ctx: Context) -> Outcome:
    src = ctx.cfg.source(DATASET)
    variant = ctx.variant or src.get("variant", "full")
    key = "full_download_file" if variant == "full" else "subset_download_file"

    ctx.log.info("resolving %s archive from %s", variant, src["discovery_url"])
    listing = fetch.get_json(src["discovery_url"])
    entry = listing[key]
    url, remote_name = entry["url"], entry["file_name"]
    ctx.log.info("upstream publishes %s", remote_name)

    dest = ctx.archives / _archive_name(ctx)
    ledger = fetch.ArtifactLedger(ctx.state / "artifacts.json")

    head = fetch.head(url)
    size = int(head.get("content-length", 0)) or None

    if ledger.has_current(_archive_name(ctx), url, size) and dest.exists():
        ctx.log.info("archive already current (%s), skipping download", remote_name)
        return Outcome.COMPLETED

    if ctx.dry_run:
        ctx.log.info("dry-run: would download %s (%s bytes)", url, size)
        return Outcome.COMPLETED

    fetch.download(url, dest, dataset=DATASET, expected_size=size)
    ledger.record(
        _archive_name(ctx),
        url,
        dest,
        remote_last_modified=head.get("last-modified"),
    )
    ledger.save()
    (ctx.state / "upstream_archive.txt").write_text(remote_name + "\n")
    return Outcome.COMPLETED


# ----------------------------------------------------------------- 01_verify


def verify(ctx: Context) -> Outcome:
    archive = ctx.archives / _archive_name(ctx)
    dump = _dump_dir(ctx)

    if not archive.exists():
        raise FileNotFoundError(f"{archive} missing; run 00_acquire first")

    if (dump / "toc.dat").exists() and not ctx.force:
        ctx.log.info("dump already unpacked at %s", dump)
    else:
        if ctx.dry_run:
            ctx.log.info("dry-run: would unpack %s", archive)
            return Outcome.COMPLETED
        tmp = ctx.work / "dump.unpacking"
        if tmp.exists():
            shutil.rmtree(tmp)
        tmp.mkdir(parents=True)
        ctx.log.info("unpacking %s", archive)
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(tmp)
        # The archive contains a single directory; hoist it.
        inner = [p for p in tmp.iterdir() if p.is_dir()]
        root = inner[0] if len(inner) == 1 and not (tmp / "toc.dat").exists() else tmp
        if dump.exists():
            shutil.rmtree(dump)
        root.rename(dump)
        if tmp.exists():
            shutil.rmtree(tmp, ignore_errors=True)

    toc = db.pg_restore_list(dump)
    (ctx.work / "toc.list").write_text("\n".join(toc))
    tables = sum(1 for line in toc if "TABLE DATA" in line)
    matviews = sum(1 for line in toc if "MATERIALIZED VIEW DATA" in line)
    ctx.log.info(
        "archive holds %d table-data and %d matview-data entries", tables, matviews
    )
    if tables == 0:
        raise RuntimeError(
            "archive contains no TABLE DATA entries; refusing to restore"
        )
    return Outcome.COMPLETED


# ---------------------------------------------------------------- 02_restore


def restore(ctx: Context) -> Outcome:
    dump = _dump_dir(ctx)
    toc = (ctx.work / "toc.list").read_text().splitlines()

    base_list = ctx.work / "restore.list"
    mv_list = ctx.work / "refresh.list"
    base_list.write_text(
        "\n".join(l for l in toc if "MATERIALIZED VIEW DATA" not in l) + "\n"
    )
    mv_list.write_text(
        "\n".join(l for l in toc if "MATERIALIZED VIEW DATA" in l) + "\n"
    )

    if ctx.dry_run:
        ctx.log.info("dry-run: would restore %s into %s", dump, ctx.dbname)
        return Outcome.COMPLETED

    archive_roles = ctx.cfg.get("restore.archive_roles", [])
    created = db.ensure_roles(ctx.cfg, archive_roles)
    if created:
        ctx.log.info("created archive ownership roles: %s", ", ".join(created))

    db.create_database(ctx.cfg, ctx.dbname, owner=ctx.cfg.role("restore_owner"))
    db.apply_session_tuning(ctx.cfg, ctx.dbname)

    # Phase 2 runs REFRESH MATERIALIZED VIEW as etl_user, but the archive
    # owns public.* as root and rpt.* is owned root/etl_user without
    # granting USAGE/SELECT to etl_user. Grant so the refresh can read
    # public.agency etc. and rpt.award_search without failing after a week.
    ctx.log.info("granting etl_user SELECT/USAGE for matview refresh")
    db.psql(
        ctx.cfg,
        ctx.dbname,
        """
        GRANT USAGE ON SCHEMA public, rpt, raw, int TO etl_user;
        GRANT SELECT ON ALL TABLES IN SCHEMA public TO etl_user;
        GRANT SELECT ON ALL TABLES IN SCHEMA rpt TO etl_user;
        ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO etl_user;
        ALTER DEFAULT PRIVILEGES IN SCHEMA rpt GRANT SELECT ON TABLES TO etl_user;
        ALTER DEFAULT PRIVILEGES FOR ROLE root IN SCHEMA public GRANT SELECT ON TABLES TO etl_user;
        ALTER DEFAULT PRIVILEGES FOR ROLE root IN SCHEMA rpt GRANT SELECT ON TABLES TO etl_user;
        """,
        tuples_only=False,
    )

    # --clean --if-exists makes the stage re-entrant. pg_restore otherwise dies
    # on CREATE SCHEMA the moment a previous attempt got far enough to create
    # anything, and a crash mid-restore is exactly the case this pipeline is
    # built to survive. It drops only what the archive itself carries, so
    # bdp_meta.run_ledger -- which is not in the archive -- is left intact.
    ctx.log.info("phase 1: base tables (this is the long one)")
    db.pg_restore(
        ctx.cfg,
        ctx.dbname,
        dump,
        use_list=base_list,
        extra=("--clean", "--if-exists"),
    )

    ctx.log.info("analyzing before matview materialization")
    db.psql(ctx.cfg, ctx.dbname, "ANALYZE;", tuples_only=False)

    ctx.log.info("phase 2: materialized view data")
    db.pg_restore(ctx.cfg, ctx.dbname, dump, use_list=mv_list)
    return Outcome.COMPLETED


# ----------------------------------------------------------------- 03_schema


def schema(ctx: Context) -> Outcome:
    if ctx.dry_run:
        ctx.log.info("dry-run: would ensure extensions and geocode columns")
        return Outcome.COMPLETED

    db.ensure_extensions(ctx.cfg, ctx.dbname, EXTENSIONS)
    # cube/earthdistance/fuzzystrmatch were added by hand on the live server;
    # recovered/usaspending/extensions_recovered.sql documents that.
    db.psql_file(ctx.cfg, ctx.dbname, RECOVERED_DIR / "extensions_recovered.sql")
    db.psql_file(ctx.cfg, ctx.dbname, RECOVERED_DIR / "rpt_geocode_columns.sql")

    db.psql(
        ctx.cfg,
        ctx.dbname,
        """
        CREATE TABLE IF NOT EXISTS public.recipient_geocode_index (
            source_id      BIGINT PRIMARY KEY,
            latitude       NUMERIC(10,8),
            longitude      NUMERIC(11,8),
            geom_point     GEOMETRY(Point, 4326),
            geocode_date   TIMESTAMPTZ,
            geocode_system VARCHAR(50)
        );
        """,
        tuples_only=False,
    )

    # The live server carries a BEFORE INSERT OR UPDATE trigger that derives
    # geom_point from latitude/longitude. The pipeline computes geom_point
    # explicitly, so the trigger is redundant for pipeline writes -- but it is
    # the only guard for manual UPDATEs, and it is part of the live structure.
    db.psql_file(ctx.cfg, ctx.dbname, RECOVERED_DIR / "geom_point_trigger.sql")
    return Outcome.COMPLETED


# ------------------------------------------------------------------ 04_index


def index(ctx: Context) -> Outcome:
    path = RECOVERED_DIR / "indexes_recovered.sql"
    if ctx.dry_run:
        ctx.log.info("dry-run: would apply %s", path)
        return Outcome.COMPLETED
    ctx.log.info("applying recovered indexes (76 for this dataset)")
    db.psql_file(ctx.cfg, ctx.dbname, path)
    return Outcome.COMPLETED


# ---------------------------------------------------------------- 05_geocode

FETCH_UNGEOCODED = """
SELECT rl.id,
       rl.address_line_1, rl.city, rl.state, rl.zip5, rl.country_code
  FROM rpt.recipient_lookup rl
  LEFT JOIN public.recipient_geocode_index g ON g.source_id = rl.id
 WHERE g.source_id IS NULL
   AND rl.id > %(cursor)s
 ORDER BY rl.id
 LIMIT %(limit)s
"""


def geocode_stage(ctx: Context) -> Outcome:
    if ctx.dry_run:
        ctx.log.info("dry-run: would geocode rpt.recipient_lookup")
        return Outcome.COMPLETED

    serving = ctx.cfg.dbname(DATASET)
    already = db.scalar(
        ctx.cfg,
        ctx.dbname,
        "SELECT count(*) FROM public.recipient_geocode_index",
    )
    if (
        ctx.dbname != serving
        and db.database_exists(ctx.cfg, serving)
        and int(already or 0) == 0
    ):
        carried = geocode.preserve_index(
            ctx.cfg,
            serving,
            ctx.dbname,
            "public.recipient_geocode_index",
            "rpt.recipient_lookup",
            ("address_line_1", "city", "state", "zip5", "country_code"),
        )
        ctx.log.info(
            "carried %d exact-match geocodes from %s before fresh geocoding",
            carried,
            serving,
        )
        ctx.shared["timer"].note(carried_geocodes=carried, carried_from=serving)
    else:
        ctx.log.info(
            "skip geocode carry from %s (index already populated or no source)",
            serving,
        )

    cursor = geocode.Cursor(ctx.state / "geocode.cursor")
    batch = int(ctx.cfg.get("geocoder.batch_size", 1000))
    budget = ctx.limit
    total = 0

    with db.connect(ctx.cfg, ctx.dbname) as conn:
        while True:
            size = batch if budget is None else min(batch, budget - total)
            if size <= 0:
                break
            with conn.cursor() as cur:
                cur.execute(
                    FETCH_UNGEOCODED,
                    {"cursor": cursor.get(CURSOR_KEY), "limit": size},
                )
                rows = cur.fetchall()
            if not rows:
                break

            items = []
            for rid, street, city, state, zip5, country in rows:
                query = geocode.clean_address(street, city, state, zip5, country)
                if query:
                    items.append(geocode.WorkItem(key=rid, query=query))

            results = geocode.run_batch(ctx.cfg, items) if items else []
            geocode.write_results(
                conn,
                "public.recipient_geocode_index",
                "source_id",
                results,
                insert=True,
            )
            conn.commit()
            cursor.set(CURSOR_KEY, rows[-1][0])
            total += len(rows)
            ctx.log.info(
                "geocoded %d recipients (cursor=%s)", total, cursor.get(CURSOR_KEY)
            )

    ctx.log.info("geocode stage finished: %d rows processed", total)
    return Outcome.COMPLETED


# ----------------------------------------------------------------- 06_derive


def derive(ctx: Context) -> Outcome:
    scripts = sorted(SQL_DIR.glob("*.sql")) + [
        RECOVERED_DIR / "mv_entity_spending_summary.sql",
        RECOVERED_DIR / "mv_district_spending.sql",
        RECOVERED_DIR / "mv_covid_spending.sql",
    ]
    for path in scripts:
        if ctx.dry_run:
            ctx.log.info("dry-run: would run %s", path.name)
            continue
        ctx.log.info("building %s", path.name)
        db.psql_file(ctx.cfg, ctx.dbname, path)

    # Recovered matviews are declared WITH NO DATA so the DDL stays cheap and
    # rerunnable; populating them is this stage's job.
    for matview in MATVIEWS:
        ctx.log.info("refreshing %s", matview)
        db.psql(ctx.cfg, ctx.dbname, f"REFRESH MATERIALIZED VIEW {matview};")

    # Indexes on these matviews were held back from 04_index because their
    # targets did not exist yet.
    derived_idx = RECOVERED_DIR / "indexes_derived.sql"
    if derived_idx.exists():
        ctx.log.info("applying recovered indexes on derived objects")
        db.psql_file(ctx.cfg, ctx.dbname, derived_idx)

    return Outcome.COMPLETED


# ---------------------------------------------------------------- 07_analyze


def analyze(ctx: Context) -> Outcome:
    if ctx.dry_run:
        ctx.log.info("dry-run: would ANALYZE")
        return Outcome.COMPLETED
    ctx.log.info("analyzing (planner has no stats until this runs)")
    db.psql(ctx.cfg, ctx.dbname, "ANALYZE;", tuples_only=False)
    return Outcome.COMPLETED


# ----------------------------------------------------------------- 08_expose


def expose(ctx: Context) -> Outcome:
    api_role = ctx.cfg.role("api_role")
    anon_role = ctx.cfg.role("anon_role")
    grants = [f"GRANT USAGE ON SCHEMA public TO {api_role}, {anon_role};"]
    for rel in EXPOSED:
        grants.append(f"GRANT SELECT ON {rel} TO {api_role}, {anon_role};")

    if ctx.dry_run:
        ctx.log.info("dry-run: would grant SELECT on %d relations", len(EXPOSED))
        return Outcome.COMPLETED

    db.psql(ctx.cfg, ctx.dbname, "\n".join(grants), tuples_only=False)
    (ctx.state / "exposed.json").write_text(json.dumps(list(EXPOSED), indent=2) + "\n")
    ctx.log.info("exposed %d relations to %s", len(EXPOSED), api_role)
    return Outcome.COMPLETED


def build() -> Pipeline:
    return Pipeline(
        dataset=DATASET,
        dbname=None,
        description="USAspending.gov bulk database archive, entities and awards",
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
