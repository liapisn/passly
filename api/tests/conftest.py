"""Test fixtures. The HTTP tests run against a fresh app with fakes injected at
the composition seam — no shared state between tests, and no need to import the
heavy solo-founder-crew framework."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.adapters.outbound.memory_shop_repository import InMemoryShopRepository
from app.deps import get_campaign_service, get_crew_service, get_shop_service
from app.domain.models import CampaignState, CampaignStatus, ReviewGate, ShopRecord
from app.main import create_app
from app.services.campaign_service import CampaignService
from app.services.crew_service import CrewService
from app.services.shop_service import ShopService


class FakeCrewGateway:
    """A CrewGateway double — returns a fixed catalogue, no framework import."""

    def role_catalogue(self) -> list[str]:
        return ["marketing", "product"]


class FakeCampaignRunner:
    """A CampaignRunner double that simulates the gate cycle deterministically:
    start → awaiting_review; approve → shipped; reject → a fresh gate; kill →
    killed. No async LLM, no framework."""

    def __init__(self) -> None:
        self._states: dict[str, CampaignState] = {}
        self._n = 0

    async def start(self, shop: ShopRecord) -> str:
        self._n += 1
        thread_id = f"camp-{self._n}"
        self._states[thread_id] = self._gate(thread_id, turn=1, name=shop.name)
        return thread_id

    def get(self, thread_id: str) -> CampaignState | None:
        return self._states.get(thread_id)

    async def respond(self, thread_id: str, action: str, feedback: str | None) -> bool:
        state = self._states.get(thread_id)
        if state is None or state.gate is None:
            return False
        if action == "approve":
            self._states[thread_id] = CampaignState(
                thread_id=thread_id,
                status=CampaignStatus.shipped,
                final_artifact=state.gate.artifact,
            )
        elif action == "reject":
            self._states[thread_id] = self._gate(thread_id, turn=state.gate.turn + 1)
        else:  # kill
            self._states[thread_id] = CampaignState(
                thread_id=thread_id, status=CampaignStatus.killed
            )
        return True

    @staticmethod
    def _gate(thread_id: str, *, turn: int, name: str = "shop") -> CampaignState:
        return CampaignState(
            thread_id=thread_id,
            status=CampaignStatus.awaiting_review,
            gate=ReviewGate(
                turn=turn,
                artifact=f"draft v{turn} for {name}",
                options=["approve", "reject", "kill"],
            ),
        )


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    repo = InMemoryShopRepository()  # shared by shop + campaign services
    runner = FakeCampaignRunner()
    app.dependency_overrides[get_shop_service] = lambda: ShopService(repo)
    app.dependency_overrides[get_crew_service] = lambda: CrewService(FakeCrewGateway())
    app.dependency_overrides[get_campaign_service] = lambda: CampaignService(repo, runner)
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
