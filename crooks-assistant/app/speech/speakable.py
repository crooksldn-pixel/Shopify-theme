"""Turning an answer written for a screen into an answer written for a mouth.

The system prompt already asks Claude for short, markdown-free, spoken-shaped sentences, and
most of the time it obliges. This module is the safety net for the times it does not, and for
the two things a text-to-speech engine reliably gets wrong for this business:

    "£430.50"     ->  "four hundred and thirty pounds fifty"
    "order #1930" ->  "order nineteen thirty"

Everything here is deterministic and conservative. It removes formatting, it re-spells numbers
that have a known spoken form, and it does nothing else — no summarising, no rephrasing, no
dropping of clauses. A sentence that reaches this module with a fact in it leaves with the same
fact in it, because the owner is going to act on what he hears.
"""

from __future__ import annotations

import re

# --------------------------------------------------------------------------- number words

_ONES = (
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
    "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen",
    "nineteen",
)
_TENS = (
    "", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety",
)

# Above this, spelling a number out stops helping: "one hundred and twenty-three thousand
# four hundred and fifty-six" is worse to hear than the digits, which the engine reads itself.
MAX_SPELLED = 999_999


def number_words(value: int) -> str:
    """British spoken form of a non-negative integer: 430 -> "four hundred and thirty"."""
    if value < 0 or value > MAX_SPELLED:
        raise ValueError(f"{value} is outside the range this speaks")
    if value < 20:
        return _ONES[value]
    if value < 100:
        tens, ones = divmod(value, 10)
        return _TENS[tens] + (f"-{_ONES[ones]}" if ones else "")
    if value < 1000:
        hundreds, rest = divmod(value, 100)
        head = f"{_ONES[hundreds]} hundred"
        return f"{head} and {number_words(rest)}" if rest else head
    thousands, rest = divmod(value, 1000)
    head = f"{number_words(thousands)} thousand"
    if not rest:
        return head
    # "one thousand and thirty", but "one thousand nine hundred and thirty".
    joiner = " and " if rest < 100 else " "
    return f"{head}{joiner}{number_words(rest)}"


def order_number_words(digits: str) -> str:
    """How this office reads an order number aloud: 1930 -> "nineteen thirty".

    Four digits are read as two pairs, which is what the owner says and what he expects back.
    Anything else keeps its digits: there is no agreed spoken form for them, and inventing one
    is how "order 12345" becomes unrecognisable."""
    if len(digits) != 4:
        return digits
    value = int(digits)
    high, low = divmod(value, 100)
    if high < 10 or high % 10 == 0:
        # 1000, 2000, 0999 — "twenty hundred" is not English and "ten oh five" is not what
        # anyone says, so these keep the plain cardinal, which is never wrong.
        return number_words(value)
    if low == 0:
        return f"{number_words(high)} hundred"
    if low < 10:
        return f"{number_words(high)} oh {number_words(low)}"
    return f"{number_words(high)} {number_words(low)}"


# --------------------------------------------------------------------------- money

_MONEY = re.compile(r"£\s?(\d{1,3}(?:,\d{3})+|\d+)(?:\.(\d{1,2}))?")


def _money_words(match: re.Match) -> str:
    whole = int(match.group(1).replace(",", ""))
    pence_text = match.group(2) or ""
    # "£430.5" is four hundred and thirty pounds fifty: a lone decimal digit is tenths.
    if len(pence_text) == 1:
        pence_text = f"{pence_text}0"
    pence = int(pence_text) if pence_text else 0
    if whole > MAX_SPELLED:
        # Keep the figure exact and let the engine read the digits; "£" alone is what it
        # cannot be trusted with.
        return f"{match.group(1)} pounds" + (f" {pence_text}" if pence else "")
    if whole == 0 and pence:
        return f"{number_words(pence)} pence"
    unit = "pound" if whole == 1 and not pence else "pounds"
    spoken = f"{number_words(whole)} {unit}"
    if not pence:
        return spoken
    # "£430.05" is "four hundred and thirty pounds oh five", the way a till reads it back.
    if len(pence_text) == 2 and pence < 10:
        return f"{spoken} oh {number_words(pence)}"
    return f"{spoken} {number_words(pence)}"


# --------------------------------------------------------------------------- order numbers

# An order-ish cue, then an optional hash, then the digits. The cue is required: a bare
# four-digit number in "1930 units in stock" is a quantity, not an order.
_ORDER = re.compile(r"\b(order|invoice)s?\b([\s:,-]*(?:number|no\.?)?[\s:,-]*)#?\s*(\d{3,6})\b", re.I)
# A hash in front of digits is always an identifier being read out, wherever it appears.
_HASH_NUMBER = re.compile(r"#\s*(\d{3,6})\b")


def _order_words(match: re.Match) -> str:
    # "order number 1930" and "order no. 1930" are both just "order nineteen thirty" aloud —
    # "no." in particular is read as the word "no", which is worse than saying nothing.
    return f"{match.group(1)} {order_number_words(match.group(3))}"


# --------------------------------------------------------------------------- formatting

_FENCE = re.compile(r"```.*?```", re.S)
_HTML_TAG = re.compile(r"<[^>\n]{1,200}>")
_URL = re.compile(r"\b(?:https?://|www\.)\S+", re.I)
_MD_LINK = re.compile(r"\[([^\]]{1,120})\]\((?:[^)]{0,300})\)")
_MD_EMPHASIS = re.compile(r"(\*{1,3}|_{1,3})(?=\S)(.+?)(?<=\S)\1", re.S)
_MD_BULLET = re.compile(r"^[ \t]*(?:[-*+•]|\d{1,2}[.)])[ \t]+", re.M)
_MD_HEADING = re.compile(r"^[ \t]*#{1,6}[ \t]+", re.M)
_MD_QUOTE = re.compile(r"^[ \t]*>[ \t]?", re.M)
# What is left once the meaning has been taken out: table pipes, rules, stray markup.
_LEFTOVER = re.compile(r"[*_`~|^{}\[\]<>\\]|(?<!\w)#(?!\w)")
# "Really?!?" and "Wait..." are typography, not speech; the engine reads a run of marks as a
# longer pause at best and as nothing at all at worst.
_REPEATED_PUNCT = re.compile(r"([!?.,;:])[!?.,;:]+")
_SPACE_BEFORE_PUNCT = re.compile(r"\s+([,.;:!?])")


def _line_break(match: re.Match) -> str:
    before = match.string[: match.start()].rstrip()
    return ". " if before and before[-1] not in ".!?:," else " "


def to_speakable(text: str, *, max_chars: int = 1200) -> str:
    """The answer, as it should be said. Empty when there is nothing worth saying."""
    if not text:
        return ""
    out = _FENCE.sub(" ", text)
    out = _MD_LINK.sub(r"\1", out)          # link text is speech; the target is not
    out = _URL.sub("a link", out)
    out = _HTML_TAG.sub(" ", out)
    out = _MD_HEADING.sub("", out)
    out = _MD_QUOTE.sub("", out)
    out = _MD_BULLET.sub("", out)
    out = _MD_EMPHASIS.sub(r"\2", out)
    out = _MONEY.sub(_money_words, out)
    out = _ORDER.sub(_order_words, out)
    out = _HASH_NUMBER.sub(lambda m: order_number_words(m.group(1)), out)
    out = out.replace("&", " and ").replace("%", " percent")
    out = _LEFTOVER.sub(" ", out)
    out = _REPEATED_PUNCT.sub(r"\1", out)
    # A line break is a pause to the eye and nothing at all to the ear, so it becomes the
    # full stop it was standing in for — otherwise a two-line list is read as one long clause.
    out = re.sub(r"[ \t]*\n[ \t\n]*", _line_break, out)
    out = _SPACE_BEFORE_PUNCT.sub(r"\1", out)
    out = _REPEATED_PUNCT.sub(r"\1", out)
    out = re.sub(r"\s{2,}", " ", out).lstrip(" .;:,-").rstrip(" ;:,-").strip()
    if len(out) > max_chars:
        cut = out[:max_chars]
        out = (cut[: cut.rfind(".") + 1] or cut).strip()
    # A residue of punctuation is not speech; do not spend a request saying it.
    return out if re.search(r"[A-Za-z0-9]", out) else ""
