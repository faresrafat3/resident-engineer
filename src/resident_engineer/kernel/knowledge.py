"""Knowledge Graph — per-project memory with precedents, doctrine, and architecture."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
import json


class KnowledgeType(str, Enum):
    DOCTRINE = "doctrine"
    ARCHITECTURE = "architecture"
    PRECEDENT = "precedent"
    FAILURE_PATTERN = "failure-pattern"
    TEST_TOPOLOGY = "test-topology"
    MAINTAINER_PREFERENCE = "maintainer-preference"
    COMPATIBILITY = "compatibility"
    PLAYBOOK = "playbook"
    ACE_PLAYBOOK = "ace-playbook"
    GEPA_OPTIMIZATION = "gepa-optimization"


@dataclass
class KnowledgeItem:
    id: str
    type: KnowledgeType
    project: str
    content: dict[str, Any]
    confidence: float = 0.5
    source: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    evidence: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


class KnowledgeGraph:
    """Stores and retrieves project-specific knowledge."""

    def __init__(self) -> None:
        self._items: dict[str, KnowledgeItem] = {}

    def add(self, item: KnowledgeItem) -> None:
        self._items[item.id] = item

    def get(self, item_id: str) -> KnowledgeItem | None:
        return self._items.get(item_id)

    def query(
        self,
        project: str | None = None,
        type: KnowledgeType | None = None,
        tags: list[str] | None = None,
        min_confidence: float = 0.0,
    ) -> list[KnowledgeItem]:
        results = []
        for item in self._items.values():
            if project and item.project != project:
                continue
            if type and item.type != type:
                continue
            if tags and not any(t in item.tags for t in tags):
                continue
            if item.confidence < min_confidence:
                continue
            results.append(item)
        return sorted(results, key=lambda x: x.confidence, reverse=True)

    def update_confidence(self, item_id: str, delta: float) -> None:
        if item_id in self._items:
            item = self._items[item_id]
            item.confidence = max(0.0, min(1.0, item.confidence + delta))
            item.updated_at = datetime.now()

    def to_dict(self) -> dict[str, Any]:
        return {
            "items": [
                {
                    "id": item.id,
                    "type": item.type.value,
                    "project": item.project,
                    "content": item.content,
                    "confidence": item.confidence,
                    "source": item.source,
                    "created_at": item.created_at.isoformat(),
                    "updated_at": item.updated_at.isoformat(),
                    "evidence": item.evidence,
                    "tags": item.tags,
                }
                for item in self._items.values()
            ]
        }
