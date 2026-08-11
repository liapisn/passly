"""Member use-case tests — pure core with in-memory repos."""

from __future__ import annotations

import pytest

from app.adapters.outbound.email_sender import FakeEmailSender
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
        svc.enroll("shop-404", "Νίκος", "nikos@example.com")


def test_enroll_mints_unique_serials():
    svc, shops = _svc()
    sid = _shop(shops)
    a = svc.enroll(sid, "Νίκος", "nikos@example.com")
    b = svc.enroll(sid, "Μαρία", "maria@example.com")
    assert a.serial_number != b.serial_number
    assert a.stamps == 0
    assert {m.name for m in svc.list_for_shop(sid)} == {"Νίκος", "Μαρία"}


def test_same_email_returns_same_member():
    svc, shops = _svc()
    sid = _shop(shops)
    a = svc.enroll(sid, "Νίκος", "nikos@example.com")
    again = svc.enroll(sid, "Nikolas", "NIKOS@example.com")  # case-insensitive
    assert again.id == a.id  # idempotent — one pass per email per shop
    assert len(svc.list_for_shop(sid)) == 1


def test_add_stamp_increments():
    svc, shops = _svc()
    sid = _shop(shops)  # default goal 10
    m = svc.enroll(sid, "Νίκος", "nikos@example.com")
    svc.add_stamp(m.id)
    svc.add_stamp(m.id)
    assert svc.get(m.id).stamps == 2
    assert svc.get(m.id).rewards == 0


def test_reaching_goal_grants_reward_and_resets():
    svc, shops = _svc()
    sid = shops.add(
        Shop(
            name="X",
            city="",
            design=PassDesign(
                logo_text="X", offer_label="L", offer_value="V", stamps_goal=2
            ),
        )
    ).id
    m = svc.enroll(sid, "Νίκος", "nikos@example.com")
    svc.add_stamp(m.id)         # 1/2
    done = svc.add_stamp(m.id)  # 2/2 → reward + reset
    assert done.stamps == 0
    assert done.rewards == 1


def test_get_unknown_member_raises():
    svc, _ = _svc()
    with pytest.raises(MemberNotFound):
        svc.get("mem-404")


def test_new_member_is_emailed_their_pass_once():
    shops = InMemoryShopRepository()
    members = InMemoryMemberRepository()
    email = FakeEmailSender()
    svc = MemberService(shops, members, email, "https://passly.test")
    sid = _shop(shops)

    m = svc.enroll(sid, "Νίκος", "nikos@example.com")
    assert len(email.sent) == 1
    assert email.sent[0]["to"] == "nikos@example.com"
    assert f"/members/{m.id}/pkpass" in email.sent[0]["body"]

    # Re-enrolling the same email (a re-download) sends no second email.
    svc.enroll(sid, "Νίκος", "nikos@example.com")
    assert len(email.sent) == 1
