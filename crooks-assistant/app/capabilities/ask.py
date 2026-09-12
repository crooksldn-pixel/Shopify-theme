"""What a request is actually asking FOR, when it opens with "can you" (§5, D-5).

The live session's turn `turn_0cce1678e014` said

    "Can you expand [name]'s customer page?"

and was answered with a thousand-pixel list of everything the product can do. The router had
one rule for the whole shape: `meta_self` — "you" beside a word of ability — and "can you" is
both. So every request that was politely phrased was read as a question about the assistant.

These are three different things and the words they share cannot tell them apart:

    "Can you access customer records?"      a question about the assistant
    "Can you open David's customer record?" an instruction to move the screen
    "Can you show today's orders?"          a piece of work

What tells them apart is never the opener. It is **what follows it** — the operation, the
entity, the task — and that is what this module reads. The rule, in one line:

    "can you" NEVER by itself means a capability question. The operation, the entity or the
    task that follows dominates it.

So a sentence is a capability question only when it names NOTHING to do it to: no record, no
period, no person, no pointer at the screen, and no word that demands a surface. Name any of
those and the sentence is navigation, work, or a change — whatever its opener.

Read by `app/fastpath/intent.py` (as the `capability_question` signal, which the
`capability_summary` family now requires) and by the tests that hold the six cases §5 names.
Nothing here touches the shop, the inbox, or the model: it is a reading of the words.
"""

from __future__ import annotations

import re
from typing import Any

# What a request turned out to be. Four kinds, and the order in which they beat each other:
# a demand for a surface beats a change beats a named target beats a question about the
# assistant. Empty means this module has nothing to say about the sentence.
CAPABILITY = "capability"      # a question about what the assistant can do
NAVIGATION = "navigation"      # move the screen to a record or a place
TASK = "task"                  # read something out of the shop or the inbox
ACTION = "action"              # change something
KINDS = (CAPABILITY, NAVIGATION, TASK, ACTION)

# §4's vocabulary: the words that REQUIRE a visible workspace. Held here, as token sequences,
# because the same list decides two things — whether a sentence is a capability question
# (it is not, if it demands a surface) and whether a turn met its contract
# (app/capabilities/ui_intent.py). One list, so the two cannot disagree.
DEMANDS: tuple[tuple[str, ...], ...] = (
    ("show", "me"),
    ("show",),
    ("open",),
    ("pull", "up"),
    ("bring", "up"),
    ("expand",),
    ("take", "me", "to"),
    ("go", "to"),
    ("view",),
)

# The demand phrases that are a MOVE and nothing else — no reading of the shop is implied by
# the words themselves. Kept apart because the landings already own "open orders" and
# "show me sales", and a second family on those sentences would land inside the router's
# margin and route nothing at all.
GOES_TO: tuple[tuple[str, ...], ...] = (("take", "me", "to"), ("go", "to"))

# The nouns that name a PAGE rather than a question: a record, a profile, a screen. "Expand
# his customer page" names one of these; "show me his orders" does not.
PAGE_WORDS = frozenset({
    "page", "pages", "record", "records", "profile", "screen", "card", "workspace",
    "account", "ui", "detail", "details", "view",
})

# The pronouns that stand for a PERSON. "His", "her", "their" point at the customer in front
# of the owner; "it" and "that" point at whatever the last card was, which is not the same.
PERSON_PRONOUNS = frozenset({"his", "her", "hers", "him", "she", "he", "their", "theirs", "them", "they"})

# The nouns that make a sentence a QUERY about a person rather than a request for their page:
# their orders, their emails, their history. The word decides which part of the workspace
# opens; it does not decide whether one opens.
QUERY_NOUNS = frozenset({
    "orders", "order", "emails", "email", "inbox", "history", "spend", "spent", "sales",
    "stock", "inventory", "returns", "refunds", "threads", "messages", "correspondence",
})


def phrase_at(words: tuple[str, ...], index: int, phrase: tuple[str, ...]) -> bool:
    return words[index:index + len(phrase)] == phrase


def demand_at(words: tuple[str, ...], phrases: tuple[tuple[str, ...], ...] = DEMANDS) -> int:
    """Where the demand phrase starts, or -1. The LONGEST phrase at the earliest position
    wins, so "show me" is read as one demand rather than "show" with "me" left over."""
    ordered = sorted(phrases, key=len, reverse=True)
    for index in range(len(words)):
        for phrase in ordered:
            if phrase_at(words, index, phrase):
                return index
    return -1


def demand_phrase(words: tuple[str, ...]) -> tuple[str, ...]:
    """The §4 phrase this sentence used, or (). The words that oblige a surface."""
    ordered = sorted(DEMANDS, key=len, reverse=True)
    for index in range(len(words)):
        for phrase in ordered:
            if phrase_at(words, index, phrase):
                return phrase
    return ()


def goes_to(words: tuple[str, ...]) -> bool:
    """"Take me to …" / "go to …" — a move, with no reading of the shop in the words."""
    return demand_at(words, GOES_TO) >= 0


def _object_of(words: tuple[str, ...]) -> tuple[str, ...]:
    """What the demand was made OF: the words after the demand phrase."""
    index = demand_at(words)
    if index < 0:
        return words
    phrase = demand_phrase(words)
    return words[index + len(phrase):]


def about_the_assistant(words: tuple[str, ...]) -> bool:
    """Whether the demand's OBJECT is the assistant itself.

    "Show me what you can do" demands a surface AND is a capability question; the two are not
    exclusive, and the object is what says so. "Show me today's orders" carries the same "can
    you" and its object is the shop's.
    """
    tail = set(_object_of(words))
    return bool(tail & {"you", "your", "yourself", "capabilities", "capability", "abilities"})


def names_a_target(sig: Any) -> bool:
    """Whether the sentence names something specific to do it to.

    A capability question names nothing: "can you access refunds" has no record, no person, no
    day and nothing on screen in it. Every one of these is a target, and any one of them means
    the sentence is about the shop rather than about the assistant.
    """
    return bool(
        getattr(sig, "order_numbers", ())
        or getattr(sig, "known_name", "")
        or getattr(sig, "possessive_name", False)
        or getattr(sig, "deixis", False)
        or getattr(sig, "period", False)
        or getattr(sig, "ranking", False)
        or getattr(sig, "status", False)
        or getattr(sig, "address", False)
        or getattr(sig, "bought", False)
        or getattr(sig, "delayed", False)
        or getattr(sig, "unfulfilled", False)
        or getattr(sig, "waiting", False)
        or getattr(sig, "has_address", False)
    )


def _names_a_page(words: tuple[str, ...]) -> bool:
    """Whether the demand's object is a page rather than a question about one."""
    tail = set(_object_of(words))
    if tail & PAGE_WORDS:
        return True
    # A bare name or pronoun with no query noun after it: "open David Harding", "take me to
    # her". The object names a record, and a record opens.
    return not (tail & QUERY_NOUNS)


def classify(sig: Any) -> str:
    """What this request is, from the signals already extracted. One of KINDS, or "".

    The order is the whole rule and it is not a preference:

        a demand for a surface   →  NAVIGATION or TASK, never CAPABILITY
        a change verb            →  ACTION
        a named target           →  TASK
        "you" and a word of ability, with nothing named  →  CAPABILITY
    """
    words = tuple(getattr(sig, "words", ()) or ())
    if not words:
        return ""
    if demand_phrase(words) and not about_the_assistant(words):
        return NAVIGATION if _names_a_page(words) else TASK
    if getattr(sig, "mutation", False):
        return ACTION
    if names_a_target(sig):
        return TASK
    if getattr(sig, "meta_self", False):
        return CAPABILITY
    return ""


def is_a_capability_question(sig: Any) -> bool:
    """The signal `capability_summary` requires. True only when the sentence names nothing to
    do, which is the whole of §5."""
    return classify(sig) == CAPABILITY


def classify_text(text: str, *, branch: Any = None) -> str:
    """The same reading, from the words. For callers that hold no Signals — the report, and
    the tests that state the six cases in the owner's own sentences."""
    from app.fastpath.intent import signals_for

    return classify(signals_for(text or "", branch=branch))


# ------------------------------------------------------------ the person the words named
#
# D-14, and the gravest thing in the live session: the owner asked what ONE customer had
# ordered in his lifetime and was told, as a statement of fact, a DIFFERENT customer's order
# history. The recipe read the order already in focus and then read that order's customer.
# A minute later the same question, phrased with a name the branch had by then resolved, was
# answered correctly.
#
# The rule that was missing: **a person named in the request outranks the record in focus,
# always.** Focus resolution is for "him", "that one", "the same customer" — never for a
# sentence that says who it is about.
#
# So this has to find a name in a sentence the branch has never heard the name in. Two ways,
# and either is enough, because the cost of finding one that is not there is a model call and
# the cost of missing one is a false fact spoken aloud:
#
#   1. CAPITALISATION. A capitalised token the router has no meaning for, not at the head of
#      the sentence (or at the head with another beside it) — "David Randall", as the
#      recogniser transcribes it.
#   2. AN UNKNOWN WORD. A token in none of the router's closed sets and none of the ordinary
#      words below. This is what catches an all-lowercase transcript.

# The ordinary words a request is made of that carry no signal and are not names. Bounded, and
# every one of them measured against the sentences the live session actually contained: without
# "lifetime" the question that exposed D-14 finds "lifetime" and calls it a person.
FILLER = frozenset({
    "a", "an", "the", "of", "in", "on", "at", "to", "for", "from", "with", "by", "about",
    "into", "over", "up", "down", "out", "off", "as", "so", "than", "that", "this", "these",
    "those", "there", "here", "it", "its", "im", "am", "be", "been", "being", "please",
    "just", "still", "yet", "very", "really", "quite", "bit", "lot", "lots", "some", "no",
    "not", "nope", "yes", "yeah", "yep", "okay", "ok", "right", "well", "now", "again",
    "ever", "never", "always", "total", "totals", "altogether", "overall", "lifetime",
    "lifetimes", "time", "times", "thing", "things", "one", "ones", "two", "three", "us",
    "we", "our", "ours", "me", "my", "mine", "i", "he", "she", "his", "her", "hers", "him",
    "them", "they", "their", "theirs", "you", "your", "yours", "who", "whos", "whose",
    "uh", "um", "er", "erm", "like", "mean", "meant", "means", "sorry", "actually",
    "can", "could", "would", "will", "shall", "should", "may", "might", "must", "do", "does",
    "did", "done", "has", "have", "had", "is", "are", "was", "were", "am", "get", "got",
    "let", "lets", "say", "said", "says", "tell", "told", "want", "wants", "wanted", "need",
    "needs", "needed", "much", "many", "more", "most", "less", "least", "all", "any", "each",
    "every", "both", "either", "neither", "other", "another", "same", "next", "last", "first",
    "second", "back", "and", "or", "but", "if", "when", "where", "why", "how", "what", "whats",
    "which", "while", "because", "then", "also", "too", "only", "even", "already", "else",
    # The verbs a request is made with. Every one of them was read as a customer's name by the
    # unknown-word rule before it was written down here: "can you ACCESS refunds" named a
    # person called Access.
    "access", "accessing", "handle", "handling", "manage", "managing", "support", "supports",
    "deal", "dealing", "reach", "use", "using", "used", "run", "running", "ran", "work",
    "works", "working", "worked", "help", "helps", "bring", "brings", "take", "takes", "go",
    "goes", "going", "come", "comes", "expand", "expanding", "pull", "pulls", "pulling",
    "view", "viewing", "display", "displaying", "know", "knows", "knew", "think", "thinks",
    "hear", "heard", "speak", "speaking", "talk", "talking", "stop", "stops", "stopping",
    "wait", "waiting", "start", "starts", "starting", "try", "trying", "keep", "keeping",
})

_CAPITALISED = re.compile(r"\b([A-Z][a-z]{1,20})\b")
_SENTENCE_START = re.compile(r"(?:^|[.!?]\s+)([A-Z][a-z]{1,20})\b")


def _known(word: str) -> bool:
    """Whether the router already has a meaning for this word."""
    from app.fastpath.intent import VOCABULARY

    lowered = word.lower()
    return lowered in VOCABULARY or lowered in FILLER or lowered in PAGE_WORDS or lowered in QUERY_NOUNS


def person_named(text: str) -> str:
    """The person this request names, as the owner said it — or "" when it names none.

    Capitalisation first, because a recogniser gives names capitals and that is the strongest
    evidence available without asking the shop. Then the unknown-word run, which holds for a
    transcript that arrived in lower case.
    """
    said = " ".join(str(text or "").split())
    if not said:
        return ""
    heads = {m.group(1) for m in _SENTENCE_START.finditer(said)}
    run: list[str] = []
    best: list[str] = []
    for match in _CAPITALISED.finditer(said):
        word = match.group(1)
        if _known(word) or (word in heads and not run):
            # A capitalised word the router knows is not a name; one at the head of a sentence
            # is only a name when another follows it into the same run.
            if len(run) > len(best):
                best = run
            run = []
            continue
        run.append(word)
    if len(run) > len(best):
        best = run
    if best:
        return " ".join(best)
    return _unknown_run(said.lower())


# The words that introduce the person a sentence is about. A single unknown word is only a
# name when it sits in a noun slot: "what has DAVID ordered" does, "can you ACCESS refunds"
# does not, and without this distinction every verb the router has no meaning for is read as a
# customer. Two or more unknown words in a row need no introducer — that is a first and last
# name, and nothing else in English looks like it.
_INTRODUCES = frozenset({
    "has", "had", "have", "did", "does", "is", "was", "for", "about", "from", "to", "of",
    "on", "by", "with", "and", "or", "the",
})


def _unknown_run(lowered: str) -> str:
    """The longest run of words the router has no meaning for, when it looks like a name."""
    from app.fastpath.intent import _tokens

    words = _tokens(lowered)
    best = ""
    index = 0
    while index < len(words):
        if words[index].isdigit() or _known(words[index]):
            index += 1
            continue
        start = index
        while index < len(words) and not (words[index].isdigit() or _known(words[index])):
            index += 1
        run = words[start:index]
        if len(run) == 1 and not (start > 0 and words[start - 1] in _INTRODUCES):
            continue
        if len(" ".join(run)) > len(best):
            best = " ".join(run)
    return best


def names_a_person(sig: Any) -> bool:
    """The signal a family blocks on: this sentence says WHO it is about.

    True for a name the branch has resolved, for a possessive ("David's"), and for a name the
    branch has never seen. The last is the one that matters: with it, the family that answers
    from the record in focus can no longer take a sentence that named somebody else.
    """
    if getattr(sig, "known_name", "") or getattr(sig, "possessive_name", False):
        return True
    said = str(getattr(sig, "raw", "") or "") or " ".join(getattr(sig, "words", ()) or ())
    return bool(person_named(said))
