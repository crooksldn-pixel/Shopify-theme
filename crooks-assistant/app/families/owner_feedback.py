""""Log that your split function is broken" is a thing the Mac can do (§16).

Twice in the live hour the owner asked for a defect to be written down, and twice he was told
there was no tool for it — "I've no tool for logging a product bug like that", then "I still
have no tool that logs product feedback". The report that came out of the session did not
mention any of the four defects he had narrated out loud.

This is the family that takes those sentences. It runs only while a TEST SESSION is active,
because that is what makes them development feedback rather than a shop instruction, and all
it does is append an `owner_feedback` event to the timeline
(`app/observability/feedback.py`) and say so.

It reads nothing and stages nothing. There is no proposal, no gesture and no approval,
because nothing is being changed: writing down what somebody said about a button is not a
change to the shop, and this module imports neither a tool nor the action engine. Nothing
here reaches Shopify or Gmail.

The sentence itself is long, and deliberately so — a tester narrating what went wrong uses
as many clauses as he needs ("a lot of your functions are broken or halfway there… especially
with the back button, back to assistant button and the next button"). The router's usual
penalty for clauses would refuse exactly the sentences this family exists for, so it opts out
of it the way the composer does, and the recognition rule carries the weight instead.
"""

from __future__ import annotations

from app.fastpath.intent import Family, extend, signal
from app.fastpath.models import Ctx, FastAnswer
from app.fastpath.recipes import CACHE_NONE, Recipe, register
from app.observability import feedback
from app.reads.scheduler import ReadPlan, ReadResult

# What the owner is told. Short, and honest about where it went: on this session's record, and
# nowhere else.
LOGGED = ("Logged against this test session, with the screen you were on. "
          "It will be in the report under owner-reported defects, so you will not have to say "
          "it again. Nothing was sent anywhere.")
LOGGED_AS_TEST = ("Logged against this test session as one to turn into a test. "
                  "It will be in the report under owner-reported defects. Nothing was sent anywhere.")


def _says_feedback(sig) -> bool:
    """A sentence of that shape, WHILE a session is being tested.

    Both halves matter. Without the recognition rule this family would take any complaint;
    without the session check it would take one on an ordinary Tuesday, when there is nowhere
    to put it and the honest answer is the one the assistant already gives.
    """
    return feedback.active() and feedback.recognise(" ".join(sig.words)) is not None


_SAYS_FEEDBACK = signal("says_owner_feedback", _says_feedback)


def _plan(ctx: Ctx) -> ReadPlan | None:      # noqa: ARG001 — nothing is read
    return None


def _render(ctx: Ctx, result: ReadResult) -> FastAnswer:      # noqa: ARG001 — nothing was read
    recognition = feedback.recognise(ctx.text)
    if recognition is None:
        return FastAnswer(answer="", defer="that did not read as feedback about the product")
    event = feedback.record(
        recognition, branch=ctx.branch,
        session_id=str(getattr(ctx.session, "session_id", "") or ""),
        turn_id=str(getattr(ctx.session, "turn_id", "") or ""),
    )
    if event is None:
        # The session stopped between the router and here. Say nothing was recorded rather
        # than say it was: a false "logged" is worse than the answer he got in September.
        return FastAnswer(answer="", defer="no test session is recording")
    return FastAnswer(
        answer=LOGGED_AS_TEST if recognition.kind == "save_as_test" else LOGGED,
        trace={"source": "owner_feedback", "kind": recognition.kind,
               "screen": list(event.get("screen") or []), "nearby": len(event.get("nearby") or [])},
    )


register(Recipe(
    recipe_id="owner_feedback", intent_family="owner_feedback", read_primitives=(),
    ui="assistant", cache_policy=CACHE_NONE, min_confidence=0.72, target_ms=30,
    plan=_plan, render=_render,
))

extend([
    # `many_clauses`, because a defect narrated out loud is one report with as many clauses as
    # the owner cares to speak. `max_words` for the same reason: the second of the two live
    # sentences ran to more than fifty words, and a family that refuses those refuses the
    # evidence. `mutation` is not blocked: "log that the refund button is broken" carries the
    # word refund, and it is still a bug report — the recognition rule, not the word list, is
    # what decides.
    # `serves_mutation_words`, because "note that the split is broken" and "record that the
    # next button does nothing" carry mutation verbs and are still reads: what they change is
    # a line in a local log, and this family names no tool, no write and no operation. The
    # router's refusal to SERVE a mutation sentence is what it always was for every family
    # that has not declared this.
    Family("owner_feedback", needs=(_SAYS_FEEDBACK,), boosts=(),
           blocks=("order_number",),
           base=0.94, floor=0.72, max_words=120, many_clauses=True,
           serves_mutation_words=True),
])
