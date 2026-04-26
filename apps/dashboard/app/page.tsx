import {
  fleetSummary,
  revenueThisMonth,
  currentRentals,
  alertsList,
  fleetUtilisation,
  recentAgentActivity,
} from "@/lib/queries";
import { PageHeader } from "@/components/ui/page-header";
import { StatCard } from "@/components/ui/stat-card";
import { CurrentRentalsCard } from "@/components/dashboard/current-rentals";
import { AlertsCard } from "@/components/dashboard/alerts-list";
import { AgentActivityCard } from "@/components/dashboard/agent-activity";
import { gbp, pct } from "@/lib/utils";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  const [summary, rev, util, rentals, alerts, activity] = await Promise.all([
    fleetSummary(),
    revenueThisMonth(),
    fleetUtilisation(),
    currentRentals(5),
    alertsList(8),
    recentAgentActivity(8),
  ]);

  const lastMonthLabel = new Date(Date.now() - 30 * 86_400_000).toLocaleDateString("en-GB", { month: "short" });

  return (
    <>
      <PageHeader title="Fleet Dashboard" subtitle="Overview of your rental operations" />

      <section aria-label="Operational summary" className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        <StatCard
          label="Active rentals"
          value={summary.active}
          hint={<span className="font-medium">↑ {pct(util.utilisation)} utilisation</span>}
          hintTone="ok"
        />
        <StatCard
          label="Available"
          value={summary.available}
          hint={`of ${summary.fleetSize} on fleet`}
        />
        <StatCard
          label={`Revenue · ${rev.monthLabel}`}
          value={gbp(rev.thisMonthGbpPence)}
          hint={
            rev.pctChange >= 0
              ? <span className="font-medium">↑ {pct(rev.pctChange)} vs {lastMonthLabel}</span>
              : <span className="font-medium">↓ {pct(Math.abs(rev.pctChange))} vs {lastMonthLabel}</span>
          }
          hintTone={rev.pctChange >= 0 ? "ok" : "bad"}
        />
        <StatCard
          label="Alerts"
          value={summary.motExpired + summary.motDueSoon}
          hint={`${summary.motExpired} expired · ${summary.motDueSoon} due soon`}
          hintTone={summary.motExpired > 0 ? "bad" : "warn"}
        />
      </section>

      <section aria-label="Day-of operations" className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard label="Returning today" value={summary.returningToday} hint="Schedule inspection & cleaning" />
        <StatCard label="Upcoming rentals" value={summary.upcoming} hint="Starting in next 14 days" />
        <StatCard label="In maintenance" value={summary.maintenance} hint="Off-fleet until service complete" />
      </section>

      <section className="mt-8 grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="xl:col-span-2 space-y-6">
          <CurrentRentalsCard rentals={rentals} />
          <AgentActivityCard items={activity} />
        </div>
        <div>
          <AlertsCard alerts={alerts} />
        </div>
      </section>
    </>
  );
}
