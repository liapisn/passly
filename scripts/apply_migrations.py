#!/usr/bin/env python3
"""Apply the SQL files in supabase/migrations/ to DATABASE_URL, in order.

    python scripts/apply_migrations.py            # dry run: list what would run
    python scripts/apply_migrations.py --commit

Each file runs inside a transaction — Postgres DDL is transactional, so a
migration either lands whole or not at all. Already-applied migrations are
tracked in `schema_migrations` and skipped, so re-running is safe.

An alternative to the Supabase SQL Editor for anyone who can reach the database
directly; the `supabase` CLI (`supabase db push`) also understands this folder.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

try:
    import psycopg
except ModuleNotFoundError:
    sys.exit("psycopg is not installed. Run: pip install 'psycopg[binary]'")

MIGRATIONS = Path(__file__).resolve().parent.parent / "supabase" / "migrations"

TRACKING = """
create table if not exists public.schema_migrations (
    version    text primary key,
    applied_at timestamptz not null default now()
)
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--commit", action="store_true", help="actually apply (default: dry run)")
    args = parser.parse_args()

    dsn = os.environ.get("DATABASE_URL", "").strip()
    if not dsn:
        sys.exit("DATABASE_URL is not set.")

    files = sorted(MIGRATIONS.glob("*.sql"))
    if not files:
        sys.exit(f"No .sql files in {MIGRATIONS}")

    with psycopg.connect(dsn, prepare_threshold=None) as conn:
        conn.execute(TRACKING)
        conn.commit()
        applied = {
            r[0] for r in conn.execute("select version from schema_migrations").fetchall()
        }

        pending = [f for f in files if f.stem not in applied]
        for f in files:
            print(f"  {'pending' if f.stem in {p.stem for p in pending} else 'applied'}  {f.name}")

        if not pending:
            print("\nNothing to do — the database is up to date.")
            return

        if not args.commit:
            print(f"\nDRY RUN — {len(pending)} migration(s) would run. Re-run with --commit.")
            return

        for f in pending:
            print(f"\nApplying {f.name} …")
            with conn.transaction():
                # No parameters, so psycopg uses the simple query protocol and
                # the file's many statements run in one round trip.
                conn.execute(f.read_text())
                conn.execute(
                    "insert into schema_migrations (version) values (%s)", (f.stem,)
                )
            print(f"  ✓ {f.name}")

        print(f"\n{len(pending)} migration(s) applied.")


if __name__ == "__main__":
    main()
