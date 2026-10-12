"""Fail-closed gate tests — the law the AGENTS.md declares, proven in code.

These tests exist because admission and verification are the two gates that
keep this system honest, and they were the parts the original single test
file did not cover. A test that only checks "it returns something" would pass
against a skill; these assert the gate actually REFUSES.

Plain pytest style (assert, not unittest.TestCase) — matches test_system.py.
"""
from __future__ import annotations

from resident_engineer.admission import (
    AdmissionDecision,
    RejectionReason,
    TaskAdmission,
)
from resident_engineer.court import CheckType, VerificationCheck, VerificationCourt, Verdict


GOOD_TITLE = "Fix ValueError when config key is missing"
GOOD_DESC = (
    "When the config file lacks the required key, parse_config raises a bare "
    "ValueError with no context. Reproduce: run parse_config({}) and observe "
    "the traceback. Expected: a clear error naming the missing key. I will "
    "add a regression test that verifies the error message."
)


class TestAdmissionFailClosed:
    """A task that cannot be verified must be rejected before work starts."""

    def setup_method(self):
        self.admission = TaskAdmission()

    def test_good_task_accepted(self):
        r = self.admission.evaluate(GOOD_TITLE, GOOD_DESC, "some/repo")
        assert r.decision == AdmissionDecision.ACCEPT

    def test_empty_title_rejected(self):
        r = self.admission.evaluate("", GOOD_DESC, "some/repo")
        assert r.decision == AdmissionDecision.REJECT

    def test_vague_task_rejected_as_unclear(self):
        r = self.admission.evaluate(
            "Fix something maybe somehow",
            "It might possibly be broken, could be something, maybe a bug somewhere somehow.",
            "some/repo",
        )
        assert r.decision == AdmissionDecision.REJECT
        assert r.rejection_reason in (RejectionReason.UNCLEAR, RejectionReason.NOT_VERIFIABLE)

    def test_no_verification_plan_rejected(self):
        # clear prose, but nothing to reproduce or verify — fail closed
        r = self.admission.evaluate(
            "Improve the configuration handling logic",
            "The configuration handling could be made cleaner and more elegant "
            "for maintainability and future-proofing purposes going forward.",
            "some/repo",
        )
        assert r.decision == AdmissionDecision.REJECT

    def test_too_many_competing_prs_rejected(self):
        r = self.admission.evaluate(GOOD_TITLE, GOOD_DESC, "some/repo",
                                    existing_prs=[1, 2, 3, 4])
        assert r.decision == AdmissionDecision.REJECT

    def test_rejection_records_its_reasons(self):
        r = self.admission.evaluate("", "", "some/repo")
        assert r.requirements  # the refusal names why


class TestCourtFailClosed:
    """A failed critical check fails the verdict — no silent pass."""

    def setup_method(self):
        self.court = VerificationCourt()

    def test_all_pass_passes(self):
        self.court.add_check(VerificationCheck(CheckType.TESTS, "tests", True, "22 passed"))
        r = self.court.evaluate()
        assert r.verdict == Verdict.PASS
        assert r.passed

    def test_one_critical_failure_fails(self):
        self.court.add_check(VerificationCheck(CheckType.TESTS, "tests", True, "ok"))
        self.court.add_check(VerificationCheck(CheckType.BEHAVIOR, "behaviour", False, "regressed"))
        r = self.court.evaluate()
        assert r.verdict == Verdict.FAIL   # the gate refuses
        assert not r.passed
        assert len(r.failures()) == 1

    def test_warning_only_is_conditional(self):
        self.court.add_check(VerificationCheck(CheckType.TESTS, "tests", True, "ok"))
        self.court.add_check(VerificationCheck(CheckType.DOCS, "docs", False, "missing", severity="warning"))
        r = self.court.evaluate()
        assert r.verdict == Verdict.CONDITIONAL
        assert len(r.warnings()) == 1
        assert len(r.failures()) == 0

    def test_empty_court_passes(self):
        # vacuous pass is a known, deliberate behaviour: no checks = nothing
        # failed. Documented here so it is a choice, not a surprise.
        r = self.court.evaluate()
        assert r.verdict == Verdict.PASS

    def test_reset_clears_checks(self):
        self.court.add_check(VerificationCheck(CheckType.TESTS, "t", True, "ok"))
        self.court.reset()
        assert self.court.evaluate().checks == []
