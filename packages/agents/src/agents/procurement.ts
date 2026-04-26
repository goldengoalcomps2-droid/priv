import { z } from "zod";
import { prisma, ApprovalKind, ProcurementOutcome, ProcurementSource, DamageCategory } from "@fleetpro/db";
import type { AgentEntry } from "../runtime/types.js";
import { tool, obj, str, int } from "../tools/shared.js";

/**
 * Procurement agent
 * - Watches vendor feeds (Copart UK, IAA, eBay Motors, AutoTrader, Car & Classic, FB Marketplace)
 * - Matches each listing against the operator's configurable strategy
 * - Surfaces opportunities + a weekly "what's hot" market-trend digest
 * - Placing a bid is irreversible and gated behind operator approval
 */

const SYSTEM_PROMPT = `You are the FleetPro Procurement Agent.

You monitor Copart UK, IAA, eBay Motors, AutoTrader, Car & Classic, and
Facebook Marketplace (where allowed by the platform's API or scraping policy).
For each new listing, you score it against the active procurement strategy
and surface the best-matching opportunities to the operator.

Placing a bid is IRREVERSIBLE — always queue it for human approval, even when
the listing scores 100%. Your weekly digest summarises trends, not actions.`;

export const procurementAgent: AgentEntry = {
  name: "PROCUREMENT",
  systemPrompt: SYSTEM_PROMPT,
  tools: [
    tool({
      name: "fetch_active_strategy",
      description: "Return the operator's active procurement strategy (make/model preferences, max bid, damage tolerance).",
      input: z.object({}),
      jsonSchema: obj({}),
      handler: async () => prisma.procurementStrategy.findFirst({ where: { active: true } }),
    }),
    tool({
      name: "scan_vendor_feed",
      description: "Pull new listings from one vendor since the last scan. Returns raw listings.",
      input: z.object({ source: z.nativeEnum(ProcurementSource) }),
      jsonSchema: obj(
        { source: { type: "string", enum: Object.values(ProcurementSource), description: "Which vendor feed to scan" } },
        ["source"],
      ),
      handler: async ({ source }) => ({ source, listings: [] as unknown[] }),
    }),
    tool({
      name: "score_listing_against_strategy",
      description: "Score a listing 0..1 vs the active strategy and produce a one-paragraph rationale.",
      input: z.object({
        make: z.string(),
        model: z.string(),
        yearOfManufacture: z.number().int().optional(),
        mileage: z.number().int().optional(),
        damageCategory: z.nativeEnum(DamageCategory).optional(),
        askingPriceGbpPence: z.number().int().optional(),
      }),
      jsonSchema: obj(
        {
          make: str("Make"),
          model: str("Model"),
          yearOfManufacture: int("Year of manufacture"),
          mileage: int("Mileage in miles"),
          damageCategory: { type: "string", enum: Object.values(DamageCategory), description: "Insurance damage category" },
          askingPriceGbpPence: int("Asking price in pence"),
        },
        ["make", "model"],
      ),
      handler: async (i) => {
        const strategy = await prisma.procurementStrategy.findFirst({ where: { active: true } });
        if (!strategy) return { score: 0, rationale: "No active strategy configured." };
        let score = 0.5;
        if (strategy.makes.length === 0 || strategy.makes.includes(i.make)) score += 0.2;
        if (strategy.minYear && i.yearOfManufacture && i.yearOfManufacture >= strategy.minYear) score += 0.1;
        if (strategy.maxMileage && i.mileage && i.mileage <= strategy.maxMileage) score += 0.1;
        if (i.damageCategory && strategy.damageCategories.includes(i.damageCategory)) score += 0.1;
        return { score: Math.min(1, score), rationale: `Match against strategy "${strategy.name}".` };
      },
    }),
    tool({
      name: "create_opportunity",
      description: "Persist a scored listing as a ProcurementOpportunity with the rationale.",
      input: z.object({
        source: z.nativeEnum(ProcurementSource),
        externalListingId: z.string(),
        url: z.string().url(),
        make: z.string(),
        model: z.string(),
        yearOfManufacture: z.number().int().optional(),
        mileage: z.number().int().optional(),
        damageCategory: z.nativeEnum(DamageCategory).default(DamageCategory.UNRECORDED),
        askingPriceGbpPence: z.number().int().optional(),
        recommendedBidGbpPence: z.number().int().optional(),
        matchScore: z.number(),
        rationale: z.string(),
      }),
      jsonSchema: obj(
        {
          source: { type: "string", enum: Object.values(ProcurementSource) },
          externalListingId: str("Vendor's listing ID"),
          url: str("Listing URL"),
          make: str("Make"),
          model: str("Model"),
          yearOfManufacture: int("Year"),
          mileage: int("Mileage"),
          damageCategory: { type: "string", enum: Object.values(DamageCategory) },
          askingPriceGbpPence: int("Asking price (pence)"),
          recommendedBidGbpPence: int("Recommended bid (pence)"),
          matchScore: { type: "number", description: "0..1 match score" },
          rationale: str("One-paragraph rationale"),
        },
        ["source", "externalListingId", "url", "make", "model", "matchScore", "rationale"],
      ),
      handler: async (i) => {
        const opp = await prisma.procurementOpportunity.upsert({
          where: { source_externalListingId: { source: i.source, externalListingId: i.externalListingId } },
          create: {
            source: i.source,
            externalListingId: i.externalListingId,
            url: i.url,
            make: i.make,
            model: i.model,
            yearOfManufacture: i.yearOfManufacture,
            mileage: i.mileage,
            damageCategory: i.damageCategory,
            askingPriceGbp: i.askingPriceGbpPence,
            recommendedBidGbp: i.recommendedBidGbpPence,
            matchScore: i.matchScore,
            rationale: i.rationale,
            outcome: ProcurementOutcome.WATCHING,
          },
          update: {
            askingPriceGbp: i.askingPriceGbpPence,
            recommendedBidGbp: i.recommendedBidGbpPence,
            matchScore: i.matchScore,
            rationale: i.rationale,
          },
        });
        return { opportunityId: opp.id };
      },
    }),
    tool({
      name: "place_bid",
      description: "Place a bid on a procurement opportunity. Always queues for operator approval.",
      input: z.object({ opportunityId: z.string(), bidGbpPence: z.number().int() }),
      jsonSchema: obj({ opportunityId: str("Opportunity ID"), bidGbpPence: int("Bid amount (pence)") }, ["opportunityId", "bidGbpPence"]),
      requiresApproval: ApprovalKind.PLACE_PROCUREMENT_BID,
      handler: async () => ({ queued: true }),
    }),
    tool({
      name: "build_market_digest",
      description: "Build a weekly 'what's hot' digest summarising trends across the watched feeds.",
      input: z.object({ daysBack: z.number().int().default(7) }),
      jsonSchema: obj({ daysBack: int("How many days of data to summarise") }),
      handler: async ({ daysBack }) => {
        const since = new Date(Date.now() - daysBack * 86_400_000);
        const opps = await prisma.procurementOpportunity.findMany({ where: { detectedAt: { gte: since } } });
        return {
          totalListingsScored: opps.length,
          highScore: opps.filter((o) => o.matchScore >= 0.75).length,
          bySource: Object.values(ProcurementSource).map((s) => ({ source: s, count: opps.filter((o) => o.source === s).length })),
        };
      },
    }),
  ],
};
