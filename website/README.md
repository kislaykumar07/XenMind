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

## v2 (2026-10-24)

- **Google sign-in gate**: the lab (`#/lab/*`) requires sign-in via Google
  Identity Services (`public/app.js`, `GOOGLE_CLIENT_ID` — a public identifier).
  The authorised JavaScript origins on that OAuth client must include
  `https://xenmind.vercel.app`. Sign-in is browser-side; the backend does not
  yet verify ID tokens server-side.
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
