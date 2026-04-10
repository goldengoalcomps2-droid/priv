"""
Lead Commander Agent - The user's primary point of contact with the team.

The Commander is the chief-of-staff for the entire agent team. He:
  * Receives every instruction, idea, message and task from the user
  * Decides which specialist agent (or group of agents) should handle it
  * Routes the work via the message bus and the orchestrator
  * Watches every other agent's actions, decisions and bus traffic
  * Produces detailed updates back to the user on what the team is doing
  * Maintains a fluid, interactive dialogue (memory of recent turns,
    follow-up suggestions, clarifying answers)

The Commander is intentionally rule-based and deterministic so it can run
without any external LLM calls. The routing logic uses keyword scoring
against each specialist's capability set so it stays accurate even as
new agents are added.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Any

from ..core.base_agent import (
    BaseAgent,
    AgentRole,
    AgentAction,
    AgentMessage,
    ActionPriority,
)


# ---------------------------------------------------------------------------
# Routing keyword map
# ---------------------------------------------------------------------------
# Words / phrases that score points toward each specialist agent.
# Each entry is (regex, weight). The commander picks the agent with the
# highest cumulative score; ties broken by capability match.
ROUTING_KEYWORDS: dict[AgentRole, list[tuple[str, int]]] = {
    AgentRole.STRATEGY: [
        (r"\bstrateg(y|ies|ic)\b", 4),
        (r"\bplan(s|ning)?\b", 3),
        (r"\bgoal(s)?\b", 3),
        (r"\bmilestone(s)?\b", 3),
        (r"\bmethod(s|ology)?\b", 2),
        (r"\bvision\b", 2),
        (r"\broadmap\b", 3),
        (r"\bpivot\b", 3),
        (r"\bdecompose\b", 2),
    ],
    AgentRole.RESEARCH: [
        (r"\bresearch\b", 4),
        (r"\bmarket\b", 3),
        (r"\bcompetit(or|ive|ion)\b", 3),
        (r"\banalys(e|is|ze)\b", 2),
        (r"\bdata\b", 2),
        (r"\bfind out\b", 3),
        (r"\binvestigat(e|ion)\b", 3),
        (r"\btrend(s)?\b", 2),
        (r"\binsight(s)?\b", 2),
        (r"\bbenchmark\b", 2),
    ],
    AgentRole.OPERATIONS: [
        (r"\bexecut(e|ion)\b", 4),
        (r"\btask(s)?\b", 3),
        (r"\bdo (this|that|it)\b", 3),
        (r"\brun\b", 2),
        (r"\bdeploy\b", 3),
        (r"\bship\b", 3),
        (r"\bworkflow(s)?\b", 3),
        (r"\bdependenc(y|ies)\b", 2),
        (r"\bprogress\b", 2),
        (r"\bschedule\b", 2),
        (r"\bbacklog\b", 2),
    ],
    AgentRole.FORECAST: [
        (r"\bforecast(s|ing)?\b", 4),
        (r"\bpredict(ion|ions)?\b", 3),
        (r"\brisk(s)?\b", 3),
        (r"\bproject(ion|ions)\b", 3),
        (r"\bscenario(s)?\b", 3),
        (r"\bvelocity\b", 3),
        (r"\bcapacity\b", 2),
        (r"\bwhen will\b", 3),
        (r"\bestimate(s|d)?\b", 2),
        (r"\bdeadline(s)?\b", 2),
    ],
    AgentRole.QA: [
        (r"\bqa\b", 4),
        (r"\bqualit(y|ies)\b", 4),
        (r"\btest(s|ing)?\b", 3),
        (r"\bvalidat(e|ion)\b", 3),
        (r"\bbug(s)?\b", 3),
        (r"\bissue(s)?\b", 2),
        (r"\bcomplian(ce|t)\b", 3),
        (r"\baudit\b", 3),
        (r"\breview\b", 2),
        (r"\bbroken\b", 3),
    ],
    AgentRole.RESOURCE: [
        (r"\bresource(s)?\b", 4),
        (r"\btool(s|ing)?\b", 3),
        (r"\bintegrat(e|ion|ions)\b", 3),
        (r"\bbudget\b", 2),
        (r"\bcost(s)?\b", 2),
        (r"\bvendor(s)?\b", 3),
        (r"\bplatform(s)?\b", 2),
        (r"\bsubscription(s)?\b", 2),
        (r"\bsoftware\b", 2),
        (r"\bservice(s)?\b", 1),
    ],
}

# Words that mean "tell me about X" rather than "go do X"
QUERY_VERBS = re.compile(
    r"\b(what|how|why|when|where|who|show|list|tell|give|status|report|update|how many|how much)\b",
    re.IGNORECASE,
)

# Words that mean "do this now"
ACTION_VERBS = re.compile(
    r"\b(do|make|build|create|run|execute|launch|start|kick off|deploy|ship|schedule|set up|delegate|assign)\b",
    re.IGNORECASE,
)

# Words that mean "I have an idea / suggestion"
IDEA_VERBS = re.compile(
    r"\b(idea|suggest|consider|what if|maybe|propose|brainstorm|thought)\b",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Lead Commander Agent
# ---------------------------------------------------------------------------
class LeadCommanderAgent(BaseAgent):
    """
    Chief-of-staff agent that fronts the entire team for the user.
    """

    def __init__(self, team_bus=None, orchestrator=None):
        super().__init__(AgentRole.COMMANDER, team_bus)
        self.name = "LeadCommander"
        self.orchestrator = orchestrator
        self._capabilities = [
            "user_dialogue",
            "intent_classification",
            "task_routing",
            "team_status_reporting",
            "agent_activity_tracking",
            "decision_summarisation",
            "memory_of_conversation",
        ]
        # Conversation memory: list of {"role": "user"|"commander", "text": ..., "ts": ...}
        self.conversation: list[dict] = []
        # Live feed of every bus event the commander has observed
        self.activity_feed: list[dict] = []
        # Per-agent action / decision tracker
        self.agent_activity: dict[str, list[dict]] = {}
        # Last routing decision (for the UI to highlight)
        self.last_routing: dict | None = None

    # --- bind to orchestrator ------------------------------------------------

    def attach_orchestrator(self, orchestrator):
        """Wire the commander to the orchestrator after both are constructed."""
        self.orchestrator = orchestrator
        if orchestrator and orchestrator.bus:
            self.team_bus = orchestrator.bus
            # Watch every message that crosses the bus
            orchestrator.bus.subscribe("all", self._observe_bus)
            orchestrator.bus.subscribe("commander", self._observe_bus)

    # --- bus observer --------------------------------------------------------

    def _observe_bus(self, message: AgentMessage):
        """Record every message we see, so we can give the user fluent updates."""
        # Avoid recording our own outbound noise
        if message.sender == self.role.value and message.recipient == "user":
            return
        entry = {
            "id": message.id,
            "ts": message.timestamp,
            "from": message.sender,
            "to": message.recipient,
            "subject": message.subject,
            "body": message.body,
            "type": message.message_type,
            "payload": message.payload,
        }
        self.activity_feed.append(entry)
        # Trim to last 500 events
        if len(self.activity_feed) > 500:
            self.activity_feed = self.activity_feed[-500:]
        # Track per-agent activity
        bucket = self.agent_activity.setdefault(message.sender, [])
        bucket.append(entry)
        if len(bucket) > 100:
            self.agent_activity[message.sender] = bucket[-100:]

    # --- intent / routing ---------------------------------------------------

    def _classify_intent(self, text: str) -> str:
        """Classify a user message as 'query', 'action', 'idea' or 'message'."""
        if QUERY_VERBS.search(text) and not ACTION_VERBS.search(text):
            return "query"
        if ACTION_VERBS.search(text):
            return "action"
        if IDEA_VERBS.search(text):
            return "idea"
        return "message"

    def _score_routes(self, text: str) -> list[tuple[AgentRole, int]]:
        """Score each specialist agent for relevance to the message."""
        text_lower = text.lower()
        scores: list[tuple[AgentRole, int]] = []
        for role, kws in ROUTING_KEYWORDS.items():
            score = 0
            for pattern, weight in kws:
                if re.search(pattern, text_lower):
                    score += weight
            if score:
                scores.append((role, score))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores

    def _route_targets(self, text: str) -> list[AgentRole]:
        """Pick the agent(s) the message should go to."""
        scores = self._score_routes(text)
        if not scores:
            # Nobody scored - it's a general team message
            return []
        # Take the top scorer plus anyone within 1 point of it (multi-route)
        top_score = scores[0][1]
        chosen = [role for role, s in scores if s >= top_score - 1]
        return chosen[:3]  # cap at 3

    # --- the main entry point: user says something --------------------------

    def handle_user_message(self, text: str) -> dict:
        """
        Process a user message end-to-end and return a structured response
        the chat UI can render.
        """
        text = (text or "").strip()
        if not text:
            return {"reply": "(empty message)", "events": []}

        # Remember it
        self.conversation.append({
            "role": "user",
            "text": text,
            "ts": datetime.now(timezone.utc).isoformat(),
        })

        # Classify and route
        intent = self._classify_intent(text)
        targets = self._route_targets(text)

        # Build the commander's reply
        events: list[dict] = []
        reply_lines: list[str] = []

        if intent == "query":
            reply_lines.append(self._answer_query(text, targets))
        elif intent == "action":
            reply_lines.append(self._dispatch_action(text, targets, events))
        elif intent == "idea":
            reply_lines.append(self._capture_idea(text, targets, events))
        else:
            reply_lines.append(self._broadcast_message(text, targets, events))

        # If we routed to specialists, append a routing summary
        if targets:
            target_names = ", ".join(t.value for t in targets)
            reply_lines.append(
                f"\nRouted to: **{target_names}**. I'll surface their next moves "
                f"in the activity feed."
            )
            self.last_routing = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "targets": [t.value for t in targets],
                "intent": intent,
                "text": text,
            }
        else:
            self.last_routing = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "targets": [],
                "intent": intent,
                "text": text,
            }

        reply = "\n".join(reply_lines)
        self.conversation.append({
            "role": "commander",
            "text": reply,
            "ts": datetime.now(timezone.utc).isoformat(),
        })

        # Mirror the user message into the bus so the rest of the team sees it
        self.send_message(
            recipient="all",
            subject=f"User instruction received [{intent}]",
            body=text,
            message_type="info",
            payload={"intent": intent, "targets": [t.value for t in targets]},
        )

        return {
            "reply": reply,
            "intent": intent,
            "targets": [t.value for t in targets],
            "events": events,
        }

    # --- helpers for each intent --------------------------------------------

    def _answer_query(self, text: str, targets: list[AgentRole]) -> str:
        """Give the user a detailed status answer drawn from the orchestrator."""
        if not self.orchestrator:
            return "Standing by - orchestrator not yet attached."

        text_lower = text.lower()

        # Whole-team status request
        if any(w in text_lower for w in ("team", "everyone", "all agents", "everything", "overview")):
            return self._team_overview()

        # Project request
        if "project" in text_lower:
            p = self.orchestrator.active_project
            if not p:
                return "No active project loaded."
            return f"**Active project:** {p.summary()}"

        # Specific agent report
        if targets:
            return self._agent_briefings(targets)

        # Generic fallback - team overview
        return self._team_overview()

    def _team_overview(self) -> str:
        if not self.orchestrator:
            return "Orchestrator not attached."
        status = self.orchestrator.team_status()
        lines = []
        active = status.get("active_project")
        lines.append(f"**Project:** {active or 'no active project'}")
        lines.append(f"**Cycles run:** {status.get('cycle_count', 0)}")
        lines.append("")
        lines.append("**Agents:**")
        for role, info in status.get("agents", {}).items():
            state = "ACTIVE" if info.get("active") else "INACTIVE"
            recent = self.agent_activity.get(role, [])
            last = recent[-1]["subject"] if recent else "-"
            lines.append(
                f"  - {role}: {state} | actions={info.get('total_actions', 0)} | last: {last}"
            )
        bus = status.get("bus_stats", {})
        lines.append("")
        lines.append(
            f"**Bus:** {bus.get('total_messages', 0)} msgs, "
            f"{bus.get('pending_approvals', 0)} approvals pending"
        )
        return "\n".join(lines)

    def _agent_briefings(self, targets: list[AgentRole]) -> str:
        if not self.orchestrator:
            return "Orchestrator not attached."
        lines = []
        for role in targets:
            agent = self.orchestrator.get_agent(role)
            if not agent:
                lines.append(f"_{role.value}: not registered_")
                continue
            project = self.orchestrator.active_project
            analysis = agent.analyse_project(project.to_dict() if project else {})
            lines.append(f"**{agent.name}** ({role.value})")
            for k, v in list(analysis.items())[:6]:
                if k == "agent":
                    continue
                lines.append(f"  - {k}: {self._fmt(v)}")
            recent = self.agent_activity.get(role.value, [])[-3:]
            if recent:
                lines.append("  Recent activity:")
                for r in recent:
                    lines.append(f"    • [{r['type']}] {r['subject']}")
            lines.append("")
        return "\n".join(lines)

    def _dispatch_action(
        self, text: str, targets: list[AgentRole], events: list[dict]
    ) -> str:
        """Turn a user action into a delegated task on the right agent(s)."""
        if not self.orchestrator:
            return "Cannot dispatch yet - orchestrator not attached."
        if not targets:
            # Default to operations
            targets = [AgentRole.OPERATIONS]
        title = text if len(text) <= 80 else text[:77] + "..."
        delivered = []
        for role in targets:
            try:
                task = self.orchestrator.delegate_task(
                    role=role,
                    title=title,
                    description=text,
                    priority="high" if "urgent" in text.lower() else "medium",
                )
                delivered.append((role.value, task))
                events.append({
                    "type": "delegation",
                    "agent": role.value,
                    "task_id": task.get("id"),
                    "title": title,
                })
            except Exception as e:
                events.append({"type": "error", "agent": role.value, "error": str(e)})
        if not delivered:
            return "I couldn't find an agent to take this. Try rephrasing or naming an agent (e.g. 'research', 'operations')."
        names = ", ".join(d[0] for d in delivered)
        return (
            f"Acknowledged. I've created a task and assigned it to **{names}**. "
            f"They'll begin work on the next cycle - I'll feed you their decisions "
            f"as they happen."
        )

    def _capture_idea(
        self, text: str, targets: list[AgentRole], events: list[dict]
    ) -> str:
        """Capture an idea and send it to the right specialist for evaluation."""
        if not self.orchestrator:
            return "Captured your idea (orchestrator offline - will route once it's up)."
        if not targets:
            targets = [AgentRole.STRATEGY]  # ideas default to Strategy
        for role in targets:
            self.send_message(
                recipient=role.value,
                subject="Idea from the user for evaluation",
                body=text,
                message_type="request",
                payload={"kind": "idea"},
            )
            events.append({
                "type": "idea_routed",
                "agent": role.value,
                "text": text,
            })
        names = ", ".join(t.value for t in targets)
        return (
            f"Got it - I've passed the idea to **{names}** for evaluation. "
            f"I'll come back with their take and any tasks it spawns."
        )

    def _broadcast_message(
        self, text: str, targets: list[AgentRole], events: list[dict]
    ) -> str:
        """Generic team-wide message."""
        recipient_value = "all" if not targets else targets[0].value
        self.send_message(
            recipient=recipient_value,
            subject="Message from the user",
            body=text,
            message_type="info",
        )
        events.append({
            "type": "broadcast",
            "agent": recipient_value,
            "text": text,
        })
        if recipient_value == "all":
            return "Message delivered to the entire team. I'll watch for responses and report back."
        return f"Message delivered to **{recipient_value}**. I'll watch for responses."

    # --- reporting helpers (used by the UI) ---------------------------------

    def get_activity_feed(self, limit: int = 50, since: str | None = None) -> list[dict]:
        feed = self.activity_feed
        if since:
            feed = [e for e in feed if e["ts"] > since]
        return feed[-limit:]

    def get_agent_activity(self, role: str, limit: int = 20) -> list[dict]:
        return self.agent_activity.get(role, [])[-limit:]

    def get_conversation(self, limit: int = 100) -> list[dict]:
        return self.conversation[-limit:]

    def briefing(self) -> dict:
        """A single payload the chat UI can poll for live updates."""
        return {
            "commander": self.name,
            "active": self.active,
            "last_routing": self.last_routing,
            "team_overview": self._team_overview() if self.orchestrator else None,
            "activity_feed": self.get_activity_feed(limit=30),
            "agent_activity": {
                k: v[-5:] for k, v in self.agent_activity.items()
            },
            "conversation_length": len(self.conversation),
        }

    # --- formatting helper ---------------------------------------------------

    @staticmethod
    def _fmt(v: Any) -> str:
        if isinstance(v, (list, tuple)):
            if not v:
                return "[]"
            if isinstance(v[0], dict):
                return f"[{len(v)} items]"
            return ", ".join(str(x) for x in v[:5])
        if isinstance(v, dict):
            return f"{{{len(v)} keys}}"
        return str(v)
