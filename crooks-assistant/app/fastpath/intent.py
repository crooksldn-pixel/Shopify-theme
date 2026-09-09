"""What was asked, as structure.

Not a phrase table. The resolver extracts SIGNALS from the request and from the branch state
— a mutation verb, an order number, a direction, a period, a metric, a meta-question, a name
the branch has already resolved, a working set under a cursor — and each intent family
declares which signals it requires, which it forbids, and what it needs to resolve before it
can act. A family wins only when it beats the runner-up by a margin and clears a floor.

The point of the structure is that "go on then" and "next one" and "and the one after that"
all reduce to the same signal (DIRECTION_NEXT) without any of them being written down as a
sentence, and that "cancel the next one" reduces to a mutation and never reaches the lane at
all.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

# ------------------------------------------------------------------ signals

# A verb that changes something. Any of these and the request leaves the fast lane: the fast
# lane cannot write, and a request it cannot serve must not be scored as if it could.
# A verb that changes something. Split in two, because English does not agree with itself:
#
#   STRONG   only ever an instruction. "Cancel", "refund", "archive".
#   SOFT     an instruction at the head of one, a noun or a description anywhere else.
#            "Email" in "email them" is a change; in "any email from her?" it is the inbox.
#            "Replying" in "who needs replying to" describes a state, not an order given.
#
# A SOFT verb counts as a mutation only when the request is NOT opened as a question. The
# cost of being wrong in the cautious direction is one model call; the cost of being wrong in
# the other direction is the fast lane trying to serve a change, which it cannot do.
MUTATION_STRONG = frozenset({
    "cancel", "cancelled", "refund", "refunded", "delete", "archive", "unarchive", "fulfil",
    "fulfill", "fulfilled", "dispatch", "restock", "untag", "revoke", "amend", "replace",
    "resend", "forward", "edit", "editing",
})
MUTATION_SOFT = frozenset({
    "add", "adding", "remove", "removing", "send", "sending", "sent", "reply", "replying",
    "draft", "drafting", "write", "writing", "email", "emailing", "note", "tag", "tagging",
    "mark", "marking", "set", "setting", "put", "make", "create", "creating", "change",
    "changing", "update", "updating", "ship", "shipping", "adjust", "adjusting", "apply",
    "move", "moving",
})
MUTATION = MUTATION_STRONG | MUTATION_SOFT
# A request that opens with one of these is asking, whatever verbs come later in it.
_OPENERS = frozenset({
    "what", "whats", "which", "who", "whose", "how", "when", "where", "why", "is", "are",
    "was", "were", "do", "does", "did", "has", "have", "had", "any", "anyone", "anybody",
    "show", "list", "tell", "give", "find", "check", "read", "look", "whos",
})


def mutating(words: tuple[str, ...]) -> bool:
    """Whether this request asks for a change."""
    have = set(words)
    if have & MUTATION_STRONG:
        return True
    if not (have & MUTATION_SOFT):
        return False
    return not (words and words[0] in _OPENERS)


# Verbs that only ever ask. Present with a mutation verb, the mutation still wins.
_QUESTION = frozenset({"what", "which", "who", "how", "when", "where", "show", "tell", "list", "find", "check", "look", "read", "give"})

_WORD = re.compile(r"[a-z0-9£$%'#]+")

# Direction: moving through a set that is already open.
_NEXT = frozenset({"next", "onwards", "forward", "another", "following"})
_PREV = frozenset({"previous", "prior", "before", "last"})
_BACK = frozenset({"back", "return"})
_HOME = frozenset({"home", "start", "top", "beginning"})

# Meta: questions about the assistant rather than the shop.
_SELF = frozenset({"you", "your", "yourself"})
# A question about what it CAN do. "You" alone is not one: "what did you do" and "what have
# you done" are questions about the last turn, and were being answered with a capability
# blurb.
_ABLE = frozenset({"can", "could", "capable", "capabilities", "capability", "abilities", "ability", "able", "handle", "manage", "know"})
_MORE = frozenset({"more", "new", "newly", "extra", "now", "changed", "gained", "added", "since", "update", "updated", "upgrade", "upgraded"})

_PERIOD = frozenset({
    "today", "yesterday", "week", "weeks", "month", "months", "year", "day", "days",
    "morning", "afternoon", "tonight", "weekend", "quarter", "recently", "lately",
})
_METRIC = frozenset({
    "sales", "selling", "sold", "revenue", "takings", "turnover", "units", "orders",
    "average", "aov", "spend", "spent", "breakdown", "split", "compare", "comparison",
    "versus", "vs", "against", "made", "money",
})
# Asking for an order of merit rather than a total: a different question and a different card.
_RANKING = frozenset({"best", "bestseller", "bestsellers", "top", "worst", "most", "least", "highest", "lowest", "popular", "biggest"})
_STOCK = frozenset({"stock", "inventory", "left", "remaining", "sizes"})
# Running out is a different question from how much is on the shelf. "What is running out"
# is a ranking by cover across the catalogue; "how much stock of the yard jeans" is one
# product, and belongs to the model, which can find the product.
_RUNNING_OUT = frozenset({"cover", "running", "low", "reorder", "restock", "restocking", "short", "soon", "empty"})
_EMAIL = frozenset({"email", "emails", "inbox", "mail", "message", "messages", "thread", "threads", "unread", "unanswered", "replied", "reply", "replies", "replying", "heard", "correspondence"})
# Someone is owed an answer. The question "who needs replying to" is this signal, not a
# request to reply: it asks about a state of the inbox.
_WAITING = frozenset({"waiting", "unanswered", "unreplied", "outstanding", "owed", "chase", "chasing", "needs", "need", "back", "ignored", "hanging"})
_DELAY = frozenset({"late", "delayed", "overdue", "waiting", "stuck", "unfulfilled", "unshipped", "slow"})
_ORDER = frozenset({"order", "orders", "invoice", "purchase"})
_CUSTOMER = frozenset({"customer", "customers", "buyer", "buyers", "client", "clients", "people", "person", "someone"})
_STATUS = frozenset({"status", "where", "shipped", "dispatched", "tracking", "delivered", "arrived", "fulfilled"})
_ADDRESS = frozenset({"address", "street", "addresses", "postcode", "house", "number", "door", "line"})
# "Before" is deliberately absent: "has she bought before" already carries "bought", and
# "the one before" is a direction. A word that means two things belongs to the reading that
# needs it, not to both.
_BOUGHT = frozenset({"bought", "buy", "buys", "ordered", "purchased", "spent", "spend", "history", "previously"})

# Complexity markers: a request with two clauses is not a fast path, whatever its words say.
_JOIN = frozenset({"and", "then", "also", "plus", "after", "afterwards", "but", "however", "while", "whilst", "if", "unless", "because"})


@dataclass(slots=True)
class Signals:
    words: tuple[str, ...] = ()
    mutation: bool = False
    question: bool = False
    joins: int = 0
    order_numbers: tuple[str, ...] = ()
    direction: str = ""             # next | previous | back | home
    meta_self: bool = False
    meta_more: bool = False
    period: bool = False
    metric: bool = False
    ranking: bool = False
    stock: bool = False
    running_out: bool = False
    email: bool = False
    waiting: bool = False
    delayed: bool = False
    order: bool = False
    customer: bool = False
    status: bool = False
    address: bool = False
    bought: bool = False
    deixis: bool = False            # "that", "this", "it", "them", "these"
    # Branch state, folded in: what the conversation already has open.
    has_entity: bool = False
    has_set: bool = False
    has_workflow: bool = False
    known_name: str = ""

    # Never written to the timeline, whatever it holds. `known_name` is a customer's name as
    # the owner said it; the observability rule is that telemetry carries ids, counts and
    # controlled words, and this is none of those. The router still uses it; the record says
    # only that a name was recognised.
    PRIVATE = ("words", "known_name")

    def as_dict(self) -> dict[str, Any]:
        out = {k: v for k, v in ((f, getattr(self, f)) for f in self.__slots__) if v and k not in self.PRIVATE}
        if self.known_name:
            out["known_name"] = True
        return out


_DEIXIS = frozenset({"that", "this", "it", "them", "those", "these", "they", "him", "her", "their"})


def signals_for(text: str, *, branch: Any = None) -> Signals:
    """Everything the router looks at, extracted once."""
    from app.routes.turn import spoken_order_numbers

    lowered = (text or "").lower()
    words = tuple(_WORD.findall(lowered))
    have = set(words)
    sig = Signals(
        words=words,
        mutation=mutating(words),
        question=bool(have & _QUESTION) or lowered.strip().endswith("?"),
        joins=sum(1 for w in words if w in _JOIN),
        order_numbers=tuple(spoken_order_numbers(text or "")),
        meta_self=bool(have & _SELF) and bool(have & _ABLE),
        meta_more=bool(have & _MORE),
        period=bool(have & _PERIOD),
        metric=bool(have & _METRIC),
        ranking=bool(have & _RANKING),
        stock=bool(have & _STOCK),
        running_out=bool(have & _RUNNING_OUT) or ({"out", "of"} <= have and not (have & _STOCK)) or ("out" in have and "running" in have),
        email=bool(have & _EMAIL),
        waiting=bool(have & _WAITING),
        delayed=bool(have & _DELAY),
        order=bool(have & _ORDER),
        customer=bool(have & _CUSTOMER),
        status=bool(have & _STATUS),
        address=bool(have & _ADDRESS),
        bought=bool(have & _BOUGHT),
        deixis=bool(have & _DEIXIS),
    )
    # A direction is a direction only when the request names NOTHING ELSE. "Next" is a
    # direction; "next week's sales" is a question about sales, "what's the last order" is a
    # question about an order, and "has she bought before" is a question about a customer.
    # Every one of those was routed to the set-walker before this check existed, and the
    # walker would have answered a question about an order with a customer.
    bare = not (sig.order or sig.customer or sig.email or sig.metric or sig.ranking
                or sig.stock or sig.running_out or sig.period or sig.status or sig.address
                or sig.bought or sig.delayed or sig.meta_self or sig.order_numbers)
    if bare and len(words) <= 5:
        if have & _NEXT:
            sig.direction = "next"
        elif have & _BACK:
            sig.direction = "back"
        elif have & _PREV:
            sig.direction = "previous"
        elif have & _HOME and len(words) <= 3:
            sig.direction = "home"
    if branch is not None:
        sig.has_entity = bool(getattr(branch, "entity", None))
        sig.has_set = bool(getattr(branch, "set_id", ""))
        sig.has_workflow = getattr(branch, "workflow", None) is not None
        sig.known_name = _known_name(text or "", branch)
    return sig


def _known_name(text: str, branch: Any) -> str:
    """A name this branch has already resolved to a record, if the request says it. Longest
    match wins, so "Millie Rogers" beats "Millie"."""
    lowered = " ".join((text or "").lower().split())
    best = ""
    for key in getattr(branch, "resolutions", {}) or {}:
        if key and key in lowered and len(key) > len(best):
            best = key
    return best


# ------------------------------------------------------------------ families


@dataclass(frozen=True, slots=True)
class Family:
    """One intent family and the signals that identify it.

    `needs` are required (all of them); `boosts` add confidence; `blocks` rule it out. `floor`
    is the confidence a match must reach; `entities` are what the runner must resolve before
    the family may run at all.
    """

    name: str
    needs: tuple[str, ...] = ()
    boosts: tuple[str, ...] = ()
    blocks: tuple[str, ...] = ()
    entities: tuple[str, ...] = ()
    base: float = 0.55
    floor: float = 0.7
    # A request longer than this many words is not this family, however it scores: a short
    # instruction is what the fast lane is for.
    max_words: int = 14


FAMILIES: tuple[Family, ...] = (
    Family("working_set_next", needs=("direction_next",), boosts=("has_workflow", "has_set"), blocks=("mutation",), entities=("workflow",), base=0.8, max_words=6),
    Family("working_set_previous", needs=("direction_previous",), boosts=("has_workflow", "has_set"), blocks=("mutation",), entities=("workflow",), base=0.8, max_words=6),
    Family("navigation_back", needs=("direction_back",), blocks=("mutation",), base=0.85, max_words=5),
    Family("navigation_home", needs=("direction_home",), blocks=("mutation",), base=0.8, max_words=4),
    Family("capability_delta", needs=("meta_self", "meta_more"), blocks=("mutation",), base=0.75, max_words=16),
    Family("capability_summary", needs=("meta_self", "question"), blocks=("mutation", "meta_more"), base=0.7, max_words=12),
    Family("order_lookup", needs=("order_number",), boosts=("order", "question"), blocks=("mutation", "metric", "email", "status", "address"), entities=("order",), base=0.8, max_words=12),
    Family("order_status_lookup", needs=("status",), boosts=("order_number", "order", "has_entity", "deixis"), blocks=("mutation", "metric", "address"), entities=("order",), base=0.72, max_words=14),
    Family("order_address_lookup", needs=("address",), boosts=("order_number", "has_entity", "deixis"), blocks=("mutation", "metric"), entities=("order",), base=0.7, max_words=14),
    Family("customer_purchase_lookup", needs=("known_name", "bought"), boosts=("customer", "question"), blocks=("mutation",), entities=("customer",), base=0.72, max_words=14),
    Family("best_sellers_period", needs=("ranking",), boosts=("period", "question", "metric"), blocks=("mutation", "email", "stock", "running_out", "order_number", "customer"), base=0.65, floor=0.72, max_words=14),
    Family("sales_breakdown_period", needs=("metric", "period"), boosts=("question",), blocks=("mutation", "email", "stock", "running_out", "order_number", "ranking"), base=0.66, floor=0.72, max_words=16),
    Family("delayed_orders", needs=("delayed", "order"), boosts=("question", "period"), blocks=("mutation", "order_number"), base=0.72, max_words=14),
    Family("stock_cover_analysis", needs=("running_out",), boosts=("question", "period", "metric", "stock"), blocks=("mutation", "email", "order_number"), base=0.7, floor=0.72, max_words=12),
    Family("needs_reply", needs=("email", "waiting"), boosts=("customer", "question"), blocks=("mutation", "metric", "order_number", "ranking"), base=0.7, floor=0.74, max_words=14),
    Family("inbox_state", needs=("email", "question"), boosts=("period",), blocks=("mutation", "metric", "customer", "waiting", "ranking", "order_number"), base=0.7, floor=0.74, max_words=12),
)

# Signal names as the families spell them, mapped to how they are read off Signals.
_LOOKUP = {
    "mutation": lambda s: s.mutation,
    "question": lambda s: s.question,
    "order_number": lambda s: bool(s.order_numbers),
    "direction_next": lambda s: s.direction == "next",
    "direction_previous": lambda s: s.direction == "previous",
    "direction_back": lambda s: s.direction == "back",
    "direction_home": lambda s: s.direction == "home",
    "meta_self": lambda s: s.meta_self,
    "meta_more": lambda s: s.meta_more,
    "period": lambda s: s.period,
    "metric": lambda s: s.metric,
    "ranking": lambda s: s.ranking,
    "stock": lambda s: s.stock,
    "running_out": lambda s: s.running_out,
    "email": lambda s: s.email,
    "waiting": lambda s: s.waiting,
    "delayed": lambda s: s.delayed,
    "order": lambda s: s.order,
    "customer": lambda s: s.customer,
    "status": lambda s: s.status,
    "address": lambda s: s.address,
    "bought": lambda s: s.bought,
    "deixis": lambda s: s.deixis,
    "has_entity": lambda s: s.has_entity,
    "has_set": lambda s: s.has_set,
    "has_workflow": lambda s: s.has_workflow,
    "known_name": lambda s: bool(s.known_name),
}


@dataclass(frozen=True, slots=True)
class Intent:
    family: str
    confidence: float
    signals: Signals
    slots: dict[str, Any] = field(default_factory=dict)
    runner_up: str = ""
    reason: str = ""

    @property
    def certain(self) -> bool:
        return self.family != "" and self.confidence > 0

    def public(self) -> dict[str, Any]:
        return {"family": self.family or None, "confidence": round(self.confidence, 3),
                "runner_up": self.runner_up or None, "reason": self.reason or None,
                "signals": self.signals.as_dict()}


# How far the winner must be clear of the runner-up. Two families within this of each other
# is an ambiguous request, and an ambiguous request belongs to the model.
MARGIN = 0.08


def score(family: Family, sig: Signals) -> float:
    """Zero when the family is ruled out; otherwise base plus what the boosts add."""
    if len(sig.words) > family.max_words:
        return 0.0
    for name in family.blocks:
        if _LOOKUP[name](sig):
            return 0.0
    for name in family.needs:
        if not _LOOKUP[name](sig):
            return 0.0
    value = family.base
    for name in family.boosts:
        if _LOOKUP[name](sig):
            value += 0.07
    # Two clauses is two requests. The second one would be dropped silently, so decline both.
    value -= 0.25 * max(0, sig.joins)
    # A short instruction is the fast lane's home ground; a long one is probably nuanced.
    if len(sig.words) <= 4:
        value += 0.06
    return max(0.0, min(0.99, value))


def resolve(text: str, *, branch: Any = None) -> Intent:
    """The request as an intent. `family` empty means "this is the model's"."""
    sig = signals_for(text, branch=branch)
    if sig.mutation:
        return Intent(family="", confidence=0.0, signals=sig, reason="asks for a change")
    scored = sorted(((score(f, sig), f) for f in FAMILIES), key=lambda pair: (-pair[0], pair[1].name))
    best_value, best = scored[0]
    second_value, second = (scored[1] if len(scored) > 1 else (0.0, None))
    if best_value <= 0:
        return Intent(family="", confidence=0.0, signals=sig, reason="no family matched")
    if best_value < best.floor:
        return Intent(family="", confidence=round(best_value, 3), signals=sig, runner_up=best.name, reason="below the family's confidence floor")
    if second is not None and second_value > 0 and best_value - second_value < MARGIN:
        return Intent(family="", confidence=round(best_value, 3), signals=sig, runner_up=second.name, reason=f"too close to {second.name}")
    return Intent(family=best.name, confidence=round(best_value, 3), signals=sig, runner_up=(second.name if second_value > 0 and second else ""),
                  slots={"order_numbers": list(sig.order_numbers), "name": sig.known_name})


def family(name: str) -> Family | None:
    for candidate in FAMILIES:
        if candidate.name == name:
            return candidate
    return None
