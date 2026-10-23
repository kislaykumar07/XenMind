# XenMind Backend — AI Agent Reliability Lab

Python + FastAPI backend for running seeded scenarios against a **deterministic mock agent**,
persisting results, exposing ordered events, replaying runs, and comparing agent versions.

> Note: this backend was built from `02_MUSE_BACKEND_PROMPT.md` before the product spec
> was available locally. The spec has since been added at `docs/XenMind_Product_Spec.md`
> (repo root) and checked against this backend on 2026-10-24: endpoints, data-model
> concepts, and evaluation/security rules match; only some field names differ in
> wording (e.g. scenario `title` here vs `name` in the spec) — the frontend adapter
> in `frontend/src/lib/api.ts` absorbs those differences.

## Honest status

- All 11 MVP endpoints implemented and tested.
- Mock tools only — `lookup_order`, `search_help_center`, `create_support_ticket`.
  No real services, no side effects, no billing, no arbitrary code execution.
- No invented latency/cost metrics. `duration_ms` is the **measured** wall time of the run.
- **Known failure by design:** `mock-v1` fails the `tool-failure` scenario (it leaks a raw
  tool error instead of a graceful fallback). `mock-v2` fixes exactly that and passes 11/11.
  That pair is what makes the Compare feature demonstrable.

## Architecture

```
app/
  main.py            FastAPI app, CORS (env-driven), lifespan: create tables + seed
  config.py          Env settings (DATABASE_URL, CORS_ORIGINS, ...)
  db.py              SQLAlchemy engine/session (SQLite default, PostgreSQL-ready)
  models/models.py   Scenario, AgentVersion, TestRun, RunEvent, AssertionResult
  schemas/schemas.py Pydantic request/response schemas + validation
  api/routes.py      All /api endpoints
  services/
    seed.py          11 seeded scenarios + agent versions mock-v1 / mock-v2
    runner_service.py  Execute a run, persist run + ordered events + assertion results
  runner/
    mock_tools.py    Deterministic in-memory tools (same input -> same output)
    mock_agent.py    Deterministic rule-based agent; behaviour = AgentVersion config flags
    assertions.py    Explicit assertions: response_contains / response_not_contains /
                     tool_called / tool_not_called / outcome_is
tests/
  conftest.py        Isolated test DB
  test_api.py        11 tests: health, scenarios, success run, known failure,
                     event ordering, replay, agent versions, comparison, validation
```

Data/seeding is idempotent: tables are created on startup (`Base.metadata.create_all`,
the SQLite/Postgres-compatible schema setup for this MVP) and seed rows are inserted
only if missing. Replay **never** overwrites the original run — it creates a new run
with `replay_of_run_id` set.

## Setup — Windows PowerShell

```powershell
cd xenmind\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python run.py
```

Then open: http://127.0.0.1:8000/docs (OpenAPI) and http://127.0.0.1:8000/health

## Setup — macOS / Linux

```bash
cd xenmind/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python run.py
# or: uvicorn app.main:app --reload --port 8000
```

## Test

```powershell
# Windows
.\.venv\Scripts\Activate.ps1
python -m pytest tests -v
```

```bash
# macOS / Linux
python -m pytest tests -v
```

Verified result at build time: **11 passed**.

## API summary

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Service + database health |
| GET | `/api/scenarios` | List seeded scenarios |
| GET | `/api/scenarios/{scenario_id}` | One scenario (with context) |
| POST | `/api/runs` | Run a scenario: `{scenario_id, agent_version_id?}` |
| GET | `/api/runs` | List runs (`?scenario_id=&agent_version_id=&status=&limit=&offset=`) |
| GET | `/api/runs/{run_id}` | Run detail incl. assertion results |
| GET | `/api/runs/{run_id}/events` | Ordered events (`seq` 1..N, strictly increasing) |
| POST | `/api/runs/{run_id}/replay` | New run from an old one, optional new `agent_version_id` |
| GET | `/api/agent-versions` | List agent versions |
| POST | `/api/agent-versions` | Create an agent version (config flags drive behaviour) |
| POST | `/api/compare` | Compare runs/agent versions: newly passed / newly failed / unchanged |

Full request/response examples for the frontend live in `LOVABLE_INTEGRATION.md`.

## Agent version behaviour flags

```json
{
  "resists_prompt_injection": true,
  "asks_clarification_when_missing_info": true,
  "handles_tool_failure_gracefully": false
}
```

`mock-v1` = graceful tool-failure handling **off** (known failure).
`mock-v2` = all flags **on** (passes 11/11).
Expected suite result: v1 = 10 passed / 1 failed (`tool-failure`), v2 = 11 passed / 0 failed.
