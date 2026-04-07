"""
Agent Team - Main entry point.

Sets up the full agent team, registers all agents, configures ACP
for external agent communication, and launches the CLI interface.

Usage:
    python -m agent_team.main
    python -m agent_team.main --project path/to/project.json
"""

import sys
import logging
from pathlib import Path

from .core.orchestrator import Orchestrator
from .core.base_agent import AgentRole
from .core.communication import CommunicationHub
from .agents.strategy_agent import StrategyAgent
from .agents.research_agent import ResearchAgent
from .agents.operations_agent import OperationsAgent
from .agents.forecast_agent import ForecastAgent
from .agents.qa_agent import QAAgent
from .agents.resource_agent import ResourceAgent
from .acp.protocol import ACPHub
from .ui.cli import CLI


def setup_logging(level: str = "WARNING"):
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.WARNING),
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def build_team() -> tuple[Orchestrator, CommunicationHub, ACPHub]:
    """Assemble the full agent team and supporting infrastructure."""

    # Core orchestrator
    orchestrator = Orchestrator()

    # Register all agents
    orchestrator.register_agent(StrategyAgent())
    orchestrator.register_agent(ResearchAgent())
    orchestrator.register_agent(OperationsAgent())
    orchestrator.register_agent(ForecastAgent())
    orchestrator.register_agent(QAAgent())
    orchestrator.register_agent(ResourceAgent())

    # Communication hub
    comm_hub = CommunicationHub(orchestrator.bus)

    # ACP hub for external agents
    acp_hub = ACPHub(team_name="AgentTeam")

    # Set up file-based exchange directory for external agent IPC
    exchange_dir = Path.home() / ".agent_team" / "acp_exchange"
    acp_hub.setup_exchange(exchange_dir)

    # Pre-register known external agents
    acp_hub.register_agent(
        name="OpenClaw",
        agent_type="openclaw",
        capabilities=[
            "legal_research", "contract_analysis", "compliance_checking",
            "document_review", "regulatory_monitoring",
        ],
        endpoint="acp://openclaw",
        metadata={"description": "Legal and compliance AI agent"},
    )
    acp_hub.register_agent(
        name="PaperClip",
        agent_type="paperclip",
        capabilities=[
            "document_generation", "template_management", "data_extraction",
            "report_formatting", "content_optimization",
        ],
        endpoint="acp://paperclip",
        metadata={"description": "Document and content management AI agent"},
    )

    return orchestrator, comm_hub, acp_hub


def main():
    """Entry point."""
    setup_logging()

    orchestrator, comm_hub, acp_hub = build_team()

    # Load project if path given
    if len(sys.argv) > 1 and sys.argv[1] == "--project":
        project_path = sys.argv[2] if len(sys.argv) > 2 else None
        if project_path and Path(project_path).exists():
            orchestrator.load_project(project_path)
            print(f"Loaded project from {project_path}")
        else:
            print(f"Project file not found: {project_path}")

    # Launch CLI
    cli = CLI(orchestrator, comm_hub, acp_hub)
    cli.run()


if __name__ == "__main__":
    main()
