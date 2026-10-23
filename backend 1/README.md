# XenMind — AI Agent Reliability Lab

> Break it. Trace it. Trust it.

XenMind tests AI agents against repeatable scenarios, records execution traces, replays failures, and compares agent versions.

**Status:** Milestone 1 — backend skeleton + health endpoint.

## Project layout

```
xenmind/
  backend/
    app/
      main.py          # FastAPI app: CORS + router registration
      config.py        # Settings loaded from .env
      api/health.py    # GET /api/health
    tests/test_health.py
    requirements.txt
    pytest.ini
    .env.example
  .gitignore
  README.md
```

## Setup (Windows PowerShell)

Requires **Python 3.11+**. Check with `python --version`.

```powershell
cd xenmind\backend

# 1. Create and activate a virtual environment (an isolated set of packages for this project)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# 3. Create your local config
Copy-Item .env.example .env
```

## Run the API

```powershell
# from xenmind\backend, with the venv active
uvicorn app.main:app --reload
```

Then open:
- http://127.0.0.1:8000/api/health → `{"status":"ok","version":"0.1.0","environment":"local"}`
- http://127.0.0.1:8000/docs → interactive API docs (Swagger UI)

Stop the server with `Ctrl+C`.

## Run the tests

```powershell
# from xenmind\backend, with the venv active
pytest -v
```

Expected: 4 tests pass.

## Manual test checklist

1. Server starts with no errors and prints `Uvicorn running on http://127.0.0.1:8000`.
2. `/api/health` returns `status: ok`.
3. `/docs` lists the `GET /api/health` endpoint.
4. In PowerShell: `Invoke-RestMethod http://127.0.0.1:8000/api/health` prints the same fields.
5. Change `ENVIRONMENT=demo` in `.env`, restart the server, and confirm `/api/health` now shows `demo`.

## Common errors

| Error | Cause | Fix |
|---|---|---|
| `Activate.ps1 cannot be loaded because running scripts is disabled` | PowerShell execution policy | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, then activate again |
| `'uvicorn' is not recognized` | venv not active | Run `.\.venv\Scripts\Activate.ps1`; the prompt should start with `(.venv)` |
| `ModuleNotFoundError: No module named 'app'` | Running from the wrong folder | `cd` into `xenmind\backend` first |
| `[WinError 10048] ... address already in use` | Port 8000 is taken | `uvicorn app.main:app --reload --port 8001` |
| Browser console: `blocked by CORS policy` | Frontend origin not allowed | Add the frontend URL to `CORS_ORIGINS` in `.env` and restart |

## Frontend contract (for Lovable)

```ts
// GET /api/health
export interface HealthResponse {
  status: "ok";
  version: string;
  environment: string;
}
```

## Milestones

1. ✅ Health endpoint and local setup
2. ⬜ Seed scenarios and deterministic mock runner
3. ⬜ Persist TestRun, RunEvent, AssertionResult
4. ⬜ Connect Lovable frontend to API
5. ⬜ Event inspector and replay
6. ⬜ Versions and comparison
7. ⬜ Tests, security review, deployment, demo
8. ⬜ Real LLM adapter, auth, quotas (after MVP)
