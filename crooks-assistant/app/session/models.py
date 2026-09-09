"""Session state: what the assistant is currently talking about, and what it is allowed to
look up. The issued-id ledger is a security control, not a convenience — see app/tools/gate.py.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.actions.models import ActionProposal


@dataclass(slots=True)
class Refusal:
    """A tool call the gate denied. Recorded so the log shows what was attempted. Never
    executable: a refusal has no proposal, no arguments to run and no path to Shopify."""

    refusal_id: str
    tool_name: str
    args: dict[str, Any]
    reason: str
    created_at: float = field(default_factory=time.time)


@dataclass(slots=True)
class Session:
    session_id: str
    created_at: float = field(default_factory=time.time)
    last_seen_at: float = field(default_factory=time.time)

    # Ids handed to the assistant by a search result this session. Detail-style tools accept
    # nothing else, so the assistant cannot look up a record it was never shown.
    issued_ids: set[str] = field(default_factory=set)

    # Whose conversation this is: the Tailscale login that started it, or "local" for one
    # started on the Mac itself. A session id is a bearer the tablet made up; this is what
    # stops another login on the tailnet using it. Empty only for a session made outside a
    # request (tests), which binds to the first caller.
    login: str = ""

    # What "that order" / "that customer" currently refers to, for conversational follow-ups.
    focus: dict[str, str] = field(default_factory=dict)

    turns: int = 0
    # The conversation's position. Advanced by every new instruction from the owner; a
    # proposal is bound to the epoch it was staged in and dies when the epoch moves on.
    epoch: int = 0
    # Changes the assistant proposed this session, waiting for or settled by the owner.
    proposals: list[ActionProposal] = field(default_factory=list)
    # Calls the gate denied. Kept apart from proposals: a refusal can never be authorised.
    refusals: list[Refusal] = field(default_factory=list)

    # Personal strings tool results exposed this session (customer names, sender addresses).
    # The turn log scrubs these from the free-text answer and question before writing, so a
    # name Claude reads aloud never lands on disk.
    pii_seen: set[str] = field(default_factory=set)

    # What the assistant is doing right now, driven by the tool actually executing — never
    # guessed from the question. The tablet polls this during a turn (M11).
    state: str = "READY"
    state_detail: str = ""
    # The question as transcribed, for the tablet to show while the answer is being worked out.
    heard: str = ""
    # Set by /cancel while a turn is in flight: the owner has moved on. The turn still ends,
    # but its answer is not synthesised for a tablet that will never ask for it.
    abandoned: bool = False
    # Why a tap from the tablet asking this turn would be refused, if it would: set by /turn
    # before the model runs, so a change proposed while changes are off is never announced as
    # something to tap. Empty when a tap would work.
    writes_blocked: str = ""

    # An order's full read started beside the model by /turn (app/routes/turn.py); collected
    # by the same turn when it lands in time, dropped otherwise. Never awaited by a turn.
    hydrating: Any = None
    # The turn being answered (turn_…), for the test-session timeline: every tool call and
    # every proposal made while it runs is written against it. Empty between turns.
    turn_id: str = ""
    # The turn's reading plan (app/analytics/plan.py): how many queries it has run, at what
    # cost, and their answers, so the same query is not run twice.
    plan: Any = None
    # The working sets this conversation holds (app/analytics/sets.py): what "these" means.
    sets: dict[str, Any] = field(default_factory=dict)

    # The entities this conversation has touched — an order, a customer, an email thread, a
    # product — most recent first. Presentation state for the tablet's context stack and
    # nothing else: no permission decision reads it (that is issued_ids, above).
    context: list[dict[str, str]] = field(default_factory=list)

    def set_state(self, state: str, detail: str = "") -> None:
        self.state = state
        self.state_detail = detail
        self.touch()

    def touch(self) -> None:
        self.last_seen_at = time.time()

    def idle_s(self) -> float:
        return time.time() - self.last_seen_at

    def remember_pii(self, *values: str) -> None:
        for value in values:
            value = (value or "").strip()
            if len(value) >= 3:
                self.pii_seen.add(value)

    def issue(self, *ids: str) -> None:
        for value in ids:
            if value:
                self.issued_ids.add(str(value))

    def refuse(self, tool_name: str, args: dict[str, Any], reason: str) -> Refusal:
        refusal = Refusal(
            refusal_id=f"ref_{uuid.uuid4().hex[:12]}",
            tool_name=tool_name,
            args=dict(args or {}),
            reason=reason,
        )
        self.refusals.append(refusal)
        del self.refusals[:-50]
        return refusal

    def stage(self, proposal: ActionProposal) -> ActionProposal:
        """Hold a staged proposal. Only the action engine builds one (app/actions/engine.py);
        the session is where it lives so that it goes when the session goes."""
        self.proposals.append(proposal)
        del self.proposals[:-50]
        return proposal

    def proposal(self, proposal_id: str) -> ActionProposal | None:
        for candidate in self.proposals:
            if candidate.proposal_id == proposal_id:
                return candidate
        return None

    def remember_context(self, kind: str, label: str, ref: str, *, limit: int = 6) -> None:
        """Bring an entity to the front of the context stack (or add it), keeping the stack
        short: six entries is already more than a screen can usefully show."""
        if not (kind and label and ref):
            return
        ref = str(ref)
        self.context = [c for c in self.context if not (c["kind"] == kind and c["ref"] == ref)]
        self.context.insert(0, {"kind": kind, "label": str(label)[:80], "ref": ref})
        del self.context[limit:]

    def set_focus(self, kind: str, value: str) -> None:
        if value:
            self.focus[kind] = str(value)
