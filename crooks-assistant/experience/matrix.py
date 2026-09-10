"""What can be reached, and how — worked out from the registries rather than written down.

A matrix maintained by hand is a document that is wrong the first time somebody adds a recipe
and forgets it. Every column here is read from the thing that actually decides:

    voice            an intent family exists for it (app/fastpath/intent.py FAMILIES)
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
}

# Operations a live read-only run must not exercise, whatever their scenario does. Nothing is
# here yet because every scenario is a read — the list exists so that adding a write-shaped
# scenario has somewhere obvious to declare it.
NOT_LIVE_SAFE: frozenset[str] = frozenset()


def build() -> list[dict[str, Any]]:
    """One row per semantic operation, derived."""
    import app.fastpath.library  # noqa: F401 — registers the recipes
    from app import commands
    from app.fastpath.intent import FAMILIES
    from app.fastpath.recipes import RECIPES
    from experience.scenarios import BY_NAME

    rows: list[dict[str, Any]] = []

    for family in FAMILIES:
        recipe = RECIPES.get(family.name)
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
