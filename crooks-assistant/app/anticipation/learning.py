"""The learned half: what the owner usually does next, and nothing about who he did it to.

This is deliberately not machine learning and deliberately not Claude. It is a table of
counted transitions between states — `order_opened[international,old,unfulfilled]` →
`tracking_checked` — with five properties the brief (§19) asks for and each of which is a test:

* **Private.** A state is an event name and allow-listed feature words (app/anticipation/
  models.py:clean_state). No order number, no address, no name, no email can reach this table:
  the vocabulary is closed, so there is nothing for an identifier to be recorded as.
* **A minimum before anything is learned.** `MIN_OBSERVATIONS` of a pair AND of the state it
  leaves, or `likely()` returns nothing. One coincidence is not a habit.
* **A confidence threshold.** Below `THRESHOLD` a transition is recorded and inspectable but
  never predicted from; `SUGGEST_THRESHOLD` is the higher bar for saying anything out loud.
* **Decay.** Weight halves every `HALF_LIFE_S`. A habit from three months ago stops being a
  prediction on its own, without a sweep and without deleting the history: `observations` keeps
  counting up while `weight` falls, and `weight` is what predicts.
* **Inspectable and resettable.** `inspect()` is the whole table with its arithmetic shown;
  `reset()` empties it. Both reach the owner through GET/POST /anticipation.

Nothing here executes anything. It answers "what usually comes next" and the engine decides
whether that is worth a READ. There is no path from this file to a write, and §19's rule that
a learned pattern may never execute a change is kept structurally: the only thing this module
returns is a state name and a number.
"""

from __future__ import annotations

import json
import logging
import math
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.anticipation.models import EVENTS, clean_state

log = logging.getLogger("crooks.anticipation")

# How many times a pair must be seen before it can predict anything.
MIN_OBSERVATIONS = 4
# The share of a state's outgoing weight a transition needs before it is predicted from.
THRESHOLD = 0.55
# The bar for telling the owner about it (level 3). Higher on purpose.
SUGGEST_THRESHOLD = 0.8
# Decay: a transition's weight halves every fortnight of wall clock.
HALF_LIFE_S = 14 * 24 * 3600.0
# A decayed weight below this predicts nothing, whatever its share: three observations a year
# ago are not a habit even when they are the only three.
MIN_WEIGHT = 2.0
# Bounds. A table this size covers every state the vocabulary can produce many times over; the
# cap is here so a bug cannot grow a file on the Mac's disk without limit.
MAX_STATES = 400
MAX_EDGES_PER_STATE = 24


@dataclass
class Transition:
    """One learned edge, and everything the debug view needs to explain it."""

    state: str
    event: str
    weight: float           # decayed count — what predicts
    observations: int       # raw count — what the minimum is measured against
    last_at: float
    confidence: float = 0.0

    def public(self, now: float) -> dict[str, Any]:
        return {
            "state": self.state, "next": self.event,
            "weight": round(self.weight, 2), "observations": self.observations,
            "confidence": round(self.confidence, 3),
            "age_s": round(max(0.0, now - self.last_at), 1),
            "predicts": self.confidence >= THRESHOLD and self.observations >= MIN_OBSERVATIONS and self.weight >= MIN_WEIGHT,
        }


class Learner:
    """The transition table. Thread-safe; small enough to hold in memory and to write as JSON.

    `path=None` means memory only, which is what a test gets. The runtime passes a path under
    the Mac's own log directory: local and private, on this machine, in a file the owner can
    read and delete.
    """

    def __init__(self, *, path: Path | str | None = None, clock=time.time) -> None:
        self.path = Path(path) if path else None
        self.clock = clock
        self._lock = threading.RLock()
        self._edges: dict[str, dict[str, Transition]] = {}
        self.observed = 0
        self.rejected = 0
        self._loaded = False
        self._dirty = False

    # ------------------------------------------------------------------ recording

    def observe(self, state: str, event: str) -> Transition | None:
        """Record that `event` followed `state` once. Returns the edge, or None when the
        vocabulary refuses it — a refusal is counted, not raised: a signal the owner caused
        must never be able to fail a request."""
        self._ensure_loaded()
        name = str(event or "").strip().lower()
        if name not in EVENTS:
            self.rejected += 1
            return None
        try:
            origin = state if "[" in str(state) or str(state) in EVENTS else clean_state(str(state))
        except ValueError:
            self.rejected += 1
            return None
        if not _is_clean(origin):
            self.rejected += 1
            return None
        now = self.clock()
        with self._lock:
            self._decay_locked(now)
            bucket = self._edges.setdefault(origin, {})
            edge = bucket.get(name)
            if edge is None:
                if len(self._edges) > MAX_STATES or len(bucket) >= MAX_EDGES_PER_STATE:
                    self.rejected += 1
                    return None
                edge = Transition(state=origin, event=name, weight=0.0, observations=0, last_at=now)
                bucket[name] = edge
            edge.weight += 1.0
            edge.observations += 1
            edge.last_at = now
            self.observed += 1
            self._dirty = True
            self._confidence_locked(origin)
            return edge

    # ------------------------------------------------------------------ predicting

    def likely(self, state: str, *, threshold: float | None = None) -> list[Transition]:
        """What usually follows this state, best first. Empty until the minimum is met.

        Three gates, all of them the brief's: enough raw observations of the pair AND of the
        state, enough surviving weight after decay, and enough share of the state's outgoing
        weight. A table that has seen one thing three times predicts nothing at all.
        """
        self._ensure_loaded()
        bar = THRESHOLD if threshold is None else float(threshold)
        now = self.clock()
        with self._lock:
            self._decay_locked(now)
            bucket = self._edges.get(str(state)) or {}
            if not bucket:
                return []
            self._confidence_locked(str(state))
            seen = sum(e.observations for e in bucket.values())
            if seen < MIN_OBSERVATIONS:
                return []
            out = [
                Transition(e.state, e.event, e.weight, e.observations, e.last_at, e.confidence)
                for e in bucket.values()
                if e.observations >= MIN_OBSERVATIONS and e.weight >= MIN_WEIGHT and e.confidence >= bar
            ]
        out.sort(key=lambda e: (-e.confidence, -e.observations, e.event))
        return out

    def confidence(self, state: str, event: str) -> float:
        for edge in self.likely(state, threshold=0.0):
            if edge.event == event:
                return edge.confidence
        return 0.0

    # ------------------------------------------------------------------ inspection

    def inspect(self, *, state: str = "") -> dict[str, Any]:
        """The whole table, with the arithmetic shown. What GET /anticipation returns."""
        self._ensure_loaded()
        now = self.clock()
        with self._lock:
            self._decay_locked(now)
            for origin in self._edges:
                self._confidence_locked(origin)
            rows = [
                edge.public(now)
                for origin, bucket in sorted(self._edges.items())
                if not state or origin == state
                for edge in sorted(bucket.values(), key=lambda e: (-e.weight, e.event))
            ]
        return {
            "states": len({r["state"] for r in rows}), "transitions": len(rows),
            "observed": self.observed, "rejected": self.rejected,
            "min_observations": MIN_OBSERVATIONS, "threshold": THRESHOLD,
            "suggest_threshold": SUGGEST_THRESHOLD, "half_life_s": HALF_LIFE_S,
            "min_weight": MIN_WEIGHT,
            "path": str(self.path) if self.path else None,
            "rows": rows,
        }

    def reset(self) -> int:
        """Forget everything, on disk as well. The owner's off switch for §19."""
        with self._lock:
            dropped = sum(len(b) for b in self._edges.values())
            self._edges.clear()
            self.observed = 0
            self.rejected = 0
            self._dirty = True
            self._loaded = True
        self.save()
        if self.path and self.path.exists():
            try:
                self.path.unlink()
            except OSError as exc:  # noqa: BLE001 — a table that will not delete is logged
                log.warning("could not delete the learned table: %s", exc)
        return dropped

    # ------------------------------------------------------------------ persistence

    def save(self) -> bool:
        if self.path is None or not self._dirty:
            return False
        with self._lock:
            payload = {
                "version": 1, "saved_at": round(self.clock(), 3), "observed": self.observed,
                "edges": [
                    {"state": e.state, "next": e.event, "weight": round(e.weight, 4),
                     "observations": e.observations, "last_at": round(e.last_at, 3)}
                    for bucket in self._edges.values() for e in bucket.values()
                ],
            }
            self._dirty = False
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            tmp.replace(self.path)
            return True
        except OSError as exc:  # noqa: BLE001 — a table that will not persist still works
            log.warning("could not write the learned table: %s", exc)
            return False

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        self._loaded = True
        if self.path is None or not self.path.exists():
            return
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:  # noqa: BLE001 — a corrupt table starts empty
            log.warning("the learned table could not be read (%s); starting empty", type(exc).__name__)
            return
        with self._lock:
            for row in (payload or {}).get("edges") or []:
                origin, event = str(row.get("state") or ""), str(row.get("next") or "")
                if event not in EVENTS or not _is_clean(origin):
                    self.rejected += 1
                    continue
                self._edges.setdefault(origin, {})[event] = Transition(
                    state=origin, event=event, weight=float(row.get("weight") or 0.0),
                    observations=int(row.get("observations") or 0), last_at=float(row.get("last_at") or 0.0),
                )
            self.observed = int((payload or {}).get("observed") or 0)

    # ------------------------------------------------------------------ internals

    def _decay_locked(self, now: float) -> None:
        """Halve every weight per half-life since it was last touched, and drop what is left
        of an edge that has decayed to nothing. Observations are never decayed: they are the
        history, and the minimum is a fact about how often a thing was seen at all."""
        for origin, bucket in list(self._edges.items()):
            for event, edge in list(bucket.items()):
                elapsed = max(0.0, now - edge.last_at)
                if elapsed <= 0:
                    continue
                factor = math.pow(0.5, elapsed / HALF_LIFE_S)
                if factor >= 1.0:
                    continue
                edge.weight *= factor
                edge.last_at = now
                self._dirty = True
                if edge.weight < 0.05:
                    del bucket[event]
            if not bucket:
                del self._edges[origin]

    def _confidence_locked(self, state: str) -> None:
        bucket = self._edges.get(state) or {}
        total = sum(e.weight for e in bucket.values())
        for edge in bucket.values():
            edge.confidence = (edge.weight / total) if total > 0 else 0.0


def _is_clean(state: str) -> bool:
    """A state that could only have come from `clean_state`: the event vocabulary, plus
    allow-listed tags in brackets. Checked on the way in AND on the way back off disk, so a
    hand-edited file cannot put an order number into the table either."""
    text = str(state or "")
    if not text or any(ch.isdigit() for ch in text) or "@" in text or "/" in text:
        return False
    head, _, tail = text.partition("[")
    if head not in EVENTS:
        return False
    if not tail:
        return True
    from app.anticipation.models import FEATURES

    if not tail.endswith("]"):
        return False
    return all(tag in FEATURES for tag in tail[:-1].split(",") if tag)


_current: Learner | None = None


def current() -> Learner:
    global _current
    if _current is None:
        _current = Learner(path=_default_path())
    return _current


def install(learner: Learner) -> Learner:
    global _current
    _current = learner
    return learner


def _default_path() -> Path | None:
    """Beside the Mac's own logs — local, private, and where the tests' temporary directory
    already points, so a suite never writes into the owner's state."""
    try:
        from config.settings import get_settings

        return Path(get_settings().log_dir) / "anticipation" / "transitions.json"
    except Exception:  # noqa: BLE001 — no settings, no persistence
        return None
