"""SQLite MemberRepository — persistent store for end-customer passes.

Each member is one customer's pass: a unique `serial_number` (the pass.json
serialNumber) plus loyalty state (`stamps`). `created_at` is an ISO timestamp.
"""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from ...domain.models import Member, MemberRecord


class SqliteMemberRepository:
    def __init__(self, db_path: str | Path) -> None:
        self._db = str(db_path)
        Path(self._db).parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as c:
            c.execute(
                "CREATE TABLE IF NOT EXISTS members "
                "(id TEXT PRIMARY KEY, n INTEGER, shop_id TEXT, "
                "serial_number TEXT UNIQUE, json TEXT)"
            )

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db)
        conn.row_factory = sqlite3.Row
        return conn

    def add(self, member: Member) -> MemberRecord:
        with self._conn() as c:
            n = c.execute("SELECT COALESCE(MAX(n), 0) + 1 AS n FROM members").fetchone()["n"]
            record = MemberRecord(
                id=f"mem-{n}",
                serial_number=f"{member.shop_id}-{n:04d}",
                stamps=0,
                created_at=datetime.now(UTC).isoformat(timespec="seconds"),
                **member.model_dump(),
            )
            c.execute(
                "INSERT INTO members(id, n, shop_id, serial_number, json) "
                "VALUES(?, ?, ?, ?, ?)",
                (record.id, n, record.shop_id, record.serial_number, record.model_dump_json()),
            )
            return record

    def get(self, member_id: str) -> MemberRecord | None:
        with self._conn() as c:
            row = c.execute(
                "SELECT json FROM members WHERE id = ?", (member_id,)
            ).fetchone()
        return MemberRecord.model_validate_json(row["json"]) if row else None

    def list_for_shop(self, shop_id: str) -> list[MemberRecord]:
        with self._conn() as c:
            rows = c.execute(
                "SELECT json FROM members WHERE shop_id = ? ORDER BY n", (shop_id,)
            ).fetchall()
        return [MemberRecord.model_validate_json(r["json"]) for r in rows]

    def save(self, member: MemberRecord) -> MemberRecord:
        with self._conn() as c:
            c.execute(
                "UPDATE members SET json = ? WHERE id = ?",
                (member.model_dump_json(), member.id),
            )
        return member
