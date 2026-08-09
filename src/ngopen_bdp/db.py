"""Database access for NGOpen BDP pipelines.

Two layers, deliberately:

* ``psql`` / ``pg_restore`` subprocess wrappers for DDL, bulk restore and
  anything where the server-side tooling is simply better than a driver.
* ``connect()`` for row-level work, using psycopg2.

Every connection parameter comes from ``ngopen.toml``. No host, port, user or
database name is written anywhere else in this codebase.
"""

from __future__ import annotations

import subprocess
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence

from .config import Config

UNIT_SEP = "\x1f"


class DatabaseError(RuntimeError):
    """Raised when a database operation fails."""


def _base_args(cfg: Config, dbname: str) -> list[str]:
    return [
        "-h",
        cfg.db_host,
        "-p",
        str(cfg.db_port),
        "-U",
        cfg.db_superuser,
        "-d",
        dbname,
    ]


def psql(
    cfg: Config,
    dbname: str,
    sql: str,
    *,
    tuples_only: bool = True,
    on_error_stop: bool = True,
) -> list[list[str]]:
    """Run SQL through psql and return unit-separated rows."""
    args = ["psql", *_base_args(cfg, dbname)]
    if tuples_only:
        args += ["-At", "-F", UNIT_SEP]
    if on_error_stop:
        args += ["-v", "ON_ERROR_STOP=1"]
    args += ["-c", sql]

    proc = subprocess.run(args, capture_output=True, text=True)
    if proc.returncode != 0:
        raise DatabaseError(f"psql failed on {dbname}: {proc.stderr.strip()}")
    if not tuples_only:
        return []
    return [
        line.split(UNIT_SEP) for line in proc.stdout.strip().split("\n") if line.strip()
    ]


def psql_file(cfg: Config, dbname: str, path: str | Path) -> None:
    """Execute a .sql file. Stops on the first error."""
    args = [
        "psql",
        *_base_args(cfg, dbname),
        "-v",
        "ON_ERROR_STOP=1",
        "-q",
        "-f",
        str(path),
    ]
    proc = subprocess.run(args, capture_output=True, text=True)
    if proc.returncode != 0:
        raise DatabaseError(f"psql -f {path} failed on {dbname}: {proc.stderr.strip()}")


def scalar(cfg: Config, dbname: str, sql: str) -> str | None:
    rows = psql(cfg, dbname, sql)
    if not rows or not rows[0]:
        return None
    return rows[0][0]


def database_exists(cfg: Config, dbname: str) -> bool:
    rows = psql(
        cfg,
        cfg.maintenance_db,
        f"SELECT 1 FROM pg_database WHERE datname = {quote_literal(dbname)}",
    )
    return bool(rows)


def create_database(cfg: Config, dbname: str, *, owner: str | None = None) -> None:
    """Create a database if it does not already exist. Never drops."""
    if database_exists(cfg, dbname):
        return
    stmt = f"CREATE DATABASE {quote_ident(dbname)}"
    if owner:
        stmt += f" OWNER {quote_ident(owner)}"
    psql(cfg, cfg.maintenance_db, stmt, tuples_only=False)


def ensure_roles(cfg: Config, roles: Iterable[str]) -> list[str]:
    """Create any missing roles named in an upstream archive's ownership metadata.

    A pg_dump archive records the owner of every object it carries. Restoring it
    into a cluster that lacks those roles aborts on the first ALTER ... OWNER TO
    statement. The alternative, --no-owner, silently rewrites ownership and
    destroys a piece of the provenance chain, so instead the roles are created
    as NOLOGIN placeholders: they own objects, they cannot authenticate.
    """
    created: list[str] = []
    for role in roles:
        exists = scalar(
            cfg,
            cfg.maintenance_db,
            f"SELECT 1 FROM pg_roles WHERE rolname = {quote_literal(role)}",
        )
        if exists:
            continue
        psql(
            cfg,
            cfg.maintenance_db,
            f"CREATE ROLE {quote_ident(role)} NOLOGIN",
            tuples_only=False,
        )
        created.append(role)
    return created


def drop_database(cfg: Config, dbname: str) -> None:
    """Drop a database. Refuses to touch any dataset target in the config."""
    protected = set(cfg.data.get("database", {}).get("targets", {}).values())
    if dbname in protected:
        raise DatabaseError(
            f"refusing to drop {dbname!r}: it is a live serving database "
            "declared in [database.targets]"
        )
    psql(
        cfg,
        cfg.maintenance_db,
        f"DROP DATABASE IF EXISTS {quote_ident(dbname)} WITH (FORCE)",
        tuples_only=False,
    )


def ensure_extensions(cfg: Config, dbname: str, extensions: Sequence[str]) -> None:
    for ext in extensions:
        psql(
            cfg,
            dbname,
            f"CREATE EXTENSION IF NOT EXISTS {quote_ident(ext)}",
            tuples_only=False,
        )


def quote_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def quote_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def pg_restore(
    cfg: Config,
    dbname: str,
    dump_dir: str | Path,
    *,
    use_list: str | Path | None = None,
    jobs: int | None = None,
    no_owner: bool = False,
    extra: Sequence[str] = (),
) -> None:
    """Run pg_restore against a directory-format archive."""
    args = [
        "pg_restore",
        "-h",
        cfg.db_host,
        "-p",
        str(cfg.db_port),
        "-U",
        cfg.db_superuser,
        "-d",
        dbname,
        "--jobs",
        str(jobs if jobs is not None else cfg.get("restore.jobs", 8)),
        "--verbose",
        "--exit-on-error",
    ]
    if use_list:
        args += ["--use-list", str(use_list)]
    if no_owner:
        args.append("--no-owner")
    args += list(extra)
    args.append(str(dump_dir))

    proc = subprocess.run(args, capture_output=True, text=True)
    if proc.returncode != 0:
        tail = "\n".join(proc.stderr.strip().split("\n")[-20:])
        raise DatabaseError(f"pg_restore failed on {dbname}:\n{tail}")


def pg_restore_list(dump_dir: str | Path) -> list[str]:
    """Return the archive table of contents as lines."""
    proc = subprocess.run(
        ["pg_restore", "--list", str(dump_dir)], capture_output=True, text=True
    )
    if proc.returncode != 0:
        raise DatabaseError(f"pg_restore --list failed: {proc.stderr.strip()}")
    return proc.stdout.split("\n")


def apply_session_tuning(cfg: Config, dbname: str) -> None:
    """Apply restore-oriented settings for the current database."""
    mwm = cfg.get("restore.maintenance_work_mem", "2GB")
    workers = cfg.get("restore.max_parallel_maintenance_workers", 4)
    psql(
        cfg,
        dbname,
        f"ALTER DATABASE {quote_ident(dbname)} SET maintenance_work_mem = '{mwm}';"
        f"ALTER DATABASE {quote_ident(dbname)} SET max_parallel_maintenance_workers = {int(workers)};",
        tuples_only=False,
    )


@contextmanager
def connect(cfg: Config, dbname: str, *, autocommit: bool = False) -> Iterator[Any]:
    """Yield a psycopg2 connection, committing on clean exit."""
    try:
        import psycopg2
    except ImportError as exc:  # pragma: no cover
        raise DatabaseError(
            "psycopg2 is required for row-level work: pip install psycopg2-binary"
        ) from exc

    conn = psycopg2.connect(
        dbname=dbname,
        host=cfg.db_host,
        port=cfg.db_port,
        user=cfg.db_superuser,
    )
    conn.autocommit = autocommit
    try:
        yield conn
        if not autocommit:
            conn.commit()
    except Exception:
        if not autocommit:
            conn.rollback()
        raise
    finally:
        conn.close()


def pool(cfg: Config, dbname: str, minconn: int = 4, maxconn: int = 50) -> Any:
    """Return a ThreadedConnectionPool for the geocoding stage."""
    try:
        from psycopg2 import pool as pgpool
    except ImportError as exc:  # pragma: no cover
        raise DatabaseError(
            "psycopg2 is required for pooled work: pip install psycopg2-binary"
        ) from exc

    return pgpool.ThreadedConnectionPool(
        minconn,
        maxconn,
        dbname=dbname,
        host=cfg.db_host,
        port=cfg.db_port,
        user=cfg.db_superuser,
    )
