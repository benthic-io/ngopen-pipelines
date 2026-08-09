"""Central configuration loader for the NGOpen BDP pipelines.

Every path, database name, endpoint and tuning knob used anywhere in this
repository is resolved through this module. Nothing else may hardcode them.
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CONFIG_ENV = "NGOPEN_CONFIG"
CONFIG_NAME = "ngopen.toml"

DATASETS = ("usaspending", "samer", "irs_ng", "usp_cl", "up_cdmaps")

_MISSING = object()


class ConfigError(RuntimeError):
    pass


def _candidates(explicit: str | Path | None) -> list[Path]:
    out: list[Path] = []
    if explicit:
        out.append(Path(explicit).expanduser())
    env = os.environ.get(CONFIG_ENV)
    if env:
        out.append(Path(env).expanduser())
    out.append(Path.cwd() / CONFIG_NAME)
    out.append(Path(__file__).resolve().parents[2] / CONFIG_NAME)
    out.append(Path.home() / ".config" / "ngopen" / CONFIG_NAME)
    return out


@dataclass(frozen=True)
class Config:
    path: Path
    data: dict[str, Any]

    # ---- generic access -------------------------------------------------

    def get(self, dotted: str, default: Any = _MISSING) -> Any:
        node: Any = self.data
        for part in dotted.split("."):
            if not isinstance(node, dict) or part not in node:
                if default is _MISSING:
                    raise ConfigError(f"{self.path}: missing key '{dotted}'")
                return default
            node = node[part]
        return node

    # ---- paths ----------------------------------------------------------

    def path_for(self, name: str) -> Path:
        return Path(self.get(f"paths.{name}")).expanduser()

    def dataset_dir(self, kind: str, dataset: str) -> Path:
        return self.path_for(kind) / dataset

    def ensure_dirs(self, dataset: str | None = None) -> None:
        for name in ("root", "archives", "work", "logs", "state"):
            self.path_for(name).mkdir(parents=True, exist_ok=True)
        if dataset:
            for name in ("archives", "work", "logs", "state"):
                self.dataset_dir(name, dataset).mkdir(parents=True, exist_ok=True)

    # ---- database -------------------------------------------------------

    def dbname(self, dataset: str) -> str:
        return self.get(f"database.targets.{dataset}")

    @property
    def db_host(self) -> str:
        return self.get("database.host")

    @property
    def db_port(self) -> int:
        return int(self.get("database.port"))

    @property
    def db_superuser(self) -> str:
        return self.get("database.superuser")

    @property
    def maintenance_db(self) -> str:
        return self.get("database.maintenance_db")

    def role(self, which: str) -> str:
        return self.get(f"database.roles.{which}")

    # ---- misc -----------------------------------------------------------

    @property
    def geocoder_endpoints(self) -> list[str]:
        return list(self.get("geocoder.endpoints"))

    def postgrest_port(self, dataset: str) -> int:
        return int(self.get(f"postgrest.ports.{dataset}"))

    def postgrest_url(self, dataset: str) -> str:
        base = str(self.get("postgrest.base_url")).rstrip("/")
        return f"{base}/{dataset}/"

    def source(self, dataset: str) -> dict[str, Any]:
        return dict(self.get(f"sources.{dataset}", {}))

    def secret(self, env_name: str) -> str | None:
        value = os.environ.get(env_name)
        return value or None


def load_config(explicit: str | Path | None = None) -> Config:
    tried: list[Path] = []
    for candidate in _candidates(explicit):
        tried.append(candidate)
        if candidate.is_file():
            with candidate.open("rb") as fh:
                return Config(path=candidate.resolve(), data=tomllib.load(fh))
    listing = "\n  ".join(str(p) for p in tried)
    raise ConfigError(f"no {CONFIG_NAME} found. Looked in:\n  {listing}")
