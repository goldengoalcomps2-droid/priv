/**
 * @fleetpro/agents — public surface
 *
 * The runtime exports a small, opinionated entry point per agent.
 * Each agent is implemented as: system prompt + tool list + entry function.
 * The orchestrator turns a tool call into either a direct execution (safe ops)
 * or an Approval row (irreversible / customer-facing ops).
 */

export type { AgentEntry, AgentRunResult, ToolDefinition, ToolHandler } from "./runtime/types.js";
export { runAgent } from "./runtime/orchestrator.js";
export { resolveApproval } from "./runtime/approvals.js";

// Per-agent entry points
export { customerOnboardingAgent } from "./agents/customer-onboarding.js";
export { hireAndAgreementAgent } from "./agents/hire-and-agreement.js";
export { finesAndPcnAgent } from "./agents/fines-and-pcn.js";
export { fleetMaintenanceAgent } from "./agents/fleet-maintenance.js";
export { procurementAgent } from "./agents/procurement.js";
export { analyticsAndDefleetAgent } from "./agents/analytics-and-defleet.js";
