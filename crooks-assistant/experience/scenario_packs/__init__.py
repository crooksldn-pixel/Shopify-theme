"""Scenario packs: golden scenarios added one file at a time.

`experience/scenarios.py` holds the Phase 1 set as a literal tuple. A Phase 3 family adds
its own scenarios as a module here exposing `SCENARIOS` — a tuple of `(name, coroutine)` in
the same shape — and `scenarios.SCENARIOS` collects them all, so two families never edit the
same line. A pack that fails to import is reported by name and does not hide the others.
"""

from __future__ import annotations

import importlib
import logging
import pkgutil
from typing import Any

log = logging.getLogger("crooks.experience")


def collect() -> tuple[tuple[str, Any], ...]:
    out: list[tuple[str, Any]] = []
    for info in sorted(pkgutil.iter_modules(__path__), key=lambda m: m.name):
        if info.name.startswith("_"):
            continue
        try:
            module = importlib.import_module(f"{__name__}.{info.name}")
        except Exception as exc:  # noqa: BLE001 — one pack must not take the rest down
            log.error("scenario pack %s failed to load: %s: %s", info.name, type(exc).__name__, exc)
            continue
        for name, fn in getattr(module, "SCENARIOS", ()) or ():
            out.append((str(name), fn))
    return tuple(out)
