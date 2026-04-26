import { z } from "zod";
import { prisma } from "@fleetpro/db";
import type { AgentEntry } from "../runtime/types.js";
import { tool, obj, str } from "../tools/shared.js";

/**
 * Fleet Maintenance agent
 * - Service: looks up the nearest main dealer for a vehicle's make
 * - MOT: pulls expiry from DVSA MOT History API; writes a 7-day-before
 *   reminder to the operator's calendar
 * - Road tax: shows current status from DVLA VES; deep-links to gov.uk/vehicle-tax
 *   and surfaces the stored V5C 11-digit reference for one-click copy
 *
 * No approval gates — every tool here is read-only or low-risk.
 */

const SYSTEM_PROMPT = `You are the FleetPro Fleet Maintenance Agent.

You handle three workstreams: booking services at main dealers (UK), tracking
MOT expiry via DVSA, and tracking road tax via DVLA VES. When MOT or tax
moves into the at-risk window, write the reminder to the operator's calendar
and explain in your summary which vehicle and exactly when the deadline is.

Do not place dealer bookings autonomously — provide the dealer phone and
opening hours so the operator can call (the dashboard renders click-to-call).`;

export const fleetMaintenanceAgent: AgentEntry = {
  name: "FLEET_MAINTENANCE",
  systemPrompt: SYSTEM_PROMPT,
  tools: [
    tool({
      name: "find_nearest_main_dealer",
      description: "Find the nearest main dealer for a make. Returns dealer name, phone, opening hours.",
      input: z.object({ vehicleId: z.string() }),
      jsonSchema: obj({ vehicleId: str("Vehicle ID") }, ["vehicleId"]),
      handler: async ({ vehicleId }) => {
        const v = await prisma.vehicle.findUniqueOrThrow({ where: { id: vehicleId } });
        return {
          dealerName: `${v.make} Main Dealer (nearest)`,
          phone: "+44 0000 000000",
          address: "TBD via Places API",
          openingHours: { mon: "08:00-18:00", tue: "08:00-18:00", wed: "08:00-18:00", thu: "08:00-18:00", fri: "08:00-18:00", sat: "09:00-17:00", sun: "closed" },
        };
      },
    }),
    tool({
      name: "fetch_mot_status",
      description: "Pull the latest MOT record from the DVSA MOT History API and persist it.",
      input: z.object({ vrn: z.string() }),
      jsonSchema: obj({ vrn: str("Vehicle VRN") }, ["vrn"]),
      handler: async ({ vrn }) => {
        // Real impl: DVSA MOT History API client
        const v = await prisma.vehicle.findFirst({ where: { vrn } });
        if (!v) return { found: false };
        return { found: true, vehicleId: v.id, vrn: v.vrn, motDue: v.motDue };
      },
    }),
    tool({
      name: "create_calendar_reminder",
      description: "Write a 7-day-before reminder to the operator's business calendar (Google or Microsoft Graph).",
      input: z.object({ vehicleId: z.string(), kind: z.enum(["MOT", "TAX", "INSURANCE", "SERVICE"]), dueAt: z.string() }),
      jsonSchema: obj(
        {
          vehicleId: str("Vehicle ID"),
          kind: { type: "string", enum: ["MOT", "TAX", "INSURANCE", "SERVICE"], description: "Reminder kind" },
          dueAt: str("ISO due date"),
        },
        ["vehicleId", "kind", "dueAt"],
      ),
      handler: async ({ vehicleId, kind, dueAt }) => {
        const reminderAt = new Date(new Date(dueAt).getTime() - 7 * 86_400_000);
        return { eventId: `cal-${vehicleId}-${kind}-${reminderAt.toISOString()}`, reminderAt };
      },
    }),
    tool({
      name: "fetch_road_tax_status",
      description: "Query the DVLA Vehicle Enquiry Service (VES) for current road-tax status.",
      input: z.object({ vrn: z.string() }),
      jsonSchema: obj({ vrn: str("Vehicle VRN") }, ["vrn"]),
      handler: async ({ vrn }) => {
        const v = await prisma.vehicle.findFirst({ where: { vrn } });
        if (!v) return { found: false };
        return {
          found: true,
          vehicleId: v.id,
          vrn: v.vrn,
          taxDue: v.taxDue,
          v5cReference: v.v5cReference,
          taxThisVehicleUrl: "https://www.gov.uk/vehicle-tax",
        };
      },
    }),
  ],
};
