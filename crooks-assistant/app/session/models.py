"""Session state: what the assistant is currently talking about, and what it is allowed to
look up. The issued-id ledger is a security control, not a convenience — see app/tools/gate.py.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class StagedProposal:
    """A RED tool call that was refused. Recorded so the log shows what was attempted."""

    proposal_id: str
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

    # What "that order" / "that customer" currently refers to, for conversational follow-ups.
    focus: dict[str, str] = field(default_factory=dict)

    turns: int = 0
    proposals: list[StagedProposal] = field(default_factory=list)

    # What the assistant is doing right now, driven by the tool actually executing — never
    # guessed from the question. The tablet polls this during a turn (M11).
    state: str = "READY"
    state_detail: str = ""

    def set_state(self, state: str, detail: str = "") -> None:
        self.state = state
        self.state_detail = detail
        self.touch()

    def touch(self) -> None:
        self.last_seen_at = time.time()

    def idle_s(self) -> float:
        return time.time() - self.last_seen_at

    def issue(self, *ids: str) -> None:
        for value in ids:
            if value:
                self.issued_ids.add(str(value))

    def stage(self, tool_name: str, args: dict[str, Any], reason: str) -> StagedProposal:
        proposal = StagedProposal(
            proposal_id=f"prop_{uuid.uuid4().hex[:12]}",
            tool_name=tool_name,
            args=args,
            reason=reason,
        )
        self.proposals.append(proposal)
        return proposal

    def set_focus(self, kind: str, value: str) -> None:
        if value:
            self.focus[kind] = str(value)
