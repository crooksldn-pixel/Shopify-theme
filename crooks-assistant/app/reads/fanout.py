"""A bounded fan-out, for the reads that really are one per thing — §14.

Most of D-4's N+1 is not a fan-out problem: seven `shopify_customer_history` calls to learn
whether seven buyers had bought before were seven reads for a fact the Mac already held, and
the fix is `app/analytics/summarise.py`, not a faster way of making seven requests.

But some reads genuinely are per-entity. "Which of today's customers have emailed us" has to
ask Gmail about each customer, because Gmail has no query that answers it in one. For those
there are three rules, and this module is the one place they are kept:

* **Bounded by the SOURCE's own slots**, read from `app/reads/budget.py` SOURCE_SLOTS. Not by
  a number written next to the call site: `email_query` kept its own semaphore of four while
  `SOURCE_SLOTS["gmail"]` was three, and two bounds on one thing is how they come to
  disagree. One table, read here.
* **Through the global throttle**, so a fan-out in a background lane cannot take the last
  slot the owner's read needs. `budget.throttle().admit` is the same check the read scheduler
  makes, and an owner lane is never refused.
* **Partial, and honest about it.** A failed read is a reported read: `gather_with_failures`
  returns what came back and what did not, so a summary that lost a row says so rather than
  quietly counting it out. That is the same rule `ReadResult.errors` keeps for a plan.

What this is NOT: a second read scheduler. `app/reads/scheduler.py` runs a GRAPH of named,
different reads with dependencies between them, which is a different shape. This runs ONE
read over MANY items, which a graph cannot express without a node per item. Neither can
write: both refuse a write tool, and nothing here dispatches a tool at all — the caller
passes the coroutine function, and `assert_read_only`/`assert_reads_only` still guard the
paths that name tools.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable, Iterable
from typing import Any, TypeVar

from app.reads import budget

log = logging.getLogger("crooks.reads")

T = TypeVar("T")
R = TypeVar("R")

# The most items one fan-out may cover, whatever the source allows in flight. A question that
# needs a two-hundredth read is a question to narrow, not to parallelise: `email_query` already
# refuses a set of more than fifty for the same reason, in the owner's words.
MAX_ITEMS = 50

# How long one item's read may take before it is abandoned and reported. Shorter than the
# scheduler's per-read timeout because a fan-out's whole point is that the answer is the SET:
# one slow member must not hold the other forty-nine.
ITEM_TIMEOUT_S = 7.0


def slots_for(source: str, lane: str = "") -> int:
    """How many of this source may be in flight in this lane. One table, read, never copied."""
    lane = lane or budget.lane_name()
    return max(1, budget.throttle().slots(source, lane))


async def gather(
    items: Iterable[T],
    read: Callable[[T], Awaitable[R]],
    *,
    source: str,
    lane: str = "",
    timeout_s: float = ITEM_TIMEOUT_S,
    limit: int = MAX_ITEMS,
) -> list[R | None]:
    """`read` over every item, at most `slots_for(source)` at a time, in the items' own order.

    A failed or refused item is `None` in its place. Use `gather_with_failures` when the
    caller has to tell "nothing there" from "could not look", which any surface that shows a
    count does.
    """
    out, _failed = await gather_with_failures(
        items, read, source=source, lane=lane, timeout_s=timeout_s, limit=limit,
    )
    return out


async def gather_with_failures(
    items: Iterable[T],
    read: Callable[[T], Awaitable[R]],
    *,
    source: str,
    lane: str = "",
    timeout_s: float = ITEM_TIMEOUT_S,
    limit: int = MAX_ITEMS,
) -> tuple[list[R | None], dict[Any, str]]:
    """(results in order, {item: why it did not come back}).

    The failure key is the item itself when it can be a dictionary key, and its index when it
    cannot — a caller that fans out over dicts still gets told which one failed.
    """
    wanted = list(items)[: max(1, int(limit))]
    if not wanted:
        return [], {}
    lane = lane or budget.lane_name()
    throttle = budget.throttle()
    gate = asyncio.Semaphore(slots_for(source, lane))
    out: list[R | None] = [None] * len(wanted)
    failed: dict[Any, str] = {}

    def name_of(index: int) -> Any:
        item = wanted[index]
        try:
            hash(item)
        except TypeError:
            return index
        return item

    async def one(index: int) -> None:
        async with gate:
            if not throttle.admit(source, lane):
                # A lower lane at the source's ceiling stands down rather than spending the
                # rate the owner is waiting on. Never an owner lane: `Throttle.admit` never
                # refuses one, which is the guarantee D-4 (phase 4) was about.
                failed[name_of(index)] = f"{source} is busy with work the owner is waiting on"
                return
            with throttle.holding(source, lane), budget.using(lane, budget.current_lane()[1], yielding=False):
                try:
                    out[index] = await asyncio.wait_for(read(wanted[index]), timeout=timeout_s)
                except TimeoutError:
                    failed[name_of(index)] = f"the {source} read did not come back in {timeout_s:.0f}s"
                except Exception as exc:  # noqa: BLE001 — a failed read is a reported read
                    failed[name_of(index)] = f"{type(exc).__name__}: {exc}"[:200]

    await asyncio.gather(*(one(index) for index in range(len(wanted))))
    if failed:
        log.debug("fan-out over %s: %d of %d did not come back", source, len(failed), len(wanted))
    return out, failed
