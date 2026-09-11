"""Spoken self-correction: "today's — uh — yesterday's orders" is a question about yesterday.

D-8 in docs/phase4/LIVE_SESSION_FORENSICS.md. The owner said it, the extractor took the first
temporal phrase, and the answer was "No orders today." He repeated himself and got ten orders.

The rule under test is narrow on purpose: a later explicit value wins ONLY when a correction
marker stands between the two, and never when the syntax says both were meant. The
must-not-flip cases below are half the point — a rule that always takes the last noun answers
"compare today with yesterday" about yesterday alone.
"""

from __future__ import annotations

import pytest

from app.fastpath.correction import corrected, corrections
from app.fastpath.intent import _tokens
from app.fastpath.library import period_from

# (said, family, what should win)
CORRECTED = [
    ("can you pull up today's, uh, yesterday's orders, please?", "period", "yesterday"),
    ("show me this week's sales, sorry, last week's", "period", "last_week"),
    ("order 1956, I mean 1957", "order_number", "1957"),
    ("a medium, no, a large", "size", "large"),
    # The same four in the other shapes a person says them.
    ("today's orders, er, yesterday's", "period", "yesterday"),
    ("this week, actually last week", "period", "last_week"),
    ("1956, sorry, 1957", "order_number", "1957"),
    ("medium, er, large", "size", "large"),
]

# Said in a shape where the LATER value must not win.
MUST_NOT_FLIP = [
    "compare today with yesterday",
    "today and yesterday",
    "how many orders yesterday compared to today",
    "last week against this week",
    "orders from 1956 to 1957",
    "1956 and 1957",
    "medium and large",
    "do we have it in medium or large",
    "this week versus last week",
]


@pytest.mark.parametrize("said,family,wins", CORRECTED)
def test_the_later_corrected_value_wins(said, family, wins):
    found = {c.family: c for c in corrections(_tokens(said.lower()))}
    assert family in found, f"no correction found in {said!r}"
    assert found[family].value == wins
    assert found[family].superseded and found[family].superseded != wins


@pytest.mark.parametrize("said", MUST_NOT_FLIP)
def test_two_values_meant_together_are_not_a_correction(said):
    assert corrections(_tokens(said.lower())) == [], f"{said!r} was read as a correction"


def test_a_negated_later_value_leaves_the_earlier_one_standing():
    found = {c.family: c for c in corrections(_tokens("yesterday's orders, not today's"))}
    assert "period" in found
    assert found["period"].value == "yesterday" and found["period"].superseded == "today"


def test_one_value_on_its_own_is_never_a_correction():
    for said in ("yesterday's orders", "order 1957", "a large", "this week's sales"):
        assert corrections(_tokens(said)) == []


def test_corrected_names_the_value_for_one_family():
    assert corrected(_tokens("today's, uh, yesterday's orders"), "period") == "yesterday"
    assert corrected(_tokens("today's orders"), "period") == ""


def test_the_period_extractor_takes_the_correction():
    """The bug itself. `period_from` declined when it saw two temporal words, and the caller's
    fallback was "today" — so the owner's correction was answered for the word he corrected."""
    assert period_from(_tokens("can you pull up today's, uh, yesterday's orders, please?")) == "yesterday"
    assert period_from(_tokens("show me this week's sales, sorry, last week's")) == "last_week"
    # And still declines where two periods were both meant.
    assert period_from(_tokens("compare this week with last week")) is None
    assert period_from(_tokens("today and yesterday")) is None
