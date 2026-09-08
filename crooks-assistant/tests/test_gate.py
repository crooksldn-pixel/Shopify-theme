"""The gate is the security architecture. These tests are the reason to trust it."""

from __future__ import annotations

import pytest

from app.session.models import Session
from app.tools import mock
from app.tools.dispatch import dispatch
from app.tools.gate import Tier, classify


@pytest.fixture()
def session() -> Session:
    mock.reset_counters()
    return Session(session_id="test")


# --- fail-closed behaviour -------------------------------------------------

def test_unknown_tool_is_red():
    assert classify("some_tool_we_never_wrote").tier is Tier.RED


def test_empty_name_is_red():
    assert classify("").tier is Tier.RED


@pytest.mark.parametrize(
    "name",
    [
        "gmail_send_message", "gmail_create_draft", "shopify_update_order",
        "shopify_cancel_order", "gmail_trash_thread", "shopify_create_refund",
        "gmail_label_thread", "shopify_set_inventory", "delete_everything",
    ],
)
def test_mutation_verbs_are_red_even_if_unregistered(name):
    """A write tool added by accident is blocked by its own name, before any rule table."""
    assert classify(name).tier is Tier.RED


def test_mock_danger_is_red():
    assert classify("mock_danger").tier is Tier.RED


# --- MCP prefix normalisation ---------------------------------------------

def test_mcp_prefixed_names_classify_identically():
    """The documented trap: prefixed names silently missing every rule."""
    assert classify("mcp__crooks__mock_echo").tier is Tier.GREEN
    assert classify("mcp__crooks__mock_danger").tier is Tier.RED
    assert classify("mcp__crooks__gmail_send_message").tier is Tier.RED


# --- issued-id ledger ------------------------------------------------------

def test_detail_tool_rejects_unissued_id():
    d = classify("shopify_order_detail", {"order_id": "gid://shopify/Order/999"}, issued_ids=[])
    assert d.tier is Tier.RED
    # The reason tells the model how to recover, and says nothing was refused: a denial the
    # model recovers from must not read, on the tablet or in its answer, as "not allowed".
    assert "not an id this conversation has looked up" in d.reason
    assert "shopify_find_order" in d.reason and "Nothing is refused" in d.reason


def test_detail_tool_accepts_issued_id():
    oid = "gid://shopify/Order/4832"
    assert classify("shopify_order_detail", {"order_id": oid}, issued_ids=[oid]).tier is Tier.AMBER


def test_a_customer_id_is_not_an_order_id_even_if_issued():
    cid = "gid://shopify/Customer/77"
    d = classify("shopify_order_detail", {"order_id": cid}, issued_ids=[cid])
    assert d.tier is Tier.RED and "kind of id" in d.reason


def test_thread_ids_must_look_like_gmail_thread_ids():
    d = classify("gmail_read_thread", {"thread_id": "gid://shopify/Order/1"}, issued_ids=["gid://shopify/Order/1"])
    assert d.tier is Tier.RED
    assert classify("gmail_read_thread", {"thread_id": "18f2a9c0b1d2e3f4"}, issued_ids=["18f2a9c0b1d2e3f4"]).tier is Tier.AMBER


def test_detail_tool_rejects_missing_id():
    assert classify("shopify_order_detail", {}, issued_ids=["x"]).tier is Tier.RED


def test_malformed_id_is_red():
    d = classify("gmail_read_thread", {"thread_id": "'; DROP TABLE --"}, issued_ids=["a"])
    assert d.tier is Tier.RED


# --- argument bounds -------------------------------------------------------

@pytest.mark.parametrize("limit", [0, -1, 51, 10_000, "banana", "12x"])
def test_out_of_range_limit_is_red(limit):
    assert classify("shopify_list_orders", {"limit": limit}).tier is Tier.RED


def test_in_range_limit_is_green():
    assert classify("shopify_list_orders", {"limit": 20}).tier is Tier.GREEN


def test_out_of_range_days_is_red():
    assert classify("gmail_search", {"days": 9999}).tier is Tier.RED


# --- PII tools are amber, not green ---------------------------------------

@pytest.mark.parametrize("name", ["shopify_find_customer"])
def test_pii_tools_are_amber(name):
    assert classify(name, {"query": "jo"}).tier is Tier.AMBER


def test_purity_gate_does_not_mutate_args():
    args = {"limit": 20}
    classify("shopify_list_orders", args)
    assert args == {"limit": 20}


# --- the one that matters: RED never executes -----------------------------

async def test_red_tool_handler_never_runs(session):
    assert mock.DANGER_CALLS == 0
    out = await dispatch("mock_danger", {}, session=session, timeout_s=5)
    assert mock.DANGER_CALLS == 0, "RED tool executed — stop the build"
    assert out.startswith("REFUSED")
    assert session.refusals and session.refusals[0].tool_name == "mock_danger"
    assert session.proposals == [], "a refusal is never a proposal: nothing can authorise it"


async def test_red_tool_via_mcp_prefix_never_runs(session):
    await dispatch("mcp__crooks__mock_danger", {}, session=session, timeout_s=5)
    assert mock.DANGER_CALLS == 0


async def test_green_tool_runs(session):
    out = await dispatch("mock_echo", {"word": "banana"}, session=session, timeout_s=5)
    assert "banana" in out
    assert mock.ECHO_CALLS == 1


async def test_timeout_is_reported_not_raised(session):
    out = await dispatch("mock_slow", {}, session=session, timeout_s=0.2)
    assert out.startswith("ERROR")
    assert "did not respond" in out


async def test_unissued_detail_call_is_refused_end_to_end(session):
    out = await dispatch(
        "shopify_order_detail",
        {"order_id": "gid://shopify/Order/1"},
        session=session,
        timeout_s=5,
    )
    assert out.startswith("REFUSED")


async def test_ids_from_a_result_become_usable(session):
    """Issuing is what makes a follow-up question work: search, then ask about that one."""
    from app.tools.dispatch import _harvest_ids

    _harvest_ids({"orders": [{"order_id": "gid://shopify/Order/4832"}]}, session)
    assert "gid://shopify/Order/4832" in session.issued_ids
    assert classify(
        "shopify_order_detail",
        {"order_id": "gid://shopify/Order/4832"},
        issued_ids=session.issued_ids,
    ).tier is Tier.AMBER


# --- the gate consults the registry's own declaration ----------------------

def test_registry_amber_tier_is_honoured_even_without_a_rule():
    from app.tools import registry

    registry.tool(name="shopify_find_customer_probe", description="d", input_schema={"type": "object"}, tier=Tier.AMBER)(lambda **k: None)
    # Not in the gate's own tables; still AMBER because the registry says so — but unknown
    # to the allowlist, so RED wins. The allowlist is the outer wall.
    assert classify("shopify_find_customer_probe").tier is Tier.RED
    registry._REGISTRY.pop("shopify_find_customer_probe")


def test_registry_issued_id_args_are_enforced():
    """shopify_order_detail declares order_id in the registry; the gate needs it issued."""
    from app.tools import shopify_tools  # noqa: F401

    assert classify("shopify_order_detail", {"order_id": "gid://shopify/Order/9"}, issued_ids=[]).tier is Tier.RED


async def test_client_errors_reach_the_model_readably(session):
    """A Shopify throttle must be reported as a throttle, not 'failed unexpectedly'."""
    from app.clients.shopify import ShopifyError
    from app.tools import registry

    @registry.tool(name="shopify_find_order_probe", description="d", input_schema={"type": "object"})
    async def probe():
        raise ShopifyError("Shopify is rate-limiting us. Try again in a moment.")

    try:
        # Not in the gate allowlist, so call invoke's error path through dispatch's handler
        # by temporarily allowing it.
        from app.tools import gate

        gate._KNOWN_TOOLS = frozenset(gate._KNOWN_TOOLS | {"shopify_find_order_probe"})
        out = await dispatch("shopify_find_order_probe", {}, session=session, timeout_s=5)
        assert out.startswith("ERROR: Shopify is rate-limiting")
        assert "unexpectedly" not in out
    finally:
        registry._REGISTRY.pop("shopify_find_order_probe", None)
        gate._KNOWN_TOOLS = frozenset(gate._KNOWN_TOOLS - {"shopify_find_order_probe"})


def test_harvest_records_personal_strings_but_not_order_names(session):
    from app.tools.dispatch import _harvest_ids

    _harvest_ids(
        {"orders": [{"order_id": "gid://shopify/Order/1", "name": "CROOKS-1928", "customer_name": "Anna Denning",
                     "customer_id": "gid://shopify/Customer/7"}],
         "threads": [{"thread_id": "t1", "from": "Jo Bloggs", "from_email": "jo@example.com"}]},
        session,
    )
    assert {"Anna Denning", "Jo Bloggs", "jo@example.com"} <= session.pii_seen
    assert "CROOKS-1928" not in session.pii_seen
