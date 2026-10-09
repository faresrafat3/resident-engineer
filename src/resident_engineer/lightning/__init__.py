"""Agent Lightning — RL-based training for agents.

Based on: Microsoft Research Agent Lightning
Enables reinforcement learning-based training of any agent framework.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
import uuid


class TrainingStatus(str, Enum):
    IDLE = "idle"
    TRAINING = "training"
    EVALUATING = "evaluating"
    COMPLETED = "completed"
    FAILED = "failed"


class RewardType(str, Enum):
    BINARY = "binary"
    CONTINUOUS = "continuous"
    RANKED = "ranked"


@dataclass
class TrainingExample:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    state: dict[str, Any] = field(default_factory=dict)
    action: dict[str, Any] = field(default_factory=dict)
    reward: float = 0.0
    reward_type: RewardType = RewardType.CONTINUOUS
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TrainingRun:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    agent_id: str = ""
    status: TrainingStatus = TrainingStatus.IDLE
    examples: list[TrainingExample] = field(default_factory=list)
    total_reward: float = 0.0
    average_reward: float = 0.0
    started_at: datetime | None = None
    completed_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_example(self, example: TrainingExample) -> None:
        self.examples.append(example)
        self.total_reward += example.reward
        self.average_reward = self.total_reward / len(self.examples)

    def start(self) -> None:
        self.status = TrainingStatus.TRAINING
        self.started_at = datetime.now()

    def complete(self) -> None:
        self.status = TrainingStatus.COMPLETED
        self.completed_at = datetime.now()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "status": self.status.value,
            "examples": [
                {
                    "id": e.id,
                    "state": e.state,
                    "action": e.action,
                    "reward": e.reward,
                    "reward_type": e.reward_type.value,
                    "timestamp": e.timestamp.isoformat(),
                    "metadata": e.metadata,
                }
                for e in self.examples
            ],
            "total_reward": self.total_reward,
            "average_reward": self.average_reward,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "metadata": self.metadata,
        }


class AgentLightning:
    """RL-based training engine for agents."""

    def __init__(self) -> None:
        self._runs: dict[str, TrainingRun] = {}

    def start_training(self, agent_id: str, metadata: dict[str, Any] | None = None) -> TrainingRun:
        run = TrainingRun(agent_id=agent_id, metadata=metadata or {})
        run.start()
        self._runs[run.id] = run
        return run

    def record_example(self, run_id: str, example: TrainingExample) -> None:
        if run_id in self._runs:
            self._runs[run_id].add_example(example)

    def complete_training(self, run_id: str) -> TrainingRun | None:
        if run_id in self._runs:
            self._runs[run_id].complete()
            return self._runs[run_id]
        return None

    def get_run(self, run_id: str) -> TrainingRun | None:
        return self._runs.get(run_id)

    def get_by_agent(self, agent_id: str) -> list[TrainingRun]:
        return [r for r in self._runs.values() if r.agent_id == agent_id]

    def to_dict(self) -> dict[str, Any]:
        return {k: v.to_dict() for k, v in self._runs.items()}
