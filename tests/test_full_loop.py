"""Full-loop wiring tests — the PR outcome reaches the brain.

apply_pr_outcome was the missing seam: system.record_outcome fed reputation +
the learning loop, but a PR's merged/rejected result never reached the brain's
precedents/failure_patterns — the structures the resident step reads next time.
These pin the closed loop end to end.
"""
from __future__ import annotations

from resident_engineer.system import ResidentEngineeringSystem
from resident_engineer.bots import create_resident_engineer
from resident_engineer.brain import RepositoryBrain, Doctrine, DoctrineType


def _system() -> tuple[ResidentEngineeringSystem, RepositoryBrain]:
    s = ResidentEngineeringSystem()
    s.register_agent(create_resident_engineer("resident-engineer"))
    brain = RepositoryBrain(project="some/repo", url="https://github.com/some/repo")
    s.register_brain(brain)
    return s, brain


class TestApplyPrOutcome:
    def test_merged_reaches_brain_as_precedent(self):
        s, brain = _system()
        r = s.apply_pr_outcome("some/repo", 10, "fix", "name the key", "merged",
                               maintainer_feedback="nice")
        assert r["recorded"] == "precedent"
        assert len(brain.precedents) == 1   # landed on the brain

    def test_rejected_reaches_brain_as_failure(self):
        s, brain = _system()
        r = s.apply_pr_outcome("some/repo", 11, "big refactor", "rewrite", "rejected",
                               maintainer_feedback="too large")
        assert r["recorded"] == "failure_pattern"
        assert len(brain.failure_patterns) == 1

    def test_unknown_outcome_records_nothing(self):
        s, brain = _system()
        r = s.apply_pr_outcome("some/repo", 12, "x", "y", "abandoned")
        assert r["recorded"] is None
        assert brain.precedents == [] and brain.failure_patterns == []

    def test_no_brain_returns_empty(self):
        s = ResidentEngineeringSystem()   # no brain registered
        assert s.apply_pr_outcome("unknown/repo", 1, "x", "y", "merged") == {}

    def test_precedent_informs_next_consultation(self):
        # the closed loop: an outcome lands, and the resident step sees it next
        s, brain = _system()
        s.apply_pr_outcome("some/repo", 13, "fix", "name the key", "merged",
                           maintainer_feedback="good")
        ctx = s.consult_brain("some/repo", "similar fix")
        # precedents are on the brain the consult reads
        assert len(brain.precedents) == 1
        assert ctx["has_brain"] is True
