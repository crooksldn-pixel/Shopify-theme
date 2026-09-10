"""The bounded query language: what the model may ask of the store's recent orders, typed and
checked here before anything is read. Not SQL, not GraphQL, not code — a small vocabulary of
entities, filters, groupings and metrics, each with bounds, and a cost the Mac estimates
before it runs. A name outside the vocabulary is refused by name, so the refusal can be
counted later as a dimension worth adding."""

from __future__ import annotations

import difflib
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

# Each filter: the type it takes, the entities it applies to ("*" is every entity), and every
# name a model might reach for instead. The aliases live in this table rather than in one of
# their own because the manifest and `commerce_capabilities` list them from here: on the
# tablet the planner burned 15 s a turn guessing at names nothing had ever told it, and a
# vocabulary that is not published is a vocabulary that gets guessed.
FILTERS: dict[str, tuple[str, tuple[str, ...], tuple[str, ...]]] = {
    "product": ("text", ("*",), ("product_title", "item", "garment", "style")),
    "product_id": ("id", ("*",), ()),
    "variant": ("text", ("*",), ("variant_title", "option")),
    "variant_id": ("id", ("*",), ()),
    "sku": ("text", ("*",), ("sku_code", "product_code")),
    "size": ("text", ("*",), ()),
    "colour": ("text", ("*",), ("color",)),
    "product_type": ("text", ("*",), ("type", "category")),
    # The value-words here (unfulfilled, fulfilled, paid, refunded, domestic...) are aliases
    # that name a VALUE as well as a filter: `_VALUE_ALIASES` reads them, and they are listed
    # here so that the published vocabulary is the whole vocabulary.
    "fulfillment": ("enum:unfulfilled,partial,fulfilled,any", ("*",),
                    ("status", "fulfilment", "fulfillment_status", "fulfilment_status", "unfulfilled", "fulfilled", "partial", "partially_fulfilled", "unshipped")),
    "payment": ("enum:paid,unpaid,pending,refunded,partially_refunded,partially_paid,any", ("*",),
                ("financial_status", "payment_status", "financial", "paid", "unpaid", "pending", "refunded")),
    "cancelled": ("enum:false,true,any", ("*",), ("canceled", "is_cancelled")),
    "has_tracking": ("bool", ("orders",), ("tracked", "tracking", "has_tracking_number")),
    # Where it is going, against where the shop is (`shop_country_from`). A bool rather than a
    # list of "foreign" codes, because the shop's own country is a fact the shop knows.
    "international": ("bool", ("*",), ("domestic", "overseas", "abroad", "export", "foreign", "outside_the_uk")),
    "customer_id": ("id", ("*",), ("customer",)),
    "customer_email": ("text", ("*",), ("email",)),
    "country_code": ("country", ("*",), ("country", "region", "ships_to", "shipping_country", "destination_country")),
    "city": ("text", ("*",), ("town", "shipping_city", "destination")),
    "tags": ("list", ("*",), ("tag",)),
    "not_tags": ("list", ("*",), ("not_tag", "without_tag", "excluding_tags")),
    "min_total": ("money", ("orders",), ("min_value", "min_amount", "total_min", "value_over", "over")),
    "max_total": ("money", ("orders",), ("max_value", "max_amount", "total_max", "value_under", "under")),
    "min_orders": ("int", ("customers",), ("orders_at_least",)),
    "max_orders": ("int", ("customers",), ()),
    "min_spent": ("money", ("customers",), ("spent_over",)),
    "max_spent": ("money", ("customers",), ()),
    "repeat": ("bool", ("customers",), ("returning",)),
    "no_later_order": ("bool", ("customers",), ("nothing_since",)),
    # How long it has been waiting. Every alias here is a shape a planner actually sent.
    "older_than_days": ("int", ("orders", "order_line_items"),
                        ("age_days", "waiting_days", "days_waiting", "older_than", "at_least_days", "waiting_at_least", "days_old", "min_age_days")),
    "newer_than_days": ("int", ("orders", "order_line_items"),
                        ("since_days", "newer_than", "within_days", "last_days", "max_age_days")),
    "min_units": ("int", ("order_line_items", "products", "variants"), ("units_at_least",)),
    "max_stock": ("int", ("products", "variants"), ("stock_under",)),
    "in_set": ("set", ("*",), ("set_id", "these")),
    "not_in_set": ("set", ("*",), ("not_set",)),
}
# Every alias, derived from the one table above, so a name documented there is a name that
# works and there is no second list to keep in step with it.
ALIASES: dict[str, str] = {alias: name for name, (_k, _e, aliases) in FILTERS.items() for alias in aliases}
_ALIASES = ALIASES

# Aliases that name a VALUE as well as a filter. A planner writes `{"unfulfilled": true}` and
# `{"domestic": true}` at least as often as it writes the filter out properly, and both were
# "Unknown filter" until now. A legal value still wins over the implied one: `{"paid":
# "refunded"}` has always meant payment=refunded and still does.
_VALUE_ALIASES: dict[str, tuple[str, Any]] = {
    "unfulfilled": ("fulfillment", "unfulfilled"), "unshipped": ("fulfillment", "unfulfilled"),
    "fulfilled": ("fulfillment", "fulfilled"), "partial": ("fulfillment", "partial"), "partially_fulfilled": ("fulfillment", "partial"),
    "paid": ("payment", "paid"), "unpaid": ("payment", "unpaid"), "pending": ("payment", "pending"), "refunded": ("payment", "refunded"),
    "domestic": ("international", False), "overseas": ("international", True), "abroad": ("international", True),
    "export": ("international", True), "foreign": ("international", True), "outside_the_uk": ("international", True),
}

# A date window belongs in `period`, but a planner puts it in `filters` — so these are read
# there and folded into the period rather than refused as unknown filters. What a window MEANS
# is decided in one place (app/analytics/periods.py); this only moves it to the right hand.
_WINDOW_FROM = ("date_from", "start_date", "created_at_min", "created_at_from", "since", "after", "from", "start")
_WINDOW_TO = ("date_to", "end_date", "created_at_max", "created_at_to", "until", "before", "to", "end")
_WINDOW_ON = ("date", "on", "day", "created_at", "placed_at")

# Nothing here knows whether a parcel ARRIVED: no carrier or shipping provider is connected,
# and Shopify's fulfilment status says a label was made, not that it was delivered. So
# "delivered"/"undelivered" is refused by name, with what CAN be answered instead — never
# quietly read as "unfulfilled", which is a different fact about a different event. The tablet
# session that asked "are any of our orders undelivered or unfulfilled?" spent three malformed
# queries and 45 s of Claude on a filter that was never going to exist.
DELIVERY_WORD = re.compile(r"\b(?:un)?deliver(?:ed|y|ies|able|s)?\b")
TRACKING_UNAVAILABLE = (
    "delivery status is not available here — no shipping provider is connected, so nothing "
    "knows whether a parcel arrived. Ask for fulfillment (unfulfilled, partial, fulfilled) "
    "or has_tracking instead."
)

# What an orders LISTING can be sorted by, as app/analytics/engine.py:_orders_listing actually
# implements it. Anything else asked of a listing is refused with these named.
LISTING_SORT_KEYS = ("created_at", "total", "age_days")
# The keys the engine has always tolerated on a grouped query even though it sorts those rows
# by metric: kept so that a call which worked yesterday works today.
_LEGACY_SORT_KEYS = ("created_at", "placed_at", "age_days", "total")
# The words a planner sends instead of a key, each with the direction it already carries. ""
# means "whatever direction was asked for". "Oldest" and "waiting longest" are the same
# request as age_days descending, and a listing sorts by created_at ascending for all three —
# one implementation, three ways of saying it.
SORT_WORDS: dict[str, tuple[str, str]] = {
    "oldest": ("created_at", "asc"), "oldest_first": ("created_at", "asc"), "earliest": ("created_at", "asc"),
    "age": ("created_at", "asc"), "waiting": ("created_at", "asc"), "waiting_longest": ("created_at", "asc"),
    "longest_waiting": ("created_at", "asc"), "waited_longest": ("created_at", "asc"), "longest": ("created_at", "asc"),
    "newest": ("created_at", "desc"), "newest_first": ("created_at", "desc"), "latest": ("created_at", "desc"),
    "recent": ("created_at", "desc"), "most_recent": ("created_at", "desc"),
    "created": ("created_at", ""), "created_date": ("created_at", ""), "placed": ("created_at", ""),
    "placed_at": ("created_at", ""), "date": ("created_at", ""), "order_date": ("created_at", ""),
    "highest_value": ("total", "desc"), "biggest": ("total", "desc"), "largest": ("total", "desc"), "highest": ("total", "desc"),
    "lowest_value": ("total", "asc"), "smallest": ("total", "asc"), "lowest": ("total", "asc"),
    "value": ("total", ""), "amount": ("total", ""), "order_total": ("total", ""), "price": ("total", ""),
}
_DIRECTIONS = {
    "asc": "asc", "ascending": "asc", "ascend": "asc", "up": "asc", "increasing": "asc", "oldest_first": "asc",
    "desc": "desc", "descending": "desc", "descend": "desc", "down": "desc", "decreasing": "desc", "newest_first": "desc",
}

# Where the shop ships FROM when nothing says otherwise. CROOKS is in London; a shop that
# moves country is one line of .env (CROOKS_SHOP_COUNTRY_CODE), not a code change.
DEFAULT_SHOP_COUNTRY = "GB"
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
    the observability layer counts those as dimensions worth adding.

    `schema_help` is what the refusal is FOR: the accepted sort keys, the filters that apply
    to this entity, and one minimal spec that works. On the tablet the planner met "sort by :
    not one of the metrics or groups asked for" three times in a row and guessed three more
    shapes, because the refusal said what was wrong and never what would be right.
    """

    def __init__(self, message: str, *, unknown: list[str] | None = None, help: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.unknown = list(unknown or [])
        self.schema_help: dict[str, Any] = dict(help or {})


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
    limit_explicit: bool = False   # the model asked for this many: a set is then the rows shown
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


def filters_for(entity: str) -> list[str]:
    """The filters that apply to this entity, by name."""
    return [name for name, (_kind, entities, _aliases) in FILTERS.items() if "*" in entities or entity in entities]


def sort_keys_for(entity: str, metrics: tuple[str, ...] | list[str] = (), groups: tuple[str, ...] | list[str] = ()) -> list[str]:
    """Everything this query may usefully be sorted by: what it asked for, plus — for a
    listing — the keys the engine sorts orders by. Named in every refusal, so one retry is
    enough. The legacy keys a grouped query still tolerates are not advertised here: the
    engine cannot order a ranking by them, and a refusal must not recommend a no-op."""
    keys = list(metrics) + list(groups) + list(LISTING_SORT_KEYS if entity == "orders" else ())
    return list(dict.fromkeys(k for k in keys if k)) or list(LISTING_SORT_KEYS)


# One worked example per entity, in the shape the tool takes. Short on purpose: it is read
# inside a tool error, where the whole message has to stay under about 500 characters or the
# planner skims it.
_EXAMPLES: dict[str, dict[str, Any]] = {
    "orders": {"entity": "orders", "period": "last_90_days", "filters": {"fulfillment": "unfulfilled"}, "sort": "oldest", "limit": 25},
    "customers": {"entity": "customers", "period": "last_90_days", "filters": {"min_spent": 250}, "metrics": ["lifetime_spent"]},
    "order_line_items": {"entity": "order_line_items", "period": "last_30_days", "group_by": ["product"], "metrics": ["units"], "sort": "units desc"},
    "products": {"entity": "products", "period": "last_30_days", "metrics": ["units"], "sort": "units desc"},
    "variants": {"entity": "variants", "period": "last_7_days", "metrics": ["days_cover"], "limit": 10},
}


def schema_help(entity: str, *, metrics: tuple[str, ...] | list[str] = (), groups: tuple[str, ...] | list[str] = ()) -> dict[str, Any]:
    """What a refused query needs in order to become a valid one, as data rather than prose."""
    known = entity if entity in ENTITIES else "orders"
    return {
        "accepted_sort_keys": sort_keys_for(known, metrics, groups),
        "filters": filters_for(known),
        "example": dict(_EXAMPLES.get(known, _EXAMPLES["orders"])),
    }


def shop_country_from(shop: dict[str, Any] | None, override: str = "") -> str:
    """Where the shop ships FROM — the other half of "international".

    The setting wins when it names something other than the default, so a shop that moves
    country is a line of configuration; otherwise whatever the shop itself reported; GB last.
    The Shop GraphQL query is deliberately NOT extended to ask Shopify for its billing
    country: that one query is where the timezone comes from, and a field the token's scopes
    do not cover would fail all of it. The fixture shop reports one, so this path is exercised.
    """
    code = str(override or "").strip().upper()[:2]
    if code and code != DEFAULT_SHOP_COUNTRY:
        return code
    reported = ""
    if isinstance(shop, dict):
        address = shop.get("billingAddress") if isinstance(shop.get("billingAddress"), dict) else {}
        reported = str(address.get("countryCodeV2") or shop.get("countryCode") or "").strip().upper()[:2]
    return reported or code or DEFAULT_SHOP_COUNTRY


def _refuse_delivery(name: str, *, where: str, entity: str = "orders", kind: str = "") -> None:
    """"delivered" and "undelivered", wherever they are asked for, refused locally and by name.

    Not a filter, not a sort key, not an entity: there is no delivery evidence in this system
    at all. Free-text values are deliberately NOT scanned — a product called "Delivery Bag"
    is a legitimate thing to filter on — so this is checked on keys, entities, groups, sort
    keys and enum values only.
    """
    # `delivery_status` and `not_delivered` are the names a planner actually sends, and an
    # underscore is a word character: "\bdelivery\b" does not match inside "delivery_status".
    if name and DELIVERY_WORD.search(str(name).replace("_", " ")):
        # `unknown` is telemetry — one controlled word and the name asked for — so it carries
        # the KIND of thing, never the sentence the owner will read.
        raise QueryError(f"{where} {name}: {TRACKING_UNAVAILABLE}", unknown=[f"{kind or where}:{name}"], help=schema_help(entity))


def _named_value(key: str, value: Any) -> tuple[str, Any]:
    """A filter named by one of its values — `{"unfulfilled": true}`, `{"domestic": 1}` — as
    the (filter, value) pair it means."""
    target, implied = _VALUE_ALIASES[key]
    kind = FILTERS[target][0]
    text = str(value).strip().lower().replace(" ", "_")
    if kind.startswith("enum:") and text in kind[5:].split(","):
        return target, value            # {"paid": "refunded"}: the value said what it meant
    if text in ("", "none", "null", "true", "yes", "1", "any"):
        return target, implied
    if text in ("false", "no", "0"):
        if kind == "bool":
            return target, not implied  # {"domestic": false} is {"international": true}
        raise QueryError(
            f"{key}: false is ambiguous here — say {target} with the value you mean, e.g. "
            f"{target}: {implied}.", help=schema_help("orders"))
    return target, value                # anything else: _coerce refuses it by name


def _date_window(raw: dict[str, Any]) -> tuple[dict[str, Any], set[str]]:
    """A date window found among the filters, as a period spec, with the keys it used."""
    window: dict[str, Any] = {}
    used: set[str] = set()
    for key, value in raw.items():
        name = _norm(key)
        if value is None or value == "":
            continue
        if name in _WINDOW_FROM:
            window["start"], _ = str(value), used.add(key)
        elif name in _WINDOW_TO:
            window["end"], _ = str(value), used.add(key)
        elif name in _WINDOW_ON:
            window["start"] = window["end"] = str(value)
            used.add(key)
    return window, used


def _sort_pair(raw: Any, *, entity: str) -> tuple[str, str]:
    """One sort item as (key, direction), from any shape a planner sends.

    `{"metric": X, "direction": D}`, `{"key": X, "order": D}`, `{"field": X, "dir": D}`,
    `{"by": X}`, `"oldest"`, `"created_at desc"`, `"-revenue"`, `"total:asc"`, `"waiting
    longest"`. Every one of those was tried on the tablet against a layer that took exactly
    one of them.
    """
    key, direction = "", ""
    if isinstance(raw, dict):
        for field in ("metric", "key", "field", "by", "column", "sort_by", "name", "on"):
            if str(raw.get(field) or "").strip():
                key = str(raw[field])
                break
        for field in ("direction", "order", "dir", "sort_direction", "sort_order", "ordering"):
            text = _norm(raw.get(field))
            if text:
                if text not in _DIRECTIONS:
                    raise QueryError(f"sort direction {text}: asc or desc.", help=schema_help(entity))
                direction = _DIRECTIONS[text]
                break
    elif isinstance(raw, str):
        text = raw.strip()
        if text.startswith("-"):
            direction, text = "desc", text[1:]
        elif text.startswith("+"):
            direction, text = "asc", text[1:]
        # "created_at desc", "total:asc", "units, descending" — the trailing word is the
        # direction when it is one; otherwise the whole string is the key ("waiting longest").
        parts = [p for p in re.split(r"[\s:,]+", text) if p]
        if len(parts) > 1 and _norm(parts[-1]) in _DIRECTIONS:
            direction = _DIRECTIONS[_norm(parts[-1])]
            parts = parts[:-1]
        key = "_".join(parts)
    elif raw is not None:
        raise QueryError("sort is a key, {metric, direction}, or a list of either.", help=schema_help(entity))
    key = _norm(key)
    _refuse_delivery(key, where="sort", entity=entity)
    key = _METRIC_ALIASES.get(key, key)
    if key in SORT_WORDS:
        mapped, implied = SORT_WORDS[key]
        # The word carries its own order: "oldest desc" is not a thing anyone means.
        key, direction = mapped, (implied or direction)
    return key, direction


def parse(spec: dict[str, Any], *, now: datetime | None = None, tz: str | ZoneInfo = "Europe/London",
          default_entity: str = "order_line_items", shop_country: str = "") -> Query:
    """The model's request, checked and normalised, or a QueryError that says what was wrong,
    names anything unknown, and CARRIES the schema that would have worked. Pure: no store, no
    clock beyond `now` — the shop's own country is passed in, never read from anywhere here."""
    try:
        return _parse(spec, now=now, tz=tz, default_entity=default_entity, shop_country=shop_country)
    except QueryError as exc:
        if not exc.schema_help:
            # Every refusal carries the schema, not only the ones raised where the entity's
            # metrics were already known: a planner recovering from "limit is 1..50" needs the
            # same one retry as a planner recovering from a bad sort key.
            exc.schema_help = schema_help(_entity_of(spec, default_entity))
        raise


def _entity_of(spec: Any, default_entity: str) -> str:
    if not isinstance(spec, dict):
        return default_entity
    name = _norm(spec.get("entity") or default_entity)
    return _ENTITY_ALIASES.get(name, name)


_ENTITY_ALIASES = {"line_items": "order_line_items", "items": "order_line_items", "sales": "order_line_items",
                   "order": "orders", "product": "products", "variant": "variants", "customer": "customers"}


def _parse(spec: dict[str, Any], *, now: datetime | None, tz: str | ZoneInfo,
           default_entity: str, shop_country: str) -> Query:
    if not isinstance(spec, dict):
        raise QueryError("The query is an object.")
    unknown: list[str] = []
    entity = _norm(spec.get("entity") or default_entity)
    entity = _ENTITY_ALIASES.get(entity, entity)
    _refuse_delivery(entity, where="entity", entity="orders")
    if entity not in ENTITIES:
        raise QueryError(f"entity is one of {', '.join(ENTITIES)}.", unknown=[f"entity:{entity}"])

    raw_filters = dict(spec.get("filters") or {}) if isinstance(spec.get("filters"), dict) else {}
    window, window_keys = _date_window(raw_filters)
    period_spec = spec.get("period", spec.get("date_range"))
    if window and (period_spec is None or period_spec == ""):
        period_spec = window
    elif window:
        raise QueryError(f"a period ({period_spec!r}) and a date window in filters were both given: keep one.")
    for key in window_keys:
        raw_filters.pop(key, None)
    try:
        period = resolve(period_spec, now=now, tz=tz)
    except PeriodError as exc:
        raise QueryError(str(exc)) from exc

    filters: dict[str, Any] = {}
    for key, value in raw_filters.items():
        given = _norm(key)
        _refuse_delivery(given, where="filter", entity=entity)
        if given in _VALUE_ALIASES and given not in FILTERS:
            name, value = _named_value(given, value)
        else:
            name = _ALIASES.get(given, given)
            if value is None or value == "":
                continue
        if name not in FILTERS:
            unknown.append(f"filter:{name}")
            continue
        kind, entities, _aliases = FILTERS[name]
        if isinstance(value, str):
            # An enum's VALUE can be a delivery word too: {"fulfillment": "delivered"} is the
            # same wrong question as {"delivered": true} and must fail the same way.
            if kind.startswith("enum:") or kind == "bool":
                _refuse_delivery(_norm(value), where=f"filter {name} =", entity=entity, kind="filter_value")
        if "*" not in entities and entity not in entities:
            raise QueryError(f"filter {name} does not apply to {entity}. On {entity}: {', '.join(filters_for(entity))}.")
        filters[name] = _coerce(name, value, kind)
    if unknown:
        # Named, with the nearest thing that exists — not with the whole table, which is 30
        # names and pushes the useful half of the message out of the planner's attention.
        names = [u.split(":", 1)[1] for u in unknown]
        near = [c for n in names for c in difflib.get_close_matches(n, list(FILTERS) + list(ALIASES), n=1)]
        suggestion = f" Did you mean {', '.join(dict.fromkeys(near))}?" if near else ""
        raise QueryError(
            f"Unknown filter(s): {', '.join(names)}.{suggestion} commerce_capabilities lists every filter.",
            unknown=unknown, help=schema_help(entity))
    filters.setdefault("cancelled", "false")
    if "international" in filters:
        # The engine compares an order's country with the shop's, and the shop's is decided
        # here, once, so the comparison is the same in the tool, the recipe and the tests.
        shop_country = (shop_country or DEFAULT_SHOP_COUNTRY).upper()[:2]

    groups: list[str] = []
    raw_groups = spec.get("group_by")
    if isinstance(raw_groups, str):
        raw_groups = [raw_groups]
    for g in raw_groups or []:
        _refuse_delivery(_norm(g), where="group_by", entity=entity)
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
    elif raw_sort is not None and not isinstance(raw_sort, list):
        raise QueryError("sort is a key, {metric, direction}, or a list of either.", help=schema_help(entity, metrics=metrics, groups=groups))
    accepted = sort_keys_for(entity, metrics, groups)
    # What is refused, versus what is recommended: a grouped query may still name created_at
    # or total, as it always could, and those are simply not offered as advice.
    allowed = set(accepted) | (set() if entity == "orders" else set(_LEGACY_SORT_KEYS))
    for s in raw_sort or []:
        key, direction = _sort_pair(s, entity=entity)
        if not key:
            # "sort by :" — the message the tablet saw three times, with nothing after the
            # colon because the key was empty. A refusal that names nothing teaches nothing.
            raise QueryError(f"sort was given no key. Sort {entity} by one of: {', '.join(accepted)}.",
                             help=schema_help(entity, metrics=metrics, groups=groups))
        if key not in allowed:
            # `unknown` is for a name the language does not have AT ALL — a dimension worth
            # adding. Sorting by a metric that exists but was not asked for is a spec to fix,
            # not a gap in the language, and counting it as one would bury the real ones.
            elsewhere = key in METRICS or key in GROUPS or key in _LEGACY_SORT_KEYS
            raise QueryError(
                f"sort by {key}: not one of the metrics or groups asked for. Sort {entity} by one of: {', '.join(accepted)}.",
                unknown=([] if elsewhere else [f"sort:{key}"]), help=schema_help(entity, metrics=metrics, groups=groups))
        sort.append((key, direction or "desc"))
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
    extra = {"shop_country": shop_country} if "international" in filters else {}
    return Query(entity=entity, period=period, filters=filters, group_by=tuple(groups), metrics=tuple(metrics), sort=tuple(sort), limit=limit, limit_explicit="limit" in spec, compare=compare, view=view, title=title, cost=cost, extra=extra)


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
