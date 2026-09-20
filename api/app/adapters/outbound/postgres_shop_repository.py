"""Postgres ShopRepository — real columns across `shops` + `pass_designs`.

The SQLite adapter this replaces stored the whole `ShopRecord` as a JSON blob;
here every field is a column, and the nested `PassDesign` is its own table
joined 1:1 on `shop_id`. Reassembly back into the pydantic model happens in
`_to_record`, so the services and the HTTP contract are unchanged.

A shop and its design are written in one transaction, so the inner join in
every read is safe: a shop row without a design cannot be committed.
"""

from __future__ import annotations

from ...domain.ids import small_id
from ...domain.models import PassDesign, Shop, ShopRecord
from .db import get_pool

# Column list shared by every read, so the joined shape stays in one place.
_SELECT = """
    select s.id, s.name, s.city, s.address, s.email, s.phone,
           s.instagram_handle, s.facebook_page_url, s.google_maps_url,
           d.pass_type, d.logo_text,
           d.offer_label, d.offer_value,
           d.secondary_label, d.secondary_value,
           d.background_color, d.foreground_color, d.label_color,
           d.barcode_message, d.stamps_goal
      from shops s
      join pass_designs d on d.shop_id = s.id
"""


def _to_record(row: dict) -> ShopRecord:
    """One joined row → the nested domain model."""
    return ShopRecord(
        id=row["id"],
        name=row["name"],
        city=row["city"],
        address=row["address"],
        email=row["email"],
        phone=row["phone"],
        instagram_handle=row["instagram_handle"],
        facebook_page_url=row["facebook_page_url"],
        google_maps_url=row["google_maps_url"],
        design=PassDesign(
            pass_type=row["pass_type"],
            logo_text=row["logo_text"],
            offer_label=row["offer_label"],
            offer_value=row["offer_value"],
            secondary_label=row["secondary_label"],
            secondary_value=row["secondary_value"],
            background_color=row["background_color"],
            foreground_color=row["foreground_color"],
            label_color=row["label_color"],
            barcode_message=row["barcode_message"],
            stamps_goal=row["stamps_goal"],
        ),
    )


class PostgresShopRepository:
    def __init__(self, pool=None) -> None:
        self._pool = pool or get_pool()

    def add(self, shop: Shop) -> ShopRecord:
        shop_id = small_id("shop")
        d = shop.design
        # One transaction: a shop is never visible without its design.
        with self._pool.connection() as conn:
            conn.execute(
                """
                insert into shops (
                    id, name, city, address, email, phone,
                    instagram_handle, facebook_page_url, google_maps_url
                ) values (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    shop_id,
                    shop.name,
                    shop.city,
                    shop.address,
                    shop.email,
                    shop.phone,
                    shop.instagram_handle,
                    shop.facebook_page_url,
                    shop.google_maps_url,
                ),
            )
            conn.execute(
                """
                insert into pass_designs (
                    id, shop_id, pass_type, logo_text,
                    offer_label, offer_value, secondary_label, secondary_value,
                    background_color, foreground_color, label_color,
                    barcode_message, stamps_goal
                ) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    small_id("dsgn"),
                    shop_id,
                    d.pass_type.value,
                    d.logo_text,
                    d.offer_label,
                    d.offer_value,
                    d.secondary_label,
                    d.secondary_value,
                    d.background_color,
                    d.foreground_color,
                    d.label_color,
                    d.barcode_message,
                    d.stamps_goal,
                ),
            )
        return ShopRecord(id=shop_id, **shop.model_dump())

    def list(self) -> list[ShopRecord]:
        with self._pool.connection() as conn:
            rows = conn.execute(_SELECT + " order by s.seq").fetchall()
        return [_to_record(r) for r in rows]

    def get(self, shop_id: str) -> ShopRecord | None:
        with self._pool.connection() as conn:
            row = conn.execute(_SELECT + " where s.id = %s", (shop_id,)).fetchone()
        return _to_record(row) if row else None

    def save(self, shop: ShopRecord) -> ShopRecord:
        """Persist mutations to the shop-details columns. `design` is owned by
        the pass designer and isn't written here."""
        with self._pool.connection() as conn:
            conn.execute(
                """
                update shops
                   set name = %s, city = %s, address = %s, email = %s,
                       phone = %s, instagram_handle = %s,
                       facebook_page_url = %s, google_maps_url = %s
                 where id = %s
                """,
                (
                    shop.name,
                    shop.city,
                    shop.address,
                    shop.email,
                    shop.phone,
                    shop.instagram_handle,
                    shop.facebook_page_url,
                    shop.google_maps_url,
                    shop.id,
                ),
            )
        return shop
