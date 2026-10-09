"""Workflow Engine — Temporal-inspired durable execution for complex multi-step tasks."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable
import uuid


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


@dataclass
class WorkflowStep:
    name: str
    agent: str
    action: str
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)
    status: StepStatus = StepStatus.PENDING
    result: dict[str, Any] | None = None
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    retry_count: int = 0
    max_retries: int = 3
    timeout_seconds: float = 300.0


@dataclass
class Workflow:
    name: str
    steps: list[WorkflowStep]
    created_at: datetime = field(default_factory=datetime.now)
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    status: StepStatus = StepStatus.PENDING
    input_data: dict[str, Any] = field(default_factory=dict)
    output_data: dict[str, Any] = field(default_factory=dict)

    def get_ready_steps(self) -> list[WorkflowStep]:
        completed = {s.name for s in self.steps if s.status == StepStatus.COMPLETED}
        return [
            s for s in self.steps
            if s.status == StepStatus.PENDING
            and all(dep in completed for dep in s.depends_on)
        ]

    def is_complete(self) -> bool:
        return all(s.status in (StepStatus.COMPLETED, StepStatus.SKIPPED, StepStatus.CANCELLED) for s in self.steps)

    def has_failures(self) -> bool:
        return any(s.status == StepStatus.FAILED for s in self.steps)


class WorkflowEngine:
    """Executes workflows with retry logic and durable state."""

    def __init__(self) -> None:
        self._workflows: dict[str, Workflow] = {}
        self._handlers: dict[str, Callable[[WorkflowStep, dict[str, Any]], dict[str, Any]]] = {}

    def register_handler(self, action: str, handler: Callable) -> None:
        self._handlers[action] = handler

    def create_workflow(self, name: str, steps: list[WorkflowStep], input_data: dict[str, Any] | None = None) -> Workflow:
        wf = Workflow(name=name, steps=steps, input_data=input_data or {})
        self._workflows[wf.id] = wf
        return wf

    def execute(self, workflow_id: str) -> Workflow:
        wf = self._workflows[workflow_id]
        wf.status = StepStatus.RUNNING
        context = dict(wf.input_data)

        while not wf.is_complete() and not wf.has_failures():
            ready = wf.get_ready_steps()
            if not ready:
                break
            for step in ready:
                step.status = StepStatus.RUNNING
                step.started_at = datetime.now()
                try:
                    handler = self._handlers.get(step.action)
                    if not handler:
                        raise RuntimeError(f"No handler for action: {step.action}")
                    step.result = handler(step, context)
                    step.status = StepStatus.COMPLETED
                    context[f"step_{step.name}"] = step.result
                except Exception as e:
                    if step.retry_count < step.max_retries:
                        step.retry_count += 1
                        step.status = StepStatus.RETRYING
                    else:
                        step.status = StepStatus.FAILED
                        step.error = str(e)
                step.completed_at = datetime.now()

        wf.output_data = context
        if wf.has_failures():
            wf.status = StepStatus.FAILED
        else:
            wf.status = StepStatus.COMPLETED
        return wf
