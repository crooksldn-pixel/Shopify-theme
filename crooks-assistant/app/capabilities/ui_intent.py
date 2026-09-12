"""The UI-intent contract (§4): some words oblige a visible workspace, and speech is not one.

    "show me David's orders"

is not answered by saying David's orders. The owner asked to be SHOWN, and a turn that
spoke and drew nothing did not do what was asked, however true the sentence was. The live
session proves the cost three times over in one defect:

    turn_0cce1678e014  "Can you expand [name]'s customer page?"  → a capability card
    turn_ddb733d15472  "Expand [name]'s customer page"           → nothing at all
    turn_9d59579ab03e  "No, bring up a UI for the customer's page" → nothing at all

The first drew a card, and the report scored it drawn. It was the wrong surface: a list of
what the product can do, in answer to a request for one customer's page. So "a card was
drawn" is not the contract either. The contract is:

    a §4 demand word obliges a surface OF THE KIND THE WORDS ASKED FOR,
    and a turn that does not draw one has NOT succeeded.

This module is that contract, and nothing else. It is pure — no families, no registration, no
reads — so the analyser and the report can import it without pulling the family stack in
behind them, and so the router and the report cannot disagree about what a demand is: both
read `app.capabilities.ask.DEMANDS`.

`UI_INTENT_UNFULFILLED` is the class the analyser files. This module names it, says what
severity it carries and which component owns it; `app/observability/visible.py` registers it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.capabilities import ask

# ------------------------------------------------------------------- the failure class

# The words demanded a surface and none of the right kind was drawn. Named here, beside the
# contract that decides it, so the analyser files exactly what this module found.
UI_INTENT_UNFULFILLED = "UI_INTENT_UNFULFILLED"
# At or above `visible.FAILS_THE_TURN` (5): the owner asked to be shown something and was not
# shown it. There is nothing partial about that — he said it three times.
SEVERITY = 5
COMPONENT = (
    "the UI-intent layer (app/capabilities/ui_intent.py, app/families/ui_intent.py): a "
    "show/open/pull-up/expand request routes to a workspace family, and the turn fails when "
    "no surface of the asked-for kind was drawn"
)
TASK = (
    "the words obliged a workspace. Route the request to the family that draws one and assert "
    "the SURFACE, never the sentence: speech alone is not success."
)
VISIBLE_WORD = "NOTHING_DRAWN"

# What a turn is, once this contract has been applied to it.
SUCCESSFUL = "successful"
UNSUCCESSFUL = "unsuccessful"


# ------------------------------------------------------------------------- the subjects

# What the demand was about, and which surfaces are an answer to it. Bounded on purpose: a
# subject this table does not know is served by any real workspace (ANY, below), and a
# capability card serves nothing but a question about the assistant.
CUSTOMER = "customer"
ORDER = "order"
EMAIL = "email"
SALES = "sales"
PRODUCTS = "products"
SCREEN = "screen"
ASSISTANT = "assistant"
UNKNOWN = ""

# The surfaces that ANSWER each subject.
#
# BOTH vocabularies, and this is not laziness. A card on the wire carries `surface` (what the
# interface is FOR — app/surfaces.py SURFACE_TYPES) and `type` (which component draws it —
# app/presentation.py UI_TYPES), and a card built before the envelope existed carries only the
# second. The read layer's analytic cards are `metric_group`, `ranking`, `table`; the same
# figures under an envelope are `analytics`. A contract that knew only one of the two would
# call a drawn card undrawn, which is the mistake this module exists to stop making in the
# other direction.
#
# AND the composed surfaces, which is the mistake above happening a third time and being
# caught by this table's own tests. `customer_workspace` and `order_workspace` (§3) and
# `summary_list` (§13) did not exist when this was written, so "expand David Randall's
# customer page" drew `['customer_workspace']` — the richest possible answer to it — and the
# contract called the turn UNSUCCESSFUL because the word `customer` was not among the types.
# A composed workspace about a record is MORE of an answer than the card it replaced, and a
# compact summary is the answer to a summary question rather than a smaller version of the
# wrong one. Both belong in every subject they can be about.
SATISFIES: dict[str, frozenset[str]] = {
    CUSTOMER: frozenset({"customer", "customer_list", "order_list", "order", "order_detail",
                         "email_list", "email_thread", "work_queue", "working_set", "workspace",
                         "customer_workspace", "order_workspace", "summary_list"}),
    ORDER: frozenset({"order_detail", "order", "order_list", "work_queue", "working_set",
                      "email_thread", "workspace", "variant_picker",
                      "order_workspace", "customer_workspace", "summary_list"}),
    EMAIL: frozenset({"email_list", "email_thread", "email_queue", "email_draft",
                      "email_compose", "reply_state", "work_queue", "working_set",
                      # A customer workspace carries his inbox as one of its sections, which
                      # is what "is he in Gmail anywhere" asked for and did not get.
                      "customer_workspace", "summary_list"}),
    SALES: frozenset({"analytics", "metric_group", "ranking", "table", "comparison", "trend",
                      "sales_summary", "order_list", "work_queue", "working_set", "summary_list"}),
    PRODUCTS: frozenset({"product", "inventory", "analytics", "ranking", "table",
                         "variant_matrix", "order_list", "working_set", "summary_list"}),
    SCREEN: frozenset({"capability", "context", "assistant"}),
    ASSISTANT: frozenset({"capability", "assistant", "context"}),
}
# A demand whose subject this table cannot name is met by any surface that shows the shop or
# the inbox. Deliberately excludes `capability` — that is the D-5 defect itself — and the
# surfaces that report on the turn rather than on the work.
NEVER_A_WORKSPACE = frozenset({
    "capability", "error", "confirmation", "assistant", "success",
    # The context stack is bookkeeping the tablet keeps for itself. A turn whose entire
    # visible output is the context stack has shown the owner nothing he asked for — which is
    # `experience/harness.py`'s own rule (BOOKKEEPING), said here too.
    "context_stack", "context",
})

# Which words say what the demand is about. Read in this order; the first that matches wins,
# because "his customer page" is about the customer whatever else the sentence carries.
_SUBJECT_WORDS: tuple[tuple[str, frozenset[str]], ...] = (
    (SCREEN, frozenset({"screen", "glass", "tablet", "display"})),
    (CUSTOMER, frozenset({"customer", "customers", "buyer", "buyers", "client", "clients",
                          "profile", "account"})),
    (EMAIL, frozenset({"email", "emails", "inbox", "mail", "thread", "threads", "message",
                       "messages", "correspondence", "unread"})),
    (SALES, frozenset({"sales", "revenue", "takings", "turnover", "numbers", "aov"})),
    (PRODUCTS, frozenset({"product", "products", "stock", "inventory", "sizes", "range"})),
    (ORDER, frozenset({"order", "orders", "invoice", "purchase", "purchases"})),
)


@dataclass(frozen=True, slots=True)
class Demand:
    """One request's claim on the screen: the words that made it, and what it was about."""

    phrase: tuple[str, ...]
    subject: str = UNKNOWN

    @property
    def words(self) -> str:
        return " ".join(self.phrase)

    @property
    def acceptable(self) -> frozenset[str]:
        """The surfaces that answer this demand. Both vocabularies; see SATISFIES."""
        from app.presentation import UI_TYPES
        from app.surfaces import SURFACE_TYPES

        named = SATISFIES.get(self.subject)
        if named is not None:
            return named
        return (frozenset(SURFACE_TYPES) | frozenset(UI_TYPES)) - NEVER_A_WORKSPACE

    def as_dict(self) -> dict[str, Any]:
        return {"phrase": self.words, "subject": self.subject or None,
                "acceptable": sorted(self.acceptable)}


def _tokens(text: str) -> tuple[str, ...]:
    from app.fastpath.intent import _tokens as tokenise

    return tokenise((text or "").lower())


def subject_of(words: tuple[str, ...], *, said: str = "") -> str:
    """What the demand was about, from the words after it (and the whole sentence if the
    demand phrase came last, which is how "pull that up" is said).

    A PERSON pointed at wins over the query noun, and that ordering is the point: "show me his
    orders" is answered by his workspace with its Orders tab open, and calling it an ORDER
    demand would have said a customer card did not answer it. "Show me today's orders" points
    at no person and stays a list of orders.
    """
    index = ask.demand_at(words)
    tail = set(words[index:]) if index >= 0 else set(words)
    if ask.about_the_assistant(words):
        return ASSISTANT
    if (tail & ask.PERSON_PRONOUNS) or ask.person_named(said or " ".join(words)):
        return CUSTOMER
    for subject, vocabulary in _SUBJECT_WORDS:
        if tail & vocabulary:
            return subject
    return UNKNOWN


def demand(text: str) -> Demand | None:
    """The claim this request makes on the screen, or None when it makes none.

    Deterministic, and the same list §5's discrimination reads: a sentence that obliges a
    surface is by that fact not a question about the assistant, and one rule cannot hold
    without the other.
    """
    words = _tokens(text)
    phrase = ask.demand_phrase(words)
    if not phrase:
        return None
    return Demand(phrase=phrase, subject=subject_of(words, said=str(text or "")))


def surface_types(ui: Any) -> list[str]:
    """The surface types actually drawn, from the wire items the tablet was sent.

    Reads the envelope's `surface` first (app/surfaces.py) and falls back to `type`, which is
    what a card built before the envelope existed carries. A card with neither is not a
    surface and does not count.
    """
    out: list[str] = []
    for item in list(ui or []):
        if not isinstance(item, dict):
            continue
        named = str(item.get("surface") or "").strip()
        if not named:
            named = str(item.get("type") or "").strip()
        if named:
            out.append(named)
    return out


def satisfied(claim: Demand | None, ui: Any) -> bool:
    """Whether what was drawn answers what was demanded.

    Two things this deliberately does NOT accept, because the live session produced both:

    * an empty deck. Speech is not a surface; "show me" is not met by saying it.
    * a capability card for a request about a record. That is D-5 exactly — one card, 1,014
      pixels, and not one fact about the customer he named.
    """
    if claim is None:
        return True
    drawn = surface_types(ui)
    if not drawn:
        return False
    return any(kind in claim.acceptable for kind in drawn)


def unfulfilled(question: str, ui: Any) -> str:
    """The class this turn earns, or "". `UI_INTENT_UNFULFILLED` when the words obliged a
    surface and none of the asked-for kind was drawn."""
    claim = demand(question)
    if claim is None or satisfied(claim, ui):
        return ""
    return UI_INTENT_UNFULFILLED


def turn_outcome(question: str, ui: Any, *, spoken: str = "") -> str:
    """`UNSUCCESSFUL` when the contract was not met, whatever was said.

    `spoken` is accepted and ignored on purpose, and the signature says so: the whole point of
    §4 is that the sentence cannot settle this. A caller that passes a perfect answer with an
    empty deck still gets UNSUCCESSFUL.
    """
    return UNSUCCESSFUL if unfulfilled(question, ui) else SUCCESSFUL


def why(question: str, ui: Any) -> str:
    """One clause for the timeline, in the owner's terms. Empty when the contract was met."""
    claim = demand(question)
    if claim is None or satisfied(claim, ui):
        return ""
    drawn = surface_types(ui)
    asked = claim.subject or "a workspace"
    if not drawn:
        return f"“{claim.words}” asked for {asked} on the screen and nothing was drawn"
    return f"“{claim.words}” asked for {asked} on the screen and what was drawn was {', '.join(sorted(set(drawn)))}"
