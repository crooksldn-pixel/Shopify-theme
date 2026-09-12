"""The screen represents the TASK, not the last tool that returned (§3, §6, §12).

D-3, verbatim from `docs/phase5/LIVE_SESSION_FORENSICS.md`. Turn `turn_1e7f630eae7e`:

    "Pull up the history of [name] and his orders. See how many times he's ordered, see how
     much he's spent, and see if he's in Gmail anywhere."

    tools:   ['gmail_search']          ← the only NEW read
    renders: [['email_list'], ['email_list']]

The spoken answer was complete and correct — two orders, sixty pounds each, £120 lifetime. The
Mac held all of it. The screen showed an email list, because the presentation layer drew the
most recent tool result and nothing else.

The chain this file holds is the replacement:

    USER INTENT → DESIRED WORKSPACE → DATA REQUIREMENTS → HELD/CACHED/NEW READS
               → PROGRESSIVE WORKSPACE HYDRATION

A new read ENRICHES the workspace it belongs to. It never replaces it. An empty section is an
empty section (§27) and an error in one section never destroys the others.
"""

from __future__ import annotations

import json

from app import entities, workspace
from app.presentation import UI_TYPES, present
from app.providers.base import ToolCall
from app.session.models import Session
from app.tools import (
    shopify_tools,  # noqa: F401 — registers the specs the rails are built from
)

CUSTOMER = "gid://shopify/Customer/7"
ORDER_A = "gid://shopify/Order/1962"
ORDER_B = "gid://shopify/Order/1930"

D3 = ("Pull up the history of Daniel and his orders. See how many times he's ordered, "
      "see how much he's spent, and see if he's in Gmail anywhere.")

HISTORY = {
    "customer_id": CUSTOMER, "name": "Daniel Sear", "email": "daniel@example.com",
    "orders": 2, "spent": "120.00 GBP", "standing": "returning", "since": "2026-03-01",
    "last_order": {"order_id": ORDER_A, "order_number": "CROOKS-1962"},
    "recent": [
        {"order_id": ORDER_A, "order_number": "CROOKS-1962", "total": "60.00 GBP",
         "placed_at": "2026-09-01T10:00:00Z", "fulfillment": "FULFILLED", "payment": "PAID"},
        {"order_id": ORDER_B, "order_number": "CROOKS-1930", "total": "60.00 GBP",
         "placed_at": "2026-08-02T10:00:00Z", "fulfillment": "FULFILLED", "payment": "PAID"},
    ],
}
THREADS = {
    "query": "daniel@example.com",
    "threads": [{"thread_id": "t-1", "from": "Daniel Sear", "from_email": "daniel@example.com",
                 "subject": "Where is my order", "date": "Mon", "snippet": "Any news?"}],
}
ORDER_DETAIL = {
    "order_id": ORDER_A, "order_number": "CROOKS-1962", "placed_at": "2026-09-01T10:00:00Z",
    "fulfillment": "UNFULFILLED", "payment": "PAID", "total": "60.00 GBP",
    "customer_name": "Daniel Sear", "customer_id": CUSTOMER, "customer_email": "daniel@example.com",
    "items": [{"title": "Yard Jeans", "variant": "Blue Wash / M", "sku": "YJ-M", "quantity": 1,
               "total": "60.00 GBP"}],
    "items_truncated": False,
    "ships_to": "London, United Kingdom",
    "shipping_address_full": "12 Somewhere Street, E1 6AN",  # must never reach the screen
}


def ok(name: str, result: dict) -> ToolCall:
    return ToolCall(name=name, args={}, ok=True, result=result)


def bad(name: str, code: str = "gmail_error") -> ToolCall:
    return ToolCall(name=name, args={}, ok=False, error=code, result=None)


def types(items: list[dict]) -> list[str]:
    return [i["type"] for i in items]


def only(items: list[dict], kind: str) -> dict:
    found = [i for i in items if i["type"] == kind]
    assert len(found) == 1, f"expected exactly one {kind}, got {types(items)}"
    return found[0]["data"]


def session(said: str, sid: str = "ws") -> Session:
    live = Session(session_id=sid)
    live.heard = said
    return live


# --------------------------------------------------------------- D-3, the whole defect


def test_the_d3_request_renders_a_customer_workspace_not_an_email_list():
    """The turn from the timeline, with the history HELD from an earlier turn and Gmail the
    only new read. What was drawn was an email list, twice. What must be drawn is the
    customer."""
    live = session(D3, "d3")
    # Turn one: the owner asked about the customer, and the Mac read his history.
    present([ok("shopify_customer_history", HISTORY)], session=live)
    # Turn two: the D-3 question. gmail_search is the only NEW read.
    items = present([ok("gmail_search", THREADS)], session=live)

    assert "email_list" not in types(items), (
        "the last tool result became the screen again: " + str(types(items)))
    data = only(items, "customer_workspace")
    assert data["title"] == "Daniel Sear"
    # Everything the spoken answer got right is on the screen too.
    assert data["sections"]["orders"]["state"] == "ready"
    assert [r["order_number"] for r in data["sections"]["orders"]["rows"]] == ["#1962", "#1930"]
    assert any("120" in str(f["value"]) for f in data["header"]), data["header"]
    assert any("2" == str(f["value"]) for f in data["header"]), data["header"]
    # And the new read enriched the workspace's Inbox rather than becoming the screen.
    assert data["sections"]["inbox"]["state"] == "ready"
    assert [r["subject"] for r in data["sections"]["inbox"]["rows"]] == ["Where is my order"]


def test_the_same_request_in_one_turn_is_one_workspace_not_three_cards():
    """The same task when every read lands in the same turn: still one surface. §6's own
    words — `shopify_find_customer` → shell, `shopify_customer_history` → enrich .orders,
    `gmail_search` → enrich .email. NOT three cards."""
    items = present([
        ok("shopify_find_customer", {"query": "daniel", "customers": [
            {"customer_id": CUSTOMER, "name": "Daniel Sear", "email": "daniel@example.com",
             "orders": 2, "spent": "120.00 GBP"}]}),
        ok("shopify_customer_history", HISTORY),
        ok("gmail_search", THREADS),
    ], session=session(D3, "one-turn"))
    assert types(items).count("customer_workspace") == 1
    for gone in ("customer", "customer_list", "email_list"):
        assert gone not in types(items), f"{gone} is a second surface for the same person"


def test_ten_reads_touching_one_customer_produce_one_customer_surface():
    """His words, turn_541df4c7a2b6: "You just pulled up two in the same UI". Ten reads of one
    person are one person."""
    calls = []
    for _ in range(4):
        calls.append(ok("shopify_find_customer", {"query": "daniel", "customers": [
            {"customer_id": CUSTOMER, "name": "Daniel Sear", "email": "daniel@example.com",
             "orders": 2, "spent": "120.00 GBP"}]}))
        calls.append(ok("shopify_customer_history", HISTORY))
    calls.append(ok("gmail_search", THREADS))
    calls.append(ok("gmail_read_thread", {"thread_id": "t-1", "message_count": 1, "messages": [
        {"message_id": "m1", "from": "Daniel Sear", "from_email": "daniel@example.com",
         "subject": "Where is my order", "body": "Any news?", "date": "Mon"}]}))
    items = present(calls, session=session(D3, "ten"))
    surfaces = [t for t in types(items) if t in ("customer_workspace", "customer", "customer_list")]
    assert surfaces == ["customer_workspace"], types(items)


# ---------------------------------------------------------------- §27, empty and error


def test_an_empty_gmail_section_preserves_the_rest_of_the_workspace():
    """EMPTY IS NOT ERROR, and an empty read is not a reason to throw the workspace away.
    The Inbox section says "No messages found" and the customer stays on screen."""
    items = present([
        ok("shopify_customer_history", HISTORY),
        ok("gmail_search", {"query": "daniel@example.com", "threads": []}),
    ], session=session(D3, "empty"))
    data = only(items, "customer_workspace")
    inbox = data["sections"]["inbox"]
    assert inbox["state"] == "empty"
    assert "no messages found" in inbox["note"].lower(), inbox["note"]
    assert inbox["rows"] == []
    # Nothing else moved.
    assert data["title"] == "Daniel Sear"
    assert data["sections"]["orders"]["state"] == "ready"
    assert len(data["sections"]["orders"]["rows"]) == 2
    assert data["sections"]["overview"]["state"] == "ready"


def test_an_error_in_one_section_does_not_destroy_the_others():
    """Gmail fell over. The customer, his lifetime value and his two orders are all still
    known, so all of them are still on the screen; the Inbox says what went wrong."""
    items = present([
        ok("shopify_customer_history", HISTORY),
        bad("gmail_search"),
    ], session=session(D3, "err"))
    data = only(items, "customer_workspace")
    assert data["sections"]["inbox"]["state"] == "error"
    assert data["sections"]["inbox"]["note"], "an error section that says nothing is a blank region"
    assert data["sections"]["orders"]["state"] == "ready"
    assert len(data["sections"]["orders"]["rows"]) == 2
    assert data["sections"]["overview"]["state"] == "ready"
    assert data["title"] == "Daniel Sear"
    # The failed service still gets its own error card; that is what it always did.
    assert "error" in types(items)


def test_a_section_still_being_read_is_loading_and_not_empty():
    """Progressive hydration: a section whose read has not landed says so. Marking it empty
    would be a lie the owner acts on."""
    plan = workspace.desired(D3, graph=_graph_with_history("hydrate"))
    assert plan is not None
    built = workspace.compose(plan, graph=_graph_with_history("hydrate"), pending=("inbox",))
    inbox = built["data"]["sections"]["inbox"]
    assert inbox["state"] == "loading" and inbox["note"]
    assert built["data"]["sections"]["orders"]["state"] == "ready"


# ------------------------------------------------------------------- §26, first viewport


def test_a_customer_first_viewport_answers_the_three_questions():
    """WHAT IS THIS / WHAT MATTERS / WHAT CAN I DO, from the payload and before any tab is
    opened. The live session's customer card answered none of them: it opened on an empty
    Email panel."""
    items = present([ok("shopify_customer_history", HISTORY), ok("gmail_search", THREADS)],
                    session=session(D3, "viewport"))
    data = only(items, "customer_workspace")

    # WHAT IS THIS — identity, and whether this person is new or returning.
    assert data["title"] == "Daniel Sear"
    assert data["subtitle"] == "daniel@example.com"
    assert data["status"].lower() in ("returning", "regular", "first order", "new", "no orders yet")

    # WHAT MATTERS — lifetime value, order count and the last order, as facts, not prose.
    keys = {f["key"].lower(): str(f["value"]) for f in data["header"]}
    assert "lifetime" in keys and "120" in keys["lifetime"]
    assert "orders" in keys and keys["orders"] == "2"
    assert "last order" in keys and "#1962" in keys["last order"]

    # WHAT CAN I DO — at least one offer, each of them a real destination (§18).
    assert data["actions"], "a workspace with nothing to do is a picture"
    for action in data["actions"]:
        assert action["label"] and action["command"]
        assert action.get("enabled") is True or action.get("reason"), action


def test_an_order_first_viewport_leads_with_the_order_not_with_its_items():
    """§12's ORDER list: number, customer, value, payment, fulfilment, date, primary attention,
    primary next actions — before Items, Shipping, Customer or Email are opened."""
    items = present([ok("shopify_order_detail", ORDER_DETAIL)],
                    session=session("Pull up order 1962", "order-vp"))
    data = only(items, "order_workspace")
    assert data["title"] == "Order #1962"
    assert data["subtitle"] == "Daniel Sear"
    keys = {f["key"].lower(): str(f["value"]) for f in data["header"]}
    assert "60" in keys["value"]
    assert keys["payment"].lower() == "paid"
    assert keys["fulfilment"].lower() in ("unfulfilled", "not shipped", "to ship")
    assert keys["placed"]
    assert [s for s in data["sections"]] == list(workspace.SECTIONS["order"])
    assert data["sections"]["items"]["rows"][0]["title"] == "Yard Jeans"
    # The full street address is not an order fact the screen carries — it never was.
    assert "Somewhere Street" not in json.dumps(data)


# ------------------------------------------------------------------------- §26, no gids


def _display_strings(value, key: str = "", trail: str = "") -> list[tuple[str, str]]:
    """Every string in a payload that a renderer could print, with where it came from.

    A ref is not a display string: `ref`, `*_id` and `thread_id` are what a tap posts to
    `open.entity`, and they have to be the shop's own ids. Everything else is words a person
    reads.
    """
    out: list[tuple[str, str]] = []
    if isinstance(value, dict):
        for k, v in value.items():
            out += _display_strings(v, str(k), f"{trail}.{k}")
    elif isinstance(value, list):
        for n, v in enumerate(value):
            out += _display_strings(v, key, f"{trail}[{n}]")
    elif isinstance(value, str):
        if key not in workspace.REF_KEYS:
            out.append((trail, value))
    return out


def test_no_raw_gid_reaches_a_non_debug_surface():
    """§26: "Order #1962", never "gid://shopify/Order/…". The ids stay on the wire as refs,
    because a tap needs them; no field a renderer prints may carry one."""
    hostile = {
        # The worst case: a shop whose order_number IS the gid, and a customer with no name.
        "order_id": ORDER_A, "order_number": ORDER_A, "total": "60.00 GBP",
        "payment": "PAID", "fulfillment": "UNFULFILLED", "placed_at": "2026-09-01T10:00:00Z",
        "customer_id": CUSTOMER, "customer_name": "", "customer_email": "",
        "items": [{"title": "", "variant": "", "quantity": 1, "total": "60.00 GBP"}],
    }
    items = present([ok("shopify_order_detail", hostile)],
                    session=session("Pull up order 1962", "gids"))
    for item in items:
        for where, value in _display_strings(item["data"]):
            assert "gid://" not in value, f"{item['type']}{where} would print {value!r}"


def test_the_refs_are_still_there_for_a_tap():
    """The other half of the rule: hiding the id from the reader must not take away the
    destination. A row that names a record still carries the ref the tap posts."""
    items = present([ok("shopify_customer_history", HISTORY)], session=session(D3, "refs"))
    data = only(items, "customer_workspace")
    assert data["ref"] == CUSTOMER
    assert [r["order_id"] for r in data["sections"]["orders"]["rows"]] == [ORDER_A, ORDER_B]


# --------------------------------------------------------------------------- §18, no fake UI


def test_a_row_the_mac_cannot_open_is_drawn_disabled_with_a_reason():
    """§18: a visible interactive element must have a valid server-backed destination BEFORE
    it is shown. `turn_dd093f86b92d` posted `open.entity`, was refused `not_held`, and drew an
    empty half. A row whose ref this conversation was never issued is not tappable."""
    live = session(D3, "fake-ui")
    data = only(present([ok("shopify_customer_history", HISTORY)], session=live), "customer_workspace")
    for row in data["sections"]["orders"]["rows"]:
        assert row["open"] is True, row
        # And the Mac issued the ref, so `open.entity` will not refuse it.
        assert row["order_id"] in live.issued_ids

    # A row whose ref is not a shape the gate accepts is shown, and shown as unopenable.
    bare = {**HISTORY, "recent": [{**HISTORY["recent"][0], "order_id": ""}]}
    data = only(present([ok("shopify_customer_history", bare)], session=session(D3, "fake-ui-2")),
                "customer_workspace")
    row = data["sections"]["orders"]["rows"][0]
    assert row["open"] is False and row["open_note"], row


# ------------------------------------------------------- the tab the task implies (D-2)


def test_the_task_names_the_tab_it_implies_and_says_why():
    """D-2: every customer card in the live session opened on Email because the tab was a
    per-BRANCH value. The workspace names the tab the TASK implies and the reason for it.
    Where that state LIVES is workstream E's; naming it is this layer's.
    """
    orders = workspace.desired("Pull up his orders and his history", graph=_graph_with_history("tab-a"))
    assert orders.tab == "orders" and orders.tab_reason

    inbox = workspace.desired("Has Daniel emailed us about anything", graph=_graph_with_history("tab-b"))
    assert inbox.tab == "inbox"

    plain = workspace.desired("Pull up Daniel", graph=_graph_with_history("tab-c"))
    assert plain.tab == "overview", "a request that names nothing opens where the answers are"

    # And it is never a tab the workspace does not have.
    for plan in (orders, inbox, plain):
        assert plan.tab in workspace.SECTIONS[plan.kind]


def test_a_tab_with_nothing_behind_it_is_never_the_one_that_opens():
    """The live failure in one line: a request for orders and history landed on an empty
    Email panel. A tab whose section is empty cannot be the one the workspace opens on."""
    plan = workspace.desired("Has Daniel emailed us about anything", graph=_graph_with_history("tab-d"))
    assert plan.tab == "inbox"
    built = workspace.compose(plan, graph=_graph_with_history("tab-d"))
    data = built["data"]
    assert data["sections"]["inbox"]["state"] == "empty"
    assert data["tab"] != "inbox"
    assert data["sections"][data["tab"]]["state"] == "ready", data["tab"]


# --------------------------------------------------------------------------- the bounds


def test_the_workspace_types_are_in_the_vocabulary_on_both_sides():
    """The rule this repository has always kept: a card type is a hand-written renderer with
    its own bounds, named on both sides. `tests/test_web.py` holds the equality; this says
    which names this pass added."""
    import re
    from pathlib import Path

    for kind in ("customer_workspace", "order_workspace"):
        assert kind in UI_TYPES
    ui_js = (Path(__file__).resolve().parent.parent / "web" / "ui.js").read_text(encoding="utf-8")
    renderers = set(re.findall(r"^\s{4}(\w+): render\w+,$", ui_js, re.M))
    assert {"customer_workspace", "order_workspace"} <= renderers


def test_a_workspace_is_bounded():
    """Every list capped, every string truncated — the same two rules the rest of the
    vocabulary keeps. A workspace is a bigger card, not an unbounded one."""
    huge = {
        **HISTORY,
        "name": "N" * 500,
        "recent": [{"order_id": f"gid://shopify/Order/{n}", "order_number": f"CROOKS-{n}",
                    "total": "60.00 GBP", "placed_at": "2026-09-01T10:00:00Z",
                    "fulfillment": "FULFILLED", "payment": "PAID"} for n in range(80)],
    }
    many = {"query": "x", "threads": [
        {"thread_id": f"t-{n}", "from": "Daniel Sear", "from_email": "daniel@example.com",
         "subject": "S" * 400, "date": "Mon", "snippet": "z" * 900} for n in range(60)]}
    data = only(present([ok("shopify_customer_history", huge), ok("gmail_search", many)],
                        session=session(D3, "bounds")), "customer_workspace")
    assert len(data["title"]) <= workspace.MAX_TITLE_CHARS
    assert len(data["sections"]["orders"]["rows"]) <= workspace.MAX_ROWS
    assert len(data["sections"]["inbox"]["rows"]) <= workspace.MAX_ROWS
    assert len(data["header"]) <= workspace.MAX_HEADER_FACTS
    assert len(data["actions"]) <= workspace.MAX_ACTIONS
    for _where, value in _display_strings(data):
        assert len(value) <= workspace.MAX_VALUE_CHARS, _where


def test_a_workspace_needs_an_identity_before_it_is_drawn():
    """No identity, no workspace: the old cards are better than an empty header. A read that
    found nobody still says so, the way it always did."""
    items = present([ok("shopify_find_customer", {"query": "nobody", "customers": []})],
                    session=session("Pull up Nobody", "none"))
    assert "customer_workspace" not in types(items)
    assert types(items) == ["customer_list"] and items[0]["data"]["empty"] is True


def test_an_analytic_question_is_not_turned_into_an_entity_workspace():
    """§13 is workstream D's, and this layer must not take its surfaces. "How many returning
    customers today" is a summary question; a customer workspace is not the answer to it."""
    items = present([ok("shopify_customer_history", HISTORY)],
                    session=session("Has anyone bought today that has bought before, a returning customer?", "d4"))
    assert "customer_workspace" not in types(items), types(items)


def _graph_with_history(sid: str) -> entities.EntityGraph:
    g = entities.graph_for(Session(session_id=sid))
    g.ingest("shopify_customer_history", HISTORY)
    return g
