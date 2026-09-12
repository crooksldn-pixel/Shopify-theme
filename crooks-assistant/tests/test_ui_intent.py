"""§4: the words that oblige a workspace, and the turn that has not succeeded without one.

    "show me David's orders"

SPEECH ALONE IS NOT SUCCESS. That is the whole of this file. The live session proves the cost
in one defect said three times:

    turn_0cce1678e014  "Can you expand [name]'s customer page?"     → a capability card
    turn_ddb733d15472  "Expand [name]'s customer page"              → nothing at all
    turn_9d59579ab03e  "No, bring up a UI for the customer's page"   → nothing at all

Every assertion below is about a SURFACE. None of them is about a return code, a tool that
answered, or a sentence that was spoken — because all three of those were fine on the turn that
drew a thousand pixels of the wrong thing.
"""

from __future__ import annotations

import pytest

from app.capabilities import ask, ui_intent
from app.families import load_all
from app.fastpath import choose_lane, recipe_for
from app.fastpath.intent import CAPABILITY, all_families, kind_of, resolve
from app.fastpath.recipes import RECIPES, assert_read_only
from app.session.branch import Branch
from app.session.models import Session

load_all()
import app.fastpath.library  # noqa: E402, F401 — registers the core recipes


@pytest.fixture()
def branch():
    return Branch(branch_id="br_test", session_id="s1")


@pytest.fixture()
def session():
    return Session(session_id="s1")


def _customer_card(ref: str = "gid://shopify/Customer/7002") -> dict:
    return {"type": "customer", "surface": "customer", "data": {"customer_id": ref}}


def _capability_card() -> dict:
    """The card D-5's first turn actually drew: 1,014 px, tabs "The shop / The inbox /
    Sales and stock", and not one fact about the customer he named."""
    return {"type": "capability", "surface": "capability", "data": {"groups": []}}


# --------------------------------------------------------------- the contract, in words

# §4's list, verbatim from the brief.
DEMAND_WORDS = ["show", "show me", "open", "pull up", "bring up", "expand", "take me to",
                "go to", "view"]


@pytest.mark.parametrize("said", DEMAND_WORDS)
def test_every_word_the_brief_names_is_a_demand_for_a_surface(said):
    claim = ui_intent.demand(f"{said} David's customer page")
    assert claim is not None, f"{said!r} does not oblige a surface"
    assert claim.subject == ui_intent.CUSTOMER


def test_a_sentence_with_none_of_those_words_makes_no_claim_on_the_screen():
    """The contract is narrow on purpose. "How much did we take today" is a question, and a
    spoken figure is a complete answer to it."""
    for said in ("how much did we take today", "has order 1938 shipped", "who needs replying to",
                 "what can you do", "tag it delayed-sept"):
        assert ui_intent.demand(said) is None, said


def test_speech_alone_is_not_success():
    """The rule, stated at the level of the turn. A perfect sentence with an empty deck is
    UNSUCCESSFUL, and the analyser's class fires."""
    said = "show me David's orders"
    spoken = "David Randall: 2 orders, £104.00 in total. The last was 1965, £60.00."
    assert ui_intent.turn_outcome(said, [], spoken=spoken) == ui_intent.UNSUCCESSFUL
    assert ui_intent.unfulfilled(said, []) == ui_intent.UI_INTENT_UNFULFILLED
    assert "nothing was drawn" in ui_intent.why(said, [])


def test_the_capability_card_does_not_answer_a_request_for_a_customer_page():
    """D-5's first turn, exactly. A card WAS drawn and the report scored it drawn; it was a
    list of what the product can do, in answer to a request for one person's page."""
    said = "Can you expand David's customer page?"
    assert ui_intent.unfulfilled(said, [_capability_card()]) == ui_intent.UI_INTENT_UNFULFILLED
    assert ui_intent.turn_outcome(said, [_capability_card()]) == ui_intent.UNSUCCESSFUL
    assert "capability" in ui_intent.why(said, [_capability_card()])


def test_the_customer_workspace_does_answer_it():
    said = "Can you expand David's customer page?"
    assert ui_intent.unfulfilled(said, [_customer_card()]) == ""
    assert ui_intent.turn_outcome(said, [_customer_card()]) == ui_intent.SUCCESSFUL
    assert ui_intent.why(said, [_customer_card()]) == ""


def test_a_capability_card_answers_a_request_to_be_shown_the_capabilities():
    """The one case where it does. The demand's OBJECT is the assistant, and the contract
    reads the object rather than only the verb."""
    said = "show me what you can do"
    assert ui_intent.demand(said).subject == ui_intent.ASSISTANT
    assert ui_intent.unfulfilled(said, [_capability_card()]) == ""


@pytest.mark.parametrize(("said", "wrong"), [
    ("show me today's orders", "capability"),
    ("pull up the inbox", "capability"),
    ("take me to sales", "error"),
    ("open David Harding", "confirmation"),
])
def test_a_card_that_reports_on_the_turn_is_never_a_workspace(said, wrong):
    """`error`, `confirmation` and `capability` say something about the turn, not about the
    shop. A demand answered with one of them has not been answered."""
    assert ui_intent.unfulfilled(said, [{"type": wrong, "surface": wrong, "data": {}}]) == \
        ui_intent.UI_INTENT_UNFULFILLED


def test_the_class_the_analyser_has_to_know_about():
    """Named here, beside the rule that decides it, so the analyser files what this module
    found rather than a second opinion."""
    assert ui_intent.UI_INTENT_UNFULFILLED == "UI_INTENT_UNFULFILLED"
    assert ui_intent.SEVERITY >= 5, "asked to be shown something and was not: not a partial turn"
    assert "ui_intent" in ui_intent.COMPONENT and ui_intent.VISIBLE_WORD


# ------------------------------------------------------------------------ and the routing


D_5 = [
    "Can you expand David's customer page?",
    "Expand David's customer page",
    "show me David's orders",
    "pull up David's orders",
]


@pytest.mark.parametrize("said", D_5)
def test_the_three_attempts_route_deterministically_to_a_workspace(said, branch):
    """§36: navigation and an obvious entity page must not need a model call. Two of these
    sentences reached NO family at all, and one reached the capability summary."""
    intent = resolve(said, branch=branch)
    assert intent.family == "customer_workspace", f"{said!r} → {intent.family or '(the model)'}"
    recipe = recipe_for(intent.family)
    assert recipe is not None
    assert choose_lane(intent, recipe=recipe, text=said)[0] == "FAST"


def test_the_third_attempt_needs_a_person_this_conversation_has_seen(branch):
    """"No, bring up a UI for the customer's page" names a person without naming one. With
    nothing open and nobody seen there is nothing to resolve, and declining is honest; once a
    customer has been on this half, it is that customer."""
    said = "No, bring up a UI for the customer's page"
    assert resolve(said, branch=branch).family == ""
    branch.remember_entity("customer", "gid://shopify/Customer/7002", "David Randall")
    assert resolve(said, branch=branch).family == "customer_workspace"


@pytest.mark.parametrize("said", D_5 + [
    "Can you open David Harding?",
    "Can you open David's customer record?",
    "bring up his page",
    "take me to the inbox",
    "go to orders",
])
def test_a_demand_for_a_surface_never_routes_to_a_capability_family(said, branch):
    """§5's rule where §4 can see it: a sentence that obliges a workspace cannot be a question
    about the assistant, so no capability family may take it."""
    intent = resolve(said, branch=branch)
    assert kind_of(intent.family) != CAPABILITY, f"{said!r} → {intent.family!r}"


@pytest.mark.parametrize("said", DEMAND_WORDS)
def test_no_demand_word_can_be_served_by_a_recipe_that_draws_nothing(said, branch):
    """Whatever a demand routes to, the recipe behind it must be able to draw. A family whose
    recipe renders `assistant` — prose — cannot honour §4, and a future family that tries is
    caught here rather than on the tablet."""
    intent = resolve(f"{said} David's customer page", branch=branch)
    if not intent.family:
        return
    recipe = recipe_for(intent.family)
    assert recipe is not None and recipe.ui != "assistant", f"{said!r} → {recipe.recipe_id}"


def test_the_workspace_recipe_is_read_only():
    """A recipe names READ tools only; the read scheduler refuses a plan containing a write."""
    import app.tools.analytics_tools  # noqa: F401 — registers the read tools these name
    import app.tools.gmail_tools  # noqa: F401
    import app.tools.shopify_tools  # noqa: F401

    for recipe_id in ("customer_workspace", "ui_area_workspace"):
        assert recipe_id in RECIPES
        assert_read_only({recipe_id: RECIPES[recipe_id]})
    assert_read_only()


def test_the_workspace_recipe_would_rather_defer_than_speak(branch, session):
    """§4 enforced where the recipe can enforce it: with nothing to draw, it does not answer.

    The turn goes to Claude — which can search, and ask — rather than being logged as a fast
    answer the owner could not see.
    """
    from app.fastpath.models import Ctx
    from app.reads.scheduler import ReadResult

    recipe = RECIPES["customer_workspace"]
    said = "expand David's customer page"
    ctx = Ctx(runtime=None, session=session, branch=branch, intent=resolve(said, branch=branch), text=said)
    answer = recipe.render(ctx, ReadResult())
    assert answer.deferred, f"it answered with nothing to show: {answer.answer!r}"


def test_the_name_is_resolved_before_anything_held_is_read(branch, session):
    """D-14's rule inside §4's family: a named person is searched for, never inferred from the
    record in focus. The plan's FIRST read is the customer search."""
    from app.fastpath.models import Ctx

    branch.visit("order", "gid://shopify/Order/1", "#1900")
    said = "expand David Randall's customer page"
    ctx = Ctx(runtime=None, session=session, branch=branch, intent=resolve(said, branch=branch), text=said)
    plan = RECIPES["customer_workspace"].plan(ctx)
    assert plan is not None and plan.reads
    assert plan.reads[0].tool == "shopify_find_customer", [r.tool for r in plan.reads]
    assert "shopify_order_detail" not in [r.tool for r in plan.reads], (
        "the order in focus must not drive a page the words named somebody else for"
    )


def test_every_new_family_is_classified_against_the_continuation_glue():
    """The rule tests/test_touch_to_voice.py holds for the whole table, said again for mine:
    a family nobody classified is a sentence a tapped control can swallow."""
    from app.routes import turn

    classified = turn._NEVER_A_CONTINUATION | turn._CARRIES_ITS_OWN_SUBJECT
    mine = {"customer_workspace", "ui_area_workspace"}
    assert mine <= {f.name for f in all_families()}
    assert mine <= classified


# ------------------------------------------------------------------ end to end, on the shop


@pytest.fixture()
async def stage():
    from experience.harness import harness

    async with harness() as h:
        yield h


async def test_expand_a_customer_page_draws_the_customer_and_calls_no_model(stage):
    """The whole turn, through /turn, against the golden shop.

    Three assertions, and the first two are the ones the live session failed: a surface came
    back, it is the customer's, and no model was asked. The third is §4's contract read over
    the turn that actually happened.
    """
    capture = await stage.say("Expand David Randall's customer page")
    assert not capture.prose_only, f"nothing was drawn: {capture.answer!r}"
    assert "customer" in capture.surface_types, capture.surface_types
    assert "capability" not in capture.surface_types, "a capability card again"
    assert capture.model_calls == 0, "navigation must not need a model (§36)"
    assert ui_intent.turn_outcome(capture.command, capture.ui) == ui_intent.SUCCESSFUL
    assert "Randall" in capture.answer, capture.answer


async def test_show_me_his_orders_draws_the_workspace_on_the_orders_tab(stage):
    """§3's other half: the tab the TASK implies. A request naming orders opens Orders."""
    await stage.say("Expand David Randall's customer page")
    capture = await stage.say("show me his orders")
    assert not capture.prose_only, f"nothing was drawn: {capture.answer!r}"
    assert capture.recipe_id == "customer_workspace", capture.recipe_id
    assert ui_intent.turn_outcome(capture.command, capture.ui) == ui_intent.SUCCESSFUL


async def test_take_me_to_the_inbox_reaches_the_dock_landing(stage):
    capture = await stage.say("take me to the inbox")
    assert capture.recipe_id == "ui_area_workspace", capture.recipe_id
    assert not capture.prose_only, f"nothing was drawn: {capture.answer!r}"
    assert capture.model_calls == 0
    assert ui_intent.turn_outcome(capture.command, capture.ui) == ui_intent.SUCCESSFUL


async def test_the_contract_is_met_by_every_demand_turn_the_suite_makes(stage):
    """The sweep. Every §4 demand said against the golden shop, and the contract applied to
    what came back — so a demand that routes to the model still has to be answered with a
    surface, and one that routes to a recipe has to draw one."""
    for said in ("show me today's orders", "pull up the inbox", "open orders",
                 "expand David Randall's customer page", "take me to sales"):
        capture = await stage.say(said)
        assert ui_intent.turn_outcome(said, capture.ui) == ui_intent.SUCCESSFUL, (
            f"{said!r} drew {capture.surface_types} and said {capture.answer!r}"
        )


# ----------------------------------------------------------------- and the shared vocabulary


def test_the_router_and_the_contract_read_one_list():
    """Two rules that cannot be allowed to disagree: whether a sentence obliges a surface, and
    whether it is a capability question. Both read `ask.DEMANDS`."""
    assert ui_intent.demand("expand his page") is not None
    assert ask.demand_phrase(("expand", "his", "page")) == ("expand",)
    for phrase in ask.DEMANDS:
        assert ui_intent.demand(" ".join(phrase) + " David's page") is not None, phrase
