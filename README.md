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

## Build phases

- **P0 — scaffold** ✅ — repo, API ↔ framework wiring, web status page
- **P1 — pass issuance** — signed `.pkpass` (Apple Wallet); needs an Apple
  Developer cert
- **P2 — shop + designer UI** — create a shop, live pass preview
- **P3 — crew + WebHITL** — crew drafts copy/campaign; approve/edit in web
- **P4 — demo polish** — real demo-shop data, end-to-end flow, UI polish

## Local development

Requires Python 3.11–3.13 and Node 20+. The `solo-founder-crew` repo must be
checked out as a sibling directory (`../solo-founder-crew`).

### API (port 8000)

```bash
cd api
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt   # installs the framework editable
.venv/bin/uvicorn app.main:app --reload
```

Smoke check: `curl localhost:8000/crew/info` should return the six crew roles.

### Web (port 3000)

```bash
cd web
cp .env.local.example .env.local
npm install
npm run dev
```

Open http://localhost:3000 — the status card confirms the
Next.js → FastAPI → solo-founder-crew chain is live.
