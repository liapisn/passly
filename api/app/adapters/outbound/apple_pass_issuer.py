"""Apple Wallet PassIssuer — builds and signs a `.pkpass`.

All Apple-specific format knowledge lives here: the pass.json shape, the
storeCard/coupon style keys, the manifest (SHA-1 per file), the detached
signature (delegated to a PassSigner), and the branded icon/logo images. The
domain and services never see any of it — they depend on the PassIssuer port.
A Google Wallet issuer would be a sibling adapter implementing the same port.
"""

from __future__ import annotations

import hashlib
import io
import json
import zipfile
from pathlib import Path

from ...domain.issued_pass import IssuedPass
from ...domain.models import PassType, ShopRecord
from ...domain.ports import PassSigner

# Shop logo used (with the shop's permission) for the pass icon/logo. Bundled
# for the single-shop demo; per-shop logos are a go-live generalisation.
_LOGO_PATH = Path(__file__).resolve().parent.parent.parent / "assets" / "pass-logo.png"
_CHIP = "#F5E6C8"  # light chip so a dark logo stays legible on any pass colour


class ApplePassIssuer:
    def __init__(self, signer: PassSigner, *, team_id: str, pass_type_id: str) -> None:
        self._signer = signer
        self._team_id = team_id
        self._pass_type_id = pass_type_id

    def issue(
        self,
        shop: ShopRecord,
        *,
        serial_number: str | None = None,
        stamps: int | None = None,
    ) -> IssuedPass:
        pass_json = self._pass_json(shop, serial_number, stamps)
        content = self._assemble(shop, pass_json)
        name = serial_number or shop.id
        return IssuedPass(
            content=content,
            media_type="application/vnd.apple.pkpass",
            filename=f"{name}.pkpass",
            platform="apple",
        )

    def _pass_json(
        self, shop: ShopRecord, serial_number: str | None, stamps: int | None
    ) -> dict:
        d = shop.design
        secondary = []
        if d.secondary_label or d.secondary_value:
            secondary.append(
                {"key": "secondary", "label": d.secondary_label, "value": d.secondary_value}
            )
        if stamps is not None:
            secondary.append(
                {"key": "stamps", "label": "Σφραγίδες", "value": f"{stamps}/{d.stamps_goal}"}
            )

        fields: dict = {
            "primaryFields": [
                {"key": "offer", "label": d.offer_label, "value": d.offer_value}
            ],
        }
        if secondary:
            fields["secondaryFields"] = secondary

        # Map the neutral PassType to Apple's style key.
        style_key = "coupon" if d.pass_type is PassType.coupon else "storeCard"

        return {
            "formatVersion": 1,
            "passTypeIdentifier": self._pass_type_id,
            "teamIdentifier": self._team_id,
            "organizationName": shop.name,
            "description": f"{shop.name} — {d.offer_label}",
            "serialNumber": serial_number or shop.id,
            "logoText": d.logo_text,
            "backgroundColor": _hex_to_rgb(d.background_color),
            "foregroundColor": _hex_to_rgb(d.foreground_color),
            "labelColor": _hex_to_rgb(d.label_color),
            "barcodes": [
                {
                    "format": "PKBarcodeFormatQR",
                    # For a member pass the QR is the member's serial so a scan
                    # identifies exactly whose card to stamp; template falls back.
                    "message": serial_number or d.barcode_message or shop.id,
                    "messageEncoding": "iso-8859-1",
                }
            ],
            style_key: fields,
        }

    def _assemble(self, shop: ShopRecord, pass_json: dict) -> bytes:
        files: dict[str, bytes] = {
            "pass.json": json.dumps(pass_json, ensure_ascii=False).encode("utf-8"),
            "icon.png": _render(29, 29, shop.design.background_color),
            "icon@2x.png": _render(58, 58, shop.design.background_color),
            "logo.png": _render(160, 50, shop.design.background_color),
            "logo@2x.png": _render(320, 100, shop.design.background_color),
        }
        manifest = {name: hashlib.sha1(data).hexdigest() for name, data in files.items()}
        manifest_bytes = json.dumps(manifest).encode("utf-8")
        signature = self._signer.sign(manifest_bytes)

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            for name, data in files.items():
                z.writestr(name, data)
            z.writestr("manifest.json", manifest_bytes)
            z.writestr("signature", signature)
        return buf.getvalue()


def _hex_to_rgb(hex_color: str) -> str:
    """`#0B5D3B` → `rgb(11, 93, 59)` (the form Apple's pass.json wants)."""
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c + c for c in h)
    r, g, b = (int(h[i : i + 2], 16) for i in (0, 2, 4))
    return f"rgb({r}, {g}, {b})"


def _render(w: int, h: int, bg_hex: str) -> bytes:
    """Pass image: the shop logo on a light chip, or a solid colour as fallback."""
    from PIL import Image

    if _LOGO_PATH.exists():
        canvas = Image.new("RGBA", (w, h), _CHIP)
        logo = Image.open(_LOGO_PATH).convert("RGBA")
        pad = round(min(w, h) * 0.12)
        logo.thumbnail((max(1, w - 2 * pad), max(1, h - 2 * pad)), Image.LANCZOS)
        canvas.paste(logo, ((w - logo.width) // 2, (h - logo.height) // 2), logo)
        img = canvas.convert("RGB")
    else:
        img = Image.new("RGB", (w, h), bg_hex)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
