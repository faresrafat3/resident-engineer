"""Verification Court — judges quality: behavior, scope, compatibility, security."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class Verdict(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    CONDITIONAL = "conditional"


class CheckType(str, Enum):
    BEHAVIOR = "behavior"
    SCOPE = "scope"
    COMPATIBILITY = "compatibility"
    SECURITY = "security"
    TESTS = "tests"
    DOCS = "docs"
    CI = "ci"


@dataclass
class VerificationCheck:
    type: CheckType
    name: str
    passed: bool
    evidence: str
    severity: str = "error"


@dataclass
class CourtResult:
    verdict: Verdict
    checks: list[VerificationCheck]
    overall_score: float
    reasoning: str
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def passed(self) -> bool:
        return self.verdict == Verdict.PASS

    def failures(self) -> list[VerificationCheck]:
        return [c for c in self.checks if not c.passed and c.severity == "error"]

    def warnings(self) -> list[VerificationCheck]:
        return [c for c in self.checks if not c.passed and c.severity == "warning"]


class VerificationCourt:
    """Runs all verification checks and returns a verdict."""

    def __init__(self) -> None:
        self._checks: list[VerificationCheck] = []

    def add_check(self, check: VerificationCheck) -> None:
        self._checks.append(check)

    def evaluate(self) -> CourtResult:
        failures = [c for c in self._checks if not c.passed and c.severity == "error"]
        warnings = [c for c in self._checks if not c.passed and c.severity == "warning"]
        passed = [c for c in self._checks if c.passed]
        if failures:
            verdict = Verdict.FAIL
            reasoning = f"Failed {len(failures)} critical checks"
        elif warnings:
            verdict = Verdict.CONDITIONAL
            reasoning = f"Passed with {len(warnings)} warnings"
        else:
            verdict = Verdict.PASS
            reasoning = "All checks passed"
        score = (len(passed) / max(len(self._checks), 1)) * 10
        return CourtResult(verdict=verdict, checks=list(self._checks), overall_score=score, reasoning=reasoning)

    def reset(self) -> None:
        self._checks.clear()
