import { z } from "zod";
import { prisma, ApprovalKind, HireStatus } from "@fleetpro/db";
import type { AgentEntry } from "../runtime/types.js";
import { tool, obj, str, int } from "../tools/shared.js";

/**
 * Hire & Agreement agent
 * - Handles "New Rental" flow with existing-customer dropdown (no re-upload)
 * - Detects timeline collisions when an operator drag-edits a hire on the Gantt
 * - Generates a hire agreement PDF, sends via Adobe Acrobat Sign
 * - Listens for the signed webhook + stores the signed PDF in the doc vault
 */

const SYSTEM_PROMPT = `You are the FleetPro Hire & Agreement Agent.

When the operator drags a hire on the Gantt timeline or creates a new rental,
you check for collisions with other hires on the same vehicle and propose
non-overlapping alternatives. Generating the agreement PDF is automatic, but
SENDING the agreement for signature is an irreversible customer-facing action
and MUST be queued for human approval.

Always cite the conflicting hire IDs and dates when reporting a collision.`;

export const hireAndAgreementAgent: AgentEntry = {
  name: "HIRE_AND_AGREEMENT",
  systemPrompt: SYSTEM_PROMPT,
  tools: [
    tool({
      name: "list_existing_customers",
      description: "Search verified customers (no upload required). Used to populate the New Rental dropdown.",
      input: z.object({ query: z.string().optional() }),
      jsonSchema: obj({ query: str("Substring search across name, email, or postcode") }),
      handler: async ({ query }) => {
        const customers = await prisma.customer.findMany({
          where: {
            onboardingStatus: "VERIFIED",
            ...(query
              ? { OR: [{ fullName: { contains: query, mode: "insensitive" } }, { email: { contains: query, mode: "insensitive" } }, { postcode: { contains: query, mode: "insensitive" } }] }
              : {}),
          },
          take: 25,
          orderBy: { createdAt: "desc" },
        });
        return customers.map((c) => ({ id: c.id, fullName: c.fullName, email: c.email, postcode: c.postcode }));
      },
    }),
    tool({
      name: "check_hire_collision",
      description: "Given a vehicleId + start/end window, list any overlapping hires.",
      input: z.object({ vehicleId: z.string(), startDate: z.string(), endDate: z.string(), excludeHireId: z.string().optional() }),
      jsonSchema: obj(
        {
          vehicleId: str("Vehicle ID"),
          startDate: str("ISO start date"),
          endDate: str("ISO end date"),
          excludeHireId: str("Optional: hire ID to exclude (e.g. when editing an existing hire)"),
        },
        ["vehicleId", "startDate", "endDate"],
      ),
      handler: async ({ vehicleId, startDate, endDate, excludeHireId }) => {
        const start = new Date(startDate);
        const end = new Date(endDate);
        const collisions = await prisma.hire.findMany({
          where: {
            vehicleId,
            id: excludeHireId ? { not: excludeHireId } : undefined,
            status: { in: [HireStatus.ACTIVE, HireStatus.AWAITING_SIGNATURE, HireStatus.DRAFT] },
            AND: [{ startDate: { lte: end } }, { endDate: { gte: start } }],
          },
          select: { id: true, startDate: true, endDate: true, customerId: true },
        });
        return { collisionCount: collisions.length, collisions };
      },
    }),
    tool({
      name: "create_draft_hire",
      description: "Create a Hire row in DRAFT status. Does not send anything yet.",
      input: z.object({
        customerId: z.string(),
        vehicleId: z.string(),
        startDate: z.string(),
        endDate: z.string(),
        weeklyRateGbpPence: z.number().int(),
      }),
      jsonSchema: obj(
        {
          customerId: str("Customer ID"),
          vehicleId: str("Vehicle ID"),
          startDate: str("ISO start date"),
          endDate: str("ISO end date"),
          weeklyRateGbpPence: int("Weekly hire rate, in pence"),
        },
        ["customerId", "vehicleId", "startDate", "endDate", "weeklyRateGbpPence"],
      ),
      handler: async (i) => {
        const start = new Date(i.startDate);
        const end = new Date(i.endDate);
        const weeks = Math.max(1, Math.ceil((end.getTime() - start.getTime()) / (7 * 86_400_000)));
        const hire = await prisma.hire.create({
          data: {
            customerId: i.customerId,
            vehicleId: i.vehicleId,
            startDate: start,
            endDate: end,
            weeklyRateGbp: i.weeklyRateGbpPence,
            totalGbp: i.weeklyRateGbpPence * weeks,
            status: HireStatus.DRAFT,
          },
        });
        return { hireId: hire.id, totalGbpPence: hire.totalGbp };
      },
    }),
    tool({
      name: "generate_agreement_pdf",
      description: "Render the hire agreement PDF and store it in the document vault.",
      input: z.object({ hireId: z.string() }),
      jsonSchema: obj({ hireId: str("Hire ID to generate the agreement for") }, ["hireId"]),
      handler: async ({ hireId }) => {
        const s3Key = `agreements/draft/${hireId}.pdf`;
        await prisma.hire.update({ where: { id: hireId }, data: { agreementPdfS3Key: s3Key } });
        await prisma.document.create({
          data: { kind: "HIRE_AGREEMENT_DRAFT", title: `Hire agreement (draft) ${hireId}`, s3Key, mimeType: "application/pdf" },
        });
        return { s3Key };
      },
    }),
    tool({
      name: "send_for_signature",
      description: "Send the agreement to the customer via Adobe Acrobat Sign.",
      input: z.object({ hireId: z.string() }),
      jsonSchema: obj({ hireId: str("Hire ID") }, ["hireId"]),
      requiresApproval: ApprovalKind.SEND_HIRE_AGREEMENT,
      handler: async () => ({ queued: true }),
    }),
    tool({
      name: "search_signed_agreements",
      description: "Retrieve signed agreements by customer name, VRN, or date window.",
      input: z.object({ query: z.string().optional(), vrn: z.string().optional(), from: z.string().optional(), to: z.string().optional() }),
      jsonSchema: obj({
        query: str("Substring search on customer name"),
        vrn: str("Filter by vehicle VRN"),
        from: str("ISO start date"),
        to: str("ISO end date"),
      }),
      handler: async ({ query, vrn, from, to }) => {
        const hires = await prisma.hire.findMany({
          where: {
            status: { in: [HireStatus.ACTIVE, HireStatus.COMPLETED] },
            signedAt: { not: null, ...(from ? { gte: new Date(from) } : {}), ...(to ? { lte: new Date(to) } : {}) },
            ...(vrn ? { vehicle: { vrn } } : {}),
            ...(query ? { customer: { fullName: { contains: query, mode: "insensitive" } } } : {}),
          },
          include: { customer: { select: { fullName: true } }, vehicle: { select: { vrn: true } } },
          take: 25,
        });
        return hires.map((h) => ({ hireId: h.id, customer: h.customer.fullName, vrn: h.vehicle.vrn, signedAt: h.signedAt, s3Key: h.signedPdfS3Key }));
      },
    }),
  ],
};
