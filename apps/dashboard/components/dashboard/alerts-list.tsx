import { AlertTriangle } from "lucide-react";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { formatDate, daysUntil } from "@/lib/utils";
import type { alertsList } from "@/lib/queries";

type Alert = Awaited<ReturnType<typeof alertsList>>[number];

export function AlertsCard({ alerts }: { alerts: Alert[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Alerts</CardTitle>
      </CardHeader>
      <ul className="divide-y divide-rule" aria-label="Vehicle alerts">
        {alerts.length === 0 && <li className="px-5 py-6 text-sm text-ink-muted text-center">No alerts.</li>}
        {alerts.map((a) => {
          const expired = a.kind === "MOT_EXPIRED";
          const tone = expired ? "bg-bad-soft text-bad" : "bg-warn-soft text-warn";
          const due = a.motDue ? daysUntil(a.motDue) : null;
          const headline = expired
            ? `MOT EXPIRED — ${a.make} ${a.model} ${a.trim ?? ""} (${a.vrn})`
            : `MOT due in ${due} days — ${a.make} ${a.model} ${a.trim ?? ""} (${a.vrn})`;
          return (
            <li key={`${a.kind}-${a.id}`} className={`px-5 py-3 flex items-start gap-3 ${tone}`}>
              <AlertTriangle className="h-4 w-4 mt-0.5 shrink-0" aria-hidden />
              <div className="text-sm">
                <div className="font-medium leading-snug">{headline}</div>
                <div className="text-xs opacity-80 tabular-nums mt-0.5">{formatDate(a.motDue)}</div>
              </div>
            </li>
          );
        })}
      </ul>
    </Card>
  );
}
