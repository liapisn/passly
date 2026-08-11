"""SQLite ShopRepository — the persistent adapter (shops survive restarts).

Domain models stay pure pydantic; the row is just the model's JSON plus an `id`
and an ordering counter. A Postgres adapter implementing the same port is the
go-live swap.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from ...domain.models import Shop, ShopRecord


class SqliteShopRepository:
    def __init__(self, db_path: str | Path) -> None:
        self._db = str(db_path)
        Path(self._db).parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as c:
            c.execute(
                "CREATE TABLE IF NOT EXISTS shops "
                "(id TEXT PRIMARY KEY, n INTEGER, json TEXT)"
            )

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db)
        conn.row_factory = sqlite3.Row
        return conn

    def add(self, shop: Shop) -> ShopRecord:
        with self._conn() as c:
            n = c.execute("SELECT COALESCE(MAX(n), 0) + 1 AS n FROM shops").fetchone()["n"]
            record = ShopRecord(id=f"shop-{n}", **shop.model_dump())
            c.execute(
                "INSERT INTO shops(id, n, json) VALUES(?, ?, ?)",
                (record.id, n, record.model_dump_json()),
            )
            return record

    def list(self) -> list[ShopRecord]:
        with self._conn() as c:
            rows = c.execute("SELECT json FROM shops ORDER BY n").fetchall()
        return [ShopRecord.model_validate_json(r["json"]) for r in rows]

    def get(self, shop_id: str) -> ShopRecord | None:
        with self._conn() as c:
            row = c.execute("SELECT json FROM shops WHERE id = ?", (shop_id,)).fetchone()
        return ShopRecord.model_validate_json(row["json"]) if row else None
