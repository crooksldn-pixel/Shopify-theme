"""§9 — ZERO-OVERLAP as a HARD RELEASE GATE.

The brief's words: *"For the primary viewport (601×889, DPR ~1.33): zero collisions involving
interactive elements. If an interactive collision is detected in browser acceptance, THE TEST
FAILS — do not merely record it as telemetry."*

Phase 4 had the measurement and not the verdict. `web/collide.js` read every rectangle on the
screen and `scripts/browser/collision.js` reported them by rule, and the live session of 11
September recorded `overflow.collisions` of 1 to 4 on twenty of its orb-screen renders while
this suite was green — because nothing anywhere turned a number into a failure. This file is
that line.

Three tests, and only one of them needs a browser, on purpose:

  * the RULES are asserted structurally, so a rule deleted or a pair quietly dropped from
    §9's list of fourteen fails on any machine, browser or no browser;
  * the FIXTURES §9 names by hand are asserted against the case list, so "50-char customer
    name" and "offline notice" cannot be removed without this failing;
  * and the VERDICT is asserted in Chromium at both viewports.

The browser test is expected to FAIL on the tree that produced the live session, and its
failure names the workstream: `#branch-bar` is a child of `.orb-zone`, a positioned element at
`z-index: 1`, so no z-index inside it can lift a chip above a `#talk` painted at 3 with
`inset: 0`. Every branch control is drawn perfectly and the browser hands the touch to the
microphone. That is workstream A's P0, and this failing is the proof the gate works.
"""

from __future__ import annotations

import json
import subprocess

import pytest

from experience.browser import COLLISION_SCRIPT, ROOT, available, run_checks

#: §9's own list, in §9's own words. The mapping onto rules lives in `web/collide.js` so the
#: browser and the page agree; what is asserted here is that all fourteen are still asked.
REQUIRED_PAIRS = (
    "button-button", "button-text", "button-input", "button-navigation",
    "Split-voice", "branch-voice", "toast-navigation", "toast-orb", "toast-approval",
    "floating-controls-dock", "tabs-content", "long-name-action", "chips-title",
    "keyboard-action",
)

#: The stress fixtures §9 names. Each is a fixture id in `scripts/browser/collision.js`.
REQUIRED_FIXTURES = {
    "50-char customer name": "name_50_chars",
    "long email": "long_email_address",
    "long address": "long_postal_address",
    "long product title": "long_product_title",
    "long SKU": "long_sku",
    "long tracking": "long_tracking_number",
    "large amount": "large_currency",
    "multiple tags": "many_status_chips",
    "four actions": "four_actions",
    "branch mode": "idle_two_halves",
    "keyboard open": "keyboard_open",
    "stacked feedback": "stacked_feedback",
    "offline notice": "offline_notice",
}

VIEWPORTS = ("601x889@1.33", "800x1280@1")


def _collide_api() -> dict:
    """`web/collide.js`, loaded in Node. No browser: the rules are arithmetic."""
    probe = subprocess.run(
        ["node", "-e",
         "const c=require('./web/collide.js');"
         "process.stdout.write(JSON.stringify({rules:c.RULES,pairs:c.PAIRS,sel:Object.keys(c.SEL)}))"],
        cwd=ROOT, capture_output=True, text=True, timeout=30,
    )
    assert probe.returncode == 0, probe.stderr
    return json.loads(probe.stdout)


def test_every_pair_the_brief_names_has_a_rule_behind_it():
    """§9's fourteen, each mapped onto rules that exist.

    A pair with no rule behind it is a pair the gate has stopped asking, and it would go
    unnoticed: `collision.js` prints a zero for a rule that can never fire just as happily as
    for one that did not.
    """
    api = _collide_api()
    for label in REQUIRED_PAIRS:
        assert label in api["pairs"], f"§9 requires a verdict for {label}"
        for rule in api["pairs"][label]:
            assert rule in api["rules"], f"{label} names a rule that does not exist: {rule}"
    # And the two that cannot be expressed as a pair of rectangles at all.
    assert "split_under_voice" in api["rules"], "D-1 needs a hit test, not only geometry"
    assert "control_clipped_by_container" in api["rules"], (
        "an interactive control cut off by the screen or by a container is invisible to every "
        "pair rule and to document_overflow_x"
    )
    # The selector groups the pair rules stand on. A rule whose side matches nothing is a
    # rule that always passes.
    for kind in ("voice", "navigation", "dock", "split", "branch", "orb", "approval",
                 "input", "tabstrip", "panel", "action", "entityname", "title", "chip"):
        assert kind in api["sel"], f"no selector group for {kind}"


def test_every_stress_fixture_the_brief_names_is_in_the_suite():
    """The thirteen §9 lists, by fixture id, read out of the script itself.

    Asserted against the source rather than against a run, so it holds on a machine with no
    browser — and so that a fixture deleted in a hurry fails here rather than shrinking a
    green number nobody was counting.
    """
    source = COLLISION_SCRIPT.read_text(encoding="utf-8")
    for words, fixture in REQUIRED_FIXTURES.items():
        assert f"'{fixture}'" in source or f'"{fixture}"' in source, (
            f"§9 names the {words} stress fixture; there is no `{fixture}` in collision.js"
        )
    # The idle screen, and the idle screen divided. Every Phase 4 fixture drew cards first,
    # which puts the page into context mode — a different screen, with the voice target as a
    # dock band and the branch controls in the rail. The defect is on the orb screen.
    assert "idle_orb" in source, "nothing measures the screen the owner was actually tapping"
    assert "nav_full_divided" in source, "nothing measures the navigation row at its fullest"


async def test_zero_interactive_collisions_at_both_viewports():
    """The hard gate. One interactive collision at either size fails the release.

    Expected to fail on the tree that produced the live session. The detail of each failure
    names the fixture, the two selectors and the two rectangles, so it can be acted on without
    re-running anything.
    """
    ok, why = available()
    if not ok:
        pytest.skip(f"the §9 gate needs a browser: {why}")
    result = await run_checks(scripts=(COLLISION_SCRIPT,))
    if result.get("skipped"):
        pytest.skip(result.get("why", "no browser"))
    names = [str(c.get("name") or "") for c in result.get("checks") or []]

    # First: it actually asked. A gate that stopped measuring must not look like a pass.
    for size in VIEWPORTS:
        assert any(size in n for n in names), f"nothing was measured at {size}"
        assert f"{size} · §9 · ZERO collisions involving an interactive element" in names, (
            f"the §9 verdict was not reached at {size}"
        )
        for label in REQUIRED_PAIRS:
            assert f"{size} · §9 pair · {label}" in names, f"{label} was not asked at {size}"

    failed = [c for c in result.get("checks") or [] if not c.get("ok")]
    detail = "\n".join(f"  - {c['name']}\n      {c.get('detail', '')}" for c in failed)
    assert not failed, (
        f"{len(failed)} of {len(names)} §9 checks failed. An interactive collision is a "
        f"release failure, not telemetry:\n{detail}"
    )
