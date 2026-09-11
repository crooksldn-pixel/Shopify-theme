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
