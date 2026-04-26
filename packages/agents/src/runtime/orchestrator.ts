import Anthropic from "@anthropic-ai/sdk";
import { prisma, ActivityKind, ApprovalStatus } from "@fleetpro/db";
import type { AgentEntry, AgentRunResult, ToolContext } from "./types.js";

const MODEL = process.env.ANTHROPIC_MODEL ?? "claude-sonnet-4-6";

/**
 * Run an agent through a tool-use loop.
 *
 * For each model turn:
 *   1. send messages + tools to Claude
 *   2. for any tool_use block:
 *      - if the tool requires approval → write Approval row, return synthetic
 *        tool_result describing the queued approval
 *      - else → execute the handler, log AgentActivity, return tool_result
 *   3. when stop_reason becomes "end_turn", return the final text
 *
 * Every tool call (executed or queued) is persisted to AgentActivity, which
 * powers the dashboard's "Agent Activity" feed.
 */
export async function runAgent(
  agent: AgentEntry,
  userMessage: string,
  ctx: ToolContext = {},
): Promise<AgentRunResult> {
  const client = new Anthropic();
  const toolsForApi = agent.tools.map((t) => ({
    name: t.name,
    description: t.description,
    input_schema: t.jsonSchema as Anthropic.Tool.InputSchema,
  }));

  const messages: Anthropic.MessageParam[] = [{ role: "user", content: userMessage }];
  const activityIds: string[] = [];
  const pendingApprovalIds: string[] = [];
  let inputTokens = 0;
  let outputTokens = 0;
  let finalText = "";

  // Cap iterations to prevent runaway loops
  for (let iter = 0; iter < 12; iter++) {
    const response = await client.messages.create({
      model: MODEL,
      max_tokens: 4096,
      system: agent.systemPrompt,
      tools: toolsForApi,
      messages,
    });
    inputTokens += response.usage.input_tokens;
    outputTokens += response.usage.output_tokens;

    if (response.stop_reason === "end_turn") {
      const textBlock = response.content.find((b): b is Anthropic.TextBlock => b.type === "text");
      finalText = textBlock?.text ?? "";
      break;
    }

    if (response.stop_reason !== "tool_use") {
      // refusal, max_tokens, etc — bail with whatever text we have
      const textBlock = response.content.find((b): b is Anthropic.TextBlock => b.type === "text");
      finalText = textBlock?.text ?? `(stopped: ${response.stop_reason})`;
      break;
    }

    // Echo the assistant's full response so tool_use IDs match on the next turn
    messages.push({ role: "assistant", content: response.content });

    const toolResults: Anthropic.ToolResultBlockParam[] = [];
    for (const block of response.content) {
      if (block.type !== "tool_use") continue;
      const tool = agent.tools.find((t) => t.name === block.name);
      if (!tool) {
        toolResults.push({
          type: "tool_result",
          tool_use_id: block.id,
          content: `Unknown tool: ${block.name}`,
          is_error: true,
        });
        continue;
      }

      const parsed = tool.inputSchema.safeParse(block.input);
      if (!parsed.success) {
        toolResults.push({
          type: "tool_result",
          tool_use_id: block.id,
          content: `Invalid input: ${parsed.error.message}`,
          is_error: true,
        });
        continue;
      }

      // Approvable side-effects: queue, do not execute
      if (tool.requiresApproval) {
        const approval = await prisma.approval.create({
          data: {
            agent: agent.name,
            kind: tool.requiresApproval,
            title: `${tool.name} (queued by ${agent.name})`,
            proposedAction: { tool: tool.name, args: parsed.data as object },
            rationale: "Awaiting operator review per the human-in-the-loop policy.",
            status: ApprovalStatus.PENDING,
            customerId: ctx.customerId,
            vehicleId: ctx.vehicleId,
            hireId: ctx.hireId,
            fineId: ctx.fineId,
            procurementOpportunityId: ctx.procurementOpportunityId,
          },
        });
        pendingApprovalIds.push(approval.id);

        const activity = await prisma.agentActivity.create({
          data: {
            agent: agent.name,
            kind: ActivityKind.APPROVAL_REQUEST,
            summary: `Queued ${tool.name} for operator approval`,
            toolName: tool.name,
            toolInput: parsed.data as object,
            customerId: ctx.customerId,
            vehicleId: ctx.vehicleId,
            hireId: ctx.hireId,
            fineId: ctx.fineId,
          },
        });
        activityIds.push(activity.id);

        toolResults.push({
          type: "tool_result",
          tool_use_id: block.id,
          content: `Action queued for human review (approval id: ${approval.id}). Inform the user that the operator must confirm in the approval queue.`,
        });
        continue;
      }

      // Direct execution
      const startedAt = Date.now();
      try {
        const output = await tool.handler(parsed.data, ctx);
        const durationMs = Date.now() - startedAt;
        const activity = await prisma.agentActivity.create({
          data: {
            agent: agent.name,
            kind: ActivityKind.TOOL_CALL,
            summary: `${tool.name} succeeded`,
            toolName: tool.name,
            toolInput: parsed.data as object,
            toolOutput: output as object,
            toolDurationMs: durationMs,
            customerId: ctx.customerId,
            vehicleId: ctx.vehicleId,
            hireId: ctx.hireId,
            fineId: ctx.fineId,
          },
        });
        activityIds.push(activity.id);
        toolResults.push({
          type: "tool_result",
          tool_use_id: block.id,
          content: JSON.stringify(output),
        });
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        await prisma.agentActivity.create({
          data: {
            agent: agent.name,
            kind: ActivityKind.ERROR,
            summary: `${tool.name} failed: ${message}`,
            toolName: tool.name,
            toolInput: parsed.data as object,
          },
        });
        toolResults.push({
          type: "tool_result",
          tool_use_id: block.id,
          content: `Tool error: ${message}`,
          is_error: true,
        });
      }
    }

    messages.push({ role: "user", content: toolResults });
  }

  return {
    text: finalText,
    activityIds,
    pendingApprovalIds,
    usage: { inputTokens, outputTokens },
  };
}
