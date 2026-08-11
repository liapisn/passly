"""Pass-issuance tests — the Apple issuer + the neutral PassService, no cert."""

from __future__ import annotations

import hashlib
import io
import json
import zipfile

import pytest

from app.adapters.outbound.apple_pass_issuer import ApplePassIssuer, _hex_to_rgb
from app.adapters.outbound.memory_member_repository import InMemoryMemberRepository
from app.adapters.outbound.memory_shop_repository import InMemoryShopRepository
from app.adapters.outbound.signer import FakeSigner
from app.domain.errors import MemberNotFound, ShopNotFound
from app.domain.models import Member, PassDesign, PassType, Shop
from app.services.pass_service import PassService

from .conftest import valid_shop


def _issuer() -> ApplePassIssuer:
    return ApplePassIssuer(FakeSigner(), team_id="TEAM123", pass_type_id="pass.com.demo")


def _service() -> tuple[PassService, InMemoryShopRepository, InMemoryMemberRepository]:
    shops = InMemoryShopRepository()
    members = InMemoryMemberRepository()
    return PassService(shops, members, _issuer()), shops, members


def _shop(repo):
    body = valid_shop()
    return repo.add(
        Shop(name=body["name"], city=body["city"], design=PassDesign(**body["design"]))
    )


def test_hex_to_rgb():
    assert _hex_to_rgb("#0B5D3B") == "rgb(11, 93, 59)"
    assert _hex_to_rgb("#FFF") == "rgb(255, 255, 255)"


def test_neutral_loyalty_maps_to_apple_store_card():
    shop = _shop(InMemoryShopRepository())
    issued = _issuer().issue(shop)
    with zipfile.ZipFile(io.BytesIO(issued.content)) as z:
        pj = json.loads(z.read("pass.json"))
    assert pj["passTypeIdentifier"] == "pass.com.demo"
    assert pj["teamIdentifier"] == "TEAM123"
    assert "storeCard" in pj  # neutral loyalty → Apple storeCard
    assert pj["serialNumber"] == shop.id  # template pass


def test_coupon_maps_to_apple_coupon():
    shop = InMemoryShopRepository().add(
        Shop(
            name="X",
            city="",
            design=PassDesign(
                pass_type=PassType.coupon, logo_text="X", offer_label="Deal", offer_value="-20%"
            ),
        )
    )
    with zipfile.ZipFile(io.BytesIO(_issuer().issue(shop).content)) as z:
        pj = json.loads(z.read("pass.json"))
    assert "coupon" in pj and "storeCard" not in pj


def test_issue_for_shop_is_a_valid_bundle():
    svc, shops, _ = _service()
    shop = _shop(shops)
    issued = svc.issue_for_shop(shop.id)
    assert issued.platform == "apple"
    assert issued.media_type == "application/vnd.apple.pkpass"
    with zipfile.ZipFile(io.BytesIO(issued.content)) as z:
        names = set(z.namelist())
        assert {
            "pass.json", "icon.png", "icon@2x.png", "logo.png", "logo@2x.png",
            "manifest.json", "signature",
        } <= names
        manifest = json.loads(z.read("manifest.json"))
        for name, digest in manifest.items():
            assert hashlib.sha1(z.read(name)).hexdigest() == digest


def test_issue_for_member_uses_serial_and_stamps():
    svc, shops, members = _service()
    shop = _shop(shops)
    member = members.add(Member(shop_id=shop.id, name="Νίκος", email="nikos@example.com"))
    members.save(member.model_copy(update={"stamps": 3}))
    issued = svc.issue_for_member(member.id)
    assert issued.filename == f"{member.serial_number}.pkpass"
    with zipfile.ZipFile(io.BytesIO(issued.content)) as z:
        pj = json.loads(z.read("pass.json"))
    assert pj["serialNumber"] == member.serial_number  # unique per customer
    stamp_fields = [f for f in pj["storeCard"]["secondaryFields"] if f["key"] == "stamps"]
    assert stamp_fields and stamp_fields[0]["value"] == "3"


def test_issue_unknown_raises():
    svc, _, _ = _service()
    with pytest.raises(ShopNotFound):
        svc.issue_for_shop("shop-404")
    with pytest.raises(MemberNotFound):
        svc.issue_for_member("mem-404")
