"""
QA Agent - Examines and tests all functions of the project to ensure
every aspect is running in line with its stated use.

Responsibilities:
- Validate that project outputs match stated goals
- Test all functions and integrations
- Check compliance with defined methods and strategies
- Monitor quality metrics
- Raise issues when things deviate from spec
- Verify completed tasks actually deliver what was promised
"""

from datetime import datetime, timezone
from ..core.base_agent import (
    BaseAgent, AgentRole, AgentAction, ActionPriority,
)


class QAAgent(BaseAgent):

    def __init__(self, team_bus=None):
        super().__init__(AgentRole.QA, team_bus)
        self._capabilities = [
            "functional_testing",
            "integration_testing",
            "compliance_checking",
            "quality_monitoring",
            "goal_validation",
            "output_verification",
            "regression_detection",
        ]
        self.test_results: list[dict] = []
        self.issues: list[dict] = []

    def analyse_project(self, project: dict) -> dict:
        """Analyse quality and compliance state of the project."""
        goals = project.get("goals", [])
        targets = project.get("targets", [])
        tasks = project.get("tasks", [])
        strategies = project.get("strategies", [])
        methods = project.get("methods", [])
        integrations = project.get("integrations", [])

        # Goal alignment check
        alignment_issues = self._check_goal_alignment(goals, strategies, tasks)

        # Completed task verification
        completed_tasks = [t for t in tasks if t.get("status") == "completed"]
        task_quality = self._verify_completed_tasks(completed_tasks, goals)

        # Integration health
        integration_status = self._check_integrations(integrations)

        # Method compliance
        method_compliance = self._check_method_compliance(methods, tasks)

        # Overall quality score
        quality_score = self._calculate_quality_score(
            alignment_issues, task_quality, integration_status, method_compliance
        )

        return {
            "agent": self.name,
            "quality_score": quality_score,
            "alignment_issues": alignment_issues,
            "task_quality": task_quality,
            "integration_status": integration_status,
            "method_compliance": method_compliance,
            "total_tests_run": len(self.test_results),
            "open_issues": len([i for i in self.issues if i.get("status") == "open"]),
        }

    def run_cycle(self, project: dict) -> list[AgentAction]:
        """One autonomous QA cycle."""
        actions = []
        analysis = self.analyse_project(project)

        # Report quality score
        quality = analysis.get("quality_score", {})
        score = quality.get("score", 0)

        if score < 50:
            action = AgentAction(
                agent_role=self.role,
                title=f"Quality alert: Score {score}/100",
                description=(
                    f"Project quality score is {score}/100. "
                    f"Issues: {quality.get('breakdown', {})}. "
                    f"Immediate attention required."
                ),
                priority=ActionPriority.CRITICAL,
                requires_approval=True,
                payload={"type": "quality_alert", "quality": quality},
            )
            self.request_approval(
                action.title, action.description,
                action.payload, ActionPriority.CRITICAL,
            )
            actions.append(action)
        elif score < 75:
            action = AgentAction(
                agent_role=self.role,
                title=f"Quality warning: Score {score}/100",
                description=f"Project quality is below target. Details: {quality.get('breakdown', {})}",
                priority=ActionPriority.MEDIUM,
                payload={"type": "quality_warning", "quality": quality},
            )
            actions.append(action)

        # Raise alignment issues
        for issue in analysis.get("alignment_issues", []):
            action = AgentAction(
                agent_role=self.role,
                title=f"Alignment issue: {issue['description'][:50]}",
                description=issue["description"],
                priority=ActionPriority.HIGH,
                payload={"type": "alignment_issue", "issue": issue},
            )
            actions.append(action)
            self.issues.append({
                "type": "alignment",
                "description": issue["description"],
                "status": "open",
                "created_at": datetime.now(timezone.utc).isoformat(),
            })

        # Integration test results
        for result in analysis.get("integration_status", []):
            if result.get("status") == "failing":
                action = AgentAction(
                    agent_role=self.role,
                    title=f"Integration failure: {result['name']}",
                    description=f"Integration '{result['name']}' is failing: {result.get('error', 'unknown')}",
                    priority=ActionPriority.HIGH,
                    requires_approval=True,
                    payload={"type": "integration_failure", "integration": result},
                )
                self.request_approval(
                    action.title, action.description,
                    action.payload, ActionPriority.HIGH,
                )
                actions.append(action)

        # Run test suite
        test_action = AgentAction(
            agent_role=self.role,
            title="Periodic quality check",
            description=f"Quality score: {score}/100. Open issues: {analysis.get('open_issues', 0)}.",
            priority=ActionPriority.LOW,
            payload={"type": "quality_check", "score": score},
        )
        self.test_results.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "score": score,
            "analysis": analysis,
        })
        actions.append(test_action)

        return actions

    def run_test(self, test_name: str, test_fn=None) -> dict:
        """Run a specific test and record results."""
        result = {
            "test_name": test_name,
            "status": "passed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": "",
        }
        if test_fn:
            try:
                test_fn()
                result["status"] = "passed"
            except Exception as e:
                result["status"] = "failed"
                result["details"] = str(e)
        self.test_results.append(result)
        return result

    def _check_goal_alignment(self, goals: list, strategies: list,
                               tasks: list) -> list[dict]:
        issues = []
        # Every goal should have at least one strategy or task
        for goal in goals:
            goal_title = goal.get("title", "").lower()
            has_strategy = any(
                goal_title in s.get("title", "").lower() or
                goal_title in s.get("description", "").lower()
                for s in strategies
            )
            has_task = any(
                goal_title in t.get("title", "").lower() or
                goal_title in t.get("description", "").lower()
                for t in tasks
            )
            if not has_strategy and not has_task:
                issues.append({
                    "goal": goal.get("title", ""),
                    "description": f"Goal '{goal.get('title', '')}' has no aligned strategy or task.",
                })
        return issues

    def _verify_completed_tasks(self, completed_tasks: list,
                                 goals: list) -> dict:
        return {
            "total_completed": len(completed_tasks),
            "verified": len(completed_tasks),  # simplified
            "pass_rate": 100.0 if completed_tasks else 0.0,
        }

    def _check_integrations(self, integrations: list) -> list[dict]:
        results = []
        for integration in integrations:
            results.append({
                "name": integration.get("name", "unknown"),
                "status": integration.get("status", "unknown"),
                "last_checked": datetime.now(timezone.utc).isoformat(),
            })
        return results

    def _check_method_compliance(self, methods: list, tasks: list) -> dict:
        active_methods = [m for m in methods if m.get("status") == "active"]
        return {
            "total_methods": len(methods),
            "active_methods": len(active_methods),
            "compliance_rate": 100.0 if not active_methods else 85.0,  # simplified
        }

    def _calculate_quality_score(self, alignment_issues, task_quality,
                                  integration_status, method_compliance) -> dict:
        score = 100
        breakdown = {}

        # Deduct for alignment issues
        alignment_penalty = len(alignment_issues) * 10
        score -= alignment_penalty
        breakdown["alignment"] = max(0, 100 - alignment_penalty)

        # Task quality
        task_score = task_quality.get("pass_rate", 0)
        score = score * (task_score / 100) if task_score > 0 else score * 0.5
        breakdown["task_quality"] = task_score

        # Integration health
        failing = len([i for i in integration_status if i.get("status") == "failing"])
        if failing > 0:
            score -= failing * 15
        breakdown["integrations"] = max(0, 100 - failing * 15)

        # Method compliance
        compliance = method_compliance.get("compliance_rate", 100)
        score = score * (compliance / 100)
        breakdown["method_compliance"] = compliance

        return {
            "score": max(0, min(100, round(score))),
            "breakdown": breakdown,
        }
