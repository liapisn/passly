"""Pass issuance use case — platform-neutral.

Fetches the shop (and, for a customer pass, the member) and delegates the
actual wallet-pass construction to the `PassIssuer` port. Knows nothing about
Apple vs Google — swapping the issuer adapter is all it takes to add a platform.
"""

from __future__ import annotations

from ..domain.errors import MemberNotFound, ShopNotFound
from ..domain.issued_pass import IssuedPass
from ..domain.ports import MemberRepository, PassIssuer, ShopRepository


class PassService:
    def __init__(
        self,
        shops: ShopRepository,
        members: MemberRepository,
        issuer: PassIssuer,
    ) -> None:
        self._shops = shops
        self._members = members
        self._issuer = issuer

    def issue_for_shop(self, shop_id: str) -> IssuedPass:
        """Template pass for a shop (serial = shop id, no stamps)."""
        shop = self._shops.get(shop_id)
        if shop is None:
            raise ShopNotFound(shop_id)
        return self._issuer.issue(shop)

    def issue_for_member(self, member_id: str) -> IssuedPass:
        """A specific customer's pass — unique serial, current stamp count and
        the holder's name."""
        member = self._members.get(member_id)
        if member is None:
            raise MemberNotFound(member_id)
        shop = self._shops.get(member.shop_id)
        if shop is None:
            raise ShopNotFound(member.shop_id)
        return self._issuer.issue(
            shop,
            serial_number=member.serial_number,
            stamps=member.stamps,
            member_name=member.name,
        )
