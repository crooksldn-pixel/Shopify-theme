"""Which changes make sense for this order, decided on the Mac from the order's own state
and from what the store has granted — never by the model, never by the tablet.

The rail on the order card shows only what is here. An action that would fail is not a
dimmed button: it is either absent, or present with the one reason it cannot be done when
the owner is likely to ask for it ("Cancel — already shipped"). A change whose tool is not
built, or whose scope the store has not granted, never becomes a chip.
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from typing import Any

from app.context.order import order_digits

# The most a card offers. More than three is a menu, and this is not a menu.
MAX_ENABLED = 3

SHIPPED = frozenset({"FULFILLED"})
PART_SHIPPED = frozenset({"PARTIALLY_FULFILLED"})
PAID = frozenset({"PAID", "PARTIALLY_REFUNDED"})
# What an order in each state needs first. The note is always offered and never counted.
_NEED_OPEN = ("fulfil", "address", "cancel", "refund", "email")
_NEED_CANCELLED = ("refund", "email", "fulfil", "address", "cancel")
_NEED_SHIPPED = ("refund", "email", "address", "fulfil", "cancel")


@dataclass(frozen=True, slots=True)
class AvailableAction:
    id: str            # "cancel", "refund" … the tablet's own vocabulary
    label: str         # the word on the chip
    operation: str     # the write's operation name, as the ledger and the capability call it
    risk: str          # "amber" | "red"
    enabled: bool
    reason: str        # why not, when not; empty when enabled
    instruction: str   # what the owner says (or the chip primes) to ask for it
    mode: str = "ask"  # "ask": the chip primes the hold with the words; nothing is staged by a tap
    # The spoken control this chip arms, when there is one: a key of commands.SPOKEN_CONTROLS.
    # Tapping such a chip binds what the NEXT SENTENCE is about, so the words that follow are
    # applied to this record and to nothing else. The mapping lives on the Mac and travels to
    # the tablet so the tablet never has to invent one; a chip with no family primes the words
    # and binds nothing, which is what every chip did before.
    family: str = ""

    def public(self) -> dict[str, Any]:
        return asdict(self)


def _amount(value: Any) -> float | None:
    try:
        return float(str(value).split()[0])
    except (TypeError, ValueError, IndexError, AttributeError):
        return None


def order_facts(order: dict[str, Any]) -> dict[str, Any]:
    """The few facts every rule turns on, read once from the order read model."""
    money = order.get("money") if isinstance(order.get("money"), dict) else {}
    status = str(order.get("fulfillment") or "").upper()
    items = [i for i in (order.get("items") or []) if isinstance(i, dict)]
    unfulfilled = any((i.get("unfulfilled_quantity") or 0) > 0 for i in items) if any("unfulfilled_quantity" in i for i in items) else status in {"UNFULFILLED", "PARTIALLY_FULFILLED", "ON_HOLD", "SCHEDULED"}
    total = _amount(order.get("total")) or _amount(money.get("total"))
    refunded = _amount(money.get("refunded")) or 0.0
    return {
        "cancelled": bool(order.get("cancelled_at")),
        "shipped": status in SHIPPED or any(str(f.get("status") or "").upper() == "SUCCESS" for f in (order.get("fulfillments") or []) if isinstance(f, dict)),
        "part_shipped": status in PART_SHIPPED,
        "unfulfilled": unfulfilled,
        "payment": str(order.get("payment") or "").upper(),
        "refundable": bool(order.get("refundable")) and (total is None or refunded < total),
        "refunded_all": total is not None and refunded >= total > 0,
        "has_address": isinstance(order.get("shipping_address"), dict) and bool(order["shipping_address"].get("lines") or order["shipping_address"].get("city")),
        "has_email": bool(order.get("customer_email")),
        "digits": order_digits(order.get("order_number")),
    }


def available_actions(order: dict[str, Any], capabilities: dict[str, dict[str, Any]] | None) -> list[dict[str, Any]]:
    """The rail for one order. `capabilities` is what the Mac can do right now, per
    operation (app/runtime.py): a change without a capability entry is not built and is
    not offered; one that is blocked is not offered either — the settings sheet says why."""
    caps = capabilities or {}
    f = order_facts(order)
    n = f["digits"] or str(order.get("order_number") or "").lstrip("#")
    candidates: list[AvailableAction] = []

    def add(id_: str, label: str, operation: str, risk: str, ok: bool, reason: str, instruction: str,
            family: str = "") -> None:
        cap = caps.get(operation)
        if not isinstance(cap, dict) or cap.get("state") not in ("ready", "unknown"):
            return   # not built, switched off, or blocked: not a chip
        candidates.append(AvailableAction(id_, label, operation, risk, ok, "" if ok else reason, instruction,
                                          family=family))

    add("note", "Note", "order_note_append", "amber", True, "", f"Add a note to order {n}", family="order.add_note")
    if f["cancelled"]:
        cancel_reason = "already cancelled"
    elif f["shipped"]:
        cancel_reason = "already shipped"
    elif f["part_shipped"]:
        cancel_reason = "partly shipped"
    else:
        cancel_reason = ""
    add("cancel", "Cancel", "order_cancel", "red", not cancel_reason, cancel_reason, f"Cancel order {n}")
    if f["cancelled"]:
        address_reason = "cancelled"
    elif f["shipped"] or f["part_shipped"]:
        address_reason = "already shipped"
    elif not f["has_address"]:
        address_reason = "no shipping address"
    else:
        address_reason = ""
    add("address", "Address", "order_shipping_address_set", "red", not address_reason, address_reason,
        f"Change the address on order {n}", family="order.change_address")
    if f["refunded_all"]:
        refund_reason = "fully refunded"
    elif f["payment"] not in PAID or not f["refundable"]:
        refund_reason = "nothing to refund" if f["payment"] in {"REFUNDED", "VOIDED"} or (f["payment"] in PAID and not f["refundable"]) else "not paid"
    else:
        refund_reason = ""
    add("refund", "Refund", "refund_create", "red", not refund_reason, refund_reason, f"Refund order {n}")
    if f["cancelled"]:
        fulfil_reason = "cancelled"
    elif not f["unfulfilled"]:
        fulfil_reason = "already shipped"
    elif f["payment"] not in PAID and not order.get("fully_paid"):
        fulfil_reason = "not paid"
    else:
        fulfil_reason = ""
    add("fulfil", "Fulfil", "fulfillment_create", "red", not fulfil_reason, fulfil_reason, f"Fulfil order {n}")
    # The chip primes a draft (the safe first step, a tap); sending is a second ask, a hold.
    add("email", "Email", "gmail_draft_new", "amber", f["has_email"], "no email address", f"Email the customer about order {n}")

    order_of_need = _NEED_CANCELLED if f["cancelled"] else _NEED_OPEN if f["unfulfilled"] else _NEED_SHIPPED
    # What the order's own context says comes first: a customer who has written, an order
    # that has waited too long. Decided here from the read model, never by the model.
    first = context_rank(order, f)
    enabled_all = [a for a in candidates if a.enabled]
    note = [a for a in enabled_all if a.id == "note"]
    rest = sorted((a for a in enabled_all if a.id != "note"), key=lambda a: (first.index(a.id) if a.id in first else len(first), order_of_need.index(a.id) if a.id in order_of_need else 99))
    enabled = note + rest[:MAX_ENABLED]
    # A disabled chip is shown only where the owner would otherwise ask and be told no.
    disabled = [a for a in candidates if not a.enabled and a.id in ("cancel", "refund", "fulfil") and a.reason][:2]
    return [a.public() for a in enabled + disabled]


def available_email_actions(thread: dict[str, Any], capabilities: dict[str, dict[str, Any]] | None,
                            *, row_actions: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """The rail for one email thread. The same shape as the order rail, for the same reason:
    the tablet renders what it is given and never decides what a chip means.

    Two kinds of chip share it. Reply arms the microphone — it binds `email.reply` to this
    thread so the sentence that follows is the reply, and nothing is staged by the tap. Archive
    is a row action (app/actions/rows.py): a tap asks the Mac to PREPARE the change, and the
    card that comes back still waits for a gesture. Both are gated by what this Mac can do.

    Until this existed, `rail()` was called from exactly one place — the order card — so an
    email on the tablet had no controls at all: Reply, Rewrite and Archive were registered on
    the Mac and reachable only by a spoken sentence.
    """
    caps = capabilities or {}
    if not str(thread.get("thread_id") or ""):
        return []
    out: list[AvailableAction] = []
    draft = caps.get("gmail_draft_reply")
    if isinstance(draft, dict) and draft.get("state") in ("ready", "unknown"):
        out.append(AvailableAction("reply", "Reply", "gmail_draft_reply", "amber", True, "",
                                   "Reply to this email", family="email.reply"))
    public = [a.public() for a in out]
    # The row actions come already gated (actions_for checks the write tool is registered and
    # changes are on); they are appended as they are, so Archive on the rail is the same
    # action as Archive beside a row, resolved by the same table.
    for a in row_actions or []:
        if isinstance(a, dict) and a.get("id"):
            public.append(dict(a))
    return public[:6]


def context_rank(order: dict[str, Any], facts: dict[str, Any] | None = None) -> list[str]:
    """The chips the order's context puts first, in order: a customer's email that mentions
    cancelling puts the cancel first and the reply beside it; one that mentions an address
    puts the address first; a refund or a return puts the refund first; any email from the
    customer puts the reply first; an order that has waited too long puts the fulfilment
    first. Pure words and dates from the read model; the rail's rules still decide what is
    enabled at all."""
    from app.context.attention import (
        _ADDRESS,
        _CANCEL,
        _REFUND,
        _RETURN,
        AGING_AMBER_DAYS,
        _days_since,
    )

    f = facts or order_facts(order)
    out: list[str] = []
    email = order.get("email") if isinstance(order.get("email"), dict) else {}
    threads = [t for t in (email.get("threads") or []) if isinstance(t, dict) and t.get("sender_match")]
    if threads:
        t = threads[0]
        text = f"{t.get('subject') or ''} {t.get('snippet') or ''}"
        open_order = not f["shipped"] and not f["cancelled"]
        if _CANCEL.search(text) and open_order:
            out.append("cancel")
        elif _ADDRESS.search(text) and open_order:
            out.append("address")
        elif _REFUND.search(text) or _RETURN.search(text):
            out.append("refund")
        out.append("email")
    age = _days_since(order.get("placed_at"), time.time())
    if not f["cancelled"] and f["unfulfilled"] and f["payment"] in PAID and age is not None and age >= AGING_AMBER_DAYS and "fulfil" not in out:
        out.append("fulfil")
    return out
