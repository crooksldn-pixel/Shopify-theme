"""The parallel read scheduler: what runs together, what waits, and what may never be in it."""

from __future__ import annotations

import asyncio

import pytest

from app.reads.scheduler import (
    Read,
    ReadPlan,
    WriteInPlan,
    _layers,
    assert_reads_only,
    run_plan,
)
from app.session.models import Session


@pytest.fixture()
def session():
    s = Session(session_id="s1")
    s.turn_id = "turn_x"
    return s


def plan_of(*reads) -> ReadPlan:
    return ReadPlan(list(reads), label="test")


def test_independent_reads_are_one_wave_and_dependents_are_the_next():
    plan = plan_of(
        Read("a", "shopify_find_order", {}),
        Read("b", "gmail_search", {}, source="gmail"),
        Read("c", "shopify_order_detail", {}, after=("a",)),
        Read("d", "shopify_customer_history", {}, after=("a", "b")),
    )
    waves = [[r.name for r in wave] for wave in _layers(plan)]
    assert waves == [["a", "b"], ["c", "d"]]


def test_a_cycle_is_dropped_rather_than_looped():
    plan = plan_of(Read("a", "shopify_find_order", {}, after=("b",)), Read("b", "shopify_find_order", {}, after=("a",)))
    assert _layers(plan) == []


def test_a_write_tool_in_a_plan_is_refused_before_anything_runs():
    import app.tools.batch_tools  # noqa: F401
    import app.tools.shopify_writes  # noqa: F401

    for tool in ("shopify_order_note_append", "batch_order_tags_add"):
        with pytest.raises(WriteInPlan):
            assert_reads_only(plan_of(Read("x", tool, {})))


def test_an_unregistered_tool_is_refused_too():
    with pytest.raises(WriteInPlan, match="not a registered tool"):
        assert_reads_only(plan_of(Read("x", "shopify_do_whatever", {})))


async def test_the_plan_runs_independent_reads_at_the_same_time(session, monkeypatch):
    import app.tools.shopify_tools  # noqa: F401
    from app.providers.base import ToolCall

    live = 0
    peak = 0

    async def fake_dispatch(name, args, *, session, timeout_s, calls=None):
        nonlocal live, peak
        live += 1
        peak = max(peak, live)
        await asyncio.sleep(0.02)
        live -= 1
        if calls is not None:
            calls.append(ToolCall(name=name, args=args, ok=True, duration_ms=20.0, result={"name": args.get("query", name)}))
        return "{}"

    monkeypatch.setattr("app.tools.dispatch.dispatch", fake_dispatch)
    result = await run_plan(plan_of(
        Read("a", "shopify_find_order", {"query": "a"}),
        Read("b", "shopify_find_customer", {"query": "b"}),
        Read("c", "shopify_product_info", {"query": "c"}),
    ), session=session)
    assert peak == 3 and result.groups == [["a", "b", "c"]]
    assert set(result.values) == {"a", "b", "c"}
    assert result.serial_ms > result.critical_path_ms and result.saved_ms > 0


async def test_a_dependent_read_gets_what_the_first_one_found(session, monkeypatch):
    import app.tools.shopify_tools  # noqa: F401
    from app.providers.base import ToolCall

    seen = []

    async def fake_dispatch(name, args, *, session, timeout_s, calls=None):
        seen.append((name, args))
        payload = {"orders": [{"order_id": "o1"}]} if name == "shopify_find_order" else {"order_id": args.get("order_id")}
        if calls is not None:
            calls.append(ToolCall(name=name, args=args, ok=True, result=payload))
        return "{}"

    monkeypatch.setattr("app.tools.dispatch.dispatch", fake_dispatch)
    result = await run_plan(plan_of(
        Read("find", "shopify_find_order", {"query": "1938"}),
        Read("detail", "shopify_order_detail", lambda values: {"order_id": values["find"]["orders"][0]["order_id"]}, after=("find",)),
    ), session=session)
    assert seen == [("shopify_find_order", {"query": "1938"}), ("shopify_order_detail", {"order_id": "o1"})]
    assert result.values["detail"] == {"order_id": "o1"} and result.groups == [["find"], ["detail"]]


async def test_a_read_whose_dependency_failed_is_skipped_not_run_with_a_hole(session, monkeypatch):
    import app.tools.shopify_tools  # noqa: F401
    from app.providers.base import ToolCall

    async def fake_dispatch(name, args, *, session, timeout_s, calls=None):
        ok = name != "shopify_find_order"
        if calls is not None:
            calls.append(ToolCall(name=name, args=args, ok=ok, error=None if ok else "Shopify is rate-limiting us", result={} if ok else None))
        return "{}"

    monkeypatch.setattr("app.tools.dispatch.dispatch", fake_dispatch)
    result = await run_plan(plan_of(
        Read("find", "shopify_find_order", {"query": "1938"}),
        Read("detail", "shopify_order_detail", {"order_id": "o1"}, after=("find",)),
    ), session=session)
    assert "find" in result.errors and result.skipped["detail"] == "what it needed did not come back"
    assert result.partial is True and "detail" not in result.values


async def test_the_results_merge_in_the_order_the_plan_declared(session, monkeypatch):
    import app.tools.shopify_tools  # noqa: F401
    from app.providers.base import ToolCall

    async def fake_dispatch(name, args, *, session, timeout_s, calls=None):
        await asyncio.sleep(0.03 if name == "shopify_find_order" else 0.001)
        if calls is not None:
            calls.append(ToolCall(name=name, args=args, ok=True, result={"tool": name}))
        return "{}"

    monkeypatch.setattr("app.tools.dispatch.dispatch", fake_dispatch)
    result = await run_plan(plan_of(
        Read("slow", "shopify_find_order", {}),
        Read("fast", "shopify_find_customer", {}),
    ), session=session)
    assert [c.name for c in result.calls] == ["shopify_find_order", "shopify_find_customer"], "plan order, not finish order"


async def test_a_source_budget_that_is_spent_stops_asking(session, monkeypatch):
    import app.tools.shopify_tools  # noqa: F401
    from app.providers.base import ToolCall

    ran = []

    async def fake_dispatch(name, args, *, session, timeout_s, calls=None):
        ran.append(name)
        if calls is not None:
            calls.append(ToolCall(name=name, args=args, ok=True, result={}))
        return "{}"

    monkeypatch.setattr("app.tools.dispatch.dispatch", fake_dispatch)
    result = await run_plan(plan_of(
        Read("a", "shopify_find_order", {}, cost=800.0),
        Read("b", "shopify_find_customer", {}, cost=800.0),
    ), session=session)
    assert len(ran) == 1
    assert "budget for this answer is spent" in " ".join(result.skipped.values())
