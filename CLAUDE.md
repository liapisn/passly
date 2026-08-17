# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Passly is the Ch.4 application of an MBA thesis: wallet passes + AI marketing for Greek SMBs. It is demo-grade with synthetic data, runs only locally (nothing is deployed), and consumes the private [`solo-founder-crew`](https://github.com/liapisn/solo-founder-crew) framework — which must be checked out as a **sibling directory** (`../solo-founder-crew`) for the live server.

## Commands

Run everything (API + web, optional public tunnel for phones):

```bash
python scripts/dev.py               # http://localhost:3000
python scripts/dev.py --tunnel      # + public HTTPS URL (needs cloudflared)
```

API (`api/`, port 8000) — always run from the `api/` directory; `.env` paths resolve relative to it:

```bash
.venv/bin/pip install -r requirements-local.txt   # deps + framework (editable)
.venv/bin/uvicorn app.main:app --reload
.venv/bin/pytest                                  # full suite, no DB needed
.venv/bin/pytest tests/test_http.py::test_name    # single test
ruff check . ../scripts                           # exactly what CI lints
```

Web (`web/`, port 3000):

```bash
npm run dev
npm run build     # CI's only web check — runs ESLint + TypeScript
```

Database (Supabase Postgres):

```bash
python scripts/check_supabase.py                  # read-only pre-flight
python scripts/apply_migrations.py --commit       # dry-runs without --commit
python scripts/migrate_sqlite_to_postgres.py      # legacy SQLite → PG, dry-runs by default
```

## Requirements split (don't collapse it)

| File | Contains | Used by |
|------|----------|---------|
| `requirements.txt` | fastapi, uvicorn | base |
| `requirements-dev.txt` | + pytest, httpx, ruff | **CI** |
| `requirements-local.txt` | + `solo-founder-crew` editable | live local server |

CI never installs the private framework. This works because the framework is imported **lazily inside methods** (`crew_runner.py`, `crew_gateway.py`) and the tests substitute fakes at the composition seam. Any new framework import must stay lazy, or CI breaks.

## Architecture

```
web/ (Next.js, :3000) ──/api proxy──► api/ (FastAPI, :8000) ──► solo-founder-crew
```

### API — hexagonal (ports & adapters)

```
app/
  domain/     models (pydantic) + ports (Protocols) + errors + ids — no FastAPI, no framework
  services/   Shop / Crew / Campaign / Member / Pass — depend only on ports
  adapters/
    inbound/  http.py — the FastAPI router
    outbound/ postgres_* repos, memory_* repos, apple_pass_issuer, signer,
              email_sender, crew_gateway, crew_runner
  deps.py     composition root — the ONE place that picks which adapter backs which port
  main.py     app factory; loads api/.env before anything reads os.environ
```

Adding a capability: define the Protocol in `domain/ports.py` → use it from a service → write the adapter → wire it in `deps.py`. Services must never import an adapter or the framework directly. A Google Wallet issuer, for instance, is a second `PassIssuer` and nothing else changes.

`deps.py` also implements **graceful degradation** — missing config picks a fake rather than failing: no `.p12`/WWDR → `FakeSigner` (structurally valid, Wallet-rejected bundle); no `RESEND_API_KEY` → `FakeEmailSender` (silently sends nothing); no `ANTHROPIC_API_KEY` → the framework's MockLLM. `DATABASE_URL` is the one hard requirement — the API will not start without it.

### The campaign / HITL flow

`SoloFounderCrewRunner` is the thesis's second HITL adapter: `_WebHITL.review()` parks the crew run on an `asyncio.Future`, publishes the draft as a pollable `awaiting_review` state, and `respond()` resolves the Future. So the HTTP surface is three calls against one in-process run: `POST /shops/{id}/campaign` → poll `GET /campaigns/{thread_id}` → `POST /campaigns/{thread_id}/respond`. The runner is an `@lru_cache` singleton because it holds those in-flight futures — it is **not** yet backed by `CampaignRepository` (that swap is the pending serverless refactor), so runs do not survive a restart.

### Domain notes

- `Member` is platform-neutral: email is identity, unique per shop. Re-enrolling returns the *same* member and pass (`POST /shops/{id}/members` → `200` existing, `201` new), then re-emails the link.
- Stamping at `stamps_goal` grants a reward and resets the count to 0.
- Each member gets a unique `serial_number`; passes are re-issued live from current stamps, so already-issued passes keep working across migrations (the SQLite migration script preserves ids and serials for this reason).

### Web

Pages are client components calling `web/lib/api.ts`, which mirrors the API's pydantic models — change one, change the other. `API_URL` defaults to the literal `"/api"`, rewritten server-side to `API_ORIGIN` in `next.config.ts`. That is deliberate: one public URL covers web + API, so no CORS and no rebuild when a tunnel hands out a new hostname. **Do not set `turbopack.root` in `next.config.ts`** — it breaks the React client manifest and 500s the dynamic routes (see the comment there).

`web/AGENTS.md` applies: this is Next.js 16, whose APIs differ from most training data. Read `node_modules/next/dist/docs/` before writing Next-specific code.

## Gotchas

- **`.pkpass` assets are PNG-only.** `api/app/assets/` holds `pass-icon.png` / `pass-logo.png` and the issuer re-renders them as PNG. Swapping in an SVG breaks every issuance — `web/public/chunky-logo.svg` is web-only.
- **Postgres adapter tests need `PASSLY_TEST_DATABASE_URL`, never `DATABASE_URL`** — they truncate every table. They skip when it is unset, which is why the default suite needs no database (HTTP and service tests use the in-memory repos).
- `DISCORD_WEBHOOK_URL` is a GitHub Actions secret, not an app env var. Putting it in `api/.env` does nothing.
- `NEXT_PUBLIC_SITE_URL` should stay unset while nothing is deployed; it falls back to localhost for canonical/OG/JSON-LD. Keyword and schema decisions live in `docs/seo-keyword-map.md`.
- RLS is on for every table with **no policies** — safe because Passly connects directly as the table owner and never uses PostgREST. Don't "fix" this by adding policies.
