"""The tiered cache.

Six tiers, each with its own lifetime and its own bound:

    HOT        seconds        a read the last question already made
    SESSION    a conversation what this conversation has been shown
    ENTITY     minutes        an order, a customer, a product, as last read
    ANALYTICS  minutes        a period's aggregate, keyed by the query's fingerprint
    EMAIL      minutes        the inbox correlated to a customer, which is expensive to build
    ACTION     the session    what a change did, once it was proven

Every entry says where it came from, when, how long it stands, what query made it, and what
the source's watermark was when it was read. That last part is what makes staleness real
rather than a guess: an entity read before the order cache's watermark moved is stale even if
its TTL has not expired.

Nothing here is authoritative for a write. Writes re-read the source; see app/actions/engine.py.
"""

from __future__ import annotations

import hashlib
import json
import threading
import time
from dataclasses import dataclass, field
from typing import Any

HOT = "hot"
SESSION = "session"
ENTITY = "entity"
ANALYTICS = "analytics"
EMAIL = "email"
ACTION = "action"

TIERS = (HOT, SESSION, ENTITY, ANALYTICS, EMAIL, ACTION)

# Lifetime and bound per tier. Small on purpose: this is a tablet's working memory, not a
# database. A tier that overflows drops its least recently used entry.
DEFAULT_TTL_S: dict[str, float] = {HOT: 20.0, SESSION: 900.0, ENTITY: 180.0, ANALYTICS: 240.0, EMAIL: 300.0, ACTION: 1800.0}
MAX_ENTRIES: dict[str, int] = {HOT: 64, SESSION: 128, ENTITY: 256, ANALYTICS: 96, EMAIL: 96, ACTION: 128}

FRESH = "fresh"
STALE = "stale"
EXPIRED = "expired"


def fingerprint(name: str, args: Any) -> str:
    """A query's identity: the tool and its arguments, order-independent."""
    blob = json.dumps({"q": name, "a": args}, sort_keys=True, default=str, ensure_ascii=False)
    return hashlib.sha1(blob.encode("utf-8")).hexdigest()[:16]


@dataclass(slots=True)
class Entry:
    key: str
    tier: str
    value: Any
    source: str                     # "shopify", "gmail", "mac", "order_cache"
    fetched_at: float
    ttl_s: float
    query: str = ""                 # the query fingerprint that produced it
    watermark: Any = None           # the source's version when this was read
    provenance: dict[str, Any] = field(default_factory=dict)
    used_at: float = 0.0
    hits: int = 0
    # Set when a write touched what this describes. The value can still be shown — labelled —
    # but never used as a precondition, and never presented as current without saying so.
    invalidated: bool = False

    def age_s(self, now: float) -> float:
        return max(0.0, now - self.fetched_at)

    def freshness(self, now: float, *, watermark: Any = None) -> str:
        if self.invalidated:
            return EXPIRED
        if self.age_s(now) > self.ttl_s:
            return EXPIRED
        if watermark is not None and self.watermark is not None and watermark != self.watermark:
            return STALE
        return FRESH

    def public(self, now: float | None = None) -> dict[str, Any]:
        now = time.time() if now is None else now
        return {
            "source": self.source, "age_s": round(self.age_s(now), 1), "ttl_s": self.ttl_s,
            "fetched_at": round(self.fetched_at, 3), "freshness": self.freshness(now),
            "query": self.query or None, "provenance": dict(self.provenance) or None,
        }


class Memory:
    """The tiers, behind one lock. Read from the event loop and from the timeline's thread."""

    def __init__(self, *, clock=time.time) -> None:
        self.clock = clock
        self._tiers: dict[str, dict[str, Entry]] = {tier: {} for tier in TIERS}
        self._lock = threading.Lock()
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.invalidations = 0
        # Of the hits, the ones served from something the anticipation layer read before it was
        # asked for (provenance origin "predicted", app/anticipation/engine.py). This is how
        # the effect of anticipation on a turn is MEASURED rather than claimed: it is published
        # on every turn's performance block under `cache`, beside the hits it is part of.
        self.predicted_hits = 0

    # -------------------------------------------------------------- read/write

    def get(self, tier: str, key: str, *, watermark: Any = None, allow_stale: bool = False) -> Entry | None:
        """The entry, if it stands. A stale one is returned only when the caller says it will
        label it; an expired or invalidated one never is."""
        now = self.clock()
        with self._lock:
            entry = self._tiers.get(tier, {}).get(key)
            if entry is None:
                self.misses += 1
                return None
            state = entry.freshness(now, watermark=watermark)
            if state == EXPIRED or (state == STALE and not allow_stale):
                if state == EXPIRED:
                    self._tiers[tier].pop(key, None)
                self.misses += 1
                return None
            entry.used_at = now
            entry.hits += 1
            self.hits += 1
            if entry.provenance.get("origin") == "predicted":
                self.predicted_hits += 1
            return entry

    def put(
        self, tier: str, key: str, value: Any, *, source: str, ttl_s: float | None = None,
        query: str = "", watermark: Any = None, provenance: dict[str, Any] | None = None,
    ) -> Entry:
        now = self.clock()
        entry = Entry(
            key=key, tier=tier, value=value, source=source, fetched_at=now,
            ttl_s=float(DEFAULT_TTL_S.get(tier, 60.0) if ttl_s is None else ttl_s),
            query=query, watermark=watermark, provenance=dict(provenance or {}), used_at=now,
        )
        with self._lock:
            bucket = self._tiers.setdefault(tier, {})
            bucket[key] = entry
            self._prune_locked(tier)
        return entry

    def _prune_locked(self, tier: str) -> None:
        bucket = self._tiers[tier]
        now = self.clock()
        for key, entry in list(bucket.items()):
            if entry.age_s(now) > entry.ttl_s:
                del bucket[key]
        limit = MAX_ENTRIES.get(tier, 64)
        if len(bucket) <= limit:
            return
        for key in sorted(bucket, key=lambda k: bucket[k].used_at)[: len(bucket) - limit]:
            del bucket[key]
            self.evictions += 1

    def drop(self, tier: str, key: str) -> bool:
        with self._lock:
            return self._tiers.get(tier, {}).pop(key, None) is not None

    # ------------------------------------------------------------ invalidation

    def invalidate(self, *, tier: str | None = None, ref: str = "", source: str = "") -> int:
        """Mark matching entries unusable. Called after a proven write, and after anything
        else that makes what is held no longer true. Marking rather than deleting keeps the
        provenance: a card can still say "as it was before the change"."""
        hit = 0
        with self._lock:
            for name in ([tier] if tier else list(self._tiers)):
                for entry in self._tiers.get(name, {}).values():
                    if ref and ref not in entry.key and ref not in str(entry.provenance.get("ref", "")):
                        continue
                    if source and entry.source != source:
                        continue
                    if not entry.invalidated:
                        entry.invalidated = True
                        hit += 1
            self.invalidations += hit
        return hit

    # ------------------------------------------------------------------ stats

    def counts(self) -> dict[str, Any]:
        with self._lock:
            sizes = {tier: len(bucket) for tier, bucket in self._tiers.items()}
        return {"hits": self.hits, "misses": self.misses, "evictions": self.evictions,
                "invalidations": self.invalidations, "predicted_hits": self.predicted_hits,
                "sizes": sizes}

    def clear(self) -> None:
        with self._lock:
            for bucket in self._tiers.values():
                bucket.clear()


_current: Memory | None = None


def install(memory: Memory) -> Memory:
    global _current
    _current = memory
    return memory


def current() -> Memory:
    global _current
    if _current is None:
        _current = Memory()
    return _current


# Which tiers a proven change makes untrue. An order's tags changed: that order's entity
# entry, every analytic that counted it, and any inbox correlation built from it. Never the
# action tier, which records what happened rather than what is.
_WRITE_TIERS = (HOT, SESSION, ENTITY, ANALYTICS, EMAIL)


def invalidate_for_write(entity_kind: str, ref: str, *, memory: Memory | None = None) -> int:
    """Called by the action engine the moment a write is proven. Nothing that described the
    thing that changed may be handed out as current again.

    Analytics are invalidated wholesale rather than by reference: an aggregate does not carry
    the ids that went into it, so the honest thing is to read it again.
    """
    store = memory if memory is not None else current()
    dropped = store.invalidate(tier=ENTITY, ref=str(ref))
    dropped += store.invalidate(tier=HOT, ref=str(ref))
    dropped += store.invalidate(tier=SESSION, ref=str(ref))
    dropped += store.invalidate(tier=ANALYTICS)
    if entity_kind in ("email", "thread", "customer", "order"):
        dropped += store.invalidate(tier=EMAIL)
    return dropped
