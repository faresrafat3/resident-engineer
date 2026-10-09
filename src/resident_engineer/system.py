"""Resident Engineering System v2 — main orchestrator."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
import json

from .kernel.identity import AgentIdentity, AgentRole
from .kernel.communication import MessageBus, Message, MessageType
from .kernel.workflow import WorkflowEngine, WorkflowStep, Workflow
from .kernel.knowledge import KnowledgeGraph, KnowledgeItem, KnowledgeType
from .kernel.reputation import ReputationLedger, ReputationEvent, OutcomeType
from .routing import TaskRouter, Task, TaskType, RouteDecision
from .kernel.learning import LearningLoop, LearningItem, LearningType
from .brain import RepositoryBrain
from .admission import TaskAdmission, AdmissionResult, AdmissionDecision
from .cell import EngineeringCell, PlanCandidate, BuildResult, ReviewResult
from .court import VerificationCourt, VerificationCheck, CheckType, CourtResult
from .pr import ProofCarryingPR, Evidence, PRStatus
from .bots import create_resident_engineer, create_reviewer
from .citizens import CitizensRegistry, Citizen, CitizenshipStatus
from .guilds import GuildRegistry, Guild, GuildType
from .institutions import InstitutionRegistry, Institution, InstitutionType, InstitutionRule, RuleSeverity
from .team import TeamFormation, Team, TeamType, TeamStatus
from .routing import TaskRouter as AdvancedRouter
from .ace import ACEEngine, ACEPlaybook, PlaybookEntry, PlaybookEntryType
from .gepa import GEPAEngine, PromptCandidate, GEPAIteration
from .lightning import AgentLightning, TrainingRun, TrainingExample, TrainingStatus
from .certification import CertificationDatabase, CertificationRecord, CertificationType, CertificationStatus


@dataclass
class ResidentEngineeringSystem:
    """The main system that orchestrates all components."""

    name: str = "resident-engineering-system"
    created_at: datetime = field(default_factory=datetime.now)
    agents: dict[str, AgentIdentity] = field(default_factory=dict)
    brains: dict[str, RepositoryBrain] = field(default_factory=dict)
    message_bus: MessageBus = field(default_factory=MessageBus)
    workflow_engine: WorkflowEngine = field(default_factory=WorkflowEngine)
    knowledge_graph: KnowledgeGraph = field(default_factory=KnowledgeGraph)
    reputation_ledger: ReputationLedger = field(default_factory=ReputationLedger)
    task_router: TaskRouter = field(default_factory=TaskRouter)
    learning_loop: LearningLoop = field(default_factory=LearningLoop)
    task_admission: TaskAdmission = field(default_factory=TaskAdmission)
    citizens: CitizensRegistry = field(default_factory=CitizensRegistry)
    guilds: GuildRegistry = field(default_factory=GuildRegistry)
    institutions: InstitutionRegistry = field(default_factory=InstitutionRegistry)
    teams: TeamFormation = field(default_factory=TeamFormation)
    ace_engine: ACEEngine = field(default_factory=ACEEngine)
    gepa_engine: GEPAEngine = field(default_factory=GEPAEngine)
    lightning: AgentLightning = field(default_factory=AgentLightning)
    certifications: CertificationDatabase = field(default_factory=CertificationDatabase)

    def register_agent(self, agent: AgentIdentity) -> None:
        self.agents[agent.id] = agent
        self.task_router.register_agent(agent, agent.reputation_score)
        self.citizens.register(agent.id)

    def register_brain(self, brain: RepositoryBrain) -> None:
        self.brains[brain.project] = brain

    def submit_task(
        self,
        title: str,
        description: str,
        project: str,
        task_type: TaskType = TaskType.BUG_FIX,
        requirements: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        task = Task(
            id=f"task-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            type=task_type,
            project=project,
            description=description,
            requirements=requirements or {},
        )
        admission = self.task_admission.evaluate(title=title, description=description, project=project)
        if admission.decision != AdmissionDecision.ACCEPT:
            return {
                "task_id": task.id,
                "status": "rejected",
                "admission": {
                    "decision": admission.decision.value,
                    "reasoning": admission.reasoning,
                    "requirements": admission.requirements,
                },
            }
        route = self.task_router.route(task)
        cell = EngineeringCell(project=project)
        return {
            "task_id": task.id,
            "status": "accepted",
            "route": {
                "agent_id": route.agent_id,
                "confidence": route.confidence,
                "reasoning": route.reasoning,
            },
            "cell": cell.to_dict(),
        }

    def record_outcome(
        self,
        agent_id: str,
        project: str,
        outcome: OutcomeType,
        delta: float,
        evidence: dict[str, Any],
    ) -> None:
        event = ReputationEvent(
            agent_id=agent_id,
            project=project,
            outcome=outcome,
            delta=delta,
            evidence=evidence,
        )
        self.reputation_ledger.record(event)
        if agent_id in self.agents:
            self.agents[agent_id].update_reputation(delta)
            self.task_router._reputation[agent_id] = self.agents[agent_id].reputation_score
        self.citizens.record_contribution(agent_id, delta)
        learning = LearningItem(
            id=f"learning-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            type=LearningType.PRECEDENT,
            project=project,
            trigger={"outcome": outcome.value, "evidence": evidence},
            lesson={"outcome": outcome.value, "delta": delta},
        )
        self.learning_loop.capture(learning)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "agents": {k: v.to_dict() for k, v in self.agents.items()},
            "brains": {k: v.to_dict() for k, v in self.brains.items()},
            "reputation": self.reputation_ledger.to_dict(),
            "learning": self.learning_loop.to_dict(),
            "citizens": self.citizens.to_dict(),
            "guilds": self.guilds.to_dict(),
            "institutions": self.institutions.to_dict(),
            "teams": self.teams.to_dict(),
            "ace": self.ace_engine.to_dict(),
            "gepa": self.gepa_engine.to_dict(),
            "lightning": self.lightning.to_dict(),
            "certifications": self.certifications.to_dict(),
        }
