"""What the golden world is wired to, asserted rather than assumed.

`experience/harness.py` and `experience/browser.py` re-point the tool modules at the fixture
store and the fixture inbox by hand, because the modules hold their clients at module level
and `runtime.build()` gave them the real ones. That hand-wiring is code with no other test
over it: a binding that is wrong in a way no scenario happens to reach stays wrong, and the
first family to reach it pays for it.
"""

from __future__ import annotations

import pytest

from experience.harness import harness


@pytest.fixture()
async def stage():
    async with harness() as h:
        yield h


async def test_the_fixture_world_can_read_the_recipient_off_an_order(stage):
    """A new email to an order's customer, in the golden world, through the same lookup
    production uses.

    The harness bound the write module a `customer=` callable — and it bound the WRONG one:
    `gmail_tools`' email-to-bool sender check, which takes one argument, while
    `gmail_writes._order_customer` calls its lookup with two. So every `gmail_draft_new` and
    `gmail_send_new` carrying an order_id died in the fixture world with a TypeError about
    positional arguments, and no scenario noticed, because none of them reached that path.

    The fix was to bind no lookup at all: the module's own fallback reads the customer off
    the order through `shopify_tools.hydrator()`, which the harness has already pointed at
    the fixture store. This asserts the whole of that — the binding, the fallback and the
    fixture order — so a lookup that cannot be called fails here instead of in whichever
    scenario is written next.
    """
    from app.tools import gmail_writes
    from experience.fixtures import data

    who = await gmail_writes._order_customer(order_id=data.SCENARIO_ORDER.order_id)

    assert who["email"] == data.MIA.email.lower(), who
    assert who["name"] and who["label"] == "#1938", who
