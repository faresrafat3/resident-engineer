# AGENTS.md — resident-engineer

Autonomous open-source Resident Engineering System: a multi-agent system that
resides inside OSS projects, understands their history and philosophy, and
evolves from visitor to trusted contributor.

This file is the **niche contract**. It refines `~/AGENTS.md` (never
contradicts it). An agent reads this first, runs the gate, and never forks a
fact into a second home.

## What is true

- **The system is real, not a skeleton.** `src/resident_engineer/` is ~2.3k
  lines across seven kernel modules (identity, communication, workflow,
  knowledge, reputation, learning) plus `pr/` and `lightning/`. Zero stubs.
- **The gate is `pytest`.** 22 tests in `tests/test_system.py` pass. The
  receipt is green tests, never prose.
- **`repos/` is vendored evidence, not source.** Typer is cloned there to
  study doctrine; it is gitignored on purpose. Never treat it as this repo's
  code, never commit it.
- **Runtime deps are stdlib-only.** NATS/Temporal are *inspired*, not
  imported — the message bus and workflow engine are reimplemented locally
  so the system runs offline and deterministically.

## What is law

- **Fail-closed.** A task that cannot be admitted (unwanted, unclear,
  unverifiable) is rejected before work starts. Admission is a gate, not a
  suggestion.
- **Independent verification.** The agent that builds does not verify its own
  work; the Verification Court (behaviour · scope · compatibility · security)
  is a separate step. Same doctrine as `crew-orchestrator` and `colony-kernel`.
- **Proof-carrying PR.** Every PR carries its evidence — tests, benchmarks,
  reviews, CI — with risks and rationale. A PR without evidence is not opened.
- **One home per fact.** A fact lives in exactly one file; everywhere else
  links to it.

## What is off-limits

- **No publication of secrets or private material** — this system touches
  public repos; nothing private leaves the boundary.
- **No self-mutation of the doctrine** — the Constitution and Principle Cards
  are updated only through the outcome-learning loop with a recorded merge or
  rejection, never by editing them to fit a decision already made.
- **`repos/` is read-only evidence** — study it, never build against it as a
  dependency.

## Gate command

```bash
# from the repo root, with a venv that has pytest:
python -m pytest tests/ -q        # 22 tests must pass
```

Verify before claiming. A green test run is the receipt; "it works" from
reasoning alone is not.

## Layout

| Path | What lives here |
|---|---|
| `src/resident_engineer/kernel/` | the seven kernel modules — identity, communication, workflow, knowledge, reputation, learning |
| `src/resident_engineer/pr/` | proof-carrying PR assembly |
| `src/resident_engineer/lightning/` | Agent-Lightning-style RL training hooks |
| `src/resident_engineer/team/` | dynamic team formation + routing |
| `tests/test_system.py` | the gate — 22 tests |
| `repos/` | vendored study clones (gitignored, read-only) |
| `profiles/` · `scripts/` | agent profiles and helper scripts |

## Where it fits

Sibling to `colony-kernel` (deterministic mission control), `quota-orchestrator`
(quota-native routing), and `crew-orchestrator` (the crew control layer). This
one is the *outward-facing* system: where the others govern an internal fleet,
resident-engineer is what crosses into public repos and earns trust there.
