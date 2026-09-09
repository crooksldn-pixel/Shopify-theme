"""The permission gate.

classify() is a pure function over (tool name, arguments, ids issued this session). It is the
only thing standing between Claude and the outside world, so it is deliberately boring. A
decision has two parts, because risk and what-happens-next are different questions:

  risk         GREEN  a read within bounds
               AMBER  a read that surfaces a person's details (read it back), or a routine
                      reversible write
               RED    a write that is hard to undo, or anything refused

  disposition  EXECUTE_NOW      run the handler now
               STAGE_FOR_OWNER  do not run it: prepare the change and wait for the owner
                                to authorise it on the tablet (app/actions/engine.py)
               DENY             refuse; nothing is prepared and nothing can be authorised

Three rules make it fail closed. An unregistered tool is denied, so adding a tool without a
rule cannot grant access. Any tool whose name reads as a mutation is denied unless it is
registered with a complete write definition (app/tools/registry.py WriteSpec), so a write path
introduced by accident is blocked by its own name. And a write is only ever staged, never
executed here: the gate has no path from a tool call to a mutation.
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


class Disposition(StrEnum):
    EXECUTE_NOW = "EXECUTE_NOW"
    STAGE_FOR_OWNER = "STAGE_FOR_OWNER"
    DENY = "DENY"


@dataclass(slots=True, frozen=True)
class Decision:
    tier: Tier
    reason: str
    disposition: Disposition = Disposition.DENY
    # True when the call was refused for something the model can put right by itself — an id
    # it has not looked up yet. Nothing is forbidden; it went about it the wrong way, and it
    # must not tell the owner it could not do this.
    recoverable: bool = False

    @property
    def allowed(self) -> bool:
        return self.disposition is not Disposition.DENY

    @property
    def executes(self) -> bool:
        return self.disposition is Disposition.EXECUTE_NOW

    @property
    def stages(self) -> bool:
        return self.disposition is Disposition.STAGE_FOR_OWNER


def deny(reason: str, *, recoverable: bool = False) -> Decision:
    return Decision(Tier.RED, reason, Disposition.DENY, recoverable=recoverable)


# Any verb that could change state anywhere is caught on sight, before the rule table is
# consulted. A name that matches is denied unless the registry holds a complete write
# definition for it (see _classify_write), and even then it is only ever staged for the owner:
# a write cannot be introduced by adding a rule, only by declaring one, and never executes here.
_MUTATION_VERBS = (
    "send", "create", "update", "delete", "modify", "write", "draft", "reply", "forward",
    "trash", "archive", "label", "cancel", "refund", "fulfil", "fulfill", "publish",
    "set_", "add_", "remove_", "edit_", "post_", "put_", "patch_", "destroy", "append",
    "restore", "commit", "approve", "execute",
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
# The kind of id each detail tool accepts. A Customer gid handed to the order tool is not
# "issued this session" in any sense that matters, even though a search did return it.
_ID_KIND = {
    "order_id": re.compile(r"^gid://shopify/Order/\d+$"),
    "thread_id": re.compile(r"^[0-9a-f]{6,}$", re.I),
}


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
        return deny("Empty tool name.")

    spec = _spec(name)
    if _looks_like_mutation(name) or (spec is not None and spec.write is not None):
        return _classify_write(name, spec, args, issued)

    if name not in _KNOWN_TOOLS:
        return deny(f"{name} is not a registered tool.")

    if name == "mock_danger":
        return deny("mock_danger exists to prove RED tools never execute.")

    # The registry's ToolSpec is the second source of truth: a tool that declares AMBER or
    # an issued-id argument there gets it here too, so the two tables cannot drift apart.
    spec_tier = spec.tier if spec is not None else None
    spec_id_args = tuple(spec.issued_id_args) if spec is not None else ()
    id_args = tuple(dict.fromkeys(_ISSUED_ID_ARGS.get(name, ()) + spec_id_args))
    if spec_tier is Tier.RED:
        return deny(f"{name} is registered as RED.")

    problem = _check_issued_ids(name, id_args, args, issued)
    if problem:
        return deny(problem.lstrip(_RECOVERABLE), recoverable=problem.startswith(_RECOVERABLE))

    limit = args.get("limit")
    if limit is not None:
        try:
            if int(limit) > _MAX_LIMIT or int(limit) < 1:
                return deny(f"limit={limit} is outside 1..{_MAX_LIMIT}.")
        except (TypeError, ValueError):
            return deny(f"limit={limit!r} is not a number.")

    days = args.get("days")
    if days is not None:
        try:
            if int(days) > _MAX_DAYS or int(days) < 1:
                return deny(f"days={days} is outside 1..{_MAX_DAYS}.")
        except (TypeError, ValueError):
            return deny(f"days={days!r} is not a number.")

    if name in _PII_TOOLS or spec_tier is Tier.AMBER:
        return Decision(
            Tier.AMBER, f"{name} returns customer personal data; read it back.", Disposition.EXECUTE_NOW,
        )

    return Decision(Tier.GREEN, "Read-only, in scope, arguments within bounds.", Disposition.EXECUTE_NOW)


def _classify_write(name: str, spec, args: dict[str, Any], issued: frozenset[str]) -> Decision:
    """A tool that reads as a write. It is staged for the owner only when it is registered
    with a complete write definition and its arguments pass every bound; otherwise denied."""
    if spec is None:
        return deny(f"{name} reads as a write operation and is not a registered tool.")
    write = spec.write
    if write is None or not write.complete:
        return deny(f"{name} reads as a write operation and has no reviewed write definition.")
    if spec.tier is Tier.GREEN:
        return deny(f"{name} is a write and cannot be GREEN.")
    id_args = tuple(dict.fromkeys(spec.issued_id_args))
    if write.entity_arg not in id_args:
        return deny(f"{name} must act on an issued {write.entity_arg}.")
    problem = _check_issued_ids(name, id_args, args, issued)
    if problem:
        return deny(problem.lstrip(_RECOVERABLE), recoverable=problem.startswith(_RECOVERABLE))
    problem = _check_schema_bounds(name, spec.input_schema, args)
    if problem:
        return deny(problem)
    return Decision(
        spec.tier,
        f"{name} is a change to the store: prepared for the owner to authorise on the tablet.",
        Disposition.STAGE_FOR_OWNER,
    )


# Prefixed to the one refusal reason the model can put right on its own. Stripped before the
# words reach the model; what it marks is whether this was a rule or a wrong turning.
_RECOVERABLE = "\x00"


def _check_issued_ids(name: str, id_args: tuple[str, ...], args: dict[str, Any], issued: frozenset[str]) -> str:
    for arg in id_args:
        value = args.get(arg)
        if value is None or not str(value).strip():
            return f"{name} requires {arg}, which was not supplied."
        value = str(value)
        if not _ID_SHAPE.match(value):
            return f"{arg}={value!r} is not a well-formed id."
        kind = _ID_KIND.get(arg)
        if kind is not None and not kind.match(value):
            return f"{arg}={value!r} is not the kind of id {name} takes."
        if value not in issued:
            return _RECOVERABLE + (
                f"{arg}={value!r} is not an id this conversation has looked up, so {name} was "
                "not run. Nothing is refused: find the record first (for an order, "
                f"shopify_find_order), then call {name} again with the id that lookup returned."
            )
    return ""


def _check_schema_bounds(name: str, schema: dict[str, Any], args: dict[str, Any]) -> str:
    """The input schema's own bounds, enforced here for writes rather than trusted to the
    model: required arguments present, no unknown arguments, strings within min and max."""
    properties = schema.get("properties") if isinstance(schema, dict) else None
    properties = properties if isinstance(properties, dict) else {}
    for required in schema.get("required", []) if isinstance(schema, dict) else []:
        if required not in args:
            return f"{name} requires {required}, which was not supplied."
    for key, value in args.items():
        if key not in properties:
            return f"{name} does not take an argument called {key}."
        rule = properties.get(key) or {}
        if rule.get("type") == "string":
            if not isinstance(value, str):
                return f"{name}.{key} must be text."
            length = len(value.strip())
            if "minLength" in rule and length < int(rule["minLength"]):
                return f"{name}.{key} is empty."
            if "maxLength" in rule and len(value) > int(rule["maxLength"]):
                return f"{name}.{key} is longer than {rule['maxLength']} characters."
    return ""


def _spec(name: str):
    """The registered ToolSpec, or None."""
    from app.tools import registry

    try:
        return registry.get(name)
    except KeyError:
        return None
