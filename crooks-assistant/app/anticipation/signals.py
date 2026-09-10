"""Turning what happened into a `Signal` — the shape of the work, never the work itself.

One function per place the owner does something the layer can learn from, and one rule they all
keep: the FEATURES are the privacy-minimised description of the record (unfulfilled, going
abroad, three weeks old, an unanswered email on it), and the ids travel separately because a
prediction needs them to read anything and the learned table must never see them.

Reading an order's shape is defensive on purpose: these dictionaries come from the order cache,
the hydrator, a tool result or memory, and a missing key must produce a poorer signal rather
than a failed request.
"""

from __future__ import annotations

import time
from typing import Any

from app.anticipation.models import Signal

# Older than this and the order is "old" — the shape in the brief's own example (§19).
OLD_DAYS = 14.0
# Over this, in the store's currency, and it is worth a different amount of care.
HIGH_VALUE = 250.0
# The domestic country. CROOKS is a London shop; everything else is international.
HOME = "GB"


def order_features(order: dict[str, Any] | None, *, extension: dict[str, Any] | None = None) -> tuple[str, ...]:
    """The shape of an order, in allow-listed words."""
    order = order if isinstance(order, dict) else {}
    extension = extension if isinstance(extension, dict) else {}
    out: list[str] = []
    fulfillment = str(order.get("fulfillment") or "").upper()
    if fulfillment in ("UNFULFILLED", "ON_HOLD", "SCHEDULED"):
        out.append("unfulfilled")
    elif fulfillment == "PARTIALLY_FULFILLED":
        out.append("partial")
    elif fulfillment == "FULFILLED":
        out.append("fulfilled")
    address = order.get("shipping_address") if isinstance(order.get("shipping_address"), dict) else {}
    country = str(address.get("country_code") or order.get("country_code") or "").upper()
    if country:
        out.append("domestic" if country == HOME else "international")
    placed = _age_days(order)
    if placed is not None:
        out.append("old" if placed >= OLD_DAYS else "recent")
    total = _money(order.get("total"))
    if total is not None and total >= HIGH_VALUE:
        out.append("high_value")
    email = extension.get("email") if extension.get("email") is not None else order.get("email")
    if isinstance(email, dict):
        # The inbox part is a dictionary whether or not there is anything in it — "available"
        # and a list — so what counts is a CORRELATED thread, not the part's presence. Read the
        # part instead of the threads and every order in the shop has email on it.
        threads = [t for t in (email.get("threads") or []) if isinstance(t, dict)]
        out.append("has_email" if threads else "no_email")
        if any(t.get("sender_match") and (t.get("waiting_since") or t.get("awaiting_reply") or t.get("unanswered"))
               for t in threads):
            out.append("inbound_unanswered")
    elif email is None:
        out.append("no_email")
    tracking = order.get("tracking") or [f.get("tracking") for f in order.get("fulfillments") or [] if isinstance(f, dict)]
    out.append("tracked" if any(tracking or ()) else "untracked")
    return tuple(dict.fromkeys(out))


def for_order(
    order_id: str, order: dict[str, Any] | None, *, session: Any, branch: Any = None,
    event: str = "order_opened", extension: dict[str, Any] | None = None,
) -> Signal:
    """The signal for an order the owner is now looking at."""
    order = order if isinstance(order, dict) else {}
    ids = {"order_id": str(order_id or order.get("order_id") or "")}
    customer = order.get("customer") if isinstance(order.get("customer"), dict) else {}
    customer_id = str(order.get("customer_id") or customer.get("customer_id") or "")
    if customer_id:
        ids["customer_id"] = customer_id
    address = str(order.get("customer_email") or customer.get("email") or "").strip().lower()
    if "@" in address:
        ids["email"] = address
    # The thread on the order, when the inbox part has landed: what a reply would have to read,
    # and what the tablet's drilldown into it reads too.
    email = (extension or {}).get("email") if isinstance((extension or {}).get("email"), dict) else (
        order.get("email") if isinstance(order.get("email"), dict) else {}
    )
    thread = str((email or {}).get("thread_id") or "")
    if not thread:
        threads = [t for t in ((email or {}).get("threads") or []) if isinstance(t, dict)]
        # "thread_id" from the correlated part, "id" from the raw Gmail shape: both appear,
        # depending on which layer the dictionary came through.
        thread = str(threads[0].get("thread_id") or threads[0].get("id") or "") if threads else ""
    if thread:
        ids["thread_id"] = thread
    features = list(order_features(order, extension=extension))
    neighbours = neighbours_of(session, branch)
    if neighbours:
        features.append("in_set")
    return Signal(
        event=event, session_id=str(getattr(session, "session_id", "") or ""),
        branch_id=str(getattr(branch, "branch_id", "") or ""),
        login=str(getattr(session, "login", "") or ""),
        kind="order", ref=ids["order_id"], features=tuple(features), ids=ids, neighbours=neighbours,
    )


def neighbours_of(session: Any, branch: Any) -> tuple[str, ...]:
    """The records either side of the cursor in the set being worked through — the next one
    first, because Next is the gesture that happens.

    Nothing is read here and nothing is issued: these are refs the conversation already holds,
    and a prediction about one still goes through the gate like any other read.
    """
    workflow = getattr(branch, "workflow", None)
    if workflow is None:
        return ()
    try:
        from app.analytics import sets as working_sets

        held = working_sets.get(session, str(getattr(workflow, "set_id", "") or ""))
    except Exception:  # noqa: BLE001 — no sets held, no neighbours
        return ()
    if held is None:
        return ()
    # In ORDER. `members_by_id` hands back a frozenset — fine for the permission check it
    # exists for, and useless here: the cursor is an index, so a set read out of order
    # predicted the wrong record and the guess was wasted every time the hash said so.
    ordered = list(held.members)
    if not ordered:
        return ()
    cursor = int(getattr(workflow, "cursor", 0) or 0)
    out: list[str] = []
    if 0 <= cursor + 1 < len(ordered):
        out.append(ordered[cursor + 1])
    if 0 <= cursor - 1 < len(ordered):
        out.append(ordered[cursor - 1])
    return tuple(out)


def _age_days(order: dict[str, Any]) -> float | None:
    if isinstance(order.get("age_days"), (int, float)):
        return float(order["age_days"])
    placed = order.get("placed_at") or order.get("created_at")
    if not placed:
        return None
    text = str(placed).replace("Z", "+00:00")
    try:
        from datetime import datetime

        when = datetime.fromisoformat(text)
    except ValueError:
        return None
    stamp = when.timestamp() if when.tzinfo is not None else when.replace(tzinfo=None).timestamp()
    return max(0.0, (time.time() - stamp) / 86400.0)


def _money(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value or "").strip()
    if not text:
        return None
    kept = "".join(ch for ch in text if ch.isdigit() or ch in ".-")
    try:
        return float(kept)
    except ValueError:
        return None
