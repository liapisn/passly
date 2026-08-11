-- Passly — initial relational schema (Supabase / Postgres).
--
-- Replaces the SQLite document-store shape (id + n + json blob) with real
-- columns, foreign keys, and domain constraints. The pydantic models in
-- api/app/domain/models.py remain the API contract; the constraints here are
-- the safety net that holds even if a row is written outside the app.
--
-- Ids stay application-generated short ids (api/app/domain/ids.py) rather than
-- uuids: they are already baked into issued Apple passes (serialNumber) and
-- into pass links emailed to customers, so they must not change.

-- ─────────────────────────────────────────────────────────────────────────
-- shops — a merchant. Identity only; pass presentation lives in pass_designs.
-- ─────────────────────────────────────────────────────────────────────────
create table public.shops (
    id          text        primary key check (id like 'shop\_%'),
    seq         bigint      generated always as identity,  -- stable list order
    name        text        not null check (length(name) between 1 and 80),
    city        text        not null default '' check (length(city) <= 80),
    created_at  timestamptz not null default now()
);

comment on column public.shops.seq is
    'Insertion order for list(). Replaces the SQLite MAX(n)+1 counter, which '
    'raced under concurrent inserts.';

-- ─────────────────────────────────────────────────────────────────────────
-- pass_designs — what the founder edits in the designer and what gets signed
-- into the .pkpass. One per shop (1:1, enforced by the unique fk).
-- ─────────────────────────────────────────────────────────────────────────
create table public.pass_designs (
    id                text        primary key check (id like 'dsgn\_%'),
    shop_id           text        not null unique
                                  references public.shops(id) on delete cascade,

    pass_type         text        not null default 'loyalty'
                                  check (pass_type in ('loyalty', 'coupon')),

    logo_text         text        not null check (length(logo_text) between 1 and 40),
    offer_label       text        not null check (length(offer_label) between 1 and 40),
    offer_value       text        not null check (length(offer_value) between 1 and 60),
    secondary_label   text        not null default '' check (length(secondary_label) <= 40),
    secondary_value   text        not null default '' check (length(secondary_value) <= 60),

    -- Normalised to uppercase by the pydantic validator; #RGB or #RRGGBB.
    background_color  text        not null default '#0B5D3B'
                                  check (background_color ~ '^#([0-9A-F]{3}|[0-9A-F]{6})$'),
    foreground_color  text        not null default '#FFFFFF'
                                  check (foreground_color ~ '^#([0-9A-F]{3}|[0-9A-F]{6})$'),
    label_color       text        not null default '#BFE8D4'
                                  check (label_color ~ '^#([0-9A-F]{3}|[0-9A-F]{6})$'),

    barcode_message   text        not null default '' check (length(barcode_message) <= 120),
    stamps_goal       integer     not null default 10 check (stamps_goal between 1 and 99),

    updated_at        timestamptz not null default now()
);

comment on table public.pass_designs is
    'Split from shops so merchant identity and pass presentation evolve '
    'separately — and so design history becomes an additive change (drop the '
    'unique on shop_id, add a validity range) rather than a migration.';

-- ─────────────────────────────────────────────────────────────────────────
-- members — one end customer holding one shop's pass.
--
-- email is the identity: lowercase-normalised, unique per shop. The SQLite
-- schema had UNIQUE(shop_id, email) under BINARY collation while lookups used
-- COLLATE NOCASE, so 'nikos@x.com' and 'Nikos@X.com' both inserted and the
-- "one pass per customer" rule silently broke. The lower() check closes that.
-- ─────────────────────────────────────────────────────────────────────────
create table public.members (
    id             text        primary key check (id like 'mem\_%'),
    seq            bigint      generated always as identity,
    shop_id        text        not null references public.shops(id) on delete cascade,

    name           text        not null default '' check (length(name) <= 80),
    email          text        not null check (
                       email = lower(email)
                       and email ~ '^[^@\s]+@[^@\s]+\.[^@\s]+$'
                       and length(email) <= 120
                   ),

    -- Becomes pass.json serialNumber — globally unique, never reused.
    serial_number  text        not null unique check (serial_number like 'psly\_%'),

    stamps         integer     not null default 0 check (stamps >= 0),
    rewards        integer     not null default 0 check (rewards >= 0),
    created_at     timestamptz not null default now(),

    unique (shop_id, email)
);

-- No separate index on members(shop_id): the unique constraint above builds a
-- btree on (shop_id, email), whose leading column already serves
-- list_for_shop's `where shop_id = ?`.

-- ─────────────────────────────────────────────────────────────────────────
-- campaigns — a crew-drafted launch campaign and its founder gate.
--
-- New in Postgres: the SQLite build kept this only in process memory, which is
-- what stopped the API from running on serverless. Persisting the gate lets
-- start / poll / respond land on three different instances.
-- ─────────────────────────────────────────────────────────────────────────
create table public.campaigns (
    thread_id       text        primary key,   -- LangGraph checkpointer thread id
    seq             bigint      generated always as identity,
    shop_id         text        not null references public.shops(id) on delete cascade,

    status          text        not null check (status in (
                        'drafting', 'awaiting_review',
                        'shipped', 'killed', 'exhausted', 'error'
                    )),

    -- The open gate (status = 'awaiting_review'); null otherwise.
    gate_turn       integer     check (gate_turn is null or gate_turn > 0),
    gate_artifact   text,
    gate_options    text[],

    final_artifact  text,       -- set iff shipped
    error           text,       -- set iff error

    created_at      timestamptz not null default now(),
    updated_at      timestamptz not null default now(),

    -- A run parked at the gate must carry the whole gate, or the founder has
    -- nothing to approve and the UI renders an empty review screen.
    constraint campaigns_gate_complete check (
        status <> 'awaiting_review'
        or (gate_turn is not null and gate_artifact is not null and gate_options is not null)
    ),

    -- Terminal states carry their payload.
    constraint campaigns_terminal_payload check (
        (status <> 'shipped' or final_artifact is not null)
        and (status <> 'error' or error is not null)
    )
);

create index campaigns_shop_id_idx on public.campaigns (shop_id);

-- ─────────────────────────────────────────────────────────────────────────
-- updated_at maintenance
-- ─────────────────────────────────────────────────────────────────────────
create or replace function public.touch_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

create trigger pass_designs_touch_updated_at
    before update on public.pass_designs
    for each row execute function public.touch_updated_at();

create trigger campaigns_touch_updated_at
    before update on public.campaigns
    for each row execute function public.touch_updated_at();

-- ─────────────────────────────────────────────────────────────────────────
-- Row Level Security
--
-- Supabase exposes every table in `public` through PostgREST using the anon
-- key. Passly has no Supabase Auth and never calls PostgREST — the API talks
-- to Postgres directly as the table owner, which bypasses RLS. So: enable RLS
-- and define NO policies. Anonymous REST access gets nothing; the API is
-- unaffected. Without this, anyone with the (publishable) anon key could read
-- and write every customer row.
-- ─────────────────────────────────────────────────────────────────────────
alter table public.shops        enable row level security;
alter table public.pass_designs enable row level security;
alter table public.members      enable row level security;
alter table public.campaigns    enable row level security;
