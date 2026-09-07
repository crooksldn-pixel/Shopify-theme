"""In-memory session store with idle expiry.

Deliberately not persisted. A restarted backend has no sessions, which is correct: the M13 rule
is that the assistant says "I've lost the thread" rather than pretending to remember.
"""

from __future__ import annotations

import threading

from app.session.models import Session


class SessionExpired(KeyError):
    """The session id is unknown or has been idle past the timeout."""


class SessionManager:
    def __init__(self, idle_timeout_s: int = 1800) -> None:
        self._sessions: dict[str, Session] = {}
        self._idle_timeout_s = idle_timeout_s
        self._lock = threading.Lock()

    def get_or_create(self, session_id: str) -> Session:
        with self._lock:
            self._sweep_locked()
            session = self._sessions.get(session_id)
            if session is None:
                session = Session(session_id=session_id)
                self._sessions[session_id] = session
            session.touch()
            return session

    def get(self, session_id: str) -> Session:
        with self._lock:
            self._sweep_locked()
            session = self._sessions.get(session_id)
            if session is None:
                raise SessionExpired(session_id)
            session.touch()
            return session

    def exists(self, session_id: str) -> bool:
        with self._lock:
            self._sweep_locked()
            return session_id in self._sessions

    def peek(self, session_id: str) -> Session:
        """Read without touching last_seen_at — polling for state must not keep a session alive."""
        with self._lock:
            self._sweep_locked()
            session = self._sessions.get(session_id)
            if session is None:
                raise SessionExpired(session_id)
            return session

    def drop(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)

    def count(self) -> int:
        with self._lock:
            self._sweep_locked()
            return len(self._sessions)

    def _sweep_locked(self) -> None:
        stale = [
            sid for sid, s in self._sessions.items() if s.idle_s() > self._idle_timeout_s
        ]
        for sid in stale:
            del self._sessions[sid]


_manager: SessionManager | None = None


def get_manager(idle_timeout_s: int = 1800) -> SessionManager:
    global _manager
    if _manager is None:
        _manager = SessionManager(idle_timeout_s=idle_timeout_s)
    return _manager
