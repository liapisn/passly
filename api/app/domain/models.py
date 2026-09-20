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

EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
GR_PHONE = re.compile(r"^\+30\s?6\d{2}\s?\d{3}\s?\d{4}$")
INSTAGRAM_HANDLE = re.compile(r"^[A-Za-z0-9_.]{1,30}$")


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
    # Stamps needed for a reward; reaching it resets the card and grants a reward.
    stamps_goal: int = Field(default=10, ge=1, le=99)

    @field_validator("background_color", "foreground_color", "label_color")
    @classmethod
    def _normalise_hex(cls, v: str) -> str:
        return v.upper()


class Shop(BaseModel):
    """A demo merchant and its pass design."""

    name: str = Field(min_length=1, max_length=100)
    city: str = Field(default="", max_length=80)
    # Contact + social fields, editable on the shop details page
    # (ShopDetails, below) independently of name/city/design.
    address: str = Field(default="", max_length=200)
    email: str = Field(default="", max_length=120)
    phone: str = Field(default="", max_length=20)
    instagram_handle: str = Field(default="", max_length=30)
    facebook_page_url: str = Field(default="", max_length=200)
    google_maps_url: str = Field(default="", max_length=300)
    design: PassDesign


class ShopRecord(Shop):
    """A persisted shop — `Shop` plus a server-assigned id."""

    id: str


class ShopDetails(BaseModel):
    """The shop details page's form contract: name plus the contact/social
    fields, validated strictly on save. Kept separate from `Shop` so creating
    a shop from the pass designer doesn't need address/email up front."""

    name: str = Field(min_length=1, max_length=100)
    address: str = Field(min_length=5, max_length=200)
    email: str = Field(pattern=EMAIL.pattern, max_length=120)
    phone: str = Field(default="", max_length=20)
    instagram_handle: str = Field(default="", max_length=30)
    facebook_page_url: str = Field(default="", max_length=200)
    google_maps_url: str = Field(default="", max_length=300)

    @field_validator("phone")
    @classmethod
    def _validate_phone(cls, v: str) -> str:
        if v and not GR_PHONE.match(v):
            raise ValueError("Έγκυρο ελληνικό νούμερο (π.χ. +30 6XX XXXXXXX)")
        return v

    @field_validator("instagram_handle")
    @classmethod
    def _validate_instagram(cls, v: str) -> str:
        if v and not INSTAGRAM_HANDLE.match(v):
            raise ValueError("Μόνο γράμματα, αριθμοί, underscore (χωρίς @)")
        return v

    @field_validator("facebook_page_url")
    @classmethod
    def _validate_facebook(cls, v: str) -> str:
        if v and not v.startswith("https://facebook.com/"):
            raise ValueError("Έγκυρη διεύθυνση Facebook (facebook.com/...)")
        return v

    @field_validator("google_maps_url")
    @classmethod
    def _validate_maps(cls, v: str) -> str:
        if v and "google.com/maps" not in v and "goo.gl/maps" not in v:
            raise ValueError("Έγκυρη διεύθυνση Google Maps")
        return v


# ── Member (an end customer holding a shop's pass) ──


class Member(BaseModel):
    """A customer enrolling in a shop's loyalty pass. Email is the identity —
    unique per shop (one pass per customer) and the channel to send the pass."""

    shop_id: str
    name: str = Field(default="", max_length=80)
    email: str = Field(pattern=EMAIL.pattern, max_length=120)

    @field_validator("email", mode="before")
    @classmethod
    def _normalise_email(cls, v: object) -> object:
        """Trim and lowercase before the pattern runs, so email is a stable
        identity. Without it "Nikos@X.com" and "nikos@x.com" enrol as two
        different customers holding two different passes; the database mirrors
        the rule with a `email = lower(email)` check."""
        return v.strip().lower() if isinstance(v, str) else v


class MemberRecord(Member):
    """A persisted member — the unit behind "each customer's pass". Carries the
    pass's unique `serial_number` and the loyalty state (`stamps`)."""

    id: str
    serial_number: str  # unique per pass; becomes pass.json serialNumber
    stamps: int = 0      # progress toward the shop's stamps_goal
    rewards: int = 0     # completed cards (reward earned; card reset)
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
