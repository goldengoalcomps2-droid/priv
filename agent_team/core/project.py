"""
Project - The data model that describes a project the agent team manages.

Holds the outline, goals, targets, current status, performance metrics,
task board, and full history of agent actions.
"""

import uuid
import json
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class ProjectStatus(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


@dataclass
class Goal:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    title: str = ""
    description: str = ""
    measurable_target: str = ""
    deadline: str = ""
    progress_pct: float = 0.0
    status: str = "active"

    def to_dict(self) -> dict:
        return self.__dict__.copy()


@dataclass
class Target:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    name: str = ""
    metric: str = ""
    current_value: float = 0.0
    target_value: float = 0.0
    unit: str = ""
    deadline: str = ""

    @property
    def progress_pct(self) -> float:
        if self.target_value == 0:
            return 0.0
        return min(100.0, (self.current_value / self.target_value) * 100)

    def to_dict(self) -> dict:
        d = self.__dict__.copy()
        d["progress_pct"] = self.progress_pct
        return d


@dataclass
class Task:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    title: str = ""
    description: str = ""
    assigned_to: str = ""  # agent role
    status: str = "pending"  # pending, in_progress, completed, blocked
    priority: str = "medium"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: str | None = None
    dependencies: list[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict:
        return self.__dict__.copy()


@dataclass
class PerformanceMetric:
    name: str = ""
    value: float = 0.0
    unit: str = ""
    trend: str = "stable"  # improving, stable, declining
    recorded_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return self.__dict__.copy()


class Project:
    """Full project representation managed by the agent team."""

    def __init__(self, name: str = "", outline: str = ""):
        self.id = uuid.uuid4().hex[:10]
        self.name = name
        self.outline = outline
        self.status = ProjectStatus.DRAFT
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.updated_at = self.created_at

        # Core definitions
        self.goals: list[Goal] = []
        self.targets: list[Target] = []
        self.strategies: list[dict] = []
        self.methods: list[dict] = []

        # Execution state
        self.tasks: list[Task] = []
        self.performance: list[PerformanceMetric] = []
        self.action_history: list[dict] = []
        self.forecasts: list[dict] = []
        self.resources: list[dict] = []
        self.integrations: list[dict] = []

        # Research & analysis
        self.research_notes: list[dict] = []
        self.market_data: list[dict] = []

        # Metadata
        self.tags: list[str] = []
        self.config: dict = {}

    # --- goals & targets -----------------------------------------------------

    def add_goal(self, title: str, description: str = "",
                 measurable_target: str = "", deadline: str = "") -> Goal:
        g = Goal(title=title, description=description,
                 measurable_target=measurable_target, deadline=deadline)
        self.goals.append(g)
        self._touch()
        return g

    def add_target(self, name: str, metric: str, target_value: float,
                   unit: str = "", deadline: str = "") -> Target:
        t = Target(name=name, metric=metric, target_value=target_value,
                   unit=unit, deadline=deadline)
        self.targets.append(t)
        self._touch()
        return t

    # --- tasks ---------------------------------------------------------------

    def add_task(self, title: str, description: str = "",
                 assigned_to: str = "", priority: str = "medium",
                 dependencies: list[str] | None = None) -> Task:
        t = Task(title=title, description=description,
                 assigned_to=assigned_to, priority=priority,
                 dependencies=dependencies or [])
        self.tasks.append(t)
        self._touch()
        return t

    def update_task(self, task_id: str, **kwargs) -> Task | None:
        for t in self.tasks:
            if t.id == task_id:
                for k, v in kwargs.items():
                    if hasattr(t, k):
                        setattr(t, k, v)
                if kwargs.get("status") == "completed":
                    t.completed_at = datetime.now(timezone.utc).isoformat()
                self._touch()
                return t
        return None

    def get_tasks(self, status: str | None = None,
                  assigned_to: str | None = None) -> list[Task]:
        tasks = self.tasks
        if status:
            tasks = [t for t in tasks if t.status == status]
        if assigned_to:
            tasks = [t for t in tasks if t.assigned_to == assigned_to]
        return tasks

    # --- performance ---------------------------------------------------------

    def record_metric(self, name: str, value: float,
                      unit: str = "", trend: str = "stable"):
        m = PerformanceMetric(name=name, value=value, unit=unit, trend=trend)
        self.performance.append(m)
        self._touch()

    # --- strategies & methods ------------------------------------------------

    def add_strategy(self, title: str, description: str,
                     actions: list[str] | None = None, rationale: str = ""):
        self.strategies.append({
            "id": uuid.uuid4().hex[:8],
            "title": title,
            "description": description,
            "actions": actions or [],
            "rationale": rationale,
            "status": "proposed",
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        self._touch()

    def add_method(self, title: str, description: str, domain: str = ""):
        self.methods.append({
            "id": uuid.uuid4().hex[:8],
            "title": title,
            "description": description,
            "domain": domain,
            "status": "active",
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        self._touch()

    # --- serialization -------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "outline": self.outline,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "goals": [g.to_dict() for g in self.goals],
            "targets": [t.to_dict() for t in self.targets],
            "strategies": self.strategies,
            "methods": self.methods,
            "tasks": [t.to_dict() for t in self.tasks],
            "performance": [p.to_dict() for p in self.performance],
            "forecasts": self.forecasts,
            "resources": self.resources,
            "integrations": self.integrations,
            "research_notes": self.research_notes,
            "market_data": self.market_data,
            "tags": self.tags,
            "config": self.config,
        }

    def save(self, path: str | Path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2))

    @classmethod
    def load(cls, path: str | Path) -> "Project":
        data = json.loads(Path(path).read_text())
        p = cls(name=data.get("name", ""), outline=data.get("outline", ""))
        p.id = data.get("id", p.id)
        p.status = ProjectStatus(data.get("status", "draft"))
        p.created_at = data.get("created_at", p.created_at)
        p.updated_at = data.get("updated_at", p.updated_at)
        p.strategies = data.get("strategies", [])
        p.methods = data.get("methods", [])
        p.forecasts = data.get("forecasts", [])
        p.resources = data.get("resources", [])
        p.integrations = data.get("integrations", [])
        p.research_notes = data.get("research_notes", [])
        p.market_data = data.get("market_data", [])
        p.tags = data.get("tags", [])
        p.config = data.get("config", {})
        for gd in data.get("goals", []):
            p.goals.append(Goal(**gd))
        for td in data.get("targets", []):
            td.pop("progress_pct", None)
            p.targets.append(Target(**td))
        for td in data.get("tasks", []):
            p.tasks.append(Task(**td))
        for md in data.get("performance", []):
            p.performance.append(PerformanceMetric(**md))
        return p

    # --- summary -------------------------------------------------------------

    def summary(self) -> str:
        lines = [
            f"Project: {self.name} [{self.status.value}]",
            f"Goals: {len(self.goals)}  |  Targets: {len(self.targets)}  |  Tasks: {len(self.tasks)}",
        ]
        for g in self.goals:
            lines.append(f"  Goal: {g.title} ({g.progress_pct:.0f}%)")
        for t in self.targets:
            lines.append(f"  Target: {t.name} = {t.current_value}/{t.target_value} {t.unit} ({t.progress_pct:.0f}%)")
        pending = len([t for t in self.tasks if t.status == "pending"])
        active = len([t for t in self.tasks if t.status == "in_progress"])
        done = len([t for t in self.tasks if t.status == "completed"])
        lines.append(f"  Tasks: {pending} pending, {active} active, {done} done")
        return "\n".join(lines)

    def _touch(self):
        self.updated_at = datetime.now(timezone.utc).isoformat()
