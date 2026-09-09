"""The parallel read scheduler.

A turn that needs an order, its customer's history and that customer's recent email is three
reads, two of which depend on the first. Run serially that is three round trips one after
another; run as a graph it is two. This module is the graph.

    plan = ReadPlan([
        Read("order", "shopify_find_order", {"query": "1938"}, source="shopify"),
        Read("history", "shopify_customer_history", args_from=..., after=("order",), source="shopify"),
        Read("email", "gmail_search", args_from=..., after=("order",), source="gmail"),
    ])
    result = await run_plan(plan, session=session)

What it guarantees:

* Only independent reads run together. `after` is the dependency; a read whose dependency
  failed is skipped, not run with a hole in its arguments.
* Per-source concurrency limits, so four parallel reads do not become four simultaneous
  Shopify calls against a leaky bucket, or four Gmail calls against a per-minute quota.
* A cost budget per source per plan. Shopify's calculated query cost is what the order cache
  already paces against (app/analytics/cache.py); a plan declares what it expects to spend
  and stops asking when it is spent.
* Cancellation: one `asyncio.TaskGroup`-shaped run, cancelled as a unit.
* Deterministic merge: results come back keyed by name, in plan order, whatever finished first.
* NO WRITES. A read whose tool has a WriteSpec or a BatchSpec is refused before the plan runs.
  Two writes must never be in flight together, and the way to guarantee that is to have no
  path from here to one.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from app.observability import timeline

log = logging.getLogger("crooks.reads")

# How many reads of one source may be in flight at once. Shopify's Admin API is a leaky
# bucket refilling at 50 points a second; Gmail's per-user quota is generous but its
# per-thread fetches are not free. Four and three are what the tablet's screens need.
SOURCE_LIMITS: dict[str, int] = {"shopify": 4, "gmail": 3, "mac": 8}
DEFAULT_LIMIT = 3

# What one plan may spend at a source, in that source's own units. Shopify counts calculated
# query cost; Gmail counts requests. Both are ceilings, not targets.
SOURCE_BUDGET: dict[str, float] = {"shopify": 900.0, "gmail": 25.0, "mac": 1000.0}
# What a read of a source costs when it does not report its own.
DEFAULT_COST: dict[str, float] = {"shopify": 60.0, "gmail": 1.0, "mac": 1.0}

# The whole plan. Past this the answer is late enough that a partial one is better.
PLAN_TIMEOUT_S = 12.0
READ_TIMEOUT_S = 8.0


class WriteInPlan(RuntimeError):
    """A plan named a write tool. Reads only; this is a structural guarantee, not a policy."""


@dataclass(slots=True)
class Read:
    """One node. `args` is either a dict or a callable taking the results so far — that is how
    a dependent read gets the id the read before it found, without the caller pre-flattening
    the graph."""

    name: str
    tool: str
    args: dict[str, Any] | Callable[[dict[str, Any]], dict[str, Any] | None] = field(default_factory=dict)
    source: str = "shopify"
    after: tuple[str, ...] = ()
    cost: float | None = None
    timeout_s: float = READ_TIMEOUT_S
    # A read the answer can do without. When it fails or is skipped, the plan says so and
    # carries on; a required read failing marks the plan partial.
    optional: bool = True


@dataclass(slots=True)
class ReadPlan:
    reads: list[Read]
    label: str = ""
    timeout_s: float = PLAN_TIMEOUT_S

    def names(self) -> list[str]:
        return [r.name for r in self.reads]


@dataclass(slots=True)
class ReadResult:
    values: dict[str, Any] = field(default_factory=dict)          # name -> the tool's payload
    calls: list[Any] = field(default_factory=list)                # ToolCall, in plan order
    ms: dict[str, float] = field(default_factory=dict)            # name -> milliseconds
    skipped: dict[str, str] = field(default_factory=dict)         # name -> why
    errors: dict[str, str] = field(default_factory=dict)
    critical_path_ms: float = 0.0
    serial_ms: float = 0.0                                        # what running them in turn would have taken
    groups: list[list[str]] = field(default_factory=list)         # what ran together
    spent: dict[str, float] = field(default_factory=dict)
    partial: bool = False

    @property
    def saved_ms(self) -> float:
        """Measured, not claimed: the sum of the read times minus the wall clock they took."""
        return max(0.0, self.serial_ms - self.critical_path_ms)

    def ok(self, name: str) -> bool:
        return name in self.values and self.values[name] is not None


def assert_reads_only(plan: ReadPlan) -> None:
    """Every tool in the plan is a read. Raised before anything runs."""
    from app.tools import registry

    for read in plan.reads:
        try:
            spec = registry.get(read.tool)
        except KeyError as exc:
            raise WriteInPlan(f"{read.tool!r} is not a registered tool") from exc
        if spec.write is not None or spec.batch is not None:
            raise WriteInPlan(
                f"{read.tool!r} is a write tool. The read scheduler runs reads only; a change "
                f"goes through the action engine, one at a time."
            )


def _layers(plan: ReadPlan) -> list[list[Read]]:
    """The plan as waves: everything in a wave is independent of everything else in it.
    A cycle, or a dependency on a name the plan does not contain, is dropped with a reason."""
    by_name = {r.name: r for r in plan.reads}
    done: set[str] = set()
    waves: list[list[Read]] = []
    remaining = list(plan.reads)
    while remaining:
        wave = [r for r in remaining if all(dep in done for dep in r.after if dep in by_name)]
        if not wave:
            break   # a cycle: the rest are reported as skipped by the runner
        waves.append(wave)
        done.update(r.name for r in wave)
        remaining = [r for r in remaining if r.name not in done]
    return waves


async def run_plan(plan: ReadPlan, *, session: Any, timeout_s: float | None = None, turn_id: str = "") -> ReadResult:
    """Run the graph. Never raises for a read that failed: a failure is a name in `errors`."""
    assert_reads_only(plan)
    from app.tools.dispatch import dispatch

    result = ReadResult()
    by_name = {r.name: r for r in plan.reads}
    started_all = time.perf_counter()
    limits = {source: asyncio.Semaphore(SOURCE_LIMITS.get(source, DEFAULT_LIMIT)) for source in {r.source for r in plan.reads}}
    budget = {source: SOURCE_BUDGET.get(source, 100.0) for source in limits}
    order = plan.names()
    calls_by_name: dict[str, Any] = {}

    done_count = 0
    total = len(plan.reads)

    def progress(read: Read) -> None:
        """What the Mac is doing, in the owner's words, while it does it (brief section 12).

        Counts and source names only — "2 of 3 checked", "reading the inbox". Never the
        model's reasoning, which the timeline does not carry and this cannot reach.
        """
        nonlocal done_count
        done_count += 1
        try:
            session.set_state(
                "CHECKING EMAIL" if read.source == "gmail" else "CHECKING SHOPIFY",
                f"{done_count} of {total} read" if total > 1 else read.tool,
            )
        except AttributeError:
            pass

    async def one(read: Read) -> None:
        args = read.args(dict(result.values)) if callable(read.args) else dict(read.args or {})
        if args is None:
            result.skipped[read.name] = "nothing to look up"
            return
        cost = float(read.cost if read.cost is not None else DEFAULT_COST.get(read.source, 1.0))
        if budget.get(read.source, 0.0) < cost:
            result.skipped[read.name] = f"the {read.source} budget for this answer is spent"
            result.partial = result.partial or not read.optional
            return
        budget[read.source] -= cost
        result.spent[read.source] = result.spent.get(read.source, 0.0) + cost
        own: list[Any] = []
        t0 = time.perf_counter()
        async with limits[read.source]:
            try:
                await dispatch(read.tool, args, session=session, timeout_s=read.timeout_s, calls=own)
            except Exception as exc:  # noqa: BLE001 — a failed read is a reported read
                result.errors[read.name] = str(exc)[:200]
        ms = (time.perf_counter() - t0) * 1000
        progress(read)
        result.ms[read.name] = round(ms, 1)
        result.serial_ms += ms
        if own:
            call = own[-1]
            calls_by_name[read.name] = call
            if call.ok:
                result.values[read.name] = call.result
            else:
                result.errors.setdefault(read.name, str(call.error or "the read did not come back")[:200])
        if read.name in result.errors and not read.optional:
            result.partial = True

    try:
        async with asyncio.timeout(plan.timeout_s if timeout_s is None else timeout_s):
            for wave in _layers(plan):
                runnable = [r for r in wave if all(d not in result.errors and d not in result.skipped for d in r.after if d in by_name)]
                for read in wave:
                    if read not in runnable:
                        result.skipped[read.name] = "what it needed did not come back"
                        result.partial = result.partial or not read.optional
                if not runnable:
                    continue
                result.groups.append([r.name for r in runnable])
                await asyncio.gather(*(one(r) for r in runnable))
    except TimeoutError:
        result.partial = True
        for read in plan.reads:
            if read.name not in result.values and read.name not in result.errors:
                result.skipped.setdefault(read.name, "the answer was already late")

    for name in by_name:
        if name not in result.values and name not in result.errors and name not in result.skipped:
            result.skipped[name] = "it depended on something that never ran"
    result.critical_path_ms = round((time.perf_counter() - started_all) * 1000, 1)
    result.serial_ms = round(result.serial_ms, 1)
    result.calls = [calls_by_name[name] for name in order if name in calls_by_name]
    result.partial = result.partial or bool(result.errors)

    if timeline.current().active is not None:
        timeline.emit(
            "read_plan", session_id=getattr(session, "session_id", None), turn_id=turn_id or getattr(session, "turn_id", "") or None,
            label=plan.label or None, groups=result.groups, fanout=max((len(g) for g in result.groups), default=0),
            critical_path_ms=result.critical_path_ms, serial_ms=result.serial_ms, saved_ms=round(result.saved_ms, 1),
            spent=result.spent, ms=result.ms, skipped=result.skipped or None, errors=list(result.errors) or None,
            partial=result.partial,
        )
    return result
