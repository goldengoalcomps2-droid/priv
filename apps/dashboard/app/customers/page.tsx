import { Plus } from "lucide-react";
import { customersList, customerSummary } from "@/lib/queries";
import { PageHeader } from "@/components/ui/page-header";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { StatCard } from "@/components/ui/stat-card";
import { Avatar } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { gbp } from "@/lib/utils";

export const dynamic = "force-dynamic";

export default async function CustomersPage() {
  const [summary, customers] = await Promise.all([customerSummary(), customersList()]);

  return (
    <>
      <PageHeader title="Customers" subtitle="Renter database, history and blacklist" />

      <section aria-label="Customer summary" className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        <StatCard label="Total customers" value={summary.total} />
        <StatCard label="Repeat (3+)" value={summary.repeat3} />
        <StatCard
          label="Blacklisted"
          value={<span className="text-bad">{summary.blacklisted}</span>}
        />
        <StatCard label="Lifetime value" value={gbp(summary.lifetimeGbpPence)} />
      </section>

      <Card className="mt-8">
        <CardHeader>
          <CardTitle>All customers</CardTitle>
          <button
            type="button"
            className="inline-flex items-center gap-2 rounded-md border border-rule bg-card px-3 py-1.5 text-sm font-medium hover:bg-page"
          >
            <Plus className="h-4 w-4" aria-hidden /> Add customer
          </button>
        </CardHeader>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-page/40">
              <tr className="text-[11px] uppercase tracking-wider text-ink-muted text-left">
                <th scope="col" className="px-5 py-2 font-semibold">Name</th>
                <th scope="col" className="px-5 py-2 font-semibold">Phone</th>
                <th scope="col" className="px-5 py-2 font-semibold">License</th>
                <th scope="col" className="px-5 py-2 font-semibold">Rentals</th>
                <th scope="col" className="px-5 py-2 font-semibold">Lifetime £</th>
                <th scope="col" className="px-5 py-2 font-semibold"><span className="sr-only">Actions</span></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-rule">
              {customers.map(({ customer: c, rentalCount, lifetimeGbpPence }) => (
                <tr
                  key={c.id}
                  className={c.blacklisted ? "bg-bad-soft/40 hover:bg-bad-soft/60" : "hover:bg-page/40"}
                >
                  <td className="px-5 py-3">
                    <div className="flex items-center gap-3">
                      <Avatar name={c.fullName} />
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{c.fullName}</span>
                          {c.blacklisted && <Badge tone="bad">Blacklisted</Badge>}
                        </div>
                        <div className="text-xs text-ink-muted">{c.email}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-5 py-3 tabular-nums">{c.phone}</td>
                  <td className="px-5 py-3 font-mono text-xs">{c.licenceNumber}</td>
                  <td className="px-5 py-3 tabular-nums">{rentalCount}</td>
                  <td className="px-5 py-3 tabular-nums">{gbp(lifetimeGbpPence)}</td>
                  <td className="px-5 py-3 text-right pr-5 whitespace-nowrap">
                    <button type="button" className="text-brand text-sm hover:underline">View</button>
                    <span className="mx-2 text-ink-subtle" aria-hidden>·</span>
                    <button type="button" className="text-bad text-sm hover:underline">
                      {c.blacklisted ? "Remove blacklist" : "Blacklist"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </>
  );
}
