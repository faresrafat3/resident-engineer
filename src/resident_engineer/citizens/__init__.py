"""Citizens — agent citizenship with rights, responsibilities, and reputation."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class CitizenshipStatus(str, Enum):
    RESIDENT = "resident"
    CITIZEN = "citizen"
    SENIOR = "senior"
    HONORED = "honored"


@dataclass
class Citizen:
    agent_id: str
    status: CitizenshipStatus = CitizenshipStatus.RESIDENT
    joined_at: datetime = field(default_factory=datetime.now)
    contributions_count: int = 0
    reputation_score: float = 0.0
    rights: list[str] = field(default_factory=list)
    responsibilities: list[str] = field(default_factory=list)
    violations: list[dict[str, Any]] = field(default_factory=list)

    def promote(self) -> None:
        if self.status == CitizenshipStatus.RESIDENT:
            self.status = CitizenshipStatus.CITIZEN
        elif self.status == CitizenshipStatus.CITIZEN:
            self.status = CitizenshipStatus.SENIOR
        elif self.status == CitizenshipStatus.SENIOR:
            self.status = CitizenshipStatus.HONORED

    def add_violation(self, violation: dict[str, Any]) -> None:
        self.violations.append(violation)

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "status": self.status.value,
            "joined_at": self.joined_at.isoformat(),
            "contributions_count": self.contributions_count,
            "reputation_score": self.reputation_score,
            "rights": self.rights,
            "responsibilities": self.responsibilities,
            "violations": self.violations,
        }


class CitizensRegistry:
    """Manages agent citizenship across the system."""

    def __init__(self) -> None:
        self._citizens: dict[str, Citizen] = {}

    def register(self, agent_id: str) -> Citizen:
        citizen = Citizen(agent_id=agent_id)
        self._citizens[agent_id] = citizen
        return citizen

    def get(self, agent_id: str) -> Citizen | None:
        return self._citizens.get(agent_id)

    def promote(self, agent_id: str) -> None:
        if agent_id in self._citizens:
            self._citizens[agent_id].promote()

    def record_contribution(self, agent_id: str, delta: float = 1.0) -> None:
        if agent_id in self._citizens:
            c = self._citizens[agent_id]
            c.contributions_count += 1
            c.reputation_score += delta
            if c.contributions_count >= 10 and c.status == CitizenshipStatus.RESIDENT:
                c.promote()
            elif c.contributions_count >= 50 and c.status == CitizenshipStatus.CITIZEN:
                c.promote()
            elif c.contributions_count >= 200 and c.status == CitizenshipStatus.SENIOR:
                c.promote()

    def to_dict(self) -> dict[str, Any]:
        return {k: v.to_dict() for k, v in self._citizens.items()}
