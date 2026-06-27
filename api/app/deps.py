"""Composition root — wires concrete adapters into services and exposes them as
FastAPI dependencies. This is the ONE place that knows which adapters are in
use; swapping an adapter (or overriding one in a test) happens here.
"""

from __future__ import annotations

from functools import lru_cache

from .adapters.outbound.crew_gateway import SoloFounderCrewGateway
from .adapters.outbound.memory_shop_repository import InMemoryShopRepository
from .services.crew_service import CrewService
from .services.shop_service import ShopService


@lru_cache
def _shop_repository() -> InMemoryShopRepository:
    # Process-wide singleton so shops created in one request survive to the next.
    return InMemoryShopRepository()


def get_shop_service() -> ShopService:
    return ShopService(_shop_repository())


def get_crew_service() -> CrewService:
    return CrewService(SoloFounderCrewGateway())
