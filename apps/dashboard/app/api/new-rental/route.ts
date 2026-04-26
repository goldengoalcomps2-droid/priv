import { NextResponse } from "next/server";
import { z } from "zod";
import { prisma, ApprovalKind, AgentName, ActivityKind, ApprovalStatus, HireStatus } from "@fleetpro/db";

const Body = z.object({
  customerId: z.string().min(1),
  vehicleId: z.string().min(1),
  startDate: z.string().min(1),
  endDate: z.string().min(1),
});

export async function POST(req: Request) {
  const body = await req.json().catch(() => null);
  const parsed = Body.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json({ error: parsed.error.flatten() }, { status: 400 });
  }
  const { customerId, vehicleId, startDate, endDate } = parsed.data;

  const start = new Date(startDate);
  const end = new Date(endDate);
  if (end <= start) return NextResponse.json({ error: "End must be after start" }, { status: 400 });

  // 1. Collision check (same logic the Hire & Agreement agent uses)
  const collisions = await prisma.hire.findMany({
    where: {
      vehicleId,
      status: { in: [HireStatus.ACTIVE, HireStatus.AWAITING_SIGNATURE, HireStatus.DRAFT] },
      AND: [{ startDate: { lte: end } }, { endDate: { gte: start } }],
    },
    select: { id: true, startDate: true, endDate: true },
  });
  if (collisions.length > 0) {
    return NextResponse.json({ error: "Collision detected", collisions }, { status: 409 });
  }

  const vehicle = await prisma.vehicle.findUniqueOrThrow({ where: { id: vehicleId } });
  const weeks = Math.max(1, Math.ceil((end.getTime() - start.getTime()) / (7 * 86_400_000)));
  const weeklyRate = Math.floor(vehicle.monthlyRateGbp / 4);

  // 2. Persist DRAFT hire
  const hire = await prisma.hire.create({
    data: {
      customerId,
      vehicleId,
      startDate: start,
      endDate: end,
      weeklyRateGbp: weeklyRate,
      totalGbp: weeklyRate * weeks,
      status: HireStatus.AWAITING_SIGNATURE,
    },
  });

  // 3. Queue approval — sending the agreement is the human-in-the-loop gate
  const approval = await prisma.approval.create({
    data: {
      agent: AgentName.HIRE_AND_AGREEMENT,
      kind: ApprovalKind.SEND_HIRE_AGREEMENT,
      title: `Send hire agreement for signature`,
      proposedAction: { tool: "adobeSign.sendForSignature", args: { hireId: hire.id } },
      rationale: "New rental wizard: customer + vehicle + dates approved by operator. Awaiting send-for-signature confirmation.",
      hireId: hire.id,
      customerId,
      vehicleId,
      status: ApprovalStatus.PENDING,
    },
  });

  // 4. Audit log
  await prisma.agentActivity.create({
    data: {
      agent: AgentName.HIRE_AND_AGREEMENT,
      kind: ActivityKind.APPROVAL_REQUEST,
      summary: `New rental drafted via wizard; queued for signature approval`,
      toolName: "newRental.queue",
      toolInput: { customerId, vehicleId, startDate, endDate },
      hireId: hire.id,
      customerId,
      vehicleId,
    },
  });

  return NextResponse.json({ hireId: hire.id, approvalId: approval.id });
}
