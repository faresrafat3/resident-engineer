"""ACE — Agentic Context Engineering.

Based on: arxiv 2510.04618
Treats contexts as evolving playbooks that accumulate, refine, and organize strategies.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
import uuid


class PlaybookEntryType(str, Enum):
    STRATEGY = "strategy"
    RULE = "rule"
    EXAMPLE = "example"
    COUNTEREXAMPLE = "counterexample"
    INSIGHT = "insight"


@dataclass
class PlaybookEntry:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    type: PlaybookEntryType = PlaybookEntryType.STRATEGY
    content: str = ""
    context: str = ""
    outcome: str = ""
    confidence: float = 0.5
    created_at: datetime = field(default_factory=datetime.now)
    usage_count: int = 0
    success_count: int = 0

    @property
    def success_rate(self) -> float:
        if self.usage_count == 0:
            return 0.0
        return self.success_count / self.usage_count


@dataclass
class ACEPlaybook:
    """Evolving playbook for a specific project or task type."""

    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    project: str = ""
    entries: list[PlaybookEntry] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def add_entry(self, entry: PlaybookEntry) -> None:
        self.entries.append(entry)
        self.updated_at = datetime.now()

    def get_relevant(self, context: str, min_confidence: float = 0.3) -> list[PlaybookEntry]:
        """Get relevant entries for a given context."""
        relevant = []
        for entry in self.entries:
            if entry.confidence < min_confidence:
                continue
            # Simple relevance: check if context keywords appear in entry
            context_words = set(context.lower().split())
            entry_words = set(entry.content.lower().split())
            overlap = len(context_words & entry_words)
            if overlap > 0:
                relevant.append(entry)
        return sorted(relevant, key=lambda e: e.confidence, reverse=True)

    def reflect(self, outcome: str, success: bool) -> None:
        """Reflect on an outcome and update playbook."""
        for entry in self.entries:
            entry.usage_count += 1
            if success:
                entry.success_count += 1
                entry.confidence = min(1.0, entry.confidence + 0.05)
            else:
                entry.confidence = max(0.0, entry.confidence - 0.03)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "project": self.project,
            "entries": [
                {
                    "id": e.id,
                    "type": e.type.value,
                    "content": e.content,
                    "context": e.context,
                    "outcome": e.outcome,
                    "confidence": e.confidence,
                    "created_at": e.created_at.isoformat(),
                    "usage_count": e.usage_count,
                    "success_count": e.success_count,
                    "success_rate": e.success_rate,
                }
                for e in self.entries
            ],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class ACEEngine:
    """Manages ACE playbooks for different projects."""

    def __init__(self) -> None:
        self._playbooks: dict[str, ACEPlaybook] = {}

    def create_playbook(self, name: str, project: str) -> ACEPlaybook:
        pb = ACEPlaybook(name=name, project=project)
        self._playbooks[pb.id] = pb
        return pb

    def get_playbook(self, pb_id: str) -> ACEPlaybook | None:
        return self._playbooks.get(pb_id)

    def get_by_project(self, project: str) -> list[ACEPlaybook]:
        return [pb for pb in self._playbooks.values() if pb.project == project]

    def to_dict(self) -> dict[str, Any]:
        return {k: v.to_dict() for k, v in self._playbooks.items()}
