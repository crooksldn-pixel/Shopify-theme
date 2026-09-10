"""What can be reached, and how — worked out from the registries rather than written down.

A matrix maintained by hand is a document that is wrong the first time somebody adds a recipe
and forgets it. Every column here is read from the thing that actually decides:

    voice            an intent family exists for it (app/fastpath/intent.py, core AND the
                     families that register through `extend()` — a Phase 3 family is as real
                     as a Phase 1 one, and iterating only the core tuple left every one of
                     them off this table)
    touch            a semantic command exists for it (app/commands.py REGISTRY)
    touch → voice    the command arms a spoken continuation (commands.SPOKEN_CONTROLS)
    fast path        a recipe is registered for the family (app/fastpath/recipes.py RECIPES)
    normal path      always true: anything the fast lane declines, Claude takes
    fixture test     a golden scenario exercises it (experience/scenarios.py)
    live read test   the same scenario is safe to run against the real shop

The only hand-written part is which scenario covers which operation, and that is a mapping of
names — if a scenario is renamed the matrix says "not covered" rather than quietly lying.
"""

from __future__ import annotations

from typing import Any

# Which golden scenario exercises which semantic operation. A name not in SCENARIOS shows as
# uncovered rather than being silently believed.
COVERAGE: dict[str, tuple[str, ...]] = {
    "capability_summary": ("capabilities",),
    "capability_delta": ("capabilities",),
    "order_lookup": ("order_lookup", "enrichment"),
    "order_reopen": ("repeat_order",),
    "order_list_period": ("today_orders", "next_previous"),
    "order_status_lookup": (),
    "order_address_lookup": ("full_address",),
    "customer_history_lookup": ("customer_history",),
    "customer_purchase_lookup": (),
    "needs_reply": ("needs_reply",),
    "inbox_state": (),
    "best_sellers_period": (),
    "sales_breakdown_period": (),
    "delayed_orders": (),
    "stock_cover_analysis": (),
    "working_set_next": ("next_previous",),
    "working_set_previous": ("next_previous",),
    "navigation_back": ("back",),
    "navigation_home": (),
    "surface.tab": ("tabs",),
    "surface.expand": (),
    "open.entity": ("linked_entities",),
    "order.open_shipping": ("tabs",),
    "order.open_items": (),
    "customer.open_orders": (),
    "voice.bind": (),
    "voice.cancel": (),
    "navigation.forward": (),
    # Phase 3's families. Each of these is reached by a sentence the live session actually
    # said, and each row names the golden scenario that proves it.
    "landing_orders": ("landing_orders",),
    "landing_inbox": ("landing_inbox",),
    "landing_sales": ("landing_sales",),
    "landing_products": ("landing_products",),
    "order_tab_show": ("spoken_tab",),
    "order_latest": ("spoken_latest",),
    "branch_switch": ("spoken_switch",),
    "order_email_draft": ("graph_compound_reply", "graph_order_to_email", "graph_no_email_about_this_order"),
    "order_email_waiting": ("graph_compound_reply",),
    "unfulfilled_orders": ("query_undelivered",),
    "international_orders": ("query_international_waiting",),
    "order_add_item": ("order_add_item_picker", "order_add_item_ambiguous", "order_add_item_cancelled"),
    "email_compose_any": ("compose_open", "compose_dictated"),
    "draft_send_instead": ("compose_send_instead", "compose_send_spoken"),
    # `compose_rewrite` has no scenario of its own: the rewrite is asserted in
    # tests/test_compose.py, where the words handed to the model can be read without a
    # customer's email going through a transcript. Shown as uncovered, which is honest.
    "compose_rewrite": (),
    "open.area": ("landing_orders", "landing_inbox", "landing_sales", "landing_products"),
    "compose.field": ("compose_dictated",),
    "compose.stage": ("compose_stage",),
    "order_edit.stage": ("order_add_item_picker",),
    # The commerce families (brief sections 11 to 14). The three creations are reached by
    # touch and by the model; only the order names a spoken family, because "create an order
    # for X" is the one sentence of the four whose whole request the Mac can resolve by
    # reading — a code's value and a credit's amount are things the owner must be able to see
    # and correct before anything is prepared, which is what the workspace is for.
    "abandoned_checkouts": ("abandoned_checkouts", "abandoned_window"),
    "discount_code": ("discount_new_code", "discount_code_taken"),
    "discount.open": ("discount_new_code", "discount_code_taken"),
    "discount.field": ("discount_new_code", "discount_code_taken"),
    "discount.stage": ("discount_new_code",),
    "order_new": ("order_new", "order_new_ambiguous"),
    "order.open": ("order_new", "order_new_ambiguous"),
    "order.field": ("order_new", "order_new_ambiguous"),
    "order.additem": ("order_new",),
    "order.stage": ("order_new",),
    "credit.field": ("store_credit_give",),
    "credit.stage": ("store_credit_give",),
    # `order_new_line`, `order.choose`, `order.customer`, `order.removeitem`,
    # `discount.choose`, `discount.discard`, `order.discard` and `credit.discard` have no
    # scenario of their own: each is asserted in tests/ (test_order_create.py,
    # test_discounts.py, test_store_credit.py), where a refused option and a discarded form
    # can be read without a transcript. Shown as uncovered, which is honest.
    "order_new_line": (),
    "discount.choose": (),
    "discount.discard": (),
    "order.choose": (),
    "order.customer": (),
    "order.removeitem": (),
    "order.discard": (),
    "credit.discard": (),
}

# Operations a live read-only run must not exercise, whatever their scenario does. Nothing is
# here yet because every scenario is a read — the list exists so that adding a write-shaped
# scenario has somewhere obvious to declare it.
NOT_LIVE_SAFE: frozenset[str] = frozenset()


def build() -> list[dict[str, Any]]:
    """One row per semantic operation, derived."""
    import app.fastpath.library  # noqa: F401 — registers the core recipes
    from app import commands
    from app.families import load_all
    from app.fastpath.intent import all_families
    from app.fastpath.recipes import recipe_for
    from experience.scenarios import BY_NAME

    load_all()
    rows: list[dict[str, Any]] = []

    for family in all_families():
        # `recipe_for`, not `RECIPES[family.name]`: the registry is keyed by recipe id, and a
        # Phase 3 family's recipe is often named for what it does rather than for the family
        # (order_email_draft is answered by order_email_reply). Looking it up by name reported
        # "no fast path" for recipes that plainly have one.
        recipe = recipe_for(family.name)
        scenarios = COVERAGE.get(family.name, ())
        rows.append({
            "operation": family.name,
            "reached_by": "intent family",
            "voice": True,
            # The tapped equivalents are the navigation commands; a question is not a button.
            "touch": family.name in {"navigation_back", "navigation_home",
                                     "working_set_next", "working_set_previous"},
            "touch_then_voice": False,
            "fast_path": recipe is not None,
            "normal_path": True,
            "fixture_test": [s for s in scenarios if s in BY_NAME],
            "live_read_test": family.name not in NOT_LIVE_SAFE and bool(scenarios),
        })

    for command in commands.public():
        name = command["name"]
        scenarios = COVERAGE.get(name, ())
        rows.append({
            "operation": name,
            "reached_by": "semantic command",
            "voice": bool(command["voice"]),
            "touch": bool(command["touch"]),
            "touch_then_voice": bool(command.get("touch_then_voice")),
            # A command is deterministic by construction: it never consults the model.
            "fast_path": True,
            "normal_path": False,
            "fixture_test": [s for s in scenarios if s in BY_NAME],
            "live_read_test": name not in NOT_LIVE_SAFE and bool(scenarios),
        })

    rows.sort(key=lambda r: (r["reached_by"], r["operation"]))
    return rows


def uncovered() -> list[str]:
    """Operations no golden scenario exercises. Printed rather than hidden: a matrix whose
    only job is to look complete is worse than no matrix."""
    return [r["operation"] for r in build() if not r["fixture_test"]]


def _tick(value: Any) -> str:
    return "✓" if value else "·"


def markdown() -> str:
    rows = build()
    out = [
        "# Feature matrix",
        "",
        "Derived from the intent families, the command registry and the scenario list — not",
        "maintained by hand. A row with no scenario is a gap, and is listed as one below.",
        "",
        "| Operation | Reached by | Voice | Touch | Touch→Voice | Fast | Normal | Fixture test | Live read |",
        "|---|---|:-:|:-:|:-:|:-:|:-:|---|:-:|",
    ]
    for r in rows:
        out.append(
            f"| `{r['operation']}` | {r['reached_by']} | {_tick(r['voice'])} | {_tick(r['touch'])} "
            f"| {_tick(r['touch_then_voice'])} | {_tick(r['fast_path'])} | {_tick(r['normal_path'])} "
            f"| {', '.join(r['fixture_test']) or '—'} | {_tick(r['live_read_test'])} |"
        )
    gaps = uncovered()
    out += ["", f"## Not covered by a scenario ({len(gaps)})", ""]
    out += [f"- `{name}`" for name in gaps] or ["- none"]
    out += [""]
    return "\n".join(out)
