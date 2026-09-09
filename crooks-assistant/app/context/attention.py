"""What an order needs, read from the order alone — its age, its money, its stock, its
customer's history and the email around it — as a few lines the card shows and the model
reads. Every line is the Mac's own reading of facts it fetched; none is an instruction. A
line may name what the owner could say next ("cancel order 1930"): a suggestion printed for
a person, never a change staged, and never on an email's say-so — an email is evidence of
what a customer wants, and the owner decides."""

from __future__ import annotations

import re
import time
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Any

MAX_LINES = 6
AGING_AMBER_DAYS = 2
AGING_RED_DAYS = 5
VISIBLE_DAYS = 60
REGULAR_ORDERS = 4
REGULAR_SPEND = 500.0
_LEVELS = {"red": 0, "amber": 1, "green": 2}
_ADDRESS = re.compile(r"\b(address|moved|wrong (?:flat|house|street|postcode)|new (?:flat|house|place)|redirect|deliver(?:y)? to)\b", re.I)
_CANCEL = re.compile(r"\b(cancel|cancellation|changed my mind|don'?t want)\b", re.I)
_REFUND = re.compile(r"\b(refund|money back|chargeback|dispute)\b", re.I)
_RETURN = re.compile(r"\b(return|exchange|swap|wrong size|too (?:small|big|large))\b", re.I)
_RETURN_STATES = {"RETURN_REQUESTED": "requested", "IN_PROGRESS": "in progress", "INSPECTION_COMPLETE": "inspected", "RETURN_FAILED": "failed"}
_PAID = {"PAID", "PARTIALLY_REFUNDED"}
_UNPAID = {"PENDING", "AUTHORIZED", "PARTIALLY_PAID", "EXPIRED"}


def _amount(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(str(value).split()[0].replace(",", ""))
    except (TypeError, ValueError, IndexError):
        return None


def _parse(stamp: Any) -> datetime | None:
    text = str(stamp or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        pass
    try:
        return parsedate_to_datetime(text)
    except (TypeError, ValueError, IndexError):
        return None


def _days_since(stamp: Any, now: float) -> float | None:
    when = _parse(stamp)
    if when is None:
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=UTC)
    days = (now - when.timestamp()) / 86400.0
    return days if days >= 0 else None


def _when(stamp: Any) -> str:
    when = _parse(stamp)
    return when.strftime("%-d %b") if when else ""


def _item_name(item: dict[str, Any]) -> str:
    return " ".join(p for p in (str(item.get("title") or ""), str(item.get("variant") or "")) if p and p.lower() != "default title")


def attention_for(order: dict[str, Any], *, now: float | None = None) -> list[dict[str, Any]]:
    """The lines, most serious first, at most six. Pure: the order read model in, words out."""
    # The rail's facts. Imported here so the context package stays free of the actions
    # package at import time (which imports this one).
    from app.actions.available import order_facts

    if not isinstance(order, dict):
        return []
    now = time.time() if now is None else float(now)
    f = order_facts(order)
    n = f["digits"] or str(order.get("order_number") or "").lstrip("#")
    money = order.get("money") if isinstance(order.get("money"), dict) else {}
    symbol = "£" if str(money.get("currency") or "GBP").upper() == "GBP" else ""
    total = _amount(order.get("total")) or _amount(money.get("total"))
    refunded = _amount(money.get("refunded")) or 0.0
    lines: list[dict[str, Any]] = []

    def add(kind: str, level: str, title: str, detail: str = "", say: str = "") -> None:
        lines.append({"kind": kind, "level": level, "title": title[:80], "detail": detail[:140], "say": say[:80]})

    # --- money
    if f["cancelled"] and total and refunded + 0.005 < total and f["payment"] in _PAID:
        add("refund", "red", "Cancelled but not refunded", f"{symbol}{total:.2f} paid, {symbol}{refunded:.2f} refunded", f"refund order {n}")
    if not f["cancelled"] and f["unfulfilled"] and f["payment"] in _UNPAID:
        add("payment", "amber", "Not paid yet", "Don't ship until it is paid")

    # --- age
    age = _days_since(order.get("placed_at"), now)
    if not f["cancelled"] and f["unfulfilled"] and f["payment"] in _PAID and age is not None and age >= AGING_AMBER_DAYS:
        add("shipping", "red" if age >= AGING_RED_DAYS else "amber", f"Unfulfilled for {int(age)} days", "Paid and still to ship", f"fulfil order {n}")

    # --- stock
    for item in (i for i in (order.get("items") or []) if isinstance(i, dict)):
        stock = item.get("stock") if isinstance(item.get("stock"), dict) else None
        if not stock or not stock.get("tracked", True):
            continue
        available = stock.get("available")
        if not isinstance(available, int) or isinstance(available, bool):
            continue
        if available < 0:
            add("stock", "red", f"Oversold: {_item_name(item)}", f"{-available} more sold than were in stock")
        elif available == 0 and (item.get("unfulfilled_quantity") or 0) > 0:
            add("stock", "amber", f"Out of stock: {_item_name(item)}", "Still to ship and none left to pick")

    # --- shipping
    fulfillments = [x for x in (order.get("fulfillments") or []) if isinstance(x, dict)]
    if f["shipped"] and fulfillments and not any(x.get("number") for x in fulfillments):
        add("shipping", "amber", "Shipped without tracking", "The customer has no tracking link")
    state = str(order.get("return_status") or "").upper()
    if state in _RETURN_STATES:
        add("return", "amber", f"Return {_RETURN_STATES[state]}", "Watch for the parcel before refunding")

    # --- email: what the customer wrote is evidence; the line says what it is about and
    # where it came from, and what the owner could say — never what the email said to do.
    email = order.get("email") if isinstance(order.get("email"), dict) else {}
    threads = [t for t in (email.get("threads") or []) if isinstance(t, dict)]
    from_customer = [t for t in threads if t.get("sender_match")]
    if from_customer:
        t = from_customer[0]
        text = f"{t.get('subject') or ''} {t.get('snippet') or ''}"
        who = f"from {t.get('from_email') or 'the customer'}" + (f", {_when(t.get('date'))}" if _when(t.get("date")) else "")
        provenance = f"{who} · {'verified sender' if t.get('verified_sender') else 'sender not verified'}"
        read = f"read the customer's email on order {n}"
        if _ADDRESS.search(text) and not f["shipped"] and not f["cancelled"]:
            add("email", "amber", "Customer emailed — mentions an address", f"{provenance} — check before shipping", read)
        elif _CANCEL.search(text) and not f["shipped"] and not f["cancelled"]:
            add("email", "amber", "Customer emailed — mentions cancelling", provenance, read)
        elif _REFUND.search(text):
            add("email", "amber", "Customer emailed — mentions a refund", provenance, read)
        elif _RETURN.search(text):
            add("email", "amber", "Customer emailed — mentions a return", provenance, read)
        else:
            add("email", "amber", f"Customer emailed: {str(t.get('subject') or '(no subject)')[:50]}", provenance, f"reply to the customer about order {n}")
    others = [t for t in threads if not t.get("sender_match")]
    if others:
        t = others[0]
        add("email", "amber", "Email about this order from someone else", f"from {t.get('from_email') or 'an unknown sender'} — not the customer on the order")

    # --- the customer
    history = order.get("history") if isinstance(order.get("history"), dict) else {}
    if history:
        other = [str(x) for x in (history.get("other_unfulfilled") or []) if x]
        if other:
            add("orders", "amber", f"{len(other)} other order{'s' if len(other) > 1 else ''} waiting to ship", ", ".join(other[:4]), "")
        count = history.get("orders")
        spent = _amount(history.get("spent"))
        first_at = str(history.get("first_order_at") or "")[:19]
        if count == 1 or (first_at and first_at == str(order.get("placed_at") or "")[:19]):
            add("customer", "green", "First order from this customer")
        elif (count or 0) >= REGULAR_ORDERS or (spent or 0.0) >= REGULAR_SPEND:
            add("customer", "green", "Regular customer", f"{count} orders, {symbol}{spent:,.0f} lifetime" if spent is not None else f"{count} orders")

    # --- what the Mac cannot see
    if age is not None and age > VISIBLE_DAYS:
        add("history", "amber", "Older than 60 days", "Email correlation covers the last 60 days; older mail is not shown")

    lines.sort(key=lambda line: _LEVELS.get(line["level"], 9))
    return lines[:MAX_LINES]
