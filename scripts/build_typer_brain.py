"""Build Repository Brain for typer from codebase analysis."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
import json
from pathlib import Path

from resident_engineer.brain import (
    RepositoryBrain, Doctrine, DoctrineType, ArchitectureComponent,
    Precedent, PlaybookEntry,
)


def build_typer_brain() -> RepositoryBrain:
    """Build Repository Brain for the typer project."""
    brain = RepositoryBrain(
        project="typer",
        url="https://github.com/fastapi/typer",
        created_at=datetime.now(),
    )

    # Doctrine from pyproject.toml and code analysis
    brain.add_doctrine(Doctrine(
        type=DoctrineType.DESIGN,
        rule="Explicit over implicit — all parameters must be explicitly typed",
        source="pyproject.toml + code analysis",
        confidence=0.9,
    ))
    brain.add_doctrine(Doctrine(
        type=DoctrineType.DESIGN,
        rule="Based on Python type hints — leverage typing system fully",
        source="README.md",
        confidence=0.9,
    ))
    brain.add_doctrine(Doctrine(
        type=DoctrineType.DEPENDENCIES,
        rule="Minimal dependencies — shellingham, rich, annotated-doc only",
        source="pyproject.toml",
        confidence=0.85,
    ))
    brain.add_doctrine(Doctrine(
        type=DoctrineType.TESTING,
        rule="Tests use pytest with coverage — all new code needs tests",
        source="scripts/test.sh",
        confidence=0.9,
    ))
    brain.add_doctrine(Doctrine(
        type=DoctrineType.CONTRIBUTION,
        rule="PRs should address one concern only — no mixed changes",
        source="community norms",
        confidence=0.8,
    ))
    brain.add_doctrine(Doctrine(
        type=DoctrineType.STYLE,
        rule="Uses annotated-doc for Doc() annotations in function signatures",
        source="code analysis",
        confidence=0.85,
    ))

    # Architecture
    brain.add_architecture(ArchitectureComponent(
        name="typer.main.Typer",
        path="typer/main.py",
        purpose="Main entrypoint — Typer class, command registration, CLI execution",
        dependencies=["typer.core", "typer.models", "typer.params", "typer.utils"],
        public_api=["Typer", "run", "launch"],
        tests=["tests/test_annotated.py", "tests/test_application.py"],
    ))
    brain.add_architecture(ArchitectureComponent(
        name="typer.core",
        path="typer/core.py",
        purpose="Core CLI abstractions — TyperCommand, TyperGroup, TyperArgument, TyperOption",
        dependencies=["typer._click", "typer.models"],
        public_api=["TyperCommand", "TyperGroup", "TyperArgument", "TyperOption"],
        tests=["tests/test_core.py"],
    ))
    brain.add_architecture(ArchitectureComponent(
        name="typer.models",
        path="typer/models.py",
        purpose="Data models — ArgumentInfo, OptionInfo, ParameterInfo, Context, File types",
        dependencies=["typer._click"],
        public_api=["Context", "FileText", "FileBinaryRead", "OptionInfo", "ArgumentInfo"],
        tests=["tests/test_types_file.py"],
    ))
    brain.add_architecture(ArchitectureComponent(
        name="typer.params",
        path="typer/params.py",
        purpose="Parameter functions — Option() and Argument() with full overloads",
        dependencies=["typer.models", "typer._click"],
        public_api=["Option", "Argument"],
        tests=["tests/test_annotated.py"],
    ))
    brain.add_architecture(ArchitectureComponent(
        name="typer.utils",
        path="typer/utils.py",
        purpose="Utilities — parameter parsing, type hints, validation",
        dependencies=["typer.models"],
        public_api=["get_params_from_function"],
        tests=[],
    ))
    brain.add_architecture(ArchitectureComponent(
        name="typer._click",
        path="typer/_click/",
        purpose="Vendored Click fork — modified for Typer's needs",
        dependencies=[],
        public_api=[],
        tests=[],
    ))
    brain.add_architecture(ArchitectureComponent(
        name="typer.completion",
        path="typer/completion.py",
        purpose="Shell completion support",
        dependencies=["typer._click"],
        public_api=["get_completion_inspect_parameters"],
        tests=["tests/test_completion"],
    ))
    brain.add_architecture(ArchitectureComponent(
        name="typer.rich_utils",
        path="typer/rich_utils.py",
        purpose="Rich integration — pretty tracebacks, help formatting",
        dependencies=["typer.core"],
        public_api=["get_traceback"],
        tests=["tests/test_rich_utils.py"],
    ))

    # Playbook entries
    brain.add_playbook_entry(PlaybookEntry(
        trigger="new bug fix",
        action="1. Reproduce 2. Write failing test 3. Fix 4. Run full test suite",
        verification="Test passes, no regressions",
    ))
    brain.add_playbook_entry(PlaybookEntry(
        trigger="new feature",
        action="1. Check roadmap 2. Design API 3. Implement with tests 4. Update docs",
        verification="Tests pass, docs updated",
    ))
    brain.add_playbook_entry(PlaybookEntry(
        trigger="refactor",
        action="1. Ensure tests exist 2. Make minimal change 3. Verify tests pass",
        verification="All tests pass, behavior unchanged",
    ))

    # Test topology
    brain.test_topology = {
        "framework": "pytest",
        "runner": "scripts/test.sh",
        "coverage": "scripts/test-cov.sh",
        "lint": "scripts/lint.sh",
        "test_count": "1000+",
        "test_location": "tests/",
    }

    # Ownership
    brain.ownership = {
        "maintainer": "tiangolo",
        "core_team": "svlandeg, YuriiMotov, phalberg",
    }

    return brain


if __name__ == "__main__":
    brain = build_typer_brain()
    print(json.dumps(brain.to_dict(), indent=2, ensure_ascii=False))
