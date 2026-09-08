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

from app.providers.base import ToolCall
from app.session.models import Session
from app.tools.gate import Tier, classify

# The component vocabulary. The tablet renders exactly these; anything else is dropped there
# too, so a typo here cannot become a blank card.
UI_TYPES = frozenset({
    "assistant", "order", "order_list", "customer", "customer_list", "product", "inventory",
    "sales_summary", "email_list", "email_thread", "email_draft", "attention", "confirmation",
    "success", "error", "context_stack",
})

# Bounds. The tablet is 8 inches wide; more than this is a spreadsheet, not an answer.
MAX_ORDERS = 10
MAX_ITEMS = 12
MAX_CUSTOMERS = 6
MAX_PRODUCTS = 4
MAX_VARIANTS = 16
MAX_MEASUREMENTS = 8
MAX_THREADS = 10
MAX_MESSAGES = 6
MAX_BODY_CHARS = 2_000
MAX_SNIPPET_CHARS = 300
MAX_TEXT_CHARS = 160
MAX_NOTE_CHARS = 400
MAX_CONTEXT = 6

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
) -> list[dict[str, Any]]:
    """The `ui` list for one turn: context cards from the tool results, one error card per
    failed service, and the context stack when the conversation has accumulated one."""
    items: list[dict[str, Any]] = []
    errors: dict[str, dict[str, Any]] = {}

    for call in calls or []:
        if not call.ok:
            error = _tool_error(call, session)
            errors.setdefault(error["data"]["service"], error)
            continue
        if not isinstance(call.result, dict):
            continue
        for item in _from_result(call.name, call.result):
            items.append(item)

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
        })]
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
        out.update({
            "items": [
                {
                    "title": _text(i.get("title")),
                    "variant": _text(i.get("variant")),
                    "sku": _text(i.get("sku")),
                    "quantity": _int(i.get("quantity")),
                    "total": _money_text(i.get("total")),
                }
                for i in _list(o.get("items"), MAX_ITEMS)
            ],
            "items_truncated": bool(o.get("items_truncated")),
            "fulfillments": [
                {
                    "status": _status(f.get("status")),
                    "shipped_at": _text(f.get("shipped_at")),
                    "carrier": _text(f.get("carrier")),
                    "number": _text(f.get("number")),
                }
                for f in _list(o.get("fulfillments"), 6)
            ],
            "cancelled_at": _text(o.get("cancelled_at")),
            "note": _text(o.get("note"), MAX_NOTE_CHARS),
            "ships_to": _text(o.get("ships_to")),
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


def _tool_error(call: ToolCall, session: Session | None) -> dict[str, Any]:
    name = call.name or ""
    issued = session.issued_ids if session is not None else ()
    blocked = classify(name, call.args or {}, issued).tier is Tier.RED
    if name.startswith("shopify_"):
        service, title = "shopify", "Shopify unavailable"
    elif name.startswith("gmail_"):
        service, title = "gmail", "Email unavailable"
    else:
        service, title = "assistant", "Lookup failed"
    if blocked:
        return _error(service, "blocked", "Not allowed", "This assistant is read-only. Nothing was changed.")
    return _error(service, "tool_failed", title, "Ask again in a moment; the answer says what happened.")


def _error(service: str, kind: str, title: str, recovery: str) -> dict[str, Any]:
    return _ui("error", {"service": service, "kind": kind, "title": title, "recovery": recovery})


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
