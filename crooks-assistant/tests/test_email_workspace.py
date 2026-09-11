"""The email workspace, the rail that leads into it, and the typing path (§19, §20, §22).

Two defects from the live session are the subject of this file.

**D-11.** Eight rail actions rendered enabled — reply ×24, email_archive ×24, note ×5,
refund ×3, email ×3, fulfil ×2, address ×2, cancel ×2 — and not one was used. The rail was a
capability list: Note first on every order whatever the order was, Reply a chip that only put
words in the owner's mouth, and a disabled Fulfil beside an enabled Refund at the same visual
weight. So every enabled chip here must have a CLICK PATH — a command it posts, a change it
prepares, or a microphone it arms — every disabled one a reason, and the order of them must
come from the entity's own state.

**D-9.** "How do I type a separate hall for you?" The composer had fields and nothing led to
them. Reply now OPENS one: the tap posts `compose.reply` with a thread id and nothing else,
the Mac reads the thread it already holds, and the card that comes back has the words of the
reply on it as an editable field. The recipient is not editable and not posted — a reply's
recipient is re-read from the thread by the write tool, as it always was.
"""

from __future__ import annotations

import time

import pytest

from app.actions.available import available_actions, available_email_actions
from app.families import compose as family
from app.session.branch import Branch
from app.session.models import Session

READY = {"state": "ready", "detail": "ready", "scope": "write_orders"}
ORDER_CAPS = {op: READY for op in (
    "order_note_append", "order_cancel", "order_shipping_address_set", "refund_create",
    "fulfillment_create", "gmail_draft_new",
)}
EMAIL_CAPS = {"gmail_draft_reply": READY, "gmail_thread_archive": READY}

OPEN_ORDER = {
    "order_number": "CROOKS-1938", "fulfillment": "UNFULFILLED", "payment": "PAID",
    "total": "60.00 GBP", "refundable": True,
    "money": {"refunded": "0.00 GBP", "total": "60.00 GBP"}, "customer_email": "d@example.com",
    "shipping_address": {"lines": ["12 Somewhere Street"], "city": "Windsor"},
    "items": [{"unfulfilled_quantity": 1}], "fulfillments": [],
}
SHIPPED_ORDER = dict(
    OPEN_ORDER, fulfillment="FULFILLED", items=[{"unfulfilled_quantity": 0}],
    fulfillments=[{"status": "SUCCESS"}],
)
THREAD_ID = "aa70d3f83dbef06e"
ARCHIVE_ROW = [{
    "id": "email_archive", "label": "Archive", "operation": "gmail_thread_archive",
    "risk": "amber", "enabled": True, "reason": "", "detail": "Takes the thread out of the inbox.",
    "mode": "stage",
}]


@pytest.fixture
def branch() -> Branch:
    return Branch(branch_id="br_email", session_id="s_email")


@pytest.fixture
def session() -> Session:
    return Session(session_id="s_email")


def _ctx(session, branch, **args):
    from app.commands import Ctx

    return Ctx(None, session, branch, args)


def _hold_thread(session, *, thread_id: str = THREAD_ID, messages=None) -> None:
    """The thread as the Mac holds it after `gmail_read_thread` — the only place a reply's
    recipient may come from, and the reason the tablet posts a thread id and nothing else."""
    from app.memory import ENTITY
    from app.memory import current as memory

    memory().put(ENTITY, f"email_thread:{thread_id}", {
        "thread_id": thread_id,
        "message_count": 2,
        "messages": messages if messages is not None else [
            {"from": "Crooks", "from_email": "orders@crooksldn.com", "subject": "Order 1938",
             "body": "Thanks for your order.", "date": "Mon, 8 Sep 2026 09:00:00 +0100", "outbound": True},
            {"from": "Mia Fenwick", "from_email": "mia@example.com", "subject": "Re: Order 1938",
             "body": "Can I change the size?", "date": "Mon, 8 Sep 2026 11:00:00 +0100"},
        ],
    }, source="gmail")
    session.issue(thread_id)


# --------------------------------------------------------------------- §22 · the rail


def test_the_thread_rail_leads_with_a_reply_that_opens_a_typing_path():
    """The one chip the owner reached for twenty-four times and never used. It must open the
    composer, not ask him to talk."""
    rail = available_email_actions({"thread_id": THREAD_ID}, EMAIL_CAPS, row_actions=list(ARCHIVE_ROW))
    reply = next(a for a in rail if a["id"] == "reply")
    assert reply["mode"] == "open", "a tap must reach a screen, not prime a sentence"
    assert reply["command"] == "compose.reply"
    assert reply["args"] == f"thread_id={THREAD_ID}"
    assert reply["priority"] == "primary"
    # And the microphone is still offered, because dictating a long reply is faster than
    # typing one. It is the composer's own control, not the thing that Reply does.
    assert reply["family"] == "email.reply"


def test_a_thread_the_mac_cannot_name_gets_no_rail():
    assert available_email_actions({"thread_id": ""}, EMAIL_CAPS, row_actions=list(ARCHIVE_ROW)) == []


@pytest.mark.parametrize("order", [OPEN_ORDER, SHIPPED_ORDER,
                                   dict(OPEN_ORDER, cancelled_at="2026-09-08T10:00:00Z"),
                                   dict(OPEN_ORDER, payment="PENDING", refundable=False)])
def test_every_enabled_chip_on_an_order_has_a_click_path(order):
    """§22: an enabled action with no click path is furniture. Three kinds are allowed, and
    nothing else: a command it posts, a change it prepares, or a microphone it arms."""
    for action in available_actions(order, ORDER_CAPS):
        if not action["enabled"]:
            continue
        mode = action["mode"]
        assert mode in ("ask", "stage", "open"), action
        if mode == "open":
            assert action["command"] and action["args"], action
        elif mode == "ask":
            assert action["instruction"], action
            assert action["family"], f"{action['id']} arms nothing, so a tap says nothing"


def test_every_enabled_chip_on_a_thread_has_a_click_path():
    for action in available_email_actions({"thread_id": THREAD_ID}, EMAIL_CAPS, row_actions=list(ARCHIVE_ROW)):
        if not action["enabled"]:
            continue
        assert action["mode"] in ("ask", "stage", "open"), action
        if action["mode"] == "open":
            assert action["command"] and action["args"], action


@pytest.mark.parametrize("order", [OPEN_ORDER, SHIPPED_ORDER,
                                   dict(OPEN_ORDER, cancelled_at="2026-09-08T10:00:00Z"),
                                   dict(OPEN_ORDER, payment="PENDING", refundable=False)])
def test_every_disabled_chip_carries_a_reason_and_never_the_first_weight(order):
    for action in available_actions(order, ORDER_CAPS):
        if action["enabled"]:
            continue
        assert action["reason"], action
        assert len(action["reason"]) <= 40, "concise, on an eight-inch screen"
        assert action["priority"] == "secondary", "a dead chip must not sit beside a live one"


def test_the_note_chip_is_no_longer_the_first_thing_on_every_order():
    """Note was rendered on every order card, first, and used nought times out of five. It is
    a fallback, so it goes behind the disclosure and what the order NEEDS leads."""
    actions = available_actions(OPEN_ORDER, ORDER_CAPS)
    by_id = {a["id"]: a for a in actions}
    assert by_id["note"]["priority"] == "secondary"
    primary = [a["id"] for a in actions if a["enabled"] and a["priority"] == "primary"]
    assert primary and primary[0] == "fulfil", f"an unfulfilled paid order needs shipping: {primary}"
    assert len(primary) <= 2, f"two chips at full weight, not a menu: {primary}"


def test_a_customer_asking_for_a_refund_makes_refund_and_email_the_primary_pair():
    asking = dict(SHIPPED_ORDER, email={"threads": [{
        "thread_id": THREAD_ID, "sender_match": True, "subject": "Refund please",
        "snippet": "I would like a refund for this.",
    }]})
    primary = [a["id"] for a in available_actions(asking, ORDER_CAPS)
               if a["enabled"] and a["priority"] == "primary"]
    assert primary == ["refund", "email"], primary


def test_a_shipped_order_does_not_show_a_dead_fulfil_beside_a_live_refund():
    actions = available_actions(SHIPPED_ORDER, ORDER_CAPS)
    weights = {a["id"]: a["priority"] for a in actions}
    assert weights["refund"] == "primary"
    assert weights.get("fulfil") == "secondary"
    assert next(a for a in actions if a["id"] == "fulfil")["reason"] == "already shipped"


def test_the_presenter_carries_the_click_path_and_the_weight_to_the_tablet():
    from app.presentation import _actions, _email_actions

    order = _actions(OPEN_ORDER, ORDER_CAPS)
    assert order and all({"command", "args", "priority"} <= set(a) for a in order)
    thread = _email_actions({"thread_id": THREAD_ID}, EMAIL_CAPS, list(ARCHIVE_ROW))
    reply = next(a for a in thread if a["id"] == "reply")
    assert (reply["command"], reply["args"]) == ("compose.reply", f"thread_id={THREAD_ID}")
    assert reply["priority"] == "primary"


# ------------------------------------------------------- §19 · the reply, opened by a tap


def test_reply_opens_a_composer_from_the_thread_the_mac_holds(branch, session):
    from app import commands

    _hold_thread(session)
    out = commands.run("compose.reply", _ctx(session, branch, thread_id=THREAD_ID))
    assert out.ok, out.detail
    data = out.surfaces[0].as_ui()["data"]
    assert data["kind"] == "reply"
    assert data["thread_id"] == THREAD_ID
    # Who you are replying to, on the card, before a word is typed.
    assert data["to"]["value"] == "mia@example.com"
    assert data["to"]["editable"] is False
    assert data["to_name"] == "Mia Fenwick"
    assert data["subject"]["value"] == "Re: Order 1938"
    assert data["subject"]["editable"] is False
    assert data["body"]["editable"] is True
    assert branch.compose["thread_id"] == THREAD_ID


def test_reply_names_the_last_person_who_wrote_in_rather_than_the_shop(branch, session):
    """The shop's own outbound message is the newest one in the thread. Replying to ourselves
    is the bug this guards."""
    from app import commands

    _hold_thread(session, messages=[
        {"from": "Mia Fenwick", "from_email": "mia@example.com", "subject": "Order 1938", "body": "Can I change the size?"},
        {"from": "Crooks", "from_email": "orders@crooksldn.com", "subject": "Re: Order 1938",
         "body": "Which size?", "outbound": True},
    ])
    out = commands.run("compose.reply", _ctx(session, branch, thread_id=THREAD_ID))
    assert out.ok and out.surfaces[0].as_ui()["data"]["to"]["value"] == "mia@example.com"


def test_the_tablet_cannot_open_a_reply_to_a_thread_it_was_never_given(branch, session):
    from app import commands

    from app.memory import ENTITY
    from app.memory import current as memory

    memory().put(ENTITY, "email_thread:ffffffffffffffff", {"thread_id": "ffffffffffffffff", "messages": [
        {"from": "Someone", "from_email": "someone@example.com", "subject": "Private"},
    ]}, source="gmail")
    out = commands.run("compose.reply", _ctx(session, branch, thread_id="ffffffffffffffff"))
    assert not out.ok and out.code == "not_this_conversation"
    assert branch.compose is None


def test_a_thread_the_mac_no_longer_holds_says_so_rather_than_opening_an_empty_reply(branch, session):
    from app import commands

    session.issue("bbbbbbbbbbbbbbbb")
    out = commands.run("compose.reply", _ctx(session, branch, thread_id="bbbbbbbbbbbbbbbb"))
    assert not out.ok and out.code == "thread_not_held"
    assert "open" in out.detail.lower()


def test_the_reply_that_is_staged_is_built_from_the_macs_copy_only(branch, session):
    from app import commands

    _hold_thread(session)
    commands.run("compose.reply", _ctx(session, branch, thread_id=THREAD_ID))
    compose_id = branch.compose["compose_id"]
    typed = commands.run("compose.field", _ctx(session, branch, compose_id=compose_id,
                                               field="body", value="A large is on its way."))
    assert typed.ok
    out = commands.run("compose.stage", _ctx(session, branch, compose_id=compose_id, mode="send"))
    assert out.ok, out.detail
    staged = out.changed["stage"]
    assert staged["tool"] == "gmail_send_reply"
    assert staged["args"] == {"thread_id": THREAD_ID, "body": "A large is on its way."}
    assert "to" not in staged["args"], "a reply's recipient is the thread's, read afresh"


def test_a_reply_cannot_have_its_recipient_or_subject_typed(branch, session):
    """The fields the card shows read-only are refused on the wire too. A closed set is only
    closed if the Mac enforces it."""
    from app import commands

    _hold_thread(session)
    commands.run("compose.reply", _ctx(session, branch, thread_id=THREAD_ID))
    compose_id = branch.compose["compose_id"]
    for field in ("to", "subject", "to_name"):
        out = commands.run("compose.field", _ctx(session, branch, compose_id=compose_id,
                                                 field=field, value="somebody@example.com"))
        assert not out.ok and out.code == "not_editable", field
    assert branch.compose["to"] == "mia@example.com"


def test_an_empty_reply_is_refused_in_words_rather_than_silently(branch, session):
    from app import commands

    _hold_thread(session)
    commands.run("compose.reply", _ctx(session, branch, thread_id=THREAD_ID))
    out = commands.run("compose.stage", _ctx(session, branch, compose_id=branch.compose["compose_id"], mode="send"))
    assert not out.ok and out.code == "not_ready" and out.detail


def test_the_reply_composer_offers_type_dictate_rewrite_cancel_and_two_ways_out(branch, session):
    from app import commands

    _hold_thread(session)
    out = commands.run("compose.reply", _ctx(session, branch, thread_id=THREAD_ID))
    actions = {a["id"]: a for a in out.surfaces[0].as_ui()["data"]["actions"]}
    assert {"save_draft", "send", "discard", "dictate"} <= set(actions)
    assert actions["dictate"]["command"] == "voice.bind"
    assert f"ref={THREAD_ID}" in actions["dictate"]["args"]
    assert "family=email.reply" in actions["dictate"]["args"]
    assert actions["send"]["command"] == "compose.stage"
    assert actions["discard"]["command"] == "compose.discard"


def test_opening_a_reply_leaves_the_thread_as_where_the_owner_is(branch, session):
    """Back has to come back to the thread, not to whatever was on screen before it."""
    from app import commands

    _hold_thread(session)
    commands.run("compose.reply", _ctx(session, branch, thread_id=THREAD_ID))
    assert (branch.entity or {}).get("kind") == "email_thread"
    assert (branch.entity or {}).get("ref") == THREAD_ID


def test_a_reply_composer_is_not_a_read_and_asks_gmail_for_nothing(branch, session):
    from app import commands

    _hold_thread(session)
    out = commands.run("compose.reply", _ctx(session, branch, thread_id=THREAD_ID))
    assert out.calls == [], "the thread is already on the Mac; a tap must not re-read it"
    assert "stage" not in out.changed, "opening a composer prepares nothing"


# --------------------------------------------------- §19 · archive, proven and out of the queue


def _proposal(*, operation: str, entity_kind: str, entity_ref: str, undo: bool = False):
    from types import MappingProxyType

    from app.actions.models import ActionProposal, ActionStatus

    return ActionProposal(
        proposal_id="prop_arch", session_id="s_email", epoch=1, tool_name=operation,
        operation=operation, risk="AMBER", model_args=MappingProxyType({}),
        execution=MappingProxyType({"thread_id": entity_ref}),
        entity_kind=entity_kind, entity_ref=entity_ref, entity_label="thread",
        interaction="tap_commit", reversible=True, before={"inbox": True},
        expected_after={"inbox": False},
        summary={"subject": "Order 1938", "from_line": "Mia <mia@example.com>"},
        fingerprint="f", created_at=time.time(), expires_at=time.time() + 60,
        status=ActionStatus.VERIFIED, undo_of="prop_first" if undo else None,
    )


def _archived_proposal(*, undo: bool = False):
    return _proposal(operation="gmail_thread_archive", entity_kind="thread",
                     entity_ref=THREAD_ID, undo=undo)


def test_a_proven_archive_tells_the_tablet_the_thread_left_the_inbox():
    from app.presentation import present_proposal_state

    items = present_proposal_state(_archived_proposal())
    success = next(i for i in items if i["type"] == "success")
    assert success["data"]["archived"] == {"kind": "email_thread", "ref": THREAD_ID}
    assert "restored" not in success["data"]


def test_a_proven_undo_of_an_archive_puts_the_thread_back_in_the_queue():
    from app.presentation import present_proposal_state

    items = present_proposal_state(_archived_proposal(undo=True))
    success = next(i for i in items if i["type"] == "success")
    assert success["data"]["restored"] == {"kind": "email_thread", "ref": THREAD_ID}
    assert "archived" not in success["data"]


def test_nothing_else_claims_a_thread_left_the_inbox():
    from app.presentation import present_proposal_state

    note = _proposal(operation="order_note_append", entity_kind="order",
                     entity_ref="gid://shopify/Order/1")
    success = next(i for i in present_proposal_state(note) if i["type"] == "success")
    assert "archived" not in success["data"] and "restored" not in success["data"]


# ------------------------------------------------------------ §20 · the typing path exists


def test_the_composer_says_out_loud_that_it_can_be_typed_into(branch, session):
    """D-9: the owner asked how to type and was not understood. The card has to say it."""
    from app import commands

    _hold_thread(session)
    out = commands.run("compose.reply", _ctx(session, branch, thread_id=THREAD_ID))
    data = out.surfaces[0].as_ui()["data"]
    assert data["how"], "the composer must say how to put words in it"
    assert "type" in data["how"].lower()


def test_every_field_the_composer_offers_is_a_field_the_mac_will_accept(branch, session):
    from app import commands

    _hold_thread(session)
    data = commands.run("compose.reply", _ctx(session, branch, thread_id=THREAD_ID)).surfaces[0].as_ui()["data"]
    editable = [name for name in ("to", "to_name", "subject", "body")
                if isinstance(data.get(name), dict) and data[name].get("editable")]
    assert editable == ["body"]
    for name in editable:
        out = commands.run("compose.field", _ctx(session, branch, compose_id=data["compose_id"],
                                                 field=name, value="typed"))
        assert out.ok, name


def test_a_new_email_still_has_every_field_typable(branch, session):
    from app import commands

    compose_id = family.open_compose(branch, to="sam@example.com", subject="Hello", body="Hi")
    session.issue(compose_id)
    surface = family.compose_surface(branch.compose).as_ui()["data"]
    assert surface["to"]["editable"] is True and surface["subject"]["editable"] is True
    out = commands.run("compose.field", _ctx(session, branch, compose_id=compose_id,
                                             field="to", value="other@example.com"))
    assert out.ok and branch.compose["to"] == "other@example.com"
