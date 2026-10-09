"""GEPA — Genetic-Pareto Prompt Evolution.

Based on: arxiv 2507.19457
Reflective prompt evolution using genetic algorithms and Pareto optimization.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
import random
import uuid


class MutationType(str, Enum):
    ADD = "add"
    REMOVE = "remove"
    MODIFY = "modify"
    REORDER = "reorder"
    COMBINE = "combine"


@dataclass
class PromptCandidate:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    text: str = ""
    score: float = 0.0
    metrics: dict[str, float] = field(default_factory=dict)
    generation: int = 0
    parent_ids: list[str] = field(default_factory=list)
    mutations: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "text": self.text,
            "score": self.score,
            "metrics": self.metrics,
            "generation": self.generation,
            "parent_ids": self.parent_ids,
            "mutations": self.mutations,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class GEPAIteration:
    iteration: int
    candidates: list[PromptCandidate]
    best_candidate: PromptCandidate | None = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "iteration": self.iteration,
            "candidates": [c.to_dict() for c in self.candidates],
            "best_candidate": self.best_candidate.to_dict() if self.best_candidate else None,
            "timestamp": self.timestamp.isoformat(),
        }


class GEPAEngine:
    """Genetic-Pareto prompt evolution engine."""

    def __init__(self, population_size: int = 10, mutation_rate: float = 0.3) -> None:
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self._iterations: list[GEPAIteration] = []
        self._population: list[PromptCandidate] = []

    def initialize(self, base_prompt: str) -> None:
        """Initialize population with variations of base prompt."""
        self._population = []
        for i in range(self.population_size):
            candidate = PromptCandidate(
                text=base_prompt,
                score=0.0,
                generation=0,
                mutations=["initial"],
            )
            self._population.append(candidate)

    def evaluate(self, evaluator: Any) -> None:
        """Evaluate all candidates using provided evaluator function."""
        for candidate in self._population:
            result = evaluator(candidate.text)
            if isinstance(result, dict):
                candidate.score = result.get("score", 0.0)
                candidate.metrics = result.get("metrics", {})
            else:
                candidate.score = float(result)

    def select(self) -> list[PromptCandidate]:
        """Select top candidates using Pareto frontier."""
        # Sort by score descending
        sorted_pop = sorted(self._population, key=lambda c: c.score, reverse=True)
        # Take top 50%
        return sorted_pop[:max(1, len(sorted_pop) // 2)]

    def mutate(self, candidate: PromptCandidate) -> PromptCandidate:
        """Create a mutated copy of a candidate."""
        mutations = []
        text = candidate.text

        if random.random() < self.mutation_rate:
            # Add a sentence
            additions = [
                "Ensure all edge cases are covered.",
                "Verify backward compatibility.",
                "Check for security implications.",
                "Validate input parameters.",
                "Test with negative cases.",
            ]
            text += " " + random.choice(additions)
            mutations.append("add")

        if random.random() < self.mutation_rate and len(text) > 100:
            # Remove a sentence
            sentences = text.split(". ")
            if len(sentences) > 1:
                idx = random.randint(0, len(sentences) - 1)
                sentences.pop(idx)
                text = ". ".join(sentences)
                mutations.append("remove")

        if random.random() < self.mutation_rate:
            # Modify wording
            replacements = {
                "check": "verify",
                "test": "validate",
                "fix": "resolve",
                "add": "introduce",
                "remove": "eliminate",
            }
            for old, new in replacements.items():
                if old in text.lower():
                    text = text.lower().replace(old, new, 1)
                    mutations.append("modify")
                    break

        return PromptCandidate(
            text=text,
            score=0.0,
            generation=candidate.generation + 1,
            parent_ids=[candidate.id],
            mutations=mutations,
        )

    def evolve(self, generations: int = 5) -> PromptCandidate:
        """Run evolution for specified generations."""
        for gen in range(generations):
            # Selection
            parents = self.select()

            # Create new population
            new_population = []
            while len(new_population) < self.population_size:
                parent = random.choice(parents)
                child = self.mutate(parent)
                new_population.append(child)

            self._population = new_population

            # Record iteration
            best = max(self._population, key=lambda c: c.score)
            iteration = GEPAIteration(
                iteration=gen + 1,
                candidates=list(self._population),
                best_candidate=best,
            )
            self._iterations.append(iteration)

        return max(self._population, key=lambda c: c.score)

    def get_best(self) -> PromptCandidate | None:
        if not self._population:
            return None
        return max(self._population, key=lambda c: c.score)

    def to_dict(self) -> dict[str, Any]:
        return {
            "population_size": self.population_size,
            "mutation_rate": self.mutation_rate,
            "iterations": [i.to_dict() for i in self._iterations],
            "current_population": [c.to_dict() for c in self._population],
        }
