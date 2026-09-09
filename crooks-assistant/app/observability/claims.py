"""What the assistant said it could not do, held against what the Mac can compose.

A refusal in the answer ("I can't…") is a deterministic signal. Whether it was warranted is
decided here, from words: the question is matched against a small map of the things the
read layer, the working sets and the batch tools compose — best sellers, a breakdown by
size, a comparison, days of cover, who has emailed, tags on all of them — and a refusal of
something on that map, with the tools registered, is a FALSE UNSUPPORTED claim: the
capability exists and the assistant did not reach for it. The same words find the bulk
requests and the follow-up shapes a session repeats. No judgement of tone; no model."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

# Words the assistant uses when it declines: the report's own rule, kept in one place.
CANNOT_RE = re.compile(
    r"\b(i can(?:no|')t|i'm not able to|i am not able to|isn't something i can|is not something i can|i (?:don't|do not) have a way to|not able to do that|i'm unable to|i am unable to|no way to|i don't have (?:a tool|access|the ability))\b",
    re.I,
)


@dataclass(frozen=True, slots=True)
class Capability:
    key: str
    tools: tuple[str, ...]
    what: str
    patterns: tuple[re.Pattern, ...]

    def matches(self, words: str) -> bool:
        return any(p.search(words) for p in self.patterns)


def _cap(key: str, tools: tuple[str, ...], what: str, *patterns: str) -> Capability:
    return Capability(key, tools, what, tuple(re.compile(p, re.I) for p in patterns))


# What the Mac composes today, by the words a question uses. Each names the tools it takes;
# a question that matches and an answer that declines is the report's business.
CAPABILITIES: tuple[Capability, ...] = (
    _cap("best_sellers", ("commerce_aggregate",), "a ranking of products by units or revenue",
         r"best[- ]?sell", r"top[- ]?sell", r"s(?:old|ells?) (?:the )?(?:most|best)", r"most popular", r"what(?:'s| is| has been) selling", r"least sold", r"worst[- ]sell", r"slowest[- ]sell", r"top (?:\d+|ten|five) (?:products|items|lines)"),
    _cap("breakdown", ("commerce_aggregate",), "a breakdown by size, colour, product, day, week, month, customer or country",
         r"\b(?:by|per|split by|broken down by|breakdown by) (?:size|colour|color|product|day|week|month|customer|country|type)\b", r"which (?:size|colour|color)s?\b.{0,30}\b(?:sells?|sold|selling)"),
    _cap("comparison", ("commerce_aggregate",), "a comparison with the period before",
         r"\bcompar", r"\bversus\b", r"\bvs\.?\b", r"(?:against|than|compared (?:to|with)) (?:last|the previous) (?:week|month|year|period)", r"\bup or down\b", r"how does (?:this|that) (?:week|month) look against"),
    _cap("aov", ("commerce_aggregate",), "average order value",
         r"average (?:order|basket|spend)", r"\baov\b", r"per order on average"),
    _cap("velocity", ("inventory_query",), "sales velocity, days of cover and what to restock",
         r"days? of (?:stock|cover)", r"run(?:ning|s)? out", r"stock cover", r"how (?:long|many days) (?:will|until|before)", r"restock", r"sell[- ]?through", r"\bvelocity\b", r"reorder"),
    _cap("customers_ranked", ("commerce_aggregate",), "customers ranked or filtered by what they have bought",
         r"(?:top|best|biggest) (?:customers|spenders|buyers)", r"customers who (?:spent|have spent|bought|ordered|have ordered)", r"spent (?:over|more than|at least)", r"repeat customers", r"lifetime (?:value|spend)", r"(?:more|fewer) than \w+ orders"),
    _cap("delayed_orders", ("commerce_query",), "orders still to ship, by age",
         r"older than", r"still (?:to|not) (?:ship|fulfil|be shipped|been shipped)", r"\bunfulfilled\b", r"not (?:been )?(?:shipped|fulfilled|sent out)", r"\bdelayed\b", r"waiting (?:to ship|more than|over)", r"(?:haven't|have not|hasn't) (?:shipped|gone out)"),
    _cap("unfulfilled_value", ("commerce_aggregate",), "the revenue tied up in orders still to ship",
         r"(?:tied up|worth|revenue|value|how much money).{0,40}(?:unfulfilled|unshipped|not shipped|still to ship)", r"(?:unfulfilled|unshipped|not shipped).{0,40}(?:worth|revenue|value|total)"),
    _cap("period_sales", ("commerce_aggregate",), "sales, orders and revenue for a named period",
         r"(?:sales|revenue|takings|orders) (?:for |in |on |this |last |over )?(?:today|yesterday|this week|last week|this month|last month|the last \d+ days)", r"how much (?:did|have) we (?:sell|take|make|do)", r"how many orders"),
    _cap("cross_source", ("email_query",), "which of a set's customers have emailed, and whether we replied",
         r"(?:who|which(?: of them| of those| ones)?) (?:has|have|had) (?:emailed|written|wrote|contacted|been in touch|chased)", r"have (?:they|those|these|any of them) (?:emailed|written|been in touch)", r"emailed us", r"heard from (?:them|those|these|any)", r"(?:have we|did we) repl"),
    _cap("bulk_tags", ("batch_order_tags_add",), "a tag on every order in a working set",
         r"\btag (?:all|them|these|those|each|every)", r"(?:add|put) (?:a |the )?tags?.{0,30}(?:all|every|each|them|these|those)", r"tag the (?:delayed|unfulfilled|late|open) orders"),
    _cap("bulk_untag", ("batch_order_tags_remove",), "a tag taken off every order in a working set",
         r"(?:remove|take off|take|untag|clear).{0,20}tag.{0,30}(?:all|every|each|them|these|those)", r"untag (?:all|them|these|those)"),
    _cap("bulk_archive", ("batch_email_archive",), "every thread in a working set archived",
         r"archive (?:all|them|these|those|every|each|the lot)"),
    _cap("bulk_drafts", ("batch_email_drafts",), "a draft to each customer in a working set",
         r"(?:draft|write|email|message|send) (?:an? )?(?:email|note|message|draft)s? (?:to |for )?(?:each|every|all of them|all the|everyone|them all|these|those)", r"(?:email|write to|message) (?:them|these|those|everyone|each) ", r"(?:email|write to|message) (?:them|these|those|everyone) all", r"\bcampaign\b", r"(?:draft|write|email) (?:each|every|all) (?:of )?(?:the |those |these )?(?:customer|of them)"),
    _cap("order_ages", ("commerce_query",), "orders by age, oldest first",
         r"oldest (?:open |unfulfilled |unshipped )?orders", r"how old (?:are|is)", r"longest (?:waiting|outstanding)"),
)

# The words of a change the Mac does singly and not yet in bulk. Asked for in bulk, they are
# potential new actions for the report — never something to do.
_BULK_ONLY_SINGLE = {
    "refund": (r"refund (?:all|them|these|those|every|each|everyone)",), "cancel": (r"cancel (?:all|them|these|those|every|each)",),
    "fulfil": (r"(?:fulfil|fulfill|ship|dispatch) (?:all|them|these|those|every|each)",), "note": (r"(?:add|put) (?:a )?notes? (?:on|to) (?:all|them|these|those|every|each)",),
    "stock": (r"(?:set|adjust|change) (?:the )?stock (?:on|for) (?:all|them|these|those|every|each)",), "send": (r"send (?:them|these|those|it) (?:all|to everyone|to each)", r"send (?:all|every) (?:the )?(?:drafts|emails)"),
}
_BULK_SUPPORTED = {"bulk_tags": "tags", "bulk_untag": "tags", "bulk_archive": "archive", "bulk_drafts": "drafts"}
BULK_RE = re.compile(r"\b(?:all of them|each of them|every one of them|all (?:the|these|those) (?:orders|customers|threads|emails)|them all|everyone|in bulk|\bbulk\b|for each (?:of them|customer|order))\b", re.I)

# The shapes of a follow-up: a few words that keep the last question and change one thing.
FOLLOW_UP_SHAPES: tuple[tuple[str, re.Pattern], ...] = (
    ("period", re.compile(r"^(?:and |just |only |now |what about |for |same (?:for|but) )?(?:today|yesterday|this (?:week|month|year)|last (?:week|month|year|7 days|30 days|seven days|thirty days))\??$", re.I)),
    ("group", re.compile(r"^(?:and |now |what about |split (?:it )?)?(?:by|per) (?:size|colour|color|product|day|week|month|customer|country|type)\??$", re.I)),
    ("filter", re.compile(r"^(?:just|only) (?:the )?[a-z0-9' -]{2,30}\??$", re.I)),
    ("set", re.compile(r"^(?:show me |list |open |what are |which are |who are )?(?:those|these|them)(?: ones)?\??$", re.I)),
    ("more", re.compile(r"^(?:and |show me )?(?:more|the rest|the next (?:few|ten|\d+))\??$", re.I)),
)


def declined(answer: str) -> bool:
    return bool(CANNOT_RE.search(str(answer or "")))


def match_capabilities(question: str) -> list[Capability]:
    words = " ".join(str(question or "").lower().split())
    return [c for c in CAPABILITIES if c.matches(words)]


def claim(question: str, answer: str, tool_calls: list[dict[str, Any]] | None, registered: set[str] | frozenset[str]) -> dict[str, Any] | None:
    """The signal for a turn whose answer declines: which composable capabilities the
    question named, whether their tools are registered (a FALSE UNSUPPORTED claim), and
    what was actually tried. None when the answer does not decline."""
    if not declined(answer):
        return None
    matched = [c for c in match_capabilities(question) if all(t in registered for t in c.tools)]
    attempted = sorted({str(tc.get("tool") or tc.get("name") or "") for tc in (tool_calls or []) if isinstance(tc, dict)} - {""})
    return {
        "false_unsupported": bool(matched),
        "capabilities": [c.key for c in matched],
        "composable_via": sorted({t for c in matched for t in c.tools}),
        "attempted": attempted,
    }


def bulk_request(question: str) -> dict[str, Any] | None:
    """A request to change many things at once: which change, and whether the Mac has a
    batch for it. None when the question is not one."""
    words = " ".join(str(question or "").lower().split())
    for cap in CAPABILITIES:
        if cap.key in _BULK_SUPPORTED and cap.matches(words):
            return {"operation": _BULK_SUPPORTED[cap.key], "supported": True, "tool": cap.tools[0]}
    for operation, patterns in _BULK_ONLY_SINGLE.items():
        if any(re.search(p, words, re.I) for p in patterns):
            return {"operation": operation, "supported": False, "tool": ""}
    if BULK_RE.search(words):
        return {"operation": "unknown", "supported": False, "tool": ""}
    return None


def follow_up_shape(question: str) -> str | None:
    words = " ".join(str(question or "").strip().split())
    if not words or len(words.split()) > 7:
        return None
    for name, pattern in FOLLOW_UP_SHAPES:
        if pattern.match(words):
            return name
    return None


def registered() -> frozenset[str]:
    """The tools this process holds, for a claim judged at turn time."""
    try:
        from app.tools import registry

        return frozenset(registry.names())
    except Exception:  # noqa: BLE001 — a claim without a registry is a claim about nothing
        return frozenset()


__all__ = ["CANNOT_RE", "CAPABILITIES", "Capability", "bulk_request", "claim", "declined", "follow_up_shape", "match_capabilities", "registered"]
