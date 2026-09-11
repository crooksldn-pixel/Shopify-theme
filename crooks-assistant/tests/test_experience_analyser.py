"""The analyser, held against the hour it scored eleven successful of fourteen (§17).

The Phase 3C live tablet test produced a report that said **11 successful, 2 partial, 1
failed**. During that hour the owner said, out loud, that the split was broken, that the
applying button was broken, and that Back, Back-to-assistant and Next had regressed. The old
report's own words for the evidence were "Potential new actions: _none_".

This file rebuilds each of those failures as a FIXTURE timeline — the same event kinds, the
same fields, the same order — so that nothing here depends on the real session, which holds
real customer names and stays in `logs/`. Every case is written as a pair, in the idiom of
tests/test_analyser.py: what the September rule said, asserted, and what is said now.

    ACTION_UI_STUCK             six reconciles keeping two settled cards → nothing
    SPLIT_NO_REDRAW             four focus changes drawing nothing       → nothing
    SPLIT_DUPLICATE_SURFACE     two halves, one screen                   → nothing
    WRONG_BRANCH_SURFACE        a control served on the other half       → nothing
    DUPLICATE_RENDER            the same card three times in a second    → nothing
    PROGRESSIVE_RENDER_MISSING  eight seconds of the previous screen     → nothing
    NAV_SEMANTIC_MISMATCH       8 Home + 4 Back in 22 s, all ok=true     → "100 % accepted"
    FAKE_CONTROL                a control refused not_held under a thumb → nothing
    DEAD_CONTROL                a tap accepted and nothing drawn         → nothing
    STALE_PENDING_ACTION        two undos counted as work outstanding    → "2 changes waiting"
    FOREGROUND_STARVED          the owner's read refused by speculation  → nothing
    SELF_UI_KNOWLEDGE_ERROR     "I don't know what that button is"       → nothing
    OWNER_FEEDBACK_IGNORED      two defects narrated, nothing recorded   → nothing
    COLLISION                   two fingers, two overlapping controls    → nothing
    FOCUS_LOST                  the keyboard and the scroll taken away   → nothing

The acceptance run against the real timeline is `test_the_real_session_is_read_as_it_was_lived`,
which is skipped where that file is not present.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from app.observability import visible
from app.observability.report import build_report, reconstruct
from app.observability.timeline import read_events

T0 = 1_800_000_000.0
SESSION = "ts-20260911-001845-fixture"
THREAD = "aa70d3f83dbef06e"
ORDER = "gid://shopify/Order/1938"


class Tape:
    """A timeline, written the way the Mac and the tablet write one."""

    def __init__(self, session_id: str = SESSION, start: float = T0) -> None:
        self.session_id = session_id
        self.now = start
        self.seq = 0
        self.events: list[dict[str, Any]] = []
        self.add("session_started", name="the live hour", started_at=start)

    def add(self, kind: str, *, source: str = "mac", step: float = 0.1, **fields: Any) -> dict[str, Any]:
        self.now += step
        self.seq += 1
        event = {"ts": round(self.now, 3), "iso": "2026-09-11T00:18:45", "seq": self.seq,
                 "test_session_id": self.session_id, "source": source, "kind": kind}
        event.update({k: v for k, v in fields.items() if v is not None})
        self.events.append(event)
        return event

    def gap(self, seconds: float = 30.0) -> None:
        self.now += seconds

    def write(self, tmp_path: Path) -> Path:
        self.add("session_stopped", name="the live hour", duration_s=round(self.now - T0, 3))
        Path(tmp_path).mkdir(parents=True, exist_ok=True)
        path = Path(tmp_path) / f"{self.session_id}.jsonl"
        path.write_text("".join(json.dumps(e) + "\n" for e in self.events), encoding="utf-8")
        return path


def turn(tape: Tape, turn_id: str, *, said: str = "", answer: str = "", ui: list[str] | None = None,
         ms: float = 900.0, workspace_ms: float | None = None, error_kind: str | None = None) -> str:
    tape.add("turn_started", session_id="s1", turn_id=turn_id, input="audio", turns_before=0, epoch=1)
    if said:
        tape.add("stt", session_id="s1", turn_id=turn_id, ok=True, engine="scribe", text=said,
                 raw_text=said, audio_s=2.2)
        tape.add("lane", session_id="s1", turn_id=turn_id, lane="NORMAL", branch_id="br_left",
                 family=None, confidence=0.0, reason="no family matched", signals={"question": True})
    if workspace_ms is not None:
        tape.add("turn_performance", session_id="s1", turn_id=turn_id, lane="NORMAL",
                 model_calls=1, workspace_ms=workspace_ms, turn_total_ms=workspace_ms)
    tape.add("turn_finished", session_id="s1", turn_id=turn_id, question=said or None,
             answer=answer or "Right.", ui=ui or ["assistant"], ms=ms, error_kind=error_kind,
             timings={"total": ms})
    return turn_id


def render(tape: Tape, turn_id: str, cards: list[dict[str, Any]], *, screen: str = "context",
           step: float = 0.1) -> dict[str, Any]:
    return tape.add("tablet_render", source="tablet", session_id="s1", turn_id=turn_id, screen=screen,
                    cards=cards, step=step, viewport={"w": 601, "h": 889, "dpr": 1.33},
                    document={"cards_height": 923, "cards_visible": 680},
                    overflow={"long_scroll": True, "clipped": 0}, t=int(tape.now * 1000))


def a_verified_send(tape: Tape, turn_id: str, proposal: str = "prop_037e20c6ea04",
                    operation: str = "gmail_send_reply") -> None:
    """A change staged, held, executed and proved — the shape of the live hour's third turn."""
    for kind, status in (("action_proposed", "PENDING"), ("action_delivered", "PENDING"),
                         ("action_armed", "PENDING"), ("action_executing", "EXECUTING"),
                         ("action_executed", "EXECUTED")):
        tape.add(kind, session_id="s1", turn_id=turn_id, proposal_id=proposal,
                 event=kind.removeprefix("action_").upper(), operation=operation, tool=operation,
                 risk="RED", interaction="hold_to_arm", status=status)
    tape.add("action_verified", session_id="s1", turn_id=turn_id, proposal_id=proposal,
             event="VERIFIED", operation=operation, tool=operation, status="VERIFIED",
             code="verified", verified=True)
    tape.add("action_commit", session_id="s1", turn_id=turn_id, proposal_id=proposal,
             operation=operation, status="VERIFIED", code="verified", verified=True, ms=1756.0)
    tape.add("tablet_action_commit", source="tablet", session_id="s1", turn_id=turn_id,
             proposal_id=proposal, status="verified", code="verified", outcome="answered",
             ms=1756, detail="200", t=int(tape.now * 1000))


# --------------------------------------------------------------------------- the fixtures


def applying_stuck(tmp_path: Path) -> Path:
    """D-1. A verified send, then six reconciles that each keep the same two settled cards."""
    tape = Tape()
    first = turn(tape, "turn_send", said="okay, how do we send?", answer="It's sent.",
                 ui=["confirmation"])
    a_verified_send(tape, first)
    render(tape, first, [{"i": 0, "type": "confirmation", "proposal_id": "prop_037e20c6ea04",
                          "surface": {"kind": "hold_to_arm", "state": "committing"}}])
    for n in range(6):
        tape.gap(12.0)
        later = turn(tape, f"turn_after_{n}",
                     said="why has the email actually sent but the applying button is still going?",
                     answer="It's sent.", ui=["email_thread"])
        tape.add("tablet_reconcile", source="tablet", session_id="s1", turn_id=later,
                 reason="turn", count=2, kept=2, cancelled=0, t=int(tape.now * 1000))
        render(tape, later, [{"i": 0, "type": "email_thread", "ref": THREAD}])
    return tape.write(tmp_path)


def one_correction(tmp_path: Path) -> Path:
    """The control for D-1: a single reconcile that settles a card and never comes back. That
    is reconcile doing its job, and it must not be reported as a stuck surface."""
    tape = Tape()
    first = turn(tape, "turn_send", said="okay, how do we send?", answer="It's sent.")
    a_verified_send(tape, first)
    tape.gap(12.0)
    later = turn(tape, "turn_next", said="what else came in?", answer="Two threads.",
                 ui=["email_list"])
    tape.add("tablet_reconcile", source="tablet", session_id="s1", turn_id=later, reason="turn",
             count=1, kept=1, cancelled=0, t=int(tape.now * 1000))
    render(tape, later, [{"i": 0, "type": "email_list"}])
    tape.gap(12.0)
    third = turn(tape, "turn_third", said="and the orders?", answer="Ten.", ui=["order_list"])
    render(tape, third, [{"i": 0, "type": "order_list"}])
    return tape.write(tmp_path)


def a_split_that_showed_two_of_the_same(tmp_path: Path) -> Path:
    """D-3. A fork, then focus changes that draw nothing, and one that draws the parent's
    screen — plus a control served on the half that was not focused."""
    tape = Tape()
    only = turn(tape, "turn_split", said="take that aside", answer="Divided.", ui=["email_thread"])
    render(tape, only, [{"i": 0, "type": "email_thread", "ref": THREAD}])
    tape.add("branch_forked", session_id="s1", branch_id="br_right", parent_branch_id="br_left")
    tape.add("tablet_toast", source="tablet", session_id="s1", turn_id=only,
             message="Divided. Tap a half to talk to it; the other keeps working.", name="note")
    tape.gap(50.0)
    # The half is focused and draws the same cards as the half before it.
    tape.add("branch_focused", session_id="s1", branch_id="br_right")
    render(tape, only, [{"i": 0, "type": "email_thread", "ref": THREAD}])
    # And then four focus changes with nothing drawn at all.
    for branch in ("br_left", "br_right", "br_left", "br_right"):
        tape.add("branch_focused", session_id="s1", branch_id=branch, step=2.0)
    tape.gap(20.0)
    # A control served on the half that is not the focused one.
    tape.add("command", session_id="s1", turn_id=only, branch_id="br_left", command="open.entity",
             ok=True, ms=0.2, entity="order", replayed=True)
    render(tape, only, [{"i": 0, "type": "order", "ref": ORDER}])
    return tape.write(tmp_path)


def the_screen_redrawn_and_late(tmp_path: Path) -> Path:
    """D-5 and D-13. Nothing at all until everything was ready, and then the same card three
    times inside a second."""
    tape = Tape()
    late = turn(tape, "turn_correlate",
                said="look up today's orders and today's emails and see if anything correlates",
                answer="Nothing correlates.", ui=["order_list"], ms=7975.0, workspace_ms=7975.2)
    render(tape, late, [{"i": 0, "type": "order_list"}], step=8.0)
    tape.gap(20.0)
    again = turn(tape, "turn_open", said="open that order", answer="#1938.", ui=["order"],
                 workspace_ms=680.0)
    for _ in range(3):
        render(tape, again, [{"i": 0, "type": "order", "ref": ORDER}], step=0.3)
    return tape.write(tmp_path)


def eight_homes_and_four_backs(tmp_path: Path) -> Path:
    """D-10. Twenty-two seconds of navigation, every one accepted, and a Home that replays the
    record already in hand instead of reaching a landing."""
    tape = Tape()
    hunting = turn(tape, "turn_lost", said="can you pull up the today's emails",
                   answer="Eight new things.", ui=["email_thread"])
    for n in range(12):
        name = "navigation.home" if n % 3 != 1 else "navigation.back"
        tape.add("command", session_id="s1", turn_id=hunting, branch_id="br_left", command=name,
                 ok=True, ms=0.1, step=1.8,
                 entity="email_thread" if name == "navigation.home" else None,
                 replayed=name == "navigation.home")
        render(tape, hunting, [{"i": 0, "type": "email_thread", "ref": THREAD}], step=0.2)
    return tape.write(tmp_path)


def controls_with_nothing_behind_them(tmp_path: Path) -> Path:
    """D-3's other half and D-11. A dock landing refused, a record refused not_held, a chip
    tapped while disabled — and a Next accepted with nothing drawn."""
    tape = Tape()
    only = turn(tape, "turn_taps", said="pull up yesterday's orders", answer="Ten orders.",
                ui=["order_list"])
    render(tape, only, [{"i": 0, "type": "order_list", "actions": [{"id": "refund", "enabled": False,
                                                                    "reason": "the order is not paid"}]}])
    tape.add("command", session_id="s1", turn_id=only, branch_id="br_left", command="open.area",
             ok=False, code="landing_unavailable", ms=3.0)
    tape.add("command", session_id="s1", turn_id=only, branch_id="br_left", command="open.entity",
             ok=False, code="not_held", ms=1.0)
    tape.add("tablet_rail_tap", source="tablet", session_id="s1", turn_id=only, action="refund",
             state="disabled", t=int(tape.now * 1000))
    tape.add("tablet_navigate", source="tablet", session_id="s1", turn_id=only, nav="dead_chip",
             t=int(tape.now * 1000))
    # A Next accepted, and nothing drawn after it for the rest of the session.
    tape.add("command", session_id="s1", turn_id=only, branch_id="br_left", command="workflow.next",
             ok=True, ms=0.4)
    tape.gap(30.0)
    return tape.write(tmp_path)


def two_undos_counted_as_work(tmp_path: Path) -> Path:
    """D-2. Two undo offers for changes that succeeded, still PENDING at the end, and a merge
    that warned about them."""
    tape = Tape()
    first = turn(tape, "turn_draft", said="draft a reply", answer="Drafted.", ui=["confirmation"])
    a_verified_send(tape, first, proposal="prop_d90e88a91d3a", operation="gmail_draft_reply")
    tape.add("action_proposed", session_id="s1", turn_id=first, proposal_id="prop_2d39c24040cd",
             event="PROPOSED", operation="gmail_draft_reply_undo", tool="gmail_draft_reply_undo",
             risk="AMBER", interaction="tap_commit", status="PENDING", undo_of="prop_d90e88a91d3a")
    tape.gap(60.0)
    second = turn(tape, "turn_archive", said="archive it", answer="Archived.", ui=["confirmation"])
    a_verified_send(tape, second, proposal="prop_d9d3ad76b4ab", operation="gmail_thread_archive")
    tape.add("action_proposed", session_id="s1", turn_id=second, proposal_id="prop_0e24a4b8c57e",
             event="PROPOSED", operation="gmail_thread_archive_undo", tool="gmail_thread_archive_undo",
             risk="AMBER", interaction="tap_commit", status="PENDING", undo_of="prop_d9d3ad76b4ab")
    tape.gap(60.0)
    third = turn(tape, "turn_merge", said="merge", answer="Merged.", ui=["assistant"])
    tape.add("branch_merged", session_id="s1", branch_id="br_right")
    tape.add("tablet_toast", source="tablet", session_id="s1", turn_id=third,
             message="Merged. 2 changes still waiting over there.", name="note")
    render(tape, third, [{"i": 0, "type": "assistant"}])
    return tape.write(tmp_path)


def the_owners_own_read_refused(tmp_path: Path) -> Path:
    """D-4. Three of the owner's own aggregates refused because the turn had read too long."""
    tape = Tape()
    starved = turn(tape, "turn_yesterday", said="pull up yesterday's orders, please",
                   answer="Ten orders yesterday.", ui=["order_list"])
    for n in range(3):
        call = f"tc_agg_{n}"
        tape.add("tool_requested", session_id="s1", turn_id=starved, tool_call_id=call,
                 tool="commerce_aggregate", args={}, tier="read")
        tape.add("tool_finished", session_id="s1", turn_id=starved, tool_call_id=call,
                 tool="commerce_aggregate", outcome="refused", ok=False, ms=0.0,
                 error="REFUSED: this turn has been reading for too long; answer from what has been read.")
    tape.add("prediction", session_id="s1", branch_id="br_left", key="order:next", level="L2",
             confidence=0.8, observations=4, read=True, tier="warm", origin="cursor")
    tape.add("anticipation", session_id="s1", branch_id="br_left", event="started", state="WORKING",
             levels=2, in_flight=1, started=2, skipped=0, learned=True)
    render(tape, starved, [{"i": 0, "type": "order_list"}])
    return tape.write(tmp_path)


def the_assistant_disclaimed_its_own_screen(tmp_path: Path) -> Path:
    """D-6. The split question, and the applying question, both answered by disclaiming the
    interface."""
    tape = Tape()
    asked = turn(tape, "turn_split_q", said="What does the split button do?",
                 answer="I don't know what that button is — not something I control, so best to "
                        "check with whoever built the tablet screen.",
                 ui=["context_stack"])
    render(tape, asked, [{"i": 0, "type": "email_thread", "ref": THREAD}])
    tape.gap(20.0)
    second = turn(tape, "turn_applying_q", said="what does applying mean?",
                  answer="That's just the tablet's screen.", ui=["context_stack"])
    render(tape, second, [{"i": 0, "type": "email_thread", "ref": THREAD}])
    # The control: a question the manifest does NOT answer, declined honestly.
    tape.gap(20.0)
    third = turn(tape, "turn_shop_q", said="what is running out?",
                 answer="I've no tool for the supplier's stock.", ui=["context_stack"])
    render(tape, third, [{"i": 0, "type": "inventory"}])
    return tape.write(tmp_path)


def two_defects_narrated_and_discarded(tmp_path: Path) -> Path:
    """D-7. Both logging requests, as they were said, with the answers they got."""
    tape = Tape()
    first = turn(tape, "turn_log_split",
                 said="Okay, uh, please log that your split function is broken. It just so shows "
                      "two of the same thing, and the applying button is also broken",
                 answer="I've no tool for logging a product bug like that. You'd need to raise it "
                        "with whoever handles the tablet app directly.",
                 ui=["context_stack"])
    render(tape, first, [{"i": 0, "type": "email_thread", "ref": THREAD}])
    tape.gap(120.0)
    second = turn(tape, "turn_log_regressions",
                  said="Log--a lot of your functions are broken or halfway there, especially with "
                       "the back button, back to assistant button and the next button",
                  answer="I still have no tool that logs product feedback or bugs.",
                  ui=["context_stack"])
    render(tape, second, [{"i": 0, "type": "ranking"}])
    return tape.write(tmp_path)


def the_same_defects_recorded(tmp_path: Path) -> Path:
    """The other half of D-7: the same session with §16's event written. Nothing is ignored,
    and the report prints both of them verbatim."""
    tape = Tape()
    first = turn(tape, "turn_log_split", said="please log that your split function is broken",
                 answer="Logged against this test session, with the screen you were on.",
                 ui=["assistant"])
    tape.add("owner_feedback", session_id="s1", turn_id=first, branch_id="br_left", shape="log",
             text="please log that your split function is broken",
             screen=["email_thread"], entities=[{"kind": "email_thread", "ref": THREAD}],
             tab="", branch_status="ACTIVE",
             nearby=[{"at": T0, "kind": "command", "id": "navigation.home", "turn_id": first}])
    render(tape, first, [{"i": 0, "type": "assistant"}])
    tape.gap(120.0)
    second = turn(tape, "turn_log_regressions",
                  said="Log that the back button and the next button have regressed",
                  answer="Logged against this test session, with the screen you were on.",
                  ui=["assistant"])
    tape.add("owner_feedback", session_id="s1", turn_id=second, branch_id="br_left", shape="log",
             text="Log that the back button and the next button have regressed",
             screen=["ranking"], entities=[], branch_status="ACTIVE")
    render(tape, second, [{"i": 0, "type": "assistant"}])
    return tape.write(tmp_path)


def fingers_and_places_lost(tmp_path: Path) -> Path:
    """D-9 and D-12's neighbours: two fingers on one control, two controls in one place, the
    keyboard taken out of a field, and the scroll thrown back to the top by a redraw."""
    tape = Tape()
    only = turn(tape, "turn_precision", said="write to the supplier about the reprint",
                answer="The composer is open.", ui=["email_compose"])
    tape.add("tablet_hold", source="tablet", session_id="s1", turn_id=only, phase="multitouch",
             fingers=2, target="dock", t=int(tape.now * 1000))
    tape.add("tablet_collision", source="tablet", session_id="s1", turn_id=only, a="orb",
             b="dock", overlap=18, t=int(tape.now * 1000))
    tape.add("tablet_compose_field", source="tablet", session_id="s1", turn_id=only, name="to",
             chars=27, t=int(tape.now * 1000))
    render(tape, only, [{"i": 0, "type": "email_compose"}])
    tape.add("tablet_compose_field", source="tablet", session_id="s1", turn_id=only, name="to",
             chars=0, t=int(tape.now * 1000))
    tape.add("tablet_focus", source="tablet", session_id="s1", turn_id=only, state="lost",
             name="subject", cause="a background render", t=int(tape.now * 1000))
    # The scroll: deep, a redraw, and back at the top of the same document.
    tape.add("tablet_scroll", source="tablet", session_id="s1", turn_id=only, depth=874,
             height=1547, width=680, t=int(tape.now * 1000))
    render(tape, only, [{"i": 0, "type": "email_compose"}, {"i": 1, "type": "order", "ref": ORDER}])
    tape.add("tablet_scroll", source="tablet", session_id="s1", turn_id=only, depth=0,
             height=1547, width=680, t=int(tape.now * 1000))
    return tape.write(tmp_path)


# ------------------------------------------------------------------------------ the cases


def _classes(rec: Any) -> set[str]:
    return {c for t in rec.turns for c in t.classes}


def test_a_verified_send_left_the_button_applying_for_ever(tmp_path):
    """SEPTEMBER: the turn was successful — the send verified, and the report had no column
    for the screen. The tablet recorded the bug once per turn for six turns, in a field
    literally named `kept`, and nothing read it.
    NOW: ACTION_UI_STUCK, and the turn is a failure as the owner lived it."""
    rec, markdown = build_report(applying_stuck(tmp_path))
    send = rec.turn("turn_send")

    # The old reading, still true of the BACKEND, asserted so the pair is a test.
    assert visible.backend_outcome(send) == "VERIFIED"
    assert [p.status for p in send.proposals] == ["VERIFIED"]

    stuck = [t for t in rec.turns if "ACTION_UI_STUCK" in t.classes]
    assert len(stuck) >= 5, [t.turn_id for t in stuck]
    assert send.visible == "APPLYING_STUCK", send.visible
    assert send.experience == "FAILED"
    # The card itself, photographed: drawn in `committing` after the Mac had settled it.
    assert any("state 'committing'" in s for s in send.signals), send.signals
    # And the tablet's own count, once per turn for the six turns that followed.
    later = [t for t in rec.turns if t.turn_id.startswith("turn_after_")]
    assert len(later) == 6
    # The FIRST reconcile of a run is a correction, which is what reconcile is for. From the
    # second on, a settle that has to be made again is a settle that did not stick.
    flagged = [t for t in later if "ACTION_UI_STUCK" in t.classes]
    assert [t.turn_id for t in flagged] == [t.turn_id for t in later[1:]], [t.classes for t in later]
    assert all(any("keeping 2" in s for s in t.signals) for t in flagged)
    assert any("consecutive reconciles" in s for t in flagged for s in t.signals)

    # The line §17 asks for, in the report, exactly as the brief writes it.
    assert "gmail_send_reply:  backend = VERIFIED   visible = APPLYING_STUCK   experience = FAILED" in markdown
    assert "## 16. Two outcomes per turn" in markdown
    assert "As the owner lived it:" in markdown


def test_one_reconcile_that_settles_a_card_is_reconcile_working(tmp_path):
    """The control. A single correction is what reconcile is FOR, and a rule that called it a
    stuck surface would cry wolf on every session."""
    rec = reconstruct(read_events(one_correction(tmp_path)))
    assert "ACTION_UI_STUCK" not in _classes(rec)
    assert rec.turn("turn_third").experience == "SUCCESSFUL"


def test_the_split_showed_two_of_the_same_thing(tmp_path):
    """SEPTEMBER: the report's branch table said "focus changed with nothing redrawn" four
    times and the turns stayed successful.
    NOW: SPLIT_NO_REDRAW and SPLIT_DUPLICATE_SURFACE, and the control served on the other
    half is WRONG_BRANCH_SURFACE."""
    rec, markdown = build_report(a_split_that_showed_two_of_the_same(tmp_path))
    found = _classes(rec)
    assert "SPLIT_NO_REDRAW" in found
    assert "SPLIT_DUPLICATE_SURFACE" in found
    assert "WRONG_BRANCH_SURFACE" in found
    reading = rec.experience
    # Both halves, each focused and drawing nothing. Repeats of the same sentence on the same
    # turn are one finding — eleven ways of saying one defect buries the other ten.
    drew_nothing = reading.of("SPLIT_NO_REDRAW")
    assert {f.subject for f in drew_nothing} == {"br_left", "br_right"}, drew_nothing
    assert any("drew the same cards as the half before it" in f.signal
               for f in reading.of("SPLIT_DUPLICATE_SURFACE"))
    assert any("while br_right was the focused half" in f.signal
               for f in reading.of("WRONG_BRANCH_SURFACE"))
    assert "SPLIT_NO_REDRAW" in markdown and "SPLIT_DUPLICATE_SURFACE" in markdown
    # The visible column takes the WORST of what went wrong, not the first found.
    assert "visible = NOT_REDRAWN" in markdown
    assert visible.VISIBLE_WORD["SPLIT_DUPLICATE_SURFACE"] == "TWO_OF_THE_SAME"


def test_nothing_appeared_until_everything_was_ready_and_then_thrice(tmp_path):
    """SEPTEMBER: 7,975 ms to first cards was a row in the performance table and not a defect,
    and five identical order renders were "duplicate reads".
    NOW: PROGRESSIVE_RENDER_MISSING and DUPLICATE_RENDER."""
    rec = reconstruct(read_events(the_screen_redrawn_and_late(tmp_path)))
    late, again = rec.turn("turn_correlate"), rec.turn("turn_open")
    assert "PROGRESSIVE_RENDER_MISSING" in late.classes
    assert any("7,975 ms with nothing drawn before them" in s for s in late.signals), late.signals
    assert "PROGRESSIVE_RENDER_MISSING" not in again.classes, "680 ms is not a stall"
    assert "DUPLICATE_RENDER" in again.classes
    assert len(rec.experience.of("DUPLICATE_RENDER")) == 2, "the second and third of three"


def test_eight_homes_and_four_backs_were_not_a_hundred_per_cent_accepted(tmp_path):
    """SEPTEMBER: "12 Home, 6 Back, 100 % accepted" — a table of HTTP outcomes for a man who
    was lost.
    NOW: NAV_SEMANTIC_MISMATCH, counting the burst and naming the Home that replayed the
    record already in hand."""
    rec, markdown = build_report(eight_homes_and_four_backs(tmp_path))
    lost = rec.turn("turn_lost")

    # The old reading: every one of them was accepted, and that was the whole report.
    posted = [e for e in rec.controls if str(e.get("kind") or "") == "command"]
    assert posted and all(e.get("ok") is not False for e in posted), "100 % accepted, as it said"

    assert "NAV_SEMANTIC_MISMATCH" in lost.classes
    assert any("accepted in" in s and "accepted is not arrived" in s for s in lost.signals), lost.signals
    assert any("replayed the email_thread already in hand" in s for s in lost.signals), lost.signals
    assert lost.visible == "WENT_NOWHERE"
    assert "WENT_NOWHERE" in markdown


def test_a_control_with_nothing_behind_it_is_a_defect_of_the_screen(tmp_path):
    """SEPTEMBER: `open.area ok=False landing_unavailable` and `open.entity ok=False not_held`
    were two refusal codes in a table.
    NOW: FAKE_CONTROL — the control was on screen, under a thumb, with nothing behind it —
    and a Next accepted with nothing drawn is DEAD_CONTROL."""
    rec = reconstruct(read_events(controls_with_nothing_behind_them(tmp_path)))
    taps = rec.turn("turn_taps")
    assert "FAKE_CONTROL" in taps.classes
    assert "DEAD_CONTROL" in taps.classes
    reasons = " ".join(taps.signals)
    assert "landing_unavailable" in reasons and "not_held" in reasons
    assert "refund chip was tapped while it was disabled" in reasons
    assert "workflow.next was accepted and nothing was drawn" in reasons


def test_a_pending_undo_is_not_work_outstanding(tmp_path):
    """SEPTEMBER: "Merged. 2 changes still waiting over there." Nothing was waiting: the two
    were undo offers for changes that had already succeeded.
    NOW: STALE_PENDING_ACTION, which names them as undo offers."""
    rec = reconstruct(read_events(two_undos_counted_as_work(tmp_path)))
    found = rec.experience.of("STALE_PENDING_ACTION")
    assert len(found) >= 3, [f.signal for f in found]
    assert sum(1 for f in found if "an undo offer" in f.signal) == 2
    assert any("the tablet said changes were still waiting" in f.signal for f in found)
    assert all(p.status == "VERIFIED" for p in rec.proposals.values() if not p.undo_of), \
        "both real changes succeeded, which is what makes the warning wrong"


def test_the_owners_own_read_refused_by_work_nobody_asked_for(tmp_path):
    """SEPTEMBER: three `commerce_aggregate` refusals inside one turn, filed under
    TOOL_SELECTION_ERROR at severity 2.
    NOW: FOREGROUND_STARVED — anticipation, added to make the product feel faster, refused
    the thing the owner actually wanted."""
    rec, markdown = build_report(the_owners_own_read_refused(tmp_path))
    starved = rec.turn("turn_yesterday")
    assert "FOREGROUND_STARVED" in starved.classes
    assert any("commerce_aggregate × 3" in s for s in starved.signals), starved.signals
    assert starved.experience == "FAILED"
    # And the prediction and anticipation records are read rather than counted as unknown —
    # in September they were "event kinds this report does not read: prediction 9,
    # anticipation 5", which is the speculation that did the starving, unreported.
    assert not rec.unknown_kinds, dict(rec.unknown_kinds)
    kinds = {str(e.get("kind") or "") for e in rec.controls}
    assert {"prediction", "anticipation"} <= kinds, kinds
    assert "prediction(s) by level" in markdown
    assert "refused work instead" in markdown


def test_the_assistant_no_longer_disclaims_its_own_screen_without_being_noticed(tmp_path):
    """SEPTEMBER: "I don't know what that button is" was a successful turn — the model
    answered, nothing errored.
    NOW: SELF_UI_KNOWLEDGE_ERROR, because the manifest has the answer."""
    rec, markdown = build_report(the_assistant_disclaimed_its_own_screen(tmp_path))
    split, applying, shop = (rec.turn(t) for t in ("turn_split_q", "turn_applying_q", "turn_shop_q"))
    assert "SELF_UI_KNOWLEDGE_ERROR" in split.classes
    assert any("asked about Split and disclaimed it" in s for s in split.signals), split.signals
    assert any("navigation" not in s and "manifest has the answer" in s for s in split.signals)
    assert "SELF_UI_KNOWLEDGE_ERROR" in applying.classes
    assert "SELF_UI_KNOWLEDGE_ERROR" not in shop.classes, \
        "a question the manifest cannot answer, declined honestly, is not this"
    assert split.visible == "DISCLAIMED"
    assert "DISCLAIMED" in markdown


def test_two_defects_narrated_out_loud_and_discarded(tmp_path):
    """SEPTEMBER: both turns successful, and "Potential new actions: _none_".
    NOW: OWNER_FEEDBACK_IGNORED, and section 15 prints what he said even though nothing
    recorded it — read back from the transcript so the hour is not lost."""
    rec, markdown = build_report(two_defects_narrated_and_discarded(tmp_path))
    first, second = rec.turn("turn_log_split"), rec.turn("turn_log_regressions")
    assert "OWNER_FEEDBACK_IGNORED" in first.classes and "OWNER_FEEDBACK_IGNORED" in second.classes
    assert first.experience == "FAILED" and second.experience == "FAILED"
    assert [r["turn_id"] for r in rec.experience.ignored_feedback] == [first.turn_id, second.turn_id]

    assert "## 15. OWNER-REPORTED DEFECTS" in markdown
    assert "2 the owner reported and NOTHING recorded" in markdown
    assert "please log that your split function is broken" in markdown
    assert "back to assistant button and the next button" in markdown
    assert "I've no tool for logging a product bug like that" in markdown
    assert "2 defect(s) the owner reported out loud that nothing recorded" in markdown


def test_the_same_defects_recorded_are_printed_verbatim_and_not_flagged(tmp_path):
    """The other half: with §16's event on the timeline, nothing is ignored and the report
    prints both of them word for word, with the screen he was on."""
    rec, markdown = build_report(the_same_defects_recorded(tmp_path))
    assert "OWNER_FEEDBACK_IGNORED" not in _classes(rec)
    assert len(rec.experience.feedback) == 2 and rec.experience.ignored_feedback == []
    assert "## 15. OWNER-REPORTED DEFECTS" in markdown
    assert "2 recorded during the session" in markdown
    assert "please log that your split function is broken" in markdown
    assert "Log that the back button and the next button have regressed" in markdown
    assert "on screen: email_thread" in markdown
    assert "email_thread aa70d3f83dbef06e" in markdown, "the refs it was holding"
    assert "Nearby: command navigation.home" in markdown


def test_two_fingers_two_controls_and_a_place_lost(tmp_path):
    """The telemetry §17 asks the analyser to process and the old one ignored: the collisions,
    the keyboard, the fields and the scroll."""
    rec = reconstruct(read_events(fingers_and_places_lost(tmp_path)))
    only = rec.turn("turn_precision")
    assert "COLLISION" in only.classes
    assert "FOCUS_LOST" in only.classes
    signals = " ".join(only.signals)
    assert "2 fingers landed on the dock at once" in signals
    assert "orb and dock overlap by 18 px" in signals
    assert "the keyboard left subject" in signals
    assert "held 27 character(s) and then held none" in signals
    assert "returned to the top after" in signals and "no navigation between" in signals


def test_what_the_owner_reported_becomes_the_heaviest_candidate(tmp_path):
    """The report is read by `app/observability/proposals.py`, which turns each row into an
    improvement candidate. A defect the owner narrated himself is the most valuable evidence in
    a session, so it is first in that file — and in September it was not in it at all."""
    from app.observability.proposals import write_proposals

    text = write_proposals(two_defects_narrated_and_discarded(tmp_path), tmp_path / "reports").read_text(encoding="utf-8")
    assert "OWNER_REPORTED" in text
    assert "The owner reported this and NOTHING recorded it" in text
    assert "please log that your split function is broken" in text
    assert "ACTION_UI_STUCK" in write_proposals(
        applying_stuck(tmp_path / "stuck"), tmp_path / "reports2").read_text(encoding="utf-8")

    recorded = write_proposals(the_same_defects_recorded(tmp_path / "kept"),
                               tmp_path / "reports3").read_text(encoding="utf-8")
    assert "The owner reported this himself" in recorded
    assert "He should not have to say it twice" in recorded


# ----------------------------------------------------------------- every class has a fixture


def test_every_class_this_module_files_has_a_fixture_that_produces_it(tmp_path):
    """A classification nobody can reproduce is a classification nobody can trust. Between the
    fixtures in this file, every one of the fifteen appears at least once."""
    seen: set[str] = set()
    for name, build in (
        ("applying_stuck", applying_stuck),
        ("split", a_split_that_showed_two_of_the_same),
        ("late", the_screen_redrawn_and_late),
        ("navigation", eight_homes_and_four_backs),
        ("controls", controls_with_nothing_behind_them),
        ("undos", two_undos_counted_as_work),
        ("starved", the_owners_own_read_refused),
        ("disclaimed", the_assistant_disclaimed_its_own_screen),
        ("feedback", two_defects_narrated_and_discarded),
        ("fingers", fingers_and_places_lost),
    ):
        rec = reconstruct(read_events(build(tmp_path / name)))
        assert rec.experience.errors == [], (name, rec.experience.errors)
        seen |= {f.name for f in rec.experience.findings}
    missing = [name for name in visible.CLASSES if name not in seen]
    assert not missing, f"no fixture produces {missing}"


def test_the_tables_the_report_needs_are_complete():
    """Every class has a severity, a component and a task, or section 12 raises a KeyError on
    the session that first produces it — which is a report that cannot be written at all."""
    from app.observability.report import CLASSES, COMPONENT, SEVERITY

    for name in visible.CLASSES:
        assert name in CLASSES, name
        assert name in SEVERITY and name in COMPONENT and name in visible.TASKS, name
        assert name in visible.VISIBLE_WORD, name


def test_nothing_in_the_second_reading_can_execute_or_authorise_anything():
    """The audit is append-only and reads. This module imports no tool, no client and no part
    of the action engine, and nothing in it writes a file."""
    import ast
    import inspect

    tree = ast.parse(inspect.getsource(visible))
    modules = {(node.module or "") for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
    modules |= {a.name for node in ast.walk(tree) if isinstance(node, ast.Import) for a in node.names}
    for module in modules:
        assert not module.startswith(("app.actions", "app.tools", "app.clients", "app.providers",
                                      "app.routes")), module
    called = {node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", "")
              for node in ast.walk(tree) if isinstance(node, ast.Call)}
    for forbidden in ("propose", "commit", "arm", "execute", "write_text", "open", "emit"):
        assert forbidden not in called, forbidden


# ------------------------------------------------------------------ the acceptance test

REAL = Path("logs/test-sessions/ts-20260911-001845-phase-3c-live-tablet-tes.jsonl")
# What the brief requires the analyser to find in the real hour, at minimum.
REQUIRED = ("ACTION_UI_STUCK", "SPLIT_NO_REDRAW", "FOREGROUND_STARVED", "SELF_UI_KNOWLEDGE_ERROR",
            "OWNER_FEEDBACK_IGNORED", "DUPLICATE_RENDER", "NAV_SEMANTIC_MISMATCH")


@pytest.mark.skipif(not REAL.exists(), reason="the live session's timeline is gitignored; it is on the Mac that recorded it")
def test_the_real_session_is_read_as_it_was_lived():
    """The acceptance test for this whole workstream, run against the hour itself.

    Nothing is asserted here that would put a customer's name in this file: the assertions are
    class names, counts and turn ids. The report it produces is written beside the timeline, in
    `logs/`, which is gitignored.
    """
    rec, markdown = build_report(REAL)
    found = rec.experience.counts
    for name in REQUIRED:
        assert found.get(name), f"the real session must produce {name}"
    assert rec.experience.errors == []

    # Six consecutive reconciles reading count=2 kept=2, and the send that was already proved.
    stuck = rec.experience.of("ACTION_UI_STUCK")
    assert any("count=2 kept=2" in f.signal for f in stuck)
    assert sum(1 for t in rec.turns if "ACTION_UI_STUCK" in t.classes) >= 6

    # Eight Homes and four Backs in twenty-odd seconds, every one accepted.
    burst = [f for f in rec.experience.of("NAV_SEMANTIC_MISMATCH") if "accepted in" in f.signal]
    assert burst and "home" in burst[0].signal and "back" in burst[0].signal

    # The three refusals, and both logging requests.
    assert any("commerce_aggregate × 3" in f.signal for f in rec.experience.of("FOREGROUND_STARVED"))
    assert len(rec.experience.of("OWNER_FEEDBACK_IGNORED")) == 2
    assert len(rec.experience.ignored_feedback) == 2

    # And the verdict: the hour was not eleven successful of fourteen.
    lived = [t.experience for t in rec.turns]
    assert lived.count("SUCCESSFUL") <= 3, lived
    assert lived.count("FAILED") >= 8, lived
    assert "backend = VERIFIED   visible = APPLYING_STUCK   experience = FAILED" in markdown
