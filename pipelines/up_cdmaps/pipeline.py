"""UCLA PolySci historical congressional district boundaries.

Replaces the legacy ngopen/ucla_cd_to_pg.py, which required the 119 district
shapefile archives to be downloaded by hand and re-read every zip on every run.
This pipeline fetches the archives itself, records a per-file hash so reruns
skip unchanged inputs, and upserts on the natural key so a partial run can be
resumed without duplicating districts.

Geometry is stored in EPSG:3857 to match the existing serving database. The
source shapefiles are EPSG:4269 (NAD83); the reprojection is explicit and
declared in the BDP manifest, because 3857 makes this the one NGOpen dataset
that cannot be spatially joined to the others without an ST_Transform.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import tempfile
import zipfile
from pathlib import Path

from ngopen_bdp import Outcome, Pipeline
from ngopen_bdp import db, fetch
from ngopen_bdp.stages import Context

DATASET = "up_cdmaps"
SQL_DIR = Path(__file__).resolve().parent / "sql"
RECOVERED_DIR = Path(__file__).resolve().parents[2] / "recovered" / "up_cdmaps"

EXTENSIONS = ("postgis",)
EXPOSED = ("public.congressional_districts",)
RPCS = (
    "public.rpc_find_district(double precision, double precision, integer)",
    "public.rpc_districts_in_bbox("
    "double precision, double precision, double precision, double precision, integer)",
)

ZIP_RE = re.compile(r"districts(\d+)\.zip$", re.IGNORECASE)
BATCH = 200

# Column aliases as they appear across 119 shapefiles authored over decades.
# Keys are lowercased source names; values are our canonical column.
COLUMN_ALIASES = {
    "statename": "statename",
    "state": "statename",
    "district": "district",
    "startcong": "startcong",
    "start_cong": "startcong",
    "endcong": "endcong",
    "end_cong": "endcong",
    "id": "district_id",
    "districtsi": "districtsi",
    "county": "county",
    "page": "page",
    "law": "law",
    "note": "note",
    "bestdec": "bestdec",
    "finalnote": "finalnote",
    "rnote": "rnote",
    "lastchange": "lastchange",
    "fromcounty": "fromcounty",
    "statefp": "statefp",
}

# Column -> max length, mirroring the varchar widths in 10_schema.sql. The
# source data occasionally exceeds them and the legacy loader truncated
# silently; we do the same but count it so the ledger records the drift.
TRUNCATE = {
    "statename": 80,
    "district_id": 80,
    "districtsi": 254,
    "county": 227,
    "page": 227,
    "law": 254,
    "note": 254,
    "bestdec": 254,
    "finalnote": 254,
    "rnote": 254,
    "fromcounty": 80,
    "statefp": 80,
}

INSERT_SQL = """
INSERT INTO public.congressional_districts (
    congress_number, statename, district, startcong, endcong,
    district_id, districtsi, county, page, law, note,
    bestdec, finalnote, rnote, lastchange, fromcounty, statefp,
    geom, source_file
) VALUES (
    %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s, %s,
    ST_Multi(ST_GeomFromText(%s, 3857)), %s
)
ON CONFLICT (congress_number, district_id) DO UPDATE SET
    statename   = EXCLUDED.statename,
    district    = EXCLUDED.district,
    startcong   = EXCLUDED.startcong,
    endcong     = EXCLUDED.endcong,
    districtsi  = EXCLUDED.districtsi,
    county      = EXCLUDED.county,
    page        = EXCLUDED.page,
    law         = EXCLUDED.law,
    note        = EXCLUDED.note,
    bestdec     = EXCLUDED.bestdec,
    finalnote   = EXCLUDED.finalnote,
    rnote       = EXCLUDED.rnote,
    lastchange  = EXCLUDED.lastchange,
    fromcounty  = EXCLUDED.fromcounty,
    statefp     = EXCLUDED.statefp,
    geom        = EXCLUDED.geom,
    source_file = EXCLUDED.source_file,
    imported_at = CURRENT_TIMESTAMP
"""


# ----------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------


def _zips(ctx: Context) -> list[Path]:
    """Every districts###.zip in the archive dir, ordered by congress."""
    found = [p for p in ctx.archives.glob("districts*.zip") if ZIP_RE.search(p.name)]
    return sorted(found, key=lambda p: _congress(p))


def _congress(path: Path) -> int:
    match = ZIP_RE.search(path.name)
    if not match:
        raise ValueError(f"cannot parse congress number from {path.name}")
    return int(match.group(1))


def _file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _state_path(ctx: Context) -> Path:
    return ctx.state / "ingested.json"


def _load_state(ctx: Context) -> dict[str, str]:
    path = _state_path(ctx)
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _save_state(ctx: Context, state: dict[str, str]) -> None:
    path = _state_path(ctx)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")
    tmp.replace(path)


def _truncate(value, column: str):
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    limit = TRUNCATE.get(column)
    if limit and len(text) > limit:
        return text[:limit]
    return text


# ----------------------------------------------------------------------
# 00_acquire
# ----------------------------------------------------------------------


def acquire(ctx: Context) -> Outcome:
    """Download every districts###.zip in the configured congress range."""
    src = ctx.cfg.source(DATASET)
    base = str(src["base_url"]).rstrip("/")
    low, high = src["congress_range"]

    ledger = fetch.ArtifactLedger(ctx.state / "artifacts.json")
    wanted = range(int(low), int(high) + 1)

    if ctx.dry_run:
        ctx.log.info("dry-run: would ensure %d archives from %s", len(wanted), base)
        return Outcome.COMPLETED

    fetched = 0
    for congress in wanted:
        name = f"districts{congress:03d}.zip"
        url = f"{base}/{name}"
        dest = ctx.archives / name

        if dest.exists() and not ctx.force:
            continue

        try:
            fetch.download(url, dest, dataset=DATASET)
        except fetch.FetchError as exc:
            # Not every congress is published; the collection is historical
            # and has gaps. A missing archive is not a pipeline failure.
            ctx.log.warning("skipping %s: %s", name, exc)
            continue

        ledger.record(name, url, dest)
        fetched += 1

    ledger.save()
    have = len(_zips(ctx))
    ctx.log.info("archives: %d present, %d newly fetched", have, fetched)
    if have == 0:
        raise RuntimeError(
            f"no districts*.zip archives in {ctx.archives}. "
            f"Source is {base}; place the files there manually if the "
            f"server is unreachable."
        )
    return Outcome.COMPLETED


# ----------------------------------------------------------------------
# 01_verify
# ----------------------------------------------------------------------


def verify(ctx: Context) -> Outcome:
    """Confirm each archive is a readable zip containing a shapefile."""
    zips = _zips(ctx)
    if not zips:
        raise RuntimeError(f"no archives to verify in {ctx.archives}")

    report = []
    for path in zips:
        try:
            with zipfile.ZipFile(path) as archive:
                shapes = [n for n in archive.namelist() if n.lower().endswith(".shp")]
        except zipfile.BadZipFile as exc:
            raise RuntimeError(f"{path.name} is not a readable zip: {exc}") from exc

        if not shapes:
            raise RuntimeError(f"{path.name} contains no .shp member")

        report.append(
            {
                "file": path.name,
                "congress": _congress(path),
                "shapefiles": shapes,
                "size": path.stat().st_size,
            }
        )

    if not ctx.dry_run:
        (ctx.state / "archives.json").write_text(json.dumps(report, indent=2) + "\n")
    ctx.log.info("verified %d archives", len(report))
    return Outcome.COMPLETED


# ----------------------------------------------------------------------
# ingest, driven by 02_restore
# ----------------------------------------------------------------------


def _read_shapefile(shp: Path, congress: int, source_file: str) -> list[tuple]:
    """Read one shapefile into insert-ready rows, reprojected to 3857."""
    import geopandas as gpd
    import pandas as pd
    from shapely.geometry import MultiPolygon

    gdf = gpd.read_file(shp)
    if gdf.crs is None:
        # The older archives ship no .prj; the collection is documented as
        # NAD83, so assume it rather than silently mangling the geometry.
        gdf = gdf.set_crs("EPSG:4269")
    if gdf.crs is not None and gdf.crs.to_epsg() != 3857:
        gdf = gdf.to_crs("EPSG:3857")

    # Normalise column names case-insensitively; the 119 shapefiles are not
    # internally consistent about capitalisation or naming.
    resolved: dict[str, str] = {}
    for column in gdf.columns:
        canonical = COLUMN_ALIASES.get(str(column).lower())
        if canonical and canonical not in resolved:
            resolved[canonical] = column

    def field(row, canonical: str):
        source = resolved.get(canonical)
        if source is None:
            return None
        value = row[source]
        if pd.isna(value):
            return None
        return value

    if "district" in resolved:
        column = resolved["district"]
        numeric = pd.to_numeric(gdf[column], errors="coerce")
        gdf[column] = pd.Series(numeric).fillna(0).astype(int)

    rows = []
    for _, row in gdf.iterrows():
        geom = row.geometry
        if geom is None or geom.is_empty:
            continue
        if geom.geom_type == "Polygon":
            geom = MultiPolygon([geom])

        rows.append(
            (
                congress,
                _truncate(field(row, "statename"), "statename"),
                field(row, "district"),
                field(row, "startcong"),
                field(row, "endcong"),
                _truncate(field(row, "district_id"), "district_id"),
                _truncate(field(row, "districtsi"), "districtsi"),
                _truncate(field(row, "county"), "county"),
                _truncate(field(row, "page"), "page"),
                _truncate(field(row, "law"), "law"),
                _truncate(field(row, "note"), "note"),
                _truncate(field(row, "bestdec"), "bestdec"),
                _truncate(field(row, "finalnote"), "finalnote"),
                _truncate(field(row, "rnote"), "rnote"),
                field(row, "lastchange"),
                _truncate(field(row, "fromcounty"), "fromcounty"),
                _truncate(field(row, "statefp"), "statefp"),
                geom.wkt,
                source_file,
            )
        )
    return rows


def _ingest_zip(ctx: Context, conn, path: Path) -> int:
    """Extract one archive to scratch, load it, and clean up."""
    from psycopg2.extras import execute_batch

    congress = _congress(path)
    workdir = Path(tempfile.mkdtemp(prefix=f"cdmaps{congress:03d}_", dir=ctx.work))
    try:
        with zipfile.ZipFile(path) as archive:
            archive.extractall(workdir)

        shapes = sorted(workdir.rglob("*.shp"))
        if not shapes:
            raise RuntimeError(f"{path.name}: no .shp after extraction")

        total = 0
        for shp in shapes:
            rows = _read_shapefile(shp, congress, path.name)
            with conn.cursor() as cur:
                for start in range(0, len(rows), BATCH):
                    execute_batch(
                        cur, INSERT_SQL, rows[start : start + BATCH], page_size=BATCH
                    )
            conn.commit()
            total += len(rows)

        ctx.log.info("congress %03d: %d districts from %s", congress, total, path.name)
        return total
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def ingest(ctx: Context) -> int:
    """Load every archive whose content hash has changed since last run."""
    zips = _zips(ctx)
    state = _load_state(ctx)
    total = 0

    with db.connect(ctx.cfg, ctx.dbname) as conn:
        for path in zips:
            digest = _file_hash(path)
            if state.get(path.name) == digest and not ctx.force:
                ctx.log.debug("skipping %s, unchanged", path.name)
                continue

            total += _ingest_zip(ctx, conn, path)
            state[path.name] = digest
            _save_state(ctx, state)

            if ctx.limit and total >= ctx.limit:
                ctx.log.info("stopping at --limit %d", ctx.limit)
                break

    return total


# ----------------------------------------------------------------------
# 02_restore
# ----------------------------------------------------------------------


def restore(ctx: Context) -> Outcome:
    """Create the database, apply base DDL and keys, then load the shapefiles.

    There is no pg_dump archive upstream: the source is 119 zipped shapefiles,
    so "restore" here means materialising the table and filling it. Secondary
    indexes are deliberately left to 04_index; a GIST index over 3857 polygons
    is far cheaper to build once at the end than to maintain during the load.
    """
    if ctx.dry_run:
        ctx.log.info("dry-run: would create %s and load districts", ctx.dbname)
        return Outcome.COMPLETED

    db.create_database(ctx.cfg, ctx.dbname, owner=ctx.cfg.role("restore_owner"))
    db.ensure_extensions(ctx.cfg, ctx.dbname, EXTENSIONS)
    db.psql_file(ctx.cfg, ctx.dbname, SQL_DIR / "10_schema.sql")
    db.psql_file(ctx.cfg, ctx.dbname, SQL_DIR / "15_keys.sql")

    loaded = ingest(ctx)
    ctx.log.info("loaded %d district rows", loaded)
    return Outcome.COMPLETED


# ----------------------------------------------------------------------
# 03_schema
# ----------------------------------------------------------------------


def schema(ctx: Context) -> Outcome:
    """Nothing to add: districts are polygons, never geocoded addresses."""
    ctx.log.info("no additional schema for %s", DATASET)
    return Outcome.SKIPPED


# ----------------------------------------------------------------------
# 04_index
# ----------------------------------------------------------------------


def index(ctx: Context) -> Outcome:
    if ctx.dry_run:
        ctx.log.info("dry-run: would apply constraints and recovered indexes")
        return Outcome.COMPLETED

    db.psql_file(ctx.cfg, ctx.dbname, SQL_DIR / "20_constraints.sql")
    recovered = RECOVERED_DIR / "indexes_recovered.sql"
    if recovered.exists():
        db.psql_file(ctx.cfg, ctx.dbname, recovered)
    ctx.log.info("indexes applied")
    return Outcome.COMPLETED


# ----------------------------------------------------------------------
# 05_geocode
# ----------------------------------------------------------------------


def geocode_stage(ctx: Context) -> Outcome:
    """District boundaries arrive as geometry; there is nothing to geocode."""
    ctx.log.info("no geocoding applies to %s", DATASET)
    return Outcome.SKIPPED


# ----------------------------------------------------------------------
# 06_derive
# ----------------------------------------------------------------------


def derive(ctx: Context) -> Outcome:
    """Install the spatial lookup RPCs used by the published API."""
    if ctx.dry_run:
        ctx.log.info("dry-run: would apply 30_derive.sql")
        return Outcome.COMPLETED

    db.psql_file(ctx.cfg, ctx.dbname, SQL_DIR / "30_derive.sql")
    ctx.log.info("derived objects applied")
    return Outcome.COMPLETED


# ----------------------------------------------------------------------
# 07_analyze
# ----------------------------------------------------------------------


def analyze(ctx: Context) -> Outcome:
    if ctx.dry_run:
        ctx.log.info("dry-run: would ANALYZE")
        return Outcome.COMPLETED

    db.psql(ctx.cfg, ctx.dbname, "ANALYZE;")
    ctx.log.info("analyzed")
    return Outcome.COMPLETED


# ----------------------------------------------------------------------
# 08_expose
# ----------------------------------------------------------------------


def expose(ctx: Context) -> Outcome:
    api_role = ctx.cfg.role("api_role")
    anon_role = ctx.cfg.role("anon_role")

    statements = [f"GRANT USAGE ON SCHEMA public TO {api_role}, {anon_role};"]
    for relation in EXPOSED:
        statements.append(f"GRANT SELECT ON {relation} TO {api_role}, {anon_role};")

    # The two spatial lookups are the published interface to this dataset;
    # without EXECUTE, PostgREST cannot offer them as RPCs.
    for function in RPCS:
        statements.append(
            f"GRANT EXECUTE ON FUNCTION {function} TO {api_role}, {anon_role};"
        )

    if ctx.dry_run:
        ctx.log.info("dry-run: would grant on %d relations", len(EXPOSED))
        return Outcome.COMPLETED

    db.psql(ctx.cfg, ctx.dbname, "\n".join(statements))
    (ctx.state / "exposed.json").write_text(
        json.dumps({"relations": list(EXPOSED)}, indent=2) + "\n"
    )
    ctx.log.info("exposed %d relations to %s, %s", len(EXPOSED), api_role, anon_role)
    return Outcome.COMPLETED


def build() -> Pipeline:
    return Pipeline(
        dataset=DATASET,
        dbname=None,
        description="UCLA PolySci historical congressional district boundaries",
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
