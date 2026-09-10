"""The golden scenarios: what the tablet is asked, and what must be true afterwards.

Each one drives real turns through the real runtime and then asserts. The assertions are
ordered the way the brief orders its oracle, and that order is load-bearing:

    1. structural   the right kind of surface exists, with the fields it must carry
    2. grounding    the values on it are the values the golden world holds
    3. mechanical   the thing can be tapped, walked, gone back from
    4. semantic     the words are reasonable

Only the first three appear here, because only the first three can be decided without an
opinion. A semantic grader can add to this and can never overturn it: a scenario that fails a
structural check has failed, whatever anything thinks of the prose.

The rule that gives this file its point is `prose_only`. A turn that answers a question about
an order and shows nothing is a failure even when the sentence is perfect and the answer
arrived in nine milliseconds — that combination is exactly what was reported from the tablet,
and it is what §29 of the brief requires a test to catch.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from experience.fixtures import data, world
from experience.harness import Harness

# What the fast lane should answer without waking the model at all.
DETERMINISTIC = frozenset({
    "capabilities", "order_lookup", "repeat_order", "today_orders", "full_address",
    "customer_history", "next_voice", "next_touch", "back", "tabs", "drilldown",
})


@dataclass
class Check:
    what: str
    ok: bool
    detail: str = ""

    def __bool__(self) -> bool:
        return self.ok


@dataclass
class Result:
    name: str
    title: str
    checks: list[Check] = field(default_factory=list)
    captures: list[Any] = field(default_factory=list)
    error: str = ""

    @property
    def status(self) -> str:
        if self.error:
            return "FAIL"
        if not self.checks:
            return "PARTIAL"
        if all(c.ok for c in self.checks):
            return "PASS"
        return "FAIL"

    @property
    def failures(self) -> list[Check]:
        return [c for c in self.checks if not c.ok]

    def as_dict(self) -> dict[str, Any]:
        return {
            "scenario": self.name, "title": self.title, "status": self.status,
            "error": self.error,
            "checks": [{"what": c.what, "ok": c.ok, "detail": c.detail} for c in self.checks],
            "captures": [c.as_dict() for c in self.captures],
        }


def check(what: str, ok: Any, detail: str = "") -> Check:
    return Check(what, bool(ok), detail)


# Scenarios that mean anything against a REAL shop. The others name a fixture record — order
# 1938, Mia Jones — and asserting those against the owner's own store would fail for the
# right reason and tell nobody anything. What a live run is for is the shapes: that a real
# order still produces an order surface with items and a rail, that a real inbox still
# correlates, that the cards fit real data.
LIVE_SCENARIOS: frozenset[str] = frozenset({
    "capabilities", "today_orders", "needs_reply", "next_previous", "back", "tabs",
})


def grounded(h: Harness) -> bool:
    """Whether the golden world's own values may be asserted. False against a real shop."""
    return not getattr(h, "live", False)


# --------------------------------------------------------------------------- shared assertions


def a_surface(capture: Any, ui_type: str, *, what: str = "") -> list[Check]:
    """The check this whole pass exists for: something to look at, of the right kind."""
    label = what or f"shows a {ui_type}"
    checks = [check(f"{label} rather than prose", not capture.prose_only,
                    f"surfaces={capture.surface_types} answer={capture.answer[:60]!r}")]
    checks.append(check(f"{label}", capture.surface(ui_type) is not None,
                        f"surfaces={capture.surface_types}"))
    return checks


def deterministic(capture: Any) -> Check:
    return check("answered without the model", capture.model_calls == 0,
                 f"model_calls={capture.model_calls}")


def entity_is(capture: Any, kind: str, ref: str = "") -> Check:
    got = capture.entity or {}
    ok = got.get("kind") == kind and (not ref or got.get("ref") == ref)
    return check(f"the current entity is the {kind}", ok, f"entity={got}")


# --------------------------------------------------------------------------- the scenarios


async def capabilities(h: Harness) -> Result:
    r = Result("capabilities", "What can you do now?")
    c = await h.say("what can you do now?", scenario="capabilities")
    r.captures.append(c)
    r.checks += a_surface(c, "capability", what="shows the capability surface")
    r.checks.append(deterministic(c))
    payload = c.data("capability")
    groups = payload.get("groups") or []
    r.checks.append(check("groups the capabilities by area", len(groups) >= 3,
                          f"groups={[g.get('area') for g in groups]}"))
    r.checks.append(check("says whether changes are on", "writes_enabled" in payload,
                          f"writes_enabled={payload.get('writes_enabled')}"))
    r.checks.append(check("offers things to ask", len(payload.get("examples") or []) >= 3))
    r.checks.append(check("the spoken answer is one line, not the list",
                          len(c.answer) < 400, f"{len(c.answer)} chars"))
    return r


def _money(value: Any) -> float | None:
    """A displayed amount as a number, or None when it is not one. Currency symbols, thousands
    separators and a stray minus all survive; anything else is not silently read as zero."""
    text = str(value or "").strip().replace(",", "")
    for symbol in ("£", "$", "€", "GBP", "USD", "EUR"):
        text = text.replace(symbol, "")
    text = text.strip()
    try:
        return float(text)
    except ValueError:
        return None


async def order_lookup(h: Harness) -> Result:
    """The regression the whole pass exists to prevent (brief §29).

    Every check here would have passed on the build that was reported as broken EXCEPT the
    ones about the surface, the items and the actions — the answer was fast and correct and
    there was nothing on the screen.
    """
    r = Result("order_lookup", "Show me order 1938")
    spec = world.order("1938")
    c = await h.say("show me order 1938", scenario="order_lookup")
    r.captures.append(c)
    r.checks += a_surface(c, "order", what="shows the order surface")
    r.checks.append(deterministic(c))
    r.checks.append(entity_is(c, "order", spec.order_id))
    card = c.data("order")
    r.checks.append(check("the card is the full order, not the brief one", card.get("detail") is True,
                          f"detail={card.get('detail')}"))
    r.checks.append(check("names the order", str(card.get("order_number")) == spec.name,
                          f"order_number={card.get('order_number')}"))
    r.checks.append(check("names the customer", str(card.get("customer_name")) == spec.person.name,
                          f"customer_name={card.get('customer_name')}"))
    # Not "the total is £84.00". The card's own arithmetic is the thing worth holding: the
    # fixture used to state a total that excluded the £5 of postage it also displayed, so every
    # order card read Subtotal £84.00 + Shipping £5.00 + Tax £0.00 = Total £84.00. A magic
    # number in a test cannot see that; a sum can.
    money = card.get("money") if isinstance(card.get("money"), dict) else {}
    parts = {k: _money(money.get(k)) for k in ("subtotal", "shipping", "tax")}
    total = _money(card.get("total"))
    r.checks.append(check("carries a total", total is not None, f"total={card.get('total')}"))
    r.checks.append(check(
        "and the money on it adds up",
        total is not None and all(v is not None for v in parts.values())
        and abs(sum(parts.values()) - total) < 0.005,
        f"{parts} -> {card.get('total')}"))
    r.checks.append(check("the goods come to what the items cost",
                          parts["subtotal"] is not None and abs(parts["subtotal"] - float(spec.total)) < 0.005,
                          f"subtotal={money.get('subtotal')} items={spec.total}"))
    items = card.get("items") or []
    r.checks.append(check("the items are reachable", len(items) == len(spec.items),
                          f"{len(items)} items, expected {len(spec.items)}"))
    if items:
        first = items[0]
        r.checks.append(check("an item carries its variant", bool(first.get("variant")),
                              f"variant={first.get('variant')!r}"))
        r.checks.append(check("an item carries its sku", bool(first.get("sku")),
                              f"sku={first.get('sku')!r}"))
    r.checks.append(check("offers actions for the order", len(c.action_ids) >= 3,
                          f"actions={c.action_ids}"))
    r.checks.append(check("offers a note", "order_note_append" in c.action_ids, f"actions={c.action_ids}"))
    r.checks.append(check("the spoken answer is short", len(c.answer) < 240, f"{len(c.answer)} chars"))
    r.checks.append(check("the spoken answer does not read the card out",
                          str(spec.address["zip"]) not in c.answer, "postcode spoken"))
    return r


async def repeat_order(h: Harness) -> Result:
    """"Show me 1938 again" — reported as staying text-heavy. It had no intent family at all."""
    r = Result("repeat_order", "Show me 1938 again")
    first = await h.say("show me order 1938", scenario="repeat_order:first")
    c = await h.say("show me 1938 again", scenario="repeat_order")
    r.captures += [first, c]
    r.checks += a_surface(c, "order", what="shows the order again")
    r.checks.append(deterministic(c))
    r.checks.append(check("takes the fast lane", c.lane == "FAST", f"lane={c.lane}"))
    r.checks.append(entity_is(c, "order", world.order("1938").order_id))
    r.checks.append(check("the repeat is not slower than the first",
                          (c.total_ms or 0) <= (first.total_ms or 0) + 50,
                          f"first={first.total_ms:.0f}ms repeat={c.total_ms:.0f}ms"))
    return r


async def today_orders(h: Harness) -> Result:
    r = Result("today_orders", "Show me today's orders")
    c = await h.say("show me today's orders", scenario="today_orders")
    r.captures.append(c)
    r.checks += a_surface(c, "order_list", what="shows the order list")
    r.checks.append(deterministic(c))
    card = c.data("order_list")
    rows = card.get("orders") or card.get("rows") or []
    r.checks.append(check("opens a set to walk", bool(c.set_id), f"set_id={c.set_id!r}"))
    r.checks.append(check("the spoken answer is short rather than a recital",
                          len(c.answer) < 200, f"{len(c.answer)} chars"))
    if grounded(h):
        expected = world.today()
        r.checks.append(check("lists today's orders", len(rows) == len(expected),
                              f"{len(rows)} rows, expected {len(expected)} ({[o.name for o in expected]})"))
        r.checks.append(check("counts them in the spoken answer", str(len(expected)) in c.answer,
                              c.answer[:80]))
    else:
        # A real shop may genuinely have had no orders today. What is being checked live is
        # that the surface and the set exist, not how many rows are in them.
        r.checks.append(check("the rows are shaped like orders",
                              all(isinstance(x, dict) for x in rows), f"{len(rows)} rows"))
    return r


async def next_and_previous(h: Harness) -> Result:
    """Voice and touch on the same cursor (brief §13 and §16)."""
    r = Result("next_previous", "Next, said and tapped")
    listing = await h.say("show me today's orders", scenario="next:list", session_id="cursor")
    v = await h.say("next", scenario="next:voice", session_id="cursor")
    t = await h.touch("workflow.next", scenario="next:touch", session_id="cursor")
    p = await h.touch("workflow.previous", scenario="previous:touch", session_id="cursor")
    r.captures += [listing, v, t, p]
    r.checks.append(check("the list opened a set", bool(listing.set_id), f"set_id={listing.set_id!r}"))
    r.checks += a_surface(v, "order", what="saying next opens the member")
    r.checks += a_surface(t, "order", what="tapping next opens the member")
    r.checks.append(deterministic(v))
    r.checks.append(deterministic(t))
    r.checks.append(check("the cursor moved once per step, whichever way it was asked",
                          "1 of" in v.answer and "2 of" in t.answer,
                          f"voice={v.answer!r} touch={t.answer!r}"))
    r.checks.append(check("previous goes back one", "1 of" in p.answer, f"previous={p.answer!r}"))
    r.checks.append(check("voice and touch walk the same set",
                          v.set_id == t.set_id == listing.set_id,
                          f"{listing.set_id} / {v.set_id} / {t.set_id}"))
    return r


async def back_navigation(h: Harness) -> Result:
    """Several levels deep, then back out, deterministically (brief §15)."""
    r = Result("back", "Back, more than once")
    one = await h.say("show me order 1938", scenario="back:1", session_id="nav")
    two = await h.say("show me order 1936", scenario="back:2", session_id="nav")
    b1 = await h.touch("navigation.back", scenario="back:tap1", session_id="nav")
    b2 = await h.touch("navigation.back", scenario="back:tap2", session_id="nav")
    r.captures += [one, two, b1, b2]
    r.checks.append(check("the second order opened", (two.entity or {}).get("ref") == world.order("1936").order_id,
                          f"entity={two.entity}"))
    r.checks += a_surface(b1, "order", what="back redraws the record it lands on")
    r.checks.append(deterministic(b1))
    r.checks.append(check("back lands on the first order",
                          (b1.entity or {}).get("ref") == world.order("1938").order_id,
                          f"entity={b1.entity}"))
    r.checks.append(check("back again reports the end rather than inventing one",
                          b2.raw.get("ok") is not False or "as far back" in b2.answer,
                          f"answer={b2.answer!r}"))
    return r


async def tabs_and_drilldown(h: Harness) -> Result:
    r = Result("tabs", "Shipping, said and tapped")
    await h.say("show me order 1938", scenario="tabs:open", session_id="tabs")
    tapped = await h.touch("surface.tab", surface="order", tab="shipping",
                           scenario="tabs:tap", session_id="tabs")
    spoken = await h.touch("order.open_shipping", scenario="tabs:spoken_equivalent", session_id="tabs")
    bad = await h.touch("surface.tab", surface="order", tab="nonsense",
                        scenario="tabs:unknown", session_id="tabs")
    r.captures += [tapped, spoken, bad]
    r.checks.append(check("tapping a tab records it as state",
                          (tapped.raw.get("changed") or {}).get("tab") == "shipping",
                          f"changed={tapped.raw.get('changed')}"))
    r.checks.append(check("the spoken shortcut reaches the same tab",
                          (spoken.raw.get("changed") or {}).get("tab") == "shipping",
                          f"changed={spoken.raw.get('changed')}"))
    r.checks.append(check("an unknown tab is refused, not guessed",
                          bad.raw.get("ok") is False and bad.raw.get("code") == "unknown_tab",
                          f"raw={ {k: bad.raw.get(k) for k in ('ok', 'code')} }"))
    r.checks.append(deterministic(tapped))
    return r


async def full_address(h: Harness) -> Result:
    r = Result("full_address", "Read me the full shipping address")
    spec = world.order("1938")
    await h.say("show me order 1938", scenario="address:open", session_id="addr")
    c = await h.say("read me the full shipping address", scenario="full_address", session_id="addr")
    r.captures.append(c)
    r.checks += a_surface(c, "order", what="shows the order with its address")
    r.checks.append(deterministic(c))
    card = c.data("order")
    address = card.get("shipping_address") or {}
    lines = " ".join(str(x) for x in (address.get("lines") or []))
    r.checks.append(check("the card carries the street", spec.address["address1"] in lines,
                          f"lines={address.get('lines')}"))
    r.checks.append(check("the card carries the postcode", address.get("zip") == spec.address["zip"],
                          f"zip={address.get('zip')}"))
    r.checks.append(check("the address was asked for, so it is spoken",
                          spec.address["zip"].split()[0].lower() in c.answer.lower().replace(" ", " "),
                          f"answer={c.answer[:120]!r}"))
    return r


async def customer_history(h: Harness) -> Result:
    r = Result("customer_history", "What else has this customer ordered?")
    await h.say("show me order 1938", scenario="history:open", session_id="hist")
    c = await h.say("what else has this customer ordered?", scenario="customer_history", session_id="hist")
    r.captures.append(c)
    r.checks += a_surface(c, "customer", what="shows the customer surface")
    r.checks.append(deterministic(c))
    card = c.data("customer")
    mine = world.orders_of(data.MIA)
    # The customer card nests the trading history under `history` — see _history() in
    # app/presentation.py. Reading it from the top level found nothing and said so, which is
    # the assertion being wrong rather than the card.
    history = card.get("history") if isinstance(card.get("history"), dict) else {}
    r.checks.append(check("names the customer",
                          data.MIA.name in (str(card.get("name") or ""), str(history.get("name") or "")),
                          f"name={card.get('name')!r} history.name={history.get('name')!r}"))
    r.checks.append(check("counts their orders",
                          (card.get("orders") or history.get("orders")) == len(mine),
                          f"orders={card.get('orders') or history.get('orders')}, expected {len(mine)}"))
    recent = history.get("recent") or card.get("recent") or []
    r.checks.append(check("lists what they bought before", len(recent) >= 2,
                          f"recent={[o.get('order_number') for o in recent]}"))
    return r


async def needs_reply(h: Harness) -> Result:
    r = Result("needs_reply", "Which customers need replying to?")
    c = await h.say("which customers need replying to?", scenario="needs_reply")
    r.captures.append(c)
    r.checks.append(check("shows something rather than prose", not c.prose_only,
                          f"surfaces={c.surface_types}"))
    r.checks.append(deterministic(c))
    expected = world.needs_reply()
    answered = [t for t in world.threads if t not in expected]
    r.checks.append(check("the golden world has both kinds to tell apart",
                          bool(expected) and bool(answered),
                          f"{len(expected)} waiting, {len(answered)} not"))
    body = " ".join(str(item.get("data")) for item in c.surfaces)

    # The answer itself, against the world's own arithmetic. Until now this scenario checked
    # only that a card was drawn and that the newsletter sender was absent from it — both of
    # which are trivially true of a card offering NOBODY, which is what it was drawing: the
    # fake inbox could not parse the correlation query, so every customer came back "emailed
    # us: no" and the assistant said "Nobody is waiting on a reply" in a world with three
    # people waiting. A scenario that cannot tell that apart from the right answer is not a
    # test of this question.
    waiting = {p.name for p in world.people.values()
               if any(p.email in max(t.messages, key=lambda m: (-m.days_ago, m.hour)).sender
                      for t in expected)}
    # In the ANSWER as well as on the card. The card's table lists every customer whatever
    # their state, so "the name appears somewhere in the payload" is true even when the
    # assistant said nobody was waiting — which is how this passed while being wrong.
    named = {name for name in waiting if name in c.answer}
    on_card = {name for name in waiting if name in body}
    r.checks.append(check("everyone the world says is waiting is named as waiting",
                          named == waiting, f"named={sorted(named)} expected={sorted(waiting)}"))
    r.checks.append(check("and each of them is on the card to act on",
                          on_card == waiting, f"on_card={sorted(on_card)}"))
    # On the SPOKEN answer, not the card. The card's table is "who has written" and rightly
    # lists everyone with their state — David Randall belongs on it, marked as replied to.
    # What must not happen is his being named as someone still waiting.
    replied_to = {p.name for p in world.people.values() if p.name not in waiting}
    wrongly = {name for name in replied_to if name and name in c.answer}
    r.checks.append(check("and nobody we have already answered is named as waiting",
                          not wrongly, f"named anyway: {sorted(wrongly)}"))
    r.checks.append(check("the spoken answer counts them rather than reading them all out",
                          str(len(waiting)) in c.answer and len(c.answer) < 200,
                          f"answer={c.answer[:90]!r}"))
    r.checks.append(check("the automated sender is not offered as a customer",
                          data.NEWSLETTER_SENDER not in body, "newsletter sender present"))
    return r


async def house_number(h: Harness) -> Result:
    """The question that used to be answered with one order's shipping address."""
    r = Result("house_number", "Did any of these customers email their house number?")
    c = await h.say("check whether any of these customers emailed us their house number",
                    scenario="house_number")
    r.captures.append(c)
    r.checks.append(check("does not answer it as one order's address",
                          c.recipe_id != "order_address_lookup",
                          f"recipe={c.recipe_id!r} lane={c.lane}"))
    r.checks.append(check("is treated as a sweep rather than a quick lookup",
                          c.lane in ("DEEP", "NORMAL"), f"lane={c.lane}"))
    r.checks.append(check("the golden world has a house number in the inbox and not on the order",
                          not data.BY_NAME["#1936"].address["address1"][0].isdigit()
                          and any("41" in m.body for t in world.threads for m in t.messages),
                          "fixture does not set the case up"))
    return r


async def unsupported_edit(h: Harness) -> Result:
    """It must never claim to have done what it cannot do (brief §30)."""
    r = Result("unsupported_edit", "Add a hoodie to this order")
    await h.say("show me order 1938", scenario="unsupported:open", session_id="unsup")
    c = await h.say("add a Black Convict hoodie to this order", scenario="unsupported_edit",
                    session_id="unsup")
    r.captures.append(c)
    r.checks.append(check("does not take the fast lane", c.lane != "FAST", f"lane={c.lane}"))
    r.checks.append(check("nothing was changed in the shop", getattr(h.store, "mutations_sent", -1) == 0,
                          f"mutations_sent={getattr(h.store, 'mutations_sent', 'NO COUNTER')}"))
    claimed = any(word in c.answer.lower() for word in ("added", "i've added", "done", "updated the order"))
    r.checks.append(check("does not claim to have added it", not claimed, f"answer={c.answer[:120]!r}"))
    r.checks.append(check("no success card was drawn", c.surface("success") is None,
                          f"surfaces={c.surface_types}"))
    return r


async def linked_entities(h: Harness) -> Result:
    """An order names its customer, and the customer can be opened from it (brief §11)."""
    r = Result("linked_entities", "From the order to the customer")
    c = await h.say("show me order 1938", scenario="linked:open", session_id="link")
    card = c.data("order")
    customer_id = str(card.get("customer_id") or "")
    r.captures.append(c)
    r.checks.append(check("the order names its customer by id", bool(customer_id),
                          f"customer_id={customer_id!r}"))
    # Reading the customer is what puts them in memory; opening a link never reads the shop.
    await h.say("what else has this customer ordered?", scenario="linked:read", session_id="link")
    opened = await h.touch("open.entity", kind="customer", ref=customer_id, label=data.MIA.name,
                           scenario="linked:tap", session_id="link")
    r.captures.append(opened)
    r.checks += a_surface(opened, "customer", what="tapping the link opens the customer")
    r.checks.append(deterministic(opened))
    r.checks.append(check("the branch followed the link",
                          (opened.entity or {}).get("ref") == customer_id, f"entity={opened.entity}"))
    missing = await h.touch("open.entity", kind="order", ref="gid://shopify/Order/999999",
                            scenario="linked:missing", session_id="link")
    r.captures.append(missing)
    r.checks.append(check("a record the Mac no longer holds is refused, not half-drawn",
                          missing.raw.get("ok") is False, f"raw={ {k: missing.raw.get(k) for k in ('ok','code')} }"))
    return r


async def split_branches(h: Harness) -> Result:
    """Two halves of the orb keep their own entity (brief §21)."""
    r = Result("split_branches", "Two halves, two records")
    session = "split"
    left = await h.say("show me order 1938", scenario="split:left", session_id=session)
    fork = await h.client.post("/branches/fork", data={"session_id": session, "label": "right"},
                               headers={"Tailscale-User-Login": "owner@example.com",
                                        "X-Forwarded-For": "100.64.0.9"})
    body = fork.json() if fork.content else {}
    right_id = str(((body.get("branch") or {}).get("branch_id")) or body.get("branch_id") or "")
    r.checks.append(check("a second half was opened", bool(right_id), f"fork={str(body)[:140]}"))
    if not right_id:
        return r
    right = await h.say("show me order 1936", scenario="split:right", session_id=session,
                        branch_id=right_id)
    r.captures += [left, right]
    left_branch = h.branch(session, left.branch_id)
    right_branch = h.branch(session, right_id)
    r.checks.append(check("the two halves hold different records",
                          (left_branch.entity or {}).get("ref") != (right_branch.entity or {}).get("ref"),
                          f"left={left_branch.entity} right={right_branch.entity}"))
    r.checks.append(check("the first half still holds the order it was left on",
                          (left_branch.entity or {}).get("ref") == world.order("1938").order_id,
                          f"left={left_branch.entity}"))
    r.checks.append(check("the second half holds its own",
                          (right_branch.entity or {}).get("ref") == world.order("1936").order_id,
                          f"right={right_branch.entity}"))
    return r


async def progressive_enrichment(h: Harness) -> Result:
    """The order goes up before the inbox has answered (brief §8)."""
    r = Result("enrichment", "The card first, the inbox after")
    c = await h.say("show me order 1938", scenario="enrichment")
    r.captures.append(c)
    r.checks += a_surface(c, "order", what="the order surface arrives with the turn")
    card = c.data("order")
    order_id = str(card.get("order_id") or "")
    r.checks.append(check("the core of the order is there at once",
                          bool(card.get("order_number")) and bool(card.get("items")),
                          f"items={len(card.get('items') or [])}"))
    if order_id:
        ms, extension = await h.enrich(order_id)
        c.enrichment_ms = round(ms, 1)
        r.checks.append(check("the rest is collected separately", isinstance(extension, dict),
                              f"enrichment={ms:.0f}ms keys={sorted(extension)[:6]}"))
        # Three numbers that have to be three numbers. This check used to be
        # `c.first_ui_ms is not None`, which restated the surface check eleven lines above and
        # could not fail — because first_ui_ms WAS total_ms, assigned from the same variable.
        r.checks.append(check("the card, the round trip and the enrichment are three measurements",
                              c.first_ui_ms is not None and c.first_ui_ms < c.total_ms
                              and c.enrichment_ms is not None,
                              f"card={c.first_ui_ms}ms round_trip={c.total_ms:.1f}ms enrichment={c.enrichment_ms}ms"))
    return r


SCENARIOS: tuple[tuple[str, Callable[[Harness], Awaitable[Result]]], ...] = (
    ("capabilities", capabilities),
    ("order_lookup", order_lookup),
    ("repeat_order", repeat_order),
    ("today_orders", today_orders),
    ("next_previous", next_and_previous),
    ("back", back_navigation),
    ("tabs", tabs_and_drilldown),
    ("full_address", full_address),
    ("customer_history", customer_history),
    ("needs_reply", needs_reply),
    ("house_number", house_number),
    ("linked_entities", linked_entities),
    ("unsupported_edit", unsupported_edit),
    ("split_branches", split_branches),
    ("enrichment", progressive_enrichment),
)

BY_NAME = dict(SCENARIOS)


async def run_all(h: Harness, only: str = "") -> list[Result]:
    """Every scenario, or one by name. A scenario that raises is a FAIL with its reason, never
    an exception that stops the rest of the run from being reported.

    A live run is narrowed to LIVE_SCENARIOS: the rest name a fixture record and would fail
    against the owner's own shop for a reason that says nothing about the code.
    """
    chosen = [(n, fn) for n, fn in SCENARIOS if not only or n == only]
    if getattr(h, "live", False):
        chosen = [(n, fn) for n, fn in chosen if n in LIVE_SCENARIOS]
    out: list[Result] = []
    for name, fn in chosen:
        try:
            out.append(await fn(h))
        except Exception as exc:  # noqa: BLE001 — one broken scenario must not hide the others
            out.append(Result(name, name, error=f"{type(exc).__name__}: {exc}"))
    return out
