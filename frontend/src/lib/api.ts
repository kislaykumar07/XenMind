import type {
  AgentVersion,
  AssertionResult,
  CompareResult,
  DataResult,
  RunEvent,
  Scenario,
  TestRun,
} from "./types";
import { demoRuns } from "./demo-data";

/**
 * XenMind backend contract (fixed 2026-10-24).
 *
 * VITE_API_BASE_URL is the backend ORIGIN only, e.g. http://127.0.0.1:8000
 * All backend routes live under /api and use snake_case JSON.
 * This module is the single adapter: nothing else in the app should
 * talk to the backend or know about snake_case.
 */
const RAW_BASE = import.meta.env["VITE_API_BASE_URL"] as string | undefined;
const BASE = RAW_BASE ? RAW_BASE.replace(/\/+$/, "").replace(/\/api$/, "") : undefined;

export const isBackendConfigured = () => Boolean(BASE);

function apiUrl(path: string): string {
  return `${BASE}/api${path}`;
}

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(apiUrl(path));
  if (!res.ok) throw new Error(`Request failed (${res.status})`);
  return res.json() as Promise<T>;
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(apiUrl(path), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body ?? {}),
  });
  if (!res.ok) throw new Error(`Request failed (${res.status})`);
  return res.json() as Promise<T>;
}

function requireBackend(): void {
  if (!BASE) throw new Error("No backend connected — set VITE_API_BASE_URL to run real tests.");
}

/* ------------------------------------------------------------------ */
/* Backend wire types (snake_case, exactly as FastAPI returns them)    */
/* ------------------------------------------------------------------ */

interface BackendScenario {
  id: string;
  title: string;
  description: string;
  category: string;
  user_message: string;
  expected_outcome: string;
  tags: string[];
  assertions?: unknown[];
}

interface BackendAgentVersion {
  id: string;
  name: string;
  version: string;
  description: string;
  config: Record<string, unknown>;
  is_default: boolean;
  created_at?: string;
}

interface BackendAssertion {
  assertion_id: string;
  description: string;
  passed: boolean;
  expected: string;
  actual: string;
  explanation: string;
}

interface BackendRun {
  id: string;
  scenario_id: string;
  agent_version_id: string;
  status: string;
  outcome: string;
  final_response: string;
  duration_ms: number | null;
  passed_count: number;
  total_count: number;
  replay_of_run_id: string | null;
  started_at: string;
  finished_at: string;
  assertions?: BackendAssertion[];
}

interface BackendEvent {
  seq: number;
  event_type: string;
  name: string;
  payload: Record<string, unknown>;
  created_at?: string;
}

/* ------------------------------------------------------------------ */
/* Mappers: backend (snake_case) -> frontend types (camelCase)         */
/* ------------------------------------------------------------------ */

function mapScenario(b: BackendScenario): Scenario {
  return {
    id: b.id,
    name: b.title,
    category: b.category,
    description: b.description,
    userMessage: b.user_message,
    expectedOutcome: b.expected_outcome,
    tags: b.tags ?? [],
  };
}

function mapAgentVersion(b: BackendAgentVersion): AgentVersion {
  return {
    id: b.id,
    label: `${b.name}@${b.version}`,
    model: "deterministic-mock",
    createdAt: b.created_at ?? "",
  };
}

function mapAssertion(b: BackendAssertion): AssertionResult {
  return {
    id: b.assertion_id,
    name: b.description || b.assertion_id,
    expected: b.expected,
    actual: b.actual,
    passed: b.passed,
    explanation: b.explanation,
  };
}

function mapRun(
  b: BackendRun,
  scenarioNames?: Map<string, string>,
  agentLabels?: Map<string, string>,
): TestRun {
  return {
    id: b.id,
    scenarioId: b.scenario_id,
    scenarioName: scenarioNames?.get(b.scenario_id) ?? b.scenario_id,
    agentVersionId: b.agent_version_id,
    agentVersionLabel: agentLabels?.get(b.agent_version_id) ?? b.agent_version_id,
    status: (b.status === "passed" || b.status === "failed" ? b.status : "error") as TestRun["status"],
    startedAt: b.started_at,
    durationMs: b.duration_ms ?? 0,
    assertionsPassed: b.passed_count,
    assertionsTotal: b.total_count,
    outcome: b.outcome,
    finalResponse: b.final_response,
    replayOfRunId: b.replay_of_run_id,
    assertions: b.assertions?.map(mapAssertion),
  };
}

const EVENT_TYPE_MAP: Record<string, RunEvent["type"]> = {
  run_started: "input",
  user_message: "input",
  tool_call: "tool_call",
  tool_result: "tool_result",
  tool_error: "error",
  agent_response: "output",
  assertion_check: "assertion",
  run_completed: "output",
};

function mapEvent(runId: string, b: BackendEvent): RunEvent {
  const isAssertion = b.event_type === "assertion_check";
  const assertionFailed = isAssertion && b.payload?.["passed"] === false;
  return {
    id: `${runId}:${b.seq}`,
    runId,
    seq: b.seq,
    type: EVENT_TYPE_MAP[b.event_type] ?? "output",
    status: b.event_type === "tool_error" || assertionFailed ? "fail" : "ok",
    label: b.name,
    durationMs: 0, // not measured per-event by the backend
    payload: b.payload,
  };
}

/** Best-effort name lookups so run lists show titles, not just ids. */
async function lookupMaps(): Promise<{ scenarios: Map<string, string>; agents: Map<string, string> }> {
  const scenarios = new Map<string, string>();
  const agents = new Map<string, string>();
  try {
    const [s, a] = await Promise.all([
      getJson<BackendScenario[]>("/scenarios"),
      getJson<BackendAgentVersion[]>("/agent-versions"),
    ]);
    s.forEach((x) => scenarios.set(x.id, x.title));
    a.forEach((x) => agents.set(x.id, `${x.name}@${x.version}`));
  } catch {
    /* names fall back to ids */
  }
  return { scenarios, agents };
}

/* ------------------------------------------------------------------ */
/* Public API (signatures used by the routes — unchanged)              */
/* ------------------------------------------------------------------ */

/** Recent runs. Falls back to clearly-labelled demo data when no backend is configured. */
export async function listRuns(): Promise<DataResult<TestRun[]>> {
  if (!BASE) return { data: demoRuns, source: "demo" };
  const [runs, maps] = await Promise.all([getJson<BackendRun[]>("/runs"), lookupMaps()]);
  return { data: runs.map((r) => mapRun(r, maps.scenarios, maps.agents)), source: "api" };
}

/** Request a new run. Without a backend this refuses rather than pretending a test ran. */
export async function requestRun(scenarioId: string, agentVersionId?: string): Promise<TestRun> {
  requireBackend();
  const [run, maps] = await Promise.all([
    postJson<BackendRun>("/runs", {
      scenario_id: scenarioId,
      ...(agentVersionId ? { agent_version_id: agentVersionId } : {}),
    }),
    lookupMaps(),
  ]);
  return mapRun(run, maps.scenarios, maps.agents);
}

export async function listScenarios(): Promise<Scenario[]> {
  requireBackend();
  const data = await getJson<BackendScenario[]>("/scenarios");
  return data.map(mapScenario);
}

export async function getScenario(scenarioId: string): Promise<Scenario> {
  requireBackend();
  return mapScenario(await getJson<BackendScenario>(`/scenarios/${encodeURIComponent(scenarioId)}`));
}

export async function getRun(runId: string): Promise<TestRun> {
  requireBackend();
  const [run, maps] = await Promise.all([
    getJson<BackendRun>(`/runs/${encodeURIComponent(runId)}`),
    lookupMaps(),
  ]);
  return mapRun(run, maps.scenarios, maps.agents);
}

export async function listRunEvents(runId: string): Promise<RunEvent[]> {
  requireBackend();
  const events = await getJson<BackendEvent[]>(`/runs/${encodeURIComponent(runId)}/events`);
  return events.map((e) => mapEvent(runId, e));
}

export async function replayRun(runId: string, agentVersionId?: string): Promise<TestRun> {
  requireBackend();
  const [run, maps] = await Promise.all([
    postJson<BackendRun>(`/runs/${encodeURIComponent(runId)}/replay`, {
      ...(agentVersionId ? { agent_version_id: agentVersionId } : {}),
    }),
    lookupMaps(),
  ]);
  return mapRun(run, maps.scenarios, maps.agents);
}

export async function listAgentVersions(): Promise<AgentVersion[]> {
  requireBackend();
  const data = await getJson<BackendAgentVersion[]>("/agent-versions");
  return data.map(mapAgentVersion);
}

export async function createAgentVersion(input: {
  name: string;
  version: string;
  description?: string;
  config?: Record<string, unknown>;
  isDefault?: boolean;
}): Promise<AgentVersion> {
  requireBackend();
  const created = await postJson<BackendAgentVersion>("/agent-versions", {
    name: input.name,
    version: input.version,
    description: input.description ?? "",
    config: input.config ?? {},
    is_default: input.isDefault ?? false,
  });
  return mapAgentVersion(created);
}

export async function compareAgentVersions(
  baselineAgentVersionId: string,
  candidateAgentVersionId: string,
): Promise<CompareResult> {
  requireBackend();
  const res = await postJson<{
    summary: Record<string, number>;
    items: { scenario_id: string; left_status: string | null; right_status: string | null; change: string }[];
  }>("/compare", {
    baseline_agent_version_id: baselineAgentVersionId,
    candidate_agent_version_id: candidateAgentVersionId,
  });
  return {
    summary: res.summary,
    items: res.items.map((i) => ({
      scenarioId: i.scenario_id,
      leftStatus: i.left_status,
      rightStatus: i.right_status,
      change: i.change,
    })),
  };
}
