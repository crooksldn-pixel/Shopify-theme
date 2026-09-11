"""A question about the screen is answered by the Mac, not guessed at by the model (§15).

    "What does the split button do?"
    "I don't know what that button is — not something I control, so best to check with
     whoever built the tablet screen."

The model had nothing to answer from, so it disclaimed the product's own primary control. The
answer exists — `app/observability/ui_semantics.py` is a bounded manifest of what each control
does, derived from the command registry that implements them — and this family is what reaches
it. One read family, no tools, no model, no reads at all: the answer is already on the Mac.

Two bounds make this safe to route so confidently.

* The signal is the manifest itself. `asks_about_the_screen` is true only when the manifest
  has a matching entry for the sentence, which needs both a frame that reads as a question
  about the interface AND an entry whose own pattern matches. "Go back" is not a question and
  still navigates; "has the order come back yet" is about the shop and never reaches here.
* It explains, and never acts. "How do I go back?" is answered with where Back is and what it
  does — it does not go back. A sentence that means the move ("go back", "back") carries no
  question frame, so it keeps `navigation_back` as it always did.

The confidence is deliberately above `navigation_back`'s: the one sentence where the two
families overlap is "how do I go back", and that is a question about a control. Anything
softer put it inside the router's margin and sent a question about the screen to the model,
which is the defect this family exists to close.
"""

from __future__ import annotations

from app.fastpath.intent import Family, extend, signal
from app.fastpath.models import Ctx, FastAnswer
from app.fastpath.recipes import CACHE_NONE, Recipe, register
from app.observability import feedback, ui_semantics
from app.reads.scheduler import ReadPlan, ReadResult
from app.surfaces import Freshness, Surface


def _asks_about_the_screen(sig) -> bool:
    """Whether the manifest can answer this sentence. The predicate IS the lookup, so the
    family cannot route a question the manifest then fails to answer."""
    return ui_semantics.lookup(" ".join(sig.words)) is not None


def _reports_a_defect(sig) -> bool:
    """Whether the sentence is a bug report rather than a question.

    "Record that the next button does nothing" names a control and is not asking what it is
    for. Both families would otherwise see it, land within the router's margin and send it to
    the model — which is where both of the September sentences went.
    """
    return feedback.recognise(" ".join(sig.words)) is not None


_SAYS_UI = signal("asks_about_the_screen", _asks_about_the_screen)
_REPORTS_DEFECT = signal("reports_a_defect", _reports_a_defect)


def _plan(ctx: Ctx) -> ReadPlan | None:       # noqa: ARG001 — nothing is read
    return None


def _surface(answer: ui_semantics.Answer) -> Surface:
    """The manifest as a card, in the vocabulary the tablet already draws.

    The `capability` renderer, because that is what this is: what the product can do, said
    about its own controls rather than about the shop. A new card type would be the defect
    D-15 names — a shape one side can emit and the other cannot draw.
    """
    groups = ui_semantics.groups()
    asked = answer.entry.group
    # The group the question was about first, so the answer is the first thing on screen.
    groups.sort(key=lambda g: (g["area"] != asked,))
    return Surface(
        surface_type="capability", ui_type="capability",
        title="The controls",
        subtitle=answer.entry.control,
        data={
            "title": "The controls",
            "build": "", "fingerprint": "", "writes_enabled": False,
            "counts": {"reads": sum(len(g["items"]) for g in groups), "changes": 0, "bulk": 0},
            "groups": groups,
            "examples": ["What does Split do?", "How do I go back?", "What does Applying mean?"],
            "note": "",
        },
        freshness=Freshness(source="mac", complete=True),
        spoken_summary=answer.words,
    )


def _render(ctx: Ctx, result: ReadResult) -> FastAnswer:      # noqa: ARG001 — nothing was read
    answer = ui_semantics.lookup(ctx.text)
    if answer is None:
        # The router matched on the tokenised words and the manifest is being asked with the
        # sentence as it was said. If those ever disagree, the model takes the turn rather
        # than this family inventing something.
        return FastAnswer(answer="", defer="the manifest has no entry for that control")
    return FastAnswer(
        answer=ui_semantics.spoken(answer),
        surfaces=[_surface(answer)], drawn=[],
        trace={"source": "ui_semantics", "entry": answer.entry.key,
               "command": answer.entry.command or None},
    )


register(Recipe(
    recipe_id="ui_semantics", intent_family="ui_semantics", read_primitives=(),
    ui="capability", cache_policy=CACHE_NONE, min_confidence=0.72, target_ms=40,
    plan=_plan, render=_render,
))

extend([
    # Above `navigation_back` (0.85) on purpose: "how do I go back" is the one sentence both
    # families see, and it is a question about a control. Blocked by everything that makes a
    # sentence about the shop instead, so a question with an order number or a period in it
    # never reaches the manifest.
    # Not blocked by `waiting`: the router counts "back" among the words of someone waiting to
    # hear back, so blocking it would have ruled out every question about the Back button.
    # The manifest's own frame is what keeps "who is waiting to hear back" out of here — it
    # is not a question about a control, so `asks_about_the_screen` is false for it.
    # `serves_mutation_words`: "what does the refund button do" carries a mutation verb and
    # is a question about a control. This family reads nothing and names no tool, and the
    # manifest lookup is the gate — "refund them the postage" has no question frame, so it
    # never reaches here.
    Family("ui_semantics", needs=(_SAYS_UI,), boosts=("question",),
           blocks=(_REPORTS_DEFECT, "order_number", "period", "ranking", "known_name",
                   "possessive_name", "stock", "running_out", "delayed",
                   "address", "status", "bought"),
           base=0.93, floor=0.72, max_words=12, serves_mutation_words=True),
])
