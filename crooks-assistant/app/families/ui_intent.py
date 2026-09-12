"""The requests that oblige a workspace, and the families that draw one (§4, D-5).

Three attempts at one thing, in the owner's own words:

    "Can you expand [name]'s customer page?"      → a capability card, 1,014 pixels
    "Expand [name]'s customer page"               → nothing
    "No, bring up a UI for the customer's page"   → nothing

The first was a routing defect (§5, now `app/capabilities/ask.py`). The second and third were
something simpler and worse: the router had **no family at all** for a request to open a
person's page. "Expand" was not a word it knew. "Bring up a UI for" was not a shape it knew.
So they fell to the model, which spoke, and speech is not what was asked for.

This module is the missing layer, and it is deliberately narrow:

* **`customer_workspace`** — a §4 demand word and a person: a name said plainly, a name the
  branch resolved, a possessive, a pronoun, or the record in front of the owner. It resolves
  WHO and draws their workspace. Nothing else.
* **`ui_area_workspace`** — "take me to the inbox", "go to orders". The two demand phrases the
  dock's landings do not already own, dispatched into the landing recipes rather than
  reimplemented beside them.

Two rules hold here that hold nowhere else in the router, and both are §4:

1. **Speech is not success.** Each render below refuses to answer unless it has a surface to
   answer WITH: no cards, no sentence, and the turn goes to Claude rather than being logged as
   a fast answer that the owner could not see. `app/capabilities/ui_intent.py` is the same rule
   said at the level of the whole turn, where the report reads it.
2. **A named person outranks the record in focus** (D-14). The plan resolves the name FIRST,
   through `shopify_find_customer`; it reaches for the held record only when the words named
   nobody.

Read-only, like every family: `assert_read_only` holds, the recipes name read tools alone, and
nothing here can stage a change.
"""

from __future__ import annotations

from typing import Any

from app.capabilities import ask
from app.fastpath import library
from app.fastpath.intent import Family, extend, signal
from app.fastpath.models import Ctx, FastAnswer
from app.fastpath.recipes import CACHE_ENTITY, Recipe, register
from app.reads.scheduler import ReadPlan, ReadResult

# The pronouns and nouns that mean "the person", as opposed to "the thing on screen". Taken
# from app/capabilities/ask.py so the discrimination rule and this family read one list.
PERSON_PRONOUNS = ask.PERSON_PRONOUNS
PAGE_WORDS = ask.PAGE_WORDS

# One person, not a list of them. "Show me the customers who bought today" is a summary
# question — D-4's defect was answering exactly that with seven full profile pages — and it
# belongs to the summary surfaces, not here. Read from `ask`, so the discrimination rule and
# this family cannot disagree about what a group is.
PLURAL_PEOPLE = ask.PLURAL_PEOPLE

# Which tab of the workspace the TASK implies (§3, and the other half of D-2). A request that
# names orders opens Orders; one that names email opens Email. The tab belongs to the request,
# never to the last tab tapped on a different record.
_TAB_WORDS: tuple[tuple[str, frozenset[str]], ...] = (
    ("orders", frozenset({"order", "orders", "purchase", "purchases", "invoice", "bought", "spend", "spent", "history"})),
    ("email", frozenset({"email", "emails", "inbox", "mail", "thread", "threads", "message", "messages", "correspondence"})),
)


def _names_a_person_subject(sig: Any) -> bool:
    """Whether this sentence says WHOSE page to open.

    Four ways, and the last is the one the owner used when nothing else worked: a name said
    plainly ("open David Harding"), a name the branch has resolved, a possessive ("David's
    customer page"), a pronoun ("bring up his page") — or a page word with a record already
    open, which is "bring up a UI for the customer's page" with a customer on screen.
    """
    words = set(sig.words)
    if words & PLURAL_PEOPLE:
        return False
    if ask.names_a_person(sig):
        return True
    if words & PERSON_PRONOUNS:
        return True
    # A PAGE word and a person already seen: "bring up a UI for the customer's page". The
    # word "customer" on its own is deliberately NOT enough — "show me the customer" with an
    # order open is that order's Customer tab, which `order_tab_show` already answers, and two
    # families on one sentence route nothing at all.
    return bool(words & PAGE_WORDS and (sig.has_entity or sig.has_recent_customer))


def _one_area(sig: Any) -> str:
    """The one dock landing this sentence names, or "" when it names none or two."""
    from app.families.landings import AREAS

    words = set(sig.words)
    named = {
        "orders": {"order", "orders"},
        "email": {"email", "emails", "inbox", "mail"},
        "sales": {"sales", "revenue", "takings", "numbers"},
        "products": {"product", "products", "stock", "inventory"},
    }
    found = [area for area, vocabulary in named.items() if words & vocabulary and area in AREAS]
    return found[0] if len(found) == 1 else ""


_ASKS_FOR_A_PAGE = signal("asks_for_a_persons_page", _names_a_person_subject)
_PLURAL_PEOPLE = signal("plural_people", lambda s: bool(set(s.words) & PLURAL_PEOPLE))
_GOES_TO_AN_AREA = signal("goes_to_an_area", lambda s: ask.goes_to(s.words) and bool(_one_area(s)))


# ------------------------------------------------------------------ a person's workspace


def _tab_for(sig: Any) -> str:
    for tab, vocabulary in _TAB_WORDS:
        if set(sig.words) & vocabulary:
            return tab
    return "overview"


def _workspace_plan(ctx: Ctx) -> ReadPlan | None:
    """Resolve WHO, then read their history.

    The order is D-14's rule: a name in the words is resolved against the shop before
    anything held is consulted. `_customer_plan` is the named path (find, then history) and
    `_customer_history_plan` is the pronoun path (the record in focus, and its customer) —
    and that one refuses outright when a name was said, so the two cannot both apply.
    """
    if ctx.intent.slots.get("name"):
        return library._customer_plan(ctx)
    held = library._customer_history_plan(ctx)
    if held is not None:
        return held
    return _recent_customer_plan(ctx)


def _recent_customer_plan(ctx: Ctx) -> ReadPlan | None:
    """"Bring up a UI for the customer's page" with the focus somewhere else.

    The third of D-5's three attempts. Nothing was in focus — a read of the inbox had moved
    it (D-3) — so there was nothing to resolve and the turn fell to the model. The person he
    meant is the customer this half has been looking at, which the branch records.
    """
    from app.reads.scheduler import Read

    recent = [e for e in (getattr(ctx.branch, "recent_entities", None) or [])
              if isinstance(e, dict) and e.get("kind") == "customer" and e.get("ref")]
    if not recent:
        return None
    return ReadPlan([Read("history", "shopify_customer_history", {"customer_id": str(recent[0]["ref"])},
                          source="shopify", cost=60.0)], label="customer_workspace")


def _workspace_render(ctx: Ctx, result: ReadResult) -> FastAnswer:
    """The customer's workspace, on the tab the request implies — or a defer.

    §4's rule, enforced where it can be enforced: this family exists because the owner asked
    to be SHOWN something, so an answer with nothing to show is not an answer. It defers, and
    Claude — which can search, and ask — takes the turn.
    """
    answer = library._customer_history_render(ctx, result)
    if answer.deferred:
        return answer
    if not (answer.calls or answer.surfaces):
        return FastAnswer(answer="", defer="the workspace could not be drawn, and a spoken answer is not what was asked for")
    tab = _tab_for(ctx.intent.signals)
    held = getattr(ctx.branch, "entity", None) or {}
    if held.get("kind") == "customer" and held.get("ref") and tab != "overview":
        # The tab the TASK implies, set on THIS entity. `visit` is where a branch records
        # which part of which record it is on (app/session/branch.py).
        ctx.branch.visit("customer", str(held["ref"]), str(held.get("label") or ""), tab=tab)
    answer.trace = {**answer.trace, "tab": tab, "ui_intent": True}
    return answer


register(Recipe(
    recipe_id="customer_workspace", intent_family="customer_workspace",
    # Deliberately none, for the reason `customer_history_lookup` gives: the recipe works from
    # EITHER a name in the words or a record in focus, and requiring both made it defer on the
    # commonest way of asking.
    required_entities=(),
    read_primitives=("shopify_find_customer", "shopify_customer_history", "shopify_order_detail"),
    parallel_nodes=(("find",), ("detail",), ("history",)), ui="customer",
    cache_policy=CACHE_ENTITY, min_confidence=0.72, target_ms=1500,
    plan=_workspace_plan, render=_workspace_render,
))


# --------------------------------------------------------------------- a place, by voice


def _area_recipe(ctx: Ctx):
    from app.families.landings import AREAS
    from app.fastpath.recipes import RECIPES

    area = _one_area(ctx.intent.signals)
    return RECIPES.get(AREAS.get(area, ""))


def _area_plan(ctx: Ctx) -> ReadPlan | None:
    """Straight into the landing's own plan. "Take me to the inbox" and a thumb on the dock's
    Inbox icon must reach the same reads, or they are two features."""
    recipe = _area_recipe(ctx)
    return recipe.plan(ctx) if recipe is not None and recipe.plan else None


def _area_render(ctx: Ctx, result: ReadResult) -> FastAnswer:
    recipe = _area_recipe(ctx)
    if recipe is None or not recipe.render:
        return FastAnswer(answer="", defer="that is not one of the dock's landings")
    answer = recipe.render(ctx, result)
    if not answer.deferred and not (answer.calls or answer.surfaces):
        return FastAnswer(answer="", defer="the landing could not be drawn, and a spoken answer is not what was asked for")
    return answer


register(Recipe(
    recipe_id="ui_area_workspace", intent_family="ui_area_workspace",
    read_primitives=("commerce_query", "commerce_aggregate", "inventory_query", "email_query", "gmail_search"),
    parallel_nodes=(("open", "today"),), ui="order_list", cache_policy=CACHE_ENTITY,
    min_confidence=0.72, target_ms=2500, plan=_area_plan, render=_area_render,
))


# --------------------------------------------------------------------------- registration

extend([
    # "Expand [name]'s customer page." "Show me his orders." "Bring up a UI for the customer's
    # page." One person, one workspace.
    #
    # `bought` is blocked on purpose, and it is the one boundary worth stating: "what has he
    # ordered", "how much has she spent" and "pull up his order history" are questions the two
    # history families already answer WITH a customer card, and a second family on those
    # sentences would land inside the router's margin and route nothing at all — which is a
    # worse outcome than either family winning. This one owns the request for the PAGE.
    #
    # The rest of the blocks keep it away from the questions that are about the shop rather
    # than about one person: a period ("show me today's orders" is a list), a metric, a
    # ranking, stock, lateness, an order number, a plural.
    Family("customer_workspace", needs=("ui_demand", _ASKS_FOR_A_PAGE),
           boosts=("customer", "question", "deixis"),
           blocks=("mutation", "order_number", "period", "metric", "ranking", "running_out",
                   "stock", "delayed", "waiting", "unfulfilled", "international", "bought",
                   "status", "address", "again", _PLURAL_PEOPLE),
           base=0.84, floor=0.72, max_words=12),
    # "Take me to the inbox." "Go to orders." The landings own "open orders" and "show me
    # sales" already (their word is `listing`, which these two phrases are not), so this takes
    # only what nothing else can take, and dispatches into the same recipes.
    Family("ui_area_workspace", needs=(_GOES_TO_AN_AREA,),
           blocks=("mutation", "order_number", "period", "known_name", "possessive_name",
                   "deixis", "waiting", "ranking", "running_out", "delayed", "again",
                   "status", "address", "bought"),
           base=0.84, floor=0.72, max_words=7),
])
