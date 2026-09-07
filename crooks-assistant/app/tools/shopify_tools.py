"""Six read-only Shopify tools.

Every one is a fixed GraphQL document with bound variables. There is no tool that accepts a
query string from the model, because that is how a read-only integration becomes a write one.
"""

from __future__ import annotations

import logging
from typing import Any

from app.clients.shopify import ShopifyClient, ShopifyError
from app.tools.gate import Tier
from app.tools.registry import ToolError, tool

log = logging.getLogger("crooks.shopify_tools")

# Shopify caps a single query at 1,000 cost points on every plan. Nested connections are the
# expensive part, so line items and similar are capped well below the API's own limit.
MAX_PAGE = 50
MAX_LINE_ITEMS = 50
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
        "name or email address. Returns the matching orders with their status and total. Use this "
        "before asking about a specific order — it is what makes the order available to look at "
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
    term = query.strip().lstrip("#").strip()
    if not term:
        raise ToolError("No order number or customer given.")

    # A bare number is an order name. Shopify stores it with the '#' prefix.
    search = f"name:#{term}" if term.isdigit() else None

    if search is None:
        # There is no `customer_name:` filter on orders. Resolve the customer first, then
        # search by customer_id — searching orders by a name string silently returns nothing.
        customers = await _search_customers(client, term, limit=5)
        if not customers:
            return {"query": query, "orders": [], "note": f"No customer matching {term!r}."}
        clauses = " OR ".join(f"customer_id:{c['id'].rsplit('/', 1)[-1]}" for c in customers)
        search = f"({clauses})"

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
    if not orders:
        result["note"] = (
            f"No order found for {query!r}. Note that without the read_all_orders scope only "
            "the last 60 days of orders are visible."
        )
    return result


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
            "days": {"type": "integer", "description": "How many days back, 1 = today.",
                     "default": 1},
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
    days: int = 1, limit: int = 20, unfulfilled_only: bool = False
) -> dict:
    client = _c()
    limit = max(1, min(int(limit), MAX_PAGE))
    days = max(1, min(int(days), 365))

    start, _ = await client.local_day_bounds(days_back=days - 1)
    query = f"created_at:>='{start}'"
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
        "timezone": str(await client.timezone()),
        "days": days,
        "count": len(orders),
        "truncated": connection["pageInfo"]["hasNextPage"],
        "orders": orders,
    }


# ------------------------------------------------------------------ customers


async def _search_customers(client: ShopifyClient, term: str, limit: int = 5) -> list[dict]:
    payload = await client.graphql(
        """
        query FindCustomers($q: String!, $n: Int!) {
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
        {"q": term, "n": max(1, min(limit, MAX_PAGE))},
    )
    return [
        {
            "id": e["node"]["id"],
            "customer_id": e["node"]["id"],
            "name": e["node"].get("displayName"),
            # Customer.email is deprecated; defaultEmailAddress is the current field.
            "email": (e["node"].get("defaultEmailAddress") or {}).get("emailAddress"),
            "orders": e["node"].get("numberOfOrders"),
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
    matches = await _search_customers(client, query.strip(), limit=limit)
    result: dict[str, Any] = {"query": query, "count": len(matches), "customers": matches}
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
    limit = max(1, min(int(limit), MAX_PAGE))
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
        {"q": f"title:*{product.strip()}*", "n": limit},
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
            if wanted and title.lower() not in wanted:
                continue
            tracked = (vn.get("inventoryItem") or {}).get("tracked", True)
            variants.append(
                {
                    "variant_id": vn["id"],
                    "variant": title,
                    "sku": vn.get("sku"),
                    "available": vn.get("inventoryQuantity") if tracked else None,
                    "tracked": tracked,
                    "note": None if tracked else "Inventory is not tracked for this variant.",
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
            "days": {"type": "integer", "description": "How many days back, 1 = today.",
                     "default": 1},
        },
    },
    tier=Tier.GREEN,
)
async def shopify_sales_summary(days: int = 1) -> dict:
    client = _c()
    days = max(1, min(int(days), 365))
    start, _ = await client.local_day_bounds(days_back=days - 1)

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
            {"q": f"created_at:>='{start}'", "n": MAX_PAGE, "after": cursor},
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
        "timezone": str(await client.timezone()),
        "days": days,
        "orders": count,
        "revenue": round(total, 2),
        "currency": currency or "GBP",
        "complete": complete,
        "basis": (
            "Current total per order including tax and shipping, before refunds. "
            "Cancelled orders are included if they were placed in the period."
        ),
        "caveat": None if complete else "More than 500 orders in the period; figure is partial.",
    }


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
                edges { node { title options { name values } } }
              }
            }
            """,
            {"n": max(1, min(limit, 250))},
        )
        for edge in payload["data"]["products"]["edges"]:
            node = edge["node"]
            terms.append(node["title"])
            for option in node.get("options") or []:
                if (option.get("name") or "").lower() not in {"size", "title"}:
                    terms.extend(option.get("values") or [])
    except ShopifyError as exc:
        log.warning("catalogue: product fetch failed, continuing: %s", exc)

    try:
        customers = await _search_customers(client, "", limit=50)
        terms.extend(c["name"] for c in customers if c.get("name"))
    except ShopifyError as exc:
        log.warning("catalogue: customer fetch failed, continuing: %s", exc)

    return [t for t in dict.fromkeys(terms) if t and len(t) > 2]
