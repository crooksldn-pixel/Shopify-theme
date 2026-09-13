# CROOKS CONTROL — the redesign, and what was actually looked at

## The rejection was right

The first CROOKS Control worked. Every control on it did what it said, the operation layer
underneath it was sound, and the owner turned it down on sight. That judgement was correct and
this document does not soften it.

What was wrong was not the styling:

* enormous dead space, and generic macOS grey buttons in the middle of it
* seven integrations drawn as an admin table
* **ten controls visible at once** — Start, Stop, Restart, Health, Start Test, Stop Test, Open
  Report, Check Update, Install Update, Rollback — so none of them was the answer to anything
* a development Mac labelled **DEGRADED**, in the same red a broken one would get
* implementation language in the owner's sentences
* no answer at all to the only three questions anybody walks up to it with

None of that is a colour problem, and none of it could have been found by looking at a
screenshot. They are all **decisions**, which is why the fix is in `CrooksControlCore` and not in
a stylesheet.

## The three questions

```
  1. Is CROOKS OS ready?
  2. Is CROOKS Pad connected AND showing CROOKS?
  3. What is the one thing I can usefully do right now?
```

`Presentation.screen(...)` answers those three and composes **one screen per state**: a word, a
line, at most a sentence, at most the tablet, and **at most one button**. A capability existing
does not earn it permanent space.

## What decides what

| decision | where it lives | why there |
|---|---|---|
| which word, which colour, which single action | `CrooksControlCore/Presentation.swift` | a decision, so a test can drive it from a real document |
| whether that action may be drawn at all | `Presentation.pick(_:_:_:_:)` | invariant 12 — see below |
| where the pixels go | `CrooksControl/ScreenView.swift` | layout only; it branches on nothing |

`ScreenView` is the whole of the view layer for the front page. It draws a `Screen` and decides
nothing, which is the same split the rest of this app is built on and the only reason any of it
could be trusted on a machine that cannot compile SwiftUI.

## Invariant 12, and the button that nearly broke it

"No fake UI or control may be shown if the server cannot perform it."

The first draft of the redesign put **RELOAD THE TABLET** under the blank-tablet state. It reads
well and there is no such control: nothing on the Mac can reload the tablet's WebView, because
the fix is on the tablet, in the owner's hand. Drawing it would have been invariant 12 broken by
the very file that is supposed to enforce it.

So every action on the front page is resolved through `pick(...)`, which returns nil unless the
actions document really offers that id and has it enabled. The blank-tablet state therefore has
**no button**, and the sentence carries the owner instead. `test_the_front_page_offers_only_
controls_the_script_really_has` holds both the Swift and the render harness to the ids
`crooks-control actions` actually prints — and it was itself wrong first time, with a character
class that could not match `reload-pad`, which is exactly the id it existed to catch.

## The colour rules, and why green almost never appears

* **Healthy systems recede.** A calm screen carries ONE small green mark — the LED beside the
  wordmark — and nothing else. `READY` is drawn in bone; `CONNECTED` is drawn in bone. The
  expected case does not need a colour.
* **Amber is attention**, and it is spent once: `STOP & ANALYSE`, which interrupts something that
  is running. An available update is an OFFER, not an alarm, so it does not light the LED.
* **Red is actual failure**, and it states the problem — never the remedy. The primary action on
  a failed screen is **bone**, not red: the word above is already unmistakable, and painting the
  way out in the failure's own colour makes the one thing that helps look like the one thing to
  avoid.
* **Bone-filled means "press this"**, and it is deliberately not a colour. Prominence and
  approval are different things; a finished test is not a success worth congratulating.

## §10 — five things a subsystem can be, not two

```
  healthy · unhealthy · INTENTIONALLY DISCONNECTED · not configured · not required here
```

A development Mac whose store is a fixture is the third. Everything required of that machine is
working, so the word is **READY**, and the environment is named *beside* it in a small chip —
never instead of it. A panel that shouts DEGRADED at a correctly configured development Mac has
taught its owner, in one move, that its loudest word means nothing.

`environment_of()` derives this from what the backend already prints ("fixture backend" in a
check's detail) rather than from a new flag somebody has to remember to set.

## The window

The rejected build opened at **720 × 760** for a panel whose healthy state has four things on it.

It is now **420 wide, and as tall as its content** — 288pt at its sparsest (OFFLINE: a word, a
sentence, one button) to 398pt at its fullest. The height changes when the appliance changes
state, not on every poll. A fixed height forces either a void under a calm screen or a scroll
under a busy one, and the first of those is what was rejected.

There is no flexible `Spacer` anywhere in `ScreenView`. That is the whole mechanism: a Spacer
would grow to fill whatever height the window happened to be, which is how the black void gets
back in.

## What was actually rendered, and what that is worth

**This is not a screenshot of CROOKS Control.** This container has no Swift toolchain at all —
not merely no SwiftUI — so nothing in `mac/` has been compiled here, and the first `xcodebuild`
on the owner's Mac is still the first moment anyone learns whether the app builds.

What was rendered is a harness: `docs/phase6/tools/control_harness.html`, driven by
`control_screen.js`, which makes **the same decisions** `Presentation.swift` makes, in the same
palette, at the same window size. The twelve states it draws come from
`control_states.py`, which bends exactly one thing about a working Mac and then asks
`scripts/control.py` for the document it really produces. So the bytes being rendered are the
bytes the app would be handed.

That is worth something and it is not a visual review of the product. The honest claim is: **the
information architecture, the hierarchy, the density and the colour discipline have been looked
at; the SwiftUI has not been drawn.** The parity test above is what keeps the harness from
drifting away from the app it stands in for.

Fonts: the app ships in **SF Pro**, the correct native face for a Mac app. The harness renders in
Inter, which stands in for it — the weights and tracking are the ones the SwiftUI carries.

## The critique loop, in order

Seven rounds, each against real screenshots rather than against the code:

1. **Dead space, ~300pt of it.** The first render reproduced the exact defect the build was
   rejected for: content pinned to the bottom of a fixed-height window. Fixed by top-aligning the
   column and sizing the window to its content.
2. **Three greens on a calm screen** — the LED, the pad pip and the primary button. Cut to one.
   `CONNECTED` and the primary action both went to bone.
3. **The status light moved to the wordmark**, so the word stands alone. A pip beside a 38pt word
   floats; a LED beside a 10pt wordmark reads as an instrument.
4. **"The store is not working — the store said 401"** — service keys leaking as product
   language. `SERVICE_NAMES` translates them; the detail stays.
5. **Red remedy on a red screen.** The recovery button went bone.
6. **An available update lit the amber LED.** An offer is not an alarm; it went quiet.
7. **Two heroes in the test state** — a 38pt "PHYSICAL TEST" competing with a 46pt clock. The
   clock is the fact; the mode became a small-caps eyebrow above it.

Screenshots for all twelve are in `docs/phase6/evidence/control/`, with `_all.png` as the contact
sheet, because the twelve have to be judged against each other and not one at a time.
