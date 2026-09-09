"""Operational memory: what the Mac already knows, and how fresh it is.

Six tiers with different lifetimes (app/memory/store.py), one in-flight coalescer so two
questions asking the same thing make one request (app/memory/coalesce.py), and a bounded
speculative prefetch that only ever reads (app/memory/prefetch.py).

Two rules hold everywhere in here and are not negotiable for speed:

* A write's precondition and its proof NEVER read from this. They re-read the source. See
  app/actions/engine.py; nothing in this package is imported there.
* A mutation authorisation is never cached. Arming is a nonce against a proposal, once.
"""

from app.memory.store import (
    ANALYTICS,
    EMAIL,
    ENTITY,
    HOT,
    Entry,
    Memory,
    current,
    install,
    invalidate_for_write,
)

__all__ = ["ANALYTICS", "EMAIL", "ENTITY", "HOT", "Entry", "Memory", "current", "install", "invalidate_for_write"]
