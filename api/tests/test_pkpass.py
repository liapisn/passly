"""Pass-issuance tests — the bundle pipeline with the fake signer, no cert."""

from __future__ import annotations

import hashlib
import io
import json
import zipfile

import pytest

from app.adapters.outbound.memory_shop_repository import InMemoryShopRepository
from app.adapters.outbound.signer import FakeSigner
from app.domain.errors import ShopNotFound
from app.domain.models import PassDesign, PassType, Shop
from app.domain.pkpass import build_pass_json, hex_to_rgb
from app.services.pass_service import PassService

from .conftest import valid_shop


def _service() -> tuple[PassService, InMemoryShopRepository]:
    repo = InMemoryShopRepository()
    svc = PassService(
        repo, FakeSigner(), team_id="TEAM123", pass_type_id="pass.com.dion.demo"
    )
    return svc, repo


def _shop(repo):
    body = valid_shop()
    return repo.add(
        Shop(name=body["name"], city=body["city"], design=PassDesign(**body["design"]))
    )


def test_hex_to_rgb():
    assert hex_to_rgb("#0B5D3B") == "rgb(11, 93, 59)"
    assert hex_to_rgb("#FFF") == "rgb(255, 255, 255)"


def test_pass_json_shape():
    repo = InMemoryShopRepository()
    shop = _shop(repo)
    pj = build_pass_json(shop, team_id="TEAM123", pass_type_id="pass.com.dion.demo")
    assert pj["teamIdentifier"] == "TEAM123"
    assert pj["passTypeIdentifier"] == "pass.com.dion.demo"
    assert pj["organizationName"] == shop.name
    assert pj["serialNumber"] == shop.id
    assert "storeCard" in pj  # loyalty → storeCard
    assert pj["storeCard"]["primaryFields"][0]["value"] == "Buy 9, get the 10th free"


def test_coupon_uses_coupon_style():
    repo = InMemoryShopRepository()
    shop = repo.add(
        Shop(
            name="X",
            city="",
            design=PassDesign(
                pass_type=PassType.coupon,
                logo_text="X",
                offer_label="Deal",
                offer_value="-20%",
            ),
        )
    )
    pj = build_pass_json(shop, team_id="T", pass_type_id="p")
    assert "coupon" in pj and "storeCard" not in pj


def test_build_pkpass_is_a_valid_bundle():
    svc, repo = _service()
    shop = _shop(repo)
    data = svc.build_pkpass(shop.id)

    with zipfile.ZipFile(io.BytesIO(data)) as z:
        names = set(z.namelist())
        assert {
            "pass.json",
            "icon.png",
            "icon@2x.png",
            "logo.png",
            "logo@2x.png",
            "manifest.json",
            "signature",
        } <= names

        manifest = json.loads(z.read("manifest.json"))
        # every hashed file's SHA-1 matches its contents
        for name, digest in manifest.items():
            assert hashlib.sha1(z.read(name)).hexdigest() == digest
        # pass.json carries the shop's Greek name intact
        assert json.loads(z.read("pass.json"))["organizationName"] == shop.name


def test_build_pkpass_unknown_shop_raises():
    svc, _ = _service()
    with pytest.raises(ShopNotFound):
        svc.build_pkpass("shop-404")
