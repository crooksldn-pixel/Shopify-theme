"""The email → order direction of the graph.

`app/context/order.py:correlate_threads` runs order → threads: given an order, which threads
are about it. Nothing ran the other way, so an email thread opened on the tablet showed its
words and hid its order (Phase 2, P0 #10): no money, no status, no link, and "check whether
they've emailed us about this" had to go to the model to rediscover what the Mac already held.

This is the reverse read, and it is deliberately a function over data the Mac ALREADY HOLDS —
the order cache's rows — so a presenter can call it without inventing a read of its own. Two
kinds of evidence are accepted, and only two:

  - an order number written in the thread (subject first, then the body), matched against a
    row's number;
  - the sender's address, matched EXACTLY against a row's customer email.

A name is not evidence: anyone can be called Sam. The answer carries how sure it is and why,
in words the tablet prints beside the link, because a wrong link on the thread the owner is
about to reply to is worse than no link at all.

    confident   a number in the thread is an order of the sender's; or the sender has exactly
                one recent order and nothing contradicts it
    possible    the sender has several recent orders (the newest three are offered); or a
                number matches an order the sender is not the customer of
    none        nothing matched, or the cache was cold

The window is sixty days, which is how far Shopify shows orders without read_all_orders and
how far the order → thread correlation looks.
"""

from __future__ import annotations

import re
import time
from datetime import datetime
from typing import Any

RECENT_DAYS = 60
MAX_POSSIBLE = 3
# Exactly four or five digits, not part of a longer run: a tracking number or a phone number
# has a five-digit stretch in it and is not an order number.
_NUMBER = re.compile(r"(?<![\dA-Za-z])#?(\d{4,5})(?!\d)")


def order_numbers_in(text: str) -> list[str]:
    """The order-shaped numbers in a piece of text, in order of appearance, deduplicated."""
    seen: list[str] = []
    for match in _NUMBER.finditer(text or ""):
        digits = match.group(1)
        if digits not in seen:
            seen.append(digits)
    return seen


def _digits_of(number: Any) -> str:
    return str(number or "").rsplit("-", 1)[-1].lstrip("#").strip()


def _placed_ts(row: dict[str, Any]) -> float:
    ts = row.get("ts")
    if isinstance(ts, (int, float)) and ts > 0:
        return float(ts)
    for key in ("placed_at", "created_at"):
        value = row.get(key)
        if not value:
            continue
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp()
        except ValueError:
            continue
    return 0.0


def _customer_of(row: dict[str, Any]) -> tuple[str, str, str]:
    """(email, id, name) whichever shape the row is in: the cache's nested `customer`, or the
    flat `customer_email`/`customer_id`/`customer_name` a read model carries."""
    nested = row.get("customer") if isinstance(row.get("customer"), dict) else {}
    email = str(row.get("customer_email") or nested.get("email") or "").strip().lower()
    cid = str(row.get("customer_id") or nested.get("customer_id") or "").strip()
    name = str(row.get("customer_name") or nested.get("name") or "").strip()
    return email, cid, name


def _thread_text(thread: dict[str, Any]) -> tuple[str, str, set[str]]:
    """(subjects, bodies, sender addresses) from a thread in either shape the tools return:
    a read thread with `messages`, or a listing summary with `from_email` and `snippet`."""
    subjects: list[str] = []
    bodies: list[str] = []
    senders: set[str] = set()
    for message in thread.get("messages") or []:
        if not isinstance(message, dict):
            continue
        subjects.append(str(message.get("subject") or ""))
        bodies.append(str(message.get("body") or message.get("snippet") or ""))
        sender = str(message.get("from_email") or "").strip().lower()
        if sender:
            senders.add(sender)
    if thread.get("subject"):
        subjects.append(str(thread["subject"]))
    if thread.get("snippet"):
        bodies.append(str(thread["snippet"]))
    sender = str(thread.get("from_email") or "").strip().lower()
    if sender:
        senders.add(sender)
    return " ".join(subjects), " ".join(bodies), senders


def _linked(row: dict[str, Any]) -> dict[str, Any]:
    email, cid, name = _customer_of(row)
    return {
        "order_id": str(row.get("order_id") or ""),
        "order_number": str(row.get("order_number") or ""),
        "total": row.get("total"),
        "currency": str(row.get("currency") or ""),
        "fulfillment": str(row.get("fulfillment") or ""),
        "customer_name": name,
        "customer_id": cid,
        "placed_at": str(row.get("placed_at") or row.get("created_at") or ""),
    }


def linked_orders_for_thread(thread: dict[str, Any], *, rows: list[dict[str, Any]], clock=time.time) -> dict[str, Any]:
    """Which orders this thread is about, from the rows the Mac holds. See the module docstring
    for the three answers; nothing here reads a source, and nothing here guesses from a name."""
    if not isinstance(thread, dict):
        thread = {}
    subjects, bodies, senders = _thread_text(thread)
    now = float(clock())
    since = now - RECENT_DAYS * 86400
    rows = [r for r in (rows or []) if isinstance(r, dict) and r.get("order_id")]
    by_digits: dict[str, dict[str, Any]] = {}
    for row in rows:
        digits = str(row.get("digits") or _digits_of(row.get("order_number")))
        if digits and digits not in by_digits:
            by_digits[digits] = row
    # Every row of the sender's, newest first; `recent` is what "one recent order" counts.
    of_sender = sorted([r for r in rows if _customer_of(r)[0] in senders], key=_placed_ts, reverse=True) if senders else []
    recent = [r for r in of_sender if _placed_ts(r) >= since]
    customer = None
    if of_sender:
        _, cid, name = _customer_of(of_sender[0])
        if cid:
            customer = {"customer_id": cid, "name": name}

    provenance: list[str] = []
    in_subject = order_numbers_in(subjects)
    in_body = [n for n in order_numbers_in(bodies) if n not in in_subject]
    mentioned = [(n, "subject") for n in in_subject] + [(n, "body") for n in in_body]
    # A number the sender's own order carries: the strongest link there is.
    theirs = [(n, where) for n, where in mentioned if n in by_digits and _customer_of(by_digits[n])[0] in senders]
    if theirs:
        linked = []
        for n, where in theirs:
            provenance.append(f"order number {n} in the {where}")
            if by_digits[n] not in linked:
                linked.append(by_digits[n])
        provenance.append("sender is the customer on that order")
        return {"linked": [_linked(r) for r in linked[:MAX_POSSIBLE]], "confidence": "confident", "provenance": provenance, "customer": customer}
    # A number that belongs to somebody else's order is a mention, not a link — it is offered
    # as possible so the owner can see it, and never as the thread's order.
    others = [(n, where) for n, where in mentioned if n in by_digits]
    if len(recent) == 1:
        provenance.append("sender is the customer on one recent order")
        for n, _ in others:
            provenance.append(f"number {n} is mentioned but the sender is not its customer")
        return {"linked": [_linked(recent[0])], "confidence": "confident", "provenance": provenance, "customer": customer}
    if len(recent) > 1:
        provenance.append(f"sender is the customer on {len(recent)} recent orders")
        return {"linked": [_linked(r) for r in recent[:MAX_POSSIBLE]], "confidence": "possible", "provenance": provenance, "customer": customer}
    if others:
        linked = []
        for n, where in others:
            provenance.append(f"number {n} in the {where}, but the sender is not its customer")
            if by_digits[n] not in linked:
                linked.append(by_digits[n])
        return {"linked": [_linked(r) for r in linked[:MAX_POSSIBLE]], "confidence": "possible", "provenance": provenance, "customer": customer}
    if of_sender:
        # Older than the window: the customer is known, the order is not recent enough to link.
        provenance.append(f"sender is a customer, but their orders are older than {RECENT_DAYS} days")
    elif senders:
        provenance.append("sender matches no recent order")
    else:
        provenance.append("no sender address on the thread")
    if not mentioned:
        provenance.append("no order number in the thread")
    return {"linked": [], "confidence": "none", "provenance": provenance, "customer": customer}
