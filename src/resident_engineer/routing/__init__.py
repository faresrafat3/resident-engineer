"""Advanced Routing — assigns tasks to the most suitable agent or team."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ..kernel.identity import AgentIdentity, AgentRole


class TaskType(str, Enum):
    BUG_FIX = "bug-fix"
    FEATURE = "feature"
    REFACTOR = "refactor"
    TESTS = "tests"
    DOCS = "docs"
    REVIEW = "review"
    TRIAGE = "triage"
    DESIGN = "design"
    PERFORMANCE = "performance"
    MIGRATION = "migration"
    SECURITY = "security"
    RESEARCH = "research"


@dataclass
class Task:
    id: str
    type: TaskType
    project: str
    description: str
    requirements: dict[str, Any] = field(default_factory=dict)
    priority: int = 2
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class RouteDecision:
    task_id: str
    agent_id: str
    confidence: float
    reasoning: str
    team_id: str | None = None


class TaskRouter:
    """Routes tasks to agents based on role, reputation, and project affinity."""

    def __init__(self) -> None:
        self._agents: dict[str, AgentIdentity] = {}
        self._reputation: dict[str, float] = {}

    def register_agent(self, agent: AgentIdentity, reputation: float = 0.0) -> None:
        self._agents[agent.id] = agent
        self._reputation[agent.id] = reputation

    def route(self, task: Task) -> RouteDecision:
        candidates = []
        for agent in self._agents.values():
            score = self._score_agent(agent, task)
            candidates.append((agent, score))

        if not candidates:
            raise RuntimeError("No agents registered")

        best = max(candidates, key=lambda x: x[1])
        return RouteDecision(
            task_id=task.id,
            agent_id=best[0].id,
            confidence=best[1],
            reasoning=f"Role={best[0].role.value}, Rep={self._reputation.get(best[0].id, 0):.1f}",
        )

    def _score_agent(self, agent: AgentIdentity, task: Task) -> float:
        score = 0.0
        role_weights = {
            TaskType.BUG_FIX: {AgentRole.RESIDENT_ENGINEER: 1.0, AgentRole.REVIEWER: 0.3},
            TaskType.FEATURE: {AgentRole.RESIDENT_ENGINEER: 0.8, AgentRole.REVIEWER: 0.4},
            TaskType.REFACTOR: {AgentRole.RESIDENT_ENGINEER: 0.9, AgentRole.REVIEWER: 0.5},
            TaskType.TESTS: {AgentRole.RESIDENT_ENGINEER: 0.9, AgentRole.REVIEWER: 0.4},
            TaskType.DOCS: {AgentRole.RESIDENT_ENGINEER: 0.6, AgentRole.REVIEWER: 0.3},
            TaskType.REVIEW: {AgentRole.REVIEWER: 1.0, AgentRole.RESIDENT_ENGINEER: 0.4},
            TaskType.TRIAGE: {AgentRole.MAINTAINER_SUPPORT: 1.0, AgentRole.RESIDENT_ENGINEER: 0.5},
            TaskType.DESIGN: {AgentRole.RESIDENT_ENGINEER: 0.7, AgentRole.REVIEWER: 0.6},
            TaskType.PERFORMANCE: {AgentRole.RESIDENT_ENGINEER: 0.8, AgentRole.REVIEWER: 0.4},
            TaskType.MIGRATION: {AgentRole.RESIDENT_ENGINEER: 0.7, AgentRole.REVIEWER: 0.5},
            TaskType.SECURITY: {AgentRole.RESIDENT_ENGINEER: 0.6, AgentRole.REVIEWER: 0.7},
            TaskType.RESEARCH: {AgentRole.RESEARCHER: 1.0, AgentRole.RESIDENT_ENGINEER: 0.3},
        }
        weights = role_weights.get(task.type, {})
        score += weights.get(agent.role, 0.1) * 40
        score += self._reputation.get(agent.id, 0.0) * 0.4
        if task.project in agent.projects:
            score += 20
        return score
