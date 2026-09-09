"""The tiered cache, the coalescer and the prefetcher.

Two invariants matter more than any hit rate here: a write never reads from this, and a
proven write makes what described the thing it changed unusable at once.
"""

from __future__ import annotations

import asyncio

import pytest

from app.memory import coalesce, prefetch
from app.memory.store import (
    ANALYTICS,
    EMAIL,
    ENTITY,
    EXPIRED,
    FRESH,
    HOT,
    MAX_ENTRIES,
    STALE,
    Memory,
    fingerprint,
    invalidate_for_write,
)


class Clock:
    def __init__(self, now: float = 1000.0) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now

    def tick(self, seconds: float) -> None:
        self.now += seconds


def test_an_entry_carries_where_it_came_from_and_how_old_it_is():
    clock = Clock()
    memory = Memory(clock=clock)
    entry = memory.put(ENTITY, "order:o1", {"order_number": "#1938"}, source="shopify",
                       query=fingerprint("shopify_order_detail", {"order_id": "o1"}), watermark=7,
                       provenance={"recipe": "order_lookup", "ref": "o1"})
    assert entry.source == "shopify" and entry.provenance["recipe"] == "order_lookup"
    assert entry.freshness(clock.now) == FRESH
    public = entry.public(clock.now)
    assert public["age_s"] == 0.0 and public["freshness"] == "fresh" and public["query"]


def test_a_ttl_that_has_run_out_is_a_miss_not_a_stale_answer():
    clock = Clock()
    memory = Memory(clock=clock)
    memory.put(ENTITY, "order:o1", {"n": 1}, source="shopify")
    assert memory.get(ENTITY, "order:o1") is not None
    clock.tick(10_000)
    assert memory.get(ENTITY, "order:o1") is None
    assert memory.misses >= 1


def test_a_moved_watermark_is_stale_and_is_only_handed_over_when_asked_for():
    clock = Clock()
    memory = Memory(clock=clock)
    memory.put(ENTITY, "order:o1", {"n": 1}, source="shopify", watermark=7)
    assert memory.get(ENTITY, "order:o1", watermark=8) is None
    held = memory.get(ENTITY, "order:o1", watermark=8, allow_stale=True)
    assert held is not None and held.freshness(clock.now, watermark=8) == STALE


def test_a_tier_is_bounded_and_drops_what_was_used_least_recently():
    clock = Clock()
    memory = Memory(clock=clock)
    limit = MAX_ENTRIES[HOT]
    for i in range(limit):
        memory.put(HOT, f"k{i}", i, source="mac")
        clock.tick(0.001)
    memory.get(HOT, "k0")           # touched, so it survives
    memory.put(HOT, "extra", 1, source="mac")
    assert memory.get(HOT, "k0") is not None
    assert memory.get(HOT, "k1") is None
    assert memory.evictions >= 1


def test_a_proven_write_makes_what_described_the_thing_unusable():
    clock = Clock()
    memory = Memory(clock=clock)
    memory.put(ENTITY, "order:o1", {"tags": []}, source="shopify")
    memory.put(ENTITY, "order:o2", {"tags": []}, source="shopify")
    memory.put(ANALYTICS, "agg1", {"rows": []}, source="shopify")
    memory.put(EMAIL, "mail1", {"rows": []}, source="gmail")
    dropped = invalidate_for_write("order", "o1", memory=memory)
    assert dropped >= 3
    assert memory.get(ENTITY, "order:o1") is None, "the order that changed"
    assert memory.get(ANALYTICS, "agg1") is None, "every total that counted it"
    assert memory.get(EMAIL, "mail1") is None, "and the inbox correlation built from it"
    assert memory.get(ENTITY, "order:o2") is not None, "but not an order nothing touched"


def test_an_invalidated_entry_is_expired_even_inside_its_ttl():
    clock = Clock()
    memory = Memory(clock=clock)
    entry = memory.put(ENTITY, "order:o1", {"n": 1}, source="shopify")
    invalidate_for_write("order", "o1", memory=memory)
    assert entry.freshness(clock.now) == EXPIRED
    assert memory.get(ENTITY, "order:o1", allow_stale=True) is None


def test_no_write_path_imports_the_cache():
    """The guarantee, checked as text: the action engine may TELL the cache a change landed,
    and must never ASK it anything."""
    from pathlib import Path

    source = Path("app/actions/engine.py").read_text(encoding="utf-8")
    assert "invalidate_for_write" in source
    for forbidden in ("memory().get(", "from app.memory import current", "memory.get("):
        assert forbidden not in source, forbidden


# ------------------------------------------------------------------ coalescing

async def test_the_same_read_asked_twice_is_made_once():
    calls = []
    started = asyncio.Event()
    release = asyncio.Event()
    c = coalesce.Coalescer()

    async def read():
        calls.append(1)
        started.set()
        await release.wait()
        return {"n": len(calls)}

    first = asyncio.create_task(c.run("k", read))
    await started.wait()
    second = asyncio.create_task(c.run("k", read))
    await asyncio.sleep(0)
    release.set()
    assert await first == await second == {"n": 1}
    assert len(calls) == 1 and c.joined == 1 and c.started == 1


async def test_a_joiner_that_gives_up_does_not_cancel_the_flight():
    release = asyncio.Event()
    c = coalesce.Coalescer()

    async def read():
        await release.wait()
        return "value"

    first = asyncio.create_task(c.run("k", read))
    await asyncio.sleep(0)
    second = asyncio.create_task(c.run("k", read))
    await asyncio.sleep(0)
    second.cancel()
    release.set()
    assert await first == "value"


async def test_a_failed_flight_tells_everyone_waiting():
    c = coalesce.Coalescer()

    async def read():
        await asyncio.sleep(0)
        raise RuntimeError("shopify said no")

    first = asyncio.create_task(c.run("k", read))
    await asyncio.sleep(0)
    second = asyncio.create_task(c.run("k", read))
    for task in (first, second):
        with pytest.raises(RuntimeError, match="shopify said no"):
            await task
    assert not c.in_flight("k")


# ------------------------------------------------------------------- prefetch

def test_a_prefetch_may_only_ever_read():
    import app.tools.shopify_tools  # noqa: F401
    import app.tools.shopify_writes  # noqa: F401

    p = prefetch.Prefetcher()
    assert p.readable("shopify_order_detail")
    assert not p.readable("shopify_order_note_append")
    assert not p.readable("batch_order_tags_add")
    assert not p.readable("something_invented")


async def test_prefetch_is_bounded_and_cancellable():
    p = prefetch.Prefetcher()
    release = asyncio.Event()

    async def slow():
        await release.wait()
        return "late"

    assert [p.start(f"k{i}", slow, branch_id="br1") for i in range(5)] == [True, True, True, False, False]
    assert p.counts()["in_flight"] == prefetch.MAX_IN_FLIGHT
    assert p.cancel_branch("br1") == 3
    assert p.counts()["in_flight"] == 0
    release.set()


async def test_a_prefetch_that_has_not_landed_is_never_waited_for():
    p = prefetch.Prefetcher()
    release = asyncio.Event()

    async def slow():
        await release.wait()
        return {"landed": True}

    p.start("k", slow)
    assert p.collect("k") is None
    release.set()
    await asyncio.sleep(0)
    await asyncio.sleep(0)
    assert p.collect("k") == {"landed": True} and p.counts()["hits"] == 1
    p.cancel_all()
