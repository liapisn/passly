"""Unit tests for the shop use cases — pure core, no HTTP, no framework.

This is the payoff of the hexagonal split: the business logic is exercised
directly against an in-memory repository double.
"""

from __future__ import annotations

import pytest

from app.adapters.outbound.memory_shop_repository import InMemoryShopRepository
from app.domain.errors import ShopNotFound
from app.domain.models import PassDesign, PassType, Shop, ShopDetails
from app.services.shop_service import ShopService


def _shop(name: str = "Καφέ Μαρία") -> Shop:
    return Shop(
        name=name,
        city="Σύρος",
        design=PassDesign(
            pass_type=PassType.loyalty,
            logo_text="ΚΑΦΕ ΜΑΡΙΑ",
            offer_label="Loyalty",
            offer_value="Buy 9, get the 10th free",
        ),
    )


def _service() -> ShopService:
    return ShopService(InMemoryShopRepository())


def test_create_assigns_id_and_persists():
    svc = _service()
    record = svc.create_shop(_shop())
    assert record.id.startswith("shop_")  # non-sequential smallId
    assert record.name == "Καφέ Μαρία"
    assert svc.get_shop(record.id) is record


def test_ids_are_unique_and_list_returns_all():
    svc = _service()
    a = svc.create_shop(_shop("A"))
    b = svc.create_shop(_shop("B"))
    assert a.id != b.id and a.id.startswith("shop_") and b.id.startswith("shop_")
    records = svc.list_shops()
    assert {r.name for r in records} == {"A", "B"}


def test_get_missing_raises_domain_error():
    svc = _service()
    with pytest.raises(ShopNotFound) as exc:
        svc.get_shop("shop-404")
    assert exc.value.shop_id == "shop-404"


def test_hex_colour_is_normalised_uppercase():
    design = PassDesign(
        logo_text="X",
        offer_label="L",
        offer_value="V",
        background_color="#0b5d3b",
    )
    assert design.background_color == "#0B5D3B"


def test_update_details_persists_contact_fields_and_keeps_design():
    svc = _service()
    record = svc.create_shop(_shop())
    details = ShopDetails(
        name="Καφέ Μαρία ΙΙ",
        address="Οδός Ερμού 12, Σύρος",
        email="maria@example.com",
        phone="+30 694 1234567",
        instagram_handle="cafe_maria",
        facebook_page_url="https://facebook.com/cafemaria",
        google_maps_url="https://goo.gl/maps/abc123",
    )
    updated = svc.update_details(record.id, details)
    assert updated.id == record.id
    assert updated.name == "Καφέ Μαρία ΙΙ"
    assert updated.address == "Οδός Ερμού 12, Σύρος"
    assert updated.email == "maria@example.com"
    assert updated.design == record.design  # untouched by the details form


def test_update_details_missing_shop_raises_domain_error():
    svc = _service()
    details = ShopDetails(name="X", address="Οδός Χ 1", email="x@example.com")
    with pytest.raises(ShopNotFound):
        svc.update_details("shop-404", details)
