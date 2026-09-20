#!/usr/bin/env python3
"""Verify a Passly database is set up correctly. Read-only — writes nothing.

    export DATABASE_URL='postgresql://...'
    python scripts/check_supabase.py

Reports which kind of Supabase endpoint you're on, whether the schema matches
0001_initial_schema.sql, whether RLS is on, and what data is present. Exits
non-zero if anything required is missing, so it doubles as a deploy pre-flight.

The connection string is read from the environment and never printed.
"""

from __future__ import annotations

import os
import sys
from urllib.parse import urlparse

try:
    import psycopg
except ModuleNotFoundError:
    sys.exit("psycopg is not installed. Run: pip install 'psycopg[binary]'")

EXPECTED: dict[str, set[str]] = {
    "shops": {
        "id", "seq", "name", "city", "address", "email", "phone",
        "instagram_handle", "facebook_page_url", "google_maps_url",
        "created_at",
    },
    "pass_designs": {
        "id", "shop_id", "pass_type", "logo_text", "offer_label", "offer_value",
        "secondary_label", "secondary_value", "background_color",
        "foreground_color", "label_color", "barcode_message", "stamps_goal",
        "updated_at",
    },
    "members": {
        "id", "seq", "shop_id", "name", "email", "serial_number",
        "stamps", "rewards", "created_at",
    },
    "campaigns": {
        "thread_id", "seq", "shop_id", "status", "gate_turn", "gate_artifact",
        "gate_options", "final_artifact", "error", "created_at", "updated_at",
    },
}

EXPECTED_FKS = {
    ("pass_designs", "shops"),
    ("members", "shops"),
    ("campaigns", "shops"),
}

OK, BAD, WARN = "  ok  ", " FAIL ", " warn "
problems: list[str] = []


def report(mark: str, msg: str) -> None:
    print(f"[{mark}] {msg}")
    if mark == BAD:
        problems.append(msg)


def describe_endpoint(dsn: str) -> None:
    host = (urlparse(dsn).hostname or "").lower()
    port = urlparse(dsn).port

    if "pooler.supabase.com" in host and port == 6543:
        report(OK, "Transaction pooler (:6543) — the right choice for Vercel/serverless")
    elif "pooler.supabase.com" in host and port == 5432:
        report(WARN, "Session pooler (:5432) — fine for local dev and migrations; "
                     "use the :6543 transaction pooler for the deployed API")
    elif host.startswith("db.") and host.endswith(".supabase.co"):
        report(WARN, "Direct connection — IPv6-only unless you have the IPv4 add-on, "
                     "and it exhausts connections on serverless. Good for migrations only")
    elif host in {"localhost", "127.0.0.1"}:
        report(OK, "Local Postgres")
    else:
        report(WARN, f"Unrecognised host ({host}:{port})")


def main() -> None:
    dsn = os.environ.get("DATABASE_URL", "").strip()
    if not dsn:
        sys.exit("DATABASE_URL is not set.")

    print("── endpoint ─────────────────────────────────────────")
    describe_endpoint(dsn)

    try:
        conn = psycopg.connect(dsn, prepare_threshold=None, connect_timeout=15)
    except Exception as exc:
        print(f"[{BAD}] Could not connect: {type(exc).__name__}: {exc}")
        print(
            "\nCommon causes:\n"
            "  • wrong password in the connection string\n"
            "  • using the direct connection from an IPv4-only network — switch\n"
            "    to the session pooler (:5432 on pooler.supabase.com)\n"
            "  • the project is paused (free tier pauses after inactivity)"
        )
        sys.exit(1)

    with conn:
        version = conn.execute("select version()").fetchone()[0]
        report(OK, f"Connected — {version.split(',')[0]}")

        print("\n── schema ───────────────────────────────────────────")
        rows = conn.execute(
            """
            select table_name, column_name
              from information_schema.columns
             where table_schema = 'public'
            """
        ).fetchall()
        actual: dict[str, set[str]] = {}
        for table, column in rows:
            actual.setdefault(table, set()).add(column)

        for table, columns in EXPECTED.items():
            if table not in actual:
                report(BAD, f"table {table!r} is missing — apply 0001_initial_schema.sql")
                continue
            missing = columns - actual[table]
            extra = actual[table] - columns
            if missing:
                report(BAD, f"{table}: missing columns {sorted(missing)}")
            else:
                note = f" (+{sorted(extra)} not in the migration)" if extra else ""
                report(OK, f"{table}: {len(columns)} columns{note}")

        print("\n── relations ────────────────────────────────────────")
        fks = {
            (r[0], r[1])
            for r in conn.execute(
                """
                select tc.table_name, ccu.table_name as references_table
                  from information_schema.table_constraints tc
                  join information_schema.constraint_column_usage ccu
                    on ccu.constraint_name = tc.constraint_name
                 where tc.constraint_type = 'FOREIGN KEY'
                   and tc.table_schema = 'public'
                """
            ).fetchall()
        }
        for child, parent in sorted(EXPECTED_FKS):
            if (child, parent) in fks:
                report(OK, f"{child} → {parent}")
            else:
                report(BAD, f"missing foreign key {child} → {parent}")

        print("\n── row level security ───────────────────────────────")
        for table, enabled in conn.execute(
            """
            select relname, relrowsecurity
              from pg_class
             where relnamespace = 'public'::regnamespace and relkind = 'r'
             order by relname
            """
        ).fetchall():
            if table not in EXPECTED:
                continue
            if enabled:
                report(OK, f"{table}: RLS enabled")
            else:
                report(BAD, f"{table}: RLS OFF — anon PostgREST access is open")

        policies = conn.execute(
            "select count(*) from pg_policies where schemaname = 'public'"
        ).fetchone()[0]
        if policies:
            report(WARN, f"{policies} RLS policies exist — Passly expects none "
                         "(the API bypasses RLS as table owner)")

        print("\n── data ─────────────────────────────────────────────")
        if all(t in actual for t in EXPECTED):
            counts = conn.execute(
                """
                select (select count(*) from shops),
                       (select count(*) from pass_designs),
                       (select count(*) from members),
                       (select count(*) from campaigns)
                """
            ).fetchone()
            print(f"        shops={counts[0]}  designs={counts[1]}  "
                  f"members={counts[2]}  campaigns={counts[3]}")
            if counts[0] != counts[1]:
                report(BAD, "every shop must have exactly one design — reads inner-join")

    print()
    if problems:
        print(f"{len(problems)} problem(s) found.")
        sys.exit(1)
    print("All good — the database is ready.")


if __name__ == "__main__":
    main()
