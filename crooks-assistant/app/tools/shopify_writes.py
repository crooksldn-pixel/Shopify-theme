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
import logging
import time
from typing import Any

from app.actions.models import Observed, Prepared
from app.clients.shopify import ShopifyClient, ShopifyError
from app.tools.gate import Tier
from app.tools.registry import ToolError, WriteSpec, tool
from app.tools.shopify_tools import _c, hydrator

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
