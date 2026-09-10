"""What a recipe is handed and what it returns."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class Ctx:
    """Everything a recipe may read. Deliberately small: a recipe that needs more than this
    is not a recipe, it is a question for the model."""

    runtime: Any
    session: Any
    branch: Any
    intent: Any
    text: str
    memory: Any = None
    calls: list[Any] = field(default_factory=list)
    # What a navigation move produced, when the runner made one before the plan ran. The plan
    # reads it to know which record it is about to land on.
    moved: dict[str, Any] = field(default_factory=dict)

    @property
    def order_number(self) -> str:
        numbers = self.intent.slots.get("order_numbers") or []
        return str(numbers[0]) if len(numbers) == 1 else ""

    def entity(self, kind: str) -> str:
        """The branch's current entity, when it is of this kind."""
        found = getattr(self.branch, "entity", None) or {}
        return str(found.get("ref") or "") if found.get("kind") == kind else ""


@dataclass(slots=True)
class FastAnswer:
    """What the fast lane produces. The same shape /turn builds from a model answer, so the
    presentation layer, the turn log and the timeline do not know the difference."""

    answer: str
    calls: list[Any] = field(default_factory=list)
    # Cards this recipe built itself, for the answers that are not derived from a tool result.
    # `present()` builds the `ui` list by walking ToolCalls, which is right for a read — but it
    # left a recipe that reads nothing with no way to draw anything at all. "What can you do
    # now?" consults the capability manifest, calls no tool, and so drew no card and spoke a
    # paragraph instead. These are appended to the turn's `ui` as they stand.
    surfaces: list[Any] = field(default_factory=list)
    # Set when part of what was asked could not be read. The answer says so in words; this is
    # for the timeline and the report.
    partial: bool = False
    # What the recipe did, for the trace: read names, cache hits, where the time went.
    trace: dict[str, Any] = field(default_factory=dict)
    # A recipe that finds it cannot honestly answer says so here and the turn goes to Claude.
    defer: str = ""

    @property
    def deferred(self) -> bool:
        return bool(self.defer)
