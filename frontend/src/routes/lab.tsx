import { createFileRoute, Link } from "@tanstack/react-router";
import { queryOptions, useSuspenseQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Logo } from "@/components/xen/Logo";
import { DemoBadge, StatusBadge } from "@/components/xen/StatusBadge";
import { listRuns, requestRun, isBackendConfigured } from "@/lib/api";

const runsQuery = queryOptions({ queryKey: ["runs"], queryFn: listRuns });

export const Route = createFileRoute("/lab")({
  head: () => ({
    meta: [
      { title: "Lab dashboard — XenMind" },
      { name: "description", content: "Recent agent test runs and their outcomes." },
      { property: "og:title", content: "Lab dashboard — XenMind" },
      { property: "og:description", content: "Recent agent test runs and their outcomes." },
    ],
  }),
  loader: ({ context }) => context.queryClient.ensureQueryData(runsQuery),
  component: Lab,
  pendingComponent: () => <Shell><p className="animate-pulse-dot text-muted-foreground">Loading runs…</p></Shell>,
  errorComponent: ({ error }) => (
    <Shell>
      <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-6">
        <p className="font-medium text-destructive">Couldn't load runs</p>
        <p className="mt-1 text-sm text-muted-foreground">{(error as Error).message}</p>
      </div>
    </Shell>
  ),
});

const nav = ["Dashboard", "Scenarios", "Runs", "Compare", "Agent versions"];

function Shell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col md:flex-row">
      <aside className="border-b bg-surface p-4 md:w-56 md:border-b-0 md:border-r">
        <Link to="/"><Logo /></Link>
        <nav className="mt-6 flex gap-1 overflow-x-auto md:flex-col">
          {nav.map((n, i) => (
            <span
              key={n}
              aria-current={i === 0 ? "page" : undefined}
              className={`whitespace-nowrap rounded-md px-3 py-2 text-sm ${i === 0 ? "bg-accent text-foreground" : "text-muted-foreground"}`}
            >
              {n}
              {i > 0 && <span className="ml-2 font-mono text-[10px] opacity-60">soon</span>}
            </span>
          ))}
        </nav>
      </aside>
      <main className="flex-1 p-6 md:p-10">{children}</main>
    </div>
  );
}

function Lab() {
  const { data: result } = useSuspenseQuery(runsQuery);
  const runs = result.data;
  const [notice, setNotice] = useState<string | null>(null);

  const onRun = async () => {
    setNotice(null);
    try {
      const run = await requestRun(runs[0]?.scenarioId ?? "");
      setNotice(`Run ${run.id} requested.`);
    } catch (e) {
      setNotice((e as Error).message);
    }
  };

  const passed = runs.filter((r) => r.status === "passed").length;

  return (
    <Shell>
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-semibold tracking-tight">Recent runs</h1>
            {result.source === "demo" && <DemoBadge />}
          </div>
          <p className="mt-1 text-sm text-muted-foreground">
            {runs.length} runs · {passed} passed · {runs.length - passed} need attention
          </p>
        </div>
        <button onClick={onRun} className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90">
          New test run
        </button>
      </div>

      {notice && (
        <p role="status" className="mt-4 rounded-md border border-warning/40 bg-warning/10 px-4 py-3 text-sm text-warning">{notice}</p>
      )}
      {!isBackendConfigured() && !notice && (
        <p className="mt-4 text-sm text-muted-foreground">No backend connected. Runs below are sample data, not real results.</p>
      )}

      {runs.length === 0 ? (
        <div className="mt-8 rounded-lg border border-dashed p-12 text-center">
          <p className="font-medium">No runs yet</p>
          <p className="mt-1 text-sm text-muted-foreground">Start a test run to see results here.</p>
        </div>
      ) : (
        <div className="mt-8 overflow-x-auto rounded-lg border">
          <table className="w-full text-sm">
            <thead className="bg-surface text-left font-mono text-xs uppercase text-muted-foreground">
              <tr>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Scenario</th>
                <th className="px-4 py-3">Agent</th>
                <th className="px-4 py-3">Assertions</th>
                <th className="px-4 py-3">Duration</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((r) => (
                <tr key={r.id} className="border-t hover:bg-accent/50">
                  <td className="px-4 py-3"><StatusBadge status={r.status} /></td>
                  <td className="px-4 py-3">
                    <p>{r.scenarioName}</p>
                    <p className="font-mono text-xs text-muted-foreground">{r.id}</p>
                  </td>
                  <td className="px-4 py-3 font-mono text-xs">{r.agentVersionLabel}</td>
                  <td className="px-4 py-3 font-mono">{r.assertionsPassed}/{r.assertionsTotal}</td>
                  <td className="px-4 py-3 font-mono text-muted-foreground">{(r.durationMs / 1000).toFixed(1)}s</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Shell>
  );
}
