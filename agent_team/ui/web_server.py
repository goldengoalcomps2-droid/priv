"""
Web Server - Flask API backend for the Agent Team browser chat interface.

Provides REST endpoints for:
- Sending messages to the team
- Viewing agent status, project info, tasks, approvals
- Running orchestration cycles
- Approving/rejecting actions
- Real-time message polling
"""

import json
import logging
from datetime import datetime, timezone
from flask import Flask, request, jsonify, send_from_directory
from pathlib import Path

from ..core.orchestrator import Orchestrator
from ..core.base_agent import AgentRole, AgentMessage
from ..core.communication import CommunicationHub
from ..core.project import Project, ProjectStatus
from ..acp.protocol import ACPHub, ACPMessageType
from ..main import build_team


app = Flask(__name__, static_folder=str(Path(__file__).parent / "static"))

# Global state
_orch: Orchestrator = None
_comm: CommunicationHub = None
_acp: ACPHub = None
_chat_log: list[dict] = []


def _init_team():
    global _orch, _comm, _acp
    if _orch is None:
        _orch, _comm, _acp = build_team()
        # Try to load existing project
        project_path = Path(__file__).parent.parent / "projects" / "income_engine.json"
        if project_path.exists():
            _orch.load_project(str(project_path))
            if _orch.active_project:
                _orch.active_project.status = ProjectStatus.ACTIVE


def _agent_response(user_msg: str) -> list[dict]:
    """Process a user message and generate agent responses."""
    _init_team()
    responses = []
    msg_lower = user_msg.lower().strip()

    # Route commands
    if msg_lower in ("status", "team status", "show status"):
        status = _orch.team_status()
        responses.append({
            "agent": "Orchestrator",
            "role": "orchestrator",
            "message": _format_status(status),
            "type": "status",
        })

    elif msg_lower in ("project", "show project", "project info"):
        p = _orch.active_project
        if p:
            responses.append({
                "agent": "Orchestrator",
                "role": "orchestrator",
                "message": p.summary(),
                "type": "project",
            })
        else:
            responses.append({
                "agent": "Orchestrator",
                "role": "orchestrator",
                "message": "No active project. Create one first.",
                "type": "info",
            })

    elif msg_lower in ("tasks", "task board", "show tasks"):
        responses.extend(_get_task_report())

    elif msg_lower in ("approvals", "pending", "show approvals"):
        responses.extend(_get_approvals())

    elif msg_lower == "approve all":
        count = _comm.approve_all("Approved via chat interface")
        responses.append({
            "agent": "Orchestrator",
            "role": "orchestrator",
            "message": f"Approved {count} pending actions.",
            "type": "success",
        })

    elif msg_lower.startswith("approve "):
        action_id = msg_lower.replace("approve ", "").strip()
        if _comm.approve(action_id):
            responses.append({
                "agent": "Orchestrator",
                "role": "orchestrator",
                "message": f"Approved action: {action_id}",
                "type": "success",
            })
        else:
            responses.append({
                "agent": "Orchestrator",
                "role": "orchestrator",
                "message": f"No pending approval found for: {action_id}",
                "type": "error",
            })

    elif msg_lower.startswith("reject "):
        action_id = msg_lower.replace("reject ", "").strip()
        if _comm.reject(action_id):
            responses.append({
                "agent": "Orchestrator",
                "role": "orchestrator",
                "message": f"Rejected action: {action_id}",
                "type": "success",
            })
        else:
            responses.append({
                "agent": "Orchestrator",
                "role": "orchestrator",
                "message": f"No pending approval found for: {action_id}",
                "type": "error",
            })

    elif msg_lower in ("run cycle", "run-cycle", "cycle"):
        result = _orch.run_cycle()
        cycle_msg = (
            f"Cycle #{result.get('cycle', '?')} complete.\n"
            f"Actions executed: {result.get('actions_executed', 0)}\n"
            f"Pending approval: {result.get('actions_pending_approval', 0)}\n"
        )
        for role, info in result.get("agent_results", {}).items():
            cycle_msg += f"\n{role}: {info.get('actions_proposed', 0)} actions proposed"
        responses.append({
            "agent": "Orchestrator",
            "role": "orchestrator",
            "message": cycle_msg,
            "type": "cycle",
        })

    elif msg_lower in ("goals", "show goals"):
        responses.extend(_get_goals())

    elif msg_lower in ("targets", "show targets"):
        responses.extend(_get_targets())

    elif msg_lower in ("forecast", "show forecast"):
        responses.extend(_get_forecast())

    elif msg_lower in ("quality", "qa", "show quality"):
        responses.extend(_get_quality())

    elif msg_lower in ("research", "show research"):
        responses.extend(_get_research())

    elif msg_lower in ("resources", "show resources"):
        responses.extend(_get_resources())

    elif msg_lower in ("strategies", "show strategies"):
        responses.extend(_get_strategies())

    elif msg_lower in ("acp", "external agents", "show acp"):
        responses.extend(_get_acp_status())

    elif msg_lower in ("plan", "show plan"):
        responses.extend(_get_plans())

    elif msg_lower in ("help", "commands"):
        responses.append({
            "agent": "Orchestrator",
            "role": "orchestrator",
            "message": _help_text(),
            "type": "info",
        })

    elif msg_lower.startswith("run "):
        agent_name = msg_lower.replace("run ", "").strip()
        try:
            role = AgentRole(agent_name)
            result = _orch.run_agent_cycle(role)
            actions = result.get("actions", [])
            msg = f"{result.get('agent', agent_name)}: {len(actions)} actions\n"
            for a in actions[:5]:
                msg += f"\n  - {a.get('title', 'untitled')}"
            responses.append({
                "agent": result.get("agent", agent_name),
                "role": agent_name,
                "message": msg,
                "type": "cycle",
            })
        except ValueError:
            responses.append({
                "agent": "Orchestrator",
                "role": "orchestrator",
                "message": f"Unknown agent: {agent_name}. Available: strategy, research, operations, forecast, qa, resource",
                "type": "error",
            })

    else:
        # General message to team
        _comm.send_to_team(user_msg)
        responses.append({
            "agent": "Orchestrator",
            "role": "orchestrator",
            "message": f"Message delivered to the team: \"{user_msg}\"",
            "type": "info",
        })
        # Each agent acknowledges
        for role, agent in _orch.agents.items():
            if agent.active:
                analysis = agent.analyse_project(_orch.active_project.to_dict() if _orch.active_project else {})
                summary_keys = [k for k in analysis.keys() if k != "agent"]
                brief = ", ".join(f"{k}: {v}" for k, v in list(analysis.items())[:3] if k != "agent")
                responses.append({
                    "agent": agent.name,
                    "role": role.value,
                    "message": f"Acknowledged. Current analysis: {brief}",
                    "type": "info",
                })

    return responses


# --- Report formatters -------------------------------------------------------

def _format_status(status: dict) -> str:
    lines = []
    if status.get("active_project"):
        lines.append(status["active_project"])
    else:
        lines.append("No active project")
    lines.append("\nAgents:")
    for role, info in status.get("agents", {}).items():
        state = "ACTIVE" if info.get("active") else "INACTIVE"
        lines.append(f"  {role}: {state} | Actions: {info.get('total_actions', 0)}")
    bus = status.get("bus_stats", {})
    lines.append(f"\nMessages: {bus.get('total_messages', 0)}")
    lines.append(f"Pending approvals: {bus.get('pending_approvals', 0)}")
    lines.append(f"Cycles run: {status.get('cycle_count', 0)}")
    return "\n".join(lines)


def _get_task_report() -> list[dict]:
    p = _orch.active_project
    if not p:
        return [{"agent": "Operations", "role": "operations", "message": "No active project", "type": "error"}]
    responses = []
    for status_name in ["in_progress", "pending", "blocked", "completed"]:
        tasks = p.get_tasks(status=status_name)
        if tasks:
            msg = f"**{status_name.upper()} ({len(tasks)})**\n"
            for t in tasks[:10]:
                agent_tag = f" [{t.assigned_to}]" if t.assigned_to else ""
                msg += f"  {'●' if status_name == 'completed' else '○'} {t.title}{agent_tag} (#{t.id})\n"
            if len(tasks) > 10:
                msg += f"  ... and {len(tasks) - 10} more"
            responses.append({
                "agent": "OperationsAgent",
                "role": "operations",
                "message": msg,
                "type": "tasks",
            })
    if not responses:
        responses.append({"agent": "OperationsAgent", "role": "operations", "message": "No tasks on the board.", "type": "info"})
    return responses


def _get_approvals() -> list[dict]:
    pending = _comm.get_pending_approvals()
    if not pending:
        return [{"agent": "Orchestrator", "role": "orchestrator", "message": "No pending approvals.", "type": "success"}]
    msg = f"**{len(pending)} Pending Approvals:**\n\n"
    for i, req in enumerate(pending[:15], 1):
        msg += f"[{i}] **{req['title']}**\n"
        msg += f"    From: {req['agent']} | Priority: {req['priority']}\n"
        msg += f"    {req['description'][:100]}\n"
        msg += f"    ID: `{req['action_id']}`\n\n"
    if len(pending) > 15:
        msg += f"... and {len(pending) - 15} more. Type 'approve all' to greenlight everything."
    return [{"agent": "Orchestrator", "role": "orchestrator", "message": msg, "type": "approvals"}]


def _get_goals() -> list[dict]:
    p = _orch.active_project
    if not p:
        return [{"agent": "StrategyAgent", "role": "strategy", "message": "No active project", "type": "error"}]
    msg = f"**Project Goals ({len(p.goals)})**\n\n"
    for g in p.goals:
        msg += f"**{g.title}** [{g.status}] ({g.progress_pct:.0f}%)\n"
        if g.description:
            msg += f"  {g.description}\n"
        if g.measurable_target:
            msg += f"  Target: {g.measurable_target}\n"
        if g.deadline:
            msg += f"  Deadline: {g.deadline}\n"
        msg += "\n"
    return [{"agent": "StrategyAgent", "role": "strategy", "message": msg, "type": "goals"}]


def _get_targets() -> list[dict]:
    p = _orch.active_project
    if not p:
        return [{"agent": "ForecastAgent", "role": "forecast", "message": "No active project", "type": "error"}]
    msg = f"**Project Targets ({len(p.targets)})**\n\n"
    for t in p.targets:
        bar_filled = int(t.progress_pct / 100 * 20)
        bar = "█" * bar_filled + "░" * (20 - bar_filled)
        msg += f"**{t.name}**\n"
        msg += f"  [{bar}] {t.progress_pct:.1f}%  ({t.current_value}/{t.target_value} {t.unit})\n"
        if t.deadline:
            msg += f"  Deadline: {t.deadline}\n"
        msg += "\n"
    return [{"agent": "ForecastAgent", "role": "forecast", "message": msg, "type": "targets"}]


def _get_forecast() -> list[dict]:
    agent = _orch.get_agent(AgentRole.FORECAST)
    p = _orch.active_project
    if not agent or not p:
        return [{"agent": "ForecastAgent", "role": "forecast", "message": "No active project or forecast agent", "type": "error"}]
    analysis = agent.analyse_project(p.to_dict())
    msg = f"**Forecast Report**\n\n"
    msg += f"Task velocity: {analysis.get('task_velocity', 0):.0%}\n"
    msg += f"Tasks remaining: {analysis.get('tasks_remaining', 0)}\n\n"
    for f in analysis.get("target_forecasts", []):
        status_icon = "✓" if f.get("on_track") else "✗"
        msg += f"  {status_icon} **{f.get('target_name', '?')}**: {f.get('projected_completion', '?')}\n"
        msg += f"    {f.get('recommendation', '')}\n"
    msg += "\n**Scenarios:**\n"
    for name, data in analysis.get("scenarios", {}).items():
        msg += f"  {name.title()}: {data.get('summary', '')}\n"
    risks = analysis.get("risk_flags", [])
    if risks:
        msg += "\n**Risk Flags:**\n"
        for r in risks:
            msg += f"  [{r.get('severity', '?').upper()}] {r.get('description', '')}\n"
    return [{"agent": "ForecastAgent", "role": "forecast", "message": msg, "type": "forecast"}]


def _get_quality() -> list[dict]:
    agent = _orch.get_agent(AgentRole.QA)
    p = _orch.active_project
    if not agent or not p:
        return [{"agent": "QAAgent", "role": "qa", "message": "No active project or QA agent", "type": "error"}]
    analysis = agent.analyse_project(p.to_dict())
    quality = analysis.get("quality_score", {})
    msg = f"**Quality Report**\n\n"
    msg += f"Quality Score: **{quality.get('score', 0)}/100**\n\n"
    msg += "Breakdown:\n"
    for k, v in quality.get("breakdown", {}).items():
        msg += f"  {k}: {v}\n"
    msg += f"\nOpen issues: {analysis.get('open_issues', 0)}\n"
    msg += f"Tests run: {analysis.get('total_tests_run', 0)}\n"
    return [{"agent": "QAAgent", "role": "qa", "message": msg, "type": "quality"}]


def _get_research() -> list[dict]:
    agent = _orch.get_agent(AgentRole.RESEARCH)
    p = _orch.active_project
    if not agent or not p:
        return [{"agent": "ResearchAgent", "role": "research", "message": "No active project", "type": "error"}]
    analysis = agent.analyse_project(p.to_dict())
    msg = f"**Research Report**\n\n"
    msg += f"Market data points: {analysis.get('total_market_data_points', 0)}\n"
    msg += f"Research notes: {analysis.get('total_research_notes', 0)}\n"
    insights = analysis.get("insights", [])
    if insights:
        msg += "\n**Insights:**\n"
        for i in insights:
            msg += f"  [{i.get('priority', 'medium').upper()}] {i.get('area', '')}: {i.get('finding', '')}\n"
    recs = analysis.get("research_recommendations", [])
    if recs:
        msg += "\n**Recommendations:**\n"
        for r in recs:
            msg += f"  - {r.get('topic', '')}: {r.get('reason', '')}\n"
    return [{"agent": "ResearchAgent", "role": "research", "message": msg, "type": "research"}]


def _get_resources() -> list[dict]:
    agent = _orch.get_agent(AgentRole.RESOURCE)
    p = _orch.active_project
    if not agent or not p:
        return [{"agent": "ResourceAgent", "role": "resource", "message": "No active project", "type": "error"}]
    analysis = agent.analyse_project(p.to_dict())
    msg = f"**Resources & Integrations**\n\n"
    msg += f"Total resources: {analysis.get('total_resources', 0)}\n"
    msg += f"Total integrations: {analysis.get('total_integrations', 0)}\n"
    gaps = analysis.get("resource_gaps", [])
    if gaps:
        msg += "\n**Gaps:**\n"
        for g in gaps:
            msg += f"  ✗ {g.get('area', '')}: {g.get('description', '')}\n"
    recs = analysis.get("recommendations", [])
    if recs:
        msg += "\n**Recommendations:**\n"
        for r in recs:
            msg += f"  → {r.get('name', '')}: {r.get('purpose', '')}\n"
    return [{"agent": "ResourceAgent", "role": "resource", "message": msg, "type": "resources"}]


def _get_strategies() -> list[dict]:
    p = _orch.active_project
    if not p:
        return [{"agent": "StrategyAgent", "role": "strategy", "message": "No active project", "type": "error"}]
    msg = f"**Active Strategies ({len(p.strategies)})**\n\n"
    for s in p.strategies:
        msg += f"**{s['title']}**\n"
        msg += f"  {s['description'][:150]}...\n"
        actions = s.get("actions", [])
        if actions:
            for a in actions[:4]:
                msg += f"    - {a}\n"
        msg += "\n"
    return [{"agent": "StrategyAgent", "role": "strategy", "message": msg, "type": "strategies"}]


def _get_acp_status() -> list[dict]:
    stats = _acp.stats()
    agents = _acp.list_agents()
    msg = f"**ACP - External Agent Communication**\n\n"
    msg += f"Registered agents: {stats.get('registered_agents', 0)}\n"
    msg += f"Total messages: {stats.get('total_messages', 0)}\n"
    msg += f"Pending responses: {stats.get('pending_responses', 0)}\n"
    if agents:
        msg += "\n**External Agents:**\n"
        for a in agents:
            caps = ", ".join(a.get("capabilities", [])[:3])
            msg += f"  **{a['name']}** ({a.get('agent_type', '?')}) [{a.get('status', '?')}]\n"
            msg += f"    Capabilities: {caps}\n"
    return [{"agent": "Orchestrator", "role": "orchestrator", "message": msg, "type": "acp"}]


def _get_plans() -> list[dict]:
    agent = _orch.get_agent(AgentRole.STRATEGY)
    p = _orch.active_project
    if not agent or not p:
        return [{"agent": "StrategyAgent", "role": "strategy", "message": "No active project", "type": "error"}]
    plans = agent.generate_plan(p.to_dict())
    msg = "**Strategic Plans**\n\n"
    for plan in plans:
        msg += f"**{plan['strategy']}**\n"
        for phase in plan.get("phases", []):
            msg += f"  Phase {phase['phase']}: {phase['name']}\n"
            for task in phase.get("tasks", []):
                msg += f"    - {task}\n"
        msg += "\n"
    return [{"agent": "StrategyAgent", "role": "strategy", "message": msg, "type": "plans"}]


def _help_text() -> str:
    return """**Available Commands:**

**Project & Status**
  `status` - Team and project overview
  `project` - Project details
  `goals` - Show all goals
  `targets` - Show all targets with progress bars
  `strategies` - Show active strategies
  `tasks` - Full task board

**Agent Reports**
  `forecast` - Forecast and risk report
  `quality` / `qa` - Quality score and issues
  `research` - Research findings and recommendations
  `resources` - Tools, integrations, and gaps
  `plan` - Strategic plans for all goals

**Execution**
  `run cycle` - Run full orchestration cycle
  `run <agent>` - Run a specific agent (strategy/research/operations/forecast/qa/resource)

**Approvals**
  `approvals` - Show pending approvals
  `approve <id>` - Approve an action
  `reject <id>` - Reject an action
  `approve all` - Approve everything pending

**Communication**
  `acp` - External agent (OpenClaw/PaperClip) status
  Any other text - sends a message to the entire team

"""


# --- Flask Routes -----------------------------------------------------------

@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    _init_team()
    data = request.get_json()
    user_msg = data.get("message", "").strip()
    if not user_msg:
        return jsonify({"error": "Empty message"}), 400

    # Log user message
    _chat_log.append({
        "sender": "user",
        "message": user_msg,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    # Get agent responses
    responses = _agent_response(user_msg)

    # Log agent responses
    for r in responses:
        _chat_log.append({
            "sender": r["agent"],
            "role": r["role"],
            "message": r["message"],
            "type": r.get("type", "info"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    return jsonify({"responses": responses})


@app.route("/api/status")
def api_status():
    _init_team()
    return jsonify(_orch.team_status())


@app.route("/api/project")
def api_project():
    _init_team()
    p = _orch.active_project
    if p:
        return jsonify(p.to_dict())
    return jsonify({"error": "No active project"}), 404


@app.route("/api/history")
def api_history():
    return jsonify({"messages": _chat_log[-100:]})


@app.route("/api/notifications")
def api_notifications():
    _init_team()
    return jsonify({
        "notifications": _comm.get_notifications(unread_only=True),
        "pending_approvals": len(_comm.get_pending_approvals()),
    })


def run_server(host="0.0.0.0", port=5000, debug=False):
    """Launch the web interface."""
    _init_team()
    print(f"\n  Agent Team Chat Interface running at http://localhost:{port}\n")
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    run_server()
