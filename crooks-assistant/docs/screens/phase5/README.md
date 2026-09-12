# Phase 5 — the screenshot matrix (§32)

Thirty-four named surfaces at **601 × 889, DPR 1.33** — the Galaxy Tab A 8.0 in the owner's
hand, which is the viewport every `tablet_render` in the 11 September session reports — and a
representative twelve repeated at **800 × 1280**.

Written by `make screens`, which runs `scripts/browser/screens.js` against a real backend
serving the golden fixture world. Nothing here is a mock-up: every card was drawn by
`web/ui.js` from data the backend produced or from a payload derived off the live timeline.

## Read the filenames first

```
601x889-04-order-detail.png                          this surface exists and was photographed
601x889-16-returning-customers-result.MISSING.png    this surface does not exist yet
```

**`.MISSING` means the file is not a picture of the thing it is named after.** Every shot in
`screens.js` declares what must be on the glass for the file to *be* that shot — shot 10 needs
a customer surface carrying their orders, their email *and* somewhere to write; shot 17 needs a
promised-but-unread card to photograph. When that is not there the check fails by name, the
picture is still written because what *was* on screen is evidence, and the suffix is on the
filename so a directory listing is the report.

This convention exists because of what it replaces. Phase 4 shipped a screenshot suite that
was green through the evening reconstructed in `docs/phase5/LIVE_SESSION_FORENSICS.md`: 63
swallowed taps, seven profile cards for a one-line answer, a customer workspace showing an
empty inbox. A suite that captures whatever happens to be on the glass and names the file after
the surface it hoped for is worse than no suite, because the filename is a claim.

`index.json` carries the same verdicts in machine form: one entry per shot, with `ok`, `why`,
and `owner` — the workstream that owes the surface.

## The thirty-four

| | surface | | surface |
|---|---|---|---|
| 01 | idle | 18 | progressive stage 2 |
| 02 | listening | 19 | progressive complete |
| 03 | orders list | 20 | split creation |
| 04 | order detail | 21 | split independent left/right |
| 05 | order items | 22 | split branch ready |
| 06 | shipping | 23 | merge |
| 07 | customer summary | 24 | keyboard open |
| 08 | customer orders | 25 | long customer name |
| 09 | customer inbox | 26 | long address |
| 10 | full customer rich workspace | 27 | long product |
| 11 | inbox list | 28 | error section |
| 12 | email thread | 29 | empty email section |
| 13 | reply composer | 30 | notification local |
| 14 | sales overview | 31 | global offline |
| 15 | products overview | 32 | action proposal |
| 16 | returning customers result | 33 | action verified |
| 17 | compound activity, progressive stage 1 | 34 | stress collision fixture |

Shot **29** is not a stress fixture: it is the state the owner was looking at when he said *"I'm
not seeing any UI here except email where there's nothing"*, drawn from
`experience/fixtures/live_states.json` — a customer card opened on an empty Email tab, which
is what fourteen of the session's nineteen tabbed customer cards were.

Shot **34** additionally asserts zero interactive collisions on itself (§9), so the worst screen
the shop can produce is photographed *and* measured in the same pass.

## Where the rest of the instruments live

| what it asks | where |
|---|---|
| does anything overlap, at both sizes, as a hard release gate | `scripts/browser/collision.js` + `web/collide.js` (§9) |
| do the states the owner actually held replay, and are they fixed | `scripts/browser/replay.js` + `experience/fixtures/live_states.py` (§30) |
| can a finger walk the four real click paths | `scripts/browser/clickpath.js` (§33) |

All four run in `experience.browser.run_checks()`'s default sweep, so none of them can quietly
stop being called between releases — which is how `accept.js` came to be the only check that
had ever seen the duplicate `replaceCard`, and how `density.js` sat declared and unrun until
this pass.

## No customer is in any of these files

The fixture world is invented (`experience/fixtures/`), and the shots derived from the live
timeline carry invented people and four-digit id tails only — see the header of
`experience/fixtures/live_states.py` and `tests/test_live_replay.py`, which refuses a full
Shopify id or any address outside `example.com` in any committed byte of that derivation.
