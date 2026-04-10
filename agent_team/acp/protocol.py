"""
Agent Communication Protocol (ACP) - Enables autonomous communication
between the agent team and external agents (OpenClaw, PaperClip, etc.)

The ACP provides:
- Agent discovery and registration
- Standardised message format for cross-agent communication
- Task delegation to/from external agents
- Shared context and data exchange
- Heartbeat and health monitoring
- Capability negotiation
"""

import uuid
import json
import logging
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable


class ACPMessageType(Enum):
    HANDSHAKE = "handshake"
    HEARTBEAT = "heartbeat"
    TASK_REQUEST = "task_request"
    TASK_RESPONSE = "task_response"
    DATA_SHARE = "data_share"
    CAPABILITY_QUERY = "capability_query"
    CAPABILITY_RESPONSE = "capability_response"
    STATUS_UPDATE = "status_update"
    ALERT = "alert"
    SHUTDOWN = "shutdown"


@dataclass
class ACPMessage:
    """Standardised message for inter-agent communication."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    source_agent: str = ""
    target_agent: str = ""
    message_type: ACPMessageType = ACPMessageType.DATA_SHARE
    subject: str = ""
    body: str = ""
    payload: dict = field(default_factory=dict)
    correlation_id: str | None = None  # links request/response pairs
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    ttl: int = 300  # message expires after N seconds

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source_agent": self.source_agent,
            "target_agent": self.target_agent,
            "message_type": self.message_type.value,
            "subject": self.subject,
            "body": self.body,
            "payload": self.payload,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp,
            "ttl": self.ttl,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: dict) -> "ACPMessage":
        data["message_type"] = ACPMessageType(data.get("message_type", "data_share"))
        return cls(**data)


@dataclass
class ExternalAgent:
    """Representation of an external agent that the team can communicate with."""
    name: str
    agent_type: str  # e.g. "openclaw", "paperclip"
    capabilities: list[str] = field(default_factory=list)
    endpoint: str = ""  # how to reach this agent
    status: str = "registered"  # registered, active, inactive, error
    last_heartbeat: str = ""
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return self.__dict__.copy()


class ACPHub:
    """
    Central ACP hub that manages communication between the internal
    agent team and external agents (OpenClaw, PaperClip, etc.)
    """

    def __init__(self, team_name: str = "AgentTeam"):
        self.team_name = team_name
        self.logger = logging.getLogger("ACPHub")
        self.external_agents: dict[str, ExternalAgent] = {}
        self.message_log: list[ACPMessage] = []
        self.pending_responses: dict[str, ACPMessage] = {}  # correlation_id -> request
        self.handlers: dict[ACPMessageType, list[Callable]] = {}
        self.inbox: list[ACPMessage] = []
        self.outbox: list[ACPMessage] = []

        # File-based message exchange directory
        self.exchange_dir: Path | None = None

    # --- agent registration --------------------------------------------------

    def register_agent(self, name: str, agent_type: str,
                       capabilities: list[str] | None = None,
                       endpoint: str = "",
                       metadata: dict | None = None) -> ExternalAgent:
        """Register an external agent for communication."""
        agent = ExternalAgent(
            name=name,
            agent_type=agent_type,
            capabilities=capabilities or [],
            endpoint=endpoint,
            metadata=metadata or {},
        )
        self.external_agents[name] = agent
        self.logger.info(f"Registered external agent: {name} ({agent_type})")

        # Send handshake
        self.send_message(
            target_agent=name,
            message_type=ACPMessageType.HANDSHAKE,
            subject=f"Handshake from {self.team_name}",
            body=f"Agent team '{self.team_name}' is ready to collaborate.",
            payload={"team_capabilities": self._get_team_capabilities()},
        )
        return agent

    def deregister_agent(self, name: str):
        if name in self.external_agents:
            self.send_message(
                target_agent=name,
                message_type=ACPMessageType.SHUTDOWN,
                subject="Disconnecting",
                body=f"Agent team '{self.team_name}' is disconnecting.",
            )
            del self.external_agents[name]

    def get_agent(self, name: str) -> ExternalAgent | None:
        return self.external_agents.get(name)

    def list_agents(self) -> list[dict]:
        return [a.to_dict() for a in self.external_agents.values()]

    # --- messaging -----------------------------------------------------------

    def send_message(self, target_agent: str,
                     message_type: ACPMessageType,
                     subject: str, body: str = "",
                     payload: dict | None = None,
                     correlation_id: str | None = None) -> ACPMessage:
        """Send a message to an external agent."""
        msg = ACPMessage(
            source_agent=self.team_name,
            target_agent=target_agent,
            message_type=message_type,
            subject=subject,
            body=body,
            payload=payload or {},
            correlation_id=correlation_id,
        )
        self.message_log.append(msg)
        self.outbox.append(msg)

        # Write to exchange directory if configured
        if self.exchange_dir:
            self._write_to_exchange(msg)

        self.logger.info(f"ACP -> {target_agent}: {subject}")
        return msg

    def request_task(self, target_agent: str, task_title: str,
                     task_description: str = "",
                     task_data: dict | None = None) -> ACPMessage:
        """Send a task request to an external agent."""
        correlation_id = uuid.uuid4().hex[:12]
        msg = self.send_message(
            target_agent=target_agent,
            message_type=ACPMessageType.TASK_REQUEST,
            subject=f"Task: {task_title}",
            body=task_description,
            payload={"task_title": task_title, "task_data": task_data or {}},
            correlation_id=correlation_id,
        )
        self.pending_responses[correlation_id] = msg
        return msg

    def respond_to_task(self, correlation_id: str, target_agent: str,
                        result: str, data: dict | None = None) -> ACPMessage:
        """Respond to a task request from an external agent."""
        return self.send_message(
            target_agent=target_agent,
            message_type=ACPMessageType.TASK_RESPONSE,
            subject=f"Task response",
            body=result,
            payload={"result": result, "data": data or {}},
            correlation_id=correlation_id,
        )

    def share_data(self, target_agent: str, data_type: str,
                   data: dict) -> ACPMessage:
        """Share data with an external agent."""
        return self.send_message(
            target_agent=target_agent,
            message_type=ACPMessageType.DATA_SHARE,
            subject=f"Data share: {data_type}",
            body=f"Sharing {data_type} data",
            payload={"data_type": data_type, "data": data},
        )

    def query_capabilities(self, target_agent: str) -> ACPMessage:
        """Ask an external agent what it can do."""
        return self.send_message(
            target_agent=target_agent,
            message_type=ACPMessageType.CAPABILITY_QUERY,
            subject="Capability query",
            body="What capabilities do you offer?",
        )

    # --- receiving -----------------------------------------------------------

    def receive_message(self, message_data: dict) -> ACPMessage:
        """Process an incoming message from an external agent."""
        msg = ACPMessage.from_dict(message_data)
        self.inbox.append(msg)
        self.message_log.append(msg)

        # Handle correlation (response to our request)
        if msg.correlation_id and msg.correlation_id in self.pending_responses:
            del self.pending_responses[msg.correlation_id]

        # Dispatch to registered handlers
        handlers = self.handlers.get(msg.message_type, [])
        for handler in handlers:
            try:
                handler(msg)
            except Exception as e:
                self.logger.error(f"ACP handler error: {e}")

        # Update heartbeat
        if msg.source_agent in self.external_agents:
            self.external_agents[msg.source_agent].last_heartbeat = msg.timestamp
            self.external_agents[msg.source_agent].status = "active"

        return msg

    def on_message(self, message_type: ACPMessageType, handler: Callable):
        """Register a handler for a specific message type."""
        self.handlers.setdefault(message_type, []).append(handler)

    # --- exchange directory (file-based IPC) ---------------------------------

    def setup_exchange(self, directory: str | Path):
        """Set up a file-based message exchange directory for IPC."""
        self.exchange_dir = Path(directory)
        self.exchange_dir.mkdir(parents=True, exist_ok=True)
        (self.exchange_dir / "inbox").mkdir(exist_ok=True)
        (self.exchange_dir / "outbox").mkdir(exist_ok=True)
        self.logger.info(f"ACP exchange directory: {self.exchange_dir}")

    def _write_to_exchange(self, msg: ACPMessage):
        if not self.exchange_dir:
            return
        outbox = self.exchange_dir / "outbox"
        filename = f"{msg.timestamp.replace(':', '-')}_{msg.id}.json"
        (outbox / filename).write_text(msg.to_json())

    def poll_exchange(self) -> list[ACPMessage]:
        """Check the exchange inbox for new messages."""
        if not self.exchange_dir:
            return []
        inbox = self.exchange_dir / "inbox"
        messages = []
        for f in sorted(inbox.glob("*.json")):
            try:
                data = json.loads(f.read_text())
                msg = self.receive_message(data)
                messages.append(msg)
                f.unlink()  # consume the message
            except Exception as e:
                self.logger.error(f"Failed to read ACP message {f}: {e}")
        return messages

    # --- health & status -----------------------------------------------------

    def send_heartbeat(self, target_agent: str):
        self.send_message(
            target_agent=target_agent,
            message_type=ACPMessageType.HEARTBEAT,
            subject="heartbeat",
            body="alive",
        )

    def broadcast_status(self, status: dict):
        """Broadcast status to all registered external agents."""
        for name in self.external_agents:
            self.send_message(
                target_agent=name,
                message_type=ACPMessageType.STATUS_UPDATE,
                subject="Team status update",
                payload=status,
            )

    def stats(self) -> dict:
        return {
            "registered_agents": len(self.external_agents),
            "agents": list(self.external_agents.keys()),
            "total_messages": len(self.message_log),
            "inbox_size": len(self.inbox),
            "outbox_size": len(self.outbox),
            "pending_responses": len(self.pending_responses),
        }

    # --- internal ------------------------------------------------------------

    def _get_team_capabilities(self) -> list[str]:
        return [
            "strategic_planning",
            "market_research",
            "operations_management",
            "forecasting",
            "quality_assurance",
            "resource_management",
            "project_management",
        ]
