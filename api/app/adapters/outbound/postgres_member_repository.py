"""Postgres MemberRepository — real columns, one row per customer pass.

Two behaviours differ from the SQLite adapter this replaces, both deliberate:

* **`created_at` is the database's.** `now()` is the column default and the
  insert returns it, so timestamps come from one clock instead of whichever
  serverless instance handled the request.
* **`save` updates only what can change** (name, stamps, rewards). The SQLite
  version rewrote a whole JSON blob while leaving the promoted `email` and
  `serial_number` columns untouched, so the two copies could drift apart.
  Identity columns are simply not in the UPDATE.
"""

from __future__ import annotations

from ...domain.ids import small_id
from ...domain.models import Member, MemberRecord
from .db import get_pool

_SELECT = """
    select id, shop_id, name, email, serial_number, stamps, rewards, created_at
      from members
"""


def _to_record(row: dict) -> MemberRecord:
    return MemberRecord(
        id=row["id"],
        shop_id=row["shop_id"],
        name=row["name"],
        email=row["email"],
        serial_number=row["serial_number"],
        stamps=row["stamps"],
        rewards=row["rewards"],
        # The API contract exposes created_at as an ISO string.
        created_at=row["created_at"].isoformat(timespec="seconds"),
    )


class PostgresMemberRepository:
    def __init__(self, pool=None) -> None:
        self._pool = pool or get_pool()

    def add(self, member: Member) -> MemberRecord:
        with self._pool.connection() as conn:
            row = conn.execute(
                """
                insert into members (id, shop_id, name, email, serial_number)
                values (%s, %s, %s, %s, %s)
                returning id, shop_id, name, email, serial_number,
                          stamps, rewards, created_at
                """,
                (
                    small_id("mem"),
                    member.shop_id,
                    member.name,
                    member.email,
                    small_id("psly"),
                ),
            ).fetchone()
        return _to_record(row)

    def get(self, member_id: str) -> MemberRecord | None:
        with self._pool.connection() as conn:
            row = conn.execute(_SELECT + " where id = %s", (member_id,)).fetchone()
        return _to_record(row) if row else None

    def find_by_email(self, shop_id: str, email: str) -> MemberRecord | None:
        # Stored lowercase (pydantic normalises, a CHECK enforces), so a plain
        # equality match is both correct and index-backed — no COLLATE needed.
        with self._pool.connection() as conn:
            row = conn.execute(
                _SELECT + " where shop_id = %s and email = %s",
                (shop_id, email.strip().lower()),
            ).fetchone()
        return _to_record(row) if row else None

    def list_for_shop(self, shop_id: str) -> list[MemberRecord]:
        with self._pool.connection() as conn:
            rows = conn.execute(_SELECT + " where shop_id = %s order by seq", (shop_id,)).fetchall()
        return [_to_record(r) for r in rows]

    def save(self, member: MemberRecord) -> MemberRecord:
        """Persist the mutable fields. Identity (shop_id, email, serial_number,
        created_at) is immutable and deliberately absent from the UPDATE."""
        with self._pool.connection() as conn:
            row = conn.execute(
                """
                update members
                   set name = %s, stamps = %s, rewards = %s
                 where id = %s
                returning id, shop_id, name, email, serial_number,
                          stamps, rewards, created_at
                """,
                (member.name, member.stamps, member.rewards, member.id),
            ).fetchone()
        if row is None:
            raise KeyError(f"No member with id {member.id!r} to save.")
        return _to_record(row)
