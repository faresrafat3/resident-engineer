# Resident Engineering System v2

Autonomous Open-Source Resident Engineering System — a multi-agent system that resides inside open-source projects, understands their history and philosophy, and gradually evolves from visitor to trusted contributor.

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
pip install -e .
```

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
