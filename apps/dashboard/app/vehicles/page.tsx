import Link from "next/link";
import { ChevronRight, Plus, AlertTriangle } from "lucide-react";
import { prisma, VehicleStatus } from "@fleetpro/db";
import { vehicleList, fleetSummary } from "@/lib/queries";
import { PageHeader } from "@/components/ui/page-header";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { StatCard } from "@/components/ui/stat-card";
import { Badge } from "@/components/ui/badge";
import { gbp, gbpCompact, formatDate, daysUntil } from "@/lib/utils";

export const dynamic = "force-dynamic";

const STATUS_TONE: Record<VehicleStatus, "active" | "ok" | "warn" | "muted" | "bad"> = {
  AVAILABLE: "ok",
  RENTED: "active",
  MAINTENANCE: "warn",
  CLEANING: "muted",
  OFF_FLEET: "muted",
  SOLD: "bad",
};

const STATUS_LABEL: Record<VehicleStatus, string> = {
  AVAILABLE: "Available",
  RENTED: "Rented",
  MAINTENANCE: "Maintenance",
  CLEANING: "Cleaning",
  OFF_FLEET: "Off fleet",
  SOLD: "Sold",
};

export default async function VehiclesPage({
  searchParams,
}: {
  searchParams: Promise<{ class?: string; availability?: string }>;
}) {
  const params = await searchParams;
  const [vehicles, summary, financeAgg, monthlyIncome, marketAgg] = await Promise.all([
    vehicleList(),
    fleetSummary(),
    prisma.vehicle.count({ where: { ownership: { in: ["PCP", "HP", "LEASE_PURCHASE"] }, status: { not: "SOLD" } } }),
    prisma.vehicle.aggregate({ _sum: { monthlyRateGbp: true }, where: { status: { not: "SOLD" } } }),
    prisma.vehicle.aggregate({ _sum: { marketValueGbp: true }, where: { status: { not: "SOLD" } } }),
  ]);

  const filtered = vehicles.filter((v) => {
    if (params.class && params.class !== "ALL" && v.vehicleClass !== params.class) return false;
    if (params.availability === "AVAILABLE" && v.status !== "AVAILABLE") return false;
    if (params.availability === "RENTED" && v.status !== "RENTED") return false;
    return true;
  });

  return (
    <>
      <PageHeader title="Vehicles" subtitle="Your fleet, current and historic" />

      <section aria-label="Fleet summary" className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-4">
        <StatCard label="Fleet size" value={summary.fleetSize} hint="vehicles on fleet" />
        <StatCard
          label="Hireable"
          value={summary.hireableCount}
          hint={`${summary.fleetSize - summary.hireableCount} not for hire`}
          hintTone="muted"
        />
        <StatCard label="Market value" value={gbpCompact(marketAgg._sum.marketValueGbp)} hint="current estimate" />
        <StatCard label="On finance" value={financeAgg} hint="PCP / HP / Lease" />
        <StatCard
          label="Monthly income"
          value={gbpCompact(monthlyIncome._sum.monthlyRateGbp)}
          hint="hireable @ 100%"
        />
      </section>

      <Card className="mt-8">
        <CardHeader>
          <CardTitle>All vehicles ({filtered.length})</CardTitle>
          <div className="flex items-center gap-2">
            <form>
              <select
                name="class"
                defaultValue={params.class ?? "ALL"}
                className="rounded-md border border-rule bg-card px-3 py-1.5 text-sm"
                aria-label="Filter by class"
              >
                <option value="ALL">All classes</option>
                <option value="COMPACT">Compact</option>
                <option value="EXECUTIVE">Executive</option>
                <option value="PREMIUM_SUV">Premium SUV</option>
                <option value="ELECTRIC">Electric</option>
                <option value="SUV">SUV</option>
                <option value="VAN">Van</option>
              </select>
              <select
                name="availability"
                defaultValue={params.availability ?? "ALL"}
                className="ml-2 rounded-md border border-rule bg-card px-3 py-1.5 text-sm"
                aria-label="Filter by availability"
              >
                <option value="ALL">All availability</option>
                <option value="AVAILABLE">Available</option>
                <option value="RENTED">Rented</option>
              </select>
            </form>
            <button
              type="button"
              className="inline-flex items-center gap-2 rounded-md border border-rule bg-card px-3 py-1.5 text-sm font-medium hover:bg-page"
            >
              <Plus className="h-4 w-4" aria-hidden /> Add vehicle
            </button>
          </div>
        </CardHeader>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-page/40">
              <tr className="text-[11px] uppercase tracking-wider text-ink-muted text-left">
                <th scope="col" className="px-5 py-2 font-semibold">Vehicle</th>
                <th scope="col" className="px-5 py-2 font-semibold">Plate</th>
                <th scope="col" className="px-5 py-2 font-semibold">Status</th>
                <th scope="col" className="px-5 py-2 font-semibold">Ownership</th>
                <th scope="col" className="px-5 py-2 font-semibold">Current renter</th>
                <th scope="col" className="px-5 py-2 font-semibold">Mileage</th>
                <th scope="col" className="px-5 py-2 font-semibold">Rate</th>
                <th scope="col" className="px-5 py-2 font-semibold">MOT due</th>
                <th scope="col" className="px-5 py-2 font-semibold"><span className="sr-only">Actions</span></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-rule">
              {filtered.map((v) => {
                const due = v.motDue ? daysUntil(v.motDue) : null;
                const motTone = due == null ? "text-ink-muted" : due < 0 ? "text-bad font-medium" : due < 30 ? "text-warn font-medium" : "text-ink";
                return (
                  <tr key={v.id} className="hover:bg-page/40">
                    <td className="px-5 py-3">
                      <div className="font-medium">{v.make} {v.model} {v.trim ?? ""}</div>
                      <div className="text-xs text-ink-muted">
                        {v.yearOfManufacture} · {v.vehicleClass.replace("_", " ").toLowerCase()} · {v.fuelType.toLowerCase()}
                      </div>
                    </td>
                    <td className="px-5 py-3 tabular-nums">{v.vrn}</td>
                    <td className="px-5 py-3">
                      <Badge tone={STATUS_TONE[v.status]}>{STATUS_LABEL[v.status]}</Badge>
                    </td>
                    <td className="px-5 py-3">
                      <span className="text-xs">{v.ownership.replace("_", " ")}</span>
                    </td>
                    <td className="px-5 py-3">
                      {v.hires[0] ? v.hires[0].customer.fullName : <span className="text-ink-muted">—</span>}
                    </td>
                    <td className="px-5 py-3 tabular-nums">{v.currentMileage.toLocaleString("en-GB")} mi</td>
                    <td className="px-5 py-3 tabular-nums">{gbp(v.monthlyRateGbp)}/mo</td>
                    <td className={`px-5 py-3 tabular-nums ${motTone}`}>
                      {formatDate(v.motDue)}
                      {due != null && due < 0 && <AlertTriangle className="inline-block h-3.5 w-3.5 ml-1" aria-label="expired" />}
                    </td>
                    <td className="px-5 py-3 text-right pr-5">
                      <Link href={`/vehicles/${v.id}`} className="inline-flex items-center gap-1 text-brand text-sm hover:underline">
                        Details <ChevronRight className="h-3 w-3" aria-hidden />
                      </Link>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>
    </>
  );
}
