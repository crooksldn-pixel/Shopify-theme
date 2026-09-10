"""The test session: what is active, persisted on the Mac so the backend, the CLI and a
restart all agree on it.

`logs/test-sessions/active.json` names the session in progress; `last.json` the one most
recently stopped, so `make test-session-report` with no argument knows which. Both are
written whole and renamed into place, created 0600, in a directory created 0700: the
timeline beside them holds what the owner said and what was answered."""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path

DIR_NAME = "test-sessions"
ACTIVE_FILE = "active.json"
LAST_FILE = "last.json"
# How long a cached answer to "is a session active" stands before the file is looked at again.
# Every event asks; the file changes only when someone runs start or stop.
RECHECK_S = 1.0

_SLUG = re.compile(r"[^a-z0-9]+")


class AlreadyActive(RuntimeError):
    """A session is running; stop it before starting another."""


@dataclass(slots=True)
class TestSession:
    test_session_id: str
    name: str
    started_at: float
    stopped_at: float | None = None

    @property
    def active(self) -> bool:
        return self.stopped_at is None

    def as_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> TestSession:
        return cls(
            test_session_id=str(data.get("test_session_id") or ""),
            name=str(data.get("name") or ""),
            started_at=float(data.get("started_at") or 0.0),
            stopped_at=(float(data["stopped_at"]) if data.get("stopped_at") is not None else None),
        )


def session_dir(log_dir: Path, dir_name: str = DIR_NAME) -> Path:
    return Path(log_dir) / dir_name


def new_session_id(name: str, now: float) -> str:
    slug = _SLUG.sub("-", (name or "").lower()).strip("-")[:24] or "session"
    stamp = time.strftime("%Y%m%d-%H%M%S", time.localtime(now))
    return f"ts-{stamp}-{slug}"


def _write_private(path: Path, data: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.write(fd, (json.dumps(data, ensure_ascii=False) + "\n").encode("utf-8"))
    finally:
        os.close(fd)
    os.replace(tmp, path)


def _read(path: Path) -> TestSession | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict) or not data.get("test_session_id"):
        return None
    return TestSession.from_dict(data)


class TestSessions:
    """The session state on disk, read by whoever asks: the backend on every event (cached
    for a second), the CLI once per command."""

    __test__ = False   # not a pytest class, whatever its name says

    def __init__(self, log_dir: Path, *, clock=time.time, dir_name: str = DIR_NAME) -> None:
        # `dir_name`, because a production recording is NOT a test session and must not share
        # a directory with one: `make test-session-report` finds the last test session by
        # reading this folder, and a recording landing in it would be reported as one.
        self.root = session_dir(log_dir, dir_name)
        self.clock = clock
        self._cached: TestSession | None = None
        self._checked_at = -1.0
        self._mtime = -1.0

    def _ensure_root(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        try:
            if self.root.stat().st_mode & 0o077:
                self.root.chmod(0o700)
        except OSError:
            pass

    @property
    def active_path(self) -> Path:
        return self.root / ACTIVE_FILE

    def timeline_path(self, session: TestSession | str) -> Path:
        ident = session.test_session_id if isinstance(session, TestSession) else str(session)
        return self.root / f"{ident}.jsonl"

    def active(self) -> TestSession | None:
        """The session in progress, or None. The file is looked at again at most once a second,
        so a start or stop from the CLI is noticed within that, without a restart."""
        now = self.clock()
        if 0 <= now - self._checked_at < RECHECK_S:
            return self._cached
        self._checked_at = now
        try:
            mtime = self.active_path.stat().st_mtime
        except OSError:
            self._cached, self._mtime = None, -1.0
            return None
        if mtime != self._mtime or self._cached is None:
            self._mtime = mtime
            self._cached = _read(self.active_path)
        return self._cached

    def start(self, name: str) -> TestSession:
        self._ensure_root()
        current = self.active()
        if current is not None:
            raise AlreadyActive(current.test_session_id)
        now = self.clock()
        session = TestSession(test_session_id=new_session_id(name, now), name=(name or "").strip()[:80] or "session", started_at=now)
        _write_private(self.active_path, session.as_dict())
        self._checked_at = -1.0
        return session

    def stop(self) -> TestSession | None:
        self._checked_at = -1.0
        current = self.active()
        if current is None:
            return None
        current.stopped_at = self.clock()
        self._ensure_root()
        _write_private(self.root / LAST_FILE, current.as_dict())
        try:
            self.active_path.unlink()
        except OSError:
            pass
        self._checked_at = -1.0
        self._cached = None
        return current

    def last(self) -> TestSession | None:
        return _read(self.root / LAST_FILE)

    def find(self, ref: str = "") -> Path | None:
        """The timeline named by a session id (or the start of one); with no name, the active
        session's, else the last stopped one's."""
        ref = (ref or "").strip()
        if not ref:
            session = self.active() or self.last()
            if session is None:
                return None
            path = self.timeline_path(session)
            return path if path.exists() else None
        if "/" in ref or ".." in ref:
            return None
        exact = self.root / (ref if ref.endswith(".jsonl") else f"{ref}.jsonl")
        if exact.exists():
            return exact
        matches = sorted(p for p in self.root.glob("*.jsonl") if p.name.startswith(ref))
        return matches[-1] if matches else None
