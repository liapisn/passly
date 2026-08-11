"""Ports — the interfaces the core depends on.

Driven adapters (in-memory store, the framework gateway, later a DB or the
Apple pass signer) implement these Protocols. The services depend only on the
Protocols, so any adapter — real or fake — drops in unchanged. This mirrors
the substrate-neutral seams in solo-founder-crew (HITLContract, LLMClient).
"""

from __future__ import annotations

from typing import Protocol

from .issued_pass import IssuedPass
from .models import CampaignState, Member, MemberRecord, Shop, ShopRecord


class ShopRepository(Protocol):
    """Persistence for shops. The adapter assigns the id on `add`."""

    def add(self, shop: Shop) -> ShopRecord: ...

    def list(self) -> list[ShopRecord]: ...

    def get(self, shop_id: str) -> ShopRecord | None: ...


class MemberRepository(Protocol):
    """Persistence for members (end-customer passes). The adapter assigns the id
    and the unique serial_number on `add`; `save` persists mutations (stamps)."""

    def add(self, member: Member) -> MemberRecord: ...

    def get(self, member_id: str) -> MemberRecord | None: ...

    def list_for_shop(self, shop_id: str) -> list[MemberRecord]: ...

    def save(self, member: MemberRecord) -> MemberRecord: ...


class CrewGateway(Protocol):
    """The solo-founder-crew framework, behind a port.

    Today it only exposes the role catalogue (the P0 smoke check). P3 grows
    this with `draft_campaign(...)` driving the marketing crew through the
    Author Flow.
    """

    def role_catalogue(self) -> list[str]: ...


class CampaignRunner(Protocol):
    """Drives the marketing crew to draft a launch campaign for a shop and
    holds the founder gate. The real adapter wraps solo-founder-crew's Author
    Flow + a web HITL surface; a fake stands in for tests.
    """

    async def start(self, shop: ShopRecord) -> str:
        """Kick off a run for the shop; returns its thread_id. The run drafts,
        then pauses at the HITL gate (state becomes `awaiting_review`)."""
        ...

    def get(self, thread_id: str) -> CampaignState | None:
        """Current pollable state, or None if the thread is unknown."""
        ...

    async def respond(self, thread_id: str, action: str, feedback: str | None) -> bool:
        """Deliver the founder's decision to a waiting gate. False if there is
        no run/gate awaiting a response."""
        ...


class PassSigner(Protocol):
    """Produces the detached PKCS#7/CMS signature over a pass's manifest.json.

    The real adapter signs with the Apple Pass Type ID certificate; a fake
    returns an empty signature for dev/CI (a structurally-valid but
    Wallet-unacceptable bundle). `real` lets callers tell the two apart.
    Apple-specific — used only by the Apple pass issuer.
    """

    real: bool

    def sign(self, manifest: bytes) -> bytes: ...


class PassIssuer(Protocol):
    """Turns a shop (and optionally a member's serial + stamps) into a wallet
    pass. Apple issues a `.pkpass`; a future Google Wallet issuer implements the
    same port. The domain and services stay platform-neutral behind it.
    """

    def issue(
        self,
        shop: ShopRecord,
        *,
        serial_number: str | None = None,
        stamps: int | None = None,
    ) -> IssuedPass: ...
