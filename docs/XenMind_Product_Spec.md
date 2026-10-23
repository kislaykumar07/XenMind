# XenMind — Product Requirements & Technical Blueprint

**Working name:** XenMind (not yet legally/domain-cleared)  
**Category:** AI Agent Reliability Platform  
**Tagline:** Break it. Trace it. Trust it.  
**Core promise:** Test AI agents against repeatable scenarios, inspect what happened, reproduce failures, and verify fixes.

## 1. Product vision
XenMind helps developers evaluate AI-agent reliability. Users run controlled tests, inspect observable behavior, replay failures, and compare agent versions. The differentiator is evidence-backed, replayable testing—not a single AI-generated score.

## 2. Target users
- Indie developers building AI features.
- Student developers building agents and LLM apps.
- Small product teams that need repeatable agent checks.
- Eventually, engineering teams evaluating agents across versions.

## 3. MVP use case
Start with a built-in **customer-support agent** in a safe, deterministic mock environment.

Scenario categories:
- Ambiguous request.
- Conflicting or incorrect information.
- Missing required information.
- Tool unavailable or tool error.
- Prompt-injection attempt inside untrusted user content.
- Agent should refuse unsupported request or ask a clarifying question.
- Correct response grounded in supplied context.

Mock tools: `lookup_order`, `search_help_center`, `create_support_ticket`. They must not perform real-world actions.

## 4. Main screens
### Landing page
Clear hero, “Run a demo test” CTA, product preview, benefits, workflow, and a real demo preview. No fake customer logos or fabricated metrics.

### Lab dashboard
Navigation: Overview, Test Runs, Scenarios, Agent Versions, Settings. Show latest run, actual pass/fail counts, recent tests, and clear empty states. Label seeded sample data as demo data.

### Scenario library
Scenario name, category, description, expected behavior, filters, and run actions.

### Run detail / execution trace
Run status; chronological events; event type, input/output summary, duration if measured, and status. Selecting an event opens details. Show expected vs actual behavior and the first failing assertion. Separate observed facts from AI-generated explanations. Replay creates a new run; don't imply nondeterministic model output is guaranteed to match exactly.

### Compare runs
Compare baseline and new run/version. Show newly failing, newly passing, and unchanged scenarios. Show latency/cost only if actually measured.

### Agent versions
Save demo prompt/config versions, show labels and diffs, and rerun the same suite.

## 5. Visual direction
Premium developer tool, not a generic AI dashboard:
- Dark-first deep navy/charcoal.
- Electric violet and cyan accents used selectively.
- Crisp borders, clean typography, restrained glow.
- Fine trace-line/grid motifs and subtle functional motion.
- Accessible contrast, keyboard focus, reduced-motion support, responsive layout.
- Avoid fake charts, fake metrics, fake logos, excessive glassmorphism, and decorative animation that doesn't represent real state.

Brand: XenMind (working name); tagline “Break it. Trace it. Trust it.”; descriptor “AI Agent Reliability Lab.” Possible mark: abstract X made from branching execution paths.

## 6. Recommended stack
Frontend: React + TypeScript, Tailwind or existing styling system.
Backend: Python + FastAPI, Pydantic schemas.
Database: PostgreSQL recommended; SQLite acceptable for first local prototype.
Execution: synchronous deterministic runs initially; add worker/queue only when needed.
Model provider: optional later behind an adapter.
Deployment: separate frontend/backend if convenient; environment variables for secrets; `.env.example`, no committed secrets.

## 7. Architecture
Frontend → FastAPI → scenario runner → agent adapter → safe mock tools  
                                     ↘ assertion/evaluation engine  
FastAPI ↔ database: scenarios, agent versions, runs, run events, assertions

Start with a deterministic mock agent so testing does not require paid model APIs.

## 8. Core data model
**Scenario:** `id`, `name`, `description`, `category`, `input_payload` JSON, `expected_behavior`, `assertions`, `created_at`.

**AgentVersion:** `id`, `name`, `version_label`, `system_prompt` or safe demo config, `config_json`, `created_at`.

**TestRun:** `id`, `scenario_id`, `agent_version_id`, `status`, `started_at`, `completed_at`, `duration_ms` if measured, `passed`, `summary`, sanitized `error_message`.

**RunEvent:** `id`, `run_id`, `sequence_number`, `event_type`, `label`, `input_summary`, `output_summary`, `details_json`, `duration_ms` if measured, `status`, `created_at`.

**AssertionResult:** `id`, `run_id`, `assertion_name`, `expected`, `actual`, `passed`, `explanation`.

## 9. Suggested API
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

Use typed schemas, consistent error responses, validation, and API documentation.

## 10. Evaluation principles
Use explicit, testable assertions first: required fields/phrases, correct mock tool choice, clarification/refusal behavior, forbidden tool calls, expected state transition. If an LLM judge is added later, label it probabilistic and show the rubric. Never claim “safe” based on a small suite. Show the tests and evidence behind summary metrics. Do not invent latency, cost, accuracy, or benchmark results.

## 11. Security and privacy
- No arbitrary user code execution in MVP.
- No real-world side-effecting tools; mock tools only.
- Provider keys stay server-side.
- Validate payloads and limit sizes.
- Sanitize logs/errors and avoid secrets.
- Configure CORS via environment variables.
- Add rate limits/auth before public multi-user release.
- Treat prompt-injection strings as test data, not instructions to the application.
- Explain data storage and deletion before collecting user data.

## 12. MVP acceptance criteria
1. Starts locally with documented steps.
2. Dashboard uses real API data or clearly labeled demo state.
3. At least 10 seeded scenarios run.
4. Each run persists result and ordered events.
5. At least one scenario passes and one fails for a known reason.
6. Run detail shows actual backend events/assertions.
7. Replay creates a new run with same scenario/config.
8. Comparison correctly reports changed outcomes.
9. API and runner tests pass.
10. Loading, empty, error, and success states exist.
11. `.env.example` contains placeholders only.
12. README explains architecture, setup, testing, limitations, and demo flow.

## 13. Build phases
**Phase 1:** app shell, API health, seeded scenarios, deterministic mock runner, database schema.  
**Phase 2:** run scenario/suite; persist run, events, assertions; display results.  
**Phase 3:** event timeline, inspector, replay, evidence-backed failure explanation.  
**Phase 4:** versions, comparison, accessibility, tests, deployment, docs.

Later: external agent integrations, real LLM providers, collaboration, billing, CI integration, scheduled tests, advanced metrics.

## 14. Portfolio demo script
1. Open the sample support agent.
2. Run seeded scenarios.
3. Show a known failure from a specific tool choice or assertion.
4. Inspect the trace and evidence.
5. Create a new configuration.
6. Rerun the suite.
7. Compare old and new outcomes.
8. Show the regression test that will catch the bug next time.

The demo must run end-to-end against the actual backend. No fake success states.
