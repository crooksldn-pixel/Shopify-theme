"""What the owner says about the product, while he is testing it (§16).

Twice in the live hour:

    "please log that your split function is broken. It just shows two of the same thing, and
     the applying button is also broken"
    → "I've no tool for logging a product bug like that."

    "Log--a lot of your functions are broken… especially with the back button, back to
     assistant button and the next button"
    → "I still have no tool that logs product feedback."

Both sentences are in this file. They are recognised, recorded against the screen he was on,
and surfaced verbatim in the report (tests/test_experience_analyser.py holds that half).

The other half of the file is the bound: nothing reaches Shopify or Gmail, nothing is
proposed, approved or armed, no customer's name or address is written down, and outside a
test session nothing is recorded at all.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.observability import feedback, timeline
from app.observability.session import TestSessions

# The two sentences, as the tablet heard them.
SPLIT_BUG = ("Okay, uh, please log that your split function is broken. It just so shows two of "
             "the same thing, and the applying button is also broken, and it just is a "
             "continuous applying animation")
REGRESSIONS = ("Log--a lot of your functions are broken or halfway there. It seems as if they've "
               "regressed, um, especially with the back button, back to assistant button and the "
               "next button.")


class FakeBranch:
    """A half of the conversation, as much of one as this needs."""

    def __init__(self) -> None:
        self.branch_id = "br_left"
        self.status = "ACTIVE"
        self.tab = "shipping"
        self.entity = {"kind": "email_thread", "ref": "aa70d3f83dbef06e", "label": "Anna Example"}
        self.recent_entities = [{"kind": "order", "ref": "gid://shopify/Order/1938", "label": "#1938"}]
        self.last_ui = [{"type": "email_thread", "data": {}}, {"type": "confirmation", "data": {}}]


@pytest.fixture()
def recording(tmp_path, monkeypatch):
    """A test session, running, writing to a temporary directory."""
    store = TestSessions(Path(tmp_path))
    line = timeline.install(timeline.Timeline(store))
    session = line.start("the live hour")
    yield line, store, session
    line.stop()
    timeline.install(timeline.NullTimeline())


def _events(store, session) -> list[dict]:
    path = store.timeline_path(session)
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


# ------------------------------------------------------------------- what is recognised


@pytest.mark.parametrize(("said", "kind"), [
    (SPLIT_BUG, "log"),
    (REGRESSIONS, "log"),
    ("please log that the applying button never stops", "log"),
    ("note that the split shows two of the same thing", "note"),
    ("note this bug: home does nothing", "note"),
    ("record that the next button does nothing", "record"),
    ("write that down, back is broken", "record"),
    ("save this as a test", "save_as_test"),
    ("turn that into a test", "save_as_test"),
    ("the back button is broken", "broken"),
    ("the split doesn't work at all", "broken"),
    ("that's a bug", "broken"),
])
def test_the_sentences_a_tester_uses_are_recognised(said, kind):
    got = feedback.recognise(said)
    assert got is not None, said
    assert got.kind == kind, (said, got.kind)
    assert got.text.startswith(said.split(".")[0][:20])


@pytest.mark.parametrize("said", [
    "log in to shopify",
    "the log says the token expired",
    "the order is wrong",
    "that customer's address is broken",
    "the delivery is broken",
    "show me today's orders",
    "refund the postage on 1938",
    "",
])
def test_a_sentence_about_the_shop_is_not_a_bug_report(said):
    """"The order is wrong" is a job. "The back button is broken" is a defect. A rule that
    could not tell them apart would turn every complaint about a parcel into a bug."""
    assert feedback.recognise(said) is None, said


# ------------------------------------------------------------------------ what is written


def test_the_feedback_is_appended_with_the_screen_the_owner_was_on(recording):
    line, store, session = recording
    event = feedback.record(feedback.recognise(SPLIT_BUG), branch=FakeBranch(),
                            session_id="s1", turn_id="turn_7afa465dda1d")
    assert event is not None
    line.flush()

    written = [e for e in _events(store, session) if e["kind"] == "owner_feedback"]
    assert len(written) == 1
    got = written[0]
    # Timestamp, branch, visible screen, entity refs, the words, and the ids nearby.
    assert got["ts"] > 0 and got["iso"]
    assert got["branch_id"] == "br_left" and got["branch_status"] == "ACTIVE"
    assert got["turn_id"] == "turn_7afa465dda1d" and got["session_id"] == "s1"
    assert got["kind"] == "owner_feedback" and got["shape"] == "log"
    assert got["text"].startswith("Okay, uh, please log that")
    assert got["screen"] == ["email_thread", "confirmation"]
    assert {"kind": "email_thread", "ref": "aa70d3f83dbef06e"} in got["entities"]
    assert {"kind": "order", "ref": "gid://shopify/Order/1938"} in got["entities"]
    assert got["tab"] == "shipping"


def test_the_words_are_kept_verbatim_and_the_labels_are_not(recording):
    """The owner's own words about his own product, as he said them — that is what the report
    prints. Everything AROUND them is an id: no customer's name, no address, no label."""
    line, store, session = recording
    feedback.record(feedback.recognise(REGRESSIONS), branch=FakeBranch(), session_id="s1")
    line.flush()
    got = next(e for e in _events(store, session) if e["kind"] == "owner_feedback")

    assert got["text"] == " ".join(REGRESSIONS.split())
    blob = json.dumps(got)
    assert "Anna Example" not in blob and "#1938" not in blob, "labels are not ids"
    for entity in got["entities"]:
        assert set(entity) == {"kind", "ref"}


def test_the_ids_of_what_was_happening_nearby_travel_with_it(recording):
    """"The applying button is broken" is worth far more with the ids of the taps and the
    changes either side of it."""
    line, store, session = recording
    timeline.emit("command", session_id="s1", branch_id="br_left", command="navigation.home", ok=True, ms=0.2)
    timeline.emit("action_verified", session_id="s1", proposal_id="prop_037e20c6ea04",
                  operation="gmail_send_reply", status="VERIFIED", verified=True)
    timeline.emit("tablet_reconcile", source="tablet", session_id="s1", reason="turn", count=2, kept=2)
    # Something that is not a correlation worth keeping.
    timeline.emit("tablet_scroll", source="tablet", session_id="s1", depth=1400)

    feedback.record(feedback.recognise(SPLIT_BUG), branch=FakeBranch(), session_id="s1")
    line.flush()
    got = next(e for e in _events(store, session) if e["kind"] == "owner_feedback")
    kinds = [row["kind"] for row in got["nearby"]]
    assert "command" in kinds and "action_verified" in kinds and "tablet_reconcile" in kinds
    assert "tablet_scroll" not in kinds, "a scroll is not what somebody was doing"
    ids = [row["id"] for row in got["nearby"]]
    assert "prop_037e20c6ea04" in ids and "navigation.home" in ids


def test_a_stale_command_is_not_reported_as_nearby(recording):
    line, _store, _session = recording
    timeline.emit("command", session_id="s1", command="navigation.home", ok=True, ts=1_000.0)
    assert line.recent(within_s=90.0, now=1_000_000.0) == []
    assert [r["id"] for r in line.recent(within_s=90.0, now=1_000.5)] == ["navigation.home"]


def test_nothing_is_recorded_when_no_session_is_being_tested():
    """On an ordinary day there is nowhere to put this, and the honest answer is the one the
    assistant already gives."""
    timeline.install(timeline.NullTimeline())
    assert feedback.active() is False
    assert feedback.record(feedback.recognise(SPLIT_BUG), branch=FakeBranch()) is None


# ------------------------------------------------------------ what it cannot possibly do


def test_recording_feedback_reaches_neither_shopify_nor_gmail_nor_the_engine():
    """A bug report is not a change. This module imports no tool, no client and no part of
    the action engine, and nothing in it can arm or commit."""
    import ast
    import inspect

    tree = ast.parse(inspect.getsource(feedback))
    imported = {
        (node.module or "") for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
    } | {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
    for module in imported:
        assert not module.startswith(("app.actions", "app.tools", "app.clients", "app.providers")), module
    assert imported <= {"__future__", "re", "dataclasses", "typing", "app.observability"}


def test_the_family_records_and_says_so(recording):
    from app.families import load_all
    from app.fastpath.intent import resolve
    from app.fastpath.models import Ctx
    from app.fastpath.recipes import RECIPES, assert_read_only
    from app.reads.scheduler import ReadResult

    load_all()
    line, store, session = recording
    assert resolve(SPLIT_BUG).family == "owner_feedback", "the router takes it now"

    recipe = RECIPES["owner_feedback"]
    assert recipe.read_primitives == ()
    assert_read_only({"owner_feedback": recipe})

    class FakeSession:
        session_id = "s1"
        turn_id = "turn_7afa465dda1d"

    ctx = Ctx(runtime=None, session=FakeSession(), branch=FakeBranch(),
              intent=resolve(SPLIT_BUG), text=SPLIT_BUG)
    assert recipe.plan(ctx) is None, "nothing is read to write something down"
    answer = recipe.render(ctx, ReadResult())
    assert not answer.deferred, answer.defer
    assert "Logged" in answer.answer and "owner-reported defects" in answer.answer
    assert "Nothing was sent anywhere." in answer.answer
    assert answer.calls == [] and answer.surfaces == []
    line.flush()
    assert [e for e in _events(store, session) if e["kind"] == "owner_feedback"]


def test_the_family_is_silent_outside_a_test_session():
    from app.families import load_all
    from app.fastpath.intent import resolve

    load_all()
    timeline.install(timeline.NullTimeline())
    assert resolve(SPLIT_BUG).family != "owner_feedback"
    assert resolve("the back button is broken").family != "owner_feedback"
