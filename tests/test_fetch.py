"""Fetcher tests — the network seam, tested with a fake runner (offline).

The fetcher is the only part of the brain that touches the wire. These tests
inject a fake `runner` so no process is spawned and no quota is spent, and
pin the fail-closed contract: a doc that fails to fetch is ABSENT, never
fabricated.
"""
from __future__ import annotations

from resident_engineer.brain.fetch import (
    build_brain_from_repo,
    fetch_doctrine_docs,
    repo_meta,
)

AGENTS = "# AGENTS.md\n\n- You **must** run the gate before committing.\n- Never push to main.\n"
CONTRIBUTING = "# Contributing\n\nFork and open a PR.\n"


def _fake_runner(files: dict[str, tuple[int, str]]):
    """Build a runner that answers per the file map; anything else 404s."""
    meta_json = ('{"full_name":"o/r","stargazers_count":10,"open_issues_count":3,'
                 '"pushed_at":"2026-10-12","archived":false,"default_branch":"main"}')

    def run(cmd: list[str]) -> tuple[int, str]:
        # the path is the segment right after 'repos/<owner>/<name>'
        # e.g. ['gh','api','repos/o/r/contents/AGENTS.md', ...]
        target = ""
        for i, part in enumerate(cmd):
            if part.startswith("repos/"):
                rest = part.split("/", 3)  # ['repos','o','r','contents/AGENTS.md']
                if len(rest) == 4 and rest[3].startswith("contents/"):
                    target = rest[3][len("contents/"):]
                break
        # meta call: 'repos/o/r' with no /contents/ -> no target
        if target == "":
            return (0, meta_json)
        return files.get(target, (1, ""))
    return run


class TestFetchDoctrineDocs:
    def test_fetches_existing_docs(self):
        runner = _fake_runner({"AGENTS.md": (0, AGENTS), "CONTRIBUTING.md": (0, CONTRIBUTING)})
        docs = fetch_doctrine_docs("o/r", runner=runner)
        assert "AGENTS.md" in docs
        assert "CONTRIBUTING.md" in docs

    def test_missing_doc_is_absent_not_fabricated(self):
        # only AGENTS.md exists; CONTRIBUTING 404s
        runner = _fake_runner({"AGENTS.md": (0, AGENTS)})
        docs = fetch_doctrine_docs("o/r", runner=runner)
        assert "AGENTS.md" in docs
        assert "CONTRIBUTING.md" not in docs   # absent, not invented

    def test_no_docs_yields_empty(self):
        runner = _fake_runner({})
        docs = fetch_doctrine_docs("o/r", runner=runner)
        assert docs == {}

    def test_empty_file_body_skipped(self):
        # exit 0 but blank body — not a real doc
        runner = _fake_runner({"AGENTS.md": (0, "   \n  ")})
        docs = fetch_doctrine_docs("o/r", runner=runner)
        assert docs == {}


class TestRepoMeta:
    def test_parses_meta(self):
        runner = _fake_runner({})
        meta = repo_meta("o/r", runner=runner)
        assert meta["stars"] == 10
        assert meta["archived"] is False
        assert meta["full_name"] == "o/r"

    def test_failure_returns_empty(self):
        def run(cmd): return (1, "not found")
        assert repo_meta("o/r", runner=run) == {}


class TestBuildBrainFromRepo:
    def test_wires_fetch_and_extract(self):
        runner = _fake_runner({"AGENTS.md": (0, AGENTS)})
        docs, brain = build_brain_from_repo("o/r", runner=runner)
        assert "AGENTS.md" in docs
        # the extracted brain carries the real rules from the fetched doc
        assert len(brain.doctrine) >= 2
        assert any("run the gate" in d.rule for d in brain.doctrine)

    def test_no_docs_empty_brain(self):
        runner = _fake_runner({})
        docs, brain = build_brain_from_repo("o/r", runner=runner)
        assert docs == {}
        assert brain.doctrine == []   # honest empty, not invented
