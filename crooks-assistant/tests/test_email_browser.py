"""The email workspace, driven with a finger in Chromium (§19, §20, §22).

The live session's rail rendered eight actions enabled and the owner used none of them, over
ten minutes, while every ASGI test in this suite stayed green. That is the gap this file
closes: a handler that EXISTS is what an ASGI test can see, and a click path that WORKS is
not. `scripts/browser/email.js` presses every enabled chip on the cards it opens, walks the
whole Reply path with real keystrokes, types through a redraw nobody asked for, holds the
card, reads VERIFIED, and then looks for the archived thread in the queue it left.

Skipped, loudly, when node/playwright-core/Chromium are not on this machine — never quietly
passed. A browser check that cannot run has proved nothing.
"""

from __future__ import annotations

import pytest

from experience.browser import EMAIL_SCRIPT, available, run_checks

# Every check the script makes must actually be made: a run that silently stopped after the
# first section would otherwise pass with three green lines.
EXPECTED_CHECKS = 43


async def test_the_email_workspace_works_under_a_finger():
    ok, why = available()
    if not ok:
        pytest.skip(f"browser checks need a browser: {why}")
    result = await run_checks(scripts=(EMAIL_SCRIPT,))
    if result.get("skipped"):
        pytest.skip(result.get("why", "no browser"))
    failed = [c for c in result.get("checks") or [] if not c.get("ok")]
    detail = "\n".join(f"  - {c['name']} :: {c.get('detail', '')}" for c in failed)
    assert result.get("ok"), f"{len(failed)} email browser check(s) failed:\n{detail}"
    assert len(result.get("checks") or []) >= EXPECTED_CHECKS, (
        f"the email run made {len(result.get('checks') or [])} checks, expected at least "
        f"{EXPECTED_CHECKS} — it stopped early"
    )
