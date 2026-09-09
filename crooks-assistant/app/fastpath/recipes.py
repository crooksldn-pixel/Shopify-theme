"""Fast-path execution recipes.

One recipe per intent family: which reads it needs, which of them are independent, what card
it prefers, how long its answers stand, and how sure the router has to be before it runs.

A recipe is a procedure, not a phrase. `order_lookup` is "find the order, then read it and
its customer's history together, then say the one sentence that answers the question" — and
that is true whether the owner said "order 1938", "pull up 1938" or "1938 please".

READ ONLY. `assert_read_only()` is checked at import and again before each run; a recipe
naming a write tool is a crash at start-up, not a surprise in production.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from app.fastpath.models import Ctx, FastAnswer
from app.reads.scheduler import ReadPlan, ReadResult

# What a recipe's answers are worth caching as, and for how long the fast path may reuse one.
CACHE_NONE = "none"
CACHE_HOT = "hot"
CACHE_ENTITY = "entity"
CACHE_ANALYTICS = "analytics"
CACHE_EMAIL = "email"


@dataclass(slots=True)
class Stats:
    """How a recipe has actually been doing. Measured, never assumed: the bench and the
    report read these rather than a number written into a docstring."""

    runs: int = 0
    hits: int = 0
    deferred: int = 0
    failures: int = 0
    total_ms: float = 0.0
    last_ms: float = 0.0
    last_success: float = 0.0

    @property
    def average_ms(self) -> float:
        return round(self.total_ms / self.runs, 1) if self.runs else 0.0

    def record(self, ms: float, *, ok: bool, deferred: bool = False, clock=time.time) -> None:
        self.runs += 1
        self.total_ms += ms
        self.last_ms = round(ms, 1)
        if deferred:
            self.deferred += 1
        elif ok:
            self.hits += 1
            self.last_success = clock()
        else:
            self.failures += 1

    def public(self) -> dict[str, Any]:
        return {"runs": self.runs, "hits": self.hits, "deferred": self.deferred, "failures": self.failures,
                "average_ms": self.average_ms, "last_ms": self.last_ms, "last_success": self.last_success or None}


@dataclass(frozen=True, slots=True)
class Recipe:
    recipe_id: str
    intent_family: str
    # What must resolve before this may run at all. The runner checks each against the
    # branch and the request; an unresolved one sends the turn to Claude.
    required_entities: tuple[str, ...] = ()
    read_primitives: tuple[str, ...] = ()
    # Which of the reads are independent, as the plan expresses it. Documentation the tests
    # assert against, so a dependency added to `plan` without updating this is caught.
    parallel_nodes: tuple[tuple[str, ...], ...] = ()
    ui: str = "assistant"
    cache_policy: str = CACHE_NONE
    min_confidence: float = 0.7
    # Milliseconds this recipe should finish in. The report flags a recipe that does not.
    target_ms: int = 1000
    plan: Callable[[Ctx], ReadPlan | None] | None = None
    render: Callable[[Ctx, ReadResult], FastAnswer] | None = None
    stats: Stats = field(default_factory=Stats)

    def public(self) -> dict[str, Any]:
        return {
            "recipe_id": self.recipe_id, "intent_family": self.intent_family,
            "required_entities": list(self.required_entities), "reads": list(self.read_primitives),
            "parallel_nodes": [list(g) for g in self.parallel_nodes], "ui": self.ui,
            "cache_policy": self.cache_policy, "min_confidence": self.min_confidence,
            "target_ms": self.target_ms, "stats": self.stats.public(),
        }


RECIPES: dict[str, Recipe] = {}


def register(recipe: Recipe) -> Recipe:
    RECIPES[recipe.recipe_id] = recipe
    return recipe


def recipe_for(family: str) -> Recipe | None:
    for recipe in RECIPES.values():
        if recipe.intent_family == family:
            return recipe
    return None


def assert_read_only(recipes: dict[str, Recipe] | None = None) -> None:
    """Every read primitive named by every recipe is a read tool. Called at start-up and
    before each run: the fast lane's inability to write is structural."""
    from app.tools import registry

    for recipe in (recipes or RECIPES).values():
        for tool in recipe.read_primitives:
            try:
                spec = registry.get(tool)
            except KeyError:
                continue    # a tool this build does not carry; the plan will skip it
            if spec.write is not None or spec.batch is not None:
                raise RuntimeError(f"recipe {recipe.recipe_id} names the write tool {tool}; the fast lane cannot write")


def stats_snapshot() -> dict[str, Any]:
    return {rid: recipe.stats.public() for rid, recipe in sorted(RECIPES.items())}
