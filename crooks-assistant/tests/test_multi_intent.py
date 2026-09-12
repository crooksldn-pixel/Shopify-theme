"""Multi-intent priority: the work the owner asked for outranks the status he asked about.

D-14. Turn 1 of the live session asked two things — "are you okay now?" and "pull up the
today's emails" — and got the capability delta and no emails. The rule is an order:

    explicit requested work  >  contextual status  >  capability explanation

A status answer may still be given; it may not take the turn.
"""

from __future__ import annotations

import pytest

from experience.harness import harness

RESTARTED = "I restarted you. Are you okay now? Can you pull up the today's emails"


@pytest.fixture()
async def stage():
    async with harness() as h:
        yield h


def _resolve(text: str):
    import app.fastpath.library  # noqa: F401 — registers the core recipes
    from app.families import load_all
    from app.fastpath.intent import resolve

    load_all()
    return resolve(text)


def test_the_restart_aside_does_not_hijack_the_request():
    """The work takes the turn and the status question is kept as the aside.

    The aside was `capability_delta` when this was written, and is `assistant_status` now
    (Phase 5 §24, app/families/interaction.py). The expectation is CHANGED, not weakened, and
    this is why: "are you okay now?" reached the delta family only because it carries the word
    "now" — `meta_more` — and the delta answers "what MORE can you do since the last build",
    which is a different question from the one he asked. There is now a family for the
    question he actually asked, and it is the more specific of the two, so it wins the aside.

    What must not change, and is asserted harder than before: the work still takes the turn,
    the status half is still kept rather than dropped, the aside is still a STATUS or
    CAPABILITY family rather than a second piece of work, and /turn still has a sentence to
    acknowledge it with.
    """
    from app.fastpath.intent import CAPABILITY, KIND_RANK, WORK, kind_of
    from app.routes.turn import _SECONDARY_WORDS

    intent = _resolve(RESTARTED)
    assert intent.family == "inbox_state", f"the turn went to {intent.family!r}"
    assert intent.secondary == "assistant_status", "the status half was thrown away rather than kept"
    assert KIND_RANK[WORK] < KIND_RANK[kind_of(intent.secondary)] <= KIND_RANK[CAPABILITY]
    assert _SECONDARY_WORDS.get(intent.secondary), "the aside has no words, so it is silently dropped"


def test_asking_to_be_shown_something_is_asking():
    """"Can you pull up the today's emails" is a request even though it opens with "can"."""
    assert _resolve("can you pull up the today's emails").family == "inbox_state"
    assert _resolve("pull up today's emails").family == "inbox_state"
    # And the plain forms still route as they did.
    assert _resolve("show me today's emails").family == "inbox_state"


def test_a_capability_question_on_its_own_is_still_a_capability_question():
    assert _resolve("what can you do now?").family in ("capability_delta", "capability_summary")
    assert _resolve("what else can you do since the last build?").family == "capability_delta"


def test_one_sentence_naming_two_jobs_is_still_the_models():
    """D-5's turn is not this rule's business: "orders AND emails AND correlate" is one
    sentence asking for a synthesis, and splitting it here would answer half of it."""
    assert _resolve("look up today's orders and today's emails and see if anything correlates").family == ""


async def test_the_multi_intent_turn_comes_back_with_the_emails(stage):
    capture = await stage.say(RESTARTED)
    assert capture.lane == "FAST", f"the turn went to {capture.lane}"
    assert capture.recipe_id == "inbox_state", f"answered by {capture.recipe_id!r}"
    assert not capture.prose_only, f"nothing on screen: {capture.answer!r}"
    assert any("email" in t for t in capture.surface_types), (
        f"no email surface; got {capture.surface_types}"
    )


async def test_the_health_answer_is_secondary_rather_than_absent(stage):
    capture = await stage.say(RESTARTED)
    assert "back" in capture.answer.lower() or "running" in capture.answer.lower(), (
        f"the owner asked if it was okay and was told nothing: {capture.answer!r}"
    )
