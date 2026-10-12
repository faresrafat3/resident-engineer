"""Brain-in-the-loop tests — the resident step that consults real doctrine.

consult_brain + its wiring into run_contribution is what makes the system
resident rather than generic: it reads the doctrine the brain extracted from
the project's own docs before engineering, and blocks an approach that
conflicts with a compatibility rule. These pin both the consult and the gate.
"""
from __future__ import annotations

from resident_engineer.system import ResidentEngineeringSystem
from resident_engineer.bots import create_resident_engineer
from resident_engineer.brain import RepositoryBrain, Doctrine, DoctrineType

TITLE = "Fix ValueError when config key is missing"
DESC = (
    "When the config file lacks the required key, parse_config raises a bare "
    "ValueError with no context. Reproduce: run parse_config({}) and observe "
    "the traceback. Expected: a clear error naming the missing key. I will "
    "add a regression test that verifies the error message."
)


def _system_with_brain(doctrines: list[Doctrine]) -> ResidentEngineeringSystem:
    s = ResidentEngineeringSystem()
    s.register_agent(create_resident_engineer("resident-engineer"))
    brain = RepositoryBrain(project="some/repo", url="https://github.com/some/repo")
    for d in doctrines:
        brain.add_doctrine(d)
    s.register_brain(brain)
    return s


class TestConsultBrain:
    def test_no_brain_is_honest_empty(self):
        s = ResidentEngineeringSystem()
        ctx = s.consult_brain("unknown/repo", "any approach")
        assert ctx["has_brain"] is False
        assert ctx["doctrine"] == []
        assert ctx["conflicts"] == []

    def test_returns_relevant_doctrine(self):
        s = _system_with_brain([
            Doctrine(DoctrineType.CONTRIBUTION, "run the gate before committing", "AGENTS.md"),
            Doctrine(DoctrineType.DESIGN, "kernel is pure", "AGENTS.md"),
        ])
        ctx = s.consult_brain("some/repo", "name the missing key")
        assert ctx["has_brain"] is True
        # contribution doctrine is relevant to a contribution; design is not returned here
        assert any("run the gate" in d["rule"] for d in ctx["doctrine"])
        assert all(d["type"] in ("contribution", "compatibility", "testing") for d in ctx["doctrine"])

    def test_detects_compatibility_conflict(self):
        s = _system_with_brain([
            Doctrine(DoctrineType.COMPATIBILITY, "never break the public API", "AGENTS.md"),
        ])
        ctx = s.consult_brain("some/repo", "rename the public API method")
        assert ctx["conflicts"]  # the approach conflicts with the doctrine

    def test_no_conflict_when_approach_is_safe(self):
        s = _system_with_brain([
            Doctrine(DoctrineType.COMPATIBILITY, "never break the public API", "AGENTS.md"),
        ])
        ctx = s.consult_brain("some/repo", "improve the error message text")
        assert ctx["conflicts"] == []


class TestContributionWithBrain:
    def test_conflicting_approach_blocked_at_brain(self):
        s = _system_with_brain([
            Doctrine(DoctrineType.COMPATIBILITY, "never break the public API", "AGENTS.md"),
        ])
        r = s.run_contribution(
            TITLE, DESC, "some/repo",
            files_changed=["config.py"], tests_added=["test_config.py"],
            test_results={"passed": 5, "failed": 0},
            approach="rename the public API and break compatibility",
            risks=[],
        )
        # the project's own doctrine blocks it before any building happens
        assert r["status"] == "blocked"
        assert r["stage"] == "brain"
        assert r.get("pr") is None

    def test_safe_approach_proceeds_past_brain(self):
        s = _system_with_brain([
            Doctrine(DoctrineType.COMPATIBILITY, "never break the public API", "AGENTS.md"),
        ])
        r = s.run_contribution(
            TITLE, DESC, "some/repo",
            files_changed=["config.py"], tests_added=["test_config.py"],
            test_results={"passed": 5, "failed": 0},
            approach="name the missing key in the error message",
            risks=[],
        )
        assert r["status"] == "ready"
