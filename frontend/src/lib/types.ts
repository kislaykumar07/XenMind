export type RunStatus = "passed" | "failed" | "running" | "error";

export interface Scenario {
  id: string;
  name: string;
  /** Backend categories are open strings (success, ambiguity, tool_failure,
   * prompt_injection, ...), not the original 4-value union. */
  category: string;
  description: string;
  userMessage?: string;
  expectedOutcome?: string;
  tags?: string[];
}

export interface AgentVersion {
  id: string;
  label: string;
  model: string;
  createdAt: string;
}

export type RunEventType = "input" | "llm_call" | "tool_call" | "tool_result" | "assertion" | "output" | "error";

export interface RunEvent {
  id: string;
  runId: string;
  seq: number;
  type: RunEventType;
  status: "ok" | "warn" | "fail";
  label: string;
  /** Backend does not measure per-event duration; 0 means "not measured", not "instant". */
  durationMs: number;
  payload?: Record<string, unknown>;
}

export interface AssertionResult {
  id: string;
  name: string;
  expected: string;
  actual: string;
  passed: boolean;
  explanation?: string;
}

export interface TestRun {
  id: string;
  scenarioId: string;
  scenarioName: string;
  agentVersionId: string;
  agentVersionLabel: string;
  status: RunStatus;
  startedAt: string;
  durationMs: number;
  assertionsPassed: number;
  assertionsTotal: number;
  outcome?: string;
  finalResponse?: string;
  replayOfRunId?: string | null;
  assertions?: AssertionResult[];
}

export interface CompareItem {
  scenarioId: string;
  leftStatus: string | null;
  rightStatus: string | null;
  change: string;
}

export interface CompareResult {
  summary: Record<string, number>;
  items: CompareItem[];
}

export interface DataResult<T> {
  data: T;
  source: "api" | "demo";
}
