# XenMind — AI Agent Reliability Lab

> Break it. Trace it. Trust it.

**Live: https://xenmind.vercel.app**

XenMind tests AI agents against repeatable scenarios, records execution traces,
replays failures, and compares agent versions — with evidence, not invented scores.

## Repo layout (cleaned 2026-10-24, live code added same day)

```
backend/    FastAPI backend — the full MVP (11 endpoints, 11 seeded scenarios,
            deterministic mock agent, replay + compare). Start here.
frontend/   Lovable/TanStack frontend source, extracted into real files.
            src/lib/api.ts is the ONLY backend adapter (see its header).
website/    The LIVE deployment (static SPA + serverless FastAPI entry) —
            see website/README.md. Google sign-in gate, cache-first UI,
            subscription plans UI (billing not live), Postgres via
            DATABASE_URL (Neon) in production.
docs/       XenMind_Product_Spec.md + project-kit notes.
```

There is **one** backend: `backend/`. An earlier health-only skeleton and the
old space-named upload folders (`backend 1`, `backend app`, `XenMind_Project_Kit`)
were removed in the cleanup — their useful content lives in `backend/` and `docs/`.

## Quick start

Backend (Windows PowerShell):

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python run.py
```

Open http://127.0.0.1:8000/docs and http://127.0.0.1:8000/health

Frontend: set `VITE_API_BASE_URL` to the backend **origin only**
(e.g. `http://127.0.0.1:8000` — no `/api` suffix; the adapter adds it),
then run the Lovable project / `npm run dev` in `frontend/`.

## Verified state

- Backend tests: 11/11 pass (`cd backend; python -m pytest tests -v`).
- Expected suite result: `mock-v1` = 10/11 (known failure: `tool-failure`),
  `mock-v2` = 11/11. Compare v1 → v2 reports `newly_passed: 1`.
- Frontend contract verified end-to-end on 2026-10-24: the extracted
  `src/lib/api.ts` was typechecked (strict TS, clean) and executed in Node
  against the running backend — scenarios, run, run list, events, replay,
  agent versions, and compare all returned correctly mapped data.

## Rules (from the product spec)

Deterministic mock tools only (`lookup_order`, `search_help_center`,
`create_support_ticket`). No real external actions, no arbitrary code execution,
no invented latency/cost/accuracy metrics — `duration_ms` is measured only.
Secrets stay server-side; `.env.example` holds placeholders only.
