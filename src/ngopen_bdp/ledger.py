"""Crash-recoverable run ledger.

Every pipeline stage records its own start, finish and failure into a table
that lives inside the target database itself. That placement is deliberate:
if the database is gone, the ledger is gone too, and a fresh run is exactly
what you want. If the database survives a crash, the ledger survives with it
and the pipeline resumes at the first stage that did not reach ``completed``.

Stages are expected to be individually idempotent. The ledger decides *what*
to skip; it never tries to undo partial work.
"""

from __future__ import annotations

import json
import os
import socket
import time
from dataclasses import dataclass
from typing import Any

from .config import Config
from .db import connect, create_database, psql, quote_literal

LEDGER_SCHEMA = "bdp_meta"
LEDGER_TABLE = "run_ledger"

DDL = f"""
CREATE SCHEMA IF NOT EXISTS {LEDGER_SCHEMA};

CREATE TABLE IF NOT EXISTS {LEDGER_SCHEMA}.{LEDGER_TABLE} (
    id            BIGSERIAL PRIMARY KEY,
    dataset       TEXT        NOT NULL,
    stage         TEXT        NOT NULL,
    status        TEXT        NOT NULL
                  CHECK (status IN ('running', 'completed', 'failed', 'skipped')),
    started_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at   TIMESTAMPTZ,
    duration_s    DOUBLE PRECISION,
    host          TEXT,
    pid           INTEGER,
    detail        JSONB       NOT NULL DEFAULT '{{}}'::jsonb,
    error         TEXT
);

CREATE INDEX IF NOT EXISTS idx_run_ledger_dataset_stage
    ON {LEDGER_SCHEMA}.{LEDGER_TABLE} (dataset, stage, started_at DESC);

CREATE INDEX IF NOT EXISTS idx_run_ledger_status
    ON {LEDGER_SCHEMA}.{LEDGER_TABLE} (status)
    WHERE status <> 'completed';
"""


@dataclass
class StageRecord:
    stage: str
    status: str
    started_at: str
    finished_at: str | None
    duration_s: float | None
    detail: dict[str, Any]
    error: str | None


class Ledger:
    """Records stage outcomes inside the target database."""

    def __init__(self, cfg: Config, dbname: str, dataset: str) -> None:
        self.cfg = cfg
        self.dbname = dbname
        self.dataset = dataset

    def ensure(self) -> None:
        """Create the ledger schema and table. Safe to call repeatedly."""
        create_database(self.cfg, self.dbname)
        psql(self.cfg, self.dbname, DDL, tuples_only=False)

    def last_status(self, stage: str) -> str | None:
        rows = psql(
            self.cfg,
            self.dbname,
            f"SELECT status FROM {LEDGER_SCHEMA}.{LEDGER_TABLE} "
            f"WHERE dataset = {quote_literal(self.dataset)} "
            f"AND stage = {quote_literal(stage)} "
            "ORDER BY started_at DESC LIMIT 1",
        )
        return rows[0][0] if rows else None

    def is_completed(self, stage: str) -> bool:
        return self.last_status(stage) == "completed"

    def history(self) -> list[StageRecord]:
        rows = psql(
            self.cfg,
            self.dbname,
            "SELECT stage, status, started_at, "
            "coalesce(finished_at::text, ''), coalesce(duration_s::text, ''), "
            "detail::text, coalesce(error, '') "
            f"FROM {LEDGER_SCHEMA}.{LEDGER_TABLE} "
            f"WHERE dataset = {quote_literal(self.dataset)} "
            "ORDER BY started_at",
        )
        out: list[StageRecord] = []
        for r in rows:
            if len(r) < 7:
                continue
            out.append(
                StageRecord(
                    stage=r[0],
                    status=r[1],
                    started_at=r[2],
                    finished_at=r[3] or None,
                    duration_s=float(r[4]) if r[4] else None,
                    detail=json.loads(r[5]) if r[5] else {},
                    error=r[6] or None,
                )
            )
        return out

    def start(self, stage: str) -> int:
        with connect(self.cfg, self.dbname, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"INSERT INTO {LEDGER_SCHEMA}.{LEDGER_TABLE} "
                    "(dataset, stage, status, host, pid) "
                    "VALUES (%s, %s, 'running', %s, %s) RETURNING id",
                    (self.dataset, stage, socket.gethostname(), os.getpid()),
                )
                row = cur.fetchone()
                return int(row[0]) if row else -1

    def finish(
        self,
        run_id: int,
        status: str,
        *,
        detail: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        with connect(self.cfg, self.dbname, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"UPDATE {LEDGER_SCHEMA}.{LEDGER_TABLE} SET "
                    "status = %s, finished_at = now(), "
                    "duration_s = EXTRACT(EPOCH FROM (now() - started_at)), "
                    "detail = %s::jsonb, error = %s WHERE id = %s",
                    (status, json.dumps(detail or {}), error, run_id),
                )

    def reset(self, stage: str | None = None) -> None:
        """Mark stages as needing a rerun by deleting their ledger rows."""
        where = f"dataset = {quote_literal(self.dataset)}"
        if stage:
            where += f" AND stage = {quote_literal(stage)}"
        psql(
            self.cfg,
            self.dbname,
            f"DELETE FROM {LEDGER_SCHEMA}.{LEDGER_TABLE} WHERE {where}",
            tuples_only=False,
        )

    def clear_stale(self) -> int:
        """Fail any 'running' rows left behind by a crashed process."""
        rows = psql(
            self.cfg,
            self.dbname,
            f"UPDATE {LEDGER_SCHEMA}.{LEDGER_TABLE} SET status = 'failed', "
            "finished_at = now(), error = 'process died without recording an outcome' "
            f"WHERE dataset = {quote_literal(self.dataset)} AND status = 'running' "
            "RETURNING id",
        )
        return len(rows)


class StageTimer:
    """Context manager wrapping one ledger-tracked stage execution."""

    def __init__(self, ledger: Ledger, stage: str) -> None:
        self.ledger = ledger
        self.stage = stage
        self.detail: dict[str, Any] = {}
        self.run_id = -1
        self._t0 = 0.0

    def __enter__(self) -> "StageTimer":
        self.run_id = self.ledger.start(self.stage)
        self._t0 = time.monotonic()
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        elapsed = time.monotonic() - self._t0
        self.detail.setdefault("elapsed_s", round(elapsed, 3))
        if exc is None:
            self.ledger.finish(self.run_id, "completed", detail=self.detail)
        else:
            self.ledger.finish(
                self.run_id,
                "failed",
                detail=self.detail,
                error=f"{exc_type.__name__}: {exc}",
            )
        return False

    def note(self, **kwargs: Any) -> None:
        self.detail.update(kwargs)
