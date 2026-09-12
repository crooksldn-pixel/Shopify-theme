# The scoreboard

§37 requires every new test to fail on the current implementation before its fix lands. So the
gates arrived first and the tree is deliberately red. This file is the count, and the pass is
finished when it reaches zero.

Measured on `f3e46ee` — forensics + regression audit + workstreams B and G merged, nothing else.

| Gate | Checks | Red | What the red ones are waiting for |
|---|---|---|---|
| `scripts/browser/collision.js` (§9) | 92 | **18** | A — DOM layering and touch ownership |
| `scripts/browser/replay.js` (§30) | 69 | **21** | A (14), C (6), B/D (1 each) |
| `scripts/browser/clickpath.js` (§33) | 38 | **8** | D — an order card offers no way to its customer; an inert Cancel |
| `docs/screens/phase5/` (§32) | 48 | **6 MISSING** | B/C/D/E — the surfaces do not exist yet |

**47 named failures and 6 unphotographable surfaces.**

## The four that matter most, verbatim from the gate

```
"Split" → the hit test at its centre reaches span#talk-label.talk-label
4× button.branch-chip → the hit test at its centre reaches button#talk.talk
26 taps of 39-140 ms on #branch-bar [data-action="split"] emit no recording
    → 26 recording(s) started, 26 "too short", 0 turn(s)
a DOM click took branches 1→2 — the control is wired; the touch never reached it
```

The last line is D-1 in one sentence. The control works; the finger never gets there.

## Why the Phase 4 gate was green through all of this

The new Split/branch-voice rules ask **the browser's own hit test** — `elementFromPoint` at the
control's centre — rather than comparing rectangles. D-1 was never a visible overlap: `#talk` is
transparent and full-viewport, so no two painted rectangles intersect. Phase 4's gate compared
rectangles and was correct in everything it measured. See R-1 in `REGRESSION_AUDIT.md`.

## Not a gate, but worth the same attention

- `tests/test_live_replay.py::test_the_fixtures_still_match_the_timeline_they_came_from` SKIPS in
  a worktree, because the timeline is gitignored and the conftest strips `CROOKS_*`. It runs on
  the owner's Mac. The comparison was verified by hand: 10 states, 0 drifted.
- The full suite cannot be run in one process on this box while the fleet is working — 50+
  Chromium processes, and a single-process run is SIGTERM-killed inside the browser tests. Both
  halves green is the valid result until the box is quiet, and the final §38 run from clean HEAD
  must be done in one piece with nothing else running.
