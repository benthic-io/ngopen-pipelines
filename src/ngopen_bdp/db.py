"""Database access for NGOpen BDP pipelines.

Two layers, deliberately:

* ``psql`` / ``pg_restore`` subprocess wrappers for DDL, bulk restore and
  anything where the server-side tooling is simply better than a driver.
* ``connect()`` for row-level work, using psycopg2.

Every connection parameter comes from ``ngopen.toml``. No host, port, user or
database name is written anywhere else in this codebase.
"""

from __future__ import annotations

import re
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import IO, Any, Iterable, Iterator, Sequence

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


def _rewrite_schema(
    source: IO[bytes],
    sink: IO[bytes],
    from_schema: str,
    to_schema: str,
    table: str,
    deferred: list[str] | None = None,
) -> None:
    """Redirect a pg_dump stream into a different schema.

    pg_dump writes fully-qualified names, so ``search_path`` cannot redirect
    them. Only the target relation and objects named after it are rewritten: a
    blanket substitution would also catch shared machinery that lives in public
    and must not move, such as operator classes like ``public.gin_trgm_ops``.

    COPY data blocks pass through untouched, because a data row containing
    ``public.`` is data, not a qualified name.

    A bare ``REFRESH MATERIALIZED VIEW`` line is dropped. pg_dump emits the
    view definition ``WITH NO DATA`` followed by a refresh, and running that
    refresh in the target database recomputes the view from whatever base
    tables happen to be there -- during a migration, the outgoing vintage.
    The staged copy's rows are loaded explicitly from the candidate database
    instead (see ``copy_matview_data``).

    When ``deferred`` is given, foreign-key statements are collected rather than
    emitted, and they are collected *before* rewriting so they name the schema
    the relations will occupy once swapped. A foreign key cannot be validated
    while the staged copy sits beside the relations it points at: the reference
    still resolves to the outgoing data, and fresh rows legitimately name
    parents that exist only in the incoming set. The caller applies them once
    the whole cluster has landed.
    """
    pattern = re.compile(
        rb"\b"
        + re.escape(from_schema.encode())
        + rb"\.("
        + re.escape(table.encode())
        + rb"\w*)"
    )
    replacement = to_schema.encode() + rb".\1"
    in_copy = False

    # pg_dump splits a constraint across two lines: the ALTER TABLE header and
    # the ADD CONSTRAINT body. The header is only recognisable as part of a
    # foreign key once the next line has been read, so it is held back.
    pending: bytes | None = None

    def flush() -> None:
        nonlocal pending
        if pending is not None:
            sink.write(pattern.sub(replacement, pending))
            pending = None

    for line in source:
        if in_copy:
            if line.rstrip(b"\r\n") == b"\\.":
                in_copy = False
            sink.write(line)
            continue

        stripped = line.lstrip()

        if stripped.startswith(b"REFRESH MATERIALIZED VIEW"):
            continue

        # A materialised view is staged as a plain table carrying the
        # candidate's rows. pg_dump emits the view definition WITH NO DATA
        # plus a refresh, and neither ships bytes: the refresh would recompute
        # from the serving schema's outgoing base tables (see copy_matview_data
        # and _populate_staged). Rewriting the shell to CREATE TABLE AS with
        # the same query WITH NO DATA yields an empty table with identical
        # columns, which COPY can then load. The served relation therefore
        # changes relkind from matview to table; that is honest -- the rows
        # are candidate bytes with no refresh promise -- and documented in
        # the migration state.
        if stripped.startswith(b"CREATE MATERIALIZED VIEW "):
            line = line.replace(b"CREATE MATERIALIZED VIEW ", b"CREATE TABLE ", 1)
        elif stripped.startswith(b"ALTER MATERIALIZED VIEW "):
            line = line.replace(b"ALTER MATERIALIZED VIEW ", b"ALTER TABLE ", 1)

        if deferred is not None:
            if pending is not None:
                if b"FOREIGN KEY" in line:
                    deferred.append((pending + line).decode("utf-8", "replace").strip())
                    pending = None
                    continue
                flush()
            if stripped.startswith(b"ALTER TABLE ") and not line.rstrip(
                b"\r\n"
            ).endswith(b";"):
                pending = line
                continue
            if b"FOREIGN KEY" in line and stripped.startswith(b"ALTER TABLE "):
                deferred.append(line.decode("utf-8", "replace").strip())
                continue

        rewritten = pattern.sub(replacement, line)
        sink.write(rewritten)

        if rewritten.lstrip().startswith(b"COPY ") and rewritten.rstrip(
            b"\r\n"
        ).endswith(b"FROM stdin;"):
            in_copy = True

    flush()


def transfer_relation(
    cfg: Config,
    source_db: str,
    target_db: str,
    relation: str,
    *,
    target_schema: str,
    defer_foreign_keys: bool = False,
) -> list[str]:
    """Stream one relation from one database into a schema of another.

    ``ALTER TABLE ... SET SCHEMA`` cannot cross a database boundary, so a
    candidate built in a separate database has to be carried into the serving
    database before it can be swapped into place. This pipes pg_dump straight
    into psql: no intermediate file, so peak disk cost is the target copy only.

    The bytes that were structurally verified in the candidate database are the
    same bytes that end up serving. Nothing is rebuilt in transit.

    Returns any foreign-key statements held back for the caller to apply.
    """
    schema, _, table = relation.rpartition(".")
    schema = schema or "public"

    psql(
        cfg,
        target_db,
        f"CREATE SCHEMA IF NOT EXISTS {quote_ident(target_schema)}",
        tuples_only=False,
    )

    dump = [
        "pg_dump",
        "-h",
        cfg.db_host,
        "-p",
        str(cfg.db_port),
        "-U",
        cfg.db_superuser,
        "-d",
        source_db,
        "--table",
        f"{schema}.{table}",
        "--no-owner",
        "--no-privileges",
        "--no-comments",
    ]
    load = [
        "psql",
        *_base_args(cfg, target_db),
        "-v",
        "ON_ERROR_STOP=1",
        "-q",
        "-f",
        "-",
    ]

    with tempfile.TemporaryFile() as dump_log, tempfile.TemporaryFile() as load_log:
        producer = subprocess.Popen(dump, stdout=subprocess.PIPE, stderr=dump_log)
        assert producer.stdout is not None
        consumer = subprocess.Popen(
            load, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=load_log
        )
        assert consumer.stdin is not None

        deferred: list[str] | None = [] if defer_foreign_keys else None
        try:
            _rewrite_schema(
                producer.stdout, consumer.stdin, schema, target_schema, table, deferred
            )
        finally:
            consumer.stdin.close()
            producer.stdout.close()

        consumer.wait()
        producer.wait()

        dump_log.seek(0)
        load_log.seek(0)
        dump_err = dump_log.read().decode(errors="replace").strip()
        load_err = load_log.read().decode(errors="replace").strip()

    if producer.returncode != 0:
        raise DatabaseError(
            f"pg_dump of {relation} from {source_db} failed: {dump_err}"
        )
    if consumer.returncode != 0:
        raise DatabaseError(
            f"loading {relation} into {target_db}.{target_schema} failed: {load_err}"
        )
    return deferred or []


def copy_matview_data(
    cfg: Config,
    source_db: str,
    target_db: str,
    relation: str,
    *,
    target_schema: str,
) -> None:
    """Carry a materialised view's rows from one database into a staged copy.

    pg_dump moves a materialised view as a definition plus a bare REFRESH, so
    the row content never crosses in the schema transfer -- and running that
    refresh would recompute the view from the *serving* base tables, i.e. the
    outgoing vintage rather than the candidate one. This streams the candidate
    rows across with COPY TO STDOUT / COPY FROM STDIN: no intermediate file,
    so peak disk cost is the target copy only.

    The staged copy is emptied first, so this is safe to re-run after a
    rollback left a previous attempt's rows behind. The staged copy is a
    plain table when the transfer filter rewrote the matview shell (see
    _rewrite_schema) and a real matview otherwise, so the emptying follows
    the live kind.
    """
    schema, _, table = relation.rpartition(".")
    schema = schema or "public"
    staged = f"{target_schema}.{table}"

    if relation_kind(cfg, target_db, staged) == "m":
        empty = f"REFRESH MATERIALIZED VIEW {quote_ident(target_schema)}.{quote_ident(table)} WITH NO DATA"
    else:
        empty = f"TRUNCATE {quote_ident(target_schema)}.{quote_ident(table)}"
    psql(cfg, target_db, empty, tuples_only=False)

    unload = [
        "psql",
        *_base_args(cfg, source_db),
        "-v",
        "ON_ERROR_STOP=1",
        "-q",
        "-c",
        f"COPY {quote_ident(schema)}.{quote_ident(table)} TO STDOUT",
    ]
    load = [
        "psql",
        *_base_args(cfg, target_db),
        "-v",
        "ON_ERROR_STOP=1",
        "-q",
        "-c",
        f"COPY {quote_ident(target_schema)}.{quote_ident(table)} FROM STDIN",
    ]

    with tempfile.TemporaryFile() as unload_log, tempfile.TemporaryFile() as load_log:
        producer = subprocess.Popen(unload, stdout=subprocess.PIPE, stderr=unload_log)
        assert producer.stdout is not None
        consumer = subprocess.Popen(
            load, stdin=producer.stdout, stdout=subprocess.DEVNULL, stderr=load_log
        )
        producer.stdout.close()

        consumer.wait()
        producer.wait()

        unload_log.seek(0)
        load_log.seek(0)
        unload_err = unload_log.read().decode(errors="replace").strip()
        load_err = load_log.read().decode(errors="replace").strip()

    if producer.returncode != 0:
        raise DatabaseError(
            f"COPY TO STDOUT of {relation} from {source_db} failed: {unload_err}"
        )
    if consumer.returncode != 0:
        raise DatabaseError(
            f"COPY FROM STDIN of {relation} into {target_db}.{target_schema} failed: {load_err}"
        )


def relation_kind(cfg: Config, dbname: str, relation: str) -> str | None:
    """Return the pg_class relkind of a qualified relation, or None if absent."""
    schema, _, table = relation.rpartition(".")
    schema = schema or "public"
    return scalar(
        cfg,
        dbname,
        "SELECT c.relkind FROM pg_class c "
        "JOIN pg_namespace n ON n.oid = c.relnamespace "
        f"WHERE n.nspname = {quote_literal(schema)} "
        f"AND c.relname = {quote_literal(table)}",
    )


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
