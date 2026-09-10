"""The external shipping boundary (§20).

Easyship is not integrated. The tests that matter are the ones that would fail if this build
started pretending it was: an adapter that reports connected, a context that claims to have
checked something it did not, a sentence that says "checked Easyship" where nothing was asked,
or a fixture answer passed off as a live one.
"""

from __future__ import annotations

import pytest

from app.shipping import ShippingContext, ShippingNotConnected, context_for, install, not_connected
from app.shipping.easyship import CLIENT, TOKEN_ENV, EasyshipProvider
from app.shipping.fixture import FixtureShipping
from app.shipping.provider import DISCONNECTED, NO_SHIPMENT, OK, UNAVAILABLE


@pytest.fixture(autouse=True)
def _no_provider():
    """This build installs nothing. Restored after each test that installs one."""
    install(None)
    yield
    install(None)


async def test_with_nothing_connected_nothing_was_checked():
    context = await context_for("gid://shopify/Order/1")
    assert context.state == DISCONNECTED and context.checked is False
    assert context.provider == "" and context.label_exists is None
    assert "not checked" in context.said()
    assert context.public()["checked"] is False


async def test_the_easyship_adapter_says_exactly_what_is_missing(monkeypatch):
    install(EasyshipProvider())
    context = await context_for("gid://shopify/Order/1")
    assert context.checked is False and context.state == DISCONNECTED
    assert any(TOKEN_ENV in item for item in context.missing)
    assert any(CLIENT in item for item in context.missing)
    # And a credential alone does not make it connected: the client does not exist either.
    monkeypatch.setenv(TOKEN_ENV, "not-a-real-key")
    again = await context_for("gid://shopify/Order/1")
    assert again.checked is False
    assert EasyshipProvider().token_present() is True
    assert EasyshipProvider().connected() is False
    assert any(CLIENT in item for item in again.missing)


async def test_the_adapter_refuses_rather_than_answering():
    provider = EasyshipProvider()
    with pytest.raises(ShippingNotConnected) as raised:
        await provider.shipment_for("gid://shopify/Order/1")
    assert raised.value.provider == "Easyship" and raised.value.missing
    with pytest.raises(ShippingNotConnected):
        await provider.document("label_1")


async def test_nothing_can_say_it_checked_easyship_unless_it_did():
    """The honesty rule of §20, as an oracle: every way of rendering a context that was not
    checked, for every state, and none of them may claim a provider checked anything."""
    install(EasyshipProvider())
    contexts = [
        await context_for("gid://shopify/Order/1"),
        not_connected("gid://shopify/Order/2"),
        ShippingContext(order_ref="x", state=UNAVAILABLE, checked=False, provider="Easyship",
                        detail="timeout", missing=("an answer",)),
    ]
    for context in contexts:
        said = context.said().lower()
        assert "not checked" in said or "did not answer" in said
        assert "easyship:" not in said, f"a context that checked nothing said {context.said()!r}"
        row = context.public()
        assert row["checked"] is False
        assert row["carrier"] is None and row["tracking"] is None and row["status"] is None


async def test_a_provider_that_fails_is_a_state_and_still_not_a_claim():
    class Broken:
        name = "Broken"

        def connected(self) -> bool:
            return True

        def missing(self) -> tuple[str, ...]:
            return ()

        async def shipment_for(self, order_ref: str) -> ShippingContext:
            raise RuntimeError("no network")

        async def document(self, reference: str) -> bytes | None:
            return None

    install(Broken())
    context = await context_for("gid://shopify/Order/1")
    assert context.state == UNAVAILABLE and context.checked is False
    assert context.detail == "RuntimeError" and "did not answer" in context.said()


async def test_the_fixture_provider_answers_the_seven_questions_and_names_itself():
    install(FixtureShipping({
        "gid://shopify/Order/1": {
            "carrier": "Royal Mail", "tracking": "AB123", "tracking_url": "https://x/AB123",
            "status": "in transit", "exception": "", "documents": ("label_1",), "label_exists": True,
        },
    }))
    context = await context_for("gid://shopify/Order/1")
    assert context.checked is True and context.state == OK
    assert context.provider == "fixture", "a fixture answer must never pass as a live one"
    assert context.label_exists is True and context.shipment_created is True
    assert context.carrier == "Royal Mail" and context.tracking == "AB123"
    assert context.status == "in transit" and context.exception == ""
    assert context.documents == ("label_1",)
    assert context.said().startswith("fixture:")
    # An order the world has no shipment for is answered, not guessed.
    empty = await context_for("gid://shopify/Order/9")
    assert empty.checked is True and empty.state == NO_SHIPMENT and empty.label_exists is False


async def test_a_document_is_fetched_by_reference_only():
    install(FixtureShipping({"o1": {"documents": ("label_1",)}}, documents={"label_1": b"%PDF-"}))
    from app.shipping import current

    provider = current()
    assert await provider.document("label_1") == b"%PDF-"
    assert await provider.document("label_2") is None


async def test_the_capability_row_says_disconnected_and_why():
    from app.capabilities import families
    from app.families import load_all

    load_all()
    table = await families.states(None)
    row = table["shipping_provider"]
    assert row["state"] == "DISCONNECTED" and row["offerable"] is False
    assert TOKEN_ENV in row["detail"] and "client" in row["detail"]
    assert row["tools"] == [] and row["operations"] == []
    # The model is told not to attempt it, in one line, with the reason.
    lines = families.words({"shipping_provider": row})
    assert lines and "DISCONNECTED" in lines[0] and "Do not attempt it" in lines[0]


async def test_the_row_follows_the_provider_rather_than_a_declaration():
    from app.capabilities import families
    from app.families import load_all

    load_all()
    install(FixtureShipping({}))
    row = (await families.states(None))["shipping_provider"]
    assert row["state"] == "READY" and "fixture" in row["detail"]


async def test_the_anticipation_layers_shipping_read_carries_the_same_flag():
    from app.anticipation import internal

    answered = await internal.run("shipping_status", {"order_id": "gid://shopify/Order/1"})
    assert answered["checked"] is False and answered["state"] == DISCONNECTED
    install(FixtureShipping({"gid://shopify/Order/1": {"carrier": "Royal Mail", "tracking": "AB1"}}))
    again = await internal.run("shipping_status", {"order_id": "gid://shopify/Order/1"})
    assert again["checked"] is True and again["provider"] == "fixture" and again["tracking"] == "AB1"


def test_the_boundary_has_no_mutation_in_it():
    """A label is bought through the action engine when that exists, not through an adapter.
    Nothing in this package may grow a write: no method here creates, buys, cancels or voids."""
    import inspect

    from app import shipping
    from app.shipping import easyship, fixture, provider

    banned = ("create", "buy", "purchase", "void", "cancel", "refund", "update", "delete", "set_")
    for module in (shipping, provider, easyship, fixture):
        for name, member in inspect.getmembers(module):
            if name.startswith("_"):
                continue
            if inspect.isclass(member) or inspect.isfunction(member):
                for attribute in dir(member):
                    assert not attribute.startswith(banned), f"{module.__name__}.{name}.{attribute}"
