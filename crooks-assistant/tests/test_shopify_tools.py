"""Shopify tool shaping, and the DST bug that only shows up in summer.

The live-store tests assert shape, not values — an order count changes every hour, so asserting
one guarantees a test that fails for the wrong reason.
"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from app.tools import shopify_tools
from app.tools.registry import ToolError
from tests.conftest import FakeShopify, needs_shopify

ORDER_NODE = {
    "id": "gid://shopify/Order/4832",
    "name": "#4832",
    "createdAt": "2026-09-07T09:14:00Z",
    "processedAt": "2026-09-07T09:14:00Z",
    "displayFulfillmentStatus": "FULFILLED",
    "displayFinancialStatus": "PAID",
    "currentTotalPriceSet": {"shopMoney": {"amount": "129.00", "currencyCode": "GBP"}},
    "customer": {
        "id": "gid://shopify/Customer/77",
        "displayName": "Anna Denning",
        "defaultEmailAddress": {"emailAddress": "anna@example.com"},
    },
}


# --- date handling: the bug that is correct all winter -----------------------

async def test_local_day_bounds_use_bst_in_summer():
    """British Summer Time is UTC+1, so a London day starts at 23:00 UTC the day before.
    Hardcoding the offset looks right in December and loses an hour of trading in July."""
    client = FakeShopify([])
    start, end = await client.local_day_bounds()
    start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
    london_midnight = start_dt.astimezone(ZoneInfo("Europe/London"))
    assert (london_midnight.hour, london_midnight.minute) == (0, 0), (
        f"{start} is not local midnight in London — this is the BST/UTC bug"
    )
    assert start.endswith("Z") and end.endswith("Z")


async def test_day_bounds_span_exactly_one_day():
    client = FakeShopify([])
    start, end = await client.local_day_bounds()
    delta = datetime.fromisoformat(end.replace("Z", "+00:00")) - datetime.fromisoformat(
        start.replace("Z", "+00:00")
    )
    assert delta.total_seconds() == 86400


# --- find_order -------------------------------------------------------------

async def test_numeric_query_searches_by_order_name():
    client = FakeShopify([{"data": {"orders": {"edges": [{"node": ORDER_NODE}]}}}])
    shopify_tools.bind(client)
    result = await shopify_tools.shopify_find_order("4832")
    # Bare `name:4832` matches both "CROOKS-4832" and legacy "#4832" — verified on the live store.
    assert result["matched_on"] == "name:4832"
    assert result["orders"][0]["order_number"] == "#4832"
    assert result["orders"][0]["order_id"] == "gid://shopify/Order/4832"


async def test_hash_prefix_is_stripped():
    client = FakeShopify([{"data": {"orders": {"edges": []}}}])
    shopify_tools.bind(client)
    result = await shopify_tools.shopify_find_order("#4832")
    assert result["matched_on"] == "name:4832"


async def test_name_query_resolves_customer_first():
    """There is no customer_name: filter on orders. Searching by a name string silently
    returns nothing, which reads as 'no orders' rather than 'wrong query'."""
    client = FakeShopify([
        {"data": {"customers": {"edges": [{"node": {
            "id": "gid://shopify/Customer/77", "displayName": "Anna Denning",
            "defaultEmailAddress": {"emailAddress": "anna@example.com"},
            "numberOfOrders": 3, "amountSpent": {"amount": "387.00", "currencyCode": "GBP"},
        }}]}}},
        {"data": {"orders": {"edges": [{"node": ORDER_NODE}]}}},
    ])
    shopify_tools.bind(client)
    result = await shopify_tools.shopify_find_order("Anna Denning")
    assert "customer_id:77" in result["matched_on"]
    assert len(client.queries) == 2


async def test_empty_result_mentions_the_60_day_window():
    client = FakeShopify([{"data": {"orders": {"edges": []}}}])
    shopify_tools.bind(client)
    result = await shopify_tools.shopify_find_order("9999")
    assert "60 days" in result["note"]


async def test_blank_query_is_refused():
    shopify_tools.bind(FakeShopify([]))
    with pytest.raises(ToolError):
        await shopify_tools.shopify_find_order("   ")


# --- inventory --------------------------------------------------------------

async def test_untracked_variant_is_flagged_not_reported_as_zero():
    client = FakeShopify([{"data": {"products": {"edges": [{"node": {
        "id": "gid://shopify/Product/1", "title": "Yard Jeans", "status": "ACTIVE",
        "totalInventory": 0,
        "variants": {"edges": [{"node": {
            "id": "gid://shopify/ProductVariant/9", "title": "M", "sku": "YJ-M",
            "inventoryQuantity": 0, "inventoryPolicy": "DENY",
            "inventoryItem": {"tracked": False},
        }}]},
    }}]}}}])
    shopify_tools.bind(client)
    variant = (await shopify_tools.shopify_inventory("Yard Jeans"))["products"][0]["variants"][0]
    assert variant["tracked"] is False
    assert variant["available"] is None, "an untracked variant must not report a quantity"
    assert "not tracked" in variant["note"]


@pytest.mark.parametrize("spoken,stored", [("medium", "M"), ("M", "M"), ("large", "L"), ("small", "S")])
async def test_spoken_sizes_match_stored_variant_titles(spoken, stored):
    client = FakeShopify([{"data": {"products": {"edges": [{"node": {
        "id": "p", "title": "Yard Jeans", "status": "ACTIVE", "totalInventory": 4,
        "variants": {"edges": [{"node": {
            "id": "v", "title": stored, "sku": "x", "inventoryQuantity": 4,
            "inventoryPolicy": "DENY", "inventoryItem": {"tracked": True},
        }}]},
    }}]}}}])
    shopify_tools.bind(client)
    result = await shopify_tools.shopify_inventory("Yard Jeans", size=spoken)
    assert result["products"][0]["variants"], f"{spoken!r} did not match stored size {stored!r}"


# --- sales summary ----------------------------------------------------------

async def test_sales_summary_never_returns_a_bare_number():
    client = FakeShopify([{"data": {"orders": {
        "edges": [
            {"cursor": "a", "node": {"id": "1", "displayFinancialStatus": "PAID",
             "currentTotalPriceSet": {"shopMoney": {"amount": "100.00", "currencyCode": "GBP"}}}},
            {"cursor": "b", "node": {"id": "2", "displayFinancialStatus": "PAID",
             "currentTotalPriceSet": {"shopMoney": {"amount": "29.50", "currencyCode": "GBP"}}}},
        ],
        "pageInfo": {"hasNextPage": False},
    }}}])
    shopify_tools.bind(client)
    result = await shopify_tools.shopify_sales_summary(days=1)
    assert result["orders"] == 2
    assert result["revenue"] == 129.5
    assert result["complete"] is True
    for key in ("source", "basis", "timezone", "since"):
        assert result[key], f"{key} missing — a figure must always carry its basis"


# --- ambiguity --------------------------------------------------------------

async def test_multiple_customers_are_marked_ambiguous():
    """Two people called John must produce a question, not a choice."""
    node = lambda i, n: {  # noqa: E731
        "id": f"gid://shopify/Customer/{i}", "displayName": n,
        "defaultEmailAddress": {"emailAddress": f"{i}@example.com"},
        "numberOfOrders": 1, "amountSpent": {"amount": "10.00", "currencyCode": "GBP"},
    }
    client = FakeShopify([{"data": {"customers": {"edges": [
        {"node": node(1, "John Smith")}, {"node": node(2, "John Doe")},
    ]}}}])
    shopify_tools.bind(client)
    result = await shopify_tools.shopify_find_customer("John")
    assert result["ambiguous"] is True
    assert "do not choose" in result["instruction"].lower()


async def test_deprecated_customer_email_field_is_not_used():
    """Customer.email is deprecated; defaultEmailAddress is the current field."""
    import inspect

    source = inspect.getsource(shopify_tools)
    assert "defaultEmailAddress" in source
    assert "\n              email\n" not in source


# --- live store (skipped without credentials) --------------------------------

@needs_shopify
async def test_live_tools_return_expected_shapes():
    from app.clients.shopify import ShopifyClient
    from config.settings import get_settings

    settings = get_settings()
    client = ShopifyClient(
        settings.shopify_shop_domain, settings.shopify_api_version,
        auth_mode=settings.shopify_auth_mode,
    )
    shopify_tools.bind(client)

    orders = await shopify_tools.shopify_list_orders(days=7, limit=3)
    assert {"since", "count", "orders", "timezone"} <= orders.keys()
    assert orders["timezone"] == "Europe/London"

    summary = await shopify_tools.shopify_sales_summary(days=1)
    assert isinstance(summary["orders"], int) and summary["source"]

    if orders["orders"]:
        detail = await shopify_tools.shopify_order_detail(orders["orders"][0]["order_id"])
        assert "items" in detail and "fulfillments" in detail


# --- lessons from the live store ------------------------------------------

@pytest.mark.parametrize("spoken", ["CROOKS-1928", "crooks 1928", "order 1928", "#1928", "1928"])
async def test_all_spoken_order_forms_search_the_bare_number(spoken):
    client = FakeShopify([{"data": {"orders": {"edges": []}}}])
    shopify_tools.bind(client)
    result = await shopify_tools.shopify_find_order(spoken)
    assert result["matched_on"] == "name:1928"


async def test_size_matches_one_segment_of_a_multi_option_variant():
    """Real variant titles look like 'Black / XS'. The size is one segment."""
    client = FakeShopify([{"data": {"products": {"edges": [{"node": {
        "id": "p", "title": "CRX GARMS T-SHIRT", "status": "ACTIVE", "totalInventory": 9,
        "variants": {"edges": [
            {"node": {"id": "v1", "title": "Black / M", "sku": None, "inventoryQuantity": 4,
                      "inventoryPolicy": "DENY", "inventoryItem": {"tracked": True}}},
            {"node": {"id": "v2", "title": "White / L", "sku": None, "inventoryQuantity": 5,
                      "inventoryPolicy": "DENY", "inventoryItem": {"tracked": True}}},
        ]},
    }}]}}}])
    shopify_tools.bind(client)
    variants = (await shopify_tools.shopify_inventory("CRX", size="medium"))["products"][0]["variants"]
    assert [v["variant"] for v in variants] == ["Black / M"]


async def test_oversold_variant_is_explained_not_negative():
    client = FakeShopify([{"data": {"products": {"edges": [{"node": {
        "id": "p", "title": "GREY CONVICT SWEATS", "status": "ACTIVE", "totalInventory": 1,
        "variants": {"edges": [{"node": {"id": "v", "title": "M", "sku": None, "inventoryQuantity": -1,
                                         "inventoryPolicy": "DENY", "inventoryItem": {"tracked": True}}}]},
    }}]}}}])
    shopify_tools.bind(client)
    v = (await shopify_tools.shopify_inventory("convict sweats"))["products"][0]["variants"][0]
    assert v["available"] == 0
    assert v["oversold_by"] == 1
    assert "Oversold" in v["note"]


async def test_first_name_search_with_many_matches_flags_ambiguity_on_orders():
    node = lambda i, n: {  # noqa: E731
        "id": f"gid://shopify/Customer/{i}", "displayName": n,
        "defaultEmailAddress": {"emailAddress": f"{i}@example.com"},
        "numberOfOrders": "1", "amountSpent": {"amount": "10.00", "currencyCode": "GBP"},
    }
    client = FakeShopify([
        {"data": {"customers": {"edges": [{"node": node(1, "Noah Brown")}, {"node": node(2, "Noah Conway")}]}}},
        {"data": {"orders": {"edges": [{"node": ORDER_NODE}]}}},
    ])
    shopify_tools.bind(client)
    result = await shopify_tools.shopify_find_order("Noah")
    assert result["ambiguous"] is True
    assert len(result["customers_matched"]) == 2
    assert "ask which" in result["instruction"].lower()


async def test_customer_search_flags_truncation():
    node = lambda i: {  # noqa: E731
        "id": f"gid://shopify/Customer/{i}", "displayName": f"Noah {i}",
        "defaultEmailAddress": {"emailAddress": f"{i}@example.com"},
        "numberOfOrders": "0", "amountSpent": {"amount": "0", "currencyCode": "GBP"},
    }
    client = FakeShopify([{"data": {"customers": {"edges": [{"node": node(i)} for i in range(3)]}}}])
    shopify_tools.bind(client)
    result = await shopify_tools.shopify_find_customer("Noah", limit=3)
    assert result["truncated"] is True
    assert result["customers"][0]["orders"] == 0  # numberOfOrders arrives as a string


async def test_empty_customer_query_is_omitted():
    client = FakeShopify([{"data": {"customers": {"edges": []}}}])
    shopify_tools.bind(client)
    await shopify_tools._search_customers(client, "", limit=5)
    assert client.queries[0][1]["q"] is None


async def test_catalogue_takes_only_colour_option_values():
    client = FakeShopify([
        {"data": {"products": {"edges": [{"node": {
            "title": "CRX GARMS T-SHIRT",
            "options": [{"name": "Colour", "values": ["Black", "White"]},
                        {"name": "Size", "values": ["XS", "S", "M"]},
                        {"name": "Grey Convict Hoodie (Size)", "values": ["XS"]},
                        {"name": "Quantity", "values": ["1pc", "3pc"]}],
        }}]}}},
        {"data": {"customers": {"edges": []}}},
    ])
    shopify_tools.bind(client)
    terms = await shopify_tools.catalogue_terms()
    assert "Black" in terms and "White" in terms
    for noise in ("XS", "S", "M", "1pc", "3pc"):
        assert noise not in terms
