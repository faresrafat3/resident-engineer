"""resident-engineer CLI — the command surface over the whole system.

pyproject declares `resident-engineer = resident_engineer.cli:main`, but the
module never existed — `pip install` produced a broken entry point. This is
that module, and it is a thin shell over the real components, not a second
implementation: every subcommand calls into system.py / brain, so the CLI and
the library share one behaviour and one gate.

Subcommands:
  brain <repo>      fetch a repo's doctrine docs + build its brain (read-only)
  contribute <repo> run the full admission → brain → cell → court → PR loop
  show <repo>       print a brain's doctrine, precedents, failure patterns

Fail-closed throughout: no network in the logic paths (only `brain`/`contribute`
touch gh, and only to READ), and a contribution that does not clear its gates
is reported blocked, never printed as ready.
"""
from __future__ import annotations

import argparse
import json
import sys

from .system import ResidentEngineeringSystem
from .bots import create_resident_engineer
from .brain.extractor import build_brain
from .brain.fetch import fetch_doctrine_docs, repo_meta


def _cmd_brain(args: argparse.Namespace) -> int:
    """Fetch a repo's doctrine docs and build its brain. Read-only."""
    docs = fetch_doctrine_docs(args.repo)
    meta = repo_meta(args.repo)
    if not docs:
        print(f"no doctrine docs found in {args.repo} "
              f"(archived={meta.get('archived', '?')})", file=sys.stderr)
        # still emit an empty, honest brain if asked for json
        if args.json:
            print(json.dumps({"repo": args.repo, "docs": [], "brain": build_brain(args.repo, "", {}).to_dict()}))
        return 0
    brain = build_brain(args.repo, f"https://github.com/{args.repo}", docs)
    if args.json:
        print(json.dumps({"repo": args.repo, "meta": meta, "docs": list(docs), "brain": brain.to_dict()}, indent=2))
        return 0
    print(f"# brain for {args.repo}")
    if meta:
        print(f"stars={meta.get('stars')} archived={meta.get('archived')} branch={meta.get('default_branch')}")
    print(f"\ndocs read: {', '.join(docs)}")
    print(f"\ndoctrine ({len(brain.doctrine)} rules):")
    for d in brain.doctrine:
        print(f"  [{d.type.value}] {d.rule}  ({d.source})")
    if brain.playbook:
        print(f"\nplaybook:")
        for e in brain.playbook:
            print(f"  {e.action}")
    return 0


def _cmd_contribute(args: argparse.Namespace) -> int:
    """Run the full contribution loop for a repo (dry — builds the PR body,
    does not push). The loop is fail-closed; a blocked contribution exits 1."""
    system = ResidentEngineeringSystem()
    system.register_agent(create_resident_engineer("resident-engineer"))
    # pull the repo's brain in so the loop consults real doctrine
    docs = fetch_doctrine_docs(args.repo)
    if docs:
        system.register_brain(build_brain(args.repo, f"https://github.com/{args.repo}", docs))

    result = system.run_contribution(
        args.title, args.description, args.repo,
        files_changed=args.files.split(",") if args.files else [],
        tests_added=args.tests.split(",") if args.tests else [],
        test_results={"passed": args.passed, "failed": args.failed},
        approach=args.approach,
        risks=args.risks.split(",") if args.risks else [],
    )
    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        status = result["status"]
        print(f"status: {status}  (stage: {result.get('stage')})")
        if status == "ready":
            print(f"court: {result['court']['verdict']}  score={result['court']['score']}")
            print(f"branch: {result['pr']['branch']}")
            print("\n--- PR body ---")
            print(result["pr_body"])
        else:
            print(f"reason: {result.get('reasoning', '')}")
            if result.get("conflicts"):
                for c in result["conflicts"]:
                    print(f"  conflict: {c}")
            if result.get("failures"):
                print(f"  failed checks: {', '.join(result['failures'])}")
    return 0 if result["status"] == "ready" else 1


def _cmd_show(args: argparse.Namespace) -> int:
    """Print a brain's learned state (doctrine / precedents / failures)."""
    brain = build_brain(args.repo, "", {"AGENTS.md": args.text} if args.text else {})
    if args.json:
        print(json.dumps(brain.to_dict(), indent=2, default=str))
        return 0
    print(f"# {brain.project} — doctrine {len(brain.doctrine)}, "
          f"precedents {len(brain.precedents)}, failures {len(brain.failure_patterns)}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="resident-engineer",
                                description="Autonomous OSS Resident Engineering System")
    sub = p.add_subparsers(dest="command", required=True)

    b = sub.add_parser("brain", help="fetch a repo's doctrine + build its brain (read-only)")
    b.add_argument("repo", help="owner/name")
    b.add_argument("--json", action="store_true")
    b.set_defaults(func=_cmd_brain)

    c = sub.add_parser("contribute", help="run the full contribution loop (dry, fail-closed)")
    c.add_argument("repo", help="owner/name")
    c.add_argument("--title", required=True)
    c.add_argument("--description", required=True)
    c.add_argument("--approach", required=True)
    c.add_argument("--files", help="comma-separated files changed")
    c.add_argument("--tests", help="comma-separated tests added")
    c.add_argument("--risks", help="comma-separated risks")
    c.add_argument("--passed", type=int, default=0)
    c.add_argument("--failed", type=int, default=0)
    c.add_argument("--json", action="store_true")
    c.set_defaults(func=_cmd_contribute)

    s = sub.add_parser("show", help="print a brain's learned state")
    s.add_argument("repo")
    s.add_argument("--text", help="raw AGENTS.md text (offline)")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=_cmd_show)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
