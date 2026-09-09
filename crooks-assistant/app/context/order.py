"""The order as the tablet shows it: one nested read, then the customer's history and the
inbox around it, fetched beside each other under a budget rather than one after the other.

The read model is a plain dict shaped here, key by key, from what Shopify returned — the
same discipline as app/presentation.py, one layer down. The model reads the same dict the
card is built from, so the spoken answer and the screen cannot disagree.

Enrichment that misses the budget is not lost: it carries on in the background, and the
tablet collects it from GET /context/order/{id} once the card is up. Nothing is hydrated
serially in front of the first paint.
"""

from __future__ import annotations

import asyncio
import logging
import re
import time
from collections.abc import Awaitable, Callable
from typing import Any

from app.clients.shopify import ShopifyClient, ShopifyError
from app.tools.registry import ToolError

log = logging.getLogger("crooks.context")

# Bounds. The card is eight inches wide; the model's context is not free either.
MAX_ITEMS = 12
RECENT_ORDERS = 5
EMAIL_THREADS = 3
MAX_EVENTS = 5
MAX_REFUNDS = 6
MAX_TEXT = 200
# How long the tool waits for the customer's history and the inbox before answering with
# what it has. The order itself is never waited on twice.
ENRICH_BUDGET_S = 1.5
# A finished enrichment is reused for the same order this long: a second look at the order
# a moment later re-reads the order (its state matters) but not the customer's history.
ENRICH_REUSE_S = 60.0
JOB_RETENTION_S = 600.0

# One document, validated against the Admin API schema (2025-07). Items, fulfilments,
# refunds and events are capped well under the 1,000-point query cost.
ORDER_CONTEXT_QUERY = """
query CrooksOrderContext($id: ID!, $n: Int!) {
  order(id: $id) {
    id
    name
    createdAt
    processedAt
    cancelledAt
    cancelReason
    closedAt
    displayFulfillmentStatus
    displayFinancialStatus
    fullyPaid
    tags
    note
    refundable
    currentTotalPriceSet { shopMoney { amount currencyCode } }
    subtotalPriceSet { shopMoney { amount currencyCode } }
    totalShippingPriceSet { shopMoney { amount currencyCode } }
    totalTaxSet { shopMoney { amount currencyCode } }
    totalDiscountsSet { shopMoney { amount currencyCode } }
    totalRefundedSet { shopMoney { amount currencyCode } }
    totalOutstandingSet { shopMoney { amount currencyCode } }
    shippingLine { title }
    shippingAddress {
      firstName lastName company address1 address2 city province provinceCode zip country countryCodeV2
    }
    customer {
      id
      displayName
      numberOfOrders
      createdAt
      amountSpent { amount currencyCode }
      defaultEmailAddress { emailAddress }
    }
    lineItems(first: $n) {
      edges { node {
        id
        title
        quantity
        currentQuantity
        refundableQuantity
        unfulfilledQuantity
        variantTitle
        sku
        originalTotalSet { shopMoney { amount currencyCode } }
        discountedTotalSet { shopMoney { amount currencyCode } }
        image { url width height }
        variant {
          id
          inventoryQuantity
          inventoryItem { id tracked }
          selectedOptions { name value }
        }
        product { id title }
      } }
    }
    fulfillments(first: 10) {
      id
      status
      displayStatus
      createdAt
      trackingInfo { company number url }
    }
    refunds(first: 10) {
      id
      createdAt
      note
      totalRefundedSet { shopMoney { amount currencyCode } }
    }
    events(first: 5, sortKey: CREATED_AT, reverse: true) {
      edges { node { id message createdAt } }
    }
  }
}
"""

CUSTOMER_ORDERS_QUERY = """
query CrooksCustomerOrders($id: ID!, $n: Int!) {
  customer(id: $id) {
    id
    displayName
    numberOfOrders
    createdAt
    tags
    amountSpent { amount currencyCode }
    defaultEmailAddress { emailAddress }
    lastOrder { id name }
    orders(first: $n, sortKey: CREATED_AT, reverse: true) {
      edges { node {
        id
        name
        createdAt
        processedAt
        cancelledAt
        displayFulfillmentStatus
        displayFinancialStatus
        currentTotalPriceSet { shopMoney { amount currencyCode } }
        lineItems(first: 5) { edges { node { title quantity } } }
      } }
    }
  }
}
"""

ThreadsFor = Callable[..., Awaitable[dict[str, Any]]]


def money(node: Any) -> str | None:
    """"430.50 GBP" — the same text form every tool returns, so the card formats it once."""
    if not isinstance(node, dict):
        return None
    shop = node.get("shopMoney") or node
    amount = shop.get("amount") if isinstance(shop, dict) else None
    if amount is None:
        return None
    return f"{amount} {shop.get('currencyCode', '')}".strip()


def money_amount(node: Any) -> float | None:
    if not isinstance(node, dict):
        return None
    shop = node.get("shopMoney") or node
    try:
        return float(shop.get("amount"))
    except (TypeError, ValueError, AttributeError):
        return None


def order_digits(name: Any) -> str:
    """"CROOKS-1938" and "#1036" are order 1938 and order 1036 to the office."""
    text = str(name or "").strip()
    digits = text.rsplit("-", 1)[-1].lstrip("#").strip()
    return digits if digits.isdigit() else ""


# ------------------------------------------------------------------ the order itself


def shape_order(node: dict[str, Any]) -> dict[str, Any]:
    """The order read model from one CrooksOrderContext node. Every key is chosen here; a
    field Shopify adds does not reach the model or the card until a line here carries it."""
    customer = node.get("customer") or {}
    email = (customer.get("defaultEmailAddress") or {}).get("emailAddress")
    items = []
    for edge in ((node.get("lineItems") or {}).get("edges") or [])[:MAX_ITEMS]:
        it = edge.get("node") or {}
        variant = it.get("variant") or {}
        inventory_item = variant.get("inventoryItem") or {}
        image = it.get("image") or {}
        quantity = it.get("quantity")
        items.append({
            "line_item_id": it.get("id"),
            "title": it.get("title"),
            "variant": it.get("variantTitle"),
            "sku": it.get("sku"),
            "quantity": quantity,
            "current_quantity": it.get("currentQuantity", quantity),
            "refundable_quantity": it.get("refundableQuantity"),
            "unfulfilled_quantity": it.get("unfulfilledQuantity"),
            "total": money(it.get("originalTotalSet")),
            "discounted_total": money(it.get("discountedTotalSet")),
            "image_url": image.get("url"),
            "variant_id": variant.get("id"),
            "product_id": (it.get("product") or {}).get("id"),
            "product_title": (it.get("product") or {}).get("title"),
            "options": [
                {"name": str(o.get("name", ""))[:40], "value": str(o.get("value", ""))[:40]}
                for o in (variant.get("selectedOptions") or [])[:4] if isinstance(o, dict)
            ],
            "stock": {
                "tracked": bool(inventory_item.get("tracked", True)),
                "available": variant.get("inventoryQuantity"),
                "inventory_item_id": inventory_item.get("id"),
            } if variant else None,
        })
    fulfillments = []
    for f in (node.get("fulfillments") or [])[:10]:
        tracking = (f.get("trackingInfo") or [{}])[0] or {}
        fulfillments.append({
            "fulfillment_id": f.get("id"),
            "status": f.get("status"),
            "display_status": f.get("displayStatus"),
            "shipped_at": f.get("createdAt"),
            "carrier": tracking.get("company"),
            "number": tracking.get("number"),
            "url": tracking.get("url"),
        })
    refunds = [
        {"refund_id": r.get("id"), "created_at": r.get("createdAt"),
         "amount": money(r.get("totalRefundedSet")), "note": _short(r.get("note"))}
        for r in (node.get("refunds") or [])[:MAX_REFUNDS]
    ]
    events = [
        {"at": (e.get("node") or {}).get("createdAt"), "message": _short((e.get("node") or {}).get("message"), 120)}
        for e in ((node.get("events") or {}).get("edges") or [])[:MAX_EVENTS]
    ]
    address = node.get("shippingAddress") or {}
    total = node.get("currentTotalPriceSet")
    return {
        "order_id": node.get("id"),
        "order_number": node.get("name"),
        "placed_at": node.get("processedAt") or node.get("createdAt"),
        "fulfillment": node.get("displayFulfillmentStatus"),
        "payment": node.get("displayFinancialStatus"),
        "total": money(total),
        "customer_name": customer.get("displayName"),
        "customer_id": customer.get("id"),
        "customer_email": email,
        "customer": {
            "customer_id": customer.get("id"),
            "name": customer.get("displayName"),
            "email": email,
            "orders": _int(customer.get("numberOfOrders")),
            "spent": money(customer.get("amountSpent")),
            "since": customer.get("createdAt"),
        } if customer else None,
        "items": items,
        "items_truncated": len(items) >= MAX_ITEMS,
        "fulfillments": fulfillments,
        "cancelled_at": node.get("cancelledAt"),
        "cancel_reason": node.get("cancelReason"),
        "closed_at": node.get("closedAt"),
        "fully_paid": node.get("fullyPaid"),
        "note": _short(node.get("note"), 1200),
        "tags": [str(t)[:40] for t in (node.get("tags") or [])[:10]],
        "money": {
            "subtotal": money(node.get("subtotalPriceSet")),
            "shipping": money(node.get("totalShippingPriceSet")),
            "tax": money(node.get("totalTaxSet")),
            "discounts": money(node.get("totalDiscountsSet")),
            "refunded": money(node.get("totalRefundedSet")),
            "outstanding": money(node.get("totalOutstandingSet")),
            "total": money(total),
            "currency": ((total or {}).get("shopMoney") or {}).get("currencyCode"),
        },
        "refundable": node.get("refundable"),
        "refunds": refunds,
        "shipping_method": ((node.get("shippingLine") or {}).get("title")),
        # City and country for a spoken answer; the address itself is for the card and for
        # the change-of-address diff, and is redacted by key wherever a log might carry it.
        "ships_to": ", ".join(p for p in (address.get("city"), address.get("country")) if p) or None,
        "shipping_address": shape_address(address) if address else None,
        "events": events,
    }


def shape_address(address: dict[str, Any]) -> dict[str, Any]:
    name = " ".join(p for p in (address.get("firstName"), address.get("lastName")) if p)
    lines = [address.get("address1"), address.get("address2")]
    return {
        "name": name or None,
        "company": address.get("company") or None,
        "lines": [str(line)[:120] for line in lines if line],
        "city": address.get("city") or None,
        "province": address.get("province") or None,
        "province_code": address.get("provinceCode") or None,
        "zip": address.get("zip") or None,
        "country": address.get("country") or None,
        "country_code": address.get("countryCodeV2") or None,
    }


# --------------------------------------------------------------- the customer's history


def shape_customer_history(node: dict[str, Any], *, current_order_id: str | None = None) -> dict[str, Any]:
    """What the owner asks about a person: first order? bought before? spent? last order?
    anything else waiting to ship?"""
    recent = []
    other_unfulfilled = []
    for edge in ((node.get("orders") or {}).get("edges") or [])[:RECENT_ORDERS]:
        o = edge.get("node") or {}
        brief = ", ".join(
            f"{(e.get('node') or {}).get('title', '')}" + (f" ×{(e.get('node') or {}).get('quantity')}" if (e.get('node') or {}).get('quantity', 1) not in (1, None) else "")
            for e in ((o.get("lineItems") or {}).get("edges") or [])[:5]
        )
        row = {
            "order_id": o.get("id"),
            "order_number": o.get("name"),
            "placed_at": o.get("processedAt") or o.get("createdAt"),
            "fulfillment": o.get("displayFulfillmentStatus"),
            "payment": o.get("displayFinancialStatus"),
            "cancelled_at": o.get("cancelledAt"),
            "total": money(o.get("currentTotalPriceSet")),
            "items_brief": brief[:MAX_TEXT] or None,
            "current": bool(current_order_id) and o.get("id") == current_order_id,
        }
        recent.append(row)
        if (
            not row["current"] and not row["cancelled_at"]
            and str(row["fulfillment"] or "").upper() in {"UNFULFILLED", "PARTIALLY_FULFILLED", "ON_HOLD", "SCHEDULED"}
        ):
            other_unfulfilled.append(row["order_number"])
    count = _int(node.get("numberOfOrders"))
    email = (node.get("defaultEmailAddress") or {}).get("emailAddress")
    last = node.get("lastOrder") or {}
    return {
        "customer_id": node.get("id"),
        "name": node.get("displayName"),
        "email": email,
        "orders": count,
        "spent": money(node.get("amountSpent")),
        "since": node.get("createdAt"),
        "tags": [str(t)[:40] for t in (node.get("tags") or [])[:10]],
        "standing": standing(count),
        # The first order is known only when every order was fetched.
        "first_order_at": recent[-1]["placed_at"] if recent and count is not None and count <= len(recent) else None,
        "last_order": {"order_id": last.get("id"), "order_number": last.get("name")} if last else None,
        "recent": recent,
        "other_unfulfilled": other_unfulfilled,
        "provenance": "SHOPIFY",
    }


def standing(count: int | None) -> str:
    if count is None:
        return "unknown"
    if count <= 1:
        return "first order"
    if count >= 4:
        return "regular"
    return "returning"


# ---------------------------------------------------------------- the inbox around it


def correlate_threads(threads: list[dict[str, Any]], *, customer_email: str | None, digits: str) -> list[dict[str, Any]]:
    """Which threads are about this order, and how sure that is. The sender matching the
    order's customer is the strong signal; the order number alone is a mention, and a name
    match is nothing at all — anyone can be called Sam."""
    email = (customer_email or "").strip().lower()
    out = []
    for t in threads:
        sender = str(t.get("from_email") or "").strip().lower()
        text = f"{t.get('subject', '')} {t.get('snippet', '')}"
        mentions = bool(digits) and re.search(rf"(?<!\d){re.escape(digits)}(?!\d)", text) is not None
        verified = bool(email) and sender == email
        if not verified and not mentions:
            continue
        out.append({
            **t,
            "verified_sender": verified,
            "match": "both" if verified and mentions else ("sender" if verified else "order_number"),
            "provenance": "CUSTOMER_EMAIL" if verified else "UNKNOWN",
        })
    return out[:EMAIL_THREADS]


# ------------------------------------------------------------------------ the hydrator


class _Job:
    """One order's enrichment in flight: the parts land one by one, so a caller who cannot
    wait for all of them takes what is there and says what is still to come."""

    __slots__ = ("order_id", "parts", "task", "started", "finished")

    def __init__(self, order_id: str, started: float) -> None:
        self.order_id = order_id
        self.parts: dict[str, Any] = {}
        self.task: asyncio.Task | None = None
        self.started = started
        self.finished: float | None = None

    @property
    def pending(self) -> list[str]:
        return [name for name in ("history", "email") if name not in self.parts]


class Hydrator:
    """Builds the read models. One per process; the tools and the /context route share it so
    an order looked up ahead of the model is not looked up again a second later."""

    def __init__(self, shopify: Callable[[], ShopifyClient], *, threads_for: ThreadsFor | None = None, clock=time.time) -> None:
        self._shopify = shopify
        self._threads_for = threads_for
        self.clock = clock
        self._jobs: dict[str, _Job] = {}
        self._cores: dict[str, asyncio.Task] = {}   # an order read in flight, so two callers share it
        self.core_reads = 0

    # -------------------------------------------------------------- order

    async def order(self, order_id: str, *, budget_s: float = ENRICH_BUDGET_S) -> dict[str, Any]:
        """The order, fresh, with as much of its history and inbox as arrives within the
        budget. `pending` names what is still on its way."""
        core = await self._core(order_id)
        job = self._enrich(order_id, core)
        if budget_s > 0 and job.task is not None and not job.task.done():
            await asyncio.wait({job.task}, timeout=budget_s)
        return self._merge(core, job)

    async def extension(self, order_id: str, *, wait_s: float) -> dict[str, Any]:
        """What the tablet collects after the card is up: the parts of the enrichment that
        missed the turn's budget. Starts the work if nothing is in flight (a restart, a card
        the owner came back to)."""
        job = self._jobs.get(order_id)
        if job is None or (job.finished is not None and self.clock() - job.finished > ENRICH_REUSE_S):
            core = await self._core(order_id)
            job = self._enrich(order_id, core)
        if job.task is not None and not job.task.done() and wait_s > 0:
            await asyncio.wait({job.task}, timeout=wait_s)
        return {"order_id": order_id, "pending": job.pending, **{k: v for k, v in job.parts.items()}}

    async def customer(self, customer_id: str) -> dict[str, Any]:
        """A customer's history on its own, with the inbox around them."""
        history = await self._history(customer_id, current_order_id=None)
        if history is None:
            raise ToolError(f"No customer with id {customer_id}.")
        email = await self._email(history.get("email"), digits="")
        return {**history, "email_threads": email}

    # --------------------------------------------------------- internals

    async def _core(self, order_id: str) -> dict[str, Any]:
        task = self._cores.get(order_id)
        if task is None or task.done():
            task = asyncio.ensure_future(self._read_order(order_id))
            self._cores[order_id] = task
        try:
            return await task
        finally:
            if self._cores.get(order_id) is task and task.done():
                self._cores.pop(order_id, None)

    async def _read_order(self, order_id: str) -> dict[str, Any]:
        self.core_reads += 1
        payload = await self._shopify().graphql(ORDER_CONTEXT_QUERY, {"id": order_id, "n": MAX_ITEMS})
        node = (payload.get("data") or {}).get("order")
        if not isinstance(node, dict) or node.get("id") != order_id:
            raise ToolError(f"No order with id {order_id}.")
        shaped = shape_order(node)
        if payload.get("_partial_errors"):
            shaped["partial"] = str(payload["_partial_errors"])[:200]
        return shaped

    def _enrich(self, order_id: str, core: dict[str, Any]) -> _Job:
        self._prune()
        job = self._jobs.get(order_id)
        now = self.clock()
        if job is not None and (job.finished is None or now - job.finished < ENRICH_REUSE_S):
            return job
        job = _Job(order_id, now)
        self._jobs[order_id] = job
        job.task = asyncio.ensure_future(self._run(job, core))
        return job

    async def _run(self, job: _Job, core: dict[str, Any]) -> None:
        customer = core.get("customer") or {}
        customer_id = customer.get("customer_id")
        digits = order_digits(core.get("order_number"))

        async def history() -> None:
            try:
                job.parts["history"] = await self._history(customer_id, current_order_id=core.get("order_id")) if customer_id else None
            except Exception as exc:  # noqa: BLE001 — the order stands without its history
                log.warning("customer history unavailable for %s: %s", job.order_id, type(exc).__name__)
                job.parts["history"] = None

        async def email() -> None:
            try:
                job.parts["email"] = await self._email(customer.get("email"), digits=digits)
            except Exception as exc:  # noqa: BLE001
                log.warning("email correlation unavailable for %s: %s", job.order_id, type(exc).__name__)
                job.parts["email"] = {"available": False, "reason": "unavailable", "threads": []}

        try:
            await asyncio.gather(history(), email())
        finally:
            job.finished = self.clock()

    async def _history(self, customer_id: str | None, *, current_order_id: str | None) -> dict[str, Any] | None:
        if not customer_id:
            return None
        try:
            payload = await self._shopify().graphql(CUSTOMER_ORDERS_QUERY, {"id": customer_id, "n": RECENT_ORDERS})
        except ShopifyError as exc:
            log.warning("customer history read failed: %s", exc)
            return None
        node = (payload.get("data") or {}).get("customer")
        if not isinstance(node, dict):
            return None
        return shape_customer_history(node, current_order_id=current_order_id)

    async def _email(self, customer_email: str | None, *, digits: str) -> dict[str, Any]:
        if self._threads_for is None:
            return {"available": False, "reason": "Gmail is not configured on this backend.", "threads": []}
        terms = [f"CROOKS-{digits}", f"#{digits}"] if digits else []
        found = await self._threads_for(sender=customer_email or "", terms=terms)
        if not found.get("available"):
            return {"available": False, "reason": str(found.get("reason") or "")[:160], "threads": []}
        threads = correlate_threads(list(found.get("threads") or []), customer_email=customer_email, digits=digits)
        return {"available": True, "threads": threads}

    def _merge(self, core: dict[str, Any], job: _Job) -> dict[str, Any]:
        out = dict(core)
        out["history"] = job.parts.get("history")
        out["email"] = job.parts.get("email")
        out["pending"] = job.pending
        return out

    def _prune(self) -> None:
        now = self.clock()
        for order_id, job in list(self._jobs.items()):
            if now - job.started > JOB_RETENTION_S:
                if job.task is not None and not job.task.done():
                    job.task.cancel()
                del self._jobs[order_id]


def _short(value: Any, limit: int = MAX_TEXT) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
