"""
Communication Hub - Manages user-facing communication and approval workflows.

Provides a structured way for agents to communicate with the user,
request approvals, send reports, and receive instructions.
"""

import json
import logging
from datetime import datetime, timezone
from dataclasses import dataclass, field

from .message_bus import MessageBus
from .base_agent import AgentMessage


@dataclass
class ApprovalRequest:
    id: str = ""
    action_id: str = ""
    agent: str = ""
    title: str = ""
    description: str = ""
    priority: str = "medium"
    status: str = "pending"  # pending, approved, rejected
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    resolved_at: str | None = None
    resolution_note: str = ""

    def to_dict(self) -> dict:
        return self.__dict__.copy()


@dataclass
class Notification:
    id: str = ""
    agent: str = ""
    title: str = ""
    body: str = ""
    notification_type: str = "info"  # info, warning, alert, success
    read: bool = False
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return self.__dict__.copy()


class CommunicationHub:
    """
    Central hub for all user-facing communication.
    Agents post here; the UI reads from here.
    """

    def __init__(self, bus: MessageBus):
        self.bus = bus
        self.logger = logging.getLogger("CommunicationHub")
        self.notifications: list[Notification] = []
        self.approval_requests: list[ApprovalRequest] = []
        self.conversation_log: list[dict] = []

        # Subscribe to user-bound messages
        self.bus.subscribe("user", self._handle_user_message)

    def _handle_user_message(self, message: AgentMessage):
        """Route agent messages to appropriate notification/approval queues."""
        if message.message_type == "approval":
            req = ApprovalRequest(
                id=message.id,
                action_id=message.payload.get("action_id", ""),
                agent=message.sender,
                title=message.subject,
                description=message.body,
                priority=message.payload.get("priority", "medium"),
            )
            self.approval_requests.append(req)
            self.logger.info(f"New approval request from {message.sender}: {message.subject}")
        else:
            notif = Notification(
                id=message.id,
                agent=message.sender,
                title=message.subject,
                body=message.body,
                notification_type=message.message_type,
            )
            self.notifications.append(notif)

        # Log to conversation
        self.conversation_log.append({
            "from": message.sender,
            "to": "user",
            "subject": message.subject,
            "body": message.body,
            "type": message.message_type,
            "timestamp": message.timestamp,
        })

    # --- user actions --------------------------------------------------------

    def send_to_team(self, message: str, target: str = "all"):
        """Send a message from the user to the team."""
        msg = AgentMessage(
            sender="user",
            recipient=target,
            subject="User message",
            body=message,
            message_type="request",
        )
        self.bus.publish(msg)
        self.conversation_log.append({
            "from": "user",
            "to": target,
            "subject": "User message",
            "body": message,
            "type": "request",
            "timestamp": msg.timestamp,
        })

    def approve(self, request_id: str, note: str = "") -> bool:
        """Approve a pending request."""
        for req in self.approval_requests:
            if (req.id == request_id or req.action_id == request_id) and req.status == "pending":
                req.status = "approved"
                req.resolved_at = datetime.now(timezone.utc).isoformat()
                req.resolution_note = note
                self.bus.resolve_approval(req.action_id, approved=True)
                self.logger.info(f"Approved: {req.title}")
                return True
        return False

    def reject(self, request_id: str, note: str = "") -> bool:
        """Reject a pending request."""
        for req in self.approval_requests:
            if (req.id == request_id or req.action_id == request_id) and req.status == "pending":
                req.status = "rejected"
                req.resolved_at = datetime.now(timezone.utc).isoformat()
                req.resolution_note = note
                self.bus.resolve_approval(req.action_id, approved=False)
                self.logger.info(f"Rejected: {req.title}")
                return True
        return False

    def approve_all(self, note: str = "") -> int:
        """Approve all pending requests."""
        count = 0
        for req in self.approval_requests:
            if req.status == "pending":
                req.status = "approved"
                req.resolved_at = datetime.now(timezone.utc).isoformat()
                req.resolution_note = note
                self.bus.resolve_approval(req.action_id, approved=True)
                count += 1
        return count

    # --- queries -------------------------------------------------------------

    def get_pending_approvals(self) -> list[dict]:
        return [r.to_dict() for r in self.approval_requests if r.status == "pending"]

    def get_notifications(self, unread_only: bool = False) -> list[dict]:
        notifs = self.notifications
        if unread_only:
            notifs = [n for n in notifs if not n.read]
        return [n.to_dict() for n in notifs]

    def mark_read(self, notification_id: str):
        for n in self.notifications:
            if n.id == notification_id:
                n.read = True
                break

    def mark_all_read(self):
        for n in self.notifications:
            n.read = True

    def get_conversation(self, limit: int = 50) -> list[dict]:
        return self.conversation_log[-limit:]

    def stats(self) -> dict:
        return {
            "total_notifications": len(self.notifications),
            "unread_notifications": len([n for n in self.notifications if not n.read]),
            "pending_approvals": len(self.get_pending_approvals()),
            "total_conversations": len(self.conversation_log),
        }
