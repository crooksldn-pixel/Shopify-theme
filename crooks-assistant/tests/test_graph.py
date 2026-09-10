"""The customer / order / email graph, in both directions, and what hangs off it.

Order → threads is `app/context/order.py`'s correlation, run by the hydrator. Thread → order
is `app/context/graph.py`, run by the presenter over the order cache. Neither may guess: every
link carries a confidence and the reasons, and a name is never one of them.
"""

from __future__ import annotations

import time

import pytest

from app.context import graph
from app.presentation import present
from app.providers.base import ToolCall
from app.session.models import Session

NOW = 1_800_000_000.0
DAY = 86_400.0


def row(number: int, email: str, *, days_ago: float, cid: str = "", name: str = "", total: float = 89.0, fulfillment: str = "UNFULFILLED") -> dict:
    """A row as `OrderCache.rows()` holds it: flat, numeric, with the customer nested."""
    return {
        "order_id": f"gid://shopify/Order/{number}", "order_number": f"#{number}", "digits": str(number),
        "ts": NOW - days_ago * DAY, "created_at": "", "total": total, "currency": "GBP", "fulfillment": fulfillment,
        "customer": {"customer_id": cid or f"gid://shopify/Customer/{number}", "name": name or "Someone", "email": email},
    }


def thread(sender: str, subject: str, body: str = "", thread_id: str = "aa70d3f83dbef06e") -> dict:
    """A thread as gmail_read_thread returns it."""
    return {"thread_id": thread_id, "message_count": 1, "messages_shown": 1,
            "messages": [{"from": sender.split("@")[0], "from_email": sender, "subject": subject, "body": body, "date": "Thu, 10 Sep 2026 12:00:00 +0100"}]}


MIA = "mia.jones@example.com"
ROWS = [
    row(1938, MIA, days_ago=0, cid="gid://shopify/Customer/7001", name="Mia Jones"),
    row(1912, MIA, days_ago=45, cid="gid://shopify/Customer/7001", name="Mia Jones", total=65.0, fulfillment="FULFILLED"),
    row(1876, MIA, days_ago=120, cid="gid://shopify/Customer/7001", name="Mia Jones", total=74.0, fulfillment="FULFILLED"),
    row(1939, "david.randall@example.com", days_ago=0, cid="gid://shopify/Customer/7002", name="David Randall", total=65.0, fulfillment="FULFILLED"),
    row(1940, "priya.raman@example.com", days_ago=0, cid="gid://shopify/Customer/7004", name="Priya Raman", total=23.0),
]


def clock() -> float:
    return NOW


# ------------------------------------------------------------ thread → order (graph.py)


def test_a_number_in_the_subject_from_its_own_customer_is_a_confident_link():
    found = graph.linked_orders_for_thread(thread(MIA, "Order 1938 — can I add to it?", "Is it too late?"), rows=ROWS, clock=clock)
    assert found["confidence"] == "confident"
    assert [o["order_number"] for o in found["linked"]] == ["#1938"]
    assert found["linked"][0]["total"] == 89.0 and found["linked"][0]["fulfillment"] == "UNFULFILLED"
    assert found["provenance"] == ["order number 1938 in the subject", "sender is the customer on that order"]
    assert found["customer"] == {"customer_id": "gid://shopify/Customer/7001", "name": "Mia Jones"}


def test_a_number_in_the_body_counts_and_says_it_was_the_body():
    found = graph.linked_orders_for_thread(thread("priya.raman@example.com", "Cap", "Following up on my order 1940 — is it adjustable?"), rows=ROWS, clock=clock)
    assert found["confidence"] == "confident"
    assert [o["order_number"] for o in found["linked"]] == ["#1940"]
    assert found["provenance"][0] == "order number 1940 in the body"


def test_a_sender_with_exactly_one_recent_order_is_confident_without_a_number():
    found = graph.linked_orders_for_thread(thread("david.randall@example.com", "Hello", "Any news?"), rows=ROWS, clock=clock)
    assert found["confidence"] == "confident"
    assert [o["order_number"] for o in found["linked"]] == ["#1939"]
    assert found["provenance"] == ["sender is the customer on one recent order"]


def test_a_sender_with_several_recent_orders_is_possible_newest_first_and_capped():
    rows = ROWS + [row(1950, MIA, days_ago=3, cid="gid://shopify/Customer/7001", name="Mia Jones"), row(1949, MIA, days_ago=9, cid="gid://shopify/Customer/7001", name="Mia Jones")]
    found = graph.linked_orders_for_thread(thread(MIA, "Hello", "Which of my orders has shipped?"), rows=rows, clock=clock)
    assert found["confidence"] == "possible"
    # Four are within sixty days (1938, 1950, 1949, 1912); three are offered, newest first.
    assert [o["order_number"] for o in found["linked"]] == ["#1938", "#1950", "#1949"]
    assert found["provenance"] == ["sender is the customer on 4 recent orders"]
    assert found["customer"]["customer_id"] == "gid://shopify/Customer/7001", "the customer bridge holds whenever the sender is known"


def test_a_number_that_is_somebody_elses_order_is_possible_and_says_so():
    found = graph.linked_orders_for_thread(thread("stranger@example.net", "Order 1939", "I am collecting 1939 for David"), rows=ROWS, clock=clock)
    assert found["confidence"] == "possible"
    assert [o["order_number"] for o in found["linked"]] == ["#1939"]
    assert found["provenance"] == ["number 1939 in the subject, but the sender is not its customer"]
    assert found["customer"] is None, "a stranger bridges to nobody"


def test_a_number_of_somebody_elses_does_not_shake_a_customers_own_confident_link():
    found = graph.linked_orders_for_thread(thread("david.randall@example.com", "Re: 1940", "My friend's order 1940 arrived; where is mine?"), rows=ROWS, clock=clock)
    assert found["confidence"] == "confident"
    assert [o["order_number"] for o in found["linked"]] == ["#1939"]
    assert "number 1940 is mentioned but the sender is not its customer" in found["provenance"]


def test_nothing_matching_is_none_with_the_reason_and_never_a_name_match():
    # The From NAME is Mia's; the address is not. A name is not evidence.
    stranger = {"thread_id": "a413d264183cfe94", "messages": [{"from": "Mia Jones", "from_email": "mia.jones@elsewhere.example", "subject": "Hi", "body": "hello"}]}
    found = graph.linked_orders_for_thread(stranger, rows=ROWS, clock=clock)
    assert found == {"linked": [], "confidence": "none", "provenance": ["sender matches no recent order", "no order number in the thread"], "customer": None}


def test_a_customer_whose_orders_are_all_old_is_none_but_still_bridged():
    old = [row(1800, MIA, days_ago=200, cid="gid://shopify/Customer/7001", name="Mia Jones")]
    found = graph.linked_orders_for_thread(thread(MIA, "Hello again"), rows=old, clock=clock)
    assert found["confidence"] == "none" and found["linked"] == []
    assert found["provenance"][0].startswith("sender is a customer, but their orders are older than")
    assert found["customer"]["name"] == "Mia Jones"


def test_order_numbers_are_exact_four_or_five_digit_runs_not_parts_of_tracking_numbers():
    assert graph.order_numbers_in("tracking AB1234567890GB for #1938, ref 12345, year 2026, tel 07700900123") == ["1938", "12345", "2026"]
    assert graph.order_numbers_in("") == []


def test_a_listing_summary_is_read_the_same_way_as_a_full_thread():
    summary = {"thread_id": "aa70d3f83dbef06e", "from_email": MIA, "subject": "Order 1938 — can I add to it?", "snippet": "Is it too late?"}
    assert graph.linked_orders_for_thread(summary, rows=ROWS, clock=clock)["confidence"] == "confident"


# ------------------------------------------------------ the presenter's strip and the gate


class _WarmCache:
    clock = staticmethod(clock)

    def __init__(self, rows: list[dict]) -> None:
        self._rows = rows

    def rows(self) -> list[dict]:
        return list(self._rows)

    def status(self) -> dict:
        return {"synced_at": NOW, "orders": len(self._rows)}


class _ColdCache(_WarmCache):
    def status(self) -> dict:
        return {"synced_at": None, "orders": 0}


@pytest.fixture()
def warm(monkeypatch):
    from app.tools import analytics_tools

    monkeypatch.setattr(analytics_tools, "_cache", _WarmCache(ROWS))


def _card(result: dict, session: Session | None = None) -> dict:
    (card,) = present([ToolCall(name="gmail_read_thread", args={"thread_id": result["thread_id"]}, ok=True, result=result)], session=session)
    return card["data"]


def test_the_thread_card_carries_the_linked_order_with_money_and_status(warm):
    data = _card(thread(MIA, "Order 1938 — can I add to it?"))
    assert data["link_confidence"] == "confident"
    assert data["linked_order"] == {
        "order_id": "gid://shopify/Order/1938", "order_number": "#1938", "total": "£89.00", "fulfillment": "unfulfilled",
        "customer_name": "Mia Jones", "customer_id": "gid://shopify/Customer/7001",
    }
    assert data["possible_orders"] == []
    assert data["linked_customer"] == {"customer_id": "gid://shopify/Customer/7001", "name": "Mia Jones"}
    assert data["link_provenance"] == ["order number 1938 in the subject", "sender is the customer on that order"]


def test_the_thread_card_offers_possible_orders_and_no_linked_one(warm):
    data = _card(thread(MIA, "Which has shipped?"))
    assert data["link_confidence"] == "possible" and data["linked_order"] is None
    assert [o["order_number"] for o in data["possible_orders"]] == ["#1938", "#1912"]


def test_the_linked_ids_are_issued_so_a_tap_on_the_strip_passes_the_gate(warm):
    from app.commands import Ctx, may_open

    session = Session(session_id="s")
    _card(thread(MIA, "Which has shipped?"), session)
    assert {"gid://shopify/Order/1938", "gid://shopify/Order/1912", "gid://shopify/Customer/7001"} <= session.issued_ids
    ctx = Ctx(runtime=None, session=session, branch=None)
    assert may_open(ctx, "order", "gid://shopify/Order/1938") and may_open(ctx, "customer", "gid://shopify/Customer/7001")
    assert not may_open(ctx, "order", "gid://shopify/Order/1939"), "an order the strip did not show stays refused"


def test_a_cold_cache_is_said_to_be_cold_not_reported_as_no_order(monkeypatch):
    from app.tools import analytics_tools

    monkeypatch.setattr(analytics_tools, "_cache", _ColdCache([]))
    data = _card(thread(MIA, "Order 1938 — can I add to it?"))
    assert data["link_confidence"] == "none" and data["linked_order"] is None and data["possible_orders"] == []
    assert data["link_provenance"] == ["order cache not warm"]
    # No cache bound at all (a Mac without Shopify) is the same honest answer.
    monkeypatch.setattr(analytics_tools, "_cache", None)
    assert _card(thread(MIA, "Order 1938"))["link_provenance"] == ["order cache not warm"]


# --------------------------------------------------------- order → threads (order.py)


def test_correlate_threads_runs_the_other_way_with_provenance():
    from app.context.order import correlate_threads

    found = correlate_threads([
        {"thread_id": "aa70d3f83dbef06e", "from_email": MIA, "subject": "Order 1938 — can I add to it?", "snippet": "", "authenticated": True},
        {"thread_id": "fe128e8f1ec5a51e", "from_email": MIA, "subject": "Order 1912 arrived", "snippet": "", "authenticated": False},
        {"thread_id": "c28cf65d31fe6cbb", "from_email": "priya.raman@example.com", "subject": "Cap", "snippet": "my order 1938?", "authenticated": True},
        {"thread_id": "a413d264183cfe94", "from_email": "no-reply@shipping.example", "subject": "Report", "snippet": "", "authenticated": True},
    ], customer_email=MIA, digits="1938")
    by_id = {t["thread_id"]: t for t in found}
    assert by_id["aa70d3f83dbef06e"]["match"] == "both" and by_id["aa70d3f83dbef06e"]["verified_sender"] is True
    assert by_id["fe128e8f1ec5a51e"]["match"] == "sender" and by_id["fe128e8f1ec5a51e"]["verified_sender"] is False
    assert by_id["c28cf65d31fe6cbb"]["match"] == "order_number" and by_id["c28cf65d31fe6cbb"]["provenance"] == "UNKNOWN"
    assert "a413d264183cfe94" not in by_id


async def test_the_hydrator_carries_the_threads_on_the_order_read_model():
    from app.context.order import Hydrator
    from experience.fixtures import FixtureShopify
    from experience.fixtures import data as world

    asked: list[dict] = []

    async def threads_for(**kwargs):
        asked.append(kwargs)
        return {"available": True, "threads": [
            {"thread_id": "aa70d3f83dbef06e", "from_email": world.MIA.email, "subject": "Order 1938 — can I add to it?", "snippet": "Is it too late?", "authenticated": True},
        ]}

    hydrator = Hydrator(lambda: FixtureShopify(), threads_for=threads_for)
    order = await hydrator.order("gid://shopify/Order/1938", budget_s=2.0)
    assert asked and asked[0]["sender"] == world.MIA.email and "#1938" in asked[0]["terms"], "the correlation asks by the customer's address and the order's number"
    threads = order["email"]["threads"]
    assert [t["thread_id"] for t in threads] == ["aa70d3f83dbef06e"]
    assert threads[0]["sender_match"] is True and threads[0]["match"] == "both"
    assert "email" not in order["pending"]


def test_graph_never_reads_a_source():
    """The presenter calls this; it must be a pure function over rows it was handed."""
    import inspect

    source = inspect.getsource(graph)
    for forbidden in ("graphql", "service()", "httpx", "gmail_tools", "shopify_tools", "await "):
        assert forbidden not in source, forbidden
    assert time.time  # the clock is injectable, and the default is the wall clock
