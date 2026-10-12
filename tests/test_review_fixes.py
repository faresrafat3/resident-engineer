"""Regression tests for the slop-reviewer's HOLD findings (2026-10-12).

Each test pins one fix so the exact bug cannot return. The reviewer verified
all of these reproduced before the fix; the fix is not real until the test
that would have caught it now passes.
"""
from __future__ import annotations

from resident_engineer.system import ResidentEngineeringSystem
from resident_engineer.bots import create_resident_engineer
from resident_engineer.brain import RepositoryBrain, Doctrine, DoctrineType
from resident_engineer.brain.extractor import extract_rules, extract_playbook
from resident_engineer.kernel.learning import LearningItem, LearningLoop, LearningType
from resident_engineer.kernel.outcome import apply_lessons

GOOD_T = "Fix ValueError when config key is missing"
GOOD_D = ("When the config file lacks the key it raises a bare ValueError. "
          "Reproduce: run parse_config({}) and observe the traceback. Expected: "
          "a clear error naming the key. I will add a regression test that verifies it.")


def _sys(doctrines=None):
    s = ResidentEngineeringSystem()
    s.register_agent(create_resident_engineer("re"))
    b = RepositoryBrain(project="some/repo", url="u")
    for t, txt in (doctrines or []):
        b.add_doctrine(Doctrine(t, txt, "AGENTS.md"))
    s.register_brain(b)
    return s, b


def _contribute(s, **over):
    kw = dict(files_changed=["a.py"], tests_added=[], test_results={"passed": 5, "failed": 0},
              approach="name the missing key", risks=[])
    kw.update(over)
    return s.run_contribution(GOOD_T, GOOD_D, "some/repo", **kw)


class TestF1ConflictOnApproach:
    def test_innocent_approach_not_blocked_by_compat_rule(self):
        # a compat rule whose text has no danger word must NOT block an
        # innocent approach (the old code matched the rule text)
        s, _ = _sys([(DoctrineType.COMPATIBILITY, "python 3.10 is required")])
        assert s.consult_brain("some/repo", "change the error message text")["conflicts"] == []

    def test_real_api_break_blocked(self):
        s, _ = _sys([(DoctrineType.COMPATIBILITY, "never break the public API")])
        conflicts = s.consult_brain("some/repo", "rename the public API and drop the old functions")["conflicts"]
        assert conflicts   # the approach breaks compat -> blocked


class TestF2ScopeIsReal:
    def test_huge_change_blocked_on_scope(self):
        s, _ = _sys()
        r = _contribute(s, files_changed=[f"f{i}.py" for i in range(500)])
        assert r["status"] == "blocked"
        assert "scope" in r["failures"]

    def test_narrow_change_passes_scope(self):
        s, _ = _sys()
        r = _contribute(s, files_changed=["a.py", "b.py"])
        assert r["status"] == "ready"


class TestF3NoBrainIsDraftNotReady:
    def test_no_brain_never_ready(self):
        s = ResidentEngineeringSystem()
        s.register_agent(create_resident_engineer("re"))
        r = _contribute(s)
        assert r["status"] == "draft"
        assert r.get("no_brain") is True


class TestF5TestResultsMustBeReal:
    def test_nonsense_passed_blocked(self):
        s, _ = _sys()
        for bad in ({"passed": "yes"}, {"passed": -5}, {"passed": True}, {"passed": 0}):
            r = _contribute(s, test_results=bad)
            assert r["status"] == "blocked", f"{bad} should block"

    def test_real_passing_run_passes(self):
        s, _ = _sys()
        assert _contribute(s, test_results={"passed": 5, "failed": 0})["status"] == "ready"


class TestF12ConsultReturnsPrecedents:
    def test_merged_outcome_appears_in_consult(self):
        s, b = _sys()
        s.apply_pr_outcome("some/repo", 7, "fix", "name the key", "merged", maintainer_feedback="good")
        ctx = s.consult_brain("some/repo", "similar fix")
        assert any(p["pr"] == 7 for p in ctx["precedents"])


class TestF13CodeFencesNotDoctrine:
    def test_fenced_example_not_extracted(self):
        text = "# AGENTS\n\n## Example\n\n```\nYou must never commit secrets to the repo.\n```\n"
        assert extract_rules(text, "AGENTS.md") == []


class TestF14PlaybookSkipsNegation:
    def test_negated_command_not_a_playbook_action(self):
        assert extract_playbook("Do not use npm run build for this.", "repo") == []

    def test_positive_command_is_playbook(self):
        pb = extract_playbook("Run `npm run verify` before you claim done.", "repo")
        assert len(pb) == 1 and "npm run verify" in pb[0].action


class TestF7BogusDoctrineTypeDoesNotPoison:
    def test_bad_type_skipped_not_raised(self):
        b = RepositoryBrain(project="some/repo", url="u")
        loop = LearningLoop()
        loop.capture(LearningItem(id="L1", type=LearningType.DOCTRINE_UPDATE,
                                  project="some/repo", trigger={},
                                  lesson={"rule": "x", "type": "bogus"}))
        # must not raise, and must not leave the lesson unapplied forever
        r = apply_lessons(b, loop)
        assert r["applied"] == 0
        # a second call does not re-process (it was marked applied)
        assert apply_lessons(b, loop)["applied"] == 0
        assert b.doctrine == []
