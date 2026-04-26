import Link from "next/link";
import { Avatar } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { gbp, formatDate } from "@/lib/utils";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import type { currentRentals } from "@/lib/queries";

type Hire = Awaited<ReturnType<typeof currentRentals>>[number];

export function CurrentRentalsCard({ rentals }: { rentals: Hire[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Current rentals</CardTitle>
        <Link href="/rentals" className="text-sm text-brand hover:underline">View all →</Link>
      </CardHeader>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-page/40">
            <tr className="text-[11px] uppercase tracking-wider text-ink-muted text-left">
              <th scope="col" className="px-5 py-2 font-semibold">Vehicle</th>
              <th scope="col" className="px-5 py-2 font-semibold">Customer</th>
              <th scope="col" className="px-5 py-2 font-semibold">Period</th>
              <th scope="col" className="px-5 py-2 font-semibold">Total</th>
              <th scope="col" className="px-5 py-2 font-semibold"><span className="sr-only">Status</span></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-rule">
            {rentals.length === 0 && (
              <tr>
                <td colSpan={5} className="px-5 py-6 text-center text-sm text-ink-muted">No active rentals.</td>
              </tr>
            )}
            {rentals.map((h) => (
              <tr key={h.id} className="hover:bg-page/40">
                <td className="px-5 py-3">
                  <div className="font-medium text-ink">{h.vehicle.make} {h.vehicle.model} {h.vehicle.trim ?? ""}</div>
                  <div className="text-xs text-ink-muted tabular-nums">{h.vehicle.vrn}</div>
                </td>
                <td className="px-5 py-3">
                  <div className="flex items-center gap-2">
                    <Avatar name={h.customer.fullName} size="sm" />
                    <span>{h.customer.fullName}</span>
                  </div>
                </td>
                <td className="px-5 py-3 text-ink-muted tabular-nums">
                  {formatDate(h.startDate)} → {formatDate(h.endDate)}
                </td>
                <td className="px-5 py-3 tabular-nums">{gbp(h.totalGbp)}</td>
                <td className="px-5 py-3 text-right pr-5">
                  <Badge tone="active">Active</Badge>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
