"""The golden scenarios, as part of the ordinary suite.

They run against the fixture world through the real runtime, so they are as offline and as
deterministic as every other test here — and they are the only tests that can catch the class
of failure this pass exists for, which is an answer that is correct, fast, and has nothing on
the screen. A unit test of a presenter cannot see that; only driving a turn can.
"""

from __future__ import annotations

import pytest

from experience.harness import harness
from experience.scenarios import BY_NAME, SCENARIOS


@pytest.fixture()
async def stage():
    async with harness() as h:
        yield h


@pytest.mark.parametrize("name", [n for n, _ in SCENARIOS])
async def test_the_golden_scenarios(name, stage):
    result = await BY_NAME[name](stage)
    assert not result.error, result.error
    failures = "\n".join(f"  - {c.what} :: {c.detail}" for c in result.failures)
    assert result.status == "PASS", f"{result.title}\n{failures}"


async def test_an_order_lookup_that_is_fast_and_empty_is_a_failure(stage):
    """The regression test the brief asks for by name (§29).

    It is worth stating what this does NOT assert: it says nothing about latency. The build
    that was reported as broken was fast — that was the whole complaint. Speed with an empty
    screen has to fail, so the assertions are all about what came back.
    """
    capture = await stage.say("show me order 1938")
    assert capture.lane == "FAST", "the fast lane should answer a plain order lookup"
    assert not capture.prose_only, (
        f"the answer was prose with no surface: {capture.answer!r}"
    )
    order = capture.surface("order")
    assert order is not None, f"no order surface; got {capture.surface_types}"
    assert order["data"].get("detail") is True, "the brief card, not the full order"
    assert order["data"].get("items"), "the items are not reachable"
    assert capture.action_ids, "no actions were offered for the order"
    assert (capture.entity or {}).get("kind") == "order", "the current entity was not established"


async def test_the_fast_lane_never_answers_an_entity_question_with_prose(stage):
    """Every recipe that answers about a record must draw one. A recipe added later that
    forgets to return calls or a surface fails here rather than on the workbench."""
    asked = [
        "show me order 1938",
        "show me today's orders",
        "what can you do now?",
        "where is order 1938",
        "how much have we sold today?",
    ]
    empty = []
    for question in asked:
        capture = await stage.say(question)
        if capture.lane == "FAST" and capture.prose_only:
            empty.append((question, capture.recipe_id, capture.answer[:60]))
    assert not empty, f"fast answers with nothing on screen: {empty}"


async def test_a_tap_and_a_sentence_reach_the_same_cursor(stage):
    await stage.say("show me today's orders", session_id="parity")
    spoken = await stage.say("next", session_id="parity")
    tapped = await stage.touch("workflow.next", session_id="parity")
    assert spoken.model_calls == 0 and tapped.model_calls == 0, "navigation woke the model"
    assert "1 of" in spoken.answer and "2 of" in tapped.answer, (
        f"the cursor did not advance once per step: {spoken.answer!r} then {tapped.answer!r}"
    )
    assert spoken.set_id and spoken.set_id == tapped.set_id, "they walked different sets"


async def test_the_fixture_world_refuses_every_write(stage):
    """A scenario can propose. It can never execute — the fixture clients have no working
    mutation, so a test that started applying changes would fail loudly rather than quietly
    passing against a shop that was being modified."""
    from experience.fixtures.gmail import FixtureWriteAttempted as GmailWrite
    from experience.fixtures.shopify import FixtureWriteAttempted as ShopifyWrite

    with pytest.raises(ShopifyWrite):
        await stage.store.mutate("order_cancel", {})
    with pytest.raises(GmailWrite):
        stage.gmail.service().users().messages().send(userId="me", body={}).execute()


async def test_back_draws_the_record_even_when_memory_has_dropped_it(stage):
    """Going back must never announce a move and leave the screen where it was.

    Memory usually holds the record — returning to something just looked at is not a new
    question — so the cheap path is a replay. When the tier has dropped it, the trail move
    still happened and the record still has to be drawn, so it is read. This empties the
    entity tier between the two lookups to force that path.
    """
    from app.memory import ENTITY
    from app.memory import current as memory

    await stage.say("show me order 1938", session_id="cold")
    await stage.say("show me order 1936", session_id="cold")

    forgotten = memory().invalidate(tier=ENTITY)
    assert forgotten, "nothing was in the entity tier to forget; the test proves nothing"

    back = await stage.touch("navigation.back", session_id="cold")
    assert back.raw.get("ok") is True, back.raw
    # The point of the test: the tier really was cold, so this had to READ rather than replay.
    # Without this the test would pass on the replay path and prove nothing.
    changed = back.raw.get("changed") or {}
    assert changed.get("replayed") is False, f"memory still held it; the cold path was not taken: {changed}"
    assert changed.get("needs_read"), f"the cold path did not ask for a read: {changed}"
    assert not back.prose_only, (
        f"back announced a move and drew nothing: {back.answer!r}"
    )
    assert back.surface("order") is not None, f"surfaces={back.surface_types}"
    assert back.data("order").get("order_number") == "#1938", back.data("order")
    assert (back.entity or {}).get("ref") == "gid://shopify/Order/1938", back.entity
    # Where the read came from — the store, or a warm read-layer cache — is not this test's
    # business. That a card appeared after memory had dropped the record is.
