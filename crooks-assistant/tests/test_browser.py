"""The page in Chromium, as part of the suite.

Skipped, loudly, when node/playwright-core/Chromium are not on this machine — never quietly
passed. A browser check that cannot run has proved nothing, and saying so is the difference
between a suite that is green and a suite that is honest.
"""

from __future__ import annotations

import pytest

from experience.browser import available, run_checks


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
