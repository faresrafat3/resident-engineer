"""Doctrine extractor — turns real repo docs (AGENTS.md, CONTRIBUTING.md) into
structured Doctrine rules.

The RepositoryBrain is a store; this is the reader that fills it from a real
repository instead of by hand. It is deliberately pure text processing: it
takes the already-fetched text of a repo's doctrine files and returns
Doctrine objects. No network, no I/O — the fetch is the caller's job, so the
extraction is deterministic and testable offline.

The extraction is conservative on purpose. A line only becomes Doctrine when
it carries an explicit rule signal ("must", "never", "always", "do not",
"refuse", "fail-closed", ...); everything else is ignored rather than guessed.
A brain full of invented rules is worse than a brain that admits what it does
not know — the same fail-closed doctrine the rest of the system runs on.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from . import Doctrine, DoctrineType, PlaybookEntry, RepositoryBrain

# Explicit rule signals. A line must contain one of these (case-insensitive)
# to be treated as a rule; otherwise it is prose and is skipped.
_RULE_SIGNALS = (
    "must", "never", "always", "do not", "don't", "refuse", "forbidden",
    "required", "fail-closed", "fail closed", "off-limits", "off limits",
    "only", "cannot", "may not", "shall",
)

# Map heading/section keywords to a DoctrineType. First match wins.
_TYPE_HINTS: list[tuple[tuple[str, ...], DoctrineType]] = [
    (("contribut", "pr", "pull request", "commit"), DoctrineType.CONTRIBUTION),
    (("test", "verify", "gate", "ci"), DoctrineType.TESTING),
    (("depend", "version", "package"), DoctrineType.DEPENDENCIES),
    (("compat", "backward", "api", "breaking"), DoctrineType.COMPATIBILITY),
    (("style", "lint", "format", "naming"), DoctrineType.STYLE),
    (("design", "architecture", "module", "layer"), DoctrineType.DESIGN),
]


@dataclass
class ExtractedRule:
    text: str
    doctrine_type: DoctrineType
    source: str
    line_no: int


def _classify(context: str) -> DoctrineType:
    low = context.lower()
    for hints, dtype in _TYPE_HINTS:
        if any(h in low for h in hints):
            return dtype
    return DoctrineType.DESIGN  # default bucket, never a guess at a specific type


def _is_rule(line: str) -> bool:
    low = line.lower()
    # strip list markers before checking
    stripped = low.lstrip("-*•>#0123456789. ").strip()
    if not stripped:
        return False
    return any(sig in low for sig in _RULE_SIGNALS)


def extract_rules(text: str, source: str) -> list[ExtractedRule]:
    """Extract Doctrine rules from a doctrine document's text.

    A rule is a line carrying an explicit rule signal. The nearest preceding
    heading supplies the DoctrineType. Returns only lines that are genuinely
    rules — no paraphrase, no invention.
    """
    rules: list[ExtractedRule] = []
    current_heading = ""
    for i, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            current_heading = line.lstrip("#").strip()
            continue
        if _is_rule(line):
            clean = line.lstrip("-*•>0123456789. ").strip()
            # skip trivial / non-substantive lines
            if len(clean) < 12:
                continue
            rules.append(ExtractedRule(
                text=clean, doctrine_type=_classify(current_heading),
                source=source, line_no=i,
            ))
    return rules


def extract_playbook(text: str, source: str) -> list[PlaybookEntry]:
    """Extract a playbook entry from a 'run the gate' style command block.

    Looks for a fenced or inline command that runs a verify/test/build step
    and records it as a playbook action with its own verification. Returns at
    most one entry — the first real command found.
    """
    cmd_patterns = (
        re.compile(r"\b(npm run (?:verify|test|build|gate))\b"),
        re.compile(r"\b(pytest [^\n`]+)\b"),
        re.compile(r"\b(node --test[^\n`]*)\b"),
        re.compile(r"\b(make (?:test|check|verify))\b"),
    )
    for raw in text.splitlines():
        for pat in cmd_patterns:
            m = pat.search(raw)
            if m:
                return [PlaybookEntry(
                    trigger="before committing / claiming done",
                    action=f"run `{m.group(1)}`",
                    verification="exit code 0",
                    exceptions=[],
                )]
    return []


def build_brain(
    project: str,
    url: str,
    docs: dict[str, str],
) -> RepositoryBrain:
    """Build a RepositoryBrain from a repo's doctrine documents.

    `docs` maps filename -> file text (e.g. {"AGENTS.md": "...", 
    "CONTRIBUTING.md": "..."}). Pure and offline: the caller fetches the text.
    Returns a brain with only what the docs actually contain — an empty
    doctrine list when the docs say nothing rule-like, which is honest.
    """
    brain = RepositoryBrain(project=project, url=url)
    all_text_parts: list[str] = []
    for filename, text in docs.items():
        all_text_parts.append(text)
        for rule in extract_rules(text, filename):
            brain.add_doctrine(Doctrine(
                type=rule.doctrine_type, rule=rule.text, source=rule.source,
                confidence=0.8, evidence=[f"{filename}:{rule.line_no}"],
            ))
    for entry in extract_playbook("\n".join(all_text_parts), "repo"):
        brain.add_playbook_entry(entry)
    return brain
