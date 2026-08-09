"""One geocoder for all five datasets.

The old codebase had three incompatible implementations: an asyncio batch
loop, an asyncio producer/consumer queue, and a thread pool over
``requests``. They disagreed on the status column name, the status values,
whether a geometry was written at all, and the batch size.

This is the single implementation. Notable decisions:

**Freetext only.** The Photon instance at the configured endpoint returns
HTTP 400 for structured queries (``?street=&city=&state=``). A stub in the
old ``geocode_sam.py`` said as much while its docstring claimed otherwise.
Verified against the live service: freetext works, structured does not.

**Endpoints are health-checked at startup.** Dead endpoints are dropped
rather than left to stall every Nth request. If none respond, the stage
fails loudly instead of silently writing nothing.

**Resumable by cursor.** Work is pulled in id-ordered batches with a
persisted high-water mark, so a crash costs at most one batch.

**Uniform output contract.** Every table gets ``latitude``, ``longitude``,
``geom_point GEOMETRY(Point, 4326)``, ``geocode_date TIMESTAMPTZ`` and
``geocode_system VARCHAR(50)``. The old ``geocoding_source`` column name used
by irs_ng is retired.
"""

from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

from .config import Config
from .log import get

SYSTEM_OK = "photon"
SYSTEM_FAILED = "photon_failed"
SYSTEM_NO_ADDRESS = "no_address"

STREET_ABBREVS = {
    "STREET": "ST",
    "AVENUE": "AVE",
    "BOULEVARD": "BLVD",
    "DRIVE": "DR",
    "ROAD": "RD",
    "LANE": "LN",
    "COURT": "CT",
    "CIRCLE": "CIR",
    "PLACE": "PL",
    "PARKWAY": "PKWY",
    "HIGHWAY": "HWY",
    "TERRACE": "TER",
    "TRAIL": "TRL",
    "SQUARE": "SQ",
    "NORTH": "N",
    "SOUTH": "S",
    "EAST": "E",
    "WEST": "W",
    "NORTHEAST": "NE",
    "NORTHWEST": "NW",
    "SOUTHEAST": "SE",
    "SOUTHWEST": "SW",
    "SUITE": "STE",
    "APARTMENT": "APT",
    "BUILDING": "BLDG",
    "FLOOR": "FL",
}

_PO_BOX = re.compile(r"\b(P\.?\s*O\.?\s*BOX|POST\s+OFFICE\s+BOX)\b", re.IGNORECASE)
_WS = re.compile(r"\s+")
_PUNCT = re.compile(r"[^\w\s,-]")


def clean_address(
    street: str | None,
    city: str | None = None,
    state: str | None = None,
    postal: str | None = None,
    country: str | None = None,
) -> str | None:
    """Build one freetext query string. The only address cleaner in the repo.

    Returns None when there is nothing worth sending to a geocoder. A PO box
    with no city is not an address; a city and state alone is a usable, if
    coarse, one.
    """
    parts: list[str] = []

    if street:
        s = _PUNCT.sub(" ", street.upper())
        s = _PO_BOX.sub("", s)
        s = _WS.sub(" ", s).strip(" ,-")
        if s:
            tokens = [STREET_ABBREVS.get(t, t) for t in s.split()]
            parts.append(" ".join(tokens))

    if city:
        c = _WS.sub(" ", _PUNCT.sub(" ", city.upper())).strip()
        if c:
            parts.append(c)

    if state:
        st = state.strip().upper()
        if st:
            parts.append(st)

    if postal:
        pc = str(postal).strip()[:5]
        if pc and pc.isdigit():
            parts.append(pc)

    if country and country.strip().upper() not in ("USA", "US", "UNITED STATES", ""):
        parts.append(country.strip().upper())

    if not parts:
        return None
    if len(parts) == 1 and postal and parts[0] == str(postal).strip()[:5]:
        return None
    return ", ".join(parts)


@dataclass
class WorkItem:
    key: Any
    query: str


@dataclass
class Result:
    key: Any
    latitude: float | None
    longitude: float | None
    system: str


class PhotonClient:
    """Freetext Photon client over one or more endpoints, round-robin."""

    def __init__(self, cfg: Config) -> None:
        self.endpoints: list[str] = list(cfg.geocoder_endpoints)
        self.timeout = float(cfg.get("geocoder.timeout_seconds", 10))
        self.retry_max = int(cfg.get("geocoder.retry_max", 3))
        self.concurrency = int(cfg.get("geocoder.concurrency", 50))
        self.batch_size = int(cfg.get("geocoder.batch_size", 1000))
        self._rr = 0
        self.log = get("geocode")

    async def health_check(self, session: Any) -> list[str]:
        """Drop endpoints that do not answer. Returns the survivors."""
        alive: list[str] = []
        for url in self.endpoints:
            probe = f"{url.rstrip('/')}/api?q=washington+dc&limit=1"
            try:
                async with session.get(probe, timeout=self.timeout) as resp:
                    if resp.status == 200:
                        alive.append(url)
                        self.log.info("geocoder up: %s", url)
                    else:
                        self.log.warning(
                            "geocoder %s returned HTTP %s, dropping", url, resp.status
                        )
            except Exception as exc:
                self.log.warning("geocoder %s unreachable (%s), dropping", url, exc)
        self.endpoints = alive
        return alive

    def _next_endpoint(self) -> str:
        url = self.endpoints[self._rr % len(self.endpoints)]
        self._rr += 1
        return url

    async def geocode(self, session: Any, item: WorkItem) -> Result:
        import aiohttp

        for attempt in range(self.retry_max):
            url = f"{self._next_endpoint().rstrip('/')}/api"
            try:
                async with session.get(
                    url,
                    params={"q": item.query, "limit": 1},
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as resp:
                    if resp.status != 200:
                        continue
                    payload = await resp.json()
            except Exception:
                if attempt == self.retry_max - 1:
                    return Result(item.key, None, None, SYSTEM_FAILED)
                await asyncio.sleep(0.25 * (attempt + 1))
                continue

            features = payload.get("features") or []
            if not features:
                return Result(item.key, None, None, SYSTEM_FAILED)
            coords = (features[0].get("geometry") or {}).get("coordinates")
            if not coords or len(coords) < 2:
                return Result(item.key, None, None, SYSTEM_FAILED)
            return Result(item.key, float(coords[1]), float(coords[0]), SYSTEM_OK)

        return Result(item.key, None, None, SYSTEM_FAILED)

    async def geocode_batch(self, items: Sequence[WorkItem]) -> list[Result]:
        import aiohttp

        if not items:
            return []
        connector = aiohttp.TCPConnector(limit=self.concurrency)
        async with aiohttp.ClientSession(connector=connector) as session:
            if not await self.health_check(session):
                raise RuntimeError(
                    "no geocoder endpoints responded; check [geocoder].endpoints "
                    "in ngopen.toml"
                )
            sem = asyncio.Semaphore(self.concurrency)

            async def bounded(it: WorkItem) -> Result:
                async with sem:
                    return await self.geocode(session, it)

            return list(await asyncio.gather(*(bounded(i) for i in items)))


def run_batch(cfg: Config, items: Sequence[WorkItem]) -> list[Result]:
    """Synchronous entry point for a single batch."""
    client = PhotonClient(cfg)
    return asyncio.run(client.geocode_batch(items))


GEOCODE_COLUMNS_SQL = """
ALTER TABLE {table}
    ADD COLUMN IF NOT EXISTS latitude       NUMERIC(10, 8),
    ADD COLUMN IF NOT EXISTS longitude      NUMERIC(11, 8),
    ADD COLUMN IF NOT EXISTS geom_point     GEOMETRY(Point, 4326),
    ADD COLUMN IF NOT EXISTS geocode_date   TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS geocode_system VARCHAR(50);
"""


def geocode_columns_ddl(table: str) -> str:
    return GEOCODE_COLUMNS_SQL.format(table=table)


class Cursor:
    """Persisted high-water mark so a crash costs at most one batch."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.data: dict[str, Any] = {}
        if path.exists():
            try:
                self.data = json.loads(path.read_text())
            except json.JSONDecodeError:
                self.data = {}

    def get(self, key: str, default: Any = 0) -> Any:
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.data[key] = value
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.data, indent=2))
        tmp.replace(self.path)

    def clear(self, key: str) -> None:
        self.data.pop(key, None)
        if self.path.exists():
            self.path.write_text(json.dumps(self.data, indent=2))


_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)?$")


def _check_ident(value: str, what: str) -> str:
    if not _IDENT_RE.match(value):
        raise ValueError(f"unsafe {what}: {value!r}")
    return value


def write_results(
    conn: Any,
    table: str,
    key_column: str,
    results: Iterable[Result],
    insert: bool = False,
) -> int:
    """Write geocode results back with parameterized SQL.

    The old ``geocode_usas.write_results_batch`` built its VALUES clause by
    f-string concatenation of raw values. That is fixed here permanently:
    every value is bound, and the two identifiers are pattern-checked.

    ``insert=True`` upserts into a side index table (the recipient geocode
    index pattern); the default updates the source table in place.
    """
    from psycopg2.extras import execute_batch

    _check_ident(table, "table name")
    _check_ident(key_column, "column name")

    rows = list(results)
    if not rows:
        return 0

    point = (
        "CASE WHEN %s IS NOT NULL AND %s IS NOT NULL "
        "THEN ST_SetSRID(ST_MakePoint(%s, %s), 4326) ELSE NULL END"
    )

    if insert:
        sql = f"""
            INSERT INTO {table}
                ({key_column}, latitude, longitude, geom_point,
                 geocode_date, geocode_system)
            VALUES (%s, %s, %s, {point}, now(), %s)
            ON CONFLICT ({key_column}) DO UPDATE SET
                latitude       = EXCLUDED.latitude,
                longitude      = EXCLUDED.longitude,
                geom_point     = EXCLUDED.geom_point,
                geocode_date   = EXCLUDED.geocode_date,
                geocode_system = EXCLUDED.geocode_system
        """
        params = [
            (
                r.key,
                r.latitude,
                r.longitude,
                r.latitude,
                r.longitude,
                r.longitude,
                r.latitude,
                r.system,
            )
            for r in rows
        ]
    else:
        sql = f"""
            UPDATE {table} SET
                latitude       = %s,
                longitude      = %s,
                geom_point     = {point},
                geocode_date   = now(),
                geocode_system = %s
            WHERE {key_column} = %s
        """
        params = [
            (
                r.latitude,
                r.longitude,
                r.latitude,
                r.longitude,
                r.longitude,
                r.latitude,
                r.system,
                r.key,
            )
            for r in rows
        ]

    with conn.cursor() as cur:
        execute_batch(cur, sql, params, page_size=500)
    return len(params)
