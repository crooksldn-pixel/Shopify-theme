"""Capability families, with a state a person can act on.

`runtime.capabilities()` answers per OPERATION (ready / blocked / disabled / unknown), which
is what the rail and the write preflight need. The owner asks a different question — "can
this Mac create a discount code?" — and the answer has more shapes than those four: the code
is written but the store has not granted the scope; the store does not offer the feature at
all; no provider is connected; it is not built yet. Those shapes are the states here, and
they reach three places from one table: /health and the capability card (so the owner sees
them), the manifest and the system prompt (so Claude stops trying things it cannot do), and
the tablet (so a chip can be hidden, disabled or explained without guessing).

    READY                   the code is here and the store lets it run
    READ_ONLY               reads work; the write half is off (writes disabled, or live read-only)
    MISSING_SCOPE           the code is here; the store has not granted the scope named
    NOT_SUPPORTED_BY_STORE  the store's plan or configuration does not offer the feature
    DISCONNECTED            an external provider that is not connected (no credentials)
    NOT_IMPLEMENTED         the contract exists; the mutation does not yet
    TEMPORARILY_UNAVAILABLE the provider did not answer the probe; ask again later

A family's `probe` runs against the live runtime (scopes, a feature query) and is cached with
the rest of the capability table; a family with no probe carries a static state. No probe
ever sends a mutation.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

log = logging.getLogger("crooks.capabilities")

STATES = ("READY", "READ_ONLY", "MISSING_SCOPE", "NOT_SUPPORTED_BY_STORE", "DISCONNECTED", "NOT_IMPLEMENTED", "TEMPORARILY_UNAVAILABLE")
# Which states let the write half of a family be offered at all.
OFFERABLE = frozenset({"READY"})


@dataclass(frozen=True)
class CapabilityFamily:
    key: str                                   # "order_edit", "discount_code", "store_credit" …
    label: str                                 # "Order item editing"
    area: str                                  # "orders" | "email" | "products" | "customers" | "analytics" | "shipping" | "system"
    what: str                                  # one sentence, in the owner's words
    operations: tuple[str, ...] = ()           # WriteSpec operations this family stages, if any
    tools: tuple[str, ...] = ()                # read tools it offers, if any
    scopes: tuple[str, ...] = ()               # Shopify / Gmail scopes the writes need
    # Static state when there is no probe, or the probe cannot decide.
    state: str = "NOT_IMPLEMENTED"
    detail: str = ""
    # async (runtime) -> {"state": ..., "detail": ..., "scope": ...}; never sends a mutation.
    probe: Callable[[Any], Awaitable[dict[str, Any]]] | None = None
    # What the tablet may do with this family's controls in each state, when it differs from
    # the default (READY: enable; anything else: explain, or hide when `hide_when_unavailable`).
    hide_when_unavailable: bool = False
    extra: dict[str, Any] = field(default_factory=dict)


REGISTRY: dict[str, CapabilityFamily] = {}


def register(family: CapabilityFamily) -> CapabilityFamily:
    if family.state not in STATES:
        raise ValueError(f"{family.key}: {family.state!r} is not a capability state")
    if family.key in REGISTRY and REGISTRY[family.key] is not family:
        raise ValueError(f"capability family {family.key!r} is registered twice")
    REGISTRY[family.key] = family
    return family


def get(key: str) -> CapabilityFamily | None:
    return REGISTRY.get(key)


def all_families() -> list[CapabilityFamily]:
    return [REGISTRY[k] for k in sorted(REGISTRY)]


async def states(runtime: Any, *, operations: dict[str, dict[str, Any]] | None = None) -> dict[str, dict[str, Any]]:
    """Every family's state now. `operations` is the per-operation table already computed by
    `runtime.capabilities()`; a family whose writes are all "ready" there and that has no probe
    of its own is READY, one whose scope is missing there is MISSING_SCOPE, and so on — the
    probe, when there is one, has the last word."""
    out: dict[str, dict[str, Any]] = {}
    for family in all_families():
        state, detail, scope = family.state, family.detail, (family.scopes[0] if family.scopes else "")
        table = operations or {}
        rows = [table.get(op) for op in family.operations if isinstance(table.get(op), dict)]
        if rows:
            blocked = [r for r in rows if r.get("state") == "blocked"]
            disabled = [r for r in rows if r.get("state") == "disabled"]
            if disabled:
                state, detail = "READ_ONLY", str(disabled[0].get("detail") or "changes are off")
            elif blocked:
                missing = [r for r in blocked if "scope" in str(r.get("detail") or "")]
                state = "MISSING_SCOPE" if missing else "READ_ONLY"
                detail = str(blocked[0].get("detail") or "")
                scope = str((missing or blocked)[0].get("scope") or scope)
            elif all(r.get("state") in ("ready", "unknown") for r in rows) and family.state in ("READY", "NOT_IMPLEMENTED", "TEMPORARILY_UNAVAILABLE"):
                state, detail = ("READY", "ready") if family.state != "NOT_IMPLEMENTED" or family.probe else (family.state, family.detail)
        if family.probe is not None:
            try:
                probed = await family.probe(runtime)
                if isinstance(probed, dict) and probed.get("state") in STATES:
                    state = str(probed["state"])
                    detail = str(probed.get("detail") or detail)
                    scope = str(probed.get("scope") or scope)
            except Exception as exc:  # noqa: BLE001 — a probe that fails is a state, not a crash
                log.warning("capability probe %s failed: %s", family.key, type(exc).__name__)
                state, detail = "TEMPORARILY_UNAVAILABLE", f"the {family.area} check did not answer ({type(exc).__name__})"
        out[family.key] = {
            "key": family.key, "label": family.label, "area": family.area, "what": family.what,
            "state": state, "detail": detail[:200], "scope": scope,
            "operations": list(family.operations), "tools": list(family.tools),
            "offerable": state in OFFERABLE, "hide": bool(family.hide_when_unavailable and state not in OFFERABLE),
        }
    return out


def words(states_table: dict[str, dict[str, Any]]) -> list[str]:
    """The families as lines for the model: what it can and cannot do, and why, so it stops
    trying the ones it cannot. One line each; the detail is the reason, never a stack trace."""
    lines = []
    for key in sorted(states_table):
        row = states_table[key]
        state = row["state"]
        if state == "READY":
            lines.append(f"- {row['label']}: READY.")
        else:
            why = row.get("detail") or state.replace("_", " ").lower()
            lines.append(f"- {row['label']}: {state} — {why}. Do not attempt it; say so if asked.")
    return lines
