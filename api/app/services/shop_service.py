"""Shop use cases. Pure application logic — depends on the ShopRepository port,
knows nothing about HTTP or the concrete store. Unit-testable with any
repository double."""

from __future__ import annotations

from ..domain.errors import ShopNotFound
from ..domain.models import Shop, ShopRecord
from ..domain.ports import ShopRepository


class ShopService:
    def __init__(self, repo: ShopRepository) -> None:
        self._repo = repo

    def create_shop(self, shop: Shop) -> ShopRecord:
        return self._repo.add(shop)

    def list_shops(self) -> list[ShopRecord]:
        return self._repo.list()

    def get_shop(self, shop_id: str) -> ShopRecord:
        record = self._repo.get(shop_id)
        if record is None:
            raise ShopNotFound(shop_id)
        return record
