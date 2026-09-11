"""The rail: which changes the Mac offers for an order, from the order's own state and from
what the store has granted. Never a dead button; never a chip for a change that is not
built or that would be refused."""

from __future__ import annotations

from app.actions.available import available_actions, order_facts

READY = {"state": "ready", "detail": "ready", "scope": "write_orders"}
ALL = {op: READY for op in ("order_note_append", "order_cancel", "order_shipping_address_set", "refund_create", "fulfillment_create", "gmail_draft_new")}

OPEN = {
    "order_number": "CROOKS-1938", "fulfillment": "UNFULFILLED", "payment": "PAID", "total": "60.00 GBP", "refundable": True,
    "money": {"refunded": "0.00 GBP", "total": "60.00 GBP"}, "customer_email": "d@example.com",
    "shipping_address": {"lines": ["12 Somewhere Street"], "city": "Windsor"}, "items": [{"unfulfilled_quantity": 1}], "fulfillments": [],
}


def ids(actions, *, enabled=None):
    return [a["id"] for a in actions if enabled is None or a["enabled"] is enabled]


def test_an_open_paid_order_offers_what_it_needs_first_and_the_note_besides():
    """A paid order waiting to ship needs shipping: fulfil leads, then the address, then the
    cancel. The note is always there, never takes one of the three places, and — since the
    live session counted five renders of it and nought taps — goes last and at half weight."""
    actions = available_actions(OPEN, ALL)
    assert ids(actions, enabled=True) == ["fulfil", "address", "cancel", "note"]
    assert [a["priority"] for a in actions if a["enabled"]] == ["primary", "primary", "secondary", "secondary"]
    assert all(a["mode"] == "ask" for a in actions if a["id"] != "email")
    assert next(a for a in actions if a["id"] == "cancel")["instruction"] == "Cancel order 1938"
    assert next(a for a in actions if a["id"] == "cancel")["risk"] == "red"
    assert next(a for a in actions if a["id"] == "fulfil")["instruction"] == "Fulfil order 1938"
    assert "email" not in ids(actions), "three places, taken by what the order needs"
    off = {a["id"]: a["reason"] for a in actions if not a["enabled"]}
    assert off == {}


def test_the_email_chip_primes_a_draft_and_is_amber_for_that_reason():
    shipped = dict(OPEN, fulfillment="FULFILLED", items=[{"unfulfilled_quantity": 0}], fulfillments=[{"status": "SUCCESS"}])
    email = next(a for a in available_actions(shipped, ALL) if a["id"] == "email")
    assert email["operation"] == "gmail_draft_new" and email["risk"] == "amber" and email["instruction"] == "Email the customer about order 1938"


def test_a_shipped_order_cannot_be_cancelled_or_readdressed_and_says_why():
    shipped = dict(OPEN, fulfillment="FULFILLED", items=[{"unfulfilled_quantity": 0}], fulfillments=[{"status": "SUCCESS"}])
    actions = available_actions(shipped, ALL)
    assert ids(actions, enabled=True) == ["refund", "email", "note"]
    off = {a["id"]: a["reason"] for a in actions if not a["enabled"]}
    assert off == {"cancel": "already shipped", "fulfil": "already shipped"}


def test_a_cancelled_or_refunded_order_offers_almost_nothing():
    cancelled = dict(OPEN, cancelled_at="2026-09-08T10:00:00Z", payment="REFUNDED", refundable=False, money={"refunded": "60.00 GBP", "total": "60.00 GBP"})
    actions = available_actions(cancelled, ALL)
    assert ids(actions, enabled=True) == ["email", "note"]
    off = {a["id"]: a["reason"] for a in actions if not a["enabled"]}
    assert off == {"cancel": "already cancelled", "refund": "fully refunded"}
    part = dict(OPEN, fulfillment="FULFILLED", items=[{"unfulfilled_quantity": 0}], fulfillments=[{"status": "SUCCESS"}], payment="PARTIALLY_REFUNDED", refundable=False, money={"refunded": "20.00 GBP", "total": "60.00 GBP"})
    assert {a["id"]: a["reason"] for a in available_actions(part, ALL) if not a["enabled"]}["refund"] == "nothing to refund", "paid, partly refunded, nothing more refundable: not 'not paid'"


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


def test_the_context_ranks_the_rail_a_customers_email_first_and_an_old_order_to_ship():
    """The rules still decide what is enabled; the order's own context decides what leads."""
    from app.actions.available import context_rank

    wrote = dict(OPEN, email={"threads": [{"sender_match": True, "subject": "Order 1938", "snippet": "any news on when it ships?"}]})
    assert context_rank(wrote) == ["email"]
    assert ids(available_actions(wrote, ALL), enabled=True) == ["email", "fulfil", "address", "note"], "the reply leads; the cancel drops off the three"
    cancelling = dict(OPEN, email={"threads": [{"sender_match": True, "subject": "Please cancel 1938", "snippet": "I ordered the wrong size"}]})
    assert context_rank(cancelling) == ["cancel", "email"]
    assert ids(available_actions(cancelling, ALL), enabled=True) == ["cancel", "email", "fulfil", "note"]
    moving = dict(OPEN, email={"threads": [{"sender_match": True, "subject": "New address", "snippet": "can you send it to my work address instead"}]})
    assert context_rank(moving) == ["address", "email"]
    shipped = dict(OPEN, fulfillment="FULFILLED", items=[{"unfulfilled_quantity": 0}], fulfillments=[{"status": "SUCCESS"}], email={"threads": [{"sender_match": True, "subject": "Refund", "snippet": "I'd like a refund please"}]})
    assert context_rank(shipped) == ["refund", "email"]
    assert ids(available_actions(shipped, ALL), enabled=True)[:2] == ["refund", "email"]
    someone_else = dict(OPEN, email={"threads": [{"sender_match": False, "subject": "Newsletter", "snippet": "sale now on"}]})
    assert context_rank(someone_else) == [], "mail from anyone but the customer ranks nothing"
    old = dict(OPEN, placed_at="2020-01-01T10:00:00Z")
    assert context_rank(old) == ["fulfil"]
    assert context_rank(dict(old, fulfillment="FULFILLED", items=[{"unfulfilled_quantity": 0}], fulfillments=[{"status": "SUCCESS"}])) == []
