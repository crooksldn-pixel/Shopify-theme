"""A question about the screen reaches the manifest, and nothing else changes (§15).

The manifest answers (tests/test_ui_semantics.py). This file is about the ROUTE to it: that
the five questions reach the family without a model, that the family draws a card the tablet
can already render, and — the part that matters most — that the sentences which MEAN a move
still make the move.
"""

from __future__ import annotations

import pytest

from app.families import load_all
from app.fastpath.intent import resolve
from app.fastpath.recipes import RECIPES, assert_read_only
from app.session.branch import Branch
from app.session.models import Session

load_all()


@pytest.fixture()
def branch():
    return Branch(branch_id="br_test", session_id="s1")


@pytest.fixture()
def session():
    return Session(session_id="s1")


FIVE = [
    ("What does the split button do?", "split"),
    ("How do I go back?", "back"),
    ("How do I type instead of speaking?", "composer"),
    ("What does Applying mean?", "applying"),
    ("How do I get back to this order?", "return_here"),
]


@pytest.mark.parametrize(("said", "_key"), FIVE)
def test_the_five_questions_take_the_fast_lane(said, _key):
    """No model on the path: a question about the product's own controls is answered by the
    product. The live session sent every one of these to Claude, which had nothing to answer
    from and said so."""
    intent = resolve(said)
    assert intent.family == "ui_semantics", f"{said!r} → {intent.family or '(the model)'}"
    assert intent.confidence >= 0.72


@pytest.mark.parametrize(("said", "key"), FIVE)
def test_the_recipe_answers_from_the_manifest_and_draws_the_controls(said, key, branch, session):
    from app.fastpath.models import Ctx
    from app.reads.scheduler import ReadResult

    recipe = RECIPES["ui_semantics"]
    ctx = Ctx(runtime=None, session=session, branch=branch, intent=resolve(said), text=said)
    assert recipe.plan(ctx) is None, "nothing is read to answer this"
    answer = recipe.render(ctx, ReadResult())
    assert not answer.deferred, answer.defer
    assert answer.trace["entry"] == key
    assert len(answer.answer) > 40
    assert len(answer.surfaces) == 1
    surface = answer.surfaces[0].as_ui()
    assert surface["type"] == "capability", "a card type the tablet already draws"
    assert surface["data"]["groups"] and surface["data"]["groups"][0]["items"]


def test_a_sentence_that_means_the_move_still_makes_the_move():
    """"Go back" navigates. "How do I go back?" explains. The distinction is the question
    frame, and nothing else about navigation changed."""
    assert resolve("go back").family == "navigation_back"
    assert resolve("back").family == "navigation_back"
    assert resolve("How do I go back?").family == "ui_semantics"


@pytest.mark.parametrize("said", [
    "has the order come back yet",
    "send it back to them",
    "who is waiting to hear back",
    "what did we sell today",
    "which orders are late",
    "order 1938",
    "what can you do?",
])
def test_a_question_about_the_shop_never_reaches_this_family(said):
    assert resolve(said).family != "ui_semantics", said


def test_the_family_reads_nothing_and_can_write_nothing():
    recipe = RECIPES["ui_semantics"]
    assert recipe.read_primitives == ()
    assert_read_only({"ui_semantics": recipe})


# ================================================== Phase 5 §23: the questions still open
#
# Four of the brief's seven were already answered above. Three were not, and two more came
# from the timeline afterwards (D-11). Every one of them is a question the assistant must
# answer from first-party semantics rather than disclaim.

NINE = [
    ("What does Split do?", "split"),
    ("How do I go back?", "back"),
    ("How do I type this?", "composer"),
    ("What is this screen?", "this_screen"),
    ("Why is this here?", "this_screen"),
    ("What happens if I merge?", "merge"),
    ("What does Next mean?", "next"),
    # D-11's two.
    ("What is on this screen?", "this_screen"),
    ("What am I looking at?", "this_screen"),
]


@pytest.mark.parametrize(("said", "key"), NINE)
def test_every_question_the_brief_names_reaches_the_manifest(said, key):
    """The manifest COVERS all nine. "What does Next mean?" matched nothing at all before —
    the entry's pattern wanted the word "do" after the control's name — and the three about
    this screen had no entry."""
    from app.observability import ui_semantics

    found = ui_semantics.lookup(said)
    assert found is not None, f"{said!r} is answered by nothing"
    assert found.entry.key == key, f"{said!r} -> {found.entry.key!r}"


@pytest.mark.parametrize(("said", "key"), NINE)
def test_every_question_the_brief_names_is_answered_without_a_model(said, key, branch):
    """§23: never "I do not know what the screen does". Both families are FAST and neither
    reads anything."""
    from app.fastpath import choose_lane, recipe_for

    intent = resolve(said, branch=branch)
    expected = "screen_state" if key == "this_screen" else "ui_semantics"
    assert intent.family == expected, f"{said!r} -> {intent.family or '(the model)'}"
    recipe = recipe_for(intent.family)
    assert recipe is not None and recipe.read_primitives == ()
    assert choose_lane(intent, recipe=recipe, text=said)[0] == "FAST"


def test_the_manifest_seam_did_not_break_the_table():
    """`extend` added an entry from a family's own file. Every entry that names a command
    still names a registered one, and nothing already in the table moved."""
    from app.observability import ui_semantics

    assert ui_semantics.check() == []
    keys = [e.key for e in ui_semantics.manifest()]
    assert len(keys) == len(set(keys)), "an entry is registered twice"
    for key in ("split", "merge", "back", "home", "next", "previous", "composer", "dock"):
        assert key in keys, key
    assert "this_screen" in keys
    with pytest.raises(ValueError, match="already registered"):
        ui_semantics.extend([ui_semantics.get("split")])


# --------------------------------------------------------- D-11: it can see the glass now


def divided(session, branch):
    """The screen the owner was actually looking at, at 23:07:41: deck empty, orb divided."""
    other = Branch(branch_id="br_other", session_id="s1", label="right", status="BACKGROUND")
    session.branches = {branch.branch_id: branch, other.branch_id: other}
    session.focused_branch = branch.branch_id
    return other


# The two answers the live session gave, verbatim. Both technically correct; both about the
# assistant's own outbox rather than about the glass, and he tapped the screen 33 times in the
# 90 seconds after them.
SEPTEMBER_ANSWERS = [
    "Nothing's come from me \u2014 I haven't run anything yet, no card's up on my end.",
    "Nothing running here, nothing pending on a card.",
]


@pytest.mark.parametrize("said", SEPTEMBER_ANSWERS)
def test_the_answers_it_actually_gave_are_recognised_as_false(said):
    from app.capabilities import screen

    assert screen.claims_an_empty_screen(said), f"this was allowed to stand: {said!r}"


@pytest.mark.parametrize("said", ["What is on this screen?", "What is it doing?", "What is this?"])
def test_with_no_cards_and_a_divided_orb_the_screen_is_not_called_empty(said, branch, session):
    """D-11, as the assertion the coordinator asked for.

    There genuinely were no CARDS. There was an orb, a dock, two half chips he could not press
    and a hold-to-speak label over all of it. An answer that says the screen is empty is
    FALSE, and a useful one names what IS there and what he can do next.
    """
    from app.capabilities import screen
    from app.fastpath.models import Ctx
    from app.reads.scheduler import ReadResult

    divided(session, branch)
    intent = resolve(said, branch=branch)
    assert intent.family == "screen_state", f"{said!r} -> {intent.family or '(the model)'}"
    recipe = RECIPES["screen_state"]
    ctx = Ctx(runtime=None, session=session, branch=branch, intent=intent, text=said)
    assert recipe.plan(ctx) is None, "nothing is read to answer this"
    answer = recipe.render(ctx, ReadResult())
    assert not answer.deferred, answer.defer

    said_back = answer.answer.lower()
    assert not screen.claims_an_empty_screen(answer.answer), answer.answer
    for phrase in ("no card's up", "nothing on the screen", "nothing pending on a card"):
        assert phrase not in said_back, f"{phrase!r} in {answer.answer!r}"
    # And what IS there, named.
    assert "orb" in said_back, answer.answer
    assert "dock" in said_back, answer.answer
    assert "half" in said_back and "divided" in said_back, answer.answer
    assert "merge" in said_back, "he was not told what he could do about it"


def test_the_answer_says_which_cards_are_up_when_there_are_some(branch, session):
    from app.fastpath.models import Ctx
    from app.reads.scheduler import ReadResult

    divided(session, branch)
    branch.shown([{"type": "customer", "data": {}}, {"type": "email_list", "data": {}}], "x", "y")
    said = "What is on this screen?"
    ctx = Ctx(runtime=None, session=session, branch=branch, intent=resolve(said, branch=branch), text=said)
    answer = RECIPES["screen_state"].render(ctx, ReadResult())
    assert "a customer" in answer.answer and "the inbox" in answer.answer, answer.answer
    # The furniture is still named, because it is still there.
    assert "dock" in answer.answer.lower()


def test_the_screen_answer_draws_a_card_the_tablet_can_already_render(branch, session):
    from app.fastpath.models import Ctx
    from app.reads.scheduler import ReadResult

    divided(session, branch)
    said = "What is on this screen?"
    ctx = Ctx(runtime=None, session=session, branch=branch, intent=resolve(said, branch=branch), text=said)
    answer = RECIPES["screen_state"].render(ctx, ReadResult())
    assert len(answer.surfaces) == 1
    card = answer.surfaces[0].as_ui()
    assert card["type"] == "capability"
    areas = [g["area"] for g in card["data"]["groups"]]
    assert areas == ["screen", "chrome"], areas
    assert card["data"]["groups"][1]["items"], "the chrome was not listed"


def test_a_bare_what_is_it_with_a_record_open_is_about_the_record(branch, session):
    """The bound on the bare form. "What is it doing" with an order on screen is about the
    order, and the model answers that — this family only takes it when there is no record for
    it to be about."""
    divided(session, branch)
    branch.visit("order", "gid://shopify/Order/1", "#1938")
    assert resolve("What is it doing?", branch=branch).family != "screen_state"


def test_the_screen_model_never_reports_an_empty_screen(branch, session):
    """The property, not the sentence: whatever the state, the furniture is non-empty, so
    there is always something true to say."""
    from app.capabilities import screen

    for build in (lambda: None, lambda: divided(session, branch),
                  lambda: branch.shown([{"type": "order", "data": {}}], "x", "y")):
        build()
        here = screen.state(session, branch)
        assert here.furniture, "the glass was reported as bare"
        assert not screen.claims_an_empty_screen(screen.words(here))


def test_the_screen_family_reads_nothing_and_can_write_nothing():
    recipe = RECIPES["screen_state"]
    assert recipe.read_primitives == ()
    assert_read_only({"screen_state": recipe})
