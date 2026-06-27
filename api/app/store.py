"""In-memory shop store for the demo.

A dict is enough for P2 — it keeps the API honest about its shape (create /
list / get) without dragging in a database before the demo needs one. A
persistent store is a P4/Passly-live concern.
"""

from __future__ import annotations

from .models import Shop, ShopRecord

# Short, readable ids (shop-1, shop-2, …) — friendlier in URLs and demos than
# uuids, and there is only ever one founder creating shops here.
_shops: dict[str, ShopRecord] = {}
_counter = 0


def create(shop: Shop) -> ShopRecord:
    global _counter
    _counter += 1
    record = ShopRecord(id=f"shop-{_counter}", **shop.model_dump())
    _shops[record.id] = record
    return record


def list_all() -> list[ShopRecord]:
    return list(_shops.values())


def get(shop_id: str) -> ShopRecord | None:
    return _shops.get(shop_id)
