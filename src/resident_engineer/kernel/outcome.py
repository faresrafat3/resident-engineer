"""Outcome learning — turns a real PR result into a precedent or a failure
pattern, and applies unapplied lessons to the project's brain.

This closes the loop the README calls "Outcome Learning": merge / rejection /
comments / regressions feed back into the brain. Two directions, both
fail-closed:

  - record_outcome(pr, result) writes a PRECEDENT (merged/accepted) or a
    FAILURE_PATTERN (rejected/regressed) onto the RepositoryBrain, with the
    maintainer feedback as the evidence. Nothing is written on a result we
    cannot classify.

  - apply_lessons(project) takes unapplied LearningItems and folds them into
    the brain — a doctrine-update becomes doctrine, a failure-pattern becomes
    a failure_pattern row — then marks them applied, so a lesson is applied
    once, not on every future call.

Conservative by design: an unknown outcome is NOT recorded. A brain that
invents a lesson from an outcome it did not understand is worse than one that
admits the gap — the same fail-closed doctrine the rest of the system runs on.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from ..kernel.learning import LearningItem, LearningLoop, LearningType
from ..brain import Precedent, RepositoryBrain


class PROutcome(str, Enum):
    MERGED = "merged"
    REJECTED = "rejected"
    REGRESSED = "regressed"
    ABANDONED = "abandoned"


# which outcome feeds which brain structure
_SUCCESS = {PROutcome.MERGED}
_FAILURE = {PROutcome.REJECTED, PROutcome.REGRESSED}


@dataclass
class PRResult:
    pr_number: int
    title: str
    approach: str
    outcome: PROutcome
    maintainer_feedback: str = ""
    files_changed: Optional[list[str]] = None

    @property
    def is_success(self) -> bool:
        return self.outcome in _SUCCESS

    @property
    def is_failure(self) -> bool:
        return self.outcome in _FAILURE


def record_outcome(brain: RepositoryBrain, result: PRResult) -> dict[str, Any]:
    """Write a PR's outcome onto the brain as precedent or failure pattern.

    Fail-closed: an outcome that is neither success nor failure (e.g.
    ABANDONED) records nothing and says so, rather than guessing which
    structure it belongs to. Returns what was written.
    """
    if result.is_success:
        precedent = Precedent(
            pr_number=result.pr_number,
            title=result.title,
            outcome=result.outcome.value,
            approach=result.approach,
            maintainer_feedback=result.maintainer_feedback,
            lesson=f"approach accepted: {result.approach}",
            confidence=0.9 if result.maintainer_feedback else 0.6,
        )
        brain.add_precedent(precedent)
        return {"recorded": "precedent", "pr": result.pr_number, "confidence": precedent.confidence}

    if result.is_failure:
        pattern = {
            "pr_number": result.pr_number,
            "title": result.title,
            "approach": result.approach,
            "outcome": result.outcome.value,
            "feedback": result.maintainer_feedback,
            "lesson": f"avoid: {result.approach}",
            "recorded_at": datetime.now().isoformat(),
        }
        brain.failure_patterns.append(pattern)
        return {"recorded": "failure_pattern", "pr": result.pr_number}

    # ABANDONED or unknown — honest no-op
    return {"recorded": None, "pr": result.pr_number,
            "reason": f"outcome '{result.outcome.value}' is neither success nor failure"}


def apply_lessons(brain: RepositoryBrain, learning: LearningLoop) -> dict[str, Any]:
    """Fold unapplied LearningItems for this project into the brain.

    A doctrine-update item becomes doctrine; a failure-pattern item becomes a
    failure_pattern row. Items are marked applied after folding, so each
    lesson lands exactly once. Returns a count of what landed.
    """
    from ..brain import Doctrine, DoctrineType

    applied = 0
    for item in learning.get_unapplied(brain.project):
        if item.type == LearningType.DOCTRINE_UPDATE:
            rule = item.lesson.get("rule")
            if rule:
                # F7: validate the type; a bogus type must not raise out of the
                # loop and leave the lesson permanently unapplied (re-raising on
                # every future call). Skip-and-mark is fail-safe, not fail-closed
                # crash — the loop survives a malformed lesson.
                try:
                    dtype = DoctrineType(item.lesson.get("type", "design"))
                except ValueError:
                    learning.mark_applied(item.id)
                    continue
                brain.add_doctrine(Doctrine(
                    type=dtype,
                    rule=rule, source=f"learning:{item.id}", confidence=item.confidence,
                    evidence=[f"lesson {item.id}"],
                ))
                learning.mark_applied(item.id)
                applied += 1
        elif item.type == LearningType.FAILURE_PATTERN:
            brain.failure_patterns.append({
                "lesson_id": item.id, "detail": item.lesson,
                "recorded_at": datetime.now().isoformat(),
            })
            learning.mark_applied(item.id)
            applied += 1
    return {"applied": applied, "project": brain.project}
