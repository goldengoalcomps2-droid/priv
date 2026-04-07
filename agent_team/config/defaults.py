"""
Default configuration for the agent team system.
"""

TEAM_CONFIG = {
    "team_name": "AgentTeam",
    "version": "1.0.0",

    # Agents to activate on startup
    "active_agents": [
        "strategy",
        "research",
        "operations",
        "forecast",
        "qa",
        "resource",
    ],

    # Auto-approve actions at or below this priority
    # Options: low, medium, high, critical
    "auto_approve_threshold": "medium",

    # ACP settings
    "acp": {
        "exchange_dir": "~/.agent_team/acp_exchange",
        "poll_interval_seconds": 30,
        "message_ttl_seconds": 300,
        "registered_agents": {
            "OpenClaw": {
                "type": "openclaw",
                "capabilities": [
                    "legal_research",
                    "contract_analysis",
                    "compliance_checking",
                ],
                "endpoint": "acp://openclaw",
            },
            "PaperClip": {
                "type": "paperclip",
                "capabilities": [
                    "document_generation",
                    "template_management",
                    "data_extraction",
                ],
                "endpoint": "acp://paperclip",
            },
        },
    },

    # Cycle settings
    "max_tasks_per_cycle": 5,
    "max_actions_per_agent_cycle": 10,

    # Project defaults
    "project": {
        "auto_save": True,
        "save_dir": "~/.agent_team/projects",
    },
}
