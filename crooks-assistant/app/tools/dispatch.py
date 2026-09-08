"""The one gated path from Claude to a tool handler.

Everything Claude can reach is wired to `dispatch`. It consults the gate, refuses RED calls
without touching the handler, runs the rest under a timeout, records issued ids, and returns a
compact string for the model. If a call did not come through here, it did not happen.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from app.actions.models import Prepared
from app.session.models import Session
from app.tools import registry
from app.tools.gate import Disposition, Tier, classify
from app.tools.registry import ToolError

log = logging.getLogger("crooks.tools")


def _readable_errors() -> tuple[type[BaseException], ...]:
    from app.clients.gmail import GmailAuthRequired, GmailError
    from app.clients.shopify import ShopifyAuthError, ShopifyError
    from app.clients.whisper import WhisperUnavailable

    return (ToolError, ShopifyError, ShopifyAuthError, GmailError, GmailAuthRequired, WhisperUnavailable)


_READABLE_ERRORS = _readable_errors()

# Result keys whose values are ids the assistant may later use in a detail-style lookup.
_ID_KEYS = ("order_id", "customer_id", "thread_id", "variant_id", "id")
# Result keys whose values are a person's details. Remembered so the turn log can scrub them.
_PII_KEYS = ("customer_name", "customer_email", "name", "from", "from_email", "email", "displayName")


def _harvest_ids(payload: Any, session: Session, *, in_customer: bool = False) -> None:
    """Walk a tool result: record every id it exposed (so follow-up lookups are permitted) and
    every personal string (so the turn log can scrub it)."""
    if isinstance(payload, dict):
        is_order = "order_id" in payload or "order_number" in payload
        customerish = in_customer or ("customer_id" in payload and not is_order) or any(
            k in payload for k in ("from_email", "email")
        )
        for key, value in payload.items():
            if key in _ID_KEYS and isinstance(value, (str, int)):
                session.issue(str(value))
            elif key in _PII_KEYS and isinstance(value, str):
                # `name` is also an order's name (CROOKS-1928); it is personal only inside a
                # customer record, never inside an order record.
                if key != "name" or (customerish and not is_order):
                    session.remember_pii(value)
            else:
                _harvest_ids(value, session, in_customer=customerish and not is_order)
    elif isinstance(payload, list):
        for item in payload:
            _harvest_ids(item, session, in_customer=in_customer)


def _render(payload: Any) -> str:
    if isinstance(payload, str):
        return payload
    return json.dumps(payload, ensure_ascii=False, default=str, indent=None)


async def dispatch(
    tool_name: str,
    args: dict[str, Any],
    *,
    session: Session,
    timeout_s: float,
    calls: list[Any] | None = None,
) -> str:
    """Execute one tool call, or refuse it. Never raises to the caller — a failure is returned
    as text the assistant can read aloud, because a traceback is not an answer."""
    from app.providers.base import ToolCall

    name = registry.normalise_tool_name(tool_name)
    decision = classify(name, args, session.issued_ids)
    log.info(
        "tool=%s tier=%s disposition=%s args=%s",
        name, decision.tier.value, decision.disposition.value, sorted(args) if args else [],
    )

    if decision.disposition is Disposition.DENY:
        refusal = session.refuse(name, args, decision.reason)
        log.warning("REFUSED tool=%s refusal=%s reason=%s", name, refusal.refusal_id, decision.reason)
        if calls is not None:
            calls.append(ToolCall(name=name, args=args, ok=False, error=decision.reason))
        return (
            f"REFUSED ({refusal.refusal_id}): {decision.reason} "
            "Tell the user plainly that you could not do this and why. Do not retry."
        )

    if decision.disposition is Disposition.STAGE_FOR_OWNER:
        return await _stage(name, args, session=session, timeout_s=timeout_s, calls=calls)

    started = time.perf_counter()
    try:
        payload = await registry.invoke(name, args, timeout_s=timeout_s)
    except _READABLE_ERRORS as exc:
        # Client errors carry a message written to be read out ("Shopify is rate-limiting
        # us"). They must reach the model intact, not as "failed unexpectedly".
        log.warning("tool=%s failed: %s", name, exc)
        if calls is not None:
            calls.append(ToolCall(name=name, args=args, ok=False, error=str(exc), duration_ms=_elapsed(started)))
        return (
            f"ERROR: {exc} Say that this lookup failed. Do not invent a result and do not "
            "report success."
        )
    except Exception as exc:  # noqa: BLE001 — a tool must never take the process down
        log.exception("tool=%s raised", name)
        if calls is not None:
            calls.append(ToolCall(name=name, args=args, ok=False, error=repr(exc), duration_ms=_elapsed(started)))
        return (
            f"ERROR: {name} failed unexpectedly ({type(exc).__name__}). Say the lookup failed. "
            "Do not invent a result."
        )

    _harvest_ids(payload, session)
    if calls is not None:
        ms = payload.get("_ms") if isinstance(payload, dict) else None
        calls.append(ToolCall(
            name=name, args=args, ok=True, duration_ms=ms,
            result=payload if isinstance(payload, dict) else None,
        ))

    text = _render(payload)
    if decision.tier is Tier.AMBER:
        text = (
            "AMBER — this result contains customer personal data. Read the identifying detail "
            "back to the user before acting on it.\n" + text
        )
    return text


async def _stage(
    name: str, args: dict[str, Any], *, session: Session, timeout_s: float, calls: list[Any] | None,
) -> str:
    """A write: the handler prepares the exact change from a fresh read and nothing is sent.
    The proposal waits on the session for the owner's tap; the model is told it is waiting."""
    from app.actions.engine import current as current_engine
    from app.providers.base import ToolCall

    spec = registry.get(name)
    try:
        prepared = await registry.invoke(name, args, timeout_s=timeout_s)
    except _READABLE_ERRORS as exc:
        log.warning("tool=%s could not be prepared: %s", name, exc)
        if calls is not None:
            calls.append(ToolCall(name=name, args=args, ok=False, error=str(exc)))
        return f"ERROR: {exc} Say that this could not be prepared. Nothing was changed."
    except Exception as exc:  # noqa: BLE001
        log.exception("tool=%s raised while preparing", name)
        if calls is not None:
            calls.append(ToolCall(name=name, args=args, ok=False, error=repr(exc)))
        return f"ERROR: {name} could not be prepared ({type(exc).__name__}). Nothing was changed."
    if not isinstance(prepared, Prepared):
        if calls is not None:
            calls.append(ToolCall(name=name, args=args, ok=False, error="handler did not prepare a change"))
        return f"ERROR: {name} did not prepare a change. Nothing was changed."

    proposal, created = current_engine().stage(session, spec, args, prepared)
    if calls is not None:
        calls.append(ToolCall(name=name, args=args, ok=True, proposal_id=proposal.proposal_id))
    log.info(
        "PROPOSED tool=%s proposal=%s entity=%s new=%s", name, proposal.proposal_id, proposal.entity_label, created,
    )
    label = f"{spec.write.entity_kind} {proposal.entity_label}".strip() if spec.write else proposal.entity_label
    if created:
        return (
            f"PROPOSED ({proposal.proposal_id}): the change to {label} is prepared and waiting for "
            "the owner to apply it by tapping the card on the tablet. It has NOT happened. Tell the "
            "owner it is ready to tap. Do not say it was done, do not ask for a spoken yes (a spoken "
            "yes cannot apply it), and do not call this tool again for the same change."
        )
    return (
        f"PROPOSED ({proposal.proposal_id}): this same change is already waiting on the tablet. "
        "It has NOT happened. Tell the owner to tap the card that is already showing. Do not call "
        "this tool again."
    )


def _elapsed(started: float) -> float:
    return round((time.perf_counter() - started) * 1000, 1)


def make_pretooluse_hook(session_getter, on_event=None):
    """Build the Agent SDK PreToolUse hook.

    The hook exists because auto-approved tools never reach `can_use_tool`, which is exactly how
    a permission gate ends up logging nothing and blocking nothing. This fires on every call.
    """

    async def hook(input_data: dict[str, Any], tool_use_id: str | None, context: Any):
        raw_name = input_data.get("tool_name", "")
        name = registry.normalise_tool_name(raw_name)
        args = input_data.get("tool_input", {}) or {}
        session = session_getter()
        decision = classify(name, args, session.issued_ids if session else ())
        log.info("PreToolUse tool=%s tier=%s disposition=%s", name, decision.tier.value, decision.disposition.value)
        if on_event is not None:
            on_event(name, decision.tier.value, decision.disposition.value)
        if decision.disposition is Disposition.DENY:
            if session is not None:
                session.refuse(name, args, decision.reason)
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": decision.reason,
                }
            }
        return {}

    return hook
