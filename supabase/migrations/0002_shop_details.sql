-- Shop details page — contact info + social links, editable separately from
-- the pass design (api/app/domain/models.py: Shop / ShopDetails).
--
-- All new columns default to '' so existing rows (and the pass designer's
-- `POST /shops`, which doesn't collect them) stay valid without a backfill.

alter table public.shops
    drop constraint shops_name_check,
    add  constraint shops_name_check check (length(name) between 1 and 100);

alter table public.shops
    add column address           text not null default '' check (length(address) <= 200),
    add column email             text not null default '' check (length(email) <= 120),
    add column phone             text not null default '' check (length(phone) <= 20),
    add column instagram_handle  text not null default '' check (length(instagram_handle) <= 30),
    add column facebook_page_url text not null default '' check (length(facebook_page_url) <= 200),
    add column google_maps_url   text not null default '' check (length(google_maps_url) <= 300);
