import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { recentAgentActivity } from "@/lib/queries";

type Activity = Awaited<ReturnType<typeof recentAgentActivity>>[number];

const AGENT_LABEL: Record<Activity["agent"], string> = {
  CUSTOMER_ONBOARDING: "Onboarding",
  HIRE_AND_AGREEMENT: "Hire",
  FINES_AND_PCN: "Fines/PCN",
  FLEET_MAINTENANCE: "Maintenance",
  PROCUREMENT: "Procurement",
  ANALYTICS_AND_DEFLEET: "Analytics",
};

const KIND_TONE: Record<Activity["kind"], "muted" | "ok" | "warn" | "bad" | "brand" | "active"> = {
  TOOL_CALL: "muted",
  DECISION: "active",
  NOTIFICATION: "muted",
  ERROR: "bad",
  APPROVAL_REQUEST: "warn",
  APPROVAL_RESOLUTION: "ok",
};

export function AgentActivityCard({ items }: { items: Activity[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Agent activity</CardTitle>
      </CardHeader>
      <ul className="divide-y divide-rule" aria-label="Recent agent activity">
        {items.length === 0 && <li className="px-5 py-6 text-sm text-ink-muted text-center">No recent activity.</li>}
        {items.map((a) => (
          <li key={a.id} className="px-5 py-3">
            <div className="flex items-center gap-2 text-xs">
              <Badge tone={KIND_TONE[a.kind]}>{AGENT_LABEL[a.agent]}</Badge>
              <time dateTime={a.occurredAt.toISOString()} className="text-ink-subtle tabular-nums">
                {a.occurredAt.toLocaleString("en-GB", { hour: "2-digit", minute: "2-digit", day: "2-digit", month: "short" })}
              </time>
            </div>
            <div className="mt-1 text-sm text-ink">{a.summary}</div>
            {a.toolName && <div className="text-xs text-ink-muted mt-0.5 font-mono">{a.toolName}</div>}
          </li>
        ))}
      </ul>
    </Card>
  );
}
