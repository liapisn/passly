"""Member use cases — enrolling a customer, tracking stamps, re-issuing passes.

Depends only on ports (ShopRepository, MemberRepository, optional EmailSender),
so it is testable with fakes and never imports the framework.
"""

from __future__ import annotations

import logging

from ..domain.errors import MemberNotFound, ShopNotFound
from ..domain.models import Member, MemberRecord
from ..domain.ports import EmailSender, MemberRepository, ShopRepository

_log = logging.getLogger("passly.member")


class MemberService:
    def __init__(
        self,
        shops: ShopRepository,
        members: MemberRepository,
        email_sender: EmailSender | None = None,
        pass_link_base: str = "",
    ) -> None:
        self._shops = shops
        self._members = members
        self._email = email_sender
        self._pass_link_base = pass_link_base.rstrip("/")

    def find(self, shop_id: str, email: str) -> MemberRecord | None:
        return self._members.find_by_email(shop_id, email)

    def enroll(self, shop_id: str, name: str, email: str) -> MemberRecord:
        if self._shops.get(shop_id) is None:
            raise ShopNotFound(shop_id)
        # One pass per email per shop — re-enrolling returns the same pass.
        existing = self._members.find_by_email(shop_id, email)
        if existing is not None:
            return existing
        member = self._members.add(Member(shop_id=shop_id, name=name, email=email))
        self._email_pass(member)  # new member → send them their pass link
        return member

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
        """+1 stamp. On reaching the shop's stamps_goal, the card completes:
        a reward is granted and the stamp count resets to 0."""
        member = self.get(member_id)
        shop = self._shops.get(member.shop_id)
        goal = shop.design.stamps_goal if shop else 10

        if member.stamps + 1 >= goal:
            update = {"stamps": 0, "rewards": member.rewards + 1}
        else:
            update = {"stamps": member.stamps + 1}
        return self._members.save(member.model_copy(update=update))

    def _email_pass(self, member: MemberRecord) -> None:
        """Best-effort — email the customer a link to their pass. A send failure
        must never break enrolment."""
        if self._email is None:
            _log.info("No email sender configured — skipping pass email for %s", member.email)
            return
        link = f"{self._pass_link_base}/members/{member.id}/pkpass"
        try:
            _log.info("Emailing pass link to %s (%s)", member.email, link)
            self._email.send(
                to=member.email,
                subject="Η κάρτα σου είναι έτοιμη 🍪",
                body=(
                    f"Γεια σου {member.name or 'φίλε'},<br><br>"
                    f'Η κάρτα πιστότητάς σου είναι έτοιμη — '
                    f'<a href="{link}">πρόσθεσέ τη στο Apple Wallet</a>.<br><br>'
                    f"Κράτα αυτό το email για να την ξανακατεβάσεις όποτε θες."
                ),
            )
        except Exception as exc:  # noqa: BLE001 — best-effort; never blocks enrolment
            _log.warning("Pass email to %s FAILED: %s", member.email, exc)
