"""
Resource Agent - Identifies tools and resources of value that bring the
project closer to achieving its goals and targets, then implements and
integrates them.

Responsibilities:
- Discover tools, platforms, and resources relevant to project goals
- Evaluate resource ROI and fit
- Implement and integrate selected resources
- Monitor resource utilization and effectiveness
- Recommend resource reallocation
- Track costs and resource budgets
"""

from datetime import datetime, timezone
from ..core.base_agent import (
    BaseAgent, AgentRole, AgentAction, ActionPriority,
)


class ResourceAgent(BaseAgent):

    def __init__(self, team_bus=None):
        super().__init__(AgentRole.RESOURCE, team_bus)
        self._capabilities = [
            "tool_discovery",
            "resource_evaluation",
            "integration_management",
            "utilization_monitoring",
            "cost_tracking",
            "vendor_assessment",
            "resource_optimization",
        ]
        self.resource_registry: list[dict] = []
        self.integration_log: list[dict] = []

    def analyse_project(self, project: dict) -> dict:
        """Analyse resource needs and current resource state."""
        goals = project.get("goals", [])
        targets = project.get("targets", [])
        resources = project.get("resources", [])
        integrations = project.get("integrations", [])
        tasks = project.get("tasks", [])

        # Identify resource gaps
        resource_gaps = self._identify_gaps(goals, targets, resources)

        # Evaluate current resource effectiveness
        resource_health = self._evaluate_resources(resources, integrations)

        # Recommend new tools / resources
        recommendations = self._recommend_resources(goals, targets, resources)

        # Utilization analysis
        utilization = self._analyse_utilization(resources, tasks)

        return {
            "agent": self.name,
            "total_resources": len(resources),
            "total_integrations": len(integrations),
            "resource_gaps": resource_gaps,
            "resource_health": resource_health,
            "recommendations": recommendations,
            "utilization": utilization,
        }

    def run_cycle(self, project: dict) -> list[AgentAction]:
        """One autonomous resource management cycle."""
        actions = []
        analysis = self.analyse_project(project)

        # Propose resources to fill gaps
        for gap in analysis.get("resource_gaps", []):
            action = AgentAction(
                agent_role=self.role,
                title=f"Resource needed: {gap['area']}",
                description=(
                    f"Gap identified: {gap['description']}. "
                    f"Recommended resource type: {gap.get('recommended_type', 'TBD')}."
                ),
                priority=ActionPriority.HIGH,
                requires_approval=True,
                payload={"type": "resource_gap", "gap": gap},
            )
            self.request_approval(
                action.title, action.description,
                action.payload, ActionPriority.HIGH,
            )
            actions.append(action)

        # Recommend new tools
        for rec in analysis.get("recommendations", []):
            action = AgentAction(
                agent_role=self.role,
                title=f"Tool recommendation: {rec['name']}",
                description=(
                    f"Recommended tool: {rec['name']}. "
                    f"Purpose: {rec['purpose']}. "
                    f"Expected impact: {rec.get('expected_impact', 'moderate')}."
                ),
                priority=ActionPriority.MEDIUM,
                requires_approval=True,
                payload={"type": "tool_recommendation", "tool": rec},
            )
            self.request_approval(
                action.title, action.description,
                action.payload, ActionPriority.MEDIUM,
            )
            actions.append(action)

        # Flag underutilized resources
        utilization = analysis.get("utilization", {})
        underutilized = utilization.get("underutilized", [])
        for resource in underutilized:
            action = AgentAction(
                agent_role=self.role,
                title=f"Underutilized: {resource['name']}",
                description=(
                    f"Resource '{resource['name']}' is underutilized "
                    f"({resource.get('utilization_pct', 0):.0f}%). "
                    f"Consider reassignment or decommissioning."
                ),
                priority=ActionPriority.LOW,
                payload={"type": "underutilized", "resource": resource},
            )
            actions.append(action)

        return actions

    def register_resource(self, name: str, resource_type: str,
                          description: str = "", config: dict | None = None) -> dict:
        """Register a new resource in the project."""
        resource = {
            "name": name,
            "type": resource_type,
            "description": description,
            "config": config or {},
            "status": "active",
            "registered_at": datetime.now(timezone.utc).isoformat(),
            "utilization": 0.0,
        }
        self.resource_registry.append(resource)
        self.send_message(
            recipient="all",
            subject=f"New resource registered: {name}",
            body=f"{resource_type}: {description}",
            message_type="info",
        )
        return resource

    def integrate_tool(self, name: str, tool_type: str,
                       config: dict | None = None) -> dict:
        """Set up integration with an external tool."""
        integration = {
            "name": name,
            "type": tool_type,
            "config": config or {},
            "status": "active",
            "integrated_at": datetime.now(timezone.utc).isoformat(),
        }
        self.integration_log.append(integration)
        return integration

    def _identify_gaps(self, goals: list, targets: list,
                       resources: list) -> list[dict]:
        gaps = []
        resource_types = {r.get("type", "") for r in resources}

        # Check if common resource types are covered
        essential_types = ["analytics", "communication", "automation", "monitoring"]
        for rt in essential_types:
            if rt not in resource_types:
                gaps.append({
                    "area": rt,
                    "description": f"No {rt} resource is currently provisioned.",
                    "recommended_type": rt,
                })

        return gaps

    def _evaluate_resources(self, resources: list, integrations: list) -> dict:
        active = [r for r in resources if r.get("status") == "active"]
        inactive = [r for r in resources if r.get("status") != "active"]
        return {
            "active_resources": len(active),
            "inactive_resources": len(inactive),
            "active_integrations": len([i for i in integrations if i.get("status") == "active"]),
            "health": "good" if len(active) > 0 else "needs_attention",
        }

    def _recommend_resources(self, goals: list, targets: list,
                              resources: list) -> list[dict]:
        recommendations = []
        resource_names = {r.get("name", "").lower() for r in resources}

        # Generic recommendations based on goals
        for goal in goals:
            title = goal.get("title", "").lower()
            if "growth" in title or "scale" in title:
                if "automation_platform" not in resource_names:
                    recommendations.append({
                        "name": "Automation Platform",
                        "purpose": f"Automate processes to support: {goal.get('title', '')}",
                        "expected_impact": "high",
                    })
            if "revenue" in title or "sales" in title:
                if "crm" not in resource_names:
                    recommendations.append({
                        "name": "CRM System",
                        "purpose": f"Track and optimise sales for: {goal.get('title', '')}",
                        "expected_impact": "high",
                    })
            if "quality" in title or "satisfaction" in title:
                if "feedback_tool" not in resource_names:
                    recommendations.append({
                        "name": "Feedback Tool",
                        "purpose": f"Collect feedback for: {goal.get('title', '')}",
                        "expected_impact": "medium",
                    })

        return recommendations

    def _analyse_utilization(self, resources: list, tasks: list) -> dict:
        underutilized = []
        for r in resources:
            util = r.get("utilization", 0)
            if util < 30 and r.get("status") == "active":
                underutilized.append({
                    "name": r.get("name", ""),
                    "utilization_pct": util,
                })
        return {
            "total_resources": len(resources),
            "underutilized": underutilized,
            "avg_utilization": (
                sum(r.get("utilization", 0) for r in resources) / max(len(resources), 1)
            ),
        }
