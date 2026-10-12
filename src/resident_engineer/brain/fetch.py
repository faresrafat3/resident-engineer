"""Repository fetcher — gets a repo's doctrine docs via `gh api`, offline-safe.

This is the network seam. It is deliberately a thin wrapper around `gh api
raw` that returns TEXT, never Doctrine: the extraction lives in extractor.py
and stays pure and offline. Keeping the seam here means:

  - the extractor is tested with no network (deterministic, no quota);
  - the fetcher is the only place that touches the wire, so a quota wall or a
    missing `gh` is one failure with one clear message, not a leak into logic.

Fail-closed: if a doc cannot be fetched, it is simply absent from the returned
dict — never fabricated. A missing AGENTS.md yields an empty docs dict, which
build_brain turns into an empty (honest) brain, not an invented one.

The `runner` is injectable so tests pass a fake that returns canned text and
never spawn a process. Default runner shells out to `gh api`.
"""
from __future__ import annotations

import json
import subprocess
from typing import TYPE_CHECKING, Callable, Optional

if TYPE_CHECKING:
    from . import RepositoryBrain

# The doctrine files worth reading, in priority order.
DOCTRINE_FILES = ("AGENTS.md", "CONTRIBUTING.md", "docs/AGENTS.md", ".github/CONTRIBUTING.md")

# A runner takes a shell command and returns (exit_code, stdout). Injectable.
Runner = Callable[[list[str]], "tuple[int, str]"]


def _default_runner(cmd: list[str]) -> tuple[int, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return r.returncode, r.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return 1, str(e)


def fetch_doctrine_docs(
    repo: str,
    *,
    filenames: tuple[str, ...] = DOCTRINE_FILES,
    runner: Optional[Runner] = None,
) -> dict[str, str]:
    """Fetch a repo's doctrine docs as {filename: text}.

    `repo` is "owner/name". Each file is fetched with `gh api` raw content
    endpoint; a file that 404s (exit != 0) is skipped, never fabricated.
    Returns only the docs that actually exist.
    """
    run = runner or _default_runner
    docs: dict[str, str] = {}
    for name in filenames:
        # the contents API returns base64; ask for the raw media type instead
        code, out = run(["gh", "api", f"repos/{repo}/contents/{name}",
                         "-H", "Accept: application/vnd.github.raw"])
        if code == 0 and out.strip():
            docs[name] = out
    return docs


def repo_meta(repo: str, *, runner: Optional[Runner] = None) -> dict:
    """Fetch repo metadata (stars, open issues, pushed date, archived?).

    Used to sanity-check a repo before spending contribution effort on it.
    Returns {} on any failure — the caller treats missing meta as 'unknown',
    never as 'fine'.
    """
    run = runner or _default_runner
    code, out = run(["gh", "api", f"repos/{repo}"])
    if code != 0 or not out.strip():
        return {}
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return {}
    return {
        "full_name": data.get("full_name"),
        "stars": data.get("stargazers_count", 0),
        "open_issues": data.get("open_issues_count", 0),
        "pushed_at": data.get("pushed_at"),
        "archived": data.get("archived", False),
        "default_branch": data.get("default_branch", "main"),
    }


def build_brain_from_repo(
    repo: str,
    *,
    runner: Optional[Runner] = None,
) -> "tuple[dict[str, str], RepositoryBrain]":
    """Fetch docs + extract a brain in one call. Returns (docs, brain).

    Convenience over fetch_doctrine_docs + build_brain, so a caller gets the
    brain without wiring the two seams itself. Offline-testable via `runner`.
    """
    from .extractor import build_brain
    docs = fetch_doctrine_docs(repo, runner=runner)
    meta = repo_meta(repo, runner=runner)
    url = f"https://github.com/{meta.get('full_name', repo)}"
    brain = build_brain(repo, url, docs)
    return docs, brain
