"""The summary questions, answered deterministically — D-4, §13, §14, §36.

    turn_be1b384ca420   "Has anyone bought today that has bought before, a returning customer?"
      12,895 ms, of which 12,116 ms was the model
      tools:   shopify_customer_history x 7, one per candidate customer
      rendered: seven full customer profile cards, 1,949 px of deck
      answer:   one. Correct.

Nothing about that turn needed a model. The question is a filter over rows the Mac already
holds, the answer is a count, and the surface is a count with one row each. So this file is

  ONE READ TOOL      `commerce_summary` — the cache view the question needed and nothing
                     else, with the aggregation done on the Mac (app/analytics/summarise.py).
  THREE RECIPES      returning customers, orders needing attention, a period's orders — each
                     one read, each one compact surface, no model call.
  THREE FAMILIES     the request shapes that route to them.

The read count is asserted, not hoped for: `MAX_READS` below is one, `read_primitives` names
the one tool, and tests/test_n_plus_one.py counts the dispatches.

What is NOT here: the full customer workspace. A tap on one of these rows posts `open.entity`
and the Mac reads that ONE record and draws workstream B's card. That is the whole point of a
summary surface — the drilldown happens for the one the owner asked about, not for all seven
before he has said which.

On the families: the shapes below are registered through `app.fastpath.intent.extend`, which
is the published way a family module adds its own (app/families/__init__.py) and touches no
shared table. `docs/phase5/SURFACES_HANDOFF.md` lists them for workstream C, which owns
app/fastpath/intent.py and the scoring they are matched by.
"""

from __future__ import annotations

import logging
import time
from datetime import timedelta
from typing import Any

from app.analytics import sets as working_sets
from app.analytics import summarise
from app.analytics.periods import Period, PeriodError, resolve
from app.capabilities.families import CapabilityFamily
from app.capabilities.families import register as register_family
from app.fastpath.intent import Family, extend, signal
from app.fastpath.library import _open_workflow, period_from
from app.fastpath.models import Ctx, FastAnswer
from app.fastpath.recipes import CACHE_ANALYTICS, Recipe, register
from app.reads.scheduler import Read, ReadPlan, ReadResult
from app.summaries import attention_rows, freshness_of, order_rows, returning_customers
from app.tools.context import current_session
from app.tools.gate import Tier
from app.tools.registry import ToolError, tool

log = logging.getLogger("crooks.families.summaries")

READ_TOOL = "commerce_summary"
READ_TIMEOUT_S = 6.0

# One read answers any of these. The bound is the point of the file: D-4 spent seven.
MAX_READS = 1

# The tasks, and what each one is called in the owner's words.
TASKS: dict[str, str] = {
    "returning_customers": "who bought in the period and had bought before it",
    "orders_attention": "the orders that need something doing",
    "order_list": "the period's orders, as rows",
}

# How far back a task looks BEYOND its own period, so that "had bought before" has something
# to be before. Ninety days is the cache's own warm window (app/analytics/cache.py
# WARM_DAYS), so this asks for what the Mac already keeps and adds no provider call in the
# ordinary case. A customer whose previous order is older than that is still counted as
# returning — Shopify's own lifetime count says so — and the row says the date is not held
# rather than inventing one.
LOOKBACK_DAYS: dict[str, int] = {"returning_customers": 90, "orders_attention": 90, "order_list": 0}

MAX_ROWS = 25


def _period_of(period: Any, now, zone):
    try:
        return resolve(period or "today", now=now)
    except PeriodError as exc:
        raise ToolError(f"Period not understood: {exc}") from exc


@tool(
    name=READ_TOOL,
    description=(
        "Answer a SUMMARY question about a period in one call, from the orders the Mac holds: "
        "who bought in the period having bought before (returning customers), which orders need "
        "attention, or the period's orders as rows. Use this instead of listing a period and then "
        "reading each customer's or each order's record: the lifetime order count and lifetime "
        "spend are already on every order row here, so 'has this buyer bought before' costs no "
        "further read."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "task": {"type": "string", "description": "returning_customers, orders_attention or order_list."},
            "period": {"description": "today (default), yesterday, this_week, last_week, this_month, last_month, last_7_days, last_30_days."},
            "limit": {"type": "integer", "description": f"rows on the surface, 1-{MAX_ROWS}, default 12. The COUNT is always the whole count."},
        },
        "required": ["task"],
    },
    tier=Tier.GREEN,
)
async def commerce_summary(task: str, period: Any = None, limit: int = 12) -> dict:
    """One cache view, one pass of pure aggregation, no per-entity read.

    The cache is the same one `commerce_query` uses, so a turn that has already listed the
    period is answered from a warm view and this costs no Shopify call at all.
    """
    from app.tools import analytics_tools

    task = str(task or "").strip()
    if task not in TASKS:
        raise ToolError(f"task is one of {', '.join(sorted(TASKS))}.")
    limit = max(1, min(int(limit or 12), MAX_ROWS))
    started = time.perf_counter()
    now, zone = await analytics_tools._now_and_zone()
    window = _period_of(period, now, zone)
    start, end = summarise.window_for(window)
    lookback = LOOKBACK_DAYS.get(task, 0)
    # ONE view, wide enough for the comparison the task needs. A wider window is not a
    # second read: the cache keeps ninety days warm (app/analytics/cache.py WARM_DAYS) and
    # serves this from memory.
    read_from = window.start - timedelta(days=lookback) if lookback else window.start
    view = await analytics_tools.cache().view(
        Period(read_from, window.end, window.label, window.kind), timeout_s=READ_TIMEOUT_S,
    )
    rows = view.rows
    if task == "returning_customers":
        found = summarise.returning_customers(rows, start=start, end=end, zone=zone, limit=limit)
        kind, ids = "customers", [r["customer_id"] for r in found["rows"]]
    elif task == "orders_attention":
        found = summarise.orders_needing_attention(
            summarise.in_window(rows, start=start, end=end) if period else rows,
            now=now.timestamp(), zone=zone, limit=limit,
        )
        kind, ids = "orders", [r["order_id"] for r in found["rows"]]
    else:
        found = summarise.order_rows(rows, start=start, end=end, now=now.timestamp(), zone=zone, limit=limit)
        kind, ids = "orders", [r["order_id"] for r in found["rows"]]

    found.update({
        "task": task,
        "period": {"label": window.label, "start": window.start.isoformat(), "end": window.end.isoformat()},
        # Whether the OWNER named a period. "Which orders need attention" names none and is
        # answered over everything the Mac holds, so its surface must not be titled "today"
        # merely because `today` is this tool's default window.
        "period_asked": bool(period),
        "coverage": {"complete": view.complete, "covered_days": view.covered_days,
                     "read_age_s": (round(view.age_s, 1) if view.age_s is not None else None)},
        "complete": bool(view.complete),
        "source": f"Shopify orders the Mac holds, read {'just now' if not view.age_s else f'{round(view.age_s)} s ago'}",
        "reads": 1,
        "_ms": round((time.perf_counter() - started) * 1000 + view.served_ms, 1),
    })
    if view.note:
        found["note"] = (str(found.get("note") or "") + " " + view.note).strip()
    # The rows as a set, so "next", "the third one" and a tap on the third row are one cursor
    # on one list. The Mac owns membership; the tablet only ever names an id back.
    session = current_session()
    if session is not None and ids:
        made = working_sets.create(
            session, kind=kind, members=[str(i) for i in ids if i],
            label=f"{TASKS[task]}, {window.label}"[:80],
            provenance={"tool": READ_TOOL, "step": "query", "query": {"task": task, "period": window.label}},
            sample=[], totals={}, labels=_labels_for(task, found),
        )
        found["set_id"] = made.set_id
    return found


def _labels_for(task: str, found: dict[str, Any]) -> dict[str, str]:
    """How a person names each member, for the batch card and the cursor's words."""
    if task == "returning_customers":
        return {str(r["customer_id"]): str(r.get("name") or r.get("email") or "")
                for r in found["rows"] if r.get("customer_id")}
    return {str(r["order_id"]): str(r.get("order_number") or "")
            for r in found["rows"] if r.get("order_id")}


# --------------------------------------------------------------------------- the recipes


def _plan_for(task: str):
    def plan(ctx: Ctx) -> ReadPlan | None:
        period = period_from(ctx.intent.signals.words) or ("today" if task != "orders_attention" else "")
        args: dict[str, Any] = {"task": task, "limit": 12}
        if period:
            args["period"] = period
        # ONE read. `cost` is the cache view's, which is the same view a listing takes.
        return ReadPlan([Read("summary", READ_TOOL, args, source="shopify", cost=120.0)],
                        label=f"summary_{task}")

    return plan


def _body(result: ReadResult) -> dict[str, Any] | None:
    body = result.values.get("summary")
    return body if isinstance(body, dict) else None


def _period_words(body: dict[str, Any], fallback: str) -> str:
    label = str((body.get("period") or {}).get("label") or "") if isinstance(body.get("period"), dict) else ""
    return label or fallback


def _returning_render(ctx: Ctx, result: ReadResult) -> FastAnswer:
    body = _body(result)
    if body is None:
        return FastAnswer(answer="", defer="the returning-customer summary did not come back")
    period = _period_words(body, "today")
    surface = returning_customers(body, session=ctx.session, period=period,
                                  freshness=freshness_of(body.get("coverage")))
    _open_cursor(ctx, body, kind="customers")
    return FastAnswer(
        answer=surface.spoken_summary, surfaces=[surface], calls=list(result.calls), drawn=[],
        partial=result.partial,
        trace={"task": "returning_customers", "rows": len(body.get("rows") or []),
               "count": int(body.get("count") or 0), "reads": len(result.calls)},
    )


def _attention_render(ctx: Ctx, result: ReadResult) -> FastAnswer:
    body = _body(result)
    if body is None:
        return FastAnswer(answer="", defer="the attention summary did not come back")
    surface = attention_rows(body, session=ctx.session,
                             period=_period_words(body, "") if body.get("period_asked") else "",
                             freshness=freshness_of(body.get("coverage")))
    _open_cursor(ctx, body, kind="orders")
    return FastAnswer(
        answer=surface.spoken_summary, surfaces=[surface], calls=list(result.calls), drawn=[],
        partial=result.partial,
        trace={"task": "orders_attention", "rows": len(body.get("rows") or []),
               "count": int(body.get("count") or 0), "red": int(body.get("red") or 0),
               "reads": len(result.calls)},
    )


def _order_list_render(ctx: Ctx, result: ReadResult) -> FastAnswer:
    body = _body(result)
    if body is None:
        return FastAnswer(answer="", defer="the order summary did not come back")
    period = _period_words(body, "today")
    surface = order_rows(body, session=ctx.session, period=period,
                         set_id=str(body.get("set_id") or ""),
                         freshness=freshness_of(body.get("coverage")))
    _open_cursor(ctx, body, kind="orders")
    return FastAnswer(
        answer=surface.spoken_summary, surfaces=[surface], calls=list(result.calls), drawn=[],
        partial=result.partial,
        trace={"task": "order_list", "rows": len(body.get("rows") or []),
               "count": int(body.get("count") or 0), "reads": len(result.calls)},
    )


def _open_cursor(ctx: Ctx, body: dict[str, Any], *, kind: str) -> None:
    """Put the summary's set under the branch's cursor, so "next" walks these rows.

    The same helper the listing recipes use (app/fastpath/library.py `_open_workflow`), so a
    summary's cursor, a listing's cursor and a landing's cursor are one mechanism. Guarded:
    a branch stand-in with no trail is most of the suite, and a summary that cannot open a
    cursor is still the answer.
    """
    set_id = str(body.get("set_id") or "")
    if not set_id:
        return
    try:
        _open_workflow(ctx, body, kind=kind, operation="review", set_id=set_id)
    except Exception as exc:  # noqa: BLE001 — a cursor is a convenience, never the answer
        log.debug("could not open a cursor on the summary: %s: %s", type(exc).__name__, exc)


register(Recipe(
    recipe_id="returning_customers", intent_family="returning_customers",
    read_primitives=(READ_TOOL,), parallel_nodes=(("summary",),), ui="summary_list",
    cache_policy=CACHE_ANALYTICS, min_confidence=0.7, target_ms=900,
    plan=_plan_for("returning_customers"), render=_returning_render,
))
register(Recipe(
    recipe_id="orders_attention", intent_family="orders_attention",
    read_primitives=(READ_TOOL,), parallel_nodes=(("summary",),), ui="summary_list",
    cache_policy=CACHE_ANALYTICS, min_confidence=0.7, target_ms=900,
    plan=_plan_for("orders_attention"), render=_attention_render,
))
register(Recipe(
    recipe_id="order_list_summary", intent_family="order_list_summary",
    read_primitives=(READ_TOOL,), parallel_nodes=(("summary",),), ui="summary_list",
    cache_policy=CACHE_ANALYTICS, min_confidence=0.7, target_ms=900,
    plan=_plan_for("order_list"), render=_order_list_render,
))


# -------------------------------------------------------------------------- the shapes

# This family's own words, through the `signal()` seam — a family brings its own word rather
# than editing the shared `Signals` dataclass, which is the table every family would otherwise
# be editing at once. Workstream C owns app/fastpath/intent.py and the scoring; these are what
# this file needs from it, in one place, listed for C in docs/phase5/SURFACES_HANDOFF.md.

# A customer who has bought more than once. "again" is deliberately NOT here: "show it again"
# is `order_reopen`, and a word that means two families means neither.
_RETURNING = frozenset({"returning", "repeat", "repeats", "returned", "regular", "regulars", "loyal"})
# "bought BEFORE", "ordered PREVIOUSLY" — the same question without the word "returning".
_BEFORE = frozenset({"before", "previously", "prior", "already", "past"})
# "needs attention", "needs chasing", "something wrong", "anything stuck".
_ATTENTION = frozenset({"attention", "chase", "chasing", "chased", "problem", "problems",
                        "wrong", "stuck", "urgent", "outstanding"})
# An order ARRIVING, with no noun for it: "what came in yesterday".
_ARRIVED = frozenset({"came", "come", "arrived", "arrive", "landed"})

_SAYS_RETURNING = signal("returning", lambda s: bool(set(s.words) & _RETURNING))
_SAYS_BEFORE = signal("before", lambda s: bool(set(s.words) & _BEFORE))
_SAYS_ATTENTION = signal("attention", lambda s: bool(set(s.words) & _ATTENTION))
# "came IN", "come THROUGH": the preposition is required, so a bare "in" is not an arrival.
_SAYS_ARRIVED = signal(
    "arrived",
    lambda s: bool(set(s.words) & _ARRIVED) and bool(set(s.words) & {"in", "through", "over"}),
)

extend([
    # "Has anyone bought today that has bought before, a returning customer?" — D-4's own
    # sentence, and the shorter ways of saying it. `returning` OR (`bought` AND `before`):
    # the word "returning" is enough on its own when a period is named, and "bought before"
    # is the same question without it.
    Family("returning_customers", needs=("returning", "period"),
           boosts=("customer", "bought", "question", "before"),
           blocks=("mutation", "order_number", "email", "stock", "running_out", "ranking",
                   "known_name", "possessive_name", "direction_next", "direction_previous"),
           base=0.72, floor=0.7, max_words=16),
    Family("returning_customers_before", needs=("bought", "before"),
           boosts=("customer", "period", "question", "returning"),
           blocks=("mutation", "order_number", "email", "stock", "running_out", "ranking",
                   "known_name", "possessive_name", "has_entity", "deixis"),
           base=0.72, floor=0.7, max_words=16),
    # "Which orders need attention?" — and NOT "show me today's orders", which is a listing.
    # `order_list_period` blocks nothing about attention, so without this family "which
    # orders need my attention today" scored as a plain period listing and answered with
    # every order of the day: the right shape of card for a different question.
    Family("orders_attention", needs=("attention",),
           boosts=("order", "question", "waiting", "delayed", "period"),
           blocks=("mutation", "order_number", "email", "metric", "ranking", "stock",
                   "running_out", "known_name", "possessive_name"),
           base=0.74, floor=0.7, max_words=14),
    # "What came in yesterday?" — a listing that names no noun. `order_list_period` needs the
    # word "order"; this takes the shapes that name the period and the arrival instead.
    Family("order_list_summary", needs=("arrived", "period"),
           boosts=("question", "listing", "order"),
           blocks=("mutation", "order_number", "metric", "ranking", "running_out", "stock",
                   "email", "delayed", "status", "address", "attention", "returning",
                   "customer"),
           base=0.74, floor=0.7, max_words=12),
])

register_family(CapabilityFamily(
    key="summary_surfaces",
    label="Summary answers",
    area="analytics",
    what=(
        "Answer a summary question about a period in one read and one compact surface: who "
        "bought having bought before, which orders need attention, a period's orders as rows"
    ),
    tools=(READ_TOOL,),
    scopes=("read_orders", "read_customers"),
    state="READY",
))
