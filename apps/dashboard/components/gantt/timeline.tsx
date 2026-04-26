"use client";

import { useMemo } from "react";
import { Wrench } from "lucide-react";
import { cn, gbp } from "@/lib/utils";
import type { HireStatus } from "@fleetpro/db";

type HireBar = {
  id: string;
  startDate: Date | string;
  endDate: Date | string;
  status: HireStatus;
  totalGbp: number;
  customer: { fullName: string };
};

type Row = {
  vehicle: {
    id: string;
    make: string;
    model: string;
    trim: string | null;
    vrn: string;
    status: string;
  };
  hires: HireBar[];
  utilisation: number;
};

type Props = {
  from: Date;
  to: Date;
  rows: Row[];
};

// Pick a tone class (bg + fg) per hire status / vehicle status
const TONE = {
  ACTIVE: "bg-gantt-active text-gantt-activeFg",
  AWAITING_SIGNATURE: "bg-gantt-upcoming text-gantt-upcomingFg",
  DRAFT: "bg-gantt-upcoming text-gantt-upcomingFg",
  COMPLETED: "bg-gantt-completed text-gantt-completedFg",
  CANCELLED: "bg-rule text-ink-muted",
} as const;

function dayKey(d: Date) {
  return `${d.getDate()}/${d.getMonth() + 1}`;
}

function pctOfWindow(t: number, from: number, span: number): number {
  return Math.max(0, Math.min(100, ((t - from) / span) * 100));
}

export function GanttTimeline({ from, to, rows }: Props) {
  const fromMs = from.getTime();
  const span = to.getTime() - fromMs;
  const today = Date.now();
  const todayPct = today >= fromMs && today <= to.getTime() ? pctOfWindow(today, fromMs, span) : null;

  // Tick marks every 7 days, plus first and last
  const ticks = useMemo(() => {
    const out: { pct: number; label: string }[] = [];
    const dayMs = 86_400_000;
    for (let t = fromMs; t <= to.getTime(); t += 7 * dayMs) {
      out.push({ pct: pctOfWindow(t, fromMs, span), label: dayKey(new Date(t)) });
    }
    return out;
  }, [fromMs, span, to]);

  return (
    <div className="overflow-x-auto" role="region" aria-label="Fleet timeline">
      <div className="min-w-[900px]">
        {/* Header row: vehicle column + tick scale */}
        <div className="grid grid-cols-[280px_1fr] border-b border-rule">
          <div className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-ink-muted">
            Vehicle
          </div>
          <div className="relative h-10">
            {ticks.map((t, i) => (
              <div
                key={i}
                className="absolute top-0 -translate-x-1/2 text-[11px] tabular-nums text-ink-muted"
                style={{ left: `${t.pct}%` }}
              >
                {t.label}
              </div>
            ))}
            {todayPct !== null && (
              <div
                className="absolute -top-0 z-10"
                style={{ left: `${todayPct}%`, transform: "translateX(-50%)" }}
              >
                <span
                  className="inline-block rounded-md bg-gantt-today text-white text-[11px] font-semibold px-2 py-0.5"
                  aria-hidden
                >
                  today
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Rows */}
        <ul className="divide-y divide-rule">
          {rows.length === 0 && (
            <li className="px-4 py-8 text-center text-sm text-ink-muted">No vehicles match this view.</li>
          )}
          {rows.map((row) => (
            <li key={row.vehicle.id} className="grid grid-cols-[280px_1fr] items-center">
              <div className="px-4 py-3">
                <div className="font-medium text-ink leading-tight">
                  {row.vehicle.make} {row.vehicle.model} {row.vehicle.trim ?? ""}
                </div>
                <div className="mt-0.5 flex items-center justify-between text-xs">
                  <span className="text-ink-muted tabular-nums">{row.vehicle.vrn}</span>
                  <span
                    className={cn(
                      "tabular-nums font-medium",
                      row.utilisation >= 0.7 ? "text-ok" : row.utilisation >= 0.4 ? "text-warn" : "text-bad",
                    )}
                  >
                    {Math.round(row.utilisation * 100)}%
                  </span>
                </div>
              </div>
              <div className="relative h-14 border-l border-rule">
                {/* Today vertical line */}
                {todayPct !== null && (
                  <div
                    className="absolute top-0 bottom-0 w-px bg-gantt-today/70"
                    style={{ left: `${todayPct}%` }}
                    aria-hidden
                  />
                )}
                {/* Vertical week guides */}
                {ticks.map((t, i) => (
                  <div
                    key={i}
                    className="absolute top-0 bottom-0 w-px bg-rule/60"
                    style={{ left: `${t.pct}%` }}
                    aria-hidden
                  />
                ))}
                {/* Hire bars */}
                {row.hires.map((h) => {
                  const startMs = new Date(h.startDate).getTime();
                  const endMs = new Date(h.endDate).getTime();
                  const left = pctOfWindow(startMs, fromMs, span);
                  const right = pctOfWindow(endMs, fromMs, span);
                  const width = Math.max(1, right - left);
                  const tone = TONE[h.status as keyof typeof TONE] ?? TONE.COMPLETED;
                  const isMaintenance = row.vehicle.status === "MAINTENANCE";
                  return (
                    <button
                      key={h.id}
                      type="button"
                      className={cn(
                        "absolute top-1/2 -translate-y-1/2 h-7 rounded-md px-2 text-[12px] font-medium truncate flex items-center gap-1 shadow-sm focus-visible:outline-2",
                        isMaintenance ? "bg-gantt-maintenance text-gantt-maintenanceFg" : tone,
                      )}
                      style={{ left: `${left}%`, width: `${width}%` }}
                      aria-label={`Hire ${h.id}, customer ${h.customer.fullName}, ${new Date(h.startDate).toLocaleDateString("en-GB")} to ${new Date(h.endDate).toLocaleDateString("en-GB")}, total ${gbp(h.totalGbp)}`}
                      title={`${h.customer.fullName} · ${new Date(h.startDate).toLocaleDateString("en-GB")} → ${new Date(h.endDate).toLocaleDateString("en-GB")}`}
                    >
                      <span className="h-1.5 w-1.5 rounded-full bg-white/90 shrink-0" aria-hidden />
                      <span className="truncate">{h.customer.fullName}</span>
                      {isMaintenance && <Wrench className="h-3 w-3 shrink-0" aria-hidden />}
                    </button>
                  );
                })}
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

export function GanttLegend() {
  const items: { tone: string; label: string }[] = [
    { tone: "bg-gantt-active", label: "Active" },
    { tone: "bg-gantt-upcoming", label: "Upcoming" },
    { tone: "bg-gantt-completed", label: "Completed" },
    { tone: "bg-gantt-maintenance", label: "Maintenance" },
  ];
  return (
    <ul className="flex items-center gap-4 text-xs text-ink-muted" aria-label="Timeline legend">
      {items.map((i) => (
        <li key={i.label} className="inline-flex items-center gap-2">
          <span className={cn("h-2.5 w-2.5 rounded-sm", i.tone)} aria-hidden />
          {i.label}
        </li>
      ))}
    </ul>
  );
}
