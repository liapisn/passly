# Passly

Wallet passes + AI marketing for Greek SMBs. The **Ch.4 application** of the
MBA διπλωματική (Liapis 2026) — a working demo where a shop owner creates a
wallet pass ("πάσο") for their shop, with the AI marketing crew drafting the
copy/campaign and the founder approving from the web.

Built on the [`solo-founder-crew`](https://github.com/liapisn/solo-founder-crew)
framework (the thesis Ch.3 contribution), consumed here as a dependency.

> Demo grade, synthetic data. Real customers / billing / GDPR are the
> post-submission Passly-live track. See the crew repo's `docs/roadmap.md`.

## Architecture

```
web/  Next.js UI  ──►  api/  FastAPI  ──►  solo-founder-crew
      "create a pass"     pass issuance      drafts copy/campaign,
                          + orchestration    founder approves (WebHITL)
```

## What it does

The full demo flow, end to end:

1. **Design** a branded wallet pass for a shop, with a live preview.
2. The **AI crew drafts** a launch campaign; the founder approves / edits / discards
   it in the browser (WebHITL — a second adapter on the framework's HITL seam).
3. Customers **join** and get their own **real signed Apple Wallet pass** (unique
   serial number).
4. The shop **stamps** loyalty visits from a console; reaching the goal grants a
   reward and resets the card.
5. Customers **re-download** their pass (welcome-back join, or an emailed link).

Shops and members persist in **SQLite**. Passes are **signed `.pkpass`** (Apple
Wallet); pass issuance sits behind a **`PassIssuer` port**, so Google Wallet is a
future drop-in. The `Member` model is platform-neutral (email = identity, unique
per shop).

## Pages (web · port 3000)

| Route | What |
|-------|------|
| `/` | Landing — Greek problem-first hero, shop scenarios, objections + live API status |
| `/design` | Pass designer — edit + live preview, save, and links onward |
| `/join/[shopId]` | Customer join / re-download — name + email → your pass |
| `/shops/[id]/campaign` | Crew campaign review — draft → approve / send back / discard |
| `/shops/[id]/members` | Members & stamps console — list customers, +1 stamp, goal/rewards |

## API (endpoints · port 8000)

| Method | Path | What |
|--------|------|------|
| GET | `/health` | liveness |
| GET | `/crew/info` | framework smoke check (role catalogue) |
| POST | `/shops` | create a shop + its pass design |
| GET | `/shops` | list shops |
| GET | `/shops/{id}` | get a shop |
| GET | `/shops/{id}/pkpass` | the shop's template pass (`.pkpass`) |
| POST | `/shops/{id}/members` | enrol a customer — `201` new / `200` existing; emails the pass link |
| GET | `/shops/{id}/members` | list a shop's members |
| GET | `/members/{id}` | get a member |
| POST | `/members/{id}/stamp` | +1 stamp (grants a reward and resets at the goal) |
| GET | `/members/{id}/pkpass` | the member's signed pass (unique serial + live stamps) |
| POST | `/shops/{id}/campaign` | start a crew campaign draft (async; poll for the gate) |
| GET | `/campaigns/{thread_id}` | poll campaign state |
| POST | `/campaigns/{thread_id}/respond` | deliver the founder's decision to the gate |

Interactive docs at `http://localhost:8000/docs` when the API is running.

## Status

Phases **P0–P4 shipped** — the demo runs end to end with real Apple-signed
passes and the AI crew. Post-P4 additions: SQLite persistence, the Member model,
loyalty stamp counting with rewards, pass re-download, and emailed pass links.

**Thesis-side work on this repo is closed (2026-08-30).** Chapter 4 is drafted
from this demo and Chapters 2–5 are stitched into a v1; nothing here is on the
thesis critical path, and nothing here needs to change before submission on
2026-09-30. Two things Ch.4 records about this repo, both deliberate and both
disclosed in the chapter rather than fixed:

- **The Crew Generator is not exercised here.** `crew_runner.py` imports
  `make_marketing` from the Role Library directly, so the application uses four
  of the framework's five components (Ch.4 §4.5.1, §4.9.3).
- **The web gate is not durable.** `_WebHITL` holds pending gates as in-memory
  `asyncio.Future` objects, so a campaign gate survives an unbounded wait
  *within* a process but not a restart of it. `deps.py` already wires a
  `PostgresCampaignRepository` for the swap; the runner does not consume it yet.
  The framework's checkpointer property is unimpaired — the application has
  simply not taken it up (Ch.4 §4.9).

Everything else open on this repo is the post-submission Passly-live track
(B0–B6 in the crew repo's roadmap), which is deliberately decoupled from the
thesis and starts in earnest after 30/9.
See the crew repo's [`docs/roadmap.md`](https://github.com/liapisn/solo-founder-crew/blob/main/docs/roadmap.md)
for the full roadmap.

## Running the demo

Passly runs **locally** — web and API on the laptop, Postgres on Supabase.
Nothing is deployed. Once set up (below), one command runs everything:

```bash
python scripts/dev.py --tunnel
```

`--tunnel` opens a public HTTPS URL so a customer's phone can open the join
page and add the pass to Apple Wallet. Because the web app proxies the API
under `/api`, that single URL covers both — no CORS, and no rebuild when the
tunnel hostname changes. Needs `cloudflared` (`brew install cloudflared`);
ngrok also works but its free tier shows an interstitial page to phones.

See [`docs/demo-runbook.md`](docs/demo-runbook.md) for the demo flow, the
pre-demo checklist, and troubleshooting.

## Local development

Requires Python 3.11–3.13 and Node 20+. The `solo-founder-crew` repo must be
checked out as a sibling directory (`../solo-founder-crew`).

### API (port 8000)

```bash
cd api
python3.11 -m venv .venv
.venv/bin/pip install -r requirements-local.txt   # deps + framework (editable)
.venv/bin/uvicorn app.main:app --reload
```

Smoke check: `curl localhost:8000/crew/info` should return the six crew roles.

Requirements are split so CI never needs the private framework repo:

| File | Contains | Used by |
|------|----------|---------|
| `requirements.txt` | fastapi, uvicorn | base |
| `requirements-dev.txt` | base + pytest, httpx, ruff | **CI** (tests fake the framework) |
| `requirements-local.txt` | dev + `solo-founder-crew` editable | running the live server locally |

The API follows a **hexagonal (ports & adapters)** layout so the core stays
framework-free and testable:

```
app/
  domain/     models + ports (Protocols) + errors + ids  — no FastAPI, no framework
  services/   Shop / Crew / Campaign / Member / Pass services — depend only on ports
  adapters/
    inbound/  http.py (FastAPI driving adapter)
    outbound/ db (pool), postgres_shop_repository,
              postgres_member_repository, postgres_campaign_repository,
              apple_pass_issuer, signer, email_sender,
              crew_gateway, crew_runner                 — driven adapters
  deps.py     composition root (which adapter backs which port)
  main.py     app factory (loads api/.env, configures logging)
```

New capabilities drop in as new ports + adapters without touching the services —
e.g. a Google Wallet `PassIssuer` or another `EmailSender`.

### Database (Supabase Postgres)

Shops, pass designs, members, and campaigns live in Postgres. The schema is
[`supabase/migrations/0001_initial_schema.sql`](supabase/migrations/0001_initial_schema.sql)
— real columns and foreign keys, not JSON blobs:

```
shops ──1:1── pass_designs      pass presentation, split from merchant identity
  │
  ├──1:N── members              one customer's pass: serial_number, stamps, rewards
  └──1:N── campaigns            a crew run and its open founder gate
```

Apply it to a fresh project with the Supabase SQL editor, or:

```bash
psql "$DATABASE_URL" -f supabase/migrations/0001_initial_schema.sql
```

RLS is enabled on every table with **no policies**: Passly never calls
PostgREST, so anonymous REST access gets nothing while the API — connecting
directly as the table owner — is unaffected.

Coming from the old SQLite store? [`scripts/migrate_sqlite_to_postgres.py`](scripts/migrate_sqlite_to_postgres.py)
carries rows across, preserving member ids and pass serial numbers so already-issued
passes keep working. It dry-runs by default.

### Configuration (`api/.env`)

Auto-loaded on startup. Copy `api/.env.example` and fill in `DATABASE_URL`
(**required** — the API will not start without it). Then, optionally: Apple
signing (`APPLE_CERT_P12` + password, `APPLE_WWDR_CERT`, team / pass-type ids)
for real `.pkpass` signing, and `RESEND_API_KEY` (+ `PASSLY_PUBLIC_URL`) to
email pass links. Those optional keys degrade gracefully when missing (unsigned
bundle, no-op email sender, MockLLM) so the demo still runs.

### Repository secrets (GitHub Actions — *not* `api/.env`)

One setting lives in GitHub rather than in `api/.env`, because CI uses it and
the app never does:

| Secret | Used by | What it does |
|--------|---------|--------------|
| `DISCORD_WEBHOOK_URL` | [`pr-review-notify.yml`](.github/workflows/pr-review-notify.yml) | Posts a PR to Discord once CI passes, so the founder can review and merge — the notify half of the Dev Flow merge gate |

Putting it in `api/.env` would do nothing: it is read as
`${{ secrets.DISCORD_WEBHOOK_URL }}` inside the workflow, never by the FastAPI
service.

To set it: in Discord, target channel → **Edit Channel → Integrations →
Webhooks → New Webhook → Copy Webhook URL**. Then in GitHub, repo **Settings →
Secrets and variables → Actions → New repository secret**, named
`DISCORD_WEBHOOK_URL`.

Optional — with the secret absent the notify job logs a warning and no-ops, so
CI stays green either way.

Tests:

```bash
cd api
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/pytest
```

The suite needs no database — the HTTP and service tests use the in-memory
repositories. The Postgres adapter tests skip unless you point them at a
throwaway database (a separate variable from `DATABASE_URL`, because they
truncate every table):

```bash
docker run -d --name passly-pg -e POSTGRES_PASSWORD=passly -e POSTGRES_DB=passly -p 55432:5432 postgres:16-alpine
psql postgresql://postgres:passly@localhost:55432/passly -f ../supabase/migrations/0001_initial_schema.sql
PASSLY_TEST_DATABASE_URL=postgresql://postgres:passly@localhost:55432/passly .venv/bin/pytest
```

### Web (port 3000)

```bash
cd web
cp .env.local.example .env.local
npm install
npm run dev
```

Open http://localhost:3000 — the status card confirms the
Next.js → FastAPI → solo-founder-crew chain is live.

`NEXT_PUBLIC_SITE_URL` is the origin the landing page uses for its canonical
link, OG tags and JSON-LD ids. Leave it unset while nothing is deployed (it
falls back to `http://localhost:3000`); set it the day Passly has a domain.
The keyword and schema decisions behind that page are in
[`docs/seo-keyword-map.md`](docs/seo-keyword-map.md).
