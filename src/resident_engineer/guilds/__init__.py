"""Guilds — groups of agents with shared goals and collaboration."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class GuildType(str, Enum):
    ENGINEERING = "engineering"
    RESEARCH = "research"
    REVIEW = "review"
    DOCUMENTATION = "documentation"
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTENANCE = "maintenance"


@dataclass
class Guild:
    id: str
    name: str
    type: GuildType
    description: str
    members: list[str] = field(default_factory=list)
    leader: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    goals: list[str] = field(default_factory=list)
    rules: list[str] = field(default_factory=list)
    reputation: float = 0.0

    def add_member(self, agent_id: str) -> None:
        if agent_id not in self.members:
            self.members.append(agent_id)

    def remove_member(self, agent_id: str) -> None:
        if agent_id in self.members:
            self.members.remove(agent_id)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "description": self.description,
            "members": self.members,
            "leader": self.leader,
            "created_at": self.created_at.isoformat(),
            "goals": self.goals,
            "rules": self.rules,
            "reputation": self.reputation,
        }


class GuildRegistry:
    """Manages guilds and their members."""

    def __init__(self) -> None:
        self._guilds: dict[str, Guild] = {}

    def create(self, name: str, type: GuildType, description: str, leader: str | None = None) -> Guild:
        guild = Guild(
            id=f"guild-{len(self._guilds)+1}",
            name=name,
            type=type,
            description=description,
            leader=leader,
        )
        self._guilds[guild.id] = guild
        return guild

    def get(self, guild_id: str) -> Guild | None:
        return self._guilds.get(guild_id)

    def add_member(self, guild_id: str, agent_id: str) -> None:
        if guild_id in self._guilds:
            self._guilds[guild_id].add_member(agent_id)

    def get_by_type(self, type: GuildType) -> list[Guild]:
        return [g for g in self._guilds.values() if g.type == type]

    def to_dict(self) -> dict[str, Any]:
        return {k: v.to_dict() for k, v in self._guilds.items()}
