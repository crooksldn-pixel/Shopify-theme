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
    # Which of `calls` should become cards, when that is not all of them. `None` — the usual
    # case — means all of them, and `calls` is what reaches the screen. `calls` ALWAYS reaches
    # the turn log and the timeline, whatever this says: what was read is a fact about the
    # turn, and what is worth looking at is a decision about the answer.
    #
    # Two recipes need the distinction. "Which customers need replying to?" passes `[]` and
    # draws its own queue, because the cards its analytic reads imply were a revenue ranking,
    # two working sets, a metric group and a table — five cards, none of which said who was
    # waiting. "What else has this customer ordered?" reads the ORDER first, only to learn
    # whose it is, and passes just the history: the order card was being redrawn above the
    # answer, pushing the answer off the bottom of the screen.
    drawn: list[Any] | None = None
    # Set when part of what was asked could not be read. The answer says so in words; this is
    # for the timeline and the report.
    partial: bool = False
    # What the recipe did, for the trace: read names, cache hits, where the time went.
    trace: dict[str, Any] = field(default_factory=dict)
    # A recipe that finds it cannot honestly answer says so here and the turn goes to Claude.
    defer: str = ""
    # The model's half of a compound answer (brief section 16). A recipe that has drawn the
    # workspace but cannot write the sentence — "tell me what they are waiting for, and draft
    # the reply" needs prose and a draft, which is Claude's — puts here what Claude should be
    # told, and the turn goes ON to the model with the cards already built. Without it the
    # recipe either answered half the question and stopped, or the owner had to ask a second
    # time; the bench's worst turn was thirty-five seconds of exactly that.
    #
    # It is an INSTRUCTION, never an answer: it quotes what was read and names the tool to
    # call. Only read with `partial` set, and never written to the timeline — it carries a
    # customer's words.
    continuation: str = ""

    @property
    def deferred(self) -> bool:
        return bool(self.defer)
