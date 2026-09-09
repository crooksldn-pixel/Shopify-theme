"""Which changes make sense for this order, decided on the Mac from the order's own state
and from what the store has granted — never by the model, never by the tablet.

The rail on the order card shows only what is here. An action that would fail is not a
dimmed button: it is either absent, or present with the one reason it cannot be done when
the owner is likely to ask for it ("Cancel — already shipped"). A change whose tool is not
built, or whose scope the store has not granted, never becomes a chip.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from app.context.order import order_digits

# The most a card offers. More than three is a menu, and this is not a menu.
MAX_ENABLED = 3

SHIPPED = frozenset({"FULFILLED"})
PART_SHIPPED = frozenset({"PARTIALLY_FULFILLED"})
PAID = frozenset({"PAID", "PARTIALLY_REFUNDED", "PARTIALLY_PAID"})


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

    def add(id_: str, label: str, operation: str, risk: str, ok: bool, reason: str, instruction: str) -> None:
        cap = caps.get(operation)
        if not isinstance(cap, dict) or cap.get("state") not in ("ready", "unknown"):
            return   # not built, switched off, or blocked: not a chip
        candidates.append(AvailableAction(id_, label, operation, risk, ok, "" if ok else reason, instruction))

    add("note", "Note", "order_note_append", "amber", True, "", f"Add a note to order {n}")
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
    add("address", "Address", "order_shipping_address_set", "red", not address_reason, address_reason, f"Change the address on order {n}")
    if f["refunded_all"]:
        refund_reason = "fully refunded"
    elif f["payment"] not in PAID or not f["refundable"]:
        refund_reason = "nothing to refund" if f["payment"] in {"REFUNDED", "VOIDED"} else "not paid"
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
    add("email", "Email", "gmail_send_reply", "amber", f["has_email"], "no email address", f"Email the customer about order {n}")

    enabled = [a for a in candidates if a.enabled][:MAX_ENABLED]
    # A disabled chip is shown only where the owner would otherwise ask and be told no.
    disabled = [a for a in candidates if not a.enabled and a.id in ("cancel", "refund", "fulfil") and a.reason][:2]
    return [a.public() for a in enabled + disabled]
