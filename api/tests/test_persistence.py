"""SQLite adapters — data survives across repository instances (i.e. restarts)."""

from __future__ import annotations

from app.adapters.outbound.sqlite_member_repository import SqliteMemberRepository
from app.adapters.outbound.sqlite_shop_repository import SqliteShopRepository
from app.domain.models import Member, PassDesign, Shop


def _shop() -> Shop:
    return Shop(
        name="Chunky Cookie Bar",
        city="Αθήνα",
        design=PassDesign(logo_text="CCB", offer_label="Loyalty", offer_value="9→10"),
    )


def test_shops_survive_a_new_repo_instance(tmp_path):
    db = tmp_path / "passly.db"
    saved = SqliteShopRepository(db).add(_shop())

    # A fresh instance on the same file = a process restart.
    reopened = SqliteShopRepository(db)
    got = reopened.get(saved.id)
    assert got is not None
    assert got.name == "Chunky Cookie Bar"  # Greek text round-trips
    assert [s.id for s in reopened.list()] == [saved.id]


def test_members_survive_and_serial_is_unique(tmp_path):
    db = tmp_path / "passly.db"
    repo = SqliteMemberRepository(db)
    a = repo.add(Member(shop_id="shop-1", name="Νίκος"))
    b = repo.add(Member(shop_id="shop-1", name="Μαρία"))
    assert a.serial_number != b.serial_number

    reopened = SqliteMemberRepository(db)
    reopened.save(a.model_copy(update={"stamps": 5}))
    assert reopened.get(a.id).stamps == 5
    assert {m.name for m in reopened.list_for_shop("shop-1")} == {"Νίκος", "Μαρία"}
