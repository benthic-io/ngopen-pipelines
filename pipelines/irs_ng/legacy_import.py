"""Import routines carried over from the legacy ngopen/irs_ng.py monolith.

Extracted verbatim so the parsing and upsert behaviour of the live irs_ng
database is reproduced exactly. Source commit: c4dd142. Extracted: 2026-08-08.

Deliberately NOT carried over, because the BDP pipeline supersedes them:

  create_schema          -> pipelines/irs_ng/sql/10_schema.sql
  clean_address          -> ngopen_bdp.geocode.clean_address
  geocode_address_sync   -> ngopen_bdp.geocode.PhotonClient
  run_geocoding_parallel -> ngopen_bdp.geocode.run_batch
  update_geocodes        -> ngopen_bdp.geocode.write_results

Progress reporting is via callbacks rather than rich/tqdm; the pipeline owns
logging. Connections are supplied by the caller, never opened here.
"""

from __future__ import annotations

import csv
import io
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

import requests

csv.field_size_limit(sys.maxsize)

logger = logging.getLogger("ngopen.irs_ng.legacy")

try:  # progress bars are optional; the pipeline logs instead
    from tqdm import tqdm

    TQDM_AVAILABLE = True
except ImportError:  # pragma: no cover
    TQDM_AVAILABLE = False

    def tqdm(iterable=None, **kwargs):
        """No-op stand-in so the carried-over loops run unchanged."""
        return iterable if iterable is not None else []


BATCH_SIZE = 5000

NCCS_RAW_BMF_URL = (
    "https://nccsdata.s3.amazonaws.com/raw/bmf/{year}-{month:02d}-BMF.csv"
)

IRS_SOI_EXTRACT_URLS = [
    # Form 990 extracts — per-EIN financial data
    "https://www.irs.gov/pub/irs-soi/24eoextract990.zip",
    "https://www.irs.gov/pub/irs-soi/23eoextract990.zip",
    "https://www.irs.gov/pub/irs-soi/22eoextract990.zip",
    "https://www.irs.gov/pub/irs-soi/21eoextract990.zip",
    "https://www.irs.gov/pub/irs-soi/20eoextract990.zip",
    "https://www.irs.gov/pub/irs-soi/19eoextract990.zip",
    "https://www.irs.gov/pub/irs-soi/18eoextract990.zip",
    # Form 990-EZ extracts
    "https://www.irs.gov/pub/irs-soi/24eoextract990EZ.zip",
    "https://www.irs.gov/pub/irs-soi/23eoextractez.zip",
    "https://www.irs.gov/pub/irs-soi/22eoextractez.zip",
    "https://www.irs.gov/pub/irs-soi/21eoextractez.zip",
    "https://www.irs.gov/pub/irs-soi/20eoextractez.zip",
    "https://www.irs.gov/pub/irs-soi/19eoextractez.zip",
    "https://www.irs.gov/pub/irs-soi/18eoextractez.zip",
    # Form 990-PF extracts
    "https://www.irs.gov/pub/irs-soi/24eoextract990pf.zip",
    "https://www.irs.gov/pub/irs-soi/23eoextract990pf.zip",
    "https://www.irs.gov/pub/irs-soi/22eoextract990pf.zip",
    "https://www.irs.gov/pub/irs-soi/21eoextract990pf.zip",
    "https://www.irs.gov/pub/irs-soi/20eoextract990pf.zip",
]

IRS_PUB78_URL = "https://apps.irs.gov/pub/epostcard/data-download-pub78.zip"

IRS_REVOCATION_URL = "https://apps.irs.gov/pub/epostcard/data-download-revocation.zip"

IRS_FORM990N_URL = "https://apps.irs.gov/pub/epostcard/data-download-epostcard.zip"

IRS_FORM990_XML_URLS = [
    ("2026", "2026_TEOS_XML_01A.zip"),
    ("2026", "2026_TEOS_XML_02A.zip"),
    ("2025", "2025_TEOS_XML_01A.zip"),
    ("2025", "2025_TEOS_XML_02A.zip"),
    ("2025", "2025_TEOS_XML_03A.zip"),
    ("2024", "2024_TEOS_XML_01A.zip"),
    ("2024", "2024_TEOS_XML_02A.zip"),
    ("2024", "2024_TEOS_XML_03A.zip"),
    ("2024", "2024_TEOS_XML_04A.zip"),
    ("2024", "2024_TEOS_XML_05A.zip"),
    ("2024", "2024_TEOS_XML_06A.zip"),
    ("2023", "2023_TEOS_XML_01A.zip"),
    ("2023", "2023_TEOS_XML_02A.zip"),
    ("2023", "2023_TEOS_XML_03A.zip"),
    ("2023", "2023_TEOS_XML_04A.zip"),
    ("2023", "2023_TEOS_XML_05A.zip"),
    ("2023", "2023_TEOS_XML_06A.zip"),
    ("2023", "2023_TEOS_XML_07A.zip"),
    ("2023", "2023_TEOS_XML_08A.zip"),
]

NTEE_MAJOR_GROUPS = {
    "A": "Arts, Culture, and Humanities",
    "B": "Education",
    "C": "Environmental Quality, Protection, and Beautification",
    "D": "Animal-Related",
    "E": "Health",
    "F": "Mental Health and Crisis Intervention",
    "G": "Diseases, Disorders, and Disciplines",
    "H": "Medical Research",
    "I": "Crime and Legal-Related",
    "J": "Employment",
    "K": "Food, Agriculture, and Nutrition",
    "L": "Housing and Shelter",
    "M": "Public Safety",
    "N": "Recreation and Sports",
    "O": "Youth Development",
    "P": "Human Services",
    "Q": "International, Foreign Affairs, and National Security",
    "R": "Civil Rights, Social Action, and Advocacy",
    "S": "Community Improvement and Capacity Building",
    "T": "Philanthropy, Voluntarism, and Grantmaking Foundations",
    "U": "Science and Technology Research Institutes",
    "V": "Social Science Research Institutes",
    "W": "Public and Societal Benefit",
    "X": "Religion-Related",
    "Y": "Mutual and Membership Benefit",
    "Z": "Unknown, Unclassified",
}

IRS_527_URLS = [
    "https://forms.irs.gov/app/pod/dataDownload/dataAG",
    "https://forms.irs.gov/app/pod/dataDownload/dataHM",
    "https://forms.irs.gov/app/pod/dataDownload/dataNR",
]


def derive_ntee_levels(ntee_code: str) -> Tuple[str, str, str]:
    if not ntee_code:
        return "", "", ""
    first = ntee_code[0].upper() if ntee_code else ""
    level1 = NTEE_MAJOR_GROUPS.get(first, "Unknown, Unclassified")
    level2 = ntee_code[:3] if len(ntee_code) >= 3 else ntee_code
    level3 = ntee_code[:4] if len(ntee_code) >= 4 else ntee_code
    return level1, level2, level3


def build_org_addr_full(street: str, city: str, state: str, zipcode: str) -> str:
    parts = [p.strip() for p in [street, city, state, zipcode] if p and p.strip()]
    return ", ".join(parts)


def file_already_imported(conn, table: str, column: str, value: str) -> bool:
    """Check if a file has already been imported into a table."""
    try:
        with conn.cursor() as cur:
            cur.execute(f"SELECT 1 FROM {table} WHERE {column} = %s LIMIT 1", (value,))
            return cur.fetchone() is not None
    except Exception:
        return False


def load_url_config(urls_file: str = "irs_urls.json") -> dict:
    if os.path.exists(urls_file):
        with open(urls_file, "r") as f:
            return json.load(f)
    return {}


def check_directory_listing(base_url: str, pattern: str) -> List[str]:
    """Try to fetch directory listing and extract matching URLs."""
    import re as _re

    try:
        resp = requests.get(base_url, timeout=15)
        resp.raise_for_status()
        regex = _re.compile(pattern)
        links = _re.findall(r'href=["\']([^"\']+)["\']', resp.text)
        matches = []
        for link in links:
            if regex.search(link):
                if link.startswith("http"):
                    matches.append(link)
                else:
                    matches.append(base_url.rstrip("/") + "/" + link.lstrip("/"))
        return sorted(set(matches))
    except Exception:
        return []


def probe_url(url: str) -> bool:
    """HEAD request to check if URL exists."""
    try:
        resp = requests.head(url, timeout=10, allow_redirects=True)
        return resp.status_code == 200
    except Exception:
        return False


def load_discovery_cache(archives_dir: str, dataset: str) -> dict:
    cache_file = os.path.join(archives_dir, dataset, "discovered_urls.json")
    if os.path.exists(cache_file):
        with open(cache_file, "r") as f:
            return json.load(f)
    return {}


def save_discovery_cache(archives_dir: str, dataset: str, urls: List[str]):
    cache_dir = os.path.join(archives_dir, dataset)
    os.makedirs(cache_dir, exist_ok=True)
    cache_file = os.path.join(cache_dir, "discovered_urls.json")
    with open(cache_file, "w") as f:
        json.dump(
            {"last_checked": datetime.now(timezone.utc).isoformat(), "urls": urls},
            f,
            indent=2,
        )


def discover_soi_urls(
    config: dict, archives_dir: str, start_year: int = 2018, force_refresh: bool = False
) -> List[str]:
    """Discover SOI extract URLs via directory listing or probing."""
    import re as _re

    cache = {} if force_refresh else load_discovery_cache(archives_dir, "soi")
    if cache.get("urls") and not force_refresh:
        last = cache.get("last_checked", "")
        if last:
            try:
                checked = datetime.fromisoformat(last)
                if (datetime.now(timezone.utc) - checked).total_seconds() < 3600:
                    return cache["urls"]
            except Exception:
                pass

    base_url = config.get("base_url", "https://www.irs.gov/pub/irs-soi/")
    patterns = config.get("patterns", [])

    # Try directory listing first
    all_pattern = "|".join(p.replace("{yy}", r"\d{2}") for p in patterns)
    listing = check_directory_listing(base_url, all_pattern)

    if listing:
        urls = listing
    else:
        # Fallback: probe by pattern
        urls = []
        current_year_2digit = datetime.now().year % 100
        for yy in range(start_year % 100, current_year_2digit + 2):
            for pattern in patterns:
                filename = pattern.replace("{yy}", f"{yy:02d}")
                url = base_url.rstrip("/") + "/" + filename
                if probe_url(url):
                    urls.append(url)

    save_discovery_cache(archives_dir, "soi", urls)
    return urls


def discover_xml_urls(
    config: dict, archives_dir: str, start_year: int = 2018, force_refresh: bool = False
) -> List[Tuple[str, str]]:
    """Discover Form 990 XML archive URLs via directory listing or probing."""
    cache = {} if force_refresh else load_discovery_cache(archives_dir, "xml")
    if cache.get("urls") and not force_refresh:
        last = cache.get("last_checked", "")
        if last:
            try:
                checked = datetime.fromisoformat(last)
                if (datetime.now(timezone.utc) - checked).total_seconds() < 3600:
                    return [
                        tuple(u) if isinstance(u, list) else u for u in cache["urls"]
                    ]
            except Exception:
                pass

    pattern = config.get("pattern", "{yyyy}_TEOS_XML_{part}A.zip")
    max_parts = config.get("max_parts", 24)
    current_year = datetime.now().year
    results = []

    for year in range(start_year, current_year + 2):
        year_str = str(year)
        base_url = f"https://apps.irs.gov/pub/epostcard/990/xml/{year_str}/"

        # Try directory listing
        year_pattern = pattern.replace("{yyyy}", year_str).replace("{part}", r"\d+")
        listing = check_directory_listing(base_url, year_pattern)

        if listing:
            for url in listing:
                fname = url.rsplit("/", 1)[-1]
                results.append((year_str, fname))
        else:
            # Fallback: probe parts
            for part in range(1, max_parts + 1):
                fname = pattern.replace("{yyyy}", year_str).replace(
                    "{part}", f"{part:02d}"
                )
                url = base_url + fname
                if probe_url(url):
                    results.append((year_str, fname))

    save_discovery_cache(archives_dir, "xml", [list(r) for r in results])
    return results


def download_file(url: str, dest_path: str, timeout: int = 600) -> bool:
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)

    if os.path.exists(dest_path):
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                expected_size = int(resp.headers.get("Content-Length", 0))
            actual_size = os.path.getsize(dest_path)

            if expected_size > 0 and actual_size >= expected_size * 0.99:
                print(
                    f"  Already downloaded: {os.path.basename(dest_path)} ({actual_size / 1024 / 1024:.1f}MB)"
                )
                return True
            print(
                f"  Incomplete file ({actual_size / 1024 / 1024:.1f}/{expected_size / 1024 / 1024:.1f}MB), re-downloading..."
            )
        except Exception:
            pass

    try:

        def reporthook(block_num, block_size, total_size):
            if total_size > 0 and block_num % 500 == 0:
                percent = min(100, block_num * block_size * 100 // total_size)
                print(f"    {percent}%", end="\r")

        print(f"  Downloading: {os.path.basename(dest_path)}")
        urllib.request.urlretrieve(url, dest_path, reporthook)
        print(f"    Done!        ")
        return True
    except Exception as e:
        print(f"    Error: {e}")
        return False


def download_zip_extract(
    zip_path: str, dest_dir: str, extensions: Optional[List[str]] = None
) -> List[str]:
    extracted = []
    extensions = extensions or [".csv", ".txt", ".dat"]
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            for name in zf.namelist():
                if any(name.lower().endswith(ext) for ext in extensions):
                    dest = os.path.join(dest_dir, os.path.basename(name))
                    if not os.path.exists(dest):
                        zf.extract(name, dest_dir)
                        os.rename(os.path.join(dest_dir, name), dest)
                    extracted.append(dest)
    except zipfile.BadZipFile as e:
        logger.error(f"Bad zip file {zip_path}: {e}")
    except NotImplementedError as e:
        logger.warning(f"Unsupported compression in {zip_path}: {e}. Skipping.")
    return extracted


def download_bmf_files(
    archives_dir: str, start_year: int = 2023, start_month: int = 6
) -> int:
    """Download BMF files from NCCS archive."""
    bmf_dir = os.path.join(archives_dir, "bmf", "raw")
    os.makedirs(bmf_dir, exist_ok=True)

    now = datetime.now()
    count = 0

    print("\n=== Downloading BMF Files ===")
    year, month = start_year, start_month
    while (year < now.year) or (year == now.year and month <= now.month):
        url = NCCS_RAW_BMF_URL.format(year=year, month=month)
        filename = f"{year}-{month:02d}-BMF.csv"
        dest = os.path.join(bmf_dir, filename)

        if download_file(url, dest):
            count += 1

        month += 1
        if month > 12:
            month = 1
            year += 1
        time.sleep(0.2)

    return count


def download_pub78_and_revocation(archives_dir: str) -> int:
    """Download Pub78 and Revocation lists."""
    count = 0

    print("\n=== Downloading Pub78 and Revocation Data ===")

    dest_dir = os.path.join(archives_dir, "status")
    os.makedirs(dest_dir, exist_ok=True)

    pub78_zip = os.path.join(dest_dir, "pub78.zip")
    if download_file(IRS_PUB78_URL, pub78_zip):
        download_zip_extract(pub78_zip, dest_dir)
        count += 1

    rev_zip = os.path.join(dest_dir, "revocation.zip")
    if download_file(IRS_REVOCATION_URL, rev_zip):
        download_zip_extract(rev_zip, dest_dir)
        count += 1

    return count


def download_form990n(archives_dir: str) -> int:
    """Download Form 990-N data."""
    print("\n=== Downloading Form 990-N ===")

    dest_dir = os.path.join(archives_dir, "form990n")
    os.makedirs(dest_dir, exist_ok=True)

    zip_path = os.path.join(dest_dir, "form990n.zip")
    if download_file(IRS_FORM990N_URL, zip_path):
        download_zip_extract(zip_path, dest_dir)
        return 1
    return 0


def download_soi(
    archives_dir: str,
    url_config: Optional[dict] = None,
    start_year: int = 2018,
    force_refresh: bool = False,
) -> int:
    """Download IRS SOI per-EIN financial extracts (ZIPs containing CSVs)."""
    count = 0

    print("\n=== Downloading SOI Data ===")

    dest_dir = os.path.join(archives_dir, "soi", "raw")
    os.makedirs(dest_dir, exist_ok=True)

    if url_config and url_config.get("discover"):
        urls = discover_soi_urls(url_config, archives_dir, start_year, force_refresh)
        if not urls:
            print("  No SOI URLs discovered, falling back to hardcoded list")
            urls = list(IRS_SOI_EXTRACT_URLS)
    else:
        urls = list(IRS_SOI_EXTRACT_URLS)

    for url in urls:
        filename = url.split("/")[-1]
        dest = os.path.join(dest_dir, filename)
        if download_file(url, dest):
            count += 1
            extracted = download_zip_extract(
                dest,
                os.path.join(archives_dir, "soi", "csv"),
                extensions=[".csv", ".txt"],
            )
            if not extracted:
                print(f"  Corrupted zip {filename}. Re-downloading...")
                try:
                    os.remove(dest)
                except:
                    pass
                if download_file(url, dest):
                    download_zip_extract(
                        dest,
                        os.path.join(archives_dir, "soi", "csv"),
                        extensions=[".csv", ".txt"],
                    )
        time.sleep(0.3)

    return count


def download_form990_xml(
    archives_dir: str,
    years: Optional[List[int]] = None,
    url_config: Optional[dict] = None,
    start_year: int = 2018,
    force_refresh: bool = False,
) -> int:
    """Download Form 990 XML files."""
    count = 0

    print("\n=== Downloading Form 990 XML ===")

    xml_dir = os.path.join(archives_dir, "form990", "xml")
    os.makedirs(xml_dir, exist_ok=True)

    if url_config and url_config.get("discover"):
        discovered = discover_xml_urls(
            url_config, archives_dir, start_year, force_refresh
        )
        if discovered:
            url_tuples = discovered
        else:
            print("  No XML URLs discovered, falling back to hardcoded list")
            url_tuples = list(IRS_FORM990_XML_URLS)
    else:
        url_tuples = list(IRS_FORM990_XML_URLS)

    for year, filename in url_tuples:
        if years and int(year) not in years:
            continue
        url = f"https://apps.irs.gov/pub/epostcard/990/xml/{year}/{filename}"
        dest = os.path.join(xml_dir, filename)
        if download_file(url, dest):
            count += 1
        time.sleep(0.3)

    return count


def download_527(archives_dir: str) -> int:
    """Download IRS 527 political organization data."""
    count = 0
    print("\n=== Downloading 527 Political Organization Data ===")
    dest_dir = os.path.join(archives_dir, "527")
    os.makedirs(dest_dir, exist_ok=True)

    for url in IRS_527_URLS:
        suffix = url.split("/")[-1].replace("data", "")
        filename = f"527_{suffix}.zip"
        dest = os.path.join(dest_dir, filename)
        if download_file(url, dest):
            count += 1
        time.sleep(0.3)

    return count


def download_census(archives_dir: str, years=None) -> int:
    """Download census tract/county demographics from Census Bureau API."""
    if years is None:
        years = list(range(2009, 2025))

    # Variables available in all years
    base_vars = "NAME,B01001_001E,B19013_001E,B17001_002E,B02001_002E,B02001_003E,B03003_003E,B25001_001E,B25077_001E"
    # B15003_022E (bachelor's degree) only available from 2012
    full_vars = base_vars + ",B15003_022E"

    states = [f"{i:02d}" for i in range(1, 57)]
    valid_states = [s for s in states if s not in ("03", "07", "14", "43", "52")]

    count = 0
    print("\n=== Downloading Census Demographics ===")

    for year in years:
        variables = full_vars if year >= 2012 else base_vars

        for geo in ["tract", "county"]:
            dest_dir = os.path.join(archives_dir, "census", str(year))
            os.makedirs(dest_dir, exist_ok=True)

            for state_fips in valid_states:
                filename = f"{geo}_{state_fips}_{year}.csv"
                dest = os.path.join(dest_dir, filename)

                if os.path.exists(dest):
                    continue

                url = f"https://api.census.gov/data/{year}/acs/acs5"
                try:
                    resp = requests.get(
                        url,
                        params={
                            "get": variables,
                            "for": f"{geo}:*",
                            "in": f"state:{state_fips}",
                        },
                        timeout=30,
                    )
                    resp.raise_for_status()
                    data = resp.json()

                    if len(data) < 2:
                        continue

                    headers = data[0]
                    with open(dest, "w", newline="") as f:
                        writer = csv.writer(f)
                        writer.writerow(headers)
                        for row in data[1:]:
                            writer.writerow(row)

                    count += 1
                    if count % 50 == 0:
                        print(f"    Downloaded {count} files...")
                except Exception as e:
                    print(f"    Error: {year}/{geo}/{state_fips}: {e}")

                time.sleep(0.1)  # rate limit

    print(f"  Census download complete: {count} files")
    return count


def import_bmf_file(
    conn, filepath: str, release_date: Optional[str] = None, progress_callback=None
) -> Tuple[int, int]:
    """Import a BMF CSV file using COPY for speed.

    The original row-at-a-time csv.DictReader loop was orders of magnitude
    slower than COPY: reading a 400MB CSV in Python and sending 52-column
    upserts through executemany is IO-bound on both sides.  This version
    COPYs the raw CSV into a temporary staging table, then runs *one*
    INSERT ... ON CONFLICT that does every transformation in Postgres,
    eliminating the Python row loop entirely.
    """
    import io as _io

    filename = os.path.basename(filepath)

    # -- step 1: COPY raw CSV into a temporary staging table ----------
    with open(filepath, "rb") as fh:
        raw = fh.read()
    # NCCS files use either \r\n or \n; detect header once.
    header, _, body = raw.partition(b"\r\n" if b"\r\n" in raw[:2000] else b"\n")
    if body and body[0:1] == b"\n":
        body = body[1:]

    stage = f"bmf_stage_{os.getpid()}"
    with conn.cursor() as cur:
        cur.execute(
            f"CREATE UNLOGGED TABLE IF NOT EXISTS {stage} ("
            "  ein text, name text, ico text, street text, city text,"
            "  state text, zip text, group_code text, subsection text,"
            "  affiliation text, classification text, ruling text,"
            "  deductibility text, foundation text, activity text,"
            "  organization text, status text, tax_period text,"
            "  asset_cd text, income_cd text, filing_req_cd text,"
            "  pf_filing_req_cd text, acct_pd text, asset_amt text,"
            "  income_amt text, revenue_amt text, ntee_cd text, sort_name text,"
            "  region text, ryear text, id text"
            ")"
        )
        cur.copy_expert(
            f"COPY {stage} FROM STDIN WITH (FORMAT csv, HEADER false)",
            _io.BytesIO(body),
        )
        loaded = cur.rowcount
        cur.execute(f"ANALYZE {stage}")

    # -- step 2: one INSERT ... ON CONFLICT with transformation in SQL --
    SQL = f"""
        INSERT INTO bmf_organizations (
            ein, ein2, ntee_irs, ntee_nccs, nteev2,
            nccs_level_1, nccs_level_2, nccs_level_3,
            f990_total_revenue_recent, f990_total_income_recent,
            f990_total_assets_recent,
            f990_org_addr_city, f990_org_addr_state,
            f990_org_addr_zip, f990_org_addr_street,
            census_cbsa_fips, census_cbsa_name, census_block_fips,
            census_urban_area, census_state_abbr, census_county_name,
            org_addr_full, org_addr_match,
            latitude, longitude, geocoder_score, geocoder_match,
            geocode_date, geocoding_source,
            bmf_subsection_code, bmf_status_code, bmf_pf_filing_req_code,
            bmf_organization_code, bmf_income_code, bmf_group_exempt_num,
            bmf_foundation_code, bmf_filing_req_code,
            bmf_deductibility_code, bmf_classification_code,
            bmf_asset_code, bmf_affiliation_code,
            org_ruling_date, org_fiscal_year, org_ruling_year,
            org_year_first, org_year_last, org_year_count,
            org_pers_ico, org_name_sec, org_name_current,
            org_fiscal_period, source_file, is_current
        )
        SELECT
            NULLIF(regexp_replace(ein, '[^0-9]', '', 'g'), ''),
            NULL,
            NULLIF(ntee_cd, ''), NULL, NULL,
            CASE LEFT(NULLIF(ntee_cd, ''), 1)
                WHEN 'A' THEN 'Arts, Culture & Humanities'
                WHEN 'B' THEN 'Educational Institutions'
                WHEN 'C' THEN 'Environmental Quality, Protection'
                WHEN 'D' THEN 'Animal Related'
                WHEN 'E' THEN 'Health – General & Rehabilitative'
                WHEN 'F' THEN 'Mental Health, Crisis Intervention'
                WHEN 'G' THEN 'Disease, Disorders, Medical Disciplines'
                WHEN 'H' THEN 'Medical Research'
                WHEN 'I' THEN 'Crime, Legal Related'
                WHEN 'J' THEN 'Employment, Job Related'
                WHEN 'K' THEN 'Food, Agriculture, Nutrition'
                WHEN 'L' THEN 'Housing, Shelter'
                WHEN 'M' THEN 'Public Safety, Disaster Preparedness'
                WHEN 'N' THEN 'Recreation, Sports, Leisure, Athletics'
                WHEN 'O' THEN 'Youth Development'
                WHEN 'P' THEN 'Human Services – Multipurpose'
                WHEN 'Q' THEN 'International, Foreign Affairs'
                WHEN 'R' THEN 'Civil Rights, Social Action'
                WHEN 'S' THEN 'Community Improvement, Capacity Building'
                WHEN 'T' THEN 'Philanthropy, Voluntarism'
                WHEN 'U' THEN 'Science & Technology'
                WHEN 'V' THEN 'Social Science'
                WHEN 'W' THEN 'Public, Society Benefit'
                WHEN 'X' THEN 'Religion, Spiritual Development'
                WHEN 'Y' THEN 'Mutual, Membership Benefit'
                WHEN 'Z' THEN 'Unknown, Unclassified'
            END,
            LEFT(NULLIF(ntee_cd, ''), 3),
            LEFT(NULLIF(ntee_cd, ''), 4),
            NULLIF(regexp_replace(revenue_amt, '[^0-9]', '', 'g'), '')::bigint,
            NULLIF(regexp_replace(income_amt,  '[^0-9]', '', 'g'), '')::bigint,
            NULLIF(regexp_replace(asset_amt,   '[^0-9]', '', 'g'), '')::bigint,
            city, state, zip, street,
            '', '', '', '', state, '',
            NULLIF(
                TRIM(COALESCE(NULLIF(street, '') || ', ', '')
                    || NULLIF(CONCAT_WS(' ', NULLIF(city, ''),
                                            NULLIF(state, ''),
                                            NULLIF(zip, '')), '')
                ), ''
            ),
            '',
            NULL, NULL, NULL, NULL, NULL, NULL,
            subsection, status, pf_filing_req_cd, organization,
            income_cd, group_code, foundation, filing_req_cd,
            deductibility, classification, asset_cd, affiliation,
            CASE
                WHEN ruling ~ '^[0-9]{8}$' THEN to_date(ruling, 'YYYYMMDD')
                WHEN ruling ~ '^[0-9]{6}$' THEN to_date(ruling, 'YYYYMM')
                WHEN ruling ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' THEN ruling::date
            END,
            acct_pd,
            COALESCE(
                CASE WHEN ruling ~ '^[0-9]{6, 8}$' THEN LEFT(ruling, 4)
                     WHEN ruling ~ '^[0-9]{4}-' THEN LEFT(ruling, 4)
                END, ''
            ),
            '', '', NULL,
            ico, sort_name,
            COALESCE(NULLIF(name, ''), sort_name),
            tax_period,
            '{filename}',
            TRUE
        FROM {stage} s
        WHERE NULLIF(regexp_replace(s.ein, '[^0-9]', '', 'g'), '') IS NOT NULL
        ON CONFLICT (ein, org_name_current) DO UPDATE SET
            ein2 = EXCLUDED.ein2,
            ntee_irs = EXCLUDED.ntee_irs,
            nccs_level_1 = EXCLUDED.nccs_level_1,
            nccs_level_2 = EXCLUDED.nccs_level_2,
            nccs_level_3 = EXCLUDED.nccs_level_3,
            f990_total_revenue_recent = EXCLUDED.f990_total_revenue_recent,
            f990_total_income_recent = EXCLUDED.f990_total_income_recent,
            f990_total_assets_recent = EXCLUDED.f990_total_assets_recent,
            f990_org_addr_city = EXCLUDED.f990_org_addr_city,
            f990_org_addr_state = EXCLUDED.f990_org_addr_state,
            f990_org_addr_zip = EXCLUDED.f990_org_addr_zip,
            f990_org_addr_street = EXCLUDED.f990_org_addr_street,
            bmf_subsection_code = EXCLUDED.bmf_subsection_code,
            bmf_status_code = EXCLUDED.bmf_status_code,
            bmf_pf_filing_req_code = EXCLUDED.bmf_pf_filing_req_code,
            bmf_organization_code = EXCLUDED.bmf_organization_code,
            bmf_income_code = EXCLUDED.bmf_income_code,
            bmf_group_exempt_num = EXCLUDED.bmf_group_exempt_num,
            bmf_foundation_code = EXCLUDED.bmf_foundation_code,
            bmf_filing_req_code = EXCLUDED.bmf_filing_req_code,
            bmf_deductibility_code = EXCLUDED.bmf_deductibility_code,
            bmf_classification_code = EXCLUDED.bmf_classification_code,
            bmf_asset_code = EXCLUDED.bmf_asset_code,
            bmf_affiliation_code = EXCLUDED.bmf_affiliation_code,
            org_ruling_date = EXCLUDED.org_ruling_date,
            org_fiscal_year = EXCLUDED.org_fiscal_year,
            org_ruling_year = EXCLUDED.org_ruling_year,
            org_name_sec = EXCLUDED.org_name_sec,
            org_fiscal_period = EXCLUDED.org_fiscal_period,
            org_addr_full = EXCLUDED.org_addr_full,
            source_file = EXCLUDED.source_file,
            is_current = TRUE,
            latitude = CASE
                WHEN EXCLUDED.f990_org_addr_street IS DISTINCT FROM
                     bmf_organizations.f990_org_addr_street
                  OR EXCLUDED.f990_org_addr_zip IS DISTINCT FROM
                     bmf_organizations.f990_org_addr_zip
                THEN NULL ELSE bmf_organizations.latitude END,
            longitude = CASE
                WHEN EXCLUDED.f990_org_addr_street IS DISTINCT FROM
                     bmf_organizations.f990_org_addr_street
                  OR EXCLUDED.f990_org_addr_zip IS DISTINCT FROM
                     bmf_organizations.f990_org_addr_zip
                THEN NULL ELSE bmf_organizations.longitude END,
            geocoder_score = CASE
                WHEN EXCLUDED.f990_org_addr_street IS DISTINCT FROM
                     bmf_organizations.f990_org_addr_street
                  OR EXCLUDED.f990_org_addr_zip IS DISTINCT FROM
                     bmf_organizations.f990_org_addr_zip
                THEN NULL ELSE bmf_organizations.geocoder_score END,
            geocoder_match = CASE
                WHEN EXCLUDED.f990_org_addr_street IS DISTINCT FROM
                     bmf_organizations.f990_org_addr_street
                  OR EXCLUDED.f990_org_addr_zip IS DISTINCT FROM
                     bmf_organizations.f990_org_addr_zip
                THEN NULL ELSE bmf_organizations.geocoder_match END,
            geocode_date = CASE
                WHEN EXCLUDED.f990_org_addr_street IS DISTINCT FROM
                     bmf_organizations.f990_org_addr_street
                  OR EXCLUDED.f990_org_addr_zip IS DISTINCT FROM
                     bmf_organizations.f990_org_addr_zip
                THEN NULL ELSE bmf_organizations.geocode_date END,
            geocoding_source = CASE
                WHEN EXCLUDED.f990_org_addr_street IS DISTINCT FROM
                     bmf_organizations.f990_org_addr_street
                  OR EXCLUDED.f990_org_addr_zip IS DISTINCT FROM
                     bmf_organizations.f990_org_addr_zip
                THEN NULL ELSE bmf_organizations.geocoding_source END,
            org_addr_match = CASE
                WHEN EXCLUDED.f990_org_addr_street IS DISTINCT FROM
                     bmf_organizations.f990_org_addr_street
                  OR EXCLUDED.f990_org_addr_zip IS DISTINCT FROM
                     bmf_organizations.f990_org_addr_zip
                THEN NULL ELSE bmf_organizations.org_addr_match END
    """
    with conn.cursor() as cur:
        cur.execute(SQL)
        row_count = cur.rowcount
    conn.commit()

    # -- step 3: one bulk snapshot at completion ---------------------------
    inserted, updated = row_count, 0

    # -- step 4: cleanup --------------------------------------------------
    with conn.cursor() as cur:
        cur.execute(f"DROP TABLE IF EXISTS {stage}")
    conn.commit()

    if progress_callback:
        progress_callback(row_count)

    print(f"  BMF {filename}: {row_count:,} rows (loaded: {loaded:,})")
    return inserted, updated


def import_527(conn, archives_dir: str) -> int:
    """Import IRS 527 political organization data."""
    import zipfile as zf_mod

    src_dir = os.path.join(archives_dir, "527")
    if not os.path.exists(src_dir):
        print("  527 directory not found, skipping")
        return 0

    count = 0
    batch = []
    batch_size = 1000

    def parse_date(s):
        if not s or s.strip() in ("", "0"):
            return None
        try:
            return datetime.strptime(s.strip()[:10], "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return None

    for filename in sorted(os.listdir(src_dir)):
        if not filename.endswith(".zip"):
            continue

        if file_already_imported(conn, "political_orgs_527", "source_file", filename):
            print(f"  Skipping {filename} (already imported)")
            continue

        filepath = os.path.join(src_dir, filename)
        print(f"  Importing {filename}")

        try:
            with zf_mod.ZipFile(filepath, "r") as z:
                txt_files = [n for n in z.namelist() if n.endswith(".txt")]
                if not txt_files:
                    print(f"    No .txt file found in zip")
                    continue

                with z.open(txt_files[0]) as f:
                    reader = io.TextIOWrapper(f, encoding="utf-8", errors="replace")
                    row_count = 0
                    for line in reader:
                        parts = line.strip().split("|")
                        if len(parts) < 13:
                            continue

                        record_type = parts[0]

                        # Only process type '1' records (main org records from Form 8871)
                        if record_type != "1":
                            continue

                        # Type '1' layout: [0]=type, [1]=form, [6]=EIN, [7]=name, [8]=addr, [10]=city, [11]=state, [12]=zip, [39]=org_type, [41]=filing_date
                        ein = parts[6].strip() if len(parts) > 6 else ""
                        org_name = parts[7].strip() if len(parts) > 7 else ""
                        address = parts[8].strip() if len(parts) > 8 else ""
                        city = parts[10].strip() if len(parts) > 10 else ""
                        state = parts[11].strip() if len(parts) > 11 else ""
                        zip_code = parts[12].strip() if len(parts) > 12 else ""
                        org_type = parts[39].strip() if len(parts) > 39 else ""
                        filing_date_str = parts[41].strip() if len(parts) > 41 else ""
                        filing_type = parts[1].strip() if len(parts) > 1 else "8871"

                        ein = ein.replace("-", "").replace(" ", "")[:20]
                        if not ein or not ein.isdigit():
                            continue

                        org_name = org_name[:500]
                        address = address[:500]
                        city = city[:100]
                        state = state[:10]
                        zip_code = zip_code[:20]
                        filing_date = parse_date(filing_date_str)

                        batch.append(
                            (
                                ein,
                                org_name,
                                filing_type,
                                org_type,
                                address,
                                city,
                                state,
                                zip_code,
                                filing_date,
                                None,
                                None,
                                None,
                                None,  # lat, lon, geocode_date, geocoding_source
                                filename,
                            )
                        )
                        row_count += 1

                        if len(batch) >= batch_size:
                            with conn.cursor() as cur:
                                cur.executemany(
                                    """
                                    INSERT INTO political_orgs_527 (
                                        ein, org_name, filing_type, org_type,
                                        address, city, state, zip,
                                        filing_date, latitude, longitude, geocode_date, geocoding_source,
                                        source_file
                                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                    ON CONFLICT (ein, filing_type) DO UPDATE SET
                                        org_name = EXCLUDED.org_name,
                                        address = EXCLUDED.address,
                                        city = EXCLUDED.city,
                                        state = EXCLUDED.state,
                                        zip = EXCLUDED.zip,
                                        org_type = EXCLUDED.org_type,
                                        filing_date = EXCLUDED.filing_date,
                                        source_file = EXCLUDED.source_file,
                                        latitude = CASE
                                            WHEN EXCLUDED.address IS DISTINCT FROM political_orgs_527.address
                                              OR EXCLUDED.city IS DISTINCT FROM political_orgs_527.city
                                              OR EXCLUDED.state IS DISTINCT FROM political_orgs_527.state
                                              OR EXCLUDED.zip IS DISTINCT FROM political_orgs_527.zip
                                            THEN NULL ELSE political_orgs_527.latitude END,
                                        longitude = CASE
                                            WHEN EXCLUDED.address IS DISTINCT FROM political_orgs_527.address
                                              OR EXCLUDED.city IS DISTINCT FROM political_orgs_527.city
                                              OR EXCLUDED.state IS DISTINCT FROM political_orgs_527.state
                                              OR EXCLUDED.zip IS DISTINCT FROM political_orgs_527.zip
                                            THEN NULL ELSE political_orgs_527.longitude END,
                                        geocode_date = CASE
                                            WHEN EXCLUDED.address IS DISTINCT FROM political_orgs_527.address
                                              OR EXCLUDED.city IS DISTINCT FROM political_orgs_527.city
                                              OR EXCLUDED.state IS DISTINCT FROM political_orgs_527.state
                                              OR EXCLUDED.zip IS DISTINCT FROM political_orgs_527.zip
                                            THEN NULL ELSE political_orgs_527.geocode_date END,
                                        geocoding_source = CASE
                                            WHEN EXCLUDED.address IS DISTINCT FROM political_orgs_527.address
                                              OR EXCLUDED.city IS DISTINCT FROM political_orgs_527.city
                                              OR EXCLUDED.state IS DISTINCT FROM political_orgs_527.state
                                              OR EXCLUDED.zip IS DISTINCT FROM political_orgs_527.zip
                                            THEN NULL ELSE political_orgs_527.geocoding_source END
                                """,
                                    batch,
                                )
                            conn.commit()
                            count += len(batch)
                            batch = []

                    print(f"    {row_count:,} records read")
        except Exception as e:
            print(f"    Error processing {filename}: {e}")
            continue

    if batch:
        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO political_orgs_527 (
                    ein, org_name, filing_type, org_type,
                    address, city, state, zip,
                    filing_date, latitude, longitude, geocode_date, geocoding_source,
                    source_file
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (ein, filing_type) DO UPDATE SET
                    org_name = EXCLUDED.org_name,
                    address = EXCLUDED.address,
                    city = EXCLUDED.city,
                    state = EXCLUDED.state,
                    zip = EXCLUDED.zip,
                    org_type = EXCLUDED.org_type,
                    filing_date = EXCLUDED.filing_date,
                    source_file = EXCLUDED.source_file,
                    latitude = CASE
                        WHEN EXCLUDED.address IS DISTINCT FROM political_orgs_527.address
                          OR EXCLUDED.city IS DISTINCT FROM political_orgs_527.city
                          OR EXCLUDED.state IS DISTINCT FROM political_orgs_527.state
                          OR EXCLUDED.zip IS DISTINCT FROM political_orgs_527.zip
                        THEN NULL ELSE political_orgs_527.latitude END,
                    longitude = CASE
                        WHEN EXCLUDED.address IS DISTINCT FROM political_orgs_527.address
                          OR EXCLUDED.city IS DISTINCT FROM political_orgs_527.city
                          OR EXCLUDED.state IS DISTINCT FROM political_orgs_527.state
                          OR EXCLUDED.zip IS DISTINCT FROM political_orgs_527.zip
                        THEN NULL ELSE political_orgs_527.longitude END,
                    geocode_date = CASE
                        WHEN EXCLUDED.address IS DISTINCT FROM political_orgs_527.address
                          OR EXCLUDED.city IS DISTINCT FROM political_orgs_527.city
                          OR EXCLUDED.state IS DISTINCT FROM political_orgs_527.state
                          OR EXCLUDED.zip IS DISTINCT FROM political_orgs_527.zip
                        THEN NULL ELSE political_orgs_527.geocode_date END,
                    geocoding_source = CASE
                        WHEN EXCLUDED.address IS DISTINCT FROM political_orgs_527.address
                          OR EXCLUDED.city IS DISTINCT FROM political_orgs_527.city
                          OR EXCLUDED.state IS DISTINCT FROM political_orgs_527.state
                          OR EXCLUDED.zip IS DISTINCT FROM political_orgs_527.zip
                        THEN NULL ELSE political_orgs_527.geocoding_source END
            """,
                batch,
            )
        conn.commit()
        count += len(batch)

    print(f"  527 import complete: {count:,} records")
    return count


def import_census(conn, archives_dir: str) -> int:
    """Import census demographics CSV files."""
    census_dir = os.path.join(archives_dir, "census")
    if not os.path.exists(census_dir):
        print("  Census directory not found, skipping")
        return 0

    count = 0
    batch = []
    batch_size = 1000

    def get_int(v):
        try:
            v = str(v).strip()
            if v in ("", "-", "-6666666666", "-8888888888", "-9999999999", "null"):
                return None
            return int(float(v))
        except (ValueError, TypeError):
            return None

    for year_dir in sorted(os.listdir(census_dir)):
        year_path = os.path.join(census_dir, year_dir)
        if not os.path.isdir(year_path):
            continue

        try:
            year = int(year_dir)
        except ValueError:
            continue

        for filename in sorted(os.listdir(year_path)):
            if not filename.endswith(".csv"):
                continue

            if file_already_imported(
                conn, "census_demographics", "source_file", filename
            ):
                continue

            filepath = os.path.join(year_path, filename)
            geo_type = "tract" if "tract" in filename else "county"

            row_count = 0
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                reader = csv.DictReader(f)

                for row in reader:
                    # Build GEOID from state + county + tract (or just state + county)
                    state = row.get("state", "").strip()
                    county = row.get("county", "").strip()
                    tract = row.get("tract", "").strip() if "tract" in row else ""

                    if geo_type == "tract" and tract:
                        geoid = f"{state}{county}{tract}"
                    else:
                        geoid = f"{state}{county}"

                    if not geoid or geoid == "":
                        continue

                    total_pop = get_int(row.get("B01001_001E"))
                    if total_pop is None or total_pop < 0:
                        continue

                    batch.append(
                        (
                            geoid,
                            geo_type,
                            year,
                            total_pop,
                            get_int(row.get("B19013_001E")),
                            get_int(row.get("B17001_002E")),
                            get_int(row.get("B02001_002E")),
                            get_int(row.get("B02001_003E")),
                            get_int(row.get("B03003_003E")),
                            get_int(row.get("B15003_022E")),
                            get_int(row.get("B25001_001E")),
                            get_int(row.get("B25077_001E")),
                            filename,
                        )
                    )
                    row_count += 1

                    if len(batch) >= batch_size:
                        with conn.cursor() as cur:
                            cur.executemany(
                                """
                                INSERT INTO census_demographics (
                                    geoid, geo_type, year, total_population,
                                    median_household_income, poverty_count,
                                    white_count, black_count, hispanic_count,
                                    bachelors_count, housing_units, median_housing_value,
                                    source_file
                                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                ON CONFLICT (geoid, year, geo_type) DO UPDATE SET
                                    total_population = EXCLUDED.total_population,
                                    median_household_income = EXCLUDED.median_household_income,
                                    poverty_count = EXCLUDED.poverty_count,
                                    white_count = EXCLUDED.white_count,
                                    black_count = EXCLUDED.black_count,
                                    hispanic_count = EXCLUDED.hispanic_count,
                                    bachelors_count = EXCLUDED.bachelors_count,
                                    housing_units = EXCLUDED.housing_units,
                                    median_housing_value = EXCLUDED.median_housing_value,
                                    source_file = EXCLUDED.source_file
                            """,
                                batch,
                            )
                        conn.commit()
                        count += len(batch)
                        batch = []

            if row_count > 0:
                print(f"    {filename}: {row_count:,} rows")

    if batch:
        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO census_demographics (
                    geoid, geo_type, year, total_population,
                    median_household_income, poverty_count,
                    white_count, black_count, hispanic_count,
                    bachelors_count, housing_units, median_housing_value,
                    source_file
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (geoid, year, geo_type) DO UPDATE SET
                    total_population = EXCLUDED.total_population,
                    median_household_income = EXCLUDED.median_household_income,
                    poverty_count = EXCLUDED.poverty_count,
                    white_count = EXCLUDED.white_count,
                    black_count = EXCLUDED.black_count,
                    hispanic_count = EXCLUDED.hispanic_count,
                    bachelors_count = EXCLUDED.bachelors_count,
                    housing_units = EXCLUDED.housing_units,
                    median_housing_value = EXCLUDED.median_housing_value,
                    source_file = EXCLUDED.source_file
            """,
                batch,
            )
        conn.commit()
        count += len(batch)

    print(f"  Census import complete: {count:,} rows")
    return count


def import_soi(conn, archives_dir: str, reimport: bool = False) -> int:
    """Import SOI per-EIN financial CSV data into form990_soi / form990_soi_private_foundation."""
    soi_csv_dir = os.path.join(archives_dir, "soi", "csv")
    if not os.path.exists(soi_csv_dir):
        print("  SOI CSV directory not found, skipping")
        return 0

    count = 0

    def year_from_filename(fname):
        m = re.match(r"(\d{2})", fname)
        if m:
            yr = int(m.group(1))
            return 2000 + yr if yr < 50 else 1900 + yr
        return None

    def get_int(row, col):
        v = row.get(col, "").strip()
        if not v or v == "-" or v == "--" or v == "":
            return None
        try:
            return int(float(v.replace(",", "").replace(" ", "")))
        except (ValueError, TypeError):
            return None

    def get_bool(row, col):
        v = row.get(col, "").strip().upper()
        return v == "X" or v == "1" or v == "TRUE" if v else None

    def detect_form_type(filename):
        fname = filename.lower()
        if "990pf" in fname or "pf" in fname.split("."):
            return "990pf"
        if "ez" in fname.split("."):
            return "990ez"
        return "990"

    batch_990 = []
    batch_990pf = []
    batch_size = 1000

    for filename in sorted(os.listdir(soi_csv_dir)):
        if not filename.endswith(".csv"):
            continue

        form_type = detect_form_type(filename)
        target_table = (
            "form990_soi_private_foundation" if form_type == "990pf" else "form990_soi"
        )

        if not reimport and file_already_imported(
            conn, target_table, "source_file", filename
        ):
            print(f"  Skipping {filename} (already imported)")
            continue

        filepath = os.path.join(soi_csv_dir, filename)
        default_year = year_from_filename(filename)

        print(f"  Importing {filename} ({form_type})")

        row_count = 0
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)

            for row in reader:
                # Normalize column names to lowercase
                r = {k.lower(): v for k, v in row.items()}

                ein = r.get("ein", "").strip().replace("-", "").replace(" ", "")
                if not ein or not ein.isdigit() or len(ein) < 9:
                    continue

                # Tax period (format varies: YYYYMM or YYYY)
                tax_pd = r.get("tax_pd", r.get("tax_prd", "")).strip()
                tax_year = None
                if tax_pd and len(tax_pd) >= 4:
                    try:
                        tax_year = int(tax_pd[:4])
                    except ValueError:
                        pass
                if not tax_year:
                    tax_year = default_year
                if not tax_year:
                    continue

                if form_type == "990pf":
                    # === FORM 990-PF ===
                    total_assets = get_int(r, "totassetsend")
                    total_receipts = get_int(r, "totrcptperbks")
                    if total_receipts is None and total_assets is None:
                        continue

                    batch_990pf.append(
                        (
                            ein,
                            tax_year,
                            tax_pd,
                            r.get("operatingcd", "").strip(),
                            get_int(r, "fairmrktvalamt"),
                            get_int(r, "grscontrgifts"),
                            get_int(r, "intrstrvnue"),
                            get_int(r, "dividndsamt"),
                            get_int(r, "grsrents"),
                            get_int(r, "grsslspramt"),
                            get_int(r, "costsold"),
                            get_int(r, "grsprofitbus"),
                            get_int(r, "otherincamt"),
                            total_receipts,
                            get_int(r, "compofficers"),
                            get_int(r, "pensplemplbenf"),
                            get_int(r, "legalfeesamt"),
                            get_int(r, "accountingfees"),
                            get_int(r, "interestamt"),
                            get_int(r, "depreciationamt"),
                            get_int(r, "occupancyamt"),
                            get_int(r, "travlconfmtns"),
                            get_int(r, "printingpubl"),
                            get_int(r, "totexpnspbks"),
                            get_int(r, "contrpdpbks"),
                            get_int(r, "excessrcpts"),
                            get_int(r, "netinvstinc"),
                            get_int(r, "adjnetinc"),
                            get_int(r, "othrcashamt"),
                            get_int(r, "invstgovtoblig"),
                            get_int(r, "invstcorpstk"),
                            get_int(r, "invstcorpbd"),
                            get_int(r, "totinvstsec"),
                            get_int(r, "mrtgloans"),
                            get_int(r, "othrinvstend"),
                            get_int(r, "othrassetseoy"),
                            total_assets,
                            get_int(r, "mrgtnotespay"),
                            get_int(r, "othrliabltseoy"),
                            get_int(r, "totliabend"),
                            get_int(r, "tfundnworth"),
                            get_int(r, "fairmrktvaleoy"),
                            get_int(r, "taxdue"),
                            get_int(r, "invstexcisetx"),
                            get_int(r, "distribamt"),
                            get_int(r, "undistribyr"),
                            get_int(r, "qlfydistribtot"),
                            get_int(r, "cmpmininvstr"),
                            get_int(r, "grntapprvfut"),
                            r.get("operatingcd", "").strip() == "1",
                            filename,
                        )
                    )
                else:
                    # === FORM 990 / 990-EZ ===
                    total_revenue = get_int(r, "totrevenue") or get_int(r, "totrevnue")
                    total_expenses = get_int(r, "totfuncexpns") or get_int(
                        r, "totexpns"
                    )
                    total_assets = get_int(r, "totassetsend")
                    if (
                        total_revenue is None
                        and total_expenses is None
                        and total_assets is None
                    ):
                        continue

                    # Grants: sum multiple columns
                    grants_paid = 0
                    has_grants = False
                    for gc in ["grntstogovt", "grnsttoindiv", "grntstofrgngovt"]:
                        v = get_int(r, gc)
                        if v is not None:
                            grants_paid += v
                            has_grants = True
                    if not has_grants:
                        grants_paid = None

                    batch_990.append(
                        (
                            ein,
                            tax_year,
                            None,  # org_name
                            None,  # state
                            None,  # ntee_code
                            None,  # asset_size
                            total_revenue,
                            total_expenses,
                            total_assets,
                            get_int(r, "totliabend"),
                            get_int(r, "totnetassetend"),
                            get_int(r, "totcntrbgfts"),
                            grants_paid,
                            get_int(r, "compnsatncurrofcr"),
                            None,  # revenue_less_expenses
                            None,  # total_programs
                            filename,
                            # Expanded fields
                            form_type,
                            r.get("subseccd", "").strip(),
                            r.get("s501c3or4947a1cd", "").strip() == "X",
                            get_int(r, "totprgmrevnue"),
                            get_int(r, "invstmntinc"),
                            get_int(r, "royaltsinc"),
                            get_int(r, "netrntlinc"),
                            get_int(r, "netgnls"),
                            get_int(r, "grsincfndrsng"),
                            get_int(r, "grsincgaming"),
                            get_int(r, "txexmptint"),
                            get_int(r, "legalfees"),
                            get_int(r, "accntingfees"),
                            get_int(r, "profndraising"),
                            get_int(r, "feesforsrvcmgmt"),
                            get_int(r, "feesforsrvcinvstmgmt"),
                            get_int(r, "advrtpromo"),
                            get_int(r, "officexpns"),
                            get_int(r, "occupancy"),
                            get_int(r, "travel"),
                            get_int(r, "insurance"),
                            get_int(r, "deprcatndepletn"),
                            get_int(r, "interestamt"),
                            get_int(r, "othrsalwages"),
                            get_int(r, "pensionplancontrb"),
                            get_int(r, "othremplyeebenef"),
                            get_int(r, "payrolltx"),
                            get_int(r, "totreprtabled"),
                            get_int(r, "totestcompf"),
                            get_int(r, "noindiv100kcnt"),
                            get_int(r, "lndbldgsequipend"),
                            get_int(r, "invstmntsend"),
                            get_int(r, "nonintcashend"),
                            get_int(r, "noemplyeesw3cnt"),
                            get_int(r, "totnooforgscnt"),
                            get_int(r, "totsupport"),
                            r.get("nonpfrea", "").strip(),
                            get_bool(r, "filedf990tcd"),
                            get_bool(r, "unrelbusinccd"),
                            get_bool(r, "frgnofficecd"),
                            get_bool(r, "politicalactvtscd"),
                            get_bool(r, "lbbyingactvtscd"),
                            get_bool(r, "operatehosptlcd"),
                            get_bool(r, "dnradvisedfundscd"),
                        )
                    )

                row_count += 1

                if form_type != "990pf" and len(batch_990) >= batch_size:
                    _flush_990_batch(conn, batch_990)
                    count += len(batch_990)
                    batch_990 = []
                elif form_type == "990pf" and len(batch_990pf) >= batch_size:
                    _flush_990pf_batch(conn, batch_990pf)
                    count += len(batch_990pf)
                    batch_990pf = []

        print(f"    {row_count:,} rows read")

    if batch_990:
        _flush_990_batch(conn, batch_990)
        count += len(batch_990)
    if batch_990pf:
        _flush_990pf_batch(conn, batch_990pf)
        count += len(batch_990pf)

    print(f"  SOI import complete: {count:,} rows")
    return count


def _flush_990_batch(conn, batch):
    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO form990_soi (
                ein, tax_year, org_name, state, ntee_code, asset_size,
                total_revenue, total_expenses, total_assets,
                total_liabilities, net_assets, contributions,
                grants_paid, compensation_officers,
                revenue_less_expenses, total_programs, source_file,
                form_type, subseccd, is_501c3,
                total_program_revenue, investment_income, royalty_income,
                net_rental_income, net_gains_losses, fundraising_income,
                gaming_income, tax_exempt_interest,
                legal_fees, accounting_fees, professional_fundraising,
                management_fees, investment_mgmt_fees,
                advertising, office_expenses, occupancy, travel,
                insurance, depreciation, interest_expense,
                other_salaries_wages, pension_contributions,
                employee_benefits, payroll_taxes,
                total_reportable_comp, total_estimated_comp,
                individuals_over_100k,
                land_buildings_equipment, investments_end, cash_end,
                num_employees, num_orgs, total_support, non_pf_reason,
                filed_990t, unrelated_business_income, foreign_offices,
                political_activities, lobbying_activities,
                operates_hospital, donor_advised_funds
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (ein, tax_year) DO UPDATE SET
                total_revenue = EXCLUDED.total_revenue,
                total_expenses = EXCLUDED.total_expenses,
                total_assets = EXCLUDED.total_assets,
                total_liabilities = EXCLUDED.total_liabilities,
                net_assets = EXCLUDED.net_assets,
                contributions = EXCLUDED.contributions,
                grants_paid = EXCLUDED.grants_paid,
                compensation_officers = EXCLUDED.compensation_officers,
                source_file = EXCLUDED.source_file,
                form_type = EXCLUDED.form_type, subseccd = EXCLUDED.subseccd, is_501c3 = EXCLUDED.is_501c3,
                total_program_revenue = EXCLUDED.total_program_revenue, investment_income = EXCLUDED.investment_income,
                royalty_income = EXCLUDED.royalty_income, net_rental_income = EXCLUDED.net_rental_income,
                net_gains_losses = EXCLUDED.net_gains_losses, fundraising_income = EXCLUDED.fundraising_income,
                gaming_income = EXCLUDED.gaming_income, tax_exempt_interest = EXCLUDED.tax_exempt_interest,
                legal_fees = EXCLUDED.legal_fees, accounting_fees = EXCLUDED.accounting_fees,
                professional_fundraising = EXCLUDED.professional_fundraising, management_fees = EXCLUDED.management_fees,
                investment_mgmt_fees = EXCLUDED.investment_mgmt_fees, advertising = EXCLUDED.advertising,
                office_expenses = EXCLUDED.office_expenses, occupancy = EXCLUDED.occupancy,
                travel = EXCLUDED.travel, insurance = EXCLUDED.insurance,
                depreciation = EXCLUDED.depreciation, interest_expense = EXCLUDED.interest_expense,
                other_salaries_wages = EXCLUDED.other_salaries_wages, pension_contributions = EXCLUDED.pension_contributions,
                employee_benefits = EXCLUDED.employee_benefits, payroll_taxes = EXCLUDED.payroll_taxes,
                total_reportable_comp = EXCLUDED.total_reportable_comp, total_estimated_comp = EXCLUDED.total_estimated_comp,
                individuals_over_100k = EXCLUDED.individuals_over_100k,
                land_buildings_equipment = EXCLUDED.land_buildings_equipment, investments_end = EXCLUDED.investments_end,
                cash_end = EXCLUDED.cash_end, num_employees = EXCLUDED.num_employees,
                num_orgs = EXCLUDED.num_orgs, total_support = EXCLUDED.total_support,
                non_pf_reason = EXCLUDED.non_pf_reason, filed_990t = EXCLUDED.filed_990t,
                unrelated_business_income = EXCLUDED.unrelated_business_income, foreign_offices = EXCLUDED.foreign_offices,
                political_activities = EXCLUDED.political_activities, lobbying_activities = EXCLUDED.lobbying_activities,
                operates_hospital = EXCLUDED.operates_hospital, donor_advised_funds = EXCLUDED.donor_advised_funds
        """,
            batch,
        )
    conn.commit()


def _flush_990pf_batch(conn, batch):
    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO form990_soi_private_foundation (
                ein, tax_year, tax_period, operating_cd,
                fair_market_value, gross_contributions, interest_revenue,
                dividends, gross_rents, gross_sales_price, cost_of_goods_sold,
                gross_profit_business, other_income, total_receipts_books,
                compensation_officers, pension_benefits, legal_fees, accounting_fees,
                interest_expense, depreciation, occupancy, travel_conferences,
                printing_publications, total_expenses_books, contributions_paid,
                excess_receipts, net_investment_income, adjusted_net_income,
                total_cash, investments_govt_obligations, investments_corp_stock,
                investments_corp_bonds, total_investment_securities, mortgage_loans,
                other_investments, other_assets, total_assets, mortgage_notes_payable,
                other_liabilities, total_liabilities, fund_net_worth,
                fair_market_value_eoy, tax_due, excise_tax, distributions,
                undistributed_income, qualifying_distributions,
                minimum_investment_return, grants_approved_future,
                is_operating, source_file
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (ein, tax_year) DO UPDATE SET
                fair_market_value = EXCLUDED.fair_market_value,
                total_receipts_books = EXCLUDED.total_receipts_books,
                total_assets = EXCLUDED.total_assets,
                total_liabilities = EXCLUDED.total_liabilities,
                distributions = EXCLUDED.distributions,
                net_investment_income = EXCLUDED.net_investment_income,
                source_file = EXCLUDED.source_file
        """,
            batch,
        )
    conn.commit()


def import_pub78(conn, archives_dir: str) -> int:
    """Import Pub78 eligible organizations."""
    status_dir = os.path.join(archives_dir, "status")
    count = 0

    for filename in os.listdir(status_dir):
        if "pub78" in filename.lower() and filename.endswith((".txt", ".dat")):
            if file_already_imported(conn, "pub78_eligible", "source_file", filename):
                print(f"  Skipping {filename} (already imported)")
                continue
            filepath = os.path.join(status_dir, filename)
            print(f"  Importing {filename}")

            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                reader = csv.reader(f, delimiter="|")
                batch = []

                for row in tqdm(reader, desc="  Processing", unit="rows"):
                    if len(row) >= 3:
                        ein = row[0].strip().replace("-", "")
                        name = row[1].strip() if len(row) > 1 else ""
                        city = row[2].strip() if len(row) > 2 else ""
                        state = row[3].strip() if len(row) > 3 else ""

                        if ein:
                            batch.append((ein, name, city, state, True, filename))

                            if len(batch) >= BATCH_SIZE:
                                insert_pub78_batch(conn, batch)
                                count += len(batch)
                                batch = []

                if batch:
                    insert_pub78_batch(conn, batch)
                    count += len(batch)

    return count


def insert_pub78_batch(conn, batch: List[Tuple]):
    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO pub78_eligible (ein, org_name, city, state, is_deductible, source_file)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (ein) DO UPDATE SET
                org_name = EXCLUDED.org_name,
                city = EXCLUDED.city,
                state = EXCLUDED.state,
                downloaded_at = CURRENT_TIMESTAMP
        """,
            batch,
        )
        conn.commit()


def import_revocation(conn, archives_dir: str) -> int:
    """Import revoked organizations."""
    status_dir = os.path.join(archives_dir, "status")
    count = 0

    for filename in os.listdir(status_dir):
        if "revocation" in filename.lower() and filename.endswith((".txt", ".dat")):
            if file_already_imported(
                conn, "revoked_organizations", "source_file", filename
            ):
                print(f"  Skipping {filename} (already imported)")
                continue
            filepath = os.path.join(status_dir, filename)
            print(f"  Importing {filename}")

            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                reader = csv.reader(f, delimiter="|")
                batch = []

                for row in tqdm(reader, desc="  Processing", unit="rows"):
                    if len(row) >= 2:
                        ein = row[0].strip().replace("-", "")
                        name = row[1].strip() if len(row) > 1 else ""

                        date_str = row[2].strip() if len(row) > 2 else ""
                        rev_date = None
                        if date_str:
                            try:
                                rev_date = datetime.strptime(
                                    date_str, "%m/%d/%Y"
                                ).date()
                            except:
                                pass

                        if ein:
                            batch.append((ein, name, rev_date, "", filename))

                            if len(batch) >= BATCH_SIZE:
                                insert_revocation_batch(conn, batch)
                                count += len(batch)
                                batch = []

                if batch:
                    insert_revocation_batch(conn, batch)
                    count += len(batch)

    return count


def insert_revocation_batch(conn, batch: List[Tuple]):
    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO revoked_organizations (ein, org_name, revocation_date, revocation_reason, source_file)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (ein) DO UPDATE SET
                org_name = EXCLUDED.org_name,
                revocation_date = EXCLUDED.revocation_date,
                downloaded_at = CURRENT_TIMESTAMP
        """,
            batch,
        )
        conn.commit()


def import_form990n(conn, archives_dir: str) -> int:
    """Import Form 990-N small org data."""
    form990n_dir = os.path.join(archives_dir, "form990n")
    count = 0

    for filename in os.listdir(form990n_dir):
        if filename.endswith((".txt", ".dat")) and "epostcard" in filename.lower():
            if file_already_imported(
                conn, "form990n_small_orgs", "source_file", filename
            ):
                print(f"  Skipping {filename} (already imported)")
                continue
            filepath = os.path.join(form990n_dir, filename)
            print(f"  Importing {filename}")

            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                reader = csv.reader(f, delimiter="|")
                batch = []

                for row in tqdm(reader, desc="  Processing", unit="rows"):
                    if len(row) >= 2:
                        ein = row[0].strip().replace("-", "")
                        name = row[1].strip()[:500] if len(row) > 1 else ""
                        tax_period = row[2].strip()[:20] if len(row) > 2 else ""
                        website = row[3].strip()[:500] if len(row) > 3 else ""

                        if ein:
                            batch.append(
                                (ein[:20], name, tax_period, website, filename)
                            )

                            if len(batch) >= BATCH_SIZE:
                                insert_990n_batch(conn, batch)
                                count += len(batch)
                                batch = []

                if batch:
                    insert_990n_batch(conn, batch)
                    count += len(batch)

    return count


def insert_990n_batch(conn, batch: List[Tuple]):
    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO form990n_small_orgs (ein, org_name, tax_period, website, source_file)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (ein) DO UPDATE SET
                org_name = EXCLUDED.org_name,
                tax_period = EXCLUDED.tax_period,
                website = EXCLUDED.website,
                downloaded_at = CURRENT_TIMESTAMP
        """,
            batch,
        )
        conn.commit()


def import_form990_xml(
    conn,
    archives_dir: str,
    limit: Optional[int] = None,
    reimport: bool = False,
    reimport_zip: str = None,
    show_status: bool = False,
) -> int:
    """Import Form 990 XML data with per-zip tracking.

    Args:
        conn: Database connection
        archives_dir: Path to archives directory
        limit: Max XML files to process per zip
        reimport: If True, reimport ALL zips regardless of status
        reimport_zip: If set, only reimport this specific zip filename
        show_status: If True, print status table and return 0

    Returns:
        Number of records imported
    """
    xml_dir = os.path.join(archives_dir, "form990", "xml")
    if not os.path.exists(xml_dir):
        print(f"  XML directory not found: {xml_dir}")
        return 0

    # Bootstrap import_log if empty (first run after adding tracking)
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM form990_xml_import_log")
        if cur.fetchone()[0] == 0:
            bootstrapped = bootstrap_import_log(conn)
            if bootstrapped:
                print(
                    f"  Bootstrapped import log with {bootstrapped} existing zip entries"
                )

    # Get current import status
    import_status = get_xml_import_status(conn)

    # Build list of zip files
    all_zips = sorted([f for f in os.listdir(xml_dir) if f.endswith(".zip")])

    # Filter to only zips that need processing
    if reimport_zip:
        # Single zip reimport
        if reimport_zip in all_zips:
            zips_to_process = [reimport_zip]
        else:
            print(f"  Zip file not found: {reimport_zip}")
            return 0
    elif reimport:
        # Force reimport all
        zips_to_process = all_zips
    else:
        # Default: only zips not marked 'complete' (smart reimport)
        zips_to_process = []
        for f in all_zips:
            status = import_status.get(f, {}).get("status")
            if status not in ("complete",):
                zips_to_process.append(f)

    # Show status mode: print table and return
    if show_status:
        print(
            f"\n{'Zip File':<35} {'XMLs':>8} {'Imported':>10} {'990':>8} {'990T':>8} {'SchedO':>8} {'Status':<12}"
        )
        print("-" * 105)
        for f in all_zips:
            s = import_status.get(f, {})
            xml_c = s.get("xml_count", "?")
            imp = s.get("records_imported", 0) or 0
            r990 = s.get("records_990", 0) or 0
            r990t = s.get("records_990t", 0) or 0
            so = s.get("schedule_o_count", 0) or 0
            st = s.get("status", "not imported")
            notes = s.get("notes", "")
            if st == "deflate64" and notes:
                st = f"{st} ({notes})"
            print(
                f"  {f:<33} {str(xml_c):>8} {imp:>10} {r990:>8} {r990t:>8} {so:>8} {st:<12}"
            )
        to_import = len(zips_to_process)
        print(
            f"\n  {len(all_zips)} total zips, {len(all_zips) - to_import} complete, {to_import} need import"
        )
        return 0

    if not zips_to_process:
        print("\n=== Form 990 XML === All zips already imported.")
        return 0

    print(f"\n=== Importing Form 990 XML === {len(zips_to_process)} zips to process")

    def process_xml_files(xml_file_list, filename, conn, temp_dir, limit, processed):
        """Process a list of extracted XML files. Returns (count_990, count_990t, sched_o_count, processed)."""
        r990, r990t, sched_o, local_processed = 0, 0, 0, 0
        for xml_name in (
            tqdm(xml_file_list, desc="    XML files", unit="files")
            if TQDM_AVAILABLE
            else xml_file_list
        ):
            if limit and processed + local_processed >= limit:
                break
            xml_path = os.path.join(temp_dir, xml_name)
            try:
                record = parse_form990_xml(xml_path, filename)
                if record:
                    if len(record) == 27:
                        insert_990t_detail(conn, record[:26], filename)
                        r990t += 1
                        sched_o_text = record[26]
                        if sched_o_text:
                            insert_schedule_o(
                                conn,
                                record[0],
                                record[1],
                                "990T",
                                sched_o_text,
                                filename,
                            )
                            sched_o += 1
                    else:
                        main_record = record[:14] + record[14:19]
                        sched_o_text = record[19] if len(record) > 19 else None
                        insert_990_detail(conn, main_record, filename)
                        r990 += 1
                        if sched_o_text:
                            insert_schedule_o(
                                conn,
                                record[0],
                                record[1],
                                record[2],
                                sched_o_text,
                                filename,
                            )
                            sched_o += 1
            except Exception as e:
                logger.debug(f"Error parsing {xml_name}: {e}")
            try:
                os.remove(xml_path)
            except:
                pass
            local_processed += 1
        return r990, r990t, sched_o, local_processed

    total_count = 0
    processed = 0

    for filename in zips_to_process:
        if limit and processed >= limit:
            break

        zip_path = os.path.join(xml_dir, filename)
        temp_dir = os.path.join(xml_dir, "temp", filename)
        os.makedirs(temp_dir, exist_ok=True)

        print(f"  Processing {filename}")

        # Count XMLs in zip for tracking
        xml_count, count_error = count_xmls_in_zip(zip_path)
        if count_error and count_error != "deflate64":
            print(f"  Warning: could not count XMLs: {count_error}")

        # Mark as started in tracking
        update_xml_import_log(conn, filename, xml_count=xml_count, started=True)

        r990, r990t, sched_o = 0, 0, 0
        error_msg = None

        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                xml_files = [n for n in zf.namelist() if n.endswith(".xml")]
                file_list = xml_files[:limit] if limit else xml_files
                for xml_name in (
                    tqdm(file_list, desc="    XML files", unit="files")
                    if TQDM_AVAILABLE
                    else file_list
                ):
                    if limit and processed >= limit:
                        break
                    zf.extract(xml_name, temp_dir)
                    xml_path = os.path.join(temp_dir, xml_name)
                    try:
                        record = parse_form990_xml(xml_path, filename)
                        if record:
                            if len(record) == 27:
                                insert_990t_detail(conn, record[:26], filename)
                                r990t += 1
                                sched_o_text = record[26]
                                if sched_o_text:
                                    insert_schedule_o(
                                        conn,
                                        record[0],
                                        record[1],
                                        "990T",
                                        sched_o_text,
                                        filename,
                                    )
                                    sched_o += 1
                            else:
                                main_record = record[:14] + record[14:19]
                                sched_o_text = record[19] if len(record) > 19 else None
                                insert_990_detail(conn, main_record, filename)
                                r990 += 1
                                if sched_o_text:
                                    insert_schedule_o(
                                        conn,
                                        record[0],
                                        record[1],
                                        record[2],
                                        sched_o_text,
                                        filename,
                                    )
                                    sched_o += 1
                    except Exception as e:
                        logger.debug(f"Error parsing {xml_name}: {e}")
                    try:
                        os.remove(xml_path)
                    except:
                        pass
                    processed += 1
        except (zipfile.BadZipFile, NotImplementedError) as e:
            # Python's zipfile doesn't support Deflate64 (method 9).
            # Fallback to system unzip command.
            print(f"  zipfile failed: {e}. Using unzip fallback...")
            try:
                import shutil

                shutil.rmtree(temp_dir)
            except:
                pass
            os.makedirs(temp_dir, exist_ok=True)

            result = subprocess.run(
                ["unzip", "-o", "-j", zip_path, "*.xml", "-d", temp_dir],
                capture_output=True,
                text=True,
                timeout=300,
            )

            xml_files = [f for f in os.listdir(temp_dir) if f.endswith(".xml")]
            if not xml_files:
                error_msg = f"unzip failed (rc={result.returncode}): {result.stderr.strip()[:200]}"
                print(f"  {error_msg}")
                try:
                    import shutil

                    shutil.rmtree(temp_dir)
                except:
                    pass
            else:
                file_list = xml_files[:limit] if limit else xml_files
                r990, r990t, sched_o, batch_processed = process_xml_files(
                    file_list, filename, conn, temp_dir, limit, processed
                )
                processed += batch_processed

        # Cleanup temp dir
        try:
            import shutil

            shutil.rmtree(temp_dir)
        except:
            pass

        # Update tracking
        total_records = r990 + r990t
        total_count += total_records
        if error_msg:
            status = "failed"
        elif xml_count and total_records < xml_count * 0.5:
            status = "partial"
        else:
            status = "complete"

        update_xml_import_log(
            conn,
            filename,
            xml_count=xml_count,
            records_990=r990,
            records_990t=r990t,
            schedule_o_count=sched_o,
            status=status,
            notes=error_msg,
        )

        print(f"    {r990} 990 + {r990t} 990T + {sched_o} SchedO records [{status}]")

    return total_count


def count_xmls_in_zip(zip_path):
    """Count XML files in a zip without extracting. Returns (count, error_message)."""
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            return sum(1 for n in zf.namelist() if n.endswith(".xml")), None
    except NotImplementedError as e:
        # Deflate64 — try unzip -l
        try:
            result = subprocess.run(
                ["unzip", "-l", zip_path], capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                count = sum(
                    1 for line in result.stdout.split("\n") if ".xml" in line.lower()
                )
                return count, "deflate64"
        except:
            pass
        return None, str(e)
    except Exception as e:
        return None, str(e)


def parse_form990_xml(xml_path: str, source_filename: str) -> Optional[Tuple]:
    """Parse Form 990 XML and return record tuple with Schedule O and R data."""
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        ein = None
        for elem in root.iter():
            if "EIN" in elem.tag or "EmployerIdentification" in elem.tag:
                if elem.text:
                    ein = elem.text.replace("-", "").strip()
                    if len(ein) == 9:
                        break

        if not ein:
            return None

        def find_text(tag):
            for elem in root.iter():
                if tag.lower() in elem.tag.lower() and elem.text:
                    return elem.text.strip()
            return None

        def find_money(tag):
            v = find_text(tag)
            if v:
                try:
                    return int(v.replace(",", "").replace("$", ""))
                except:
                    pass
            return None

        def find_bool(tag):
            v = find_text(tag)
            if v:
                return v.lower() in ("true", "x", "1")
            return False

        tax_period = None
        for elem in root.iter():
            if "TaxPeriod" in elem.tag or "TaxYear" in elem.tag:
                if elem.text:
                    tax_period = re.sub(r"[^0-9]", "", elem.text)[:6]
                    break

        form_type = "990"
        for tag in ["Form990T", "Form990", "Form990EZ", "Form990PF"]:
            for elem in root.iter():
                if tag in elem.tag:
                    form_type = tag.replace("Form", "")
                    break
            if form_type != "990":
                break

        # 990T has different field structure - return early with 990T mapping
        if form_type == "990T":
            o501c = find_text("Organization501cTypeTxt") or ""
            filing_date_str = find_text("SignatureDt")
            filing_date = filing_date_str if filing_date_str else None

            # Schedule O text for 990T
            sched_o_supplemental = ""
            for elem in root.iter():
                tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
                if tag == "ExplanationTxt":
                    if elem.text and len(elem.text.strip()) > 10:
                        sched_o_supplemental += elem.text.strip() + "\n"

            sched_o_text = (
                sched_o_supplemental
                if len(sched_o_supplemental.strip()) >= 20
                else None
            )

            # Return tuple matching form990t_details INSERT column order (26 columns)
            # + sched_o_text at index 26 (extracted by routing code)
            return (
                ein,  # 0
                tax_period or "",  # 1
                filing_date,  # 2
                find_text("Organization501cTypeTxt") or "",  # 3
                find_money("BookValueAssetsEOYAmt"),  # 4
                find_money("TotalUBTIComputedAmt"),  # 5
                find_money("TotalUBTIAmt"),  # 6
                find_money("TaxableCorporationAmt"),  # 7
                find_money("TotalTaxComputationAmt"),  # 8
                find_money("TotalTaxAmt"),  # 9
                find_money("EstimatedTaxPaymentsAmt"),  # 10
                find_money("SpecificDeductionAmt"),  # 11
                find_money("TotalDeductionAmt"),  # 12
                find_money("CharitableContributionsDedAmt"),  # 13
                find_money("CapitalGainNetIncomeAmt"),  # 14
                find_money("TotalOrdinaryGainLossAmt"),  # 15
                find_money("TotalPrtshpSCorpIncomeAmt"),  # 16
                find_money("OtherIncomeAmt"),  # 17
                find_money("InterestDeductionAmt"),  # 18
                find_money("OtherDeductionsAmt"),  # 19
                find_money("TotalDeductionsAmt"),  # 20
                find_money("UnrelatedBusinessTaxblIncmAmt"),  # 21
                find_text("PrincipalBusinessActivityCd") or "",  # 22
                find_text("TradeOrBusinessDesc") or "",  # 23
                source_filename,  # 24
                xml_path,  # 25
                sched_o_text,  # 26
            )

        # Schedule R flags
        sched_r_disregarded = find_bool("DisregardedEntityInd")
        sched_r_related = find_bool("RelatedEntityInd")
        sched_r_control = find_bool("RelatedOrganizationCtrlEntInd")
        sched_r_transfer = find_bool("TrnsfrExmptNonChrtblRltdOrgInd")
        sched_r_partnership = find_bool("ActivitiesConductedPrtshpInd")

        # Schedule O text (program accomplishments, governance, supplemental)
        sched_o_program = ""
        sched_o_governance = ""
        sched_o_supplemental = ""
        has_schedule_o = False
        for elem in root.iter():
            tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
            if tag == "IRS990ScheduleO":
                has_schedule_o = True
            elif tag == "DescriptionProgramSrvcAccomTxt":
                # Program accomplishment narrative (Part III)
                if elem.text and len(elem.text.strip()) > 10:
                    sched_o_program += elem.text.strip() + "\n"
            elif tag == "ExplanationTxt":
                # Schedule O supplemental explanations (SupplementalInformationDetail children)
                if elem.text and len(elem.text.strip()) > 10:
                    sched_o_supplemental += elem.text.strip() + "\n"
            elif tag == "DescriptionOfProgramSrvcAccomTxt":
                # Alternative tag for program accomplishments
                if elem.text and len(elem.text.strip()) > 10:
                    sched_o_program += elem.text.strip() + "\n"

        return (
            ein,
            tax_period or "",
            form_type,
            None,
            find_money("TotalRevenue"),
            find_money("Contributions"),
            find_money("ProgramServiceRevenue"),
            find_money("TotalExpenses"),
            find_money("GrantsAndOtherAmountsPaid"),
            find_money("TotalAssets"),
            find_money("TotalLiabilities"),
            find_money("NetAssets"),
            source_filename,
            xml_path,
            # Schedule R flags
            sched_r_disregarded,
            sched_r_related,
            sched_r_control,
            sched_r_transfer,
            sched_r_partnership,
            # Schedule O data (separate return value)
            (sched_o_program or sched_o_governance or sched_o_supplemental),
        )
    except Exception:
        return None


def get_xml_import_status(conn):
    """Get import status for all XML zip files. Returns dict of filename -> status row."""
    status = {}
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT zip_filename, xml_count, records_imported, records_990, records_990t, schedule_o_count, import_status, notes FROM form990_xml_import_log"
            )
            for row in cur.fetchall():
                status[row[0]] = {
                    "xml_count": row[1],
                    "records_imported": row[2],
                    "records_990": row[3],
                    "records_990t": row[4],
                    "schedule_o_count": row[5],
                    "status": row[6],
                    "notes": row[7],
                }
    except Exception:
        pass
    return status


def update_xml_import_log(
    conn,
    filename,
    xml_count=None,
    records_990=0,
    records_990t=0,
    schedule_o_count=0,
    status=None,
    notes=None,
    started=False,
):
    """Update or insert import tracking for a zip file."""
    try:
        with conn.cursor() as cur:
            if started:
                cur.execute(
                    """
                    INSERT INTO form990_xml_import_log (zip_filename, xml_count, import_started_at, import_status)
                    VALUES (%s, %s, CURRENT_TIMESTAMP, 'processing')
                    ON CONFLICT (zip_filename) DO UPDATE SET
                        xml_count = COALESCE(EXCLUDED.xml_count, form990_xml_import_log.xml_count),
                        import_started_at = CURRENT_TIMESTAMP,
                        import_status = 'processing'
                """,
                    (filename, xml_count),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO form990_xml_import_log
                        (zip_filename, xml_count, records_imported, records_990, records_990t,
                         schedule_o_count, import_completed_at, import_status, notes)
                    VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, %s, %s)
                    ON CONFLICT (zip_filename) DO UPDATE SET
                        xml_count = COALESCE(EXCLUDED.xml_count, form990_xml_import_log.xml_count),
                        records_imported = EXCLUDED.records_imported,
                        records_990 = EXCLUDED.records_990,
                        records_990t = EXCLUDED.records_990t,
                        schedule_o_count = EXCLUDED.schedule_o_count,
                        import_completed_at = CURRENT_TIMESTAMP,
                        import_status = EXCLUDED.import_status,
                        notes = EXCLUDED.notes
                """,
                    (
                        filename,
                        xml_count,
                        records_990 + records_990t,
                        records_990,
                        records_990t,
                        schedule_o_count,
                        status,
                        notes,
                    ),
                )
            conn.commit()
    except Exception as e:
        conn.rollback()
        logger.debug(f"Error updating import log for {filename}: {e}")


def bootstrap_import_log(conn):
    """Populate import_log from existing data for zips already imported before tracking."""
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO form990_xml_import_log
                    (zip_filename, records_imported, records_990, records_990t, schedule_o_count,
                     import_status, import_completed_at, notes)
                SELECT
                    source_file,
                    COALESCE(d.cnt, 0) + COALESCE(t.cnt, 0),
                    COALESCE(d.cnt, 0),
                    COALESCE(t.cnt, 0),
                    COALESCE(s.cnt, 0),
                    'complete',
                    CURRENT_TIMESTAMP,
                    'bootstrapped from existing data'
                FROM (
                    SELECT DISTINCT source_file FROM form990_details
                    UNION
                    SELECT DISTINCT source_file FROM form990t_details
                    UNION
                    SELECT DISTINCT source_file FROM form990_schedule_o
                ) z
                LEFT JOIN (SELECT source_file, COUNT(*) AS cnt FROM form990_details GROUP BY source_file) d ON z.source_file = d.source_file
                LEFT JOIN (SELECT source_file, COUNT(*) AS cnt FROM form990t_details GROUP BY source_file) t ON z.source_file = t.source_file
                LEFT JOIN (SELECT source_file, COUNT(*) AS cnt FROM form990_schedule_o GROUP BY source_file) s ON z.source_file = s.source_file
                WHERE z.source_file IS NOT NULL
                ON CONFLICT (zip_filename) DO NOTHING
            """)
            conn.commit()
            return cur.rowcount
    except Exception as e:
        conn.rollback()
        logger.debug(f"Error bootstrapping import log: {e}")
        return 0


def insert_990_detail(conn, record: Tuple, source: str):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO form990_details (
                ein, tax_period, form_type, filing_date, total_revenue,
                contributions_received, program_service_revenue, total_expenses,
                grants_paid, total_assets, total_liabilities, net_assets,
                source_file, xml_path,
                has_disregarded_entity, has_related_entity,
                has_related_org_control, has_transfer_to_noncharitable,
                has_partnership_activity
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (ein, tax_period) DO UPDATE SET
                form_type = EXCLUDED.form_type,
                filing_date = EXCLUDED.filing_date,
                total_revenue = EXCLUDED.total_revenue,
                contributions_received = EXCLUDED.contributions_received,
                program_service_revenue = EXCLUDED.program_service_revenue,
                total_expenses = EXCLUDED.total_expenses,
                grants_paid = EXCLUDED.grants_paid,
                total_assets = EXCLUDED.total_assets,
                total_liabilities = EXCLUDED.total_liabilities,
                net_assets = EXCLUDED.net_assets,
                source_file = EXCLUDED.source_file,
                xml_path = EXCLUDED.xml_path,
                has_disregarded_entity = EXCLUDED.has_disregarded_entity,
                has_related_entity = EXCLUDED.has_related_entity,
                has_related_org_control = EXCLUDED.has_related_org_control,
                has_transfer_to_noncharitable = EXCLUDED.has_transfer_to_noncharitable,
                has_partnership_activity = EXCLUDED.has_partnership_activity
        """,
            record,
        )
        conn.commit()


def insert_990t_detail(conn, record: Tuple, source: str):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO form990t_details (
                ein, tax_period, filing_date, organization_501c_type,
                book_value_assets_eoy, total_ubti_computed, total_ubti,
                taxable_corporation, total_tax_computation, total_tax,
                estimated_tax_payments, specific_deduction, total_deduction,
                charitable_contributions_ded, capital_gain_net_income,
                total_ordinary_gain_loss, total_prtshp_scorp_income,
                other_income, interest_deduction, other_deductions,
                total_deductions, unrelated_bus_income,
                principal_business_activity_cd, trade_or_business_desc,
                source_file, xml_path
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (ein, tax_period) DO UPDATE SET
                filing_date = EXCLUDED.filing_date,
                organization_501c_type = EXCLUDED.organization_501c_type,
                book_value_assets_eoy = EXCLUDED.book_value_assets_eoy,
                total_ubti_computed = EXCLUDED.total_ubti_computed,
                total_ubti = EXCLUDED.total_ubti,
                taxable_corporation = EXCLUDED.taxable_corporation,
                total_tax_computation = EXCLUDED.total_tax_computation,
                total_tax = EXCLUDED.total_tax,
                estimated_tax_payments = EXCLUDED.estimated_tax_payments,
                specific_deduction = EXCLUDED.specific_deduction,
                total_deduction = EXCLUDED.total_deduction,
                charitable_contributions_ded = EXCLUDED.charitable_contributions_ded,
                capital_gain_net_income = EXCLUDED.capital_gain_net_income,
                total_ordinary_gain_loss = EXCLUDED.total_ordinary_gain_loss,
                total_prtshp_scorp_income = EXCLUDED.total_prtshp_scorp_income,
                other_income = EXCLUDED.other_income,
                interest_deduction = EXCLUDED.interest_deduction,
                other_deductions = EXCLUDED.other_deductions,
                total_deductions = EXCLUDED.total_deductions,
                unrelated_bus_income = EXCLUDED.unrelated_bus_income,
                principal_business_activity_cd = EXCLUDED.principal_business_activity_cd,
                trade_or_business_desc = EXCLUDED.trade_or_business_desc,
                source_file = EXCLUDED.source_file,
                xml_path = EXCLUDED.xml_path
        """,
            record,
        )
        conn.commit()


def insert_schedule_o(conn, ein, tax_period, form_type, text, source):
    """Insert Schedule O narrative data."""
    if not text or len(text.strip()) < 20:
        return
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO form990_schedule_o (ein, tax_period, form_type, program_accomplishments, source_file)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (ein, tax_period, form_type) DO UPDATE SET
                program_accomplishments = EXCLUDED.program_accomplishments
        """,
            (ein, tax_period, form_type, text[:5000], source),
        )
        conn.commit()
