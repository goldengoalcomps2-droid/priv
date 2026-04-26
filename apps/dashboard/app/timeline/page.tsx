import Link from "next/link";
import { ChevronLeft, ChevronRight, Search } from "lucide-react";
import { timelineRows } from "@/lib/queries";
import { PageHeader } from "@/components/ui/page-header";
import { Card } from "@/components/ui/card";
import { GanttTimeline, GanttLegend } from "@/components/gantt/timeline";
import { cn, formatDate, pct } from "@/lib/utils";

export const dynamic = "force-dynamic";

const PRESETS = [
  { id: "7", label: "7 days", days: 7 },
  { id: "30", label: "30 days", days: 30 },
  { id: "60", label: "60 days", days: 60 },
  { id: "180", label: "6 months", days: 180 },
  { id: "365", label: "12 months", days: 365 },
] as const;

export default async function TimelinePage({
  searchParams,
}: {
  searchParams: Promise<{ preset?: string; q?: string; class?: string; from?: string }>;
}) {
  const params = await searchParams;
  const preset = PRESETS.find((p) => p.id === params.preset) ?? PRESETS[2]!; // 60 days default
  const from = params.from ? new Date(params.from) : new Date(new Date().setHours(0, 0, 0, 0));
  // Snap from to the start of the current month for a tidy default
  if (!params.from) from.setDate(1);
  const to = new Date(from.getTime() + preset.days * 86_400_000);

  const { rows, fleetUtilisation } = await timelineRows({
    from,
    to,
    q: params.q,
    vehicleClass: params.class,
  });

  return (
    <>
      <PageHeader
        title="Fleet Timeline"
        subtitle={`${preset.days}-day view of hired and upcoming vehicles`}
      />

      <Card>
        <div className="px-5 py-4 border-b border-rule flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-1" role="tablist" aria-label="Timeline range presets">
            {PRESETS.map((p) => (
              <Link
                key={p.id}
                href={{ pathname: "/timeline", query: { ...params, preset: p.id } }}
                role="tab"
                aria-selected={p.id === preset.id}
                className={cn(
                  "rounded-md px-3 py-1.5 text-sm border",
                  p.id === preset.id
                    ? "border-rule bg-card text-ink shadow-sm"
                    : "border-transparent text-ink-muted hover:text-ink",
                )}
              >
                {p.label}
              </Link>
            ))}
            <Link
              href={{ pathname: "/timeline", query: { ...params, preset: "custom" } }}
              className="rounded-md px-3 py-1.5 text-sm border border-transparent text-ink-muted hover:text-ink"
            >
              Custom…
            </Link>
          </div>
          <div className="ml-auto flex items-center gap-1" aria-label="Pagination">
            <Link
              href={{ pathname: "/timeline", query: { ...params, from: new Date(from.getTime() - preset.days * 86_400_000).toISOString() } }}
              aria-label="Previous window"
              className="rounded-md border border-rule bg-card px-2 py-1.5"
            >
              <ChevronLeft className="h-4 w-4" aria-hidden />
            </Link>
            <Link
              href={{ pathname: "/timeline" }}
              className="rounded-md border border-rule bg-card px-3 py-1.5 text-sm"
            >
              Today
            </Link>
            <Link
              href={{ pathname: "/timeline", query: { ...params, from: new Date(from.getTime() + preset.days * 86_400_000).toISOString() } }}
              aria-label="Next window"
              className="rounded-md border border-rule bg-card px-2 py-1.5"
            >
              <ChevronRight className="h-4 w-4" aria-hidden />
            </Link>
          </div>
        </div>

        <div className="px-5 py-3 border-b border-rule flex flex-wrap items-center gap-4 text-sm">
          <span className="tabular-nums text-ink-muted">
            {formatDate(from)} → {formatDate(to)}
          </span>
          <span className="rounded-md bg-page px-2 py-0.5 text-xs font-medium text-ink-muted">{preset.days} days</span>
          <span className="text-ink-muted">|</span>
          <span className="text-ink">
            Fleet utilisation in window: <strong className="tabular-nums">{pct(fleetUtilisation)}</strong>
          </span>
          <span className="ml-auto">
            <GanttLegend />
          </span>
        </div>

        <form className="px-5 py-3 border-b border-rule flex flex-wrap items-center gap-3" role="search">
          <label className="relative">
            <span className="sr-only">Search plate, model, customer</span>
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-ink-subtle" aria-hidden />
            <input
              name="q"
              defaultValue={params.q ?? ""}
              placeholder="Search plate, model, customer"
              className="w-64 rounded-md border border-rule bg-card pl-9 pr-3 py-1.5 text-sm placeholder:text-ink-subtle"
            />
          </label>
          <input type="hidden" name="preset" value={preset.id} />
          <label>
            <span className="sr-only">Filter by class</span>
            <select
              name="class"
              defaultValue={params.class ?? "ALL"}
              className="rounded-md border border-rule bg-card px-3 py-1.5 text-sm"
            >
              <option value="ALL">All classes</option>
              <option value="COMPACT">Compact</option>
              <option value="EXECUTIVE">Executive</option>
              <option value="PREMIUM_SUV">Premium SUV</option>
              <option value="ELECTRIC">Electric</option>
              <option value="SUV">SUV</option>
              <option value="VAN">Van</option>
            </select>
          </label>
          <label>
            <span className="sr-only">Sort</span>
            <select className="rounded-md border border-rule bg-card px-3 py-1.5 text-sm" name="sort" defaultValue="az">
              <option value="az">Sort: A–Z</option>
              <option value="util">Sort: Utilisation</option>
            </select>
          </label>
        </form>

        <GanttTimeline from={from} to={to} rows={rows} />
      </Card>
    </>
  );
}
