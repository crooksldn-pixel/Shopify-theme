"""The permission gate.

classify() is a pure function over (tool name, arguments, ids issued this session). It is the
only thing standing between Claude and the outside world, so it is deliberately boring:

  GREEN  execute now
  AMBER  execute, but the answer must be read back before it is acted on, and the call is
         logged prominently — used for reads that surface customer personal data
  RED    never executes; the runtime stages a proposal and tells the assistant it needs
         confirmation it cannot obtain on Day 1

Two rules make it fail closed. An unregistered tool is RED, so adding a tool without adding a
rule cannot silently grant access. Any tool whose name looks like a mutation is RED regardless
of the rule table, so a write path introduced by accident is blocked by its own name.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class Tier(StrEnum):
    GREEN = "GREEN"
    AMBER = "AMBER"
    RED = "RED"


@dataclass(slots=True, frozen=True)
class Decision:
    tier: Tier
    reason: str

    @property
    def allowed(self) -> bool:
        return self.tier is not Tier.RED


# Day 1 is read-only. Any verb that could change state anywhere is refused on sight, before
# the rule table is consulted, so a write tool cannot be introduced by adding a rule.
_MUTATION_VERBS = (
    "send", "create", "update", "delete", "modify", "write", "draft", "reply", "forward",
    "trash", "archive", "label", "cancel", "refund", "fulfil", "fulfill", "publish",
    "set_", "add_", "remove_", "edit_", "post_", "put_", "patch_", "destroy",
)

# Reads that return customer personal data. They run, but the assistant is told to read the
# match back rather than act on it, which is the M13 low-confidence rule in tool form.
_PII_TOOLS = frozenset({"shopify_find_customer", "shopify_order_detail", "gmail_read_thread"})

_KNOWN_TOOLS = frozenset({
    # mocks — M5 only
    "mock_echo", "mock_slow", "mock_danger",
    # Shopify — M7
    "shopify_find_order", "shopify_order_detail", "shopify_list_orders",
    "shopify_find_customer", "shopify_inventory", "shopify_sales_summary",
    "shopify_product_info",
    # Gmail — M9
    "gmail_search", "gmail_read_thread",
})

# Tools that may only be called with an id this session already handed to the assistant. Stops
# Claude inventing an order id or a thread id and being told about a stranger's order.
_ISSUED_ID_ARGS: dict[str, tuple[str, ...]] = {
    "shopify_order_detail": ("order_id",),
    "gmail_read_thread": ("thread_id",),
}

# Argument bounds. Exceeding one is not an error — it is clamped by the tool — but a wildly
# out-of-range request usually means the model has misunderstood, so it is worth refusing.
_MAX_LIMIT = 50
_MAX_DAYS = 365

_ID_SHAPE = re.compile(r"^[A-Za-z0-9/_.:=+-]{1,200}$")


def _looks_like_mutation(name: str) -> bool:
    return any(verb in name for verb in _MUTATION_VERBS)


def classify(
    tool_name: str,
    args: dict[str, Any] | None = None,
    issued_ids: Iterable[str] | None = None,
) -> Decision:
    """Classify one tool call. Pure: no I/O, no globals, no clock."""
    from app.tools.registry import normalise_tool_name

    name = normalise_tool_name(tool_name)
    args = args or {}
    issued = frozenset(issued_ids or ())

    if not name:
        return Decision(Tier.RED, "Empty tool name.")

    if _looks_like_mutation(name):
        return Decision(
            Tier.RED,
            f"{name} reads as a write operation. Day 1 is strictly read-only.",
        )

    if name not in _KNOWN_TOOLS:
        return Decision(Tier.RED, f"{name} is not a registered tool.")

    if name == "mock_danger":
        return Decision(Tier.RED, "mock_danger exists to prove RED tools never execute.")

    for arg in _ISSUED_ID_ARGS.get(name, ()):
        value = args.get(arg)
        if value is None or not str(value).strip():
            return Decision(Tier.RED, f"{name} requires {arg}, which was not supplied.")
        value = str(value)
        if not _ID_SHAPE.match(value):
            return Decision(Tier.RED, f"{arg}={value!r} is not a well-formed id.")
        if value not in issued:
            return Decision(
                Tier.RED,
                f"{arg}={value!r} was not issued in this session. "
                "Search for the record first, then use the id that search returned.",
            )

    limit = args.get("limit")
    if limit is not None:
        try:
            if int(limit) > _MAX_LIMIT or int(limit) < 1:
                return Decision(Tier.RED, f"limit={limit} is outside 1..{_MAX_LIMIT}.")
        except (TypeError, ValueError):
            return Decision(Tier.RED, f"limit={limit!r} is not a number.")

    days = args.get("days")
    if days is not None:
        try:
            if int(days) > _MAX_DAYS or int(days) < 1:
                return Decision(Tier.RED, f"days={days} is outside 1..{_MAX_DAYS}.")
        except (TypeError, ValueError):
            return Decision(Tier.RED, f"days={days!r} is not a number.")

    if name in _PII_TOOLS:
        return Decision(Tier.AMBER, f"{name} returns customer personal data; read it back.")

    return Decision(Tier.GREEN, "Read-only, in scope, arguments within bounds.")
