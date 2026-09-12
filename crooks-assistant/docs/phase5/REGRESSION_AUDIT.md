# Phase 5 — regression audit

§34: *"Do not assume newer is better."*

**First, the fact that makes this audit possible and uncomfortable.** Phase 4 was pushed at
**05:47 on 11 September**. The physical tablet session ran at **20:11 the same day**, fourteen
hours later, and its timeline contains `owner_feedback` events — a family that did not exist
before Phase 4. So the owner was running the Phase 4 build.

Phase 4's report ended with a gate block declaring `601x889 COLLISIONS: ZERO`, `FAKE CONTROLS:
ZERO`, `P0 REMAINING: none`, `SAFE FOR PHYSICAL SAMSUNG TEST: YES`. Within fourteen hours the
physical test produced 63 swallowed control taps, a fake control, four collisions and the
largest P0 of the programme so far.

Those gate lines were not lies — every one of them was measured, and the measurements were
real. They were **the wrong measurements**, and three of them were wrong in a way that is
written down in my own comments. That is what this document is for.

---

## R-1 · The collision gate was configured blind to the element that caused the P0

**Original good behaviour:** none — this is not a regression. It is a false assurance, which is
worse, because it retired the suspicion that would have found the defect.

**What Phase 4 claimed:** `601x889 COLLISIONS: ZERO`, from 28 checks over 21 stress fixtures
under 7 geometry rules at both viewports.

**Current cause, in my own words.** `web/collide.js`, written in Phase 4:

```js
// Something a finger presses. `#talk` is deliberately absent: it is the transparent
// hold region that lies UNDER the dock by design, so counting it as a control would
// report the design as a defect. It is chrome here, and a card control that strays into
// its band is caught by `content_under_chrome` instead — which is the real fault.
control: [ 'button:not(#talk)', … ]
```

`#talk` was **deliberately excluded** from the control list, and placed in `chrome` — the list
of furniture that *messages must not cover*. The gate therefore asked "does anything cover the
voice region?" and never once asked "does the voice region cover anything?"

The stated justification — *"it lies UNDER the dock by design"* — is true in context mode,
where `#talk` is a 112 px band. It is **false in orb mode**, where
`body[data-mode="orb"] .talk{inset:0}` makes it the size of the viewport at `z-index: 3`, above
`.orb-zone`'s stacking context at `z-index: 1`, which contains the branch bar.

So the instrument was told, in writing, to ignore the one element that then swallowed 63 taps.

**Fix:** workstream G extends the gate with `Split-voice` and `branch-voice` pair rules and
makes an interactive overlap a hard failure at both viewports; workstream A removes the
condition being tested. **Both** are needed: a gate that cannot see a class of defect is worth
less than no gate, because it is trusted.

**Test:** `scripts/browser/collision.js` must fail on the pre-Phase-5 tree for
`Split-voice`/`branch-voice`, and `scripts/browser/touch.js` must record zero recording events
from control taps.

---

## R-2 · "Fake controls = zero" tested syntax, not resolution

**What Phase 4 claimed:** `FAKE CONTROLS: ZERO`, swept across 21 fixtures at both viewports by
the check *"every control either works, or says why it cannot"*.

**What the sweep actually asserted:** that an enabled control **carries** something to act on —
a non-empty `data-command`, `data-ref`, `data-area`, and that the value is not the literal
string `"null"`. It was written to catch a real bug (`data-command="null"` on every rail chip)
and it caught it.

**What it never asserted:** that the reference **resolves**. `turn_dd093f86b92d` posted
`open.entity` with a perfectly well-formed `data-ref` and the Mac refused it `not_held`. A
control with a syntactically valid reference to something the server does not hold passes the
Phase 4 sweep and is exactly the "refusal under a finger" §18 forbids.

**Fix:** §18 — resolve before drawing, or draw disabled with a reason (workstream A for branch
controls, B for entity surfaces, D for compact rows). **Test:** a control whose reference the
Mac would refuse must not be drawn enabled — asserted against the Mac's own holdings, not
against the attribute's shape.

---

## R-3 · COLLISION means two different things and the gate measured one

The live session recorded `COLLISION × 4`. All four are *"2 fingers landed on the dock at
once."* No geometry check can see that: it is not two rectangles overlapping, it is two pointers
claiming one target. Phase 4 measured **rectangle overlap** and reported it under a class name
that the analyser also uses for **pointer contention**, so a green geometry gate read as "no
collisions" when four pointer collisions had happened.

**Fix:** the two concepts get two names. Geometry stays `COLLISION`; pointer contention becomes
the touch-ownership machine's business (workstream A) with its own classes in the analyser
(workstream H). **Test:** two-finger-on-one-control is a case in the pointer suite, and the
geometry gate no longer claims to cover it.

---

## R-4 · The notification architecture was declared finished without a policy

**Original good behaviour:** Phase 4 genuinely improved this — it replaced one floating bubble
with three homes (CONTROL-LOCAL / WORKSPACE-LOCAL / GLOBAL) and moved the "other half has an
answer" message off the screen the owner was reading. That was right and it stands.

**What was missing:** any rule about *when to speak at all*. The live session produced **16
notifications, 11 of them with no text whatsoever**, and the five with text were `divided`,
`merged`, `divided`, `merged`, `divided` — state changes the screen already shows.

Phase 4 built the plumbing and called it done. §10 is the policy that should have come with it.

**Fix:** workstream F — a written policy, a cap, dedupe, and a rule that a notification with no
words is not a notification. **Test:** the eleven empty notifications of this session cannot
happen; `divided`/`merged`/`opened`/`tab changed` produce no global notification.

---

## R-5 · Per-card tab memory: wrong scope from birth, not a regression

Worth recording precisely, because it would be easy to file this as "a later rewrite broke it".
It is not.

`renderOpts().tab = branchState.tab` arrived on **2026-09-09** in `d04361a` — *"The screen: one
screenful at a time, buttons where the owner asked for them"* — the Phase 3 compact-tabbed-UI
work. Before that there were no tabs at all, so there is no earlier better behaviour to
restore.

The FEATURE was right: return to a card and it should still be on the tab you left it on. The
SCOPE was wrong on the day it was written — one value per *branch*, applied to every card that
has tabs — and it took a physical session to expose it, because in a synthetic test nobody taps
Email on one customer and then asks about a different one.

**Fix:** workstream E moves tab state to the entity. **Test:** tap Email on customer A, render
customer B, B does not open on Email.

---

## R-6 · Home was rebuilt and the owner still pressed it seven times in four seconds

**Original good behaviour:** unclear, and that is the finding. Phase 4 rebuilt `navigation.home`
from a trail move into a branch landing, with 20 tests, 4 golden scenarios and 11 browser
checks, because the Phase 3 session pressed Home eight times in twenty-two seconds.

The Phase 4 build then recorded:

```
20:12:41  home
20:15:17  home  home  home
20:15:20  home  home  home  home
```

Seven presses in four seconds, every one accepted, zero refused. Faster than before and no more
effective. Either it did not visibly arrive, or it arrived somewhere he did not recognise as
home, or it was not the control he was trying to press at all — and note that this burst sits
inside the window where the voice layer was eating his taps (R-1), so a share of these may be
the *chip he could reach* being pressed in frustration while the ones he wanted were dead.

**This is the one finding in this document I cannot fully explain from the timeline**, and it is
why §30 exists: the fix is a replay fixture built from this exact sequence (workstream G) rather
than a twentieth assertion about `navigation.home`'s return code.

---

## R-7 · Render suppression did not cover the path the live session used

Phase 4 added render suppression and measured it: 24 identical thread renders became 1 drawn
and 23 suppressed. The live session nonetheless recorded `DUPLICATE_RENDER × 8`, seven of them
in one turn (`turn_f0628fcf7be5`: `order_list + working_set + folded` drawn seven times, #2–#7
at 0.0 s apart).

The suppression Phase 4 built counts patches within the progressive workspace. The live
duplicates came through repeated whole-surface draws on one turn. The measurement was honest
and the coverage was partial, and the report quoted the measurement.

**Fix:** workstream E owns patch-in-place for the draw path; workstream H fixes the class so
that seven *different* entities are not reported as a duplicate at all (see the forensics
headline — three of the report's own top findings were false).

---

## What genuinely held up

Not everything newer was worse. These Phase 4 additions were load-bearing in the physical
session and are being kept and extended (§35):

- **Owner feedback.** Eight defects captured verbatim with branch, screen and held entities.
  Every substantive finding in this pass traces to one of those eight recordings. It is the
  single most valuable thing Phase 4 built — and the analyser then filed three of them as
  severity-5 `UNFULFILLED_ACTION` failures, which workstream H is fixing.
- **Backend vs owner-visible outcomes.** The dual column is why the session reads 24/6/14
  instead of 29/1/14. Without it this pass would have started from "mostly fine".
- **The read lanes.** Zero `landing_unavailable` refusals in the whole session, against three in
  Phase 3's hour. That defect is gone.
- **The action engine.** Zero proposals all evening, so it was not exercised — but nothing in
  the session suggests any weakening, and this pass does not touch it.
- **Tool reliability.** 40 calls, nine distinct tools, **100% success**. No tool failed.
- **Read correctness.** Context hydration never missed customer history, never missed email
  correlation, never left an order incomplete.

---

## The lesson this pass should carry

Every one of R-1 through R-4 is the same mistake in a different place: **a gate that measured
something real, reported it accurately, and did not measure the thing that mattered** — and
because it was green, it retired the question.

Phase 4's report said the browser gate went from 61 checks to 229. The count went up ninefold
and the blind spot that mattered was written into the fixture list as a deliberate exclusion.
More checks is not more coverage.

So for Phase 5 the standard is not "is the gate green" but **"can this gate fail for the reason
the owner actually complained about?"** — and the way that is proved is §37: every new test must
be shown to FAIL on the current tree before its fix lands. Not asserted to. Shown, with output.

---

## PRE-PHASE-5 BASELINE (§2)

Recorded on the starting tree, `925e398`, before any Phase 5 change:

```
python   2400 passed, 2 skipped   (11m16s)
ruff     All checks passed
node     203 tests across 9 files
browser  229 Chromium checks, 0 failed, 7 scripts, both viewports
```

The two skips are environment and not code: no Gmail token and no Shopify Keychain entry on
this machine. Every one of those 2,400 stays green through this pass unless the old behaviour
is provably wrong, and where an expectation changes the test itself says why — including the
several in this document that were provably measuring the wrong thing.
