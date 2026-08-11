"""Postgres connection pool — shared by the repository adapters.

One lazily-opened pool per process. On a long-lived server that is the usual
pool; on serverless each instance opens its own small pool and lets it idle
down to zero, which is why `min_size` is 0.

Supabase connection strings come in three shapes; use the pooled one for
anything serverless:

    :5432 direct           one connection per client — exhausts fast on Vercel
    :6543 transaction pool pgbouncer, transaction mode — the serverless choice
    :5432 session pool     pgbouncer, session mode — for tools needing a session

`prepare_threshold=None` disables psycopg's automatic prepared statements.
pgbouncer in transaction mode hands each transaction a different backend
connection, so a statement prepared on one is missing on the next; leaving
preparation on produces intermittent "prepared statement does not exist"
errors under load. Turning it off costs a little planning time per query and
is the documented way to run psycopg behind a transaction pooler.
"""

from __future__ import annotations

import os

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

_pool: ConnectionPool | None = None


def database_url() -> str:
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError(
            "DATABASE_URL is not set. Point it at your Supabase Postgres "
            "(Project Settings → Database → Connection string). Use the "
            "transaction pooler on port 6543 for serverless deployments."
        )
    return url


def get_pool() -> ConnectionPool:
    """The process-wide pool, opened on first use."""
    global _pool
    if _pool is None:
        _pool = ConnectionPool(
            database_url(),
            min_size=0,
            max_size=int(os.environ.get("PASSLY_DB_POOL_MAX", "4")),
            kwargs={"row_factory": dict_row, "prepare_threshold": None},
            open=True,
        )
    return _pool


def close_pool() -> None:
    """Close the pool (tests, and a clean server shutdown)."""
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None
