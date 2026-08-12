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


# ── thread ids ───────────────────────────────────────────────────────────
# The real runner's id generator, tested directly. Importing the adapter is
# framework-free by design, so this runs in CI without solo-founder-crew.


def test_thread_ids_are_unique_and_non_sequential():
    from app.adapters.outbound.crew_runner import SoloFounderCrewRunner

    ids = [SoloFounderCrewRunner.new_thread_id() for _ in range(200)]
    assert len(set(ids)) == 200
    assert all(i.startswith("camp_") for i in ids)
    # A counter issues ids in ascending order. 200 random ids arriving already
    # sorted has probability ~1/200!, so this catches a regression to a sequence.
    assert sorted(ids) != ids


def test_thread_ids_do_not_restart_with_a_new_runner():
    """The bug this replaced: a per-process counter restarted at 1 on every
    boot, so a restarted server reissued thread ids that already exist as
    primary keys in the campaigns table."""
    from app.adapters.outbound.crew_runner import SoloFounderCrewRunner

    first = {SoloFounderCrewRunner().new_thread_id() for _ in range(50)}
    second = {SoloFounderCrewRunner().new_thread_id() for _ in range(50)}
    assert first.isdisjoint(second)
