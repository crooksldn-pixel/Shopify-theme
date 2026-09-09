"""Working sets: the exact things a listing found, held on the Mac under a short id, so
"these", "those" and "all of them" mean precisely what was shown — not a re-run of the
search, not a list of ids passed through the model.

A set is immutable: its members never change. A narrowing makes a new set that remembers
its parent and the step that made it, so a batch proposal, later, can say exactly which set
it acts on and how that set came to be. Sets belong to one conversation, expire when it
goes quiet, and are few: the newest twelve are kept."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Any

KINDS = ("orders", "customers", "products", "variants", "emails")
MAX_SETS = 12
MAX_MEMBERS = 500
MAX_SAMPLE = 5
TTL_S = 1800.0


def new_set_id() -> str:
    return f"set_{os.urandom(6).hex()}"


@dataclass(frozen=True, slots=True)
class WorkingSet:
    set_id: str
    kind: str
    members: tuple[str, ...]
    label: str
    created_at: float
    expires_at: float
    session_id: str
    turn_id: str
    provenance: dict[str, Any] = field(default_factory=dict)   # tool, query, parent, step
    sample: tuple[dict[str, Any], ...] = ()
    totals: dict[str, Any] = field(default_factory=dict)
    truncated: bool = False

    @property
    def count(self) -> int:
        return len(self.members)

    @property
    def parent(self) -> str | None:
        return self.provenance.get("parent")

    @property
    def step(self) -> str:
        return str(self.provenance.get("step") or "query")

    def public(self) -> dict[str, Any]:
        """What the model and the tablet are told: the id, the kind, the count, the label, a
        few members by name — never the whole membership."""
        return {
            "set_id": self.set_id, "kind": self.kind, "count": self.count, "label": self.label, "sample": list(self.sample),
            "parent": self.parent, "parent_label": self.provenance.get("parent_label"), "step": self.step, "truncated": self.truncated, "totals": dict(self.totals),
            "expires_in_s": max(0, int(self.expires_at - time.time())),
        }


def _held(session: Any) -> dict[str, WorkingSet]:
    sets = getattr(session, "sets", None)
    if not isinstance(sets, dict):
        sets = {}
        try:
            session.sets = sets
        except AttributeError:
            pass
    return sets


def create(
    session: Any, *, kind: str, members: list[str], label: str, provenance: dict[str, Any] | None = None,
    sample: list[dict[str, Any]] | None = None, totals: dict[str, Any] | None = None, clock=time.time,
) -> WorkingSet:
    """A new set on the session, its ids issued to the conversation, the newest first."""
    if kind not in KINDS:
        raise ValueError(f"unknown set kind {kind!r}")
    now = clock()
    prune(session, now)
    ids = list(dict.fromkeys(str(m) for m in members if m))
    truncated = len(ids) > MAX_MEMBERS
    ids = ids[:MAX_MEMBERS]
    ws = WorkingSet(
        set_id=new_set_id(), kind=kind, members=tuple(ids), label=" ".join(str(label or "").split())[:80] or kind,
        created_at=now, expires_at=now + TTL_S, session_id=str(getattr(session, "session_id", "") or ""), turn_id=str(getattr(session, "turn_id", "") or ""),
        provenance=dict(provenance or {}), sample=tuple({"ref": str(s.get("ref") or ""), "label": str(s.get("label") or "")[:60]} for s in (sample or [])[:MAX_SAMPLE]),
        totals={k: v for k, v in (totals or {}).items() if isinstance(v, (int, float, str)) and not isinstance(v, bool)}, truncated=truncated,
    )
    held = _held(session)
    held[ws.set_id] = ws
    while len(held) > MAX_SETS:
        oldest = min(held.values(), key=lambda s: s.created_at)
        del held[oldest.set_id]
    issue = getattr(session, "issue", None)
    if callable(issue):
        issue(ws.set_id, *ids)
    focus = getattr(session, "focus", None)
    if isinstance(focus, dict):
        focus["set"] = ws.set_id
    return ws


def derive(session: Any, parent: WorkingSet, *, members: list[str], label: str, step: str, detail: dict[str, Any] | None = None, kind: str | None = None, clock=time.time, **extra: Any) -> WorkingSet:
    """A narrowing (or a correlation) of a set: a new set that remembers where it came from."""
    return create(
        session, kind=kind or parent.kind, members=members, label=label, clock=clock,
        provenance={"tool": (detail or {}).get("tool") or "", "parent": parent.set_id, "parent_label": parent.label, "step": step, "detail": dict(detail or {})}, **extra,
    )


def get(session: Any, set_id: str, *, clock=time.time) -> WorkingSet | None:
    """The set, if the conversation still holds it; asking for it keeps it a while longer."""
    now = clock()
    prune(session, now)
    held = _held(session)
    ws = held.get(str(set_id or ""))
    if ws is None:
        return None
    if ws.expires_at - now < TTL_S / 2:
        ws = WorkingSet(**{**_fields(ws), "expires_at": now + TTL_S})
        held[ws.set_id] = ws
    return ws


def latest(session: Any, *, kind: str | None = None) -> WorkingSet | None:
    held = _held(session)
    candidates = [s for s in held.values() if kind is None or s.kind == kind]
    # Ties on the clock go to the set made last (dict order is insertion order).
    return max(reversed(candidates), key=lambda s: s.created_at) if candidates else None


def prune(session: Any, now: float | None = None) -> None:
    now = time.time() if now is None else now
    held = _held(session)
    for set_id, ws in list(held.items()):
        if ws.expires_at <= now:
            del held[set_id]
    focus = getattr(session, "focus", None)
    if isinstance(focus, dict) and focus.get("set") and focus["set"] not in held:
        focus.pop("set", None)


def members_by_id(session: Any) -> dict[str, frozenset[str]]:
    return {set_id: frozenset(ws.members) for set_id, ws in _held(session).items()}


def _fields(ws: WorkingSet) -> dict[str, Any]:
    return {name: getattr(ws, name) for name in WorkingSet.__slots__}   # type: ignore[attr-defined]


def prompt_line(session: Any, *, clock=time.time) -> str:
    """What the model is told at the top of a turn about the set in focus: one line."""
    ws = None
    focus = getattr(session, "focus", None)
    if isinstance(focus, dict) and focus.get("set"):
        ws = get(session, focus["set"], clock=clock)
    if ws is None:
        ws = latest(session)
    if ws is None:
        return ""
    return (
        f'[Working set {ws.set_id}: {ws.count} {ws.kind} — "{ws.label}". "These", "those", "them" and "all of them" mean exactly these; '
        f'pass filters.in_set = "{ws.set_id}" to narrow or total them, and set_id = "{ws.set_id}" to act on them.]'
    )
