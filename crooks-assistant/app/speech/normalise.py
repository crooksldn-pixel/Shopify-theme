"""Turn what Whisper heard into what was actually said.

Whisper has never seen "Yard Jeans" and will confidently produce "yard genes". No general model
fixes that; a small catalogue of the words this business actually uses does. The catalogue is a
hand-written seed file at M3 and the live Shopify product/customer list from M7 — same interface,
so nothing downstream changes when it is repointed.

Three things learned from the real CROOKSLDN catalogue shaped this module:

- Product names are stylised ("CRXST★RZ T-SHIRT", "MOTIONTEC™️") and will never be transcribed
  as spelled, so the seed file supports explicit spoken aliases: `cross stars tee => CRXST★RZ T-Shirt`.
- Whisper splits compound words ("hydro cuff wind breaker"), so a space-insensitive scorer is
  needed alongside the token scorer.
- Two products can differ only by colour ("BLACK/BLUE" vs "WHITE/RED MOTIONTEC SOCKS"). When a
  heard phrase scores equally against two terms the normaliser leaves it alone and reports the
  ambiguity — picking one silently is exactly the guess the whole product is built not to make.

Phonetics use jellyfish's Metaphone. The plan specified Double Metaphone, which jellyfish removed
in 1.0; Metaphone is the closest maintained equivalent and is what the thresholds below were
tuned against.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path

from jellyfish import metaphone
from rapidfuzz import fuzz

log = logging.getLogger("crooks.normalise")

# A fuzzy match this good is a match. Tuned on the real catalogue so "yard genes" → "Yard Jeans"
# lands but "cross stars tee" does not collapse into "Crooks Express Tee".
FUZZY_THRESHOLD = 85
# Two candidates this close are a tie, and a tie is not a decision.
AMBIGUITY_MARGIN = 3
# Windows and terms may differ by this many words (compound splits: "wind breaker").
MAX_WORD_COUNT_DIFF = 2

# A short single-word term — a colour, mostly — is one or two characters away from a dozen
# ordinary English words, so 85 is not evidence for it. Measured against the live catalogue:
# "back" scores 89 against "Black", "and" 86 against "Sand", "read" 86 against "Red", "one" 86
# against "Bone". Every one of those was a sentence the recogniser got RIGHT and we corrupted.
SHORT_TERM_CHARS = 6
SHORT_TERM_THRESHOLD = 92
# Metaphone codes collide constantly on short words ("what" and "white" are both WT), so an
# equal code is corroboration, never proof. It may only promote a match that already looks
# alike. "gray"/"Grey" scores 75 and is a real correction; "what"/"White" scores 67 and is not.
PHONETIC_MIN_RATIO = 70

# Ordinary English. A window made only of these is speech, not a product name: it may still
# match a catalogue entry exactly — "black" displays as "Black" — but it is never fuzzily or
# phonetically corrected towards one.
#
# This is the general form of the "what" → "White" bug. The live catalogue contributes the
# store's colour options as one-word terms, and one-word terms are close to ordinary speech;
# no threshold alone separates them, because the false matches score as high as the true ones.
# Knowing which words are ordinary English does separate them. Deliberately no colours, no
# garment nouns and no names in here — those are exactly the words a catalogue owns.
COMMON_WORDS = frozenset(
    """
    a about actually after again against all almost already also always am an and another any
    anyone anything are around as at away back be because been before being below best better
    between both but buy by call called came can cannot cant come coming could couldnt cover
    day days did didnt do does doesnt doing done dont down due during each early either else
    email emails enough even ever every everyone everything exactly far few find first for
    found from further get gets getting give given go goes going gone good got had hadnt has
    hasnt have havent having he her here hers herself hes him himself his how however i id if
    ill im in into is isnt it its itself ive just keep kept know known last late later least
    left less let lets like little long look looked looking lot made make makes making many
    may maybe me mean means might mine month months more morning most much must my myself
    near need needs never new next night no none nor not nothing now number of off often ok
    okay old on once one only or order ordered ordering orders other others our ours out over
    own past pay paid people per perhaps please put quite ran read really right run said same
    saw say saying says second see seen send sent several shall she shes should shouldnt show
    showed since so some someone something soon sorry still such take taken tell telling than
    thank thanks that thats the their theirs them themselves then there theres these they
    theyre theyve thing things think this those though through time times to today together
    told too took total two under until up upon us use used very want wanted was wasnt way we
    week weeks well went were weve what whats when where whether which while who whom whose
    why will with within without wont would wouldnt yes yesterday yet you your yours youre
    """.split()
)


def is_common_speech(phrase: str) -> bool:
    """True when every word of a cleaned phrase is ordinary English.

    Apostrophes are dropped first, so "what's" is judged as "whats"."""
    words = phrase.split()
    return bool(words) and all(w.replace("'", "") in COMMON_WORDS for w in words)


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
_WORD_RE = re.compile(r"[A-Za-z0-9'★™]+|[^\sA-Za-z0-9'★™]")
_ORDER_CUE = re.compile(r"\b(order|invoice|number|no\.?|crooks)[\s-]*#?\s*", re.I)

# Words people say one way and Shopify spells another. Applied to both sides before scoring.
_SYNONYMS = {"t shirt": "tee", "tshirt": "tee", "t-shirt": "tee", "hoody": "hoodie"}


def clean(text: str) -> str:
    """The comparison form: lower-case ASCII words, separators and symbols dropped, synonyms
    applied. 'BLACK/BLUE MOTIONTEC™️ SOCKS' → 'black blue motiontec socks'."""
    text = text.lower()
    text = re.sub(r"[/_&+\-]", " ", text)
    text = re.sub(r"[^a-z0-9' ]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    for spoken, canonical in _SYNONYMS.items():
        text = re.sub(rf"\b{re.escape(spoken)}\b", canonical, text)
    return text


def squash(text: str) -> str:
    return text.replace(" ", "")


def _swallows_ordinary_words(window: list[str], term: str) -> bool:
    """True if the window starts or ends on an ordinary English word the term does not have.

    Windows are scored at every offset, so a good match will always also be reachable one word
    in. Refusing the edge is how "how many Blue Wash Yard Jeans in medium" keeps its "many"
    and its "in"."""
    term_words = set(clean(term).split())
    for edge in (window[0], window[-1]):
        word = clean(edge)
        if word and word.replace("'", "") in COMMON_WORDS and word not in term_words:
            return True
    return False


def threshold_for(key: str) -> int:
    """How good a match has to be before it may overwrite what was said.

    Short single-word terms need more evidence than long ones: "Black" and "back" are one
    character apart, "Blue Wash Yard Jeans" and any ordinary phrase are not."""
    if len(key.split()) == 1 and len(key) <= SHORT_TERM_CHARS:
        return SHORT_TERM_THRESHOLD
    return FUZZY_THRESHOLD


@dataclass(slots=True)
class Match:
    heard: str
    replaced_with: str
    score: float
    via: str  # "fuzzy", "phonetic", "squashed" or "alias"


@dataclass(slots=True)
class Ambiguity:
    heard: str
    candidates: list[str]


@dataclass(slots=True)
class Normalised:
    raw: str
    text: str
    matches: list[Match] = field(default_factory=list)
    ambiguities: list[Ambiguity] = field(default_factory=list)
    order_numbers: list[str] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return self.raw != self.text


# --------------------------------------------------------------------------- catalogue


class Catalogue:
    """The set of terms worth correcting towards. Swappable: M3 loads a file, M7 loads Shopify."""

    def __init__(
        self,
        terms: Iterable[str],
        aliases: Mapping[str, str] | None = None,
        personal: Iterable[str] | None = None,
    ) -> None:
        seen: dict[str, str] = {}
        for term in terms:
            term = " ".join(str(term).split())
            if term.startswith("\x00"):
                continue  # runtime's product/customer boundary marker, not a term
            key = clean(term)
            if key and key not in seen:
                seen[key] = term
        self.aliases: dict[str, str] = {}
        for spoken, canonical in (aliases or {}).items():
            spoken_key = clean(spoken)
            canonical = " ".join(str(canonical).split())
            if not spoken_key or not canonical:
                continue
            self.aliases[spoken_key] = canonical
            seen.setdefault(clean(canonical), canonical)
        # Terms that are somebody's name. They still correct a transcript here on this Mac;
        # they are excluded from anything sent to a third party — see external_terms().
        self.personal: frozenset[str] = frozenset(
            k for k in (clean(p) for p in (personal or ())) if k
        )
        self.terms: list[str] = list(seen.values())
        self._by_key: dict[str, str] = dict(seen)  # comparison form -> display form
        self._keys: list[str] = list(seen.keys())
        self._codes: list[str] = [self._code(k) for k in self._keys]
        self._alias_keys: list[tuple[str, str]] = list(self.aliases.items())
        all_keys = self._keys + [k for k, _ in self._alias_keys]
        self.max_words: int = max((len(k.split()) for k in all_keys), default=1)

    @staticmethod
    def _code(text: str) -> str:
        return " ".join(metaphone(w) for w in text.split() if w)

    def prompt_terms(self) -> list[str]:
        """Terms for Whisper's initial prompt: display case, symbols dropped, hand-written
        spoken forms LAST because the prompt is truncated from the front.

        Case matters: Whisper copies the prompt's style, so an all-lower-case prompt yields
        an all-lower-case, unpunctuated transcript (measured, not assumed)."""
        out = [re.sub(r"[^A-Za-z0-9' ]+", " ", t).strip() for t in self.terms]
        out += [k.title() for k, _ in self._alias_keys]
        return [" ".join(t.split()) for t in dict.fromkeys(out) if t.strip()]

    def external_terms(self) -> list[str]:
        """prompt_terms() with the personal names removed: the only list allowed off this Mac.

        Whisper runs locally, so biasing it with a customer's name costs nothing. ElevenLabs
        does not, and a customer's name is personal data, not speech-bias vocabulary."""
        if not self.personal:
            return self.prompt_terms()
        return [t for t in self.prompt_terms() if clean(t) not in self.personal]

    def best(self, phrase: str) -> tuple[str, float, str] | None:
        """Best catalogue entry for a heard phrase. Returns ("", score, "ambiguous") on a tie."""
        pc = clean(phrase)
        if not pc:
            return None
        if pc in self.aliases:
            # A hand-written spoken form is a deliberate instruction and outranks every rule
            # below it, including the ordinary-English one.
            return self.aliases[pc], 100.0, "alias"

        if is_common_speech(pc):
            # Ordinary English. An exact catalogue entry may claim it ("black" → "Black"); a
            # near miss may not. Correcting a word the recogniser got right is the one failure
            # that turns a good transcript into a wrong answer, so this stays conservative.
            exact = self._by_key.get(pc)
            return (exact, 100.0, "exact") if exact else None

        p_words = len(pc.split())
        p_code = self._code(pc)
        p_squash = squash(pc)

        scored: dict[str, tuple[float, str]] = {}

        def consider(canonical: str, key: str, code: str) -> None:
            if abs(len(key.split()) - p_words) > MAX_WORD_COUNT_DIFF:
                return
            token_score = fuzz.token_sort_ratio(pc, key)
            squash_score = fuzz.ratio(p_squash, squash(key))
            score, via = max((token_score, "fuzzy"), (squash_score, "squashed"))
            threshold = threshold_for(key)
            if (
                score < threshold
                and p_code
                and code
                and p_code == code
                # An equal metaphone code promotes a match; it does not invent one.
                and max(token_score, squash_score) >= PHONETIC_MIN_RATIO
            ):
                score, via = float(threshold), "phonetic"
            if score >= threshold and score > scored.get(canonical, (0.0, ""))[0]:
                scored[canonical] = (float(score), via)

        for canonical, key, code in zip(self.terms, self._keys, self._codes, strict=True):
            consider(canonical, key, code)
        for spoken_key, canonical in self._alias_keys:
            consider(canonical, spoken_key, self._code(spoken_key))

        if not scored:
            return None
        ranked = sorted(scored.items(), key=lambda kv: -kv[1][0])
        (best_term, (best_score, via)) = ranked[0]
        if len(ranked) > 1 and ranked[0][1][0] - ranked[1][1][0] <= AMBIGUITY_MARGIN:
            return "", best_score, "ambiguous"
        return best_term, best_score, via

    def candidates(self, phrase: str, limit: int = 4) -> list[str]:
        """The near-ties for a phrase, for reporting an ambiguity."""
        pc = clean(phrase)
        scored = []
        for canonical, key in zip(self.terms, self._keys, strict=True):
            score = max(fuzz.token_sort_ratio(pc, key), fuzz.ratio(squash(pc), squash(key)))
            if score >= threshold_for(key) - AMBIGUITY_MARGIN:
                scored.append((score, canonical))
        return [c for _, c in sorted(scored, reverse=True)[:limit]]

    def __len__(self) -> int:
        return len(self.terms)


_ALIAS_RE = re.compile(r"^(.+?)\s*=>\s*(.+)$")


def load_terminology(path: Path) -> tuple[list[str], dict[str, str]]:
    """Read kb/terminology.md.

    One term per line; `- ` bullets allowed; `#` headings and `>` quotes ignored; a trailing
    `# comment` is stripped; `spoken form => Canonical Name` declares an alias.
    """
    if not path.exists():
        log.warning("terminology file %s not found — normalisation will be a no-op", path)
        return [], {}
    terms: list[str] = []
    aliases: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith(">"):
            continue
        line = re.sub(r"^[-*+]\s+", "", line)
        line = re.sub(r"\s+(#|//).*$", "", line).strip()
        if not line:
            continue
        alias = _ALIAS_RE.match(line)
        if alias:
            aliases[alias.group(1).strip()] = alias.group(2).strip()
        elif _looks_like_prose(line):
            log.debug("terminology: skipping prose line %r", line[:40])
        else:
            terms.append(line)
    return terms, aliases


def _looks_like_prose(line: str) -> bool:
    """A sentence, not a name: many words and sentence punctuation. No product is 8 words."""
    words = len(line.split())
    return words >= 8 or (words >= 6 and line.endswith((".", ":", ";")))


def load_terms(path: Path) -> list[str]:
    """Terms only. Kept for callers that do not care about aliases."""
    return load_terminology(path)[0]


# --------------------------------------------------------------------------- numbers


def words_to_digits(tokens: list[str]) -> list[str]:
    """Collapse spoken digit strings into numbers.

    "four eight three two" -> "4832"; "nineteen twenty eight" -> "1928". Both are how people
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
                    if nxt in _UNITS and 0 < _UNITS[nxt] < 10:
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
            # A lone number word stays a word: "three shirts", "oh, how many" — rewriting
            # those damages a correct transcript for no gain.
            out.append(tokens[i])
            i += 1
            continue
        out.append(tokens[i])
        i += 1
    return out


def extract_order_numbers(text: str) -> list[str]:
    """Order numbers as CROOKS uses them: 3–5 digits after an order-ish cue. 'order 1928',
    '#1928', 'CROOKS-1928' and 'crooks 1928' all yield '1928'. Six digits and up is a phone
    number fragment, not an order."""
    found: list[str] = []
    for match in re.finditer(r"(?<!\d)#?\s*(\d{3,5})\b(?!\s*\d)", text):
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
        """Drop the cache so the source is re-read on next use."""
        self._cached = None

    def repoint(
        self,
        terms: Iterable[str],
        aliases: Mapping[str, str] | None = None,
        personal: Iterable[str] | None = None,
    ) -> None:
        """Swap the catalogue. M7 calls this hourly with the live Shopify list.

        `personal` names the subset that must not be sent to a third-party recogniser."""
        frozen_terms = list(terms)
        frozen_aliases = dict(aliases or {})
        frozen_personal = list(personal or ())
        self._source = lambda: Catalogue(frozen_terms, frozen_aliases, frozen_personal)
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
        ambiguities: list[Ambiguity] = []

        # Score every candidate window, then take the best matches first. Scoring left to
        # right and taking the first hit lets a window absorb its neighbour — "many Blue Wash
        # Yard" scores 87 against "Blue Wash Yard Jeans", beating the threshold before the
        # correct alignment starting one word later is ever considered.
        candidates: list[tuple[float, int, int, str, str]] = []
        max_n = max(1, catalogue.max_words + MAX_WORD_COUNT_DIFF)
        for i in range(len(tokens)):
            for n in range(1, min(max_n, len(tokens) - i) + 1):
                window = tokens[i : i + n]
                if not any(w[:1].isalpha() for w in window):
                    continue
                phrase = " ".join(window)
                if len(phrase) < 3:
                    continue
                best = catalogue.best(phrase)
                if best is None:
                    continue
                term, score, via = best
                if via != "alias" and _swallows_ordinary_words(window, term):
                    # "many blue wash yard jeans" scores well against the four-word product,
                    # and replacing it would eat "many". A match may not claim an ordinary
                    # English word at its edge that the term itself does not contain.
                    continue
                candidates.append((score, n, i, term, via))

        # A window that sits entirely inside another valid window loses to it. The live
        # catalogue contributes colour options as one-word terms, and "blue" matches "Blue"
        # exactly — which used to consume the first word of "blue wash yard genes" and leave
        # the product name uncorrected. The longer catalogue entry is the more specific claim.
        spans = [(i, i + n) for _, n, i, _, _ in candidates]
        candidates = [
            c
            for c in candidates
            if not any(start <= c[2] and c[2] + c[1] <= end and end - start > c[1]
                       for start, end in spans)
        ]

        # Highest score wins; among near-perfect scores the longer span wins, so the
        # five-word "black blue motiontec socks" beats the three-word alias inside it.
        candidates.sort(key=lambda c: (-min(c[0], 95.0), -c[1], c[2]))
        chosen: dict[int, tuple[int, str]] = {}
        taken: set[int] = set()
        for score, n, i, term, via in candidates:
            span = range(i, i + n)
            if any(k in taken for k in span):
                continue
            taken.update(span)
            phrase = " ".join(tokens[i : i + n])
            if via == "ambiguous":
                # Leave the words as heard; say what they might have been.
                ambiguities.append(Ambiguity(phrase, catalogue.candidates(phrase)))
                chosen[i] = (n, phrase)
                continue
            chosen[i] = (n, term)
            if clean(term) != clean(phrase):
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
            ambiguities=ambiguities,
            order_numbers=extract_order_numbers(joined),
        )


def _detokenise(tokens: list[str]) -> str:
    out = ""
    for token in tokens:
        if not out:
            out = token
        elif token in ",.?!;:'-" or token.startswith("'"):
            out += token
        elif out.endswith(("#", "(", "-")):
            out += token
        else:
            out += " " + token
    return out


def from_file(path: Path) -> Normaliser:
    """M3's normaliser: the hand-written seed list, with aliases."""
    return Normaliser(lambda: Catalogue(*load_terminology(path)))


def from_terms(
    terms: Iterable[str],
    aliases: Mapping[str, str] | None = None,
    personal: Iterable[str] | None = None,
) -> Normaliser:
    """Test and M7 entry point: any iterable of terms."""
    frozen = list(terms)
    frozen_aliases = dict(aliases or {})
    frozen_personal = list(personal or ())
    return Normaliser(lambda: Catalogue(frozen, frozen_aliases, frozen_personal))
