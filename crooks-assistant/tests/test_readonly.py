"""The read-only latch: what it stops, and that it is off unless someone put it on.

This is a safety device, so the tests are about the guarantee rather than the mechanism. The
guarantee is that a latched process cannot execute a Shopify or a Gmail change, and that the
two places every change funnels through both refuse.
"""

from __future__ import annotations

import pytest

from app import readonly
from app.clients.gmail import GmailClient
from app.clients.shopify import ShopifyClient


@pytest.fixture()
def latched(monkeypatch):
    """Engage the latch for one test. There is deliberately no release in the module itself —
    a process that has been read-only stays that way — so the test restores the flag directly,
    which is a thing only a test can reach."""
    monkeypatch.setattr(readonly, "_engaged", True)
    monkeypatch.setattr(readonly, "_reason", "a test")
    return readonly


def test_it_is_off_unless_someone_engages_it():
    assert readonly.active() is False
    assert readonly.banner() == ""
    readonly.assert_writable("anything")   # does not raise


async def test_a_latched_process_cannot_send_a_shopify_mutation(latched):
    client = ShopifyClient("fake.myshopify.com", "2025-07")
    with pytest.raises(readonly.WriteRefused) as caught:
        await client.mutate("order_note_append", {"id": "gid://shopify/Order/1", "note": "x"})
    assert "read-only" in str(caught.value)


@pytest.mark.parametrize(("what", "call"), [
    ("send_message", lambda c: c.send_message("raw", None)),
    ("send_draft", lambda c: c.send_draft("d1")),
    ("create_draft", lambda c: c.create_draft("raw", None)),
    ("delete_draft", lambda c: c.delete_draft("d1")),
    ("modify_thread", lambda c: c.modify_thread("t1", add=[], remove=[])),
])
def test_a_latched_process_cannot_change_the_mailbox(what, call, latched):
    with pytest.raises(readonly.WriteRefused):
        call(GmailClient())


async def test_the_action_engine_refuses_before_it_claims_anything(latched):
    """One layer above the client, so the refusal is a code on the card rather than an
    exception in a log — and so nothing is marked EXECUTING on the way to being refused."""
    from app.actions.engine import ActionEngine
    from app.actions.ledger import NullLedger

    engine = ActionEngine(ledger=NullLedger())
    result = await engine.commit("prop_nothing", "s1", caller="owner@example.com", spec_lookup=lambda _n: None)
    assert result.code == "read_only"


def test_the_refusal_has_words_for_the_card():
    from app.presentation import _COMMIT_BLOCKED_WORDS

    assert "read_only" in _COMMIT_BLOCKED_WORDS
    assert "read-only" in _COMMIT_BLOCKED_WORDS["read_only"].lower()


def test_the_live_clients_have_no_working_mutation():
    """Defence in depth: even with the latch somehow released, the clients a live run binds
    cannot write. The latch would have to fail AND the client would have to be the wrong
    class before anything could be sent."""
    from experience.live import LiveWriteAttempted, ReadOnlyGmail, ReadOnlyShopify

    gmail = ReadOnlyGmail()
    for call in (lambda: gmail.send_message("r", None), lambda: gmail.send_draft("d"),
                 lambda: gmail.create_draft("r", None), lambda: gmail.delete_draft("d"),
                 lambda: gmail.modify_thread("t", add=[], remove=[])):
        with pytest.raises((LiveWriteAttempted, readonly.WriteRefused)):
            call()
    assert ReadOnlyShopify.mutate is not ShopifyClient.mutate
