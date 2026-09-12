"""The 11 September evening, rebuilt as a fixture (§37).

Every shape in here is taken from `ts-20260911-201129-phase-4-live-tablet-test.jsonl` — the
same event kinds, the same fields, the same millisecond gaps, the same burst structure — with
**no real data of any kind**. The names are invented, the customer ids are invented, the order
numbers are invented. The real file stays in `logs/test-sessions/`, which is gitignored,
because it holds three real customer email addresses (D-15) and a name on every turn.

What each builder reproduces, and the measurement it is built from:

    swallowed_control_taps     8 taps at 68, 46, 83, 68, 71, 94, 81, 67 ms and then, eleven
                               seconds later, the owner saying he cannot press anything.
                               Plus one 400 ms hold that is a real short recording, one
                               recording a second finger ended, and one 4,526 ms hold that
                               came back empty inside the burst (D-13).
    seven_profiles_for_one     "has anyone bought today that has bought before" answered
                               correctly with ONE and drawn as seven 265 px customer cards,
                               delivered as two telemetry frames 41 ms apart.
    the_same_record_twice      one deck, one customer, drawn at index 0 and again at index 3.
    feedback_that_was_recorded four of the owner's own sentences, recorded, with the mutation
                               words that made three of them UNFULFILLED_ACTION.
    wordless_notifications     sixteen notifications, eleven with nothing to read.
    asked_to_see_and_saw_nothing
                               "can you expand his customer page" → a 1,014 px capability
                               card; said again → nothing; "No, bring up a UI for the
                               customer's page" → nothing.
    answered_about_someone_else
                               the worst turn of the evening: the order in focus won over the
                               name he said, and the same question a minute later resolved the
                               name and answered about somebody different.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

T0 = 1_800_000_000.0
SESSION = "ts-20260911-201129-phase-5-fixture"

# Invented ids, in the shape the real ones have. Seven customers for the seven-profile deck.
CUSTOMERS = [
    "gid://shopify/Customer/70000000000001",
    "gid://shopify/Customer/70000000000002",
    "gid://shopify/Customer/70000000000003",
    "gid://shopify/Customer/70000000000004",
    "gid://shopify/Customer/70000000000005",
    "gid://shopify/Customer/70000000000006",
    "gid://shopify/Customer/70000000000007",
]
# The two people the wrong-entity turn confuses. Invented names, invented ids.
ASKED_ABOUT = "Rowan Mitcham"          # who the owner named
ASKED_ABOUT_ID = "gid://shopify/Customer/70000000000003"
HELD_INSTEAD = "Tessa Bramley"         # whose history it spoke
HELD_INSTEAD_ID = "gid://shopify/Customer/70000000000001"
HELD_ORDER = "gid://shopify/Order/70000000000901"


class Tape:
    """A timeline, written the way the Mac and the tablet write one."""

    def __init__(self, session_id: str = SESSION, start: float = T0) -> None:
        self.session_id = session_id
        self.now = start
        self.seq = 0
        self.events: list[dict[str, Any]] = []
        self.add("session_started", name="phase 4 live tablet test", started_at=start)

    def add(self, kind: str, *, source: str = "mac", step: float = 0.1, **fields: Any) -> dict[str, Any]:
        self.now += step
        self.seq += 1
        event = {"ts": round(self.now, 3), "iso": "2026-09-11T20:11:29", "seq": self.seq,
                 "test_session_id": self.session_id, "source": source, "kind": kind}
        event.update({k: v for k, v in fields.items() if v is not None})
        self.events.append(event)
        return event

    def gap(self, seconds: float = 30.0) -> None:
        self.now += seconds

    @property
    def t(self) -> int:
        """The tablet's own millisecond clock, which is what the touch rules read."""
        return int(self.now * 1000)

    def write(self, tmp_path: Path) -> Path:
        self.add("session_stopped", name="phase 4 live tablet test", duration_s=round(self.now - T0, 3))
        Path(tmp_path).mkdir(parents=True, exist_ok=True)
        path = Path(tmp_path) / f"{self.session_id}.jsonl"
        path.write_text("".join(json.dumps(e) + "\n" for e in self.events), encoding="utf-8")
        return path


# ------------------------------------------------------------------------ small writers


def turn(tape: Tape, turn_id: str, *, said: str = "", answer: str = "", ui: list[str] | None = None,
         ms: float = 900.0, error_kind: str | None = None, family: str | None = None,
         entities: list[dict[str, str]] | None = None, stt_ok: bool = True,
         stt_reason: str | None = None, step: float = 0.1) -> str:
    tape.add("turn_started", session_id="s1", turn_id=turn_id, input="audio", turns_before=0,
             epoch=1, step=step)
    if said or not stt_ok:
        tape.add("stt", session_id="s1", turn_id=turn_id, ok=stt_ok, engine="scribe",
                 text=said or None, raw_text=said or None, audio_s=2.2, reason=stt_reason)
        tape.add("lane", session_id="s1", turn_id=turn_id, lane="NORMAL", branch_id="br_left",
                 family=family, confidence=0.0, reason="no family matched",
                 signals={"question": True})
    tape.add("turn_finished", session_id="s1", turn_id=turn_id, question=said or None,
             answer=answer or None, ui=ui or ["assistant"], ms=ms, error_kind=error_kind,
             ui_entities=entities, timings={"total": ms})
    return turn_id


def render(tape: Tape, turn_id: str, cards: list[dict[str, Any]], *, step: float = 0.1) -> dict[str, Any]:
    return tape.add("tablet_render", source="tablet", session_id="s1", turn_id=turn_id,
                    screen="context", cards=cards, step=step,
                    viewport={"w": 601, "h": 889, "dpr": 1.33},
                    document={"cards_height": sum(int(c.get("height") or 0) for c in cards),
                              "cards_visible": 680},
                    overflow={"long_scroll": True, "clipped": 0}, t=tape.t)


def tool(tape: Tape, turn_id: str, name: str, args: dict[str, Any],
         result: dict[str, Any] | None = None) -> None:
    call = f"call_{tape.seq:04d}"
    tape.add("tool_requested", session_id="s1", turn_id=turn_id, tool_call_id=call, tool=name,
             args=args)
    tape.add("tool_finished", session_id="s1", turn_id=turn_id, tool_call_id=call, tool=name,
             ok=True, outcome="ok", ms=210.0, result=result or {"ok": True})


def hold(tape: Tape, turn_id: str | None, ms: float, *, target: str = "dock",
         outcome: str = "sent", too_short: bool = True, fingers: int = 0,
         owner: str | None = None, step: float = 0.35) -> None:
    """One press of the glass, exactly as the tablet reports one.

    `phase: "start"` carries the target, `phase: "release"` the duration and what became of
    the recording, and a second finger arrives as `phase: "multitouch"` two milliseconds AFTER
    the release it ended — which is where the real file puts all eighteen of its own.
    """
    tape.add("tablet_hold", source="tablet", session_id="s1", turn_id=turn_id, phase="start",
             state="ready", target=target, owner=owner, t=tape.t, step=step)
    tape.add("tablet_hold", source="tablet", session_id="s1", turn_id=turn_id, phase="release",
             ms=ms, outcome=outcome, t=int(tape.t + ms), step=ms / 1000.0)
    if fingers:
        tape.add("tablet_hold", source="tablet", session_id="s1", turn_id=turn_id,
                 phase="multitouch", fingers=fingers, target=target, t=int(tape.t + 2),
                 step=0.002)
    if too_short and outcome == "sent":
        tape.add("tablet_recording_too_short", source="tablet", session_id="s1", turn_id=turn_id,
                 ms=ms, t=tape.t, step=0.01)


def customer_card(index: int, ref: str, *, tab: str = "Overview", height: int = 265) -> dict[str, Any]:
    return {"i": index, "type": "customer", "ref": ref,
            "tabs": ["Overview", "Orders", "Email"], "tab_active": tab,
            "sections": ["Orders", "Email"], "relations": ["order"], "height": height}


# ------------------------------------------------------------------------- the fixtures


def swallowed_control_taps(tmp_path: Path) -> Path:
    """D-1 and D-13. The burst, the owner saying what it felt like, and the real holds in it.

    The eight durations are the real ones from 20:14:48–20:14:50. Eleven seconds after the
    last of them he said he could not click anything, which is what turns this burst from an
    inference into a corroborated finding.
    """
    tape = Tape()
    watching = turn(tape, "turn_taps", said="what came in today?", answer="Eight orders.",
                    ui=["order_list"])
    render(tape, watching, [{"i": 0, "type": "order_list", "height": 320}])

    # Eight taps on the branch chips, every one of them sent to the recogniser.
    for ms in (68, 46, 83, 68, 71, 94, 81, 67):
        hold(tape, watching, ms)

    tape.gap(8.0)
    said = ("Uh, can you also log, I cannot click the merge or close button or any of the "
            "other buttons for the two blobs, um, because wherever I press just leads to you "
            "listening")
    complaining = turn(tape, "turn_said_so", said=said,
                       answer="Logged against this test session, with the screen you were on.")
    tape.add("owner_feedback", session_id="s1", turn_id=complaining, branch_id="br_left",
             shape="log", text=said, screen=["order_list"], branch_status="ACTIVE")

    # D-13, in its own window: a burst of taps with a real, deliberate, properly held question
    # in the middle of it. The 4,526 ms hold came back empty and was filed under speech; his
    # other finger was starting and ending a competing recording on the same element throughout.
    tape.gap(60.0)
    hunting = turn(tape, "turn_hunting", said="where are the buttons?", answer="Here.",
                   ui=["order_list"])
    render(tape, hunting, [{"i": 0, "type": "order_list", "height": 320}])
    for ms in (104, 88, 81):
        hold(tape, hunting, ms)
    tape.add("tablet_hold", source="tablet", session_id="s1", turn_id=hunting, phase="start",
             state="ready", target="dock", t=tape.t, step=0.4)
    tape.add("tablet_hold", source="tablet", session_id="s1", turn_id=hunting, phase="release",
             ms=4526, outcome="sent", t=int(tape.t + 4526), step=4.526)
    drowned = turn(tape, "turn_drowned", said="", answer="I could not hear that clearly.",
                   stt_ok=False, stt_reason="empty transcript", error_kind="speech")
    for ms in (118, 88, 82):
        hold(tape, drowned, ms)

    # A genuine short attempt to speak, on its own, well away from any burst.
    tape.gap(90.0)
    speaking = turn(tape, "turn_short", said="", answer="That was too short.",
                    error_kind="empty")
    hold(tape, speaking, 400)

    # And a recording a second finger ended.
    tape.gap(60.0)
    collided = turn(tape, "turn_collided", said="", answer="I could not hear that clearly.",
                    stt_ok=False, stt_reason="empty transcript")
    hold(tape, collided, 820, fingers=2)
    return tape.write(tmp_path)


def a_tap_the_timeline_can_name(tmp_path: Path) -> Path:
    """Workstream A's richer signal: one 70 ms touch whose pointer OWNER is a control.

    No burst, no corroboration and no inference — the timeline says outright where the finger
    landed, which is what the touch-ownership state machine is for.
    """
    tape = Tape()
    only = turn(tape, "turn_named", said="what came in today?", answer="Eight orders.",
                ui=["order_list"])
    render(tape, only, [{"i": 0, "type": "order_list", "height": 320}])
    hold(tape, only, 70, target="branch-chip-merge", owner="branch-bar")
    return tape.write(tmp_path)


def seven_profiles_for_one_answer(tmp_path: Path) -> Path:
    """D-4. A list question answered with seven full profile pages, seven different people.

    The deck arrives as TWO telemetry frames 41 ms apart, which is what the real tablet did
    and what the old rule read as the same cards drawn again.
    """
    tape = Tape()
    asked = turn(tape, "turn_seven",
                 said="Has anyone bought today that has bought before and they're return, a returning customer?",
                 answer="One, Rowan — order 1962 today, and order 1833 back on the thirty-first of August.",
                 ui=["customer"] * 7,
                 entities=[{"type": "customer", "ref": ref} for ref in CUSTOMERS])
    for ref in CUSTOMERS:
        tool(tape, asked, "shopify_customer_history", {"customer_id": ref},
             {"customer_id": ref, "orders": 1})
    cards = [customer_card(i, ref, tab="Email") for i, ref in enumerate(CUSTOMERS)]
    render(tape, asked, cards)
    render(tape, asked, cards, step=0.041)
    return tape.write(tmp_path)


def the_same_record_twice(tmp_path: Path) -> Path:
    """The control for D-4: one deck, ONE customer, drawn twice in it. That is a duplicate."""
    tape = Tape()
    asked = turn(tape, "turn_twice", said="pull up that customer", answer="Here.",
                 ui=["customer", "order", "customer"],
                 entities=[{"type": "customer", "ref": CUSTOMERS[0]}])
    render(tape, asked, [
        customer_card(0, CUSTOMERS[0]),
        {"i": 1, "type": "order", "ref": HELD_ORDER, "height": 200},
        customer_card(2, CUSTOMERS[0]),
    ])
    return tape.write(tmp_path)


def feedback_that_was_recorded(tmp_path: Path) -> Path:
    """D-9. The owner reporting defects, in his own words, every one of them recorded.

    Three of these were filed UNFULFILLED_ACTION at severity 5/5 against "the write tools",
    because the classifier saw "make a note", "log" and "tag" and did not check that
    `owner_feedback` had already answered.
    """
    tape = Tape()
    for turn_id, shape, said in (
        ("turn_note", "record",
         "Okay, can you make a note of what you just failed to do, please? Can you tag that?"),
        ("turn_log_one", "log", "Can you just log your error there as well?"),
        ("turn_log_two", "log", "Log your error there"),
        ("turn_log_three", "log",
         "Uh, can you log that I'm not seeing any UI here except email where there's nothing? "
         "I want to also be seeing his orders and his history and like an email write box, and "
         "there's none of that here"),
    ):
        tape.gap(20.0)
        which = turn(tape, turn_id, said=said,
                     answer="Logged against this test session, with the screen you were on. It "
                            "will be in the report under owner-reported defects, so you will "
                            "not have to say it again.",
                     ui=["assistant"])
        tape.add("owner_feedback", session_id="s1", turn_id=which, branch_id="br_left",
                 shape=shape, text=said, screen=["customer"],
                 entities=[{"kind": "customer", "ref": CUSTOMERS[0]}], tab="orders",
                 branch_status="ACTIVE")
    return tape.write(tmp_path)


def wordless_notifications(tmp_path: Path) -> Path:
    """D-10. Sixteen notifications; eleven of them with nothing at all to read."""
    tape = Tape()
    only = turn(tape, "turn_notified", said="take that aside", answer="Divided.",
                ui=["order_list"])
    render(tape, only, [{"i": 0, "type": "order_list", "height": 320}])
    for code in ("divided", None, None, "merged", None, None, None, "divided", None, None,
                 None, "merged", None, None, "divided", None):
        tape.add("tablet_notify", source="tablet", session_id="s1", turn_id=only,
                 name="workspace", code=code, t=tape.t, step=1.5)
    return tape.write(tmp_path)


def asked_to_see_and_saw_nothing(tmp_path: Path) -> Path:
    """D-5. Three attempts at a customer page in twenty seconds, escalating to "bring up a UI".

    The first drew a 1,014 px list of what the system can do, which is not a customer page.
    The other two drew nothing and answered in speech.
    """
    tape = Tape()
    first = turn(tape, "turn_expand_one", said="Can you expand Rowan's customer page?",
                 answer="I can look at the shop, the inbox, and sales and stock.",
                 ui=["capability"])
    render(tape, first, [{"i": 0, "type": "capability", "height": 1014,
                          "tabs": ["The shop", "The inbox", "Sales and stock"]}])
    tape.gap(7.0)
    turn(tape, "turn_expand_two", said="Expand Rowan's customer page",
         answer="I cannot put that on the screen.", ui=[])
    tape.gap(13.0)
    turn(tape, "turn_expand_three", said="No, bring up a UI for the customer's page",
         answer="There is no way to bring that up.", ui=[])
    return tape.write(tmp_path)


def answered_about_someone_else(tmp_path: Path) -> Path:
    """D-14. He named one customer; it spoke another customer's history at him as fact.

    The failing turn hydrates from the ORDER already in focus and reads that order's customer.
    The turn a minute later runs a resolving read on the name he actually said and answers
    about somebody else — which is the only reason anybody knows the first one was wrong.
    Scored `backend = READ_OK / visible = DRAWN / experience = SUCCESSFUL` by the old rule.
    """
    tape = Tape()
    # The order is already in hand, from the turn before.
    held = turn(tape, "turn_held", said="open that order", answer="Order 1965, sixty pounds.",
                ui=["order"], entities=[{"type": "order", "ref": HELD_ORDER}])
    tool(tape, held, "shopify_order_detail", {"order_id": HELD_ORDER},
         {"order_id": HELD_ORDER, "customer_id": HELD_INSTEAD_ID})
    render(tape, held, [{"i": 0, "type": "order", "ref": HELD_ORDER, "height": 454}])

    tape.gap(18.0)
    wrong = turn(tape, "turn_wrong_person",
                 said=f"Um, what has {ASKED_ABOUT} ordered in his lifetime?",
                 answer=f"{HELD_INSTEAD}: 1 order, 60.0 GBP in total. The last was CROOKS-1965, "
                        f"£60.00 on 2026-09-11.",
                 ui=["customer"], family="customer_history_lookup",
                 entities=[{"type": "customer", "ref": HELD_INSTEAD_ID}])
    tool(tape, wrong, "shopify_order_detail", {"order_id": HELD_ORDER},
         {"order_id": HELD_ORDER, "customer_id": HELD_INSTEAD_ID})
    tool(tape, wrong, "shopify_customer_history", {"customer_id": HELD_INSTEAD_ID},
         {"customer_id": HELD_INSTEAD_ID, "orders": 1})
    render(tape, wrong, [customer_card(0, HELD_INSTEAD_ID, tab="Orders", height=454)])

    tape.gap(66.0)
    right = turn(tape, "turn_right_person",
                 said=f"Show me {ASKED_ABOUT}'s orders in his lifetime",
                 answer=f"{ASKED_ABOUT} — two orders, both today, sixty pounds each.",
                 ui=["customer"], family="customer_history_lookup",
                 entities=[{"type": "customer", "ref": ASKED_ABOUT_ID}])
    tool(tape, right, "shopify_find_customer", {"query": ASKED_ABOUT},
         {"customer_id": ASKED_ABOUT_ID})
    tool(tape, right, "shopify_customer_history", {"customer_id": ASKED_ABOUT_ID},
         {"customer_id": ASKED_ABOUT_ID, "orders": 2})
    render(tape, right, [customer_card(0, ASKED_ABOUT_ID, tab="Orders", height=454)])
    return tape.write(tmp_path)


# Every builder in this file, for the test that asserts each class has a fixture that
# produces it.
FIXTURES: tuple[tuple[str, Any], ...] = (
    ("swallowed_control_taps", swallowed_control_taps),
    ("a_tap_the_timeline_can_name", a_tap_the_timeline_can_name),
    ("seven_profiles_for_one_answer", seven_profiles_for_one_answer),
    ("the_same_record_twice", the_same_record_twice),
    ("feedback_that_was_recorded", feedback_that_was_recorded),
    ("wordless_notifications", wordless_notifications),
    ("asked_to_see_and_saw_nothing", asked_to_see_and_saw_nothing),
    ("answered_about_someone_else", answered_about_someone_else),
)
