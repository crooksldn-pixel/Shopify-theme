"""The two sentences the tablet could not answer (brief §15).

Both were asked out loud on the physical tablet and both spent 15-16 s of Claude producing
three refused `commerce_query` calls and then an apology:

    "Can you see if any of our orders are undelivered or unfulfilled?"
    "Find a real international order that has been waiting too long and hasn't been fulfilled"

Here they go through the whole runtime — the same POST /turn a voice reaches — against the
golden world, and what is asserted is what was missing: the fast lane, no model, a list to
look at with the oldest thing waiting at the top of it, and an answer that says "unfulfilled"
while admitting that delivery is not something this Mac can see.
"""

from __future__ import annotations

from typing import Any

from experience.fixtures import data
from experience.harness import Harness

# `Result`, `check` and the shared assertions live in experience/scenarios.py, which collects
# the packs at the END of its own module body, so these names are bound by the time this pack
# is imported.
from experience.scenarios import Result, a_surface, check, deterministic, grounded

UNDELIVERED = "Can you see if any of our orders are undelivered or unfulfilled?"
INTERNATIONAL = "Find a real international order that has been waiting too long and hasn't been fulfilled"


def _orders(capture: Any) -> list[dict[str, Any]]:
    """The rows of the first order list on screen."""
    data_ = capture.data("order_list")
    return [o for o in (data_.get("orders") or data_.get("rows") or []) if isinstance(o, dict)]


def _the_international_order() -> Any:
    """The fixture order going abroad and still waiting: appended to the golden world for
    exactly this question (experience/fixtures/data.py)."""
    return data.INTERNATIONAL_ORDER


async def query_undelivered(h: Harness) -> Result:
    r = Result("query_undelivered", "“Are any of our orders undelivered or unfulfilled?”")
    c = await h.say(UNDELIVERED, scenario="query_undelivered", session_id="q1")
    r.captures.append(c)
    r.checks.append(check("the question the tablet lost 45 s to takes the fast lane",
                          c.lane == "FAST" and c.recipe_id == "unfulfilled_orders",
                          f"lane={c.lane} recipe={c.recipe_id!r} intent={c.intent_family!r}"))
    r.checks.append(deterministic(c))
    r.checks += a_surface(c, "order_list", what="draws the orders still to go out")
    r.checks.append(check("and a set to work through", bool(c.set_id) and c.surface("working_set") is not None,
                          f"set_id={c.set_id!r} surfaces={c.surface_types}"))
    # The one thing the answer must not do: quietly answer the delivery half.
    r.checks.append(check("says unfulfilled, and says delivery is not known here",
                          "unfulfilled" in c.answer.lower() and "tracking status is not available" in c.answer.lower(),
                          c.answer[:200]))
    r.checks.append(check("never claims to know what is undelivered",
                          "undelivered" not in c.answer.lower(), c.answer[:200]))
    if grounded(h):
        rows = _orders(c)
        spec = _the_international_order()
        waiting = [o for o in data.ORDERS if o.fulfillment != "FULFILLED" and o.cancelled_days_ago is None]
        oldest = max(waiting, key=lambda o: o.days_ago)
        r.checks.append(check("the golden world has something waiting to be found", bool(waiting),
                              f"{len(waiting)} unfulfilled"))
        r.checks.append(check("the oldest thing waiting is at the top of the list",
                              bool(rows) and str(rows[0].get("order_number")) == oldest.name,
                              f"first={rows[0].get('order_number') if rows else None} expected={oldest.name}"))
        r.checks.append(check("which is the order going abroad", oldest.name == spec.name,
                              f"oldest={oldest.name} international={spec.name}"))
        r.checks.append(check("every row on the list is one that has not gone out",
                              bool(rows) and all("unfulfilled" in str(o.get("fulfillment") or "").lower() for o in rows),
                              f"{[o.get('fulfillment') for o in rows]}"))
    return r


async def query_international_waiting(h: Harness) -> Result:
    r = Result("query_international_waiting", "“A real international order that has been waiting too long”")
    c = await h.say(INTERNATIONAL, scenario="query_international_waiting", session_id="q2")
    r.captures.append(c)
    r.checks.append(check("“hasn't been fulfilled” is a description, not an instruction: the fast lane takes it",
                          c.lane == "FAST" and c.recipe_id == "international_waiting_orders",
                          f"lane={c.lane} recipe={c.recipe_id!r} intent={c.intent_family!r}"))
    r.checks.append(deterministic(c))
    r.checks += a_surface(c, "order_list", what="draws the international orders waiting")
    r.checks.append(check("says it is international and unfulfilled",
                          "international" in c.answer.lower() and "unfulfilled" in c.answer.lower(), c.answer[:200]))
    r.checks.append(check("delivery is not mentioned: it was not asked about",
                          "tracking status" not in c.answer.lower(), c.answer[:200]))
    if grounded(h):
        spec = _the_international_order()
        rows = _orders(c)
        r.checks.append(check("the order going abroad is the one on the list",
                              [str(o.get("order_number")) for o in rows] == [spec.name],
                              f"rows={[o.get('order_number') for o in rows]} expected=[{spec.name}]"))
        r.checks.append(check("and it is named, with how long it has waited",
                              spec.name.lstrip("#") in c.answer and str(int(spec.days_ago)) in c.answer,
                              c.answer[:200]))
        # A domestic order that is ALSO waiting must not be on this list, or "international"
        # is decoration rather than a filter.
        home = [o for o in data.ORDERS if o.fulfillment != "FULFILLED" and o.cancelled_days_ago is None
                and str(o.address.get("countryCodeV2")) == data.SHOP_COUNTRY]
        r.checks.append(check("the golden world has domestic orders waiting too", bool(home),
                              f"{len(home)} at home"))
        r.checks.append(check("and none of them is on this list",
                              not ({str(o.get("order_number")) for o in rows} & {o.name for o in home}),
                              f"rows={[o.get('order_number') for o in rows]}"))
    return r


async def query_language_no_collision(h: Harness) -> Result:
    """The families around this one keep their sentences: a landing, a period list and the
    lateness question all resolve where they did before, through the real router."""
    r = Result("query_language_no_collision", "The neighbouring questions still go where they went")
    first = await h.say("which orders are unfulfilled", scenario="query_language_no_collision", session_id="q3")
    r.captures.append(first)
    r.checks.append(check("“which orders are unfulfilled” is this family",
                          first.recipe_id == "unfulfilled_orders", f"recipe={first.recipe_id!r}"))
    for text, expected in (("show me today's orders", "order_list_period"),
                           ("open orders", "landing_orders"),
                           ("which orders are late", "delayed_orders")):
        c = await h.say(text, scenario="query_language_no_collision", session_id="q3")
        r.captures.append(c)
        r.checks.append(check(f"“{text}” is still {expected}", c.recipe_id == expected,
                              f"recipe={c.recipe_id!r} intent={c.intent_family!r}"))
        r.checks.append(deterministic(c))
    return r


SCENARIOS = (
    ("query_undelivered", query_undelivered),
    ("query_international_waiting", query_international_waiting),
    ("query_language_no_collision", query_language_no_collision),
)
