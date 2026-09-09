"""The rail: which changes the Mac offers for an order, from the order's own state and from
what the store has granted. Never a dead button; never a chip for a change that is not
built or that would be refused."""

from __future__ import annotations

from app.actions.available import available_actions, order_facts

READY = {"state": "ready", "detail": "ready", "scope": "write_orders"}
ALL = {op: READY for op in ("order_note_append", "order_cancel", "order_shipping_address_set", "refund_create", "fulfillment_create", "gmail_send_reply")}

OPEN = {
    "order_number": "CROOKS-1938", "fulfillment": "UNFULFILLED", "payment": "PAID", "total": "60.00 GBP", "refundable": True,
    "money": {"refunded": "0.00 GBP", "total": "60.00 GBP"}, "customer_email": "d@example.com",
    "shipping_address": {"lines": ["12 Somewhere Street"], "city": "Windsor"}, "items": [{"unfulfilled_quantity": 1}], "fulfillments": [],
}


def ids(actions, *, enabled=None):
    return [a["id"] for a in actions if enabled is None or a["enabled"] is enabled]


def test_an_open_paid_order_offers_the_first_three_changes_and_no_more():
    actions = available_actions(OPEN, ALL)
    assert ids(actions, enabled=True) == ["note", "cancel", "address"]
    assert all(a["mode"] == "ask" for a in actions)
    assert next(a for a in actions if a["id"] == "cancel")["instruction"] == "Cancel order 1938"
    assert next(a for a in actions if a["id"] == "cancel")["risk"] == "red"


def test_a_shipped_order_cannot_be_cancelled_or_readdressed_and_says_why():
    shipped = dict(OPEN, fulfillment="FULFILLED", items=[{"unfulfilled_quantity": 0}], fulfillments=[{"status": "SUCCESS"}])
    actions = available_actions(shipped, ALL)
    assert ids(actions, enabled=True) == ["note", "refund", "email"]
    off = {a["id"]: a["reason"] for a in actions if not a["enabled"]}
    assert off == {"cancel": "already shipped", "fulfil": "already shipped"}


def test_a_cancelled_or_refunded_order_offers_almost_nothing():
    cancelled = dict(OPEN, cancelled_at="2026-09-08T10:00:00Z", payment="REFUNDED", refundable=False, money={"refunded": "60.00 GBP", "total": "60.00 GBP"})
    actions = available_actions(cancelled, ALL)
    assert ids(actions, enabled=True) == ["note", "email"]
    off = {a["id"]: a["reason"] for a in actions if not a["enabled"]}
    assert off == {"cancel": "already cancelled", "refund": "fully refunded"}


def test_an_unpaid_order_is_not_fulfilled_or_refunded():
    unpaid = dict(OPEN, payment="PENDING", refundable=False)
    actions = available_actions(unpaid, ALL)
    assert "fulfil" not in ids(actions, enabled=True) and "refund" not in ids(actions, enabled=True)
    assert {a["id"]: a["reason"] for a in actions if not a["enabled"]} == {"refund": "not paid", "fulfil": "not paid"}


def test_a_change_that_is_not_built_or_not_granted_is_not_a_chip():
    only_note = {"order_note_append": READY, "order_cancel": {"state": "blocked", "detail": "blocked — Shopify write_orders scope missing"}}
    actions = available_actions(OPEN, only_note)
    assert ids(actions) == ["note"]
    assert available_actions(OPEN, {}) == [] and available_actions(OPEN, None) == []
    unknown = {"order_cancel": {"state": "unknown", "detail": "ready, unverified"}}
    assert ids(available_actions(OPEN, unknown)) == ["cancel"], "a scope the Mac could not check is offered; Shopify decides the tap"
    off = {op: {"state": "disabled", "detail": "off"} for op in ALL}
    assert available_actions(OPEN, off) == []


def test_the_facts_are_read_defensively():
    facts = order_facts({})
    assert facts["cancelled"] is False and facts["shipped"] is False and facts["refundable"] is False and facts["digits"] == ""
    assert order_facts({"order_number": "#1036"})["digits"] == "1036"
    assert order_facts({"fulfillment": "UNFULFILLED"})["unfulfilled"] is True
