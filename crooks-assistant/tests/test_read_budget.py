"""Read budgets with strict priority (§11) — D-4.

    turn_6089e7517986  commerce_aggregate  REFUSED: this turn has been reading for too long
    00:25:48           open.area           ok=False  code=landing_unavailable

One budget was shared by speculation, hydration and the owner's own foreground request, and
it was scoped to a long-lived turn — so reads nobody asked for could refuse the thing the
owner did ask for, and a turn that had been reading could refuse a tap that came after it.

The order the budgets enforce:

    1  active owner foreground read
    2  owner navigation hydration
    3  mutation precondition / verification
    4  active branch requested background job
    5  anticipation / speculation

Background and speculative work yields immediately, and lanes 4 and 5 can never spend what
lanes 1 to 3 need.
"""

from __future__ import annotations

import asyncio

import pytest

from app.reads import budget
from app.reads.scheduler import Read, ReadPlan, run_plan
from experience.harness import harness


@pytest.fixture()
async def stage():
    async with harness() as h:
        yield h


@pytest.fixture(autouse=True)
def _fresh_throttle():
    budget.throttle().reset()
    yield
    budget.throttle().reset()


# ------------------------------------------------------------------ the shape of the thing


def test_the_lanes_are_the_five_the_brief_names_in_its_order():
    assert budget.LANES == (
        budget.FOREGROUND, budget.NAVIGATION, budget.PRECONDITION,
        budget.BACKGROUND, budget.SPECULATION,
    )
    assert [budget.PRIORITY[lane] for lane in budget.LANES] == [1, 2, 3, 4, 5]
    assert budget.outranks(budget.FOREGROUND, budget.SPECULATION)
    assert budget.outranks(budget.NAVIGATION, budget.BACKGROUND)
    assert not budget.outranks(budget.SPECULATION, budget.PRECONDITION)


def test_each_lane_spends_its_own_budget_and_no_other():
    ledger = budget.Ledger()
    for _ in range(budget.BUDGETS[budget.SPECULATION].calls + 3):
        ledger.record(budget.SPECULATION, "guess", cost=2)
    assert ledger.check(budget.SPECULATION, "guess", cost=1), "the speculative lane never ran out"
    assert not ledger.check(budget.FOREGROUND, "turn_1", cost=4), (
        "speculation spent the owner's budget — this is D-4"
    )
    assert not ledger.check(budget.NAVIGATION, "tap_1", cost=4)
    assert not ledger.check(budget.PRECONDITION, "prop_1", cost=4)


def test_a_long_lived_key_never_contaminates_the_next_one():
    """A turn that read a great deal must not refuse the tap that comes after it."""
    ledger = budget.Ledger()
    while not ledger.check(budget.FOREGROUND, "turn_orders", cost=6):
        ledger.record(budget.FOREGROUND, "turn_orders", cost=6)
    assert ledger.check(budget.FOREGROUND, "turn_orders", cost=6)
    assert not ledger.check(budget.FOREGROUND, "turn_sales", cost=6), "the next turn inherited the last one's spend"
    assert not ledger.check(budget.NAVIGATION, "tap_sales", cost=6), "a tap inherited a turn's spend"


def test_the_lower_lanes_can_never_take_the_last_slot_of_a_source():
    """Speculation and background are capped below a source's concurrency, so an owner read
    always finds a slot. Measured against the scheduler's own limits."""
    throttle = budget.Throttle()
    for lane in (budget.BACKGROUND, budget.SPECULATION):
        for source in ("shopify", "gmail"):
            assert throttle.slots(source, lane) < throttle.slots(source, budget.FOREGROUND)
    held = []
    while throttle.admit("shopify", budget.SPECULATION):
        held.append(throttle.take("shopify", budget.SPECULATION))
    assert held, "speculation could not take a single slot"
    assert throttle.admit("shopify", budget.FOREGROUND), "the owner's read was locked out"


def test_starting_owner_work_stands_the_lower_lanes_down():
    stood_down: list[tuple[str, str]] = []
    token = budget.on_yield(lambda scope, lane: stood_down.append((scope, lane)) or 1)
    try:
        assert budget.yield_to(budget.FOREGROUND, scope="owner|s1") == 2
        assert [lane for _, lane in stood_down] == [budget.BACKGROUND, budget.SPECULATION]
        stood_down.clear()
        # Speculation asking to run stands nothing down: there is nothing below it.
        assert budget.yield_to(budget.SPECULATION, scope="owner|s1") == 0
        assert stood_down == []
    finally:
        budget.off_yield(token)


# ------------------------------------------------------------------ the session's own reads


async def _speculate(stage, times: int, session_id: str = "s1") -> None:
    """Run the anticipation layer's own read shape until its bound stops it."""
    session = stage.runtime.sessions.get_or_create(session_id)
    for n in range(times):
        plan = ReadPlan(
            [Read("guess", "commerce_query", {
                "entity": "orders", "period": "today", "limit": 10, "title": f"guess {n}",
            }, source="shopify", cost=120.0)],
            label="anticipate:test", origin="predicted", why="a hunch",
        )
        await run_plan(plan, session=session, turn_id=getattr(session, "turn_id", ""))


async def test_speculation_at_its_cap_does_not_refuse_the_owners_dock_command(stage):
    """The D-4 regression, in the order the live session hit it."""
    await stage.say("show me today's orders")
    await _speculate(stage, 12)
    tap = await stage.touch("open.area", area="orders")
    assert tap.status == 200
    assert tap.raw.get("ok") is True, f"the dock landing was refused: {tap.raw.get('code')} {tap.raw.get('detail')}"
    assert tap.surfaces, "the landing came back with nothing on it"


async def test_a_read_heavy_turn_does_not_refuse_the_tap_that_follows_it(stage):
    """"Opening Sales after exploring orders must get Sales.""""
    from app.tools.dispatch import dispatch

    session = stage.runtime.sessions.get_or_create("s1")
    await stage.say("show me today's orders")
    refusals = 0
    for days in range(1, 14):
        rendered = await dispatch(
            "commerce_query",
            {"entity": "orders", "period": {"days": days}, "limit": 10},
            session=session, timeout_s=8.0,
        )
        refusals += rendered.startswith("REFUSED")
    assert refusals, "the turn budget never ran out, so this test proves nothing"

    tap = await stage.touch("open.area", area="sales")
    assert tap.raw.get("ok") is True, f"Sales was refused after exploring orders: {tap.raw.get('code')}"
    assert tap.surfaces, "Sales drew nothing"
    assert tap.raw.get("changed", {}).get("area") == "sales"


async def test_speculation_never_spends_the_owners_turn_budget(stage):
    from app.tools.dispatch import dispatch

    session = stage.runtime.sessions.get_or_create("s1")
    await stage.say("show me today's orders")
    before = budget.ledger_for(session).spent(budget.FOREGROUND, session.turn_id)
    await _speculate(stage, 12)
    after = budget.ledger_for(session).spent(budget.FOREGROUND, session.turn_id)
    assert after == before, "speculation was charged to the owner's turn"
    rendered = await dispatch(
        "commerce_query", {"entity": "orders", "period": "yesterday", "limit": 10},
        session=session, timeout_s=8.0,
    )
    assert not rendered.startswith("REFUSED"), f"the owner's own read was refused: {rendered[:120]}"


async def test_a_budget_refusal_is_not_reported_as_a_missing_landing(stage):
    """`landing_unavailable` means "that could not be drawn"; a spent budget is not that.
    The owner was told the screen did not exist when the truth was that it had read too much."""
    session = stage.runtime.sessions.get_or_create("s1")
    ledger = budget.ledger_for(session)
    while not ledger.check(budget.NAVIGATION, "open.area", cost=6):
        ledger.record(budget.NAVIGATION, "open.area", cost=6)
    tap = await stage.touch("open.area", area="orders")
    if tap.raw.get("ok") is False:
        assert tap.raw.get("code") == "read_budget_spent", (
            f"a budget refusal came back as {tap.raw.get('code')!r}"
        )


async def test_the_owner_asking_stands_the_speculative_lane_down(stage):
    """`run_plan` already did this for speculation; now it does it for background work too,
    and it is the budget layer that decides which lanes are below the one asking."""
    session = stage.runtime.sessions.get_or_create("s1")
    stood: list[str] = []
    token = budget.on_yield(lambda scope, lane: stood.append(lane) or 0)
    try:
        await run_plan(
            ReadPlan([Read("mine", "commerce_query", {"entity": "orders", "period": "today", "limit": 5},
                           source="shopify", cost=120.0)], label="owner"),
            session=session, turn_id=session.turn_id,
        )
    finally:
        budget.off_yield(token)
    assert budget.BACKGROUND in stood and budget.SPECULATION in stood


async def test_reads_stay_reads_whatever_lane_they_are_in():
    """The non-negotiable, restated where the lanes are chosen: no lane can name a write."""
    from app.reads.scheduler import WriteInPlan, assert_reads_only

    import app.tools.shopify_writes  # noqa: F401

    for lane in budget.LANES:
        plan = ReadPlan([Read("x", "shopify_order_note_append", {})], lane=lane)
        with pytest.raises(WriteInPlan):
            assert_reads_only(plan)


async def test_a_speculative_plan_is_in_the_speculative_lane():
    assert ReadPlan([], origin="predicted").lane == budget.SPECULATION
    assert ReadPlan([], origin="requested").lane == budget.FOREGROUND
    assert ReadPlan([], lane=budget.NAVIGATION).lane == budget.NAVIGATION


async def test_two_lanes_run_at_once_without_one_starving_the_other(stage):
    """The whole point: speculation in flight must not delay the owner's read behind it."""
    session = stage.runtime.sessions.get_or_create("s1")
    slow = asyncio.gather(*(_speculate(stage, 3) for _ in range(3)))
    result = await run_plan(
        ReadPlan([Read("mine", "commerce_query", {"entity": "orders", "period": "today", "limit": 5},
                       source="shopify", cost=120.0)], label="owner"),
        session=session, turn_id="turn_owner",
    )
    await slow
    assert result.ok("mine"), f"the owner's read did not come back: {result.errors} {result.skipped}"
