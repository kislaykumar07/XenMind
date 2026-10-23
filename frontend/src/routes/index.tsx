import { createFileRoute, Link } from "@tanstack/react-router";
import { Logo } from "@/components/xen/Logo";
import { DemoBadge } from "@/components/xen/StatusBadge";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "XenMind — AI Agent Reliability Lab" },
      { name: "description", content: "Break it. Trace it. Trust it. Test AI agents, inspect execution traces, replay failures and compare runs." },
      { property: "og:title", content: "XenMind — AI Agent Reliability Lab" },
      { property: "og:description", content: "Test AI agents, inspect traces, replay failures, compare runs." },
    ],
  }),
  component: Landing,
});

const timeline = [
  { t: "input", label: "User: refund order, no ID given", s: "ok" },
  { t: "llm_call", label: "Plan: look up recent orders", s: "ok" },
  { t: "tool_call", label: "orders.search(email)", s: "ok" },
  { t: "tool_result", label: "3 orders returned", s: "ok" },
  { t: "assertion", label: "Asks user to confirm order", s: "fail" },
  { t: "output", label: "Refund issued on wrong order", s: "fail" },
];

const benefits = [
  { h: "Scenario tests", p: "Codify the edge cases that break agents — tool failures, injections, ambiguous asks." },
  { h: "Step-level traces", p: "Every LLM call, tool call and result on one timeline. Click any step to inspect it." },
  { h: "Replay & compare", p: "Re-run a failure against a new agent version and see exactly which outcomes changed." },
];

function Landing() {
  return (
    <div className="min-h-screen">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
        <Logo />
        <Link to="/lab" className="rounded-md border px-4 py-2 text-sm hover:bg-accent">Open lab</Link>
      </header>

      <section className="bg-grid border-y">
        <div className="mx-auto grid max-w-6xl gap-12 px-6 py-20 lg:grid-cols-2 lg:items-center">
          <div>
            <p className="font-mono text-xs uppercase tracking-widest text-cyan">AI Agent Reliability Lab</p>
            <h1 className="mt-4 text-5xl font-semibold leading-tight tracking-tight md:text-6xl">
              Break it. <span className="text-signal">Trace it.</span> Trust it.
            </h1>
            <p className="mt-6 max-w-md text-lg text-muted-foreground">
              Run your agent through hostile scenarios, see every step it took, and know what changed between versions.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link to="/lab" className="rounded-md bg-primary px-5 py-3 font-medium text-primary-foreground shadow-glow hover:bg-primary/90">
                Run a demo test
              </Link>
              <a href="#workflow" className="rounded-md border px-5 py-3 font-medium hover:bg-accent">How it works</a>
            </div>
          </div>

          <div className="rounded-xl border bg-card p-5 shadow-glow">
            <div className="mb-4 flex items-center justify-between">
              <span className="font-mono text-sm">run_demo_014 · support-agent@v3</span>
              <DemoBadge />
            </div>
            <ol className="space-y-0">
              {timeline.map((e, i) => (
                <li key={i} className="relative flex gap-3 pb-4 last:pb-0">
                  {i < timeline.length - 1 && <span className="absolute left-[5px] top-4 h-full w-px bg-border" />}
                  <span className={`mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full ${e.s === "fail" ? "bg-destructive" : "bg-cyan"}`} />
                  <div className="min-w-0">
                    <p className="font-mono text-[11px] uppercase text-muted-foreground">{e.t}</p>
                    <p className={`text-sm ${e.s === "fail" ? "text-destructive" : ""}`}>{e.label}</p>
                  </div>
                </li>
              ))}
            </ol>
          </div>
        </div>
      </section>

      <section className="mx-auto grid max-w-6xl gap-6 px-6 py-20 md:grid-cols-3">
        {benefits.map((b) => (
          <div key={b.h} className="rounded-lg border bg-surface p-6">
            <h3 className="font-semibold">{b.h}</h3>
            <p className="mt-2 text-sm text-muted-foreground">{b.p}</p>
          </div>
        ))}
      </section>

      <section id="workflow" className="border-t">
        <div className="mx-auto max-w-6xl px-6 py-20">
          <h2 className="text-3xl font-semibold tracking-tight">The workflow</h2>
          <ol className="mt-10 grid gap-6 md:grid-cols-4">
            {["Pick a scenario", "Run your agent", "Inspect the trace", "Replay & compare"].map((s, i) => (
              <li key={s} className="border-l-2 border-primary pl-4">
                <span className="font-mono text-xs text-cyan">0{i + 1}</span>
                <p className="mt-1 font-medium">{s}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <footer className="border-t py-8 text-center text-sm text-muted-foreground">XenMind · working name</footer>
    </div>
  );
}
