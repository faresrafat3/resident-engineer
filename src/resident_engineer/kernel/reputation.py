"""Reputation Ledger — global reputation across projects."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class OutcomeType(str, Enum):
    PR_MERGED = "pr-merged"
    PR_REJECTED = "pr-rejected"
    BUG_FIXED = "bug-fixed"
    BUG_REINTRODUCED = "bug-reintroduced"
    REVIEW_HELPFUL = "review-helpful"
    REVIEW_MISSED = "review-missed"
    TEST_ADDED = "test-added"
    TEST_BROKEN = "test-broken"
    DOCS_IMPROVED = "docs-improved"
    CI_FIXED = "ci-fixed"
    GUILD_CONTRIBUTION = "guild-contribution"
    INSTITUTION_VIOLATION = "institution-violation"
    CERTIFICATION_EARNED = "certification-earned"


@dataclass
class ReputationEvent:
    agent_id: str
    project: str
    outcome: OutcomeType
    delta: float
    evidence: dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)


class ReputationLedger:
    """Tracks reputation scores across all projects."""

    def __init__(self) -> None:
        self._events: list[ReputationEvent] = []
        self._scores: dict[str, float] = {}

    def record(self, event: ReputationEvent) -> None:
        self._events.append(event)
        current = self._scores.get(event.agent_id, 0.0)
        self._scores[event.agent_id] = max(0.0, min(100.0, current + event.delta))

    def get_score(self, agent_id: str) -> float:
        return self._scores.get(agent_id, 0.0)

    def get_events(
        self,
        agent_id: str | None = None,
        project: str | None = None,
        outcome: OutcomeType | None = None,
    ) -> list[ReputationEvent]:
        results = self._events
        if agent_id:
            results = [e for e in results if e.agent_id == agent_id]
        if project:
            results = [e for e in results if e.project == project]
        if outcome:
            results = [e for e in results if e.outcome == outcome]
        return sorted(results, key=lambda e: e.timestamp, reverse=True)

    def to_dict(self) -> dict[str, Any]:
        return {
            "scores": self._scores,
            "events": [
                {
                    "agent_id": e.agent_id,
                    "project": e.project,
                    "outcome": e.outcome.value,
                    "delta": e.delta,
                    "evidence": e.evidence,
                    "timestamp": e.timestamp.isoformat(),
                }
                for e in self._events
            ],
        }
