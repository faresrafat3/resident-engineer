"""End-to-end contribution loop tests — the pipeline wired, and the gate holds.

run_contribution is the piece that connects admission → route → cell →
court → PR, which the orchestrator described but never wired. These tests
prove both directions: a clean contribution reaches a ready PR, and a failing
one is BLOCKED at the court — not quietly returned ready.
"""
from __future__ import annotations

from resident_engineer.system import ResidentEngineeringSystem
from resident_engineer.bots import create_resident_engineer
from resident_engineer.pr import PRStatus

TITLE = "Fix ValueError when config key is missing"
DESC = (
    "When the config file lacks the required key, parse_config raises a bare "
    "ValueError with no context. Reproduce: run parse_config({}) and observe "
    "the traceback. Expected: a clear error naming the missing key. I will "
    "add a regression test that verifies the error message."
)


def _system_with_engineer() -> ResidentEngineeringSystem:
    s = ResidentEngineeringSystem()
    s.register_agent(create_resident_engineer("resident-engineer"))
    return s


class TestContributionLoop:
    def test_clean_contribution_reaches_ready_pr(self):
        s = _system_with_engineer()
        r = s.run_contribution(
            TITLE, DESC, "some/repo",
            files_changed=["config.py"], tests_added=["test_config.py"],
            test_results={"passed": 12, "failed": 0},
            approach="name the missing key in the error",
            risks=[],
        )
        assert r["status"] == "ready"
        assert r["stage"] == "pr"
        assert r["pr"]["status"] == PRStatus.READY.value
        assert r["court"]["verdict"] == "pass"
        # the body carries its evidence — proof-carrying, not a bare PR
        assert "## Evidence" in r["pr_body"]
        assert "## Rationale" in r["pr_body"]

    def test_failing_tests_blocked_at_court(self):
        s = _system_with_engineer()
        r = s.run_contribution(
            TITLE, DESC, "some/repo",
            files_changed=["config.py"], tests_added=["test_config.py"],
            test_results={"passed": 10, "failed": 2},
            approach="name the missing key in the error",
            risks=[],
        )
        # the gate refuses — a PR with failing tests is never returned ready
        assert r["status"] == "blocked"
        assert r["stage"] in ("review", "court")
        assert r.get("pr") is None

    def test_risky_contribution_held_at_review(self):
        s = _system_with_engineer()
        r = s.run_contribution(
            TITLE, DESC, "some/repo",
            files_changed=["config.py"], tests_added=["test_config.py"],
            test_results={"passed": 12, "failed": 0},
            approach="touch a public API",
            risks=["changes public behaviour"],
        )
        # risks present -> independent review withholds approval -> revise
        assert r["status"] == "blocked"
        assert r["stage"] == "review"

    def test_unverifiable_task_rejected_before_work(self):
        s = _system_with_engineer()
        r = s.run_contribution(
            "fix something", "maybe it is broken somehow could be a bug maybe.",
            "some/repo",
            files_changed=["x.py"], tests_added=[], test_results={"passed": 1},
            approach="guess", risks=[],
        )
        assert r["status"] == "rejected"
        assert r["stage"] == "admission"

    def test_pr_body_lists_files_and_tests(self):
        s = _system_with_engineer()
        r = s.run_contribution(
            TITLE, DESC, "some/repo",
            files_changed=["config.py", "cli.py"], tests_added=["test_config.py"],
            test_results={"passed": 5, "failed": 0},
            approach="name the missing key", risks=[],
        )
        body = r["pr_body"]
        assert "`config.py`" in body
        assert "`cli.py`" in body
        assert "test_config.py" in body
