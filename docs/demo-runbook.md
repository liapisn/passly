# Demo runbook

Passly runs **locally** for the thesis demo — web and API on the laptop,
Postgres on Supabase. Nothing is deployed. This is a deliberate choice: the
evaluation posture is a sandbox demonstration, so a hosted URL is not evidence
for any claim the thesis makes, and running locally removes the whole
serverless problem (campaign runs can stay in one process).

## One command

```bash
python scripts/dev.py --tunnel
```

That checks the database, opens a public HTTPS tunnel, starts the API and the
web app, and prints the URLs. `Ctrl-C` stops everything.

Drop `--tunnel` for laptop-only work. You need it whenever a **phone** is
involved — which is the whole customer half of the demo.

## Why one tunnel is enough

Every page is a client component, so API calls happen in the visitor's browser.
Rather than exposing two origins, the web app proxies the API under `/api`
(`web/next.config.ts`), so:

- one public URL covers the founder pages, the join page, and pass downloads
- there is no CORS to configure
- `NEXT_PUBLIC_API_URL` stays the literal `/api`, so a fresh tunnel hostname
  needs no rebuild and no edit
- emailed pass links are built from the same origin, so they open on a phone

```
phone ──► https://<tunnel>/join/<shopId>      Next.js :3000
          https://<tunnel>/api/...        ──► rewrite ──► FastAPI :8000 ──► Supabase
```

## Before the demo

1. **Wake Supabase.** The free tier pauses after ~7 days idle. `scripts/dev.py`
   fails fast with a clear message if it is asleep, but resuming takes a minute
   or two — do it the day before, not in the room.
2. **Do a full dry run**, including the phone. The tunnel hostname changes on
   every start, so any URL written on a slide will be stale.
3. **Check Resend.** Without a verified domain it only delivers to your own
   address, so enrol with `nikos@liapis.info` if you want the email to arrive.
   Enrolment still succeeds either way — the email is best-effort and never
   blocks the flow.

## The flow

| # | Who | Where | What |
|---|-----|-------|------|
| 1 | Founder | `/design` | Design the pass, live preview, save → gives a `shopId` |
| 2 | Founder | `/shops/<id>/campaign` | Crew drafts the launch copy; approve / send back / discard — this is the WebHITL gate |
| 3 | Customer | `/join/<shopId>` | Name + email on a phone → real signed `.pkpass` into Apple Wallet |
| 4 | Founder | `/shops/<id>/members` | +1 stamp per visit; reaching the goal grants a reward and resets |
| 5 | Customer | emailed link | Re-download the same pass |

Step 2 is the one worth narrating: the same `HITLContract` the framework uses
for its Discord surface is being satisfied by a web page, unchanged. That is
the §3.8 substitutability claim, demonstrated live.

## If something breaks

| Symptom | Cause | Fix |
|---|---|---|
| `Port 8000/3000 already in use` | Server left from a previous run | The error prints the `lsof` / `kill` commands |
| `Database check failed` | Supabase paused, or no network | Open the Supabase dashboard to resume |
| Join page 500, "React Client Manifest" | `turbopack.root` set in `next.config.ts` | Don't set it — see the note in that file |
| Phone sees a warning page before the site | Using ngrok's free tier | Use cloudflared: `brew install cloudflared` |
| Pass link in email opens nothing | Started without `--tunnel` | Restart with it; links are built from the tunnel URL |

## Offline fallback

Everything above needs internet, because Supabase is remote. If the venue's
network is doubtful, run Postgres locally instead — the adapters are identical,
so it is one variable:

```bash
docker run -d --name passly-pg -e POSTGRES_PASSWORD=passly \
    -e POSTGRES_DB=passly -p 55432:5432 postgres:16-alpine
DATABASE_URL=postgresql://postgres:passly@localhost:55432/passly \
    python scripts/apply_migrations.py --commit
```

Then point `DATABASE_URL` in `api/.env` at it and seed a shop through
`/design`. Note the phone half still needs the tunnel, so this only helps when
the database is the fragile part.

## What is deliberately not done

Deployment. The Vercel plan (two projects, Supabase transaction pooler,
certificates as base64 env vars) is documented but shelved — picking it up
belongs to the post-submission Passly-live track. The database half is already
compatible, so it stays a small step rather than a rewrite.
