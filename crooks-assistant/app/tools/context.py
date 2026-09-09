"""The session a tool call runs for, reachable from inside the handler without passing it
through every signature: the dispatcher sets it around the call, on the task the call runs
in. A tool that needs the conversation's working sets, or the turn's id, reads it here."""

from __future__ import annotations

from contextvars import ContextVar
from typing import Any

CURRENT_SESSION: ContextVar[Any] = ContextVar("crooks_current_session", default=None)


def current_session() -> Any:
    return CURRENT_SESSION.get()
