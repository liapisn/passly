"""In-memory ShopRepository adapter.

The demo's persistence (and a perfectly good test double). A DB-backed adapter
implementing the same port is a P4 / Passly-live concern; swapping it in needs
no change to the services. Ids are short and readable (shop-1, shop-2, …).
"""

from __future__ import annotations

from ...domain.models import Shop, ShopRecord


class InMemoryShopRepository:
    def __init__(self) -> None:
        self._shops: dict[str, ShopRecord] = {}
        self._counter = 0

    def add(self, shop: Shop) -> ShopRecord:
        self._counter += 1
        record = ShopRecord(id=f"shop-{self._counter}", **shop.model_dump())
        self._shops[record.id] = record
        return record

    def list(self) -> list[ShopRecord]:
        return list(self._shops.values())

    def get(self, shop_id: str) -> ShopRecord | None:
        return self._shops.get(shop_id)
