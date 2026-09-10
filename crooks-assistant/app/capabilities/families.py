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
        state, detail, scope = family.state, family.detail, _said(family.scopes[0] if family.scopes else "")
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


def _said(scope: str) -> str:
    """A scope as a person says it.

    A Gmail scope is a URL — the API wants the whole thing, and one family registered it that
    way — but this string is read by the OWNER, in the settings sheet, and by the model in one
    line of prompt. "gmail.compose" and
    "https://www.googleapis.com/auth/gmail.compose" are the same grant, and only one of them
    is a sentence. Shopify's scopes have no slash and come through unchanged.
    """
    return scope.rsplit("/", 1)[-1] if "://" in scope else scope


def words(states_table: dict[str, dict[str, Any]], *, only_unavailable: bool = True) -> list[str]:
    """The families as lines for the model.

    Only the ones it cannot use, by default, and that is deliberate: what saves the fifteen
    seconds the live test lost is knowing that store credit is not on this store, not being
    told fifteen times a turn that reading orders is READY. The ready ones are the tools it
    is offered — `runtime.withheld_by_family` takes away the rest, so the tool list already
    says what is available, and repeating it on every prompt is model context spent to say
    nothing (brief section 25).

    `only_unavailable=False` gives every family, for the capability surfaces the owner reads.
    """
    if not only_unavailable:
        # The owner's list: every family, in full, with the instruction on each line. Nothing
        # is grouped or clipped, because this is read on a card and not paid for per turn.
        lines = []
        for key in sorted(states_table):
            row = states_table[key]
            if row["state"] == "READY":
                lines.append(f"- {row['label']}: READY.")
                continue
            lines.append(f"- {row['label']}: {row['state']} — {_with_scope(row)}. Do not attempt it; say so if asked.")
        return lines

    # The model's list. Families that are unavailable FOR THE SAME REASON share a line: four
    # NOT_IMPLEMENTED families each repeating "the scope is not granted and the reviewed
    # mutation is not written" was 248 characters of identical text on every model-path turn.
    # State and reason first, then who — because the model reads this to answer "can you do
    # X", and the answer is the state. The scope stays beside each name, since "what
    # permission do you need?" is the follow-up question.
    grouped: dict[tuple[str, str], list[str]] = {}
    for key in sorted(states_table):
        row = states_table[key]
        if row["state"] == "READY":
            continue
        why = _clipped(row.get("detail") or row["state"].replace("_", " ").lower())
        scope = str(row.get("scope") or "")
        name = f"{row['label']} ({scope})" if scope and scope not in why else str(row["label"])
        grouped.setdefault((row["state"], why), []).append(name)
    return [f"- {state} — {why}: {', '.join(names)}" for (state, why), names in grouped.items()]


def _with_scope(row: dict[str, Any]) -> str:
    why = str(row.get("detail") or row["state"].replace("_", " ").lower())
    scope = str(row.get("scope") or "")
    return f"{why} ({scope})" if scope and scope not in why else why


# One clause is enough for the model to answer "can you do X" honestly. The owner's card is
# where a paragraph belongs.
REASON_CHARS = 90


def _clipped(why: str) -> str:
    why = " ".join(str(why).split())
    if len(why) <= REASON_CHARS:
        return why
    cut = why[:REASON_CHARS]
    # Prefer a clause boundary, so the sentence does not stop mid-word.
    for mark in ("; ", ", ", " — "):
        at = cut.rfind(mark)
        if at > REASON_CHARS // 2:
            return cut[:at]
    return cut.rsplit(" ", 1)[0] + "…"
