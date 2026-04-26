import {
  analyticsTotals,
  fleetUtilisation,
  revenueLastSixMonths,
  fleetMixByClass,
} from "@/lib/queries";
import { PageHeader } from "@/components/ui/page-header";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { StatCard } from "@/components/ui/stat-card";
import { RevenueBarChart } from "@/components/charts/revenue-bar";
import { FleetMixDonut } from "@/components/charts/fleet-mix-donut";
import { gbp, pct } from "@/lib/utils";

export const dynamic = "force-dynamic";

export default async function AnalyticsPage() {
  const [totals, util, monthly, mix] = await Promise.all([
    analyticsTotals(),
    fleetUtilisation(),
    revenueLastSixMonths(),
    fleetMixByClass(),
  ]);

  return (
    <>
      <PageHeader title="Analytics" subtitle="Revenue & utilisation insights" />

      <section aria-label="Analytics summary" className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        <StatCard
          label="Fleet utilisation"
          value={pct(util.utilisation)}
          hint={`${util.activeHires} of ${util.hireable} on hire`}
          hintTone="ok"
        />
        <StatCard label="Total revenue" value={gbp(totals.totalRevenueGbpPence)} hint={`across all vehicles`} />
        <StatCard
          label="Avg rental value"
          value={gbp(totals.avgRentalGbpPence)}
          hint={`across ${totals.totalHires} rentals`}
        />
        <StatCard
          label="Avg duration"
          value={`${(totals.avgDurationDays / 30).toFixed(1)} mo`}
          hint={`${totals.avgDurationDays} days average`}
        />
      </section>

      <section className="mt-8 grid grid-cols-1 xl:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Revenue by month</CardTitle>
          </CardHeader>
          <div className="p-5">
            <RevenueBarChart data={monthly} />
          </div>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Fleet mix by class</CardTitle>
          </CardHeader>
          <div className="p-5">
            <FleetMixDonut data={mix} />
          </div>
        </Card>
      </section>
    </>
  );
}
