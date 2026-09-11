"""What the owner says about the product while he is testing it (§16).

    "please log that your split function is broken. It just shows two of the same thing,
     and the applying button is also broken"
    "I've no tool for logging a product bug like that."

    …four turns later…

    "Log — a lot of your functions are broken… especially with the back button, back to
     assistant button and the next button"
    "I still have no tool that logs product feedback."

He did the most valuable thing a tester can do — narrate defects as they happen — and the
machine discarded all of it, twice, and then produced a report that did not mention them.

So: while a TEST SESSION is running, a sentence of that shape is recognised as local
development feedback and appended to the timeline as an `owner_feedback` event. What it is,
and what it is not:

* It is **observability metadata**, written to the same append-only timeline as everything
  else, and it is what `app/observability/report.py` reads to print OWNER-REPORTED DEFECTS
  verbatim. The owner never has to repeat himself after the session.
* It is **local**. Nothing here reaches Shopify or Gmail; this module imports neither, nor
  the action engine, nor any tool. There is no proposal, no arming, no gesture and no
  approval, because nothing is being changed — writing down what somebody said is not a
  change to the shop.
* It is **test mode only**. `record` writes nothing when no test session is active, so a
  sentence like this on an ordinary day is answered by the assistant as it always was.

On what it holds. The rule for the timeline is ids, counts, tool names and milliseconds, and
the one exception is what the OWNER said — the timeline already carries his question and the
answer on every turn, because a session you cannot read back is not a record. His feedback is
his own words about his own product; it is kept as he said it, bounded, and everything
AROUND it is ids: the branch, the card types on screen, the entity kind and ref, and the ids
of the commands and proposals nearby. No customer's name, no address, no label.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app.observability import timeline

MAX_FEEDBACK_CHARS = 600
# How far back a command or an action still counts as "what he was doing when he said it".
NEARBY_S = 90.0
MAX_NEARBY = 8

# The shapes the owner actually used, and the ones a tester reaches for. Each is anchored on
# an instruction to RECORD something, or on a plain statement that something is broken — a
# sentence that merely contains the word "log" ("the log says") is not one of these.
KINDS: tuple[tuple[str, Any], ...] = (
    ("log", re.compile(r"\b(?:please )?log(?: that| this| it)?\b(?!\s*(?:says?|file|in\b|out\b))", re.I)),
    ("note", re.compile(r"\b(?:note|make a note of|take a note of)\s+(?:that|this|the)\b|\bnote this bug\b", re.I)),
    ("record", re.compile(r"\brecord (?:that|this|it)\b|\bwrite (?:that|this) down\b|\bmake a note\b", re.I)),
    ("save_as_test", re.compile(r"\bsave (?:this|that|it) as a (?:test|case|regression)\b|\bturn (?:this|that) into a test\b", re.I)),
    ("broken", re.compile(r"\b(?:is|are|isn'?t|aren'?t|was|were)\s+(?:completely |totally |still |also |a bit |quite )?"
                          r"(?:broken|not working|buggy|stuck|frozen|dead|wrong|regressed)\b"
                          r"|\bdoes(?:n'?t| not) work(?: at all)?\b"
                          r"|\bthis is (?:a )?bug\b|\bthat'?s (?:a )?bug\b", re.I)),
)
# Words that make a "broken" sentence about the SHOP rather than about the product. "The
# order is wrong" is a complaint about an order; "the back button is broken" is a defect.
_ABOUT_THE_SHOP = re.compile(
    r"\b(?:order|orders|customer|customers|refund|invoice|address|delivery|parcel|tracking|"
    r"stock|price|product|discount|payment)\b", re.I)


@dataclass(frozen=True)
class Recognition:
    """A sentence read as feedback about the product, and which rule read it that way."""

    kind: str                # log | note | record | save_as_test | broken
    text: str                # what he said, as he said it

    def as_dict(self) -> dict[str, Any]:
        return {"kind": self.kind, "text": self.text}


def recognise(text: str) -> Recognition | None:
    """The sentence as local development feedback, or None.

    An instruction to log, note, record or save is feedback whatever else is in it: "log that
    the split is broken" and "log that the refund did not go through" are both things the
    owner wants written down. A bare statement that something is broken is feedback only when
    it is not about the shop, because "the order is wrong" is a job, not a bug report.
    """
    said = " ".join(str(text or "").split())
    if not said:
        return None
    for kind, pattern in KINDS:
        if not pattern.search(said):
            continue
        if kind == "broken" and _ABOUT_THE_SHOP.search(said):
            return None
        return Recognition(kind=kind, text=said[:MAX_FEEDBACK_CHARS])
    return None


# ------------------------------------------------------------------- what was on screen


def _screen(branch: Any) -> list[str]:
    """The card types this half last put on the glass. Types, never their contents."""
    ui = getattr(branch, "last_ui", None) or []
    return [str(u.get("type") or "") for u in ui if isinstance(u, dict) and u.get("type")][:6]


def _entities(branch: Any) -> list[dict[str, str]]:
    """What the half is on, and what it has been on. Kind and ref — never the label, which is
    a customer's name."""
    out: list[dict[str, str]] = []
    entity = getattr(branch, "entity", None) or {}
    if entity.get("kind") and entity.get("ref"):
        out.append({"kind": str(entity["kind"]), "ref": str(entity["ref"])})
    for recent in (getattr(branch, "recent_entities", None) or [])[:4]:
        if not isinstance(recent, dict) or not recent.get("ref"):
            continue
        row = {"kind": str(recent.get("kind") or ""), "ref": str(recent["ref"])}
        if row not in out:
            out.append(row)
    return out[:5]


def context(branch: Any, *, now: float | None = None) -> dict[str, Any]:
    """Everything the event carries about WHERE the owner was when he said it: the half, the
    screen, the records in hand, and the ids of what happened around him."""
    return {
        "branch_id": str(getattr(branch, "branch_id", "") or ""),
        "branch_status": str(getattr(branch, "status", "") or ""),
        "screen": _screen(branch),
        "entities": _entities(branch),
        "tab": str(getattr(branch, "tab", "") or ""),
        "nearby": timeline.current().recent(within_s=NEARBY_S, limit=MAX_NEARBY, now=now),
    }


# -------------------------------------------------------------------------- recording


def record(recognition: Recognition, *, branch: Any = None, session_id: str = "",
           turn_id: str = "", now: float | None = None) -> dict[str, Any] | None:
    """Append the feedback to the timeline. Returns the event, or None when nothing is
    recording.

    Nothing here can fail a turn: `timeline.emit` is a queue put that never raises, and with
    no test session active this is one cached stat and a return.
    """
    if timeline.current().own is None:
        return None
    where = context(branch, now=now)
    return timeline.emit(
        "owner_feedback",
        session_id=session_id or None,
        turn_id=turn_id or None,
        branch_id=where["branch_id"] or None,
        # `shape`, not `kind`: every timeline event's `kind` is the event's own name, and this
        # event's name is `owner_feedback`. What KIND of feedback it is goes beside it.
        shape=recognition.kind,
        text=recognition.text,
        screen=where["screen"] or None,
        entities=where["entities"] or None,
        tab=where["tab"] or None,
        branch_status=where["branch_status"] or None,
        nearby=where["nearby"] or None,
    )


def active() -> bool:
    """Whether a test session is running, so feedback has somewhere to go."""
    return timeline.current().own is not None
