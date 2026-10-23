# Lovable Integration — XenMind Backend Contract

Base URL (local): `http://127.0.0.1:8000`
All JSON. Interactive docs: `GET /docs`. CORS is configured from the backend's
`CORS_ORIGINS` env variable (plus `*.lovable.app`), so set your deployed Lovable
origin there when you deploy the backend.

**Frontend adapter (already implemented, 2026-10-24):** the repo's
`frontend/src/lib/api.ts` is the single adapter for this contract — it takes
`VITE_API_BASE_URL` as the origin above (no `/api` suffix), calls the `/api/*`
routes below, and maps snake_case responses to the app's camelCase types.
The raw contract below is what that adapter (or any other client) must follow.

## Errors (consistent)

```json
{ "detail": { "code": "scenario_not_found", "message": "scenario not found" } }
```
Validation errors return HTTP 422 with FastAPI's standard `detail` list.
Not-found codes: `scenario_not_found`, `run_not_found`, `agent_version_not_found`.

## Endpoints

### GET /health
```json
{ "status": "ok", "service": "xenmind-backend", "version": "0.1.0", "database": "ok" }
```

### GET /api/scenarios
Array of: `id, title, description, category, user_message, expected_outcome, tags, assertions[]`
Seeded ids: `order-status-success`, `order-not-found`, `ambiguous-request`,
`missing-information`, `tool-failure`, `unsupported-request`, `prompt-injection`,
`help-center-returns`, `help-center-no-results`, `ticket-escalation`, `invalid-order-format`.

### GET /api/scenarios/{scenario_id}
Same as above plus `context` and `created_at`.

### POST /api/runs  (201)
Request:
```json
{ "scenario_id": "order-status-success", "agent_version_id": "mock-v2" }
```
`agent_version_id` is optional — omit it to use the default version (`mock-v1`).

Response (RunDetail):
```json
{
  "id": "…hex…", "scenario_id": "order-status-success", "agent_version_id": "mock-v2",
  "status": "passed", "outcome": "order_status_provided",
  "final_response": "Your order ORD-1001 … is shipped…",
  "duration_ms": 0, "passed_count": 3, "total_count": 3,
  "replay_of_run_id": null, "started_at": "…", "finished_at": "…",
  "assertions": [
    { "assertion_id": "tool-lookup", "description": "…", "passed": true,
      "expected": "tool called: lookup_order", "actual": "tools called: lookup_order",
      "explanation": "Tool was called." }
  ]
}
```
`status` is only `passed` when **all** assertions pass, otherwise `failed`.
Failures always carry an `explanation` — show it in the UI.

### GET /api/runs?scenario_id=&agent_version_id=&status=&limit=50&offset=0
Array of runs **without** assertions (use the detail endpoint for those).

### GET /api/runs/{run_id}
RunDetail (as above, with assertions).

### GET /api/runs/{run_id}/events
Ordered by `seq` ascending, `seq` starts at 1 and is strictly increasing:
```json
[
  { "seq": 1, "event_type": "run_started", "name": "run_started", "payload": {} },
  { "seq": 3, "event_type": "tool_call", "name": "lookup_order", "payload": { "tool": "lookup_order", "args": {} } },
  { "seq": 4, "event_type": "tool_result", "name": "lookup_order", "payload": {} },
  { "seq": 6, "event_type": "assertion_check", "name": "tool-lookup", "payload": { "passed": true, "explanation": "…" } }
]
```
Event types: `run_started`, `user_message`, `tool_call`, `tool_result`, `tool_error`,
`agent_response`, `assertion_check`, `run_completed`.

### POST /api/runs/{run_id}/replay  (201)
Body optional: `{ "agent_version_id": "mock-v2" }` — replay on a different version,
or `{}` / no body to replay on the original version. Always returns a **new** run
whose `replay_of_run_id` is the original run's id. The original run is never changed.

### GET /api/agent-versions
Array of: `id, name, version, description, config, is_default, created_at`.
Seeded: `mock-v1` (default, fails `tool-failure` on purpose) and `mock-v2` (passes all).

### POST /api/agent-versions  (201, 409 on duplicate id)
```json
{
  "name": "Mock Support Agent", "version": "v3",
  "description": "…",
  "config": {
    "resists_prompt_injection": true,
    "asks_clarification_when_missing_info": true,
    "handles_tool_failure_gracefully": true
  },
  "is_default": false
}
```
`id` is optional; when omitted it is generated from name+version.

### POST /api/compare
Mode A — explicit runs, paired by scenario:
```json
{ "left_run_ids": ["<runId>"], "right_run_ids": ["<runId>"] }
```
Mode B — latest run per scenario for each version:
```json
{ "baseline_agent_version_id": "mock-v1", "candidate_agent_version_id": "mock-v2" }
```
Response:
```json
{
  "summary": { "newly_passed": 1, "newly_failed": 0, "unchanged_passed": 10,
               "unchanged_failed": 0, "only_left": 0, "only_right": 0 },
  "items": [
    { "scenario_id": "tool-failure", "left_status": "failed",
      "right_status": "passed", "change": "newly_passed" }
  ]
}
```
`change` values: `newly_passed | newly_failed | unchanged_passed | unchanged_failed | only_left | only_right`.

## Paste-ready prompt for Lovable

> Build the frontend for XenMind, an AI Agent Reliability Lab, against the backend
> contract in this document. Pages: (1) Scenarios — list from GET /api/scenarios with
> category and tags, click to view detail; (2) Run — pick an agent version from
> GET /api/agent-versions, run a scenario with POST /api/runs, show pass/fail,
> the final response, and every assertion with its explanation; (3) Run detail —
> timeline of GET /api/runs/{id}/events in seq order, plus a Replay button that
> POSTs to /api/runs/{id}/replay; (4) Runs history — GET /api/runs with filters;
> (5) Compare — choose two agent versions, run/compare via POST /api/compare in
> Mode B, and highlight newly_passed in green and newly_failed in red.
> Set the API base URL from an environment variable. Do not invent metrics:
> the only timing shown is the backend's measured `duration_ms`.
