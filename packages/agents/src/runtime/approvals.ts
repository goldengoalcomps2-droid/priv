import { prisma, ActivityKind, ApprovalStatus } from "@fleetpro/db";

/**
 * Resolve a pending approval. Called from the dashboard's approval queue UI
 * when an operator clicks Approve or Reject.
 *
 * On approve: caller is expected to actually execute the proposed action
 * (this function only flips state + writes audit). The dashboard wires this
 * to the same tool handlers used in direct execution.
 */
export async function resolveApproval(opts: {
  approvalId: string;
  reviewerId: string;
  decision: "APPROVED" | "REJECTED";
  note?: string;
}) {
  const { approvalId, reviewerId, decision, note } = opts;
  const approval = await prisma.approval.findUniqueOrThrow({ where: { id: approvalId } });
  if (approval.status !== ApprovalStatus.PENDING) {
    throw new Error(`Approval ${approvalId} is already ${approval.status}`);
  }

  const updated = await prisma.approval.update({
    where: { id: approvalId },
    data: {
      status: decision === "APPROVED" ? ApprovalStatus.APPROVED : ApprovalStatus.REJECTED,
      reviewerId,
      reviewerNote: note,
      resolvedAt: new Date(),
    },
  });

  await prisma.agentActivity.create({
    data: {
      agent: approval.agent,
      kind: ActivityKind.APPROVAL_RESOLUTION,
      summary: `Approval ${decision.toLowerCase()} by operator`,
      toolName: (approval.proposedAction as { tool: string }).tool,
      toolInput: approval.proposedAction as object,
      actorUserId: reviewerId,
      customerId: approval.customerId,
      vehicleId: approval.vehicleId,
      hireId: approval.hireId,
      fineId: approval.fineId,
    },
  });

  return updated;
}
