# XenMind — live website

**Live: https://xenmind.vercel.app** (Vercel project `xenmind`, production)

This folder is the exact code serving the live site:

```
public/          Static frontend (index.html, styles.css, app.js) — the repo's
                 design (oklch tokens, logo, landing + lab screens) implemented
                 as a dependency-free SPA using the same /api contract as
                 frontend/src/lib/api.ts.
api/index.py     Serverless entrypoint: statically defines `app` and proxies
                 in-process (httpx ASGI transport) to the real backend in
                 api/app/ — a copy of ../backend kept in sync.
vercel.json      Runtime env for the deployment.
requirements.txt Pinned deps for the serverless build (incl. psycopg).
```

## v3 (2026-10-24)

- **Real LLM agent mode**: agent versions whose config carries `llm`
  (`provider`, `model`, `system_prompt`, `temperature`) run through a real
  model via its OpenAI-compatible API (Groq default `openai/gpt-oss-20b` (llama-3.3-70b-versatile was retired for free keys in Aug 2026),
  OpenAI `gpt-4o-mini`), with the same deterministic mock tools and the same
  assertion engine. Keys are BYOK: the browser sends `X-LLM-Key` per request
  and the server never stores or logs it (server env keys only power
  scheduled runs). A provider failure persists an honest `error` run.
- **Custom scenarios**: `POST /api/scenarios` (signed in) + a builder form in
  the lab; 12 new seeded packs (refunds, Hindi, injections, escalation,
  delivery help, edge cases) → 23 scenarios total.
- **Workspaces**: create/join by code, runs scoped by `workspace_id`.
- **Schedules & alerts**: `POST /api/schedules` + Run now; `/api/cron/daily`
  (Vercel Cron, guarded by `CRON_SECRET`) re-runs enabled schedules and posts
  regression alerts to the in-app feed and an optional webhook.
- **Server-side auth**: Google ID tokens are verified server-side
  (`POST /api/auth/google` → HMAC session token); writes require the session
  and run creation is rate-limited (60/min mock, 10/min LLM per IP).
- **Billing (dormant)**: Razorpay checkout + signature verification endpoints
  exist, but return `billing_not_configured` until `RAZORPAY_KEY_ID` /
  `RAZORPAY_KEY_SECRET` are set — the UI falls back to the preview toast.
- **Frontend richness**: animated hero trace diagram, scenario marquee,
  scroll reveals, Dashboard trend charts (`GET /api/stats`), shareable
  read-only run reports (`#/share/<id>`) + downloadable HTML reports, PWA
  manifest + service worker (app shell cached, `/api` always live).

## v2 (2026-10-24)

- **Google sign-in gate**: the lab (`#/lab/*`) requires sign-in via Google
  Identity Services (`public/app.js`, `GOOGLE_CLIENT_ID` — a public identifier).
  The authorised JavaScript origins on that OAuth client must include
  `https://xenmind.vercel.app`. Server-side verification arrived in v3.
- **No loading flashes**: the SPA renders instantly from a cache-first data
  layer and refreshes in the background; full-page loading only appears on the
  very first lab entry.
- **Subscription UI**: Free ₹0 / Pro ₹499/mo / Team ₹1,499/mo on the landing
  page and in the lab (Subscription). Billing is NOT live — plan selection is
  a stored preview, no payment is taken.
- **Database**: production uses Postgres via `DATABASE_URL` (Neon) set as a
  Vercel project env var — never commit the connection string. Without it the
  backend falls back to SQLite (`/tmp` on Vercel, local file in dev).

## Redeploy

Upload every file in this folder to the Vercel project and create a
production deployment with `projectSettings.framework = "fastapi"` — without
that flag the static site serves but all API routes 404 at the edge.
