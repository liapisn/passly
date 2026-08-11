"""Member use-case tests — pure core with in-memory repos."""

from __future__ import annotations

import pytest

from app.adapters.outbound.memory_member_repository import InMemoryMemberRepository
from app.adapters.outbound.memory_shop_repository import InMemoryShopRepository
from app.domain.errors import MemberNotFound, ShopNotFound
from app.domain.models import PassDesign, Shop
from app.services.member_service import MemberService


def _svc() -> tuple[MemberService, InMemoryShopRepository]:
    shops = InMemoryShopRepository()
    return MemberService(shops, InMemoryMemberRepository()), shops


def _shop(repo) -> str:
    return repo.add(
        Shop(name="Chunky", city="Αθήνα", design=PassDesign(
            logo_text="C", offer_label="Loyalty", offer_value="9→10"))
    ).id


def test_enroll_unknown_shop_raises():
    svc, _ = _svc()
    with pytest.raises(ShopNotFound):
        svc.enroll("shop-404", "Νίκος")


def test_enroll_mints_unique_serials():
    svc, shops = _svc()
    sid = _shop(shops)
    a = svc.enroll(sid, "Νίκος")
    b = svc.enroll(sid, "Μαρία")
    assert a.serial_number != b.serial_number
    assert a.stamps == 0
    assert {m.name for m in svc.list_for_shop(sid)} == {"Νίκος", "Μαρία"}


def test_add_stamp_increments():
    svc, shops = _svc()
    sid = _shop(shops)
    m = svc.enroll(sid, "Νίκος")
    svc.add_stamp(m.id)
    svc.add_stamp(m.id)
    assert svc.get(m.id).stamps == 2


def test_get_unknown_member_raises():
    svc, _ = _svc()
    with pytest.raises(MemberNotFound):
        svc.get("mem-404")
