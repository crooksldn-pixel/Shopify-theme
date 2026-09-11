"""Row actions: a button beside a row on a card.

The September session: "Give me an option to remove the emails … with a button next to them",
answered "I can't add buttons to the card, that's fixed by the tablet". The tablet's cards
are fixed — that part was true — but what is ON them is the Mac's to decide, and this is the
table that decides it.

The safety shape matters and is the same as everywhere else:

* The list of actions a row may carry is SERVER-OWNED. The tablet renders what it is given.
* A tap posts the action's ID and the row's REF, nothing else. It never posts arguments.
* The Mac looks the action up here, builds the arguments itself from a fresh read (the write
  tool's own prepare step), and stages a proposal exactly as a model-proposed change is
  staged — through the gate, with a gesture still to come.
* "Remove" means ARCHIVE. Gmail's trash is a different capability and is not offered here;
  a row action never maps a soft word onto a destructive change.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class RowAction:
    """One button. `tool` is a registered write tool; `args` builds its arguments from the
    row's reference, which must be an id this conversation has been issued."""

    id: str
    label: str
    tool: str
    args: Callable[[str], dict[str, Any]]
    kind: str                    # the row's entity kind, for the issued-id check
    risk: str = "amber"
    # What the button says it does, in the owner's words. Shown under a confirm.
    detail: str = ""

    def public(self) -> dict[str, Any]:
        return {"id": self.id, "label": self.label, "operation": self.tool, "risk": self.risk,
                "enabled": True, "reason": "", "detail": self.detail, "mode": "stage",
                # A row action posts its own id and its row's ref, never a command of its own.
                "command": "", "args": "", "priority": "primary"}


ROW_ACTIONS: dict[str, RowAction] = {
    "email_archive": RowAction(
        id="email_archive",
        label="Archive",
        tool="gmail_thread_archive",
        args=lambda ref: {"thread_id": str(ref)},
        kind="email_thread",
        detail="Takes the thread out of the inbox. It stays in Gmail and can be put back; nothing is deleted.",
    ),
}

# Which actions each kind of row may carry. A kind not listed here carries none.
BY_KIND: dict[str, tuple[str, ...]] = {
    "email_thread": ("email_archive",),
}


def actions_for(kind: str, *, writes_enabled: bool, registered: set[str] | None = None) -> list[dict[str, Any]]:
    """What a row of this kind may offer on this build. Empty while changes are off, and
    empty for an action whose write tool this build does not carry."""
    if not writes_enabled:
        return []
    known = registered if registered is not None else _registered()
    out: list[dict[str, Any]] = []
    for action_id in BY_KIND.get(kind, ()):
        action = ROW_ACTIONS.get(action_id)
        if action is not None and action.tool in known:
            out.append(action.public())
    return out


def _registered() -> set[str]:
    from app.tools import registry

    return set(registry.names())


class UnknownRowAction(KeyError):
    """The tablet named an action this build does not offer. Fail closed."""


def resolve(action_id: str, ref: str) -> tuple[RowAction, dict[str, Any]]:
    """The write tool and the arguments for one row action. Raises rather than guessing.

    The action must be one BY_KIND offers for a row of its own kind. Today there is one
    action and one kind, so the check cannot fail; it is here so that adding a second kind
    does not silently let the tablet pair any action with any row.
    """
    action = ROW_ACTIONS.get(str(action_id or ""))
    if action is None:
        raise UnknownRowAction(str(action_id or ""))
    if action.id not in BY_KIND.get(action.kind, ()):
        raise UnknownRowAction(f"{action.id} is not offered on a {action.kind} row")
    ref = str(ref or "").strip()
    if not ref:
        raise UnknownRowAction("no row was named")
    return action, action.args(ref)
