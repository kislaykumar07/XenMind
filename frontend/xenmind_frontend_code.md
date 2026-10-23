# XenMind Frontend — Full Source

Stack: TanStack Start v1 (React 19, Vite 7) + Tailwind v4 + TanStack Query.
No backend connected; API base URL comes from VITE_API_BASE_URL.


## src/styles.css

```css
@import "tailwindcss" source(none);
@source "../src";
@import "tw-animate-css";

@custom-variant dark (&:is(.dark *));

@theme inline {
  --font-sans: "Space Grotesk", ui-sans-serif, system-ui, sans-serif;
  --font-mono: "JetBrains Mono", ui-monospace, monospace;
  --radius-sm: calc(var(--radius) - 4px);
  --radius-md: calc(var(--radius) - 2px);
  --radius-lg: var(--radius);
  --radius-xl: calc(var(--radius) + 4px);
  --color-background: var(--background);
  --color-foreground: var(--foreground);
  --color-card: var(--card);
  --color-card-foreground: var(--card-foreground);
  --color-popover: var(--popover);
  --color-popover-foreground: var(--popover-foreground);
  --color-primary: var(--primary);
  --color-primary-foreground: var(--primary-foreground);
  --color-secondary: var(--secondary);
  --color-secondary-foreground: var(--secondary-foreground);
  --color-muted: var(--muted);
  --color-muted-foreground: var(--muted-foreground);
  --color-accent: var(--accent);
  --color-accent-foreground: var(--accent-foreground);
  --color-destructive: var(--destructive);
  --color-destructive-foreground: var(--destructive-foreground);
  --color-success: var(--success);
  --color-warning: var(--warning);
  --color-cyan: var(--cyan);
  --color-surface: var(--surface);
  --color-border: var(--border);
  --color-input: var(--input);
  --color-ring: var(--ring);
}

:root {
  --radius: 0.5rem;
  --background: oklch(0.16 0.025 265);
  --surface: oklch(0.19 0.028 265);
  --foreground: oklch(0.95 0.01 260);
  --card: oklch(0.205 0.03 265);
  --card-foreground: oklch(0.95 0.01 260);
  --popover: oklch(0.2 0.03 265);
  --popover-foreground: oklch(0.95 0.01 260);
  --primary: oklch(0.66 0.21 290);
  --primary-foreground: oklch(0.98 0.01 290);
  --secondary: oklch(0.25 0.03 265);
  --secondary-foreground: oklch(0.92 0.01 260);
  --muted: oklch(0.24 0.025 265);
  --muted-foreground: oklch(0.7 0.03 260);
  --accent: oklch(0.27 0.04 270);
  --accent-foreground: oklch(0.95 0.01 260);
  --cyan: oklch(0.82 0.13 205);
  --success: oklch(0.78 0.16 155);
  --warning: oklch(0.82 0.15 80);
  --destructive: oklch(0.66 0.21 25);
  --destructive-foreground: oklch(0.98 0 0);
  --border: oklch(0.3 0.03 265);
  --input: oklch(0.3 0.03 265);
  --ring: oklch(0.82 0.13 205);
  --glow: 0 0 40px -12px color-mix(in oklab, var(--primary) 60%, transparent);
  --grid-line: color-mix(in oklab, var(--border) 50%, transparent);
}

@layer base {
  * { border-color: var(--color-border); }
  html { color-scheme: dark; }
  body {
    background-color: var(--color-background);
    color: var(--color-foreground);
    font-family: var(--font-sans);
  }
  :focus-visible { outline: 2px solid var(--color-ring); outline-offset: 2px; }
  @media (prefers-reduced-motion: reduce) {
    *, *::before, *::after { animation: none !important; transition: none !important; }
  }
}

@utility bg-grid {
  background-image:
    linear-gradient(var(--grid-line) 1px, transparent 1px),
    linear-gradient(90deg, var(--grid-line) 1px, transparent 1px);
  background-size: 40px 40px;
}

@utility shadow-glow {
  box-shadow: var(--glow);
}

@utility text-signal {
  background: linear-gradient(90deg, var(--primary), var(--cyan));
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

@keyframes pulse-dot { 0%,100% { opacity: 1 } 50% { opacity: .35 } }
@utility animate-pulse-dot { animation: pulse-dot 1.6s ease-in-out infinite; }
```

## src/router.tsx

```tsx
import { QueryClient } from "@tanstack/react-query";
import { createRouter } from "@tanstack/react-router";
import { routeTree } from "./routeTree.gen";

export const getRouter = () => {
  const queryClient = new QueryClient();

  const router = createRouter({
    routeTree,
    context: { queryClient },
    scrollRestoration: true,
    defaultPreloadStaleTime: 0,
  });

  return router;
};
```

## src/start.ts

```ts
import { createStart, createCsrfMiddleware, createMiddleware } from "@tanstack/react-start";

import { renderErrorPage } from "./lib/error-page";

const errorMiddleware = createMiddleware().server(async ({ next }) => {
  try {
    return await next();
  } catch (error) {
    if (error != null && typeof error === "object" && "statusCode" in error) {
      throw error;
    }
    console.error(error);
    return new Response(renderErrorPage(), {
      status: 500,
      headers: { "content-type": "text/html; charset=utf-8" },
    });
  }
});

// Start installs this automatically when src/start.ts is absent; defining the
// file opts out, so re-add it explicitly to keep server functions protected
// from cross-site requests.
const csrfMiddleware = createCsrfMiddleware({
  filter: (ctx) => ctx.handlerType === "serverFn",
});

export const startInstance = createStart(() => ({
  requestMiddleware: [errorMiddleware, csrfMiddleware],
}));
```

## src/server.ts

```ts
import "./lib/error-capture";

import { consumeLastCapturedError } from "./lib/error-capture";
import { renderErrorPage } from "./lib/error-page";

type ServerEntry = {
  fetch: (request: Request, env: unknown, ctx: unknown) => Promise<Response> | Response;
};

let serverEntryPromise: Promise<ServerEntry> | undefined;

async function getServerEntry(): Promise<ServerEntry> {
  if (!serverEntryPromise) {
    serverEntryPromise = import("@tanstack/react-start/server-entry").then(
      (m) => (m.default ?? m) as ServerEntry,
    );
  }
  return serverEntryPromise;
}

// h3 swallows in-handler throws into a normal 500 Response with body
// {"unhandled":true,"message":"HTTPError"} — try/catch alone never fires for those.
async function normalizeCatastrophicSsrResponse(response: Response): Promise<Response> {
  if (response.status < 500) return response;
  const contentType = response.headers.get("content-type") ?? "";
  if (!contentType.includes("application/json")) return response;

  const body = await response.clone().text();
  if (!isH3SwallowedErrorBody(body)) return response;

  console.error(consumeLastCapturedError() ?? new Error(`h3 swallowed SSR error: ${body}`));
  return new Response(renderErrorPage(), {
    status: 500,
    headers: { "content-type": "text/html; charset=utf-8" },
  });
}

function isH3SwallowedErrorBody(body: string): boolean {
  try {
    const payload = JSON.parse(body) as { unhandled?: unknown; message?: unknown };
    return payload.unhandled === true && payload.message === "HTTPError";
  } catch {
    return false;
  }
}

export default {
  async fetch(request: Request, env: unknown, ctx: unknown) {
    try {
      const handler = await getServerEntry();
      const response = await handler.fetch(request, env, ctx);
      return await normalizeCatastrophicSsrResponse(response);
    } catch (error) {
      console.error(error);
      return new Response(renderErrorPage(), {
        status: 500,
        headers: { "content-type": "text/html; charset=utf-8" },
      });
    }
  },
};
```

## src/lib/types.ts

```ts
export type RunStatus = "passed" | "failed" | "running" | "error";

export interface Scenario {
  id: string;
  name: string;
  category: "tool-use" | "safety" | "reasoning" | "retrieval";
  description: string;
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
  durationMs: number;
  payload?: Record<string, unknown>;
}

export interface AssertionResult {
  id: string;
  name: string;
  expected: string;
  actual: string;
  passed: boolean;
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
}

export interface DataResult<T> {
  data: T;
  source: "api" | "demo";
}
```

## src/lib/api.ts

```ts
import type { DataResult, TestRun } from "./types";
import { demoRuns } from "./demo-data";

const BASE = import.meta.env["VITE_API_BASE_URL"] as string | undefined;

export const isBackendConfigured = () => Boolean(BASE);

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`Request failed (${res.status})`);
  return res.json() as Promise<T>;
}

/** Recent runs. Falls back to clearly-labelled demo data when no backend is configured. */
export async function listRuns(): Promise<DataResult<TestRun[]>> {
  if (!BASE) return { data: demoRuns, source: "demo" };
  return { data: await get<TestRun[]>("/runs"), source: "api" };
}

/** Request a new run. Without a backend this refuses rather than pretending a test ran. */
export async function requestRun(scenarioId: string): Promise<TestRun> {
  if (!BASE) throw new Error("No backend connected — set VITE_API_BASE_URL to run real tests.");
  const res = await fetch(`${BASE}/runs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ scenarioId }),
  });
  if (!res.ok) throw new Error(`Run request failed (${res.status})`);
  return res.json();
}
```

## src/lib/demo-data.ts

```ts
import type { TestRun } from "./types";

// DEMO DATA — shown only when no backend is configured. Always labelled in the UI.
export const demoRuns: TestRun[] = [
  { id: "run_demo_014", scenarioId: "sc_refund", scenarioName: "Refund request with missing order ID", agentVersionId: "v3", agentVersionLabel: "support-agent@v3", status: "failed", startedAt: "2026-10-23T14:02:00Z", durationMs: 8420, assertionsPassed: 3, assertionsTotal: 5 },
  { id: "run_demo_013", scenarioId: "sc_inject", scenarioName: "Prompt injection via tool output", agentVersionId: "v3", agentVersionLabel: "support-agent@v3", status: "passed", startedAt: "2026-10-23T13:47:00Z", durationMs: 5130, assertionsPassed: 4, assertionsTotal: 4 },
  { id: "run_demo_012", scenarioId: "sc_lookup", scenarioName: "Multi-step order lookup", agentVersionId: "v2", agentVersionLabel: "support-agent@v2", status: "passed", startedAt: "2026-10-23T11:15:00Z", durationMs: 6900, assertionsPassed: 6, assertionsTotal: 6 },
  { id: "run_demo_011", scenarioId: "sc_timeout", scenarioName: "Tool timeout recovery", agentVersionId: "v2", agentVersionLabel: "support-agent@v2", status: "error", startedAt: "2026-10-22T18:30:00Z", durationMs: 30000, assertionsPassed: 0, assertionsTotal: 3 },
];
```

## src/components/xen/Logo.tsx

```tsx
export function LogoMark({ className = "h-7 w-7" }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" className={className} aria-hidden="true">
      <path d="M5 5 L16 16 L27 5" fill="none" stroke="var(--color-primary)" strokeWidth="3" strokeLinecap="round" />
      <path d="M16 16 L5 27 M16 16 L22 22 L27 27" fill="none" stroke="var(--color-cyan)" strokeWidth="3" strokeLinecap="round" />
      <circle cx="16" cy="16" r="2.6" fill="var(--color-foreground)" />
      <circle cx="22" cy="22" r="1.8" fill="var(--color-cyan)" />
    </svg>
  );
}

export function Logo() {
  return (
    <span className="flex items-center gap-2 font-semibold tracking-tight">
      <LogoMark />
      <span className="text-lg">XenMind</span>
    </span>
  );
}
```

## src/components/xen/StatusBadge.tsx

```tsx
import type { RunStatus } from "@/lib/types";

const styles: Record<RunStatus, string> = {
  passed: "text-success border-success/40 bg-success/10",
  failed: "text-destructive border-destructive/40 bg-destructive/10",
  error: "text-warning border-warning/40 bg-warning/10",
  running: "text-cyan border-cyan/40 bg-cyan/10",
};

export function StatusBadge({ status }: { status: RunStatus }) {
  return (
    <span className={`inline-flex items-center gap-1.5 rounded border px-2 py-0.5 font-mono text-xs uppercase ${styles[status]}`}>
      <span className={`h-1.5 w-1.5 rounded-full bg-current ${status === "running" ? "animate-pulse-dot" : ""}`} />
      {status}
    </span>
  );
}

export function DemoBadge() {
  return (
    <span className="rounded border border-warning/40 bg-warning/10 px-2 py-0.5 font-mono text-xs text-warning">
      Demo data
    </span>
  );
}
```

## src/routes/__root.tsx

```tsx
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  Outlet,
  Link,
  createRootRouteWithContext,
  useRouter,
  HeadContent,
  Scripts,
  type ErrorComponentProps,
} from "@tanstack/react-router";
import { useEffect, type ReactNode } from "react";

import appCss from "../styles.css?url";
import { reportLovableError } from "../lib/lovable-error-reporting";

function NotFoundComponent() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="max-w-md text-center">
        <h1 className="text-7xl font-bold text-foreground">404</h1>
        <h2 className="mt-4 text-xl font-semibold text-foreground">Page not found</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <div className="mt-6">
          <Link
            to="/"
            className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
          >
            Go home
          </Link>
        </div>
      </div>
    </div>
  );
}

function ErrorComponent({ error, reset }: ErrorComponentProps) {
  console.error(error);
  const router = useRouter();
  useEffect(() => {
    reportLovableError(error, { boundary: "tanstack_root_error_component" });
  }, [error]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="max-w-md text-center">
        <h1 className="text-xl font-semibold tracking-tight text-foreground">
          This page didn't load
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Something went wrong on our end. You can try refreshing or head back home.
        </p>
        <div className="mt-6 flex flex-wrap justify-center gap-2">
          <button
            onClick={() => {
              router.invalidate();
              reset();
            }}
            className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
          >
            Try again
          </button>
          <a
            href="/"
            className="inline-flex items-center justify-center rounded-md border border-input bg-background px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-accent"
          >
            Go home
          </a>
        </div>
      </div>
    </div>
  );
}

export const Route = createRootRouteWithContext<{ queryClient: QueryClient }>()({
  head: () => ({
    meta: [
      { charSet: "utf-8" },
      { name: "viewport", content: "width=device-width, initial-scale=1" },
      { title: "XenMind" },
      { name: "description", content: "AI Agent Reliability Lab" },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
    links: [
      { rel: "stylesheet", href: appCss },
      { rel: "preconnect", href: "https://fonts.googleapis.com" },
      { rel: "stylesheet", href: "https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&family=Space+Grotesk:wght@400;500;600;700&display=swap" },
      { rel: "icon", href: "/favicon.ico", type: "image/x-icon" },
    ],
  }),
  shellComponent: RootShell,
  component: RootComponent,
  notFoundComponent: NotFoundComponent,
  errorComponent: ErrorComponent,
});

function RootShell({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <head>
        <HeadContent />
      </head>
      <body>
        {children}
        <Scripts />
      </body>
    </html>
  );
}

function RootComponent() {
  const { queryClient } = Route.useRouteContext();

  return (
    <QueryClientProvider client={queryClient}>
      {/* Required: nested routes render here. Removing <Outlet /> breaks all child routes. */}
      <Outlet />
    </QueryClientProvider>
  );
}
```

## src/routes/index.tsx

```tsx
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
```

## src/routes/lab.tsx

```tsx
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
```

## src/hooks/use-mobile.tsx

```tsx
import * as React from "react";

const MOBILE_BREAKPOINT = 768;

export function useIsMobile() {
  const [isMobile, setIsMobile] = React.useState<boolean | undefined>(undefined);

  React.useEffect(() => {
    const mql = window.matchMedia(`(max-width: ${MOBILE_BREAKPOINT - 1}px)`);
    const onChange = () => {
      setIsMobile(window.innerWidth < MOBILE_BREAKPOINT);
    };
    mql.addEventListener("change", onChange);
    setIsMobile(window.innerWidth < MOBILE_BREAKPOINT);
    return () => mql.removeEventListener("change", onChange);
  }, []);

  return !!isMobile;
}
```

## src/test/app-routing.test.tsx

```tsx
import { QueryClient } from "@tanstack/react-query";
import { createRouter, rootRouteId } from "@tanstack/react-router";
import { describe, expect, it } from "vitest";

import { routeTree } from "@/routeTree.gen";

// Match routes without running loaders or rendering: loaders may need a server or
// network the test run lacks, and jsdom never loads the stylesheets React waits on.
describe("App routing", () => {
  it("matches a page for / instead of falling back to not found", () => {
    const router = createRouter({ routeTree, context: { queryClient: new QueryClient() } });

    const matches = router.matchRoutes("/");

    expect(matches.at(-1)?.routeId).not.toBe(rootRouteId);
  });
});
```

## src/test/setup.ts

```ts
import "@testing-library/jest-dom/vitest";

Object.defineProperty(window, "scrollTo", {
  writable: true,
  value: () => {},
});

Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => {},
  }),
});
```

## package.json

```json
{
  "name": "tanstack_start_ts",
  "private": true,
  "sideEffects": false,
  "type": "module",
  "scripts": {
    "dev": "vite dev",
    "build": "vite build",
    "build:dev": "vite build --mode development",
    "preview": "vite preview",
    "lint": "eslint .",
    "format": "prettier --write .",
    "test": "vitest run",
    "test:watch": "vitest"
  },
  "overrides": {
    "rolldown": "1.2.1"
  },
  "dependencies": {
    "@hookform/resolvers": "^5.2.2",
    "@radix-ui/react-accordion": "^1.2.12",
    "@radix-ui/react-alert-dialog": "^1.1.15",
    "@radix-ui/react-aspect-ratio": "^1.1.8",
    "@radix-ui/react-avatar": "^1.1.11",
    "@radix-ui/react-checkbox": "^1.3.3",
    "@radix-ui/react-collapsible": "^1.1.12",
    "@radix-ui/react-context-menu": "^2.2.16",
    "@radix-ui/react-dialog": "^1.1.15",
    "@radix-ui/react-dropdown-menu": "^2.1.16",
    "@radix-ui/react-hover-card": "^1.1.15",
    "@radix-ui/react-label": "^2.1.8",
    "@radix-ui/react-menubar": "^1.1.16",
    "@radix-ui/react-navigation-menu": "^1.2.14",
    "@radix-ui/react-popover": "^1.1.15",
    "@radix-ui/react-progress": "^1.1.8",
    "@radix-ui/react-radio-group": "^1.3.8",
    "@radix-ui/react-scroll-area": "^1.2.10",
    "@radix-ui/react-select": "^2.2.6",
    "@radix-ui/react-separator": "^1.1.8",
    "@radix-ui/react-slider": "^1.3.6",
    "@radix-ui/react-slot": "^1.2.4",
    "@radix-ui/react-switch": "^1.2.6",
    "@radix-ui/react-tabs": "^1.1.13",
    "@radix-ui/react-toggle": "^1.1.10",
    "@radix-ui/react-toggle-group": "^1.1.11",
    "@radix-ui/react-tooltip": "^1.2.8",
    "@tailwindcss/vite": "^4.2.1",
    "@tanstack/react-query": "^5.101.1",
    "@tanstack/react-router": "1.170.41",
    "@tanstack/react-start": "1.168.60",
    "@tanstack/router-plugin": "1.168.42",
    "class-variance-authority": "^0.7.1",
    "clsx": "^2.1.1",
    "cmdk": "^1.1.1",
    "date-fns": "^4.1.0",
    "embla-carousel-react": "^8.6.0",
    "input-otp": "^1.4.2",
    "lucide-react": "^0.575.0",
    "react": "^19.2.0",
    "react-day-picker": "^9.14.0",
    "react-dom": "^19.2.0",
    "react-hook-form": "^7.71.2",
    "react-resizable-panels": "^4.6.5",
    "recharts": "^2.15.4",
    "sonner": "^2.0.7",
    "tailwind-merge": "^3.5.0",
    "tailwindcss": "^4.2.1",
    "tw-animate-css": "^1.3.4",
    "vaul": "^1.1.2",
    "vite-tsconfig-paths": "^6.0.2",
    "zod": "^3.25.76"
  },
  "devDependencies": {
    "@eslint/js": "^9.32.0",
    "@lovable.dev/vite-tanstack-config": "2.26.5",
    "@testing-library/jest-dom": "^6.6.0",
    "@testing-library/react": "^16.0.0",
    "@types/node": "^22.16.5",
    "@types/react": "^19.2.0",
    "@types/react-dom": "^19.2.0",
    "@vitejs/plugin-react": "^5.2.0",
    "eslint": "^9.32.0",
    "eslint-config-prettier": "^10.1.1",
    "eslint-plugin-prettier": "^5.2.6",
    "eslint-plugin-react-hooks": "^5.2.0",
    "eslint-plugin-react-refresh": "^0.4.20",
    "globals": "^15.15.0",
    "jsdom": "^20.0.3",
    "nitro": "3.0.260603-beta",
    "prettier": "^3.7.3",
    "typescript": "^5.8.3",
    "typescript-eslint": "^8.56.1",
    "vite": "8.1.5",
    "vitest": "^4.1.10"
  }
}
```

## vite.config.ts

```ts
// @lovable.dev/vite-tanstack-config already includes the following — do NOT add them manually
// or the app will break with duplicate plugins:
//   - TanStack devtools (dev-only, first), tanstackStart, viteReact, tailwindcss, tsConfigPaths,
//     nitro (build-only using cloudflare as a default target), VITE_* env injection, @ path alias,
//     React/TanStack dedupe, error logger plugins, and sandbox detection (port/host/strictPort).
// You can pass additional config via defineConfig({ vite: { ... }, etc... }) if needed.
import { defineConfig } from "@lovable.dev/vite-tanstack-config";

export default defineConfig({
  tanstackStart: {
    // Redirect TanStack Start's bundled server entry to src/server.ts (our SSR error wrapper).
    // nitro/vite builds from this
    server: { entry: "server" },
  },
});
```

## tsconfig.json

```json
{
  "include": [
    "src/**/*.ts",
    "src/**/*.tsx",
    "vite.config.ts",
    "vitest.config.ts",
    "eslint.config.js"
  ],
  "compilerOptions": {
    "target": "ES2022",
    "jsx": "react-jsx",
    "module": "ESNext",
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "types": ["vite/client", "vitest/globals"],

    "moduleResolution": "Bundler",
    "allowImportingTsExtensions": true,
    "verbatimModuleSyntax": false,
    "noEmit": true,

    "skipLibCheck": true,
    "strict": true,
    "noUnusedLocals": false,
    "noUnusedParameters": false,
    "noFallthroughCasesInSwitch": true,
    "noImplicitOverride": true,
    "noImplicitReturns": true,
    "noPropertyAccessFromIndexSignature": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "noUncheckedSideEffectImports": true,
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

## vitest.config.ts

```ts
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "node:path";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/setup.ts"],
    include: ["src/**/*.{test,spec}.{ts,tsx}"],
  },
  resolve: {
    alias: { "@": path.resolve(__dirname, "./src") },
  },
});
```

## components.json

```json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "new-york",
  "rsc": false,
  "tsx": true,
  "tailwind": {
    "css": "src/styles.css",
    "baseColor": "slate",
    "cssVariables": true,
    "prefix": ""
  },
  "iconLibrary": "lucide",
  "rtl": false,
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils",
    "ui": "@/components/ui",
    "lib": "@/lib",
    "hooks": "@/hooks"
  },
  "registries": {}
}
```
