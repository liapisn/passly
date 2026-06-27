"""Unit tests for campaign use cases — pure core with fakes, no HTTP/framework."""

from __future__ import annotations

import pytest

from app.adapters.outbound.memory_shop_repository import InMemoryShopRepository
from app.domain.errors import CampaignNotFound, ShopNotFound
from app.domain.models import CampaignStatus, PassDesign, Shop
from app.services.campaign_service import CampaignService

from .conftest import FakeCampaignRunner


def _shop() -> Shop:
    return Shop(
        name="Καφέ Μαρία",
        city="Σύρος",
        design=PassDesign(
            logo_text="ΚΑΦΕ ΜΑΡΙΑ",
            offer_label="Loyalty",
            offer_value="Buy 9, get the 10th free",
        ),
    )


def _service() -> tuple[CampaignService, InMemoryShopRepository]:
    repo = InMemoryShopRepository()
    return CampaignService(repo, FakeCampaignRunner()), repo


async def test_start_unknown_shop_raises():
    svc, _ = _service()
    with pytest.raises(ShopNotFound):
        await svc.start_for_shop("shop-404")


async def test_start_for_existing_shop_pauses_at_gate():
    svc, repo = _service()
    shop = repo.add(_shop())
    state = await svc.start_for_shop(shop.id)
    assert state.status is CampaignStatus.awaiting_review
    assert state.gate is not None
    assert "approve" in state.gate.options


async def test_respond_unknown_campaign_raises():
    svc, _ = _service()
    with pytest.raises(CampaignNotFound):
        await svc.respond("camp-404", "approve", None)


async def test_approve_ships_the_artifact():
    svc, repo = _service()
    shop = repo.add(_shop())
    started = await svc.start_for_shop(shop.id)
    final = await svc.respond(started.thread_id, "approve", None)
    assert final.status is CampaignStatus.shipped
    assert final.final_artifact is not None
