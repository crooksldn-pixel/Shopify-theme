"""The claims rule: what the Mac composes, by the words of a question; a refusal of it is a
false unsupported claim; bulk requests and follow-up shapes are found the same way."""

from __future__ import annotations

import pytest

from app.observability import claims

REGISTERED = frozenset({"commerce_aggregate", "commerce_query", "inventory_query", "email_query", "batch_order_tags_add", "batch_order_tags_remove", "batch_email_archive", "batch_email_drafts"})


@pytest.mark.parametrize("question, keys", [
    ("what were our best sellers this month", ["best_sellers"]),
    ("how many orders did we take last week", ["period_sales"]),
    ("which size of the joggers sells most", ["best_sellers", "breakdown"]),
    ("how does this week compare with last week", ["comparison"]),
    ("what's the average order value", ["aov"]),
    ("how many days of stock do we have on the black joggers", ["velocity"]),
    ("which customers have spent over 250 pounds", ["customers_ranked"]),
    ("orders older than five days still to ship", ["delayed_orders"]),
    ("how much revenue is tied up in unfulfilled orders", ["delayed_orders", "unfulfilled_value"]),
    ("which of them have emailed us", ["cross_source"]),
    ("tag all of those delayed", ["delayed_orders", "bulk_tags"]),
    ("archive all of them", ["bulk_archive"]),
    ("draft an email to each of them", ["bulk_drafts"]),
    ("what is the inseam on the jeans", []),
])
def test_questions_match_the_capabilities_the_mac_composes(question, keys):
    assert [c.key for c in claims.match_capabilities(question)] == keys


def test_a_refusal_of_a_composable_question_is_a_false_unsupported_claim():
    signal = claims.claim("what sold best by colour last month", "I can't break sales down by colour from here.", [], REGISTERED)
    assert signal == {"false_unsupported": True, "capabilities": ["best_sellers", "breakdown"], "composable_via": ["commerce_aggregate"], "attempted": [], "hinted": False}
    assert claims.claim("what sold best by colour last month", "Black joggers, then the grey hoodie.", [], REGISTERED) is None, "no refusal, no claim"
    honest = claims.claim("give daniel ten pounds of store credit", "I can't add store credit from here.", [{"tool": "shopify_customer_store_credit_add"}], REGISTERED)
    assert honest == {"false_unsupported": False, "capabilities": [], "composable_via": [], "attempted": ["shopify_customer_store_credit_add"], "hinted": False}
    without = claims.claim("what sold best by colour last month", "I can't break sales down by colour.", [], frozenset())
    assert without is not None and without["false_unsupported"] is False, "a capability not registered on this Mac is not a false claim"


def test_bulk_requests_are_found_and_told_apart_from_the_ones_with_no_batch():
    assert claims.bulk_request("tag all of them delayed") == {"operation": "tags", "supported": True, "tool": "batch_order_tags_add"}
    assert claims.bulk_request("archive those") == {"operation": "archive", "supported": True, "tool": "batch_email_archive"}
    assert claims.bulk_request("email each of them about the delay") == {"operation": "drafts", "supported": True, "tool": "batch_email_drafts"}
    assert claims.bulk_request("refund all of them") == {"operation": "refund", "supported": False, "tool": ""}
    assert claims.bulk_request("cancel every one of them") == {"operation": "cancel", "supported": False, "tool": ""}
    assert claims.bulk_request("ship them all today") == {"operation": "fulfil", "supported": False, "tool": ""}
    assert claims.bulk_request("do that for each of them") == {"operation": "unknown", "supported": False, "tool": ""}
    assert claims.bulk_request("show me order 1938") is None


@pytest.mark.parametrize("question, shape", [
    ("just this week", "period"), ("last month", "period"), ("and yesterday?", "period"), ("by size", "group"), ("now by colour", "group"),
    ("only joggers", "filter"), ("just the UK ones", "filter"), ("show me those", "set"), ("these", "set"), ("more", "more"),
    ("what were the best sellers this month", None), ("just", None),
])
def test_follow_up_shapes(question, shape):
    assert claims.follow_up_shape(question) == shape
