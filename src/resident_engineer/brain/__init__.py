"""Repository Brain — per-project memory: doctrine, architecture, precedents, playbook."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
import hashlib
import json


class DoctrineType(str, Enum):
    DESIGN = "design"
    COMPATIBILITY = "compatibility"
    DEPENDENCIES = "dependencies"
    CONTRIBUTION = "contribution"
    TESTING = "testing"
    STYLE = "style"


@dataclass
class Doctrine:
    type: DoctrineType
    rule: str
    source: str
    confidence: float = 0.8
    evidence: list[str] = field(default_factory=list)


@dataclass
class ArchitectureComponent:
    name: str
    path: str
    purpose: str
    dependencies: list[str] = field(default_factory=list)
    public_api: list[str] = field(default_factory=list)
    tests: list[str] = field(default_factory=list)


@dataclass
class Precedent:
    pr_number: int
    title: str
    outcome: str
    approach: str
    maintainer_feedback: str
    lesson: str
    confidence: float = 0.5


@dataclass
class PlaybookEntry:
    trigger: str
    action: str
    verification: str
    exceptions: list[str] = field(default_factory=list)


@dataclass
class RepositoryBrain:
    project: str
    url: str
    created_at: datetime = field(default_factory=datetime.now)
    doctrine: list[Doctrine] = field(default_factory=list)
    architecture: list[ArchitectureComponent] = field(default_factory=list)
    precedents: list[Precedent] = field(default_factory=list)
    playbook: list[PlaybookEntry] = field(default_factory=list)
    failure_patterns: list[dict[str, Any]] = field(default_factory=list)
    maintainer_preferences: list[str] = field(default_factory=list)
    compatibility_constraints: list[str] = field(default_factory=list)
    test_topology: dict[str, Any] = field(default_factory=dict)
    ownership: dict[str, str] = field(default_factory=dict)

    @property
    def id(self) -> str:
        return hashlib.sha256(f"{self.project}:{self.url}".encode()).hexdigest()[:12]

    def add_doctrine(self, d: Doctrine) -> None:
        self.doctrine.append(d)

    def add_architecture(self, a: ArchitectureComponent) -> None:
        self.architecture.append(a)

    def add_precedent(self, p: Precedent) -> None:
        self.precedents.append(p)

    def add_playbook_entry(self, e: PlaybookEntry) -> None:
        self.playbook.append(e)

    def get_relevant_doctrine(self, tags: list[str]) -> list[Doctrine]:
        return [d for d in self.doctrine if any(t in d.rule.lower() for t in tags)]

    def get_relevant_precedents(self, approach: str) -> list[Precedent]:
        return sorted(self.precedents, key=lambda p: p.confidence, reverse=True)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "project": self.project,
            "url": self.url,
            "created_at": self.created_at.isoformat(),
            "doctrine": [
                {"type": d.type.value, "rule": d.rule, "source": d.source, "confidence": d.confidence, "evidence": d.evidence}
                for d in self.doctrine
            ],
            "architecture": [
                {"name": a.name, "path": a.path, "purpose": a.purpose, "dependencies": a.dependencies, "public_api": a.public_api, "tests": a.tests}
                for a in self.architecture
            ],
            "precedents": [
                {"pr_number": p.pr_number, "title": p.title, "outcome": p.outcome, "approach": p.approach, "maintainer_feedback": p.maintainer_feedback, "lesson": p.lesson, "confidence": p.confidence}
                for p in self.precedents
            ],
            "playbook": [
                {"trigger": e.trigger, "action": e.action, "verification": e.verification, "exceptions": e.exceptions}
                for e in self.playbook
            ],
            "failure_patterns": self.failure_patterns,
            "maintainer_preferences": self.maintainer_preferences,
            "compatibility_constraints": self.compatibility_constraints,
            "test_topology": self.test_topology,
            "ownership": self.ownership,
        }
