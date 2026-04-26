import { z } from "zod";
import type { ToolDefinition } from "../runtime/types.js";

/**
 * Helper that lifts a Zod schema into the JSON Schema shape Claude expects.
 * Keeps tool definitions terse and avoids hand-maintaining two schemas.
 */
export function tool<I, O>(opts: {
  name: string;
  description: string;
  input: z.ZodType<I>;
  jsonSchema: Record<string, unknown>;
  handler: (input: I) => Promise<O>;
  requiresApproval?: ToolDefinition["requiresApproval"];
}): ToolDefinition<I, O> {
  return {
    name: opts.name,
    description: opts.description,
    inputSchema: opts.input,
    jsonSchema: opts.jsonSchema,
    handler: opts.handler,
    requiresApproval: opts.requiresApproval,
  };
}

/** Standard input_schema with no parameters. */
export const emptySchema = {
  type: "object",
  properties: {},
  additionalProperties: false,
} as const;

/** Coerce a `{type:"object",properties:{...},required:[...]}` literal. */
export const obj = (
  properties: Record<string, unknown>,
  required: string[] = [],
): Record<string, unknown> => ({
  type: "object",
  properties,
  required,
  additionalProperties: false,
});

export const str = (description: string) => ({ type: "string", description });
export const num = (description: string) => ({ type: "number", description });
export const int = (description: string) => ({ type: "integer", description });
export const bool = (description: string) => ({ type: "boolean", description });
