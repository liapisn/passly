"""Ports — the interfaces the core depends on.

Driven adapters (in-memory store, the framework gateway, later a DB or the
Apple pass signer) implement these Protocols. The services depend only on the
Protocols, so any adapter — real or fake — drops in unchanged. This mirrors
the substrate-neutral seams in solo-founder-crew (HITLContract, LLMClient).
"""

from __future__ import annotations

from typing import Protocol

from .models import Shop, ShopRecord


class ShopRepository(Protocol):
    """Persistence for shops. The adapter assigns the id on `add`."""

    def add(self, shop: Shop) -> ShopRecord: ...

    def list(self) -> list[ShopRecord]: ...

    def get(self, shop_id: str) -> ShopRecord | None: ...


class CrewGateway(Protocol):
    """The solo-founder-crew framework, behind a port.

    Today it only exposes the role catalogue (the P0 smoke check). P3 grows
    this with `draft_campaign(...)` driving the marketing crew through the
    Author Flow.
    """

    def role_catalogue(self) -> list[str]: ...
