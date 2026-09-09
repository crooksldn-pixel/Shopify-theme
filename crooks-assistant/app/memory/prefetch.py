"""Speculative prefetch: read, in the background, the thing the owner is most likely to ask
for next — and nothing else.

Four rules, all of them bounds:

* READ ONLY. Nothing here can reach a write tool; `_READABLE` is the whole vocabulary.
* BOUNDED. At most `MAX_IN_FLIGHT` at a time, at most `MAX_PER_TURN` started per turn, each
  with its own timeout, and never for a source already at its concurrency limit.
* CANCELABLE. Everything started is tracked and dropped when the branch is cancelled or the
  conversation moves on.
* FRESHNESS AWARE. A prefetch whose answer is already fresh in memory does not run.

A prefetch that does not land in time costs nothing: the read it would have saved happens
anyway, at the price it always had.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

log = logging.getLogger("crooks.memory")

MAX_IN_FLIGHT = 3
MAX_PER_TURN = 2
TIMEOUT_S = 6.0

# The only tools a prefetch may call. Read tools, by name, checked against the registry at
# call time as well: a tool that gained a write later must not become prefetchable silently.
_READABLE = frozenset({
    "shopify_find_order", "shopify_order_detail", "shopify_find_customer",
    "shopify_customer_history", "shopify_product_info", "shopify_inventory",
    "gmail_search", "gmail_read_thread", "commerce_query", "commerce_aggregate",
    "inventory_query", "email_query",
})


class Prefetcher:
    def __init__(self) -> None:
        self._tasks: dict[str, asyncio.Task] = {}
        self.started = 0
        self.hits = 0
        self.cancelled = 0

    def readable(self, tool: str) -> bool:
        """Read-only, by this module's own list AND by the registry. Both must agree."""
        if tool not in _READABLE:
            return False
        try:
            from app.tools import registry

            spec = registry.get(tool)
        except Exception:  # noqa: BLE001 — an unregistered tool is not prefetchable
            return False
        return spec.write is None and spec.batch is None

    def start(self, key: str, factory, *, branch_id: str = "") -> bool:
        """Begin one speculative read. False when a bound says no."""
        if key in self._tasks and not self._tasks[key].done():
            return False
        self._reap()
        # In flight, not held: `_reap` keeps a finished task for a while so `collect` can
        # still find it, and counting those against the limit would stop prefetching for
        # twelve seconds after three quick reads.
        if sum(1 for t in self._tasks.values() if not t.done()) >= MAX_IN_FLIGHT:
            return False
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return False

        async def guarded() -> Any:
            try:
                return await asyncio.wait_for(factory(), timeout=TIMEOUT_S)
            except (TimeoutError, asyncio.CancelledError):
                raise
            except Exception as exc:  # noqa: BLE001 — a speculative read that fails costs nothing
                log.debug("prefetch %s failed: %s", key, exc)
                return None

        task = loop.create_task(guarded())
        task.crooks_branch = branch_id      # type: ignore[attr-defined]
        task.crooks_started = time.monotonic()   # type: ignore[attr-defined]
        self._tasks[key] = task
        self.started += 1
        return True

    def collect(self, key: str) -> Any:
        """What a prefetch found, if it has landed. Never waits."""
        task = self._tasks.get(key)
        if task is None or not task.done() or task.cancelled():
            return None
        if task.exception() is not None:
            return None
        value = task.result()
        if value is not None:
            self.hits += 1
        return value

    def cancel_branch(self, branch_id: str) -> int:
        stopped = 0
        for key, task in list(self._tasks.items()):
            if getattr(task, "crooks_branch", "") == branch_id and not task.done():
                task.cancel()
                del self._tasks[key]
                stopped += 1
        self.cancelled += stopped
        return stopped

    def cancel_all(self) -> int:
        stopped = 0
        for key, task in list(self._tasks.items()):
            if not task.done():
                task.cancel()
                stopped += 1
            del self._tasks[key]
        self.cancelled += stopped
        return stopped

    def _reap(self) -> None:
        for key, task in list(self._tasks.items()):
            if task.done():
                if not task.cancelled() and task.exception() is not None:
                    task.exception()
                # Kept briefly so `collect` can still find it; dropped once it is old.
                if time.monotonic() - getattr(task, "crooks_started", 0.0) > TIMEOUT_S * 2:
                    del self._tasks[key]

    def counts(self) -> dict[str, int]:
        return {"started": self.started, "hits": self.hits, "cancelled": self.cancelled, "in_flight": sum(1 for t in self._tasks.values() if not t.done())}


_current: Prefetcher | None = None


def current() -> Prefetcher:
    global _current
    if _current is None:
        _current = Prefetcher()
    return _current


def install(prefetcher: Prefetcher) -> Prefetcher:
    global _current
    _current = prefetcher
    return prefetcher
