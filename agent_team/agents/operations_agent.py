"""
Operations Agent - Handles the day-to-day running of the project.

Responsibilities:
- Execute tasks from the project task board
- Manage task dependencies and sequencing
- Track progress and update metrics
- Coordinate between agents for cross-functional tasks
- Handle routine operations and maintenance
- Escalate blockers and issues
"""

from datetime import datetime, timezone
from ..core.base_agent import (
    BaseAgent, AgentRole, AgentAction, ActionPriority,
)


class OperationsAgent(BaseAgent):

    def __init__(self, team_bus=None):
        super().__init__(AgentRole.OPERATIONS, team_bus)
        self._capabilities = [
            "task_execution",
            "dependency_management",
            "progress_tracking",
            "resource_coordination",
            "issue_escalation",
            "daily_operations",
            "workflow_management",
        ]
        self.execution_log: list[dict] = []

    def analyse_project(self, project: dict) -> dict:
        """Analyse operational state of the project."""
        tasks = project.get("tasks", [])

        by_status = {}
        for t in tasks:
            status = t.get("status", "unknown")
            by_status.setdefault(status, []).append(t)

        by_agent = {}
        for t in tasks:
            assigned = t.get("assigned_to", "unassigned")
            by_agent.setdefault(assigned, []).append(t)

        # Find blocked tasks
        blocked = []
        completed_ids = {t["id"] for t in tasks if t.get("status") == "completed"}
        for t in tasks:
            if t.get("status") != "completed":
                deps = t.get("dependencies", [])
                unmet = [d for d in deps if d not in completed_ids]
                if unmet:
                    blocked.append({
                        "task": t["title"],
                        "task_id": t["id"],
                        "unmet_dependencies": unmet,
                    })

        # High priority pending
        high_priority = [
            t for t in tasks
            if t.get("priority") in ("high", "critical")
            and t.get("status") in ("pending", "in_progress")
        ]

        return {
            "agent": self.name,
            "task_summary": {k: len(v) for k, v in by_status.items()},
            "tasks_by_agent": {k: len(v) for k, v in by_agent.items()},
            "blocked_tasks": blocked,
            "high_priority_tasks": [
                {"id": t["id"], "title": t["title"], "priority": t["priority"]}
                for t in high_priority
            ],
            "operational_health": self._assess_health(by_status, blocked),
        }

    def run_cycle(self, project: dict) -> list[AgentAction]:
        """One autonomous operations cycle."""
        actions = []
        analysis = self.analyse_project(project)
        tasks = project.get("tasks", [])

        # Execute ready tasks (no unmet dependencies, pending status)
        completed_ids = {t["id"] for t in tasks if t.get("status") == "completed"}
        ready_tasks = []
        for t in tasks:
            if t.get("status") == "pending":
                deps = t.get("dependencies", [])
                if all(d in completed_ids for d in deps):
                    ready_tasks.append(t)

        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        ready_tasks.sort(key=lambda t: priority_order.get(t.get("priority", "medium"), 2))

        for task in ready_tasks[:5]:  # Process up to 5 tasks per cycle
            action = AgentAction(
                agent_role=self.role,
                title=f"Execute task: {task['title']}",
                description=f"Starting execution of task '{task['title']}' (priority: {task.get('priority', 'medium')})",
                priority=ActionPriority.MEDIUM,
                payload={
                    "type": "task_execution",
                    "task_id": task["id"],
                    "task_title": task["title"],
                },
            )
            actions.append(action)

        # Report blockers
        for blocked in analysis.get("blocked_tasks", []):
            action = AgentAction(
                agent_role=self.role,
                title=f"Blocker: {blocked['task']}",
                description=(
                    f"Task '{blocked['task']}' is blocked by unmet dependencies: "
                    f"{', '.join(blocked['unmet_dependencies'])}"
                ),
                priority=ActionPriority.HIGH,
                payload={"type": "blocker", "blocked_task": blocked},
            )
            actions.append(action)
            self.send_message(
                recipient="user",
                subject=f"Blocker detected: {blocked['task']}",
                body=action.description,
                message_type="alert",
            )

        # Operational health alerts
        health = analysis.get("operational_health", {})
        if health.get("status") == "critical":
            action = AgentAction(
                agent_role=self.role,
                title="Operational health: CRITICAL",
                description=health.get("details", "Multiple operational issues detected."),
                priority=ActionPriority.CRITICAL,
                requires_approval=True,
                payload={"type": "health_alert", "health": health},
            )
            self.request_approval(
                action.title, action.description,
                action.payload, ActionPriority.CRITICAL,
            )
            actions.append(action)

        return actions

    def execute_task(self, task_id: str, result: str = "completed") -> dict:
        """Mark a task as executed and log it."""
        entry = {
            "task_id": task_id,
            "result": result,
            "executed_at": datetime.now(timezone.utc).isoformat(),
            "agent": self.name,
        }
        self.execution_log.append(entry)
        return entry

    def _assess_health(self, by_status: dict, blocked: list) -> dict:
        total = sum(len(v) for v in by_status.values())
        if total == 0:
            return {"status": "idle", "details": "No tasks in the project."}

        blocked_count = len(blocked)
        completed = len(by_status.get("completed", []))
        completion_rate = (completed / total * 100) if total > 0 else 0

        if blocked_count > total * 0.3:
            return {
                "status": "critical",
                "details": f"{blocked_count}/{total} tasks are blocked. Immediate attention needed.",
                "completion_rate": completion_rate,
            }
        elif blocked_count > 0:
            return {
                "status": "warning",
                "details": f"{blocked_count} blocked tasks. Monitor closely.",
                "completion_rate": completion_rate,
            }
        else:
            return {
                "status": "healthy",
                "details": f"Operations running smoothly. {completion_rate:.0f}% complete.",
                "completion_rate": completion_rate,
            }
