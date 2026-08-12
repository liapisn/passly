#!/usr/bin/env python3
"""One-shot migration: the SQLite JSON-blob store → the relational Postgres schema.

Reads `shops` and `members` out of the old SQLite file, unpacks each row's
`json` column, and writes real columns into Postgres.

Ids and serial numbers are carried across unchanged — deliberately. A member's
`serial_number` is the `serialNumber` inside a `.pkpass` already sitting in
someone's Apple Wallet, and `/members/{id}/pkpass` links have been emailed out.
Regenerating either would orphan every issued pass.

Run the schema migration first, then:

    export DATABASE_URL='postgresql://...'          # Supabase connection string
    python scripts/migrate_sqlite_to_postgres.py api/data/passly.db
    python scripts/migrate_sqlite_to_postgres.py api/data/passly.db --commit

Without --commit it is a dry run: it reports exactly what it would write and
touches nothing. Re-running is safe; existing ids are skipped, not overwritten.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from collections import Counter

try:
    import psycopg
except ModuleNotFoundError:
    sys.exit("psycopg is not installed. Run: pip install 'psycopg[binary]'")

# Design fields, in the order the pass_designs insert expects them, paired with
# the defaults the old pydantic model applied when a key was absent.
DESIGN_FIELDS = {
    "pass_type": "loyalty",
    "logo_text": "",
    "offer_label": "",
    "offer_value": "",
    "secondary_label": "",
    "secondary_value": "",
    "background_color": "#0B5D3B",
    "foreground_color": "#FFFFFF",
    "label_color": "#BFE8D4",
    "barcode_message": "",
    "stamps_goal": 10,
}


def _small_id(prefix: str, length: int = 12) -> str:
    import secrets

    alphabet = "0123456789abcdefghjkmnpqrstvwxyz"
    return f"{prefix}_{''.join(secrets.choice(alphabet) for _ in range(length))}"


def read_sqlite(db_path: str) -> tuple[list[dict], list[dict]]:
    if not os.path.exists(db_path):
        sys.exit(f"No SQLite file at {db_path}")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        shops = [json.loads(r["json"]) for r in conn.execute("select json from shops order by n")]
        members = [
            json.loads(r["json"]) for r in conn.execute("select json from members order by n")
        ]
    finally:
        conn.close()
    return shops, members


def check_email_collisions(members: list[dict]) -> list[tuple[str, str]]:
    """Lowercasing is the whole point of the new unique constraint, so any two
    old rows that differed only by case would now collide. Report them rather
    than letting Postgres fail halfway through."""
    seen = Counter((m["shop_id"], m["email"].strip().lower()) for m in members)
    return [key for key, n in seen.items() if n > 1]


def migrate(shops: list[dict], members: list[dict], dsn: str, *, commit: bool) -> None:
    # prepare_threshold=None so this also works through Supabase's transaction
    # pooler, which hands each transaction a different backend connection and
    # would otherwise lose the prepared statements psycopg creates.
    with psycopg.connect(dsn, prepare_threshold=None) as conn:
        with conn.transaction() as tx:
            shops_written = designs_written = members_written = 0

            for shop in shops:
                design = {**DESIGN_FIELDS, **shop.get("design", {})}
                inserted = conn.execute(
                    """
                    insert into shops (id, name, city) values (%s, %s, %s)
                    on conflict (id) do nothing returning id
                    """,
                    (shop["id"], shop["name"], shop.get("city", "")),
                ).fetchone()
                if inserted is None:
                    print(f"  shop   {shop['id']}  already present — skipped")
                    continue
                shops_written += 1

                conn.execute(
                    """
                    insert into pass_designs (
                        id, shop_id, pass_type, logo_text,
                        offer_label, offer_value, secondary_label, secondary_value,
                        background_color, foreground_color, label_color,
                        barcode_message, stamps_goal
                    ) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    on conflict (shop_id) do nothing
                    """,
                    (_small_id("dsgn"), shop["id"], *(design[k] for k in DESIGN_FIELDS)),
                )
                designs_written += 1
                print(f"  shop   {shop['id']}  {shop['name']!r} + design")

            for member in members:
                email = member["email"].strip().lower()
                inserted = conn.execute(
                    """
                    insert into members (
                        id, shop_id, name, email, serial_number,
                        stamps, rewards, created_at
                    ) values (%s, %s, %s, %s, %s, %s, %s, coalesce(%s::timestamptz, now()))
                    on conflict (id) do nothing returning id
                    """,
                    (
                        member["id"],
                        member["shop_id"],
                        member.get("name", ""),
                        email,
                        member["serial_number"],
                        member.get("stamps", 0),
                        member.get("rewards", 0),
                        member.get("created_at") or None,
                    ),
                ).fetchone()
                if inserted is None:
                    print(f"  member {member['id']}  already present — skipped")
                    continue
                members_written += 1
                changed = email != member["email"]
                note = f" (email lowercased from {member['email']!r})" if changed else ""
                print(f"  member {member['id']}  {email}  serial={member['serial_number']}{note}")

            print(
                f"\n{shops_written} shops, {designs_written} designs, "
                f"{members_written} members"
            )
            if not commit:
                print("DRY RUN — rolling back. Re-run with --commit to write.")
                # psycopg unwinds the transaction block on this and swallows it.
                raise psycopg.Rollback(tx)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sqlite_path", help="path to the old passly.db")
    parser.add_argument("--commit", action="store_true", help="actually write (default: dry run)")
    args = parser.parse_args()

    dsn = os.environ.get("DATABASE_URL", "").strip()
    if not dsn:
        sys.exit("DATABASE_URL is not set — point it at the target Postgres.")

    shops, members = read_sqlite(args.sqlite_path)
    print(f"Read {len(shops)} shops and {len(members)} members from {args.sqlite_path}\n")

    collisions = check_email_collisions(members)
    if collisions:
        print("Refusing to migrate — these (shop, email) pairs collide once lowercased:")
        for shop_id, email in collisions:
            print(f"  {shop_id}  {email}")
        sys.exit("Merge or delete the duplicate members first.")

    migrate(shops, members, dsn, commit=args.commit)


if __name__ == "__main__":
    main()
