"""Read budgets, with strict priority, and the provider throttles underneath them.

D-4 in docs/phase4/LIVE_SESSION_FORENSICS.md is one sentence: *anticipation, added to make
the product feel faster, made it refuse the owner's own work.* Three `commerce_aggregate`
calls in `turn_6089e7517986` came back

    REFUSED: this turn has been reading for too long; answer from what has been read.

and two turns earlier a dock landing was refused outright. There was ONE budget — eight
calls, thirty points, forty-five seconds — and it was spent by whatever read next, whether
the owner had asked for it or the anticipation layer had guessed at it. It was also keyed on
a turn, and a turn outlives itself: the tap that came after a read-heavy turn inherited its
spend.

So: five budgets, one per LANE, in the priority order the brief names.

    1  FOREGROUND     the read the owner is waiting on
    2  NAVIGATION     hydrating what a tap or a move landed on
    3  PRECONDITION   a mutation's precondition or its proof
    4  BACKGROUND     a job this branch asked for and is not waiting on
    5  SPECULATION    anticipation, reading before it was asked

Three properties, each of which is a test in tests/test_read_budget.py:

* **A lane spends only its own budget.** Speculation at its cap cannot refuse the owner.
* **A budget belongs to a unit of work, not to a clock.** The key is the turn id, the
  command, the proposal — so a later tap starts fresh however much the last turn read.
* **The lower lanes can never take a source's last slot.** `Throttle` caps BACKGROUND and
  SPECULATION below the source's concurrency, so an owner read always finds a slot, and
  `yield_to` stands the lower lanes down the moment owner work starts.

What this module does NOT do is decide whether something is a read. That is
`app/reads/scheduler.py::assert_reads_only` and `app/tools/gate.py`, and no lane here
widens either: a write is refused in every lane, which tests/test_read_budget.py asserts
lane by lane.
"""

from __future__ import annotations

import contextvars
import logging
import math
import threading
import time
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

log = logging.getLogger("crooks.reads")

FOREGROUND = "foreground"
NAVIGATION = "navigation"
PRECONDITION = "precondition"
BACKGROUND = "background"
SPECULATION = "speculation"

# In the order of the brief. Index plus one is the priority, and `PRIORITY` is derived from
# this tuple rather than written twice: two tables that must agree eventually do not.
LANES: tuple[str, ...] = (FOREGROUND, NAVIGATION, PRECONDITION, BACKGROUND, SPECULATION)
PRIORITY: dict[str, int] = {lane: n + 1 for n, lane in enumerate(LANES)}
# The lanes the owner is, or soon will be, waiting on. Starting work in one of these stands
# everything below it down.
OWNER_LANES: frozenset[str] = frozenset({FOREGROUND, NAVIGATION, PRECONDITION})
# The lanes that yield. Nothing is waiting on them, so nothing is lost by stopping them.
YIELDING_LANES: tuple[str, ...] = (BACKGROUND, SPECULATION)


def outranks(lane: str, other: str) -> bool:
    """Whether `lane` comes first. An unknown lane is the lowest there is."""
    return PRIORITY.get(lane, 99) < PRIORITY.get(other, 99)


@dataclass(frozen=True, slots=True)
class Budget:
    """What one unit of work in one lane may spend.

    The foreground numbers are the ones the analytics layer already had (eight calls, thirty
    points, forty-five seconds — app/analytics/plan.py, app/analytics/query.py:TURN_COST), so
    the owner's own budget is not narrowed by this change. Every other lane is a fraction of
    it, and the fractions descend with the priority: a guess gets a quarter of what the owner
    gets, which is what makes it impossible for a guess to spend his.
    """

    calls: int
    cost: int
    elapsed_s: float


BUDGETS: dict[str, Budget] = {
    FOREGROUND: Budget(calls=8, cost=30, elapsed_s=45.0),
    NAVIGATION: Budget(calls=6, cost=24, elapsed_s=20.0),
    # Small and short on purpose: a precondition is one entity read and its proof, and a
    # mutation that needs six reads to know what it is about is a bug, not a budget.
    PRECONDITION: Budget(calls=4, cost=16, elapsed_s=15.0),
    BACKGROUND: Budget(calls=4, cost=12, elapsed_s=30.0),
    SPECULATION: Budget(calls=3, cost=8, elapsed_s=12.0),
}

# How many spends are kept per session. A diagnostic, not a log: the oldest go first.
MAX_SPENDS = 64


@dataclass
class Spend:
    """One unit of work's reading, in one lane."""

    lane: str
    key: str
    started: float
    calls: int = 0
    cost: int = 0
    refusals: int = 0
    # The rendered result of each query this unit has already run, by fingerprint — the
    # "never the same query twice" half of the old TurnPlan, now per lane so a guess and the
    # owner do not share an answer they may need at different freshnesses.
    seen: dict[str, str] = field(default_factory=dict)
    steps: list[dict[str, Any]] = field(default_factory=list)

    def public(self) -> dict[str, Any]:
        return {"lane": self.lane, "key": self.key, "calls": self.calls, "cost": self.cost,
                "refusals": self.refusals, "steps": len(self.steps)}


class Ledger:
    """Every unit of work's spend, per lane, for one conversation."""

    def __init__(self, *, clock=time.monotonic) -> None:
        self.clock = clock
        self._spends: dict[tuple[str, str], Spend] = {}
        self._lock = threading.Lock()
        self.refusals = 0

    # ------------------------------------------------------------------ reading

    def spend(self, lane: str, key: str) -> Spend:
        lane = lane if lane in PRIORITY else FOREGROUND
        with self._lock:
            found = self._spends.get((lane, key))
            if found is None:
                found = Spend(lane=lane, key=str(key), started=self.clock())
                self._spends[(lane, key)] = found
                self._prune_locked()
            return found

    def spent(self, lane: str, key: str) -> int:
        with self._lock:
            found = self._spends.get((lane, str(key)))
            return found.cost if found is not None else 0

    def calls(self, lane: str, key: str) -> int:
        with self._lock:
            found = self._spends.get((lane, str(key)))
            return found.calls if found is not None else 0

    # ------------------------------------------------------------------ deciding

    def check(self, lane: str, key: str, *, cost: int = 0) -> str:
        """Why this read must not run, in the owner's words, or empty.

        Never raises and never blocks: a refusal is a sentence the model can act on, and the
        caller decides whether that is an answer from what it already has or a lane change.
        """
        lane = lane if lane in PRIORITY else FOREGROUND
        budget = BUDGETS[lane]
        spend = self.spend(lane, key)
        if spend.calls >= budget.calls:
            return self._refuse(
                spend,
                f"REFUSED: this {_words(lane)} has already run {spend.calls} queries; answer from "
                "what they returned, or ask the owner to narrow the question.",
            )
        if spend.cost + int(cost) > budget.cost:
            return self._refuse(
                spend,
                f"REFUSED: this {_words(lane)}'s query budget is spent ({spend.cost} of "
                f"{budget.cost} points used; this query costs {int(cost)}). Answer from what has "
                "been read, or narrow the period.",
            )
        if self.clock() - spend.started > budget.elapsed_s:
            return self._refuse(
                spend,
                f"REFUSED: this {_words(lane)} has been reading for too long; answer from what "
                "has been read.",
            )
        return ""

    def _refuse(self, spend: Spend, words: str) -> str:
        spend.refusals += 1
        self.refusals += 1
        return words

    def record(self, lane: str, key: str, *, cost: int = 0, fingerprint: str = "",
               rendered: str = "", step: dict[str, Any] | None = None) -> Spend:
        spend = self.spend(lane, key)
        with self._lock:
            spend.calls += 1
            spend.cost += int(cost)
            if fingerprint:
                spend.seen[fingerprint] = rendered
            if step is not None:
                spend.steps.append(step)
        return spend

    def reuse(self, lane: str, key: str, fingerprint: str) -> str | None:
        """What this unit of work already got for this exact query, if anything.

        Not consulted for a precondition: `must_be_fresh` below is the one rule this whole
        file is subordinate to.
        """
        if must_be_fresh(lane) or not fingerprint:
            return None
        return self.spend(lane, key).seen.get(fingerprint)

    # ------------------------------------------------------------------ housekeeping

    def reset(self, lane: str = "", key: str = "") -> int:
        with self._lock:
            doomed = [
                pair for pair in self._spends
                if (not lane or pair[0] == lane) and (not key or pair[1] == key)
            ]
            for pair in doomed:
                del self._spends[pair]
        return len(doomed)

    def _prune_locked(self) -> None:
        if len(self._spends) <= MAX_SPENDS:
            return
        for pair in sorted(self._spends, key=lambda p: self._spends[p].started)[: len(self._spends) - MAX_SPENDS]:
            del self._spends[pair]

    def counts(self) -> dict[str, Any]:
        with self._lock:
            spends = [s.public() for s in self._spends.values()]
        by_lane: dict[str, dict[str, int]] = {}
        for row in spends:
            seen = by_lane.setdefault(row["lane"], {"units": 0, "calls": 0, "cost": 0, "refusals": 0})
            seen["units"] += 1
            seen["calls"] += row["calls"]
            seen["cost"] += row["cost"]
            seen["refusals"] += row["refusals"]
        return {"refusals": self.refusals, "lanes": by_lane}


def must_be_fresh(lane: str) -> bool:
    """A precondition or a verification read is never served from anything held. The action
    engine re-reads the source for its own reasons (app/actions/engine.py); this is the same
    rule stated where the saving is decided, so a future caller cannot opt into the saving by
    accident."""
    return lane == PRECONDITION


def _words(lane: str) -> str:
    return {FOREGROUND: "turn", NAVIGATION: "screen", PRECONDITION: "change",
            BACKGROUND: "background job", SPECULATION: "guess"}.get(lane, "turn")


# ------------------------------------------------------------------ where the lane lives

# The lane the code running right now is in, and which unit of work it belongs to. A
# contextvar rather than an argument because everything between the decision and the tool —
# the read scheduler, a recipe's plan, `dispatch` — would otherwise have to carry it, and a
# parameter that must be threaded through nine call sites is a parameter that will be
# forgotten at one of them. `asyncio.Task` copies the context at creation, so a prefetch task
# started inside a speculative lease stays speculative wherever it lands.
_LANE: contextvars.ContextVar[tuple[str, str]] = contextvars.ContextVar("crooks_read_lane", default=("", ""))


def current_lane() -> tuple[str, str]:
    """The lane in force, defaulted. Nobody having said is the owner's foreground read: that
    is what every caller meant before lanes existed, and a read that escaped a budget by not
    naming one would not be bounded at all."""
    lane, key = _LANE.get()
    return (lane or FOREGROUND), key


def ambient_lane() -> tuple[str, str]:
    """What a caller DELIBERATELY entered, ("", "") when nobody has. The difference from
    `current_lane` matters at exactly one place: a read plan with no lane of its own takes
    the lane it is running inside, and must be able to tell "inside nothing" from "inside the
    foreground"."""
    return _LANE.get()


def lane_name() -> str:
    return current_lane()[0]


@contextmanager
def using(lane: str, key: str = "", *, scope: str = "", branch_id: str = "", yielding: bool = True):
    """Run this block in `lane`, on behalf of the unit of work `key`.

    Entering an owner lane stands the lower lanes down first (`yielding=False` for a caller
    that has already done it, so one turn does not cancel its own speculation twice).
    """
    lane = lane if lane in PRIORITY else FOREGROUND
    if yielding and lane in OWNER_LANES:
        yield_to(lane, scope=scope, branch_id=branch_id)
    token = _LANE.set((lane, str(key)))
    try:
        yield lane
    finally:
        _LANE.reset(token)


# ------------------------------------------------------------------ standing down

@dataclass(frozen=True, slots=True)
class Standdown:
    """One request to stand down: which conversation, which lane, and which half of a split
    workspace — a question asked of one half must not throw away what was being read for the
    other, so the branch travels with the request rather than being guessed at."""

    scope: str
    lane: str
    branch_id: str = ""


# Called once per lane that must stand down, and returns how many pieces of work it stopped.
# Registered by the anticipation layer and by anything else that holds work nobody is waiting
# on; kept as callbacks so this module imports none of them and a process without them does
# nothing here.
_YIELDERS: dict[int, Callable[[Standdown], int]] = {}
_NEXT_TOKEN = [1]


def on_yield(fn: Callable[[Standdown], int]) -> int:
    token = _NEXT_TOKEN[0]
    _NEXT_TOKEN[0] += 1
    _YIELDERS[token] = fn
    return token


def off_yield(token: int) -> None:
    _YIELDERS.pop(token, None)


def yielders() -> int:
    return len(_YIELDERS)


def yield_to(lane: str, *, scope: str = "", branch_id: str = "") -> int:
    """Everything below `lane` stands down, now. Returns how many pieces of work stopped.

    Immediate and unconditional: the brief's word is "yields immediately", and a background
    read that gets to finish its request first is a background read the owner waited behind.
    """
    stopped = 0
    for lower in YIELDING_LANES:
        if not outranks(lane, lower):
            continue
        for fn in list(_YIELDERS.values()):
            try:
                stopped += int(fn(Standdown(scope=scope, lane=lower, branch_id=branch_id)) or 0)
            except Exception as exc:  # noqa: BLE001 — standing down never costs the owner a turn
                log.debug("a yielder failed: %s: %s", type(exc).__name__, exc)
    return stopped


# ------------------------------------------------------------------ the provider throttles

# How much of each source there is. Shopify's Admin API is a leaky bucket refilling at 50
# points a second; Gmail's per-user quota is generous but its per-thread fetches are not free.
# Four and three are what the tablet's screens need — the argument is in
# app/reads/scheduler.py, whose per-plan semaphore reads this same table, and in
# bench/anticipation.py, which measures against it.
#
# It lives here rather than there because this is where it has to mean something ACROSS
# plans: a semaphore built per plan cannot see that speculation is holding four Shopify slots
# while the owner's plan holds four more and both are spending one bucket.
SOURCE_SLOTS: dict[str, int] = {"shopify": 4, "gmail": 3, "mac": 8}
DEFAULT_SLOTS = 3
# What this throttle adds, and what it deliberately does not.
#
# It ADDS the global view. `SOURCE_LIMITS` in the scheduler is a semaphore built PER PLAN, so
# speculation in its own plan held four Shopify slots while the owner's plan held four more,
# and both went to the same leaky bucket. Here the count is across plans.
#
# It does NOT re-bound speculation. How many reads the anticipation layer may have in flight
# per source is MAX_PER_SOURCE in app/anticipation/engine.py, measured by bench/anticipation.py
# against Shopify's 50-points-a-second refill. A second, tighter ceiling here would halve that
# layer's behaviour from underneath it, and two bounds on one thing is how they come to
# disagree. So a lower lane's ceiling IS the source's limit, and what this file guarantees is
# the other half: an owner lane is never refused a slot, whatever the lower lanes hold.
LANE_SHARE: dict[str, float] = {
    FOREGROUND: 1.0, NAVIGATION: 1.0, PRECONDITION: 1.0, BACKGROUND: 1.0, SPECULATION: 1.0,
}


class Throttle:
    """How much of each source is in flight, per lane. Counting only: the waiting is the
    scheduler's semaphore and the yielding is `yield_to`. A counter that blocks is a counter
    that can deadlock a turn, and this one is consulted on the owner's critical path."""

    def __init__(self) -> None:
        self._held: dict[tuple[str, str], int] = {}
        self._lock = threading.Lock()
        self.admitted = 0
        self.refused = 0

    def slots(self, source: str, lane: str) -> int:
        """This lane's ceiling on this source. See LANE_SHARE for why a lower lane's ceiling
        is the source's own and not a fraction of it."""
        total = SOURCE_SLOTS.get(source, DEFAULT_SLOTS)
        share = LANE_SHARE.get(lane, 1.0)
        if share >= 1.0:
            return total
        return max(1, min(total - 1, math.ceil(total * share)))

    def in_flight(self, source: str = "", lane: str = "") -> int:
        with self._lock:
            return sum(
                n for (src, ln), n in self._held.items()
                if (not source or src == source) and (not lane or ln == lane)
            )

    def admit(self, source: str, lane: str) -> bool:
        """Whether a read of this source may start in this lane.

        An owner lane is never refused. That is deliberate and it is the whole point: his
        reads are what the source is for, they are paced by the scheduler's own per-plan
        semaphore, and a throttle that could tell the owner's read to wait for a guess would
        be D-4 with a different message on it.

        A lower lane is refused when the source is at its limit ACROSS plans. A refused
        speculative read costs nothing: the prediction lands empty and the read it would have
        saved happens later at the price it always had (app/memory/prefetch.py).
        """
        ok = lane in OWNER_LANES or (
            self.in_flight(source, lane) < self.slots(source, lane)
            and self.in_flight(source) < SOURCE_SLOTS.get(source, DEFAULT_SLOTS)
        )
        with self._lock:
            if ok:
                self.admitted += 1
            else:
                self.refused += 1
        return ok

    def take(self, source: str, lane: str) -> tuple[str, str]:
        with self._lock:
            self._held[(source, lane)] = self._held.get((source, lane), 0) + 1
        return (source, lane)

    def give_back(self, held: tuple[str, str]) -> None:
        with self._lock:
            if self._held.get(held, 0) > 0:
                self._held[held] -= 1
                if not self._held[held]:
                    del self._held[held]

    @contextmanager
    def holding(self, source: str, lane: str):
        held = self.take(source, lane)
        try:
            yield held
        finally:
            self.give_back(held)

    def reset(self) -> None:
        with self._lock:
            self._held.clear()
            self.admitted = 0
            self.refused = 0

    def counts(self) -> dict[str, Any]:
        with self._lock:
            held = {f"{src}:{lane}": n for (src, lane), n in self._held.items()}
        return {"admitted": self.admitted, "refused": self.refused, "in_flight": held}


_throttle: Throttle | None = None


def throttle() -> Throttle:
    global _throttle
    if _throttle is None:
        _throttle = Throttle()
    return _throttle


def install_throttle(new: Throttle) -> Throttle:
    global _throttle
    _throttle = new
    return _throttle


# ------------------------------------------------------------------ per conversation


def scope_of(session: Any) -> str:
    """The conversation a piece of reading belongs to: a login and a session id.

    The isolation key everything here is keyed by, and the one the anticipation layer's own
    scopes use (app/anticipation/engine.py::scope_of delegates to this). It lives here
    because three modules need it and none of them should import another to get it.
    """
    login = str(getattr(session, "login", "") or "") or "owner"
    return f"{login}|{getattr(session, 'session_id', '') or ''}"


def ledger_for(session: Any) -> Ledger:
    """The conversation's own ledger, made on first use and kept on the session.

    A session-less caller (a bench, a unit test) gets a process-wide one rather than an
    error: a read budget is a bound, and a bound that can be escaped by not having a session
    is not one.
    """
    if session is None:
        return _fallback_ledger()
    found = getattr(session, "read_budgets", None)
    if isinstance(found, Ledger):
        return found
    ledger = Ledger()
    try:
        session.read_budgets = ledger
    except AttributeError:
        return _fallback_ledger()
    return ledger


_FALLBACK: list[Ledger] = []


def _fallback_ledger() -> Ledger:
    if not _FALLBACK:
        _FALLBACK.append(Ledger())
    return _FALLBACK[0]


def key_for(session: Any, lane: str) -> str:
    """The unit of work a lane's budget belongs to, from what the session knows.

    FOREGROUND is the turn; everything else is named by its caller and falls back to the
    turn, because an unnamed unit of work sharing the turn's key is the old behaviour and is
    never worse than it.
    """
    turn = str(getattr(session, "turn_id", "") or "")
    if lane == FOREGROUND:
        return turn
    lane_name_now, key = current_lane()
    if lane_name_now == lane and key:
        return key
    return turn


def report(session: Any) -> dict[str, Any]:
    """What the lanes did, for the turn's performance block and GET /anticipation."""
    return {
        "lanes": list(LANES),
        "priority": dict(PRIORITY),
        "budgets": {lane: {"calls": b.calls, "cost": b.cost, "elapsed_s": b.elapsed_s}
                    for lane, b in BUDGETS.items()},
        "spend": ledger_for(session).counts(),
        "throttle": throttle().counts(),
    }
