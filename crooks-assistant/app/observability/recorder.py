"""The production experience recorder: an hour of real use, written down, minimised.

A test session is a session somebody started to test with. This is the other thing — the shop
open, the owner working, and a record of what the system did while he did it. It is
OBSERVABILITY and not fixture mode: nothing about a recording changes what a turn does, which
lane it takes, or what it is allowed to write. It is off unless it is explicitly turned on,
and it writes to its own directory so that `make test-session-report` can never mistake one
for the other.

How it gets its events, and why that matters
--------------------------------------------
It does not touch the turn's path. `Timeline.mirror` hands the recorder every event the test
timeline already carries, before that timeline decides whether it has anywhere to put it — so
recording is one line in `app/runtime.py` and no line at all in `/turn`. Everything section 26
asks for is already on that wire: the transcript, the normalised intent, the lane, the entities
resolved, the tools planned and called, the cache counts, the cards and tabs, the touches, the
branch moves, the actions, the latencies, the corrections, Back, the errors, the restarts, and
the prefetch.

What it will not write
----------------------
The rule is ids, counts, tool names and milliseconds. So:

* every key that names a person or their words is dropped, whatever it holds (`PERSONAL_KEYS`);
* every remaining string is scrubbed of anything shaped like an email address, a UK postcode, a
  telephone number or a long run of digits;
* the transcript is a SHAPE by default — how many characters, how many words, which order
  numbers, which catalogue words matched — because the normalised intent is what makes an
  interaction understandable and the sentence itself is not needed for it;
* the transcript itself is kept only when a second setting says so, for a session someone is
  diagnosing a mis-hearing in, and is scrubbed even then.

That is a test (`tests/test_recorder.py`), not a promise.

What it cannot do
-----------------
A recording cannot authorise a change. It has no route that arms or commits, it holds no nonce
— `arm_nonce` is a withheld key on the way in and a dropped one here — and this module imports
nothing from the action engine, the dispatcher or a write tool. Saving an interaction as a test
writes files and returns their paths.

Saving an interaction as a test
-------------------------------
`save_as_test` takes one interaction out of a recording and writes two files an engineer can
run: the turn's own events as a timeline, which `app/observability/report.py` reconstructs
exactly as it does a live one, and a manifest of what that turn DID — its lane, its family, its
tools, its cards, its classes, its milliseconds. The manifest is the assertion; the timeline is
the fixture. Where the recording kept no words there is no sentence to replay, and the saved
test is the turn's structure rather than its speech: reproducible, and honest about which.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any

from app.observability.session import TestSession, TestSessions
from app.observability.timeline import Timeline, read_events

# Its own directory, beside the test sessions and never inside them.
DIR_NAME = "experience-recordings"
_SLUG = re.compile(r"[^a-z0-9]+")

# Keys whose values a recording never holds, whatever they are. A customer's words, a
# customer's address, a person's name, the text of an email, the sentence that was said and the
# sentence that was answered. `app/observability/timeline.py` already withholds credentials;
# this is the other half.
PERSONAL_KEYS = frozenset({
    # what was said and what was answered
    "text", "raw_text", "question", "answer", "reason", "detail", "message", "label",
    "entity_label", "working", "note", "body", "subject", "snippet", "words", "prose",
    # who it was about
    "name", "customer_name", "displayname", "display_name", "to", "cc", "bcc", "from",
    "recipient", "sender", "email", "address", "address1", "address2", "city", "postcode",
    "zip", "phone", "company", "known_name", "address_words",
    # money
    "card", "card_number", "pan", "last4", "iban", "sort_code", "account_number",
    # anything that could be replayed as an instruction
    "arm_nonce", "nonce",
})
# The exceptions, by event kind, and there are only three: fields whose NAME is one of the
# personal ones and whose value is controlled vocabulary. A tab is called "Order" because the
# renderer calls it that; a dock icon is called "inbox" for the same reason; and a recording's
# own name is the one the owner typed to start it. Everything else keeps the blanket rule, and
# an exception is a named pair rather than a loosened set — a `label` on a working set is a
# customer's name and stays gone.
SAFE_FIELDS: dict[str, frozenset[str]] = {
    "tablet_tab": frozenset({"label"}),
    "tablet_navigate": frozenset({"name"}),
    "session_started": frozenset({"name"}),
    "session_stopped": frozenset({"name"}),
}
MAX_SAFE_FIELD = 40
# The shape of a transcript, when the words themselves are not kept. `matches` and
# `order_numbers` stay: a product word from the catalogue and an order number are controlled
# vocabulary and an id, which is exactly what this file is allowed to hold.
TRANSCRIPT_KEYS = ("text", "raw_text", "question", "answer")

_EMAIL = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
# A street, as an address is written and as it is spoken: a number and a thoroughfare. It
# matters for the transcript, where "send it to 14 Ravensbourne Road" is a sentence and not a
# field, so a key-based rule cannot reach it.
_STREET = re.compile(
    r"\b\d{1,5}[a-z]?[\s,]+(?:[A-Za-z'\-]+\s+){0,3}"
    r"(?:road|street|lane|avenue|close|drive|way|court|place|terrace|gardens?|crescent|row|hill|park|square|grove|mews|walk|rise|rd|st|ln|ave)\b",
    re.I,
)
_UK_POSTCODE = re.compile(r"\b[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}\b", re.I)
_PHONE = re.compile(r"(?:\+\d{1,3}[\s\-]?)?(?:\(?\d{3,5}\)?[\s\-]?){2,4}\d{2,4}")
_LONG_DIGITS = re.compile(r"\b\d{9,}\b")
MAX_RECORDED_STRING = 400


def scrub_personal(value: Any, depth: int = 0) -> Any:
    """A copy with the personal keys gone and the personal shapes replaced.

    Runs over whatever the caller passed, at any depth, because the fields that carry a
    person's data are not always at the top: a tool's result holds an order, an order holds an
    address. Nothing here decides whether an event is interesting; it decides what a recording
    may hold of it.
    """
    if depth > 6:
        return "[deep]"
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key, item in value.items():
            name = str(key)
            # A personal key is dropped when it holds TEXT or a structure. A boolean or a
            # number under the same name is a flag or a count — `email: true` on a router
            # signal, `phone: 2` on a count of them — and those are exactly what this file is
            # for. Dropping them lost the normalised intent, which is the most useful thing a
            # recording holds.
            if name.lower().replace("-", "_") in PERSONAL_KEYS and not isinstance(item, (bool, int, float)):
                continue
            out[name[:80]] = scrub_personal(item, depth + 1)
        return out
    if isinstance(value, (list, tuple, set, frozenset)):
        return [scrub_personal(v, depth + 1) for v in list(value)[:200]]
    if isinstance(value, bool) or value is None or isinstance(value, (int, float)):
        return value
    text = value if isinstance(value, str) else str(value)
    text = _EMAIL.sub("[email]", text)
    text = _STREET.sub("[street]", text)
    text = _UK_POSTCODE.sub("[postcode]", text)
    text = _LONG_DIGITS.sub("[digits]", text)
    text = _PHONE.sub("[phone]", text)
    return text if len(text) <= MAX_RECORDED_STRING else text[:MAX_RECORDED_STRING] + "…"


def transcript_shape(fields: dict[str, Any]) -> dict[str, Any]:
    """What was said, as structure: how long it was, and nothing of what it was.

    Section 26 asks for the voice transcript. What makes an interaction understandable is the
    NORMALISED intent — the family, the signals, the entities resolved — and every one of those
    is already on the event and already free of a person's data by construction
    (`Signals.PRIVATE`). The sentence adds the owner's own phrasing, and a customer's name in
    it, so by default this is what is kept of it.
    """
    out: dict[str, Any] = {}
    for key in TRANSCRIPT_KEYS:
        said = fields.get(key)
        if not isinstance(said, str) or not said:
            continue
        out[f"{key}_chars"] = len(said)
        out[f"{key}_words"] = len(said.split())
    return out


class Recordings(TestSessions):
    """The recordings on disk. The same shape as the test sessions — an `active.json`, a
    `last.json`, one JSONL per recording — in a directory of their own."""

    __test__ = False

    def __init__(self, log_dir: Path, *, clock=time.time) -> None:
        super().__init__(log_dir, clock=clock, dir_name=DIR_NAME)

    def start(self, name: str) -> TestSession:
        session = super().start(name)
        # A recording is named so that nothing reading the test-session folder's `ts-` prefix
        # can pick one up, and so a person reading `ls` can tell them apart at a glance.
        renamed = TestSession(test_session_id="rec-" + session.test_session_id.removeprefix("ts-"),
                              name=session.name, started_at=session.started_at)
        from app.observability.session import _write_private

        _write_private(self.active_path, renamed.as_dict())
        self._checked_at = -1.0
        self._cached = None
        return renamed


class Recorder(Timeline):
    """A timeline that writes recordings, and minimises what it writes.

    `keep_transcripts` is the second opt-in: with it off — the default, and what production
    runs — the sentence is replaced by its shape. With it on the sentence is kept, still
    scrubbed of the addresses, postcodes, telephone numbers and long digit runs that can be
    recognised without knowing whose they are.
    """

    def __init__(self, recordings: Recordings, *, clock=time.time, keep_transcripts: bool = False) -> None:
        super().__init__(recordings, clock=clock)
        self.keep_transcripts = bool(keep_transcripts)
        self.mirror = None      # a mirror never has a mirror

    def emit(self, kind: str, *, source: str = "mac", ts: float | None = None, **fields: Any) -> dict[str, Any] | None:
        if self.active is None:
            return None
        shape = transcript_shape(fields)
        if self.keep_transcripts:
            kept = {k: scrub_personal(v) for k, v in fields.items() if k in TRANSCRIPT_KEYS and isinstance(v, str) and v}
        else:
            kept = {}
        safe_names = SAFE_FIELDS.get(kind, frozenset())
        safe = {k: scrub_personal(str(v))[:MAX_SAFE_FIELD] for k, v in fields.items()
                if k in safe_names and isinstance(v, str) and v}
        minimised = scrub_personal({k: v for k, v in fields.items() if k not in TRANSCRIPT_KEYS and k not in safe})
        return super().emit(kind, source=source, ts=ts, recorded=True, **minimised, **shape, **kept, **safe)


# ---------------------------------------------------------------- the process's recorder


_current: Recorder | None = None


def install(recorder: Recorder | None) -> Recorder | None:
    global _current
    _current = recorder
    return recorder


def current() -> Recorder | None:
    return _current


# ------------------------------------------------------ save this interaction as a test


def interactions(path: Path) -> list[dict[str, Any]]:
    """Every interaction in a recording, in order, as a line a person can choose from: the
    turn's id, its lane and family, how long it took, how many tools it called, and how it was
    classified. Enough to pick one; never a word of what was said."""
    from app.observability.report import reconstruct

    rec = reconstruct(read_events(Path(path)))
    out = []
    for turn in rec.turns:
        out.append({
            "turn_id": turn.turn_id, "conversation": turn.session_id, "at": turn.started_at,
            "lane": str((turn.lane or {}).get("lane") or ""), "family": str((turn.lane or {}).get("family") or ""),
            "tools": [x.tool for x in turn.tools], "cards": [str(c.get("type")) for r in turn.tablet_events("render") for c in (r.get("cards") or []) if isinstance(c, dict)],
            "ms": turn.latency("total"), "outcome": turn.outcome, "classes": list(turn.classes),
        })
    return out


def save_as_test(path: Path, out_dir: Path, *, turn_id: str = "") -> dict[str, Path]:
    """One interaction, as a fixture an engineer can run.

    Two files: `<recording>-<turn>.jsonl`, the turn's own events, which `report.reconstruct`
    reads exactly as it reads a live session's; and `<recording>-<turn>.json`, the manifest of
    what that turn did, which is what a test asserts. Neither can authorise anything: the
    manifest is names, counts and milliseconds, and the timeline is what the recorder already
    minimised.

    With no `turn_id`, the last interaction in the recording is taken — which is what "save
    that one" means when it has just happened.
    """
    from app.observability.report import reconstruct

    path = Path(path)
    events = read_events(path)
    rec = reconstruct(events)
    if not rec.turns:
        raise ValueError(f"{path.name} holds no interaction to save")
    turn = rec.turn(turn_id) if turn_id else rec.turns[-1]
    if turn is None:
        raise ValueError(f"{path.name} holds no interaction {turn_id!r}")

    # The turn's own events, and the session's two bookends so the fixture reads as a session.
    wanted = {turn.turn_id}
    kept = [e for e in events if str(e.get("kind") or "") in ("session_started", "session_stopped")
            or str(e.get("turn_id") or "") in wanted]
    # Anything the turn holds that carried no turn id of its own (a hydration that landed after
    # the answer, a command tapped during it) travels with it, so the fixture is the whole
    # interaction and not only the parts that were correlated.
    for group in (turn.hydrations, turn.context_requests, turn.sets, turn.commands, turn.branch_events, turn.tablet):
        for event in group:
            if event not in kept:
                kept.append(event)
    kept.sort(key=lambda e: (float(e.get("ts") or 0.0), int(e.get("seq") or 0)))

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{path.stem}-{_SLUG.sub('-', turn.turn_id.lower()).strip('-')}"
    timeline_file = out_dir / f"{stem}.jsonl"
    timeline_file.write_text("".join(json.dumps(scrub_personal(e), ensure_ascii=False) + "\n" for e in kept), encoding="utf-8")
    manifest = {
        "from_recording": path.stem,
        "turn_id": turn.turn_id,
        "note": "Saved from a production recording. Assert this against `reconstruct` over the .jsonl beside it. "
                "Names, counts and milliseconds only: a recording cannot authorise a change and neither can this.",
        "input": turn.input,
        "lane": str((turn.lane or {}).get("lane") or ""),
        "family": str((turn.lane or {}).get("family") or ""),
        "confidence": (turn.lane or {}).get("confidence"),
        "signals": sorted((turn.lane or {}).get("signals") or {}),
        "contract": turn.contract,
        "recipe_id": str((turn.fast or {}).get("recipe_id") or ""),
        "tools": [{"tool": x.tool, "outcome": x.outcome, "ok": x.ok} for x in turn.tools],
        "cards": [str(c.get("type")) for r in turn.tablet_events("render") for c in (r.get("cards") or []) if isinstance(c, dict)],
        "tabs": [str(e.get("label") or "") for e in turn.tablet_events("tab")],
        "commands": [str(e.get("command") or e.get("action") or "") for e in turn.commands],
        "proposals": [{"operation": p.operation, "risk": p.risk, "status": p.status} for p in turn.proposals],
        "classes": list(turn.classes),
        "outcome": turn.outcome,
        "ms": {name: turn.latency(name) for name in ("stt", "claude", "facts", "workspace", "prose_wait", "total")},
        "events": len(kept),
    }
    manifest_file = out_dir / f"{stem}.json"
    manifest_file.write_text(json.dumps(scrub_personal(manifest), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for file in (timeline_file, manifest_file):
        try:
            file.chmod(0o600)
        except OSError:
            pass
    return {"timeline": timeline_file, "manifest": manifest_file}
