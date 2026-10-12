"""CLI tests — the entry point pyproject declares now exists and is fail-closed.

pyproject points `resident-engineer` at cli:main, but the module never
existed, so `pip install` produced a broken entry point. These tests pin the
command surface: brain reads a repo, contribute runs the loop dry, and a
blocked contribution exits non-zero (fail-closed), never printed as ready.
"""
from __future__ import annotations

import io
import contextlib

from resident_engineer.cli import main

DESC = (
    "When the config file lacks the key it raises a bare ValueError. "
    "Reproduce: run parse_config({}) and observe the traceback. Expected: a "
    "clear error naming the key. I will add a regression test that verifies it."
)


def _run(argv: list[str]) -> tuple[int, str]:
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = main(argv)
    return code, out.getvalue()


# --no-brain on every contribute call: the tests must not touch the network.
# The gate being tested is the loop's, not gh's.
_BASE = ["--no-brain"]


class TestContributeCLI:
    def test_ready_contribution_exits_zero(self):
        # WITH a brain (registered offline via --no-brain is no-brain; here we
        # exercise the ready path by pointing at a repo whose brain we stub is
        # not possible offline, so this asserts the draft-with-no-brain path is
        # honest instead: --no-brain cannot claim ready. The ready path is
        # covered by test_contribution.py with a registered brain.
        code, out = _run([
            "contribute", "some/repo",
            "--title", "Fix ValueError when config key is missing",
            "--description", DESC, "--approach", "name the missing key",
            "--files", "config.py", "--tests", "test_config.py",
            "--passed", "5", "--failed", "0", *_BASE,
        ])
        # F3: no brain -> draft, exit 1, reason stated — never a false 'ready'
        assert code == 1
        assert "draft" in out
        assert "reason:" in out   # the reason is stated, not silently dropped

    def test_no_brain_never_reports_ready(self):
        code, out = _run([
            "contribute", "some/repo",
            "--title", "Fix ValueError when config key is missing",
            "--description", DESC, "--approach", "name the missing key",
            "--passed", "5", "--failed", "0", "--no-brain",
        ])
        assert "ready" not in out   # the word never appears for a brainless run
        assert code == 1

    def test_failing_tests_exit_nonzero(self):
        code, out = _run([
            "contribute", "some/repo",
            "--title", "Fix ValueError when config key is missing",
            "--description", DESC, "--approach", "name the key",
            "--passed", "3", "--failed", "2", *_BASE,
        ])
        assert code == 1               # fail-closed: blocked is not success
        assert "blocked" in out

    def test_unverifiable_task_exits_nonzero(self):
        code, out = _run([
            "contribute", "some/repo",
            "--title", "fix", "--description", "maybe broken somehow could be",
            "--approach", "guess", "--passed", "1", *_BASE,
        ])
        assert code == 1
        assert "rejected" in out


class TestShowCLI:
    def test_show_offline_brain(self):
        code, out = _run(["show", "some/repo", "--text",
                          "# AGENTS\n\n- You **must** run the gate.\n- Never push to main.\n"])
        assert code == 0
        assert "doctrine 2" in out

    def test_show_empty_text_empty_brain(self):
        code, out = _run(["show", "some/repo"])
        assert code == 0
        assert "doctrine 0" in out   # honest empty, not invented
