"""What the tablet shows, chosen from what the tools returned — never from the prose.

The answer Claude speaks is free text. What the screen shows beside it is not: it is a short
list of `ui` items, each one a type from a fixed vocabulary and a bounded, whitelisted slice of
the data a tool actually returned this turn. The tablet renders those types with its own DOM
code and ignores anything else. Claude cannot ask for a component, cannot supply markup, and
cannot put a value on screen that a tool did not return — the prose and the cards are built
from the same tool results, so they cannot disagree.

Two rules, and both are here rather than on the tablet so that a test can hold them:

- Bounded. Every list is capped and every string truncated. A payload the tablet cannot
  render is a payload it should never have been sent.
- Whitelisted. Values are copied key by key. A new field in a tool result reaches the screen
  only when a line is added here to carry it.

Nothing in this module decides what a tool may do. The gate (app/tools/gate.py) did that
before the tool ran; this runs afterwards and only shapes what is already known.
"""

from __future__ import annotations

from typing import Any

from app.actions import grammar
from app.providers.base import ToolCall
from app.session.models import Session
from app.tools.gate import Disposition, classify

# The component vocabulary. The tablet renders exactly these; anything else is dropped there
# too, so a typo here cannot become a blank card.
UI_TYPES = frozenset({
    "assistant", "order", "order_list", "customer", "customer_list", "product", "inventory",
    "sales_summary", "email_list", "email_thread", "email_draft", "attention", "confirmation",
    "success", "error", "context_stack",
    # the read layer's cards (app/analytics/present.py)
    "metric_group", "ranking", "table", "comparison", "variant_matrix", "trend", "working_set",
    # bulk changes (app/actions/batch.py): the card before the gesture, the count after it
    "batch_action", "batch_result",
    # what this build can do, grouped (app/capabilities/surface.py). Built by a recipe rather
    # than from a tool result: the manifest is read from the registry, not from the shop.
    "capability",
})
MAX_BATCH_ROWS = 50
ANALYTIC_TOOLS = frozenset({"commerce_aggregate", "commerce_query", "inventory_query", "email_query"})

# Bounds. The tablet is 8 inches wide; more than this is a spreadsheet, not an answer.
MAX_ORDERS = 10
MAX_ITEMS = 12
MAX_CUSTOMERS = 6
MAX_PRODUCTS = 4
MAX_VARIANTS = 16
MAX_MEASUREMENTS = 8
MAX_BREAKDOWN_DAYS = 31
MAX_THREADS = 10
MAX_MESSAGES = 6
MAX_BODY_CHARS = 2_000
MAX_SNIPPET_CHARS = 300
MAX_TEXT_CHARS = 160
MAX_NOTE_CHARS = 400
MAX_EMAIL_BODY_CHARS = 2400
MAX_ATTENTION = 6
MAX_CONTEXT = 6

# The interaction grammar: how the owner authorises a proposal. The card names one of these
# and the tablet renders it; a kind the tablet does not implement renders as unavailable, never
# as a plain button. The table and its words live in app/actions/grammar.py.
INTERACTIONS = frozenset(grammar.KINDS)
# The dead time after an action card appears before a tap can count. A finger lifting off the
# orb must never land on a card that materialised under it.
ARMED_AFTER_MS = grammar.ARMED_AFTER_MS

# "What are we low on?" — the threshold that makes a variant an exception, not a row.
LOW_STOCK_AT = 5

_CURRENCY_SYMBOL = {"GBP": "£", "USD": "$", "EUR": "€"}

# Errors, named calmly. The spoken answer already explains; the card gives one recovery.
_TURN_ERRORS: dict[str, tuple[str, str, str]] = {
    # error_kind: (service, title, recovery)
    "speech": ("speech", "Couldn't understand that", "Hold and ask again, a little closer to the tablet."),
    "empty": ("speech", "Didn't catch that", "Hold the orb while you speak."),
    "audio_too_large": ("speech", "That recording was too long", "Ask it in a shorter sentence."),
    "lost_thread": ("assistant", "Lost the thread", "Ask again from the start."),
    "timeout": ("assistant", "That took too long", "Ask again."),
    "not_started": ("assistant", "Assistant still starting", "Wait a moment and ask again."),
    "usage_limit": ("assistant", "Claude usage limit reached", "Try again later."),
    "auth": ("assistant", "Claude needs signing in on the Mac", "On the Mac: run claude, then /login."),
    "max_turns": ("assistant", "Stopped part-way", "Ask a narrower question."),
    "api_error": ("assistant", "Assistant unavailable", "Try again in a moment."),
}


def present(
    calls: list[ToolCall] | None,
    *,
    session: Session | None = None,
    error_kind: str | None = None,
    writes: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """The `ui` list for one turn: context cards from the tool results, one error card per
    failed service, and the context stack when the conversation has accumulated one."""
    items: list[dict[str, Any]] = []
    errors: dict[str, dict[str, Any]] = {}
    calls = list(calls or [])
    capabilities = writes.get("capabilities") if isinstance(writes, dict) and isinstance(writes.get("capabilities"), dict) else {}

    # What a row on a card may offer, decided here rather than by the tablet
    # (app/actions/rows.py). Empty while changes are off.
    row_actions = _row_actions(writes)

    for index, call in enumerate(calls):
        if not call.ok:
            if _recovered(call, calls[index + 1:]):
                # The gate refused a call and the model then did it properly — looked the
                # record up, called again. The owner sees the outcome, not the stumble.
                continue
            error = _tool_error(call, session)
            errors.setdefault(error["data"]["service"], error)
            continue
        if call.proposal_id and str(call.proposal_id).startswith("batch_"):
            batch = session.batches.get(call.proposal_id) if session is not None else None
            if batch is not None and not any(
                i["type"] == "batch_action" and i["data"].get("batch_id") == batch.batch_id for i in items
            ):
                items.append(_batch_card(batch, writes=writes))
        elif call.proposal_id:
            proposal = session.proposal(call.proposal_id) if session is not None else None
            if proposal is not None and not any(
                i["type"] == "confirmation" and i["data"].get("proposal_id") == proposal.proposal_id for i in items
            ):
                items.append(_confirmation(proposal, writes=writes))
            continue
        if not isinstance(call.result, dict):
            continue
        for item in _from_result(call.name, call.result):
            if item["type"] == "email_list" and row_actions.get("email_thread"):
                for thread in item["data"].get("threads") or []:
                    if thread.get("thread_id"):
                        thread["actions"] = row_actions["email_thread"]
            if item["type"] == "order" and item["data"].get("detail"):
                # The rail: which changes make sense for this order, decided on the Mac from
                # the order's own state and what the store has granted this Mac.
                item["data"]["actions"] = _actions(call.result, capabilities)
            items.append(item)
            if item["type"] == "order" and item["data"].get("detail"):
                # What the order needs, read on the Mac, as its own card after the order.
                attention = _attention_items(call.result)
                if attention:
                    items.append(_ui("attention", {"items": attention, "for": item["data"].get("order_id")}))

    items = _merge(items)
    if session is not None:
        _remember(items, session)

    if error_kind:
        service, title, recovery = _TURN_ERRORS.get(
            error_kind, ("assistant", "Something went wrong", "Ask again.")
        )
        errors.setdefault(service, _error(service, error_kind, title, recovery))

    out = items + list(errors.values())
    if session is not None and len(session.context) >= 2:
        out.append(_ui("context_stack", {"entries": [dict(c) for c in session.context[:MAX_CONTEXT]]}))
    return [item for item in out if item["type"] in UI_TYPES]


# --------------------------------------------------------------------------- per tool


def _from_result(name: str, result: dict[str, Any]) -> list[dict[str, Any]]:
    if name in ANALYTIC_TOOLS:
        from app.analytics.present import build, working_set_items

        return build(result, tool=name) + working_set_items(result)
    if name == "shopify_order_detail":
        return [_ui("order", _order(result, detail=True))]
    if name == "shopify_find_order":
        orders = [_order(o) for o in _list(result.get("orders"), MAX_ORDERS)]
        out: list[dict[str, Any]] = []
        if len(orders) == 1:
            out.append(_ui("order", orders[0]))
        elif orders:
            out.append(_ui("order_list", {
                "title": "Orders", "query": _text(result.get("query")), "orders": orders,
                "count": len(orders), "truncated": False,
            }))
        matched = _list(result.get("customers_matched"), MAX_CUSTOMERS)
        if result.get("ambiguous") and matched:
            out.append(_ui("customer_list", {
                "title": "Which customer?", "query": _text(result.get("query")),
                "customers": [_customer(c) for c in matched], "ambiguous": True,
            }))
        return out
    if name == "shopify_list_orders":
        orders = [_order(o) for o in _list(result.get("orders"), MAX_ORDERS)]
        if not orders:
            return []
        return [_ui("order_list", {
            "title": _window_title(result),
            "since": _text(result.get("since")), "until": _text(result.get("until")),
            "days": _int(result.get("days")), "days_ago": _int(result.get("days_ago")),
            "count": _int(result.get("count")) or len(orders),
            "truncated": bool(result.get("truncated")),
            "orders": orders,
            "value": "",
        })]
    if name == "shopify_customer_history":
        card = _customer(result)
        card["history"] = _history(result)
        card["related_email"] = _related_email(result.get("email_threads"))
        return [_ui("customer", card)]
    if name == "shopify_find_customer":
        customers = [_customer(c) for c in _list(result.get("customers"), MAX_CUSTOMERS)]
        if len(customers) == 1:
            return [_ui("customer", customers[0])]
        if customers:
            return [_ui("customer_list", {
                "title": "Which customer?" if result.get("ambiguous") else "Customers",
                "query": _text(result.get("query")), "customers": customers,
                "ambiguous": bool(result.get("ambiguous")),
            })]
        return []
    if name == "shopify_inventory":
        products = [_inventory_product(p) for p in _list(result.get("products"), MAX_PRODUCTS)]
        if not products:
            return []
        exceptions = [e for p in products for e in p.pop("_exceptions")]
        return [_ui("inventory", {
            "query": _text(result.get("product")), "size": _text(result.get("size")),
            "products": products,
            "exceptions": exceptions[:MAX_VARIANTS],
            "low_stock_at": LOW_STOCK_AT,
        })]
    if name == "shopify_sales_summary":
        orders = _int(result.get("orders"))
        revenue = _float(result.get("revenue"))
        currency = _text(result.get("currency")) or "GBP"
        return [_ui("sales_summary", {
            "title": _window_title(result),
            "since": _text(result.get("since")), "until": _text(result.get("until")),
            "days": _int(result.get("days")), "days_ago": _int(result.get("days_ago")),
            "orders": orders,
            "revenue": _money_display(revenue, currency),
            "aov": _money_display(revenue / orders, currency) if orders and revenue is not None else None,
            "currency": currency,
            "complete": bool(result.get("complete", True)),
            "by_day": [_sales_day(d, currency) for d in _list(result.get("by_day"), MAX_BREAKDOWN_DAYS)],
            "basis": _text(result.get("basis"), MAX_NOTE_CHARS),
            "caveat": _text(result.get("caveat"), MAX_NOTE_CHARS),
        })]
    if name == "shopify_product_info":
        products = [_product(p) for p in _list(result.get("products"), MAX_PRODUCTS)]
        if not products:
            return []
        return [_ui("product", {
            "query": _text(result.get("product")), "size": _text(result.get("size")),
            "products": products,
        })]
    if name == "gmail_search":
        threads = [_thread_summary(t) for t in _list(result.get("threads"), MAX_THREADS)]
        if not threads:
            return []
        return [_ui("email_list", {
            "title": "Email", "query": _text(result.get("query"), MAX_NOTE_CHARS),
            "count": _int(result.get("count")) or len(threads), "threads": threads,
        })]
    if name == "gmail_read_thread":
        messages = [_message(m) for m in _list(result.get("messages"), MAX_MESSAGES)]
        if not messages:
            return []
        return [_ui("email_thread", {
            "thread_id": _text(result.get("thread_id")),
            "subject": next((m["subject"] for m in messages if m["subject"]), ""),
            "message_count": _int(result.get("message_count")) or len(messages),
            "truncated": bool(result.get("truncated")) or len(messages) < (_int(result.get("messages_shown")) or 0),
            "messages": messages,
        })]
    return []


# --------------------------------------------------------------------------- shapes


def _order(o: dict[str, Any], *, detail: bool = False) -> dict[str, Any]:
    out = {
        "order_id": _text(o.get("order_id")),
        "order_number": _order_number(o.get("order_number")),
        "placed_at": _text(o.get("placed_at")),
        "fulfillment": _status(o.get("fulfillment")),
        "payment": _status(o.get("payment")),
        "total": _money_text(o.get("total")),
        "customer_name": _text(o.get("customer_name")),
        "customer_id": _text(o.get("customer_id")),
        "customer_email": _text(o.get("customer_email")),
        "detail": detail,
    }
    if detail:
        money = o.get("money") if isinstance(o.get("money"), dict) else {}
        out.update({
            "items": [_item(i) for i in _list(o.get("items"), MAX_ITEMS)],
            "items_truncated": bool(o.get("items_truncated")),
            "fulfillments": [
                {
                    "status": _status(f.get("status")),
                    "shipped_at": _text(f.get("shipped_at")),
                    "carrier": _text(f.get("carrier")),
                    "number": _text(f.get("number")),
                    "url": _tracking_url(f.get("url")),
                }
                for f in _list(o.get("fulfillments"), 6)
            ],
            "cancelled_at": _text(o.get("cancelled_at")),
            "cancel_reason": _status(o.get("cancel_reason")),
            "note": _text(o.get("note"), MAX_NOTE_CHARS),
            "tags": [_text(t, 40) for t in (o.get("tags") or [])[:10] if isinstance(t, str)],
            "ships_to": _text(o.get("ships_to")),
            "shipping_method": _text(o.get("shipping_method")),
            "shipping_address": _address(o.get("shipping_address")),
            "money": {
                "subtotal": _money_text(money.get("subtotal")),
                "shipping": _money_text(money.get("shipping")),
                "tax": _money_text(money.get("tax")),
                "discounts": _money_text(money.get("discounts")),
                "refunded": _money_text(money.get("refunded")),
                "outstanding": _money_text(money.get("outstanding")),
            } if money else None,
            "refunds": [
                {"created_at": _text(r.get("created_at")), "amount": _money_text(r.get("amount")), "note": _text(r.get("note"))}
                for r in _list(o.get("refunds"), 6)
            ],
            "history": _history(o.get("history")),
            "email": _related_email(o.get("email")),
            "pending": [_text(p, 20) for p in (o.get("pending") or [])[:4] if isinstance(p, str)],
        })
    return out


def _row_actions(writes: dict[str, Any] | None) -> dict[str, list[dict[str, Any]]]:
    """The buttons each kind of row carries on this build, by kind. Read once per turn."""
    from app.actions.rows import BY_KIND, actions_for

    enabled = bool(isinstance(writes, dict) and writes.get("allowed"))
    if not enabled:
        return {}
    return {kind: actions_for(kind, writes_enabled=True) for kind in BY_KIND}


def _actions(order: dict[str, Any], capabilities: dict[str, Any]) -> list[dict[str, Any]]:
    from app.actions.available import available_actions

    return [
        {
            "id": _text(a.get("id"), 20), "label": _text(a.get("label"), 20), "operation": _text(a.get("operation"), 40),
            "risk": "red" if a.get("risk") == "red" else "amber", "enabled": bool(a.get("enabled")),
            "reason": _text(a.get("reason"), 60), "instruction": _text(a.get("instruction"), 120), "mode": _text(a.get("mode"), 12) or "ask",
        }
        for a in available_actions(order, capabilities)[:6]
    ]


def _item(i: dict[str, Any]) -> dict[str, Any]:
    stock = i.get("stock") if isinstance(i.get("stock"), dict) else None
    return {
        "title": _text(i.get("title")),
        "variant": _text(i.get("variant")),
        "sku": _text(i.get("sku")),
        "quantity": _int(i.get("quantity")),
        "total": _money_text(i.get("total")),
        "image": _media_path(i.get("image_url")),
        "variant_id": _text(i.get("variant_id")),
        "product_id": _text(i.get("product_id")),
        "stock": {
            "tracked": bool(stock.get("tracked", True)),
            "available": _int(stock.get("available")),
        } if stock else None,
    }


def _address(a: Any) -> dict[str, Any] | None:
    """The address as the card prints it: a name and a few lines. The postcode and country
    are what a change-of-address diff turns on, so they are kept as fields of their own."""
    if not isinstance(a, dict):
        return None
    lines = [_text(line, 120) for line in (a.get("lines") or [])[:3] if isinstance(line, str) and line.strip()]
    return {
        "name": _text(a.get("name")),
        "company": _text(a.get("company")),
        "lines": lines,
        "city": _text(a.get("city")),
        "province": _text(a.get("province")),
        "zip": _text(a.get("zip"), 20),
        "country": _text(a.get("country")),
        "country_code": _text(a.get("country_code"), 4),
    }


def _history(h: Any) -> dict[str, Any] | None:
    """The customer's history beside their order: the five questions the owner asks."""
    if not isinstance(h, dict):
        return None
    last = h.get("last_order") if isinstance(h.get("last_order"), dict) else None
    return {
        "customer_id": _text(h.get("customer_id")),
        "name": _text(h.get("name")),
        "orders": _int(h.get("orders")),
        "spent": _money_text(h.get("spent")),
        "since": _text(h.get("since")),
        "standing": _text(h.get("standing"), 20),
        "first_order_at": _text(h.get("first_order_at")),
        "last_order": {"order_id": _text(last.get("order_id")), "order_number": _order_number(last.get("order_number"))} if last else None,
        "recent": [
            {
                "order_id": _text(r.get("order_id")),
                "order_number": _order_number(r.get("order_number")),
                "placed_at": _text(r.get("placed_at")),
                "fulfillment": _status(r.get("fulfillment")),
                "payment": _status(r.get("payment")),
                "cancelled": bool(r.get("cancelled_at")),
                "total": _money_text(r.get("total")),
                "items_brief": _text(r.get("items_brief")),
                "current": bool(r.get("current")),
            }
            for r in _list(h.get("recent"), 5)
        ],
        "recent_truncated": bool(h.get("recent_truncated")),
        "other_unfulfilled": [_order_number(n) for n in (h.get("other_unfulfilled") or [])[:5] if isinstance(n, str)],
        "tags": [_text(t, 40) for t in (h.get("tags") or [])[:6] if isinstance(t, str)],
        "provenance": _text(h.get("provenance"), 20) or "SHOPIFY",
    }


def _related_email(e: Any) -> dict[str, Any] | None:
    """Email that is about this order, and how sure that is. Every thread carries its
    provenance: a verified sender is the customer; anything else is a mention."""
    if not isinstance(e, dict):
        return None
    return {
        "available": bool(e.get("available")),
        "reason": _text(e.get("reason")),
        "threads": [
            {
                **_thread_summary(t),
                "sender_match": bool(t.get("sender_match")),
                "verified_sender": bool(t.get("verified_sender")),
                "match": _text(t.get("match"), 20),
                "provenance": _text(t.get("provenance"), 20) or "UNKNOWN",
            }
            for t in _list(e.get("threads"), 3)
        ],
    }


def _tracking_url(value: Any) -> str:
    """A carrier's tracking link, shown only when it is an https link. Never opened by the
    tablet on its own; the owner taps it."""
    text = _text(value, 400)
    return text if text.lower().startswith("https://") else ""


def _media_path(value: Any) -> str:
    """An image reaches the tablet only as a same-origin path the Mac signed. A Shopify CDN
    URL the Mac does not recognise becomes no image at all."""
    from app.media import signed_path

    return signed_path(value) or ""


def present_extension(ext: dict[str, Any]) -> dict[str, Any]:
    """What GET /context/order returns: the parts of the order card that arrived after the
    turn, bounded the same way as the card itself."""
    return {
        "order_id": _text(ext.get("order_id")),
        "pending": [_text(p, 20) for p in (ext.get("pending") or [])[:4] if isinstance(p, str)],
        "history": _history(ext.get("history")),
        "email": _related_email(ext.get("email")),
        **({"attention": _attention_items(ext)} if isinstance(ext.get("attention"), list) else {}),
    }


def _attention_items(order: dict[str, Any]) -> list[dict[str, Any]]:
    """The attention lines the Mac read from the order, bounded for the card. A "say" is
    printed as words the owner could use — the card never offers to do it."""
    out = []
    for a in _list(order.get("attention"), MAX_ATTENTION):
        if not isinstance(a, dict) or not a.get("title"):
            continue
        detail = _text(a.get("detail"), MAX_TEXT_CHARS)
        say = _text(a.get("say"), 80)
        if say:
            detail = f"{detail} — say “{say}”" if detail else f"Say “{say}”"
        out.append({
            "kind": _text(a.get("kind"), 20), "title": _text(a.get("title"), 80), "detail": _text(detail, 200),
            "level": a.get("level") if a.get("level") in ("red", "amber", "green") else "amber",
        })
    return out


def _customer(c: dict[str, Any]) -> dict[str, Any]:
    return {
        "customer_id": _text(c.get("customer_id") or c.get("id")),
        "name": _text(c.get("name")),
        "email": _text(c.get("email")),
        "orders": _int(c.get("orders")),
        "spent": _money_text(c.get("spent")),
    }


def _inventory_product(p: dict[str, Any]) -> dict[str, Any]:
    variants = []
    exceptions = []
    title = _text(p.get("title"))
    for v in _list(p.get("variants"), MAX_VARIANTS):
        available = _int(v.get("available"))
        oversold = _int(v.get("oversold_by")) or 0
        tracked = bool(v.get("tracked", True))
        level = _stock_level(available, oversold, tracked)
        row = {
            "variant_id": _text(v.get("variant_id")),
            "variant": _text(v.get("variant")),
            "sku": _text(v.get("sku")),
            "available": available,
            "oversold_by": oversold,
            "tracked": tracked,
            "level": level,
        }
        variants.append(row)
        if level in {"out", "low", "oversold"}:
            exceptions.append({"product": title, **row})
    return {
        "product_id": _text(p.get("product_id")),
        "title": title,
        "status": _status(p.get("status")),
        "total_inventory": _int(p.get("total_inventory")),
        "variants": variants,
        "_exceptions": exceptions,
    }


def _stock_level(available: int | None, oversold: int, tracked: bool) -> str:
    if not tracked:
        return "untracked"
    if oversold > 0:
        return "oversold"
    if available is None:
        return "unknown"
    if available == 0:
        return "out"
    if available <= LOW_STOCK_AT:
        return "low"
    return "ok"


def _product(p: dict[str, Any]) -> dict[str, Any]:
    measurements = []
    for m in _list(p.get("measurements"), MAX_MEASUREMENTS):
        if isinstance(m, dict):
            measurements.append({str(k)[:24]: _text(v, 40) for k, v in list(m.items())[:8]})
    return {
        "product_id": _text(p.get("product_id")),
        "title": _text(p.get("title")),
        "status": _status(p.get("status")),
        "description": _text(p.get("description"), 600),
        "subtitle": _text(p.get("subtitle")),
        "fabric": _text(p.get("fabric"), MAX_NOTE_CHARS),
        "cut": _text(p.get("cut"), MAX_NOTE_CHARS),
        "origin": _text(p.get("origin"), MAX_NOTE_CHARS),
        "care": _text(p.get("care"), MAX_NOTE_CHARS),
        "measurements": measurements,
        "measurements_note": _text(p.get("measurements_note")),
    }


def _thread_summary(t: dict[str, Any]) -> dict[str, Any]:
    return {
        "thread_id": _text(t.get("thread_id")),
        "from": _text(t.get("from")),
        "from_email": _text(t.get("from_email")),
        "subject": _text(t.get("subject")),
        "date": _text(t.get("date")),
        "snippet": _text(t.get("snippet"), MAX_SNIPPET_CHARS),
        "likely_bulk": bool(t.get("likely_bulk")),
        "known_customer": t.get("known_customer") if isinstance(t.get("known_customer"), bool) else None,
    }


def _message(m: dict[str, Any]) -> dict[str, Any]:
    return {
        "from": _text(m.get("from")),
        "from_email": _text(m.get("from_email")),
        "date": _text(m.get("date")),
        "subject": _text(m.get("subject")),
        "body": _text(m.get("body"), MAX_BODY_CHARS),
    }


# --------------------------------------------------------------------------- errors


def _recovered(call: ToolCall, later: list[ToolCall]) -> bool:
    """The gate refused this call and the model then did the same thing properly. The same
    thing: the same tool on the same entity — a note refused for one order is not made good
    by a note prepared for another, and the owner must see the refusal."""
    entity = _entity_of(call)
    return any(c.ok and c.name == call.name and (entity is None or _entity_of(c) == entity) for c in later)


def _entity_of(call: ToolCall) -> str | None:
    """The entity a call was about, as the store numbers it: "1938" whether the model wrote
    the bare number or the full gid. The refused call and the one that put it right are the
    same thing only when this matches."""
    for key, value in (call.args or {}).items():
        if key.endswith("_id") and isinstance(value, str) and value.strip():
            return value.rstrip("/").rsplit("/", 1)[-1].lower()
    return None


def _tool_error(call: ToolCall, session: Session | None) -> dict[str, Any]:
    name = call.name or ""
    issued = session.issued_ids if session is not None else ()
    blocked = classify(name, call.args or {}, issued).disposition is Disposition.DENY
    if name.startswith("shopify_"):
        service, title = "shopify", "Shopify unavailable"
    elif name.startswith("gmail_"):
        service, title = "gmail", "Email unavailable"
    else:
        service, title = "assistant", "Lookup failed"
    if blocked:
        # The assistant's own rules stopped it, not the owner's permissions: it asked for
        # something it may not do, or in a way it may not. Nothing left the Mac.
        return _error(service, "blocked", "Refused by the assistant's rules", "The assistant tried something outside what it may do. Nothing was changed.")
    return _error(service, "tool_failed", title, "Ask again in a moment; the answer says what happened.")


def _error(service: str, kind: str, title: str, recovery: str) -> dict[str, Any]:
    return _ui("error", {"service": service, "kind": kind, "title": title, "recovery": recovery})


# --------------------------------------------------------------------------- actions


def _confirmation(proposal, *, writes: dict[str, Any] | None = None) -> dict[str, Any]:
    """The action card, from the staged proposal and nothing else: the model chose no
    component and supplied no label. The tool's own `present` names the change; this bounds
    it and adds what the tablet needs to run the interaction and nothing it does not. When
    the Mac already knows a tap from this tablet would be refused, the card says so instead
    of arming a surface that would fail."""
    words = _present_words(proposal)
    interaction = proposal.interaction if proposal.interaction in INTERACTIONS else "unsupported"
    gesture = grammar.words_for(interaction)
    commit = _commit_words(proposal, writes)
    return _ui("confirmation", {
        "proposal_id": _text(proposal.proposal_id, 40),
        "status": _text(proposal.status.value.lower(), 20),
        "risk": "red" if proposal.risk == "RED" else "amber",
        "operation": _text(proposal.operation, 60),
        "title": _text(words.get("title")),
        "entity": _entity_line(proposal),
        "entity_kind": _text(proposal.entity_kind, 20),
        "entity_ref": _text(proposal.entity_ref, 200),
        "summary": _text(words.get("summary"), MAX_NOTE_CHARS),
        # An email's whole text, when the change is an email: the card is the draft.
        "body": _text(words.get("body"), MAX_EMAIL_BODY_CHARS),
        "detail": _text(words.get("detail")),
        # The facts the gesture authorises, printed above it: what the change will do and to
        # whom, built by the tool from what it read. Never a place for the model's words.
        "facts": [
            {"label": _text(f.get("label"), 40), "value": _text(f.get("value"), 120), "tone": _text(f.get("tone"), 10)}
            for f in _list(words.get("facts"), 8)
        ],
        "interaction": {
            "kind": interaction,
            "label": _text(words.get("confirm_label") or gesture["label"], 60),
            "footer": _text(gesture["footer"], 120),
            # The words on the target or the handle — the consequence, from the tool.
            "target": _text(words.get("target"), 60),
            "armed_after_ms": ARMED_AFTER_MS,
            "hold_ms": grammar.HOLD_MS,
            "armed_for_s": grammar.ARMED_FOR_S,
            "swipe_fraction": grammar.SWIPE_FRACTION,
        },
        "expires_at": proposal.public()["expires_at"],
        "ttl_s": proposal.ttl_s(),
        "reversible": bool(proposal.reversible),
        "commit": commit if commit else {"allowed": True},
    })


# Why a tap would be refused from here, in the words the card shows under the change.
_COMMIT_BLOCKED_WORDS = {
    "writes_disabled": "Changes are switched off on the Mac (CROOKS_WRITES_ENABLED).",
    "allow_list_missing": "No allowed logins are set on the Mac (CROOKS_ALLOWED_LOGINS).",
    "not_authorised": "This tablet's login is not on the allowed list. Open /whoami to see it.",
    "not_authorised_local": "Asked on the Mac itself, which may not apply changes (CROOKS_WRITES_LOCAL_OWNER).",
    "scope_missing": "The store has not granted the permission this change needs.",
    "gmail_scope_missing": "The Gmail credential cannot make this change yet.",
    "identity_unverified": "The Mac could not confirm this tablet's identity with Tailscale.",
    "read_only": "This backend is in read-only test mode and cannot apply changes.",
}


def _present_words(proposal) -> dict[str, Any]:
    from app.tools import registry

    try:
        spec = registry.get(proposal.tool_name)
    except KeyError:
        return {}
    if spec.write is None:
        return {}
    try:
        words = spec.write.present(proposal)
    except Exception:  # noqa: BLE001 — a card with no words is still a card
        return {}
    return words if isinstance(words, dict) else {}


def _entity_line(proposal) -> str:
    kind = (proposal.entity_kind or "").capitalize()
    return _text(f"{kind} {proposal.entity_label}".strip())


def present_action(result, *, session: Session | None = None, writes: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """What the tablet shows once a tap has been answered: a success card and the entity as
    it now is (from the verifying re-read), or a calm failure. Built from the engine's result,
    never from the tablet's expectation."""
    proposal = result.proposal
    if proposal is None:
        return []
    recovery = result.spoken if result.code in ("stale", "unverified", "failed", "service_unavailable") else ""
    return present_proposal_state(proposal, session=session, code=result.code, writes=writes, recovery=recovery)


def _service_of(proposal) -> str:
    return "gmail" if str(proposal.tool_name or "").startswith("gmail_") else "shopify"


def _service_name(proposal) -> str:
    return "Gmail" if _service_of(proposal) == "gmail" else "Shopify"


# --------------------------------------------------------------------------- batches


def _batch_words(batch) -> dict[str, Any]:
    from app.tools import registry

    try:
        spec = registry.get(batch.tool_name)
    except KeyError:
        return {}
    if spec.batch is None:
        return {}
    try:
        words = spec.batch.present(batch)
    except Exception:  # noqa: BLE001 — a card with no words is still a card
        return {}
    return words if isinstance(words, dict) else {}


def _batch_scope(batch) -> dict[str, Any]:
    return {"set_id": _text(batch.set_id, 40), "label": _text(batch.set_label, 80), "kind": _text(batch.set_kind, 20), "count": int(batch.requested)}


def _batch_card(batch, *, writes: dict[str, Any] | None = None) -> dict[str, Any]:
    """The bulk-change card: how many, of what, with what consequence, who is excluded and
    why, every member by name to inspect, and the one gesture. Built from the batch the Mac
    staged and the tool's own words; the model chose none of it."""
    words = _batch_words(batch)
    interaction = batch.interaction if batch.interaction in INTERACTIONS else "unsupported"
    gesture = grammar.words_for(interaction)
    commit = _commit_words(batch, writes)
    preview = batch.summary.get("preview") if isinstance(batch.summary.get("preview"), dict) else {}
    return _ui("batch_action", {
        "batch_id": _text(batch.batch_id, 40),
        "status": _text(batch.status.value.lower(), 20),
        "risk": "red" if batch.risk == "RED" else "amber",
        "operation": _text(batch.operation, 60),
        "title": _text(words.get("title")),
        "summary": _text(words.get("summary"), MAX_NOTE_CHARS),
        "body": _text(words.get("body"), MAX_EMAIL_BODY_CHARS),
        "detail": _text(words.get("detail"), MAX_NOTE_CHARS),
        "set": _batch_scope(batch),
        "requested": int(batch.requested),
        "eligible": len(batch.eligible),
        "excluded_count": len(batch.excluded),
        "excluded": [{"label": _text(c.label, 60), "reason": _text(c.excluded, 120)} for c in batch.excluded[:MAX_BATCH_ROWS]],
        "members": [_text(c.label, 60) for c in batch.eligible[:MAX_BATCH_ROWS]],
        "facts": [
            {"label": _text(f.get("label"), 40), "value": _text(f.get("value"), 120), "tone": _text(f.get("tone"), 10)}
            for f in _list(words.get("facts"), 8)
        ],
        # One member's email as it will be saved: the campaign, previewed on the first.
        "preview": {"to": _text(preview.get("to")), "subject": _text(preview.get("subject"), 200), "body": _text(preview.get("body"), MAX_EMAIL_BODY_CHARS)} if preview else None,
        "interaction": {
            "kind": interaction,
            "label": _text(words.get("confirm_label") or gesture["label"], 60),
            "footer": _text(gesture["footer"], 120),
            "target": _text(words.get("target"), 60),
            "armed_after_ms": ARMED_AFTER_MS,
            "hold_ms": grammar.HOLD_MS,
            "armed_for_s": grammar.ARMED_FOR_S,
            "swipe_fraction": grammar.SWIPE_FRACTION,
        },
        "expires_at": batch.public()["expires_at"],
        "ttl_s": batch.ttl_s(),
        "reversible": bool(batch.reversible),
        "commit": commit if commit else {"allowed": True},
    })


_OUTCOME_LABELS = {
    "verified": "applied", "unverified": "not confirmed", "stale": "changed meanwhile, left alone", "failed": "not applied",
    "service_unavailable": "not applied", "refused": "refused", "not_attempted": "not attempted", "already_executed": "applied",
    "expired": "not attempted", "revoked": "not attempted", "in_progress": "not confirmed",
}


def present_batch(result, *, session: Session | None = None, writes: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    batch = result.batch
    if batch is None:
        return []
    return present_batch_state(batch, session=session, code=result.code, writes=writes)


def present_batch_state(batch, *, session: Session | None = None, code: str | None = None, writes: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """What the tablet shows for a batch: the card while it waits, the count once it has run
    — every member with its outcome, and never a total the engine did not prove."""
    code = code or batch.code or batch.status.value.lower()
    status = batch.status.value.lower()
    words = _batch_words(batch)
    if status == "done":
        counts = {k: int(batch.counts.get(k) or 0) for k in ("requested", "eligible", "excluded", "verified", "unverified", "stale", "failed", "not_attempted")}
        rows = [{"label": _text(c.label, 60), "outcome": _text(_OUTCOME_LABELS.get(c.code, c.code or "not attempted"), 40), "code": _text(c.code, 30)} for c in batch.eligible[:MAX_BATCH_ROWS]]
        rows += [{"label": _text(c.label, 60), "outcome": "excluded: " + _text(c.excluded, 100), "code": "excluded"} for c in batch.excluded[: max(0, MAX_BATCH_ROWS - len(rows))]]
        title = _text(words.get("undone_title") or "Undone") if batch.undo_of else _text(words.get("done_title") or "Done")
        verified, eligible = counts["verified"], counts["eligible"]
        not_applied = eligible - verified
        # One denominator, the one the owner gestured for: the eligible members on the card.
        # The excluded were named there before the gesture and are not counted against it.
        return [_ui("batch_result", {
            "batch_id": _text(batch.batch_id, 40), "operation": _text(batch.operation, 60),
            "title": f"{title}: {verified} of {eligible}",
            "detail": f"{_text(batch.set_label, 80)} · {counts['requested']} {_text(batch.set_kind, 20)}" + (f" · {counts['excluded']} excluded before the gesture" if counts["excluded"] else ""),
            "all_verified": batch.all_verified,
            "summary": f"{verified} applied" + (f", {not_applied} not" if not_applied else ""),
            "counts": counts, "rows": rows,
            "note": "" if verified == eligible else f"The {not_applied} marked not applied were left as they were. Ask for the change again for those, or check them in Shopify.",
        })]
    if status == "pending":
        return [_batch_card(batch, writes=writes)]
    if status == "executing":
        return [_error("shopify" if not str(batch.child_tool).startswith("gmail_") else "gmail", "in_progress", *_OUTCOME_WORDS["in_progress"])]
    title, line = _OUTCOME_WORDS.get(code, _OUTCOME_WORDS["failed"])
    if code == "revoked" and batch.undo_of:
        line = "The undo was withdrawn when you moved on."
    return [_error("shopify" if not str(batch.child_tool).startswith("gmail_") else "gmail", _text(code, 40), title, _text(line, 200))]


def present_proposal_state(
    proposal, *, session: Session | None = None, code: str | None = None,
    writes: dict[str, Any] | None = None, recovery: str = "",
) -> list[dict[str, Any]]:
    code = code or proposal.code or proposal.status.value.lower()
    words = _present_words(proposal)
    entity_line = _entity_line(proposal)
    items: list[dict[str, Any]] = []
    status = proposal.status.value.lower()
    if status == "verified":
        title = _text(words.get("undone_title") or _undone_title(proposal)) if proposal.undo_of else _text(words.get("done_title") or _done_title(proposal))
        items.append(_ui("success", {
            "title": title, "detail": entity_line,
            "proposal_id": _text(proposal.proposal_id, 40), "operation": _text(proposal.operation, 60),
            # What the proof could not yet see ("the refund isn't showing yet"): on the card,
            # not only in the voice.
            "note": _text(proposal.note, 200),
        }))
        if isinstance(proposal.entity, dict) and proposal.entity_kind == "order":
            items.append(_ui("order", _order(proposal.entity, detail=True)))
        elif isinstance(proposal.entity, dict) and proposal.entity.get("kind") == "email" and proposal.entity.get("body"):
            e = proposal.entity
            items.append(_ui("email_draft", {
                "to": _text(e.get("to")), "subject": _text(e.get("subject"), 200), "body": _text(e.get("body"), MAX_EMAIL_BODY_CHARS),
                "state": "sent" if e.get("state") == "sent" else "draft",
            }))
    elif status == "pending":
        # Whether a tap from this request could work, on this card too: a card recovered
        # after a lost connection must not offer a tap the Mac would refuse.
        items.append(_confirmation(proposal, writes=writes))
    elif status in ("executing", "executed"):
        # Claimed, sent, or being proven: the outcome is not known yet, and the card must not
        # say "not applied" about a change that may be on the order this second.
        items.append(_error(_service_of(proposal), "in_progress", *_OUTCOME_WORDS["in_progress"]))
    else:
        title, words = _OUTCOME_WORDS.get(code, _OUTCOME_WORDS["failed"])
        if code == "refused":
            # The service answered and said no: its reason, bounded, is the one useful line.
            words = f"{_service_name(proposal)} refused it: {_text(proposal.reason, 140)}. Nothing was changed."
        elif code == "revoked" and proposal.undo_of:
            words = "The undo was withdrawn when you moved on."
        elif recovery:
            # The tool's own words for this outcome (the voice says the same): "a new message
            # arrived in that thread", "the stock moved" — never "the order" for an email.
            words = recovery
        items.append(_error(_service_of(proposal), _text(code, 40), title, _text(words, 200)))
    if session is not None:
        _remember(items, session)
    return items


def _commit_words(proposal, writes: dict[str, Any] | None) -> dict[str, Any] | None:
    """Whether a gesture on THIS card could work, from this request's identity and from the
    capability of this card's own change — a fulfilment scope the store has not granted must
    not mark a note as blocked, and write_orders being granted must not mark an email as
    tappable. When it could not, the words name the permission the status carries."""
    if not isinstance(writes, dict):
        return None
    code, detail = "", ""
    if writes.get("allowed") is False:
        code, detail = str(writes.get("code") or ""), str(writes.get("detail") or "")
    else:
        capabilities = writes.get("capabilities") if isinstance(writes.get("capabilities"), dict) else {}
        operation = str(proposal.operation or "").removesuffix("_undo")
        entry = capabilities.get(operation)
        if isinstance(entry, dict) and entry.get("state") not in ("ready", "unknown"):
            from app.runtime import WriteStatus

            detail = str(entry.get("detail") or "")
            code = WriteStatus(str(entry.get("state") or "blocked"), detail).code
    if not code:
        return None
    reason = _COMMIT_BLOCKED_WORDS.get(code, "Changes cannot be applied from this tablet.")
    if code in ("scope_missing", "gmail_scope_missing") and detail:
        reason = f"{reason} ({_text(detail.replace('blocked — ', '', 1), 140)})"
    return {"allowed": False, "code": _text(code, 40), "reason": _text(reason, 200)}


def _done_title(proposal) -> str:
    return {
        "order_note_append": "Note added", "order_tags_add": "Tags added", "order_cancel": "Cancelled",
        "refund_create": "Refunded", "order_shipping_address_set": "Address changed", "fulfillment_create": "Shipped",
        "gmail_draft_reply": "Draft saved", "gmail_draft_new": "Draft saved", "gmail_send_reply": "Reply sent", "gmail_send_new": "Email sent",
        "gmail_thread_archive": "Archived", "inventory_set": "Stock adjusted", "order_tags_remove": "Tags removed",
        "fulfillment_tracking_set": "Tracking added",
    }.get(proposal.operation, "Done")


def _undone_title(proposal) -> str:
    return {
        "order_note_append_undo": "Note restored", "order_tags_add_undo": "Tags removed",
        "gmail_draft_reply_undo": "Draft deleted", "gmail_draft_new_undo": "Draft deleted", "gmail_thread_archive_undo": "Back in the inbox",
        "inventory_set_undo": "Stock put back", "order_tags_remove_undo": "Tags put back",
    }.get(proposal.operation, "Undone")


# What a settled-but-not-successful proposal says on the card. Calm, and nothing from Shopify.
# "Nothing was changed" appears only under codes the engine proves: a failure before the
# mutation left, or a re-read that still shows the order as it was. An ambiguous outcome says
# to check the order, and never guesses either way.
_OUTCOME_WORDS: dict[str, tuple[str, str]] = {
    "stale": ("Not applied", "The order changed since this was prepared. Ask again for a fresh one."),
    "expired": ("Expired", "That action waited too long. Ask again."),
    "revoked": ("Withdrawn", "You moved on to something else. Ask again if you still want it."),
    "unverified": ("Could not confirm", "The change could not be confirmed. Check the order before asking again."),
    "service_unavailable": ("Not applied", "Shopify could not be reached. Nothing was changed."),
    "already_executed": ("Already applied", "This was applied once already; it is not applied twice."),
    "in_progress": ("Applying", "Still being applied. Give it a moment."),
    "failed": ("Not applied", "That did not go through. Nothing was changed."),
    "refused": ("Refused", "The service answered and said no. Nothing was changed."),
}


# --------------------------------------------------------------------------- merging, memory


def _merge(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """One card per entity. A find followed by a detail lookup of the same order in one turn
    yields the detail card only; the summary is a strict subset of it."""
    out: list[dict[str, Any]] = []
    seen_orders: dict[str, int] = {}
    for item in items:
        if item["type"] == "order":
            ref = item["data"].get("order_id") or item["data"].get("order_number")
            if ref in seen_orders:
                index = seen_orders[ref]
                if item["data"].get("detail") or not out[index]["data"].get("detail"):
                    out[index] = item
                continue
            seen_orders[ref] = len(out)
        out.append(item)
    return out


def _remember(items: list[dict[str, Any]], session: Session) -> None:
    """Push this turn's entities onto the session's context stack, oldest first so the most
    specific thing (a detail card) ends up at the front."""
    for item in items:
        kind, data = item["type"], item["data"]
        if kind == "order":
            session.remember_context("order", data.get("order_number") or "", data.get("order_id") or "", limit=MAX_CONTEXT)
            if data.get("customer_name") and data.get("customer_id"):
                session.remember_context("customer", data["customer_name"], data["customer_id"], limit=MAX_CONTEXT)
        elif kind == "customer":
            session.remember_context("customer", data.get("name") or "", data.get("customer_id") or "", limit=MAX_CONTEXT)
        elif kind == "email_thread":
            session.remember_context("email", data.get("subject") or "(no subject)", data.get("thread_id") or "", limit=MAX_CONTEXT)
        elif kind in {"inventory", "product"}:
            for p in data.get("products", [])[:1]:
                session.remember_context("product", p.get("title") or "", p.get("product_id") or "", limit=MAX_CONTEXT)


# --------------------------------------------------------------------------- helpers


def _ui(kind: str, data: dict[str, Any]) -> dict[str, Any]:
    return {"type": kind, "data": data}


def _list(value: Any, limit: int) -> list[Any]:
    if not isinstance(value, list):
        return []
    return [v for v in value[:limit] if isinstance(v, dict)]


def _text(value: Any, limit: int = MAX_TEXT_CHARS) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _float(value: Any) -> float | None:
    try:
        return None if value is None or isinstance(value, bool) else float(value)
    except (TypeError, ValueError):
        return None


def _status(value: Any) -> str:
    """Shopify's SHOUTED_ENUMS, as words: PARTIALLY_FULFILLED -> "partially fulfilled"."""
    return _text(value).replace("_", " ").lower()


def _order_number(value: Any) -> str:
    """The store names orders "CROOKS-1928" and older ones "#1036"; the card says #1928."""
    text = _text(value)
    digits = text.rsplit("-", 1)[-1].lstrip("#").strip()
    return f"#{digits}" if digits.isdigit() else text


def _money_text(value: Any) -> str:
    """The tools return "430.50 GBP"; the card shows £430.50."""
    text = _text(value)
    if not text:
        return ""
    parts = text.split()
    if len(parts) == 2:
        amount, currency = parts
        try:
            return _money_display(float(amount), currency) or text
        except ValueError:
            return text
    return text


def _money_display(amount: float | None, currency: str) -> str | None:
    if amount is None:
        return None
    symbol = _CURRENCY_SYMBOL.get((currency or "").upper())
    if symbol:
        return f"{symbol}{amount:,.2f}"
    return f"{amount:,.2f} {currency}".strip()


def _sales_day(day: object, currency: str) -> dict:
    day = day if isinstance(day, dict) else {}
    revenue = _float(day.get("revenue"))
    return {
        "date": _text(day.get("date")),
        "orders": _int(day.get("orders")),
        "revenue": _money_display(revenue, currency) if revenue is not None else None,
    }


def _window_title(result: dict[str, Any]) -> str:
    days = _int(result.get("days")) or 1
    ago = _int(result.get("days_ago")) or 0
    if days == 1 and ago == 0:
        return "Today"
    if days == 1 and ago == 1:
        return "Yesterday"
    if days == 7 and ago == 0:
        return "Last 7 days"
    if ago == 0:
        return f"Last {days} days"
    return f"{days} day{'s' if days != 1 else ''}, ending {ago} day{'s' if ago != 1 else ''} ago"
