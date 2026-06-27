"""Campaign use cases — the founder asks the crew to draft a launch campaign
for a shop, then approves/revises/kills it at the gate.

Depends only on the ShopRepository and CampaignRunner ports, so it is testable
with fakes and never imports the framework.
"""

from __future__ import annotations

from ..domain.errors import CampaignNotFound, ShopNotFound
from ..domain.models import CampaignState
from ..domain.ports import CampaignRunner, ShopRepository


class CampaignService:
    def __init__(self, shops: ShopRepository, runner: CampaignRunner) -> None:
        self._shops = shops
        self._runner = runner

    async def start_for_shop(self, shop_id: str) -> CampaignState:
        shop = self._shops.get(shop_id)
        if shop is None:
            raise ShopNotFound(shop_id)
        thread_id = await self._runner.start(shop)
        return self.get(thread_id)

    def get(self, thread_id: str) -> CampaignState:
        state = self._runner.get(thread_id)
        if state is None:
            raise CampaignNotFound(thread_id)
        return state

    async def respond(
        self, thread_id: str, action: str, feedback: str | None
    ) -> CampaignState:
        delivered = await self._runner.respond(thread_id, action, feedback)
        if not delivered:
            raise CampaignNotFound(thread_id)
        return self.get(thread_id)
