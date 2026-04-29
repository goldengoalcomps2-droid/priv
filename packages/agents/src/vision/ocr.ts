import Anthropic from "@anthropic-ai/sdk";
import { z } from "zod";

const MODEL = process.env.ANTHROPIC_MODEL ?? "claude-sonnet-4-6";

/**
 * UK driving licence fields the Customer Onboarding agent extracts via
 * Claude Vision. The schema mirrors the visible DVLA layout — we keep the
 * shape strict so downstream code never has to "interpret" the model.
 *
 * If a field is illegible/missing, the model returns null for that field
 * (NEVER guesses). We then surface those as flags for operator review.
 */
export const LicenceOcrSchema = z.object({
  fullName: z.string().nullable(),
  dateOfBirth: z.string().nullable(), // ISO 8601
  licenceNumber: z.string().nullable(),
  issueDate: z.string().nullable(),
  expiryDate: z.string().nullable(),
  issuingAuthority: z.string().nullable(), // "DVLA" / "DVA" (NI)
  address: z.string().nullable(),
  categories: z.array(z.string()),
  flags: z.array(z.string()), // illegibility / suspected forgery / mismatch hints
});
export type LicenceOcr = z.infer<typeof LicenceOcrSchema>;

const SYSTEM = `You are a forensic OCR assistant reading UK driving licences (DVLA / DVA).
Extract ONLY what you can see. NEVER guess.
- Dates must be ISO 8601 (YYYY-MM-DD).
- If a field is illegible or absent, return null for that field — do NOT fabricate.
- "categories" is the list of vehicle categories visible on the licence (e.g. ["B", "AM"]).
- "flags" is a free-form array of strings describing anything suspicious (e.g.
  "front and back appear to be different documents", "expiry date in the past",
  "photo region appears edited"). Empty array if everything looks consistent.
- If the image is not actually a UK driving licence, return all-null fields and
  add a flag "not_a_uk_driving_licence".
Respond ONLY with JSON matching the requested schema.`;

const TOOL: Anthropic.Tool = {
  name: "record_licence",
  description: "Record the OCR'd UK driving licence fields.",
  input_schema: {
    type: "object",
    properties: {
      fullName: { type: ["string", "null"] },
      dateOfBirth: { type: ["string", "null"], description: "ISO 8601 date" },
      licenceNumber: { type: ["string", "null"] },
      issueDate: { type: ["string", "null"], description: "ISO 8601 date" },
      expiryDate: { type: ["string", "null"], description: "ISO 8601 date" },
      issuingAuthority: { type: ["string", "null"] },
      address: { type: ["string", "null"] },
      categories: { type: "array", items: { type: "string" } },
      flags: { type: "array", items: { type: "string" } },
    },
    required: ["fullName", "dateOfBirth", "licenceNumber", "issueDate", "expiryDate", "issuingAuthority", "address", "categories", "flags"],
  },
};

/**
 * OCR a UK driving licence using Claude Vision. Provide raw image bytes and
 * media type — the helper handles base64 + the strict tool-use round-trip.
 */
export async function ocrDrivingLicence(opts: {
  frontImage: { bytes: Buffer; mediaType: "image/jpeg" | "image/png" | "image/webp" };
  backImage?: { bytes: Buffer; mediaType: "image/jpeg" | "image/png" | "image/webp" };
}): Promise<LicenceOcr> {
  const client = new Anthropic();
  const content: Anthropic.ContentBlockParam[] = [
    { type: "text", text: "Extract the licence fields from these images." },
    {
      type: "image",
      source: { type: "base64", media_type: opts.frontImage.mediaType, data: opts.frontImage.bytes.toString("base64") },
    },
  ];
  if (opts.backImage) {
    content.push({
      type: "image",
      source: { type: "base64", media_type: opts.backImage.mediaType, data: opts.backImage.bytes.toString("base64") },
    });
  }

  const response = await client.messages.create({
    model: MODEL,
    max_tokens: 1024,
    system: SYSTEM,
    tools: [TOOL],
    tool_choice: { type: "tool", name: "record_licence" },
    messages: [{ role: "user", content }],
  });

  const toolUse = response.content.find((b): b is Anthropic.ToolUseBlock => b.type === "tool_use");
  if (!toolUse) throw new Error("Model returned no tool_use block");
  return LicenceOcrSchema.parse(toolUse.input);
}

// ─── PCN OCR ──────────────────────────────────────────────────────────

export const PcnOcrSchema = z.object({
  issuingAuthority: z.string().nullable(),
  pcnNumber: z.string().nullable(),
  vrn: z.string().nullable(),
  offenceAt: z.string().nullable(), // ISO 8601 datetime
  location: z.string().nullable(),
  amountGbpPence: z.number().int().nullable(),
  flags: z.array(z.string()),
});
export type PcnOcr = z.infer<typeof PcnOcrSchema>;

const PCN_TOOL: Anthropic.Tool = {
  name: "record_pcn",
  description: "Record the OCR'd PCN / penalty charge notice fields.",
  input_schema: {
    type: "object",
    properties: {
      issuingAuthority: { type: ["string", "null"] },
      pcnNumber: { type: ["string", "null"] },
      vrn: { type: ["string", "null"] },
      offenceAt: { type: ["string", "null"], description: "ISO 8601 datetime" },
      location: { type: ["string", "null"] },
      amountGbpPence: { type: ["integer", "null"] },
      flags: { type: "array", items: { type: "string" } },
    },
    required: ["issuingAuthority", "pcnNumber", "vrn", "offenceAt", "location", "amountGbpPence", "flags"],
  },
};

export async function ocrPcnNotice(opts: { image: { bytes: Buffer; mediaType: "image/jpeg" | "image/png" | "image/webp" } }): Promise<PcnOcr> {
  const client = new Anthropic();
  const response = await client.messages.create({
    model: MODEL,
    max_tokens: 1024,
    system:
      "You read UK Penalty Charge Notices. Extract issuing authority, PCN reference, VRN, offence datetime, location, and amount in PENCE. Use ISO 8601 for the datetime. Return null for unreadable fields. Respond ONLY by calling the tool.",
    tools: [PCN_TOOL],
    tool_choice: { type: "tool", name: "record_pcn" },
    messages: [
      {
        role: "user",
        content: [
          { type: "text", text: "Extract the fields from this PCN notice." },
          { type: "image", source: { type: "base64", media_type: opts.image.mediaType, data: opts.image.bytes.toString("base64") } },
        ],
      },
    ],
  });
  const toolUse = response.content.find((b): b is Anthropic.ToolUseBlock => b.type === "tool_use");
  if (!toolUse) throw new Error("Model returned no tool_use block");
  return PcnOcrSchema.parse(toolUse.input);
}
