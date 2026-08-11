"""Pass + shop domain models.

These mirror the fields a real Apple Wallet `.pkpass` needs, so P1 can turn a
saved design straight into a signed pass without reshaping the data. Kept
deliberately small for the demo: a store card (loyalty) or a coupon.
"""

from __future__ import annotations

import re
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, Field, field_validator

HEX_COLOR = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")

Hex = Annotated[str, Field(pattern=HEX_COLOR.pattern, examples=["#0B5"])]


class PassType(StrEnum):
    """Platform-neutral pass shape. The issuer adapter maps it to each wallet's
    terms (Apple storeCard / Google loyalty class, Apple coupon / Google offer)."""

    loyalty = "loyalty"   # stamp / points card
    coupon = "coupon"     # a single offer / discount


class PassDesign(BaseModel):
    """Everything the founder edits in the designer and P1 signs into a pass."""

    pass_type: PassType = PassType.loyalty
    logo_text: str = Field(min_length=1, max_length=40)
    # The hero line on the pass, e.g. "Buy 9, get the 10th free".
    offer_label: str = Field(min_length=1, max_length=40)
    offer_value: str = Field(min_length=1, max_length=60)
    # A secondary field, e.g. "Member" / "Nikos" or "Expires" / "31 Dec".
    secondary_label: str = Field(default="", max_length=40)
    secondary_value: str = Field(default="", max_length=60)
    background_color: Hex = "#0B5D3B"
    foreground_color: Hex = "#FFFFFF"
    label_color: Hex = "#BFE8D4"
    barcode_message: str = Field(default="", max_length=120)

    @field_validator("background_color", "foreground_color", "label_color")
    @classmethod
    def _normalise_hex(cls, v: str) -> str:
        return v.upper()


class Shop(BaseModel):
    """A demo merchant and its pass design."""

    name: str = Field(min_length=1, max_length=80)
    city: str = Field(default="", max_length=80)
    design: PassDesign


class ShopRecord(Shop):
    """A persisted shop — `Shop` plus a server-assigned id."""

    id: str


# ── Member (an end customer holding a shop's pass) ──


class Member(BaseModel):
    """A customer enrolling in a shop's loyalty pass."""

    shop_id: str
    name: str = Field(default="", max_length=80)


class MemberRecord(Member):
    """A persisted member — the unit behind "each customer's pass". Carries the
    pass's unique `serial_number` and the loyalty state (`stamps`)."""

    id: str
    serial_number: str  # unique per pass; becomes pass.json serialNumber
    stamps: int = 0
    created_at: str = ""


# ── Campaign (the crew drafting a launch campaign, gated by the founder) ──


class CampaignStatus(StrEnum):
    """Lifecycle of a crew-drafted campaign. The terminal three mirror the
    framework's AuthorFlowResult.status exactly."""

    drafting = "drafting"               # crew is generating / revising
    awaiting_review = "awaiting_review"  # paused at the HITL gate
    shipped = "shipped"                 # founder approved → published
    killed = "killed"                   # founder killed the run
    exhausted = "exhausted"             # revision budget spent
    error = "error"                     # the run raised


class ReviewGate(BaseModel):
    """What the founder sees at a HITL gate — the draft under review."""

    turn: int
    artifact: str
    options: list[str]  # allowed actions, e.g. ["approve", "reject", "kill"]


class CampaignState(BaseModel):
    """Pollable state of a campaign run. Exactly one of `gate` /
    `final_artifact` / `error` is meaningful, per `status`."""

    thread_id: str
    status: CampaignStatus
    gate: ReviewGate | None = None
    final_artifact: str | None = None
    error: str | None = None
