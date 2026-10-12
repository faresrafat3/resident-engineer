First public release. A multi-agent system that reads a real OSS repo's doctrine, runs a **fail-closed** contribution loop, and learns from PR outcomes.

## What ships

**83 tests pass. Zero runtime dependencies** (stdlib only).

- **Doctrine reader** — `brain/extractor.py` + `brain/fetch.py` read a real repo's `AGENTS.md`/`CONTRIBUTING.md` via `gh api` and extract explicit rules. Conservative: prose without a rule signal is ignored, never invented.
- **Fail-closed gates** — `TaskAdmission` rejects unclear/unverifiable tasks; `VerificationCourt` fails on any critical check. Both tested.
- **Full contribution loop** — `run_contribution` wires admission → brain consult → route → cell(plan/build/review) → court → proof-carrying PR. A blocked stage returns `blocked`, never `ready`.
- **Resident step** — `consult_brain` reads the project's extracted doctrine before building and blocks an approach that conflicts with a compatibility rule.
- **Closed loop** — `apply_pr_outcome` folds a real PR's merged/rejected result into the brain as a precedent/failure_pattern, which the next `consult_brain` reads.
- **CLI** — `resident-engineer brain|contribute|show`, fail-closed (blocked exits 1). `--no-brain` stays fully offline.

## Install

```bash
pip install -e .
```

Requires Python ≥3.10. `gh` CLI only for the live-repo read commands; everything else runs offline.

## Verified

Against `colony-kernel`: fetches its real AGENTS.md, extracts its doctrine, recovers the gate command (`npm run verify`).
