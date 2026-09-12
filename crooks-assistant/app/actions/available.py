"""Which changes make sense for this order, decided on the Mac from the order's own state
and from what the store has granted — never by the model, never by the tablet.

The rail on the order card shows only what is here. An action that would fail is not a
dimmed button: it is either absent, or present with the one reason it cannot be done when
the owner is likely to ask for it ("Cancel — already shipped"). A change whose tool is not
built, or whose scope the store has not granted, never becomes a chip.

WHAT THE LIVE SESSION CHANGED (D-11). Eight actions were rendered enabled across ten
minutes — reply 24 times, archive 24, note 5, refund 3, email 3, fulfil 2, address 2,
cancel 2 — and **not one was used**. Two things were wrong with that rail, and both are
fixed here rather than on the tablet:

* **Everything was the same size.** Note led every order card whatever the order was, and a
  disabled Fulfil sat beside an enabled Refund at the same weight. So every action now
  carries a `priority`: at most `MAX_PRIMARY` are drawn full-size, and the rest — the
  fallbacks, and every disabled one — sit behind the rail's disclosure.
* **A chip that only primes a sentence is not a control.** `mode="open"` is the third kind:
  the chip carries a semantic command and its arguments, both built here, and a tap posts
  them and gets a screen back. Reply on an email thread is the first of them — the owner
  tapped it twenty-four times expecting a reply he could type, and got a dock label. An
  `ask` chip is unchanged and must still name the spoken control it arms, or a tap on it
  says nothing the owner can see.
"""

from __future__ import annotations

import re
import time
from dataclasses import asdict, dataclass
from typing import Any

from app.context.order import order_digits

# The most a card offers, and the most it offers at FULL weight.
#
# PHASE 5 · §25, AND WHAT THE AUDIT ACTUALLY FOUND. The live session's numbers are the
# starting point, not the conclusion: the rail exposed `fulfil`, `address`, `cancel` and
# `note` on EVERY order card — four enabled actions, four exposures each, sixteen
# chip-exposures in one evening — and exactly one tap landed on any of them (`address`,
# once). "Exposed but never used: cancel, fulfil, note."
#
# The obvious answer is to cut the rail to two chips with one at full weight. It was tried,
# and it is WRONG, for reasons the browser gate and the golden scenarios state plainly:
#
#   * `note` is the only `ask`-mode chip on an order that carries a `family`. Tapping it is
#     the ONLY WAY TO BIND THE MICROPHONE TO THIS ORDER BY TOUCH (§20 — voice is intent,
#     touch is precision, and they are two controls; D-11 is the whole of that story).
#     Deleting it deletes a capability, not a decoration. It stays, and it stays LAST and
#     never at full weight — which is what its five renders and nought taps do justify.
#   * on a real order — unfulfilled, paid, the customer has written in, and the address
#     needs correcting — the card genuinely owes FOUR things: the reply the customer is
#     waiting on, the shipping the order is waiting on, the address as something to type,
#     and the microphone. Two slots cannot hold them, and `address` is the one chip the
#     owner did use. Cutting to two dropped it (`scripts/browser/email.js`: "an order that
#     has not shipped offers its address as something to type").
#
# So the number of chips is not the defect. Their WEIGHT and their RELEVANCE are:
#
#   MAX_ENABLED = 3   plus the note, which is always offered and never counted
#   MAX_PRIMARY = 2   chosen by the order's own context — "the reply leads and the
#                     fulfilment is beside it" — and everything else disclosed
#
# and the removal the evidence does support is one chip rather than a quota: see `cancel`
# below. §25's five questions have five answers, and "remove it" is only one of them.
MAX_ENABLED = 3
MAX_PRIMARY = 2

# What the owner calls an order. Never an id: §26 — "Order #1962", never
# `gid://shopify/Order/…`, and a technical id only on a debug surface. This is not
# cosmetic — an `ask` chip's instruction is the sentence the owner is primed to SAY, and
# "Fulfil order gid://shopify/Order/1938" is not a sentence anybody says.
_HUMAN_NUMBER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9\-_ ]{0,15}$")

def order_words(order: dict[str, Any]) -> str:
    """The order as the office says it — "1938" — or nothing at all.

    `order_digits` already answers this for every name Shopify produces. What was wrong was
    the FALLBACK behind it: `order_number` was passed through raw, so a read model carrying
    only the Shopify id put `gid://shopify/Order/1938` into four chip instructions, and one
    carrying no number at all produced "Fulfil order " — a control primed with a sentence
    that names no record. Both are refused here, and a chip that cannot name what it is
    about is not offered at all (see `available_actions`).
    """
    digits = order_digits(order.get("order_number"))
    if digits:
        return digits
    raw = str(order.get("order_number") or "").strip().lstrip("#").strip()
    return raw if raw and "://" not in raw and _HUMAN_NUMBER.match(raw) else ""


def order_phrase(order: dict[str, Any]) -> str:
    """How a sentence refers to this order: "order 1938", or "this order" when the read model
    has no human name for it. Never "order " with nothing after it — which is what four chip
    instructions said on an order whose number had not been read yet."""
    n = order_words(order)
    return f"order {n}" if n else "this order"


SHIPPED = frozenset({"FULFILLED"})
PART_SHIPPED = frozenset({"PARTIALLY_FULFILLED"})
PAID = frozenset({"PAID", "PARTIALLY_REFUNDED"})
# What an order in each state needs first.
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
    # Three kinds of chip, and the tablet renders all three the same way:
    #   "ask"    the chip primes the hold with the words and arms `family`; nothing is staged
    #   "stage"  a row action (app/actions/rows.py): the tap asks the Mac to PREPARE the change
    #   "open"   the tap posts `command` with `args` and a screen comes back — a composer, a
    #            workspace. Nothing is staged by it either, and nothing in `args` is an
    #            argument of a change: they are identities this Mac issued.
    mode: str = "ask"
    # The spoken control this chip arms, when there is one: a key of commands.SPOKEN_CONTROLS.
    # Tapping such a chip binds what the NEXT SENTENCE is about, so the words that follow are
    # applied to this record and to nothing else. The mapping lives on the Mac and travels to
    # the tablet so the tablet never has to invent one; a chip with no family primes the words
    # and binds nothing, which is what every chip did before.
    family: str = ""
    # For "open": the semantic command a tap posts, and its arguments as a query string. Both
    # built here from ids this Mac issued — the tablet forwards them and cannot compose one of
    # its own (app/routes/command.py bounds what a command may be posted).
    command: str = ""
    args: str = ""
    # "primary" is drawn at full weight; "secondary" sits behind the rail's disclosure. The
    # entity's own state decides which — never the model, never the tablet.
    priority: str = "primary"

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
    n = order_words(order)
    phrase = order_phrase(order)
    # The id the "open" chips carry, when the read model has one. A chip that cannot name its
    # record cannot post a command about it, and falls back to priming the words.
    order_id = str(order.get("order_id") or "")
    candidates: list[AvailableAction] = []

    def add(id_: str, label: str, operation: str, risk: str, ok: bool, reason: str, instruction: str,
            family: str = "", mode: str = "ask", command: str = "", args: str = "") -> None:
        cap = caps.get(operation)
        if not isinstance(cap, dict) or cap.get("state") not in ("ready", "unknown"):
            return   # not built, switched off, or blocked: not a chip
        if mode == "ask" and not n:
            # An "ask" chip IS its instruction: the tap primes that sentence and nothing
            # else. With no human name for the order the sentence cannot name the record, so
            # there is no control to draw — §18, a control is not offered before what it
            # acts on is known to exist. An "open" chip carries the id itself and is
            # unaffected, because a tap on it reaches a screen rather than a microphone.
            return
        candidates.append(AvailableAction(id_, label, operation, risk, ok, "" if ok else reason, instruction,
                                          family=family, mode=mode, command=command, args=args))

    # NOTE. Five renders, nought taps, and it was the FIRST chip on every order card whatever
    # the order was — so Phase 4 sent it last and behind the disclosure, and that is correct
    # and stays. It is not REMOVED, and the §25 question it passes is "is there a better
    # contextual location": there is not. It is the only chip on an order that both primes a
    # sentence and names the spoken control it arms (`family`), which makes it the one way to
    # bind the microphone to THIS order with a thumb. A chip nobody taps is still the only
    # door to a capability.
    add("note", "Note", "order_note_append", "amber", True, "", f"Add a note to {phrase}", family="order.add_note")
    if f["cancelled"]:
        cancel_reason = "already cancelled"
    elif f["shipped"]:
        cancel_reason = "already shipped"
    elif f["part_shipped"]:
        cancel_reason = "partly shipped"
    else:
        cancel_reason = ""
    add("cancel", "Cancel", "order_cancel", "red", not cancel_reason, cancel_reason, f"Cancel {phrase}")
    if f["cancelled"]:
        address_reason = "cancelled"
    elif f["shipped"] or f["part_shipped"]:
        address_reason = "already shipped"
    elif not f["has_address"]:
        address_reason = "no shipping address"
    else:
        address_reason = ""
    # Address OPENS the address, with the parts of the current one already in the boxes
    # (`app/families/address.py`). A postcode is the worst thing in the shop to dictate —
    # "BS7 9AL" and "BS7 8AL" are both valid and one of them is a stranger's house — and
    # until this chip opened something, correcting one was a sentence into a microphone that
    # had already produced four recordings under 150 ms. The spoken control rides along.
    add("address", "Address", "order_shipping_address_set", "red", not address_reason, address_reason,
        f"Change the address on {phrase}", family="order.change_address",
        mode="open" if order_id else "ask",
        command="address.open" if order_id else "",
        args=f"order_id={order_id}" if order_id else "")
    if f["refunded_all"]:
        refund_reason = "fully refunded"
    elif f["payment"] not in PAID or not f["refundable"]:
        refund_reason = "nothing to refund" if f["payment"] in {"REFUNDED", "VOIDED"} or (f["payment"] in PAID and not f["refundable"]) else "not paid"
    else:
        refund_reason = ""
    add("refund", "Refund", "refund_create", "red", not refund_reason, refund_reason, f"Refund {phrase}")
    if f["cancelled"]:
        fulfil_reason = "cancelled"
    elif not f["unfulfilled"]:
        fulfil_reason = "already shipped"
    elif f["payment"] not in PAID and not order.get("fully_paid"):
        fulfil_reason = "not paid"
    else:
        fulfil_reason = ""
    add("fulfil", "Fulfil", "fulfillment_create", "red", not fulfil_reason, fulfil_reason, f"Fulfil {phrase}")
    # Email OPENS a composer addressed to the customer, so the owner can type or dictate it
    # (`compose.to_customer`). It was an "ask" chip that primed a sentence, rendered three
    # times in the live session and used nought — a chip named Email that produced a dock
    # label rather than somewhere to write is the whole of D-11 in one control. The address
    # is not on the chip: the command carries the ORDER, and the Mac reads the recipient off
    # its own copy of it.
    add("email", "Email", "gmail_draft_new", "amber", f["has_email"], "no email address",
        f"Email the customer about {phrase}",
        mode="open" if order_id else "ask",
        command="compose.to_customer" if order_id else "",
        args=f"order_id={order_id}" if order_id else "")

    order_of_need = _NEED_CANCELLED if f["cancelled"] else _NEED_OPEN if f["unfulfilled"] else _NEED_SHIPPED
    # What the order's own context says comes first: a customer who has written, an order
    # that has waited too long. Decided here from the read model, never by the model.
    first = context_rank(order, f)
    enabled_all = [a for a in candidates if a.enabled]
    # The note is always offered and never takes one of the three places (see above).
    note = [a for a in enabled_all if a.id == "note"]

    # CANCEL GOES LAST UNLESS THE ORDER ITSELF ASKS FOR IT — and on any order with something
    # else to offer, last means off the card. This is the removal §25's evidence supports:
    # two renders, nought taps, and it is the reddest, least reversible thing on the rail.
    # An order needs cancelling because a PERSON said so, which `context_rank` already reads
    # out of the customer's own email; nothing about an order's state asks for it by itself.
    #
    # Ranked rather than filtered, deliberately: a Mac whose only granted write is the cancel
    # still offers it (there is nothing else to offer), and a cancel that CANNOT be done is
    # untouched by this and still appears with its one reason (§19 — the owner who would ask
    # is told no).
    def rank(a: AvailableAction) -> tuple[int, int, int]:
        return (
            first.index(a.id) if a.id in first else len(first),
            1 if a.id == "cancel" and "cancel" not in first else 0,
            order_of_need.index(a.id) if a.id in order_of_need else 99,
        )

    rest = sorted((a for a in enabled_all if a.id != "note"), key=rank)
    # A disabled chip is shown only where the owner would otherwise ask and be told no.
    disabled = [a for a in candidates if not a.enabled and a.id in ("cancel", "refund", "fulfil") and a.reason][:2]
    # THE NOTE IS WEIGHED SEPARATELY, and that is the fix rather than a detail: it used to be
    # appended to `enabled` and then weighed by POSITION, so on an order with only one other
    # thing to offer — a cancelled one, a fully refunded one — it landed at index 1 and was
    # drawn at FULL WEIGHT. "Note first on every card" is the defect the live session counted,
    # and the quietest version of it survived Phase 4 on exactly the orders that need nothing.
    return [a.public() for a in weigh(rest[:MAX_ENABLED])
            + [_secondary(a) for a in note]
            + [_secondary(a) for a in disabled]]


def _secondary(action: AvailableAction) -> AvailableAction:
    from dataclasses import replace

    return replace(action, priority="secondary")


def weigh(enabled: list[AvailableAction]) -> list[AvailableAction]:
    """The first `MAX_PRIMARY` at full weight; everything after them behind the disclosure.

    One function for both rails, because "this is not a menu" has to mean the same thing on an
    order card and on an email thread. Order is already decided by the caller — what the
    entity's state needs comes first — so this only says how loud each one is.
    """
    return [a if i < MAX_PRIMARY else _secondary(a) for i, a in enumerate(enabled)]


def available_email_actions(thread: dict[str, Any], capabilities: dict[str, dict[str, Any]] | None,
                            *, row_actions: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """The rail for one email thread. The same shape as the order rail, for the same reason:
    the tablet renders what it is given and never decides what a chip means.

    Two kinds of chip share it. **Reply OPENS the reply** — the tap posts `compose.reply`
    with this thread's id and nothing else, and the card that comes back has the words of the
    reply on it as a field a thumb can type into (app/families/compose.py). It used to arm the
    microphone and only that: rendered twenty-four times in the live session, tapped nought,
    while the owner asked out loud how to type. The microphone is still there — `family` rides
    along, and the composer's own Dictate button binds it — but a chip called Reply now
    produces a reply. Archive is a row action (app/actions/rows.py): a tap asks the Mac to
    PREPARE the change, and the card that comes back still waits for a gesture. Both are gated
    by what this Mac can do.

    Until this existed, `rail()` was called from exactly one place — the order card — so an
    email on the tablet had no controls at all: Reply, Rewrite and Archive were registered on
    the Mac and reachable only by a spoken sentence.
    """
    caps = capabilities or {}
    thread_id = str(thread.get("thread_id") or "")
    if not thread_id:
        return []
    out: list[AvailableAction] = []
    draft = caps.get("gmail_draft_reply")
    if isinstance(draft, dict) and draft.get("state") in ("ready", "unknown"):
        out.append(AvailableAction(
            "reply", "Reply", "gmail_draft_reply", "amber", True, "", "Reply to this email",
            family="email.reply", mode="open", command="compose.reply",
            args=f"thread_id={thread_id}",
        ))
    public = [a.public() for a in out]
    # The row actions come already gated (actions_for checks the write tool is registered and
    # changes are on); they are appended as they are, so Archive on the rail is the same
    # action as Archive beside a row, resolved by the same table.
    for a in row_actions or []:
        if isinstance(a, dict) and a.get("id"):
            public.append({"command": "", "args": "", **dict(a)})
    # Reply and Archive are the two things a thread is for, so they are the two at full
    # weight; everything after them is disclosed.
    public = [{**a, "priority": "primary" if i < MAX_PRIMARY else "secondary"} for i, a in enumerate(public)]
    if out:
        # And the other way in, behind the disclosure: arm the microphone for this thread
        # without opening a keyboard first. §20's two halves as two controls — voice is
        # intent, touch is precision — with the precision one leading, because that is the
        # one the live session had no way to reach at all.
        #
        # PHASE 5 · §25 asked whether this earns its space, given that the composer Reply
        # opens carries a Dictate of its own with the same family and the same ref. It does:
        # that one only EXISTS once a composer is open, and this is the only way to bind the
        # microphone to a thread before then — the difference between "dictate this reply"
        # and "say something about this thread". Removing it was tried and it closed the
        # only door (`scripts/browser/tablet.js` taps
        # `.rail-chip[data-mode="ask"][data-family="email.reply"]` for exactly this reason).
        dictate = AvailableAction(
            "dictate", "Dictate", "gmail_draft_reply", "amber", True, "", "Reply to this email",
            family="email.reply", mode="ask", priority="secondary",
        )
        public.append(dictate.public())
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
