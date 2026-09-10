"""Three sentences from the brief's own fast-lane list that still reached the model (§17).

Section 17 names the requests that "should generally avoid a full model critical path". Run
against the router, three of them did not:

    "show me the shipping"        NORMAL   no family matched
    "show me the latest order"    NORMAL   no family matched
    "switch to the other half"    NORMAL   no family matched

Not because the fast lane could not answer them — the tab is a command the tablet already
posts, the latest order is one read, the switch is a move on the session — but because the
router had no WORD for shipping, latest or half. Its signal vocabulary is fixed, and a family
that needed a word of its own had no way to ask for one without editing the `Signals`
dataclass, which is the file every family would then be editing at once.

So `app.fastpath.intent.signal(name, predicate)` — a family brings its own word — and these
three families use it. A core signal can never be shadowed; see the seam's docstring.

Everything here is a read or a move. The tab and the switch touch branch state, which is
position and presentation; nothing in this module can change anything in the shop or the
inbox, and `assert_read_only` holds for its recipes as it does for every other.
"""

from __future__ import annotations

from typing import Any

from app import commands
from app.fastpath import library
from app.fastpath.intent import Family, extend, signal
from app.fastpath.models import Ctx, FastAnswer
from app.fastpath.recipes import CACHE_ANALYTICS, CACHE_ENTITY, Recipe, register
from app.reads.scheduler import Read, ReadPlan, ReadResult

# The tab words, and the tab each one means. "The customer" and "the items" are what the owner
# says; `overview` has no word because asking for it is asking for the card, which is what
# `order_reopen` already answers.
TAB_WORDS: dict[str, str] = {
    # Not "address": "read me the full address" is `order_address_lookup`, which reads it out.
    # This family only moves the screen, and taking that sentence from it made a fast answer
    # ambiguous and sent it to the model — measured, and the reason the blocks below name it.
    "shipping": "shipping", "delivery": "shipping", "postage": "shipping",
    # Not "products": with an order open, "open products" is the dock's Products landing, and
    # putting the word here sent it to the order's Items tab instead — measured. The tab is
    # reached by items, lines or contents.
    "items": "items", "item": "items", "lines": "items", "contents": "items",
    "customer": "customer", "buyer": "customer",
    # Not a bare "email" either: with an order open, "show me the email" is genuinely
    # ambiguous between this order's Email tab and the inbox, and the router said so —
    # 0.96 against 0.90, inside the margin, so nothing routed and the turn went to the model.
    # The inbox owns the bare word; the tab is reached by a sentence that says which order it
    # is about ("the email about this order"), and by the tap, which is never ambiguous.
    "correspondence": "email",
}
# Not "last": walking a set, "the last one" means the PREVIOUS member, and
# `working_set_previous` owns that word. "Latest" and "newest" cannot mean anything else.
LATEST_WORDS = frozenset({"latest", "newest", "recent"})
OTHER_WORDS = frozenset({"other", "second", "first", "left", "right"})
HALF_WORDS = frozenset({"half", "side", "branch"})

_SAYS_TAB = signal("says_tab", lambda s: any(w in TAB_WORDS for w in s.words))
_SAYS_LATEST = signal("says_latest", lambda s: bool(set(s.words) & LATEST_WORDS))
_SAYS_OTHER_HALF = signal("says_other_half", lambda s: bool(set(s.words) & OTHER_WORDS) and bool(set(s.words) & HALF_WORDS))


# ------------------------------------------------------------------- a part of the record


def _tab_wanted(ctx: Ctx) -> str:
    for word in ctx.intent.signals.words:
        if word in TAB_WORDS:
            return TAB_WORDS[word]
    return ""


def _tab_plan(ctx: Ctx) -> ReadPlan | None:
    """Move the branch to the tab, and draw the record it belongs to.

    The move goes through the `surface.tab` command — the same code the tap reaches, which is
    the whole point of the command layer — so a spoken "show me the shipping" and a thumb on
    Shipping cannot disagree about where the branch now is.
    """
    kind = str((getattr(ctx.branch, "entity", None) or {}).get("kind") or "")
    ref = str((getattr(ctx.branch, "entity", None) or {}).get("ref") or "")
    tab = _tab_wanted(ctx)
    if not tab or not ref or tab not in commands.TABS.get(kind, ()):
        return None
    # "Show me the shipping on 1912" names a record that is not the one on screen. A bare
    # number is deliberately not extracted as an order number (a bare 2025 is a year), so the
    # `order_number` block cannot catch this; the guard the lookup recipes use can, and
    # without it this family answered confidently about the wrong customer's address.
    if library._names_another_order(ctx, ref):
        return None
    outcome = commands.run("surface.tab", commands.Ctx(ctx.runtime, ctx.session, ctx.branch, {"surface": kind, "tab": tab}))
    if not outcome.ok:
        return None
    # The card, from what the Mac already holds where it can: going to a tab is not a new
    # question about the record. `replay` refuses a record this conversation was never shown,
    # so the gate is not bypassed by reading the cache.
    held = commands.replay(commands.Ctx(ctx.runtime, ctx.session, ctx.branch, {}), kind, ref)
    if held:
        ctx.calls.extend(held)
        return ReadPlan([], label="order_tab_show")
    tool, argument = ("shopify_order_detail", "order_id") if kind == "order" else ("shopify_customer_history", "customer_id")
    return ReadPlan([Read("detail", tool, {argument: ref}, source="shopify", cost=90.0)], label="order_tab_show")


def _tab_render(ctx: Ctx, result: ReadResult) -> FastAnswer:
    tab = _tab_wanted(ctx)
    label = str((getattr(ctx.branch, "entity", None) or {}).get("label") or "that record")
    calls = list(ctx.calls) + list(result.calls)
    if not calls:
        return FastAnswer(answer="", defer="nothing to draw the record from")
    # The sentence says where the screen now is, and nothing else: what the tab holds is on
    # the card, and reading a shipping address aloud unasked is how PII gets spoken.
    words = {"shipping": f"The shipping for {label}.", "items": f"What is on {label}.",
             "customer": f"The customer on {label}.", "email": f"The email about {label}."}
    return FastAnswer(answer=words.get(tab, f"{label}, on {tab}."), calls=calls,
                      trace={"tab": tab, "replayed": not result.calls})


# ------------------------------------------------------------------------- the latest order


def _latest_plan(ctx: Ctx) -> ReadPlan | None:
    """The most recent order, newest first, one row — then the order itself.

    Through `commerce_query` rather than a listing tool because the query layer holds the
    recent orders already; the second read is the full record the card is built from.
    """
    return ReadPlan([
        Read("listing", "commerce_query", {
            "entity": "orders", "period": "last_30_days",
            "sort": [{"metric": "created_at", "direction": "desc"}], "limit": 1, "title": "The latest order",
        }, source="shopify", cost=120.0),
        Read("detail", "shopify_order_detail", _latest_detail_args, source="shopify", after=("listing",), cost=90.0),
    ], label="order_latest")


def _latest_detail_args(values: dict[str, Any]) -> dict[str, Any] | None:
    body = values.get("listing")
    rows = [r for r in ((body or {}).get("rows") or []) if isinstance(r, dict)] if isinstance(body, dict) else []
    order_id = str(rows[0].get("order_id") or "") if rows else ""
    return {"order_id": order_id} if order_id else None


def _latest_render(ctx: Ctx, result: ReadResult) -> FastAnswer:
    detail = result.values.get("detail")
    if isinstance(detail, dict) and detail.get("order_id"):
        answer = library._order_render(ctx, result)
        if not answer.deferred:
            # Say WHICH order, because "the latest" is a description and the owner wants the
            # number he can repeat back.
            return FastAnswer(answer=f"The latest is {str(detail.get('order_number') or '').lstrip('#')}. {answer.answer}",
                              calls=answer.calls, drawn=answer.drawn, partial=answer.partial,
                              trace={**answer.trace, "latest": True})
        return answer
    body = result.values.get("listing")
    rows = [r for r in ((body or {}).get("rows") or []) if isinstance(r, dict)] if isinstance(body, dict) else []
    if not rows:
        return FastAnswer(answer="Nothing has come in for the last thirty days.", calls=list(result.calls), trace={"rows": 0})
    return FastAnswer(answer="", defer="the latest order did not read in full")


# ------------------------------------------------------------------------- the other half


def _switch_plan(ctx: Ctx) -> ReadPlan | None:
    """Talk to the other half. A move on the session, like Back is a move on the trail."""
    session = ctx.session
    others = [b for b in getattr(session, "branches", {}).values()
              if b.branch_id != ctx.branch.branch_id and getattr(b, "status", "") in ("ACTIVE", "BACKGROUND")]
    if len(others) != 1:
        # Nought or two: there is nothing unambiguous to switch to, and guessing which half
        # the owner meant is worse than asking.
        return None
    session.focus_branch(others[0].branch_id)
    ctx.moved = {"branch_id": others[0].branch_id}
    return ReadPlan([], label="branch_switch")


def _switch_render(ctx: Ctx, result: ReadResult) -> FastAnswer:
    branch_id = str((ctx.moved or {}).get("branch_id") or "")
    other = (getattr(ctx.session, "branches", {}) or {}).get(branch_id)
    if other is None:
        return FastAnswer(answer="", defer="the other half went away")
    # What that half is looking at, drawn — the same surfaces `branch.show` hands the tablet
    # when its chip is tapped. Switching that says nothing and draws nothing is the Phase 2
    # failure this whole area exists to fix.
    outcome = commands.run("branch.show", commands.Ctx(ctx.runtime, ctx.session, ctx.branch, {"branch_id": branch_id}))
    label = str(getattr(other, "label", "") or "the other half")
    if outcome.ok and outcome.surfaces:
        return FastAnswer(answer=outcome.answer or f"That is {label}.", surfaces=list(outcome.surfaces), drawn=[],
                          trace={"branch_id": branch_id, "drawn": True})
    return FastAnswer(answer=f"{label.capitalize()} has nothing on it yet. Ask it something.",
                      trace={"branch_id": branch_id, "drawn": False})


# --------------------------------------------------------------------------- registration

register(Recipe(
    recipe_id="order_tab_show", intent_family="order_tab_show", required_entities=("order",),
    read_primitives=("shopify_order_detail",), parallel_nodes=(("detail",),), ui="order",
    cache_policy=CACHE_ENTITY, min_confidence=0.72, target_ms=700,
    plan=_tab_plan, render=_tab_render,
))
register(Recipe(
    recipe_id="order_latest", intent_family="order_latest", read_primitives=("commerce_query", "shopify_order_detail"),
    parallel_nodes=(("listing",), ("detail",)), ui="order", cache_policy=CACHE_ANALYTICS,
    min_confidence=0.72, target_ms=1200, plan=_latest_plan, render=_latest_render,
))
register(Recipe(
    recipe_id="branch_switch", intent_family="branch_switch", ui="order",
    min_confidence=0.72, target_ms=120, plan=_switch_plan, render=_switch_render,
))

extend([
    # A part of the open record. Needs a record open; an order number in the sentence means
    # it is about a different order and belongs to the lookup families.
    Family("order_tab_show", needs=(_SAYS_TAB, "has_entity"), boosts=("question", "listing", "deixis"),
           blocks=("mutation", "order_number", "metric", "ranking", "period", "waiting", "address", "status", "known_name", "possessive_name", "bought", "stock", "running_out"),
           entities=("order",), base=0.76, floor=0.72, max_words=7),
    # "The latest order". Not a period question ("today's orders" is a list) and not a
    # ranking ("the best seller"), both of which name their own families.
    Family("order_latest", needs=(_SAYS_LATEST, "order"), boosts=("question", "listing"),
           blocks=("mutation", "order_number", "metric", "period", "email", "stock", "running_out", "waiting", "delayed", "possessive_name", "known_name", "address", "status"),
           base=0.78, floor=0.72, max_words=6),
    # "Switch to the other half."
    Family("branch_switch", needs=(_SAYS_OTHER_HALF,), boosts=("listing",),
           blocks=("mutation", "order_number", "metric", "ranking", "period", "email"),
           base=0.84, floor=0.72, max_words=7),
])
