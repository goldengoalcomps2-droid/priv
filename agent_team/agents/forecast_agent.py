"""
Forecast Agent - Predicts future needs and requirements based on
project targets, goals, current performance and capacity.

Responsibilities:
- Forecast resource needs based on project trajectory
- Predict timeline risks and milestone completion dates
- Capacity planning and workload projection
- Trend extrapolation from performance data
- Scenario modelling (best/expected/worst case)
- Implement findings by creating tasks and recommending strategy changes
"""

from datetime import datetime, timezone
from ..core.base_agent import (
    BaseAgent, AgentRole, AgentAction, ActionPriority,
)


class ForecastAgent(BaseAgent):

    def __init__(self, team_bus=None):
        super().__init__(AgentRole.FORECAST, team_bus)
        self._capabilities = [
            "trend_extrapolation",
            "capacity_planning",
            "timeline_forecasting",
            "resource_projection",
            "scenario_modelling",
            "risk_prediction",
            "demand_forecasting",
        ]
        self.forecast_history: list[dict] = []

    def analyse_project(self, project: dict) -> dict:
        """Analyse the project from a forecasting perspective."""
        targets = project.get("targets", [])
        performance = project.get("performance", [])
        tasks = project.get("tasks", [])
        goals = project.get("goals", [])

        # Velocity: tasks completed vs total
        completed = [t for t in tasks if t.get("status") == "completed"]
        total = len(tasks)
        velocity = len(completed) / max(total, 1)

        # Target trajectory
        target_forecasts = []
        for t in targets:
            current = t.get("current_value", 0)
            target_val = t.get("target_value", 0)
            progress = t.get("progress_pct", 0)
            forecast = self._forecast_target(t, performance)
            target_forecasts.append(forecast)

        # Capacity assessment
        in_progress = [t for t in tasks if t.get("status") == "in_progress"]
        pending = [t for t in tasks if t.get("status") == "pending"]
        capacity = self._assess_capacity(in_progress, pending, completed)

        # Scenario modelling
        scenarios = self._model_scenarios(targets, velocity, performance)

        return {
            "agent": self.name,
            "task_velocity": velocity,
            "tasks_completed": len(completed),
            "tasks_remaining": len(pending) + len(in_progress),
            "target_forecasts": target_forecasts,
            "capacity_assessment": capacity,
            "scenarios": scenarios,
            "risk_flags": self._identify_risks(target_forecasts, capacity),
        }

    def run_cycle(self, project: dict) -> list[AgentAction]:
        """One autonomous forecasting cycle."""
        actions = []
        analysis = self.analyse_project(project)

        # Store forecast
        forecast_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "analysis": analysis,
        }
        self.forecast_history.append(forecast_entry)

        # Alert on high-risk targets
        for forecast in analysis.get("target_forecasts", []):
            if forecast.get("risk_level") == "high":
                action = AgentAction(
                    agent_role=self.role,
                    title=f"Forecast risk: {forecast['target_name']}",
                    description=(
                        f"Target '{forecast['target_name']}' is projected to "
                        f"{'miss' if not forecast.get('on_track') else 'meet'} its deadline. "
                        f"Current trajectory: {forecast.get('projected_completion', 'unknown')}. "
                        f"Recommendation: {forecast.get('recommendation', 'review resources')}"
                    ),
                    priority=ActionPriority.HIGH,
                    requires_approval=True,
                    payload={"type": "forecast_risk", "forecast": forecast},
                )
                self.request_approval(
                    action.title, action.description,
                    action.payload, ActionPriority.HIGH,
                )
                actions.append(action)

        # Capacity warnings
        capacity = analysis.get("capacity_assessment", {})
        if capacity.get("status") == "overloaded":
            action = AgentAction(
                agent_role=self.role,
                title="Capacity warning: Team overloaded",
                description=(
                    f"Current workload exceeds capacity. "
                    f"{capacity.get('in_progress', 0)} tasks in progress, "
                    f"{capacity.get('pending', 0)} pending. "
                    f"Recommend prioritisation review or resource expansion."
                ),
                priority=ActionPriority.HIGH,
                requires_approval=True,
                payload={"type": "capacity_warning", "capacity": capacity},
            )
            self.request_approval(
                action.title, action.description,
                action.payload, ActionPriority.HIGH,
            )
            actions.append(action)

        # Share scenarios with strategy agent
        scenarios = analysis.get("scenarios", {})
        if scenarios:
            self.send_message(
                recipient="strategy",
                subject="Updated scenario models",
                body=f"Best case: {scenarios.get('best', {}).get('summary', 'N/A')}, "
                     f"Expected: {scenarios.get('expected', {}).get('summary', 'N/A')}, "
                     f"Worst case: {scenarios.get('worst', {}).get('summary', 'N/A')}",
                message_type="info",
                payload={"scenarios": scenarios},
            )

        # Periodic forecast report
        action = AgentAction(
            agent_role=self.role,
            title="Periodic forecast report",
            description=f"Velocity: {analysis['task_velocity']:.0%}, "
                        f"Remaining tasks: {analysis['tasks_remaining']}, "
                        f"Risk flags: {len(analysis.get('risk_flags', []))}",
            priority=ActionPriority.LOW,
            payload={"type": "forecast_report", "summary": analysis},
        )
        actions.append(action)

        return actions

    def _forecast_target(self, target: dict, performance: list) -> dict:
        """Forecast a single target's trajectory."""
        current = target.get("current_value", 0)
        target_val = target.get("target_value", 0)
        progress = target.get("progress_pct", 0)
        name = target.get("name", "Unknown")

        if target_val == 0:
            return {
                "target_name": name,
                "on_track": True,
                "risk_level": "low",
                "projected_completion": "N/A",
                "recommendation": "Set a measurable target value.",
            }

        gap = target_val - current
        on_track = progress >= 25  # simplified heuristic

        risk_level = "low"
        if progress < 10:
            risk_level = "high"
        elif progress < 30:
            risk_level = "medium"

        recommendation = "On track - maintain current approach."
        if risk_level == "high":
            recommendation = "Significantly behind. Reallocate resources and intensify efforts."
        elif risk_level == "medium":
            recommendation = "Slightly behind. Monitor closely and consider method adjustments."

        return {
            "target_name": name,
            "current_value": current,
            "target_value": target_val,
            "gap": gap,
            "progress_pct": progress,
            "on_track": on_track,
            "risk_level": risk_level,
            "projected_completion": "on_schedule" if on_track else "at_risk",
            "recommendation": recommendation,
        }

    def _assess_capacity(self, in_progress: list, pending: list,
                         completed: list) -> dict:
        active = len(in_progress)
        queued = len(pending)
        done = len(completed)
        total_load = active + queued

        if active > 10:
            status = "overloaded"
        elif active > 5:
            status = "high_utilization"
        elif active > 0:
            status = "normal"
        else:
            status = "idle"

        return {
            "status": status,
            "in_progress": active,
            "pending": queued,
            "completed": done,
            "total_load": total_load,
            "utilization_pct": min(100, (active / max(1, active + 2)) * 100),
        }

    def _model_scenarios(self, targets: list, velocity: float,
                         performance: list) -> dict:
        return {
            "best": {
                "summary": f"All targets met with {velocity:.0%} velocity sustained and improving",
                "velocity_assumed": min(1.0, velocity * 1.3),
                "confidence": 0.2,
            },
            "expected": {
                "summary": f"Most targets met with current {velocity:.0%} velocity",
                "velocity_assumed": velocity,
                "confidence": 0.6,
            },
            "worst": {
                "summary": f"Significant delays with velocity dropping below {velocity * 0.5:.0%}",
                "velocity_assumed": max(0.0, velocity * 0.5),
                "confidence": 0.2,
            },
        }

    def _identify_risks(self, target_forecasts: list, capacity: dict) -> list[dict]:
        risks = []
        high_risk_targets = [f for f in target_forecasts if f.get("risk_level") == "high"]
        if high_risk_targets:
            risks.append({
                "type": "target_risk",
                "severity": "high",
                "description": f"{len(high_risk_targets)} targets at high risk of missing deadline.",
            })
        if capacity.get("status") == "overloaded":
            risks.append({
                "type": "capacity_risk",
                "severity": "high",
                "description": "Team capacity exceeded. Risk of burnout and quality decline.",
            })
        return risks
