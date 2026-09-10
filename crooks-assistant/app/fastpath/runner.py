"""Running a recipe.

The whole of the fast lane's critical path: resolve what the recipe needs, run its reads
through the parallel scheduler, render one sentence and the cards, and put what was read into
memory so the next question is faster still.

If anything is not certain — a required entity that does not resolve, a read that came back
empty, a recipe that says it cannot honestly answer — the runner defers and /turn hands the
question to Claude exactly as before. Deferring is cheap; answering the wrong question is not.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from app.fastpath import recipes as recipe_mod
from app.fastpath.models import Ctx, FastAnswer
from app.observability import timeline
from app.reads.scheduler import ReadResult, run_plan

log = logging.getLogger("crooks.fastpath")

# A fast path that has not answered by here has stopped being fast. The turn goes to Claude
# with whatever the reads found, rather than waiting longer for a shortcut.
BUDGET_MS = 5_000


async def run(recipe: recipe_mod.Recipe, ctx: Ctx) -> FastAnswer:
    """One recipe, end to end. Never raises: a failure defers."""
    recipe_mod.assert_read_only({recipe.recipe_id: recipe})
    started = time.perf_counter()
    answer: FastAnswer
    try:
        missing = _unresolved(recipe, ctx)
        if missing:
            answer = FastAnswer(answer="", defer=f"{missing} did not resolve")
        else:
            _advance(recipe, ctx)
            plan = recipe.plan(ctx) if recipe.plan else None
            result = ReadResult()
            if plan is not None:
                result = await run_plan(plan, session=ctx.session, timeout_s=min(plan.timeout_s, BUDGET_MS / 1000), turn_id=getattr(ctx.session, "turn_id", ""))
            answer = recipe.render(ctx, result) if recipe.render else FastAnswer(answer="", defer="no renderer")
            if not answer.deferred:
                _keep(recipe, ctx, result)
                answer.trace.setdefault("reads", list(result.values))
                answer.trace.setdefault("critical_path_ms", result.critical_path_ms)
                answer.trace.setdefault("serial_ms", result.serial_ms)
                answer.trace.setdefault("saved_ms", round(result.saved_ms, 1))
    except Exception as exc:  # noqa: BLE001 — the fast lane never takes a turn down
        log.warning("recipe %s failed: %s", recipe.recipe_id, exc)
        answer = FastAnswer(answer="", defer=f"{type(exc).__name__}")
    ms = (time.perf_counter() - started) * 1000
    if not answer.deferred and not str(answer.answer or "").strip():
        answer = FastAnswer(answer="", defer="the recipe produced no answer")
    recipe.stats.record(ms, ok=not answer.deferred, deferred=answer.deferred)
    answer.trace["ms"] = round(ms, 1)
    answer.trace["recipe_id"] = recipe.recipe_id
    if timeline.current().active is not None:
        timeline.emit(
            "fast_path", session_id=getattr(ctx.session, "session_id", None), turn_id=getattr(ctx.session, "turn_id", "") or None,
            recipe_id=recipe.recipe_id, intent=ctx.intent.family, confidence=ctx.intent.confidence,
            branch_id=getattr(ctx.branch, "branch_id", None), ms=round(ms, 1), target_ms=recipe.target_ms,
            hit=not answer.deferred, defer=answer.defer or None, partial=answer.partial or None,
            trace={k: v for k, v in answer.trace.items() if k not in ("recipe_id",)},
        )
    return answer


def _unresolved(recipe: recipe_mod.Recipe, ctx: Ctx) -> str:
    """The first required entity that does not resolve, by name. Empty when all of them do."""
    for needed in recipe.required_entities:
        if needed == "workflow":
            if ctx.branch.workflow is None and not _adopt_latest_set(ctx):
                return "the set being worked through"
        elif needed == "order":
            if not (ctx.order_number or ctx.entity("order")):
                return "an order"
        elif needed == "customer":
            if not (ctx.intent.slots.get("name") or ctx.entity("customer")):
                return "a customer"
    return ""


def _adopt_latest_set(ctx: Ctx) -> bool:
    """A listing was shown and the owner said "next": the newest working set becomes the
    thing being worked through, positioned before its first member so that the cursor move
    lands on it. Nothing is read here — this is only where the conversation is."""
    from app.analytics import sets as working_sets
    from app.session.branch import Workflow

    ws = working_sets.latest(ctx.session)
    if ws is None or not ws.members:
        return False
    ctx.branch.set_id = ws.set_id
    # Positioned BEFORE the first member, so the first "Next" lands on it. `_open_workflow`
    # in the recipe library does the same: a set opened by a listing and a set adopted by a
    # "Next" must count from the same place, or the same word means two different things.
    ctx.branch.workflow = Workflow(
        workflow_id=f"wf_{int(time.time() * 1000) % 10**9:09d}", set_id=ws.set_id, kind=ws.kind,
        operation="review", cursor=-1, total=len(ws.members),
    )
    return True


def _advance(recipe: recipe_mod.Recipe, ctx: Ctx) -> None:
    """The cursor move, before the read.

    The arithmetic itself is `app/commands.py:move_cursor`, which is also what a tap on Next
    reaches. It used to live here, keyed on a recipe id, where touch could not get at it — so
    the word "next" and the button called Next were two implementations of one idea and were
    free to disagree about where a list ends.
    """
    from app.commands import NAV_MOVES, move_cursor, move_nav

    # A navigation recipe moves the trail here, before its plan runs, so the plan knows which
    # record it will land on and can read it when memory does not hold it. Without this the
    # move happened during the render, by which time it was too late to read anything and a
    # dropped cache entry meant announcing a move and drawing nothing.
    direction = NAV_MOVES.get(f"navigation.{recipe.recipe_id.removeprefix('navigation_')}")
    if direction is not None:
        ctx.moved = move_nav(ctx.branch, direction)
        return
    if ctx.branch.workflow is None:
        return
    # The result is kept, not discarded: it says whether the cursor actually moved. Thrown
    # away, the ends of a list stopped existing on this path — the plan re-read the clamped
    # last member and the render announced it again as though "next" had done something.
    if recipe.recipe_id == "working_set_next":
        ctx.moved = move_cursor(ctx.session, ctx.branch, forward=True)
    elif recipe.recipe_id == "working_set_previous":
        ctx.moved = move_cursor(ctx.session, ctx.branch, forward=False)


def _keep(recipe: recipe_mod.Recipe, ctx: Ctx, result: ReadResult) -> None:
    """What was read, into the tier its recipe says. An entity read goes under its own id, so
    the next question about the same order does not touch Shopify."""
    from app.memory import ANALYTICS, EMAIL, ENTITY, HOT
    from app.memory import current as memory

    if recipe.cache_policy == recipe_mod.CACHE_NONE:
        return
    tier = {recipe_mod.CACHE_HOT: HOT, recipe_mod.CACHE_ENTITY: ENTITY,
            recipe_mod.CACHE_ANALYTICS: ANALYTICS, recipe_mod.CACHE_EMAIL: EMAIL}.get(recipe.cache_policy)
    if tier is None:
        return
    store = memory()
    for name, value in result.values.items():
        if not isinstance(value, dict):
            continue
        key = _key_for(tier, name, value, ctx)
        if not key:
            continue
        store.put(tier, key, value, source=("gmail" if name in ("mail", "inbox") else "shopify"),
                  query=recipe.recipe_id, provenance={"recipe": recipe.recipe_id, "read": name, "ref": _ref_of(value)})


def _ref_of(value: dict[str, Any]) -> str:
    for key in ("order_id", "customer_id", "thread_id", "set_id"):
        if value.get(key):
            return str(value[key])
    return ""


def _key_for(tier: str, name: str, value: dict[str, Any], ctx: Ctx) -> str:
    from app.memory import ANALYTICS, ENTITY

    if tier == ENTITY:
        for key, kind in (("order_id", "order"), ("customer_id", "customer"), ("thread_id", "email_thread")):
            if value.get(key):
                return f"{kind}:{value[key]}"
        return ""
    if tier == ANALYTICS:
        from app.memory.store import fingerprint

        return fingerprint(name, value.get("query") or {})
    return f"{ctx.session.session_id}:{name}"
