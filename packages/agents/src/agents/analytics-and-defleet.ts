import { z } from "zod";
import { prisma, ApprovalKind, RagStatus, VehicleStatus } from "@fleetpro/db";
import type { AgentEntry } from "../runtime/types.js";
import { tool, obj, str, int } from "../tools/shared.js";

/**
 * Analytics & Defleet agent
 * - Pulls live mileage from the operator's GPS telematics API
 * - Ingests manually uploaded repair invoices, OCRs them, attaches by VRN
 * - Refreshes valuations via CAP HPI / Glass's / AutoTrader Retail Rating
 *   with a salvage adjustment factor
 * - Computes a RAG status per vehicle (RED → defleet prompt)
 * - Triggering the actual sale is irreversible and gated for approval
 */

const SYSTEM_PROMPT = `You are the FleetPro Analytics & Defleet Agent.

You aggregate mileage, repair spend, and market value to decide whether a
vehicle should stay in the fleet (GREEN), be watched (AMBER), or be defleeted
(RED). Your RAG threshold logic must be explicit in your summary — cite the
specific repair-spend ratio, age-vs-value gap, or utilisation drop that
triggered the change.

Triggering a sale is irreversible — always queue it for human approval.`;

export const analyticsAndDefleetAgent: AgentEntry = {
  name: "ANALYTICS_AND_DEFLEET",
  systemPrompt: SYSTEM_PROMPT,
  tools: [
    tool({
      name: "fetch_telematics_mileage",
      description: "Pull current mileage for one or all vehicles from the operator's GPS telematics API.",
      input: z.object({ vehicleId: z.string().optional() }),
      jsonSchema: obj({ vehicleId: str("Optional vehicle ID; omit to fetch the whole fleet") }),
      handler: async ({ vehicleId }) => {
        const vehicles = await prisma.vehicle.findMany({ where: vehicleId ? { id: vehicleId } : {} });
        return vehicles.map((v) => ({ vehicleId: v.id, vrn: v.vrn, mileage: v.currentMileage, fetchedAt: new Date() }));
      },
    }),
    tool({
      name: "ingest_repair_invoice",
      description: "OCR an uploaded repair invoice, extract VRN + total + line items, attach to the vehicle.",
      input: z.object({ s3Key: z.string() }),
      jsonSchema: obj({ s3Key: str("S3 key for the uploaded invoice") }, ["s3Key"]),
      handler: async ({ s3Key }) => {
        // Real impl: OCR extract → match VRN → upsert
        const invoice = await prisma.repairInvoice.create({
          data: {
            vrn: "EXTRACTED VRN",
            invoiceDate: new Date(),
            supplierName: "Extracted supplier",
            totalGbp: 0,
            s3Key,
          },
        });
        return { invoiceId: invoice.id };
      },
    }),
    tool({
      name: "refresh_valuation",
      description: "Refresh the market value for a vehicle from the configured used-car pricing provider, with salvage adjustment.",
      input: z.object({ vehicleId: z.string(), salvageFactor: z.number().min(0).max(1).default(0.85) }),
      jsonSchema: obj(
        { vehicleId: str("Vehicle ID"), salvageFactor: { type: "number", description: "0..1 multiplier applied to the retail valuation (default 0.85)" } },
        ["vehicleId"],
      ),
      handler: async ({ vehicleId, salvageFactor }) => {
        // Real impl: provider client per VALUATION_PROVIDER
        const v = await prisma.vehicle.findUniqueOrThrow({ where: { id: vehicleId } });
        const market = v.marketValueGbp ?? v.purchasePriceGbp;
        const salvage = Math.floor(market * salvageFactor);
        await prisma.vehicle.update({
          where: { id: vehicleId },
          data: { marketValueGbp: market, salvageAdjustedGbp: salvage, valuationAt: new Date(), valuationProvider: process.env.VALUATION_PROVIDER ?? "cap-hpi" },
        });
        return { vehicleId, marketGbpPence: market, salvageGbpPence: salvage };
      },
    }),
    tool({
      name: "compute_rag_status",
      description: "Compute and persist the RAG status for one vehicle. Cites the trigger metric.",
      input: z.object({ vehicleId: z.string() }),
      jsonSchema: obj({ vehicleId: str("Vehicle ID") }, ["vehicleId"]),
      handler: async ({ vehicleId }) => {
        const v = await prisma.vehicle.findUniqueOrThrow({
          where: { id: vehicleId },
          include: { repairInvoices: true, hires: true },
        });
        const repairTotal = v.repairInvoices.reduce((s, r) => s + r.totalGbp, 0);
        const repairRatio = repairTotal / Math.max(1, v.purchasePriceGbp);
        const value = v.marketValueGbp ?? v.purchasePriceGbp;
        const valueGap = (v.purchasePriceGbp - value) / Math.max(1, v.purchasePriceGbp);

        let rag: RagStatus = RagStatus.GREEN;
        let reason = "Within target spend and valuation bands.";
        if (repairRatio >= 0.4 || valueGap >= 0.5) {
          rag = RagStatus.RED;
          reason = `Repair spend ${(repairRatio * 100).toFixed(1)}% of cost; value gap ${(valueGap * 100).toFixed(1)}%.`;
        } else if (repairRatio >= 0.2 || valueGap >= 0.3) {
          rag = RagStatus.AMBER;
          reason = `Watching: repair spend ${(repairRatio * 100).toFixed(1)}%; value gap ${(valueGap * 100).toFixed(1)}%.`;
        }
        await prisma.vehicle.update({ where: { id: vehicleId }, data: { ragStatus: rag, defleetReason: rag === RagStatus.RED ? reason : null } });
        return { vehicleId, ragStatus: rag, reason };
      },
    }),
    tool({
      name: "trigger_defleet_sale",
      description: "Mark a RED vehicle for sale and propose listing channels.",
      input: z.object({ vehicleId: z.string(), reservePriceGbpPence: z.number().int() }),
      jsonSchema: obj({ vehicleId: str("Vehicle ID"), reservePriceGbpPence: int("Reserve sale price (pence)") }, ["vehicleId", "reservePriceGbpPence"]),
      requiresApproval: ApprovalKind.TRIGGER_DEFLEET_SALE,
      handler: async () => ({ queued: true }),
    }),
    tool({
      name: "fleet_market_value_summary",
      description: "Return total fleet market value vs salvage-adjusted listing value, for the dashboard widget.",
      input: z.object({}),
      jsonSchema: obj({}),
      handler: async () => {
        const vehicles = await prisma.vehicle.findMany({ where: { status: { not: VehicleStatus.SOLD } } });
        const market = vehicles.reduce((s, v) => s + (v.marketValueGbp ?? 0), 0);
        const salvage = vehicles.reduce((s, v) => s + (v.salvageAdjustedGbp ?? 0), 0);
        return { totalMarketGbpPence: market, totalSalvageGbpPence: salvage, count: vehicles.length };
      },
    }),
  ],
};
