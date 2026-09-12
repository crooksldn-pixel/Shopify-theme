# CROOKS OS — Phase 5 product experience report

**Mission (§0):** *restore the wow factor; make CROOKS OS feel intuitive, rich, fast, visually
cohesive and deliberate.* Not a feature pass. The standard §42 sets is not "does the code
work" but **"does this feel like a finished product?"**

**Starting SHA** `925e398` (the Phase 4 tree the owner physically tested).
**Branch** `claude/crooks-assistant-build-lgxlau`. **Not deployed** (§41).

---

## 1 · What this pass was actually about

Phase 4 ended with a gate block reading `601x889 COLLISIONS: ZERO`, `FAKE CONTROLS: ZERO`,
`P0 REMAINING: none`, `SAFE FOR PHYSICAL SAMSUNG TEST: YES`. Fourteen hours later the owner
picked up the tablet and **63 of his taps became recordings**. He said, out loud, on the
record:

> *"I cannot click the merge or close button or any of the other buttons for the two blobs,
> because wherever I press just leads to you listening."*

None of those gate lines was a lie. Every one was measured. They were **the wrong
measurements** — and three of them were wrong in a way written down in my own comments from
the pass before. `docs/phase5/REGRESSION_AUDIT.md` is that accounting, and the standard it
sets for this pass is not "is the gate green" but **"can this gate fail for the reason the
owner actually complained about?"**

So the pass began by not trusting its own inputs.

## 2 · §0 — the analyser was wrong three times, and the brief said so first

The brief's opening instruction: *"Do NOT treat the generated proposals report as
authoritative… The automated analyser MISDIAGNOSED some physical interactions."*

It had. `docs/phase5/LIVE_SESSION_FORENSICS.md` reconstructs the evening from the raw
1,365-event JSONL and corrects the report three times:

| The report said | The timeline says |
|---|---|
| 62 × "precision input required" (severity 2, the single heaviest finding) | **63 ordinary control taps**, 39–140 ms, that the voice layer turned into recordings. The top finding of the whole session was a touch-routing bug wearing the costume of a speech problem. |
| "the same customer card drawn 7 times" (`DUPLICATE_RENDER`) | **Seven different customers.** Nothing was drawn twice. The real defect was a summary question answered with seven full profiles — 1,949 px of scrolling to say "one". |
| 3 × `UNFULFILLED_ACTION`, severity 5, component "the write tools" | **The owner-feedback system working.** Three of the eight defects he dictated were filed as failures of the thing that recorded them. |

Had the pass tuned the recogniser and added keyboard fields — which is what the top finding
literally asked for — it would have shipped a build in which the owner still could not press
Merge.

The same file names fifteen defects D-1…D-15, each with the owner's own words, a timestamp,
and the line of code that causes it. **Everything below traces to one of those fifteen.**

## 3 · The P0, and its actual cause

`web/style.css` in three lines:

```
--z-orb:1;  --z-context:2;  --z-talk:3;                    /* :65  */
.orb-zone{ position:relative; z-index:var(--z-orb) }       /* :132 */
.talk{ position:absolute; z-index:var(--z-talk) }          /* :515 */
body[data-mode="orb"] .talk{ inset:0 }                     /* :525 — the whole screen */
```

and `web/index.html:68`, where `#branch-bar` sat **inside** `<section id="orb-zone">`.

A positioned element with a `z-index` creates a stacking context, and everything inside it is
trapped below that level whatever its own `z-index` says. So the branch bar — Split, Merge,
Close, both half chips — was painted and hit-tested **under** a transparent, full-viewport
voice target. Every tap on it was a 95 ms hold. Every 95 ms hold was a recording too short to
use.

Two fixes, both needed. The condition is gone (the halves have their own band, outside the
orb's stacking context, with a pointer-ownership state machine deciding what a finger is
before anything reacts). And the instrument that could not see it now can: §30's replay
fixtures drive the real states with `elementFromPoint`, which is the only question geometry
cannot answer — *if a finger lands here, what does the browser hand it to?*

## 4 · Every section, and where it landed

| § | Asked for | Result |
|---|---|---|
| 0 | Reconstruct the session; do not trust the analyser | `LIVE_SESSION_FORENSICS.md`, 15 defects, 3 analyser corrections |
| 1 | VOICE = intent, TOUCH = navigation, TEXT = precision | The pointer machine assigns one owner per `pointerId` in the capture phase |
| 2 | Do not regress; record a baseline | Baseline in `REGRESSION_AUDIT.md`; the security, mutation, integration, audit and observability list is untouched |
| 3 | Intent-driven workspaces | `app/workspace.py` — the question is asked what surface it wants, and the answer is composed over the canonical entity |
| 4 | An explicit UI-intent contract | `app/capabilities/ui_intent.py` — show/open/pull up/bring up/expand/take me to/go to/view oblige a surface; speech alone is UNSUCCESSFUL whatever it said |
| 5 | Fix capability overmatching | "can you" alone no longer routes to capability; "can you access refunds?" still does |
| 6 | Normalise entities before presentation | `app/entities.py` — one canonical graph per conversation; `gid://shopify/Customer/7` and `7` are one customer |
| 7 | Touch ownership — P0 | CONTROL / SCROLL / VOICE / SPLIT_GESTURE / APPROVAL_GESTURE / NONE; **zero** control taps emit a recording |
| 8 | Separate navigation / voice / split physically | Three zones. The halves have their own band; the strip that carried 807 px in 571 px does not exist |
| 9 | Zero overlap as a hard release gate | Zero interactive collisions at 601×889 and 800×1280, over 21 stress fixtures and the live states |
| 10 | Notification de-spam | A written policy with a cap and dedupe; the 16 notifications (11 wordless) of the live session cannot recur |
| 11 | Restore the wow factor | See §5 below — subtraction first, and the before/after critiques |
| 12 | Rich workspaces | Composed surfaces with per-section states; the first screenful answers the question |
| 13 | Task-specific result surfaces | `summary_list` — a count and a row each, where seven profiles used to be |
| 14 | Fix N+1 reads | 8 reads → 2 on returning customers; the bound is asserted, not commented |
| 15 | Progressive rendering that feels progressive | Four measured numbers; a shell that names nothing no longer claims to be progress |
| 16 | Navigation must feel obvious | Home's arrival is measured as the screen changing, not as `ok=true` |
| 17 | Split as a premium feature | Four facts per half, from the Mac; one un-divide control per distinct outcome |
| 18 | Fake UI is forbidden | Resolve before drawing; a control whose destination the Mac would refuse is not drawn enabled |
| 19 | Visual state outranks the spoken claim | The composer that said "Gone" and stayed on the glass — §6 below |
| 20 | Preserve the owner-feedback system | Preserved and extended; a complaint no longer needs the word "log" |
| 21 | The analyser must stop chasing false defects | Four touch classes where there was one bucket of 62; the precision table 62 rows → 1 |
| 22 | STT only after touch | Untouched, deliberately. No audio reached the recogniser in those 63 events |
| 23 | Contextual UI self-knowledge | "What is on this screen?" is answered from the live screen with no model — §6 below |
| 24 | Interruptions and Stop | Held |
| 25 | Remove UI that does not earn its space | Controls audited and removed; one over-removal caught and reverted (§7) |
| 26 | Content hierarchy | EMPTY, THESE and `confident` are gone from the glass; a duplicated count line removed |
| 27 | Loading / empty / error states | Five states; EMPTY is not ERROR, and an empty section keeps its workspace |
| 28 | Animation and feel | Motion tokens held; nothing moves under a thumb while a section lands |
| 29 | 601×889 DPR 1.33 authoritative | Both viewports on every geometry gate |
| 30 | Replay REAL live states | Ten fixtures derived from the raw timeline, PII-scrubbed, driven in Chromium |
| 31 | A visual review loop | Two critiques, before and after, from photographs |
| 32 | A 34-shot matrix | 46 files; 5 MISSING with a named owner each (§8) |
| 33 | A real click-path matrix | 38 of 38, including a path that had never walked |
| 34 | Regression cleanup | `REGRESSION_AUDIT.md` — R-1…R-7, four of them my own |
| 35 | Keep the good Phase 4 work | Owner feedback, dual outcomes, read lanes, tool reliability — all kept and extended |
| 36 | Performance | No model on a summary turn; no read on a tap on a held row |
| 37 | Every new test must fail on the current tree | Shown with output, per workstream, in the commits |
| 38 | A final quality gate | §9 below |
| 39 | A physical acceptance script | `PHYSICAL_SAMSUNG_ACCEPTANCE.md` — 12 steps, on FEEL |
| 40 | This report | — |
| 41 | Do not deploy | Not deployed |
| 42 | The standard | Answered honestly in §10 |

## 5 · §11 — restoring the wow factor was mostly subtraction

The before-critique's governing finding, written before any change:

> **The visual language is not the problem.** The dark ground, the restrained type, the glass
> panels, the gold accent, the three stat tiles, the order rows — these are good. A high-end
> designer would keep almost all of it. §11 says "do not turn it into a generic admin
> dashboard", and the honest answer is that it is not one; it is a well-drawn interface with a
> badly organised screen.

So no restyling was done, and none was needed. What was done was subtraction: seven findings,
five of them fixed, each one returning vertical space or removing a contradiction.
`VISUAL_CRITIQUE_BEFORE.md` and `VISUAL_CRITIQUE_AFTER.md` are the two passes, and the second
one names what was deliberately NOT fixed and why.

Three defects were found **only by looking at pictures**, after the screens above them were
fixed. All three are the same class and none was caught by any test:

1. A half chip reading `#1927 Fionn Doherty28 Aug, 23:00£83.0…` — the record's human label,
   built by scraping the tapped row's whole `textContent`.
2. An inbox row reading `#1938 · confident` — the correlator's own grade for how sure the link
   is, printed at the owner.
3. `THESE 3 orders` — a machine word as a heading.

That is the §31 loop earning its place: *do not stop because tests are green if the
screenshots still look mediocre.*

## 6 · Three defects worth naming individually

**The composer that said it was gone.** `compose.discard` answers *"Gone. Nothing was saved."*,
clears the composer on the Mac and sends `changed.discarded` with no `ui`. Nothing on the
tablet acted on it. So Cancel spoke, the composer stayed, and the owner's next tap on it was
refused `no_composer` — the Mac had discarded a card the screen was still showing. §19 in one
control. Found by §33's click-path matrix, which had never walked PATH 3 to the end.

**"What is it doing?"** Two workstreams both claimed that sentence: one as a complaint, one as
a question about the screen. Recognised feedback takes a turn before anything else, so the
owner asking what was in front of him was told his complaint had been recorded. Both readings
are fair; the tie-break is that **one of them can be answered**, and a product able to say
what is on its own glass should say it.

**"The wrong customer, answered confidently."** D-14. A turn named one customer, the context
layer hydrated a different one that happened to be in focus, and the assistant stated a fact
about the wrong person — and the analyser scored the turn SUCCESSFUL, because the tool
succeeded and a card was drawn. The class exists now, and the regression test with it.

## 7 · WHAT WAS REMOVED

§40 asks for this explicitly.

**Removed, and not coming back:**
- **`#talk`'s reign over the idle screen.** The transparent full-viewport voice target that
  swallowed 63 taps. The hold region is now a bounded surface with an owner per pointer.
- **The eight-control navigation strip.** Six heterogeneous controls plus two branch chips in
  one 571 px row, with Merge at x=590 and Close at x=664 — off the glass. The halves moved to
  their own band; the strip holds the trail and the list cursor.
- **The unlabelled `‹` chip.** A 44 px bare glyph between Back and Next that the visual pass
  called "a tiny unlabelled chip that means nothing to anyone". It says *Previous*.
- **Merge over a half holding nothing.** Not because it fails — it returns 200, and the live
  session's own record proves it — but because keeping and letting go of nothing are one
  outcome, and §25 says one control per outcome.
- **Notifications that narrate the screen.** `divided`, `merged`, `opened`, `tab changed`:
  silent. And a notification with no words in it is not a notification.
- **A floating message beside a control that already says why it is disabled.** The control
  carries its own outcome.
- **`EMPTY`, `WORKSPACE`, `THESE`, `confident`, `possible`** as words on the glass. Database
  and correlator tokens that had leaked to the surface.
- **The duplicated count line.** `3 orders` printed 40 px above a tile reading `3 / ORDERS`.
- **A card's `textContent` as a human label.** Nothing is scraped now; the renderers say what
  a record is called.
- **Two dead ends in the entity graph.** Order → customer was unwalkable at step 4 of 8.

**Removed and then RESTORED**, because the pass got it wrong:
- Three controls, including `note` and `dictate` — the only touch paths that bind the
  microphone to a record — and a cap of 2 enabled / 1 primary that dropped `address`, the one
  chip the owner actually tapped. The lesson is written into the test that now guards it:
  **a control nobody taps is not the same as a control nobody needs.**

**Deliberately NOT removed**, with the reason recorded:
- The working-set strip beside a listing, which duplicates a stat tile. A green test asserts
  it, the forensics does not call it wrong, and §2 forbids changing an expectation on a
  debatable basis.
- The row chevron. Measured, overlaps nothing, and it is the only visible sign that a row can
  be pressed.
- The area kicker on a single-card deck. One line of small uppercase, and on a mixed deck it
  is the only thing telling two cards apart.

## 8 · The instruments, and what they can now fail for

The point of §30 and §34 is that a green gate should mean something. What changed:

- **`hit_test`** asks `elementFromPoint` at a control's centre what the browser would hand a
  finger to. This is the only check that could have caught the P0, and rectangle geometry
  cannot do it.
- **`undivide_controls`** asserts the un-divide strip as a SET and then hit-tests every member
  — so it fails on a missing Merge, on a Merge that has nothing to do, and on either being
  unreachable.
- **Ancestor invisibility** now propagates in the collision collector. `opacity` is not an
  inherited computed value, so a control inside a footer folded away by design read as a
  48 px navigation control the layout had squeezed — and the code names the LIMIT of the fix,
  because R-1 is what happens when one does not: a faded element is still hit-testable, and
  geometry must not be trusted on that question.
- **The §4 contract table** knows the composed surfaces. It had judged the richest possible
  answer to a request UNSUCCESSFUL because the word `customer` was not among the card types.
- **Five screenshot expectations** were the defect rather than the state: one rejected
  `summary_list` (the answer to D-4), one photographed a notification §10 now correctly
  silences, one reached its state through the D-2 defect itself.
- **The analyser** ranks by severity before frequency, with a confidence discount on inferred
  findings, so 2 × 62 taps can no longer outrank every P0.

Four shots remain MISSING, each saved under that name with its reason and owner in the file
name. They are named rather than quietly absent, which is the §32 requirement — and one of
them has a specific cause worth writing down rather than leaving as "not produced":

**`present(pending=…)` has no live caller, so no section is ever drawn as LOADING.** The
workspace composition accepts `pending` and each section renderer honours it; the two
vocabularies were even checked and found compatible (`_hit` in app/workspace.py takes the
section's own name and its aliases, so E's "orders"/"inbox" and B's "email" all land). What
is missing is a place to call it from:

* `progressive.observe()` calls `present()` with **no session** on purpose — so that early
  staging does not put a record on the context stack the owner never saw, or issue an id
  nobody was shown — and `_compose_workspace` returns immediately without one. So `pending`
  passed there would be discarded.
* the turn's own `present()` (app/routes/turn.py) runs when the turn is **over**, by which
  point every read has landed or failed and `in_flight` is empty by construction.

So the section that is still reading is not drawn as loading — it is simply not drawn yet,
and appears when it lands. That is honest but it is not §15's "watch each one fill in", and
it is why shots 17–19 cannot be photographed: there is no promised-but-unread card on the
glass to photograph.

Deliberately NOT wired. E left this join unwired and said why ("guessing which it wants
would have been a silent mismatch"); the remaining gap is not the vocabulary but the call
site, and adding the line at the site E named would be a no-op that LOOKS done — which is
worse than the gap, and is the exact failure mode §34 is about. The fix is a composition
that runs while reads are in flight, which is a piece of work, not a line.

## 8b · What the final gate found, which is the point of having one

Worth recording separately, because the pass would have reported itself finished without it.
The full suite was green at 2,812 passed / 2 failed, and those two failures carried twelve
browser checks between them. Six of the twelve were instruments; **three were real**:

- **D-6's whole CLASS, not the instance.** §33's sweep tried every `[data-ref]` on a products
  landing and three product rows were refused `not_held`. `app/analytics/present.py` takes
  `ref`/`kind` off an aggregate's GROUP KEY, and it is handed a read result and no session —
  so it cannot ask whether a record is openable at all. Every product an aggregate grouped by
  got a tappable row whether the Mac had read it or not. Fixed as a sweep where the session
  is, asking the two things the tap will ask.
- **The label scrape a second time**, visible in the gate's own failure text:
  `"1Convict Hoodie3units£180.00 r"`. Ranking rows carried no name of their own.
- **A bug of my own**, and the reason every state also asserts `no script error while
  replaying it`: I added `fx()` to a branch without adding it to the function's signature,
  and one undefined name failed a whole state and took its other eight checks with it.

And one finding that is a lesson rather than a defect. Fixing D-6 made
`no_control_carries_unheld_ref` **unmeasurable** — with every dead ref correctly withheld,
that deck offers nothing, and the check reported "0 offered ... so §18 could not be
measured" rather than passing. It was right to. *Unmeasurable is not satisfied*, and a gate
that goes green because nothing happened is how the Phase 4 suite stayed green. So the
fixture now drives both directions on two decks: the ranking's refs withheld while its
figures survive, then a deck whose offers the Mac does hold — because without that second
leg the sweep could have withheld EVERY ref on the product and nothing would have noticed.

Three fixtures also turned out to be asserting the DEFECT, which is what the FIXTURE half of
a live state is for: it reproduces what the tablet recorded. Two of those states can no
longer be reproduced, because the fix is in the renderer the fixture drives. Each became the
claim that now matters rather than being weakened — `no_card_open_on` is a rule where
`every_card_open_on` had been a description.

## 9 · §38 — the final gate

Run from a clean head, in one process, with nothing else on the machine — which matters: the
parallel workstreams left 50+ Chromium processes on the box and a single-process run was
SIGTERM-killed at ~14% three times during the pass. The numbers are in the block at the end
of this pass's final message.

What each gate line in that block actually measures, so it can be disagreed with:

| Line | The measurement behind it |
|---|---|
| FULL TEST RESULT | `pytest -q` over the whole tree, one process, browser tests included inline |
| LIVE-STATE REPLAY | `scripts/browser/replay.js` — the ten §30 fixtures derived from the raw timeline, driven in Chromium at 601×889 DPR 1.33, with `elementFromPoint` hit tests and real pointer presses at the durations the tablet recorded |
| 601x889 COLLISIONS | `scripts/browser/collision.js` — the count of geometry hits naming an interactive element on either side, over 21 stress fixtures plus the three new divided states, at both viewports. NOT the total hit count: a sideways document scroll is a hit and is not a collision |
| FAKE CONTROLS | The §18 sweep — every element a thumb would read as a control, on every fixture, at both viewports: it works, or it is visibly disabled with a reason. Since this pass it also asks whether the DESTINATION resolves, not only whether the attribute is well-formed, which is what R-2 was about |
| CONTROL-TAP VOICE LEAKS | `scripts/browser/touch.js` — real pointer presses on real controls, counting recording events. The bar the brief sets is **zero**, not "better" |
| P0 REMAINING | Defects from `LIVE_SESSION_FORENSICS.md` still unfixed at severity 6 |

## 10 · §42 — the honest answer

*Does this feel like a finished product?*

**Not yet — but for the first time the remaining distance is a matter of taste rather than of
faults.** The things the owner hit last time are gone at the cause, not at the symptom: a tap
is a tap, a request to see produces something to look at, a count is a count and not seven
profiles, a half says what it is, and nothing floats up to tell him what he can already see.

What is not finished is the part no gate can measure. The first screenful of a rich workspace
is right on the surfaces this pass composed and ordinary on the ones it did not. The
animation work of §28 is tokens and restraint rather than anything anyone would call
delightful. And the honest test — *could you hand this to somebody with no explanation?* — is
step 12 of the acceptance script for a reason: **I cannot answer it from here.** Everything in
this pass that mattered was found by a man holding the tablet and saying what he saw, and the
two instruments that found the rest of it were a photograph and a click path, not a test
suite.

So: safe to hand him, worth twenty minutes of his time, and the next pass should start the way
this one did — with what he says while he is holding it.
