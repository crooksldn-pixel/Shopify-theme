"""Shopify tool shaping, and the DST bug that only shows up in summer.

The live-store tests assert shape, not values — an order count changes every hour, so asserting
one guarantees a test that fails for the wrong reason.
"""

from __future__ import annotations

from datetime import datetime, timedelta
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

@pytest.mark.live
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


async def test_product_info_parses_measurements_and_narrows_by_size():
    client = FakeShopify([{"data": {"products": {"edges": [{"node": {
        "id": "p", "title": "BLUE WASH YARD JEANS", "status": "ACTIVE",
        "description": "Yard jeans — Blue wash. 14oz denim.",
        "metafields": {"edges": [
            {"node": {"key": "fabric", "type": "single_line_text_field", "value": "14oz denim"}},
            {"node": {"key": "care", "type": "multi_line_text_field", "value": "Cold wash inside out."}},
            {"node": {"key": "measurements", "type": "json", "value":
             '[{"size":"S","waist":"81.3cm","inseam":"76.2cm"},{"size":"M","waist":"86.4cm","inseam":"77.5cm"}]'}},
            {"node": {"key": "set_partner", "type": "product_reference", "value": "gid://x"}},
        ]},
    }}]}}}])
    shopify_tools.bind(client)
    result = await shopify_tools.shopify_product_info("yard jeans", size="medium")
    info = result["products"][0]
    assert info["fabric"] == "14oz denim" and info["care"].startswith("Cold wash")
    assert info["measurements"] == [{"size": "M", "waist": "86.4cm", "inseam": "77.5cm"}]
    assert "set_partner" not in info


async def test_product_info_without_measurements_says_so():
    client = FakeShopify([{"data": {"products": {"edges": [{"node": {
        "id": "p", "title": "HYDROCUFF WINDBREAKER", "status": "ACTIVE", "description": "",
        "metafields": {"edges": []},
    }}]}}}])
    shopify_tools.bind(client)
    info = (await shopify_tools.shopify_product_info("hydrocuff"))["products"][0]
    assert info["measurements"] == []
    assert "No measurements" in info["measurements_note"]


async def test_product_info_is_green_and_registered():
    from app.tools.gate import Tier, classify
    from app.tools.registry import get

    assert classify("shopify_product_info", {"product": "jeans"}).tier is Tier.GREEN
    assert get("shopify_product_info").tier is Tier.GREEN


async def test_catalogue_includes_store_short_names():
    client = FakeShopify([
        {"data": {"products": {"edges": [{"node": {
            "title": "GREY CONVICT HOODIE", "options": [], "shortName": {"value": "Convict Hoodie"},
        }}]}}},
        {"data": {"customers": {"edges": []}}},
    ])
    shopify_tools.bind(client)
    assert "Convict Hoodie" in await shopify_tools.catalogue_terms()


# --- the review's findings ---------------------------------------------------

async def test_yesterday_is_an_explicit_window():
    """days=1, days_ago=1 must be exactly yesterday, with both bounds in the query."""
    client = FakeShopify([{"data": {"orders": {"edges": [], "pageInfo": {"hasNextPage": False}}}}])
    shopify_tools.bind(client)
    result = await shopify_tools.shopify_list_orders(days=1, days_ago=1)
    q = client.queries[0][1]["q"]
    assert "created_at:>=" in q and "created_at:<" in q
    start = datetime.fromisoformat(result["since"].replace("Z", "+00:00"))
    end = datetime.fromisoformat(result["until"].replace("Z", "+00:00"))
    assert (end - start).total_seconds() == 86400
    london_end = end.astimezone(ZoneInfo("Europe/London"))
    assert london_end.date() == datetime.now(ZoneInfo("Europe/London")).date()


async def test_throttling_arrives_as_http_200_and_is_named():
    from app.clients.shopify import ShopifyError

    class Throttled(FakeShopify):
        async def graphql(self, query, variables=None):
            raise ShopifyError("Shopify is rate-limiting us. Try again in a moment.")

    shopify_tools.bind(Throttled([]))
    with pytest.raises(ShopifyError, match="rate-limiting"):
        await shopify_tools.shopify_sales_summary(days=1)


def test_throttled_extension_code_is_detected():
    """The real client: a 200 with errors[].extensions.code == THROTTLED is a throttle."""
    import asyncio

    from app.clients.shopify import ShopifyClient, ShopifyError

    class FakeResponse:
        status_code = 200
        text = ""

        def json(self):
            return {"data": None, "errors": [{"message": "Throttled", "extensions": {"code": "THROTTLED"}}]}

    client = ShopifyClient("x.myshopify.com", "2025-07", auth_mode="static_token")

    async def run():
        import httpx

        class FakeHttp:
            def __init__(self, *a, **k): pass
            async def __aenter__(self): return self
            async def __aexit__(self, *a): return False
            async def post(self, *a, **k): return FakeResponse()

        original = httpx.AsyncClient
        httpx.AsyncClient = FakeHttp
        try:
            client._access_token = lambda: _coro("tok")  # type: ignore[assignment]
            with pytest.raises(ShopifyError, match="rate-limiting"):
                await client.graphql("query { shop { name } }")
        finally:
            httpx.AsyncClient = original

    asyncio.run(run())


async def _coro(value):
    return value


def test_product_query_strips_search_syntax():
    assert shopify_tools._product_query('yard "jeans" *') == "yard  jeans"
    assert shopify_tools._product_query("") == "*"
    assert ":" not in shopify_tools._search_term("title:jeans") and "*" not in shopify_tools._search_term("a*")


async def test_email_lookup_is_quoted():
    client = FakeShopify([{"data": {"customers": {"edges": []}}}])
    shopify_tools.bind(client)
    await shopify_tools._search_customers(client, "email:evil*@x.com", limit=1)
    assert client.queries[0][1]["q"] == 'email:"evil @x.com"'


async def test_inventory_limit_is_capped_for_query_cost():
    client = FakeShopify([{"data": {"products": {"edges": []}}}])
    shopify_tools.bind(client)
    await shopify_tools.shopify_inventory("jeans", limit=50)
    assert client.queries[0][1]["n"] == shopify_tools.MAX_PRODUCTS


@pytest.mark.parametrize(
    "doc",
    [
        "mutation { orderUpdate(input: {}) { order { id } } }",
        "mutation M($id: ID!) { orderCancel(orderId: $id) { job { id } } }",
        "  # a comment\n  mutation { x }",
        "MUTATION { y }",
    ],
)
async def test_client_refuses_any_mutation(doc):
    from app.clients.shopify import ShopifyClient, ShopifyError, _is_mutation

    assert _is_mutation(doc)
    client = ShopifyClient("x.myshopify.com", "2025-07", auth_mode="static_token")
    with pytest.raises(ShopifyError, match="never sends"):
        await client.graphql(doc)


@pytest.mark.parametrize("doc", ["query { shop { name } }", "{ shop { name } }", "query Q($n: Int!) { orders(first: $n) { edges { node { id } } } }"])
def test_reads_are_not_mutations(doc):
    from app.clients.shopify import _is_mutation

    assert not _is_mutation(doc)


async def test_sales_summary_can_break_the_window_down_by_day():
    """'How were sales each day this week' used to cost seven tool calls; one call with
    by_day=true answers it, bucketed by the shop's own calendar day."""
    from datetime import UTC

    tz = ZoneInfo("Europe/London")
    today = datetime.now(tz).date()
    yesterday = today - timedelta(days=1)

    def node(i, day, amount):
        created = datetime(day.year, day.month, day.day, 10, 0, tzinfo=tz).astimezone(UTC)
        return {"cursor": str(i), "node": {
            "id": str(i), "createdAt": created.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "displayFinancialStatus": "PAID",
            "currentTotalPriceSet": {"shopMoney": {"amount": amount, "currencyCode": "GBP"}},
        }}

    client = FakeShopify([{"data": {"orders": {
        "edges": [node(1, yesterday, "40.00"), node(2, today, "10.00"), node(3, today, "5.50")],
        "pageInfo": {"hasNextPage": False},
    }}}])
    shopify_tools.bind(client)
    result = await shopify_tools.shopify_sales_summary(days=2, by_day=True)
    assert result["orders"] == 3 and result["revenue"] == 55.5
    assert result["by_day"] == [
        {"date": yesterday.isoformat(), "orders": 1, "revenue": 40.0},
        {"date": today.isoformat(), "orders": 2, "revenue": 15.5},
    ]
    assert "createdAt" in client.queries[0][0]
    assert result["caveat"] is None


async def test_sales_summary_breakdown_lists_empty_days_and_stops_at_a_month():
    empty = {"data": {"orders": {"edges": [], "pageInfo": {"hasNextPage": False}}}}
    shopify_tools.bind(FakeShopify([empty]))
    result = await shopify_tools.shopify_sales_summary(days=3, by_day=True)
    assert [d["orders"] for d in result["by_day"]] == [0, 0, 0], "a quiet day is a row, not a gap"
    assert result["by_day"][0]["date"] < result["by_day"][-1]["date"]

    shopify_tools.bind(FakeShopify([empty]))
    result = await shopify_tools.shopify_sales_summary(days=60, by_day=True)
    assert result["by_day"] is None and "31" in result["caveat"]

    shopify_tools.bind(FakeShopify([empty]))
    assert (await shopify_tools.shopify_sales_summary(days=7))["by_day"] is None, "off unless asked"
