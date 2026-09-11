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
# The five words a half's state can be, and the only five. ACTIVE means the owner can talk to
# it and nothing is running; the other four are what it is doing. There is no percentage here
# and there never will be: nothing on the Mac can compute one honestly, and a bar that guesses
# is a lie drawn to two decimal places.
BRANCH_STATES = ("ACTIVE", "WORKING", "WAITING", "READY", "FAILED")
# What a half is showing, in one word, from the cards it presented. The tablet draws this as
# that half's header. The Phase 3 live test recorded the owner tapping between two halves six
# times in nine seconds looking for the difference, then saying "it just shows two of the same
# thing" — because nothing on either screen said which half it was.
AREA_OF_CARD = {
    "order": "ORDER", "order_list": "ORDERS", "attention": "ORDERS",
    "customer": "CUSTOMER", "customer_list": "CUSTOMERS",
    "email_list": "INBOX", "email_queue": "INBOX", "work_queue": "INBOX",
    "email_thread": "EMAIL", "email_draft": "DRAFT", "email_compose": "DRAFT", "reply_state": "EMAIL",
    "sales_summary": "SALES", "metric_group": "SALES", "trend": "SALES", "comparison": "SALES",
    "ranking": "PRODUCTS", "product": "PRODUCT", "variant_matrix": "PRODUCT", "variant_picker": "PRODUCT",
    "inventory": "STOCK", "working_set": "LIST", "capability": "SYSTEM", "workspace": "BUILDING",
    "batch_action": "BATCH", "batch_result": "BATCH",
}
# And the same from the record the half is on, which is the better evidence when the two
# disagree: the entity is where the branch IS, the cards are what it last drew.
AREA_OF_KIND = {
    "order": "ORDER", "customer": "CUSTOMER", "email_thread": "EMAIL",
    "product": "PRODUCT", "variant": "PRODUCT", "draft": "DRAFT", "set": "LIST",
}


def area_of(ui: list[dict[str, Any]] | None) -> str:
    """The one-word area a screenful of cards is about. The first card that names one wins."""
    for item in ui or []:
        if isinstance(item, dict):
            area = AREA_OF_CARD.get(str(item.get("type") or ""))
            if area:
                return area
    return ""
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
    # What a person calls this set. The tablet's set chip — the thing on screen that says what
    # "these" currently means — used to read it off a `working_set` CARD, so the chip only
    # changed when a card happened to be drawn. It now comes from here, with the rest of the
    # branch, which is the only copy that is always right.
    label: str = ""
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
            "label": self.label,
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
    # This half's own count of instructions. A turn records it when it starts and a tool
    # call compares (app/providers/max_agent_sdk.py): a later instruction to THIS half means
    # the turn is answering a replaced question and its calls act for nobody — while an
    # instruction to the other half, which also moves the session's epoch, means nothing
    # here. Without it the two halves could not think at once: the right half's question
    # refused every tool call the left half was still making.
    instruction_seq: int = 0
    # A /cancel aimed at this half. Read where the session-wide flag is read; set only by
    # a cancel that names the half, so a cancel on the left never silences the right.
    abandoned: bool = False
    # Turns actually running on this half, counted up when one begins and down when it ends.
    # `state()` reads it, and it is the whole of why WORKING is a fact rather than a leftover:
    # a task dictionary saying WORKING is only a note somebody wrote, and a half whose turn
    # died would have gone on saying "working" for as long as the conversation lasted.
    in_flight: int = 0
    # What this half received when the orb divided, kept so a refusal can say what it has to
    # work with instead of leaving the owner with a dead control (see `holds`).
    inherited: dict[str, Any] | None = None
    # The one-word area this half last drew (AREA_OF_CARD). Presentation, and the header the
    # tablet puts on this half so two halves are never indistinguishable.
    area: str = ""

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
    # What the next thing said applies to, when the owner tapped a control that expects words.
    # Tapping Rewrite on a draft binds the draft here and starts listening, so "make it shorter
    # and more apologetic" lands on that draft without the owner naming it again. Held on the
    # BRANCH, never on the session: a continuation armed on one half of the orb must not catch
    # a sentence spoken to the other. It expires, because a binding the owner has forgotten
    # about is a sentence applied to the wrong thing.
    voice_context: dict[str, Any] | None = None
    # An email being composed on this half (app/families/compose.py): who it is to, what it
    # is about, the words so far, and the status of each field. Held here and NOWHERE else,
    # because it is the Mac's copy of a change that has not been prepared yet: the tablet
    # posts a compose id and a typed value, and the execution arguments are built from THIS
    # dictionary when the owner's gesture asks for them. A composer is one half's, like every
    # other position — an email started on the left is not what "send it" means on the right.
    compose: dict[str, Any] | None = None
    # A structured workspace being filled on this half (app/families/_workspace.py): the
    # discount code being written, the order being built, the credit being decided. The same
    # thing the composer is and for the same reason — the Mac's copy of a change nobody has
    # proposed yet — and one at a time per half, because the execution arguments are built
    # from THIS dictionary when a gesture asks for them and the owner is looking at one card.
    workspace: dict[str, Any] | None = None

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

    # What this half last put on the screen: the cards as presented (bounded), the sentence,
    # and the question they answered. Held so that tapping a half SHOWS that half — the Phase
    # 2 live test found that tapping the other half changed who was listening and nothing
    # visible — and so that a reload, or a half put aside that has since finished, can be drawn
    # from the Mac's copy rather than from a browser cache. Presentation data only: it has
    # already been sent to the tablet once, and it stages nothing.
    last_ui: list[dict[str, Any]] = field(default_factory=list)
    last_answer: str = ""
    last_question: str = ""
    last_at: float = 0.0

    def shown(self, ui: list[dict[str, Any]], answer: str, question: str, *, clock=time.time) -> None:
        """The screen this half now has. Cards only (never the context stack, which the
        tablet keeps for itself), at most six, and never an error card standing in for a
        record the branch still holds."""
        kept = [u for u in (ui or []) if isinstance(u, dict) and u.get("type") not in ("context_stack",)]
        if kept or not self.last_ui:
            self.last_ui = kept[:6]
            self.area = area_of(kept) or self.area
        self.last_answer = str(answer or "")[:400]
        self.last_question = str(question or "")[:200]
        self.last_at = clock()

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

    def begin_turn(self, what: str, *, clock=time.time) -> None:
        """A turn has started on this half. The counter is what makes WORKING true rather
        than merely written down; `working()` on its own says nothing about whether anything
        is still running."""
        self.in_flight += 1
        self.working(what, clock=clock)

    def end_turn(self) -> None:
        """It has stopped, however it stopped — answered, refused, timed out, abandoned."""
        self.in_flight = max(0, self.in_flight - 1)

    def state(self) -> str:
        """This half, in one of five words (BRANCH_STATES).

        READY and FAILED are outcomes and stand on their own. WORKING and WAITING are claims
        about right now, so they are only said while a turn is actually in flight here: a task
        left saying WORKING by a turn that died reads ACTIVE, which is what it is.
        """
        named = str((self.task or {}).get("state") or "")
        if named in ("READY", "FAILED"):
            return named
        if self.in_flight <= 0:
            return "ACTIVE"
        return "WAITING" if named in ("WAITING", "QUEUED") else "WORKING"

    def headline(self) -> dict[str, str]:
        """What this half IS, in a line the tablet draws on it: "ORDER · #1957", "INBOX · READY".

        Never two indistinguishable halves — this is the difference the owner could not find.
        It is built here, on the Mac, from branch state, so both ends say the same thing and
        the tablet invents none of it.
        """
        entity = self.entity or {}
        area = AREA_OF_KIND.get(str(entity.get("kind") or ""), "") or self.area
        state = self.state()
        detail = str(entity.get("label") or "").strip()
        if not detail and self.workflow is not None:
            detail = str(self.workflow.label or "").strip()
        if not area:
            area = "WORKSPACE" if (self.last_ui or self.last_answer) else "EMPTY"
        if not detail:
            detail = "nothing yet" if area == "EMPTY" and state == "ACTIVE" else state
        detail = detail[:40]
        return {"area": area, "detail": detail, "state": state, "title": f"{area} · {detail}"}

    def holds(self) -> dict[str, Any]:
        """What this half has to work with, said plainly.

        The forked half in the Phase 3 live session was refused `landing_unavailable` and then
        `not_held`, and neither refusal told the owner what the half DID have or what to do
        next. A refusal he cannot act on is a dead control, so every refusal that can reach a
        divided orb carries this.
        """
        return {
            "entity": dict(self.entity) if self.entity else None,
            "set_id": self.set_id or "",
            "recent": [dict(e) for e in self.recent_entities[:4]],
            "from": self.parent_id or "",
            "state": self.state(),
        }

    # ------------------------------------------------------------- navigation

    def visit(self, kind: str, ref: str, label: str, *, tab: str = "", set_id: str = "") -> NavEntry:
        """Go somewhere. Truncates any forward history, as a browser does.

        Asking about the record you are already on is not going anywhere, so it does not push a
        stop. Every read calls this (`app/fastpath/library.py:_remember`), so three questions
        about one order used to leave three identical entries on the trail — and Back then
        landed on the same record, on the same tab, and said the same sentence, which is a
        button that visibly does nothing. The owner has no way to tell that from a Back that
        failed.
        """
        current = self.nav[self.nav_index] if 0 <= self.nav_index < len(self.nav) else None
        if current is not None and current.kind == kind and current.ref == str(ref) and current.tab == tab:
            current.set_id = set_id or self.set_id
            self.entity = {"kind": kind, "ref": str(ref), "label": str(label)[:80]}
            self.scroll = 0
            self.remember_entity(kind, ref, label)
            return current
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

    # How long a tapped control waits for the words that go with it. Long enough to think of
    # the sentence, short enough that a tap made and abandoned does not catch the next question.
    VOICE_CONTEXT_TTL_S = 120.0

    def bind_voice(self, family: str, *, kind: str = "", ref: str = "", label: str = "",
                   prompt: str = "", phrase: str = "", clock=time.time) -> dict[str, Any]:
        """Arm this branch for a spoken continuation of a tapped control.

        `prompt` is what the screen should say it is waiting for — "Add a note". It is stored
        rather than looked up again so that `public()` can hand it to the tablet on every
        reply, including one that follows a reload, without importing the command table.
        """
        self.voice_context = {
            "family": family, "kind": kind, "ref": ref, "label": label, "prompt": prompt, "phrase": phrase,
            "branch_id": self.branch_id, "at": clock(),
            "expires_at": clock() + self.VOICE_CONTEXT_TTL_S,
        }
        return dict(self.voice_context)

    def voice_target(self, *, clock=time.time) -> dict[str, Any] | None:
        """What the next sentence applies to, or nothing.

        Checks the branch it was armed on as well as the clock: a context that somehow reached
        another half is not this half's, and is ignored rather than obeyed.
        """
        held = self.voice_context
        if not held:
            return None
        if held.get("branch_id") != self.branch_id or clock() >= float(held.get("expires_at") or 0):
            self.voice_context = None
            return None
        return dict(held)

    def release_voice(self) -> None:
        """One sentence, one binding. Cleared as soon as it has been used or abandoned."""
        self.voice_context = None

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
            # `status` is where the half lives (ACTIVE, BACKGROUND, MERGED, CANCELLED);
            # `state` is what it is doing, in one of five words, and it is what the chip says.
            "state": self.state(),
            # The line drawn ON this half, so tapping between two halves can never again show
            # the owner two screens he cannot tell apart.
            "headline": self.headline(),
            "label": self.label, "entity": self.entity, "set_id": self.set_id or None,
            "workflow": self.workflow.public() if self.workflow else None,
            "tab": self.tab or None, "scroll": self.scroll, "expanded": list(self.expanded),
            # What the tablet should show as the target of the next thing said, when a tapped
            # control is waiting for words.
            # The prompt and the deadline travel with it: the tablet draws a band naming what
            # it is listening for, and the band was previously drawn from the tap alone — so a
            # binding made by voice, or one surviving a reload, left the screen silent about it.
            "listening_for": ({"family": self.voice_context["family"], "label": self.voice_context.get("label", ""),
                               "prompt": self.voice_context.get("prompt", ""), "phrase": self.voice_context.get("phrase", ""),
                               "expires_at": self.voice_context.get("expires_at")}
                              if self.voice_target() else None),
            # The composer, in five fields: enough for the tablet to know one is open and
            # what it is to, never the body (that is on the card the Mac drew, and a branch
            # summary goes out with every reply).
            "compose": ({"compose_id": str(self.compose.get("compose_id") or ""),
                         "kind": str(self.compose.get("kind") or ""),
                         "to": str(self.compose.get("to") or "")[:254],
                         "subject": str(self.compose.get("subject") or "")[:120],
                         "thread_id": str(self.compose.get("thread_id") or "")}
                        if isinstance(self.compose, dict) and self.compose.get("compose_id") else None),
            # What this half is BUILDING, in two fields: which workspace and what kind of
            # thing it makes. Deliberately not its values — `has_workspace` below is about
            # whether there is a screen to redraw, and this is about whether a discount, an
            # order or a credit is half-written on this half; the values are on the card the
            # Mac drew, and a branch summary goes out with every reply.
            "building": ({"workspace_id": str(self.workspace.get("workspace_id") or ""),
                          "kind": str(self.workspace.get("kind") or "")}
                         if isinstance(self.workspace, dict) and self.workspace.get("workspace_id") else None),
            "can_back": self.nav_index > 0, "can_forward": 0 <= self.nav_index < len(self.nav) - 1,
            "depth": max(0, self.nav_index), "recent": list(self.recent_entities[:4]),
            "task": dict(self.task) if self.task else None,
            # Whether there is a screen to show for this half, and what it answered. The cards
            # themselves come through `branch.show`, on request, not with every reply.
            "has_workspace": bool(self.last_ui or self.last_answer),
            "last_question": self.last_question, "last_at": self.last_at or None,
        }


def fork_from(parent: Branch, *, label: str = "") -> Branch:
    """The orb divides. One function, so what a half inherits is one contract with one test.

    The child inherits what its parent HOLDS — the record it is on, the working set, the names
    it has already resolved, the trail of what it has looked at — and NOTHING of what its
    parent is SHOWING. That division is the whole of D-3. Cloning the parent's screen is what
    produced two identical halves; withholding what the parent held is what made `open.area`
    and `open.entity` refuse the clone with reasons its owner could not act on. So: context
    yes, presentation no, and the child says plainly that it holds nothing yet.

    Nothing that could be APPLIED crosses: no proposal, no composer, no half-written workspace,
    no armed voice binding, no task. A change belongs to the half it was asked for in.
    """
    child = Branch(
        branch_id=new_branch_id(), session_id=parent.session_id, parent_id=parent.branch_id,
        label=str(label or "").strip()[:40] or "second",
        entity=dict(parent.entity) if parent.entity else None,
        set_id=parent.set_id, tab=parent.tab,
    )
    if parent.workflow is not None:
        # The same set at the same place; advancing one cursor does not move the other.
        from dataclasses import replace

        child.workflow = replace(parent.workflow, workflow_id=f"{parent.workflow.workflow_id}b",
                                 visited=list(parent.workflow.visited))
    # What its parent had already worked out. These are resolutions and references, not
    # permissions — the gate still reads `Session.issued_ids` — and they are exactly what the
    # clone never received in the live session.
    child.recent_entities = [dict(e) for e in parent.recent_entities[:MAX_RECENT]]
    child.resolutions = {said: dict(value) for said, value in parent.resolutions.items()}
    child.inherited = {
        "from": parent.branch_id,
        "entity": dict(parent.entity) if parent.entity else None,
        "set_id": parent.set_id or "",
        "area": parent.headline()["area"],
    }
    if parent.entity:
        # Its own one-stop trail, so Back and Home have a floor of their own rather than
        # walking a stack that belongs to the other half.
        child.visit(parent.entity["kind"], parent.entity["ref"], parent.entity["label"], tab=parent.tab)
    return child


def _resolution_key(said: str) -> str:
    return " ".join(str(said or "").lower().split())[:60]
