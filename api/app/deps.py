"""Composition root — wires concrete adapters into services and exposes them as
FastAPI dependencies. This is the ONE place that knows which adapters are in
use; swapping an adapter (or overriding one in a test) happens here.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from .adapters.outbound.apple_pass_issuer import ApplePassIssuer
from .adapters.outbound.crew_gateway import SoloFounderCrewGateway
from .adapters.outbound.crew_runner import SoloFounderCrewRunner
from .adapters.outbound.postgres_campaign_repository import PostgresCampaignRepository
from .adapters.outbound.postgres_member_repository import PostgresMemberRepository
from .adapters.outbound.postgres_shop_repository import PostgresShopRepository
from .domain.ports import EmailSender, PassSigner
from .services.campaign_service import CampaignService
from .services.crew_service import CrewService
from .services.member_service import MemberService
from .services.pass_service import PassService
from .services.shop_service import ShopService


@lru_cache
def _shop_repository() -> PostgresShopRepository:
    return PostgresShopRepository()


@lru_cache
def _member_repository() -> PostgresMemberRepository:
    return PostgresMemberRepository()


@lru_cache
def _campaign_repository() -> PostgresCampaignRepository:
    # Storage for campaign gates. Not yet consumed by the crew runner — that
    # swap lands with the serverless campaign refactor.
    return PostgresCampaignRepository()


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


@lru_cache
def _email_sender() -> EmailSender:
    import logging

    log = logging.getLogger("passly.deps")
    key = os.environ.get("RESEND_API_KEY")
    if key and not key.startswith("re_xxx"):
        from .adapters.outbound.email_sender import ResendEmailSender

        sender = os.environ.get("PASSLY_EMAIL_FROM", "onboarding@resend.dev")
        log.info("Email: ResendEmailSender active (from %s)", sender)
        return ResendEmailSender(key, from_addr=sender)

    from .adapters.outbound.email_sender import FakeEmailSender

    log.warning(
        "Email: no valid RESEND_API_KEY -> FakeEmailSender (NO mail is sent). "
        "Set RESEND_API_KEY in api/.env to send for real."
    )
    return FakeEmailSender()


def get_member_service() -> MemberService:
    return MemberService(
        _shop_repository(),
        _member_repository(),
        _email_sender(),
        os.environ.get("PASSLY_PUBLIC_URL", "http://localhost:8000"),
    )


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


def _pass_issuer() -> ApplePassIssuer:
    return ApplePassIssuer(
        _pass_signer(),
        team_id=os.environ.get("APPLE_TEAM_ID", "TEAMID0000"),
        pass_type_id=os.environ.get("APPLE_PASS_TYPE_ID", "pass.com.dion.passly-demo"),
    )


def get_pass_service() -> PassService:
    return PassService(_shop_repository(), _member_repository(), _pass_issuer())
