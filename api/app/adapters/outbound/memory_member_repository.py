"""In-memory MemberRepository — the test double (and a fine dev fallback).

Deterministic ids/serials so tests are stable.
"""

from __future__ import annotations

from ...domain.ids import small_id
from ...domain.models import Member, MemberRecord


class InMemoryMemberRepository:
    def __init__(self) -> None:
        self._members: dict[str, MemberRecord] = {}

    def add(self, member: Member) -> MemberRecord:
        record = MemberRecord(
            id=small_id("mem"),
            serial_number=small_id("psly"),
            stamps=0,
            created_at="",
            **member.model_dump(),
        )
        self._members[record.id] = record
        return record

    def get(self, member_id: str) -> MemberRecord | None:
        return self._members.get(member_id)

    def find_by_email(self, shop_id: str, email: str) -> MemberRecord | None:
        return next(
            (
                m
                for m in self._members.values()
                if m.shop_id == shop_id and m.email.lower() == email.lower()
            ),
            None,
        )

    def list_for_shop(self, shop_id: str) -> list[MemberRecord]:
        return [m for m in self._members.values() if m.shop_id == shop_id]

    def save(self, member: MemberRecord) -> MemberRecord:
        self._members[member.id] = member
        return member
