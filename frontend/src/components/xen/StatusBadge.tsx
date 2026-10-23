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
