import { cn, daysUntil, formatDate } from "@/lib/utils";

/**
 * Compact "label: value" pill used in Maintenance.
 *  - OVERDUE  → red
 *  - ≤ 30d    → amber
 *  - > 30d    → green
 */
export function DuePill({ label, due }: { label: string; due: Date | string | null | undefined }) {
  if (!due) return <span className="text-ink-muted text-xs">—</span>;
  const days = daysUntil(due);
  const overdue = days < 0;
  const soon = days >= 0 && days <= 30;
  const tone = overdue
    ? "bg-bad-soft text-bad"
    : soon
      ? "bg-warn-soft text-warn"
      : "bg-ok-soft text-ok";
  return (
    <span className="inline-flex flex-col gap-0.5">
      <span className="tabular-nums text-xs">{formatDate(due)}</span>
      <span className={cn("inline-flex w-fit items-center rounded-md px-1.5 py-0.5 text-[11px] font-medium", tone)}>
        {label}: {overdue ? "OVERDUE" : `${days}d`}
      </span>
    </span>
  );
}
