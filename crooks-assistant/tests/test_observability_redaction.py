"""The timeline's own redaction, held to the invariant it is supposed to keep (D-15).

    "No customer detail in the ledger, the timeline or a proposal beyond what the owner
     said aloud."

Measured over all 1,365 events of `ts-20260911-201129-phase-4-live-tablet-test.jsonl` before
anything changed:

    turn_finished.question   redacted — 8 events carry `[name]`
    turn_finished.answer     redacted — 7 events carry `[name]`
    tts.text                 NOT redacted — raw name AND raw email address
    model.answer             NOT redacted — raw email address
    prediction.key           NOT redacted — raw email address

Three real customer email addresses sat in that file. The redaction was applied at ONE CALL
SITE — `app/routes/turn.py::_written`, on the turn record — so the same sentence was scrubbed
where it was written down as an ANSWER and intact where it was written down as something
SPOKEN. `logs/test-sessions/` is gitignored, so nothing leaked to the repository; a timeline is
nevertheless exported, read, pasted into reports and handed to engineering agents, and this
very pass received three real addresses that way.

The fix is ONE SEAM, at the place events are written, and the test below is the point of it: it
walks an entire timeline, every event, every field, however deep, and asserts that nothing in
it matches an email pattern. The per-call-site approach would rot again the moment somebody
adds an event kind, and this test is what stops that.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest

from app.observability import timeline
from app.observability.session import TestSessions

# The shapes that must never appear in a written timeline. Deliberately independent of the
# redactor's own patterns: a test that reused them would pass on any redactor, including one
# that does nothing.
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
CARD = re.compile(r"(?<![\w.-])(?:\d[ -]?){13,19}(?![\w.-])")
UK_POSTCODE = re.compile(r"\b[A-Z]{1,2}\d[A-Z\d]?\s*\d(?!XL|XS|PK|PC)[A-Z]{2}\b")
# The ids the timeline is MADE of, taken out of the string before the card and postcode checks
# run over it. A Shopify GID ends in a fourteen-digit number and a thread id is a hex run;
# neither is a payment card, and a redactor that ate them would take the analyser with it —
# `test_the_ids_counts_and_milliseconds_a_report_is_built_from_survive` is the other half of
# this. Only the EMAIL check runs over the whole string, because no id in this system looks
# like an address.
NOT_PERSONAL = re.compile(r"gid://\w+/\w+/\d+|prop_[0-9a-f]+|[0-9a-f]{16,}|\d{8}-\d{6}(?:\.\w+)?")

# What the evening actually contained, with invented names and invented addresses in place of
# the real ones. One entry per field the measurement above found unredacted, plus the two it
# found already covered, so the test proves the seam rather than one caller.
A_SESSION = (
    ("stt", {"ok": True, "text": "Pull up the history of Rowan Mitcham and his orders"}),
    ("lane", {"lane": "NORMAL", "family": "customer_history_lookup"}),
    ("tool_finished", {"tool": "shopify_find_customer", "ok": True,
                       "result": {"customer_id": "gid://shopify/Customer/70000000000003",
                                  "name": "Rowan Mitcham",
                                  "email": "rowan.mitcham@example.co.uk"}}),
    ("context_hydration", {"order_id": "gid://shopify/Order/70000000000901",
                           "customer": {"email": "rowan.mitcham@example.co.uk",
                                        "address": "14 Ashmill Street, London NW1 6RA",
                                        "phone": "+44 7700 900123"}}),
    ("model", {"ms": 3100.0,
               "answer": "Rowan Mitcham, rowan.mitcham@example.co.uk — two orders, sixty "
                         "pounds each."}),
    ("prediction", {"key": "rowan.mitcham@example.co.uk", "hit": False}),
    ("anticipation", {"edges": ["rowan.mitcham@example.co.uk"], "n": 1}),
    ("tts", {"engine": "eleven", "ms_first_byte": 780.0,
             "text": "Rowan Mitcham, rowan.mitcham@example.co.uk — two orders, both today."}),
    ("owner_feedback", {"shape": "log",
                        "text": "Log that it showed me Rowan Mitcham's email in the answer"}),
    ("turn_finished", {"ms": 4200.0, "question": "Pull up the history of Rowan Mitcham",
                       "answer": "Rowan Mitcham — two orders."}),
    # An event kind nobody has written yet. This is the one the per-call-site approach always
    # misses, and the reason the seam has to be where it is.
    ("a_kind_added_next_week", {"whatever": "rowan.mitcham@example.co.uk",
                                "nested": [{"deeper": {"also": "rowan.mitcham@example.co.uk"}}]}),
)
NAMES = ("Rowan Mitcham",)


def _strings(value: Any, path: str = "") -> list[tuple[str, str]]:
    """Every string in an event, with where it was found. Keys as well as values: an address
    used as a dictionary key is still an address."""
    out: list[tuple[str, str]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            out.append((f"{path}.<key>", str(key)))
            out.extend(_strings(item, f"{path}.{key}"))
    elif isinstance(value, (list, tuple)):
        for i, item in enumerate(value):
            out.extend(_strings(item, f"{path}[{i}]"))
    elif isinstance(value, str):
        out.append((path or "<root>", value))
    return out


@pytest.fixture()
def recording(tmp_path):
    """A test session, running, writing to a temporary directory."""
    timeline.forget_names()
    store = TestSessions(Path(tmp_path))
    line = timeline.install(timeline.Timeline(store))
    session = line.start("the eleventh of September")
    yield line, store, session
    line.stop()
    timeline.install(timeline.NullTimeline())
    timeline.forget_names()


def _write_the_session(line: timeline.Timeline, *, tell_it_the_names: bool = True) -> None:
    if tell_it_the_names:
        timeline.note_names(NAMES)
    for kind, fields in A_SESSION:
        line.emit(kind, session_id="s1", turn_id="turn_history", **fields)
    line.flush()


# ------------------------------------------------------------------------- the invariant


def test_no_field_of_any_event_in_a_whole_timeline_matches_an_email(recording):
    """THE test D-15 asks for. Not "the fields we remembered" — every field of every event,
    however deeply nested, keys included, read back from the file on disk.

    BEFORE: `tts.text`, `model.answer` and `prediction.key` carried a raw email address,
    because redaction lived at one call site and none of those three went through it.
    """
    line, store, session = recording
    _write_the_session(line)

    path = store.timeline_path(session)
    events = [json.loads(row) for row in path.read_text(encoding="utf-8").splitlines() if row.strip()]
    assert len(events) >= len(A_SESSION), events

    offences: list[tuple[str, str, str]] = []
    for event in events:
        for where, text in _strings(event):
            without_ids = NOT_PERSONAL.sub(" ", text)
            if EMAIL.search(text) or CARD.search(without_ids) or UK_POSTCODE.search(without_ids):
                offences.append((str(event.get("kind")), where, text))
    assert offences == [], offences

    # And the redaction actually happened rather than the events going missing.
    kinds = {str(e.get("kind")) for e in events}
    assert {"tts", "model", "prediction", "a_kind_added_next_week"} <= kinds, kinds
    spoken = next(e for e in events if e.get("kind") == "tts")
    assert "[email]" in spoken["text"], spoken
    assert "two orders" in spoken["text"], "the sentence must survive, only the address goes"


def test_an_event_kind_nobody_has_written_yet_is_covered_too(recording):
    """The whole point of a seam. A new event kind cannot arrive unredacted, because there is
    nowhere for it to arrive from that does not pass through `scrub`."""
    line, store, session = recording
    timeline.note_names(NAMES)
    line.emit("something_new", session_id="s1",
              deep={"a": [{"b": {"c": "rowan.mitcham@example.co.uk"}}]},
              also="call 07700 900123 or write to NW1 6RA")
    line.flush()

    written = store.timeline_path(session).read_text(encoding="utf-8")
    assert "rowan.mitcham@example.co.uk" not in written
    assert "[email]" in written
    assert "07700 900123" not in written and "NW1 6RA" not in written


def test_the_seam_works_before_anything_tells_it_a_name(recording):
    """Shape redaction does not depend on `note_names` having run. A process that never reaches
    a turn — the recorder, the read scheduler, the ledger observer — still writes no address."""
    line, store, session = recording
    _write_the_session(line, tell_it_the_names=False)

    written = store.timeline_path(session).read_text(encoding="utf-8")
    assert "rowan.mitcham@example.co.uk" not in written
    assert "[email]" in written
    # The NAME survives, because a name is not a shape and nothing told it this one. That is
    # the honest limit of the seam, and it is why `note_names` exists.
    assert "Rowan Mitcham" in written


def test_the_names_a_turn_knows_reach_every_event_after_it(recording):
    """`note_names` is the one call the seam needs, and `app/routes/turn.py` makes it from the
    place that already computes the set (`session.pii_seen`)."""
    line, store, session = recording
    timeline.note_names(NAMES)
    line.emit("tts", session_id="s1", turn_id="turn_history",
              text="Rowan Mitcham, two orders, both today.")
    line.flush()

    written = store.timeline_path(session).read_text(encoding="utf-8")
    assert "Rowan Mitcham" not in written
    assert "[name]" in written and "two orders" in written


def test_the_route_that_knows_the_names_is_the_one_that_tells_the_seam():
    """A seam nobody feeds is a seam that only does shapes. Asserted against the source, so
    the single call cannot be removed without this failing."""
    source = Path("app/routes/turn.py").read_text(encoding="utf-8")
    assert "timeline.note_names(names)" in source, (
        "app/routes/turn.py must feed the timeline's redaction seam the names it already has")


# ------------------------------------------------------- what redaction must NOT take away


def test_the_ids_counts_and_milliseconds_a_report_is_built_from_survive(recording):
    """The timeline is the evidence every finding cites. A redactor that ate the ids would take
    the analyser with it, so the shapes that look like personal data and are not — Shopify
    GIDs, proposal ids, order numbers, hex ids, errnos, timestamped filenames — are protected
    by `app/logging/turnlog.py` and are asserted here."""
    line, store, session = recording
    timeline.note_names(NAMES)
    line.emit("tool_finished", session_id="s1", turn_id="turn_history",
              tool="shopify_order_detail", ok=True, ms=210.4,
              result={"order_id": "gid://shopify/Order/70000000000901",
                      "order_number": "CROOKS-1965",
                      "customer_id": "gid://shopify/Customer/70000000000003",
                      "proposal_id": "prop_037e20c6ea04",
                      "thread_id": "aa70d3f83dbef06e",
                      "total": "60.0 GBP", "audio": "20260907-225520.webm",
                      "error": "[Errno -1094995529]"})
    line.flush()

    written = store.timeline_path(session).read_text(encoding="utf-8")
    for kept in ("gid://shopify/Order/70000000000901", "gid://shopify/Customer/70000000000003",
                 "CROOKS-1965", "prop_037e20c6ea04", "aa70d3f83dbef06e", "60.0 GBP",
                 "20260907-225520.webm", "Errno -1094995529", "210.4"):
        assert kept in written, kept


def test_a_credential_is_still_withheld_and_still_scrubbed(recording):
    """The seam's older job, so redaction cannot have displaced it."""
    line, store, session = recording
    line.emit("tool_requested", session_id="s1", tool="shopify_order_detail",
              authorization="Bearer abcdefghijklmnopqrst",
              args={"token": "shpat_0123456789abcdef", "note": "shpat_0123456789abcdef"})
    line.flush()

    written = store.timeline_path(session).read_text(encoding="utf-8")
    assert "shpat_0123456789abcdef" not in written
    assert "[withheld]" in written and "[secret]" in written


def test_nothing_here_can_take_a_turn_down(recording):
    """Observability never raises. A name set full of nonsense, a value that cannot be
    serialised, a recursive structure — the event is written or it is dropped, and either way
    the caller returns."""
    line, store, session = recording
    timeline.note_names([None, "", "ab", 7, "Rowan Mitcham"])

    class Awkward:
        def __str__(self) -> str:
            return "Rowan Mitcham <rowan.mitcham@example.co.uk>"

    assert line.emit("odd", session_id="s1", thing=Awkward(), deep={"x": {"y": {"z": {"a": {"b": {"c": 1}}}}}})
    line.flush()
    written = store.timeline_path(session).read_text(encoding="utf-8")
    assert "rowan.mitcham@example.co.uk" not in written
    assert timeline.MAX_NAMES >= 1
