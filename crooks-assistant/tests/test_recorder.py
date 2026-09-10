"""The production experience recorder: what it captures, what it refuses to hold, and what it
cannot do.

Three things are held here, and the second and third are the point of the file:

    it captures enough structure to understand an interaction — the lane, the normalised
    intent, the entities, the tools planned and called, the cache counts, the cards, the tabs,
    the touches, the branch moves, the latencies, the corrections, Back, the errors and the
    prefetch — because it is handed the same events a test session is;

    it never holds a customer's words or address. Not "should not": the personal shapes are
    put THROUGH it here — an email address, a street, a postcode, a telephone number, a card
    number, a customer's name in every field that could carry one — and the file on disk is
    read back and searched for each of them;

    it cannot authorise a change. A recording of a session in which changes were armed and
    committed is replayed, saved as a test, and reported on, with the dispatcher and the arm
    and commit paths replaced by something that raises if it is ever reached.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.observability import recorder as recorder_module
from app.observability.recorder import Recorder, Recordings, save_as_test, scrub_personal
from app.observability.report import reconstruct
from app.observability.session import TestSessions
from app.observability.timeline import Timeline, read_events

# The personal data that must never survive. Each of these goes in somewhere different.
EMAIL = "mia.jones@example.com"
STREET = "14 Ravensbourne Road"
POSTCODE = "SE6 4TT"
PHONE = "+44 7700 900123"
CARD = "4242424242424242"
CUSTOMER = "Mia Jones"
SENTENCE = f"draft a reply to {CUSTOMER} about her hoodie"
PERSONAL = (EMAIL, STREET, POSTCODE, PHONE, CARD)


class Clock:
    def __init__(self, now: float = 1_800_000_000.0) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now


def _recorder(tmp_path, *, transcripts: bool = False) -> tuple[Recorder, Recordings]:
    store = Recordings(tmp_path, clock=Clock())
    return Recorder(store, clock=Clock(), keep_transcripts=transcripts), store


def _busy_hour(recorder: Recorder) -> None:
    """One interaction of every shape section 26 names, with a person's data in each of them."""
    recorder.emit("turn_started", session_id="s1", turn_id="turn_1", input="audio", turns_before=3, epoch=4,
                  focus={"type": "order", "ref": "gid://shopify/Order/1938", "label": CUSTOMER})
    recorder.emit("stt", session_id="s1", turn_id="turn_1", ok=True, engine="scribe", text=SENTENCE,
                  raw_text=SENTENCE + " " + PHONE, audio_s=2.4, timings={"transcribe": 900.0},
                  matches=["hoodie"], order_numbers=["1938"])
    recorder.emit("lane", session_id="s1", turn_id="turn_1", lane="FAST", why="", family="order_email_draft",
                  confidence=0.81, runner_up=None, reason=None, signals={"email": True, "question": True})
    recorder.emit("prefetch", session_id="s1", turn_id="turn_1", order_numbers=["1938"], hit=True, ms=31.0, hydrating=True)
    recorder.emit("read_plan", session_id="s1", turn_id="turn_1", label="order_email_draft", reads=["order", "threads"])
    recorder.emit("tool_requested", session_id="s1", turn_id="turn_1", tool_call_id="tc_1", tool="gmail_read_thread",
                  args={"thread_id": "aa70d3f83dbef06e", "to": EMAIL}, tier="read")
    recorder.emit("tool_finished", session_id="s1", turn_id="turn_1", tool_call_id="tc_1", tool="gmail_read_thread",
                  outcome="ok", ok=True, ms=210.0,
                  result={"thread_id": "aa70d3f83dbef06e", "from": EMAIL, "subject": "My hoodie",
                          "body": f"Hello, I live at {STREET}, {POSTCODE}. Ring me on {PHONE}.",
                          "customer": {"name": CUSTOMER, "address1": STREET, "postcode": POSTCODE, "card": CARD},
                          "orders": {"count": 1, "ids": ["gid://shopify/Order/1938"]}})
    recorder.emit("context_hydration", session_id="s1", hydration="order", order_id="gid://shopify/Order/1938",
                  ms=140.0, unavailable=[], reused_core=True)
    recorder.emit("working_set", session_id="s1", turn_id="turn_1", set_id="ws_1", set_kind="orders", count=3,
                  label=f"{CUSTOMER}'s orders", step="filter", tool="commerce_query")
    recorder.emit("cross_source", session_id="s1", turn_id="turn_1", set_id="ws_1", customers=3,
                  counts={"threads": 4}, ms=310.0)
    recorder.emit("turn_performance", session_id="s1", turn_id="turn_1", lane="FAST", recipe_id="order_email_reply",
                  fast_path_hit=True, model_calls=0, facts_ms=420.0, workspace_ms=460.0, prose_wait_ms=None,
                  turn_total_ms=980.0, cache={"hits": 7, "misses": 1}, tool_calls=1)
    recorder.emit("turn_finished", session_id="s1", turn_id="turn_1", question=SENTENCE,
                  answer=f"{CUSTOMER} asked about her hoodie. Reply to {EMAIL}?",
                  ui=["email_thread"], ui_entities=[{"type": "thread", "ref": "aa70d3f83dbef06e"}], ms=980.0,
                  timings={"total": 980.0})
    recorder.emit("tablet_render", source="tablet", session_id="s1", turn_id="turn_1", screen="context",
                  cards=[{"i": 0, "type": "email_thread", "ref": "aa70d3f83dbef06e", "sections": ["Messages"],
                          "relations": ["order"], "tabs": ["Messages", "Order"]}],
                  viewport={"w": 601, "h": 889, "dpr": 1.33}, t=1_800_000_010_000)
    recorder.emit("tablet_tab", source="tablet", session_id="s1", turn_id="turn_1", label="Order")
    recorder.emit("tablet_hold", source="tablet", session_id="s1", turn_id="turn_1", phase="multitouch", fingers=2, target="orb")
    recorder.emit("tablet_navigate", source="tablet", session_id="s1", turn_id="turn_1", nav="back", **{"from": 2, "to": 1})
    recorder.emit("command", session_id="s1", branch_id="br_left", command="open.entity", ok=True, ms=11.0, entity="order")
    recorder.emit("branch_forked", session_id="s1", branch_id="br_right", parent_branch_id="br_left")
    # The changes: armed, committed, proven. Every one of these is a RECORD of a change that
    # already happened, and none of them is a way to make one.
    recorder.emit("action_proposed", session_id="s1", turn_id="turn_1", proposal_id="pr_1", event="PROPOSED",
                  operation="gmail_draft_reply", tool="gmail_draft_reply", risk="AMBER", interaction="tap_commit",
                  entity_kind="thread", entity_label=f"{CUSTOMER} — My hoodie", arm_nonce="nonce-please-do-not-keep-me")
    recorder.emit("action_executing", session_id="s1", turn_id="turn_1", proposal_id="pr_1", event="EXECUTING")
    recorder.emit("action_verified", session_id="s1", turn_id="turn_1", proposal_id="pr_1", event="VERIFIED",
                  status="VERIFIED", code="verified", verified=True, ms=640.0)
    recorder.emit("tts", session_id="s1", turn_id="turn_1", ok=True, ms_first_byte=610.0, chars=88, ms=1400.0)
    recorder.flush()


# ------------------------------------------------------------------- what it holds


def test_a_recording_captures_the_structure_of_an_interaction(tmp_path):
    recorder, store = _recorder(tmp_path)
    session = recorder.start("thursday afternoon")
    assert session.test_session_id.startswith("rec-"), "a recording is never mistaken for a test session"
    assert store.root.name == recorder_module.DIR_NAME
    assert TestSessions(tmp_path).root != store.root, "its own directory, beside the test sessions"
    _busy_hour(recorder)

    rec = reconstruct(read_events(store.timeline_path(session)))
    turn = rec.turn("turn_1")
    assert turn is not None and turn.input == "audio"
    # Every one of section 26's items, from the recording alone.
    assert turn.lane["lane"] == "FAST" and turn.lane["family"] == "order_email_draft" and turn.lane["confidence"] == 0.81
    assert sorted(turn.lane["signals"]) == ["email", "question"], "the normalised intent"
    assert turn.stt["order_numbers"] == ["1938"] and turn.stt["matches"] == ["hoodie"], "entities resolved"
    assert turn.stt["audio_s"] == 2.4 and turn.latency("stt") == 900.0
    assert turn.read_plans and turn.read_plans[0]["reads"] == ["order", "threads"], "tools planned"
    assert [x.tool for x in turn.tools] == ["gmail_read_thread"] and turn.tools[0].outcome == "ok", "tools called"
    assert turn.performance["cache"] == {"hits": 7, "misses": 1}, "cache hits"
    assert turn.latency("facts") == 420.0 and turn.latency("workspace") == 460.0 and turn.latency("total") == 980.0
    assert turn.prefetch["hit"] is True, "prediction / prefetch"
    assert turn.render["cards"][0]["type"] == "email_thread" and turn.render["cards"][0]["tabs"] == ["Messages", "Order"]
    assert [e["label"] for e in turn.tablet_events("tab")] == ["Order"], "tabs"
    assert turn.tablet_events("hold")[0]["fingers"] == 2, "touches"
    assert [e["nav"] for e in turn.tablet_events("navigate")] == ["back"], "Back"
    assert [str(e.get("kind")) for e in turn.branch_events] == ["branch_forked"], "branch changes"
    assert [str(e.get("command")) for e in turn.commands] == ["open.entity"]
    assert turn.proposals and turn.proposals[0].status == "VERIFIED", "actions"
    assert turn.hydrations and turn.hydrations[0]["reused_core"] is True
    assert turn.sets and {str(e["kind"]) for e in turn.sets} == {"working_set", "cross_source"}
    assert turn.tts[0]["ms_first_byte"] == 610.0

    counts = recorder.counts
    assert counts["on_disk"] >= 20 and counts["dropped"] == 0
    stopped = recorder.stop()
    assert stopped is not None and store.active() is None and store.last().test_session_id == session.test_session_id


def test_a_recording_holds_no_customers_words_and_no_address(tmp_path):
    """The rule, as a test rather than a promise: ids, counts, tool names and milliseconds."""
    recorder, store = _recorder(tmp_path)
    session = recorder.start("thursday afternoon")
    _busy_hour(recorder)
    raw = store.timeline_path(session).read_text(encoding="utf-8")

    for personal in PERSONAL:
        assert personal not in raw, personal
    assert CUSTOMER not in raw, "a customer's name, in the focus label, the set label and the answer"
    assert SENTENCE not in raw and "hoodie about" not in raw
    assert "nonce-please-do-not-keep-me" not in raw, "nothing that could be replayed as an authorisation"
    for word in ("Hello, I live at", "My hoodie", "asked about her"):
        assert word not in raw, word

    # And what it DOES hold, so the minimisation is not simply an empty file.
    events = read_events(store.timeline_path(session))
    finished = next(e for e in events if e["kind"] == "turn_finished")
    assert finished["question_chars"] == len(SENTENCE) and finished["question_words"] == len(SENTENCE.split())
    assert "question" not in finished and "answer" not in finished
    assert finished["ms"] == 980.0 and finished["ui"] == ["email_thread"]
    tool = next(e for e in events if e["kind"] == "tool_finished")
    assert tool["tool"] == "gmail_read_thread" and tool["ms"] == 210.0
    assert tool["result"]["orders"] == {"count": 1, "ids": ["gid://shopify/Order/1938"]}
    assert tool["result"]["thread_id"] == "aa70d3f83dbef06e"
    assert "customer" in tool["result"] and tool["result"]["customer"] == {}, "the customer is a shape with nothing in it"
    assert next(e for e in events if e["kind"] == "tablet_tab")["label"] == "Order", "a tab's caption is controlled vocabulary"
    assert next(e for e in events if e["kind"] == "lane")["signals"] == {"email": True, "question": True}, \
        "`email: true` is a router signal, not an email address"
    assert all(e.get("recorded") is True for e in events if e["kind"] != "session_started" or True)


def test_the_transcript_is_kept_only_when_it_is_asked_for_and_is_scrubbed_even_then(tmp_path):
    plain, store = _recorder(tmp_path, transcripts=False)
    session = plain.start("shape only")
    plain.emit("stt", session_id="s1", turn_id="t1", ok=True, text=SENTENCE, raw_text=f"{SENTENCE} {PHONE}")
    plain.flush()
    events = read_events(store.timeline_path(session))
    stt = next(e for e in events if e["kind"] == "stt")
    assert "text" not in stt and "raw_text" not in stt
    assert stt["text_chars"] == len(SENTENCE) and stt["raw_text_words"] == len(SENTENCE.split()) + 3
    plain.stop()

    kept, store2 = _recorder(tmp_path, transcripts=True)
    session2 = kept.start("diagnosing a mishearing")
    kept.emit("stt", session_id="s1", turn_id="t1", ok=True, text=f"send it to {EMAIL} at {STREET}, {POSTCODE}",
              raw_text=f"ring {PHONE}")
    kept.flush()
    raw = store2.timeline_path(session2).read_text(encoding="utf-8")
    assert "send it to" in raw, "the sentence is kept when it is asked for"
    for personal in (EMAIL, STREET, POSTCODE, PHONE):
        assert personal not in raw, personal
    assert "[email]" in raw and "[street]" in raw and "[postcode]" in raw and "[phone]" in raw


def test_the_scrub_leaves_the_ids_the_counts_and_the_milliseconds():
    kept = scrub_personal({"order_id": "gid://shopify/Order/1938", "count": 3, "ms": 210.5, "ok": True,
                           "tool": "gmail_read_thread", "ids": ["aa70d3f83dbef06e"], "nothing": None,
                           "name": CUSTOMER, "address1": STREET, "body": "words", "nested": {"phone": PHONE}})
    assert kept == {"order_id": "gid://shopify/Order/1938", "count": 3, "ms": 210.5, "ok": True,
                    "tool": "gmail_read_thread", "ids": ["aa70d3f83dbef06e"], "nothing": None, "nested": {}}
    assert scrub_personal(f"posted to {EMAIL}") == "posted to [email]"
    assert scrub_personal(f"deliver to {STREET}, {POSTCODE}") == "deliver to [street], [postcode]"
    assert scrub_personal({"email": True, "phone": 2}) == {"email": True, "phone": 2}, "a flag and a count are not a person"
    assert scrub_personal({"detail": "anything"}) == {}, "a free-text field is dropped by its key alone"


# ------------------------------------------------------- recording is not fixture mode


def test_recording_is_off_by_default_and_changes_nothing_about_a_turn(tmp_path):
    from config.settings import Settings

    settings = Settings(_env_file=None)
    assert settings.record_experience is False and settings.record_transcripts is False

    # With no recorder installed the timeline behaves exactly as it always did.
    tests = TestSessions(tmp_path, clock=Clock())
    timeline = Timeline(tests, clock=Clock())
    assert timeline.mirror is None
    assert timeline.emit("turn_started", session_id="s1") is None, "no test session: nothing written"

    # With one, the test session's own behaviour is untouched and the recording is a second
    # file. A recording running while no test session does is the ordinary case.
    recorder, recordings = _recorder(tmp_path)
    timeline.mirror = recorder
    recording = recorder.start("in production")
    assert timeline.emit("turn_started", session_id="s1", turn_id="t1", input="audio") is None
    recorder.flush()
    assert read_events(recordings.timeline_path(recording))[-1]["turn_id"] == "t1"
    assert tests.active() is None, "recording did not start a test session"
    assert not list(tests.root.glob("*.jsonl")) if tests.root.exists() else True


def test_a_recording_cannot_authorise_a_change(monkeypatch, tmp_path):
    """A recording is a record. Saving one as a test, listing its interactions and reporting on
    it are all reads: the dispatcher, the arm and the commit are replaced here by something
    that raises, and the recording that is put through them is one full of changes."""
    import app.tools.dispatch as dispatch_module
    from app.actions import engine as engine_module

    def refuse(*args, **kwargs):  # noqa: ARG001
        raise AssertionError("a recording reached a write path")

    monkeypatch.setattr(dispatch_module, "dispatch", refuse)
    monkeypatch.setattr(engine_module.ActionEngine, "arm", refuse, raising=False)
    monkeypatch.setattr(engine_module.ActionEngine, "commit", refuse, raising=False)

    recorder, store = _recorder(tmp_path)
    session = recorder.start("an hour of changes")
    _busy_hour(recorder)
    path = store.timeline_path(session)
    recorder.stop()

    rows = recorder_module.interactions(path)
    assert [r["turn_id"] for r in rows] == ["turn_1"] and rows[0]["lane"] == "FAST"
    written = save_as_test(path, tmp_path / "fixtures")
    manifest = json.loads(written["manifest"].read_text(encoding="utf-8"))
    assert manifest["turn_id"] == "turn_1" and manifest["lane"] == "FAST" and manifest["family"] == "order_email_draft"
    assert manifest["tools"] == [{"tool": "gmail_read_thread", "outcome": "ok", "ok": True}]
    assert manifest["cards"] == ["email_thread"] and manifest["tabs"] == ["Order"]
    assert manifest["commands"] == ["open.entity"] and manifest["ms"]["total"] == 980.0
    assert manifest["proposals"] == [{"operation": "gmail_draft_reply", "risk": "AMBER", "status": "VERIFIED"}]

    both = written["timeline"].read_text(encoding="utf-8") + written["manifest"].read_text(encoding="utf-8")
    for forbidden in ("nonce", "arm_nonce", "authorization", "Bearer", "shpat_"):
        assert forbidden not in both, forbidden
    for personal in (*PERSONAL, CUSTOMER):
        assert personal not in both, personal

    # And the fixture is a fixture: the report reads it exactly as it reads a live session.
    from app.observability.report import build_report

    replayed, markdown = build_report(written["timeline"], tools_registered=["gmail_read_thread"])
    assert [t.turn_id for t in replayed.turns] == ["turn_1"]
    assert replayed.turn("turn_1").lane["family"] == manifest["family"]
    assert "## 1. Session summary" in markdown and "Interactions: **1** turns" in markdown


def test_the_recorder_module_never_imports_a_write_path():
    """A source check, so the property above cannot be lost by an import somebody adds later."""
    source = Path(recorder_module.__file__).read_text(encoding="utf-8")
    for forbidden in ("actions.engine", "shopify_writes", "gmail_writes", "tools.dispatch",
                      "ActionEngine", "def arm", "def commit"):
        assert forbidden not in source, forbidden


def test_saving_an_interaction_that_is_not_there_says_so(tmp_path):
    recorder, store = _recorder(tmp_path)
    session = recorder.start("empty")
    recorder.flush()
    path = store.timeline_path(session)
    with pytest.raises(ValueError, match="no interaction to save"):
        save_as_test(path, tmp_path / "fixtures")
    _busy_hour(recorder)
    with pytest.raises(ValueError, match="no interaction 'turn_missing'"):
        save_as_test(path, tmp_path / "fixtures", turn_id="turn_missing")


def test_the_cli_refuses_to_start_a_recording_the_backend_would_not_write(monkeypatch, tmp_path, capsys):
    import scripts.record as cli
    from config.settings import Settings

    monkeypatch.setattr(cli, "_settings", lambda: Settings(_env_file=None, log_dir=tmp_path))
    assert cli.main(["start", "--name", "nope"]) == 2
    assert "CROOKS_RECORD_EXPERIENCE=true" in capsys.readouterr().err
    assert not (tmp_path / recorder_module.DIR_NAME).exists()

    on = Settings(_env_file=None, log_dir=tmp_path, record_experience=True)
    monkeypatch.setattr(cli, "_settings", lambda: on)
    assert cli.main(["start", "--name", "thursday"]) == 0
    started = capsys.readouterr().out.strip()
    assert started.startswith("rec-") and started.endswith("-thursday")
    assert cli.main(["status"]) == 0 and capsys.readouterr().out.strip() == started
    assert cli.main(["stop"]) == 0 and capsys.readouterr().out.strip() == started
    assert cli.main(["status"]) == 0 and "not recording" in capsys.readouterr().out
