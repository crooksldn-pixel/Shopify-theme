"""Turn what Whisper heard into what was actually said.

Whisper has never seen "Yard Jeans" and will confidently produce "yard genes". No general model
fixes that; a small catalogue of the words this business actually uses does. The catalogue is a
hand-written seed file at M3 and the live Shopify product/customer list from M7 — same interface,
so nothing downstream changes when it is repointed.

Phonetics use jellyfish's Metaphone. The plan specified Double Metaphone, which jellyfish removed
in 1.0; Metaphone is the closest maintained equivalent and is what the thresholds below were
tuned against.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from pathlib import Path

from jellyfish import metaphone
from rapidfuzz import fuzz

log = logging.getLogger("crooks.normalise")

# A fuzzy match this good is a match. Tuned so "yard genes" -> "Yard Jeans" lands but two
# genuinely different product names never collapse into one another.
FUZZY_THRESHOLD = 82
# A weaker fuzzy score is still accepted when the phonetic codes agree exactly, which is the
# case that matters: heard correctly, spelled wrongly.
PHONETIC_FUZZY_FLOOR = 62

_UNITS = {
    "zero": 0, "oh": 0, "o": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
    "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17,
    "eighteen": 18, "nineteen": 19,
}
_TENS = {
    "twenty": 20, "thirty": 30, "forty": 40, "fourty": 40, "fifty": 50, "sixty": 60,
    "seventy": 70, "eighty": 80, "ninety": 90,
}
_WORD_RE = re.compile(r"[A-Za-z0-9']+|[^\sA-Za-z0-9']")
_ORDER_CUE = re.compile(r"\b(order|invoice|number|no\.?)\s*#?\s*", re.I)


@dataclass(slots=True)
class Match:
    heard: str
    replaced_with: str
    score: float
    via: str  # "fuzzy" or "phonetic"


@dataclass(slots=True)
class Normalised:
    raw: str
    text: str
    matches: list[Match] = field(default_factory=list)
    order_numbers: list[str] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return self.raw != self.text


# --------------------------------------------------------------------------- catalogue


class Catalogue:
    """The set of terms worth correcting towards. Swappable: M3 loads a file, M7 loads Shopify."""

    def __init__(self, terms: Iterable[str]) -> None:
        seen: dict[str, str] = {}
        for term in terms:
            term = " ".join(term.split())
            if term and term.lower() not in seen:
                seen[term.lower()] = term
        self.terms: list[str] = list(seen.values())
        self._codes: list[str] = [self._code(t) for t in self.terms]
        self.max_words: int = max((len(t.split()) for t in self.terms), default=1)

    @staticmethod
    def _code(text: str) -> str:
        return " ".join(metaphone(w) for w in text.split() if w)

    def best(self, phrase: str) -> tuple[str, float, str] | None:
        """Best catalogue entry for a heard phrase, or None."""
        if not phrase.strip():
            return None
        code = self._code(phrase)
        best: tuple[str, float, str] | None = None
        for term, term_code in zip(self.terms, self._codes, strict=True):
            score = fuzz.token_sort_ratio(phrase.lower(), term.lower())
            via = "fuzzy"
            if score < FUZZY_THRESHOLD and code and code == term_code:
                score = max(score, FUZZY_THRESHOLD)
                via = "phonetic"
            elif score < FUZZY_THRESHOLD and code and term_code and score >= PHONETIC_FUZZY_FLOOR:
                # Same number of syllables landing on the same codes word-for-word.
                if sum(a == b for a, b in zip(code.split(), term_code.split(), strict=False)):
                    if code.split()[-1:] == term_code.split()[-1:]:
                        score = max(score, FUZZY_THRESHOLD)
                        via = "phonetic"
            if score >= FUZZY_THRESHOLD and (best is None or score > best[1]):
                best = (term, float(score), via)
        return best

    def __len__(self) -> int:
        return len(self.terms)


def load_terms(path: Path) -> list[str]:
    """Read kb/terminology.md. Markdown list items and plain lines; '#' headings are sections."""
    if not path.exists():
        log.warning("terminology file %s not found — normalisation will be a no-op", path)
        return []
    terms: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith(">"):
            continue
        line = re.sub(r"^[-*+]\s+", "", line)
        line = re.sub(r"\s*(#|//|—).*$", "", line).strip()  # trailing comments
        if line:
            terms.append(line)
    return terms


# --------------------------------------------------------------------------- numbers


def words_to_digits(tokens: list[str]) -> list[str]:
    """Collapse spoken digit strings into numbers.

    "four eight three two" -> "4832"; "forty eight thirty two" -> "4832". Both are how people
    read an order number aloud, and Whisper transcribes them as words.
    """
    out: list[str] = []
    i = 0
    while i < len(tokens):
        lower = tokens[i].lower().strip(".,?!")
        if lower in _UNITS or lower in _TENS:
            run: list[int] = []
            j = i
            while j < len(tokens):
                w = tokens[j].lower().strip(".,?!")
                if w in _UNITS:
                    run.append(_UNITS[w])
                elif w in _TENS:
                    nxt = tokens[j + 1].lower().strip(".,?!") if j + 1 < len(tokens) else ""
                    if nxt in _UNITS and _UNITS[nxt] < 10 and _UNITS[nxt] != 0:
                        run.append(_TENS[w] + _UNITS[nxt])
                        j += 1
                    else:
                        run.append(_TENS[w])
                elif w == "hundred" and run:
                    run[-1] *= 100
                else:
                    break
                j += 1
            if len(run) >= 2:
                out.append("".join(str(n) for n in run))
                i = j
                continue
            out.append(str(run[0]) if run else tokens[i])
            i = j if run else i + 1
            continue
        out.append(tokens[i])
        i += 1
    return out


def extract_order_numbers(text: str) -> list[str]:
    """Order numbers as CROOKS uses them: 3–6 digits, '#' optional, after an order-ish cue."""
    found: list[str] = []
    for match in re.finditer(r"#?\s*(\d{3,6})\b", text):
        digits = match.group(1)
        before = text[max(0, match.start() - 24) : match.start()]
        if _ORDER_CUE.search(before) or match.group(0).lstrip().startswith("#"):
            if digits not in found:
                found.append(digits)
    return found


# --------------------------------------------------------------------------- pipeline


class Normaliser:
    def __init__(self, catalogue_source: Callable[[], Catalogue]) -> None:
        self._source = catalogue_source
        self._cached: Catalogue | None = None

    @property
    def catalogue(self) -> Catalogue:
        if self._cached is None:
            self._cached = self._source()
        return self._cached

    def refresh(self) -> None:
        """Drop the cache. M7 calls this hourly once the catalogue is Shopify-backed."""
        self._cached = None

    def __call__(self, raw: str) -> Normalised:
        return self.normalise(raw)

    def normalise(self, raw: str) -> Normalised:
        text = raw.strip()
        if not text:
            return Normalised(raw=raw, text="")

        tokens = _WORD_RE.findall(text)
        tokens = words_to_digits(tokens)
        catalogue = self.catalogue
        matches: list[Match] = []

        # Score every candidate window, then take the best matches first. Scoring left to
        # right and taking the first hit lets a window absorb its neighbour — "many Blue Wash
        # Yard" scores 87 against "Blue Wash Yard Jeans", beating the threshold before the
        # correct alignment starting one word later is ever considered.
        candidates: list[tuple[float, int, int, str, str]] = []
        max_n = max(1, catalogue.max_words)
        for i in range(len(tokens)):
            for n in range(1, min(max_n, len(tokens) - i) + 1):
                window = tokens[i : i + n]
                if not any(w[:1].isalpha() for w in window):
                    continue
                phrase = " ".join(window)
                if len(phrase) < 3:
                    continue
                best = catalogue.best(phrase)
                if best is not None:
                    term, score, via = best
                    candidates.append((score, n, i, term, via))

        # Highest score wins; longer spans break ties, so the four-word product name is
        # preferred over the two-word one it contains.
        candidates.sort(key=lambda c: (-c[0], -c[1], c[2]))
        chosen: dict[int, tuple[int, str]] = {}
        taken: set[int] = set()
        for score, n, i, term, via in candidates:
            span = range(i, i + n)
            if any(k in taken for k in span):
                continue
            taken.update(span)
            chosen[i] = (n, term)
            phrase = " ".join(tokens[i : i + n])
            if term.lower() != phrase.lower():
                matches.append(Match(phrase, term, score, via))

        out: list[str] = []
        i = 0
        while i < len(tokens):
            if i in chosen:
                n, term = chosen[i]
                out.append(term)
                i += n
            else:
                out.append(tokens[i])
                i += 1

        matches.sort(key=lambda m: raw.lower().find(m.heard.lower().split()[0]))
        joined = _detokenise(out)
        joined = re.sub(r"\border\s+#\s*(\d)", r"order \1", joined, flags=re.I)
        return Normalised(
            raw=raw,
            text=joined,
            matches=matches,
            order_numbers=extract_order_numbers(joined),
        )


def _detokenise(tokens: list[str]) -> str:
    out = ""
    for token in tokens:
        if not out:
            out = token
        elif token in ",.?!;:'" or token.startswith("'"):
            out += token
        elif out.endswith(("#", "(")):
            out += token
        else:
            out += " " + token
    return out


def from_file(path: Path) -> Normaliser:
    """M3's normaliser: the hand-written seed list."""
    return Normaliser(lambda: Catalogue(load_terms(path)))


def from_terms(terms: Iterable[str]) -> Normaliser:
    """Test and M7 entry point: any iterable of terms."""
    frozen = list(terms)
    return Normaliser(lambda: Catalogue(frozen))
