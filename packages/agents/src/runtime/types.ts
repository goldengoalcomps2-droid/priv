import type { AgentName, ApprovalKind } from "@fleetpro/db";
import type { z } from "zod";

/**
 * A tool the agent may call. `requiresApproval` flips the orchestrator
 * from direct execution to writing an Approval row that an operator must
 * confirm in the dashboard's approval queue.
 */
export type ToolHandler<I, O> = (input: I, ctx: ToolContext) => Promise<O>;

export interface ToolDefinition<I = unknown, O = unknown> {
  name: string;
  description: string;
  inputSchema: z.ZodType<I>;
  /** JSON Schema sent to Claude (derived from the Zod schema, or hand-written). */
  jsonSchema: Record<string, unknown>;
  handler: ToolHandler<I, O>;
  /** Approvable side-effect: orchestrator writes Approval row instead of executing. */
  requiresApproval?: ApprovalKind;
}

export interface ToolContext {
  /** Operator session if invoked from the dashboard, else undefined for cron / webhook. */
  userId?: string;
  /** Polymorphic context the tool may attach to AgentActivity / Approval. */
  customerId?: string;
  vehicleId?: string;
  hireId?: string;
  fineId?: string;
  procurementOpportunityId?: string;
}

export interface AgentEntry {
  name: AgentName;
  systemPrompt: string;
  tools: ToolDefinition[];
}

export interface AgentRunResult {
  /** Final assistant text the agent produced. */
  text: string;
  /** Activity log IDs written during this run, for the dashboard feed. */
  activityIds: string[];
  /** Approval IDs created during this run (operator must resolve these). */
  pendingApprovalIds: string[];
  /** Total token usage from the model. */
  usage: { inputTokens: number; outputTokens: number };
}
