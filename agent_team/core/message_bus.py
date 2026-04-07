"""
Message Bus - Central communication backbone for the agent team.

All inter-agent messages, user messages, and external ACP messages
flow through this bus. Supports subscriptions, routing, and history.
"""

import logging
from datetime import datetime, timezone
from collections import defaultdict
from typing import Callable, Any

from .base_agent import AgentMessage


class MessageBus:
    """Publish-subscribe message bus for agent team communication."""

    def __init__(self):
        self.logger = logging.getLogger("MessageBus")
        self._subscribers: dict[str, list[Callable]] = defaultdict(list)
        self._history: list[AgentMessage] = []
        self._user_inbox: list[AgentMessage] = []
        self._pending_approvals: list[AgentMessage] = []

    # --- pub/sub -------------------------------------------------------------

    def subscribe(self, channel: str, handler: Callable):
        """Subscribe a handler to a channel (agent role name, 'user', or 'all')."""
        self._subscribers[channel].append(handler)

    def unsubscribe(self, channel: str, handler: Callable):
        if handler in self._subscribers[channel]:
            self._subscribers[channel].remove(handler)

    def publish(self, message: AgentMessage):
        """Publish a message to the bus."""
        self._history.append(message)

        # Route to user inbox
        if message.recipient in ("user", "all"):
            self._user_inbox.append(message)

        # Track approval requests
        if message.message_type == "approval":
            self._pending_approvals.append(message)

        # Deliver to subscribers
        targets = set()
        targets.update(self._subscribers.get(message.recipient, []))
        targets.update(self._subscribers.get("all", []))
        for handler in targets:
            try:
                handler(message)
            except Exception as e:
                self.logger.error(f"Handler error on {message.subject}: {e}")

    # --- querying ------------------------------------------------------------

    def get_user_inbox(self, unread_only: bool = False) -> list[AgentMessage]:
        return list(self._user_inbox)

    def get_pending_approvals(self) -> list[AgentMessage]:
        return [m for m in self._pending_approvals
                if m.payload.get("approval_status", "pending") == "pending"]

    def get_history(self, limit: int = 50, sender: str | None = None,
                    recipient: str | None = None) -> list[AgentMessage]:
        msgs = self._history
        if sender:
            msgs = [m for m in msgs if m.sender == sender]
        if recipient:
            msgs = [m for m in msgs if m.recipient == recipient]
        return msgs[-limit:]

    def clear_user_inbox(self):
        self._user_inbox.clear()

    def resolve_approval(self, action_id: str, approved: bool) -> bool:
        """Resolve a pending approval by action_id."""
        for msg in self._pending_approvals:
            if msg.payload.get("action_id") == action_id:
                msg.payload["approval_status"] = "approved" if approved else "rejected"
                # Notify the originating agent
                self.publish(AgentMessage(
                    sender="user",
                    recipient=msg.sender,
                    subject=f"Approval {'granted' if approved else 'denied'}: {msg.subject}",
                    body=f"Action {action_id} has been {'approved' if approved else 'rejected'}.",
                    message_type="info",
                    payload={"action_id": action_id, "approved": approved},
                ))
                return True
        return False

    def stats(self) -> dict:
        return {
            "total_messages": len(self._history),
            "user_inbox_size": len(self._user_inbox),
            "pending_approvals": len(self.get_pending_approvals()),
            "subscriber_channels": list(self._subscribers.keys()),
        }
