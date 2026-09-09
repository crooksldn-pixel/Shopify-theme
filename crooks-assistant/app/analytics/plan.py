"""The bounds on one turn's reading: how many analytic queries it may run, how much they may
cost together, how long they may take, and that the same query is not run twice. A model
that composes reads is welcome to; one that loops is stopped, and told why, before Shopify
notices."""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any

from app.analytics.query import TURN_COST

MAX_CALLS = 8
MAX_ELAPSED_S = 45.0


@dataclass(slots=True)
class TurnPlan:
    turn_id: str
    started: float = field(default_factory=time.monotonic)
    calls: int = 0
    cost: int = 0
    seen: dict[str, str] = field(default_factory=dict)      # args fingerprint -> rendered result
    steps: list[dict[str, Any]] = field(default_factory=list)


def fingerprint(name: str, args: dict[str, Any]) -> str:
    return hashlib.sha1(json.dumps({"tool": name, "args": args}, sort_keys=True, default=str).encode()).hexdigest()[:16]


def plan_for(session: Any) -> TurnPlan:
    """The plan for the session's current turn, started afresh when the turn changes."""
    turn_id = str(getattr(session, "turn_id", "") or "")
    plan = getattr(session, "plan", None)
    if not isinstance(plan, TurnPlan) or plan.turn_id != turn_id:
        plan = TurnPlan(turn_id=turn_id)
        try:
            session.plan = plan
        except AttributeError:
            pass
    return plan


def check(session: Any, name: str, args: dict[str, Any], *, cost: int) -> tuple[str | None, str | None]:
    """(refusal, cached) — a refusal when the turn's bounds are spent, the earlier answer when
    this exact query already ran this turn, else (None, None)."""
    plan = plan_for(session)
    key = fingerprint(name, args)
    if key in plan.seen:
        return None, plan.seen[key]
    if plan.calls >= MAX_CALLS:
        return f"REFUSED: this turn has already run {plan.calls} queries; answer from what they returned, or ask the owner to narrow the question.", None
    if plan.cost + cost > TURN_COST:
        return f"REFUSED: this turn's query budget is spent ({plan.cost} of {TURN_COST} points used; this query costs {cost}). Answer from what has been read, or narrow the period.", None
    if time.monotonic() - plan.started > MAX_ELAPSED_S:
        return "REFUSED: this turn has been reading for too long; answer from what has been read.", None
    return None, None


def record(session: Any, name: str, args: dict[str, Any], *, cost: int, rendered: str, ms: float, cached: bool, **fields: Any) -> None:
    plan = plan_for(session)
    plan.calls += 1
    plan.cost += cost
    plan.seen[fingerprint(name, args)] = rendered
    plan.steps.append({"tool": name, "cost": cost, "ms": round(ms, 1), "cached": cached, **fields})
