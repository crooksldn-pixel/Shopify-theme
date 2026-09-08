"""The proposal: an ephemeral, immutable record of one change the owner may authorise.

Everything that will ever be sent to Shopify is decided when the proposal is staged — from a
fresh read of the entity, on the Mac — and stored here. The tablet later names a proposal id;
it never supplies an argument. The model that asked for the change never sees this object.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType
from typing import Any

# How long a proposal waits for a tap. Long enough to hear the sentence and look at the card;
# short enough that a card the owner walked away from cannot be acted on later.
PROPOSAL_TTL_S = 60.0


class ActionStatus(StrEnum):
    PENDING = "PENDING"          # staged, waiting for the owner
    EXECUTING = "EXECUTING"      # claimed by one commit; the mutation may be in flight
    EXECUTED = "EXECUTED"        # Shopify accepted the mutation; not yet proven
    VERIFIED = "VERIFIED"        # re-read matches what was asked for
    UNVERIFIED = "UNVERIFIED"    # Shopify accepted it, but the re-read does not match
    FAILED = "FAILED"            # the mutation was refused or could not be sent
    STALE = "STALE"              # the entity changed between staging and the tap; nothing sent
    EXPIRED = "EXPIRED"          # the owner did not tap in time
    REVOKED = "REVOKED"          # the owner moved on (a new instruction, a reset, a cancel)


TERMINAL = frozenset({
    ActionStatus.VERIFIED, ActionStatus.UNVERIFIED, ActionStatus.FAILED, ActionStatus.STALE,
    ActionStatus.EXPIRED, ActionStatus.REVOKED,
})


@dataclass(frozen=True, slots=True)
class Prepared:
    """What a write tool's handler returns: the change, fully decided, and nothing sent."""

    execution: dict[str, Any]        # the exact arguments the mutation will be sent with
    before: dict[str, Any]           # fingerprint of the state read now (no personal data)
    expected_after: dict[str, Any]   # fingerprint the state must show once the change is made
    entity_ref: str                  # the entity's id, e.g. gid://shopify/Order/1
    entity_label: str                # how a person names it, e.g. #1930
    summary: dict[str, Any] = field(default_factory=dict)   # bounded fields for the card only


@dataclass(frozen=True, slots=True)
class Observed:
    """One deterministic read of the entity: its fingerprint, and a bounded copy for the screen."""

    fingerprint: dict[str, Any]
    entity: dict[str, Any] | None = None


@dataclass(slots=True)
class ActionProposal:
    proposal_id: str
    session_id: str
    epoch: int
    tool_name: str
    operation: str
    risk: str                                  # "AMBER" | "RED"
    model_args: MappingProxyType               # what the model asked for, read-only
    execution: MappingProxyType                # what will be sent, read-only, server-built
    entity_kind: str
    entity_ref: str
    entity_label: str
    interaction: str
    reversible: bool
    before: dict[str, Any]
    expected_after: dict[str, Any]
    summary: dict[str, Any]
    fingerprint: str                           # canonical hash of (tool, model args); dedupe key
    created_at: float
    expires_at: float
    status: ActionStatus = ActionStatus.PENDING
    reason: str = ""
    code: str = ""                             # controlled outcome code, once terminal
    caller: str = ""                           # who authorised it, when someone did
    executed_at: float | None = None
    finished_at: float | None = None
    verified: bool | None = None
    after: dict[str, Any] | None = None
    entity: dict[str, Any] | None = None       # the bounded re-read after the change
    undo_of: str | None = None                 # set on an undo proposal
    undo_id: str | None = None                 # set on a verified proposal that can be undone
    # Set once the proposal is terminal, so a second commit that arrived while the first was
    # executing can wait for the real outcome instead of guessing.
    done: asyncio.Event = field(default_factory=asyncio.Event)

    @property
    def terminal(self) -> bool:
        return self.status in TERMINAL

    def expired(self, now: float | None = None) -> bool:
        return (now if now is not None else time.time()) > self.expires_at

    def ttl_s(self, now: float | None = None) -> int:
        return max(0, int(round(self.expires_at - (now if now is not None else time.time()))))

    def public(self, now: float | None = None) -> dict[str, Any]:
        """The fields the tablet may see. No arguments, no fingerprints, no personal data."""
        return {
            "proposal_id": self.proposal_id,
            "status": self.status.value.lower(),
            "code": self.code,
            "operation": self.operation,
            "risk": self.risk.lower(),
            "entity_kind": self.entity_kind,
            "entity_label": self.entity_label,
            "interaction": self.interaction,
            "reversible": self.reversible,
            "expires_at": _iso(self.expires_at),
            "ttl_s": self.ttl_s(now),
            "undo_of": self.undo_of,
            "undo_id": self.undo_id,
        }


def new_proposal_id() -> str:
    return f"prop_{uuid.uuid4().hex[:12]}"


def args_fingerprint(tool_name: str, args: dict[str, Any]) -> str:
    """One canonical hash for one (tool, arguments) pair, so the same request twice is one
    proposal and a different request is another."""
    canonical = json.dumps({"tool": tool_name, "args": args}, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:24]


def text_fingerprint(value: str | None) -> dict[str, Any]:
    """A fingerprint of a text field that carries none of the text: its hash and its length.
    Line endings are normalised so a note that came back through Shopify still matches."""
    text = (value or "").replace("\r\n", "\n")
    return {"sha": hashlib.sha256(text.encode("utf-8")).hexdigest()[:16], "len": len(text)}


def _iso(ts: float) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(ts)) + "Z"
