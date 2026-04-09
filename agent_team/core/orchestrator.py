"""
Orchestrator - The brain of the agent team.

Coordinates all agents, manages work cycles, routes decisions,
handles user approvals, and maintains overall project state.
"""

import logging
from datetime import datetime, timezone
from typing import Any

from .base_agent import (
    BaseAgent, AgentRole, AgentAction, AgentMessage,
    ActionPriority, ApprovalStatus,
)
from .message_bus import MessageBus
from .project import Project, ProjectStatus


class Orchestrator:
    """Central coordinator that runs the agent team."""

    def __init__(self):
        self.logger = logging.getLogger("Orchestrator")
        self.bus = MessageBus()
        self.agents: dict[AgentRole, BaseAgent] = {}
        self.projects: dict[str, Project] = {}
        self.active_project_id: str | None = None
        self.cycle_count = 0
        self.running = False

        # Auto-approve actions below this priority threshold
        self.auto_approve_threshold = ActionPriority.MEDIUM

        # Subscribe orchestrator to all messages
        self.bus.subscribe("all", self._handle_message)
        self.bus.subscribe("orchestrator", self._handle_message)

    # --- agent registration --------------------------------------------------

    def register_agent(self, agent: BaseAgent):
        agent.team_bus = self.bus
        self.agents[agent.role] = agent
        self.bus.subscribe(agent.role.value, lambda msg, a=agent: a.send_message(
            "orchestrator", f"ACK: {msg.subject}", "", "info"))
        self.logger.info(f"Registered {agent.name}")

    def get_agent(self, role: AgentRole) -> BaseAgent | None:
        return self.agents.get(role)

    # --- project management --------------------------------------------------

    def create_project(self, name: str, outline: str,
                       goals: list[dict] | None = None,
                       targets: list[dict] | None = None) -> Project:
        project = Project(name=name, outline=outline)
        if goals:
            for g in goals:
                project.add_goal(**g)
        if targets:
            for t in targets:
                project.add_target(**t)
        self.projects[project.id] = project
        self.active_project_id = project.id
        self.bus.publish(AgentMessage(
            sender="orchestrator",
            recipient="all",
            subject=f"New project created: {name}",
            body=outline,
            message_type="info",
            payload={"project_id": project.id},
        ))
        return project

    def load_project(self, path: str) -> Project:
        project = Project.load(path)
        self.projects[project.id] = project
        self.active_project_id = project.id
        return project

    @property
    def active_project(self) -> Project | None:
        if self.active_project_id:
            return self.projects.get(self.active_project_id)
        return None

    # --- orchestration cycle -------------------------------------------------

    def run_cycle(self) -> dict:
        """Run one orchestration cycle across all agents."""
        project = self.active_project
        if not project:
            return {"error": "No active project"}

        self.cycle_count += 1
        cycle_results = {"cycle": self.cycle_count, "agent_results": {}}

        project_dict = project.to_dict()

        # Phase 1: Each agent analyses the project
        analyses = {}
        for role, agent in self.agents.items():
            if agent.active and role != AgentRole.ORCHESTRATOR:
                try:
                    analyses[role.value] = agent.analyse_project(project_dict)
                except Exception as e:
                    self.logger.error(f"{agent.name} analysis failed: {e}")
                    analyses[role.value] = {"error": str(e)}

        # Phase 2: Each agent generates plans / proposes actions
        proposed_actions: list[AgentAction] = []
        for role, agent in self.agents.items():
            if agent.active and role != AgentRole.ORCHESTRATOR:
                try:
                    actions = agent.run_cycle(project_dict)
                    proposed_actions.extend(actions)
                    cycle_results["agent_results"][role.value] = {
                        "actions_proposed": len(actions),
                        "analysis": analyses.get(role.value, {}),
                    }
                except Exception as e:
                    self.logger.error(f"{agent.name} cycle failed: {e}")

        # Phase 3: Process actions (auto-approve or queue for user)
        executed = []
        pending_approval = []
        for action in proposed_actions:
            if action.requires_approval:
                pending_approval.append(action)
            else:
                agent = self.agents.get(action.agent_role)
                if agent:
                    agent.execute_action(action)
                    executed.append(action)

        cycle_results["actions_executed"] = len(executed)
        cycle_results["actions_pending_approval"] = len(pending_approval)
        cycle_results["timestamp"] = datetime.now(timezone.utc).isoformat()

        # Record to project history
        project.action_history.append(cycle_results)

        return cycle_results

    def run_agent_cycle(self, role: AgentRole) -> dict:
        """Run a cycle for a single agent."""
        agent = self.agents.get(role)
        project = self.active_project
        if not agent or not project:
            return {"error": "Agent or project not found"}
        actions = agent.run_cycle(project.to_dict())
        return {
            "agent": agent.name,
            "actions": [a.to_dict() for a in actions],
        }

    # --- approval workflow ---------------------------------------------------

    def approve_action(self, action_id: str) -> bool:
        return self.bus.resolve_approval(action_id, approved=True)

    def reject_action(self, action_id: str) -> bool:
        return self.bus.resolve_approval(action_id, approved=False)

    def get_pending_approvals(self) -> list[dict]:
        return [m.to_dict() for m in self.bus.get_pending_approvals()]

    # --- delegation ----------------------------------------------------------

    def delegate_task(self, role: AgentRole, title: str,
                      description: str = "", priority: str = "medium") -> dict:
        """Create a task and assign it to a specific agent."""
        project = self.active_project
        if not project:
            return {"error": "No active project"}
        task = project.add_task(
            title=title, description=description,
            assigned_to=role.value, priority=priority,
        )
        self.bus.publish(AgentMessage(
            sender="orchestrator",
            recipient=role.value,
            subject=f"New task assigned: {title}",
            body=description,
            message_type="request",
            payload={"task_id": task.id},
        ))
        return task.to_dict()

    # --- reporting -----------------------------------------------------------

    def team_status(self) -> dict:
        return {
            "agents": {r.value: a.status_report() for r, a in self.agents.items()},
            "active_project": self.active_project.summary() if self.active_project else None,
            "cycle_count": self.cycle_count,
            "bus_stats": self.bus.stats(),
        }

    def project_report(self) -> dict:
        project = self.active_project
        if not project:
            return {"error": "No active project"}
        return {
            "summary": project.summary(),
            "details": project.to_dict(),
            "team_status": self.team_status(),
        }

    # --- internal ------------------------------------------------------------

    def _handle_message(self, message: AgentMessage):
        self.logger.debug(f"Bus msg: [{message.sender}] -> [{message.recipient}] {message.subject}")
