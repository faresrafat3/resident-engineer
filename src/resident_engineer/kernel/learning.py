"""Learning Loop — learns from outcomes to improve future decisions."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class LearningType(str, Enum):
    PRECEDENT = "precedent"
    FAILURE_PATTERN = "failure-pattern"
    DOCTRINE_UPDATE = "doctrine-update"
    PLAYBOOK_UPDATE = "playbook-update"
    ROUTING_IMPROVEMENT = "routing-improvement"
    ACE_REFLECTION = "ace-reflection"
    GEPA_MUTATION = "gepa-mutation"
    LIGHTNING_TRAINING = "lightning-training"


@dataclass
class LearningItem:
    id: str
    type: LearningType
    project: str
    trigger: dict[str, Any]
    lesson: dict[str, Any]
    confidence: float = 0.5
    created_at: datetime = field(default_factory=datetime.now)
    applied: bool = False


class LearningLoop:
    """Captures lessons from outcomes and applies them to future decisions."""

    def __init__(self) -> None:
        self._items: dict[str, LearningItem] = {}

    def capture(self, item: LearningItem) -> None:
        self._items[item.id] = item

    def get_unapplied(self, project: str | None = None) -> list[LearningItem]:
        items = [i for i in self._items.values() if not i.applied]
        if project:
            items = [i for i in items if i.project == project]
        return sorted(items, key=lambda x: x.confidence, reverse=True)

    def mark_applied(self, item_id: str) -> None:
        if item_id in self._items:
            self._items[item_id].applied = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "items": [
                {
                    "id": item.id,
                    "type": item.type.value,
                    "project": item.project,
                    "trigger": item.trigger,
                    "lesson": item.lesson,
                    "confidence": item.confidence,
                    "created_at": item.created_at.isoformat(),
                    "applied": item.applied,
                }
                for item in self._items.values()
            ]
        }
