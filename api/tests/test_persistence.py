"""Postgres adapters — integration tests against a real database.

Skipped unless PASSLY_TEST_DATABASE_URL is set, so CI and the offline suite
stay database-free (the HTTP tests use the in-memory repositories). A separate
variable from DATABASE_URL on purpose: these tests truncate every table, and
pointing them at a dev database by accident should not be one typo away.

    docker run -d --name passly-pg -e POSTGRES_PASSWORD=passly \
        -e POSTGRES_DB=passly -p 55432:5432 postgres:16-alpine
    psql "$PASSLY_TEST_DATABASE_URL" -f ../supabase/migrations/0001_initial_schema.sql
    PASSLY_TEST_DATABASE_URL=postgresql://postgres:passly@localhost:55432/passly pytest
"""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.skipif(
    not os.environ.get("PASSLY_TEST_DATABASE_URL"),
    reason="PASSLY_TEST_DATABASE_URL not set — skipping Postgres integration tests",
)

psycopg = pytest.importorskip("psycopg")
psycopg_pool = pytest.importorskip("psycopg_pool")

from app.adapters.outbound.postgres_campaign_repository import (  # noqa: E402
    PostgresCampaignRepository,
)
from app.adapters.outbound.postgres_member_repository import (  # noqa: E402
    PostgresMemberRepository,
)
from app.adapters.outbound.postgres_shop_repository import (  # noqa: E402
    PostgresShopRepository,
)
from app.domain.models import (  # noqa: E402
    CampaignState,
    CampaignStatus,
    Member,
    PassDesign,
    ReviewGate,
    Shop,
)


@pytest.fixture
def pool():
    from psycopg.rows import dict_row
    from psycopg_pool import ConnectionPool

    p = ConnectionPool(
        os.environ["PASSLY_TEST_DATABASE_URL"],
        min_size=1,
        max_size=2,
        kwargs={"row_factory": dict_row},
        open=True,
    )
    with p.connection() as conn:
        conn.execute("truncate shops, pass_designs, members, campaigns cascade")
    yield p
    p.close()


@pytest.fixture
def shops(pool):
    return PostgresShopRepository(pool)


@pytest.fixture
def members(pool):
    return PostgresMemberRepository(pool)


def _shop() -> Shop:
    return Shop(
        name="Chunky Cookie Bar",
        city="Αθήνα",
        design=PassDesign(
            logo_text="CCB",
            offer_label="Loyalty",
            offer_value="Στα 9 cookies, το 10ο κέρασμα",
            stamps_goal=9,
        ),
    )


# ── shops + designs ──────────────────────────────────────────────────────


def test_shop_round_trips_through_columns(shops):
    """The nested PassDesign survives being split across two tables."""
    saved = shops.add(_shop())
    got = shops.get(saved.id)

    assert got is not None
    assert got.name == "Chunky Cookie Bar"  # Greek text round-trips
    assert got.city == "Αθήνα"
    assert got.design.offer_value == "Στα 9 cookies, το 10ο κέρασμα"
    assert got.design.stamps_goal == 9
    assert got.design.background_color == "#0B5D3B"  # column default path
    assert got == saved


def test_shops_list_in_insertion_order(shops):
    a = shops.add(_shop())
    b = shops.add(_shop())
    assert [s.id for s in shops.list()] == [a.id, b.id]


def test_save_persists_shop_details_and_leaves_design(shops):
    saved = shops.add(_shop())
    updated = saved.model_copy(
        update={
            "name": "Chunky Cookie Bar II",
            "address": "Ermou 12, Athens",
            "email": "owner@example.com",
            "phone": "+30 694 1234567",
            "instagram_handle": "chunky_cookie_bar",
            "facebook_page_url": "https://facebook.com/chunkycookiebar",
            "google_maps_url": "https://goo.gl/maps/abc123",
        }
    )
    shops.save(updated)

    got = shops.get(saved.id)
    assert got is not None
    assert got.name == "Chunky Cookie Bar II"
    assert got.address == "Ermou 12, Athens"
    assert got.email == "owner@example.com"
    assert got.instagram_handle == "chunky_cookie_bar"
    assert got.design == saved.design  # save() doesn't touch pass_designs


def test_unknown_shop_is_none(shops):
    assert shops.get("shop_doesnotexist") is None


def test_design_is_written_in_the_same_transaction(shops, pool):
    """A shop is never readable without its design (the reads inner-join)."""
    saved = shops.add(_shop())
    with pool.connection() as conn:
        row = conn.execute(
            "select count(*) as n from pass_designs where shop_id = %s", (saved.id,)
        ).fetchone()
    assert row["n"] == 1


# ── members ──────────────────────────────────────────────────────────────


def test_members_persist_with_unique_serials(shops, members):
    shop = shops.add(_shop())
    a = members.add(Member(shop_id=shop.id, name="Νίκος", email="nikos@example.com"))
    b = members.add(Member(shop_id=shop.id, name="Μαρία", email="maria@example.com"))

    assert a.serial_number != b.serial_number
    assert a.created_at  # the database supplied it
    assert [m.name for m in members.list_for_shop(shop.id)] == ["Νίκος", "Μαρία"]


def test_email_is_case_insensitive_identity(shops, members):
    """The bug the SQLite schema had: UNIQUE was case-sensitive while lookups
    were not, so one customer could end up holding two passes."""
    shop = shops.add(_shop())
    created = members.add(Member(shop_id=shop.id, name="N", email="Nikos@Example.COM"))

    assert created.email == "nikos@example.com"
    assert members.find_by_email(shop.id, "NIKOS@EXAMPLE.COM").id == created.id
    assert members.find_by_email(shop.id, "  nikos@example.com  ").id == created.id

    with pytest.raises(psycopg.errors.UniqueViolation):
        members.add(Member(shop_id=shop.id, name="N", email="NIKOS@example.com"))


def test_same_email_may_join_two_different_shops(shops, members):
    one, two = shops.add(_shop()), shops.add(_shop())
    a = members.add(Member(shop_id=one.id, email="nikos@example.com"))
    b = members.add(Member(shop_id=two.id, email="nikos@example.com"))
    assert a.id != b.id and a.serial_number != b.serial_number


def test_save_persists_stamps_and_leaves_identity_alone(shops, members):
    shop = shops.add(_shop())
    member = members.add(Member(shop_id=shop.id, name="Νίκος", email="n@example.com"))

    updated = members.save(member.model_copy(update={"stamps": 5, "rewards": 1}))

    assert (updated.stamps, updated.rewards) == (5, 1)
    assert updated.serial_number == member.serial_number
    assert updated.email == member.email
    assert updated.created_at == member.created_at
    assert members.get(member.id).stamps == 5


def test_saving_an_unknown_member_raises(shops, members):
    shop = shops.add(_shop())
    ghost = members.add(Member(shop_id=shop.id, email="x@example.com")).model_copy(
        update={"id": "mem_gone"}
    )
    with pytest.raises(KeyError):
        members.save(ghost)


def test_member_of_an_unknown_shop_is_rejected(members):
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        members.add(Member(shop_id="shop_doesnotexist", email="x@example.com"))


def test_deleting_a_shop_cascades_to_its_members(shops, members, pool):
    shop = shops.add(_shop())
    member = members.add(Member(shop_id=shop.id, email="x@example.com"))
    with pool.connection() as conn:
        conn.execute("delete from shops where id = %s", (shop.id,))
    assert members.get(member.id) is None


# ── campaigns ────────────────────────────────────────────────────────────


def test_campaign_gate_round_trips_and_is_cleared_on_terminal(shops, pool):
    campaigns = PostgresCampaignRepository(pool)
    shop = shops.add(_shop())

    gated = campaigns.save(
        shop.id,
        CampaignState(
            thread_id="camp_abc123",
            status=CampaignStatus.awaiting_review,
            gate=ReviewGate(turn=1, artifact="draft v1", options=["approve", "kill"]),
        ),
    )
    assert gated.gate.options == ["approve", "kill"]
    assert campaigns.get("camp_abc123").gate.artifact == "draft v1"

    # Same thread_id → upsert, and the stale gate must not survive.
    shipped = campaigns.save(
        shop.id,
        CampaignState(
            thread_id="camp_abc123",
            status=CampaignStatus.shipped,
            final_artifact="final copy",
        ),
    )
    assert shipped.gate is None
    assert shipped.final_artifact == "final copy"


def test_unknown_campaign_is_none(pool):
    assert PostgresCampaignRepository(pool).get("camp_nope") is None
