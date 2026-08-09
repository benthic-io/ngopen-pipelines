"""The stage contract shared by all five pipelines.

Every dataset implements the same ordered sequence. A stage that does not
apply to a dataset returns ``SKIPPED`` rather than being omitted, so the
ledger reads identically across pipelines and an auditor can see at a glance
that, say, ``samer`` has no restore step because its source is a flat file.

    00_acquire   fetch source artifacts to <paths.archives>/<dataset>/
    01_verify    checksum and shape-check what was fetched
    02_restore   load raw source into Postgres (pg_restore, COPY, parsers)
    03_schema    extensions, tables, columns, constraints
    04_index     indexes, coded and recovered
    05_geocode   Photon freetext geocoding, resumable
    06_derive    materialized views and derived relations
    07_analyze   ANALYZE and matview refresh
    08_expose    grants for the PostgREST role

Stages are idempotent. Rerunning a completed pipeline performs a refresh, not
a rebuild: 00 re-checks the source for a newer artifact, and everything
downstream reacts to whether 00 found one.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Sequence

from .config import Config
from .ledger import Ledger, StageTimer
from .log import get

STAGE_NAMES: tuple[str, ...] = (
    "00_acquire",
    "01_verify",
    "02_restore",
    "03_schema",
    "04_index",
    "05_geocode",
    "06_derive",
    "07_analyze",
    "08_expose",
)


class Outcome(Enum):
    COMPLETED = "completed"
    SKIPPED = "skipped"


@dataclass
class Context:
    """Everything a stage function is given."""

    cfg: Config
    dataset: str
    dbname: str
    ledger: Ledger
    force: bool = False
    dry_run: bool = False
    limit: int | None = None
    variant: str | None = None
    shared: dict = field(default_factory=dict)

    @property
    def archives(self):
        return self.cfg.dataset_dir("archives", self.dataset)

    @property
    def work(self):
        return self.cfg.dataset_dir("work", self.dataset)

    @property
    def state(self):
        return self.cfg.dataset_dir("state", self.dataset)

    @property
    def log(self):
        return get(self.dataset)


StageFn = Callable[[Context], Outcome | None]


@dataclass
class Pipeline:
    """An ordered, ledger-aware sequence of stages for one dataset."""

    dataset: str
    stages: dict[str, StageFn]
    dbname: str | None = None
    description: str = ""

    def resolve_dbname(self, cfg: Config, override: str | None = None) -> str:
        """Database name comes from ngopen.toml unless explicitly overridden.

        The override exists for validation runs, which restore into a throwaway
        database and must never touch the serving one.
        """
        return override or self.dbname or cfg.dbname(self.dataset)

    def stage_order(self) -> tuple[str, ...]:
        unknown = set(self.stages) - set(STAGE_NAMES)
        if unknown:
            raise ValueError(f"{self.dataset}: unknown stages {sorted(unknown)}")
        return tuple(name for name in STAGE_NAMES if name in self.stages)

    def run(
        self,
        cfg: Config,
        *,
        only: Sequence[str] | None = None,
        start_at: str | None = None,
        force: bool = False,
        dry_run: bool = False,
        limit: int | None = None,
        variant: str | None = None,
        dbname: str | None = None,
    ) -> int:
        log = get(self.dataset)
        target = self.resolve_dbname(cfg, dbname)
        ledger = Ledger(cfg, target, self.dataset)
        ledger.ensure()

        stale = ledger.clear_stale()
        if stale:
            log.warning(
                "%d stage(s) were left 'running' by a previous crash; marked failed",
                stale,
            )

        ctx = Context(
            cfg=cfg,
            dataset=self.dataset,
            dbname=target,
            ledger=ledger,
            force=force,
            dry_run=dry_run,
            limit=limit,
            variant=variant,
        )
        cfg.ensure_dirs(self.dataset)

        order = list(self.stage_order())
        if start_at:
            if start_at not in order:
                log.error("unknown start stage %s", start_at)
                return 2
            order = order[order.index(start_at) :]
        if only:
            missing = [s for s in only if s not in self.stages]
            if missing:
                log.error("unknown stage(s): %s", ", ".join(missing))
                return 2
            order = [s for s in order if s in set(only)]

        for name in order:
            if not force and ledger.is_completed(name):
                log.info("%s already completed, skipping (use --force to rerun)", name)
                continue

            fn = self.stages[name]
            log.info("--- %s ---", name)
            if dry_run:
                log.info("%s: dry run, not executing", name)
                continue

            try:
                with StageTimer(ledger, name) as timer:
                    ctx.shared["timer"] = timer
                    result = fn(ctx)
                    if result is Outcome.SKIPPED:
                        timer.note(skipped=True)
            except Exception as exc:
                log.error("%s FAILED: %s", name, exc)
                log.error("pipeline halted; rerun to resume from this stage")
                return 1

            log.info("%s ok", name)

        log.info("pipeline %s finished", self.dataset)
        return 0

    def status(self, cfg: Config, dbname: str | None = None) -> list[tuple[str, str]]:
        ledger = Ledger(cfg, self.resolve_dbname(cfg, dbname), self.dataset)
        rows: list[tuple[str, str]] = []
        for name in self.stage_order():
            try:
                rows.append((name, ledger.last_status(name) or "-"))
            except Exception:
                rows.append((name, "?"))
        return rows
