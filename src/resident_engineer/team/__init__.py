"""Team Formation — dynamic assembly of agent teams for tasks."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class TeamType(str, Enum):
    BUG_FIX = "bug-fix"
    FEATURE = "feature"
    REFACTOR = "refactor"
    REVIEW = "review"
    RESEARCH = "research"
    MAINTENANCE = "maintenance"
    SECURITY = "security"
    PERFORMANCE = "performance"


class TeamStatus(str, Enum):
    FORMING = "forming"
    ACTIVE = "active"
    COMPLETED = "completed"
    DISSOLVED = "dissolved"


@dataclass
class Team:
    id: str
    name: str
    type: TeamType
    members: list[str] = field(default_factory=list)
    leader: str | None = None
    status: TeamStatus = TeamStatus.FORMING
    created_at: datetime = field(default_factory=datetime.now)
    task_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_member(self, agent_id: str) -> None:
        if agent_id not in self.members:
            self.members.append(agent_id)

    def remove_member(self, agent_id: str) -> None:
        if agent_id in self.members:
            self.members.remove(agent_id)

    def activate(self) -> None:
        self.status = TeamStatus.ACTIVE

    def complete(self) -> None:
        self.status = TeamStatus.COMPLETED

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "members": self.members,
            "leader": self.leader,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "task_id": self.task_id,
            "metadata": self.metadata,
        }


class TeamFormation:
    """Forms teams dynamically based on task requirements."""

    def __init__(self) -> None:
        self._teams: dict[str, Team] = {}

    def form_team(
        self,
        name: str,
        type: TeamType,
        required_roles: list[str],
        available_agents: dict[str, Any],
        task_id: str | None = None,
    ) -> Team:
        """Form a team by selecting agents with required roles."""
        members = []
        leader = None

        for agent_id, agent_data in available_agents.items():
            role = agent_data.get("role", "")
            if role in required_roles:
                members.append(agent_id)
                if leader is None and role == required_roles[0]:
                    leader = agent_id

        team = Team(
            id=f"team-{len(self._teams)+1}",
            name=name,
            type=type,
            members=members,
            leader=leader,
            task_id=task_id,
        )
        self._teams[team.id] = team
        return team

    def get(self, team_id: str) -> Team | None:
        return self._teams.get(team_id)

    def get_by_type(self, type: TeamType) -> list[Team]:
        return [t for t in self._teams.values() if t.type == type]

    def to_dict(self) -> dict[str, Any]:
        return {k: v.to_dict() for k, v in self._teams.items()}
