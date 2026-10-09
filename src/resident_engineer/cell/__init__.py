"""Engineering Cell — plans, builds, reviews, and revises."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class CellStage(str, Enum):
    PLAN = "plan"
    BUILD = "build"
    REVIEW = "review"
    REVISE = "revise"
    COMPLETE = "complete"


@dataclass
class PlanCandidate:
    id: str
    approach: str
    files_to_change: list[str]
    tests_to_add: list[str]
    risks: list[str]
    estimated_effort: str
    score: float = 0.0


@dataclass
class BuildResult:
    files_changed: list[str]
    tests_added: list[str]
    diff: str
    build_success: bool
    test_results: dict[str, Any]
    errors: list[str] = field(default_factory=list)


@dataclass
class ReviewResult:
    approved: bool
    issues: list[str]
    suggestions: list[str]
    score: float
    reviewer: str


@dataclass
class EngineeringCell:
    """The core engineering loop: Plan → Build → Review → Revise."""

    project: str
    stage: CellStage = CellStage.PLAN
    plan: PlanCandidate | None = None
    build: BuildResult | None = None
    review: ReviewResult | None = None
    revision_history: list[dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    def set_plan(self, plan: PlanCandidate) -> None:
        self.plan = plan
        self.stage = CellStage.BUILD

    def set_build(self, build: BuildResult) -> None:
        self.build = build
        self.stage = CellStage.REVIEW

    def set_review(self, review: ReviewResult) -> None:
        self.review = review
        if review.approved:
            self.stage = CellStage.COMPLETE
        else:
            self.stage = CellStage.REVISE

    def revise(self, changes: dict[str, Any]) -> None:
        self.revision_history.append({"timestamp": datetime.now().isoformat(), "changes": changes})
        self.stage = CellStage.BUILD

    def is_complete(self) -> bool:
        return self.stage == CellStage.COMPLETE

    def to_dict(self) -> dict[str, Any]:
        return {
            "project": self.project,
            "stage": self.stage.value,
            "plan": {
                "id": self.plan.id, "approach": self.plan.approach,
                "files_to_change": self.plan.files_to_change, "tests_to_add": self.plan.tests_to_add,
                "risks": self.plan.risks, "estimated_effort": self.plan.estimated_effort,
                "score": self.plan.score,
            } if self.plan else None,
            "build": {
                "files_changed": self.build.files_changed, "tests_added": self.build.tests_added,
                "build_success": self.build.build_success, "test_results": self.build.test_results,
                "errors": self.build.errors,
            } if self.build else None,
            "review": {
                "approved": self.review.approved, "issues": self.review.issues,
                "suggestions": self.review.suggestions, "score": self.review.score,
                "reviewer": self.review.reviewer,
            } if self.review else None,
            "revision_history": self.revision_history,
            "created_at": self.created_at.isoformat(),
        }
