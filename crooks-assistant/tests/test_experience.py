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
