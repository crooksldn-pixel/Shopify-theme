"""crooks-watch, as §35 asks for it: one job going through the machine, in one line each.

    VOICE "reply to anna"
    READ Gmail thread 312ms
    STAGE gmail_send_reply RED
    ARM owner
    WRITE Gmail 452ms
    VERIFY Gmail ✓
    UI confirmation → VERIFIED 31ms

and, when the tablet and the Mac disagree about the same change — which is the defect the
live hour spent ten minutes on while the timeline recorded it once a turn —

    UI action prop_037e20c6ea04 stuck EXECUTING after server VERIFIED
    ERROR ACTION_UI_STUCK

The other half of the file is what makes it usable: it is not overwhelming by default, and
`-v` shows everything.
"""

from __future__ import annotations

import json
from typing import Any

from scripts import watch

T0 = 1_800_000_000.0


def _event(kind: str, **fields: Any) -> dict[str, Any]:
    event = {"kind": kind, "iso": "2026-09-11T00:21:51", "ts": T0, "turn_id": "turn_49d445f24ee2",
             "session_id": "s1"}
    event.update(fields)
    return event


def _send() -> list[dict[str, Any]]:
    """One job: heard, routed, read, staged, armed, written, proved, and confirmed on the
    glass. The live hour's third turn, event for event."""
    return [
        _event("stt", ok=True, engine="scribe", text="reply to anna and send it", audio_s=2.2),
        _event("lane", lane="NORMAL", family="order_email_reply", why="asks for a change"),
        _event("tool_finished", tool="gmail_read_thread", tool_call_id="tc_1", outcome="ok",
               ok=True, ms=312.0),
        _event("action_proposed", proposal_id="prop_037e20c6ea04", event="PROPOSED",
               operation="gmail_send_reply", risk="RED", interaction="hold_to_arm", status="PENDING"),
        _event("action_armed", proposal_id="prop_037e20c6ea04", event="ARMED",
               operation="gmail_send_reply", status="PENDING", caller_present=False),
        _event("action_executed", proposal_id="prop_037e20c6ea04", event="EXECUTED",
               operation="gmail_send_reply", status="EXECUTED", ms=452.0),
        _event("action_verified", proposal_id="prop_037e20c6ea04", event="VERIFIED",
               operation="gmail_send_reply", status="VERIFIED", code="verified", verified=True),
        _event("tablet_action_commit", source="tablet", proposal_id="prop_037e20c6ea04",
               status="verified", code="verified", outcome="answered", ms=31),
    ]


def _rendered(events: list[dict[str, Any]], *, verbose: bool = False) -> list[str]:
    out: list[str] = []
    state = watch.Watch(colour=False, verbose=verbose)
    for event in events:
        out.extend(state.lines(event))
    return out


# ------------------------------------------------------------------------ the job


def test_one_job_reads_as_one_job():
    """The seven lines §35 names, in order, with nothing between them."""
    lines = _rendered(_send())
    assert len(lines) == 8, lines
    assert 'VOICE  “reply to anna and send it”' in lines[0]
    assert "LANE   NORMAL order_email_reply" in lines[1]
    assert "READ   Gmail thread 312ms" in lines[2]
    assert "gmail_read_thread ok" in lines[2], "the tool and its outcome, for the engineer"
    assert "STAGE  gmail_send_reply RED" in lines[3]
    # Always the owner: nothing else can arm a change, whatever the ledger recorded about
    # which identity made the request.
    assert "ARM    owner" in lines[4]
    assert "WRITE  Gmail 452ms" in lines[5]
    assert "VERIFY Gmail ✓" in lines[6]
    assert "UI     confirmation → VERIFIED 31ms" in lines[7]


def test_the_two_halves_caught_disagreeing():
    """D-1, live. The server settles the send; the tablet goes on holding it. Neither event
    says so on its own, which is why nothing noticed for ten minutes."""
    events = _send() + [
        _event("tablet_reconcile", source="tablet", turn_id="turn_b9c757f271ff", reason="turn",
               count=2, kept=2, cancelled=0),
    ]
    lines = _rendered(events)
    assert "UI     action prop_037e20c6ea04 stuck EXECUTING after server VERIFIED" in lines[-2]
    assert "ERROR  ACTION_UI_STUCK" in lines[-1]
    assert "kept 2" in lines[-1]


def test_a_card_still_saying_applying_is_the_same_report():
    """The other evidence for the same fault: the surface itself, drawn in `committing` for a
    change the server has finished."""
    events = _send() + [
        _event("tablet_render", source="tablet", cards=[
            {"i": 0, "type": "confirmation", "proposal_id": "prop_037e20c6ea04",
             "surface": {"kind": "hold_to_arm", "state": "committing"}},
        ]),
    ]
    lines = _rendered(events)
    assert "stuck EXECUTING after server VERIFIED" in lines[-2]
    assert "ERROR  ACTION_UI_STUCK" in lines[-1]
    assert "committing" in lines[-1]


def test_it_says_it_once_and_not_once_per_reconcile():
    """The live hour would have printed this six times. It is one fault about one card."""
    events = _send() + [
        _event("tablet_reconcile", source="tablet", reason="turn", count=2, kept=2) for _ in range(6)
    ]
    lines = _rendered(events)
    assert sum(1 for x in lines if "ACTION_UI_STUCK" in x) == 1, lines


def test_a_change_being_staged_is_one_line_and_not_two():
    """The tool finishing with `staged` and the proposal being written are the same event
    twice. The proposal's line says which change and how heavy it is, so it is the one kept."""
    events = [
        _event("tool_finished", tool="gmail_send_reply", outcome="staged", ok=True, ms=452.0,
               proposal_id="prop_037e20c6ea04"),
        _event("action_proposed", proposal_id="prop_037e20c6ea04", operation="gmail_send_reply",
               risk="RED", status="PENDING"),
    ]
    quiet = _rendered(events)
    assert quiet == [x for x in quiet if "STAGE  gmail_send_reply RED" in x], quiet
    assert len(_rendered(events, verbose=True)) == 2


def test_a_reconcile_that_settles_nothing_says_nothing():
    """Reconcile doing its job is not news, and neither is one that keeps a card the server
    has not finished with."""
    quiet = _rendered([
        _event("action_proposed", proposal_id="prop_x", operation="gmail_send_reply", risk="RED",
               status="PENDING"),
        _event("tablet_reconcile", source="tablet", reason="turn", count=1, kept=0),
        _event("tablet_reconcile", source="tablet", reason="turn", count=1, kept=1),
    ])
    assert not [x for x in quiet if "ACTION_UI_STUCK" in x], quiet


# ------------------------------------------------------------------ navigation


def test_back_and_home_have_lines_of_their_own():
    """D-10 in the terminal: Home that replays what was already in hand, and a burst of them
    that is somebody hunting rather than moving."""
    events = [
        _event("command", ts=T0, command="navigation.home", ok=True, ms=0.2,
               entity="email_thread", replayed=True, branch_id="br_left"),
        _event("command", ts=T0 + 2, command="navigation.back", ok=True, ms=0.1, branch_id="br_left"),
        _event("command", ts=T0 + 4, command="navigation.home", ok=True, ms=0.1,
               entity="email_thread", replayed=True, branch_id="br_left"),
        _event("command", ts=T0 + 6, command="navigation.home", ok=True, ms=0.1,
               entity="email_thread", replayed=True, branch_id="br_left"),
    ]
    lines = _rendered(events)
    assert "NAV    Home → email_thread" in lines[0]
    assert "replayed what was already in hand" in lines[0]
    assert "NAV    Back" in lines[1]
    burst = [x for x in lines if "WARN" in x]
    assert burst and "3 × Home" in burst[0] and "1 × Back" in burst[0]
    assert "every one accepted" in burst[0]


def test_a_control_the_mac_refused_is_a_line_by_itself():
    lines = _rendered([_event("command", command="open.entity", ok=False, code="not_held", ms=1.0)])
    assert lines == [x for x in lines if "DEAD   open.entity refused not_held" in x]


def test_feedback_the_owner_gives_is_printed_as_it_is_logged():
    lines = _rendered([_event("owner_feedback", shape="log", branch_id="br_left",
                              text="log that the split function is broken")])
    assert "NOTE   logged “log that the split function is broken”" in lines[0]


# -------------------------------------------------------------- not overwhelming


def test_by_default_the_noise_is_not_printed_and_verbose_prints_it():
    noise = [
        _event("turn_started", input="audio", turns_before=0),
        _event("read_plan", groups=[["a"], ["b"]], critical_path_ms=120.0, saved_ms=40.0),
        _event("model", ms=2900.0, steps=[1, 2], tool_calls=[1]),
        _event("tablet_scroll", source="tablet", depth=874, height=1547),
        _event("tablet_render", source="tablet", cards=[{"i": 0, "type": "order"}]),
        _event("branch_focused", branch_id="br_right"),
        _event("turn_performance", lane="FAST", model_calls=0),
        _event("prediction", branch_id="br_left", level="L2", confidence=0.8),
    ]
    assert _rendered(noise) == [], "a live watch must be readable while it is being watched"
    loud = _rendered(noise, verbose=True)
    assert len(loud) >= 7, loud
    assert any("heard (audio)" in x for x in loud)
    assert any("claude 2.9s" in x for x in loud)
    assert any("drew 1 card(s)" in x for x in loud)
    assert any("focused br_right" in x for x in loud)
    assert any("prediction" in x for x in loud)


def test_the_important_lines_are_printed_whether_or_not_verbose_is_on():
    quiet = _rendered(_send())
    loud = _rendered(_send(), verbose=True)
    for x in quiet:
        assert x in loud, x


def test_an_event_kind_it_has_no_line_for_says_nothing():
    assert watch.line(_event("something_new"), colour=False) is None
    assert watch.line(_event("something_new"), colour=False, verbose=True) is None


def test_a_field_it_was_never_told_about_is_not_printed():
    """The allow-list, still. A field added to the timeline tomorrow cannot start appearing in
    somebody's terminal."""
    rendered = watch.line(_event("tool_finished", tool="shopify_order_address", outcome="ok",
                                 ms=120.0, street="12 Elm Road", authorization="Bearer abc"),
                          colour=False)
    assert "shopify_order_address ok" in rendered
    assert "Elm" not in rendered and "Bearer" not in rendered


def test_the_follow_loop_uses_one_watch_so_state_survives_the_file(tmp_path, capsys):
    """The disagreement is only visible across events, so the loop cannot build a new watch
    per line."""
    path = tmp_path / "ts-x.jsonl"
    events = [_event("session_started")] + _send() + [
        _event("tablet_reconcile", source="tablet", reason="turn", count=2, kept=2),
        _event("session_stopped"),
    ]
    path.write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")
    assert watch.follow(path, once=False, colour=False) == 0
    out = capsys.readouterr().out
    assert "session started" in out and "session stopped" in out
    assert "ERROR  ACTION_UI_STUCK" in out
    assert "VERIFY Gmail ✓" in out


def test_the_burst_threshold_is_the_analysers_own():
    """The terminal and the report must agree about what a burst of navigation is."""
    from app.observability import visible

    assert watch.NAV_BURST == visible.NAV_BURST
    assert watch.NAV_WINDOW_S == visible.NAV_WINDOW_S
