"""The general read tools: one bounded query language over the store's recent orders instead
of a tool for every question. `commerce_aggregate` counts and totals by product, size, colour,
day, customer…; `commerce_query` lists orders or customers that match; `inventory_query`
ranks variants by how soon they run out; `commerce_capabilities` says, concisely, what the
language can express. All of them read; none of them can change anything."""

from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Any

from app.analytics import engine
from app.analytics.cache import OrderCache
from app.analytics.periods import MAX_DAYS, NAMED, Period
from app.analytics.query import (
    ENTITIES,
    FILTERS,
    GROUPS,
    MAX_COST,
    MAX_LIMIT,
    METRICS,
    TURN_COST,
    VIEWS,
    Query,
    QueryError,
    parse,
)
from app.tools.context import current_session
from app.tools.gate import Tier
from app.tools.registry import ToolError, tool

log = logging.getLogger("crooks.analytics")

_cache: OrderCache | None = None
READ_TIMEOUT_S = 6.0
PLANNED = frozenset({"commerce_aggregate", "commerce_query", "inventory_query"})
# What the model reads of a result: never the membership lists the Mac keeps for itself.
_MODEL_HIDDEN = ("member_ids", "variant_ids")


def bind(cache: OrderCache | None) -> None:
    global _cache
    _cache = cache


def cache() -> OrderCache:
    if _cache is None:
        raise ToolError("The order cache is not configured on this backend.")
    return _cache


async def _now_and_zone() -> tuple[datetime, Any]:
    client = cache()._client()
    zone = await client.timezone()
    return datetime.now(zone), zone


def sets_for(session: Any) -> dict[str, frozenset[str]]:
    """The working sets the conversation holds, as the engine wants them."""
    out: dict[str, frozenset[str]] = {}
    for set_id, ws in (getattr(session, "sets", None) or {}).items():
        members = getattr(ws, "members", None)
        if members is not None:
            out[str(set_id)] = frozenset(str(m) for m in members)
    return out


def _model_view(result: Any) -> Any:
    if not isinstance(result, dict):
        return result
    out = {k: v for k, v in result.items() if k not in _MODEL_HIDDEN}
    if isinstance(out.get("rows"), list):
        out["rows"] = [{k: v for k, v in r.items() if k not in _MODEL_HIDDEN} for r in out["rows"] if isinstance(r, dict)]
    if isinstance(out.get("compare"), dict) and isinstance(out["compare"].get("rows"), list):
        out["compare"] = {**out["compare"], "rows": [{k: v for k, v in r.items() if k not in _MODEL_HIDDEN} for r in out["compare"]["rows"] if isinstance(r, dict)]}
    return out


def _sets_in(query: Query) -> None:
    session = current_session()
    held = sets_for(session)
    for key in ("in_set", "not_in_set"):
        set_id = query.filters.get(key)
        if set_id and set_id not in held:
            raise ToolError(f"There is no working set {set_id} in this conversation. Use the set id the last listing gave you.")


async def _run(spec: dict[str, Any], *, default_entity: str) -> dict[str, Any]:
    now, zone = await _now_and_zone()
    try:
        query = parse(spec, now=now, tz=zone, default_entity=default_entity)
    except QueryError as exc:
        raise ToolError(f"Query not understood: {exc}") from exc
    _sets_in(query)
    started = time.perf_counter()
    window = query.period.previous().start if query.compare else query.period.start
    view = await cache().view(Period(window, query.period.end, query.period.label, query.period.kind), timeout_s=READ_TIMEOUT_S)
    stock: dict[str, dict[str, Any]] = {}
    if query.needs_stock:
        selected = engine.select(view.rows, query.period, query.filters, now=now.timestamp(), sets=sets_for(current_session()))
        wanted = {i["variant_id"] for o in selected for i in engine.matching_items(o, query.filters) if i.get("variant_id")}
        stock = await cache().stock(sorted(wanted)[:400], timeout_s=READ_TIMEOUT_S)
    result = engine.aggregate(query, view.rows, now=now.timestamp(), tz=zone, stock=stock, sets=sets_for(current_session()))
    result["complete"] = view.complete and not result.get("truncated", False) or (view.complete and result.get("truncated", False))
    result["coverage"] = {"complete": view.complete, "covered_days": view.covered_days, "read_age_s": (round(view.age_s, 1) if view.age_s is not None else None), "note": view.note or None}
    result["source"] = "Shopify orders created in the period" + (f", as read by the Mac {round(view.age_s)} s ago" if view.age_s is not None else "")
    result["cost"] = query.cost
    result["_ms"] = round((time.perf_counter() - started) * 1000 + view.served_ms, 1)
    if view.note:
        result["note"] = (result.get("note") + " " if result.get("note") else "") + view.note
    return result


# --------------------------------------------------------------------------- the tools

_PERIOD_DESC = "today, yesterday, this_week, last_week, this_month, last_month, last_7_days, last_30_days, last_90_days, since_launch, {\"days\": N} or {\"start\",\"end\"}. Default last_30_days."
_FILTERS_DESC = "Common: product (words, e.g. 'pink joggers'), size, colour, fulfillment (unfulfilled|partial|fulfilled), payment, country_code, tags, min_total, older_than_days, customer_id, in_set; customers: min_orders, min_spent, repeat, no_later_order. commerce_capabilities lists all."
_VIEW_DESC = "auto (default), ranking, table, comparison, matrix, metrics, trend or list."


@tool(
    name="commerce_aggregate",
    description=(
        "Count and total orders over a period, grouped and sorted as asked: best sellers by units "
        "or revenue, sales by size, colour or day, customers by spend, average order value, this "
        "period against the one before. Nearly any question about what sold, to whom, when, is one call."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "entity": {"type": "string", "description": "order_line_items (default; what sold), orders, customers, products or variants."},
            "period": {"description": _PERIOD_DESC},
            "filters": {"type": "object", "description": _FILTERS_DESC},
            "group_by": {"type": "array", "items": {"type": "string"}, "description": "Up to two of product, product_type, variant, size, colour, day, week, month, customer, country, fulfillment, payment."},
            "metrics": {"type": "array", "items": {"type": "string"}, "description": "units, revenue, orders, customers, aov, refunded, unfulfilled_value, share; variants/products: stock, velocity, days_cover; customers: lifetime_orders, lifetime_spent."},
            "sort": {"type": "array", "items": {"type": "object"}, "description": "[{\"metric\": \"units\", \"direction\": \"desc\"}]; default the first metric, descending."},
            "limit": {"type": "integer", "description": f"1-{MAX_LIMIT}, default 10."},
            "compare": {"type": "boolean", "description": "Also the period before, with the change."},
            "view": {"type": "string", "description": _VIEW_DESC},
            "title": {"type": "string", "description": "A short card title in the owner's words."},
        },
    },
    tier=Tier.GREEN,
    model_view=_model_view,
)
async def commerce_aggregate(entity: str = "order_line_items", period: Any = None, filters: dict | None = None, group_by: Any = None, metrics: Any = None, sort: Any = None, limit: int = 10, compare: bool = False, view: str = "auto", title: str = "") -> dict:
    return await _run({"entity": entity, "period": period, "filters": filters or {}, "group_by": group_by, "metrics": metrics, "sort": sort, "limit": limit, "compare": compare, "view": view, "title": title}, default_entity="order_line_items")


@tool(
    name="commerce_query",
    description=(
        "List the orders or customers that match: unfulfilled orders older than five days, customers "
        "who bought the pink joggers and nothing since. The list becomes a working set ('these'): its "
        "set_id is in the result, and later calls narrow it with filters.in_set."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "entity": {"type": "string", "description": "orders (default) or customers."},
            "period": {"description": _PERIOD_DESC},
            "filters": {"type": "object", "description": _FILTERS_DESC},
            "sort": {"type": "array", "items": {"type": "object"}, "description": "Orders: created_at, total or age_days; customers: a metric. Default newest first."},
            "limit": {"type": "integer", "description": f"Rows shown (1-{MAX_LIMIT}), default 25; the set holds every match."},
            "metrics": {"type": "array", "items": {"type": "string"}, "description": "Customers only: orders, revenue, lifetime_orders, lifetime_spent."},
            "title": {"type": "string", "description": "A short name for the set, in the owner's words."},
        },
    },
    tier=Tier.AMBER,
    model_view=_model_view,
)
async def commerce_query(entity: str = "orders", period: Any = None, filters: dict | None = None, sort: Any = None, limit: int = 25, metrics: Any = None, title: str = "") -> dict:
    spec = {"entity": entity, "period": period, "filters": filters or {}, "sort": sort, "limit": limit, "metrics": metrics, "view": "list", "title": title}
    if str(entity or "").strip().lower() not in ("orders", "order", "customers", "customer"):
        raise ToolError("commerce_query lists orders or customers; for products, sizes or sales use commerce_aggregate.")
    result = await _run(spec, default_entity="orders")
    return result


@tool(
    name="inventory_query",
    description=(
        "Which variants are running out: stock beside units sold over the period, with the velocity "
        "(units a day) and estimated days of cover derived from them, soonest out first. Narrow to a "
        "product, colour or size. Cover is an estimate, not a forecast."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "period": {"description": "The sales window for the velocity; default last_7_days."},
            "product": {"type": "string", "description": "Words that name the product(s), e.g. 'joggers'."},
            "colour": {"type": "string"}, "size": {"type": "string"},
            "limit": {"type": "integer", "description": f"1-{MAX_LIMIT}, default 10."},
            "max_days_cover": {"type": "number", "description": "Only variants with this much cover or less."},
            "title": {"type": "string"},
        },
    },
    tier=Tier.GREEN,
    model_view=_model_view,
)
async def inventory_query(period: Any = None, product: str = "", colour: str = "", size: str = "", limit: int = 10, max_days_cover: float | None = None, title: str = "") -> dict:
    filters: dict[str, Any] = {}
    if product:
        filters["product"] = product
    if colour:
        filters["colour"] = colour
    if size:
        filters["size"] = size
    spec = {"entity": "variants", "period": period or "last_7_days", "filters": filters, "group_by": ["variant"], "metrics": ["stock", "units", "velocity", "days_cover"], "sort": [{"metric": "days_cover", "direction": "asc"}], "limit": limit, "view": "ranking", "title": title or "Restock priority"}
    result = await _run(spec, default_entity="variants")
    if max_days_cover is not None:
        try:
            bound = float(max_days_cover)
        except (TypeError, ValueError) as exc:
            raise ToolError("max_days_cover is a number of days.") from exc
        result["rows"] = [r for r in result["rows"] if r.get("days_cover") is not None and r["days_cover"] <= bound]
    result["note"] = (
        f"Velocity is units sold over the last {int(round(float(result['period']['days'])))} day(s) divided by the days; cover is stock divided by that — "
        "an estimate from recent sales, not a forecast. A variant with no sales in the period has no cover to estimate; one Shopify does not track has no stock figure."
    ) + (" " + result["note"] if result.get("note") else "")
    result["mode"] = "restock_priority"
    return result


@tool(
    name="commerce_capabilities",
    description="What the read language can express: entities, periods, filters, groupings, metrics, views, examples. Call it before saying a question about sales, products, customers or stock cannot be answered.",
    input_schema={"type": "object", "properties": {}},
    tier=Tier.GREEN,
)
async def commerce_capabilities() -> dict:
    return catalogue()


def catalogue() -> dict[str, Any]:
    """The language, concisely, for the model and for the report."""
    return {
        "read_only": True,
        "entities": list(ENTITIES),
        "periods": list(NAMED) + ["{\"days\": N}", "{\"days\": N, \"days_ago\": M}", "{\"start\": \"YYYY-MM-DD\", \"end\": \"YYYY-MM-DD\"}"],
        "timezone": "Europe/London", "max_days": MAX_DAYS,
        "filters": {name: {"type": kind.split(":", 1)[0], "values": kind.split(":", 1)[1].split(",") if ":" in kind else None, "entities": list(entities)} for name, (kind, entities) in FILTERS.items()},
        "group_by": list(GROUPS), "metrics": list(METRICS), "views": list(VIEWS),
        "bounds": {"limit": MAX_LIMIT, "group_by": 2, "cost_per_query": MAX_COST, "cost_per_turn": TURN_COST},
        "examples": [
            {"ask": "best sellers this month", "call": {"tool": "commerce_aggregate", "period": "this_month", "group_by": ["product"], "metrics": ["units", "revenue"], "view": "ranking"}},
            {"ask": "which size of the black joggers sells most", "call": {"tool": "commerce_aggregate", "entity": "variants", "filters": {"product": "black joggers"}, "group_by": ["size"], "metrics": ["units"]}},
            {"ask": "compare this week with last week", "call": {"tool": "commerce_aggregate", "entity": "orders", "period": "this_week", "metrics": ["orders", "revenue", "aov"], "compare": True, "view": "comparison"}},
            {"ask": "what needs restocking", "call": {"tool": "inventory_query", "period": "last_7_days"}},
            {"ask": "unfulfilled orders older than five days", "call": {"tool": "commerce_query", "entity": "orders", "period": "last_90_days", "filters": {"fulfillment": "unfulfilled", "older_than_days": 5}}},
            {"ask": "customers who spent over £250", "call": {"tool": "commerce_aggregate", "entity": "customers", "period": "last_90_days", "filters": {"min_spent": 250}, "metrics": ["lifetime_spent", "lifetime_orders"]}},
            {"ask": "revenue tied up in unfulfilled orders", "call": {"tool": "commerce_aggregate", "entity": "orders", "period": "last_90_days", "filters": {"fulfillment": "unfulfilled"}, "metrics": ["orders", "unfulfilled_value"], "view": "metrics"}},
        ],
    }


def cost_of(name: str, args: dict[str, Any]) -> int:
    """The estimate the plan charges before the tool runs; a query the language refuses costs one."""
    try:
        spec = dict(args)
        if name == "inventory_query":
            spec = {"entity": "variants", "period": spec.get("period") or "last_7_days", "metrics": ["days_cover"], "limit": spec.get("limit", 10)}
        return parse(spec, default_entity="orders" if name == "commerce_query" else "order_line_items").cost
    except QueryError:
        return 1
