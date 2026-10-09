"""Certification Database — stores and verifies agent certifications."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
import hashlib
import json


class CertificationStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    PENDING = "pending"


class CertificationType(str, Enum):
    BUG_FIX = "bug-fix"
    FEATURE = "feature"
    REVIEW = "review"
    SECURITY = "security"
    PERFORMANCE = "performance"
    DOCUMENTATION = "documentation"
    MAINTENANCE = "maintenance"
    MENTORSHIP = "mentorship"


@dataclass
class CertificationRecord:
    id: str
    agent_id: str
    name: str
    type: CertificationType
    level: str
    project: str
    status: CertificationStatus = CertificationStatus.ACTIVE
    issued_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime | None = None
    revoked_at: datetime | None = None
    evidence: dict[str, Any] = field(default_factory=dict)
    issuer: str = ""
    signature: str = ""

    def verify(self) -> bool:
        """Verify certification is valid."""
        if self.status != CertificationStatus.ACTIVE:
            return False
        if self.expires_at and datetime.now() > self.expires_at:
            return False
        return True

    def revoke(self, reason: str = "") -> None:
        self.status = CertificationStatus.REVOKED
        self.revoked_at = datetime.now()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "name": self.name,
            "type": self.type.value,
            "level": self.level,
            "project": self.project,
            "status": self.status.value,
            "issued_at": self.issued_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
            "evidence": self.evidence,
            "issuer": self.issuer,
            "signature": self.signature,
        }


class CertificationDatabase:
    """Manages certifications with verification."""

    def __init__(self) -> None:
        self._certifications: dict[str, CertificationRecord] = {}

    def issue(
        self,
        agent_id: str,
        name: str,
        type: CertificationType,
        level: str,
        project: str,
        evidence: dict[str, Any],
        issuer: str = "",
        expires_at: datetime | None = None,
    ) -> CertificationRecord:
        cert_id = hashlib.sha256(
            f"{agent_id}:{name}:{project}:{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]

        cert = CertificationRecord(
            id=cert_id,
            agent_id=agent_id,
            name=name,
            type=type,
            level=level,
            project=project,
            expires_at=expires_at,
            evidence=evidence,
            issuer=issuer,
        )
        self._certifications[cert_id] = cert
        return cert

    def get(self, cert_id: str) -> CertificationRecord | None:
        return self._certifications.get(cert_id)

    def verify(self, cert_id: str) -> bool:
        cert = self._certifications.get(cert_id)
        if not cert:
            return False
        return cert.verify()

    def revoke(self, cert_id: str, reason: str = "") -> bool:
        cert = self._certifications.get(cert_id)
        if cert:
            cert.revoke(reason)
            return True
        return False

    def get_by_agent(self, agent_id: str) -> list[CertificationRecord]:
        return [c for c in self._certifications.values() if c.agent_id == agent_id]

    def get_by_project(self, project: str) -> list[CertificationRecord]:
        return [c for c in self._certifications.values() if c.project == project]

    def get_by_type(self, type: CertificationType) -> list[CertificationRecord]:
        return [c for c in self._certifications.values() if c.type == type]

    def get_active(self) -> list[CertificationRecord]:
        return [c for c in self._certifications.values() if c.verify()]

    def to_dict(self) -> dict[str, Any]:
        return {k: v.to_dict() for k, v in self._certifications.items()}
