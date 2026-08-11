"""In-memory ShopRepository adapter.

A test double (SQLite is the real store). Ids are non-sequential smallIds
(`shop_…`) from the shared id helper, same as the SQLite adapter.
"""

from __future__ import annotations

from ...domain.ids import small_id
from ...domain.models import Shop, ShopRecord


class InMemoryShopRepository:
    def __init__(self) -> None:
        self._shops: dict[str, ShopRecord] = {}

    def add(self, shop: Shop) -> ShopRecord:
        record = ShopRecord(id=small_id("shop"), **shop.model_dump())
        self._shops[record.id] = record
        return record

    def list(self) -> list[ShopRecord]:
        return list(self._shops.values())

    def get(self, shop_id: str) -> ShopRecord | None:
        return self._shops.get(shop_id)
