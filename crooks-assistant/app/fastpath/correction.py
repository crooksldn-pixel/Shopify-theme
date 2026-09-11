"""Spoken self-correction: the value the owner corrected to, not the one he corrected.

D-8. The owner said

    "can you pull up today's, uh, yesterday's orders, please?"

and was told "No orders today." He said it again without the stumble and got ten orders. The
period extractor saw two temporal words, declined, and its caller's fallback was "today" — so
the machine answered the word he had just taken back.

The rule is deliberately narrow, because the wrong version of it is worse than the bug. A
rule that takes the last value would answer "compare today with yesterday" about yesterday
alone, and "orders from 1956 to 1957" about one order. So a correction needs THREE things:

1. two values of the same FAMILY (two periods, two order numbers, two sizes) in one sentence;
2. a correction marker between them — a hesitation ("uh", "er"), an apology ("sorry"), a
   retraction ("no", "actually", "I mean", "make that");
3. nothing between them that says both were meant — a conjunction, a comparison, a range.

And one more shape, which is the same rule read backwards: when the LATER value is negated
("yesterday's orders, not today's"), the earlier one is the one that stands.

Everything else is left alone: a sentence with one value, or two values joined by "and", has
no correction in it, and `corrections()` returns nothing. tests/test_self_correction.py holds
the four pairs the brief names and the nine sentences that must not flip.
"""

from __future__ import annotations

from dataclasses import dataclass

# ------------------------------------------------------------------ what can be corrected

# A family is an ordered list of (words that name a value, the value). Multi-word forms come
# first so "last week" is found before "week". The value strings are what the read layer
# already calls these things — the period names in app/analytics/periods.py:NAMED, a bare
# order number, a size as the catalogue spells it.
_PERIOD_FORMS: tuple[tuple[tuple[str, ...], str], ...] = (
    (("last", "week"), "last_week"),
    (("this", "week"), "this_week"),
    (("last", "month"), "last_month"),
    (("this", "month"), "this_month"),
    (("today",), "today"),
    (("yesterday",), "yesterday"),
    (("tomorrow",), "tomorrow"),
    (("week",), "this_week"),
    (("month",), "this_month"),
)
_SIZE_FORMS: tuple[tuple[tuple[str, ...], str], ...] = (
    (("extra", "small"), "xs"), (("extra", "large"), "xl"),
    (("xsmall",), "xs"), (("xlarge",), "xl"), (("xxl",), "xxl"), (("xl",), "xl"), (("xs",), "xs"),
    (("small",), "small"), (("medium",), "medium"), (("large",), "large"),
)

PERIOD = "period"
ORDER_NUMBER = "order_number"
SIZE = "size"
FAMILIES = (PERIOD, ORDER_NUMBER, SIZE)

# A stumble, an apology, or a retraction. What separates "today's, uh, yesterday's" from
# "today and yesterday".
MARKERS = frozenset({
    "uh", "um", "er", "erm", "ah", "eh", "hmm", "mmm",
    "sorry", "apologies", "no", "nope", "actually", "rather", "wait", "scratch",
    "correction", "mean", "meant", "means",
})
# Two values were both meant: a conjunction, a comparison, or a range. Any of these between
# them and there is no correction, whatever markers are also in the gap.
TOGETHER = frozenset({
    "and", "or", "with", "plus", "both", "versus", "vs", "against", "compare", "compared",
    "comparison", "comparing", "between", "through", "til", "till", "until", "to", "than",
    "alongside", "well",
})
# The later value is being refused, so the earlier one stands. Checked at the END of the gap
# — immediately before the later value — because "not" earlier in a sentence is about
# something else.
REFUSERS = frozenset({"not", "isnt", "arent", "wasnt", "werent", "dont", "doesnt", "didnt", "never"})
# "rather than X" and "instead of X" refuse X; "rather" and "instead" alone are retractions.
_REFUSING_PAIRS = (("rather", "than"), ("instead", "of"), ("opposed", "to"))
# How far before the later value a refuser still attaches to it.
REFUSER_REACH = 3


@dataclass(frozen=True, slots=True)
class Correction:
    """One value the owner replaced, and what he replaced it with."""

    family: str
    value: str                 # what stands
    superseded: str            # what it replaced
    marker: str                # the word that made it a correction
    at: int                    # the index of the winning value's first word

    def public(self) -> dict[str, str | int]:
        return {"family": self.family, "value": self.value, "superseded": self.superseded,
                "marker": self.marker, "at": self.at}


# ------------------------------------------------------------------ finding the values


def _mentions(words: tuple[str, ...], family: str) -> list[tuple[int, int, str]]:
    """(start, end, value) for each value of this family the words name, in the order said.

    `end` is exclusive, so the gap between two mentions is `words[a.end:b.start]`. A longer
    form wins over a shorter one at the same place: "last week" is one mention, not "week".
    """
    forms = {PERIOD: _PERIOD_FORMS, SIZE: _SIZE_FORMS}.get(family)
    out: list[tuple[int, int, str]] = []
    index = 0
    while index < len(words):
        if family == ORDER_NUMBER:
            word = words[index]
            if word.isdigit() and 3 <= len(word) <= 6:
                out.append((index, index + 1, word))
            index += 1
            continue
        matched = 0
        for needed, value in forms or ():
            if tuple(words[index:index + len(needed)]) == needed:
                out.append((index, index + len(needed), value))
                matched = len(needed)
                break
        index += matched or 1
    return out


def _gap_reading(gap: tuple[str, ...]) -> tuple[str, str]:
    """What the words between two values say about them: ("correction", marker),
    ("refused", marker) or ("together", word) — or ("", "") when they say nothing."""
    have = set(gap)
    # A range or a comparison outranks everything: "from 1956 to 1957" names two orders even
    # though a person may hesitate in the middle of it.
    for word in gap:
        if word in TOGETHER:
            return "together", word
    for first, second in _REFUSING_PAIRS:
        for n in range(len(gap) - 1):
            if gap[n] == first and gap[n + 1] == second:
                return "refused", f"{first} {second}"
    tail = gap[-REFUSER_REACH:] if gap else ()
    for word in tail:
        if word in REFUSERS:
            return "refused", word
    for word in gap:
        if word in MARKERS:
            return "correction", word
    if have:
        return "", ""
    return "", ""


def corrections(words: tuple[str, ...]) -> list[Correction]:
    """Every family the owner corrected himself about, in the order the sentence said them.

    Takes the tokens `app/fastpath/intent.py::_tokens` produces — possessives already
    stripped, so "today's" is "today" and "yesterday's" is "yesterday", and the hesitation
    words are still there, which is what makes this possible at all.
    """
    out: list[Correction] = []
    for family in FAMILIES:
        found = _mentions(words, family)
        if len(found) < 2:
            continue
        standing: tuple[int, int, str] | None = None
        marker = ""
        superseded = ""
        for earlier, later in zip(found, found[1:], strict=False):
            base = standing or earlier
            reading, word = _gap_reading(tuple(words[base[1]:later[0]]))
            if reading == "together":
                standing = None
                break
            if base[2] == later[2]:
                continue            # the same value said twice is not a correction
            if reading == "correction":
                standing, marker, superseded = later, word, base[2]
            elif reading == "refused":
                standing, marker, superseded = base, word, later[2]
        if standing is not None and marker and superseded and standing[2] != superseded:
            out.append(Correction(family=family, value=standing[2], superseded=superseded,
                                  marker=marker, at=standing[0]))
    return out


def corrected(words: tuple[str, ...], family: str) -> str:
    """The value that stands for one family, or empty when nothing was corrected."""
    for found in corrections(words):
        if found.family == family:
            return found.value
    return ""
