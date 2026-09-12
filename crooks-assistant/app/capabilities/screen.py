"""What is actually on the glass (D-11, §23).

The verified exchange, from the raw timeline:

    23:07:41  RENDER []  mode=orb          the deck is EMPTY; chrome only
    23:08:27  HE SAID:   "What is it? … why is there bullshit on the screen right now?"
    23:08:30  IT SAID:   "Nothing's come from me — I haven't run anything yet, no card's up
                          on my end."
    23:08:56  HE SAID:   "What is, what is it doing? Oh"
    23:08:58  IT SAID:   "Nothing running here, nothing pending on a card."

Both answers are true and both are useless. There genuinely were no CARDS. But the orb was
divided, and what he was looking at was an orb, a dock, two half chips he could not press and
a hold-to-speak label over all of it. He tapped the screen 33 times in the next 90 seconds.

The assistant could enumerate the cards it had sent. It could not see the interface it was
sitting in, so when the owner asked about the screen it answered about its own outbox.

This module is the missing model, and it is built the only honest way: from the state the Mac
already holds, against the FIXED first-party chrome. The tablet reports nothing here and is
asked nothing — the orb, the dock, the half chips and the trail controls are this product's
own furniture, and whether each is on the glass follows from the session:

    the orb       always
    the dock      always, one landing per area the dock offers
    half chips    while the conversation is divided
    Back / Home   while this half has a trail to move along
    the deck      the cards this half last had drawn, which may be none

The rule this exists to hold, which is §19 pointed the other way: **"nothing is on screen"
must be TRUE before it is said.** §19 says do not claim you did something you did not do;
this says do not claim there is nothing there while he is looking at it.

Read-only and derived. Nothing here draws anything, and nothing here can.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# The two things the glass can be doing. `deck` when this half has cards on it; `orb` when it
# has none — which is NOT the same as an empty screen, and is exactly the distinction the live
# session's two answers missed.
DECK = "deck"
ORB = "orb"

# A half that is on the glass. MERGED and CANCELLED halves are gone and draw no chip.
LIVE = ("ACTIVE", "BACKGROUND")


@dataclass(frozen=True, slots=True)
class Chrome:
    """One piece of the fixed furniture, and what the owner can do with it."""

    key: str
    name: str
    what: str
    does: str = ""


@dataclass(frozen=True, slots=True)
class Screen:
    """The glass, as the Mac can honestly account for it."""

    mode: str = ORB
    cards: tuple[str, ...] = ()
    divided: bool = False
    halves: tuple[str, ...] = ()
    listening: str = ""
    dock: tuple[str, ...] = ()
    trail: int = 0
    headline: str = ""

    @property
    def empty(self) -> bool:
        """Whether the DECK is empty. Never whether the SCREEN is: see `furniture`."""
        return not self.cards

    @property
    def furniture(self) -> tuple[Chrome, ...]:
        """Everything on the glass that is not a card. Never empty — the orb and the dock are
        always there, which is why "nothing is on the screen" is never a true sentence."""
        out = [
            Chrome("orb", "the orb", "the round target in the middle",
                   "hold the orb and speak"),
            Chrome("dock", "the dock",
                   "the strip of landings down the edge — " + _listed(self.dock),
                   "tap a landing to start somewhere"),
        ]
        if self.divided:
            out.append(Chrome(
                "halves", f"{_count(len(self.halves))} half chips",
                "one per half of the divided conversation — " + _listed(self.halves),
                "tap a half to talk to it, or say merge to put them back together",
            ))
        if self.trail > 0:
            out.append(Chrome("trail", "Back and Home",
                              "at the top left, because this half has somewhere to go back to",
                              "say go back, or go home"))
        if self.listening:
            out.append(Chrome("listening", "the listening label",
                              f"the screen is waiting for words about {self.listening}",
                              "say the sentence, or say stop"))
        return tuple(out)

    def as_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode, "cards": list(self.cards), "divided": self.divided,
            "halves": list(self.halves), "listening": self.listening or None,
            "dock": list(self.dock), "trail": self.trail,
            "chrome": [c.key for c in self.furniture],
        }


def _listed(items: tuple[str, ...] | list[str]) -> str:
    names = [str(i) for i in items if str(i or "").strip()]
    if not names:
        return "nothing"
    if len(names) == 1:
        return names[0]
    return ", ".join(names[:-1]) + " and " + names[-1]


def _count(n: int) -> str:
    return {0: "no", 1: "one", 2: "two", 3: "three", 4: "four"}.get(n, str(n))


def _dock_areas() -> tuple[str, ...]:
    """The dock's landings, from the families that implement them — never a copy."""
    try:
        from app.families.landings import AREA_LABELS, AREAS

        return tuple(AREA_LABELS.get(a, a) for a in sorted(AREAS))
    except Exception:  # noqa: BLE001 — the model still reads without the family modules
        return ("Inbox", "Orders", "Products", "Sales")


def state(session: Any = None, branch: Any = None) -> Screen:
    """The glass as it stands, from the session and the half being talked to.

    Every value is read, never assumed. With no session at all the answer is still honest:
    the orb and the dock are there, and nothing is claimed about a deck nobody can see.
    """
    halves: list[Any] = []
    if session is not None:
        halves = [b for b in (getattr(session, "branches", {}) or {}).values()
                  if str(getattr(b, "status", "")) in LIVE]
    here = branch if branch is not None else (halves[0] if halves else None)
    cards = tuple(
        str(item.get("type") or "")
        for item in (getattr(here, "last_ui", None) or [])
        if isinstance(item, dict) and item.get("type")
    )
    listening = ""
    if here is not None and hasattr(here, "voice_target"):
        target = here.voice_target()
        if target:
            listening = str(target.get("label") or target.get("prompt") or "the last thing you tapped")
    return Screen(
        mode=DECK if cards else ORB,
        cards=cards,
        divided=len(halves) > 1,
        halves=_half_names(halves),
        listening=listening,
        dock=_dock_areas(),
        trail=max(0, int(getattr(here, "nav_index", -1) or -1)),
        headline=str((here.headline() or {}).get("title") or "") if here is not None and hasattr(here, "headline") else "",
    )


def _half_names(halves: list[Any]) -> tuple[str, ...]:
    """One name per half, and never two of the same.

    "Never two indistinguishable halves" is `Branch.headline`'s own rule, but two halves that
    hold nothing yet give the same headline honestly — and naming them both "EMPTY · nothing
    yet" is exactly the screen the owner could not read. Where they collide, the half's own
    label breaks the tie.
    """
    names = [_half_name(b) for b in halves]
    if len(set(names)) == len(names):
        return tuple(names)
    out: list[str] = []
    for index, (branch, name) in enumerate(zip(halves, names, strict=False)):
        label = str(getattr(branch, "label", "") or "").strip() or f"half {index + 1}"
        out.append(f"{label} ({name})" if name else label)
    return tuple(out)


def _half_name(branch: Any) -> str:
    if hasattr(branch, "headline"):
        try:
            return str((branch.headline() or {}).get("title") or "")
        except Exception:  # noqa: BLE001 — a half that cannot name itself is still a half
            pass
    return str(getattr(branch, "label", "") or "a half")


# --------------------------------------------------------------------------- in words


def words(screen: Screen) -> str:
    """What is on the screen, said so that the owner can act on it.

    Three parts, in the order that answers the question he actually asked: what the deck is
    showing, what the furniture is, and what he can do from here. The deck comes first
    because it is what changes; the furniture is said WHENEVER the deck is empty, because
    that is the case where the old answer said "nothing" and was wrong.
    """
    parts: list[str] = []
    if screen.cards:
        parts.append(f"On the deck: {_listed(_readable(screen.cards))}.")
        if screen.headline:
            parts.append(f"This half is {screen.headline}.")
    else:
        # Deliberately not "nothing is on the screen", and deliberately not "no card's up":
        # both were said in the live session and both were false. The deck having nothing on
        # it is a fact about the deck, and the sentence says which.
        parts.append("Nothing has been drawn on the deck. What you are looking at is the "
                     "screen itself, which is always there:")
    furniture = screen.furniture
    if not screen.cards or screen.divided or screen.listening:
        head = "" if not screen.cards else "Also on the glass: "
        parts.append(head + "; ".join(f"{c.name} — {c.what}" for c in furniture) + ".")
    if screen.divided:
        parts.append("The conversation is divided, so each half has its own record and its own trail.")
    parts.append("From here you can " + _listed(tuple(c.does for c in furniture if c.does)) + ".")
    return " ".join(p for p in parts if p)


# The card types as a person would name them. A type the map does not know is said as it is,
# with its underscores taken out — never invented, and never dropped silently.
_CARD_WORDS = {
    "order": "an order", "order_list": "a list of orders", "customer": "a customer",
    "customer_list": "a list of customers", "email_list": "the inbox", "email_thread": "an email thread",
    "email_compose": "an email being written", "metric_group": "the numbers", "ranking": "a ranking",
    "table": "a table", "comparison": "a comparison", "working_set": "a set to walk",
    "capability": "what I can do", "attention": "what needs attention", "error": "an error",
    "workspace": "something being built", "batch_action": "a bulk change waiting",
    "inventory": "stock", "product": "a product", "reply_state": "who is waiting on a reply",
    "variant_picker": "which variant you mean", "folded": "a folded section",
}


def _readable(cards: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(_CARD_WORDS.get(c, c.replace("_", " ")) for c in cards)


def claims_an_empty_screen(answer: str) -> bool:
    """Whether a sentence tells the owner there is nothing on his screen.

    The check the live session needed and did not have. Used by the test that holds D-11: with
    an empty deck and a divided orb, an answer that says any of these is FALSE, because the
    orb, the dock and two half chips were all on the glass.
    """
    said = " ".join(str(answer or "").lower().split())
    return any(phrase in said for phrase in (
        "no card's up", "no cards up", "no card is up", "nothing on the screen",
        "nothing on screen", "nothing is on the screen", "nothing's on the screen",
        "the screen is empty", "screen's empty", "nothing to see", "nothing there",
        "nothing pending on a card", "nothing's come from me", "nothing has come from me",
        "nothing running here",
    ))
