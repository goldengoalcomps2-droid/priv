import { z } from "zod";
import { prisma, ApprovalKind, FineStatus, HireStatus } from "@fleetpro/db";
import type { AgentEntry } from "../runtime/types.js";
import { tool, obj, str, int } from "../tools/shared.js";

/**
 * Fines & PCN agent
 * - OCRs an uploaded PCN photo (mobile camera capture)
 * - Matches the offence datetime + VRN to an active hire → liable customer
 * - Generates a Transfer-of-Liability pack (hire agreement + customer details + statement)
 * - Pre-stages the council's PCN challenge URL with the pack attached;
 *   actually clicking Send is HUMAN-IN-THE-LOOP (queued for approval)
 */

const SYSTEM_PROMPT = `You are the FleetPro Fines & PCN Agent.

Workflow: OCR the PCN → match to vehicle and active hire at the offence datetime
→ identify the liable customer → produce an admin-fee invoice and a Transfer
of Liability (ToL) pack. Submitting the PCN challenge to the issuing council
is irreversible and customer-facing — always queue it for operator approval.

Cite the matching hire ID and exact offence datetime in your summary.`;

export const finesAndPcnAgent: AgentEntry = {
  name: "FINES_AND_PCN",
  systemPrompt: SYSTEM_PROMPT,
  tools: [
    tool({
      name: "ocr_pcn_notice",
      description: "Run OCR on an uploaded PCN photo. Extracts authority, PCN number, VRN, datetime, location, amount.",
      input: z.object({ s3Key: z.string() }),
      jsonSchema: obj({ s3Key: str("S3 key for the PCN notice photo") }, ["s3Key"]),
      handler: async () => ({
        issuingAuthority: "EXTRACTED AUTHORITY",
        pcnNumber: "PCN0000000",
        vrn: "AB12 CDE",
        offenceAt: new Date().toISOString(),
        location: "EXTRACTED LOCATION",
        amountGbpPence: 13_000,
      }),
    }),
    tool({
      name: "match_fine_to_hire",
      description: "Find the active hire on the given VRN at the given datetime; resolve to a customer.",
      input: z.object({ vrn: z.string(), offenceAt: z.string() }),
      jsonSchema: obj({ vrn: str("Vehicle VRN"), offenceAt: str("ISO datetime of the offence") }, ["vrn", "offenceAt"]),
      handler: async ({ vrn, offenceAt }) => {
        const t = new Date(offenceAt);
        const hire = await prisma.hire.findFirst({
          where: {
            vehicle: { vrn },
            status: { in: [HireStatus.ACTIVE, HireStatus.COMPLETED] },
            startDate: { lte: t },
            endDate: { gte: t },
          },
          include: { vehicle: { select: { id: true } }, customer: { select: { id: true, fullName: true } } },
        });
        if (!hire) return { matched: false };
        return {
          matched: true,
          hireId: hire.id,
          vehicleId: hire.vehicle.id,
          customerId: hire.customer.id,
          customerName: hire.customer.fullName,
        };
      },
    }),
    tool({
      name: "create_fine_record",
      description: "Persist the Fine row, link it to vehicle/hire/customer, and apply the admin fee from T&Cs.",
      input: z.object({
        pcnNumber: z.string(),
        issuingAuthority: z.string(),
        vrn: z.string(),
        vehicleId: z.string(),
        hireId: z.string().optional(),
        customerId: z.string().optional(),
        offenceAt: z.string(),
        location: z.string(),
        amountGbpPence: z.number().int(),
        adminFeeGbpPence: z.number().int().default(2500),
        s3Key: z.string(),
      }),
      jsonSchema: obj(
        {
          pcnNumber: str("Unique PCN number"),
          issuingAuthority: str("Issuing council / TfL"),
          vrn: str("Vehicle VRN"),
          vehicleId: str("Vehicle ID"),
          hireId: str("Matched hire ID"),
          customerId: str("Liable customer ID"),
          offenceAt: str("ISO offence datetime"),
          location: str("Offence location"),
          amountGbpPence: int("PCN amount in pence"),
          adminFeeGbpPence: int("Admin fee in pence"),
          s3Key: str("S3 key for the original notice photo"),
        },
        ["pcnNumber", "issuingAuthority", "vrn", "vehicleId", "offenceAt", "location", "amountGbpPence", "s3Key"],
      ),
      handler: async (i) => {
        const fine = await prisma.fine.create({
          data: {
            pcnNumber: i.pcnNumber,
            issuingAuthority: i.issuingAuthority,
            vrn: i.vrn,
            vehicleId: i.vehicleId,
            hireId: i.hireId,
            customerId: i.customerId,
            offenceAt: new Date(i.offenceAt),
            location: i.location,
            amountGbp: i.amountGbpPence,
            adminFeeGbp: i.adminFeeGbpPence,
            status: i.hireId ? FineStatus.MATCHED : FineStatus.RECEIVED,
            noticePhotoS3Key: i.s3Key,
          },
        });
        return { fineId: fine.id };
      },
    }),
    tool({
      name: "build_transfer_of_liability_pack",
      description: "Assemble the ToL pack PDF (hire agreement + customer details + statement) and store it.",
      input: z.object({ fineId: z.string() }),
      jsonSchema: obj({ fineId: str("Fine ID") }, ["fineId"]),
      handler: async ({ fineId }) => {
        const s3Key = `pcn-tol-packs/${fineId}.pdf`;
        await prisma.fine.update({ where: { id: fineId }, data: { challengePackS3Key: s3Key } });
        await prisma.document.create({
          data: { kind: "TRANSFER_OF_LIABILITY_PACK", title: `ToL pack ${fineId}`, s3Key, mimeType: "application/pdf" },
        });
        return { s3Key };
      },
    }),
    tool({
      name: "charge_customer_admin_fee",
      description: "Raise an admin-fee charge on the customer's account and email them.",
      input: z.object({ fineId: z.string() }),
      jsonSchema: obj({ fineId: str("Fine ID") }, ["fineId"]),
      requiresApproval: ApprovalKind.CHARGE_CUSTOMER_FOR_FINE,
      handler: async () => ({ queued: true }),
    }),
    tool({
      name: "submit_pcn_challenge",
      description: "Open the council's challenge URL pre-staged with the ToL pack and notify the operator to click Send.",
      input: z.object({ fineId: z.string(), challengeUrl: z.string().url() }),
      jsonSchema: obj({ fineId: str("Fine ID"), challengeUrl: str("Issuing authority's challenge URL") }, ["fineId", "challengeUrl"]),
      requiresApproval: ApprovalKind.SUBMIT_PCN_CHALLENGE,
      handler: async () => ({ queued: true }),
    }),
  ],
};
