"""Agent Identity — every bot has a unique identity, history, and certifications."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
import hashlib
import json


class AgentRole(str, Enum):
    RESIDENT_ENGINEER = "resident-engineer"
    REVIEWER = "reviewer"
    RESEARCHER = "researcher"
    COORDINATOR = "coordinator"
    MAINTAINER_SUPPORT = "maintainer-support"
    GUILD_LEADER = "guild-leader"
    INSTITUTION_ADMIN = "institution-admin"


class CertificationLevel(str, Enum):
    NONE = "none"
    NOVICE = "novice"
    CONTRIBUTOR = "contributor"
    TRUSTED = "trusted"
    EXPERT = "expert"
    MAINTAINER = "maintainer"


@dataclass
class Certification:
    id: str
    name: str
    level: CertificationLevel
    project: str
    issued_at: datetime
    evidence: dict[str, Any]
    expires_at: datetime | None = None
    issuer: str = ""


@dataclass
class AgentIdentity:
    name: str
    role: AgentRole
    created_at: datetime = field(default_factory=datetime.now)
    certifications: list[Certification] = field(default_factory=list)
    reputation_score: float = 0.0
    projects: list[str] = field(default_factory=list)
    guilds: list[str] = field(default_factory=list)
    institutions: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def id(self) -> str:
        raw = f"{self.name}:{self.role.value}:{self.created_at.isoformat()}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def add_certification(self, cert: Certification) -> None:
        self.certifications.append(cert)

    def update_reputation(self, delta: float) -> None:
        self.reputation_score = max(0.0, min(100.0, self.reputation_score + delta))

    def join_guild(self, guild_id: str) -> None:
        if guild_id not in self.guilds:
            self.guilds.append(guild_id)

    def join_institution(self, inst_id: str) -> None:
        if inst_id not in self.institutions:
            self.institutions.append(inst_id)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role.value,
            "created_at": self.created_at.isoformat(),
            "certifications": [
                {
                    "id": c.id,
                    "name": c.name,
                    "level": c.level.value,
                    "project": c.project,
                    "issued_at": c.issued_at.isoformat(),
                    "evidence": c.evidence,
                    "expires_at": c.expires_at.isoformat() if c.expires_at else None,
                    "issuer": c.issuer,
                }
                for c in self.certifications
            ],
            "reputation_score": self.reputation_score,
            "projects": self.projects,
            "guilds": self.guilds,
            "institutions": self.institutions,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AgentIdentity:
        agent = cls(
            name=data["name"],
            role=AgentRole(data["role"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            reputation_score=data.get("reputation_score", 0.0),
            projects=data.get("projects", []),
            guilds=data.get("guilds", []),
            institutions=data.get("institutions", []),
            metadata=data.get("metadata", {}),
        )
        for c in data.get("certifications", []):
            agent.certifications.append(
                Certification(
                    id=c["id"],
                    name=c["name"],
                    level=CertificationLevel(c["level"]),
                    project=c["project"],
                    issued_at=datetime.fromisoformat(c["issued_at"]),
                    evidence=c.get("evidence", {}),
                    expires_at=datetime.fromisoformat(c["expires_at"]) if c.get("expires_at") else None,
                    issuer=c.get("issuer", ""),
                )
            )
        return agent
