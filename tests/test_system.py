"""Tests for the Resident Engineering System v2."""
from __future__ import annotations

import pytest
from datetime import datetime

from resident_engineer.kernel.identity import AgentIdentity, AgentRole, Certification, CertificationLevel
from resident_engineer.kernel.communication import MessageBus, Message, MessageType, MessagePriority
from resident_engineer.kernel.workflow import WorkflowEngine, WorkflowStep, StepStatus
from resident_engineer.kernel.knowledge import KnowledgeGraph, KnowledgeItem, KnowledgeType
from resident_engineer.kernel.reputation import ReputationLedger, ReputationEvent, OutcomeType
from resident_engineer.kernel.learning import LearningLoop, LearningItem, LearningType
from resident_engineer.brain import RepositoryBrain, Doctrine, DoctrineType, Precedent, PlaybookEntry
from resident_engineer.admission import TaskAdmission, AdmissionDecision, RejectionReason
from resident_engineer.cell import EngineeringCell, PlanCandidate, BuildResult, ReviewResult
from resident_engineer.court import VerificationCourt, VerificationCheck, CheckType, Verdict
from resident_engineer.pr import ProofCarryingPR, Evidence, PRStatus
from resident_engineer.bots import create_resident_engineer, create_reviewer
from resident_engineer.citizens import CitizensRegistry, Citizen, CitizenshipStatus
from resident_engineer.guilds import GuildRegistry, Guild, GuildType
from resident_engineer.institutions import InstitutionRegistry, Institution, InstitutionType, InstitutionRule, RuleSeverity
from resident_engineer.team import TeamFormation, Team, TeamType, TeamStatus
from resident_engineer.routing import TaskRouter, Task, TaskType, RouteDecision
from resident_engineer.ace import ACEEngine, ACEPlaybook, PlaybookEntry, PlaybookEntryType
from resident_engineer.gepa import GEPAEngine, PromptCandidate, GEPAIteration
from resident_engineer.lightning import AgentLightning, TrainingRun, TrainingExample, TrainingStatus
from resident_engineer.certification import CertificationDatabase, CertificationRecord, CertificationType, CertificationStatus
from resident_engineer.system import ResidentEngineeringSystem


class TestAgentIdentity:
    def test_create_agent(self):
        agent = AgentIdentity(name="test", role=AgentRole.RESIDENT_ENGINEER)
        assert agent.name == "test"
        assert agent.role == AgentRole.RESIDENT_ENGINEER
        assert agent.reputation_score == 0.0
        assert len(agent.id) == 16

    def test_add_certification(self):
        agent = AgentIdentity(name="test", role=AgentRole.RESIDENT_ENGINEER)
        cert = Certification(id="cert-1", name="Test Cert", level=CertificationLevel.CONTRIBUTOR, project="test-project", issued_at=datetime.now(), evidence={"test": "passed"})
        agent.add_certification(cert)
        assert len(agent.certifications) == 1

    def test_update_reputation(self):
        agent = AgentIdentity(name="test", role=AgentRole.RESIDENT_ENGINEER)
        agent.update_reputation(10.0)
        assert agent.reputation_score == 10.0
        agent.update_reputation(-5.0)
        assert agent.reputation_score == 5.0
        agent.update_reputation(-100.0)
        assert agent.reputation_score == 0.0
        agent.update_reputation(200.0)
        assert agent.reputation_score == 100.0

    def test_serialization(self):
        agent = AgentIdentity(name="test", role=AgentRole.RESIDENT_ENGINEER)
        agent.update_reputation(50.0)
        data = agent.to_dict()
        restored = AgentIdentity.from_dict(data)
        assert restored.name == agent.name
        assert restored.role == agent.role
        assert restored.reputation_score == agent.reputation_score


class TestMessageBus:
    def test_publish_subscribe(self):
        bus = MessageBus()
        received = []
        bus.subscribe("test-topic", lambda m: received.append(m))
        bus.start()
        msg = Message(sender="a", recipient="test-topic", type=MessageType.STATUS_UPDATE, payload={})
        bus.publish(msg)
        import time
        time.sleep(0.2)
        bus.stop()
        assert len(received) == 1

    def test_priority_ordering(self):
        bus = MessageBus()
        received = []
        bus.subscribe("test-topic", lambda m: received.append(m))
        bus.start()
        bus.publish(Message(sender="a", recipient="test-topic", type=MessageType.STATUS_UPDATE, payload={}, priority=MessagePriority.LOW))
        bus.publish(Message(sender="b", recipient="test-topic", type=MessageType.STATUS_UPDATE, payload={}, priority=MessagePriority.HIGH))
        bus.publish(Message(sender="c", recipient="test-topic", type=MessageType.STATUS_UPDATE, payload={}, priority=MessagePriority.NORMAL))
        import time
        time.sleep(0.3)
        bus.stop()
        assert len(received) == 3
        assert received[0].sender == "b"
        assert received[1].sender == "c"
        assert received[2].sender == "a"


class TestWorkflowEngine:
    def test_simple_workflow(self):
        engine = WorkflowEngine()
        results = []
        engine.register_handler("action-a", lambda step, ctx: results.append("a") or {"result": "a"})
        engine.register_handler("action-b", lambda step, ctx: results.append("b") or {"result": "b"})
        steps = [WorkflowStep(name="step-a", agent="agent-1", action="action-a"), WorkflowStep(name="step-b", agent="agent-1", action="action-b", depends_on=["step-a"])]
        wf = engine.create_workflow("test", steps)
        result = engine.execute(wf.id)
        assert result.is_complete()
        assert results == ["a", "b"]


class TestKnowledgeGraph:
    def test_add_and_query(self):
        kg = KnowledgeGraph()
        item = KnowledgeItem(id="k1", type=KnowledgeType.DOCTRINE, project="test-project", content={"rule": "no global state"}, confidence=0.9)
        kg.add(item)
        results = kg.query(project="test-project")
        assert len(results) == 1


class TestReputationLedger:
    def test_record_and_score(self):
        ledger = ReputationLedger()
        ledger.record(ReputationEvent(agent_id="a1", project="p1", outcome=OutcomeType.PR_MERGED, delta=10.0, evidence={}))
        assert ledger.get_score("a1") == 10.0


class TestTaskRouter:
    def test_route_by_role(self):
        router = TaskRouter()
        re = create_resident_engineer()
        rv = create_reviewer()
        router.register_agent(re, 50.0)
        router.register_agent(rv, 30.0)
        task = Task(id="t1", type=TaskType.BUG_FIX, project="p1", description="fix bug", requirements={})
        decision = router.route(task)
        assert decision.agent_id == re.id


class TestCitizens:
    def test_register_and_promote(self):
        registry = CitizensRegistry()
        citizen = registry.register("agent-1")
        assert citizen.status == CitizenshipStatus.RESIDENT
        registry.record_contribution("agent-1", 1.0)
        assert citizen.contributions_count == 1


class TestGuilds:
    def test_create_guild(self):
        registry = GuildRegistry()
        guild = registry.create("Test Guild", GuildType.ENGINEERING, "Test description")
        assert guild.name == "Test Guild"
        assert guild.type == GuildType.ENGINEERING


class TestInstitutions:
    def test_create_institution(self):
        registry = InstitutionRegistry()
        inst = registry.create("Test Inst", InstitutionType.PROJECT, "Test description")
        assert inst.name == "Test Inst"
        assert inst.type == InstitutionType.PROJECT


class TestTeamFormation:
    def test_form_team(self):
        formation = TeamFormation()
        agents = {"a1": {"role": "resident-engineer"}, "a2": {"role": "reviewer"}}
        team = formation.form_team("Test Team", TeamType.BUG_FIX, ["resident-engineer", "reviewer"], agents)
        assert len(team.members) == 2


class TestACE:
    def test_create_playbook(self):
        engine = ACEEngine()
        pb = engine.create_playbook("Test", "test-project")
        assert pb.name == "Test"
        assert pb.project == "test-project"


class TestGEPA:
    def test_initialize(self):
        engine = GEPAEngine(population_size=5)
        engine.initialize("Base prompt")
        assert len(engine._population) == 5


class TestLightning:
    def test_start_training(self):
        engine = AgentLightning()
        run = engine.start_training("agent-1")
        assert run.status == TrainingStatus.TRAINING


class TestCertification:
    def test_issue_certification(self):
        db = CertificationDatabase()
        cert = db.issue("agent-1", "Test Cert", CertificationType.BUG_FIX, "level-1", "test-project", {})
        assert cert.name == "Test Cert"
        assert cert.verify()


class TestResidentEngineeringSystem:
    def test_register_agent(self):
        system = ResidentEngineeringSystem()
        agent = create_resident_engineer()
        system.register_agent(agent)
        assert agent.id in system.agents

    def test_submit_task_accept(self):
        system = ResidentEngineeringSystem()
        agent = create_resident_engineer()
        system.register_agent(agent)
        result = system.submit_task(title="Fix CSV exporter escaped quotes handling", description="The CSV exporter does not handle escaped quotes properly. When a field contains a quote character, the output is malformed. Steps to reproduce: 1. Create CSV with escaped quotes 2. Export 3. Verify output is correct.", project="test-project")
        assert result["status"] == "accepted"

    def test_submit_task_reject(self):
        system = ResidentEngineeringSystem()
        agent = create_resident_engineer()
        system.register_agent(agent)
        result = system.submit_task(title="Fix something", description="Something is broken maybe.", project="test-project")
        assert result["status"] == "rejected"

    def test_record_outcome(self):
        system = ResidentEngineeringSystem()
        agent = create_resident_engineer()
        system.register_agent(agent)
        system.record_outcome(agent_id=agent.id, project="test-project", outcome=OutcomeType.PR_MERGED, delta=10.0, evidence={"pr_number": 100})
        assert system.reputation_ledger.get_score(agent.id) == 10.0
