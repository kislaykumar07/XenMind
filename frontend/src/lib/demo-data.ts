import type { TestRun } from "./types";

// DEMO DATA — shown only when no backend is configured. Always labelled in the UI.
export const demoRuns: TestRun[] = [
  { id: "run_demo_014", scenarioId: "sc_refund", scenarioName: "Refund request with missing order ID", agentVersionId: "v3", agentVersionLabel: "support-agent@v3", status: "failed", startedAt: "2026-10-23T14:02:00Z", durationMs: 8420, assertionsPassed: 3, assertionsTotal: 5 },
  { id: "run_demo_013", scenarioId: "sc_inject", scenarioName: "Prompt injection via tool output", agentVersionId: "v3", agentVersionLabel: "support-agent@v3", status: "passed", startedAt: "2026-10-23T13:47:00Z", durationMs: 5130, assertionsPassed: 4, assertionsTotal: 4 },
  { id: "run_demo_012", scenarioId: "sc_lookup", scenarioName: "Multi-step order lookup", agentVersionId: "v2", agentVersionLabel: "support-agent@v2", status: "passed", startedAt: "2026-10-23T11:15:00Z", durationMs: 6900, assertionsPassed: 6, assertionsTotal: 6 },
  { id: "run_demo_011", scenarioId: "sc_timeout", scenarioName: "Tool timeout recovery", agentVersionId: "v2", agentVersionLabel: "support-agent@v2", status: "error", startedAt: "2026-10-22T18:30:00Z", durationMs: 30000, assertionsPassed: 0, assertionsTotal: 3 },
];
