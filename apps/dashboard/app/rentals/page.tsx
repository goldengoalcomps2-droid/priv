import Link from "next/link";
import { Plus } from "lucide-react";
import { rentalsList } from "@/lib/queries";
import { PageHeader } from "@/components/ui/page-header";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { StatCard } from "@/components/ui/stat-card";
import { Badge, type BadgeTone } from "@/components/ui/badge";
import { Avatar } from "@/components/ui/avatar";
import { gbp, formatDate, cn } from "@/lib/utils";
import { HireStatus, prisma } from "@fleetpro/db";

export const dynamic = "force-dynamic";

const STATUS_TONE: Record<HireStatus, BadgeTone> = {
  DRAFT: "muted",
  AWAITING_SIGNATURE: "warn",
  ACTIVE: "active",
  COMPLETED: "ok",
  CANCELLED: "muted",
};

const STATUS_LABEL: Record<HireStatus, string> = {
  DRAFT: "Draft",
  AWAITING_SIGNATURE: "Awaiting signature",
  ACTIVE: "Active",
  COMPLETED: "Completed",
  CANCELLED: "Cancelled",
};

const FILTERS = [
  { id: "ALL", label: "All" },
  { id: "ACTIVE", label: "Active" },
  { id: "AWAITING_SIGNATURE", label: "Awaiting" },
  { id: "COMPLETED", label: "Completed" },
] as const;

export default async function RentalsPage({
  searchParams,
}: {
  searchParams: Promise<{ status?: string }>;
}) {
  const params = await searchParams;
  const status = (params.status ?? "ALL") as (typeof FILTERS)[number]["id"];

  const [rentals, totals] = await Promise.all([
    rentalsList({ status: status === "ALL" ? "ALL" : (status as HireStatus) }),
    Promise.all([
      prisma.hire.count({ where: { status: HireStatus.ACTIVE } }),
      prisma.hire.count({ where: { status: HireStatus.AWAITING_SIGNATURE } }),
      prisma.hire.count({ where: { status: HireStatus.COMPLETED } }),
      prisma.hire.aggregate({ _sum: { totalGbp: true }, where: { status: { in: [HireStatus.ACTIVE, HireStatus.COMPLETED] } } }),
    ]),
  ]);
  const [active, awaiting, completed, revAgg] = totals;

  return (
    <>
      <PageHeader
        title="Rentals"
        subtitle="Active, upcoming, and historic hires"
        right={
          <Link
            href="/?new=1"
            className="inline-flex items-center gap-2 rounded-md bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-brand-hover"
          >
            <Plus className="h-4 w-4" aria-hidden /> New Rental
          </Link>
        }
      />

      <section aria-label="Rentals summary" className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        <StatCard label="Active" value={active} hintTone="ok" />
        <StatCard label="Awaiting signature" value={awaiting} hintTone="warn" />
        <StatCard label="Completed (lifetime)" value={completed} />
        <StatCard label="Lifetime revenue" value={gbp(revAgg._sum.totalGbp ?? 0)} />
      </section>

      <Card className="mt-8">
        <CardHeader>
          <CardTitle>Rentals</CardTitle>
          <div className="flex items-center gap-1" role="tablist" aria-label="Filter rentals by status">
            {FILTERS.map((f) => (
              <Link
                key={f.id}
                href={{ pathname: "/rentals", query: { status: f.id } }}
                role="tab"
                aria-selected={f.id === status}
                className={cn(
                  "rounded-md px-3 py-1.5 text-sm border",
                  f.id === status ? "border-rule bg-card text-ink shadow-sm" : "border-transparent text-ink-muted hover:text-ink",
                )}
              >
                {f.label}
              </Link>
            ))}
          </div>
        </CardHeader>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-page/40">
              <tr className="text-[11px] uppercase tracking-wider text-ink-muted text-left">
                <th scope="col" className="px-5 py-2 font-semibold">Vehicle</th>
                <th scope="col" className="px-5 py-2 font-semibold">Customer</th>
                <th scope="col" className="px-5 py-2 font-semibold">Period</th>
                <th scope="col" className="px-5 py-2 font-semibold">Total</th>
                <th scope="col" className="px-5 py-2 font-semibold">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-rule">
              {rentals.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-5 py-8 text-center text-sm text-ink-muted">No rentals found.</td>
                </tr>
              )}
              {rentals.map((h) => (
                <tr key={h.id} className="hover:bg-page/40">
                  <td className="px-5 py-3">
                    <div className="font-medium">{h.vehicle.make} {h.vehicle.model} {h.vehicle.trim ?? ""}</div>
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
                  <td className="px-5 py-3">
                    <Badge tone={STATUS_TONE[h.status]}>{STATUS_LABEL[h.status]}</Badge>
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
