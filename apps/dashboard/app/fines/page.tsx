import { Camera } from "lucide-react";
import { finesList, finesSummary } from "@/lib/queries";
import { PageHeader } from "@/components/ui/page-header";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { StatCard } from "@/components/ui/stat-card";
import { Badge, type BadgeTone } from "@/components/ui/badge";
import { gbp, formatDate } from "@/lib/utils";
import type { FineStatus } from "@fleetpro/db";

export const dynamic = "force-dynamic";

const STATUS_TONE: Record<FineStatus, BadgeTone> = {
  RECEIVED: "warn",
  MATCHED: "warn",
  CHARGED_TO_CUSTOMER: "active",
  CHALLENGE_PREPARED: "warn",
  CHALLENGE_SUBMITTED: "active",
  RESOLVED: "ok",
  WRITTEN_OFF: "muted",
};

const STATUS_LABEL: Record<FineStatus, string> = {
  RECEIVED: "Pending",
  MATCHED: "Pending",
  CHARGED_TO_CUSTOMER: "Charged",
  CHALLENGE_PREPARED: "Challenge ready",
  CHALLENGE_SUBMITTED: "Submitted",
  RESOLVED: "Resolved",
  WRITTEN_OFF: "Written off",
};

export default async function FinesPage() {
  const [summary, fines] = await Promise.all([finesSummary(), finesList()]);

  return (
    <>
      <PageHeader title="Fines" subtitle="Parking fines and penalty charges" />

      <section aria-label="Fines summary" className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        <StatCard
          label="Outstanding"
          value={<span className="text-bad">{gbp(summary.outstandingGbpPence)}</span>}
          hint={`${summary.outstandingCount} fines unpaid`}
          hintTone="bad"
        />
        <StatCard
          label="Collected"
          value={<span className="text-ink-muted">{gbp(summary.collectedGbpPence)}</span>}
          hint={`${summary.collectedCount} fines paid`}
        />
        <StatCard label="Disputed" value={summary.disputedCount} hint="under review" />
        <StatCard
          label="This month"
          value={gbp(summary.thisMonthGbpPence)}
          hint={`${summary.thisMonthCount} fines · top: ${summary.topLocation}`}
        />
      </section>

      <Card className="mt-8">
        <CardHeader>
          <CardTitle>
            <span className="inline-flex items-center gap-2">
              <Camera className="h-4 w-4 text-brand" aria-hidden /> Upload PCN photo
            </span>
          </CardTitle>
        </CardHeader>
        <div className="px-5 pb-5">
          <p className="text-sm text-ink-muted">
            Upload a photo of the parking fine — the vehicle and customer will be matched automatically.
          </p>
          <label
            htmlFor="pcn-upload"
            className="mt-4 grid place-items-center text-center rounded-xl border-2 border-dashed border-rule bg-page/40 px-6 py-12 cursor-pointer hover:border-brand hover:bg-brand-soft/40 focus-within:outline-2 focus-within:outline-brand"
          >
            <Camera className="h-8 w-8 text-ink-subtle" aria-hidden />
            <div className="mt-2 text-sm font-medium">Click to upload PCN photo</div>
            <div className="mt-1 text-xs text-ink-muted">
              PNG or JPG · we'll extract date, time, VRN, amount and match to a rental
            </div>
            <input id="pcn-upload" type="file" accept="image/*" capture="environment" className="sr-only" />
          </label>
        </div>
      </Card>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>All fines ({fines.length})</CardTitle>
        </CardHeader>
        <p className="px-5 pt-1 pb-3 text-xs text-ink-muted">Tap any row to view or update the fine. Click-through opens the detail modal.</p>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-page/40">
              <tr className="text-[11px] uppercase tracking-wider text-ink-muted text-left">
                <th scope="col" className="px-5 py-2 font-semibold">Date</th>
                <th scope="col" className="px-5 py-2 font-semibold">Vehicle</th>
                <th scope="col" className="px-5 py-2 font-semibold">Customer</th>
                <th scope="col" className="px-5 py-2 font-semibold">Authority</th>
                <th scope="col" className="px-5 py-2 font-semibold">Reference</th>
                <th scope="col" className="px-5 py-2 font-semibold">Fine</th>
                <th scope="col" className="px-5 py-2 font-semibold">Total</th>
                <th scope="col" className="px-5 py-2 font-semibold">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-rule">
              {fines.length === 0 && (
                <tr>
                  <td colSpan={8} className="px-5 py-8 text-center text-sm text-ink-muted">
                    No fines on record.
                  </td>
                </tr>
              )}
              {fines.map((f) => (
                <tr key={f.id} className="hover:bg-page/40">
                  <td className="px-5 py-3 tabular-nums">
                    <div>{formatDate(f.offenceAt)}</div>
                    <div className="text-xs text-ink-muted">
                      {new Date(f.offenceAt).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" })}
                    </div>
                  </td>
                  <td className="px-5 py-3">
                    <div className="font-medium">{f.vehicle ? `${f.vehicle.make} ${f.vehicle.model} ${f.vehicle.trim ?? ""}` : "—"}</div>
                    <div className="text-xs text-ink-muted tabular-nums">{f.vrn}</div>
                  </td>
                  <td className="px-5 py-3">{f.customer?.fullName ?? <span className="text-ink-muted">—</span>}</td>
                  <td className="px-5 py-3">{f.issuingAuthority}</td>
                  <td className="px-5 py-3 font-mono text-xs">{f.pcnNumber}</td>
                  <td className="px-5 py-3 tabular-nums">{gbp(f.amountGbp)}</td>
                  <td className="px-5 py-3 tabular-nums font-medium">{gbp(f.amountGbp + f.adminFeeGbp)}</td>
                  <td className="px-5 py-3">
                    <Badge tone={STATUS_TONE[f.status]}>{STATUS_LABEL[f.status]}</Badge>
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
