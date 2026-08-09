"""One logging setup for every pipeline.

The old ngopen scripts had five different approaches: bare print, file-only at
ERROR, file plus stdout at INFO, a module-import-time basicConfig at WARNING,
and a rich dashboard. This replaces all of them.

Logs go to stdout and to ``<paths.logs>/<dataset>.log`` simultaneously. Level
is INFO by default, DEBUG with ``--verbose``.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from .config import Config

FORMAT = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"
DATEFMT = "%Y-%m-%d %H:%M:%S"


def setup(cfg: Config, dataset: str, *, verbose: bool = False) -> logging.Logger:
    level = logging.DEBUG if verbose else logging.INFO

    log_dir = cfg.path_for("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{dataset}.log"

    root = logging.getLogger()
    for handler in list(root.handlers):
        root.removeHandler(handler)

    formatter = logging.Formatter(FORMAT, datefmt=DATEFMT)

    stream = logging.StreamHandler(sys.stdout)
    stream.setFormatter(formatter)
    root.addHandler(stream)

    fileh = logging.FileHandler(log_file, encoding="utf-8")
    fileh.setFormatter(formatter)
    root.addHandler(fileh)

    root.setLevel(level)

    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    logger = logging.getLogger(f"ngopen.{dataset}")
    logger.debug("logging to %s", log_file)
    return logger


def get(name: str) -> logging.Logger:
    return logging.getLogger(f"ngopen.{name}")
