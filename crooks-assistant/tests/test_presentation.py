"""The `ui` contract: what the tablet is told to show, and the bounds on it.

Every card is built from a tool result, by key. These tests hold the two properties the tablet
relies on — nothing outside the vocabulary, nothing unbounded — and the two the office relies
on: a card never carries a field the whitelist does not name, and a refused tool shows as
"not allowed", never as a result.
"""

from __future__ import annotations

from app.presentation import (
    LOW_STOCK_AT,
    MAX_BODY_CHARS,
    MAX_MESSAGES,
    MAX_ORDERS,
    MAX_THREADS,
    UI_TYPES,
    present,
)
from app.providers.base import ToolCall
from app.session.models import Session
from app.tools import (
    shopify_tools,  # noqa: F401 — registers the write spec the action cards present
)

ORDER = {
    "order_id": "gid://shopify/Order/1", "order_number": "CROOKS-1930",
    "placed_at": "2026-09-08T10:00:00Z", "fulfillment": "UNFULFILLED", "payment": "PAID",
    "total": "60.00 GBP", "customer_name": "Daniel Sear", "customer_id": "gid://shopify/Customer/7",
}
DETAIL = {
    **ORDER,
    "items": [{"title": "Yard Jeans", "variant": "Blue Wash / M", "sku": "YJ-M", "quantity": 1, "total": "60.00 GBP"}],
    "items_truncated": False,
    "fulfillments": [{"status": "SUCCESS", "shipped_at": "2026-09-09", "carrier": "Royal Mail", "number": "RM1"}],
    "cancelled_at": None, "note": "Leave with neighbour", "ships_to": "London, United Kingdom",
    "shipping_address_full": "12 Somewhere Street, E1 6AN",  # must never reach the screen
}


def ok(name: str, result: dict) -> ToolCall:
    return ToolCall(name=name, args={}, ok=True, result=result)


def types(items: list[dict]) -> list[str]:
    return [i["type"] for i in items]


# --------------------------------------------------------------------------- vocabulary


def test_every_item_has_a_type_from_the_vocabulary_and_a_data_dict():
    items = present([ok("shopify_find_order", {"orders": [ORDER]}), ok("gmail_search", {"threads": [
        {"thread_id": "t1", "from": "Jo", "subject": "Hi", "date": "Mon", "snippet": "…"}]})])
    assert items
    for item in items:
        assert set(item) == {"type", "data"}
        assert item["type"] in UI_TYPES
        assert isinstance(item["data"], dict)


def test_unknown_tools_and_non_dict_results_produce_nothing():
    assert present([ok("mock_echo", {"echo": "hi"}), ToolCall(name="shopify_find_order", args={}, ok=True, result=None)]) == []
    assert present([]) == []
    assert present(None) == []


# --------------------------------------------------------------------------- orders


def test_one_order_is_an_order_card_with_the_hash_number_and_pounds():
    (card,) = present([ok("shopify_find_order", {"orders": [ORDER]})])
    assert card["type"] == "order"
    assert card["data"]["order_number"] == "#1930"
    assert card["data"]["total"] == "£60.00"
    assert card["data"]["fulfillment"] == "unfulfilled"
    assert card["data"]["customer_name"] == "Daniel Sear"
    assert card["data"]["detail"] is False


def test_detail_supersedes_the_summary_of_the_same_order_in_one_turn():
    items = present([ok("shopify_find_order", {"orders": [ORDER]}), ok("shopify_order_detail", DETAIL)])
    assert types(items) == ["order"]
    data = items[0]["data"]
    assert data["detail"] is True
    assert data["items"][0]["variant"] == "Blue Wash / M"
    assert data["fulfillments"][0]["carrier"] == "Royal Mail"
    assert data["ships_to"] == "London, United Kingdom"
    assert "shipping_address_full" not in data  # whitelist, not a copy


def test_several_orders_are_a_bounded_list():
    orders = [{**ORDER, "order_id": f"gid://shopify/Order/{i}", "order_number": f"CROOKS-{i}"} for i in range(40)]
    (card,) = present([ok("shopify_list_orders", {"days": 1, "days_ago": 0, "count": 40, "truncated": True, "orders": orders})])
    assert card["type"] == "order_list"
    assert card["data"]["title"] == "Today"
    assert len(card["data"]["orders"]) == MAX_ORDERS
    assert card["data"]["count"] == 40 and card["data"]["truncated"] is True


def test_an_ambiguous_customer_search_asks_which_customer():
    result = {
        "query": "dan", "orders": [], "ambiguous": True,
        "customers_matched": [{"customer_id": "c1", "name": "Dan A"}, {"customer_id": "c2", "name": "Dan B"}],
    }
    (card,) = present([ok("shopify_find_order", result)])
    assert card["type"] == "customer_list" and card["data"]["ambiguous"] is True
    assert [c["name"] for c in card["data"]["customers"]] == ["Dan A", "Dan B"]


# --------------------------------------------------------------------------- customers, stock, sales


def test_customer_card_and_list():
    one = {"customers": [{"customer_id": "c1", "name": "Jo", "email": "jo@example.com", "orders": 3, "spent": "180.00 GBP"}]}
    (card,) = present([ok("shopify_find_customer", one)])
    assert card["type"] == "customer" and card["data"]["spent"] == "£180.00" and card["data"]["orders"] == 3
    many = {"customers": one["customers"] * 2, "ambiguous": True}
    (card,) = present([ok("shopify_find_customer", many)])
    assert card["type"] == "customer_list" and card["data"]["title"] == "Which customer?"


def test_inventory_marks_exceptions_by_level():
    result = {"product": "Yard Jeans", "products": [{
        "product_id": "p1", "title": "Blue Wash Yard Jeans", "status": "ACTIVE", "total_inventory": 9,
        "variants": [
            {"variant_id": "v1", "variant": "S", "available": 0, "oversold_by": 0, "tracked": True},
            {"variant_id": "v2", "variant": "M", "available": 3, "oversold_by": 0, "tracked": True},
            {"variant_id": "v3", "variant": "L", "available": 0, "oversold_by": 2, "tracked": True},
            {"variant_id": "v4", "variant": "XL", "available": 40, "oversold_by": 0, "tracked": True},
            {"variant_id": "v5", "variant": "XXL", "available": None, "oversold_by": 0, "tracked": False},
        ],
    }]}
    (card,) = present([ok("shopify_inventory", result)])
    assert card["type"] == "inventory"
    levels = {v["variant"]: v["level"] for v in card["data"]["products"][0]["variants"]}
    assert levels == {"S": "out", "M": "low", "L": "oversold", "XL": "ok", "XXL": "untracked"}
    assert [e["variant"] for e in card["data"]["exceptions"]] == ["S", "M", "L"]
    assert card["data"]["low_stock_at"] == LOW_STOCK_AT
    assert "_exceptions" not in card["data"]["products"][0]


def test_sales_summary_derives_aov_from_real_figures_only():
    result = {"days": 1, "days_ago": 0, "orders": 12, "revenue": 430.5, "currency": "GBP", "complete": True,
              "basis": "orders created in the period"}
    (card,) = present([ok("shopify_sales_summary", result)])
    assert card["type"] == "sales_summary"
    assert card["data"]["revenue"] == "£430.50" and card["data"]["aov"] == "£35.88"
    assert card["data"]["title"] == "Today"
    (empty,) = present([ok("shopify_sales_summary", {**result, "orders": 0, "revenue": 0})])
    assert empty["data"]["aov"] is None
    (yesterday,) = present([ok("shopify_sales_summary", {**result, "days_ago": 1})])
    assert yesterday["data"]["title"] == "Yesterday"


# --------------------------------------------------------------------------- email


def test_email_list_and_thread_are_bounded():
    threads = [{"thread_id": f"t{i}", "from": "Jo", "from_email": "jo@example.com", "subject": "Re: order",
                "date": "Mon", "snippet": "x" * 900, "likely_bulk": False, "known_customer": True} for i in range(30)]
    (card,) = present([ok("gmail_search", {"query": "newer_than:1d", "count": 30, "threads": threads})])
    assert card["type"] == "email_list"
    assert len(card["data"]["threads"]) == MAX_THREADS
    assert len(card["data"]["threads"][0]["snippet"]) <= 300
    messages = [{"from": "Jo", "from_email": "jo@example.com", "date": "Mon", "subject": "Re: order",
                 "body": "b" * 10_000} for _ in range(20)]
    (card,) = present([ok("gmail_read_thread", {"thread_id": "t1", "message_count": 20, "messages_shown": 20, "messages": messages})])
    assert card["type"] == "email_thread"
    assert len(card["data"]["messages"]) == MAX_MESSAGES
    assert len(card["data"]["messages"][0]["body"]) <= MAX_BODY_CHARS
    assert card["data"]["truncated"] is True
    assert card["data"]["subject"] == "Re: order"


# --------------------------------------------------------------------------- errors


def test_a_failed_shopify_call_is_a_calm_error_with_no_raw_detail():
    failed = ToolCall(name="shopify_find_order", args={"query": "1930"}, ok=False,
                      error="ShopifyError: 502 Bad Gateway <html>…</html> token=shpat_secret")
    (card,) = present([failed])
    assert card["type"] == "error"
    assert card["data"]["service"] == "shopify" and card["data"]["title"] == "Shopify unavailable"
    assert "shpat" not in repr(card) and "html" not in repr(card)


def test_a_refused_tool_shows_as_refused_by_the_assistants_rules():
    refused = ToolCall(name="shopify_cancel_order", args={"order_id": "x"}, ok=False, error="registered as RED")
    (card,) = present([refused])
    assert card["data"]["kind"] == "blocked" and card["data"]["title"] == "Refused by the assistant's rules"
    assert "Nothing was changed" in card["data"]["recovery"]
    assert "not allowed" not in repr(card).lower(), "the owner's permissions had nothing to do with it"


def test_a_denial_the_model_recovers_from_is_not_a_card():
    """The gate refused a note whose order id had not been looked up; the model then found
    the order and proposed the note properly. The owner sees the proposal, not the stumble —
    the 'Not allowed' card beside a live proposal was the most likely shape of the perceived
    refusal."""
    from app.session.models import Session

    session = Session(session_id="s")
    session.issue("gid://shopify/Order/1938")
    # The first call named the order the way the owner said it, before anything had looked
    # it up: denied by the gate. The model then found it and proposed the note properly.
    stumble = ToolCall(name="shopify_order_note_append", args={"order_id": "1938", "note": "x"}, ok=False, error="not looked up")
    found = ToolCall(name="shopify_find_order", args={"order_number": "1938"}, ok=True, result={"orders": []})
    staged = ToolCall(name="shopify_order_note_append", args={"order_id": "gid://shopify/Order/1938", "note": "x"}, ok=True, result={}, proposal_id="prop_x")
    items = present([stumble, found, staged], session=session)
    assert all(i["type"] != "error" for i in items), items
    # Unrecovered, the refusal is shown — as the assistant's rule, not the owner's permission.
    (card,) = [i for i in present([stumble], session=session) if i["type"] == "error"]
    assert card["data"]["title"] == "Refused by the assistant's rules"
    # And a note refused for one order is not made good by a note prepared for another: that
    # refusal is still shown, beside the card for the order that did work.
    other = ToolCall(name="shopify_order_note_append", args={"order_id": "gid://shopify/Order/22", "note": "x"}, ok=True, result={}, proposal_id="prop_y")
    mixed = present([stumble, found, other], session=session)
    assert [i["type"] for i in mixed if i["type"] == "error"], mixed


def test_one_error_per_service_and_turn_errors_are_named():
    calls = [ToolCall(name="gmail_search", args={}, ok=False, error="a"), ToolCall(name="gmail_read_thread", args={}, ok=False, error="b")]
    items = present(calls, error_kind="timeout")
    assert types(items) == ["error", "error"]
    assert {i["data"]["service"] for i in items} == {"gmail", "assistant"}
    (speech,) = present([], error_kind="speech")
    assert speech["data"]["title"] == "Couldn't understand that"
    (unknown,) = present([], error_kind="something_new")
    assert unknown["data"]["title"] == "Something went wrong"


# --------------------------------------------------------------------------- context stack


def test_context_stack_appears_once_the_conversation_has_two_entities():
    session = Session(session_id="s")
    items = present([ok("shopify_find_order", {"orders": [ORDER]})], session=session)
    # One order carries its customer too: two entries, most specific first.
    assert types(items) == ["order", "context_stack"]
    stack = items[-1]["data"]["entries"]
    assert [(e["kind"], e["label"]) for e in stack] == [("customer", "Daniel Sear"), ("order", "#1930")]

    thread = {"thread_id": "t1", "messages": [{"from": "Jo", "subject": "Re: order 1930", "body": "hi", "date": "Mon"}]}
    items = present([ok("gmail_read_thread", thread)], session=session)
    stack = items[-1]["data"]["entries"]
    assert stack[0] == {"kind": "email", "label": "Re: order 1930", "ref": "t1"}
    assert len(stack) == 3

    # Touching the order again brings it to the front rather than duplicating it.
    present([ok("shopify_order_detail", DETAIL)], session=session)
    assert [e["kind"] for e in session.context] == ["customer", "order", "email"]
    assert len(session.context) == 3


def test_no_context_stack_for_a_single_entity_or_without_a_session():
    session = Session(session_id="s")
    thread = {"thread_id": "t1", "messages": [{"from": "Jo", "subject": "Hi", "body": "hi"}]}
    assert types(present([ok("gmail_read_thread", thread)], session=session)) == ["email_thread"]
    assert types(present([ok("shopify_find_order", {"orders": [ORDER]})])) == ["order"]


def test_sales_summary_carries_the_day_rows_bounded_and_formatted():
    result = {"days": 2, "days_ago": 0, "orders": 3, "revenue": 55.5, "currency": "GBP", "complete": True,
              "by_day": [{"date": "2026-09-07", "orders": 1, "revenue": 40},
                         {"date": "2026-09-08", "orders": 2, "revenue": 15.5}]}
    (card,) = present([ok("shopify_sales_summary", result)])
    assert card["data"]["by_day"] == [
        {"date": "2026-09-07", "orders": 1, "revenue": "£40.00"},
        {"date": "2026-09-08", "orders": 2, "revenue": "£15.50"},
    ]
    (many,) = present([ok("shopify_sales_summary", {
        **result, "by_day": [{"date": f"d{i}", "orders": 1, "revenue": 1} for i in range(60)]})])
    assert len(many["data"]["by_day"]) == 31
    (none,) = present([ok("shopify_sales_summary", {**result, "by_day": None})])
    assert none["data"]["by_day"] == []
    (junk,) = present([ok("shopify_sales_summary", {**result, "by_day": ["x", 3, {"date": "d", "revenue": "lots"}]})])
    assert junk["data"]["by_day"][-1] == {"date": "d", "orders": None, "revenue": None}


# --------------------------------------------------------------------------- actions


def _proposal(**overrides):
    from types import MappingProxyType

    from app.actions.models import ActionProposal, ActionStatus

    fields = dict(
        proposal_id="prop_abc", session_id="s", epoch=1, tool_name="shopify_order_note_append",
        operation="order_note_append", risk="AMBER", model_args=MappingProxyType({}),
        execution=MappingProxyType({"order_id": "gid://shopify/Order/1", "desired_note": "SECRET", "previous_note": ""}),
        entity_kind="order", entity_ref="gid://shopify/Order/1", entity_label="#1930", interaction="tap_commit",
        reversible=True, before={"sha": "a", "len": 0}, expected_after={"sha": "b", "len": 5},
        summary={"appended": "Hold for collection", "had_note": False}, fingerprint="f", created_at=0.0,
        expires_at=10_000_000_000.0, status=ActionStatus.PENDING,
    )
    fields.update(overrides)
    return ActionProposal(**fields)


def test_the_action_card_is_built_from_the_proposal_and_carries_no_execution_data():
    from app.presentation import present_proposal_state

    (card,) = present_proposal_state(_proposal())
    assert card["type"] == "confirmation"
    data = card["data"]
    assert data["proposal_id"] == "prop_abc" and data["operation"] == "order_note_append"
    assert data["entity"] == "Order #1930" and data["summary"] == "Hold for collection"
    assert data["interaction"]["kind"] == "tap_commit" and data["interaction"]["armed_after_ms"] == 650
    assert "SECRET" not in str(card) and "execution" not in data and "before" not in data


def test_an_unknown_interaction_kind_is_sent_as_unsupported_not_as_a_button():
    from app.presentation import present_proposal_state

    (card,) = present_proposal_state(_proposal(interaction="teleport"))
    assert card["data"]["interaction"]["kind"] == "unsupported"


def test_settled_proposals_present_calmly_and_success_only_when_verified():
    from app.actions.models import ActionStatus
    from app.presentation import present_proposal_state

    verified = present_proposal_state(_proposal(status=ActionStatus.VERIFIED, code="verified", entity={
        "order_id": "gid://shopify/Order/1", "order_number": "#1930", "note": "Hold for collection", "items": [], "fulfillments": [],
    }))
    assert [i["type"] for i in verified] == ["success", "order"]
    assert verified[0]["data"]["title"] == "Note added" and verified[1]["data"]["note"] == "Hold for collection"
    for status, code in ((ActionStatus.STALE, "stale"), (ActionStatus.EXPIRED, "expired"), (ActionStatus.UNVERIFIED, "unverified"), (ActionStatus.FAILED, "service_unavailable")):
        (card,) = present_proposal_state(_proposal(status=status, code=code))
        assert card["type"] == "error" and card["data"]["kind"] == code
        assert "graphql" not in str(card).lower() and "token" not in str(card).lower()


def test_a_summary_is_bounded():
    from app.presentation import MAX_NOTE_CHARS, present_proposal_state

    (card,) = present_proposal_state(_proposal(summary={"appended": "x" * 5000, "had_note": True}))
    assert len(card["data"]["summary"]) <= MAX_NOTE_CHARS


# --------------------------------------------------------------------------- the rail


def test_the_order_card_carries_the_rail_only_from_the_macs_capabilities():
    caps = {"order_note_append": {"state": "ready"}, "order_cancel": {"state": "ready"}}
    open_order = {**DETAIL, "fulfillment": "UNFULFILLED", "fulfillments": [], "items": [{"title": "Yard Jeans", "unfulfilled_quantity": 1}], "refundable": True}
    with_rail = present([ok("shopify_order_detail", open_order)], writes={"allowed": True, "capabilities": caps})
    actions = with_rail[0]["data"]["actions"]
    assert [a["id"] for a in actions] == ["note", "cancel"] and actions[1]["instruction"] == "Cancel order 1930"
    assert set(actions[0]) == {"id", "label", "operation", "risk", "enabled", "reason", "instruction", "mode"}
    without = present([ok("shopify_order_detail", open_order)])
    assert without[0]["data"]["actions"] == []
    summary = present([ok("shopify_find_order", {"orders": [ORDER]})], writes={"allowed": True, "capabilities": caps})
    assert "actions" not in summary[0]["data"], "a summary card has no rail; the order is not known well enough"
