import { Card } from "./card";
import { cn } from "@/lib/utils";

export type StatCardProps = {
  label: string;
  value: React.ReactNode;
  hint?: React.ReactNode;
  /** Tone for the small hint line below the number. */
  hintTone?: "ok" | "warn" | "bad" | "muted";
};

const HINT_CLASSES: Record<NonNullable<StatCardProps["hintTone"]>, string> = {
  ok: "text-ok",
  warn: "text-warn",
  bad: "text-bad",
  muted: "text-ink-muted",
};

export function StatCard({ label, value, hint, hintTone = "muted" }: StatCardProps) {
  return (
    <Card className="p-5">
      <dt className="text-xs font-semibold tracking-wider text-ink-muted uppercase">{label}</dt>
      <dd className="mt-2 text-3xl font-semibold text-ink tabular-nums">{value}</dd>
      {hint && <div className={cn("mt-2 text-xs", HINT_CLASSES[hintTone])}>{hint}</div>}
    </Card>
  );
}
