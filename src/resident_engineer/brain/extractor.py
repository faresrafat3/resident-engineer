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

# A rule's own TEXT can override the heading's type. When a line explicitly
# names a compatibility surface, it is a compatibility rule no matter which
# section it sits under — the heading is a hint, the content is the truth.
# Without this, a "Never break the public API" rule under a "## Design"
# heading was classified DESIGN and the brain's conflict check (which only
# inspects COMPATIBILITY doctrine) never saw it.
_TEXT_OVERRIDES: list[tuple[tuple[str, ...], DoctrineType]] = [
    (("public api", "backward", "backwards", "breaking change", "break the api",
      "compatib"), DoctrineType.COMPATIBILITY),
]


def _word_match(text: str, hint: str) -> bool:
    """Word-boundary match for short/ambiguous hints.

    F11: substring matching let "pr" match inside "propose"/"approvals", "ci"
    inside "recipe"/"reconcile", "only" inside "ff-only" — misclassifying ~20-40%
    of real rules into the wrong (or a silent 'design') bucket. Short hints
    (<=3 chars, or known-ambiguous tokens) must match whole words only; longer,
    distinctive phrases keep substring matching. Compiled once at module load.
    """
    if len(hint) <= 3 or hint in ("api", "only", "ci", "pr"):
        return _WORD_RE[hint].search(text) is not None if hint in _WORD_RE \
            else re.search(rf"\b{re.escape(hint)}\b", text) is not None
    return hint in text


# precompiled word-boundary patterns for the ambiguous short tokens
_WORD_RE = {h: re.compile(rf"\b{re.escape(h)}\b") for h in ("api", "only", "ci", "pr")}


def _classify(heading: str, rule_text: str = "") -> DoctrineType:
    """Classify a rule by its section heading, then its own text.

    Text overrides heading: a rule that explicitly names a compatibility
    surface is COMPATIBILITY regardless of the section it sits in. Falls back
    to DESIGN (a neutral bucket, never a guess at a specific type).
    """
    low_rule = rule_text.lower()
    for hints, dtype in _TEXT_OVERRIDES:
        if any(_word_match(low_rule, h) for h in hints):
            return dtype
    low = heading.lower()
    for hints, dtype in _TYPE_HINTS:
        if any(_word_match(low, h) for h in hints):
            return dtype
    return DoctrineType.DESIGN  # default bucket, never a guess at a specific type


@dataclass
class ExtractedRule:
    text: str
    doctrine_type: DoctrineType
    source: str
    line_no: int


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
    in_fence = False  # F13: lines between ``` fences are example code, not doctrine
    for i, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
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
                text=clean, doctrine_type=_classify(current_heading, clean),
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
        # F14: skip a negated command — "Do not use npm run build" must not
        # become "run npm run build". Check for a negation near the match.
        low = raw.lower()
        if any(neg in low for neg in ("do not", "don't", "never", "avoid", "not ")):
            continue
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
