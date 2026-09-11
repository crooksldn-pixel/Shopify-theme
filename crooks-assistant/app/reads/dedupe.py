"""One request per thing asked for — D-13.

    turn_26db2bafe507   commerce_query ×2   gmail_search ×2
    turn_6089e7517986   gmail_search   ×2   shopify_order_detail ×2

Two duplicates in each of two turns, and twenty-four `email_thread` renders across fourteen
turns. There were two mechanisms and each had a hole in it. `app/memory/coalesce.py` joins
callers to a flight, but only the anticipation layer used it. `app/analytics/plan.py` kept
what a turn had already run, but only for the three analytic tools and only on an exact
argument match — so `commerce_query(title="Today")` and `commerce_query(title="Orders")`,
which read the same rows for two cards, were two requests.

This module is the one place a read goes through, and it has one key:

    scope | tool | entity | canonical args | freshness

* **canonical args** drop what does not change what is read. A card's `title` is
  presentation; `#1938` and ` 1938 ` are one order. That is the line that turns two
  presentation paths into one request.
* **entity** is named separately so a card and a rail and an enrichment asking about one
  order collapse whatever else differs.
* **scope** is the LOGIN, not the conversation: two of the owner's conversations wanting the
  same record want one request, and another login must never be served his.
* **freshness** is what a precondition changes. `must_be_fresh` (app/reads/budget.py) puts a
  read in its own key space, so a mutation's precondition or proof neither reads what was
  held nor joins a flight that was started for something else. It is the one rule this file
  is subordinate to: never reuse stale mutation-sensitive data.

Everything is measured rather than claimed — `requests_avoided`, `latency_saved_ms`,
`provider_calls_saved` — from the duration the avoided read actually took.
"""

from __future__ import annotations

import copy
import hashlib
import json
import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from app.memory.coalesce import Coalescer
from app.reads import budget

log = logging.getLogger("crooks.reads")

FRESH = "fresh"            # a read that must go to the source: a precondition, a proof
REUSABLE = "reusable"      # a read that may be served from a flight or a recent answer

# How long a landed read stands, per source. Short: this is "the same thing, asked twice",
# not a cache — the tiered cache is app/memory/store.py and has the lifetimes that belong to
# a record. Gmail is longer than Shopify because a thread list changes when mail arrives and
# an order changes when the shop is worked on.
RECENT_TTL_S: dict[str, float] = {"shopify": 12.0, "gmail": 20.0, "mac": 30.0}
DEFAULT_TTL_S = 10.0
# How many landed reads are kept. Bounded like everything else here.
MAX_RECENT = 256

# Arguments that change how a result is DRAWN and not what is READ. Dropped from the key.
PRESENTATION_ARGS = frozenset({"title", "label", "view", "caption", "heading"})

# The reads whose WHOLE effect is the answer they return, and therefore the reads two callers
# may share. Nothing outside this set is coalesced or reused.
#
# The distinction is not "is it a read" — the registry already answers that, and `_assert_read`
# enforces it. It is whether running the tool a second time does anything besides return the
# same answer. Several registered reads DO: `commerce_query` publishes a working set, which is
# what makes a listing navigable (app/tools/analytics_tools.py); the workspace tools open a
# form on the branch. Serving their second caller from the first's answer would skip the thing
# the second caller rang for — a discount workspace that never opened, a set that "next" has
# nothing to walk.
#
# Those duplicates are not left unhandled: an analytic query that has already run for this
# unit of work is answered from app/analytics/plan.py, which hands back the same rendered
# result WITHOUT re-creating the set, and now fingerprints its arguments through `canonical`
# below — so `commerce_query(title="Today")` and `commerce_query(title="Orders")`, the two
# presentation paths of D-13, are one query there.
#
# This is the same line app/memory/prefetch.py draws for what may be read speculatively, and
# it is drawn for the same reason.
PURE_READS = frozenset({
    "shopify_find_order", "shopify_order_detail", "shopify_find_customer",
    "shopify_customer_history", "shopify_product_info", "shopify_inventory",
    "shopify_variant_search", "gmail_search", "gmail_read_thread",
})
# Where an argument names the record a read is about. First match wins, in this order.
ENTITY_ARGS = ("order_id", "customer_id", "thread_id", "message_id", "variant_id",
               "product_id", "draft_order_id", "query", "q")

# Which source a tool reads. By prefix, so a tool added later is classified without this
# table being edited — and "mac" (the Mac's own internal reads) spends no provider call, so
# `provider_calls_saved` does not count it.
_SOURCE_PREFIX = (("gmail_", "gmail"), ("email_", "gmail"), ("shopify_", "shopify"),
                  ("commerce_", "shopify"), ("inventory_", "shopify"), ("analytics_", "shopify"))
PROVIDER_SOURCES = frozenset({"shopify", "gmail"})


class NotAReadError(RuntimeError):
    """A write tool was handed to the dedupe layer. Two commits of one change are two
    commits; nothing here may ever join, reuse or hold one."""


def source_of(tool: str) -> str:
    for prefix, source in _SOURCE_PREFIX:
        if tool.startswith(prefix):
            return source
    return "mac"


def _scalar(value: Any) -> Any:
    if isinstance(value, str):
        # An order said as "#1938" and typed as " 1938 " is one order.
        return value.strip().lstrip("#")
    if isinstance(value, bool):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def canonical(args: Any) -> Any:
    """The arguments as their identity: presentation dropped, empties dropped, keys sorted."""
    if isinstance(args, dict):
        out = {}
        for key, value in args.items():
            name = str(key)
            if name in PRESENTATION_ARGS or value is None or value == "" or value == [] or value == {}:
                continue
            out[name] = canonical(value)
        return dict(sorted(out.items()))
    if isinstance(args, (list, tuple)):
        return [canonical(v) for v in args]
    return _scalar(args)


def fingerprint(args: Any) -> str:
    blob = json.dumps(canonical(args), sort_keys=True, default=str, ensure_ascii=False)
    return hashlib.sha1(blob.encode("utf-8")).hexdigest()[:16]


def entity_of(args: dict[str, Any] | None) -> str:
    for name in ENTITY_ARGS:
        value = (args or {}).get(name)
        if isinstance(value, (str, int)) and str(value).strip():
            return str(_scalar(str(value)))
    return ""


@dataclass(frozen=True, slots=True)
class ReadKey:
    tool: str
    args: str
    entity: str
    scope: str
    freshness: str

    def __str__(self) -> str:
        return f"{self.scope}|{self.tool}|{self.entity}|{self.args}|{self.freshness}"


def key_for(tool: str, args: dict[str, Any] | None = None, *, scope: str = "",
            must_be_fresh: bool = False) -> ReadKey:
    return ReadKey(
        tool=str(tool), args=fingerprint(args or {}), entity=entity_of(args),
        scope=str(scope or "owner"), freshness=FRESH if must_be_fresh else REUSABLE,
    )


@dataclass(slots=True)
class Landed:
    value: Any
    at: float
    ms: float
    source: str


@dataclass(slots=True)
class Saving:
    """What was avoided, in the units the brief asks for."""

    requests_avoided: int = 0
    latency_saved_ms: float = 0.0
    provider_calls_saved: int = 0
    served: int = 0
    coalesced: int = 0          # joined a flight already running
    reused: int = 0             # answered from a read that had just landed
    by_tool: dict[str, int] = field(default_factory=dict)

    def avoided(self, tool: str, *, ms: float, source: str, joined: bool) -> None:
        self.requests_avoided += 1
        self.latency_saved_ms += max(0.0, float(ms))
        if source in PROVIDER_SOURCES:
            self.provider_calls_saved += 1
        if joined:
            self.coalesced += 1
        else:
            self.reused += 1
        self.by_tool[tool] = self.by_tool.get(tool, 0) + 1

    def public(self) -> dict[str, Any]:
        return {
            "requests_avoided": self.requests_avoided,
            "latency_saved_ms": round(self.latency_saved_ms, 1),
            "provider_calls_saved": self.provider_calls_saved,
            "served": self.served, "coalesced": self.coalesced, "reused": self.reused,
            "by_tool": dict(sorted(self.by_tool.items())),
        }


class Dedupe:
    """In-flight coalescing and recent-read reuse, behind one key."""

    def __init__(self, *, clock=time.monotonic, coalescer: Coalescer | None = None) -> None:
        self.clock = clock
        self._flights = coalescer if coalescer is not None else Coalescer(clock=clock)
        self._recent: dict[str, Landed] = {}
        self.saving = Saving()

    # ------------------------------------------------------------------ the read

    async def read(
        self, tool: str, args: dict[str, Any] | None = None, *, scope: str = "",
        lane: str = budget.FOREGROUND, factory: Callable[[], Awaitable[Any]],
        source: str = "", ttl_s: float | None = None,
    ) -> Any:
        """`factory()`'s result, made once per key while it is worth making once.

        A precondition or verification read (`lane` PRECONDITION) neither reads the recent
        table nor joins a flight: it calls `factory` itself, every time. Its answer is still
        published, because the freshest thing there is cannot make a later read staler.
        """
        _assert_read(tool)
        source = source or source_of(tool)
        reusable = str(key_for(tool, args, scope=scope, must_be_fresh=False))

        async def once() -> Any:
            started = self.clock()
            value = await factory()
            ms = (self.clock() - started) * 1000
            self.saving.served += 1
            if value is not None:
                self._remember(reusable, value, ms=ms, source=source)
            return value

        if budget.must_be_fresh(lane) or tool not in PURE_READS:
            # No flight, no recent answer, no shared future. A change is proven against the
            # source and against nothing else — and a read that also changes what the
            # conversation holds is run for every caller that asks for it (see PURE_READS).
            return await once()

        held = self._held(reusable, source, ttl_s)
        if held is not None:
            self.saving.avoided(tool, ms=held.ms, source=source, joined=False)
            return self._copy_out(held.value, held)

        # `Coalescer.run` joins an existing flight or starts one, and this caller needs to
        # know which it did: the counter on the coalescer is shared, so reading it afterwards
        # told the caller that STARTED the flight that it had joined one.
        #
        # There is no await between this check and `run`'s own, so the two cannot disagree.
        joining = self._flights.in_flight(reusable)
        value = await self._flights.run(reusable, once)
        if joining:
            self.saving.avoided(tool, ms=self._ms_of(reusable), source=source, joined=True)
            return self._copy_out(value, None)
        return value

    # ------------------------------------------------------------------ what is held

    def _held(self, key: str, source: str, ttl_s: float | None) -> Landed | None:
        found = self._recent.get(key)
        if found is None:
            return None
        ttl = float(RECENT_TTL_S.get(source, DEFAULT_TTL_S) if ttl_s is None else ttl_s)
        if self.clock() - found.at > ttl:
            del self._recent[key]
            return None
        return found

    def _ms_of(self, key: str) -> float:
        found = self._recent.get(key)
        return found.ms if found is not None else 0.0

    def _remember(self, key: str, value: Any, *, ms: float, source: str) -> None:
        self._recent[key] = Landed(value=_copy(value), at=self.clock(), ms=ms, source=source)
        if len(self._recent) > MAX_RECENT:
            for old in sorted(self._recent, key=lambda k: self._recent[k].at)[: len(self._recent) - MAX_RECENT]:
                del self._recent[old]

    def _copy_out(self, value: Any, held: Landed | None) -> Any:
        """A caller gets its own copy, marked as reused. Handing out the held object let the
        first caller's edit change what the second one saw, which is a bug that only appears
        once two paths really do share a read."""
        out = _copy(value)
        if isinstance(out, dict):
            out["_reused"] = True
            if held is not None:
                out["_reused_age_ms"] = round((self.clock() - held.at) * 1000, 1)
        return out

    # ------------------------------------------------------------------ invalidation

    def invalidate(self, ref: str = "", *, tool: str = "", scope: str = "") -> int:
        """Drop what is held about a record. Called the moment a write is proven
        (app/memory/store.py::invalidate_for_write) — nothing that described the thing that
        changed may be handed out again, however recently it was read."""
        doomed = [
            key for key in self._recent
            if (not ref or str(ref) in key) and (not tool or f"|{tool}|" in key)
            and (not scope or key.startswith(f"{scope}|"))
        ]
        for key in doomed:
            del self._recent[key]
        return len(doomed)

    def reset(self) -> None:
        self._recent.clear()
        self.saving = Saving()

    def stats(self) -> dict[str, Any]:
        out = self.saving.public()
        out["flights"] = self._flights.counts()
        out["held"] = len(self._recent)
        return out


def _copy(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        try:
            return copy.deepcopy(value)
        except Exception:  # noqa: BLE001 — an uncopyable payload is handed back as it is
            return value
    return value


def _assert_read(tool: str) -> None:
    from app.tools import registry

    try:
        spec = registry.get(tool)
    except KeyError as exc:
        raise NotAReadError(f"{tool!r} is not a registered tool") from exc
    if spec.write is not None or spec.batch is not None:
        raise NotAReadError(
            f"{tool!r} is a write tool. Reads are deduped; a change is staged, armed and "
            "proven once, by the action engine."
        )


_current: Dedupe | None = None


def current() -> Dedupe:
    global _current
    if _current is None:
        _current = Dedupe()
    return _current


def install(new: Dedupe) -> Dedupe:
    global _current
    _current = new
    return _current


def scope_of(session: Any) -> str:
    """The login a read is made for. Deliberately the login and not the conversation: the
    same owner's two conversations want one request for one record, and a different login
    must never be served his."""
    return str(getattr(session, "login", "") or "") or "owner"
