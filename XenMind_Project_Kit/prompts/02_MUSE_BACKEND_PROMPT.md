# Muse Prompt — XenMind Backend

Build the backend for **XenMind**, an AI Agent Reliability Lab. Read `XenMind_Product_Spec.md` first. Adapt to Muse's actual capabilities; do not pretend an integration exists if it is unavailable.

## Goal
Create a reliable, testable Python + FastAPI backend for running seeded scenarios against a deterministic mock agent, persisting results, exposing ordered events, replaying runs, and comparing outcomes.

## Required MVP endpoints
- `GET /health`
- `GET /api/scenarios`
- `GET /api/scenarios/{scenario_id}`
- `POST /api/runs`
- `GET /api/runs`
- `GET /api/runs/{run_id}`
- `GET /api/runs/{run_id}/events`
- `POST /api/runs/{run_id}/replay`
- `GET /api/agent-versions`
- `POST /api/agent-versions`
- `POST /api/compare`

Use Pydantic schemas, validation, consistent errors, and OpenAPI docs.

## Data and runner
Implement Scenario, AgentVersion, TestRun, RunEvent, AssertionResult. Use PostgreSQL if ready; SQLite is fine for the first local prototype. Include schema setup/migrations.

- Seed at least 10 scenarios: normal success, ambiguity, missing information, tool failure, unsupported request, prompt-injection-like input, etc.
- Use deterministic mock tools only: `lookup_order`, `search_help_center`, `create_support_ticket`.
- Mock tools must not call real services or cause side effects.
- Record status, ordered events, assertions, start/end time, and measured duration if available.
- Use explicit deterministic assertions; failures must have known explanations.
- Replay creates a new run; never overwrite the original.
- Comparison reports newly passed, newly failed, and unchanged outcomes.
- Never invent latency/cost metrics.

## Engineering
- Suggested structure: `app/main.py`, `app/api/`, `app/models/`, `app/schemas/`, `app/services/`, `app/runner/`, `tests/`.
- `.env.example` placeholders only.
- Keep secrets server-side.
- Validate payloads, limit sizes, sanitize errors, and avoid logging secrets.
- Configure CORS through environment variables.
- Add tests for health, scenarios, successful run, known failure, event ordering, replay, and comparison.
- Document setup, run, seed, and test commands.
- No arbitrary code execution, no real external tool actions, and no billing in MVP.

## Workflow
1. Inspect the repository and existing code.
2. Propose architecture and file tree.
3. Implement one vertical slice: health → list scenarios → run one scenario → persist result/events → retrieve run.
4. Run tests and fix errors before adding replay/comparison.
5. Give exact Windows PowerShell commands where applicable.
6. Do not claim tests passed unless they were actually run.
7. Do not delete/replace existing files without asking.
8. Keep API contract clear for Lovable.

Start by inspecting the repository and proposing a plan. Implement only the first vertical slice.
