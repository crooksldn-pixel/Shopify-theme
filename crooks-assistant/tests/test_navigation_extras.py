"""The three fast-lane sentences the brief names that the router could not hear (§17).

The brief's section 17 lists what "should generally avoid a full model critical path". Three
of its examples resolved to no family at all — "show me the shipping", "show me the latest
order", "switch to the other half" — because the router's signal vocabulary is fixed and none
of those words was in it.

What these tests hold: the three sentences now take the FAST lane; the sentences they could
have stolen still belong to the families that owned them (the regression this change caused
once and the blocks now prevent); and a family cannot shadow a core signal.
"""

from __future__ import annotations

import pytest

from app.families import load_all
from app.fastpath import choose_lane, recipe_for, resolve
from app.session.branch import Branch, Workflow
from app.session.models import Session

load_all()


@pytest.fixture()
def branch():
    """An order open, a set being walked, and a second half of the orb — the state the
    tablet is in when these sentences are said."""
    session = Session(session_id="s")
    first = session.branch()
    first.entity = {"kind": "order", "ref": "gid://shopify/Order/1", "label": "#1938"}
    first.set_id = "ws_1"
    first.workflow = Workflow(workflow_id="wf", set_id="ws_1", kind="orders", label="today",
                              operation="review", cursor=0, total=3)
    session.branches["b2"] = Branch(branch_id="b2", session_id="s", label="second")
    return first


def lane_for(text: str, branch) -> tuple[str, str]:
    intent = resolve(text, branch=branch)
    recipe = recipe_for(intent.family) if intent.family else None
    lane, _why = choose_lane(intent, recipe=recipe, text=text)
    return lane, intent.family


@pytest.mark.parametrize(
    "text,family",
    [
        # The three the brief names.
        ("show me the shipping", "order_tab_show"),
        ("show me the items", "order_tab_show"),
        ("show me the customer", "order_tab_show"),
        ("show me the latest order", "order_latest"),
        ("the most recent order", "order_latest"),
        ("the newest order", "order_latest"),
        ("switch to the other half", "branch_switch"),
        ("the other half", "branch_switch"),
        ("talk to the other side", "branch_switch"),
    ],
)
def test_the_sentences_the_brief_names_take_the_fast_lane(text, family, branch):
    assert lane_for(text, branch) == ("FAST", family)


@pytest.mark.parametrize(
    "text,family",
    [
        # Each of these was, or could have been, taken by one of the three above. The first
        # is the regression this change actually caused: "address" was a shipping-tab word,
        # so the sentence that READS THE ADDRESS OUT became ambiguous and went to the model.
        ("read me the full address", "order_address_lookup"),
        # There is no email tab word. `order_email_draft` reads the thread and draws it,
        # which answers this sentence rather than pointing at where the answer is.
        ("the correspondence about this order", "order_email_draft"),
        ("show me the full shipping address", "order_address_lookup"),
        # "The last one" is the cursor going back, not the newest order.
        ("the last one", "working_set_previous"),
        ("previous", "working_set_previous"),
        # And the families that were already fast stay fast.
        ("order 1938", "order_lookup"),
        ("show me today's orders", "order_list_period"),
        ("where is order 1938", "order_status_lookup"),
        ("what sold best this month", "best_sellers_period"),
        ("which orders are late", "delayed_orders"),
        ("open orders", "landing_orders"),
        ("open the inbox", "landing_inbox"),
        # "Products" was a shipping-tab word ("show me the products" meaning the order's
        # items), which sent one of the dock's own four areas to the order's Items tab. The
        # tab is reached by items, lines or contents; the landing owns the product words.
        ("open products", "landing_products"),
        ("show me products", "landing_products"),
        ("open inventory", "landing_products"),
        ("show me the items", "order_tab_show"),
        ("show me the contents", "order_tab_show"),
        ("what is running out", "stock_cover_analysis"),
        # With an order open, a bare "show me the email" is genuinely ambiguous between this
        # order's Email tab and the inbox — the router measured 0.96 against 0.90, inside the
        # margin, so nothing routed at all. The inbox owns the bare word; the tab is reached
        # by a sentence that says which order, and by the tap.
        ("show me the email", "landing_inbox"),
        ("what can you do?", "capability_summary"),
    ],
)
def test_nothing_else_was_taken(text, family, branch):
    assert lane_for(text, branch) == ("FAST", family)


def test_a_tab_sentence_about_a_different_order_is_declined(branch):
    """"Show me the shipping on 1912" names a record that is not the one on screen.

    The family still matches — a bare number is deliberately not extracted as an order number
    (a bare 2025 is a year), so the router cannot tell — and the RECIPE is what refuses: it
    declines the plan, the turn defers, and a lane that can look 1912 up answers. Without the
    guard it moved the tab and drew the wrong customer's address, confidently.
    """
    from app.families.navigation_extras import _tab_plan
    from app.fastpath.models import Ctx

    text = "show me the shipping on 1912"
    session = Session(session_id="s2")
    open_order = session.branch()
    open_order.entity = dict(branch.entity)
    ctx = Ctx(runtime=None, session=session, branch=open_order, intent=resolve(text, branch=open_order), text=text)
    assert _tab_plan(ctx) is None
    assert open_order.tab != "shipping", "the branch was moved for a question about another order"

    # The same sentence about the order that IS open moves the tab.
    text = "show me the shipping on 1938"
    ctx = Ctx(runtime=None, session=session, branch=open_order, intent=resolve(text, branch=open_order), text=text)
    assert _tab_plan(ctx) is not None
    assert open_order.tab == "shipping"


def test_a_tab_sentence_with_nothing_open_reaches_the_model():
    session = Session(session_id="empty")
    assert lane_for("show me the shipping", session.branch()) == ("NORMAL", "")


def test_a_family_cannot_shadow_a_core_signal():
    """The signal table is a seam, not a free-for-all: redefining `order` or `mutation` from a
    family module would change how every other family routes."""
    from app.fastpath.intent import signal

    for core in ("order", "mutation", "question", "has_entity"):
        with pytest.raises(ValueError, match="core signal"):
            signal(core, lambda s: True)


def test_a_signal_registered_twice_by_the_same_module_is_harmless():
    """A module imported twice must not raise; a DIFFERENT predicate under a taken name must."""
    from app.fastpath.intent import signal

    predicate = def_predicate = (lambda s: "zzz" in s.words)
    assert signal("test_only_signal", predicate) == "test_only_signal"
    assert signal("test_only_signal", def_predicate) == "test_only_signal"
    with pytest.raises(ValueError, match="already registered"):
        signal("test_only_signal", lambda s: False)


def test_switching_halves_when_there_is_only_one_defers(branch):
    """Nought or two other halves is nothing unambiguous to switch to. The recipe declines and
    the turn goes to the model, which can ask which one."""
    from app.families.navigation_extras import _switch_plan
    from app.fastpath.models import Ctx

    session = Session(session_id="alone")
    only = session.branch()
    ctx = Ctx(runtime=None, session=session, branch=only, intent=resolve("the other half", branch=only), text="the other half")
    assert _switch_plan(ctx) is None
    # Two others: also ambiguous.
    session.branches["b2"] = Branch(branch_id="b2", session_id="alone")
    session.branches["b3"] = Branch(branch_id="b3", session_id="alone")
    assert _switch_plan(ctx) is None
    # Exactly one: the move happens, and the session's focus follows it.
    del session.branches["b3"]
    assert _switch_plan(ctx) is not None
    assert session.focused_branch == "b2"


def test_the_switch_never_moves_a_closed_half(branch):
    from app.families.navigation_extras import _switch_plan
    from app.fastpath.models import Ctx

    session = Session(session_id="closed")
    first = session.branch()
    session.branches["gone"] = Branch(branch_id="gone", session_id="closed", status="MERGED")
    ctx = Ctx(runtime=None, session=session, branch=first, intent=resolve("the other half", branch=first), text="the other half")
    assert _switch_plan(ctx) is None
    assert session.focused_branch == first.branch_id
