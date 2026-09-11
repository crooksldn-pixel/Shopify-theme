"""The bounds on one piece of work's reading: how many analytic queries it may run, how much
they may cost together, how long they may take, and that the same query is not run twice. A
model that composes reads is welcome to; one that loops is stopped, and told why, before
Shopify notices.

It used to be one bound per TURN, and that is D-4. The turn's budget was spent by whatever
read next — the owner's question, a hydration, or a guess the anticipation layer had made —
and the turn outlived itself, so the tap that came after a read-heavy turn inherited its
spend and a dock landing was refused `landing_unavailable`. The bounds now belong to a LANE
and a unit of work (app/reads/budget.py): a guess cannot spend the owner's, and a tap starts
fresh.

What is unchanged is the owner's own ceiling. FOREGROUND is eight calls, thirty points and
forty-five seconds, which is exactly what this module enforced before, so nothing the owner
asks for got narrower.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from app.analytics.query import TURN_COST
from app.reads import budget

# Kept as names because the report and the tests quote them; the numbers themselves live in
# app/reads/budget.py:BUDGETS, which is the one place that decides.
MAX_CALLS = budget.BUDGETS[budget.FOREGROUND].calls
MAX_ELAPSED_S = budget.BUDGETS[budget.FOREGROUND].elapsed_s

# What a unit of work's reading is, now that it belongs to a lane. Named here because this is
# where callers have always looked for it.
TurnPlan = budget.Spend

_MISSING = object()


def fingerprint(name: str, args: dict[str, Any]) -> str:
    """One query's identity, through the read layer's canonical form.

    That form drops what changes how a result is DRAWN rather than what is READ — a card's
    `title`, above all. `turn_26db2bafe507` and `turn_6089e7517986` each ran `commerce_query`
    twice for two cards over the same rows, and an exact-argument fingerprint could not see
    that they were one query (D-13). Answering the second from the first also leaves the
    working set the first one published alone, which is what a second identical query would
    have rebuilt.
    """
    from app.reads import dedupe

    return hashlib.sha1(
        json.dumps({"tool": name, "args": dedupe.canonical(args)}, sort_keys=True, default=str).encode()
    ).hexdigest()[:16]


def lane_and_key(session: Any) -> tuple[str, str]:
    """Which lane this read is in, and which unit of work its budget belongs to."""
    lane, key = budget.current_lane()
    return lane, key or budget.key_for(session, lane)


def plan_for(session: Any) -> budget.Spend:
    """This unit of work's reading, live.

    Also honours the reset the benches and the tests have always used — `session.plan = None`
    between rows — because a bound that a caller believes it has cleared and has not is a
    bound that fails a bench for the wrong reason.
    """
    ledger = budget.ledger_for(session)
    if getattr(session, "plan", _MISSING) is None:
        ledger.reset()
    lane, key = lane_and_key(session)
    spend = ledger.spend(lane, key)
    try:
        session.plan = spend
    except AttributeError:
        pass
    return spend


# There was a `restart(session)` here for a moment in Phase 4, to give a TAP its own scope —
# the plan was keyed on session.turn_id and a tap starts no turn, so a tap after a spoken
# question inherited that question's bounds AND its "the same query already ran" answers. The
# lanes above do that job properly: `plan_for` resolves the unit of work from the lane the
# caller entered, so a tap in the NAVIGATION lane with its own key is already a fresh scope,
# for the bounds and for the reuse both. Two mechanisms for one rule is one too many.


def check(session: Any, name: str, args: dict[str, Any], *, cost: int) -> tuple[str | None, str | None]:
    """(refusal, cached) — a refusal when this lane's bounds are spent, the earlier answer
    when this exact query already ran for this unit of work, else (None, None).

    A precondition or verification read never gets the earlier answer: `Ledger.reuse` refuses
    it by lane, which is the same rule app/reads/dedupe.py keeps for every other read.
    """
    plan_for(session)                       # honour the reset, and settle the lane
    lane, key = lane_and_key(session)
    ledger = budget.ledger_for(session)
    reused = ledger.reuse(lane, key, fingerprint(name, args))
    if reused is not None:
        return None, reused
    return (ledger.check(lane, key, cost=int(cost)) or None), None


def record(session: Any, name: str, args: dict[str, Any], *, cost: int, rendered: str, ms: float, cached: bool, **fields: Any) -> None:
    plan_for(session)
    lane, key = lane_and_key(session)
    budget.ledger_for(session).record(
        lane, key, cost=int(cost), fingerprint=fingerprint(name, args), rendered=rendered,
        step={"tool": name, "cost": cost, "ms": round(ms, 1), "cached": cached, "lane": lane, **fields},
    )


__all__ = ["MAX_CALLS", "MAX_ELAPSED_S", "TURN_COST", "TurnPlan", "check", "fingerprint",
           "lane_and_key", "plan_for", "record"]
