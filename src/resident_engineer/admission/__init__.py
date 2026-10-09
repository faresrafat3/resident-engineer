"""Task Admission — decides whether a task is wanted, clear, valuable, and verifiable."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class AdmissionDecision(str, Enum):
    ACCEPT = "accept"
    REJECT = "reject"
    NEEDS_MORE_INFO = "needs-more-info"


class RejectionReason(str, Enum):
    NOT_WANTED = "not-wanted"
    UNCLEAR = "unclear"
    NOT_VERIFIABLE = "not-verifiable"
    COMPETING_PR = "competing-pr"
    TOO_LARGE = "too-large"
    OUT_OF_SCOPE = "out-of-scope"
    MISSING_CONTEXT = "missing-context"


@dataclass
class AdmissionResult:
    decision: AdmissionDecision
    reasoning: str
    rejection_reason: RejectionReason | None = None
    confidence: float = 0.5
    requirements: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


class TaskAdmission:
    """Evaluates whether a task should be accepted for work."""

    def __init__(self) -> None:
        self._checks: list[Any] = []

    def add_check(self, check: Any) -> None:
        self._checks.append(check)

    def evaluate(
        self,
        title: str,
        description: str,
        project: str,
        issue_number: int | None = None,
        existing_prs: list[int] | None = None,
        contributing_guide: str | None = None,
        codeowners: dict[str, str] | None = None,
    ) -> AdmissionResult:
        issues = []
        if not title or len(title.strip()) < 10:
            issues.append("Title too short or empty")
        if not description or len(description.strip()) < 50:
            issues.append("Description too short — needs more detail")
        vague_words = ["something", "somehow", "maybe", "might", "could", "possibly"]
        desc_lower = description.lower()
        vague_count = sum(1 for w in vague_words if w in desc_lower)
        if vague_count > 2:
            issues.append("Description contains too many vague terms")
        has_reproduction = any(kw in desc_lower for kw in ["reproduce", "expected", "actual", "error", "traceback", "steps"])
        has_test_plan = any(kw in desc_lower for kw in ["test", "verify", "validate", "check"])
        if not has_reproduction and not has_test_plan:
            issues.append("No clear reproduction steps or verification plan")
        if existing_prs and len(existing_prs) > 3:
            issues.append(f"Too many competing PRs: {existing_prs}")
        scope_keywords = ["refactor", "rewrite", "redesign", "migrate", "upgrade"]
        if any(kw in title.lower() for kw in scope_keywords):
            if not contributing_guide:
                issues.append("Large scope change but no CONTRIBUTING guide found")
        if issues:
            return AdmissionResult(
                decision=AdmissionDecision.REJECT,
                reasoning="; ".join(issues),
                rejection_reason=RejectionReason.UNCLEAR if "vague" in " ".join(issues) else RejectionReason.NOT_VERIFIABLE,
                confidence=0.7,
                requirements=issues,
            )
        return AdmissionResult(
            decision=AdmissionDecision.ACCEPT,
            reasoning="Task is clear, wanted, and verifiable",
            confidence=0.8,
        )
