"""Institutions — formal rules and governance for projects."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class InstitutionType(str, Enum):
    PROJECT = "project"
    COMMUNITY = "community"
    STANDARDS = "standards"
    ETHICS = "ethics"
    CERTIFICATION = "certification"


class RuleSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class InstitutionRule:
    id: str
    name: str
    description: str
    severity: RuleSeverity
    condition: str
    action: str
    exceptions: list[str] = field(default_factory=list)


@dataclass
class Institution:
    id: str
    name: str
    type: InstitutionType
    description: str
    rules: list[InstitutionRule] = field(default_factory=list)
    members: list[str] = field(default_factory=list)
    admins: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_rule(self, rule: InstitutionRule) -> None:
        self.rules.append(rule)

    def check_compliance(self, action: str, context: dict[str, Any]) -> list[InstitutionRule]:
        """Check if an action complies with institution rules."""
        violations = []
        for rule in self.rules:
            if rule.condition in action:
                violations.append(rule)
        return violations

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "description": self.description,
            "rules": [
                {
                    "id": r.id,
                    "name": r.name,
                    "description": r.description,
                    "severity": r.severity.value,
                    "condition": r.condition,
                    "action": r.action,
                    "exceptions": r.exceptions,
                }
                for r in self.rules
            ],
            "members": self.members,
            "admins": self.admins,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }


class InstitutionRegistry:
    """Manages institutions and their rules."""

    def __init__(self) -> None:
        self._institutions: dict[str, Institution] = {}

    def create(self, name: str, type: InstitutionType, description: str) -> Institution:
        inst = Institution(
            id=f"inst-{len(self._institutions)+1}",
            name=name,
            type=type,
            description=description,
        )
        self._institutions[inst.id] = inst
        return inst

    def get(self, inst_id: str) -> Institution | None:
        return self._institutions.get(inst_id)

    def check_all(self, action: str, context: dict[str, Any]) -> list[tuple[Institution, InstitutionRule]]:
        """Check action against all institutions."""
        violations = []
        for inst in self._institutions.values():
            for rule in inst.check_compliance(action, context):
                violations.append((inst, rule))
        return violations

    def to_dict(self) -> dict[str, Any]:
        return {k: v.to_dict() for k, v in self._institutions.items()}
