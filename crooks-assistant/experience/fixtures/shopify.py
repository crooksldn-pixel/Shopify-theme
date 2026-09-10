"""A Shopify that answers from the golden world instead of the network.

This is a `ShopifyClient` with `graphql()` replaced, which is the narrowest possible seam: the
query strings, the variables, the retry policy, the shop/timezone handling and every line of
result shaping above it are the ones that run in production. A fixture run therefore exercises
`_order_summary`, `_ORDER_SELECTION` shaping, the analytics cache and the presenters for real.

Dispatch is on the operation name. An operation this file does not know raises rather than
returning an empty connection, because a scenario that silently reads nothing is a scenario
that silently proves nothing.

Writes are refused. `mutate()` raises for every mutation that changes anything, so a fixture
world can never be the thing that makes a change look as though it succeeded. The two
exceptions are an order edit's `orderEditBegin` and `orderEditAddVariant`, which change
nothing: they build and price a CalculatedOrder — a scratch copy — and the real order does not
move until `orderEditCommit`, which is not answered here and raises like the rest. They are
answered because every number on the card the owner authorises comes from them, and a scenario
that cannot see that card cannot check what he is being asked to agree to.
"""

from __future__ import annotations

import copy
import re
from typing import Any
from zoneinfo import ZoneInfo

from app import readonly
from app.clients.shopify import REVIEWED_MUTATIONS, ShopifyClient
from experience.fixtures import data
from experience.fixtures.data import BY_ID, ORDERS, PEOPLE, PRODUCTS, VARIANTS, OrderSpec

_OPERATION = re.compile(r"\b(?:query|mutation)\s+(\w+)")

# What the fixture shop grants. Every write capability the assistant knows about is present,
# so that a scenario testing "the action is offered" is not passing for want of a scope.
SCOPES = (
    "read_orders", "write_orders", "read_customers", "read_products", "read_inventory",
    "write_inventory", "read_fulfillments", "write_fulfillments", "read_merchant_managed_fulfillment_orders",
    "write_merchant_managed_fulfillment_orders", "read_returns", "write_returns",
    # Phase 3: order item editing (app/families/order_edit.py). Granted here for the same
    # reason as the rest — a scenario about what the card says must not pass or fail on a
    # scope. A store without it is the MISSING_SCOPE case, and that is a unit test.
    "write_order_edits",
    # Phase 3: the commerce writes (app/families/discounts.py, order_create.py,
    # store_credit.py). Granted here for the same reason as the rest — a scenario about what
    # a card says must not pass or fail on a scope. A store without one of them is the
    # MISSING_SCOPE case, and that is a unit test.
    "read_discounts", "write_discounts",
    "read_draft_orders", "write_draft_orders",
    "read_store_credit_accounts", "write_store_credit_account_transactions",
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
        # The CALCULATION mutations of an order edit, and the scratch orders they built. Kept
        # apart from `mutations_sent` on purpose: nothing here has changed the shop, and
        # "nothing was changed" is a check other scenarios make against that counter.
        self.calculations: list[tuple[str, dict[str, Any]]] = []
        self.calculated: dict[str, dict[str, Any]] = {}
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
        # Two mutations are answered here, and they are the two that change nothing: an order
        # edit's `orderEditBegin` and `orderEditAddVariant` build and price a CalculatedOrder
        # — a scratch copy — and the real order is untouched until `orderEditCommit`. A
        # scenario has to be able to see the card the owner would see, and every number on
        # that card comes from these two. `order_edit_commit` is deliberately absent and
        # falls through to the refusal below, with every other mutation in the application.
        calculation = _CALCULATIONS.get(name)
        if calculation is not None:
            # The same order the production client keeps: refused before anything is looked
            # up when the process is latched read-only, so a live read-only run cannot even
            # open an edit — and held to the reviewed variable set, which the real `mutate`
            # checks and this seam would otherwise skip.
            readonly.assert_writable(f"the Shopify mutation {name!r}")
            reviewed = REVIEWED_MUTATIONS[name]
            if set(variables) != set(reviewed.variables):
                raise FixtureWriteAttempted(
                    f"{name} was sent {sorted(variables)}; the reviewed document takes {sorted(reviewed.variables)}."
                )
            self.calculations.append((name, copy.deepcopy(variables)))
            return calculation(self, dict(variables))
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


# --------------------------------------------------------------- order editing (Phase 3)
#
# The reads a proposal to add a line needs, and the two CALCULATION mutations that price it.
# The prices are the catalogue's own (data.py), the postage is data.SHIPPING, and what the
# customer will owe is worked out from what the order has already been paid — so a scenario
# asserting "£60.00 more, £149.00 total, £60.00 outstanding" is asserting arithmetic this
# file did rather than a number somebody typed into a fixture.


def _variant_for_edit(_store: FixtureShopify, v: dict) -> dict:
    """One variant by id, as `shopify_order_add_item` reads it before it opens an edit."""
    variant = VARIANTS.get(str(v.get("id") or ""))
    if variant is None:
        return {"data": {"productVariant": None}}
    product = variant["product"]
    return {"data": {"productVariant": {
        "id": variant["id"], "title": variant["title"], "sku": variant["sku"], "price": variant["price"],
        "availableForSale": variant["inventoryQuantity"] > 0,
        "inventoryQuantity": variant["inventoryQuantity"],
        "selectedOptions": [{"name": n, "value": val} for n, val in variant["options"]],
        "product": {"id": product["id"], "title": product["title"], "status": product["status"]},
    }}}


def _calculated_order(spec: OrderSpec, added: list[tuple[str, int]], calculated_id: str) -> dict[str, Any]:
    """The scratch order as Shopify would price it: the order's own lines plus what has been
    added, folded by variant because `allowDuplicates` is false, and the money recomputed."""
    node = data.order_node(spec)
    current = float(node["currentTotalPriceSet"]["shopMoney"]["amount"])
    outstanding = float(node["totalOutstandingSet"]["shopMoney"]["amount"])
    paid = current - outstanding
    lines: dict[str, int] = {}
    for variant_id, quantity in list(spec.items) + list(added):
        lines[variant_id] = lines.get(variant_id, 0) + int(quantity)
    subtotal = sum(float(VARIANTS[v]["price"]) * q for v, q in lines.items())
    total = subtotal + data.SHIPPING
    return {
        "id": calculated_id,
        "subtotalPriceSet": data._money(f"{subtotal:.2f}"),
        "totalPriceSet": data._money(f"{total:.2f}"),
        "totalOutstandingSet": data._money(f"{max(0.0, total - paid):.2f}"),
        "lineItems": {"edges": [
            {"node": {"id": f"gid://shopify/CalculatedLineItem/{index}", "quantity": quantity, "variant": {"id": variant_id}}}
            for index, (variant_id, quantity) in enumerate(lines.items())
        ]},
    }


def _order_edit_begin(store: FixtureShopify, v: dict) -> dict:
    spec = BY_ID.get(str(v.get("id") or ""))
    if spec is None:
        return {"data": {"orderEditBegin": {"calculatedOrder": None,
                                            "userErrors": [{"field": ["id"], "message": "Order not found."}]}}}
    calculated_id = f"gid://shopify/CalculatedOrder/{spec.number}"
    store.calculated[calculated_id] = {"order_id": spec.order_id, "added": []}
    return {"data": {"orderEditBegin": {
        "calculatedOrder": {"id": calculated_id, "committed": False}, "userErrors": [],
    }}}


def _order_edit_add_variant(store: FixtureShopify, v: dict) -> dict:
    calculated_id = str(v.get("id") or "")
    state = store.calculated.get(calculated_id)
    if state is None:
        return {"data": {"orderEditAddVariant": {"calculatedLineItem": None, "calculatedOrder": None,
                                                 "userErrors": [{"field": ["id"], "message": "No order edit is in progress."}]}}}
    variant = VARIANTS.get(str(v.get("variantId") or ""))
    if variant is None:
        return {"data": {"orderEditAddVariant": {"calculatedLineItem": None, "calculatedOrder": None,
                                                 "userErrors": [{"field": ["variantId"], "message": "Variant not found."}]}}}
    quantity = int(v.get("quantity") or 0)
    state["added"].append((variant["id"], quantity))
    spec = BY_ID[state["order_id"]]
    unit = data._money(variant["price"])
    return {"data": {"orderEditAddVariant": {
        "calculatedLineItem": {
            "id": f"gid://shopify/CalculatedLineItem/new-{variant['id'].rsplit('/', 1)[-1]}",
            "title": variant["product"]["title"], "variantTitle": variant["title"],
            "quantity": quantity, "originalUnitPriceSet": unit,
        },
        "calculatedOrder": _calculated_order(spec, state["added"], calculated_id),
        "userErrors": [],
    }}}


_HANDLERS["CrooksOrderEditState"] = _order_by_id
_HANDLERS["CrooksVariantForOrderEdit"] = _variant_for_edit
_HANDLERS["CrooksVariantSearch"] = _products

# The only two mutations this fixture answers. Adding a third is adding a way for a fixture
# run to look as though it changed the shop, which is the one thing it must never do.
_CALCULATIONS: dict[str, Any] = {
    "order_edit_begin": _order_edit_begin,
    "order_edit_add_variant": _order_edit_add_variant,
}


# ------------------------------------------------------------ the commerce writes (Phase 3)
#
# The READS the three creation families make before they propose anything: whether a discount
# code is taken. Nothing here answers a creation — `discount_code_create`,
# `draft_order_create`, `draft_order_complete` and `store_credit_credit` are all absent from
# `_CALCULATIONS` above and fall through to the refusal, which is the point: a scenario sees
# the card the owner would authorise, and the shop is never changed by seeing it.


def _discount_by_code(_store: FixtureShopify, v: dict) -> dict:
    """One code, as `app/families/discounts.py` reads it before it prepares a creation. A
    code the golden world does not have answers null, which is what "the code is free" is."""
    code = str(v.get("code") or "").upper()
    found = data.DISCOUNTS.get(code)
    if found is None:
        return {"data": {"codeDiscountNodeByCode": None}}
    return {"data": {"codeDiscountNodeByCode": {
        "id": found["id"],
        "codeDiscount": {
            "__typename": "DiscountCodeBasic",
            "title": found["title"], "status": found["status"],
            "startsAt": found["startsAt"], "endsAt": found["endsAt"],
            "usageLimit": found["usageLimit"], "asyncUsageCount": found["asyncUsageCount"],
            "customerGets": {"value": copy.deepcopy(found["value"])},
        },
    }}}


def _abandoned_checkouts(_store: FixtureShopify, v: dict) -> dict:
    """The checkouts begun and not paid for, filtered by the same window the application
    sends. The completed one is returned WITH its `completedAt` rather than hidden here: the
    filter is the application's (`app/families/abandoned.py`), and a fixture that pre-filtered
    would leave that line untested."""
    since = _iso(str(_CREATED_FROM.search(str(v.get("q") or "")).group(1)) if _CREATED_FROM.search(str(v.get("q") or "")) else "1970-01-01")
    limit = max(1, int(v.get("n") or 25))
    chosen = []
    for checkout in sorted(data.ABANDONED, key=lambda c: c["days_ago"]):
        created = _iso(data._at(checkout["days_ago"]))
        if created < since:
            continue
        person = checkout["customer"]
        chosen.append({"node": {
            "id": checkout["id"],
            "name": checkout["name"],
            "createdAt": data._at(checkout["days_ago"]),
            "completedAt": data._at(max(0.0, checkout["days_ago"] - 0.1)) if checkout["completed"] else None,
            "totalPriceSet": data._money(f"{data.abandoned_total(checkout):.2f}"),
            "customer": ({"id": person.customer_id, "displayName": person.name} if person else None),
            "lineItems": {"edges": [
                {"node": {
                    "title": VARIANTS[variant]["product"]["title"],
                    "variantTitle": VARIANTS[variant]["title"],
                    "quantity": quantity,
                    "variant": {"id": variant},
                    "product": {"id": VARIANTS[variant]["product"]["id"], "title": VARIANTS[variant]["product"]["title"]},
                }}
                for variant, quantity in checkout["lines"]
            ]},
        }})
    return {"data": {"abandonedCheckouts": {
        "edges": chosen[:limit], "pageInfo": {"hasNextPage": len(chosen) > limit},
    }}}


_HANDLERS["CrooksDiscountByCode"] = _discount_by_code
_HANDLERS["CrooksAbandonedCheckouts"] = _abandoned_checkouts
