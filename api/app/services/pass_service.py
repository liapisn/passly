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

from ..domain.errors import ShopNotFound
from ..domain.pkpass import build_pass_json
from ..domain.ports import PassSigner, ShopRepository


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
        icon = _solid_icon(shop.design.background_color, 29)
        icon2x = _solid_icon(shop.design.background_color, 58)

        files: dict[str, bytes] = {
            "pass.json": json.dumps(pass_json, ensure_ascii=False).encode("utf-8"),
            "icon.png": icon,
            "icon@2x.png": icon2x,
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


def _solid_icon(hex_color: str, size: int) -> bytes:
    """A solid-colour square PNG — Apple requires an icon; branding polish is P4."""
    from PIL import Image

    img = Image.new("RGB", (size, size), hex_color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
