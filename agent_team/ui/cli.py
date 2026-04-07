"""
CLI User Interface - Interactive command-line interface for direct
communication with the agent team at all times.

Commands:
  status            - Show team and project status
  project           - Show detailed project info
  agents            - List all agents and their status
  goals             - Show project goals
  targets           - Show project targets
  tasks             - Show task board
  approvals         - Show pending approvals
  approve <id>      - Approve a pending action
  reject <id>       - Reject a pending action
  approve-all       - Approve all pending actions
  notifications     - Show notifications
  msg <text>        - Send a message to the entire team
  msg:<agent> <txt> - Send message to a specific agent
  run-cycle         - Run one orchestration cycle
  run <agent>       - Run a cycle for a specific agent
  plan              - Show strategic plans for all goals
  forecast          - Show latest forecasts
  research          - Show research findings
  quality           - Show quality report
  resources         - Show resources and integrations
  acp               - Show ACP (external agent) status
  acp:register      - Register a new external agent
  acp:send <agent>  - Send ACP message to external agent
  add-goal          - Add a new goal
  add-target        - Add a new target
  add-task          - Add a new task
  delegate <agent>  - Delegate a task to an agent
  save              - Save project to file
  load              - Load project from file
  new-project       - Create a new project
  help              - Show this help
  quit / exit       - Exit the interface
"""

import json
import sys
from pathlib import Path

from ..core.orchestrator import Orchestrator
from ..core.base_agent import AgentRole
from ..core.communication import CommunicationHub
from ..acp.protocol import ACPHub, ACPMessageType


# ANSI colour helpers
BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
RESET = "\033[0m"
BLUE = "\033[94m"


def _header(text: str) -> str:
    return f"\n{BOLD}{CYAN}{'─' * 60}{RESET}\n{BOLD}{CYAN}  {text}{RESET}\n{BOLD}{CYAN}{'─' * 60}{RESET}"


def _section(text: str) -> str:
    return f"\n{BOLD}{YELLOW}  {text}{RESET}\n{DIM}  {'─' * 40}{RESET}"


def _ok(text: str) -> str:
    return f"  {GREEN}✓{RESET} {text}"


def _warn(text: str) -> str:
    return f"  {YELLOW}!{RESET} {text}"


def _err(text: str) -> str:
    return f"  {RED}✗{RESET} {text}"


def _info(text: str) -> str:
    return f"  {BLUE}→{RESET} {text}"


def _prompt(text: str) -> str:
    return input(f"{BOLD}{MAGENTA}{text}{RESET}")


class CLI:
    """Interactive command-line interface for the agent team."""

    def __init__(self, orchestrator: Orchestrator, comm_hub: CommunicationHub,
                 acp_hub: ACPHub):
        self.orch = orchestrator
        self.comm = comm_hub
        self.acp = acp_hub

    def run(self):
        """Main interactive loop."""
        print(_header("Agent Team - Project Management System"))
        print(_info("Type 'help' for available commands.\n"))

        if not self.orch.active_project:
            print(_warn("No active project. Use 'new-project' to create one."))

        while True:
            try:
                raw = _prompt("\n[agent-team] > ").strip()
                if not raw:
                    continue
                parts = raw.split(maxsplit=1)
                cmd = parts[0].lower()
                args = parts[1] if len(parts) > 1 else ""

                if cmd in ("quit", "exit", "q"):
                    print(_info("Goodbye."))
                    break
                elif cmd == "help":
                    self._help()
                elif cmd == "status":
                    self._status()
                elif cmd == "project":
                    self._project()
                elif cmd == "agents":
                    self._agents()
                elif cmd == "goals":
                    self._goals()
                elif cmd == "targets":
                    self._targets()
                elif cmd == "tasks":
                    self._tasks()
                elif cmd == "approvals":
                    self._approvals()
                elif cmd == "approve":
                    self._approve(args)
                elif cmd == "reject":
                    self._reject(args)
                elif cmd == "approve-all":
                    self._approve_all()
                elif cmd == "notifications":
                    self._notifications()
                elif cmd.startswith("msg:"):
                    agent = cmd.split(":")[1]
                    self._message(args, target=agent)
                elif cmd == "msg":
                    self._message(args)
                elif cmd == "run-cycle":
                    self._run_cycle()
                elif cmd == "run":
                    self._run_agent(args)
                elif cmd == "plan":
                    self._plan()
                elif cmd == "forecast":
                    self._forecast()
                elif cmd == "research":
                    self._research()
                elif cmd == "quality":
                    self._quality()
                elif cmd == "resources":
                    self._resources()
                elif cmd == "acp":
                    self._acp_status()
                elif cmd == "acp:register":
                    self._acp_register()
                elif cmd == "acp:send":
                    self._acp_send(args)
                elif cmd == "add-goal":
                    self._add_goal()
                elif cmd == "add-target":
                    self._add_target()
                elif cmd == "add-task":
                    self._add_task()
                elif cmd == "delegate":
                    self._delegate(args)
                elif cmd == "save":
                    self._save(args)
                elif cmd == "load":
                    self._load(args)
                elif cmd == "new-project":
                    self._new_project()
                else:
                    # Treat as a message to the team
                    self._message(raw)
            except KeyboardInterrupt:
                print(f"\n{_info('Use quit to exit.')}")
            except EOFError:
                print(_info("Goodbye."))
                break
            except Exception as e:
                print(_err(f"Error: {e}"))

    # --- commands -----------------------------------------------------------

    def _help(self):
        print(__doc__)

    def _status(self):
        status = self.orch.team_status()
        print(_header("Team Status"))

        if status.get("active_project"):
            print(f"\n{status['active_project']}")
        else:
            print(_warn("No active project"))

        print(_section("Agents"))
        for role, info in status.get("agents", {}).items():
            state = f"{GREEN}active{RESET}" if info.get("active") else f"{RED}inactive{RESET}"
            print(f"  {BOLD}{role:12s}{RESET}  {state}  actions: {info.get('total_actions', 0)}")

        bus = status.get("bus_stats", {})
        print(_section("Communication"))
        print(f"  Messages: {bus.get('total_messages', 0)}")
        print(f"  Pending approvals: {bus.get('pending_approvals', 0)}")
        print(f"  Cycles run: {status.get('cycle_count', 0)}")

    def _project(self):
        p = self.orch.active_project
        if not p:
            print(_warn("No active project"))
            return
        print(_header(f"Project: {p.name}"))
        print(f"  ID: {p.id}")
        print(f"  Status: {p.status.value}")
        print(f"  Created: {p.created_at}")
        print(f"\n  {BOLD}Outline:{RESET}")
        for line in p.outline.split("\n"):
            print(f"    {line}")
        print(f"\n{p.summary()}")

    def _agents(self):
        print(_header("Agent Roster"))
        for role, agent in self.orch.agents.items():
            state = f"{GREEN}active{RESET}" if agent.active else f"{RED}inactive{RESET}"
            print(f"\n  {BOLD}{agent.name}{RESET} [{state}]")
            print(f"    Capabilities: {', '.join(agent._capabilities[:4])}...")
            print(f"    Actions logged: {len(agent.action_log)}")

    def _goals(self):
        p = self.orch.active_project
        if not p:
            print(_warn("No active project"))
            return
        print(_header("Project Goals"))
        if not p.goals:
            print(_warn("No goals defined. Use 'add-goal' to create one."))
            return
        for g in p.goals:
            print(f"\n  {BOLD}{g.title}{RESET} [{g.status}] ({g.progress_pct:.0f}%)")
            if g.description:
                print(f"    {g.description}")
            if g.measurable_target:
                print(f"    Target: {g.measurable_target}")
            if g.deadline:
                print(f"    Deadline: {g.deadline}")

    def _targets(self):
        p = self.orch.active_project
        if not p:
            print(_warn("No active project"))
            return
        print(_header("Project Targets"))
        if not p.targets:
            print(_warn("No targets defined. Use 'add-target' to create one."))
            return
        for t in p.targets:
            bar_len = 20
            filled = int(t.progress_pct / 100 * bar_len)
            bar = f"{'█' * filled}{'░' * (bar_len - filled)}"
            colour = GREEN if t.progress_pct >= 75 else YELLOW if t.progress_pct >= 25 else RED
            print(f"\n  {BOLD}{t.name}{RESET}")
            print(f"    {colour}{bar} {t.progress_pct:.1f}%{RESET}  ({t.current_value}/{t.target_value} {t.unit})")
            if t.deadline:
                print(f"    Deadline: {t.deadline}")

    def _tasks(self):
        p = self.orch.active_project
        if not p:
            print(_warn("No active project"))
            return
        print(_header("Task Board"))
        for status in ["in_progress", "pending", "blocked", "completed"]:
            tasks = p.get_tasks(status=status)
            if tasks:
                print(_section(f"{status.upper()} ({len(tasks)})"))
                for t in tasks:
                    icon = {"pending": "○", "in_progress": "◔", "completed": "●", "blocked": "⊘"}.get(status, "?")
                    colour = {"pending": DIM, "in_progress": YELLOW, "completed": GREEN, "blocked": RED}.get(status, "")
                    agent = f" [{t.assigned_to}]" if t.assigned_to else ""
                    print(f"  {colour}{icon} {t.title}{agent} (#{t.id}){RESET}")

    def _approvals(self):
        pending = self.comm.get_pending_approvals()
        print(_header(f"Pending Approvals ({len(pending)})"))
        if not pending:
            print(_ok("No pending approvals."))
            return
        for req in pending:
            print(f"\n  {BOLD}{YELLOW}[{req['priority'].upper()}]{RESET} {req['title']}")
            print(f"    From: {req['agent']}")
            print(f"    {req['description'][:100]}")
            print(f"    ID: {req['action_id']}")
            print(f"    → approve {req['action_id']}  /  reject {req['action_id']}")

    def _approve(self, action_id: str):
        if not action_id:
            print(_err("Usage: approve <action_id>"))
            return
        if self.comm.approve(action_id.strip()):
            print(_ok(f"Approved: {action_id}"))
        else:
            print(_err(f"No pending approval found for: {action_id}"))

    def _reject(self, action_id: str):
        if not action_id:
            print(_err("Usage: reject <action_id>"))
            return
        note = _prompt("  Reason (optional): ")
        if self.comm.reject(action_id.strip(), note):
            print(_ok(f"Rejected: {action_id}"))
        else:
            print(_err(f"No pending approval found for: {action_id}"))

    def _approve_all(self):
        count = self.comm.approve_all("Bulk approved by user")
        print(_ok(f"Approved {count} pending requests."))

    def _notifications(self):
        notifs = self.comm.get_notifications()
        print(_header(f"Notifications ({len(notifs)})"))
        for n in notifs[-20:]:
            read_marker = DIM if n.get("read") else ""
            type_colour = {
                "info": BLUE, "warning": YELLOW, "alert": RED, "success": GREEN
            }.get(n.get("notification_type", "info"), "")
            print(f"  {read_marker}{type_colour}[{n['notification_type']}]{RESET} "
                  f"{n['title']}")
            if n.get("body"):
                print(f"    {n['body'][:80]}")
        self.comm.mark_all_read()

    def _message(self, text: str, target: str = "all"):
        if not text:
            text = _prompt("  Message: ")
        self.comm.send_to_team(text, target)
        print(_ok(f"Message sent to {target}."))

    def _run_cycle(self):
        print(_info("Running orchestration cycle..."))
        result = self.orch.run_cycle()
        print(_ok(f"Cycle #{result.get('cycle', '?')} complete."))
        print(f"  Actions executed: {result.get('actions_executed', 0)}")
        print(f"  Pending approval: {result.get('actions_pending_approval', 0)}")
        for role, info in result.get("agent_results", {}).items():
            print(f"  {role}: {info.get('actions_proposed', 0)} actions proposed")

        # Show pending approvals if any
        pending = self.comm.get_pending_approvals()
        if pending:
            print(f"\n{YELLOW}  {len(pending)} actions awaiting your approval. Type 'approvals' to review.{RESET}")

    def _run_agent(self, agent_name: str):
        if not agent_name:
            print(_err("Usage: run <agent_name>"))
            print(f"  Available: {', '.join(r.value for r in AgentRole if r != AgentRole.ORCHESTRATOR)}")
            return
        try:
            role = AgentRole(agent_name.strip().lower())
        except ValueError:
            print(_err(f"Unknown agent: {agent_name}"))
            return
        print(_info(f"Running {role.value} agent cycle..."))
        result = self.orch.run_agent_cycle(role)
        actions = result.get("actions", [])
        print(_ok(f"{result.get('agent', role.value)}: {len(actions)} actions"))
        for a in actions[:5]:
            print(f"    {a.get('title', 'untitled')}")

    def _plan(self):
        p = self.orch.active_project
        agent = self.orch.get_agent(AgentRole.STRATEGY)
        if not p or not agent:
            print(_warn("No active project or strategy agent"))
            return
        plans = agent.generate_plan(p.to_dict())
        print(_header("Strategic Plans"))
        for plan in plans:
            print(f"\n  {BOLD}{plan['strategy']}{RESET}")
            for phase in plan.get("phases", []):
                print(f"    Phase {phase['phase']}: {phase['name']}")
                for task in phase.get("tasks", []):
                    print(f"      - {task}")

    def _forecast(self):
        agent = self.orch.get_agent(AgentRole.FORECAST)
        p = self.orch.active_project
        if not agent or not p:
            print(_warn("No active project or forecast agent"))
            return
        analysis = agent.analyse_project(p.to_dict())
        print(_header("Forecast Report"))
        print(f"  Task velocity: {analysis.get('task_velocity', 0):.0%}")
        print(f"  Tasks remaining: {analysis.get('tasks_remaining', 0)}")

        print(_section("Target Forecasts"))
        for f in analysis.get("target_forecasts", []):
            colour = GREEN if f.get("on_track") else RED
            print(f"  {colour}{f.get('target_name', '?')}: {f.get('projected_completion', '?')}{RESET}")
            print(f"    {f.get('recommendation', '')}")

        print(_section("Scenarios"))
        for scenario, data in analysis.get("scenarios", {}).items():
            print(f"  {BOLD}{scenario.title()}{RESET}: {data.get('summary', '')}")

        risks = analysis.get("risk_flags", [])
        if risks:
            print(_section("Risk Flags"))
            for r in risks:
                print(f"  {RED}[{r.get('severity', '?').upper()}]{RESET} {r.get('description', '')}")

    def _research(self):
        agent = self.orch.get_agent(AgentRole.RESEARCH)
        p = self.orch.active_project
        if not agent or not p:
            print(_warn("No active project or research agent"))
            return
        analysis = agent.analyse_project(p.to_dict())
        print(_header("Research Report"))
        print(f"  Market data points: {analysis.get('total_market_data_points', 0)}")
        print(f"  Research notes: {analysis.get('total_research_notes', 0)}")

        insights = analysis.get("insights", [])
        if insights:
            print(_section("Insights"))
            for i in insights:
                print(f"  [{i.get('priority', 'medium').upper()}] {i.get('area', '')}")
                print(f"    {i.get('finding', '')}")

        recs = analysis.get("research_recommendations", [])
        if recs:
            print(_section("Research Recommendations"))
            for r in recs:
                print(f"  - {r.get('topic', '')}: {r.get('reason', '')}")

    def _quality(self):
        agent = self.orch.get_agent(AgentRole.QA)
        p = self.orch.active_project
        if not agent or not p:
            print(_warn("No active project or QA agent"))
            return
        analysis = agent.analyse_project(p.to_dict())
        print(_header("Quality Report"))
        quality = analysis.get("quality_score", {})
        score = quality.get("score", 0)
        colour = GREEN if score >= 75 else YELLOW if score >= 50 else RED
        print(f"\n  {BOLD}Quality Score: {colour}{score}/100{RESET}")
        breakdown = quality.get("breakdown", {})
        for k, v in breakdown.items():
            print(f"    {k}: {v}")
        print(f"\n  Open issues: {analysis.get('open_issues', 0)}")
        print(f"  Tests run: {analysis.get('total_tests_run', 0)}")

    def _resources(self):
        agent = self.orch.get_agent(AgentRole.RESOURCE)
        p = self.orch.active_project
        if not agent or not p:
            print(_warn("No active project or resource agent"))
            return
        analysis = agent.analyse_project(p.to_dict())
        print(_header("Resources & Integrations"))
        print(f"  Total resources: {analysis.get('total_resources', 0)}")
        print(f"  Total integrations: {analysis.get('total_integrations', 0)}")

        gaps = analysis.get("resource_gaps", [])
        if gaps:
            print(_section("Resource Gaps"))
            for g in gaps:
                print(f"  {RED}✗{RESET} {g.get('area', '')}: {g.get('description', '')}")

        recs = analysis.get("recommendations", [])
        if recs:
            print(_section("Tool Recommendations"))
            for r in recs:
                print(f"  → {r.get('name', '')}: {r.get('purpose', '')}")

    def _acp_status(self):
        stats = self.acp.stats()
        print(_header("ACP - External Agent Communication"))
        print(f"  Registered agents: {stats.get('registered_agents', 0)}")
        print(f"  Total messages: {stats.get('total_messages', 0)}")
        print(f"  Pending responses: {stats.get('pending_responses', 0)}")

        agents = self.acp.list_agents()
        if agents:
            print(_section("Registered External Agents"))
            for a in agents:
                status_colour = GREEN if a.get("status") == "active" else YELLOW
                print(f"  {BOLD}{a['name']}{RESET} ({a.get('agent_type', '?')}) "
                      f"[{status_colour}{a.get('status', '?')}{RESET}]")
                caps = a.get("capabilities", [])
                if caps:
                    print(f"    Capabilities: {', '.join(caps[:5])}")
        else:
            print(_warn("No external agents registered. Use 'acp:register' to add one."))

    def _acp_register(self):
        name = _prompt("  Agent name: ")
        agent_type = _prompt("  Agent type (e.g. openclaw, paperclip): ")
        caps = _prompt("  Capabilities (comma-separated): ")
        endpoint = _prompt("  Endpoint (optional): ")
        capabilities = [c.strip() for c in caps.split(",") if c.strip()]
        agent = self.acp.register_agent(name, agent_type, capabilities, endpoint)
        print(_ok(f"Registered: {agent.name} ({agent.agent_type})"))

    def _acp_send(self, target: str):
        if not target:
            print(_err("Usage: acp:send <agent_name>"))
            return
        target = target.strip()
        if target not in self.acp.external_agents:
            print(_err(f"Unknown agent: {target}"))
            return
        subject = _prompt("  Subject: ")
        body = _prompt("  Body: ")
        self.acp.send_message(
            target_agent=target,
            message_type=ACPMessageType.DATA_SHARE,
            subject=subject,
            body=body,
        )
        print(_ok(f"Message sent to {target}."))

    def _add_goal(self):
        p = self.orch.active_project
        if not p:
            print(_warn("No active project"))
            return
        title = _prompt("  Goal title: ")
        desc = _prompt("  Description: ")
        target = _prompt("  Measurable target: ")
        deadline = _prompt("  Deadline (YYYY-MM-DD): ")
        g = p.add_goal(title, desc, target, deadline)
        print(_ok(f"Goal added: {g.title} (#{g.id})"))

    def _add_target(self):
        p = self.orch.active_project
        if not p:
            print(_warn("No active project"))
            return
        name = _prompt("  Target name: ")
        metric = _prompt("  Metric: ")
        target_val = float(_prompt("  Target value: ") or "0")
        unit = _prompt("  Unit: ")
        deadline = _prompt("  Deadline (YYYY-MM-DD): ")
        t = p.add_target(name, metric, target_val, unit, deadline)
        print(_ok(f"Target added: {t.name} (#{t.id})"))

    def _add_task(self):
        p = self.orch.active_project
        if not p:
            print(_warn("No active project"))
            return
        title = _prompt("  Task title: ")
        desc = _prompt("  Description: ")
        agent = _prompt(f"  Assign to ({', '.join(r.value for r in AgentRole if r != AgentRole.ORCHESTRATOR)}): ")
        priority = _prompt("  Priority (low/medium/high/critical): ") or "medium"
        t = p.add_task(title, desc, agent.strip(), priority.strip())
        print(_ok(f"Task added: {t.title} (#{t.id})"))

    def _delegate(self, agent_name: str):
        if not agent_name:
            print(_err("Usage: delegate <agent_name>"))
            return
        try:
            role = AgentRole(agent_name.strip().lower())
        except ValueError:
            print(_err(f"Unknown agent: {agent_name}"))
            return
        title = _prompt("  Task title: ")
        desc = _prompt("  Description: ")
        priority = _prompt("  Priority (low/medium/high/critical): ") or "medium"
        result = self.orch.delegate_task(role, title, desc, priority.strip())
        print(_ok(f"Delegated to {agent_name}: {result.get('title', title)}"))

    def _save(self, path: str):
        p = self.orch.active_project
        if not p:
            print(_warn("No active project"))
            return
        path = path.strip() or f"project_{p.id}.json"
        p.save(path)
        print(_ok(f"Project saved to {path}"))

    def _load(self, path: str):
        if not path:
            path = _prompt("  File path: ")
        path = path.strip()
        if not Path(path).exists():
            print(_err(f"File not found: {path}"))
            return
        project = self.orch.load_project(path)
        print(_ok(f"Loaded project: {project.name} (#{project.id})"))

    def _new_project(self):
        name = _prompt("  Project name: ")
        print("  Enter project outline (empty line to finish):")
        lines = []
        while True:
            line = _prompt("    ")
            if not line:
                break
            lines.append(line)
        outline = "\n".join(lines)

        project = self.orch.create_project(name, outline)
        project.status = project.status.__class__("active")

        print(_ok(f"Project created: {project.name} (#{project.id})"))
        print(_info("Add goals with 'add-goal' and targets with 'add-target'."))
