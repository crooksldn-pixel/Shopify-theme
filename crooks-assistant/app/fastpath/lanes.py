"""Which lane a request runs in.

    FAST    the Mac already knows the procedure: no model call on the critical path
    NORMAL  Claude, with only the context this question needs
    DEEP    more work than one answer: progressive, backgroundable, never a locked screen

The lane is decided from structure — the resolved intent, whether a recipe exists for it, and
whether the request's own shape says it is large — never from a phrase. A request that cannot
be served by a recipe is NORMAL; the fast lane is an optimisation, never a fallback.
"""

from __future__ import annotations

from typing import Any

FAST = "FAST"
NORMAL = "NORMAL"
DEEP = "DEEP"

# Words that describe a scope rather than a thing: every one of them means the answer is a
# sweep, and a sweep is DEEP whether or not it is phrased as a question.
_EXHAUSTIVE = frozenset({"all", "every", "each", "everyone", "everybody", "any", "across", "whole", "entire", "exhaustive", "one by one", "through"})
# A DEEP request is one that is large by shape: two or more clauses, or a sweep, or both
# sources at once over a set.
_MIN_DEEP_WORDS = 8


def choose_lane(intent: Any, *, recipe: Any = None, text: str = "") -> tuple[str, str]:
    """(lane, why). `why` is one clause, for the timeline and the trace — never reasoning."""
    words = getattr(getattr(intent, "signals", None), "words", ()) or ()
    have = set(words)
    sig = getattr(intent, "signals", None)

    if recipe is not None and getattr(intent, "family", "") and intent.confidence >= recipe.min_confidence:
        return FAST, f"{intent.family} at {intent.confidence:.2f}"

    exhaustive = bool(have & _EXHAUSTIVE)
    joins = getattr(sig, "joins", 0) if sig is not None else 0
    cross_source = bool(sig is not None and sig.email and (sig.order or sig.customer or sig.metric))
    if len(words) >= _MIN_DEEP_WORDS and (exhaustive or joins >= 2 or (cross_source and exhaustive)):
        why = "a sweep" if exhaustive else "several things at once"
        return DEEP, why
    if cross_source and len(words) >= _MIN_DEEP_WORDS:
        return DEEP, "the shop and the inbox together"
    return NORMAL, getattr(intent, "reason", "") or "an ordinary question"
