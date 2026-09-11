"""What the first viewport says, measured in a real browser at 601 x 889 (§8, D-12).

The live session recorded 38 long-scroll surfaces, the tallest 1,999 px against a 680 px
viewport, and a deepest scroll of 2,014 px. Those are measurements and this is a measurement:
Chromium at the tablet's own size against the real backend, reading getBoundingClientRect. A
structural test under the DOM stand-in cannot do it — the stand-in has no layout — so this is
the one that proves the density work rather than describing it.

Skipped, loudly, when there is no browser on this machine. A check that cannot run has proved
nothing, and saying so is the difference between a suite that is green and one that is honest.
"""

from __future__ import annotations

import pytest

from experience.browser import DENSITY_SCRIPT, available, run_checks


async def test_the_first_viewport_answers_the_three_questions():
    ok, why = available()
    if not ok:
        pytest.skip(f"the density measurement needs a browser: {why}")
    result = await run_checks(scripts=(DENSITY_SCRIPT,))
    if result.get("skipped"):
        pytest.skip(result.get("why", "no browser"))
    failed = [c for c in result.get("checks") or [] if not c.get("ok")]
    detail = "\n".join(f"  - {c['name']} :: {c.get('detail', '')}" for c in failed)
    assert result.get("ok"), f"{len(failed)} density check(s) failed at 601 x 889:\n{detail}"
    # An order, an email thread and an order list, five questions each plus the shape checks.
    assert len(result.get("checks") or []) >= 16, "the density run did fewer checks than expected"
