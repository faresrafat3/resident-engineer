"""Doctrine extractor tests — the brain must read, never invent.

The extractor is the piece that fills the RepositoryBrain from real repo
docs. Its honesty is the whole point: it must extract explicit rules and
refuse to fabricate doctrine from prose. A brain full of invented rules is
worse than an empty one, so these tests pin both directions.
"""
from __future__ import annotations

from resident_engineer.brain.extractor import (
    build_brain,
    extract_playbook,
    extract_rules,
)
from resident_engineer.brain import DoctrineType

AGENTS_MD = """# AGENTS.md — some/repo

## Contribution rules

- You **must** run the gate before committing.
- Never push directly to main.
- Tests are required for every change.

## Verification

Run `npm run verify` before you claim anything is done. The green gate is the
receipt, never prose.

## Design

The kernel is pure: no I/O, no clocks, no randomness. It is a layering rule.

## Notes

This project was started in 2024. We like clean code.
"""

CONTRIBUTING_MD = """# Contributing

Fork and open a PR. The maintainer reviews within a week.
"""


class TestExtractRules:
    def test_extracts_explicit_rules(self):
        rules = extract_rules(AGENTS_MD, "AGENTS.md")
        texts = [r.text for r in rules]
        assert any("run the gate" in t for t in texts)
        assert any("push directly to main" in t for t in texts)
        assert any("Tests are required" in t for t in texts)

    def test_ignores_prose_without_rule_signal(self):
        rules = extract_rules(AGENTS_MD, "AGENTS.md")
        # the "started in 2024 / we like clean code" lines carry no rule
        # signal and must NOT become doctrine
        assert not any("started in 2024" in r.text for r in rules)
        assert not any("clean code" in r.text for r in rules)

    def test_classifies_by_heading(self):
        rules = extract_rules(AGENTS_MD, "AGENTS.md")
        by_text = {r.text: r for r in rules}
        gate_rule = next(r for r in rules if "run the gate" in r.text)
        assert gate_rule.doctrine_type == DoctrineType.CONTRIBUTION

    def test_empty_doc_yields_nothing(self):
        assert extract_rules("", "x.md") == []
        assert extract_rules("just some prose here\nnothing formal\n", "x.md") == []

    def test_records_source_and_line(self):
        rules = extract_rules(AGENTS_MD, "AGENTS.md")
        assert all(r.source == "AGENTS.md" for r in rules)
        assert all(r.line_no > 0 for r in rules)

    def test_text_overrides_heading_type(self):
        # a rule whose OWN text names a compatibility surface is COMPATIBILITY
        # even under a non-compat heading — the heading is a hint, text is truth
        text = ("## Design notes\n\n"
                "- You must never break the public API when changing this module.\n")
        rules = extract_rules(text, "AGENTS.md")
        assert len(rules) == 1
        assert rules[0].doctrine_type == DoctrineType.COMPATIBILITY

    def test_heading_still_classifies_when_text_neutral(self):
        text = ("## Compatibility\n\n"
                "- You must keep this stable across releases.\n")
        rules = extract_rules(text, "AGENTS.md")
        assert rules[0].doctrine_type == DoctrineType.COMPATIBILITY


class TestExtractPlaybook:
    def test_extracts_gate_command(self):
        pb = extract_playbook("Run `npm run verify` before you claim done.", "repo")
        assert len(pb) == 1
        assert "npm run verify" in pb[0].action

    def test_no_command_no_playbook(self):
        assert extract_playbook("Just a description with no command.", "repo") == []


class TestBuildBrain:
    def test_brain_carries_extracted_doctrine(self):
        brain = build_brain("some/repo", "https://github.com/some/repo",
                            {"AGENTS.md": AGENTS_MD, "CONTRIBUTING.md": CONTRIBUTING_MD})
        assert len(brain.doctrine) >= 3
        # the playbook entry comes from the gate command
        assert len(brain.playbook) == 1

    def test_brain_from_doctrine_free_docs_is_empty_not_invented(self):
        # CONTRIBUTING has no explicit rules — the brain must NOT invent any
        brain = build_brain("x/y", "https://github.com/x/y", {"CONTRIBUTING.md": CONTRIBUTING_MD})
        assert brain.doctrine == []
        assert brain.playbook == []  # no gate command in it either

    def test_brain_is_deterministic(self):
        docs = {"AGENTS.md": AGENTS_MD}
        a = build_brain("some/repo", "u", docs)
        b = build_brain("some/repo", "u", docs)
        assert [d.rule for d in a.doctrine] == [d.rule for d in b.doctrine]
        assert a.id == b.id
