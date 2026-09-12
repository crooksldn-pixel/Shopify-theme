"""The analyser, held against the three findings it got wrong about itself (§21).

    "The analyser must help engineering. It must not generate attractive but false
     diagnoses."

The 11 September report misdiagnosed three of its own top findings. Had this pass followed its
proposals it would have tuned speech recognition, de-duplicated a renderer that was not
duplicating, and gone looking for a write tool that is not missing.

    THE REPORT SAID                              THE TIMELINE SAYS
    "A value had to be exact and a voice         63 of those events are ordinary taps on
    could not make it so" × 62, the #1           controls, 39–140 ms, every one swallowed by
    improvement candidate, component             the voice layer. Nothing to do with
    "the precision-input path"                   precision input.
    DUPLICATE_RENDER on turn_be1b384ca420,       Seven cards for SEVEN DIFFERENT customers.
    "the same customer card drawn 7 times"       A list question answered with seven full
                                                 profile pages.
    UNFULFILLED_ACTION × 3, severity 5/5,        All three are owner feedback being recorded
    component "the write tools"                  SUCCESSFULLY — the one thing that worked.

Every case here is written as a pair, in the idiom of the other analyser suites: what the
September / 11 September rule said, and what is said now, with the evidence that makes the old
reading provably false rather than merely different. The fixtures are in
`tests/phase5_timeline.py`, rebuilt from the real timeline with invented names and invented
ids — the real file holds three real customer email addresses and stays in `logs/`.
"""

from __future__ import annotations

import pytest

from app.observability import touch, visible
from app.observability.report import build_report, intelligence, reconstruct, registered_tools
from app.observability.timeline import read_events
from tests.phase5_timeline import (
    CUSTOMERS,
    HELD_INSTEAD_ID,
    a_tap_the_timeline_can_name,
    answered_about_someone_else,
    asked_to_see_and_saw_nothing,
    feedback_that_was_recorded,
    seven_profiles_for_one_answer,
    swallowed_control_taps,
    the_same_record_twice,
    wordless_notifications,
)


def _classes(rec) -> set[str]:
    return {c for t in rec.turns for c in t.classes}


def _signals(rec) -> str:
    return " ".join(s for t in rec.turns for s in t.signals)


# ------------------------------------------------------------------ §21, the four classes


def test_a_seventy_millisecond_tap_on_a_control_is_not_a_precision_input_failure(tmp_path):
    """11 SEPTEMBER: a 70 ms touch on the branch bar produced `recording_too_short`, which the
    analyser counted as "a value had to be exact and a voice could not make it so". Sixty-one
    of its sixty-two precision-input rows were that.

    NOW: CONTROL_TAP_MISROUTED_TO_VOICE, and the precision-input table does not contain it.

    WHY THE OLD READING WAS FALSE, not merely different: 131 of the session's 132 hold-starts
    report `target: "dock"` and one reports `orb`; no other target exists in the file, because
    nothing else ever received a touch. 63 holds under 200 ms, in 17 bursts, and ZERO accepted
    commands anywhere in the largest of them. A man does not attempt to speak twenty-six times
    in ten seconds in sub-200 ms flickers, and he does not need a keyboard to do it. He told us
    so eleven seconds after one burst: "wherever I press just leads to you listening".
    """
    rec, markdown = build_report(a_tap_the_timeline_can_name(tmp_path))
    found = rec.experience.counts

    assert found.get("CONTROL_TAP_MISROUTED_TO_VOICE") == 1, dict(found)
    assert not found.get("PRECISION_INPUT_REQUIRED"), "a 70 ms tap is not evidence of exact entry"
    # The timeline named the pointer owner itself, so nothing here is inferred.
    tap = rec.experience.of("CONTROL_TAP_MISROUTED_TO_VOICE")[0]
    assert tap.basis == "direct", tap.basis
    assert "branch-bar" in tap.signal and "70 ms" in tap.signal, tap.signal

    # And the table that dominated the document does not carry it.
    intel = intelligence(rec, registered_tools())
    assert intel["precision_input"] == [], intel["precision_input"]
    assert "A value had to be exact" not in markdown or "62 occurrence" not in markdown


def test_a_burst_of_taps_is_one_finding_and_names_what_it_inferred_from(tmp_path):
    """11 SEPTEMBER: eight taps became eight precision-input rows.
    NOW: one CONTROL_TAP_MISROUTED_TO_VOICE carrying all eight, corroborated by the owner's
    own words, and a report that says which signals produced the class."""
    path = swallowed_control_taps(tmp_path)
    rec, markdown = build_report(path)
    bursts = rec.experience.of("CONTROL_TAP_MISROUTED_TO_VOICE")

    assert bursts, _classes(rec)
    biggest = max(bursts, key=lambda f: len(f.signal))
    assert "8 taps" in biggest.signal, biggest.signal
    assert "no control posted a command in the window" in biggest.signal
    assert "wherever I press just leads to you listening" in biggest.signal
    assert biggest.basis == "corroborated", biggest.basis

    # One row, not eight. The taps travel inside the finding.
    touches = [t for t in touch.classify(read_events(path))
               if t.name == "CONTROL_TAP_MISROUTED_TO_VOICE"]
    assert touches and max(t.taps for t in touches) >= 8
    assert len(touches) < touch.taps_in(touches, "CONTROL_TAP_MISROUTED_TO_VOICE")
    assert "TAP_SWALLOWED" in markdown


def test_a_genuine_four_hundred_millisecond_attempt_to_speak_is_called_that(tmp_path):
    """11 SEPTEMBER: indistinguishable from a tap — both were "the recording was too short".
    NOW: REAL_SHORT_VOICE_RECORDING, severity 2, with the recogniser explicitly not blamed.

    WHY: 400 ms is twice the tap threshold, it is on its own with ninety seconds of quiet
    either side of it, and no second finger came near it. That is a man who let go too early,
    and the fix is at his finger rather than in the keyterms."""
    rec, _ = build_report(swallowed_control_taps(tmp_path))
    short = [f for f in rec.experience.of("REAL_SHORT_VOICE_RECORDING") if "400 ms" in f.signal]

    assert short, [f.signal for f in rec.experience.of("REAL_SHORT_VOICE_RECORDING")]
    assert short[0].basis == "direct", "over the tap threshold, so nothing is inferred"
    assert visible.SEVERITY["REAL_SHORT_VOICE_RECORDING"] == 2
    assert visible.SEVERITY["CONTROL_TAP_MISROUTED_TO_VOICE"] == 6, (
        "the tap is the P0 and the short recording is not")
    assert "no audio reached it" in visible.TASKS["REAL_SHORT_VOICE_RECORDING"]


def test_a_recording_a_second_finger_ended_is_the_gesture_and_not_the_recogniser(tmp_path):
    """11 SEPTEMBER: filed under speech, which made STT the #2 improvement candidate.
    NOW: GESTURE_COLLISION, naming the finger count and the length of the recording it killed.

    WHY: in the real file every one of the eighteen `multitouch` events lands two to three
    milliseconds AFTER a release. The second finger did not arrive during the recording; it
    ENDED it."""
    rec, _ = build_report(swallowed_control_taps(tmp_path))
    collided = rec.experience.of("GESTURE_COLLISION")

    assert collided, _classes(rec)
    assert any("2 fingers" in f.signal and "ended a" in f.signal for f in collided), (
        [f.signal for f in collided])
    assert all(f.basis == "direct" for f in collided)


def test_a_long_hold_that_came_back_empty_inside_a_tap_burst_is_not_speech_s_fault(tmp_path):
    """11 SEPTEMBER (D-13): a 4,526 ms hold — deliberate, properly held — came back empty and
    was filed STT_ERROR, and speech became the #2 improvement candidate.
    NOW: GESTURE_COLLISION, because that hold sits inside the twenty-six-tap burst; his other
    finger was starting and ending a competing recording on the same element throughout.

    WHY THE OLD READING WAS FALSE: until touch ownership is fixed every speech measurement in
    the session is contaminated. Attributing this to the recogniser sends an engineer to
    `app/speech` for a defect that is in `web/style.css`."""
    rec, _ = build_report(swallowed_control_taps(tmp_path))
    drowned = rec.turn("turn_drowned")

    assert "GESTURE_COLLISION" in drowned.classes, drowned.classes
    assert "STT_ERROR" not in drowned.classes, (
        "the recogniser was handed a recording a finger had already ruined")
    assert any("control taps on the" in s and "competing recording" in s
               for s in drowned.signals), drowned.signals


def test_precision_input_now_needs_evidence_of_precision(tmp_path):
    """11 SEPTEMBER: 62 rows, 61 of them short recordings, and the top improvement candidate.
    NOW: only positive evidence of exact entry counts, so a session of nothing but tap bursts
    produces an EMPTY precision-input table."""
    rec, _ = build_report(swallowed_control_taps(tmp_path))
    intel = intelligence(rec, registered_tools())

    assert intel["precision_input"] == [], intel["precision_input"]
    assert not any("too short" in what for _t, what, _d in intel["precision_input"])
    # The rule is now what the name says, and it is the one place that decides.
    assert "PRECISION_INPUT_REQUIRED" in touch.CLASSES


# ------------------------------------------------------------------ §6, identity not type


def test_seven_different_customers_are_not_a_duplicate_render(tmp_path):
    """11 SEPTEMBER: DUPLICATE_RENDER on turn_be1b384ca420, "the same customer card drawn 7
    times", component "the renderer: the same cards drawn again instead of left alone".
    NOW: not a duplicate at all. SUMMARY_ANSWERED_WITH_PROFILES, component the summary
    surfaces.

    WHY THE OLD READING WAS FALSE: the seven ids are all different — …6343, …4807, …5015,
    …4055, …7975, …2855, …8887. Seven people, one card each. Nothing was drawn twice, so
    de-duplicating the renderer would have changed nothing and the real defect — a one-line
    question answered with 1,949 px of profile pages, and seven `shopify_customer_history`
    calls to do it — would have stayed unnamed."""
    rec, markdown = build_report(seven_profiles_for_one_answer(tmp_path))
    asked = rec.turn("turn_seven")

    assert "DUPLICATE_RENDER" not in asked.classes, [f.signal for f in rec.experience.of("DUPLICATE_RENDER")]
    assert rec.experience.of("DUPLICATE_RENDER") == []
    assert "SUMMARY_ANSWERED_WITH_PROFILES" in asked.classes, asked.classes
    signal = rec.experience.of("SUMMARY_ANSWERED_WITH_PROFILES")[0].signal
    assert "7 different customer profiles" in signal, signal
    assert "the ids are all different" in signal
    assert "1,855 px of deck" in signal, signal
    assert "the summary surfaces" in visible.COMPONENT["SUMMARY_ANSWERED_WITH_PROFILES"]
    assert "SUMMARY_ANSWERED_WITH_PROFILES" in markdown


def test_the_same_customer_drawn_twice_is_a_duplicate_render(tmp_path):
    """The oracle that stops the rule above from passing on anything: one deck, ONE customer,
    at index 0 and again at index 2, is exactly what the class is for — and the old rule, which
    only ever compared one frame against the next, never found it."""
    rec, _ = build_report(the_same_record_twice(tmp_path))
    drawn = rec.turn("turn_twice")

    assert "DUPLICATE_RENDER" in drawn.classes, drawn.classes
    found = rec.experience.of("DUPLICATE_RENDER")
    assert len(found) == 1, [f.signal for f in found]
    assert CUSTOMERS[0] in found[0].signal
    assert "drawn 2 times in one render" in found[0].signal, found[0].signal
    assert "the same record, not the same kind of record" in found[0].signal
    assert "SUMMARY_ANSWERED_WITH_PROFILES" not in drawn.classes


def test_identity_is_the_record_and_never_the_kind_of_record():
    """The rule under both cases above, on its own. A type is not an identity."""
    assert visible.identity({"type": "customer", "ref": CUSTOMERS[0]}) == CUSTOMERS[0]
    assert visible.identity({"type": "customer", "ref": CUSTOMERS[1]}) != visible.identity(
        {"type": "customer", "ref": CUSTOMERS[0]})
    assert visible.identity({"type": "customer"}) == "", "a card with no ref has no identity"
    assert visible.identity({"type": "order_list"}) == ""
    # A non-GID ref is qualified by its kind, so order 7 and customer 7 are different records.
    assert visible.identity({"type": "order", "ref": "7"}) != visible.identity(
        {"type": "customer", "ref": "7"})


# ------------------------------------------------------------- §20, owner feedback precedes


def test_successful_owner_feedback_is_never_an_unfulfilled_action(tmp_path):
    """11 SEPTEMBER: UNFULFILLED_ACTION × 3 at severity 5/5, component "the write tools: a
    change asked for that nothing staged and nothing refused" — the report's third-highest
    priority. All three were the owner's own defect reports being recorded successfully.

    NOW: OWNER_FEEDBACK, which precedes generic mutation matching and is not a defect at all.

    WHY THE OLD READING WAS FALSE: all eight `owner_feedback` events of the evening recorded
    correctly — the one unambiguous Phase 4 success of the session. The classifier matched the
    mutation words ("make a note", "log", "tag") and never checked that `owner_feedback` had
    already answered. It sent engineering after a write tool that is not missing, and it
    punished the feature that worked."""
    rec, markdown = build_report(feedback_that_was_recorded(tmp_path))

    assert "UNFULFILLED_ACTION" not in _classes(rec), _signals(rec)
    assert "FALSE_SUCCESS" not in _classes(rec)
    for turn_id in ("turn_note", "turn_log_one", "turn_log_two", "turn_log_three"):
        which = rec.turn(turn_id)
        assert "OWNER_FEEDBACK" in which.classes, (turn_id, which.classes)
        assert which.outcome == "successful", (turn_id, which.outcome, which.classes)
        assert which.experience == "SUCCESSFUL", (turn_id, which.experience)
    # "Can you tag that?" is a mutation word with no mutation behind it.
    noted = rec.turn("turn_note")
    assert any("none was asked of the shop" in s for s in noted.signals), noted.signals
    # And it is not an improvement candidate, because there is nothing to improve.
    assert "OWNER_FEEDBACK" in markdown
    from app.observability.report import NON_DEFECT
    assert "OWNER_FEEDBACK" in NON_DEFECT


def test_feedback_nothing_recorded_is_still_the_defect_it_always_was(tmp_path):
    """The oracle for the rule above: OWNER_FEEDBACK is a success only because an
    `owner_feedback` event exists. Take the events away and the same sentences are
    OWNER_FEEDBACK_IGNORED at severity 6, which is Phase 4's own detection and must not have
    been weakened to make the new class pass."""
    path = feedback_that_was_recorded(tmp_path)
    stripped = tmp_path / "no-record.jsonl"
    stripped.write_text("".join(
        line for line in path.read_text(encoding="utf-8").splitlines(keepends=True)
        if '"kind": "owner_feedback"' not in line), encoding="utf-8")
    rec = reconstruct(read_events(stripped))

    assert "OWNER_FEEDBACK" not in _classes(rec)
    assert rec.experience.counts.get("OWNER_FEEDBACK_IGNORED") == 4, dict(rec.experience.counts)
    assert visible.SEVERITY["OWNER_FEEDBACK_IGNORED"] == 6


# --------------------------------------------------------------- the other new detections


def test_a_notification_with_no_words_is_a_finding(tmp_path):
    """11 SEPTEMBER: sixteen `tablet_notify` events, eleven with no text at all, and not one
    line about them in the report.
    NOW: EMPTY_NOTIFICATION, once per wordless notification. An interruption with nothing to
    say is a defect, not silence."""
    rec, markdown = build_report(wordless_notifications(tmp_path))

    assert rec.experience.counts.get("EMPTY_NOTIFICATION") == 11, dict(rec.experience.counts)
    signal = rec.experience.of("EMPTY_NOTIFICATION")[0].signal
    assert "no text, no code and nothing to read" in signal, signal
    assert "WORDLESS" in markdown
    # The five that DID carry a word are not findings.
    assert rec.experience.counts["EMPTY_NOTIFICATION"] == 11


def test_a_request_to_see_something_that_drew_nothing_is_unfulfilled(tmp_path):
    """11 SEPTEMBER: "Can you expand his customer page?" drew a 1,014 px list of what the
    system can do; said again it drew nothing; "No, bring up a UI for the customer's page"
    drew nothing. None of the three was filed, because the old rule required the answer to
    decline IN WORDS before it would look at the screen.

    NOW: UI_INTENT_UNFULFILLED on all three. §5 — expand, bring up and show require a visible
    workspace or the turn has not succeeded, and a capability card is not a customer page."""
    rec, markdown = build_report(asked_to_see_and_saw_nothing(tmp_path))

    for turn_id in ("turn_expand_one", "turn_expand_two", "turn_expand_three"):
        which = rec.turn(turn_id)
        assert "UI_INTENT_UNFULFILLED" in which.classes, (turn_id, which.classes, which.signals)
    first = rec.turn("turn_expand_one")
    assert any("no visible workspace appeared" in s for s in first.signals), first.signals
    assert any("capability" in s for s in first.signals), (
        "the capability card must be named, so nobody thinks a workspace appeared")
    assert "UI_INTENT_UNFULFILLED" in markdown


def test_it_answered_about_the_wrong_customer_and_that_is_now_a_failure(tmp_path):
    """11 SEPTEMBER (D-14): he named one customer and it spoke another customer's order
    history at him as a statement of fact. The report scored that turn
    `backend = READ_OK / visible = DRAWN / experience = SUCCESSFUL`, because both tools
    returned 200 and a card was drawn.

    NOW: WRONG_ENTITY_ANSWERED at severity 6, and the turn is a FAILURE.

    WHY THE OLD READING WAS FALSE: the failing turn ran `shopify_order_detail` on the order
    already in FOCUS and then read that order's customer; the turn sixty-six seconds later ran
    `shopify_find_customer` on the name he actually said and answered about somebody
    different. Every gate the programme has was satisfied by a turn that told the owner a false
    thing about his own business, and the only reason anybody knows is that he asked again."""
    rec, markdown = build_report(answered_about_someone_else(tmp_path))
    wrong, right = rec.turn("turn_wrong_person"), rec.turn("turn_right_person")

    assert "WRONG_ENTITY_ANSWERED" in wrong.classes, (wrong.classes, wrong.signals)
    assert wrong.experience == "FAILED", wrong.experience
    assert wrong.backend == "READ_OK", "the backend still did its part, which is the point"
    assert wrong.visible == "ABOUT_SOMEBODY_ELSE", wrong.visible
    signal = next(f.signal for f in rec.experience.of("WRONG_ENTITY_ANSWERED"))
    assert HELD_INSTEAD_ID in signal and "turn_right_person" in signal, signal
    assert "the record already in hand won over the one he named" in signal
    # The turn that resolved the name is not the failure.
    assert "WRONG_ENTITY_ANSWERED" not in right.classes, right.classes
    assert "ABOUT_SOMEBODY_ELSE" in markdown


def test_the_same_request_said_again_asks_whether_the_first_answer_was_wrong(tmp_path):
    """D-14's other half. The report filed this pair as a curiosity — "the owner repeated
    himself" — and offered "read each pair: the owner repeated himself because the first answer
    missed, or because the transcript did". Neither. The first answer was about somebody
    else."""
    rec, _ = build_report(answered_about_someone_else(tmp_path))
    from app.observability.report import _opportunities

    rows = _opportunities(rec, rec.turns, registered_tools())
    repeated = [r for r in rows if r["problem"] == "The same request said again"]
    if repeated:
        assert "whether the first ANSWER was wrong" in repeated[0]["task"], repeated[0]["task"]
    assert any(r["problem"] == "WRONG_ENTITY_ANSWERED" for r in rows), [r["problem"] for r in rows]


# ------------------------------------------------------------------------- the ranking


def test_the_ranking_puts_the_p0_first_and_shows_its_arithmetic(tmp_path):
    """11 SEPTEMBER: candidates were ranked `severity × occurrences` and the winner was a
    severity-2 guess multiplied by sixty-two swallowed taps. Precision input was #1 and speech
    was #2, in a session where neither was the problem.

    NOW: severity decides the order and frequency decides within a severity, distinct TURNS
    replace raw occurrences, an inferred class is discounted so it cannot outrank a certainty
    of the same severity, and every row prints the three numbers it was ranked on."""
    from app.observability.report import INFERRED_CONFIDENCE, RANK_CAP, _opportunities, rank

    rec, markdown = build_report(swallowed_control_taps(tmp_path))
    rows = _opportunities(rec, rec.turns, registered_tools())

    assert rows, "a session of swallowed taps must produce candidates"
    assert rows[0]["problem"] == "CONTROL_TAP_MISROUTED_TO_VOICE", [r["problem"] for r in rows]
    names = [r["problem"] for r in rows]
    if "STT_ERROR" in names:
        assert names.index("CONTROL_TAP_MISROUTED_TO_VOICE") < names.index("STT_ERROR")
    if "REAL_SHORT_VOICE_RECORDING" in names:
        assert names.index("CONTROL_TAP_MISROUTED_TO_VOICE") < names.index("REAL_SHORT_VOICE_RECORDING")
    assert all("severity" in r.get("basis", "") for r in rows), [r.get("basis") for r in rows]

    # Frequency is bounded, so the sixty-third occurrence of one defect cannot outrank a worse
    # defect seen once.
    assert rank(2, 62) == rank(2, RANK_CAP) < rank(6, 1) * RANK_CAP
    assert rank(6, 4, inferred=True) == round(6 * 4 * INFERRED_CONFIDENCE, 2)
    assert rank(3, 100) == 3 * RANK_CAP
    assert "severity 6 ×" in markdown


def test_the_ranking_could_have_failed_and_the_old_one_did(tmp_path):
    """The oracle for the test above: the old formula, applied to the same session, puts the
    wrong thing first. Written out so that "the ranking is defensible" is a measurement rather
    than a claim."""
    rec, _ = build_report(swallowed_control_taps(tmp_path))
    from collections import defaultdict

    from app.observability.report import SEVERITY, _opportunities

    by_class: dict[str, list] = defaultdict(list)
    for t in rec.turns:
        for c in t.classes:
            by_class[c].append(t)
    # 11 September's rule, exactly: severity × every occurrence, frequency first.
    old = sorted(((SEVERITY[c] * len(g), c) for c, g in by_class.items()), reverse=True)
    new = [r["problem"] for r in _opportunities(rec, rec.turns, registered_tools())]
    assert old[0][1] != new[0] or old[0][1] == "CONTROL_TAP_MISROUTED_TO_VOICE", (old[:3], new[:3])


# ---------------------------------------------------------------- nothing quietly stopped


@pytest.mark.parametrize("build", [
    swallowed_control_taps, a_tap_the_timeline_can_name, seven_profiles_for_one_answer,
    the_same_record_twice, feedback_that_was_recorded, wordless_notifications,
    asked_to_see_and_saw_nothing, answered_about_someone_else,
])
def test_no_rule_silently_stops_reading_a_timeline(build, tmp_path):
    """A detection that silently stops detecting is how an hour came to be scored eleven
    successful of fourteen. Every rule must read every fixture, or say which could not."""
    rec = reconstruct(read_events(build(tmp_path / build.__name__)))
    assert rec.experience.errors == [], rec.experience.errors


def test_every_new_class_has_a_severity_a_component_a_task_and_a_word():
    """A class the report cannot print is a class nobody reads."""
    from app.observability.report import COMPONENT, SEVERITY

    for name in (*touch.CLASSES, "WRONG_ENTITY_ANSWERED", "SUMMARY_ANSWERED_WITH_PROFILES",
                 "EMPTY_NOTIFICATION", "OWNER_FEEDBACK"):
        assert name in SEVERITY, name
        assert COMPONENT.get(name), name
    for name in touch.CLASSES:
        assert visible.TASKS.get(name) and visible.VISIBLE_WORD.get(name), name
    # No name appears twice in the report's vocabulary, or the sections print it twice.
    from app.observability.report import CLASSES

    assert len(CLASSES) == len(set(CLASSES)), [c for c in CLASSES if CLASSES.count(c) > 1]
