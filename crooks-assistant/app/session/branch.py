"""Branch state: where the conversation is, per branch of it.

The tablet's orb can divide in two (app/routes/branches.py). Each half is a branch: its own
current entity, working set, workflow and cursor, navigation stack, selected tab and scroll
position, its own recent reads and its own pending changes. What they share is only what is
safe to share — the read caches (app/memory), the source clients, the issued-id ledger — and
never a mutable position, a proposal or an approval.

The point of holding this is speed. "Next" is a cursor increment and one read of a member
the Mac already knows the id of; it is not a question for the model. Nothing here is a
permission: the gate reads `Session.issued_ids`, which is not branch state.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Any

# Two branches at most. The orb divides once; it does not become a window manager.
MAX_BRANCHES = 2
# Entities, results and actions kept per branch. A tablet screen shows a handful; the rest is
# memory that would go stale before it was read.
MAX_RECENT = 8
MAX_NAV = 12
# How a resolution ("Millie Rogers" -> customer_id) stands before it is looked up again.
RESOLUTION_TTL_S = 900.0
MAX_RESOLUTIONS = 60


def new_branch_id() -> str:
    return f"br_{os.urandom(5).hex()}"


@dataclass(slots=True)
class Workflow:
    """A thing being worked through, member by member: a working set and a position in it.

    `operation` is what is being done at each stop ("review", "reply", "check") and is
    presentation only — a workflow never applies anything. Advancing the cursor is what
    "Next" means, and it is arithmetic, not reasoning.
    """

    workflow_id: str
    set_id: str
    kind: str
    operation: str = "review"
    cursor: int = 0
    total: int = 0
    started_at: float = field(default_factory=time.time)
    # Members already visited, by ref, so "back" and "next" agree about where they have been.
    visited: list[str] = field(default_factory=list)

    @property
    def position(self) -> int:
        """The cursor as a person counts: one-based, never past the end, and zero before the
        first "Next" has landed on anything (the cursor starts at -1, waiting)."""
        if not self.total or self.cursor < 0:
            return 0
        return min(self.cursor + 1, self.total)

    def at_end(self) -> bool:
        return self.total > 0 and self.cursor >= self.total - 1

    def at_start(self) -> bool:
        return self.cursor <= 0

    def public(self) -> dict[str, Any]:
        return {
            "workflow_id": self.workflow_id, "set_id": self.set_id, "kind": self.kind,
            "operation": self.operation, "position": self.position, "total": self.total,
            "at_end": self.at_end(), "at_start": self.at_start(),
        }


@dataclass(slots=True)
class NavEntry:
    """One stop on the branch's back stack. Holds what it takes to put the screen back as it
    was — which entity, which tab, how far down — never the rendered cards themselves."""

    entry_id: str
    kind: str
    ref: str
    label: str
    tab: str = ""
    scroll: int = 0
    set_id: str = ""
    at: float = field(default_factory=time.time)

    def public(self) -> dict[str, Any]:
        return {"entry_id": self.entry_id, "kind": self.kind, "ref": self.ref, "label": self.label,
                "tab": self.tab, "scroll": self.scroll, "set_id": self.set_id}


@dataclass(slots=True)
class Branch:
    """One half of the conversation. Created on demand; the first is made with the session."""

    branch_id: str
    session_id: str = ""
    parent_id: str = ""
    # ACTIVE (the owner is talking to it), BACKGROUND (it is working while he is elsewhere),
    # MERGED or CANCELLED (it is over). A background branch never commits a change: see
    # app/actions/engine.py, which refuses a commit whose branch is not the focused one.
    status: str = "ACTIVE"
    label: str = ""
    created_at: float = field(default_factory=time.time)

    # Where the branch is.
    entity: dict[str, str] | None = None          # {"kind","ref","label"}
    set_id: str = ""                               # the working set "these" means here
    workflow: Workflow | None = None
    nav: list[NavEntry] = field(default_factory=list)
    nav_index: int = -1
    tab: str = ""
    scroll: int = 0
    # Rows opened in place on the current surface, by ref. Branch state rather than something
    # only the DOM knows, so a Back that returns here returns to the same shape of screen, and
    # a half put aside keeps its own.
    expanded: list[str] = field(default_factory=list)

    # What it has seen, most recent first.
    recent_entities: list[dict[str, str]] = field(default_factory=list)
    recent_results: list[dict[str, Any]] = field(default_factory=list)
    recent_actions: list[dict[str, Any]] = field(default_factory=list)
    # name (as said) -> {"kind","ref","label","at"}. A resolution, not a permission.
    resolutions: dict[str, dict[str, Any]] = field(default_factory=dict)

    # Work running for this branch that the owner is not waiting on. Semantic states only:
    # QUEUED, WORKING, WAITING, READY, FAILED — never a percentage nobody can compute,
    # because nothing here can compute one honestly.
    task: dict[str, Any] | None = None

    # ------------------------------------------------------------------ work

    def working(self, what: str, *, clock=time.time) -> None:
        """This branch has taken on a piece of work. `what` is a short phrase in the owner's
        words — never a tool name, never the model's reasoning."""
        self.task = {"state": "WORKING", "what": str(what)[:80], "since": clock()}

    def waiting(self, what: str = "", *, clock=time.time) -> None:
        """Working, but on something outside the Mac: a source that has not answered yet."""
        self.task = {"state": "WAITING", "what": str(what or (self.task or {}).get("what") or "")[:80], "since": clock()}

    def ready(self, what: str = "", *, clock=time.time) -> None:
        """There is an answer here whenever the owner wants it. This is what makes the
        background half pulse; it never takes his attention (app/routes/branches.py)."""
        self.task = {"state": "READY", "what": str(what or (self.task or {}).get("what") or "")[:80], "since": clock()}

    def failed(self, why: str, *, clock=time.time) -> None:
        self.task = {"state": "FAILED", "what": str(why)[:80], "since": clock()}

    def idle(self) -> None:
        self.task = None

    # ------------------------------------------------------------- navigation

    def visit(self, kind: str, ref: str, label: str, *, tab: str = "", set_id: str = "") -> NavEntry:
        """Go somewhere. Truncates any forward history, as a browser does."""
        if self.nav_index >= 0:
            del self.nav[self.nav_index + 1 :]
        entry = NavEntry(entry_id=f"nav_{os.urandom(4).hex()}", kind=kind, ref=str(ref), label=str(label)[:80], tab=tab, set_id=set_id or self.set_id)
        self.nav.append(entry)
        del self.nav[:-MAX_NAV]
        self.nav_index = len(self.nav) - 1
        self.entity = {"kind": kind, "ref": str(ref), "label": str(label)[:80]}
        self.tab = tab
        self.scroll = 0
        self.remember_entity(kind, ref, label)
        return entry

    def back(self) -> NavEntry | None:
        if self.nav_index <= 0:
            return None
        self.nav_index -= 1
        return self._land()

    def forward(self) -> NavEntry | None:
        if self.nav_index < 0 or self.nav_index >= len(self.nav) - 1:
            return None
        self.nav_index += 1
        return self._land()

    def _land(self) -> NavEntry:
        entry = self.nav[self.nav_index]
        self.entity = {"kind": entry.kind, "ref": entry.ref, "label": entry.label}
        self.tab = entry.tab
        self.scroll = entry.scroll
        self.set_id = entry.set_id or self.set_id
        return entry

    def mark(self, *, tab: str | None = None, scroll: int | None = None) -> None:
        """The screen moved. Kept on the current stack entry so going back restores it."""
        if tab is not None:
            self.tab = str(tab)[:40]
        if scroll is not None:
            self.scroll = max(0, int(scroll))
        if 0 <= self.nav_index < len(self.nav):
            entry = self.nav[self.nav_index]
            if tab is not None:
                entry.tab = self.tab
            if scroll is not None:
                entry.scroll = self.scroll

    # ---------------------------------------------------------------- memory

    def remember_entity(self, kind: str, ref: str, label: str) -> None:
        if not (kind and ref):
            return
        ref = str(ref)
        self.recent_entities = [e for e in self.recent_entities if not (e["kind"] == kind and e["ref"] == ref)]
        self.recent_entities.insert(0, {"kind": kind, "ref": ref, "label": str(label or "")[:80]})
        del self.recent_entities[MAX_RECENT:]

    def remember_result(self, tool: str, *, summary: str, ref: str = "", ms: float = 0.0, cached: bool = False) -> None:
        """A compact note of a read, not the read. What goes to the model later is this line;
        the whole result stays on the Mac (app/memory)."""
        self.recent_results.insert(0, {"tool": tool, "summary": str(summary)[:200], "ref": str(ref)[:80], "ms": round(ms, 1), "cached": bool(cached), "at": time.time()})
        del self.recent_results[MAX_RECENT:]

    def remember_action(self, proposal_id: str, operation: str, status: str, *, spoken: str = "") -> None:
        self.recent_actions = [a for a in self.recent_actions if a["proposal_id"] != proposal_id]
        self.recent_actions.insert(0, {"proposal_id": proposal_id, "operation": operation, "status": status, "spoken": str(spoken)[:200], "at": time.time()})
        del self.recent_actions[MAX_RECENT:]

    def resolve(self, said: str, *, clock=time.time) -> dict[str, Any] | None:
        """What this branch already knows a name means, if it still stands."""
        key = _resolution_key(said)
        found = self.resolutions.get(key)
        if not found:
            return None
        if clock() - float(found.get("at") or 0) > RESOLUTION_TTL_S:
            self.resolutions.pop(key, None)
            return None
        return found

    def learn(self, said: str, kind: str, ref: str, label: str, *, clock=time.time) -> None:
        key = _resolution_key(said)
        if not key or not ref:
            return
        self.resolutions[key] = {"kind": kind, "ref": str(ref), "label": str(label or "")[:80], "at": clock()}
        if len(self.resolutions) > MAX_RESOLUTIONS:
            for old in sorted(self.resolutions, key=lambda k: self.resolutions[k]["at"])[: len(self.resolutions) - MAX_RESOLUTIONS]:
                self.resolutions.pop(old, None)

    # ----------------------------------------------------------------- shape

    def public(self) -> dict[str, Any]:
        return {
            "branch_id": self.branch_id, "parent_id": self.parent_id or None, "status": self.status,
            "label": self.label, "entity": self.entity, "set_id": self.set_id or None,
            "workflow": self.workflow.public() if self.workflow else None,
            "tab": self.tab or None, "scroll": self.scroll, "expanded": list(self.expanded),
            "can_back": self.nav_index > 0, "can_forward": 0 <= self.nav_index < len(self.nav) - 1,
            "depth": max(0, self.nav_index), "recent": list(self.recent_entities[:4]),
            "task": dict(self.task) if self.task else None,
        }


def _resolution_key(said: str) -> str:
    return " ".join(str(said or "").lower().split())[:60]
