"""Six read-only Shopify tools.

Every one is a fixed GraphQL document with bound variables. There is no tool that accepts a
query string from the model, because that is how a read-only integration becomes a write one.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from app.clients.shopify import ShopifyClient, ShopifyError
from app.tools.gate import Tier
from app.tools.registry import ToolError, tool

log = logging.getLogger("crooks.shopify_tools")

# Shopify caps a single query at 1,000 cost points on every plan. Nested connections are the
# expensive part, so line items and similar are capped well below the API's own limit.
MAX_PAGE = 50
MAX_LINE_ITEMS = 50
# products x variants is the expensive nesting; 10 x 50 stays under Shopify's 1,000-point cap.
MAX_PRODUCTS = 10
MAX_BODY_CHARS = 1200

_client: ShopifyClient | None = None


def bind(client: ShopifyClient) -> None:
    """Give the tools their client. Called once at startup, and by tests with a fake."""
    global _client
    _client = client


def _c() -> ShopifyClient:
    if _client is None:
        raise ToolError("Shopify is not configured on this backend.")
    return _client


def _truncate(text: str, limit: int = MAX_BODY_CHARS) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"… [truncated, {len(text) - limit} more characters]"


def _money(node: Any) -> str | None:
    if not node:
        return None
    shop_money = node.get("shopMoney") or node
    amount = shop_money.get("amount")
    currency = shop_money.get("currencyCode", "")
    return f"{amount} {currency}".strip() if amount is not None else None


# --------------------------------------------------------------------- orders

_ORDER_FIELDS = """
  id
  name
  createdAt
  processedAt
  displayFulfillmentStatus
  displayFinancialStatus
  currentTotalPriceSet { shopMoney { amount currencyCode } }
  customer { id displayName defaultEmailAddress { emailAddress } }
"""


@tool(
    name="shopify_find_order",
    description=(
        "Find a CROOKS order by its order number (for example 4832 or #4832), or by a customer's "
        "name or email address. Returns the matching orders with their fulfilment status, payment "
        "status, total, date and customer — enough to answer 'has it shipped', 'how much was it' "
        "and 'when was it placed' directly, so answer from this result when it already answers "
        "the question. Only call shopify_order_detail when the items, the shipping or tracking, "
        "or the order's note are actually asked for. This is also what makes an order available "
        "in more detail."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "An order number, a customer name, or an email address.",
            },
            "limit": {"type": "integer", "description": "Maximum orders to return (1-50).",
                      "default": 5},
        },
        "required": ["query"],
    },
    tier=Tier.GREEN,
)
async def shopify_find_order(query: str, limit: int = 5) -> dict:
    client = _c()
    limit = max(1, min(int(limit), MAX_PAGE))
    term = _strip_order_prefix(query)
    if not term:
        raise ToolError("No order number or customer given.")

    # A bare number is an order name. This store names orders "CROOKS-1928" (older ones
    # "#1036"); a bare `name:1928` matches both forms — verified against the live store.
    search = f"name:{term}" if term.isdigit() else None
    ambiguous_customers: list[dict] = []

    if search is None:
        # There is no `customer_name:` filter on orders. Resolve the customer first, then
        # search by customer_id — searching orders by a name string silently returns nothing.
        customers = await _search_customers(client, term, limit=10)
        if not customers:
            return {"query": query, "orders": [], "note": f"No customer matching {term!r}."}
        clauses = " OR ".join(f"customer_id:{c['id'].rsplit('/', 1)[-1]}" for c in customers)
        search = f"({clauses})"
        ambiguous_customers = customers if len(customers) > 1 else []

    payload = await client.graphql(
        f"""
        query FindOrders($q: String!, $n: Int!) {{
          orders(first: $n, query: $q, sortKey: CREATED_AT, reverse: true) {{
            edges {{ node {{ {_ORDER_FIELDS} }} }}
          }}
        }}
        """,
        {"q": search, "n": limit},
    )
    orders = [_order_summary(e["node"]) for e in payload["data"]["orders"]["edges"]]
    result: dict[str, Any] = {"query": query, "matched_on": search, "orders": orders}
    if payload.get("_partial_errors"):
        result["partial"] = payload["_partial_errors"]
    if not term.isdigit() and ambiguous_customers:
        result["ambiguous"] = True
        result["customers_matched"] = [
            {"customer_id": c["customer_id"], "name": c["name"]} for c in ambiguous_customers
        ]
        result["instruction"] = (
            "More than one customer matched that name. Say which customers you found and ask "
            "which one is meant before reporting an order as theirs."
        )
    if not orders:
        result["note"] = (
            f"No order found for {query!r}. Note that without the read_all_orders scope only "
            "the last 60 days of orders are visible."
        )
    return result


_ORDER_PREFIX_RE = re.compile(r"^\s*(?:order\s*)?(?:crooks[\s-]*)?#?\s*", re.I)


def _strip_order_prefix(query: str) -> str:
    """'CROOKS-1928', 'crooks 1928', '#1928', 'order 1928' and '1928' are all the same order."""
    query = query.strip()
    stripped = _ORDER_PREFIX_RE.sub("", query).strip()
    return stripped if stripped.isdigit() else query.lstrip("#").strip()


def _order_summary(node: dict) -> dict:
    customer = node.get("customer") or {}
    return {
        "order_id": node["id"],
        "order_number": node["name"],
        "placed_at": node.get("processedAt") or node.get("createdAt"),
        "fulfillment": node.get("displayFulfillmentStatus"),
        "payment": node.get("displayFinancialStatus"),
        "total": _money(node.get("currentTotalPriceSet")),
        "customer_name": customer.get("displayName"),
        "customer_id": customer.get("id"),
        "customer_email": (customer.get("defaultEmailAddress") or {}).get("emailAddress"),
    }


@tool(
    name="shopify_order_detail",
    description=(
        "Get the full detail of one order: what was bought, the shipping status and any tracking "
        "number. Requires an order_id from shopify_find_order or shopify_list_orders — you cannot "
        "guess one."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "order_id": {
                "type": "string",
                "description": "The order_id returned by a previous search.",
            }
        },
        "required": ["order_id"],
    },
    tier=Tier.AMBER,
    issued_id_args=("order_id",),
)
async def shopify_order_detail(order_id: str) -> dict:
    client = _c()
    payload = await client.graphql(
        f"""
        query OrderDetail($id: ID!, $n: Int!) {{
          order(id: $id) {{
            {_ORDER_FIELDS}
            note
            cancelledAt
            lineItems(first: $n) {{
              edges {{ node {{
                title
                quantity
                variantTitle
                sku
                originalTotalSet {{ shopMoney {{ amount currencyCode }} }}
              }} }}
            }}
            fulfillments(first: 10) {{
              status
              createdAt
              trackingInfo {{ company number url }}
            }}
            shippingAddress {{ city province country }}
          }}
        }}
        """,
        {"id": order_id, "n": MAX_LINE_ITEMS},
    )
    node = payload["data"].get("order")
    if node is None:
        raise ToolError(f"No order with id {order_id}.")

    items = [
        {
            "title": e["node"]["title"],
            "variant": e["node"].get("variantTitle"),
            "sku": e["node"].get("sku"),
            "quantity": e["node"]["quantity"],
            "total": _money(e["node"].get("originalTotalSet")),
        }
        for e in node["lineItems"]["edges"]
    ]
    tracking = [
        {
            "status": f.get("status"),
            "shipped_at": f.get("createdAt"),
            "carrier": (f.get("trackingInfo") or [{}])[0].get("company"),
            "number": (f.get("trackingInfo") or [{}])[0].get("number"),
        }
        for f in (node.get("fulfillments") or [])
    ]
    address = node.get("shippingAddress") or {}
    detail = _order_summary(node)
    detail.update(
        {
            "items": items,
            "items_truncated": len(items) >= MAX_LINE_ITEMS,
            "fulfillments": tracking,
            "cancelled_at": node.get("cancelledAt"),
            "note": _truncate(node.get("note") or "") or None,
            # Deliberately city/country only — a full address has no place in a spoken answer
            # or in a log file.
            "ships_to": " ".join(
                p for p in (address.get("city"), address.get("country")) if p
            ) or None,
        }
    )
    return detail


@tool(
    name="shopify_list_orders",
    description=(
        "List recent CROOKS orders for a period, newest first. Use days=1 for today. Good for "
        "'what orders have we had today' and 'what came in over the weekend'."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "days": {"type": "integer", "description": "How many days the window covers, 1 = one day.",
                     "default": 1},
            "days_ago": {"type": "integer", "description": "Shift the window back: 0 = ends today, 1 = ends yesterday. 'Yesterday' is days=1, days_ago=1.",
                         "default": 0},
            "limit": {"type": "integer", "description": "Maximum orders (1-50).", "default": 20},
            "unfulfilled_only": {
                "type": "boolean",
                "description": "Only orders that have not shipped.",
                "default": False,
            },
        },
    },
    tier=Tier.GREEN,
)
async def shopify_list_orders(
    days: int = 1, limit: int = 20, unfulfilled_only: bool = False, days_ago: int = 0
) -> dict:
    client = _c()
    limit = max(1, min(int(limit), MAX_PAGE))
    days = max(1, min(int(days), 365))
    days_ago = max(0, min(int(days_ago), 365))

    start, end = await _window(client, days, days_ago)
    query = f"created_at:>='{start}' AND created_at:<'{end}'"
    if unfulfilled_only:
        query += " AND fulfillment_status:unfulfilled"

    payload = await client.graphql(
        f"""
        query ListOrders($q: String!, $n: Int!) {{
          orders(first: $n, query: $q, sortKey: CREATED_AT, reverse: true) {{
            edges {{ node {{ {_ORDER_FIELDS} }} }}
            pageInfo {{ hasNextPage }}
          }}
        }}
        """,
        {"q": query, "n": limit},
    )
    connection = payload["data"]["orders"]
    orders = [_order_summary(e["node"]) for e in connection["edges"]]
    return {
        "since": start,
        "until": end,
        "timezone": str(await client.timezone()),
        "days": days,
        "days_ago": days_ago,
        "count": len(orders),
        "truncated": connection["pageInfo"]["hasNextPage"],
        "orders": orders,
    }


async def _window(client: ShopifyClient, days: int, days_ago: int) -> tuple[str, str]:
    """[start, end) in UTC for a window of `days` shop-local days ending `days_ago` days ago."""
    start, _ = await client.local_day_bounds(days_back=days_ago + days - 1)
    _, end = await client.local_day_bounds(days_back=days_ago)
    return start, end


# ------------------------------------------------------------------ customers


async def _search_customers(client: ShopifyClient, term: str, limit: int = 5) -> list[dict]:
    term = term.strip()
    if term.lower().startswith("email:"):
        term = f'email:"{_search_term(term[6:])}"'
    else:
        term = _search_term(term)
    payload = await client.graphql(
        """
        query FindCustomers($q: String, $n: Int!) {
          customers(first: $n, query: $q) {
            edges { node {
              id
              displayName
              defaultEmailAddress { emailAddress }
              numberOfOrders
              amountSpent { amount currencyCode }
            } }
          }
        }
        """,
        {"q": term.strip() or None, "n": max(1, min(limit, MAX_PAGE))},
    )
    return [
        {
            "id": e["node"]["id"],
            "customer_id": e["node"]["id"],
            "name": e["node"].get("displayName"),
            # Customer.email is deprecated; defaultEmailAddress is the current field.
            "email": (e["node"].get("defaultEmailAddress") or {}).get("emailAddress"),
            "orders": int(e["node"].get("numberOfOrders") or 0),
            "spent": _money(e["node"].get("amountSpent")),
        }
        for e in payload["data"]["customers"]["edges"]
    ]


@tool(
    name="shopify_find_customer",
    description=(
        "Find a CROOKS customer by name or email address. Returns every close match — if more "
        "than one comes back, ask which one rather than choosing."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "A customer name or email address."},
            "limit": {"type": "integer", "description": "Maximum matches (1-50).", "default": 5},
        },
        "required": ["query"],
    },
    tier=Tier.AMBER,
)
async def shopify_find_customer(query: str, limit: int = 5) -> dict:
    client = _c()
    limit = max(1, min(int(limit), MAX_PAGE))
    matches = await _search_customers(client, query.strip(), limit=limit)
    result: dict[str, Any] = {"query": query, "count": len(matches), "customers": matches}
    if not matches and client.last_partial_errors:
        result["partial"] = client.last_partial_errors
    if len(matches) >= limit:
        result["truncated"] = True
        result["note"] = f"Showing the first {limit}; there may be more. Narrow the search."
    if len(matches) > 1:
        result["ambiguous"] = True
        result["instruction"] = "More than one customer matched. Ask which one; do not choose."
    elif not matches:
        result["note"] = f"No customer matching {query!r}."
    return result


# ------------------------------------------------------------------ inventory


@tool(
    name="shopify_inventory",
    description=(
        "Check CROOKS stock for a product, optionally in one size. Returns the quantity available "
        "per variant. Says so explicitly when a variant does not have inventory tracking turned "
        "on, rather than reporting zero."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "product": {"type": "string", "description": "The product name, e.g. 'Yard Jeans'."},
            "size": {"type": "string", "description": "Optional size, e.g. 'M' or 'medium'."},
            "limit": {"type": "integer", "description": "Maximum products (1-50).", "default": 5},
        },
        "required": ["product"],
    },
    tier=Tier.GREEN,
)
async def shopify_inventory(product: str, size: str = "", limit: int = 5) -> dict:
    client = _c()
    limit = max(1, min(int(limit), MAX_PRODUCTS))
    payload = await client.graphql(
        """
        query Inventory($q: String!, $n: Int!) {
          products(first: $n, query: $q) {
            edges { node {
              id
              title
              status
              totalInventory
              variants(first: 50) {
                edges { node {
                  id
                  title
                  sku
                  inventoryQuantity
                  inventoryPolicy
                  inventoryItem { tracked }
                } }
              }
            } }
          }
        }
        """,
        {"q": _product_query(product), "n": limit},
    )
    edges = payload["data"]["products"]["edges"]
    if not edges:
        return {"product": product, "note": f"No product matching {product!r}."}

    wanted = _size_aliases(size)
    products = []
    for edge in edges:
        node = edge["node"]
        variants = []
        for v in node["variants"]["edges"]:
            vn = v["node"]
            title = (vn.get("title") or "").strip()
            segments = {seg.strip().lower() for seg in title.split("/")}
            if wanted and not (segments & wanted):
                continue
            tracked = (vn.get("inventoryItem") or {}).get("tracked", True)
            quantity = vn.get("inventoryQuantity")
            note = None
            if not tracked:
                note = "Inventory is not tracked for this variant."
            elif quantity is not None and quantity < 0:
                note = f"Oversold by {abs(quantity)} — more sold than were in stock."
            variants.append(
                {
                    "variant_id": vn["id"],
                    "variant": title,
                    "sku": vn.get("sku"),
                    "available": (max(quantity, 0) if quantity is not None else None) if tracked else None,
                    "oversold_by": abs(quantity) if tracked and quantity is not None and quantity < 0 else 0,
                    "tracked": tracked,
                    "note": note,
                }
            )
        products.append(
            {
                "product_id": node["id"],
                "title": node["title"],
                "status": node.get("status"),
                "total_inventory": node.get("totalInventory"),
                "variants": variants,
            }
        )

    result: dict[str, Any] = {"product": product, "size": size or None, "products": products}
    if size and all(not p["variants"] for p in products):
        result["note"] = f"No variant matching size {size!r} on the matched products."
    return result


def _search_term(text: str) -> str:
    """Strip characters that have meaning in Shopify's search syntax from user-supplied text."""
    return re.sub(r"[\"'*:()\\]", " ", text).strip()


def _product_query(product: str) -> str:
    """Bare words match across title and tags and are ANDed — verified on the live store. A
    leading wildcard inside a multi-word `title:` clause is not documented to work."""
    return _search_term(product) or "*"


def _size_aliases(size: str) -> set[str]:
    """People say 'medium', Shopify stores 'M'. Match either without guessing at the data."""
    size = size.strip().lower()
    if not size:
        return set()
    groups = [
        {"xs", "extra small", "x-small"},
        {"s", "small"},
        {"m", "medium", "med"},
        {"l", "large"},
        {"xl", "extra large", "x-large"},
        {"xxl", "2xl", "extra extra large"},
    ]
    for group in groups:
        if size in group:
            return group
    return {size}


# --------------------------------------------------------------------- sales


@tool(
    name="shopify_sales_summary",
    description=(
        "Total CROOKS sales for a period: order count and revenue. Use days=1 for today. Always "
        "reports which orders it counted and whether the figure is complete, so the number is "
        "never quoted without its basis."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "days": {"type": "integer", "description": "How many days the window covers, 1 = one day.",
                     "default": 1},
            "days_ago": {"type": "integer", "description": "Shift the window back: 0 = ends today, 1 = ends yesterday. 'Yesterday' is days=1, days_ago=1.",
                         "default": 0},
        },
    },
    tier=Tier.GREEN,
)
async def shopify_sales_summary(days: int = 1, days_ago: int = 0) -> dict:
    client = _c()
    days = max(1, min(int(days), 365))
    days_ago = max(0, min(int(days_ago), 365))
    start, end = await _window(client, days, days_ago)

    total = 0.0
    count = 0
    currency = ""
    cursor: str | None = None
    pages = 0
    complete = True

    while pages < 10:  # 10 * 50 = 500 orders; beyond that, say so rather than paginating forever
        payload = await client.graphql(
            """
            query Sales($q: String!, $n: Int!, $after: String) {
              orders(first: $n, query: $q, after: $after, sortKey: CREATED_AT) {
                edges {
                  cursor
                  node {
                    id
                    currentTotalPriceSet { shopMoney { amount currencyCode } }
                    displayFinancialStatus
                  }
                }
                pageInfo { hasNextPage }
              }
            }
            """,
            {"q": f"created_at:>='{start}' AND created_at:<'{end}'", "n": MAX_PAGE, "after": cursor},
        )
        connection = payload["data"]["orders"]
        for edge in connection["edges"]:
            money = (edge["node"].get("currentTotalPriceSet") or {}).get("shopMoney") or {}
            if money.get("amount") is not None:
                total += float(money["amount"])
                currency = currency or money.get("currencyCode", "")
            count += 1
            cursor = edge["cursor"]
        pages += 1
        if not connection["pageInfo"]["hasNextPage"]:
            break
    else:
        complete = False

    return {
        # Never a bare number: the source and the precision travel with the figure.
        "source": "Shopify Admin API, orders created in the period",
        "since": start,
        "until": end,
        "timezone": str(await client.timezone()),
        "days": days,
        "days_ago": days_ago,
        "orders": count,
        "revenue": round(total, 2),
        "currency": currency or "GBP",
        "complete": complete,
        "basis": (
            "Current total per order including tax and shipping, after any refunds. "
            "Cancelled orders are included if they were placed in the period."
        ),
        "caveat": None if complete else "More than 500 orders in the period; figure is partial.",
    }


# ------------------------------------------------------------ product info


@tool(
    name="shopify_product_info",
    description=(
        "Read a CROOKS product's description and the garment facts the store publishes for it: "
        "fabric, cut, origin, care, and measurements per size. Use for 'what's the inseam on a "
        "medium' or 'what are the jeans made of'. Not for stock — use shopify_inventory."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "product": {"type": "string", "description": "The product name, e.g. 'Yard Jeans'."},
            "size": {"type": "string", "description": "Optional size to narrow the measurements to."},
            "limit": {"type": "integer", "description": "Maximum products (1-50).", "default": 3},
        },
        "required": ["product"],
    },
    tier=Tier.GREEN,
)
async def shopify_product_info(product: str, size: str = "", limit: int = 3) -> dict:
    client = _c()
    limit = max(1, min(int(limit), MAX_PRODUCTS))
    payload = await client.graphql(
        """
        query ProductInfo($q: String!, $n: Int!) {
          products(first: $n, query: $q) {
            edges { node {
              id
              title
              status
              description
              metafields(first: 10, namespace: "crooks") {
                edges { node { key type value } }
              }
            } }
          }
        }
        """,
        {"q": _product_query(product), "n": limit},
    )
    edges = payload["data"]["products"]["edges"]
    if not edges:
        return {"product": product, "note": f"No product matching {product!r}."}

    wanted = _size_aliases(size)
    products = []
    for edge in edges:
        node = edge["node"]
        facts: dict[str, Any] = {}
        measurements: list[dict] = []
        for m in node["metafields"]["edges"]:
            key, value = m["node"]["key"], m["node"]["value"]
            if key == "measurements":
                try:
                    measurements = json.loads(value)
                except (TypeError, ValueError):
                    measurements = []
            elif key in {"fabric", "cut", "origin", "care", "subtitle", "set_short_name"}:
                facts[key] = value
        if wanted:
            measurements = [m for m in measurements if str(m.get("size", "")).lower() in wanted]
        products.append(
            {
                "product_id": node["id"],
                "title": node["title"],
                "status": node.get("status"),
                "description": _truncate(node.get("description") or "", 600) or None,
                **facts,
                "measurements": measurements,
                "measurements_note": (
                    "Garment measurements in centimetres." if measurements
                    else "No measurements are published for this product."
                ),
            }
        )
    return {"product": product, "size": size or None, "products": products}


# ----------------------------------------------------- live catalogue for M3's normaliser


async def catalogue_terms(limit: int = 250) -> list[str]:
    """Product titles, variant names and recent customer names, for app/speech/normalise.py.

    This is the M7 half of the normaliser: the same interface the seed file satisfies at M3,
    backed by what the store actually sells.
    """
    client = _c()
    terms: list[str] = []
    try:
        payload = await client.graphql(
            """
            query Catalogue($n: Int!) {
              products(first: $n) {
                edges { node {
                  title
                  options { name values }
                  shortName: metafield(namespace: "crooks", key: "set_short_name") { value }
                } }
              }
            }
            """,
            {"n": max(1, min(limit, 250))},
        )
        for edge in payload["data"]["products"]["edges"]:
            node = edge["node"]
            terms.append(node["title"])
            short = (node.get("shortName") or {}).get("value")
            if short:
                terms.append(short)  # "Convict Hoodie" — how the store itself abbreviates it
            for option in node.get("options") or []:
                name = (option.get("name") or "").lower()
                if "colour" in name or "color" in name:
                    terms.extend(option.get("values") or [])
    except ShopifyError as exc:
        log.warning("catalogue: product fetch failed, continuing: %s", exc)

    terms.append("\x00customers")  # boundary: everything after this is a person's name
    try:
        customers = await _search_customers(client, "", limit=50)
        terms.extend(c["name"] for c in customers if c.get("name"))
    except ShopifyError as exc:
        log.warning("catalogue: customer fetch failed, continuing: %s", exc)

    return [t for t in dict.fromkeys(terms) if t and (len(t) > 2 or t.startswith("\x00"))]
