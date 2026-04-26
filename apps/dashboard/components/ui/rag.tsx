import type { RagStatus } from "@fleetpro/db";

const MAP: Record<RagStatus, { label: string; bg: string; fg: string; aria: string }> = {
  GREEN: { label: "Good to Go", bg: "bg-ok-soft", fg: "text-ok", aria: "RAG status: green, good to go" },
  AMBER: { label: "Consider Defleet", bg: "bg-warn-soft", fg: "text-warn", aria: "RAG status: amber, consider defleet" },
  RED: { label: "Risk Asset — Defleet", bg: "bg-bad-soft", fg: "text-bad", aria: "RAG status: red, risk asset, defleet" },
};

export function RagPill({ status }: { status: RagStatus }) {
  const m = MAP[status];
  return (
    <span aria-label={m.aria} className={`inline-flex items-center gap-1.5 rounded-md ${m.bg} ${m.fg} px-2 py-0.5 text-xs font-medium`}>
      <span className="h-1.5 w-1.5 rounded-full bg-current" aria-hidden />
      {m.label}
    </span>
  );
}

export function RagDot({ status }: { status: RagStatus }) {
  const m = MAP[status];
  return <span aria-label={m.aria} className={`inline-block h-2 w-2 rounded-full ${m.fg}`} />;
}
