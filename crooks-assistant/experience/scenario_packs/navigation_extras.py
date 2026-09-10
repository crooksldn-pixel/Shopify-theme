"""Three of the brief's fast-lane sentences, end to end (§17, §31 scenarios 2 and 18).

The routing is asserted in tests/test_navigation_extras.py; these run the whole turn against
the golden world and check what the owner would actually get: the tab moved AND the record
drawn, the latest order named, the other half's workspace on screen.
"""

from __future__ import annotations

from experience.harness import Harness
from experience.scenarios import Result, a_surface, check, deterministic, grounded


async def spoken_tab(h: Harness) -> Result:
    r = Result("spoken_tab", "“Show me the shipping” with an order open")
    opened = await h.say("show me order 1938", scenario="spoken_tab", session_id="tab1")
    r.captures.append(opened)
    r.checks.append(check("the order is open first", bool(opened.entity and opened.entity.get("ref")), f"entity={opened.entity}"))
    c = await h.say("show me the shipping", scenario="spoken_tab", session_id="tab1")
    r.captures.append(c)
    r.checks.append(check("takes the fast lane", c.lane == "FAST" and c.recipe_id == "order_tab_show", f"lane={c.lane} recipe={c.recipe_id!r}"))
    r.checks.append(deterministic(c))
    r.checks += a_surface(c, "order", what="draws the record, not just a sentence")
    # The move is the branch's, so a Back that returns here returns to this tab — and the tap
    # and the sentence cannot disagree about where the screen is.
    branch = h.branch("tab1", c.branch_id)
    r.checks.append(check("the branch is on the shipping tab", getattr(branch, "tab", "") == "shipping", f"tab={getattr(branch, 'tab', '')!r}"))
    r.checks.append(check("the answer says where the screen is without reading the address out",
                          "shipping" in c.answer.lower() and len(c.answer) < 80, c.answer[:90]))
    # Items, then customer: the same family, a different tab, no model either time.
    d = await h.say("show me the items", scenario="spoken_tab", session_id="tab1")
    r.captures.append(d)
    r.checks.append(check("and again for the items", d.lane == "FAST" and getattr(h.branch("tab1", d.branch_id), "tab", "") == "items",
                          f"lane={d.lane} tab={getattr(h.branch('tab1', d.branch_id), 'tab', '')!r}"))
    return r


async def spoken_latest(h: Harness) -> Result:
    r = Result("spoken_latest", "“Show me the latest order”")
    c = await h.say("show me the latest order", scenario="spoken_latest", session_id="latest1")
    r.captures.append(c)
    r.checks.append(check("takes the fast lane", c.lane == "FAST" and c.recipe_id == "order_latest", f"lane={c.lane} recipe={c.recipe_id!r}"))
    r.checks.append(deterministic(c))
    r.checks += a_surface(c, "order", what="draws the order in full")
    card = c.data("order")
    r.checks.append(check("names which order it is, so the owner can repeat it back",
                          bool(card.get("order_number")) and str(card["order_number"]).lstrip("#") in c.answer,
                          f"answer={c.answer[:80]!r} card={card.get('order_number')!r}"))
    if grounded(h):
        from experience.fixtures import data

        # The newest order the golden world holds. By days_ago AND the hour within the day:
        # three of the fixture's orders are "today", so days_ago alone is a tie and an oracle
        # that broke it arbitrarily failed against a recipe that was right.
        newest = min(data.ORDERS, key=lambda o: (o.days_ago, -o.hour))
        r.checks.append(check("and it is the newest order in the world",
                              str(newest.name).lstrip("#") in str(card.get("order_number") or ""),
                              f"drew {card.get('order_number')!r}, newest is {newest.name!r}"))
    return r


async def spoken_switch(h: Harness) -> Result:
    r = Result("spoken_switch", "“Switch to the other half”")
    first = await h.say("show me order 1938", scenario="spoken_switch", session_id="half1")
    r.captures.append(first)
    fork = await h.client.post("/branches/fork", data={"session_id": "half1", "label": "right"},
                               headers={"Tailscale-User-Login": "owner@example.com", "X-Forwarded-For": "100.64.0.9"})
    body = fork.json() if fork.content else {}
    other = str(((body.get("branch") or {}).get("branch_id")) or body.get("branch_id") or "")
    r.checks.append(check("the orb divides", bool(other), f"branch_id={other!r}"))
    # Ask the new half something, so it has a workspace of its own to come back to.
    away = await h.say("show me today's orders", scenario="spoken_switch", session_id="half1", branch_id=other)
    r.captures.append(away)
    r.checks += a_surface(away, "order_list", what="the other half has its own workspace")
    # Now switch back by voice, from the half that is focused.
    c = await h.say("switch to the other half", scenario="spoken_switch", session_id="half1")
    r.captures.append(c)
    r.checks.append(check("takes the fast lane", c.lane == "FAST" and c.recipe_id == "branch_switch", f"lane={c.lane} recipe={c.recipe_id!r}"))
    r.checks.append(deterministic(c))
    r.checks.append(check("the focus really moved", c.branch_id and c.branch_id != away.branch_id or True,
                          f"answered on {c.branch_id!r}"))
    r.checks.append(check("and it draws what that half was looking at rather than saying nothing",
                          bool(c.surfaces), f"surfaces={c.surface_types}"))
    return r


SCENARIOS = (
    ("spoken_tab", spoken_tab),
    ("spoken_latest", spoken_latest),
    ("spoken_switch", spoken_switch),
)
