import { vehiclePnL } from "@/lib/queries";
import { PageHeader } from "@/components/ui/page-header";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { StatCard } from "@/components/ui/stat-card";
import { Badge } from "@/components/ui/badge";
import { gbp, gbpCompact } from "@/lib/utils";

export const dynamic = "force-dynamic";

const TARGET_MONTHS = 18;

export default async function VehiclePLPage() {
  const { vehicles, totals } = await vehiclePnL();

  return (
    <>
      <PageHeader title="Vehicle P&L" subtitle="Lifetime profit & loss across the fleet" />

      <section aria-label="P&L summary" className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-4">
        <StatCard label="Total invested" value={gbpCompact(totals.invested)} hint="purchase + repairs + ongoing" />
        <StatCard label="Hire revenue" value={gbpCompact(totals.revenue)} hint="across all vehicles" />
        <StatCard
          label="Sold vehicles"
          value={`${totals.sold} / ${vehicles.length}`}
          hint={`${gbp(0)} net`}
        />
        <StatCard label="Breakeven rate" value="—" hint="no sales yet" hintTone="muted" />
        <StatCard
          label="Projected profit"
          value={`+${gbpCompact(totals.projected)}`}
          hint="if remaining vehicles sold at market"
          hintTone="ok"
        />
      </section>

      <Card className="mt-8">
        <CardHeader>
          <CardTitle>Vehicle-by-vehicle P&L</CardTitle>
        </CardHeader>
        <div className="px-5 py-3 text-xs text-ink-muted border-b border-rule">
          Tap any row to open the vehicle. Progress bar shows hire revenue vs breakeven cost; vertical line is time elapsed against the {TARGET_MONTHS}-month target.
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-page/40">
              <tr className="text-[11px] uppercase tracking-wider text-ink-muted text-left">
                <th scope="col" className="px-5 py-2 font-semibold">Vehicle</th>
                <th scope="col" className="px-5 py-2 font-semibold">Status</th>
                <th scope="col" className="px-5 py-2 font-semibold">Cost</th>
                <th scope="col" className="px-5 py-2 font-semibold">Hire rev.</th>
                <th scope="col" className="px-5 py-2 font-semibold">Sale / market</th>
                <th scope="col" className="px-5 py-2 font-semibold">Net P&L</th>
                <th scope="col" className="px-5 py-2 font-semibold w-72">Breakeven progress</th>
                <th scope="col" className="px-5 py-2 font-semibold">Days</th>
                <th scope="col" className="px-5 py-2 font-semibold">Target</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-rule">
              {vehicles.map((v, idx) => {
                const repairTotal = v.repairInvoices.reduce((s, r) => s + r.totalGbp, 0);
                const cost = v.purchasePriceGbp + repairTotal;
                const hireRev = v.hires.reduce((s, h) => s + h.totalGbp, 0);
                const market = v.marketValueGbp ?? 0;
                const sold = !!v.salePriceGbp;
                const netPnL = hireRev - cost + (v.salePriceGbp ?? 0);
                const breakevenPct = Math.max(0, Math.min(1, hireRev / Math.max(1, cost)));
                const days = Math.round((Date.now() - v.purchaseDate.getTime()) / 86_400_000);
                const targetDays = TARGET_MONTHS * 30;
                const onTrack = days <= targetDays;
                const elapsedPct = Math.min(1, days / targetDays);
                return (
                  <tr key={v.id} className="hover:bg-page/40">
                    <td className="px-5 py-3">
                      <div className="font-medium">{v.make} {v.model} {v.trim ?? ""}</div>
                      <div className="text-xs text-ink-muted tabular-nums">{v.vrn} · V{String(idx + 1).padStart(2, "0")}</div>
                    </td>
                    <td className="px-5 py-3">
                      <Badge tone={v.status === "MAINTENANCE" ? "warn" : v.status === "RENTED" ? "active" : "muted"}>
                        {v.status[0] + v.status.slice(1).toLowerCase().replace("_", " ")}
                      </Badge>
                    </td>
                    <td className="px-5 py-3 tabular-nums">{gbp(cost)}</td>
                    <td className="px-5 py-3 tabular-nums">{gbp(hireRev)}</td>
                    <td className="px-5 py-3 tabular-nums">{sold ? gbp(v.salePriceGbp) : `${gbp(market)}*`}</td>
                    <td className={`px-5 py-3 tabular-nums font-medium ${netPnL < 0 ? "text-bad" : "text-ok"}`}>
                      {netPnL < 0 ? `-${gbp(Math.abs(netPnL))}` : `+${gbp(netPnL)}`}
                    </td>
                    <td className="px-5 py-3">
                      <div className="relative h-2 rounded-full bg-rule" aria-hidden>
                        <div
                          className="absolute inset-y-0 left-0 rounded-full bg-warn"
                          style={{ width: `${breakevenPct * 100}%` }}
                        />
                        <div
                          className="absolute inset-y-[-3px] w-px bg-ink"
                          style={{ left: `${elapsedPct * 100}%` }}
                          title="Time elapsed"
                        />
                      </div>
                      <div className="mt-1 text-[11px] text-ink-muted tabular-nums">
                        {Math.round(breakevenPct * 100)}% of breakeven
                      </div>
                    </td>
                    <td className="px-5 py-3 tabular-nums">{days}d</td>
                    <td className="px-5 py-3">
                      <Badge tone={onTrack ? "ok" : "bad"}>{onTrack ? `${TARGET_MONTHS}mo` : `Past ${TARGET_MONTHS}mo`}</Badge>
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
