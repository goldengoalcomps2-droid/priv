"""
Research Agent - Constantly researches project data and wider market data
to analyse, suggest and implement methods for project success.

Responsibilities:
- Monitor and analyse project performance data
- Research market trends, competitors, and opportunities
- Provide data-backed recommendations
- Identify emerging risks and opportunities
- Feed insights to Strategy and Forecast agents
"""

from datetime import datetime, timezone
from ..core.base_agent import (
    BaseAgent, AgentRole, AgentAction, ActionPriority,
)


class ResearchAgent(BaseAgent):

    def __init__(self, team_bus=None):
        super().__init__(AgentRole.RESEARCH, team_bus)
        self._capabilities = [
            "market_analysis",
            "competitive_intelligence",
            "data_analysis",
            "trend_identification",
            "opportunity_detection",
            "risk_assessment",
            "benchmarking",
        ]
        self.research_queue: list[dict] = []
        self.findings: list[dict] = []

    def analyse_project(self, project: dict) -> dict:
        """Analyse project from a research & data perspective."""
        performance = project.get("performance", [])
        targets = project.get("targets", [])
        market_data = project.get("market_data", [])
        research_notes = project.get("research_notes", [])

        # Performance trend analysis
        trends = {}
        for m in performance:
            name = m.get("name", "unknown")
            if name not in trends:
                trends[name] = []
            trends[name].append({
                "value": m.get("value", 0),
                "trend": m.get("trend", "stable"),
                "recorded_at": m.get("recorded_at", ""),
            })

        # Target gap analysis
        target_gaps = []
        for t in targets:
            gap = t.get("target_value", 0) - t.get("current_value", 0)
            if gap > 0:
                target_gaps.append({
                    "target": t.get("name", ""),
                    "gap": gap,
                    "unit": t.get("unit", ""),
                    "progress_pct": t.get("progress_pct", 0),
                })

        # Research coverage
        researched_topics = {n.get("topic", "") for n in research_notes}

        return {
            "agent": self.name,
            "performance_trends": trends,
            "target_gaps": sorted(target_gaps, key=lambda x: x["progress_pct"]),
            "total_market_data_points": len(market_data),
            "total_research_notes": len(research_notes),
            "researched_topics": list(researched_topics),
            "insights": self._generate_insights(trends, target_gaps, market_data),
            "research_recommendations": self._recommend_research(
                project, researched_topics
            ),
        }

    def run_cycle(self, project: dict) -> list[AgentAction]:
        """One autonomous research cycle."""
        actions = []
        analysis = self.analyse_project(project)

        # Generate insights as actions
        for insight in analysis.get("insights", []):
            action = AgentAction(
                agent_role=self.role,
                title=f"Research insight: {insight['area']}",
                description=insight["finding"],
                priority=ActionPriority(insight.get("priority", "medium")),
                payload={
                    "type": "insight",
                    "area": insight["area"],
                    "data": insight.get("data", {}),
                },
            )
            actions.append(action)
            # Share insights with strategy agent
            self.send_message(
                recipient="strategy",
                subject=f"Research insight: {insight['area']}",
                body=insight["finding"],
                message_type="info",
                payload={"insight": insight},
            )

        # Queue research tasks for gaps
        for rec in analysis.get("research_recommendations", []):
            action = AgentAction(
                agent_role=self.role,
                title=f"Research needed: {rec['topic']}",
                description=rec["reason"],
                priority=ActionPriority.MEDIUM,
                payload={"type": "research_task", "topic": rec["topic"]},
            )
            actions.append(action)

        # Flag critical target gaps
        for gap in analysis.get("target_gaps", []):
            if gap["progress_pct"] < 10:
                action = AgentAction(
                    agent_role=self.role,
                    title=f"Critical gap alert: {gap['target']}",
                    description=(
                        f"Target '{gap['target']}' is at {gap['progress_pct']:.1f}% "
                        f"with a gap of {gap['gap']} {gap['unit']}. "
                        f"Recommending immediate research into acceleration methods."
                    ),
                    priority=ActionPriority.HIGH,
                    requires_approval=True,
                    payload={"type": "gap_alert", "gap": gap},
                )
                self.request_approval(
                    action.title, action.description,
                    action.payload, ActionPriority.HIGH,
                )
                actions.append(action)

        return actions

    def add_research(self, topic: str, source: str = "",
                     data: dict | None = None) -> dict:
        """Add a research finding."""
        finding = {
            "topic": topic,
            "source": source,
            "data": data or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent": self.name,
        }
        self.findings.append(finding)
        return finding

    def add_market_data(self, project: dict, category: str,
                        data_point: dict) -> dict:
        """Record a market data observation."""
        entry = {
            "category": category,
            "data": data_point,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "agent": self.name,
        }
        return entry

    def _generate_insights(self, trends: dict, target_gaps: list,
                           market_data: list) -> list[dict]:
        insights = []

        # Declining metrics
        for metric_name, readings in trends.items():
            declining = [r for r in readings if r.get("trend") == "declining"]
            if len(declining) >= 2:
                insights.append({
                    "area": f"Declining: {metric_name}",
                    "finding": (
                        f"Metric '{metric_name}' shows a sustained decline "
                        f"({len(declining)} declining readings). "
                        f"Root cause investigation recommended."
                    ),
                    "priority": "high",
                    "data": {"metric": metric_name, "readings": readings},
                })

        # Large target gaps
        critical_gaps = [g for g in target_gaps if g["progress_pct"] < 20]
        if critical_gaps:
            insights.append({
                "area": "Target Achievement Risk",
                "finding": (
                    f"{len(critical_gaps)} targets are below 20% progress. "
                    f"Recommend intensive resource reallocation or target revision."
                ),
                "priority": "high",
                "data": {"critical_gaps": critical_gaps},
            })

        # Market data patterns
        if len(market_data) > 5:
            insights.append({
                "area": "Market Intelligence",
                "finding": (
                    f"Accumulated {len(market_data)} market data points. "
                    f"Pattern analysis available for strategic review."
                ),
                "priority": "medium",
                "data": {"total_points": len(market_data)},
            })

        return insights

    def _recommend_research(self, project: dict,
                            researched_topics: set) -> list[dict]:
        recommendations = []
        goals = project.get("goals", [])

        for goal in goals:
            topic = f"market_analysis_{goal.get('title', '').replace(' ', '_').lower()}"
            if topic not in researched_topics:
                recommendations.append({
                    "topic": topic,
                    "reason": f"No market research exists for goal: {goal.get('title', '')}",
                })

        if "competitive_landscape" not in researched_topics:
            recommendations.append({
                "topic": "competitive_landscape",
                "reason": "No competitive analysis has been performed yet.",
            })

        if "industry_trends" not in researched_topics:
            recommendations.append({
                "topic": "industry_trends",
                "reason": "No industry trend analysis exists.",
            })

        return recommendations
