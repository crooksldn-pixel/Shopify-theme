"""The recipes themselves.

Each one is a plan (which reads, and which of them are independent) and a render (the one
sentence that answers, and the cards behind it). Between them they cover the work the
September test session showed being done over and over: an order, a customer, a period's
sales, the inbox's reply state, moving through a set, and the two questions the assistant is
asked about itself.

Nothing here writes. Nothing here calls a model.
"""

from __future__ import annotations

import time
from typing import Any

from app.fastpath.models import Ctx, FastAnswer
from app.fastpath.recipes import (
    CACHE_ANALYTICS,
    CACHE_EMAIL,
    CACHE_ENTITY,
    CACHE_HOT,
    CACHE_NONE,
    Recipe,
    register,
)
from app.reads.scheduler import Read, ReadPlan, ReadResult

# --------------------------------------------------------------- shared helpers

# The named periods, from the words that name them. Deliberately narrow: a period the map
# does not recognise sends the turn to Claude rather than guessing at "the last little while".
_PERIODS: tuple[tuple[tuple[str, ...], str], ...] = (
    (("today",), "today"),
    (("yesterday",), "yesterday"),
    (("last", "week"), "last_week"),
    (("this", "week"), "this_week"),
    (("last", "month"), "last_month"),
    (("this", "month"), "this_month"),
    (("week",), "this_week"),
    (("month",), "this_month"),
)
_DAY_WINDOWS = {"7": "last_7_days", "seven": "last_7_days", "30": "last_30_days", "thirty": "last_30_days", "90": "last_90_days", "ninety": "last_90_days"}


def period_from(words: tuple[str, ...]) -> str | None:
    """The named period the request asks for, or None when it names none — or names two.

    "This week against last week" is two periods and a comparison, and which one is the
    subject is a judgement rather than a lookup. A deterministic parser that guesses there
    would answer the wrong question quickly, so it declines and Claude takes the turn.
    """
    have = set(words)
    if {"this", "last"} <= have or {"today", "yesterday"} <= have:
        return None
    if "days" in have or "day" in have:
        for word in words:
            if word in _DAY_WINDOWS:
                return _DAY_WINDOWS[word]
    for needed, name in _PERIODS:
        if set(needed) <= have:
            return name
    return None


# "By colour", "by size", "per day": a grouping the read layer already has a name for.
# Closed set, taken from app/analytics/query.py GROUPS — a word that is not one of these is
# not guessed at, and the turn goes to Claude, who can ask what was meant.
_DIMENSIONS: dict[str, str] = {
    "colour": "colour", "color": "colour", "colours": "colour", "colors": "colour",
    "size": "size", "sizes": "size", "product": "product", "products": "product",
    "variant": "variant", "variants": "variant", "type": "product_type", "types": "product_type",
    "day": "day", "daily": "day", "week": "week", "weekly": "week", "month": "month",
    "monthly": "month", "country": "country", "customer": "customer", "customers": "customer",
}


def dimension_from(words: tuple[str, ...]) -> str | None:
    """The grouping the request names after "by" or "per", when it names exactly one."""
    found: set[str] = set()
    for index, word in enumerate(words):
        if word in ("by", "per") and index + 1 < len(words):
            group = _DIMENSIONS.get(words[index + 1])
            if group:
                found.add(group)
    return next(iter(found)) if len(found) == 1 else None


def _order_of(result: ReadResult, name: str = "find") -> dict[str, Any] | None:
    """The one order a search found, when it found exactly one."""
    found = result.values.get(name)
    orders = found.get("orders") if isinstance(found, dict) else None
    if isinstance(orders, list) and len(orders) == 1 and isinstance(orders[0], dict):
        return orders[0]
    return None


def _hedge(body: dict[str, Any]) -> str:
    """What the read itself says about its own completeness, added to the answer rather than
    left in the payload for nobody. The order cache says `complete: False` with a `note`
    while it is still filling — which is exactly the first questions after a restart."""
    if not isinstance(body, dict) or body.get("complete") is not False:
        return ""
    note = " ".join(str(body.get("note") or "").split())
    return f" {note}" if note else " The Mac is still reading recent orders, so this is what it holds so far."


def _how_many(body: dict[str, Any], shown: int) -> str:
    """How many there are, not how many fitted. A limit of 25 against 61 matching orders was
    being spoken as "25 orders are unfulfilled"."""
    total = body.get("row_count")
    if isinstance(total, int) and total > shown:
        return f"{total} (showing {shown})"
    return str(shown)


def _period_words(body: dict[str, Any], fallback: str = "the period") -> str:
    """The period as a person says it. The read layer's own label first; its slug, spelled
    out, second — "last_30_days" was being read aloud with the underscores in it."""
    period = body.get("period") if isinstance(body.get("period"), dict) else {}
    label = str(period.get("label") or "").strip()
    if label:
        return label
    slug = str(period.get("name") or period.get("period") or "").strip()
    return slug.replace("_", " ") if slug else fallback


# What the Mac's own reads call money. Shopify's shape is already a string with its currency
# in it ("45.00 GBP"); the read layer's is a bare number with the currency beside it. One
# answer must not contain both shapes.
_SYMBOL = {"GBP": "£", "USD": "$", "EUR": "€"}


def _money(value: Any, currency: str = "GBP") -> str:
    if isinstance(value, str):
        parts = value.split()
        if len(parts) == 2 and parts[1].isalpha():
            value, currency = parts[0], parts[1].upper()
    try:
        return f"{_SYMBOL.get(currency.upper(), currency.upper() + ' ')}{float(value):,.2f}"
    except (TypeError, ValueError):
        return str(value or "")


def _order_line(order: dict[str, Any]) -> str:
    """An order in a sentence: who, how much, and where it has got to."""
    number = str(order.get("order_number") or "").lstrip("#")
    who = str((order.get("customer") or {}).get("name") or order.get("customer_name") or "").strip()
    total = _money(order.get("total") or order.get("total_price"))
    state = str(order.get("fulfillment_status") or order.get("fulfillment") or "").replace("_", " ").lower()
    bits = [f"{number}" if number else "That order"]
    if who:
        bits.append(f"is {who}'s")
    if total:
        bits.append(f"for {total}")
    line = " ".join(bits)
    if state and state not in ("null", "none"):
        line += f", {state}"
    return line + "."


def _remember(ctx: Ctx, kind: str, ref: str, label: str, *, tab: str = "") -> None:
    ctx.branch.visit(kind, ref, label, tab=tab)
    ctx.session.remember_context(kind, label, ref)
    ctx.session.set_focus(kind, ref)


# ------------------------------------------------------------ capability truth


def _capability_plan(ctx: Ctx) -> ReadPlan | None:      # noqa: ARG001 — no source is read
    return None


def _capability_summary(ctx: Ctx, result: ReadResult) -> FastAnswer:   # noqa: ARG001
    # Imported by name, not as a module: app/capabilities/__init__.py re-exports `delta` and
    # `build` as functions, so `from app.capabilities import delta` gets the function and
    # `delta_mod.spoken_delta` is an AttributeError at the worst possible moment.
    from app.capabilities.manifest import build as build_manifest
    from app.capabilities.manifest import spoken_summary
    from app.capabilities.surface import build_surface

    manifest = getattr(ctx.runtime, "manifest", None)
    if not manifest:
        # Built here only if the runtime has none, and never with writes assumed on: saying
        # "I can change things" while changes are switched off is the worst answer available.
        settings = getattr(ctx.runtime, "settings", None)
        manifest = build_manifest(build_id=getattr(ctx.runtime, "build", ""), writes_enabled=bool(getattr(settings, "writes_enabled", False)))
    spoken = spoken_summary(manifest)
    # The sentence and the card are built from the same manifest, so the screen cannot list a
    # capability the spoken answer denies. Thirty capabilities are a list, not a paragraph.
    surface = build_surface(manifest, spoken=spoken, states=_capability_states(ctx))
    return FastAnswer(answer=spoken, surfaces=[surface],
                      trace={"source": "manifest", "fingerprint": manifest.get("fingerprint")})


def _capability_states(ctx: Ctx) -> dict[str, dict[str, Any]] | None:
    """The per-change table /health computed on its last run, when there is one.

    Read from the runtime's cache rather than recomputed: working out whether a change is
    possible asks Shopify and Google for their scopes, and a question about what the assistant
    can do must not become two network round trips. Absent, every change reads as "unknown",
    which is the honest answer when nobody has checked.
    """
    cached = getattr(ctx.runtime, "capability_states", None)
    return cached if isinstance(cached, dict) and cached else None


def _capability_delta(ctx: Ctx, result: ReadResult) -> FastAnswer:     # noqa: ARG001
    from app.capabilities.delta import delta as compute_delta
    from app.capabilities.delta import spoken_delta
    from app.capabilities.surface import build_surface

    record = getattr(ctx.runtime, "capability_record", None)
    if not record:
        return FastAnswer(answer="", defer="no capability record on this backend")
    spoken = spoken_delta(record)
    current = record.get("current") if isinstance(record.get("current"), dict) else {}
    moved = compute_delta(record)
    surface = build_surface(
        current or {}, spoken=spoken, states=_capability_states(ctx),
        changed={
            "since": moved.get("previous_build") or "",
            "added": [f"{e.get('name')}: {e.get('what')}" for e in (moved.get("added") or [])],
            "gone": [f"{e.get('name')}: {e.get('what')}" for e in (moved.get("removed") or [])],
        },
    )
    return FastAnswer(answer=spoken, surfaces=[surface],
                      trace={"source": "capability delta", "fingerprint": (record.get("current") or {}).get("fingerprint")})


register(Recipe(
    recipe_id="capability_summary", intent_family="capability_summary",
    read_primitives=(), ui="capability", cache_policy=CACHE_NONE, min_confidence=0.7,
    target_ms=50, plan=_capability_plan, render=_capability_summary,
))
register(Recipe(
    recipe_id="capability_delta", intent_family="capability_delta",
    read_primitives=(), ui="capability", cache_policy=CACHE_NONE, min_confidence=0.7,
    target_ms=50, plan=_capability_plan, render=_capability_delta,
))


# ------------------------------------------------------------------ navigation


def _nav_plan(ctx: Ctx) -> ReadPlan | None:     # noqa: ARG001
    return None


def _command(ctx: Ctx, name: str) -> FastAnswer:
    """A spoken instruction that is a semantic command, handed to the one implementation of it.

    Back, Forward and Home are the same operations a tap performs, and there is now one of
    each rather than two. `app/commands.py` is where they live; this is the spoken door into
    them, and it contains no navigation logic of its own.
    """
    from app import commands

    outcome = commands.run(name, commands.Ctx(ctx.runtime, ctx.session, ctx.branch))
    return FastAnswer(answer=outcome.answer, calls=list(outcome.calls),
                      surfaces=list(outcome.surfaces), trace={"command": name, **outcome.changed})


def _nav_back(ctx: Ctx, result: ReadResult) -> FastAnswer:      # noqa: ARG001
    return _command(ctx, "navigation.back")


def _nav_home(ctx: Ctx, result: ReadResult) -> FastAnswer:      # noqa: ARG001
    return _command(ctx, "navigation.home")


def _replay(ctx: Ctx, entry) -> list[Any]:
    """A card rebuilt from what the Mac still holds, rather than read again. Nothing is shown
    that memory cannot supply; a stop whose entry has gone leaves the sentence on its own."""
    from app.memory import ENTITY
    from app.memory import current as memory
    from app.providers.base import ToolCall

    held = memory().get(ENTITY, f"{entry.kind}:{entry.ref}", allow_stale=True)
    if held is None:
        return []
    tool = {"order": "shopify_order_detail", "customer": "shopify_customer_history", "email_thread": "gmail_read_thread"}.get(entry.kind, "")
    if not tool:
        return []
    return [ToolCall(name=tool, args={f"{entry.kind}_id": entry.ref}, ok=True, result=held.value)]


register(Recipe(recipe_id="navigation_back", intent_family="navigation_back", ui="context_stack",
                cache_policy=CACHE_HOT, min_confidence=0.75, target_ms=100, plan=_nav_plan, render=_nav_back))
register(Recipe(recipe_id="navigation_home", intent_family="navigation_home", ui="context_stack",
                cache_policy=CACHE_HOT, min_confidence=0.75, target_ms=100, plan=_nav_plan, render=_nav_home))


# -------------------------------------------------------------- working sets

def _member_plan(ctx: Ctx) -> ReadPlan | None:
    """The read for wherever the cursor now points. One read, of one member."""
    workflow = ctx.branch.workflow
    if workflow is None:
        return None
    from app.analytics import sets as working_sets

    ws = working_sets.get(ctx.session, workflow.set_id)
    if ws is None or not ws.members:
        return None
    ref = ws.members[min(max(workflow.cursor, 0), len(ws.members) - 1)]
    tool, arg = {"orders": ("shopify_order_detail", "order_id"), "customers": ("shopify_customer_history", "customer_id"),
                 "emails": ("gmail_read_thread", "thread_id")}.get(ws.kind, ("", ""))
    if not tool:
        return None
    return ReadPlan([Read("member", tool, {arg: ref}, source="gmail" if tool.startswith("gmail_") else "shopify")], label=f"workflow:{ws.kind}")


def _member_answer(ctx: Ctx, result: ReadResult) -> FastAnswer:
    from app.analytics import sets as working_sets

    workflow = ctx.branch.workflow
    ws = working_sets.get(ctx.session, workflow.set_id) if workflow else None
    if workflow is None or ws is None or not ws.members:
        return FastAnswer(answer="", defer="the set this was working through has gone")
    ref = ws.members[min(max(workflow.cursor, 0), len(ws.members) - 1)]
    label = ws.labels.get(ref) or ref
    if ref not in workflow.visited:
        workflow.visited.append(ref)
    where = f"{workflow.position} of {workflow.total}"
    body = result.values.get("member")
    if isinstance(body, dict):
        kind = {"orders": "order", "customers": "customer", "emails": "email_thread"}.get(ws.kind, "order")
        _remember(ctx, kind, ref, label)
        if ws.kind == "orders":
            head = _order_line(body)
        elif ws.kind == "customers":
            head = _customer_line(body, label)
        else:
            head = f"{body.get('subject') or label}."
        return FastAnswer(answer=f"{head} {where}.", calls=list(result.calls), partial=result.partial,
                          trace={"set_id": ws.set_id, "cursor": workflow.cursor, "ref": ref})
    return FastAnswer(answer=f"{label}. {where}. I could not read the rest of it just now.",
                      partial=True, trace={"set_id": ws.set_id, "cursor": workflow.cursor, "ref": ref, "read": "failed"})


def _next(ctx: Ctx, result: ReadResult) -> FastAnswer:
    return _member_answer(ctx, result)


def _previous(ctx: Ctx, result: ReadResult) -> FastAnswer:
    return _member_answer(ctx, result)


register(Recipe(
    recipe_id="working_set_next", intent_family="working_set_next", required_entities=("workflow",),
    read_primitives=("shopify_order_detail", "shopify_customer_history", "gmail_read_thread"),
    ui="order", cache_policy=CACHE_ENTITY, min_confidence=0.75, target_ms=750,
    plan=_member_plan, render=_next,
))
register(Recipe(
    recipe_id="working_set_previous", intent_family="working_set_previous", required_entities=("workflow",),
    read_primitives=("shopify_order_detail", "shopify_customer_history", "gmail_read_thread"),
    ui="order", cache_policy=CACHE_ENTITY, min_confidence=0.75, target_ms=750,
    plan=_member_plan, render=_previous,
))


# ------------------------------------------------------------------- an order


def _order_plan(ctx: Ctx) -> ReadPlan | None:
    """Find the order, then read it in full. The second read depends on the first, so the
    plan is two waves rather than one — and says so."""
    number = ctx.order_number
    known = ctx.entity("order")
    if number:
        return ReadPlan([
            Read("find", "shopify_find_order", {"query": number}, source="shopify", cost=30.0),
            Read("detail", "shopify_order_detail", _detail_args, source="shopify", after=("find",), cost=90.0),
        ], label="order_lookup")
    if known:
        return ReadPlan([Read("detail", "shopify_order_detail", {"order_id": known}, source="shopify", cost=90.0)], label="order_lookup")
    return None


def _detail_args(values: dict[str, Any]) -> dict[str, Any] | None:
    found = values.get("find")
    orders = found.get("orders") if isinstance(found, dict) else None
    if isinstance(orders, list) and len(orders) == 1 and isinstance(orders[0], dict) and orders[0].get("order_id"):
        return {"order_id": str(orders[0]["order_id"])}
    return None


def _order_render(ctx: Ctx, result: ReadResult) -> FastAnswer:
    detail = result.values.get("detail")
    if not isinstance(detail, dict):
        found = _order_of(result)
        if found is None:
            return FastAnswer(answer="", defer="the order did not resolve to exactly one record")
        _remember(ctx, "order", str(found.get("order_id") or ""), str(found.get("order_number") or ""))
        return FastAnswer(answer=_order_line(found), calls=list(result.calls), partial=True, trace={"detail": "not read"})
    _remember(ctx, "order", str(detail.get("order_id") or ""), str(detail.get("order_number") or ""), tab="overview")
    items = detail.get("items") or []
    line = _order_line(detail)
    if items:
        first = items[0] if isinstance(items[0], dict) else {}
        more = f" and {len(items) - 1} more" if len(items) > 1 else ""
        line += f" {first.get('quantity') or 1} × {first.get('title') or 'item'}{more}."
    return FastAnswer(answer=line, calls=list(result.calls), partial=result.partial, trace={"order_id": detail.get("order_id")})


def _status_render(ctx: Ctx, result: ReadResult) -> FastAnswer:
    detail = result.values.get("detail")
    if not isinstance(detail, dict):
        return FastAnswer(answer="", defer="the order was not read")
    _remember(ctx, "order", str(detail.get("order_id") or ""), str(detail.get("order_number") or ""), tab="shipping")
    number = str(detail.get("order_number") or "").lstrip("#")
    fulfilments = [f for f in (detail.get("fulfillments") or []) if isinstance(f, dict)]
    state = str(detail.get("fulfillment_status") or "").replace("_", " ").lower() or "not fulfilled"
    if fulfilments:
        first = fulfilments[0]
        carrier = str(first.get("company") or first.get("carrier") or "").strip()
        tracking = str(first.get("tracking_number") or "").strip()
        words = f"{number} went out{f' with {carrier}' if carrier else ''}"
        if tracking:
            words += f", tracking {tracking}"
        return FastAnswer(answer=words + ".", calls=list(result.calls), trace={"order_id": detail.get("order_id"), "state": state})
    age = detail.get("age_days")
    tail = f" It was placed {int(age)} days ago." if isinstance(age, (int, float)) and age else ""
    return FastAnswer(answer=f"{number} is {state}; nothing has shipped yet.{tail}", calls=list(result.calls), trace={"order_id": detail.get("order_id"), "state": state})


def _address_render(ctx: Ctx, result: ReadResult) -> FastAnswer:
    """The full shipping address, because the owner asked for it. The card carries it; the
    spoken line carries it too, which is the point of the question. Neither reaches the
    timeline: dispatch writes a result's shape, never its contents."""
    detail = result.values.get("detail")
    if not isinstance(detail, dict):
        return FastAnswer(answer="", defer="the order was not read")
    address = detail.get("shipping_address")
    if not isinstance(address, dict):
        return FastAnswer(answer=f"{str(detail.get('order_number') or 'That order').lstrip('#')} has no shipping address on it.",
                          calls=list(result.calls), trace={"address": "none"})
    _remember(ctx, "order", str(detail.get("order_id") or ""), str(detail.get("order_number") or ""), tab="shipping")
    ctx.session.remember_pii(*[str(v) for v in address.get("lines") or []], str(address.get("zip") or ""), str(address.get("name") or ""))
    parts = [*(address.get("lines") or []), address.get("city"), address.get("province"), address.get("zip"), address.get("country")]
    written = ", ".join(str(p).strip() for p in parts if str(p or "").strip())
    who = str(address.get("name") or "").strip()
    number = str(detail.get("order_number") or "").lstrip("#")
    return FastAnswer(answer=f"{number} ships to {who + ', ' if who else ''}{written}.", calls=list(result.calls),
                      trace={"order_id": detail.get("order_id"), "address": "read"})


register(Recipe(
    recipe_id="order_lookup", intent_family="order_lookup", required_entities=("order",),
    read_primitives=("shopify_find_order", "shopify_order_detail"),
    parallel_nodes=(("find",), ("detail",)), ui="order", cache_policy=CACHE_ENTITY,
    min_confidence=0.75, target_ms=1000, plan=_order_plan, render=_order_render,
))
register(Recipe(
    recipe_id="order_status_lookup", intent_family="order_status_lookup", required_entities=("order",),
    read_primitives=("shopify_find_order", "shopify_order_detail"),
    parallel_nodes=(("find",), ("detail",)), ui="order", cache_policy=CACHE_ENTITY,
    min_confidence=0.75, target_ms=1000, plan=_order_plan, render=_status_render,
))
register(Recipe(
    recipe_id="order_address_lookup", intent_family="order_address_lookup", required_entities=("order",),
    read_primitives=("shopify_find_order", "shopify_order_detail"),
    parallel_nodes=(("find",), ("detail",)), ui="order", cache_policy=CACHE_ENTITY,
    min_confidence=0.72, target_ms=1000, plan=_order_plan, render=_address_render,
))


# ----------------------------------------------------------------- a customer


def _order_list_plan(ctx: Ctx) -> ReadPlan | None:
    """The orders in a period, as a list. `shopify_list_orders` already returns the shape the
    order_list card is built from, so this is one read and one card."""
    days, days_ago = _period_days(ctx.intent.signals.words)
    return ReadPlan([Read("listing", "shopify_list_orders", {"days": days, "days_ago": days_ago, "limit": 10},
                          source="shopify", cost=90.0)], label="order_list_period")


def _period_days(words: tuple[str, ...]) -> tuple[int, int]:
    """How wide a window the question asked for, and how far back it starts.

    Deliberately small: the fast lane takes "today", "yesterday" and "this week" and defers
    anything cleverer to the read layer, which can parse a period properly.
    """
    have = set(words)
    if "yesterday" in have:
        return 1, 1
    if "week" in have:
        return 7, 0
    if "month" in have:
        return 30, 0
    return 1, 0


def _order_list_render(ctx: Ctx, result: ReadResult) -> FastAnswer:
    """A sentence about the shape of the list, and the list itself on screen.

    The sentence deliberately does not read the orders out. Seven orders spoken is a minute of
    talking nobody listens to; "seven today, three still to go out" is what a person says, and
    the rows are there to be looked at and tapped.
    """
    body = result.values.get("listing")
    if not isinstance(body, dict):
        return FastAnswer(answer="", defer="the order list did not come back")
    orders = [o for o in (body.get("orders") or []) if isinstance(o, dict)]
    period = "today" if int(body.get("days") or 1) == 1 and not int(body.get("days_ago") or 0) else "in that period"
    if not orders:
        return FastAnswer(answer=f"No orders {period}.", calls=list(result.calls), trace={"rows": 0})
    # The set the cursor walks, so "next" and a tap on the third row mean the same thing.
    _open_workflow(ctx, body, kind="orders", operation="review", set_id=_set_id_of(body))
    unfulfilled = sum(1 for o in orders if "unfulfilled" in str(o.get("fulfillment") or "").lower())
    words = f"{len(orders)} order{'s' if len(orders) != 1 else ''} {period}"
    if unfulfilled:
        words += f"; {unfulfilled} still to go out"
    more = " There are more than I have shown." if body.get("truncated") else ""
    return FastAnswer(answer=words + "." + more, calls=list(result.calls), partial=result.partial,
                      trace={"rows": len(orders), "unfulfilled": unfulfilled})


register(Recipe(
    recipe_id="order_list_period", intent_family="order_list_period",
    read_primitives=("shopify_list_orders",), parallel_nodes=(("listing",),), ui="order_list",
    cache_policy=CACHE_HOT, min_confidence=0.74, target_ms=900,
    plan=_order_list_plan, render=_order_list_render,
))
# Showing the open order again is the same procedure as looking it up: `_order_plan` already
# falls back to the branch's current entity when no number was said, which is exactly this
# case. A second recipe rather than a second condition, because recipe_for maps one family to
# one recipe and the two families are genuinely different questions.
register(Recipe(
    recipe_id="order_reopen", intent_family="order_reopen", required_entities=("order",),
    read_primitives=("shopify_order_detail",), parallel_nodes=(("detail",),), ui="order",
    cache_policy=CACHE_ENTITY, min_confidence=0.74, target_ms=700,
    plan=_order_plan, render=_order_render,
))


def _customer_plan(ctx: Ctx) -> ReadPlan | None:
    """A name this branch has already resolved needs no search: read the history straight."""
    said = ctx.intent.slots.get("name") or ""
    known = ctx.branch.resolve(said) if said else None
    if known and known.get("kind") == "customer":
        return ReadPlan([Read("history", "shopify_customer_history", {"customer_id": known["ref"]}, source="shopify", cost=60.0)], label="customer_lookup")
    if said:
        return ReadPlan([
            Read("find", "shopify_find_customer", {"query": said}, source="shopify", cost=30.0),
            Read("history", "shopify_customer_history", _history_args, source="shopify", after=("find",), cost=60.0),
        ], label="customer_lookup")
    return None


def _history_args(values: dict[str, Any]) -> dict[str, Any] | None:
    found = values.get("find")
    people = found.get("customers") if isinstance(found, dict) else None
    if isinstance(people, list) and len(people) == 1 and isinstance(people[0], dict) and people[0].get("customer_id"):
        return {"customer_id": str(people[0]["customer_id"])}
    return None


def _customer_line(history: dict[str, Any], fallback: str = "") -> str:
    """A customer in a sentence, from the shape `shape_customer_history` actually returns:
    `orders` is a COUNT (an int, or None when Shopify did not say) and `spent` is already
    money as a string. Reading them as a list and a number produced "0 orders, in total" for
    every customer walked with "Next" — a confident sentence that was simply false."""
    name = str(history.get("name") or fallback or "They").strip()
    count = history.get("orders")
    spent = str(history.get("spent") or "").strip()
    if not isinstance(count, int):
        # Shopify did not give a count. Say what is known and nothing more.
        return f"{name}." if not spent else f"{name}, {spent} spent with us."
    orders = "no orders yet" if count == 0 else f"{count} order{'' if count == 1 else 's'}"
    return f"{name}: {orders}" + (f", {spent} in total." if spent else ".")


def _customer_render(ctx: Ctx, result: ReadResult) -> FastAnswer:
    history = result.values.get("history")
    if not isinstance(history, dict):
        return FastAnswer(answer="", defer="the customer did not resolve to exactly one record")
    name = str(history.get("name") or ctx.intent.slots.get("name") or "").strip()
    ref = str(history.get("customer_id") or "")
    _remember(ctx, "customer", ref, name, tab="orders")
    if ctx.intent.slots.get("name"):
        ctx.branch.learn(ctx.intent.slots["name"], "customer", ref, name)
    recent = [o for o in (history.get("recent") or []) if isinstance(o, dict)]
    last = recent[0] if recent else {}
    tail = ""
    if last:
        tail = f" The last was {str(last.get('order_number') or '').lstrip('#')}"
        if last.get("total"):
            tail += f", {_money(last['total'])}"
        if last.get("placed_at"):
            tail += f" on {str(last['placed_at'])[:10]}"
        tail += "."
    return FastAnswer(answer=_customer_line(history, name) + tail, calls=list(result.calls),
                      partial=result.partial, trace={"customer_id": ref})


def _customer_history_plan(ctx: Ctx) -> ReadPlan | None:
    """"What else has this customer ordered?" — the person is whoever the open record belongs
    to, so nothing has to be resolved from the words.

    Two shapes. With a customer open it is one read. With an ORDER open the customer is not
    known until the order has been read, so it is two waves — the same find-then-detail
    pattern the order recipes use, and the scheduler runs them in dependency order.
    """
    customer = ctx.entity("customer")
    if customer:
        return ReadPlan([Read("history", "shopify_customer_history", {"customer_id": customer},
                              source="shopify", cost=60.0)], label="customer_history")
    order = ctx.entity("order")
    if order:
        return ReadPlan([
            Read("detail", "shopify_order_detail", {"order_id": order}, source="shopify", cost=90.0),
            Read("history", "shopify_customer_history", _history_from_order, source="shopify", after=("detail",), cost=60.0),
        ], label="customer_history")
    return None


def _history_from_order(values: dict[str, Any]) -> dict[str, Any] | None:
    detail = values.get("detail")
    customer = detail.get("customer") if isinstance(detail, dict) else None
    ref = customer.get("customer_id") if isinstance(customer, dict) else None
    return {"customer_id": str(ref)} if ref else None


def _customer_history_render(ctx: Ctx, result: ReadResult) -> FastAnswer:
    """The same card and the same sentence as a lookup by name — this is the same question
    asked a different way, and answering it differently would be a second implementation of
    one thing. What differs is only how the customer was found."""
    return _customer_render(ctx, result)


register(Recipe(
    recipe_id="customer_history_lookup", intent_family="customer_history_lookup",
    required_entities=("customer", "order"),
    read_primitives=("shopify_order_detail", "shopify_customer_history"),
    parallel_nodes=(("detail",), ("history",)), ui="customer", cache_policy=CACHE_ENTITY,
    min_confidence=0.74, target_ms=1500, plan=_customer_history_plan, render=_customer_history_render,
))


register(Recipe(
    recipe_id="customer_purchase_lookup", intent_family="customer_purchase_lookup", required_entities=("customer",),
    read_primitives=("shopify_find_customer", "shopify_customer_history"),
    parallel_nodes=(("find",), ("history",)), ui="customer", cache_policy=CACHE_ENTITY,
    min_confidence=0.72, target_ms=1500, plan=_customer_plan, render=_customer_render,
))


# ----------------------------------------------------------------- the numbers


def _best_sellers_plan(ctx: Ctx) -> ReadPlan | None:
    words = ctx.intent.signals.words
    period = period_from(words)
    if period is None:
        # No period named at all is "recently" and has a sensible default; a period the map
        # DECLINED (two of them, an ambiguity) must not be defaulted over — that is exactly
        # the case it declined for. The sibling recipe honours this and so must this one.
        if ctx.intent.signals.period:
            return None
        period = "last_30_days"
    # "By colour" and "by size" are the same question with one dimension changed, which is
    # what the read layer is for. A "by" the map does not know is not guessed at: the plan
    # declines and Claude takes the turn.
    if any(w in ("by", "per") for w in words):
        group = dimension_from(words)
        if group is None:
            return None
    else:
        group = "product"
    entity = "variants" if group in ("size", "colour", "variant") else "order_line_items"
    return ReadPlan([Read("agg", "commerce_aggregate", {
        "entity": entity, "period": period, "group_by": [group],
        "metrics": ["units", "revenue"], "sort": [{"metric": "units", "direction": "desc"}],
        "limit": 10, "view": "ranking", "title": f"Best sellers by {group}" if group != "product" else "Best sellers",
    }, source="shopify", cost=120.0)], label="best_sellers")


def _breakdown_plan(ctx: Ctx) -> ReadPlan | None:
    period = period_from(ctx.intent.signals.words)
    if period is None:
        return None
    return ReadPlan([Read("agg", "commerce_aggregate", {
        "entity": "orders", "period": period, "metrics": ["revenue", "orders", "aov"],
        "compare": True, "view": "metrics", "title": "Sales",
    }, source="shopify", cost=120.0)], label="sales_breakdown")


def _aggregate_render(ctx: Ctx, result: ReadResult) -> FastAnswer:
    body = result.values.get("agg")
    if not isinstance(body, dict):
        return FastAnswer(answer="", defer="the read layer did not answer")
    # The analytics tool itself records the query it ran (app/tools/analytics_tools.py); the
    # payload has no `query` key, and writing one from it set the follow-up hint to None.
    rows = [r for r in (body.get("rows") or []) if isinstance(r, dict)]
    period = _period_words(body)
    if not rows:
        totals = body.get("totals") or {}
        if totals:
            return FastAnswer(answer=_totals_line(totals, period, str(body.get("currency") or "GBP")) + _hedge(body), calls=list(result.calls), trace={"rows": 0})
        return FastAnswer(answer=f"Nothing sold in {period}." + _hedge(body), calls=list(result.calls), trace={"rows": 0})
    top = rows[0]
    label = str(top.get("label") or top.get("product") or "").strip()
    units = top.get("units")
    words = f"Best in {period}: {label}"
    if units is not None:
        words += f", {int(units)} units"
    if top.get("revenue") is not None:
        words += f" and {_money(top['revenue'], str(body.get('currency') or 'GBP'))}"
    if len(rows) > 1:
        second = rows[1]
        words += f". Then {str(second.get('label') or '').strip()}"
        if second.get("units") is not None:
            words += f" on {int(second['units'])}"
    return FastAnswer(answer=words + "." + _hedge(body), calls=list(result.calls), partial=result.partial, trace={"rows": len(rows), "period": period})


def _totals_line(totals: dict[str, Any], period: str, currency: str = "GBP") -> str:
    bits = []
    if totals.get("revenue") is not None:
        bits.append(_money(totals["revenue"], currency))
    if totals.get("orders") is not None:
        bits.append(f"{int(totals['orders'])} orders")
    if totals.get("aov") is not None:
        bits.append(f"{_money(totals['aov'], currency)} average")
    head = period[:1].upper() + period[1:] if period else "The period"
    return (f"{head}: " + ", ".join(bits) + ".") if bits else f"Nothing to report for {period}."


def _breakdown_render(ctx: Ctx, result: ReadResult) -> FastAnswer:
    body = result.values.get("agg")
    if not isinstance(body, dict):
        return FastAnswer(answer="", defer="the read layer did not answer")
    totals = body.get("totals") or {}
    period = _period_words(body)
    line = _totals_line(totals, period, str(body.get("currency") or "GBP"))
    # The engine's shape is {metric: {"from", "to", "delta", "pct"}}. Reading a `revenue_pct`
    # that has never existed meant the comparison was requested, paid for in query cost, and
    # thrown away — half an answer to the question actually asked.
    compare = body.get("compare") if isinstance(body.get("compare"), dict) else {}
    change = compare.get("change") if isinstance(compare.get("change"), dict) else {}
    moved = change.get("revenue") if isinstance(change.get("revenue"), dict) else change.get("orders")
    if isinstance(moved, dict) and isinstance(moved.get("pct"), (int, float)):
        pct = moved["pct"]
        before = _period_words(compare, fallback="the period before")
        line += f" That is {abs(pct):.0f}% {'up on' if pct >= 0 else 'down on'} {before}."
    return FastAnswer(answer=line + _hedge(body), calls=list(result.calls), partial=result.partial, trace={"period": period})


register(Recipe(
    recipe_id="best_sellers_period", intent_family="best_sellers_period",
    read_primitives=("commerce_aggregate",), parallel_nodes=(("agg",),), ui="ranking",
    cache_policy=CACHE_ANALYTICS, min_confidence=0.72, target_ms=2500,
    plan=_best_sellers_plan, render=_aggregate_render,
))
register(Recipe(
    recipe_id="sales_breakdown_period", intent_family="sales_breakdown_period",
    read_primitives=("commerce_aggregate",), parallel_nodes=(("agg",),), ui="metric_group",
    cache_policy=CACHE_ANALYTICS, min_confidence=0.72, target_ms=2500,
    plan=_breakdown_plan, render=_breakdown_render,
))


# ------------------------------------------------------------- late and low


def _delayed_plan(ctx: Ctx) -> ReadPlan | None:
    # Ninety days, as the read layer's own catalogue answers this question: an order that has
    # been waiting forty-five days is the one that matters most, and a thirty-day window is
    # exactly the window that cannot see it.
    return ReadPlan([Read("late", "commerce_query", {
        "entity": "orders", "period": "last_90_days", "filters": {"fulfillment": "unfulfilled", "older_than_days": 5},
        "sort": [{"metric": "age_days", "direction": "desc"}], "limit": 25, "title": "Waiting to go out",
    }, source="shopify", cost=120.0)], label="delayed_orders")


def _delayed_render(ctx: Ctx, result: ReadResult) -> FastAnswer:
    body = result.values.get("late")
    if not isinstance(body, dict):
        return FastAnswer(answer="", defer="the read layer did not answer")
    rows = [r for r in (body.get("rows") or []) if isinstance(r, dict)]
    _open_workflow(ctx, body, kind="orders", operation="review")
    if not rows:
        return FastAnswer(answer="Nothing is sitting unfulfilled past five days." + _hedge(body), calls=list(result.calls), trace={"rows": 0})
    oldest = rows[0]
    return FastAnswer(
        answer=f"{_how_many(body, len(rows))} orders are unfulfilled past five days; the oldest is {str(oldest.get('order_number') or '').lstrip('#')} at {int(oldest.get('age_days') or 0)} days." + _hedge(body),
        calls=list(result.calls), partial=result.partial, trace={"rows": len(rows), "row_count": body.get("row_count")},
    )


def _stock_plan(ctx: Ctx) -> ReadPlan | None:
    return ReadPlan([Read("stock", "inventory_query", {"period": period_from(ctx.intent.signals.words) or "last_7_days", "limit": 10}, source="shopify", cost=120.0)], label="stock_cover")


def _stock_render(ctx: Ctx, result: ReadResult) -> FastAnswer:
    body = result.values.get("stock")
    if not isinstance(body, dict):
        return FastAnswer(answer="", defer="the read layer did not answer")
    rows = [r for r in (body.get("rows") or []) if isinstance(r, dict)]
    if not rows:
        return FastAnswer(answer="Nothing is close to running out on recent sales." + _hedge(body), calls=list(result.calls), trace={"rows": 0})
    first = rows[0]
    cover = first.get("days_cover")
    words = f"Closest to running out: {str(first.get('label') or '').strip()}"
    if isinstance(cover, (int, float)):
        words += f", about {cover:.0f} days of cover"
    if first.get("stock") is not None:
        words += f" on {int(first['stock'])} in stock"
    return FastAnswer(answer=words + f". {_how_many(body, len(rows))} on the list." + _hedge(body), calls=list(result.calls), partial=result.partial, trace={"rows": len(rows)})


register(Recipe(
    recipe_id="delayed_orders", intent_family="delayed_orders", read_primitives=("commerce_query",),
    parallel_nodes=(("late",),), ui="table", cache_policy=CACHE_ANALYTICS, min_confidence=0.72,
    target_ms=2500, plan=_delayed_plan, render=_delayed_render,
))
register(Recipe(
    recipe_id="stock_cover_analysis", intent_family="stock_cover_analysis", read_primitives=("inventory_query",),
    parallel_nodes=(("stock",),), ui="ranking", cache_policy=CACHE_ANALYTICS, min_confidence=0.72,
    target_ms=2500, plan=_stock_plan, render=_stock_render,
))


# ------------------------------------------------------------------ the inbox


def _inbox_plan(ctx: Ctx) -> ReadPlan | None:
    return ReadPlan([Read("inbox", "gmail_search", {"query": "", "days": 7, "limit": 12}, source="gmail", cost=2.0)], label="inbox_state")


def _inbox_render(ctx: Ctx, result: ReadResult) -> FastAnswer:
    body = result.values.get("inbox")
    if not isinstance(body, dict):
        return FastAnswer(answer="", defer="the inbox did not answer")
    threads = [t for t in (body.get("threads") or []) if isinstance(t, dict)]
    real = [t for t in threads if not t.get("likely_bulk")]
    if not real:
        return FastAnswer(answer="Nothing from a person in the inbox this week.", calls=list(result.calls), trace={"threads": 0})
    newest = real[0]
    return FastAnswer(answer=f"{len(real)} threads from people this week; the newest is {newest.get('from') or 'someone'} about {newest.get('subject') or 'no subject'}.",
                      calls=list(result.calls), partial=result.partial, trace={"threads": len(real)})


def _needs_reply_plan(ctx: Ctx) -> ReadPlan | None:
    """Who is waiting on us: recent customers, then their inbox state, at customer level and
    across threads. Two waves — the second needs the set the first makes."""
    return ReadPlan([
        Read("customers", "commerce_query", {"entity": "customers", "period": "last_30_days", "limit": 25, "title": "Recent customers"}, source="shopify", cost=120.0),
        Read("mail", "email_query", _needs_reply_args, source="gmail", after=("customers",), cost=8.0, timeout_s=10.0),
    ], label="needs_reply", timeout_s=16.0)


def _needs_reply_args(values: dict[str, Any]) -> dict[str, Any] | None:
    set_id = _set_id_of(values.get("customers"))
    return {"set_id": set_id, "days": 30} if set_id else None


def _set_id_of(body: Any, key: str = "set") -> str:
    """The working set a listing made. The read layer publishes it under `set` (the whole
    public shape) — `set_id` at the top level is what the batch tools' own results use — so
    both are looked for rather than one being assumed."""
    if not isinstance(body, dict):
        return ""
    held = body.get(key)
    if isinstance(held, dict) and held.get("set_id"):
        return str(held["set_id"])
    return str(body.get("set_id") or "")


def _needs_reply_render(ctx: Ctx, result: ReadResult) -> FastAnswer:
    body = result.values.get("mail")
    if not isinstance(body, dict):
        return FastAnswer(answer="", defer="the inbox correlation did not come back")
    rows = [r for r in (body.get("rows") or []) if isinstance(r, dict)]
    waiting = [r for r in rows if r.get("needs_reply")]
    counts = body.get("counts") or {}
    unchecked = int(counts.get("unchecked") or 0)
    total = int(counts.get("contacted") or 0) + int(counts.get("not_contacted") or 0) + unchecked or len(rows)
    # Only when there IS a set of people waiting. Falling back to the parent set would leave
    # the branch walking twenty-five customers under an operation called "reply", most of whom
    # are not waiting for one.
    waiting_set = _set_id_of(body, "set_needs_reply")
    if waiting_set:
        _open_workflow(ctx, body, kind="customers", operation="reply", set_id=waiting_set)
    if not waiting:
        tail = f" {unchecked} could not be checked." if unchecked else ""
        return FastAnswer(answer=f"Nobody is waiting on a reply — {len(rows)} of {total} customers checked.{tail}", calls=list(result.calls),
                          partial=bool(unchecked) or result.partial, trace={"rows": len(rows), "waiting": 0, "unchecked": unchecked})
    names = ", ".join(str(r.get("customer_name") or "someone") for r in waiting[:3])
    tail = f" {unchecked} could not be checked." if unchecked else ""
    return FastAnswer(
        answer=f"{len(waiting)} of {len(rows)} customers checked are waiting on a reply: {names}{' and others' if len(waiting) > 3 else ''}.{tail}",
        calls=list(result.calls), partial=bool(unchecked) or result.partial,
        trace={"rows": len(rows), "waiting": len(waiting), "unchecked": unchecked},
    )


def _open_workflow(ctx: Ctx, body: dict[str, Any], *, kind: str, operation: str, set_id: str = "") -> None:
    """A listing becomes something to work through: the branch takes its cursor to the top.
    "Next" is then arithmetic, which is the whole point."""
    from app.analytics import sets as working_sets
    from app.session.branch import Workflow

    set_id = set_id or _set_id_of(body)
    if not set_id:
        return
    ws = working_sets.get(ctx.session, set_id)
    if ws is None or not ws.members:
        return
    ctx.branch.set_id = ws.set_id
    # Before the first member, so the first "Next" lands on it — the same place a set adopted
    # by a bare "Next" starts from (app/fastpath/runner.py).
    ctx.branch.workflow = Workflow(workflow_id=f"wf_{int(time.time() * 1000) % 10**9:09d}", set_id=ws.set_id, kind=kind, operation=operation, cursor=-1, total=len(ws.members))


register(Recipe(
    recipe_id="inbox_state", intent_family="inbox_state", read_primitives=("gmail_search",),
    parallel_nodes=(("inbox",),), ui="email_list", cache_policy=CACHE_EMAIL, min_confidence=0.74,
    target_ms=2500, plan=_inbox_plan, render=_inbox_render,
))
register(Recipe(
    recipe_id="needs_reply", intent_family="needs_reply", read_primitives=("commerce_query", "email_query"),
    parallel_nodes=(("customers",), ("mail",)), ui="email_list", cache_policy=CACHE_EMAIL,
    min_confidence=0.74, target_ms=4000, plan=_needs_reply_plan, render=_needs_reply_render,
))
