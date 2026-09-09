"""The changes that move money or end an order: cancel (here), and the refund, the address
and the fulfilment that follow. Each one PREPARES from a fresh read — the exact arguments the
mutation will be sent with, the facts the card prints, the fingerprint the engine checks —
and sends nothing. The engine sends the one reviewed mutation later, by name, after the
owner's gesture, waits for Shopify to finish where Shopify finishes later, and proves the
change by reading again. Policy (refund on cancel, restock, notify) is configuration, printed
on the card; it is never an argument the model supplies.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import re
import time
from email.utils import parsedate_to_datetime
from typing import Any

from app.actions.models import Observed, Prepared
from app.clients.shopify import ShopifyClient, ShopifyError
from app.tools.gate import Tier
from app.tools.registry import ToolError, WriteSpec, tool
from app.tools.shopify_tools import _c, append_note, hydrator

log = logging.getLogger("crooks.shopify_writes")

_policy = None


def bind_policy(getter) -> None:
    """Where the write policy comes from: the runtime's settings. Tests bind their own."""
    global _policy
    _policy = getter


def policy():
    if _policy is not None:
        return _policy()
    from config.settings import get_settings

    return get_settings()


def _amount(node: Any) -> float | None:
    try:
        shop = (node or {}).get("shopMoney") or node
        return round(float(shop["amount"]), 2)
    except (TypeError, KeyError, ValueError, AttributeError):
        return None


def _currency(node: Any) -> str:
    try:
        return str(((node or {}).get("shopMoney") or node).get("currencyCode") or "GBP")
    except AttributeError:
        return "GBP"


def _display(amount: float | None, currency: str) -> str:
    if amount is None:
        return "—"
    symbol = {"GBP": "£", "USD": "$", "EUR": "€"}.get(currency.upper())
    return f"{symbol}{amount:,.2f}" if symbol else f"{amount:,.2f} {currency}"


def _spoken_money(amount: float | None, currency: str) -> str:
    """The amount as the voice says it: the speakable layer already turns "£60.00" into
    "sixty pounds"; the model is handed the words so it reads them back the same way."""
    if amount is None:
        return "an unknown amount"
    from app.speech.speakable import to_speakable

    return to_speakable(_display(amount, currency))


# ------------------------------------------------------------------------- cancel

CANCEL_REASONS = {
    "customer": "CUSTOMER", "inventory": "INVENTORY", "fraud": "FRAUD", "declined": "DECLINED", "staff": "STAFF", "other": "OTHER",
}
REASON_WORDS = {
    "CUSTOMER": "customer request", "INVENTORY": "out of stock", "FRAUD": "suspected fraud", "DECLINED": "payment declined",
    "STAFF": "staff error", "OTHER": "other",
}
MAX_STAFF_NOTE_CHARS = 200
# The job Shopify runs to cancel is waited for this long, looking a little less often each time.
JOB_WAIT_S = 12.0
JOB_POLL_FIRST_S = 0.3
JOB_POLL_GROWTH = 1.5
JOB_POLL_MAX_S = 2.0

CANCEL_STATE_QUERY = """
query CrooksOrderCancelState($id: ID!) {
  order(id: $id) {
    id
    name
    cancelledAt
    cancelReason
    displayFinancialStatus
    displayFulfillmentStatus
    fullyPaid
    currentTotalPriceSet { shopMoney { amount currencyCode } }
    totalRefundedSet { shopMoney { amount currencyCode } }
    totalOutstandingSet { shopMoney { amount currencyCode } }
    customer { displayName }
    fullRefund: suggestedRefund(suggestFullRefund: true) {
      amountSet { shopMoney { amount currencyCode } }
      maximumRefundableSet { shopMoney { amount currencyCode } }
    }
    lineItems(first: 50) { edges { node { id quantity unfulfilledQuantity refundableQuantity } } }
  }
}
"""


async def _read_cancel_state(client: ShopifyClient, order_id: str) -> dict[str, Any]:
    payload = await client.graphql(CANCEL_STATE_QUERY, {"id": order_id})
    node = (payload.get("data") or {}).get("order")
    if not isinstance(node, dict) or node.get("id") != order_id:
        raise ToolError(f"No order with id {order_id}.")
    return node


def cancel_fingerprint(node: dict[str, Any]) -> dict[str, Any]:
    """What a cancellation turns on and what it must change: cancelled, the statuses, and the
    money refunded so far. Numbers and words; nothing personal."""
    refunded = _amount(node.get("totalRefundedSet"))
    return {
        "cancelled": bool(node.get("cancelledAt")),
        "fulfillment": str(node.get("displayFulfillmentStatus") or ""),
        "financial": str(node.get("displayFinancialStatus") or ""),
        "refunded": f"{refunded:.2f}" if refunded is not None else "",
    }


async def _observe_cancel(execution: dict) -> Observed:
    node = await _read_cancel_state(_c(), str(execution["order_id"]))
    return Observed(fingerprint=cancel_fingerprint(node), entity=None)


async def _entity_after(execution: dict) -> dict:
    return await hydrator().order(str(execution["order_id"]), budget_s=0.0, fresh=True)


async def _execute_cancel(execution: dict) -> dict:
    client = _c()
    order_id = str(execution["order_id"])
    payload = await client.mutate("order_cancel", {
        "orderId": order_id,
        "reason": str(execution["reason"]),
        "refundMethod": {"originalPaymentMethodsRefund": bool(execution["refund"])},
        "restock": bool(execution["restock"]),
        "notifyCustomer": bool(execution["notify"]),
        "staffNote": str(execution.get("staff_note") or ""),
    })
    hydrator().forget(order_id)
    job = ((payload.get("data") or {}).get("orderCancel") or {}).get("job")
    if not isinstance(job, dict) or not job.get("id"):
        # No job and no user error: Shopify did not take it. The engine looks, not guesses.
        raise ShopifyError("Shopify did not start the cancellation.")
    return {"job_id": str(job["id"]), "done": bool(job.get("done"))}


async def _settle_cancel(execution: dict, sent: dict) -> None:
    """Wait for the job Shopify started, bounded, looking a little less often each time. A job
    Shopify has forgotten, or one that is still running at the bound, is left to the proving
    read: the engine says what it sees, never what it hopes."""
    job_id = str((sent or {}).get("job_id") or "")
    if not job_id or (sent or {}).get("done"):
        return
    client = _c()
    deadline = time.monotonic() + JOB_WAIT_S
    wait = JOB_POLL_FIRST_S
    while time.monotonic() < deadline:
        await asyncio.sleep(min(wait, max(0.0, deadline - time.monotonic())))
        try:
            done = await client.job_done(job_id)
        except ShopifyError as exc:
            log.warning("job %s could not be checked: %s", job_id, exc)
            return
        if done is None or done:
            return
        wait = min(wait * JOB_POLL_GROWTH, JOB_POLL_MAX_S)
    log.warning("job %s still running after %.0fs; the re-read decides", job_id, JOB_WAIT_S)


def _verify_cancel(before: dict, observed: dict, execution: dict) -> tuple[bool, str]:
    if not observed.get("cancelled"):
        return False, ""
    expected = float(execution.get("expected_refund") or 0)
    if execution.get("refund") and expected > 0:
        try:
            landed = float(observed.get("refunded") or 0) - float(before.get("refunded") or 0)
        except ValueError:
            landed = 0.0
        if landed + 0.005 < expected:
            return True, "The refund isn't showing yet; check the order."
    return True, ""


def _present_cancel(proposal) -> dict:
    s = proposal.summary
    currency = str(s.get("currency") or "GBP")
    amount = s.get("refund_amount")
    refund_words = (
        _display(float(amount), currency) + " to the original payment" if s.get("refund") and amount
        else ("nothing captured to refund" if s.get("refund") else "not refunded (policy)")
    )
    facts = [
        {"label": "Customer", "value": str(s.get("customer") or "—")},
        {"label": "Items", "value": f"{s.get('items', 0)} · {_display(float(s['total']), currency) if s.get('total') else '—'}, {str(s.get('financial') or '').lower().replace('_', ' ') or 'unknown'}"},
        {"label": "Refund", "value": refund_words, "tone": "bad" if s.get("refund") and amount else ""},
        {"label": "Restock", "value": f"{s.get('restock_count', 0)} item{'s' if s.get('restock_count', 0) != 1 else ''}" if s.get("restock") else "no"},
        {"label": "Customer emailed", "value": "yes" if s.get("notify") else "no"},
        {"label": "Reason", "value": REASON_WORDS.get(str(s.get("reason")), "other")},
    ]
    target = f"Drop to cancel and refund {_display(float(amount), currency)}" if s.get("refund") and amount else "Drop to cancel"
    return {
        "title": "Cancel order", "summary": "", "detail": "Cancelling cannot be undone.",
        "facts": facts, "target": target, "done_title": "Cancelled",
    }


@tool(
    name="shopify_order_cancel",
    description=(
        "Prepare the cancellation of one order that has not shipped. Stages it for the owner to "
        "apply on the tablet with a hold and a drag; nothing is cancelled by calling it. Whether it "
        "refunds, restocks and emails the customer is the Mac's policy, shown on the card — not "
        "yours to choose. Requires an order_id from a previous search."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "order_id": {"type": "string", "description": "The order_id returned by a previous search."},
            "reason": {"type": "string", "maxLength": 12, "description": "One of: customer, inventory, fraud, declined, staff, other. Default customer."},
            "staff_note": {"type": "string", "maxLength": MAX_STAFF_NOTE_CHARS, "description": "Optional internal note on the cancellation, one sentence."},
        },
        "required": ["order_id"],
    },
    tier=Tier.RED,
    issued_id_args=("order_id",),
    write=WriteSpec(
        operation="order_cancel",
        entity_kind="order",
        entity_arg="order_id",
        mutation="order_cancel",
        observe=_observe_cancel,
        execute=_execute_cancel,
        present=_present_cancel,
        entity=_entity_after,
        settle=_settle_cancel,
        verify=_verify_cancel,
        op_class="money",
        reversible=False,
        spoken_success="Order {label} cancelled.",
        spoken_failure="I couldn't confirm the cancellation. Check the order before asking again.",
        spoken_stale="The order changed since this was prepared. Nothing was sent.",
    ),
)
async def shopify_order_cancel(order_id: str, reason: str = "customer", staff_note: str = "") -> Prepared:
    """Prepare, never send: read the order as it is now, decide every argument, and hand the
    engine the fingerprint it must see again before it sends."""
    code = CANCEL_REASONS.get(str(reason or "customer").strip().lower())
    if code is None:
        raise ToolError("The reason must be one of: customer, inventory, fraud, declined, staff, other.")
    note = " ".join(str(staff_note or "").split())
    if len(note) > MAX_STAFF_NOTE_CHARS or "<" in note:
        raise ToolError("The staff note must be one plain sentence.")
    node = await _read_cancel_state(_c(), str(order_id))
    if node.get("cancelledAt"):
        raise ToolError(f"Order {node.get('name')} is already cancelled.")
    status = str(node.get("displayFulfillmentStatus") or "").upper()
    if status in ("FULFILLED", "PARTIALLY_FULFILLED"):
        raise ToolError(f"Order {node.get('name')} has shipped; it cannot be cancelled from here.")
    if str(node.get("displayFinancialStatus") or "").upper() == "VOIDED":
        raise ToolError(f"Order {node.get('name')} is voided; there is nothing to cancel.")
    settings = policy()
    full = node.get("fullRefund") or {}
    currency = _currency(node.get("currentTotalPriceSet"))
    refundable = _amount(full.get("amountSet")) if full else None
    maximum = _amount(full.get("maximumRefundableSet")) if full else None
    amount = min(x for x in (refundable, maximum) if x is not None) if refundable is not None or maximum is not None else None
    refund = bool(settings.cancel_refund) and (amount or 0) > 0
    restock_count = sum(int((e.get("node") or {}).get("unfulfilledQuantity") or 0) for e in ((node.get("lineItems") or {}).get("edges") or []))
    restock = bool(settings.cancel_restock) and restock_count > 0
    # A customer who asked to cancel expects the email; suspected fraud or a declined card gets none.
    notify = bool(settings.cancel_notify) and code not in ("FRAUD", "DECLINED")
    items = len((node.get("lineItems") or {}).get("edges") or [])
    total = _amount(node.get("currentTotalPriceSet"))
    execution = {
        "order_id": str(order_id), "reason": code, "staff_note": note, "refund": refund, "restock": restock,
        "notify": notify, "expected_refund": f"{amount:.2f}" if refund and amount else "0.00", "currency": currency,
    }
    read_back = "cancel order " + str(node.get("name") or "").rsplit("-", 1)[-1].lstrip("#")
    if refund and amount:
        read_back += f", refunding {_spoken_money(amount, currency)} to the original payment"
    read_back += (", restocking" if restock else ", no restock") + (", emailing the customer" if notify else ", without emailing the customer")
    return Prepared(
        execution=execution,
        before=cancel_fingerprint(node),
        expected_after={"cancelled": True},
        entity_ref=str(order_id),
        entity_label=str(node.get("name") or ""),
        summary={
            "customer": str((node.get("customer") or {}).get("displayName") or ""), "items": items, "total": total,
            "financial": str(node.get("displayFinancialStatus") or ""), "refund": refund, "refund_amount": amount if refund else None,
            "restock": restock, "restock_count": restock_count, "notify": notify, "reason": code, "currency": currency,
            "read_back": read_back,
            "ledger": {"refund": refund, "amount": f"{amount:.2f}" if refund and amount else "0.00", "currency": currency, "restock": restock_count if restock else 0, "notify": notify, "reason": code},
        },
    )


# ------------------------------------------------------------------------- refund
#
# Three shapes a clothing label actually issues, all priced by Shopify itself
# (suggestedRefund) and never by the model: the returned items (with restock), the postage,
# or a goodwill amount. The amount is capped at what the store can still refund; the
# transactions are Shopify's suggested ones, each capped at its own maximum; a gift-card
# tender is refused. Verified by the refunded total moving by exactly the amount.

MAX_REFUND_NOTE_CHARS = 120
RESTOCK_KINDS = {"return": "RETURN", "cancel": "CANCEL", "none": "NO_RESTOCK"}

REFUND_STATE_QUERY = """
query CrooksRefundState($id: ID!) {
  order(id: $id) {
    id
    name
    cancelledAt
    displayFinancialStatus
    refundable
    currentTotalPriceSet { shopMoney { amount currencyCode } }
    totalRefundedSet { shopMoney { amount currencyCode } }
  }
}
"""

SUGGESTED_REFUND_QUERY = """
query CrooksSuggestedRefund($id: ID!, $shippingAmount: Money, $shippingFull: Boolean, $refundLineItems: [RefundLineItemInput!], $full: Boolean) {
  order(id: $id) {
    id
    name
    suggestedRefund(shippingAmount: $shippingAmount, refundShipping: $shippingFull, refundLineItems: $refundLineItems, suggestFullRefund: $full) {
      amountSet { shopMoney { amount currencyCode } }
      subtotalSet { shopMoney { amount currencyCode } }
      totalTaxSet { shopMoney { amount currencyCode } }
      maximumRefundableSet { shopMoney { amount currencyCode } }
      shipping { amountSet { shopMoney { amount currencyCode } } maximumRefundableSet { shopMoney { amount currencyCode } } }
      suggestedTransactions { amountSet { shopMoney { amount currencyCode } } maximumRefundableSet { shopMoney { amount currencyCode } } gateway kind parentTransaction { id } }
      refundLineItems { quantity lineItem { id title } priceSet { shopMoney { amount currencyCode } } }
    }
  }
}
"""

LOCATIONS_QUERY = """
query CrooksLocations { locations(first: 10, includeInactive: false) { edges { node { id name isActive fulfillsOnlineOrders } } } }
"""


async def _read_refund_state(client: ShopifyClient, order_id: str) -> dict[str, Any]:
    payload = await client.graphql(REFUND_STATE_QUERY, {"id": order_id})
    node = (payload.get("data") or {}).get("order")
    if not isinstance(node, dict) or node.get("id") != order_id:
        raise ToolError(f"No order with id {order_id}.")
    return node


def refund_fingerprint(node: dict[str, Any]) -> dict[str, Any]:
    refunded = _amount(node.get("totalRefundedSet"))
    return {"refunded": f"{refunded:.2f}" if refunded is not None else "", "financial": str(node.get("displayFinancialStatus") or "")}


async def _observe_refund(execution: dict) -> Observed:
    node = await _read_refund_state(_c(), str(execution["order_id"]))
    return Observed(fingerprint=refund_fingerprint(node), entity=None)


async def _restock_location(client: ShopifyClient) -> tuple[str, str] | None:
    """The one location stock goes back to. None when there is not exactly one candidate:
    a guess between warehouses is not a restock."""
    payload = await client.graphql(LOCATIONS_QUERY)
    nodes = [e.get("node") or {} for e in ((payload.get("data") or {}).get("locations") or {}).get("edges") or []]
    candidates = [n for n in nodes if n.get("isActive") and n.get("fulfillsOnlineOrders")] or [n for n in nodes if n.get("isActive")]
    if len(candidates) != 1 or not candidates[0].get("id"):
        return None
    return str(candidates[0]["id"]), str(candidates[0].get("name") or "")


def _allocate(amount: float, suggested: list[dict[str, Any]], order_id: str) -> list[dict[str, Any]]:
    """The amount across Shopify's suggested transactions, in order, each capped at what it
    can refund. Not a gift card: money goes back the way it came, and only that way."""
    remaining = round(amount, 2)
    out: list[dict[str, Any]] = []
    for t in suggested:
        if remaining <= 0.004:
            break
        gateway = str(t.get("gateway") or "")
        if not gateway or "gift" in gateway.lower():
            continue
        parent = (t.get("parentTransaction") or {}).get("id")
        cap = _amount(t.get("maximumRefundableSet")) or _amount(t.get("amountSet")) or 0.0
        if not parent or cap <= 0:
            continue
        take = round(min(cap, remaining), 2)
        out.append({"orderId": order_id, "gateway": gateway, "kind": "REFUND", "amount": f"{take:.2f}", "parentId": str(parent)})
        remaining = round(remaining - take, 2)
    if remaining > 0.004:
        raise ToolError("That amount cannot go back the way it was paid; the store can refund less than that to the original payment.")
    return out


async def _entity_after_refund(execution: dict) -> dict:
    return await hydrator().order(str(execution["order_id"]), budget_s=0.0, fresh=True)


async def _execute_refund(execution: dict) -> dict:
    client = _c()
    order_id = str(execution["order_id"])
    payload = await client.mutate("refund_create", {"input": dict(execution["input"])})
    hydrator().forget(order_id)
    refund = ((payload.get("data") or {}).get("refundCreate") or {}).get("refund") or {}
    if not refund.get("id"):
        raise ShopifyError("Shopify did not confirm the refund.")
    return {"refund_id": str(refund["id"])}


def _verify_refund(before: dict, observed: dict, execution: dict) -> tuple[bool, str]:
    try:
        moved = round(float(observed.get("refunded") or 0) - float(before.get("refunded") or 0), 2)
        expected = round(float(execution.get("amount") or 0), 2)
    except ValueError:
        return False, ""
    return abs(moved - expected) < 0.005, ""


def _present_refund(proposal) -> dict:
    s = proposal.summary
    currency = str(s.get("currency") or "GBP")
    amount = float(s.get("amount") or 0)
    facts = [
        {"label": "Amount", "value": f"{_display(amount, currency)} to the original payment", "tone": "bad"},
        {"label": "Of", "value": f"{_display(float(s.get('paid') or 0), currency)} paid · {_display(float(s.get('remaining_after') or 0), currency)} remains refundable after"},
        {"label": "Items", "value": str(s.get("items_words") or "none · goodwill")},
        {"label": "Shipping", "value": str(s.get("shipping_words") or "no")},
        {"label": "Restock", "value": str(s.get("restock_words") or "no")},
        {"label": "Customer emailed", "value": "yes" if s.get("notify") else "no"},
    ]
    if s.get("reason"):
        facts.append({"label": "Reason", "value": str(s.get("reason"))})
    return {
        "title": "Refund", "summary": "", "detail": "A refund cannot be undone.", "facts": facts,
        "target": f"Drop to refund {_display(amount, currency)}", "done_title": "Refunded",
    }


@tool(
    name="shopify_refund_create",
    description=(
        "Prepare a refund on one order, priced by Shopify: the returned items (with restock), "
        "the postage, or a plain amount. Stages it for the owner to apply on the tablet with a "
        "hold and a drag; nothing is refunded by calling it. Requires an order_id from a previous "
        "search; item ids come from shopify_order_detail."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "order_id": {"type": "string", "description": "The order_id returned by a previous search."},
            "amount": {"type": "string", "maxLength": 12, "description": "A plain amount, e.g. \"20.00\". Leave out when refunding items."},
            "items": {
                "type": "array", "maxItems": 12,
                "items": {"type": "object", "properties": {"line_item_id": {"type": "string"}, "quantity": {"type": "integer"}}, "required": ["line_item_id", "quantity"]},
                "description": "The items being refunded, by line_item_id from the order detail, with quantities.",
            },
            "restock": {"type": "string", "maxLength": 8, "description": "For items: return (they came back), cancel (never shipped), or none. Default none."},
            "shipping": {"type": "string", "maxLength": 12, "description": "Refund the postage too: \"full\", or an amount such as \"3.95\". Default none."},
            "reason": {"type": "string", "maxLength": MAX_REFUND_NOTE_CHARS, "description": "Optional short reason, kept on the refund."},
        },
        "required": ["order_id"],
    },
    tier=Tier.RED,
    issued_id_args=("order_id",),
    write=WriteSpec(
        operation="refund_create",
        entity_kind="order",
        entity_arg="order_id",
        mutation="refund_create",
        observe=_observe_refund,
        execute=_execute_refund,
        present=_present_refund,
        entity=_entity_after_refund,
        verify=_verify_refund,
        op_class="money",
        reversible=False,
        spoken_success="Refunded {amount} on order {label}.",
        spoken_failure="I couldn't confirm the refund. Check the order before asking again.",
        spoken_stale="The order's payments changed since this was prepared. Nothing was sent.",
    ),
)
async def shopify_refund_create(
    order_id: str, amount: str = "", items: list | None = None, restock: str = "none", shipping: str = "", reason: str = "",
) -> Prepared:
    """Prepare, never send. Shopify prices the refund; the Mac decides every argument."""
    client = _c()
    reason = " ".join(str(reason or "").split())[:MAX_REFUND_NOTE_CHARS]
    if "<" in reason:
        raise ToolError("The reason must be plain text.")
    restock_kind = RESTOCK_KINDS.get(str(restock or "none").strip().lower())
    if restock_kind is None:
        raise ToolError("restock must be return, cancel or none.")
    items = items or []
    if not isinstance(items, list) or len(items) > 12:
        raise ToolError("Give up to twelve items.")
    shipping_word = str(shipping or "").strip().lower()
    plain = _decimal(amount) if str(amount or "").strip() else None
    if str(amount or "").strip() and plain is None:
        raise ToolError("The amount must be a number of pounds, like 20.00.")
    if plain is not None and (items or shipping_word):
        raise ToolError("Give either a plain amount, or items and/or shipping — not both.")
    if plain is None and not items and not shipping_word:
        raise ToolError("Say what to refund: an amount, the items, or the shipping.")

    state = await _read_refund_state(client, str(order_id))
    if str(state.get("displayFinancialStatus") or "").upper() in ("VOIDED", "REFUNDED") or state.get("refundable") is False:
        raise ToolError(f"Order {state.get('name')} has nothing left to refund.")
    currency = _currency(state.get("currentTotalPriceSet"))
    paid = _amount(state.get("currentTotalPriceSet")) or 0.0
    refunded_so_far = _amount(state.get("totalRefundedSet")) or 0.0

    # The items, checked against the order as it is now — not against what the model said.
    order = await hydrator().order(str(order_id), budget_s=0.0, fresh=True)
    by_id = {str(i.get("line_item_id")): i for i in order.get("items") or [] if i.get("line_item_id")}
    refund_lines: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            raise ToolError("Each item needs a line_item_id and a quantity.")
        line_id = str(item.get("line_item_id") or "")
        try:
            quantity = int(item.get("quantity"))
        except (TypeError, ValueError):
            raise ToolError("Each item needs a whole-number quantity.") from None
        known = by_id.get(line_id)
        if known is None:
            raise ToolError(f"{line_id or 'that item'} is not on order {state.get('name')}.")
        limit = known.get("refundable_quantity")
        if quantity < 1 or (isinstance(limit, int) and quantity > limit):
            raise ToolError(f"Only {limit} of {known.get('title')} can be refunded.")
        refund_lines.append({"lineItemId": line_id, "quantity": quantity, "restockType": restock_kind, "title": str(known.get("title") or ""), "variant": str(known.get("variant") or "")})

    location: tuple[str, str] | None = None
    if refund_lines and restock_kind != "NO_RESTOCK":
        location = await _restock_location(client)
        if location is None:
            raise ToolError("Stock cannot be put back: the store has no single location to restock at. Say restock none, or restock in Admin.")

    # Shopify prices it. A plain amount is priced against the full refund and then capped.
    shipping_amount = None
    shipping_full = None
    if shipping_word == "full":
        shipping_full = True
    elif shipping_word:
        shipping_amount = _decimal(shipping_word)
        if shipping_amount is None:
            raise ToolError("The shipping amount must be a number of pounds, like 3.95.")
    variables: dict[str, Any] = {"id": str(order_id), "shippingAmount": None, "shippingFull": None, "refundLineItems": None, "full": None}
    if plain is not None:
        variables["full"] = True
    else:
        variables["refundLineItems"] = [{"lineItemId": line["lineItemId"], "quantity": line["quantity"], "restockType": line["restockType"]} for line in refund_lines] or None
        variables["shippingAmount"] = f"{shipping_amount:.2f}" if shipping_amount is not None else None
        variables["shippingFull"] = shipping_full
    payload = await client.graphql(SUGGESTED_REFUND_QUERY, variables)
    node = (payload.get("data") or {}).get("order") or {}
    suggested = node.get("suggestedRefund") or {}
    maximum = _amount(suggested.get("maximumRefundableSet"))
    priced = _amount(suggested.get("amountSet"))
    if plain is not None:
        total = plain
    else:
        total = priced
    if total is None or total <= 0:
        raise ToolError("There is nothing to refund for that.")
    if maximum is not None and total > maximum + 0.004:
        raise ToolError(f"Only {_display(maximum, currency)} can still be refunded on order {state.get('name')}.")
    transactions = _allocate(total, list(suggested.get("suggestedTransactions") or []), str(order_id))
    shipping_priced = _amount((suggested.get("shipping") or {}).get("amountSet")) if plain is None else None

    settings = policy()
    notify = bool(getattr(settings, "refund_notify", True))
    refund_input: dict[str, Any] = {"orderId": str(order_id), "notify": notify, "currency": currency, "transactions": transactions}
    if reason:
        refund_input["note"] = reason
    if refund_lines:
        refund_input["refundLineItems"] = [
            {"lineItemId": line["lineItemId"], "quantity": line["quantity"], "restockType": line["restockType"], **({"locationId": location[0]} if location else {})}
            for line in refund_lines
        ]
    if shipping_full:
        refund_input["shipping"] = {"fullRefund": True}
    elif shipping_amount is not None:
        refund_input["shipping"] = {"amount": f"{shipping_amount:.2f}"}

    items_words = ", ".join(f"{line['title']}{' ' + line['variant'] if line['variant'] else ''}{' ×' + str(line['quantity']) if line['quantity'] > 1 else ''}" for line in refund_lines) or ("none · goodwill" if plain is not None else "none")
    shipping_words = "in full" if shipping_full else (_display(shipping_amount, currency) if shipping_amount is not None else "no")
    restock_words = f"{'returned to' if restock_kind == 'RETURN' else 'back into'} stock at {location[1]}" if location else "no"
    label = str(node.get("name") or state.get("name") or "")
    digits = label.rsplit("-", 1)[-1].lstrip("#")
    read_back = f"refund {_spoken_money(total, currency)} on order {digits}"
    if refund_lines:
        read_back += f" for {items_words}"
    if shipping_full or shipping_amount is not None:
        read_back += f", shipping {shipping_words}"
    read_back += (", restocking" if location else "") + (", emailing the customer" if notify else ", without emailing the customer")
    return Prepared(
        execution={"order_id": str(order_id), "input": refund_input, "amount": f"{total:.2f}", "currency": currency},
        before=refund_fingerprint(state),
        expected_after={"refunded": f"{refunded_so_far + total:.2f}"},
        entity_ref=str(order_id),
        entity_label=label,
        summary={
            "amount": f"{total:.2f}", "currency": currency, "paid": f"{paid:.2f}", "remaining_after": f"{max(0.0, (maximum if maximum is not None else paid - refunded_so_far) - total):.2f}",
            "items_words": items_words, "shipping_words": shipping_words, "restock_words": restock_words, "notify": notify, "reason": reason,
            "shipping_priced": f"{shipping_priced:.2f}" if shipping_priced is not None else "", "read_back": read_back,
            "ledger": {"amount": f"{total:.2f}", "currency": currency, "lines": len(refund_lines), "restock": restock_kind if refund_lines else "NO_RESTOCK", "shipping": bool(shipping_full or shipping_amount), "notify": notify, "tenders": len(transactions)},
        },
    )


def _decimal(value: object) -> float | None:
    text = str(value or "").strip().replace("£", "").replace(",", "")
    try:
        amount = round(float(text), 2)
    except ValueError:
        return None
    if amount <= 0 or amount > 9_999_999:
        return None
    return amount


# ------------------------------------------------------------------------ address
#
# The shipping address, changed to what the customer asked for and nothing else. RED
# always: a redirected parcel is the oldest fraud there is, and a DKIM pass proves the
# mailbox sent the mail, not that the account holder did — provenance is printed on the
# card, never a reason to soften the gesture. The evidence is one message, read here on
# the Mac: its sender must be the order's customer, and the postcode and street the model
# gives must appear in its text. The changed fields are merged into the address as it is
# now, every field is diffed, a reprint note goes on the order in the same write, and the
# change is proven by re-reading the address. There is no undo card: "change it back" is
# a fresh instruction with a fresh diff.

ADDRESS_STATE_QUERY = """
query CrooksAddressState($id: ID!) {
  order(id: $id) {
    id
    name
    note
    email
    cancelledAt
    displayFulfillmentStatus
    customer { displayName defaultEmailAddress { emailAddress } }
    shippingAddress { firstName lastName company address1 address2 city province provinceCode zip country countryCodeV2 phone }
    fulfillments(first: 5) { id status }
  }
}
"""

# Where the open fulfilment orders will ship. Needs a fulfilment-order scope the store may
# not have granted; read best-effort and printed after the change, never a reason to stop it.
DESTINATION_QUERY = """
query CrooksFulfillmentDestination($id: ID!) {
  order(id: $id) {
    id
    fulfillmentOrders(first: 5) {
      edges { node { id status destination { address1 address2 city zip countryCode } } }
    }
  }
}
"""

REPRINT_NOTE = "ADDRESS CHANGED — reprint label"
MAX_ADDRESS_CHARS = 100
# Shopify's MailingAddressInput, in its own names. The read side answers with countryCodeV2.
_ADDRESS_INPUT_KEYS = ("firstName", "lastName", "company", "address1", "address2", "city", "provinceCode", "zip", "countryCode", "phone")
# The fields that say where a parcel goes, as a fulfilment-order destination has them.
_PLACE_KEYS = ("address1", "address2", "city", "zip", "countryCode")
_CHANGE_WORDS = {
    "address1": "street", "address2": "second line", "city": "town", "zip": "postcode", "countryCode": "country",
    "provinceCode": "region", "firstName": "name", "lastName": "name", "company": "company", "phone": "phone",
}
_OPEN_FULFILLMENT_ORDERS = frozenset({"OPEN", "IN_PROGRESS", "SCHEDULED", "ON_HOLD"})
_COUNTRY_CODE = re.compile(r"^[A-Za-z]{2}$")
_PROVINCE_CODE = re.compile(r"^[A-Za-z0-9]{1,5}$")
_PHONE = re.compile(r"^\+?[0-9 ()\-]{6,20}$")
_WORD = re.compile(r"[a-z0-9]+")

_evidence_reader = None        # async (message_id) -> the message; the Gmail read, injectable
_destination_reads = True      # False once the store has said the fulfilment-order scope is missing


def bind_evidence(reader) -> None:
    """The read that turns a message id into the message. Tests hand in a fake inbox."""
    global _evidence_reader
    _evidence_reader = reader


async def _evidence(message_id: str) -> dict[str, Any]:
    reader = _evidence_reader
    if reader is None:
        from app.tools.gmail_tools import message_evidence

        reader = message_evidence
    return await reader(message_id)


def _clean_field(value: object, limit: int = MAX_ADDRESS_CHARS) -> str:
    text = " ".join(str(value or "").split())
    if len(text) > limit or "<" in text or any(ord(ch) < 32 for ch in text):
        raise ToolError("Address fields must be plain text, each under a hundred characters.")
    return text


def address_input(address: dict[str, Any] | None) -> dict[str, str]:
    """A MailingAddressInput from an address as Shopify answers with it: the same ten fields,
    whitespace collapsed, empty ones left out."""
    address = address if isinstance(address, dict) else {}
    out: dict[str, str] = {}
    for key in _ADDRESS_INPUT_KEYS:
        value = address.get("countryCodeV2") if key == "countryCode" and address.get("countryCodeV2") else address.get(key)
        text = " ".join(str(value or "").split())
        if text:
            out[key] = text
    return out


def _canon(value: object, key: str) -> str:
    text = " ".join(str(value or "").split()).casefold()
    if key == "zip":
        return text.replace(" ", "")
    if key == "phone":
        return re.sub(r"\D", "", text)
    return text


def address_hash(address: dict[str, Any]) -> str:
    """Sixteen hex characters standing for an address, case and spacing aside: what the
    fingerprint and the ledger carry instead of the street."""
    canon = {k: _canon(address.get(k), k) for k in _ADDRESS_INPUT_KEYS}
    return hashlib.sha256(json.dumps(canon, sort_keys=True).encode("utf-8")).hexdigest()[:16]


def place_hash(address: dict[str, Any]) -> str:
    """The same, for the five fields a fulfilment-order destination has."""
    canon = {k: _canon(address.get(k), k) for k in _PLACE_KEYS}
    return hashlib.sha256(json.dumps(canon, sort_keys=True).encode("utf-8")).hexdigest()[:16]


def _note_hash(note: object) -> str:
    text = (note if isinstance(note, str) else "").replace("\r\n", "\n").strip()
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def address_line(address: dict[str, Any]) -> str:
    """One line for the card: the street lines, the town, the postcode, the country when
    it is not the store's own."""
    parts = [address.get("address1"), address.get("address2"), address.get("city"), address.get("zip")]
    line = ", ".join(p for p in (str(x or "").strip() for x in parts) if p)
    country = str(address.get("countryCode") or "").upper()
    return f"{line}, {country}" if country and country != "GB" else line


async def _read_address_state(client: ShopifyClient, order_id: str) -> dict[str, Any]:
    payload = await client.graphql(ADDRESS_STATE_QUERY, {"id": order_id})
    node = (payload.get("data") or {}).get("order")
    if not isinstance(node, dict) or node.get("id") != order_id:
        raise ToolError(f"No order with id {order_id}.")
    return node


async def _read_destination(client: ShopifyClient, order_id: str) -> str:
    """The place hashes of the open fulfilment orders, joined; "none" when there are none;
    "unknown" when the store would not say."""
    global _destination_reads
    if not _destination_reads:
        return "unknown"
    try:
        payload = await client.graphql(DESTINATION_QUERY, {"id": order_id})
    except Exception as exc:  # noqa: BLE001 — a courtesy read; the address itself is the proof
        text = str(exc)
        if "ACCESS_DENIED" in text.upper() or "access denied" in text.lower():
            _destination_reads = False
        log.info("fulfilment destination not readable for %s: %s", order_id, text[:120])
        return "unknown"
    edges = (((payload.get("data") or {}).get("order") or {}).get("fulfillmentOrders") or {}).get("edges") or []
    places = []
    for edge in edges:
        node = edge.get("node") or {}
        destination = node.get("destination")
        if str(node.get("status") or "").upper() in _OPEN_FULFILLMENT_ORDERS and isinstance(destination, dict):
            places.append(place_hash(destination))
    return "|".join(sorted(set(places))) or "none"


def address_fingerprint(node: dict[str, Any], destination: str) -> dict[str, Any]:
    return {
        "address": address_hash(address_input(node.get("shippingAddress"))),
        "note": _note_hash(node.get("note")),
        "fulfillment": str(node.get("displayFulfillmentStatus") or ""),
        "cancelled": bool(node.get("cancelledAt")),
        "destination": destination,
    }


async def _observe_address(execution: dict) -> Observed:
    client = _c()
    order_id = str(execution["order_id"])
    node, destination = await asyncio.gather(_read_address_state(client, order_id), _read_destination(client, order_id))
    return Observed(fingerprint=address_fingerprint(node, destination), entity=None)


async def _execute_address(execution: dict) -> dict:
    client = _c()
    order_id = str(execution["order_id"])
    payload = await client.mutate(
        "order_shipping_address_set", {"id": order_id, "address": dict(execution["address"]), "note": str(execution["note"])},
    )
    hydrator().forget(order_id)
    order = ((payload.get("data") or {}).get("orderUpdate") or {}).get("order") or {}
    if order.get("id") != order_id:
        raise ShopifyError("Shopify did not confirm which order it updated.")
    return {"order_id": order_id}


def _verify_address(before: dict, observed: dict, execution: dict) -> tuple[bool, str]:
    """The address on the order is the staged one: proven. The note and the fulfilment
    destination are courtesies, said out loud when they did not follow."""
    if observed.get("address") != execution.get("address_hash"):
        return False, ""
    notes = []
    if observed.get("note") != execution.get("note_hash"):
        notes.append("The reprint note didn't stick; add it by hand.")
    destination = str(observed.get("destination") or "")
    if destination not in ("", "none", "unknown") and any(part != execution.get("place_hash") for part in destination.split("|")):
        notes.append("The fulfilment destination still shows the old address; check it before printing the label.")
    return True, " ".join(notes)


def _present_address(proposal) -> dict:
    s = proposal.summary
    facts = [
        {"label": "Customer", "value": str(s.get("customer") or "")},
        {"label": "From", "value": str(s.get("from_line") or "")},
        {"label": "To", "value": str(s.get("to_line") or ""), "tone": "warn"},
        {"label": "Changes", "value": ", ".join(str(c) for c in s.get("changes") or [])},
        {"label": "Cited", "value": str(s.get("cited") or ""), "tone": "" if s.get("evidence") else "warn"},
        {"label": "Note", "value": REPRINT_NOTE},
    ]
    return {
        "title": "Change the address", "summary": "",
        "detail": "Not shipped yet. If a label is already printed, reprint it.",
        "facts": facts, "done_title": "Address changed",
    }


def _when(date_header: str) -> str:
    try:
        return parsedate_to_datetime(date_header).strftime("%-d %b %H:%M")
    except (TypeError, ValueError, IndexError):
        return str(date_header or "")[:16]


def _mentions(body: str, new: dict[str, str], changed: set[str]) -> tuple[list[str], list[str]]:
    """Which of the changed parts the message's own text contains, and which it does not.
    The postcode with its spaces removed; the street by its number and its longest word,
    so "12 Baker St" in the mail matches "12 Baker Street" on the card."""
    text = " ".join(str(body or "").split()).casefold()
    squashed = text.replace(" ", "")
    found, missing = [], []
    if "zip" in changed:
        (found if _canon(new.get("zip"), "zip") and _canon(new.get("zip"), "zip") in squashed else missing).append("postcode")
    if "address1" in changed:
        tokens = _WORD.findall(str(new.get("address1") or "").casefold())
        number = tokens[0] if tokens else ""
        word = max((t for t in tokens if t.isalpha() and len(t) >= 3), key=len, default="")
        ok = bool(tokens) and re.search(rf"(?<![a-z0-9]){re.escape(number)}(?![a-z0-9])", text) is not None and (not word or word in text)
        (found if ok else missing).append("street")
    if "city" in changed and not ({"zip", "address1"} & changed):
        city = _canon(new.get("city"), "city")
        (found if city and city in text else missing).append("town")
    return found, missing


@tool(
    name="shopify_order_shipping_address_set",
    description=(
        "Prepare a change to one order's shipping address, before it ships. Give only the parts "
        "that change; the Mac merges them into the address as it is now and prints the difference. "
        "When the new address came from an email, pass that message's message_id: the Mac reads "
        "the message itself and refuses unless the postcode and street appear in it. Staged for "
        "the owner to apply with a hold on the tablet; nothing changes by calling it."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "order_id": {"type": "string", "description": "The order_id returned by a previous search."},
            "evidence_message_id": {"type": "string", "maxLength": 40, "description": "The message_id of the customer's email giving the new address, when there is one."},
            "address1": {"type": "string", "maxLength": MAX_ADDRESS_CHARS, "description": "The new first line: number and street."},
            "address2": {"type": "string", "maxLength": MAX_ADDRESS_CHARS, "description": "The new second line (flat, building), if any."},
            "city": {"type": "string", "maxLength": MAX_ADDRESS_CHARS, "description": "The new town or city."},
            "postcode": {"type": "string", "maxLength": 12, "description": "The new postcode."},
            "country_code": {"type": "string", "maxLength": 2, "description": "Two-letter country code, only when the country changes."},
            "province_code": {"type": "string", "maxLength": 5, "description": "Region or state code, only when the country needs one."},
            "name": {"type": "string", "maxLength": 80, "description": "The recipient's name, only when it changes."},
            "company": {"type": "string", "maxLength": MAX_ADDRESS_CHARS, "description": "Company or building name, only when it changes."},
            "phone": {"type": "string", "maxLength": 20, "description": "Delivery phone number, only when it changes."},
        },
        "required": ["order_id"],
    },
    tier=Tier.RED,
    issued_id_args=("order_id", "evidence_message_id"),
    write=WriteSpec(
        operation="order_shipping_address_set",
        entity_kind="order",
        entity_arg="order_id",
        mutation="order_shipping_address_set",
        observe=_observe_address,
        execute=_execute_address,
        present=_present_address,
        entity=_entity_after,
        verify=_verify_address,
        op_class="irreversible",
        reversible=False,
        spoken_success="Changed the address on order {label}. Reprint the label if one is printed.",
        spoken_failure="I couldn't confirm the address change. Check the order before asking again.",
        spoken_stale="The order changed since this was prepared. Nothing was sent.",
    ),
)
async def shopify_order_shipping_address_set(
    order_id: str, evidence_message_id: str = "", address1: str = "", address2: str = "", city: str = "", postcode: str = "",
    country_code: str = "", province_code: str = "", name: str = "", company: str = "", phone: str = "",
) -> Prepared:
    """Prepare, never send: the address as it is now, the parts that change merged in, the
    evidence read and checked, the diff printed, and the fingerprint the engine must see
    again before it sends."""
    client = _c()
    given = {k: _clean_field(v) for k, v in {
        "address1": address1, "address2": address2, "city": city, "zip": postcode, "countryCode": country_code,
        "provinceCode": province_code, "name": name, "company": company, "phone": phone,
    }.items()}
    given["zip"] = given["zip"].upper()
    if len(given["zip"]) > 12:
        raise ToolError("That postcode is too long.")
    if given["countryCode"] and not _COUNTRY_CODE.match(given["countryCode"]):
        raise ToolError("country_code must be two letters, like GB.")
    if given["provinceCode"] and not _PROVINCE_CODE.match(given["provinceCode"]):
        raise ToolError("province_code must be a short code, like ENG or CA.")
    if given["phone"] and not _PHONE.match(given["phone"]):
        raise ToolError("The phone number must be digits, with an optional leading +.")

    node = await _read_address_state(client, str(order_id))
    label = str(node.get("name") or "")
    if node.get("cancelledAt"):
        raise ToolError(f"Order {label} is cancelled; its address does not matter now.")
    status = str(node.get("displayFulfillmentStatus") or "").upper()
    shipped = status in ("FULFILLED", "PARTIALLY_FULFILLED") or any(
        str(f.get("status") or "").upper() == "SUCCESS" for f in node.get("fulfillments") or [] if isinstance(f, dict)
    )
    if shipped:
        raise ToolError(f"Order {label} has shipped; the address cannot be changed from here. Contact the carrier.")
    current = address_input(node.get("shippingAddress"))
    if not current.get("address1"):
        raise ToolError(f"Order {label} has no shipping address to change.")

    # The merge: a new street brings its own second line (an old flat number on a new street
    # is a wrong address); a new country drops a region code that belonged to the old one.
    new = dict(current)
    if given["address1"]:
        new["address1"] = given["address1"]
        new.pop("address2", None)
        if given["address2"]:
            new["address2"] = given["address2"]
    elif given["address2"]:
        new["address2"] = given["address2"]
    if given["city"]:
        new["city"] = given["city"]
    if given["zip"]:
        new["zip"] = given["zip"]
    if given["countryCode"] and given["countryCode"].upper() != current.get("countryCode"):
        new["countryCode"] = given["countryCode"].upper()
        new.pop("provinceCode", None)
    if given["provinceCode"]:
        new["provinceCode"] = given["provinceCode"].upper()
    if given["name"]:
        first, _, last = given["name"].partition(" ")
        new["firstName"] = first
        new.pop("lastName", None)
        if last:
            new["lastName"] = last
    if given["company"]:
        new["company"] = given["company"]
    if given["phone"]:
        new["phone"] = given["phone"]
    if not new.get("countryCode"):
        raise ToolError(f"Order {label}'s address has no country; set it in Admin first.")

    changed = {k for k in _ADDRESS_INPUT_KEYS if _canon(new.get(k), k) != _canon(current.get(k), k)}
    if not changed:
        raise ToolError(f"That is the address already on order {label}; nothing to change.")
    changes = []
    for key in _ADDRESS_INPUT_KEYS:
        if key in changed:
            word = _CHANGE_WORDS[key] + (" cleared" if not new.get(key) else "")
            if word not in changes:
                changes.append(word)

    # The evidence: read here, never trusted from the model's summary of it.
    customer_email = str(node.get("email") or ((node.get("customer") or {}).get("defaultEmailAddress") or {}).get("emailAddress") or "").strip().lower()
    evidence = None
    message_id = str(evidence_message_id or "").strip()
    if message_id:
        evidence = await _evidence(message_id)
        sender = str(evidence.get("from_email") or "").strip().lower()
        if not customer_email or sender != customer_email:
            raise ToolError(
                f"That email is from {sender or 'an unknown sender'}, not the customer on order {label}. "
                "The address was not changed; do it in Admin if you are sure."
            )
        found, missing = _mentions(str(evidence.get("body") or ""), new, changed)
        if missing:
            raise ToolError(
                f"The email does not contain the new {' or '.join(missing)}. Read it again, or change the address in Admin."
            )
        cited = (
            f"Email from {sender}, {_when(str(evidence.get('date') or ''))} · "
            f"{'verified sender' if evidence.get('authenticated') else 'sender not verified'}"
            + (f" · {' and '.join(found)} found in the message" if found else "")
        )
    else:
        cited = "none — as dictated"

    note = append_note(str(node.get("note") or ""), REPRINT_NOTE) if REPRINT_NOTE not in str(node.get("note") or "") else str(node.get("note") or "")
    destination = await _read_destination(client, str(order_id))
    from_line = address_line(current)
    to_line = address_line(new)
    digits = label.rsplit("-", 1)[-1].lstrip("#")
    read_back = f"change the address on order {digits} to {to_line}"
    execution = {
        "order_id": str(order_id), "address": new, "note": note,
        "address_hash": address_hash(new), "place_hash": place_hash(new), "note_hash": _note_hash(note),
    }
    pii = [v for v in (current.get("address1"), current.get("address2"), current.get("zip"), new.get("address1"), new.get("address2"), new.get("zip"),
                       new.get("phone"), given["name"]) if v]
    return Prepared(
        execution=execution,
        before=address_fingerprint(node, destination),
        expected_after={"address": execution["address_hash"]},
        entity_ref=str(order_id),
        entity_label=label,
        summary={
            "customer": str((node.get("customer") or {}).get("displayName") or ""),
            "from_line": from_line, "to_line": to_line, "changes": changes, "cited": cited,
            "evidence": bool(evidence), "verified_sender": bool(evidence and evidence.get("authenticated")),
            "read_back": read_back, "pii": pii,
            "ledger": {
                "line1": "address1" in changed, "post": "zip" in changed, "town": "city" in changed, "country": new.get("countryCode", ""),
                "evidence": bool(evidence), "verified_sender": bool(evidence and evidence.get("authenticated")),
                "destination_known": destination != "unknown",
            },
        },
    )
