"""Member use cases — enrolling a customer in a shop's pass and tracking stamps.

Depends only on the ShopRepository + MemberRepository ports.
"""

from __future__ import annotations

from ..domain.errors import MemberNotFound, ShopNotFound
from ..domain.models import Member, MemberRecord
from ..domain.ports import MemberRepository, ShopRepository


class MemberService:
    def __init__(self, shops: ShopRepository, members: MemberRepository) -> None:
        self._shops = shops
        self._members = members

    def enroll(self, shop_id: str, name: str, email: str) -> MemberRecord:
        if self._shops.get(shop_id) is None:
            raise ShopNotFound(shop_id)
        # One pass per email per shop — re-enrolling returns the same pass.
        existing = self._members.find_by_email(shop_id, email)
        if existing is not None:
            return existing
        return self._members.add(Member(shop_id=shop_id, name=name, email=email))

    def list_for_shop(self, shop_id: str) -> list[MemberRecord]:
        if self._shops.get(shop_id) is None:
            raise ShopNotFound(shop_id)
        return self._members.list_for_shop(shop_id)

    def get(self, member_id: str) -> MemberRecord:
        member = self._members.get(member_id)
        if member is None:
            raise MemberNotFound(member_id)
        return member

    def add_stamp(self, member_id: str) -> MemberRecord:
        member = self.get(member_id)
        return self._members.save(member.model_copy(update={"stamps": member.stamps + 1}))
