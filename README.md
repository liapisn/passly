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
| `/` | Landing — hero + live API status |
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
See the crew repo's [`docs/roadmap.md`](https://github.com/liapisn/solo-founder-crew/blob/main/docs/roadmap.md)
for the full roadmap.

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
    outbound/ sqlite_shop_repository, sqlite_member_repository,
              apple_pass_issuer, signer, email_sender,
              crew_gateway, crew_runner                 — driven adapters
  deps.py     composition root (which adapter backs which port)
  main.py     app factory (loads api/.env, configures logging)
```

New capabilities drop in as new ports + adapters without touching the services —
e.g. a Postgres repository, a Google Wallet `PassIssuer`, or another `EmailSender`.

### Configuration (`api/.env`)

Auto-loaded on startup. Copy `api/.env.example` and fill in:
Apple signing (`APPLE_CERT_P12` + password, `APPLE_WWDR_CERT`, team / pass-type
ids) for real `.pkpass` signing; `RESEND_API_KEY` (+ `PASSLY_PUBLIC_URL`) to email
pass links; `PASSLY_DB` for the SQLite path. Missing keys degrade gracefully
(unsigned bundle, no-op email sender, MockLLM) so the demo still runs.

Tests:

```bash
cd api
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/pytest
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
