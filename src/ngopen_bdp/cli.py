"""Single command-line entry point for every NGOpen BDP pipeline.

Replaces the three incompatible flag conventions of the legacy scripts
(``--host``, ``--db-host``, ``--sam-db-host``) with one surface.  Connection
details are never flags: they come from ``ngopen.toml``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Callable

from . import log
from .config import DATASETS, Config, ConfigError, load_config
from .stages import STAGE_NAMES, Pipeline

PipelineFactory = Callable[[], Pipeline]


def _registry() -> dict[str, PipelineFactory]:
    """Lazy import so a broken pipeline module cannot break the whole CLI."""

    def _load(name: str) -> PipelineFactory:
        def factory() -> Pipeline:
            import importlib

            module = importlib.import_module(f"pipelines.{name}.pipeline")
            return module.build()

        return factory

    return {name: _load(name) for name in DATASETS}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ngopen",
        description="Run NGOpen BDP ETL pipelines.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  ngopen run usaspending                  # full run, resumes where it stopped\n"
            "  ngopen run usaspending --variant subset # small archive, for validation\n"
            "  ngopen run samer --only 05_geocode      # one stage\n"
            "  ngopen run irs_ng --start-at 04_index   # resume from a stage\n"
            "  ngopen status usaspending               # per-stage ledger state\n"
            "  ngopen reset usaspending --stage 05_geocode\n"
        ),
    )
    parser.add_argument("--config", help="Path to ngopen.toml (default: search order).")
    parser.add_argument("-v", "--verbose", action="store_true")

    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="Run a pipeline.")
    run.add_argument("dataset", choices=DATASETS)
    run.add_argument("--only", choices=STAGE_NAMES, help="Run exactly one stage.")
    run.add_argument("--start-at", choices=STAGE_NAMES, help="Resume from this stage.")
    run.add_argument(
        "--force",
        action="store_true",
        help="Re-run stages already marked completed in the ledger.",
    )
    run.add_argument(
        "--dry-run", action="store_true", help="Report intent, change nothing."
    )
    run.add_argument("--limit", type=int, help="Cap rows/files processed (testing).")
    run.add_argument(
        "--variant",
        help="Source variant, e.g. 'full' or 'subset' for usaspending.",
    )
    run.add_argument(
        "--dbname",
        help="Override the target database. Use for validation runs only.",
    )

    status = sub.add_parser("status", help="Show ledger state per stage.")
    status.add_argument("dataset", choices=DATASETS)
    status.add_argument("--dbname")

    reset = sub.add_parser("reset", help="Clear ledger rows so stages re-run.")
    reset.add_argument("dataset", choices=DATASETS)
    reset.add_argument("--stage", choices=STAGE_NAMES, help="Default: all stages.")
    reset.add_argument("--dbname")

    compare = sub.add_parser(
        "compare",
        help="Diff two databases structurally (gate) and by content (advisory).",
    )
    compare.add_argument("dataset", choices=DATASETS)
    compare.add_argument(
        "--left",
        help="Reference database. Default: the serving database for this dataset.",
    )
    compare.add_argument("--right", required=True, help="Candidate database.")
    compare.add_argument(
        "--schema",
        action="append",
        help="Schema to compare (repeatable). Default: public.",
    )
    compare.add_argument(
        "--no-content",
        action="store_true",
        help="Skip the advisory row-count section.",
    )
    compare.add_argument("--out", help="Write the markdown report here.")
    compare.add_argument(
        "--json", dest="as_json", action="store_true", help="Emit JSON, not markdown."
    )

    sub.add_parser("stages", help="List the canonical stage sequence.")
    sub.add_parser("config", help="Show the resolved configuration file path.")

    return parser


def _pipeline(dataset: str) -> Pipeline:
    factory = _registry()[dataset]
    return factory()


def _cmd_run(cfg: Config, args: argparse.Namespace) -> int:
    pipeline = _pipeline(args.dataset)
    return pipeline.run(
        cfg,
        only=[args.only] if args.only else None,
        start_at=args.start_at,
        force=args.force,
        dry_run=args.dry_run,
        limit=args.limit,
        variant=args.variant,
        dbname=args.dbname,
    )


def _cmd_status(cfg: Config, args: argparse.Namespace) -> int:
    pipeline = _pipeline(args.dataset)
    target = pipeline.resolve_dbname(cfg, args.dbname)
    print(f"{args.dataset}  ->  {target}")
    for stage, status in pipeline.status(cfg, args.dbname):
        print(f"  {stage:<12} {status}")
    return 0


def _cmd_reset(cfg: Config, args: argparse.Namespace) -> int:
    from .ledger import Ledger

    pipeline = _pipeline(args.dataset)
    dbname = pipeline.resolve_dbname(cfg, args.dbname)
    ledger = Ledger(cfg, dbname, args.dataset)
    ledger.ensure()
    removed = ledger.reset(args.stage)
    target = args.stage or "all stages"
    print(f"reset {target} for {args.dataset} ({removed} ledger rows removed)")
    return 0


def _cmd_compare(cfg: Config, args: argparse.Namespace) -> int:
    import json as _json

    from . import compare as cmp

    left = args.left or cfg.dbname(args.dataset)
    schemas = args.schema or ["public"]

    result = cmp.compare(cfg, left, args.right, schemas, content=not args.no_content)

    if args.as_json:
        rendered = _json.dumps(cmp.render_json(result), indent=2) + "\n"
    else:
        rendered = cmp.render_markdown(result, title=args.dataset)

    if args.out:
        Path(args.out).write_text(rendered, encoding="utf-8")
        print(f"wrote {args.out}", file=sys.stderr)
    else:
        print(rendered, end="")

    # Structural drift is a gate: a non-zero exit lets callers script on it.
    return 0 if result.structurally_clean else 1


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "stages":
        for name in STAGE_NAMES:
            print(name)
        return 0

    try:
        cfg = load_config(args.config)
    except ConfigError as exc:
        print(f"config error: {exc}", file=sys.stderr)
        return 2

    if args.command == "config":
        print(cfg.path)
        return 0

    log.setup(cfg, args.dataset, verbose=args.verbose)

    try:
        if args.command == "run":
            return _cmd_run(cfg, args)
        if args.command == "status":
            return _cmd_status(cfg, args)
        if args.command == "reset":
            return _cmd_reset(cfg, args)
        if args.command == "compare":
            return _cmd_compare(cfg, args)
    except ConfigError as exc:
        print(f"config error: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print(
            "\ninterrupted; rerun to resume from the last completed stage",
            file=sys.stderr,
        )
        return 130

    parser.error(f"unknown command {args.command!r}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
