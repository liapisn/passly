"""Composition root — wires concrete adapters into services and exposes them as
FastAPI dependencies. This is the ONE place that knows which adapters are in
use; swapping an adapter (or overriding one in a test) happens here.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from .adapters.outbound.crew_gateway import SoloFounderCrewGateway
from .adapters.outbound.crew_runner import SoloFounderCrewRunner
from .adapters.outbound.memory_shop_repository import InMemoryShopRepository
from .domain.ports import PassSigner
from .services.campaign_service import CampaignService
from .services.crew_service import CrewService
from .services.pass_service import PassService
from .services.shop_service import ShopService


@lru_cache
def _shop_repository() -> InMemoryShopRepository:
    # Process-wide singleton so shops created in one request survive to the next.
    return InMemoryShopRepository()


@lru_cache
def _crew_runner() -> SoloFounderCrewRunner:
    # Singleton: holds in-flight runs, their pending gates, and background tasks.
    return SoloFounderCrewRunner()


def get_shop_service() -> ShopService:
    return ShopService(_shop_repository())


def get_crew_service() -> CrewService:
    return CrewService(SoloFounderCrewGateway())


def get_campaign_service() -> CampaignService:
    return CampaignService(_shop_repository(), _crew_runner())


# api/ — signing-material paths in .env are resolved relative to here, so the
# real signer engages regardless of the process's working directory.
_API_DIR = Path(__file__).resolve().parent.parent


def _resolve(value: str | None) -> str | None:
    if not value:
        return None
    p = Path(value)
    return str(p if p.is_absolute() else (_API_DIR / p).resolve())


@lru_cache
def _pass_signer() -> PassSigner:
    """Real Apple signer when a .p12 + WWDR are configured and present; else the
    fake (a structurally-valid but unsigned bundle) so dev/CI work without a cert."""
    p12 = _resolve(os.environ.get("APPLE_CERT_P12"))
    wwdr = _resolve(os.environ.get("APPLE_WWDR_CERT"))
    if p12 and wwdr and os.path.exists(p12) and os.path.exists(wwdr):
        from .adapters.outbound.signer import AppleP12Signer

        return AppleP12Signer(p12, os.environ.get("APPLE_CERT_PASSWORD", ""), wwdr)

    from .adapters.outbound.signer import FakeSigner

    return FakeSigner()


def get_pass_service() -> PassService:
    return PassService(
        _shop_repository(),
        _pass_signer(),
        team_id=os.environ.get("APPLE_TEAM_ID", "TEAMID0000"),
        pass_type_id=os.environ.get("APPLE_PASS_TYPE_ID", "pass.com.dion.passly-demo"),
    )
