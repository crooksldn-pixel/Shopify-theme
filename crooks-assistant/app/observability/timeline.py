"""The timeline: one JSON line per event, from the Mac and from the tablet, into the active
test session's file. Nothing here is on a turn's path: `emit` puts the line on a queue and a
thread writes it. Off — no session active — `emit` is a cached stat and a return.

Every event carries the time, a sequence number, the test session, its source and its kind,
and whatever correlation ids the caller has (session_id, turn_id, tool_call_id, proposal_id,
context_request_id). Never a credential: keys that name one are withheld and strings that
look like one are scrubbed, whatever the caller passed."""

from __future__ import annotations

import json
import logging
import os
import queue
import re
import threading
import time
from pathlib import Path
from typing import Any

from app.observability.session import TestSession, TestSessions

log = logging.getLogger("crooks.observe")

MAX_STRING = 6_000
MAX_DEPTH = 6
MAX_LIST = 400

# Keys whose values are never written, whatever they hold.
WITHHELD_KEYS = frozenset({
    "authorization", "cookie", "cookies", "set-cookie", "x-api-key", "xi-api-key", "api_key", "apikey",
    "token", "access_token", "refresh_token", "id_token", "oauth_token", "client_secret", "secret",
    "password", "nonce", "arm_nonce", "x-crooks-arm", "headers", "raw_headers", "credentials", "credential",
})
# Strings shaped like a credential, scrubbed wherever they appear.
_SECRET = re.compile(
    r"(shpat_[A-Za-z0-9]{8,}|shpca_[A-Za-z0-9]{8,}|shpss_[A-Za-z0-9]{8,}|sk-ant-[A-Za-z0-9_\-]{8,}|sk_[A-Za-z0-9]{20,}"
    r"|ya29\.[A-Za-z0-9_\-]{8,}|1//[A-Za-z0-9_\-]{20,}|xoxb-[A-Za-z0-9\-]{8,}"
    r"|eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}"
    r"|(?i:bearer)\s+[A-Za-z0-9._\-]{16,})"
)


def scrub(value: Any, depth: int = 0) -> Any:
    """A copy safe to write: withheld keys gone, credential-shaped strings replaced, sizes
    bounded, anything unserialisable rendered as text."""
    if depth > MAX_DEPTH:
        return "[deep]"
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key, item in value.items():
            name = str(key)
            if name.lower().replace("_", "-") in WITHHELD_KEYS or name.lower() in WITHHELD_KEYS:
                out[name[:80]] = "[withheld]"
            else:
                out[name[:80]] = scrub(item, depth + 1)
        return out
    if isinstance(value, (list, tuple, set, frozenset)):
        items = list(value)[:MAX_LIST]
        return [scrub(v, depth + 1) for v in items]
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, (int, float)):
        return value if value == value and abs(value) != float("inf") else None
    if isinstance(value, bytes):
        return f"<{len(value)} bytes>"
    text = value if isinstance(value, str) else str(value)
    text = _SECRET.sub("[secret]", text)
    return text if len(text) <= MAX_STRING else text[:MAX_STRING] + "…"


class Timeline:
    def __init__(self, sessions: TestSessions, *, clock=time.time) -> None:
        self.sessions = sessions
        self.clock = clock
        self._queue: queue.SimpleQueue = queue.SimpleQueue()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._seq = 0
        self._written = 0
        self._dropped = 0

    # ----------------------------------------------------------------- state

    @property
    def active(self) -> TestSession | None:
        return self.sessions.active()

    @property
    def active_id(self) -> str | None:
        session = self.active
        return session.test_session_id if session is not None else None

    def start(self, name: str) -> TestSession:
        session = self.sessions.start(name)
        self.emit("session_started", name=session.name, started_at=session.started_at)
        self.flush()
        return session

    def stop(self) -> TestSession | None:
        current = self.active
        if current is None:
            return None
        self.emit("session_stopped", name=current.name, duration_s=round(self.clock() - current.started_at, 3))
        self.flush()
        return self.sessions.stop()

    # ------------------------------------------------------------------ emit

    def emit(self, kind: str, *, source: str = "mac", ts: float | None = None, **fields: Any) -> dict[str, Any] | None:
        """One event, if a session is active. Returns what was queued (for tests), else None.
        Never raises: an event that cannot be written is a dropped event, counted."""
        try:
            session = self.active
            if session is None:
                return None
            now = self.clock()
            with self._lock:
                self._seq += 1
                seq = self._seq
            event: dict[str, Any] = {
                "ts": round(float(ts) if ts is not None else now, 3),
                "iso": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(now)),
                "seq": seq,
                "test_session_id": session.test_session_id,
                "source": source,
                "kind": str(kind)[:40],
            }
            for key, value in fields.items():
                if value is None or key in event:
                    continue
                event[key] = value
            event = scrub(event)
            line = json.dumps(event, ensure_ascii=False, default=str)
            self._queue.put((self.sessions.timeline_path(session), line))
            self._ensure_writer()
            return event
        except Exception as exc:  # noqa: BLE001 — observability never takes a turn down
            self._dropped += 1
            log.debug("timeline event dropped: %s", exc)
            return None

    # ----------------------------------------------------------------- writer

    def _ensure_writer(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return
            self._thread = threading.Thread(target=self._run, name="crooks-timeline", daemon=True)
            self._thread.start()

    def _run(self) -> None:
        while True:
            path, line = self._queue.get()
            batch: dict[Path, list[str]] = {path: [line]}
            # Whatever else is waiting goes out in the same write.
            while True:
                try:
                    more_path, more = self._queue.get_nowait()
                except queue.Empty:
                    break
                batch.setdefault(more_path, []).append(more)
            for target, lines in batch.items():
                self._append(target, lines)

    def _append(self, path: Path, lines: list[str]) -> None:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
            try:
                os.write(fd, ("\n".join(lines) + "\n").encode("utf-8"))
            finally:
                os.close(fd)
            self._written += len(lines)
        except OSError as exc:
            self._dropped += len(lines)
            log.warning("could not write the timeline: %s", exc)

    def flush(self, timeout_s: float = 2.0) -> bool:
        """Wait, briefly, for what is queued to reach disk. For stop, and for tests."""
        deadline = time.monotonic() + timeout_s
        while not self._queue.empty() and time.monotonic() < deadline:
            time.sleep(0.005)
        # The writer may hold the last batch after the queue is empty; give it a moment.
        time.sleep(0.01)
        return self._queue.empty()

    @property
    def counts(self) -> dict[str, Any]:
        """How many events this session actually holds.

        `written` is counted from the FILE, not from a counter in memory. The counters are
        per-process and a restart zeroes them, which is how `make test-session-status`
        reported "events written=0" against a session that already held a thousand — the
        supervisor had restarted the backend mid-session and the timeline kept growing
        underneath it. The file is the session; the counters describe this process's part
        in it, and are reported as such.
        """
        # The session this is about: the one running, or — just after `stop`, which is when
        # the count is most often asked for — the one that has just ended.
        session = self.active or self.sessions.last()
        on_disk = count_events(self.sessions.timeline_path(session)) if session is not None else 0
        queued = self._queue.qsize()
        return {
            "written": on_disk + queued,          # what the session holds once the queue lands
            "on_disk": on_disk,
            "queued": queued,
            "dropped": self._dropped,
            "this_process": self._written,
            "test_session_id": session.test_session_id if session is not None else "",
        }


class NullTimeline(Timeline):
    """Nothing active, ever: what a process without a log directory uses."""

    def __init__(self) -> None:  # noqa: D107 — no sessions, no thread
        self._seq = 0
        self._written = 0
        self._dropped = 0

    @property
    def active(self) -> TestSession | None:
        return None

    def emit(self, kind: str, **fields: Any) -> dict[str, Any] | None:  # noqa: ARG002
        return None

    def flush(self, timeout_s: float = 0.0) -> bool:  # noqa: ARG002
        return True

    @property
    def counts(self) -> dict[str, Any]:
        return {"written": 0, "on_disk": 0, "queued": 0, "dropped": 0, "this_process": 0, "test_session_id": ""}


_current: Timeline = NullTimeline()


def install(timeline: Timeline) -> Timeline:
    global _current
    _current = timeline
    return timeline


def current() -> Timeline:
    return _current


def emit(kind: str, **fields: Any) -> dict[str, Any] | None:
    """The process's timeline, for code that has no runtime in hand (the dispatcher, the
    engine, the hydrator)."""
    return _current.emit(kind, **fields)


def new_id(prefix: str) -> str:
    return f"{prefix}_{os.urandom(6).hex()}"


def count_events(path: Path) -> int:
    """The number of events in a timeline, counted from the file. Cheap: lines, not JSON.
    Zero for a file that is not there yet, which is what an unwritten session looks like."""
    try:
        with Path(path).open("rb") as handle:
            return sum(1 for line in handle if line.strip())
    except OSError:
        return 0


def read_events(path: Path) -> list[dict[str, Any]]:
    """Every event in a timeline, in the order written."""
    events: list[dict[str, Any]] = []
    try:
        with Path(path).open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except ValueError:
                    continue
                if isinstance(event, dict):
                    events.append(event)
    except OSError:
        return []
    events.sort(key=lambda e: (float(e.get("ts") or 0), int(e.get("seq") or 0)))
    return events
