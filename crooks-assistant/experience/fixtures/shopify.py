"""A Shopify that answers from the golden world instead of the network.

This is a `ShopifyClient` with `graphql()` replaced, which is the narrowest possible seam: the
query strings, the variables, the retry policy, the shop/timezone handling and every line of
result shaping above it are the ones that run in production. A fixture run therefore exercises
`_order_summary`, `_ORDER_SELECTION` shaping, the analytics cache and the presenters for real.

Dispatch is on the operation name. An operation this file does not know raises rather than
returning an empty connection, because a scenario that silently reads nothing is a scenario
that silently proves nothing.

Writes are refused outright. `mutate()` raises, so a fixture world can never be the thing that
makes a mutation look as though it succeeded.
"""

from __future__ import annotations

import re
from typing import Any
from zoneinfo import ZoneInfo

from app.clients.shopify import ShopifyClient
from experience.fixtures import data
from experience.fixtures.data import BY_ID, ORDERS, PEOPLE, PRODUCTS, VARIANTS, OrderSpec

_OPERATION = re.compile(r"\b(?:query|mutation)\s+(\w+)")

# What the fixture shop grants. Every write capability the assistant knows about is present,
# so that a scenario testing "the action is offered" is not passing for want of a scope.
SCOPES = (
    "read_orders", "write_orders", "read_customers", "read_products", "read_inventory",
    "write_inventory", "read_fulfillments", "write_fulfillments", "read_merchant_managed_fulfillment_orders",
    "write_merchant_managed_fulfillment_orders", "read_returns", "write_returns",
)


class FixtureWriteAttempted(AssertionError):
    """A fixture run tried to change the shop. Nothing in a read scenario may reach this."""


class UnknownFixtureQuery(AssertionError):
    """The application asked something the fixture world has no answer for."""


class FixtureShopify(ShopifyClient):
    """The golden shop. Records every query so a scenario can assert what was actually read."""

    def __init__(self, *, domain: str = "fixture.myshopify.com") -> None:
        super().__init__(domain, "2025-07")
        self.queries: list[tuple[str, dict[str, Any]]] = []
        self.scopes: tuple[str, ...] = SCOPES
        self._shop = {
            "name": "CROOKS LDN (fixture)", "myshopifyDomain": domain,
            "ianaTimezone": data.SHOP_TIMEZONE, "currencyCode": data.CURRENCY,
            # Where the golden shop ships from, so the "international" filter is answered from
            # the shop rather than from a constant (app/analytics/query.py:shop_country_from).
            "billingAddress": {"countryCodeV2": data.SHOP_COUNTRY},
        }
        self._tz = ZoneInfo(data.SHOP_TIMEZONE)

    # ---------------------------------------------------------------- the seam

    async def graphql(self, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        variables = dict(variables or {})
        match = _OPERATION.search(query)
        operation = match.group(1) if match else ""
        self.queries.append((operation, variables))
        handler = _HANDLERS.get(operation)
        if handler is None:
            raise UnknownFixtureQuery(
                f"the fixture shop has no answer for operation {operation!r}. "
                "Add it to experience/fixtures/shopify.py rather than letting the scenario read nothing."
            )
        return handler(self, variables)

    async def mutate(self, name: str, variables: dict[str, Any]) -> dict[str, Any]:
        raise FixtureWriteAttempted(
            f"a fixture run tried to execute the mutation {name!r}. Fixture scenarios propose "
            "changes and inspect the proposal; they never execute one."
        )

    async def access_scopes(self) -> list[str]:
        return list(self.scopes)


# --------------------------------------------------------------------------- query filtering

_CREATED_FROM = re.compile(r"created_at:>='([^']+)'")
_CREATED_TO = re.compile(r"created_at:<'([^']+)'")
_NAME = re.compile(r"\bname:#?(\d+)")
_EMAIL = re.compile(r'\bemail:"?([^"\s]+)"?')


def _iso(value: str) -> str:
    return value.replace("Z", "").replace("T", " ")[:19]


def _matches(spec: OrderSpec, search: str) -> bool:
    """The subset of Shopify's order search the application actually sends."""
    node = data.order_node(spec)
    created = _iso(node["createdAt"])
    lower = _CREATED_FROM.search(search)
    if lower and created < _iso(lower.group(1)):
        return False
    upper = _CREATED_TO.search(search)
    if upper and created >= _iso(upper.group(1)):
        return False
    name = _NAME.search(search)
    if name and spec.name != f"#{name.group(1)}":
        return False
    email = _EMAIL.search(search)
    if email and spec.person.email.lower() != email.group(1).strip('"').lower():
        return False
    if "fulfillment_status:unfulfilled" in search and spec.fulfillment == "FULFILLED":
        return False
    # A bare term, as `shopify_find_order` sends for a number it could not strip to digits.
    bare = search.strip()
    if bare and not any(c in bare for c in (":", "'")):
        if bare.lstrip("#").isdigit():
            return spec.name == f"#{bare.lstrip('#')}"
        return bare.lower() in spec.person.name.lower()
    return True


def _sort_key(spec: OrderSpec) -> tuple[float, float]:
    """Newest first, in the same order Shopify would return them."""
    if spec.today:
        return (0.0, -float(spec.today_fraction or 0))
    return (1.0, spec.days_ago)


def _selected(search: str, limit: int) -> list[OrderSpec]:
    found = [o for o in ORDERS if _matches(o, search)]
    found.sort(key=_sort_key)
    return found[: max(1, int(limit or 10))]


def _connection(specs: list[OrderSpec], *, more: bool = False, cursors: bool = False) -> dict[str, Any]:
    edges: list[dict[str, Any]] = []
    for spec in specs:
        edge: dict[str, Any] = {"node": data.order_node(spec)}
        if cursors:
            edge["cursor"] = f"cursor:{spec.number}"
        edges.append(edge)
    return {"edges": edges, "pageInfo": {"hasNextPage": more, "endCursor": edges[-1]["cursor"] if cursors and edges else None}}


# --------------------------------------------------------------------------- handlers


def _scopes(_store: FixtureShopify, _v: dict) -> dict:
    return {"data": {"currentAppInstallation": {"accessScopes": [{"handle": h} for h in sorted(_store.scopes)]}}}


def _shop(store: FixtureShopify, _v: dict) -> dict:
    return {"data": {"shop": store._shop}}


def _orders_search(_store: FixtureShopify, v: dict) -> dict:
    return {"data": {"orders": _connection(_selected(str(v.get("q") or ""), v.get("n") or 10))}}


def _order_rows(_store: FixtureShopify, v: dict) -> dict:
    return {"data": {"orders": _connection(_selected(str(v.get("q") or ""), v.get("n") or 50), cursors=True)}}


def _order_by_id(_store: FixtureShopify, v: dict) -> dict:
    spec = BY_ID.get(str(v.get("id") or ""))
    return {"data": {"order": data.order_node(spec) if spec else None}}


def _customer_orders(_store: FixtureShopify, v: dict) -> dict:
    person = PEOPLE.get(str(v.get("id") or ""))
    if person is None:
        return {"data": {"customer": None}}
    theirs = sorted([o for o in ORDERS if o.person is person], key=_sort_key)
    first = theirs[-1] if theirs else None
    open_orders = [o for o in theirs if o.fulfillment != "FULFILLED" and o.cancelled_days_ago is None]

    def brief(spec: OrderSpec) -> dict[str, Any]:
        node = data.order_node(spec)
        return {
            "id": node["id"], "name": node["name"], "createdAt": node["createdAt"],
            "processedAt": node["processedAt"], "cancelledAt": node["cancelledAt"],
            "displayFulfillmentStatus": node["displayFulfillmentStatus"],
            "displayFinancialStatus": node["displayFinancialStatus"],
            "currentTotalPriceSet": node["currentTotalPriceSet"],
            "lineItems": {"edges": [{"node": {"title": e["node"]["title"], "quantity": e["node"]["quantity"]}}
                                    for e in node["lineItems"]["edges"][:5]]},
        }

    return {"data": {"customer": {
        "id": person.customer_id,
        "displayName": person.name,
        "numberOfOrders": str(person.orders),
        "createdAt": data._at(person.since_days),
        "tags": [],
        "amountSpent": {"amount": person.spent, "currencyCode": data.CURRENCY},
        "defaultEmailAddress": {"emailAddress": person.email},
        "lastOrder": ({"id": theirs[0].order_id, "name": theirs[0].name} if theirs else None),
        "firstOrder": {"edges": ([{"node": {"id": first.order_id, "name": first.name,
                                            "processedAt": first.placed_at(),
                                            "createdAt": first.placed_at()}}] if first else [])},
        "openOrders": {"edges": [{"node": {"id": o.order_id, "name": o.name, "cancelledAt": None,
                                           "displayFulfillmentStatus": o.fulfillment}} for o in open_orders]},
        "orders": {"edges": [{"node": brief(o)} for o in theirs[: v.get("n") or 10]]},
    }}}


def _customers_search(_store: FixtureShopify, v: dict) -> dict:
    term = str(v.get("q") or "").strip().strip('"').lower()
    email = _EMAIL.search(term)
    people = list(PEOPLE.values())
    if email:
        people = [p for p in people if p.email.lower() == email.group(1)]
    elif term:
        people = [p for p in people if term in p.name.lower() or term in p.email.lower()]
    return {"data": {"customers": {"edges": [{"node": {
        "id": p.customer_id, "displayName": p.name, "numberOfOrders": str(p.orders),
        "createdAt": data._at(p.since_days),
        "amountSpent": {"amount": p.spent, "currencyCode": data.CURRENCY},
        "defaultEmailAddress": {"emailAddress": p.email},
    }} for p in people[: v.get("n") or 5]]}}}


def _variant_stock(_store: FixtureShopify, v: dict) -> dict:
    ids = [str(i) for i in (v.get("ids") or [])]
    return {"data": {"nodes": [
        ({"id": i, "inventoryQuantity": VARIANTS[i]["inventoryQuantity"],
          "inventoryItem": {"tracked": True},
          "product": {"id": VARIANTS[i]["product"]["id"], "title": VARIANTS[i]["product"]["title"]},
          "title": VARIANTS[i]["title"]} if i in VARIANTS else None)
        for i in ids
    ]}}


def _product_nodes(term: str, limit: int) -> list[dict[str, Any]]:
    term = term.strip().strip('"').lower()
    for prefix in ("title:", "product_type:"):
        if term.startswith(prefix):
            term = term[len(prefix):].strip().strip('"')
    found = [p for p in PRODUCTS if not term or term in p["title"].lower()] or []
    out = []
    for product in found[: max(1, limit)]:
        out.append({
            "id": product["id"], "title": product["title"], "status": product["status"],
            "productType": product["productType"], "totalInventory": product["totalInventory"],
            "featuredImage": product["featuredImage"],
            "variants": {"edges": [{"node": {
                "id": variant["id"], "title": variant["title"], "sku": variant["sku"],
                "price": variant["price"], "inventoryQuantity": variant["inventoryQuantity"],
                "availableForSale": variant["inventoryQuantity"] > 0,
                "inventoryItem": {"id": variant["id"].replace("ProductVariant", "InventoryItem"), "tracked": True},
                "selectedOptions": [{"name": n, "value": val} for n, val in variant["options"]],
            }} for variant in product["variants"]]},
        })
    return out


def _products(_store: FixtureShopify, v: dict) -> dict:
    nodes = _product_nodes(str(v.get("q") or ""), int(v.get("n") or 5))
    return {"data": {"products": {"edges": [{"node": n} for n in nodes], "pageInfo": {"hasNextPage": False}}}}


def _locations(_store: FixtureShopify, _v: dict) -> dict:
    return {"data": {"locations": {"edges": [{"node": {"id": "gid://shopify/Location/1", "name": "Studio", "isActive": True}}]}}}


_HANDLERS: dict[str, Any] = {
    "CrooksScopes": _scopes,
    "CrooksShop": _shop,
    "Shop": _shop,
    "FindOrders": _orders_search,
    "ListOrders": _orders_search,
    "Sales": _order_rows,
    "CrooksOrderRows": _order_rows,
    "CrooksOrderByName": _orders_search,
    "CrooksOrderContext": _order_by_id,
    "CrooksOrderNote": _order_by_id,
    "CrooksOrderTags": _order_by_id,
    "CrooksOrderCancelState": _order_by_id,
    "CrooksRefundState": _order_by_id,
    "CrooksAddressState": _order_by_id,
    "CrooksCustomerOrders": _customer_orders,
    "CrooksCustomerAddress": _customer_orders,
    "FindCustomers": _customers_search,
    "CrooksVariantStock": _variant_stock,
    "Inventory": _products,
    "ProductInfo": _products,
    "Catalogue": _products,
    "CrooksLocations": _locations,
}
