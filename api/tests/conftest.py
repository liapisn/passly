"""Test fixtures. The HTTP tests run against a fresh app with fakes injected at
the composition seam — no shared state between tests, and no need to import the
heavy solo-founder-crew framework."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.adapters.outbound.memory_shop_repository import InMemoryShopRepository
from app.deps import get_crew_service, get_shop_service
from app.main import create_app
from app.services.crew_service import CrewService
from app.services.shop_service import ShopService


class FakeCrewGateway:
    """A CrewGateway double — returns a fixed catalogue, no framework import."""

    def role_catalogue(self) -> list[str]:
        return ["marketing", "product"]


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    repo = InMemoryShopRepository()
    app.dependency_overrides[get_shop_service] = lambda: ShopService(repo)
    app.dependency_overrides[get_crew_service] = lambda: CrewService(FakeCrewGateway())
    return TestClient(app)


def valid_shop() -> dict:
    return {
        "name": "Καφέ Μαρία",
        "city": "Σύρος",
        "design": {
            "pass_type": "storeCard",
            "logo_text": "ΚΑΦΕ ΜΑΡΙΑ",
            "offer_label": "Loyalty",
            "offer_value": "Buy 9, get the 10th free",
            "secondary_label": "Member",
            "secondary_value": "—",
            "background_color": "#0B5D3B",
            "foreground_color": "#FFFFFF",
            "label_color": "#BFE8D4",
            "barcode_message": "passly:demo",
        },
    }
