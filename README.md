# Resident Engineering System v2

Autonomous Open-Source Resident Engineering System — a multi-agent system that resides inside open-source projects, understands their history and philosophy, and gradually evolves from visitor to trusted contributor.

## Status — what actually runs (verified 2026-10-12)

The architecture below is the design. **This is what is implemented and
tested today** — not the vision, the code on disk:

- **Doctrine reader** — `brain/extractor.py` + `brain/fetch.py` read a real
  repo's `AGENTS.md`/`CONTRIBUTING.md` via `gh api` and extract explicit rules
  (lines carrying a rule signal). Conservative: prose without a rule signal is
  ignored, never invented. Code fences are skipped; short/ambiguous tokens
  (`pr`, `ci`, `only`) match whole words only, not inside other words.
- **Fail-closed gates** — `TaskAdmission` rejects unclear/unverifiable tasks;
  `VerificationCourt` fails on any critical check (including a real scope limit
  and real test-result validation). Both tested.
- **Full contribution loop** — `run_contribution` wires
  admission → brain consult → route → cell(plan/build/review) → court →
  proof-carrying PR. A blocked stage returns `blocked`, never `ready`; a
  brainless run is `draft`, never `ready`.
- **Resident step** — `consult_brain` reads the project's extracted doctrine
  before building and blocks an approach that conflicts with a compatibility
  rule (the conflict keys on the approach, not the rule text).
- **Closed loop** — `apply_pr_outcome` folds a real PR's merged/rejected result
  into the brain as a precedent/failure_pattern, which the next `consult_brain`
  reads.
- **CLI** — `resident-engineer brain|contribute|show`, fail-closed (blocked
  exits 1). `contribute` is dry by default; `--no-brain` stays offline.

**96 tests pass** (`pytest`). Runtime deps: **zero** (stdlib only).

**Review-hardened (v0.1.1).** An adversarial `slop-reviewer` pass over the
v0.1.0 diff returned HOLD with 16 findings; every critical one was reproduced,
fixed, and pinned with a regression test (`tests/test_review_fixes.py`). Among
the fixes: the scope check is a real threshold not a hardcoded pass, a
brainless run is draft not ready, test results must be real ints, doctrine
classification is word-boundary not substring, and code fences are not
doctrine.

```bash
# read a repo's doctrine into a brain (read-only)
resident-engineer brain owner/repo

# run the full loop, dry (builds the PR body, pushes nothing)
resident-engineer contribute owner/repo --title "..." --description "..." \
  --approach "..." --files a.py --passed 5

# offline / testable (skip the network fetch)
resident-engineer contribute owner/repo ... --no-brain
```

## Architecture

```
                 GLOBAL WISDOM COMMONS
      Constitution + Principle Cards + Skills
                           │
                           ▼
                  REPOSITORY BRAIN
       Doctrine + Architecture + Precedents
       Tests + Ownership + Repo Playbook
                           │
                           ▼
                     TASK ADMISSION
        Is it wanted? clear? valuable? verifiable?
                           │
                           ▼
                 ACCEPTANCE THESIS
        Why should this contribution be accepted?
                           │
                           ▼
                    ENGINEERING CELL
       Interpret → Plan → Build → Review → Revise
                           │
                           ▼
                 VERIFICATION COURT
     Behaviour + Scope + Compatibility + Security
                           │
                           ▼
                   PROOF-CARRYING PR
       Patch + Tests + Evidence + Risks + Rationale
                           │
                           ▼
                    OUTCOME LEARNING
      Merge / rejection / comments / regressions
                           │
                           └──→ Update candidate wisdom
```

## Concepts

### Core
- **Citizens** — agent citizenship with rights, responsibilities, and reputation
- **Guilds** — groups of agents with shared goals and collaboration
- **Institutions** — formal rules and governance for projects
- **Team Formation** — dynamic assembly of agent teams for tasks
- **Global Reputation** — reputation across all projects
- **Advanced Routing** — assigns tasks to the most suitable agent or team

### Research-Based
- **ACE** (Agentic Context Engineering) — arxiv 2510.04618 — evolving playbooks
- **GEPA** (Genetic-Pareto Prompt Evolution) — arxiv 2507.19457 — reflective prompt optimization
- **Agent Lightning** — Microsoft Research — RL-based training for agents

### Infrastructure
- **NATS** — messaging system for inter-agent communication
- **Temporal** — durable execution for complex workflows
- **Certification DB** — stores and verifies agent certifications

## Components

### Kernel
- **Agent Identity** — every bot has a unique identity, history, and certifications
- **Communication Fabric** — NATS-inspired message bus with pub/sub and request-reply
- **Workflow Engine** — Temporal-inspired durable execution with retry logic
- **Knowledge Graph** — per-project memory with precedents, doctrine, and architecture
- **Reputation Ledger** — global reputation across projects
- **Task Router** — assigns tasks to the most suitable agent
- **Learning Loop** — learns from outcomes to improve future decisions

### Repository Brain
- **Doctrine** — project-specific rules extracted from AGENTS.md, CONTRIBUTING.md, etc.
- **Architecture** — component map with dependencies and public APIs
- **Precedents** — merged/rejected PR patterns with maintainer feedback
- **Playbook** — procedural knowledge for common tasks

### Task Admission
- Evaluates whether a task is wanted, clear, valuable, and verifiable
- Rejects tasks that don't meet criteria

### Engineering Cell
- **Plan** — generates plan candidates
- **Build** — executes the plan
- **Review** — independent review
- **Revise** — fixes based on review feedback

### Verification Court
- **Behavior** — tests pass
- **Scope** — no unrelated changes
- **Compatibility** — public behavior preserved
- **Security** — no vulnerabilities introduced

### Proof-Carrying PR
- Every PR carries its evidence: tests, benchmarks, reviews, CI results
- Risks and rationale are documented

## Levels

### Level 1 — Repository Technician
- Fix small, clear bugs
- Write regression tests
- Fix type/lint errors
- Fix CI workflows
- Fix boundary conditions
- Fix documentation-code inconsistencies

### Level 2 — Issue Resolution Engineer
- Root cause analysis
- Modify 2-8 related files
- Understand call graph
- Maintain backward compatibility
- Add positive and negative tests

### Level 3 — Repository Resident Engineer
- Repeated contributions to same project
- Deep understanding of subsystems
- Suggest fixes aligned with project direction
- Discover issues similar to past errors
- Review PRs
- Identify missing tests

### Level 4 — Maintainer-Support Engineer
- Issue triage
- Reproduce bug reports
- Detect duplicates
- Classify severity
- Review PRs and identify blockers
- Write design proposals
- Split large features into small PRs

## Wisdom Stack

### 1. Engineering Constitution
Fixed principles that become policy checks, diff constraints, plan scoring, verifier rules, and automatic rejection reasons.

### 2. Repository Doctrine
Project-specific wisdom extracted from AGENTS.md, CONTRIBUTING.md, README, GOVERNANCE.md, CODEOWNERS, issue/PR templates, CI workflows, ADRs, tests, release notes, maintainer comments, merged/rejected PRs.

### 3. Principle Cards
Each wisdom becomes an executable artifact: Trigger → Rule → Exception → Evidence → Verifier.

### 4. Precedent Graph
Learning from past decisions: Issue → Proposed approach → Maintainer objection → Revision → Merge/Close → Post-merge outcome.

### 5. Skills
Procedural expertise as independent packages: reproduce-bug, review-public-api-change, design-regression-tests, minimal-pr-design, dependency-change-review, maintainer-comment-analysis, performance-regression-check.

### 6. Verifier Packs
What to measure for each task type: Bug Fix, API Change, Performance, Migration, Refactor, Documentation.

## Installation

```bash
git clone https://github.com/faresrafat3/resident-engineer
cd resident-engineer
pip install -e .
```

Requires Python ≥3.10. **Zero runtime dependencies** (stdlib only). `gh` CLI
is needed only for the `brain`/`contribute` commands that read a live repo;
everything else — admission, the court, the loop, the CLI's `show` — runs
fully offline.

## Usage

```python
from resident_engineer import ResidentEngineeringSystem
from resident_engineer.bots import create_resident_engineer, create_reviewer

# Create the system
system = ResidentEngineeringSystem()

# Register agents
re = create_resident_engineer()
rv = create_reviewer()
system.register_agent(re)
system.register_agent(rv)

# Submit a task
result = system.submit_task(
    title="Fix CSV exporter escaped quotes handling",
    description="The CSV exporter does not handle escaped quotes properly...",
    project="my-project",
)

# Record outcome
system.record_outcome(
    agent_id=re.id,
    project="my-project",
    outcome=OutcomeType.PR_MERGED,
    delta=10.0,
    evidence={"pr_number": 100},
)
```

## Development

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=src/resident_engineer

# Type check
mypy src/resident_engineer

# Lint
ruff check src/resident_engineer
```

## License

MIT
