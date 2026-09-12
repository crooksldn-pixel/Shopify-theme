"""§30 — browser replay of the REAL live states, and the promise that no customer is in them.

Phase 4's browser gate was nineteen invented fixtures and it was green all the way through the
evening reconstructed in `docs/phase5/LIVE_SESSION_FORENSICS.md`. The brief's verdict on that:
*"A screenshot suite that never reaches the broken state is not sufficient."*

Four tests, in order of what they protect:

  1. NO CUSTOMER IS IN THE FIXTURES. The raw timeline has real names, real addresses and full
     Shopify ids in it. It is gitignored; the committed fixture is derived from it. This test
     reads every committed byte of that derivation and refuses a full id or an address outside
     the reserved example domains. It needs nothing but the repository, so it runs everywhere.
  2. the ten states the brief lists are all there, and each says what it reproduces and which
     workstream owns its verdict.
  3. the derivation still MATCHES the timeline, where the timeline is on this machine. A
     fixture that has drifted from what the tablet recorded is a broken instrument, and a gate
     whose fixtures have quietly drifted is the failure this whole section is about.
  4. and the replay itself, in Chromium.

Test 4 is expected to fail on this tree. Its failures are the proof the gate works: they name
the workstream in every line.
"""

from __future__ import annotations

import json

import pytest

from experience.browser import REPLAY_SCRIPT, available, run_checks
from experience.fixtures import live_states

#: The ten §30 lists, by fixture id.
REQUIRED_STATES = {
    "duplicate_customer_surface": "the duplicate customer surface",
    "returning_customers_seven_cards": "the returning-customer result",
    "customer_history_gmail_email_list_only": "the customer history + Gmail request that rendered only email_list",
    "split_overlap_branch_under_voice": "the split overlap",
    "merge_close_tap": "the merge/close tap",
    "dock_touch_burst": "the dock touch burst",
    "refused_open_entity_half_empty": "the fake open.entity refused not_held",
    "home_back_no_arrival": "the Home/Back failure",
    "customer_page_expansion_capability": "the customer page expansion",
    "empty_email_section": "the empty Gmail section",
}


def test_no_customer_and_no_address_reached_the_committed_fixtures():
    """The promise the brief makes in capitals, enforced over every committed byte.

    `assert_clean` refuses two things: any run of thirteen or more digits (a Shopify id; the
    fixtures carry four-digit tails and nothing longer) and any email address outside
    example.com / .org / .net. Run over the JSON and over the module that builds it, because
    the invented names and addresses live in the module.
    """
    blob = live_states.STATES_JSON.read_text(encoding="utf-8")
    live_states.assert_clean(blob, "experience/fixtures/live_states.json")
    source = (live_states.STATES_JSON.parent / "live_states.py").read_text(encoding="utf-8")
    live_states.assert_clean(source, "experience/fixtures/live_states.py")
    # And the browser script that reads them, in case a debugging line ever pasted one in.
    live_states.assert_clean(REPLAY_SCRIPT.read_text(encoding="utf-8"), REPLAY_SCRIPT.name)

    # The invented people are invented: none of them may be a name the timeline carries. The
    # timeline is not readable here, so this is the other half of the guarantee — the list is
    # fixed in the module and reviewed, and its shape is asserted.
    assert len(set(live_states.INVENTED)) == len(live_states.INVENTED)
    assert all(" " in name for name in live_states.INVENTED), "a first name and a surname"


def test_the_seven_are_seven_different_people():
    """D-4's whole point, in the fixture as well as in the ids.

    The analyser filed turn_be1b384ca420 as `DUPLICATE_RENDER` — "the same customer card drawn
    7 times" — and the forensics had to correct it: seven cards for seven DIFFERENT customers.
    The first version of `invented_name` took the id's last four digits modulo a twelve-name
    list, and on these seven ids that lands on two values, so the fixture meant to disprove a
    duplicate render drew two people seven times. It was visible in the screenshot before it
    was visible anywhere else.

    So the mapping is asserted, not trusted.
    """
    names = [live_states.invented_name(ref) for ref in live_states.SEVEN]
    assert len(set(names)) == len(live_states.SEVEN), (
        f"{len(set(names))} people across {len(live_states.SEVEN)} records: "
        f"{dict(zip(live_states.SEVEN, names, strict=True))}"
    )
    emails = [live_states.invented_email(ref) for ref in live_states.SEVEN]
    assert len(set(emails)) == len(live_states.SEVEN)
    # And stable: the same id is the same person on the next call, in the next process, on
    # another machine. `hash()` is salted per process and would not be.
    assert names == [live_states.invented_name(ref) for ref in live_states.SEVEN]
    # Which the committed fixture has to agree with, or the JSON was built before this changed.
    drawn = [item["data"]["name"] for item in
             live_states.state("returning_customers_seven_cards")["replay"]["ui"]]
    assert drawn == names, f"the committed fixture draws {drawn}"


def test_the_ten_states_the_brief_lists_are_all_there():
    fixture = live_states.load()
    assert fixture["source"] == live_states.SOURCE_SESSION
    assert fixture["events"] > 1000, "derived from the whole timeline, not a slice of it"
    got = {entry["id"] for entry in fixture["states"]}
    for wanted, words in REQUIRED_STATES.items():
        assert wanted in got, f"§30 lists {words}; there is no `{wanted}` fixture"
    for entry in fixture["states"]:
        assert entry.get("reproduces"), f"{entry['id']} does not say what it reproduces"
        assert entry.get("gate"), f"{entry['id']} does not say what it gates"
        assert entry.get("observed"), f"{entry['id']} carries no measurements from the timeline"
        # A state is either a payload to draw, a script to drive, or both. One that is neither
        # is a note, not a fixture.
        assert entry.get("replay") or entry.get("drive"), f"{entry['id']} cannot be replayed"


def test_the_fixtures_still_match_the_timeline_they_came_from():
    """Re-derive and compare, where the raw file is on this machine.

    Skipped — loudly — where it is not: the timeline is gitignored because it has real
    customers in it, so on a fresh clone this cannot run and must not pretend to have.
    """
    try:
        rows = live_states.read_rows()
    except live_states.TimelineMissing as missing:
        pytest.skip(f"the raw timeline is not on this machine: {missing}")
    fresh = live_states.derive(rows)
    committed = {entry["id"]: entry["observed"] for entry in live_states.load()["states"]}
    assert set(fresh) == set(committed)
    for fixture_id, observed in committed.items():
        assert observed == fresh[fixture_id], (
            f"{fixture_id} has drifted from the timeline it claims to come from.\n"
            f"  committed: {json.dumps(observed, sort_keys=True)[:400]}\n"
            f"  timeline:  {json.dumps(fresh[fixture_id], sort_keys=True)[:400]}"
        )
    # The headline numbers of the forensics document, so a derivation that started measuring
    # something else fails here by name rather than by a diff nobody reads.
    burst = fresh["dock_touch_burst"]
    assert burst["taps"] == 26, "the 23:08:31 burst is 26 taps"
    assert burst["sent_under_200ms"] == 63, "63 sub-200ms holds were sent"
    assert burst["hold_starts_on_dock"] == 131, "131 of 132 hold starts report target dock"
    seven = fresh["returning_customers_seven_cards"]
    assert seven["distinct_refs"] == 7, "seven DIFFERENT customers, not one drawn seven times"
    assert seven["cards_height"] == 1949, "1,949px of deck"
    assert all(card["height"] == 265 for card in seven["cards"]), "265px each"
    assert fresh["customer_page_expansion_capability"]["cards"][0]["height"] == 1014
    assert fresh["refused_open_entity_half_empty"]["code"] == "not_held"
    assert fresh["home_back_no_arrival"]["commands_accepted"] == 8
    assert fresh["home_back_no_arrival"]["commands_refused"] == 0


async def test_the_live_states_replay_in_a_browser():
    ok, why = available()
    if not ok:
        pytest.skip(f"the live replay needs a browser: {why}")
    result = await run_checks(scripts=(REPLAY_SCRIPT,))
    if result.get("skipped"):
        pytest.skip(result.get("why", "no browser"))
    checks = result.get("checks") or []
    names = [str(c.get("name") or "") for c in checks]

    # It asked. Every state must have been both reproduced and gated, or the run stopped
    # early and a smaller green number would have hidden it.
    for fixture_id in REQUIRED_STATES:
        assert any(f"· {fixture_id} ·" in n for n in names), f"{fixture_id} was never replayed"
    assert any(n.startswith("FIXTURE ·") for n in names), "nothing checked that a state was reached"
    assert any(n.startswith("GATE ·") for n in names), "nothing checked that a state was fixed"

    # A fixture that no longer reaches the broken state is an instrument fault, and it is
    # reported separately from a gate that is still red — they are acted on by different people.
    broken = [c for c in checks if not c.get("ok") and str(c.get("name")).startswith("FIXTURE ·")]
    assert not broken, (
        "the fixtures no longer reproduce what the tablet recorded:\n"
        + "\n".join(f"  - {c['name']}\n      {c.get('detail', '')}" for c in broken)
    )
    failed = [c for c in checks if not c.get("ok")]
    detail = "\n".join(f"  - {c['name']}\n      {c.get('detail', '')}" for c in failed)
    assert not failed, f"{len(failed)} of {len(checks)} live-state gates failed:\n{detail}"
