"""The page in Chromium, as part of the suite.

Skipped, loudly, when node/playwright-core/Chromium are not on this machine — never quietly
passed. A browser check that cannot run has proved nothing, and saying so is the difference
between a suite that is green and a suite that is honest.
"""

from __future__ import annotations

import pytest

from experience.browser import COLLISION_SCRIPT, SCRIPT, TABLET_SCRIPT, available, run_checks


def test_the_gate_runs_all_three_browser_scripts():
    """The gate is three scripts, not one, and none of them is optional.

    `experience.js` proves the backend's cards can be drawn and touched at 800 x 1280.
    `tablet.js` proves the same at the size the tablet physically is. `collision.js` reads
    every rectangle on screen against nineteen stress fixtures at both sizes, because the
    live session of 11 September recorded `clipped=0` on every render while the owner was
    looking at overlapping text and controls. A file that is not in this tuple is a check
    nobody runs, which is how that session came to be green.
    """
    from experience import browser

    for script in (SCRIPT, TABLET_SCRIPT, COLLISION_SCRIPT):
        assert script.exists(), f"{script.name} is missing"
    source = (browser.ROOT / "experience" / "browser.py").read_text(encoding="utf-8")
    assert "COLLISION_SCRIPT" in source
    assert source.count("COLLISION_SCRIPT") >= 3, "declared, screenshotted and checked"


async def test_the_page_works_in_a_real_browser():
    ok, why = available()
    if not ok:
        pytest.skip(f"browser checks need a browser: {why}")
    result = await run_checks()
    if result.get("skipped"):
        pytest.skip(result.get("why", "no browser"))
    failed = [c for c in result.get("checks") or [] if not c.get("ok")]
    detail = "\n".join(f"  - {c['name']} :: {c.get('detail', '')}" for c in failed)
    assert result.get("ok"), f"{len(failed)} browser check(s) failed:\n{detail}"
    assert len(result.get("checks") or []) >= 12, "the browser run did fewer checks than expected"
    # The collision suite's own names, so a run that quietly stopped measuring geometry is a
    # failure rather than a smaller green number.
    names = " | ".join(str(c.get("name") or "") for c in result.get("checks") or [])
    for size in ("601x889@1.33", "800x1280@1"):
        assert size in names, f"nothing was measured at {size}"
    for rule in ("no interactive control overlaps another", "no text overlaps an action control",
                 "no notification overlaps the dock", "nothing essential is hidden under the fixed furniture",
                 "every control a finger uses is about 44px"):
        assert rule in names, f"the collision suite did not run: {rule}"
