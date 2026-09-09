"""Where the existing records feed the timeline: the action ledger's lines become action
events, with the proposal's own turn, gesture and risk beside them."""

from __future__ import annotations

from typing import Any

from app.observability import timeline


def ledger_observer(entry: dict[str, Any], proposal: Any) -> None:
    """Every ledger line, as an `action_<event>` timeline event. Called by the ledger after
    the line is on disk; nothing here is on the tap's path but a queue put."""
    if timeline.current().active is None:
        return
    event = str(entry.get("event") or "").lower()
    if entry.get("batch_id") and not entry.get("proposal_id"):
        counts = entry.get("counts") if isinstance(entry.get("counts"), dict) else None
        timeline.emit(
            f"batch_{event}", session_id=entry.get("session_id"), turn_id=getattr(proposal, "turn_id", "") or None,
            batch_id=entry.get("batch_id"), event=str(entry.get("event") or ""), operation=entry.get("operation"), tool=entry.get("tool"),
            child_tool=entry.get("child_tool"), risk=entry.get("risk"), interaction=entry.get("interaction"), set_id=entry.get("set_id"),
            set_kind=entry.get("set_kind"), requested=entry.get("requested"), eligible=entry.get("eligible"), excluded=entry.get("excluded"),
            children=len(entry.get("children") or []), status=entry.get("status"), code=entry.get("code"), counts=counts,
            reason=entry.get("reason"), ms=entry.get("ms"), undo_of=entry.get("undo_of"), caller_present=bool(entry.get("caller")), epoch=entry.get("epoch"),
        )
        return
    timeline.emit(
        f"action_{event}",
        session_id=entry.get("session_id"),
        turn_id=getattr(proposal, "turn_id", "") or None,
        proposal_id=entry.get("proposal_id"),
        event=str(entry.get("event") or ""),
        operation=entry.get("operation"),
        tool=entry.get("tool"),
        risk=entry.get("risk"),
        interaction=getattr(proposal, "interaction", None),
        reversible=getattr(proposal, "reversible", None),
        entity_kind=entry.get("entity_kind"),
        entity_label=entry.get("entity_label"),
        status=entry.get("status"),
        code=entry.get("code"),
        verified=entry.get("verified"),
        reason=entry.get("reason"),
        detail=entry.get("detail"),
        ms=entry.get("ms"),
        undo_of=entry.get("undo_of"),
        batch_id=entry.get("batch_id"),
        caller_present=bool(entry.get("caller")),
        epoch=entry.get("epoch"),
    )
