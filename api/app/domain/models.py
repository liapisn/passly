"""Pass + shop domain models.

These mirror the fields a real Apple Wallet `.pkpass` needs, so P1 can turn a
saved design straight into a signed pass without reshaping the data. Kept
deliberately small for the demo: a store card (loyalty) or a coupon.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, Field, field_validator

HEX_COLOR = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")

Hex = Annotated[str, Field(pattern=HEX_COLOR.pattern, examples=["#0B5"])]


class PassType(str, Enum):
    """The two pass shapes the demo supports."""

    store_card = "storeCard"   # loyalty / stamp card
    coupon = "coupon"          # a single offer / discount


class PassDesign(BaseModel):
    """Everything the founder edits in the designer and P1 signs into a pass."""

    pass_type: PassType = PassType.store_card
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
