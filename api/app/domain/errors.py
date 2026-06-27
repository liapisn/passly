"""Domain errors — framework-agnostic. Inbound adapters map these to transport
status codes (e.g. HTTP 404); the core never imports FastAPI."""

from __future__ import annotations


class ShopNotFound(Exception):
    def __init__(self, shop_id: str) -> None:
        super().__init__(f"No shop {shop_id!r}")
        self.shop_id = shop_id


class CampaignNotFound(Exception):
    def __init__(self, thread_id: str) -> None:
        super().__init__(f"No campaign {thread_id!r} (or no gate awaiting a response)")
        self.thread_id = thread_id
