"""The order cache: the store's recent orders, with their line items and customers, held on
the Mac so a question about them is answered from memory rather than from a fresh walk
through Shopify. The source stays Shopify: every row is stamped with when it was read, a
sync refreshes what changed, a backfill extends the window when a longer period is asked
for, and nothing here is ever used as the precondition of a write — a change re-reads the
live record on its own path."""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from app.analytics.periods import MAX_DAYS, Period

log = logging.getLogger("crooks.analytics")

PAGE = 40                # orders per page: with a dozen line items each, well inside Shopify's cost per query
ITEMS_PER_ORDER = 12
MAX_PAGES = 60           # 2,400 orders in one backfill; beyond that the figures say they are partial
TTL_S = 300.0            # how long a sync stands before changed orders are read again
STOCK_TTL_S = 120.0
STOCK_CHUNK = 100
WARM_DAYS = 90
THROTTLE_WAIT_S = 4.0

ORDERS_QUERY = f"""
query CrooksOrderRows($q: String!, $n: Int!, $after: String) {{
  orders(first: $n, query: $q, after: $after, sortKey: CREATED_AT, reverse: true) {{
    edges {{
      cursor
      node {{
        id name createdAt processedAt updatedAt cancelledAt closedAt
        displayFinancialStatus displayFulfillmentStatus tags
        currentTotalPriceSet {{ shopMoney {{ amount currencyCode }} }}
        subtotalPriceSet {{ shopMoney {{ amount }} }}
        totalShippingPriceSet {{ shopMoney {{ amount }} }}
        totalRefundedSet {{ shopMoney {{ amount }} }}
        totalOutstandingSet {{ shopMoney {{ amount }} }}
        customer {{ id displayName numberOfOrders createdAt amountSpent {{ amount currencyCode }} defaultEmailAddress {{ emailAddress }} }}
        shippingAddress {{ countryCodeV2 city }}
        fulfillments {{ status trackingInfo {{ number }} }}
        lineItems(first: {ITEMS_PER_ORDER}) {{
          pageInfo {{ hasNextPage }}
          edges {{ node {{
            id title quantity currentQuantity unfulfilledQuantity refundableQuantity sku variantTitle
            discountedTotalSet {{ shopMoney {{ amount }} }}
            variant {{ id selectedOptions {{ name value }} }}
            product {{ id title productType }}
          }} }}
        }}
      }}
    }}
    pageInfo {{ hasNextPage }}
  }}
}}
"""

STOCK_QUERY = """
query CrooksVariantStock($ids: [ID!]!) {
  nodes(ids: $ids) {
    ... on ProductVariant {
      id title inventoryQuantity
      inventoryItem { tracked }
      product { id title }
      selectedOptions { name value }
    }
  }
}
"""


def _money(block: Any) -> float | None:
    money = (block or {}).get("shopMoney") if isinstance(block, dict) else None
    try:
        return float(money["amount"]) if money and money.get("amount") is not None else None
    except (TypeError, ValueError):
        return None


def _amount(money: Any) -> float:
    """A MoneyV2 ({amount, currencyCode}), as a customer's amountSpent is."""
    try:
        return float(money["amount"]) if isinstance(money, dict) and money.get("amount") is not None else 0.0
    except (TypeError, ValueError):
        return 0.0


def _ts(value: Any) -> float:
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp()
    except (TypeError, ValueError):
        return 0.0


def _option(options: Any, *names: str) -> str:
    for option in options or []:
        if isinstance(option, dict) and str(option.get("name") or "").strip().lower() in names:
            return str(option.get("value") or "").strip()
    return ""


def shape_item(node: dict[str, Any]) -> dict[str, Any]:
    variant = node.get("variant") if isinstance(node.get("variant"), dict) else {}
    product = node.get("product") if isinstance(node.get("product"), dict) else {}
    options = variant.get("selectedOptions") or []
    return {
        "line_item_id": str(node.get("id") or ""), "product_id": str(product.get("id") or ""), "product": str(product.get("title") or node.get("title") or ""),
        "product_type": str(product.get("productType") or ""), "variant_id": str(variant.get("id") or ""), "variant": str(node.get("variantTitle") or ""),
        "sku": str(node.get("sku") or ""), "size": _option(options, "size", "sizes", "taille"), "colour": _option(options, "colour", "color", "colours", "colors"),
        "quantity": int(node.get("quantity") or 0), "current_quantity": int(node.get("currentQuantity") if node.get("currentQuantity") is not None else node.get("quantity") or 0),
        "unfulfilled_quantity": int(node.get("unfulfilledQuantity") or 0), "refundable_quantity": int(node.get("refundableQuantity") or 0),
        "total": _money(node.get("discountedTotalSet")) or 0.0,
    }


def shape_order(node: dict[str, Any], *, read_at: float) -> dict[str, Any]:
    """One order as the engine reads it: flat, numeric, stamped with when it was read."""
    customer = node.get("customer") if isinstance(node.get("customer"), dict) else None
    edges = ((node.get("lineItems") or {}).get("edges") or [])
    items = [shape_item(e.get("node") or {}) for e in edges if isinstance(e, dict)]
    address = node.get("shippingAddress") if isinstance(node.get("shippingAddress"), dict) else {}
    fulfillments = [f for f in node.get("fulfillments") or [] if isinstance(f, dict)]
    total = _money(node.get("currentTotalPriceSet"))
    currency = ((node.get("currentTotalPriceSet") or {}).get("shopMoney") or {}).get("currencyCode") or "GBP"
    name = str(node.get("name") or "")
    return {
        "order_id": str(node.get("id") or ""), "order_number": name, "digits": name.rsplit("-", 1)[-1].lstrip("#"),
        "created_at": str(node.get("createdAt") or ""), "ts": _ts(node.get("createdAt")), "updated_ts": _ts(node.get("updatedAt")),
        "cancelled": bool(node.get("cancelledAt")), "cancelled_at": node.get("cancelledAt"), "closed": bool(node.get("closedAt")),
        "financial": str(node.get("displayFinancialStatus") or ""), "fulfillment": str(node.get("displayFulfillmentStatus") or ""),
        "total": total or 0.0, "subtotal": _money(node.get("subtotalPriceSet")) or 0.0, "shipping": _money(node.get("totalShippingPriceSet")) or 0.0,
        "refunded": _money(node.get("totalRefundedSet")) or 0.0, "outstanding": _money(node.get("totalOutstandingSet")) or 0.0, "currency": str(currency),
        "customer": {
            "customer_id": str(customer.get("id") or ""), "name": str(customer.get("displayName") or ""),
            "email": str(((customer.get("defaultEmailAddress") or {}).get("emailAddress")) or "").lower(),
            "orders": int(customer.get("numberOfOrders") or 0), "spent": _amount(customer.get("amountSpent")), "since": str(customer.get("createdAt") or ""),
        } if customer and customer.get("id") else None,
        "country_code": str(address.get("countryCodeV2") or ""), "city": str(address.get("city") or ""),
        "tags": [str(t) for t in node.get("tags") or [] if isinstance(t, str)],
        "units": sum(i["quantity"] for i in items), "unfulfilled_units": sum(i["unfulfilled_quantity"] for i in items),
        "has_tracking": any((f.get("trackingInfo") or [{}])[0].get("number") for f in fulfillments if f.get("trackingInfo")),
        "fulfilled_count": sum(1 for f in fulfillments if str(f.get("status") or "").upper() == "SUCCESS"),
        "items": items, "items_truncated": bool(((node.get("lineItems") or {}).get("pageInfo") or {}).get("hasNextPage")),
        "read_at": read_at,
    }


@dataclass(slots=True)
class CacheView:
    """What a query gets: the rows, and the truth about them."""

    rows: list[dict[str, Any]]
    complete: bool               # the cache covers the whole period asked for
    covered_days: float          # how far back the cache reaches
    synced_at: float | None      # when the last sync finished
    syncing: bool
    note: str = ""
    served_ms: float = 0.0
    asked_at: float = 0.0        # the cache's clock when the view was taken

    @property
    def age_s(self) -> float | None:
        return None if self.synced_at is None else max(0.0, self.asked_at - self.synced_at)


@dataclass(slots=True)
class _Stock:
    value: dict[str, Any]
    at: float


class OrderCache:
    def __init__(self, client: Callable[[], Any], *, clock: Callable[[], float] = time.time) -> None:
        self._client = client
        self.clock = clock
        self._orders: dict[str, dict[str, Any]] = {}
        self._covered_since: float | None = None      # created_at boundary the cache reaches back to
        self._synced_at: float | None = None
        self._lock = asyncio.Lock()
        self._task: asyncio.Task | None = None
        self._stock: dict[str, _Stock] = {}
        self._stale_ids: set[str] = set()              # orders a change was applied to: read again by id
        self.reads = 0                                 # Shopify pages read, for the tests and /health
        self.last_error = ""

    # ----------------------------------------------------------------- status

    @property
    def size(self) -> int:
        return len(self._orders)

    def status(self) -> dict[str, Any]:
        now = self.clock()
        return {
            "orders": len(self._orders), "covered_days": round((now - self._covered_since) / 86400, 1) if self._covered_since else 0.0,
            "synced_at": self._synced_at, "age_s": round(now - self._synced_at, 1) if self._synced_at else None,
            "syncing": bool(self._task and not self._task.done()), "pages_read": self.reads, "last_error": self.last_error or None,
        }

    def rows(self) -> list[dict[str, Any]]:
        return list(self._orders.values())

    def invalidate(self, order_id: str) -> None:
        """A change was applied to this order: what is held of it is no longer it. The next
        sync reads it again; until then it is dropped rather than served stale."""
        self._orders.pop(str(order_id), None)
        self._stale_ids.add(str(order_id))

    # ------------------------------------------------------------------ views

    async def view(self, period: Period, *, timeout_s: float = 6.0) -> CacheView:
        """The rows for a period, syncing and backfilling as needed within the time allowed.
        Past it, what is held is served and the view says it is not complete."""
        started = time.perf_counter()
        now = self.clock()
        since = period.start.timestamp()
        task = self._kick(since)
        if task is not None and not task.done():
            try:
                await asyncio.wait_for(asyncio.shield(task), timeout=timeout_s)
            except TimeoutError:
                pass
            except Exception as exc:  # noqa: BLE001 — the task records its own error
                log.debug("cache sync failed: %s", exc)
        complete = self._covered_since is not None and self._covered_since <= since and self._synced_at is not None
        covered_days = (now - self._covered_since) / 86400 if self._covered_since else 0.0
        rows = [o for o in self._orders.values() if o["ts"] >= since]
        note = ""
        if not complete:
            if self.last_error:
                note = f"Shopify could not be read fully ({self.last_error}); figures cover what the Mac holds."
            elif self._covered_since is None:
                note = "The Mac is still reading recent orders from Shopify; ask again in a moment."
            elif self._covered_since > since:
                note = f"The Mac holds {covered_days:.0f} day(s) of orders so far and is reading further back; figures cover that much."
            else:
                note = "Recent changes are still being read; figures may lag by a few minutes."
        return CacheView(rows=rows, complete=complete, covered_days=round(covered_days, 1), synced_at=self._synced_at, syncing=bool(self._task and not self._task.done()), note=note, served_ms=round((time.perf_counter() - started) * 1000, 1), asked_at=now)

    def warm(self, days: int = WARM_DAYS) -> asyncio.Task | None:
        """Start reading the recent window in the background: at boot, so the first question
        of the day is answered from memory."""
        return self._kick(self.clock() - min(days, MAX_DAYS) * 86400)

    def _kick(self, since: float) -> asyncio.Task | None:
        need_backfill = self._covered_since is None or since < self._covered_since
        need_delta = self._synced_at is None or self.clock() - self._synced_at > TTL_S or bool(self._stale_ids)
        if not need_backfill and not need_delta:
            return None
        if self._task is not None and not self._task.done():
            if need_backfill and getattr(self._task, "_crooks_since", 0.0) <= since:
                return self._task
            if not need_backfill:
                return self._task
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return None
        previous = self._task
        task = loop.create_task(self._sync(since, after=previous))
        task._crooks_since = since  # type: ignore[attr-defined]
        self._task = task
        return task

    async def _sync(self, since: float, *, after: asyncio.Task | None = None) -> None:
        if after is not None and not after.done():
            try:
                await after
            except Exception:  # noqa: BLE001
                pass
        async with self._lock:
            try:
                if self._covered_since is None or since < self._covered_since:
                    await self._backfill(since)
                if self._stale_ids:
                    await self._reread()
                if self._synced_at is None or self.clock() - self._synced_at > TTL_S:
                    await self._delta()
                self.last_error = ""
            except Exception as exc:  # noqa: BLE001 — the cache serves what it has and says so
                self.last_error = f"{type(exc).__name__}: {str(exc)[:120]}"
                log.warning("order cache sync failed: %s", self.last_error)

    async def _backfill(self, since: float) -> None:
        """Orders created between `since` and the oldest the cache already holds."""
        upper = self._covered_since
        lower_iso = datetime.fromtimestamp(since, UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        query = f"created_at:>='{lower_iso}'"
        if upper is not None:
            query += f" AND created_at:<'{datetime.fromtimestamp(upper, UTC).strftime('%Y-%m-%dT%H:%M:%SZ')}'"
        reached_end = await self._walk(query)
        if reached_end:
            self._covered_since = since if self._covered_since is None else min(self._covered_since, since)
        elif self._orders:
            self._covered_since = min(o["ts"] for o in self._orders.values())
        if self._synced_at is None:
            self._synced_at = self.clock()

    async def _delta(self) -> None:
        """Orders changed since the last sync: a fulfilment, a refund, a tag. Read again."""
        if self._synced_at is None or self._covered_since is None:
            self._synced_at = self.clock()
            return
        lower = datetime.fromtimestamp(self._synced_at - 120, UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        await self._walk(f"updated_at:>='{lower}'")
        self._synced_at = self.clock()

    async def _reread(self) -> None:
        """The orders a change was applied to, read again by id — at once, not at the next
        delta, so the figures follow the change."""
        stale, self._stale_ids = set(self._stale_ids), set()
        for order_id in sorted(stale)[:20]:
            digits = order_id.rsplit("/", 1)[-1]
            if digits.isdigit():
                await self._walk(f"id:{digits}")

    async def _walk(self, query: str) -> bool:
        """Every page of orders for a Shopify search, into the cache. True when the last page
        was reached within the page bound."""
        client = self._client()
        cursor: str | None = None
        for _ in range(MAX_PAGES):
            payload = await self._page(client, query, cursor)
            connection = (payload.get("data") or {}).get("orders") or {}
            read_at = self.clock()
            for edge in connection.get("edges") or []:
                node = edge.get("node") if isinstance(edge, dict) else None
                if isinstance(node, dict) and node.get("id"):
                    row = shape_order(node, read_at=read_at)
                    self._orders[row["order_id"]] = row
                    cursor = edge.get("cursor") or cursor
            self.reads += 1
            if not (connection.get("pageInfo") or {}).get("hasNextPage"):
                return True
        return False

    async def _page(self, client: Any, query: str, cursor: str | None) -> dict[str, Any]:
        from app.clients.shopify import ShopifyThrottled

        for attempt in range(3):
            try:
                return await client.graphql(ORDERS_QUERY, {"q": query, "n": PAGE, "after": cursor})
            except ShopifyThrottled as exc:
                if attempt == 2:
                    raise
                await asyncio.sleep(min(THROTTLE_WAIT_S, float(getattr(exc, "wait_s", 1.0) or 1.0)))
        raise RuntimeError("unreachable")

    # ------------------------------------------------------------------ stock

    async def stock(self, variant_ids: Iterable[str], *, timeout_s: float = 6.0) -> dict[str, dict[str, Any]]:
        """Available stock per variant, read from Shopify in chunks and held briefly. A
        variant Shopify does not track has no number, and says so."""
        wanted = [v for v in dict.fromkeys(str(v) for v in variant_ids if v) if v.startswith("gid://shopify/ProductVariant/")]
        now = self.clock()
        out: dict[str, dict[str, Any]] = {}
        missing: list[str] = []
        for v in wanted:
            held = self._stock.get(v)
            if held is not None and now - held.at < STOCK_TTL_S:
                out[v] = held.value
            else:
                missing.append(v)
        if missing:
            client = self._client()
            deadline = time.perf_counter() + timeout_s
            for start in range(0, len(missing), STOCK_CHUNK):
                if time.perf_counter() > deadline:
                    break
                chunk = missing[start : start + STOCK_CHUNK]
                try:
                    payload = await asyncio.wait_for(client.graphql(STOCK_QUERY, {"ids": chunk}), timeout=max(0.5, deadline - time.perf_counter()))
                except Exception as exc:  # noqa: BLE001 — stock unknown is an honest answer
                    log.warning("stock read failed: %s", type(exc).__name__)
                    break
                self.reads += 1
                for node in (payload.get("data") or {}).get("nodes") or []:
                    if not isinstance(node, dict) or not node.get("id"):
                        continue
                    options = node.get("selectedOptions") or []
                    value = {
                        "variant_id": str(node["id"]), "product": str((node.get("product") or {}).get("title") or ""), "product_id": str((node.get("product") or {}).get("id") or ""),
                        "variant": str(node.get("title") or ""), "size": _option(options, "size", "sizes"), "colour": _option(options, "colour", "color", "colours", "colors"),
                        "tracked": bool((node.get("inventoryItem") or {}).get("tracked")), "available": (int(node["inventoryQuantity"]) if node.get("inventoryQuantity") is not None else None),
                        "read_at": now,
                    }
                    self._stock[value["variant_id"]] = _Stock(value, now)
                    out[value["variant_id"]] = value
        return out

    def forget_stock(self, variant_id: str = "") -> None:
        if variant_id:
            self._stock.pop(variant_id, None)
        else:
            self._stock.clear()
