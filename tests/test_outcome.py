"""Outcome learning tests — the loop closes, and closes honestly.

record_outcome writes a PR result onto the brain as precedent or failure
pattern; apply_lessons folds unapplied LearningItems in once. Both are
fail-closed: an unclassifiable outcome records nothing, and a lesson is
applied exactly once, not on every call.
"""
from __future__ import annotations

from resident_engineer.brain import RepositoryBrain, Doctrine, DoctrineType
from resident_engineer.kernel.learning import LearningItem, LearningLoop, LearningType
from resident_engineer.kernel.outcome import PROutcome, PRResult, apply_lessons, record_outcome


def _brain() -> RepositoryBrain:
    return RepositoryBrain(project="some/repo", url="https://github.com/some/repo")


class TestRecordOutcome:
    def test_merged_writes_precedent(self):
        brain = _brain()
        r = record_outcome(brain, PRResult(1, "fix bug", "name the key", PROutcome.MERGED,
                                           maintainer_feedback="nice, thanks"))
        assert r["recorded"] == "precedent"
        assert len(brain.precedents) == 1
        # maintainer feedback raises confidence — evidence-backed
        assert brain.precedents[0].confidence >= 0.9

    def test_rejected_writes_failure_pattern(self):
        brain = _brain()
        r = record_outcome(brain, PRResult(2, "big refactor", "rewrite the module",
                                           PROutcome.REJECTED, maintainer_feedback="too large"))
        assert r["recorded"] == "failure_pattern"
        assert len(brain.failure_patterns) == 1
        assert brain.failure_patterns[0]["lesson"].startswith("avoid")

    def test_regressed_writes_failure_pattern(self):
        brain = _brain()
        record_outcome(brain, PRResult(3, "tweak", "change default", PROutcome.REGRESSED))
        assert len(brain.failure_patterns) == 1

    def test_abandoned_records_nothing(self):
        brain = _brain()
        r = record_outcome(brain, PRResult(4, "stale", "?", PROutcome.ABANDONED))
        # fail-closed: an outcome we cannot classify is NOT guessed into a slot
        assert r["recorded"] is None
        assert brain.precedents == []
        assert brain.failure_patterns == []

    def test_no_feedback_lowers_confidence(self):
        brain = _brain()
        record_outcome(brain, PRResult(5, "fix", "approach", PROutcome.MERGED))
        assert brain.precedents[0].confidence < 0.9  # unverified, stated not hidden


class TestApplyLessons:
    def test_doctrine_update_becomes_doctrine(self):
        brain = _brain()
        loop = LearningLoop()
        loop.capture(LearningItem(
            id="L1", type=LearningType.DOCTRINE_UPDATE, project="some/repo",
            trigger={}, lesson={"rule": "always run the gate", "type": "testing"},
        ))
        r = apply_lessons(brain, loop)
        assert r["applied"] == 1
        assert any("run the gate" in d.rule for d in brain.doctrine)

    def test_failure_pattern_lesson_becomes_pattern(self):
        brain = _brain()
        loop = LearningLoop()
        loop.capture(LearningItem(
            id="L2", type=LearningType.FAILURE_PATTERN, project="some/repo",
            trigger={}, lesson={"detail": "large PRs get rejected"},
        ))
        r = apply_lessons(brain, loop)
        assert r["applied"] == 1
        assert len(brain.failure_patterns) == 1

    def test_lesson_applied_exactly_once(self):
        brain = _brain()
        loop = LearningLoop()
        loop.capture(LearningItem(
            id="L3", type=LearningType.DOCTRINE_UPDATE, project="some/repo",
            trigger={}, lesson={"rule": "never force-push", "type": "contribution"},
        ))
        apply_lessons(brain, loop)
        r2 = apply_lessons(brain, loop)   # second call — nothing new to apply
        assert r2["applied"] == 0
        # and the doctrine landed exactly once, not duplicated
        assert sum(1 for d in brain.doctrine if "force-push" in d.rule) == 1

    def test_other_project_lessons_ignored(self):
        brain = _brain()
        loop = LearningLoop()
        loop.capture(LearningItem(
            id="L4", type=LearningType.DOCTRINE_UPDATE, project="other/repo",
            trigger={}, lesson={"rule": "x"},
        ))
        r = apply_lessons(brain, loop)
        assert r["applied"] == 0   # not this project's lesson
