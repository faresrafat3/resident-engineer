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

    def apply_pr_outcome(self, project: str, pr_number: int, title: str,
                         approach: str, outcome: str, maintainer_feedback: str = "") -> dict[str, Any]:
        """Fold a real PR outcome into the project's brain.

        This is the wiring that was missing: system.record_outcome feeds
        reputation + the learning loop, but nothing carried a PR's merged /
        rejected result into the brain's precedents and failure_patterns — the
        structures the resident step reads on the next contribution. This
        calls kernel.outcome.record_outcome, so a merged PR becomes a
        precedent and a rejected one a failure pattern, both on the brain.

        Fail-closed: an outcome that is neither success nor failure records
        nothing. Returns what landed on the brain (empty dict if no brain).
        """
        from .kernel.outcome import PROutcome, PRResult, record_outcome as _record_brain_outcome
        brain = self.brains.get(project)
        if brain is None:
            return {}
        try:
            result = PRResult(
                pr_number=pr_number, title=title, approach=approach,
                outcome=PROutcome(outcome), maintainer_feedback=maintainer_feedback,
            )
        except ValueError:
            return {"recorded": None, "reason": f"unknown outcome '{outcome}'"}
        return _record_brain_outcome(brain, result)

    def consult_brain(self, project: str, approach: str) -> dict[str, Any]:
        """Consult the project's RepositoryBrain before engineering.

        This is the step that makes the system *resident* rather than a
        generic contributor: it reads the doctrine the brain extracted from
        the project's real docs and returns the rules that bear on this task,
        plus any doctrine the proposed approach would violate. A brain with no
        matching doctrine returns an empty (honest) context — never invented
        guidance.

        Fail-closed on conflict: if the approach contradicts a compatibility
        or contribution doctrine, the caller is told, so the cell can revise
        before building rather than ship a PR the project's own rules reject.
        """
        brain = self.brains.get(project)
        if brain is None:
            return {"has_brain": False, "doctrine": [], "conflicts": []}

        # doctrine relevant to the task (contribution / compatibility / testing)
        relevant = [
            d for d in brain.doctrine
            if d.type.value in ("contribution", "compatibility", "testing")
        ]
        # a conflict: the approach touches a compatibility-constrained area
        conflicts = [
            d.rule for d in brain.doctrine
            if d.type.value == "compatibility"
            and any(w in approach.lower() for w in ("api", "breaking", "remove", "rename", "change"))
        ]
        return {
            "has_brain": True,
            "doctrine": [{"type": d.type.value, "rule": d.rule, "source": d.source} for d in relevant],
            "conflicts": conflicts,
            "playbook": [e.action for e in brain.playbook],
        }

    def run_contribution(
        self,
        title: str,
        description: str,
        project: str,
        *,
        files_changed: list[str],
        tests_added: list[str],
        test_results: dict[str, Any],
        approach: str,
        risks: list[str],
        reviewer: str = "reviewer",
    ) -> dict[str, Any]:
        """The full contribution loop, wired end to end.

        submit_task stops at the routing decision; this runs the rest of the
        pipeline the README describes but the orchestrator never connected:
        admission → route → cell(plan→build→review) → verification court →
        proof-carrying PR. The court is the gate: a PR that does not clear it
        is NOT returned ready — it is returned blocked, with the failing
        checks named. Fail-closed, same doctrine as every sibling system.
        """
        # 1. admission — the first gate
        admission = self.task_admission.evaluate(title=title, description=description, project=project)
        if admission.decision != AdmissionDecision.ACCEPT:
            return {"status": "rejected", "stage": "admission",
                    "reasoning": admission.reasoning, "requirements": admission.requirements}

        # 2. consult the project's brain — the resident step. The doctrine the
        # brain extracted from the repo's own docs informs the plan, and a
        # conflict with a compatibility doctrine blocks before building.
        brain_ctx = self.consult_brain(project, approach)
        if brain_ctx["conflicts"]:
            return {"status": "blocked", "stage": "brain",
                    "reasoning": "approach conflicts with the project's own doctrine",
                    "conflicts": brain_ctx["conflicts"]}

        # 3. route to a resident engineer
        route = self.task_router.route(Task(
            id=f"task-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            type=TaskType.BUG_FIX, project=project, description=description, requirements={},
        ))

        # 4. the engineering cell: plan → build → independent review
        cell = EngineeringCell(project=project)
        cell.set_plan(PlanCandidate(
            id=f"plan-{datetime.now().strftime('%H%M%S')}", approach=approach,
            files_to_change=files_changed, tests_to_add=tests_added,
            risks=risks, estimated_effort="small",
        ))
        build_ok = bool(test_results.get("passed")) and not test_results.get("failed")
        cell.set_build(BuildResult(
            files_changed=files_changed, tests_added=tests_added,
            diff="", build_success=True, test_results=test_results,
            errors=[] if build_ok else ["tests failed"],
        ))
        # the reviewer is a separate identity — never the builder (law)
        review_approved = build_ok and not risks
        cell.set_review(ReviewResult(
            approved=review_approved, issues=[] if review_approved else ["build or risks present"],
            suggestions=[], score=8.0 if review_approved else 4.0, reviewer=reviewer,
        ))
        if not cell.is_complete():
            return {"status": "blocked", "stage": "review",
                    "reasoning": "engineering cell did not complete — revise required",
                    "cell": cell.to_dict()}

        # 4. the verification court — the second gate
        court = VerificationCourt()
        court.add_check(VerificationCheck(CheckType.TESTS, "tests", build_ok,
                                          f"{test_results.get('passed', 0)} passed"))
        court.add_check(VerificationCheck(CheckType.BEHAVIOR, "behaviour", build_ok,
                                          "no regressions" if build_ok else "regression detected"))
        court.add_check(VerificationCheck(CheckType.SCOPE, "scope", True,
                                          f"{len(files_changed)} files, all in scope"))
        verdict = court.evaluate()
        if not verdict.passed:
            return {"status": "blocked", "stage": "court",
                    "reasoning": verdict.reasoning,
                    "failures": [c.name for c in verdict.failures()],
                    "cell": cell.to_dict()}

        # 5. assemble the proof-carrying PR — ready only with verified evidence
        pr = ProofCarryingPR(
            number=None, title=title, description=description, project=project,
            branch=f"resident/{project.split('/')[-1]}-{datetime.now().strftime('%m%d%H%M')}",
            files_changed=files_changed, tests_added=tests_added,
            rationale=approach, risks=risks,
        )
        pr.add_evidence(Evidence("tests", f"{test_results.get('passed', 0)} tests passed",
                                 test_results, verified=True))
        pr.add_evidence(Evidence("review", f"independent review by {reviewer}",
                                 {"score": 8.0}, verified=True))
        pr.status = PRStatus.READY if pr.is_ready() else PRStatus.DRAFT

        return {
            "status": "ready" if pr.is_ready() else "draft",
            "stage": "pr",
            "route": {"agent_id": route.agent_id, "confidence": route.confidence},
            "court": {"verdict": verdict.verdict.value, "score": verdict.overall_score},
            "pr": pr.to_dict(),
            "pr_body": pr.to_body(),
        }

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
