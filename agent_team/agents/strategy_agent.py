"""
Strategy Agent - Creates, integrates and implements strategies, plans and methods
designed to achieve the goals and targets of the project.

Responsibilities:
- Analyse project goals/targets and derive actionable strategies
- Break strategies into executable plans with clear milestones
- Propose methods and frameworks to reach targets
- Continuously refine strategies based on performance data
- Request user approval for major strategic shifts
"""

from ..core.base_agent import (
    BaseAgent, AgentRole, AgentAction, ActionPriority, ApprovalStatus,
)


class StrategyAgent(BaseAgent):

    def __init__(self, team_bus=None):
        super().__init__(AgentRole.STRATEGY, team_bus)
        self._capabilities = [
            "strategic_planning",
            "goal_decomposition",
            "method_design",
            "milestone_tracking",
            "strategy_refinement",
            "competitive_positioning",
        ]

    def analyse_project(self, project: dict) -> dict:
        """Evaluate current strategic posture of the project."""
        goals = project.get("goals", [])
        targets = project.get("targets", [])
        strategies = project.get("strategies", [])
        tasks = project.get("tasks", [])
        performance = project.get("performance", [])

        # Identify gaps
        goals_without_strategy = []
        strategy_titles = {s["title"].lower() for s in strategies}
        for g in goals:
            if not any(g["title"].lower() in st for st in strategy_titles):
                goals_without_strategy.append(g["title"])

        # Check target coverage
        targets_off_track = []
        for t in targets:
            if t.get("progress_pct", 0) < 25 and t.get("target_value", 0) > 0:
                targets_off_track.append(t["name"])

        # Task completion velocity
        completed = [t for t in tasks if t.get("status") == "completed"]
        pending = [t for t in tasks if t.get("status") == "pending"]

        return {
            "agent": self.name,
            "total_goals": len(goals),
            "total_targets": len(targets),
            "active_strategies": len([s for s in strategies if s.get("status") == "proposed" or s.get("status") == "active"]),
            "goals_needing_strategy": goals_without_strategy,
            "targets_off_track": targets_off_track,
            "tasks_completed": len(completed),
            "tasks_pending": len(pending),
            "recommendations": self._generate_recommendations(
                goals_without_strategy, targets_off_track, performance
            ),
        }

    def generate_plan(self, project: dict) -> list[dict]:
        """Generate a strategic plan for all uncovered goals."""
        plans = []
        goals = project.get("goals", [])
        targets = project.get("targets", [])

        for goal in goals:
            related_targets = [
                t for t in targets
                if goal.get("title", "").lower() in t.get("name", "").lower()
                or t.get("name", "").lower() in goal.get("title", "").lower()
            ]
            plan = {
                "goal_id": goal["id"],
                "goal_title": goal["title"],
                "strategy": f"Strategic approach for: {goal['title']}",
                "phases": [
                    {
                        "phase": 1,
                        "name": "Foundation & Setup",
                        "description": f"Establish the baseline for {goal['title']}",
                        "tasks": [
                            f"Define KPIs for {goal['title']}",
                            f"Identify required resources for {goal['title']}",
                            f"Set up tracking and monitoring",
                        ],
                    },
                    {
                        "phase": 2,
                        "name": "Execution & Growth",
                        "description": f"Execute primary actions toward {goal['title']}",
                        "tasks": [
                            f"Implement core methods for {goal['title']}",
                            f"Monitor progress against targets",
                            f"Iterate on approach based on data",
                        ],
                    },
                    {
                        "phase": 3,
                        "name": "Optimization & Scale",
                        "description": f"Optimize and scale successful approaches",
                        "tasks": [
                            f"Analyse what's working and double down",
                            f"Eliminate underperforming methods",
                            f"Scale proven strategies",
                        ],
                    },
                ],
                "related_targets": [t.get("name", "") for t in related_targets],
                "estimated_methods": self._suggest_methods(goal),
            }
            plans.append(plan)

        return plans

    def run_cycle(self, project: dict) -> list[AgentAction]:
        """One autonomous strategy cycle."""
        actions = []
        analysis = self.analyse_project(project)

        # Create strategies for uncovered goals
        for goal_title in analysis.get("goals_needing_strategy", []):
            action = AgentAction(
                agent_role=self.role,
                title=f"New strategy: {goal_title}",
                description=f"Proposing strategic approach for goal: {goal_title}",
                priority=ActionPriority.HIGH,
                requires_approval=True,
                payload={"goal_title": goal_title, "type": "new_strategy"},
            )
            self.request_approval(
                action.title, action.description,
                action.payload, ActionPriority.HIGH,
            )
            actions.append(action)

        # Propose recovery plans for off-track targets
        for target_name in analysis.get("targets_off_track", []):
            action = AgentAction(
                agent_role=self.role,
                title=f"Recovery plan: {target_name}",
                description=f"Target '{target_name}' is off-track. Proposing accelerated methods.",
                priority=ActionPriority.HIGH,
                requires_approval=True,
                payload={"target_name": target_name, "type": "recovery_plan"},
            )
            self.request_approval(
                action.title, action.description,
                action.payload, ActionPriority.HIGH,
            )
            actions.append(action)

        # General strategy refinement based on performance
        if analysis.get("recommendations"):
            for rec in analysis["recommendations"]:
                action = AgentAction(
                    agent_role=self.role,
                    title=f"Strategy refinement: {rec['area']}",
                    description=rec["suggestion"],
                    priority=ActionPriority.MEDIUM,
                    payload={"type": "refinement", "recommendation": rec},
                )
                actions.append(action)

        return actions

    def _generate_recommendations(self, uncovered_goals, off_track_targets,
                                   performance) -> list[dict]:
        recs = []
        if uncovered_goals:
            recs.append({
                "area": "Goal Coverage",
                "suggestion": f"{len(uncovered_goals)} goals lack a strategic approach. "
                              f"Priority: create strategies for these goals.",
            })
        if off_track_targets:
            recs.append({
                "area": "Target Recovery",
                "suggestion": f"{len(off_track_targets)} targets are significantly behind. "
                              f"Consider reallocating resources or adjusting methods.",
            })
        declining = [p for p in performance if p.get("trend") == "declining"]
        if declining:
            recs.append({
                "area": "Performance Decline",
                "suggestion": f"{len(declining)} metrics are declining. Root cause analysis recommended.",
            })
        return recs

    def _suggest_methods(self, goal: dict) -> list[str]:
        return [
            f"Data-driven approach for {goal.get('title', '')}",
            f"Iterative execution with weekly checkpoints",
            f"Cross-functional resource alignment",
            f"Continuous measurement and feedback loops",
        ]
