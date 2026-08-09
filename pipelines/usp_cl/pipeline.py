"""usp_cl -- United States Congress legislators, committees and offices.

Replaces the legacy ``ngopen/us_project_to_pg.py``, which dropped and recreated
the entire database on every run.  Here the load is idempotent: every insert
carries an ``ON CONFLICT`` clause, so a rerun refreshes the data in place
rather than destroying it.

Source is the community-maintained ``unitedstates/congress-legislators``
repository.  It is a git checkout rather than a downloadable archive, so
``00_acquire`` clones or fast-forwards it and records the resulting commit.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from ngopen_bdp import Outcome, Pipeline
from ngopen_bdp import db, geocode
from ngopen_bdp.stages import Context

DATASET = "usp_cl"
SQL_DIR = Path(__file__).resolve().parent / "sql"
RECOVERED_DIR = Path(__file__).resolve().parents[2] / "recovered" / "usp_cl"

EXTENSIONS = ("postgis", "pg_trgm")

CHECKOUT = "congress-legislators"

# The eight YAML documents the legacy importer consumed, in load order.
SOURCE_FILES = (
    "legislators-historical.yaml",
    "legislators-current.yaml",
    "legislators-social-media.yaml",
    "legislators-district-offices.yaml",
    "committees-historical.yaml",
    "committees-current.yaml",
    "committee-membership-current.yaml",
    "executive.yaml",
)

EXPOSED = (
    "public.legislators",
    "public.legislator_terms",
    "public.legislator_other_names",
    "public.legislator_social_media",
    "public.district_offices",
    "public.committees",
    "public.subcommittees",
    "public.committee_membership",
    "public.executives",
    "public.executive_terms",
    "public.mv_current_lawmakers",
    "public.mv_committee_power",
)

MATVIEWS = ("public.mv_current_lawmakers", "public.mv_committee_power")

BATCH = 1000

# ---------------------------------------------------------------------------
# congress numbering
# ---------------------------------------------------------------------------

# Carried verbatim from us_project_to_pg.py.  The 20th Amendment moved the
# start of a Congress from March 4 to January 3, effective 1935, so dates
# either side of that boundary are bucketed differently.
FIRST_CONGRESS_YEAR = 1789


def calculate_congress(date_str: str | None) -> str | None:
    """Map an ISO date onto its zero-padded Congress number, 001-119."""
    if not date_str:
        return None
    try:
        dt = datetime.strptime(str(date_str)[:10], "%Y-%m-%d")
    except (ValueError, TypeError):
        return None
    if dt.year < FIRST_CONGRESS_YEAR:
        return None
    congress = ((dt.year - FIRST_CONGRESS_YEAR) // 2) + 1
    if dt.year >= 1935:
        if dt.month == 1 and dt.day <= 2:
            congress -= 1
    elif dt.month < 3 or (dt.month == 3 and dt.day < 4):
        congress -= 1
    return f"{max(1, congress):03d}"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _checkout(ctx: Context) -> Path:
    return ctx.archives / CHECKOUT


def _load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _first(value: Any) -> Any:
    """YAML gives lists for some identifier fields; keep them as JSON text."""
    if isinstance(value, list):
        return json.dumps(value) if value else None
    return value


def _git(args: list[str], cwd: Path) -> str:
    proc = subprocess.run(
        ["git", *args], cwd=str(cwd), capture_output=True, text=True, check=False
    )
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout.strip()


def _executemany(conn, sql: str, rows: list[tuple]) -> int:
    if not rows:
        return 0
    from psycopg2.extras import execute_batch

    with conn.cursor() as cur:
        execute_batch(cur, sql, rows, page_size=500)
    conn.commit()
    return len(rows)


# ---------------------------------------------------------------------------
# 00_acquire
# ---------------------------------------------------------------------------


def acquire(ctx: Context) -> Outcome:
    src = ctx.cfg.source(DATASET)
    repo_url = src["repo_url"]
    dest = _checkout(ctx)

    if ctx.dry_run:
        ctx.log.info("dry-run: would sync %s -> %s", repo_url, dest)
        return Outcome.COMPLETED

    if (dest / ".git").exists():
        ctx.log.info("fast-forwarding existing checkout at %s", dest)
        _git(["fetch", "--depth", "1", "origin"], dest)
        _git(["reset", "--hard", "origin/HEAD"], dest)
    else:
        ctx.log.info("cloning %s -> %s", repo_url, dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, str(dest)],
            check=True,
        )

    commit = _git(["rev-parse", "HEAD"], dest)
    (ctx.state / "upstream_commit.txt").write_text(commit + "\n", encoding="utf-8")
    ctx.log.info("source at commit %s", commit)
    return Outcome.COMPLETED


# ---------------------------------------------------------------------------
# 01_verify
# ---------------------------------------------------------------------------


def verify(ctx: Context) -> Outcome:
    dest = _checkout(ctx)
    if ctx.dry_run:
        ctx.log.info("dry-run: would verify %d YAML documents", len(SOURCE_FILES))
        return Outcome.COMPLETED

    summary: dict[str, int] = {}
    for name in SOURCE_FILES:
        path = dest / name
        if not path.exists():
            raise RuntimeError(
                f"missing source document {name} in {dest}. "
                "Rerun 00_acquire, or check that upstream has not renamed it."
            )
        data = _load_yaml(path)
        if not data:
            raise RuntimeError(f"{name} parsed empty -- refusing to load")
        summary[name] = len(data)
        ctx.log.info("%-42s %8d records", name, len(data))

    (ctx.state / "sources.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    return Outcome.COMPLETED


# ---------------------------------------------------------------------------
# ingest -- driven by 02_restore
# ---------------------------------------------------------------------------

SQL_LEGISLATOR = """
INSERT INTO public.legislators (
    bioguide_id, thomas_id, lis_id, govtrack_id, opensecrets_id, votesmart_id,
    cspan_id, wikipedia_page, ballotpedia_page, maplight_id, house_history_id,
    icpsr_id, wikidata_id, google_entity_id, pictorial_id, fec_ids,
    bioguide_previous, first_name, middle_name, last_name, suffix, nickname,
    official_full, birthday, gender, is_current, first_term_start, last_term_end
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
)
ON CONFLICT (bioguide_id) DO UPDATE SET
    thomas_id = EXCLUDED.thomas_id,
    lis_id = EXCLUDED.lis_id,
    govtrack_id = EXCLUDED.govtrack_id,
    opensecrets_id = EXCLUDED.opensecrets_id,
    votesmart_id = EXCLUDED.votesmart_id,
    cspan_id = EXCLUDED.cspan_id,
    wikipedia_page = EXCLUDED.wikipedia_page,
    ballotpedia_page = EXCLUDED.ballotpedia_page,
    maplight_id = EXCLUDED.maplight_id,
    house_history_id = EXCLUDED.house_history_id,
    icpsr_id = EXCLUDED.icpsr_id,
    wikidata_id = EXCLUDED.wikidata_id,
    google_entity_id = EXCLUDED.google_entity_id,
    pictorial_id = EXCLUDED.pictorial_id,
    fec_ids = EXCLUDED.fec_ids,
    bioguide_previous = EXCLUDED.bioguide_previous,
    first_name = EXCLUDED.first_name,
    middle_name = EXCLUDED.middle_name,
    last_name = EXCLUDED.last_name,
    suffix = EXCLUDED.suffix,
    nickname = EXCLUDED.nickname,
    official_full = EXCLUDED.official_full,
    birthday = EXCLUDED.birthday,
    gender = EXCLUDED.gender,
    is_current = EXCLUDED.is_current,
    first_term_start = EXCLUDED.first_term_start,
    last_term_end = EXCLUDED.last_term_end
"""

SQL_TERM = """
INSERT INTO public.legislator_terms (
    bioguide_id, congress_start, congress_end, term_start, term_end, term_type,
    state, district, class, state_rank, party, url, address, phone, fax,
    contact_form, office, rss_url, how, end_type
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
)
ON CONFLICT (bioguide_id, term_start, term_type) DO NOTHING
"""

SQL_OTHER_NAME = """
INSERT INTO public.legislator_other_names (
    bioguide_id, first_name, middle_name, last_name, suffix, start_date, end_date
) VALUES (%s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (bioguide_id, first_name, last_name, start_date) DO NOTHING
"""

SQL_SOCIAL = """
INSERT INTO public.legislator_social_media (
    bioguide_id, twitter, twitter_id, facebook, facebook_id,
    youtube, youtube_id, instagram, instagram_id
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (bioguide_id) DO UPDATE SET
    twitter = EXCLUDED.twitter,
    twitter_id = EXCLUDED.twitter_id,
    facebook = EXCLUDED.facebook,
    facebook_id = EXCLUDED.facebook_id,
    youtube = EXCLUDED.youtube,
    youtube_id = EXCLUDED.youtube_id,
    instagram = EXCLUDED.instagram,
    instagram_id = EXCLUDED.instagram_id
"""

SQL_OFFICE = """
INSERT INTO public.district_offices (
    bioguide_id, office_key, address, suite, building, city, state, zip,
    latitude, longitude, phone, fax, hours, geom_point
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
    CASE WHEN %s IS NOT NULL AND %s IS NOT NULL
         THEN ST_SetSRID(ST_MakePoint(%s, %s), 4326) END
)
ON CONFLICT (bioguide_id, office_key) DO UPDATE SET
    address = EXCLUDED.address,
    suite = EXCLUDED.suite,
    building = EXCLUDED.building,
    city = EXCLUDED.city,
    state = EXCLUDED.state,
    zip = EXCLUDED.zip,
    phone = EXCLUDED.phone,
    fax = EXCLUDED.fax,
    hours = EXCLUDED.hours
"""

SQL_COMMITTEE = """
INSERT INTO public.committees (
    thomas_id, house_committee_id, senate_committee_id, committee_type, name,
    url, minority_url, address, phone, jurisdiction, rss_url, youtube_id,
    congresses, is_current
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (thomas_id) DO UPDATE SET
    house_committee_id = EXCLUDED.house_committee_id,
    senate_committee_id = EXCLUDED.senate_committee_id,
    committee_type = EXCLUDED.committee_type,
    name = EXCLUDED.name,
    url = EXCLUDED.url,
    minority_url = EXCLUDED.minority_url,
    address = EXCLUDED.address,
    phone = EXCLUDED.phone,
    jurisdiction = EXCLUDED.jurisdiction,
    rss_url = EXCLUDED.rss_url,
    youtube_id = EXCLUDED.youtube_id,
    congresses = EXCLUDED.congresses,
    is_current = EXCLUDED.is_current
"""

SQL_SUBCOMMITTEE = """
INSERT INTO public.subcommittees (
    committee_id, thomas_id, name, address, phone, congresses
) VALUES (%s, %s, %s, %s, %s, %s)
ON CONFLICT (committee_id, thomas_id) DO UPDATE SET
    name = EXCLUDED.name,
    address = EXCLUDED.address,
    phone = EXCLUDED.phone,
    congresses = EXCLUDED.congresses
"""

SQL_MEMBERSHIP = """
INSERT INTO public.committee_membership (
    committee_thomas_id, bioguide_id, legislator_name, party, rank, title
) VALUES (%s, %s, %s, %s, %s, %s)
ON CONFLICT (committee_thomas_id, bioguide_id) DO UPDATE SET
    legislator_name = EXCLUDED.legislator_name,
    party = EXCLUDED.party,
    rank = EXCLUDED.rank,
    title = EXCLUDED.title
"""

SQL_EXECUTIVE = """
INSERT INTO public.executives (
    bioguide_id, govtrack_id, icpsr_prez_id, first_name, middle_name,
    last_name, suffix, birthday, gender
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (bioguide_id) DO NOTHING
"""

SQL_EXECUTIVE_TERM = """
INSERT INTO public.executive_terms (
    bioguide_id, term_type, start_date, end_date, party, how
) VALUES (%s, %s, %s, %s, %s, %s)
ON CONFLICT (bioguide_id, start_date) DO NOTHING
"""


def _ingest_legislators(ctx: Context, conn, dest: Path) -> int:
    merged: dict[str, dict] = {}
    for name, current in (
        ("legislators-historical.yaml", False),
        ("legislators-current.yaml", True),
    ):
        for leg in _load_yaml(dest / name) or []:
            bioguide = (leg.get("id") or {}).get("bioguide")
            if not bioguide:
                continue
            leg["_is_current"] = current
            merged[bioguide] = leg

    people: list[tuple] = []
    terms: list[tuple] = []
    other: list[tuple] = []

    for bioguide, leg in merged.items():
        ids = leg.get("id") or {}
        name = leg.get("name") or {}
        bio = leg.get("bio") or {}
        leg_terms = leg.get("terms") or []
        people.append(
            (
                bioguide,
                ids.get("thomas"),
                ids.get("lis"),
                ids.get("govtrack"),
                ids.get("opensecrets"),
                ids.get("votesmart"),
                ids.get("cspan"),
                ids.get("wikipedia"),
                ids.get("ballotpedia"),
                ids.get("maplight"),
                ids.get("house_history"),
                ids.get("icpsr"),
                ids.get("wikidata"),
                ids.get("google_entity_id"),
                ids.get("pictorial"),
                _first(ids.get("fec")),
                _first(ids.get("bioguide_previous")),
                name.get("first"),
                name.get("middle"),
                name.get("last"),
                name.get("suffix"),
                name.get("nickname"),
                name.get("official_full"),
                bio.get("birthday"),
                bio.get("gender"),
                leg["_is_current"],
                leg_terms[0].get("start") if leg_terms else None,
                leg_terms[-1].get("end") if leg_terms else None,
            )
        )
        for term in leg_terms:
            terms.append(
                (
                    bioguide,
                    calculate_congress(term.get("start")),
                    calculate_congress(term.get("end")),
                    term.get("start"),
                    term.get("end"),
                    term.get("type"),
                    term.get("state"),
                    str(term["district"]) if term.get("district") is not None else None,
                    str(term["class"]) if term.get("class") is not None else None,
                    term.get("state_rank"),
                    term.get("party"),
                    term.get("url"),
                    term.get("address"),
                    term.get("phone"),
                    term.get("fax"),
                    term.get("contact_form"),
                    term.get("office"),
                    term.get("rss_url"),
                    term.get("how"),
                    term.get("end-type"),
                )
            )
        for alt in leg.get("other_names") or []:
            other.append(
                (
                    bioguide,
                    alt.get("first"),
                    alt.get("middle"),
                    alt.get("last"),
                    alt.get("suffix"),
                    alt.get("start"),
                    alt.get("end"),
                )
            )

    total = _executemany(conn, SQL_LEGISLATOR, people)
    total += _executemany(conn, SQL_TERM, terms)
    total += _executemany(conn, SQL_OTHER_NAME, other)
    ctx.log.info(
        "legislators %d, terms %d, other names %d", len(people), len(terms), len(other)
    )
    return total


def _ingest_social(ctx: Context, conn, dest: Path) -> int:
    rows = []
    for record in _load_yaml(dest / "legislators-social-media.yaml") or []:
        bioguide = (record.get("id") or {}).get("bioguide")
        social = record.get("social") or {}
        if not bioguide:
            continue
        rows.append(
            (
                bioguide,
                social.get("twitter"),
                social.get("twitter_id"),
                social.get("facebook"),
                social.get("facebook_id"),
                social.get("youtube"),
                social.get("youtube_id"),
                social.get("instagram"),
                social.get("instagram_id"),
            )
        )
    ctx.log.info("social media accounts %d", len(rows))
    return _executemany(conn, SQL_SOCIAL, rows)


def _ingest_offices(ctx: Context, conn, dest: Path) -> int:
    rows = []
    for record in _load_yaml(dest / "legislators-district-offices.yaml") or []:
        bioguide = (record.get("id") or {}).get("bioguide")
        if not bioguide:
            continue
        for office in record.get("offices") or []:
            lat = office.get("latitude")
            lon = office.get("longitude")
            rows.append(
                (
                    bioguide,
                    office.get("id"),
                    office.get("address"),
                    office.get("suite"),
                    office.get("building"),
                    office.get("city"),
                    office.get("state"),
                    office.get("zip"),
                    lat,
                    lon,
                    office.get("phone"),
                    office.get("fax"),
                    office.get("hours"),
                    lat,
                    lon,
                    lon,
                    lat,
                )
            )
    ctx.log.info("district offices %d", len(rows))
    return _executemany(conn, SQL_OFFICE, rows)


def _ingest_committees(ctx: Context, conn, dest: Path) -> int:
    merged: dict[str, dict] = {}
    for name, current in (
        ("committees-historical.yaml", False),
        ("committees-current.yaml", True),
    ):
        for comm in _load_yaml(dest / name) or []:
            thomas = comm.get("thomas_id")
            if not thomas:
                continue
            comm["_is_current"] = current
            merged[thomas] = comm

    rows = [
        (
            thomas,
            comm.get("house_committee_id"),
            comm.get("senate_committee_id"),
            comm.get("type"),
            comm.get("name"),
            comm.get("url"),
            comm.get("minority_url"),
            comm.get("address"),
            comm.get("phone"),
            comm.get("jurisdiction"),
            comm.get("rss_url"),
            comm.get("youtube_id"),
            _first(comm.get("congresses")),
            comm["_is_current"],
        )
        for thomas, comm in merged.items()
    ]
    total = _executemany(conn, SQL_COMMITTEE, rows)

    # Subcommittees reference the surrogate committee_id, so read it back.
    with conn.cursor() as cur:
        cur.execute("SELECT committee_id, thomas_id FROM public.committees")
        id_map = {thomas: cid for cid, thomas in cur.fetchall()}

    subs = []
    for thomas, comm in merged.items():
        parent = id_map.get(thomas)
        if parent is None:
            continue
        for sub in comm.get("subcommittees") or []:
            subs.append(
                (
                    parent,
                    sub.get("thomas_id"),
                    sub.get("name"),
                    sub.get("address"),
                    sub.get("phone"),
                    _first(sub.get("congresses")),
                )
            )
    total += _executemany(conn, SQL_SUBCOMMITTEE, subs)
    ctx.log.info("committees %d, subcommittees %d", len(rows), len(subs))
    return total


def _ingest_membership(ctx: Context, conn, dest: Path) -> int:
    data = _load_yaml(dest / "committee-membership-current.yaml") or {}
    rows = []
    for thomas, members in data.items():
        for member in members or []:
            rows.append(
                (
                    thomas,
                    member.get("bioguide"),
                    member.get("name"),
                    member.get("party"),
                    member.get("rank"),
                    member.get("title"),
                )
            )
    ctx.log.info("committee memberships %d", len(rows))
    return _executemany(conn, SQL_MEMBERSHIP, rows)


def _ingest_executives(ctx: Context, conn, dest: Path) -> int:
    people = []
    terms = []
    for record in _load_yaml(dest / "executive.yaml") or []:
        ids = record.get("id") or {}
        name = record.get("name") or {}
        bio = record.get("bio") or {}
        bioguide = ids.get("bioguide")
        if not bioguide:
            continue
        people.append(
            (
                bioguide,
                ids.get("govtrack"),
                ids.get("icpsr_prez"),
                name.get("first"),
                name.get("middle"),
                name.get("last"),
                name.get("suffix"),
                bio.get("birthday"),
                bio.get("gender"),
            )
        )
        for term in record.get("terms") or []:
            terms.append(
                (
                    bioguide,
                    term.get("type"),
                    term.get("start"),
                    term.get("end"),
                    term.get("party"),
                    term.get("how"),
                )
            )
    total = _executemany(conn, SQL_EXECUTIVE, people)
    total += _executemany(conn, SQL_EXECUTIVE_TERM, terms)
    ctx.log.info("executives %d, executive terms %d", len(people), len(terms))
    return total


def ingest(ctx: Context) -> int:
    dest = _checkout(ctx)
    total = 0
    with db.connect(ctx.cfg, ctx.dbname) as conn:
        total += _ingest_legislators(ctx, conn, dest)
        total += _ingest_social(ctx, conn, dest)
        total += _ingest_offices(ctx, conn, dest)
        total += _ingest_committees(ctx, conn, dest)
        total += _ingest_membership(ctx, conn, dest)
        total += _ingest_executives(ctx, conn, dest)
    ctx.log.info("ingested %d rows total", total)
    return total


# ---------------------------------------------------------------------------
# 02_restore
# ---------------------------------------------------------------------------


def restore(ctx: Context) -> Outcome:
    """Materialise the base tables from the YAML checkout.

    The upstream project ships no database archive, so "restore" here means
    create, define, load.  Unlike the legacy importer this never drops the
    database; every statement upserts.
    """
    if ctx.dry_run:
        ctx.log.info("dry-run: would create %s and load the YAML corpus", ctx.dbname)
        return Outcome.COMPLETED

    db.create_database(ctx.cfg, ctx.dbname, owner=ctx.cfg.role("restore_owner"))
    db.ensure_extensions(ctx.cfg, ctx.dbname, EXTENSIONS)
    db.psql_file(ctx.cfg, ctx.dbname, SQL_DIR / "10_schema.sql")
    db.psql_file(ctx.cfg, ctx.dbname, SQL_DIR / "15_keys.sql")
    db.psql_file(ctx.cfg, ctx.dbname, SQL_DIR / "16_natural_keys.sql")
    ingest(ctx)
    return Outcome.COMPLETED


# ---------------------------------------------------------------------------
# 03_schema
# ---------------------------------------------------------------------------


def schema(ctx: Context) -> Outcome:
    """Geocoding columns on district_offices.

    Upstream already supplies latitude/longitude for most offices; this only
    guarantees the uniform BDP geocoding contract is present so 05_geocode can
    fill the gaps and record provenance.
    """
    if ctx.dry_run:
        ctx.log.info("dry-run: would ensure geocoding columns")
        return Outcome.COMPLETED
    db.psql(
        ctx.cfg,
        ctx.dbname,
        geocode.geocode_columns_ddl("public.district_offices"),
        tuples_only=False,
    )
    ctx.log.info("geocoding columns ensured")
    return Outcome.COMPLETED


# ---------------------------------------------------------------------------
# 04_index
# ---------------------------------------------------------------------------


def index(ctx: Context) -> Outcome:
    if ctx.dry_run:
        ctx.log.info("dry-run: would apply constraints and indexes")
        return Outcome.COMPLETED
    db.psql_file(ctx.cfg, ctx.dbname, SQL_DIR / "20_constraints.sql")
    recovered = RECOVERED_DIR / "indexes_recovered.sql"
    if recovered.exists():
        db.psql_file(ctx.cfg, ctx.dbname, recovered)
    ctx.log.info("constraints and indexes applied")
    return Outcome.COMPLETED


# ---------------------------------------------------------------------------
# 05_geocode
# ---------------------------------------------------------------------------

FETCH_UNGEOCODED = """
SELECT office_id, address, city, state, zip
FROM public.district_offices
WHERE latitude IS NULL
  AND geocode_system IS NULL
  AND address IS NOT NULL
  AND office_id > %(cursor)s
ORDER BY office_id
LIMIT %(limit)s
"""


def geocode_stage(ctx: Context) -> Outcome:
    if ctx.dry_run:
        ctx.log.info("dry-run: would geocode district offices missing coordinates")
        return Outcome.COMPLETED

    cursor = geocode.Cursor(ctx.state / "geocode.cursor")
    batch = int(ctx.cfg.get("geocoder.batch_size", 1000))
    budget = ctx.limit
    done = 0

    with db.connect(ctx.cfg, ctx.dbname) as conn:
        while True:
            size = batch if budget is None else min(batch, budget - done)
            if size <= 0:
                break
            with conn.cursor() as cur:
                cur.execute(FETCH_UNGEOCODED, {"cursor": cursor.get(), "limit": size})
                rows = cur.fetchall()
            if not rows:
                break

            items = []
            for office_id, address, city, state, postal in rows:
                query = geocode.clean_address(address, city, state, postal, None)
                if query:
                    items.append(geocode.WorkItem(key=office_id, query=query))

            if items:
                results = geocode.run_batch(ctx.cfg, items)
                geocode.write_results(
                    conn, "public.district_offices", "office_id", results
                )
                conn.commit()

            cursor.set(rows[-1][0])
            done += len(rows)
            ctx.log.info("geocoded %d offices", done)

    ctx.log.info("geocoding complete, %d offices processed", done)
    return Outcome.COMPLETED


# ---------------------------------------------------------------------------
# 06_derive
# ---------------------------------------------------------------------------


def derive(ctx: Context) -> Outcome:
    if ctx.dry_run:
        ctx.log.info("dry-run: would build and refresh %d matviews", len(MATVIEWS))
        return Outcome.COMPLETED
    db.psql_file(ctx.cfg, ctx.dbname, SQL_DIR / "30_derive.sql")
    for view in MATVIEWS:
        ctx.log.info("refreshing %s", view)
        db.psql(
            ctx.cfg, ctx.dbname, f"REFRESH MATERIALIZED VIEW {view};", tuples_only=False
        )
    return Outcome.COMPLETED


# ---------------------------------------------------------------------------
# 07_analyze
# ---------------------------------------------------------------------------


def analyze(ctx: Context) -> Outcome:
    if ctx.dry_run:
        ctx.log.info("dry-run: would ANALYZE")
        return Outcome.COMPLETED
    db.psql(ctx.cfg, ctx.dbname, "ANALYZE;", tuples_only=False)
    ctx.log.info("statistics updated")
    return Outcome.COMPLETED


# ---------------------------------------------------------------------------
# 08_expose
# ---------------------------------------------------------------------------


def expose(ctx: Context) -> Outcome:
    api_role = ctx.cfg.role("api_role")
    anon_role = ctx.cfg.role("anon_role")
    statements = [f"GRANT USAGE ON SCHEMA public TO {api_role}, {anon_role};"]
    statements += [
        f"GRANT SELECT ON {rel} TO {api_role}, {anon_role};" for rel in EXPOSED
    ]

    if ctx.dry_run:
        ctx.log.info("dry-run: would grant SELECT on %d relations", len(EXPOSED))
        return Outcome.COMPLETED

    db.psql(ctx.cfg, ctx.dbname, "\n".join(statements), tuples_only=False)
    (ctx.state / "exposed.json").write_text(
        json.dumps(sorted(EXPOSED), indent=2) + "\n", encoding="utf-8"
    )
    ctx.log.info("exposed %d relations to %s", len(EXPOSED), api_role)
    return Outcome.COMPLETED


def build() -> Pipeline:
    return Pipeline(
        dataset=DATASET,
        dbname=None,
        description="US Congress legislators, committees, and district offices",
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
