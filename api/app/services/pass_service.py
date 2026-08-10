"""Pass issuance use case — assemble a signed `.pkpass` bundle for a shop.

A `.pkpass` is a zip of: `pass.json`, image assets, a `manifest.json` (SHA-1 of
every file), and a detached `signature` over that manifest. This service builds
all of it; the signature step is delegated to the `PassSigner` port, so the
real Apple signer drops in without touching this code.
"""

from __future__ import annotations

import hashlib
import io
import json
import zipfile
from pathlib import Path

from ..domain.errors import ShopNotFound
from ..domain.pkpass import build_pass_json
from ..domain.ports import PassSigner, ShopRepository

# Shop logo used (with the shop's permission) for the pass icon/logo. Bundled
# for the single-shop demo; per-shop logos are a go-live generalisation.
_LOGO_PATH = Path(__file__).resolve().parent.parent / "assets" / "pass-logo.png"
# The logo is dark on transparent, so it is composited on a light chip to stay
# legible on any pass background.
_CHIP = "#F5E6C8"


class PassService:
    def __init__(
        self,
        shops: ShopRepository,
        signer: PassSigner,
        *,
        team_id: str,
        pass_type_id: str,
    ) -> None:
        self._shops = shops
        self._signer = signer
        self._team_id = team_id
        self._pass_type_id = pass_type_id

    def build_pkpass(self, shop_id: str) -> bytes:
        shop = self._shops.get(shop_id)
        if shop is None:
            raise ShopNotFound(shop_id)

        pass_json = build_pass_json(
            shop, team_id=self._team_id, pass_type_id=self._pass_type_id
        )
        files: dict[str, bytes] = {
            "pass.json": json.dumps(pass_json, ensure_ascii=False).encode("utf-8"),
            "icon.png": _icon(shop.design.background_color, 29),
            "icon@2x.png": _icon(shop.design.background_color, 58),
            "logo.png": _logo(shop.design.background_color, 160, 50),
            "logo@2x.png": _logo(shop.design.background_color, 320, 100),
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


def _icon(bg_hex: str, size: int) -> bytes:
    """Square pass icon: the shop logo on a light chip, or a solid colour if no
    logo asset is bundled."""
    return _render(size, size, bg_hex)


def _logo(bg_hex: str, w: int, h: int) -> bytes:
    """Pass banner logo: the shop logo on a light chip (letterboxed)."""
    return _render(w, h, bg_hex)


def _render(w: int, h: int, bg_hex: str) -> bytes:
    from PIL import Image

    if _LOGO_PATH.exists():
        canvas = Image.new("RGBA", (w, h), _CHIP)
        logo = Image.open(_LOGO_PATH).convert("RGBA")
        pad = round(min(w, h) * 0.12)
        box = (max(1, w - 2 * pad), max(1, h - 2 * pad))
        logo.thumbnail(box, Image.LANCZOS)
        canvas.paste(logo, ((w - logo.width) // 2, (h - logo.height) // 2), logo)
        img = canvas.convert("RGB")
    else:  # fallback: solid brand colour
        img = Image.new("RGB", (w, h), bg_hex)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
