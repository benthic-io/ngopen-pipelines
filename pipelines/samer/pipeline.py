"""SAM.gov Entity Registration pipeline.

Replaces the legacy ``gov_to_pg.py`` + ``sam_pipeline.py`` + ``geocode_sam.py``
trio with a single staged, resumable pipeline.

Source data are the SAM.gov monthly public extracts: pipe-delimited ``.dat``
files with 142 positional fields. They are downloadable through the SAM.gov
Entity Management API when ``SAM_API_KEY`` is present in the environment; if it
is not, the stage fails with the exact filename and destination directory the
operator needs to place by hand.
"""

from __future__ import annotations

import csv
import glob
import io
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from ngopen_bdp import Outcome, Pipeline
from ngopen_bdp import db, geocode
from ngopen_bdp.stages import Context

DATASET = "samer"
CURSOR_KEY = "sam_registrations"
SQL_DIR = Path(__file__).resolve().parent / "sql"
RECOVERED_DIR = Path(__file__).resolve().parents[2] / "recovered" / "samer"

EXTENSIONS = ("postgis", "pg_trgm")

EXPOSED = ("public.sam_registrations", "public.mv_contractor_registry")

# The 142-field monthly extract. Only the fields the schema actually stores are
# mapped; the positional indices are the contract with SAM.gov's layout and are
# carried over verbatim from gov_to_pg.py.
FIELD_MAP = {
    "uei": 0,
    "entity_id": 1,
    "duns": 2,
    "legal_business_name": 12,
    "dba_name": 13,
    "physical_address_line1": 14,
    "physical_city": 16,
    "physical_state": 17,
    "physical_zip": 18,
    "physical_country": 20,
    "mailing_address_line1": 21,
    "mailing_city": 23,
    "mailing_state": 24,
    "mailing_zip": 25,
    "mailing_country": 27,
    "registration_expiration": 8,
    "last_update": 9,
    "business_start_date": 10,
    "corporate_url": 30,
    "primary_naics": 31,
    "naics_codes": 32,
    "psc_codes": 33,
    "entity_structure": 34,
    "state_of_incorporation": 35,
    "country_of_incorporation": 36,
    "registration_status": 4,
}

INSERT_SQL = """
INSERT INTO public.sam_registrations (
    uei, entity_id, duns, legal_business_name, dba_name,
    physical_address_line1, physical_city, physical_state, physical_zip,
    physical_country, mailing_address_line1, mailing_city, mailing_state,
    mailing_zip, mailing_country, registration_expiration, last_update,
    business_start_date, corporate_url, primary_naics, naics_codes,
    psc_codes, entity_structure, state_of_incorporation,
    country_of_incorporation, registration_status, source_file, is_current
) VALUES (
    %(uei)s, %(entity_id)s, %(duns)s, %(legal_business_name)s, %(dba_name)s,
    %(physical_address_line1)s, %(physical_city)s, %(physical_state)s,
    %(physical_zip)s, %(physical_country)s, %(mailing_address_line1)s,
    %(mailing_city)s, %(mailing_state)s, %(mailing_zip)s,
    %(mailing_country)s, %(registration_expiration)s, %(last_update)s,
    %(business_start_date)s, %(corporate_url)s, %(primary_naics)s,
    %(naics_codes)s, %(psc_codes)s, %(entity_structure)s,
    %(state_of_incorporation)s, %(country_of_incorporation)s,
    %(registration_status)s, %(source_file)s, TRUE
)
ON CONFLICT (uei, source_file) DO UPDATE SET
    legal_business_name = EXCLUDED.legal_business_name,
    dba_name = EXCLUDED.dba_name,
    physical_address_line1 = EXCLUDED.physical_address_line1,
    physical_city = EXCLUDED.physical_city,
    physical_state = EXCLUDED.physical_state,
    physical_zip = EXCLUDED.physical_zip,
    registration_expiration = EXCLUDED.registration_expiration,
    last_update = EXCLUDED.last_update,
    registration_status = EXCLUDED.registration_status
"""

# Carry a previous geocode forward when the address has not moved, so a new
# monthly snapshot does not force a full re-geocode of 850k rows.
COPY_FORWARD_SQL = """
UPDATE public.sam_registrations AS new
SET latitude = old.latitude,
    longitude = old.longitude,
    geom_point = old.geom_point,
    geocode_date = old.geocode_date,
    geocode_system = old.geocode_system
FROM public.sam_registrations AS old
WHERE new.uei = old.uei
  AND new.source_file <> old.source_file
  AND new.latitude IS NULL
  AND old.latitude IS NOT NULL
  AND COALESCE(new.physical_address_line1, '') = COALESCE(old.physical_address_line1, '')
  AND COALESCE(new.physical_zip, '') = COALESCE(old.physical_zip, '')
"""

FETCH_UNGEOCODED = """
SELECT id, physical_address_line1, physical_city, physical_state,
       physical_zip, physical_country
FROM public.sam_registrations
WHERE latitude IS NULL
  AND geocode_system IS NULL
  AND is_current
  AND id > %(cursor)s
ORDER BY id
LIMIT %(limit)s
"""


def _extracts(ctx: Context) -> list[Path]:
    """Monthly extracts on disk, newest last."""
    found: list[Path] = []
    for pattern in ("SAM*.dat", "SAM*.DAT", "SAM*.csv"):
        found.extend(Path(p) for p in glob.glob(str(ctx.archives / pattern)))
    return sorted(set(found))


# ---------------------------------------------------------------------------
# 00_acquire
# ---------------------------------------------------------------------------


def acquire(ctx: Context) -> Outcome:
    src = ctx.cfg.source(DATASET)
    existing = _extracts(ctx)

    if existing and not ctx.force:
        ctx.log.info(
            "%d monthly extract(s) already present, newest %s",
            len(existing),
            existing[-1].name,
        )
        return Outcome.COMPLETED

    api_key = ctx.cfg.secret("SAM_API_KEY")
    if not api_key:
        raise RuntimeError(
            "No SAM.gov extract found in %s and SAM_API_KEY is not set.\n"
            "Either export SAM_API_KEY (sam.gov -> Account Details -> Public "
            "API Key) or download the monthly extract by hand from\n"
            "  %s\n"
            "and place the SAM_PUBLIC_MONTHLY_V2_YYYYMMDD.dat file in\n"
            "  %s"
            % (ctx.archives, src.get("public_page", "https://sam.gov"), ctx.archives)
        )

    if ctx.dry_run:
        ctx.log.info("[dry-run] would request a SAM.gov extract via the API")
        return Outcome.COMPLETED

    path = _download_via_api(ctx, src["api_base"], api_key)
    ctx.log.info("acquired %s (%.1f MB)", path.name, path.stat().st_size / 1e6)
    return Outcome.COMPLETED


def _download_via_api(ctx: Context, api_base: str, api_key: str) -> Path:
    """Async extract request -> poll -> download, per SAM.gov API v4."""
    import time
    from urllib.parse import urlencode

    params = urlencode(
        {
            "api_key": api_key,
            "samRegistered": "Yes",
            "format": "csv",
            "emailId": "",
            "includeSections": "All",
        }
    )
    req = Request(f"{api_base}?{params}", headers={"X-Api-Key": api_key})
    with urlopen(req, timeout=120) as resp:
        payload = json.loads(resp.read())

    token = payload.get("token") or payload.get("requestToken")
    if not token:
        raise RuntimeError(f"SAM.gov did not return an extract token: {payload}")

    ctx.log.info("extract requested, token=%s; polling", token)
    deadline = time.time() + 3600
    while time.time() < deadline:
        time.sleep(30)
        try:
            poll = Request(
                f"{api_base}/download?api_key={api_key}&token={token}",
                headers={"X-Api-Key": api_key},
            )
            with urlopen(poll, timeout=300) as resp:
                blob = resp.read()
            break
        except HTTPError as exc:
            if exc.code in (202, 404):
                continue
            raise
    else:
        raise RuntimeError("SAM.gov extract did not become ready within one hour")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    if blob[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(blob)) as zf:
            name = zf.namelist()[0]
            dest = ctx.archives / f"SAM_API_{stamp}{Path(name).suffix}"
            dest.write_bytes(zf.read(name))
    else:
        dest = ctx.archives / f"SAM_API_{stamp}.csv"
        dest.write_bytes(blob)
    return dest


# ---------------------------------------------------------------------------
# 01_verify
# ---------------------------------------------------------------------------


def verify(ctx: Context) -> Outcome:
    files = _extracts(ctx)
    if not files:
        raise RuntimeError(f"no SAM extract found in {ctx.archives}")

    manifest = []
    for path in files:
        with path.open("r", encoding="utf-8", errors="replace") as fh:
            first = fh.readline()
        fields = first.count("|") + 1 if "|" in first else 0
        if path.suffix.lower() == ".dat" and fields < 100:
            raise RuntimeError(
                f"{path.name} has {fields} pipe-delimited fields, expected ~142; "
                "the SAM.gov layout may have changed"
            )
        manifest.append(
            {"file": path.name, "bytes": path.stat().st_size, "fields": fields}
        )
        ctx.log.info(
            "%s: %d fields, %.1f MB", path.name, fields, path.stat().st_size / 1e6
        )

    (ctx.state / "extracts.json").write_text(json.dumps(manifest, indent=2))
    return Outcome.COMPLETED


# ---------------------------------------------------------------------------
# 02_restore
#
# SAM ships flat files rather than a pg_dump archive, so "restore" here means
# materialising the base tables from the acquired extracts: create the
# database, install extensions, apply the table DDL, then bulk load. Indexes
# deliberately come later in 04_index -- loading into an unindexed table is
# substantially faster and the end state is identical.
# ---------------------------------------------------------------------------


def restore(ctx: Context) -> Outcome:
    if ctx.dry_run:
        ctx.log.info(
            "[dry-run] would create %s, apply schema, load extracts", ctx.dbname
        )
        return Outcome.COMPLETED
    db.create_database(ctx.cfg, ctx.dbname, owner=ctx.cfg.role("restore_owner"))
    db.ensure_extensions(ctx.cfg, ctx.dbname, EXTENSIONS)
    db.psql_file(ctx.cfg, ctx.dbname, SQL_DIR / "10_schema.sql")
    db.psql_file(ctx.cfg, ctx.dbname, SQL_DIR / "15_keys.sql")
    return ingest(ctx)


# ---------------------------------------------------------------------------
# 03_schema -- geocoding columns, added after load so the DDL stays cheap
# ---------------------------------------------------------------------------


def schema(ctx: Context) -> Outcome:
    if ctx.dry_run:
        ctx.log.info("[dry-run] would add geocoding columns")
        return Outcome.COMPLETED
    db.psql(
        ctx.cfg, ctx.dbname, geocode.geocode_columns_ddl("public.sam_registrations")
    )
    ctx.log.info("geocoding columns ensured")
    return Outcome.COMPLETED


# ---------------------------------------------------------------------------
# 04_index
# ---------------------------------------------------------------------------


def index(ctx: Context) -> Outcome:
    if ctx.dry_run:
        return Outcome.COMPLETED
    db.psql_file(ctx.cfg, ctx.dbname, SQL_DIR / "20_constraints.sql")
    recovered = RECOVERED_DIR / "indexes_recovered.sql"
    if recovered.exists():
        db.psql_file(ctx.cfg, ctx.dbname, recovered)
    ctx.log.info("constraints and indexes applied")
    return Outcome.COMPLETED


# ---------------------------------------------------------------------------
# bulk load, driven by 02_restore
# ---------------------------------------------------------------------------


def _load_file(ctx: Context, path: Path) -> int:
    """Stream one extract into sam_registrations. Idempotent per source_file."""
    import psycopg2.extras

    delimiter = "|" if path.suffix.lower() == ".dat" else ","
    inserted = 0
    batch: list[dict] = []

    with db.connect(ctx.cfg, ctx.dbname) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT count(*) FROM public.sam_registrations WHERE source_file = %s",
            (path.name,),
        )
        already = cur.fetchone()[0]
        if already and not ctx.force:
            ctx.log.info("%s already imported (%d rows), skipping", path.name, already)
            return 0

        with path.open("r", encoding="utf-8", errors="replace", newline="") as fh:
            reader = csv.reader(fh, delimiter=delimiter, quoting=csv.QUOTE_NONE)
            for lineno, row in enumerate(reader, 1):
                if len(row) < 40:
                    continue
                record = {
                    key: (row[idx].strip() or None) if idx < len(row) else None
                    for key, idx in FIELD_MAP.items()
                }
                if not record["uei"]:
                    continue
                record["source_file"] = path.name
                batch.append(record)

                if len(batch) >= 1000:
                    psycopg2.extras.execute_batch(cur, INSERT_SQL, batch, page_size=500)
                    inserted += len(batch)
                    batch.clear()
                    conn.commit()
                    if inserted % 100000 == 0:
                        ctx.log.info("%s: %d rows", path.name, inserted)

            if batch:
                psycopg2.extras.execute_batch(cur, INSERT_SQL, batch, page_size=500)
                inserted += len(batch)
                conn.commit()

        cur.execute(
            "UPDATE public.sam_registrations SET is_current = (source_file = %s)",
            (path.name,),
        )
        conn.commit()

    ctx.log.info("%s: %d rows imported", path.name, inserted)
    return inserted


def ingest(ctx: Context) -> Outcome:
    files = _extracts(ctx)
    if ctx.dry_run:
        ctx.log.info("[dry-run] would import %d extract(s)", len(files))
        return Outcome.COMPLETED
    total = sum(_load_file(ctx, path) for path in files)
    ctx.log.info("ingest complete: %d rows", total)
    return Outcome.COMPLETED


# ---------------------------------------------------------------------------
# 05_geocode
# ---------------------------------------------------------------------------


def geocode_stage(ctx: Context) -> Outcome:
    if ctx.dry_run:
        ctx.log.info("[dry-run] would geocode ungeocoded registrations")
        return Outcome.COMPLETED

    with db.connect(ctx.cfg, ctx.dbname) as conn:
        cur = conn.cursor()
        cur.execute(COPY_FORWARD_SQL)
        carried = cur.rowcount
        conn.commit()
    if carried:
        ctx.log.info("carried %d geocodes forward from the previous snapshot", carried)

    cursor = geocode.Cursor(ctx.state / "geocode.cursor")
    batch_size = int(ctx.cfg.get("geocoder.batch_size", 1000))
    budget = ctx.limit
    done = 0

    while True:
        take = batch_size if budget is None else min(batch_size, budget - done)
        if take <= 0:
            break
        with db.connect(ctx.cfg, ctx.dbname) as conn:
            cur = conn.cursor()
            cur.execute(
                FETCH_UNGEOCODED,
                {"cursor": cursor.get(CURSOR_KEY), "limit": take},
            )
            rows = cur.fetchall()
            if not rows:
                break

            items = []
            for row_id, street, city, state, postal, country in rows:
                query = geocode.clean_address(street, city, state, postal, country)
                if query:
                    items.append(geocode.WorkItem(key=row_id, query=query))

            results = geocode.run_batch(ctx.cfg, items) if items else []
            if results:
                geocode.write_results(conn, "public.sam_registrations", "id", results)
            conn.commit()

        cursor.set(CURSOR_KEY, rows[-1][0])
        done += len(rows)
        ctx.log.info("geocoded %d / %d rows", len(results), done)

    ctx.log.info("geocode stage complete: %d rows processed", done)
    return Outcome.COMPLETED


# ---------------------------------------------------------------------------
# 06_derive
# ---------------------------------------------------------------------------


def derive(ctx: Context) -> Outcome:
    if ctx.dry_run:
        return Outcome.COMPLETED
    db.psql_file(ctx.cfg, ctx.dbname, SQL_DIR / "30_derive.sql")
    db.psql(
        ctx.cfg, ctx.dbname, "REFRESH MATERIALIZED VIEW public.mv_contractor_registry;"
    )
    ctx.log.info("materialized views refreshed")

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


# ---------------------------------------------------------------------------
# 07_analyze
# ---------------------------------------------------------------------------


def analyze(ctx: Context) -> Outcome:
    if ctx.dry_run:
        return Outcome.COMPLETED
    db.psql(ctx.cfg, ctx.dbname, "ANALYZE;")
    ctx.log.info("statistics refreshed")
    return Outcome.COMPLETED


# ---------------------------------------------------------------------------
# 08_expose
# ---------------------------------------------------------------------------


def expose(ctx: Context) -> Outcome:
    api_role = ctx.cfg.role("api_role")
    anon_role = ctx.cfg.role("anon_role")
    statements = [f"GRANT USAGE ON SCHEMA public TO {api_role}, {anon_role};"]
    for relation in EXPOSED:
        statements.append(f"GRANT SELECT ON {relation} TO {api_role}, {anon_role};")

    if ctx.dry_run:
        ctx.log.info("[dry-run] would grant SELECT on %d relations", len(EXPOSED))
        return Outcome.COMPLETED

    db.psql(ctx.cfg, ctx.dbname, "\n".join(statements))
    (ctx.state / "exposed.json").write_text(json.dumps(list(EXPOSED), indent=2))
    ctx.log.info("exposed %d relations to %s / %s", len(EXPOSED), api_role, anon_role)
    return Outcome.COMPLETED


def build() -> Pipeline:
    return Pipeline(
        dataset=DATASET,
        dbname=None,
        description="SAM.gov entity registrations, geocoded",
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
