import { AlertOctagon, Clock, CheckCircle2 } from "lucide-react";
import { maintenanceBuckets } from "@/lib/queries";
import { PageHeader } from "@/components/ui/page-header";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { DuePill } from "@/components/ui/due-pill";
import { cn } from "@/lib/utils";

export const dynamic = "force-dynamic";

type Vehicle = Awaited<ReturnType<typeof maintenanceBuckets>>["overdue"][number];

const SECTION_ICON = {
  overdue: { icon: AlertOctagon, color: "text-bad" },
  dueSoon: { icon: Clock, color: "text-warn" },
  allGood: { icon: CheckCircle2, color: "text-ok" },
} as const;

function MaintenanceTable({ vehicles }: { vehicles: Vehicle[] }) {
  if (vehicles.length === 0) {
    return <div className="px-5 py-6 text-sm text-ink-muted text-center">No vehicles in this bucket.</div>;
  }
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="bg-page/40">
          <tr className="text-[11px] uppercase tracking-wider text-ink-muted text-left">
            <th scope="col" className="px-5 py-2 font-semibold">Vehicle</th>
            <th scope="col" className="px-5 py-2 font-semibold">Plate</th>
            <th scope="col" className="px-5 py-2 font-semibold">MOT</th>
            <th scope="col" className="px-5 py-2 font-semibold">Insurance</th>
            <th scope="col" className="px-5 py-2 font-semibold">Service</th>
            <th scope="col" className="px-5 py-2 font-semibold"><span className="sr-only">Actions</span></th>
          </tr>
        </thead>
        <tbody className="divide-y divide-rule">
          {vehicles.map((v) => (
            <tr key={v.id} className="hover:bg-page/40">
              <td className="px-5 py-3">
                <div className="font-medium">{v.make} {v.model} {v.trim ?? ""}</div>
                <div className="text-xs text-ink-muted">{v.yearOfManufacture}</div>
              </td>
              <td className="px-5 py-3 tabular-nums">{v.vrn}</td>
              <td className="px-5 py-3"><DuePill label="MOT" due={v.motDue} /></td>
              <td className="px-5 py-3"><DuePill label="Ins" due={v.insuranceDue} /></td>
              <td className="px-5 py-3"><DuePill label="Svc" due={v.taxDue} /></td>
              <td className="px-5 py-3 text-right pr-5">
                <button
                  type="button"
                  className="rounded-md border border-rule bg-card px-3 py-1.5 text-xs font-medium hover:bg-page focus-visible:outline-2"
                  aria-label={`Book service for ${v.make} ${v.model} ${v.vrn}`}
                >
                  Book service
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function MaintenanceStat({ tone, label, count }: { tone: "bad" | "warn" | "ok"; label: string; count: number }) {
  const border = tone === "bad" ? "border-l-bad" : tone === "warn" ? "border-l-warn" : "border-l-ok";
  const num = tone === "bad" ? "text-bad" : tone === "warn" ? "text-warn" : "text-ok";
  return (
    <Card className={cn("p-5 border-l-4 rounded-l-md", border)}>
      <dt className="text-xs font-semibold tracking-wider text-ink-muted uppercase">{label}</dt>
      <dd className={cn("mt-2 text-3xl font-semibold tabular-nums", num)}>{count}</dd>
    </Card>
  );
}

export default async function MaintenancePage() {
  const buckets = await maintenanceBuckets();

  return (
    <>
      <PageHeader title="Maintenance & MOT" subtitle="Service schedule, MOT, insurance expiry" />

      <section aria-label="Maintenance summary" className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MaintenanceStat tone="bad" label="Overdue" count={buckets.overdue.length} />
        <MaintenanceStat tone="warn" label="Due in 30 days" count={buckets.dueSoon.length} />
        <MaintenanceStat tone="ok" label="All good" count={buckets.allGood.length} />
      </section>

      {(["overdue", "dueSoon", "allGood"] as const).map((key) => {
        const Icon = SECTION_ICON[key].icon;
        const color = SECTION_ICON[key].color;
        const title =
          key === "overdue" ? `Overdue (${buckets.overdue.length})` :
          key === "dueSoon" ? `Due in 30 days (${buckets.dueSoon.length})` :
                              `All good (${buckets.allGood.length})`;
        const list = buckets[key];
        return (
          <Card key={key} className="mt-6">
            <CardHeader>
              <CardTitle>
                <span className="inline-flex items-center gap-2">
                  <Icon className={cn("h-4 w-4", color)} aria-hidden /> {title}
                </span>
              </CardTitle>
            </CardHeader>
            <MaintenanceTable vehicles={list} />
          </Card>
        );
      })}
    </>
  );
}
