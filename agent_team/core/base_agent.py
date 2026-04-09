"""
Base Agent - Foundation class for all agents in the team.

Every agent has an identity, a role, a message bus connection, a log,
and the ability to propose actions that require user approval.
"""

import uuid
import json
import logging
from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Optional


class AgentRole(Enum):
    STRATEGY = "strategy"
    RESEARCH = "research"
    OPERATIONS = "operations"
    FORECAST = "forecast"
    QA = "qa"
    RESOURCE = "resource"
    ORCHESTRATOR = "orchestrator"


class ActionPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ApprovalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    AUTO_APPROVED = "auto_approved"


@dataclass
class AgentAction:
    """An action proposed or executed by an agent."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    agent_role: AgentRole = AgentRole.OPERATIONS
    title: str = ""
    description: str = ""
    priority: ActionPriority = ActionPriority.MEDIUM
    requires_approval: bool = False
    approval_status: ApprovalStatus = ApprovalStatus.AUTO_APPROVED
    payload: dict = field(default_factory=dict)
    result: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "agent_role": self.agent_role.value,
            "title": self.title,
            "description": self.description,
            "priority": self.priority.value,
            "requires_approval": self.requires_approval,
            "approval_status": self.approval_status.value,
            "payload": self.payload,
            "result": self.result,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
        }


@dataclass
class AgentMessage:
    """Inter-agent or agent-to-user message."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    sender: str = ""
    recipient: str = "all"  # agent role, "user", or "all"
    subject: str = ""
    body: str = ""
    message_type: str = "info"  # info, request, approval, alert, report
    payload: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "sender": self.sender,
            "recipient": self.recipient,
            "subject": self.subject,
            "body": self.body,
            "message_type": self.message_type,
            "payload": self.payload,
            "timestamp": self.timestamp,
        }


class BaseAgent:
    """Foundation for every agent on the team."""

    def __init__(self, role: AgentRole, team_bus: Any = None):
        self.role = role
        self.name = f"{role.value.title()}Agent"
        self.id = uuid.uuid4().hex[:8]
        self.team_bus = team_bus  # set by orchestrator
        self.logger = logging.getLogger(self.name)
        self.action_log: list[AgentAction] = []
        self.active = True
        self._capabilities: list[str] = []

    # --- lifecycle -----------------------------------------------------------

    def activate(self):
        self.active = True
        self.logger.info(f"{self.name} activated")

    def deactivate(self):
        self.active = False
        self.logger.info(f"{self.name} deactivated")

    # --- messaging -----------------------------------------------------------

    def send_message(self, recipient: str, subject: str, body: str,
                     message_type: str = "info", payload: dict | None = None):
        msg = AgentMessage(
            sender=self.role.value,
            recipient=recipient,
            subject=subject,
            body=body,
            message_type=message_type,
            payload=payload or {},
        )
        if self.team_bus:
            self.team_bus.publish(msg)
        return msg

    def request_approval(self, title: str, description: str,
                         payload: dict | None = None,
                         priority: ActionPriority = ActionPriority.HIGH) -> AgentAction:
        action = AgentAction(
            agent_role=self.role,
            title=title,
            description=description,
            priority=priority,
            requires_approval=True,
            approval_status=ApprovalStatus.PENDING,
            payload=payload or {},
        )
        self.action_log.append(action)
        self.send_message(
            recipient="user",
            subject=f"[APPROVAL REQUIRED] {title}",
            body=description,
            message_type="approval",
            payload={"action_id": action.id, **action.to_dict()},
        )
        return action

    # --- execution -----------------------------------------------------------

    def execute_action(self, action: AgentAction) -> AgentAction:
        """Execute an action. Override in subclasses for real work."""
        self.logger.info(f"{self.name} executing: {action.title}")
        action.result = "executed"
        action.completed_at = datetime.now(timezone.utc).isoformat()
        self.action_log.append(action)
        return action

    # --- project interface ----------------------------------------------------

    def analyse_project(self, project: dict) -> dict:
        """Analyse a project from this agent's perspective. Override per role."""
        return {"agent": self.name, "status": "no analysis implemented"}

    def generate_plan(self, project: dict) -> list[dict]:
        """Generate a plan of actions for this agent's domain."""
        return []

    def run_cycle(self, project: dict) -> list[AgentAction]:
        """One autonomous work cycle. Called repeatedly by orchestrator."""
        return []

    # --- reporting -----------------------------------------------------------

    def status_report(self) -> dict:
        return {
            "agent": self.name,
            "role": self.role.value,
            "active": self.active,
            "total_actions": len(self.action_log),
            "capabilities": self._capabilities,
        }

    def __repr__(self):
        return f"<{self.name} id={self.id} active={self.active}>"
