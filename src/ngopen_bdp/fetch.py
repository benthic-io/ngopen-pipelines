"""Resumable HTTP fetching and artifact bookkeeping.

Downloads are the first thing that breaks on a multi-hour ETL run, so every
fetch here is restartable (HTTP Range), verified by size, and recorded in a
per-dataset JSON ledger so a rerun can tell "already have it" from "source
published a newer file".
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .log import get

USER_AGENT = "ngopen-bdp/1.0 (+https://benthic.io/bdp/)"
CHUNK = 1 << 20


class FetchError(RuntimeError):
    pass


@dataclass
class Artifact:
    """One downloaded file, as recorded in the artifact ledger."""

    name: str
    url: str
    path: str
    size: int
    sha256: str | None
    fetched_at: str
    remote_last_modified: str | None = None


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def get_json(url: str, timeout: int = 60) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def head(url: str, timeout: int = 60) -> dict[str, str]:
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return {k.lower(): v for k, v in resp.headers.items()}


def sha256_file(path: Path, chunk: int = CHUNK) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            block = fh.read(chunk)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def _content_length(url: str) -> int | None:
    try:
        value = head(url).get("content-length")
        return int(value) if value else None
    except Exception:
        return None


def download(
    url: str,
    dest: Path,
    *,
    dataset: str = "fetch",
    expected_size: int | None = None,
    resume: bool = True,
    timeout: int = 120,
) -> Path:
    """Download ``url`` to ``dest``, resuming a partial file when possible.

    Prefers ``aria2c`` for large multi-gigabyte archives when it is present,
    since it parallelises and resumes far better than urllib. Falls back to a
    plain ranged GET otherwise.
    """

    log = get(dataset)
    dest.parent.mkdir(parents=True, exist_ok=True)
    remote_size = expected_size if expected_size is not None else _content_length(url)

    if dest.exists() and remote_size and dest.stat().st_size == remote_size:
        log.info("already have %s (%d bytes)", dest.name, remote_size)
        return dest

    if shutil.which("aria2c") and (remote_size or 0) > (256 << 20):
        log.info("fetching %s via aria2c", dest.name)
        cmd = [
            "aria2c",
            "--continue=true",
            "--max-connection-per-server=8",
            "--split=8",
            "--min-split-size=64M",
            "--file-allocation=none",
            "--summary-interval=60",
            f"--user-agent={USER_AGENT}",
            "--dir",
            str(dest.parent),
            "--out",
            dest.name,
            url,
        ]
        result = subprocess.run(cmd)
        if result.returncode != 0:
            raise FetchError(f"aria2c failed for {url} (exit {result.returncode})")
        return dest

    part = dest.with_suffix(dest.suffix + ".part")
    offset = part.stat().st_size if (resume and part.exists()) else 0
    headers = {"User-Agent": USER_AGENT}
    if offset:
        headers["Range"] = f"bytes={offset}-"
        log.info("resuming %s at %d bytes", dest.name, offset)
    else:
        log.info("fetching %s", dest.name)

    req = urllib.request.Request(url, headers=headers)
    mode = "ab" if offset else "wb"
    with urllib.request.urlopen(req, timeout=timeout) as resp, part.open(mode) as fh:
        while True:
            block = resp.read(CHUNK)
            if not block:
                break
            fh.write(block)

    if remote_size and part.stat().st_size != remote_size:
        raise FetchError(
            f"{dest.name}: got {part.stat().st_size} bytes, expected {remote_size}"
        )
    os.replace(part, dest)
    return dest


class ArtifactLedger:
    """JSON record of what was fetched, so reruns can detect new releases."""

    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._data: dict[str, dict] = {}
        if self.path.exists():
            try:
                self._data = json.loads(self.path.read_text())
            except json.JSONDecodeError:
                self._data = {}

    def get(self, name: str) -> Artifact | None:
        raw = self._data.get(name)
        return Artifact(**raw) if raw else None

    def record(
        self,
        name: str,
        url: str,
        path: Path,
        *,
        checksum: bool = False,
        remote_last_modified: str | None = None,
    ) -> Artifact:
        artifact = Artifact(
            name=name,
            url=url,
            path=str(path),
            size=path.stat().st_size,
            sha256=sha256_file(path) if checksum else None,
            fetched_at=_now(),
            remote_last_modified=remote_last_modified,
        )
        self._data[name] = asdict(artifact)
        self.save()
        return artifact

    def has_current(self, name: str, url: str, size: int | None) -> bool:
        existing = self.get(name)
        if not existing:
            return False
        if existing.url != url:
            return False
        if not Path(existing.path).exists():
            return False
        if size is not None and existing.size != size:
            return False
        return True

    def all(self) -> list[Artifact]:
        return [Artifact(**raw) for raw in self._data.values()]

    def save(self) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._data, indent=2, sort_keys=True) + "\n")
        os.replace(tmp, self.path)
