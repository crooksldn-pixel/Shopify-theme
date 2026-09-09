"""The fast lane: what it takes, what it refuses to take, and what it does when it takes it.

The rule this file exists to hold: being quick is never a reason to answer a different
question. Every case below that ends in NORMAL is a case where the Mac could have guessed
and chose not to.
"""

from __future__ import annotations

import pytest

from app.analytics import sets as working_sets
from app.fastpath import choose_lane, recipe_for, resolve
from app.fastpath.intent import mutating
from app.fastpath.library import dimension_from, period_from
from app.fastpath.models import Ctx
from app.fastpath.recipes import RECIPES, assert_read_only
from app.fastpath.runner import _unresolved, run
from app.session.branch import Branch, Workflow
from app.session.models import Session


@pytest.fixture()
def branch():
    return Branch(branch_id="br_test", session_id="s1")


def lane_for(text: str, branch) -> tuple[str, str]:
    intent = resolve(text, branch=branch)
    recipe = recipe_for(intent.family) if intent.family else None
    return choose_lane(intent, recipe=recipe, text=text)[0], intent.family


# --------------------------------------------------------------- what it takes

FAST_CASES = [
    ("next", "working_set_next"),
    ("go back", "navigation_back"),
    ("what can you do?", "capability_summary"),
    ("what more can you do now?", "capability_delta"),
    ("order 1938", "order_lookup"),
    ("where is order 1938", "order_status_lookup"),
    ("has order 1938 shipped?", "order_status_lookup"),
    ("read me the full address for order 1938", "order_address_lookup"),
    ("what sold best this month", "best_sellers_period"),
    ("how were sales last week", "sales_breakdown_period"),
    ("which orders are late", "delayed_orders"),
    ("what is running out", "stock_cover_analysis"),
    ("who needs replying to", "needs_reply"),
]


@pytest.mark.parametrize(("text", "family"), FAST_CASES)
def test_the_ordinary_questions_take_the_fast_lane(text, family, branch):
    lane, got = lane_for(text, branch)
    assert (lane, got) == ("FAST", family), text


# ------------------------------------------------------------ what it refuses

NEVER_FAST = [
    ("cancel order 1938", "a change"),
    ("refund order 1938", "a change"),
    ("add a note to 1938 saying he called", "a change"),
    ("archive those emails", "a change"),
    ("email everyone who has not replied", "a change"),
    ("how much stock of the yard jeans", "one product, not a restock ranking"),
    ("who are our top customers", "a customer ranking makes a set"),
    ("show me order 1938 and tell me if the customer has written in", "two questions"),
]


@pytest.mark.parametrize(("text", "why"), NEVER_FAST)
def test_what_the_fast_lane_declines(text, why, branch):
    lane, _ = lane_for(text, branch)
    assert lane in ("NORMAL", "DEEP"), f"{text!r} should not be fast: {why}"


# Routing is structure; whether the data supports a deterministic answer is the recipe's own
# check. These read as best-seller questions and are routed as such — and then the recipe
# declines to build a plan, so the turn goes to Claude with nothing invented.
DECLINED_AT_PLAN = [
    ("what sold best by material last month", "best_sellers_period"),
    ("how does this week compare against last week", "sales_breakdown_period"),
]


@pytest.mark.parametrize(("text", "recipe_id"), DECLINED_AT_PLAN)
def test_a_recipe_declines_to_plan_what_it_cannot_read_exactly(text, recipe_id, branch):
    session = Session(session_id="s1")
    intent = resolve(text, branch=branch)
    recipe = recipe_for(intent.family)
    assert recipe is not None and recipe.recipe_id == recipe_id
    ctx = Ctx(runtime=None, session=session, branch=branch, intent=intent, text=text)
    assert recipe.plan(ctx) is None, f"{text!r} must not be planned deterministically"


def test_a_mutation_verb_leaves_the_lane_whatever_else_it_says(branch):
    for text in ("cancel it", "refund the lot", "archive them", "fulfil 1938", "tag these as vip"):
        assert resolve(text, branch=branch).family == ""
        assert resolve(text, branch=branch).reason == "asks for a change"


def test_a_gerund_after_a_question_word_is_not_an_instruction():
    assert not mutating(("who", "needs", "replying", "to"))
    assert not mutating(("which", "customers", "are", "waiting", "on", "an", "email"))
    assert mutating(("reply", "to", "millie"))
    assert mutating(("email", "them", "all"))
    assert mutating(("cancel", "it")) and mutating(("what", "should", "i", "cancel"))


def test_two_clauses_are_never_one_fast_answer(branch):
    one = resolve("order 1938", branch=branch)
    two = resolve("order 1938 and what did she buy before", branch=branch)
    assert one.family == "order_lookup" and two.family == ""


# --------------------------------------------------------------- the pieces

def test_the_period_map_declines_what_it_cannot_read():
    assert period_from(("sales", "this", "month")) == "this_month"
    assert period_from(("best", "sellers", "last", "week")) == "last_week"
    assert period_from(("last", "7", "days")) == "last_7_days"
    assert period_from(("how", "are", "we", "doing")) is None
    assert period_from(("this", "week", "against", "last", "week")) is None


def test_the_dimension_map_declines_two_and_declines_the_unknown():
    assert dimension_from(("by", "colour")) == "colour"
    assert dimension_from(("sales", "per", "day")) == "day"
    assert dimension_from(("by", "material")) is None
    assert dimension_from(("by", "colour", "and", "by", "size")) is None


def test_every_recipe_is_read_only_and_declared():
    assert_read_only()
    for recipe in RECIPES.values():
        assert recipe.plan is not None and recipe.render is not None, recipe.recipe_id
        assert recipe.min_confidence >= 0.7, recipe.recipe_id
        for group in recipe.parallel_nodes:
            assert group, recipe.recipe_id


def test_a_recipe_that_names_a_write_tool_is_a_crash_not_a_surprise():
    from dataclasses import replace

    import app.tools.shopify_writes  # noqa: F401 — registers the write tool this names

    victim = replace(RECIPES["order_lookup"], read_primitives=("shopify_order_note_append",))
    with pytest.raises(RuntimeError, match="cannot write"):
        assert_read_only({"victim": victim})


# ------------------------------------------------------------- the cursor

def test_next_is_a_cursor_move_and_one_read(branch):
    session = Session(session_id="s1")
    ws = working_sets.create(session, kind="orders", members=["o1", "o2", "o3"], label="late orders")
    branch.workflow = Workflow(workflow_id="wf1", set_id=ws.set_id, kind="orders", total=3, cursor=0)
    recipe = RECIPES["working_set_next"]
    ctx = Ctx(runtime=None, session=session, branch=branch, intent=resolve("next", branch=branch), text="next")
    assert _unresolved(recipe, ctx) == ""
    from app.fastpath.runner import _advance

    _advance(recipe, ctx)
    assert branch.workflow.cursor == 1 and branch.workflow.position == 2
    _advance(recipe, ctx)
    _advance(recipe, ctx)
    assert branch.workflow.cursor == 2, "the cursor stops at the end rather than running past it"
    _advance(RECIPES["working_set_previous"], ctx)
    assert branch.workflow.cursor == 1


def test_next_with_a_listing_but_no_workflow_adopts_the_newest_set(branch):
    session = Session(session_id="s1")
    working_sets.create(session, kind="orders", members=["o1", "o2"], label="late")
    ctx = Ctx(runtime=None, session=session, branch=branch, intent=resolve("next", branch=branch), text="next")
    assert _unresolved(RECIPES["working_set_next"], ctx) == ""
    assert branch.workflow is not None and branch.workflow.cursor == -1
    from app.fastpath.runner import _advance

    _advance(RECIPES["working_set_next"], ctx)
    assert branch.workflow.cursor == 0, "the first Next lands on the first member"


def test_next_with_nothing_open_defers_rather_than_guessing(branch):
    session = Session(session_id="s1")
    ctx = Ctx(runtime=None, session=session, branch=branch, intent=resolve("next", branch=branch), text="next")
    assert _unresolved(RECIPES["working_set_next"], ctx) == "the set being worked through"


async def test_a_recipe_that_cannot_answer_defers_and_never_invents(branch):
    session = Session(session_id="s1")
    session.turn_id = "turn_x"
    recipe = RECIPES["capability_delta"]

    class Runtime:
        capability_record = None

    answer = await run(recipe, Ctx(runtime=Runtime(), session=session, branch=branch, intent=resolve("what more can you do now", branch=branch), text="x"))
    assert answer.deferred and answer.answer == ""
    assert recipe.stats.deferred >= 1


# --------------------------------------------------------------- navigation

def test_the_branch_back_stack_restores_the_tab_and_the_scroll(branch):
    branch.visit("order", "o1", "#1938", tab="overview")
    branch.mark(tab="shipping", scroll=420)
    branch.visit("customer", "c1", "Millie Rogers", tab="orders")
    assert branch.entity["ref"] == "c1"
    back = branch.back()
    assert back.ref == "o1" and branch.tab == "shipping" and branch.scroll == 420
    forward = branch.forward()
    assert forward.ref == "c1" and branch.tab == "orders"
    branch.visit("order", "o2", "#1939")
    assert branch.forward() is None, "going somewhere new truncates the forward history"


def test_a_branch_remembers_a_name_it_resolved_and_forgets_it_when_it_is_old(branch):
    branch.learn("millie rogers", "customer", "c1", "Millie Rogers", clock=lambda: 1000.0)
    assert branch.resolve("Millie Rogers", clock=lambda: 1100.0)["ref"] == "c1"
    assert branch.resolve("millie rogers", clock=lambda: 9000.0) is None
