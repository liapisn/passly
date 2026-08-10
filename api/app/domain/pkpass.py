"""Build an Apple Wallet `pass.json` from a shop's design — pure, no I/O.

Maps our `PassDesign` onto the fields Apple expects. The signing and zip
assembly live in the pass service; this module only shapes the JSON so it is
trivially testable.
"""

from __future__ import annotations

from .models import PassType, ShopRecord


def hex_to_rgb(hex_color: str) -> str:
    """`#0B5D3B` → `rgb(11, 93, 59)` (the form Apple's pass.json wants)."""
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c + c for c in h)
    r, g, b = (int(h[i : i + 2], 16) for i in (0, 2, 4))
    return f"rgb({r}, {g}, {b})"


def build_pass_json(
    shop: ShopRecord, *, team_id: str, pass_type_id: str
) -> dict:
    d = shop.design

    fields = {
        "primaryFields": [
            {"key": "offer", "label": d.offer_label, "value": d.offer_value}
        ],
    }
    if d.secondary_label or d.secondary_value:
        fields["secondaryFields"] = [
            {"key": "secondary", "label": d.secondary_label, "value": d.secondary_value}
        ]

    style_key = "coupon" if d.pass_type is PassType.coupon else "storeCard"

    return {
        "formatVersion": 1,
        "passTypeIdentifier": pass_type_id,
        "teamIdentifier": team_id,
        "organizationName": shop.name,
        "description": f"{shop.name} — {d.offer_label}",
        "serialNumber": shop.id,
        "logoText": d.logo_text,
        "backgroundColor": hex_to_rgb(d.background_color),
        "foregroundColor": hex_to_rgb(d.foreground_color),
        "labelColor": hex_to_rgb(d.label_color),
        "barcodes": [
            {
                "format": "PKBarcodeFormatQR",
                "message": d.barcode_message or shop.id,
                "messageEncoding": "iso-8859-1",
            }
        ],
        style_key: fields,
    }
