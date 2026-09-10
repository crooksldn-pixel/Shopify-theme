"""Reviewed order item editing (brief §10): adding a line to an order that already exists.

"Add a black hoodie to this order" was refused all through Phase 2 — honestly, because line
items could not be changed. This is the family that changes that, and everything in it exists
to answer one question before the owner's finger moves: WHICH garment, and WHAT does it cost
the customer.

The shape, end to end:

    a control on the order card  →  order_edit.find      a read: the catalogue's candidates
    a candidate and a quantity   →  order_edit.stage     a proposal: Shopify prices the edit
    the hold on that card        →  /actions/…/commit    the one mutation

Three things about it are deliberate.

**The picker is a read.** `order_edit.find` runs a FAST recipe that calls
`shopify_variant_search` and draws a `variant_picker`. It stages nothing, proposes nothing and
cannot: a recipe naming a write tool is a crash at start-up (app/fastpath/recipes.py). The
owner is choosing, and choosing is not authorising.

**The consequence is Shopify's arithmetic, not ours.** `order_edit.stage` prepares through the
one action engine, and the write tool's PREPARE step runs `orderEditBegin` and
`orderEditAddVariant` — which build and price a CalculatedOrder and change nothing on the real
order. So the card says what the line costs, what the order becomes and what the customer will
owe, from Shopify itself, before anything is applied. `orderEditCommit` is the only mutation
the gesture authorises.

**It cannot be reached by voice, and this says so rather than pretending.** `intent.resolve`
returns no family for any sentence carrying a mutation signal, and "add" is one — that is the
fast lane's structural inability to write, and it is right. So the intent family below can
never win a turn: it *requires* the mutation signal that stops resolution before scoring
begins. It is registered anyway, because a family whose reachability is written down is a
family whose reachability can be tested (tests/test_order_edit.py), and because when a spoken
route to a proposal exists this is where it plugs in. Until then the touch path is the whole
path, and it is complete: a control on the order card, a picker, a card, a hold.
"""

from __future__ import annotations

from typing import Any

from app.capabilities.families import CapabilityFamily
from app.capabilities.families import register as register_family
from app.commands import Command, Outcome, may_open
from app.commands import Ctx as CommandCtx
from app.commands import register as register_command
from app.fastpath.intent import Family, extend
from app.fastpath.models import Ctx, FastAnswer
from app.fastpath.recipes import CACHE_NONE, Recipe, register
from app.presentation import MAX_PICKER_QUANTITY, variant_picker
from app.reads.scheduler import Read, ReadPlan, ReadResult
from app.surfaces import Entity, Freshness, Surface

# The write this family stages, and the read that feeds it. Named once, here, so the
# capability family, the recipe and the command cannot drift apart.
WRITE_TOOL = "shopify_order_add_item"
SEARCH_TOOL = "shopify_variant_search"
OPERATION = "order_edit_add_line"
SCOPE = "write_order_edits"

# What the tablet may post to narrow the picker, and how much of it. Words, not arguments:
# they reach a READ, and the Mac reads the price and builds every execution argument itself.
MAX_WORD_CHARS = {"product": 60, "colour": 30, "size": 20}


# ------------------------------------------------------------------ the picker (a read)


def _picker_plan(ctx: Ctx) -> ReadPlan | None:
    """One read: the variants matching the words, or the catalogue's first few when there are
    none. `slots` is where a tap's words arrive and where a sentence's would (app/routes/
    command.py); `text` is what was actually said, and is the product words when a spoken
    route to this family exists."""
    slots = ctx.intent.slots or {}
    product = str(slots.get("product") or ctx.text or "").strip()[: MAX_WORD_CHARS["product"]]
    return ReadPlan([
        Read("variants", SEARCH_TOOL, {
            "product": product,
            "colour": str(slots.get("colour") or "").strip()[: MAX_WORD_CHARS["colour"]],
            "size": str(slots.get("size") or "").strip()[: MAX_WORD_CHARS["size"]],
            "limit": 8,
        }, source="shopify", cost=90.0, optional=False),
    ], label="order_add_item")


def _picker_render(ctx: Ctx, result: ReadResult) -> FastAnswer:
    """The picker card, and a sentence that says how many there are to choose from.

    Deferring rather than drawing an empty card is the rule here as everywhere: a card
    offering nothing to add is worse than a sentence saying the words matched nothing, and the
    model can find a product this cannot.
    """
    body = result.values.get("variants")
    if not isinstance(body, dict):
        return FastAnswer(answer="", defer="the catalogue did not answer")
    order_id = ctx.entity("order")
    if not order_id:
        # The command checks this before the recipe runs; a recipe that trusted it would draw
        # a picker whose Add button had no order to add to.
        return FastAnswer(answer="", defer="no order is open to add to")
    candidates = [c for c in (body.get("candidates") or []) if isinstance(c, dict)]
    if not candidates:
        asked = " ".join(str(v) for v in (body.get("asked") or {}).values() if str(v or "").strip())
        return FastAnswer(answer="", defer=f"nothing in the catalogue matches {asked!r}" if asked else "the catalogue is empty")
    label = _order_label(ctx)
    data = variant_picker(body, order_id=order_id, order_number=label, quantity=1)
    surface = Surface(
        surface_type="variant_picker",
        ui_type="variant_picker",
        data=data,
        entity=Entity(kind="order", ref=order_id, label=label),
        title="Add to the order",
        subtitle=f"{data['count']} to choose from" if data["count"] != 1 else "One match",
        freshness=Freshness(source="shopify", complete=not result.partial),
    )
    if data["confident_variant_id"]:
        first = data["candidates"][0]
        variant = f", {first['variant']}" if first["variant"] else ""
        words = f"One match: {first['title']}{variant} at {first['price']}. Tap Add to prepare it."
    else:
        words = f"{data['count']} to choose from. Pick one and tap Add."
    if data["note"]:
        words = f"{words} {data['note']}"
    return FastAnswer(
        answer=words, calls=list(result.calls), drawn=[], surfaces=[surface], partial=result.partial,
        trace={"candidates": len(data["candidates"]), "confident": bool(data["confident_variant_id"])},
    )


def _order_label(ctx: Ctx) -> str:
    found = getattr(ctx.branch, "entity", None) or {}
    return str(found.get("label") or "")


register(Recipe(
    recipe_id="order_add_item", intent_family="order_add_item", required_entities=("order",),
    read_primitives=(SEARCH_TOOL,), parallel_nodes=(("variants",),), ui="variant_picker",
    # Never cached: what is for sale and what is in stock is exactly what must not be stale on
    # the card the owner is about to add from.
    cache_policy=CACHE_NONE, min_confidence=0.75, target_ms=1200,
    plan=_picker_plan, render=_picker_render,
))

# The spoken family, declared so its unreachability is a fact with a test rather than a
# comment. `mutation` is in `needs` on purpose: an add is an instruction, and
# `intent.resolve` returns no family at all for a sentence carrying that signal — so this
# scores only when scoring is never reached. `has_entity` is the other half of the brief's
# rule ("block when no order is open"): a need that is not met rules the family out.
extend([
    Family("order_add_item", needs=("mutation", "order", "has_entity"),
           boosts=("deixis",), blocks=("question", "metric", "email", "ranking", "status", "address"),
           entities=("order",), base=0.8, floor=0.75, max_words=12),
])


# ------------------------------------------------------------------ the commands (touch)


def _open_picker(ctx: CommandCtx) -> Outcome:
    """A control on the order card. Names the recipe and the words to narrow it by; reads and
    stages nothing itself (a command is synchronous — see app/commands.py).

    The order is the one on screen. The tablet may name it, and then it must be that one: a
    posted id that is issued but is not what the owner is looking at would prepare a change
    to an order he cannot see.
    """
    entity = getattr(ctx.branch, "entity", None) or {}
    open_order = str(entity.get("ref") or "") if entity.get("kind") == "order" else ""
    if not open_order:
        return Outcome.refused("no_order", "There is no order open to add anything to.")
    asked = ctx.arg("order_id")
    if asked and asked != open_order:
        return Outcome.refused("wrong_order", "That is not the order on screen.")
    slots = {key: ctx.arg(key)[:limit] for key, limit in MAX_WORD_CHARS.items()}
    return Outcome(answer="", changed={"recipe": "order_add_item", "slots": slots,
                                       "entity": {"kind": "order", "ref": open_order, "label": str(entity.get("label") or "")}})


def _stage_add_item(ctx: CommandCtx) -> Outcome:
    """"Add to order" on the picker. The tablet posts which order, which variant and how many
    — three identities and a small integer — and the Mac does everything else.

    What it does NOT post is a single argument of the mutation. The price, the calculated
    order, the new total and what the customer will owe are read and built on the Mac by the
    write tool's PREPARE step (app/tools/shopify_writes.py), stored on the proposal, and sent
    only after the hold. This returns the change to be prepared; `app/routes/command.py`
    prepares it through the same gate and the same action engine a model-proposed change goes
    through, and answers with the confirmation card.
    """
    order_id, variant_id = ctx.arg("order_id"), ctx.arg("variant_id")
    entity = getattr(ctx.branch, "entity", None) or {}
    if not order_id:
        order_id = str(entity.get("ref") or "") if entity.get("kind") == "order" else ""
    if not order_id or not variant_id:
        return Outcome.refused("no_target", "That says which order or which item is being added.")
    # Issued to THIS conversation, and of the right kind. The gate checks both again before
    # the tool runs; checking here means the refusal is a sentence rather than a tool error,
    # and that a guessed id never reaches a Shopify read.
    if not may_open(ctx, "order", order_id):
        return Outcome.refused("not_held", "I do not have that order to hand; open it again.")
    if variant_id not in (getattr(ctx.session, "issued_ids", None) or frozenset()):
        return Outcome.refused("unknown_variant", "That item is not one I have looked up; open the picker again.")
    quantity, problem = _quantity(ctx.arg("quantity", "1"))
    if problem:
        return Outcome.refused("bad_quantity", problem)
    return Outcome(answer="", changed={
        "stage": {"tool": WRITE_TOOL, "args": {"order_id": order_id, "variant_id": variant_id, "quantity": quantity}},
        "entity": {"kind": "order", "ref": order_id, "label": str(entity.get("label") or "")},
    })


def _quantity(value: str) -> tuple[int, str]:
    """The stepper's number, as a number. A form field is a string; a quantity that is not a
    small whole number is refused here rather than being clamped, because clamping a typo to
    1 and adding it to a paid order is a change nobody asked for."""
    try:
        quantity = int(str(value or "1").strip())
    except (TypeError, ValueError):
        return 0, "How many is not a number."
    if not 1 <= quantity <= MAX_PICKER_QUANTITY:
        return 0, f"How many must be between 1 and {MAX_PICKER_QUANTITY}."
    return quantity, ""


# Touch only, both of them. There is no sentence that reaches either: a spoken instruction to
# add something carries a mutation signal, and the fast lane declines every one of those.
register_command(Command("order_edit.find", "Find the item to add to this order", _open_picker,
                         voice=False, needs_entity=("order",)))
register_command(Command("order_edit.stage", "Prepare adding the chosen item to this order", _stage_add_item,
                         voice=False, needs_entity=("order",)))


# ------------------------------------------------------------------ the capability state


async def _probe(runtime: Any) -> dict[str, Any]:
    """Whether this Mac could edit an order right now. One read — the scopes the store has
    granted, cached with the rest of the capability table — and never a mutation.

    A store that has not granted `write_order_edits` gets MISSING_SCOPE with the scope named,
    which does two things: the capability card and /health say which permission is wanted, and
    `runtime.withheld_by_family()` stops the model being offered the write tool at all, so it
    does not spend a turn trying an operation the store could only refuse.
    """
    try:
        granted = set(await runtime.shopify.access_scopes())
    except Exception as exc:  # noqa: BLE001 — Shopify not answering is not a missing grant
        return {"state": "TEMPORARILY_UNAVAILABLE",
                "detail": f"the Shopify scope check did not answer ({type(exc).__name__})", "scope": SCOPE}
    if SCOPE not in granted:
        return {"state": "MISSING_SCOPE",
                "detail": f"the store has not granted {SCOPE}; add it on the Dev Dashboard and approve it in the store admin",
                "scope": SCOPE}
    return {"state": "READY", "detail": "ready — an item can be added to an order", "scope": SCOPE}


register_family(CapabilityFamily(
    key="order_edit",
    label="Order item editing",
    area="orders",
    what="Add an item to an existing order, priced by Shopify before you authorise it",
    operations=(OPERATION,),
    tools=(SEARCH_TOOL, WRITE_TOOL),
    scopes=(SCOPE,),
    state="READY",
    probe=_probe,
))
