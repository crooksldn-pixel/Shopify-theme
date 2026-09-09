"""The bounded query language: what the model may ask of the store's recent orders, typed and
checked here before anything is read. Not SQL, not GraphQL, not code — a small vocabulary of
entities, filters, groupings and metrics, each with bounds, and a cost the Mac estimates
before it runs. A name outside the vocabulary is refused by name, so the refusal can be
counted later as a dimension worth adding."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from app.analytics.periods import MAX_DAYS, Period, PeriodError, resolve

ENTITIES = ("orders", "order_line_items", "customers", "products", "variants")
GROUPS = ("product", "product_type", "variant", "size", "colour", "day", "week", "month", "customer", "country", "fulfillment", "payment")
METRICS = (
    "units", "revenue", "orders", "customers", "aov", "refunded", "unfulfilled_units", "unfulfilled_value", "share",
    "stock", "velocity", "days_cover", "lifetime_orders", "lifetime_spent", "last_order_at", "first_order_at", "age_days",
)
# What is read from Shopify as it is, and what the Mac works out from it. The result says which.
MEASURED = frozenset({"units", "revenue", "orders", "customers", "refunded", "unfulfilled_units", "unfulfilled_value", "stock", "lifetime_orders", "lifetime_spent", "last_order_at", "first_order_at"})
DERIVED = frozenset({"aov", "share", "velocity", "days_cover", "age_days"})
VIEWS = ("auto", "ranking", "table", "comparison", "matrix", "metrics", "trend", "list")

# Each filter: the type it takes and the entities it applies to. "*" is every entity.
FILTERS: dict[str, tuple[str, tuple[str, ...]]] = {
    "product": ("text", ("*",)), "product_id": ("id", ("*",)), "variant_id": ("id", ("*",)), "sku": ("text", ("*",)),
    "size": ("text", ("*",)), "colour": ("text", ("*",)), "product_type": ("text", ("*",)),
    "fulfillment": ("enum:unfulfilled,partial,fulfilled,any", ("*",)), "payment": ("enum:paid,pending,refunded,partially_refunded,partially_paid,any", ("*",)),
    "cancelled": ("enum:false,true,any", ("*",)), "has_tracking": ("bool", ("orders",)),
    "customer_id": ("id", ("*",)), "customer_email": ("text", ("*",)), "country_code": ("country", ("*",)),
    "tags": ("list", ("*",)), "not_tags": ("list", ("*",)),
    "min_total": ("money", ("orders",)), "max_total": ("money", ("orders",)),
    "min_orders": ("int", ("customers",)), "max_orders": ("int", ("customers",)), "min_spent": ("money", ("customers",)), "max_spent": ("money", ("customers",)),
    "repeat": ("bool", ("customers",)), "no_later_order": ("bool", ("customers",)),
    "older_than_days": ("int", ("orders", "order_line_items")), "newer_than_days": ("int", ("orders", "order_line_items")),
    "min_units": ("int", ("order_line_items", "products", "variants")), "max_stock": ("int", ("products", "variants")),
    "in_set": ("set", ("*",)), "not_in_set": ("set", ("*",)),
}
_ALIASES = {"color": "colour", "status": "fulfillment", "paid": "payment", "country": "country_code", "tag": "tags", "since_days": "newer_than_days", "age_days": "older_than_days", "customer": "customer_id"}
_GROUP_ALIASES = {"color": "colour", "date": "day", "daily": "day", "weekly": "week", "monthly": "month", "products": "product", "variants": "variant", "sizes": "size", "colours": "colour", "customers": "customer", "type": "product_type"}
_METRIC_ALIASES = {"quantity": "units", "sold": "units", "sales": "revenue", "gross_revenue": "revenue", "net_revenue": "revenue", "order_count": "orders", "customer_count": "customers", "average_order_value": "aov", "inventory": "stock", "cover": "days_cover", "stock_cover": "days_cover", "sales_velocity": "velocity", "refund_amount": "refunded"}

MAX_LIMIT = 50
DEFAULT_LIMIT = 10
MAX_GROUPS = 2
MAX_COST = 12          # one query
TURN_COST = 30         # every analytic query in one turn, together
MAX_LIST = 10
_ID = re.compile(r"^gid://shopify/(Order|Customer|Product|ProductVariant)/\d+$")
_ID_KIND = {"customer_id": "Customer", "product_id": "Product", "variant_id": "ProductVariant", "order_id": "Order"}
_SET = re.compile(r"^set_[0-9a-f]{6,}$")
_TEXT = re.compile(r"^[^<>{}\[\]\\]{1,80}$")


class QueryError(ValueError):
    """A query outside the language. `unknown` names what was asked for and does not exist —
    the observability layer counts those as dimensions worth adding."""

    def __init__(self, message: str, *, unknown: list[str] | None = None) -> None:
        super().__init__(message)
        self.unknown = list(unknown or [])


@dataclass(frozen=True, slots=True)
class Query:
    entity: str
    period: Period
    filters: dict[str, Any]
    group_by: tuple[str, ...]
    metrics: tuple[str, ...]
    sort: tuple[tuple[str, str], ...]     # (metric or key, "desc"|"asc")
    limit: int
    compare: bool
    view: str
    title: str
    cost: int
    extra: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "entity": self.entity, "period": self.period.as_dict(), "filters": dict(self.filters), "group_by": list(self.group_by),
            "metrics": list(self.metrics), "sort": [list(s) for s in self.sort], "limit": self.limit, "compare": self.compare,
            "view": self.view, "title": self.title, "cost": self.cost,
        }

    @property
    def needs_stock(self) -> bool:
        return any(m in ("stock", "velocity", "days_cover") for m in self.metrics) or "max_stock" in self.filters

    @property
    def grouped(self) -> bool:
        return bool(self.group_by) or self.entity in ("products", "variants", "customers")


def _norm(name: Any) -> str:
    return str(name or "").strip().lower().replace("-", "_").replace(" ", "_")


def _coerce(key: str, value: Any, kind: str) -> Any:
    if kind == "text":
        text = " ".join(str(value).split())
        if not _TEXT.match(text):
            raise QueryError(f"{key}: a short plain value, please.")
        return text
    if kind == "id":
        text = str(value).strip()
        wanted = _ID_KIND.get(key, "")
        if not _ID.match(text) or (wanted and not text.startswith(f"gid://shopify/{wanted}/")):
            raise QueryError(f"{key}={text!r} is not a Shopify {wanted or 'id'} id.")
        return text
    if kind == "set":
        text = str(value).strip()
        if not _SET.match(text):
            raise QueryError(f"{key}={text!r} is not a working set id.")
        return text
    if kind == "bool":
        if isinstance(value, bool):
            return value
        text = str(value).strip().lower()
        if text in ("true", "yes", "1"):
            return True
        if text in ("false", "no", "0"):
            return False
        raise QueryError(f"{key} is true or false.")
    if kind in ("int", "money"):
        try:
            number = float(value)
        except (TypeError, ValueError) as exc:
            raise QueryError(f"{key} is a number.") from exc
        if number < 0 or number > 1_000_000:
            raise QueryError(f"{key} is out of range.")
        return int(number) if kind == "int" else round(number, 2)
    if kind == "country":
        text = str(value).strip().upper()
        if not re.match(r"^[A-Z]{2}$", text):
            raise QueryError(f"{key} is a two-letter country code.")
        return text
    if kind == "list":
        items = value if isinstance(value, list) else [v.strip() for v in str(value).split(",")]
        items = [str(v).strip() for v in items if str(v).strip()]
        if not items or len(items) > MAX_LIST or any(not _TEXT.match(v) for v in items):
            raise QueryError(f"{key}: one to {MAX_LIST} short plain values.")
        return items
    if kind.startswith("enum:"):
        allowed = kind[5:].split(",")
        text = str(value).strip().lower().replace(" ", "_")
        if text in ("partially_fulfilled", "partially"):
            text = "partial"
        if text not in allowed:
            raise QueryError(f"{key} is one of {', '.join(allowed)}.")
        return text
    raise QueryError(f"{key} cannot be read.")


def parse(spec: dict[str, Any], *, now: datetime | None = None, tz: str | ZoneInfo = "Europe/London", default_entity: str = "order_line_items") -> Query:
    """The model's request, checked and normalised, or a QueryError that says what was wrong
    and names anything unknown. Pure: no store, no clock beyond `now`."""
    if not isinstance(spec, dict):
        raise QueryError("The query is an object.")
    unknown: list[str] = []
    entity = _norm(spec.get("entity") or default_entity)
    entity = {"line_items": "order_line_items", "items": "order_line_items", "sales": "order_line_items", "order": "orders", "product": "products", "variant": "variants", "customer": "customers"}.get(entity, entity)
    if entity not in ENTITIES:
        raise QueryError(f"entity is one of {', '.join(ENTITIES)}.", unknown=[f"entity:{entity}"])
    try:
        period = resolve(spec.get("period", spec.get("date_range")), now=now, tz=tz)
    except PeriodError as exc:
        raise QueryError(str(exc)) from exc

    filters: dict[str, Any] = {}
    raw_filters = spec.get("filters") if isinstance(spec.get("filters"), dict) else {}
    for key, value in raw_filters.items():
        name = _ALIASES.get(_norm(key), _norm(key))
        if value is None or value == "":
            continue
        if name not in FILTERS:
            unknown.append(f"filter:{name}")
            continue
        kind, entities = FILTERS[name]
        if "*" not in entities and entity not in entities:
            raise QueryError(f"filter {name} does not apply to {entity}.")
        filters[name] = _coerce(name, value, kind)
    if unknown:
        raise QueryError(f"Unknown filter(s): {', '.join(u.split(':', 1)[1] for u in unknown)}. Filters are {', '.join(FILTERS)}.", unknown=unknown)
    filters.setdefault("cancelled", "false")

    groups: list[str] = []
    raw_groups = spec.get("group_by")
    if isinstance(raw_groups, str):
        raw_groups = [raw_groups]
    for g in raw_groups or []:
        name = _GROUP_ALIASES.get(_norm(g), _norm(g))
        if name not in GROUPS:
            unknown.append(f"group:{name}")
        elif name not in groups:
            groups.append(name)
    if unknown:
        raise QueryError(f"Unknown group_by: {', '.join(u.split(':', 1)[1] for u in unknown)}. Groups are {', '.join(GROUPS)}.", unknown=unknown)
    if len(groups) > MAX_GROUPS:
        raise QueryError(f"group_by takes at most {MAX_GROUPS} dimensions.")
    if entity == "products" and "product" not in groups:
        groups = ["product"] + [g for g in groups if g != "product"][: MAX_GROUPS - 1]
    if entity == "variants" and not groups:
        groups = ["variant"]
    if entity == "customers" and "customer" not in groups:
        groups = ["customer"]
    if entity == "orders" and groups:
        raise QueryError("orders lists orders; to group, ask for order_line_items, products, variants or customers.")

    metrics: list[str] = []
    raw_metrics = spec.get("metrics")
    if isinstance(raw_metrics, str):
        raw_metrics = [raw_metrics]
    for m in raw_metrics or []:
        name = _METRIC_ALIASES.get(_norm(m), _norm(m))
        if name not in METRICS:
            unknown.append(f"metric:{name}")
        elif name not in metrics:
            metrics.append(name)
    if unknown:
        raise QueryError(f"Unknown metric(s): {', '.join(u.split(':', 1)[1] for u in unknown)}. Metrics are {', '.join(METRICS)}.", unknown=unknown)
    if not metrics:
        metrics = {"orders": ["orders", "revenue", "unfulfilled_value"], "customers": ["orders", "revenue", "lifetime_orders", "lifetime_spent"], "variants": ["units", "revenue"], "products": ["units", "revenue"]}.get(entity, ["units", "revenue"])
    if any(m in ("stock", "velocity", "days_cover") for m in metrics) and entity not in ("variants", "products"):
        raise QueryError("stock, velocity and days_cover apply to variants or products.")
    if any(m in ("lifetime_orders", "lifetime_spent", "last_order_at", "first_order_at") for m in metrics) and entity != "customers":
        raise QueryError("lifetime_orders, lifetime_spent, last_order_at and first_order_at apply to customers.")
    if "age_days" in metrics and entity != "orders":
        raise QueryError("age_days applies to orders.")
    if "velocity" in metrics and "units" not in metrics:
        metrics.append("units")
    if "days_cover" in metrics:
        for needed in ("stock", "velocity", "units"):
            if needed not in metrics:
                metrics.append(needed)

    sort: list[tuple[str, str]] = []
    raw_sort = spec.get("sort")
    if isinstance(raw_sort, (str, dict)):
        raw_sort = [raw_sort]
    for s in raw_sort or []:
        if isinstance(s, str):
            raw = s.strip()
            direction = "asc" if raw.startswith("+") else "desc"
            key = _norm(raw.lstrip("+-"))
        elif isinstance(s, dict):
            key = _METRIC_ALIASES.get(_norm(s.get("metric") or s.get("by") or s.get("key")), _norm(s.get("metric") or s.get("by") or s.get("key")))
            direction = _norm(s.get("direction") or "desc")
        else:
            raise QueryError("sort is a list of {metric, direction}.")
        key = _METRIC_ALIASES.get(key, key)
        if direction not in ("asc", "desc"):
            raise QueryError("sort direction is asc or desc.")
        if key not in metrics and key not in groups and key not in ("created_at", "placed_at", "age_days", "total"):
            raise QueryError(f"sort by {key}: not one of the metrics or groups asked for ({', '.join(metrics + groups)}).")
        sort.append((key, direction))
    if not sort:
        if entity == "orders":
            sort = [("created_at", "desc")]
        elif "days_cover" in metrics:
            sort = [("days_cover", "asc")]
        elif entity == "customers":
            sort = [("lifetime_spent" if "lifetime_spent" in metrics else metrics[0], "desc")]
        else:
            sort = [(metrics[0], "desc")]

    limit = spec.get("limit", DEFAULT_LIMIT)
    try:
        limit = int(limit)
    except (TypeError, ValueError) as exc:
        raise QueryError("limit is a whole number.") from exc
    if limit < 1 or limit > MAX_LIMIT:
        raise QueryError(f"limit is 1..{MAX_LIMIT}.")

    compare = spec.get("compare")
    compare = bool(compare) and str(compare).lower() not in ("false", "none", "0", "")
    view = _norm(spec.get("view") or "auto")
    if view not in VIEWS:
        raise QueryError(f"view is one of {', '.join(VIEWS)}.", unknown=[f"view:{view}"])
    title = " ".join(str(spec.get("title") or "").split())[:60]
    if title and not _TEXT.match(title):
        title = ""

    cost = estimate_cost(entity, period, groups, metrics, limit, compare)
    if cost > MAX_COST:
        raise QueryError(f"That query is too expensive to run at once (cost {cost} > {MAX_COST}): narrow the period, drop the comparison, or ask for fewer rows.")
    return Query(entity=entity, period=period, filters=filters, group_by=tuple(groups), metrics=tuple(metrics), sort=tuple(sort), limit=limit, compare=compare, view=view, title=title, cost=cost)


def estimate_cost(entity: str, period: Period, groups: list[str], metrics: list[str], limit: int, compare: bool) -> int:
    """Points, before anything runs: a month of orders is one, each grouping one more, a stock
    join a couple, a comparison doubles the period. Bounded per query and per turn."""
    days = period.days * (2 if compare else 1)
    cost = max(1, int(-(-days // 30)))
    cost += len(groups)
    if any(m in ("stock", "velocity", "days_cover") for m in metrics):
        cost += 2 + (1 if limit > 25 else 0)
    if entity == "customers":
        cost += 1
    if days > MAX_DAYS:
        cost += 4
    return cost
