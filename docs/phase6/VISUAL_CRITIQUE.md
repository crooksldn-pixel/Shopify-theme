# VISUAL CRITIQUE — §27

## Read this first: what was actually looked at

§27 asks for a visual review. A visual review means *looking at rendered pixels*. This section
exists so that nobody reads the critique below and believes more was seen than was seen.

| surface | rendered? | how |
|---|---|---|
| **the CROOKS web UI** (what CROOKS Pad shows) | **YES** | headless Chromium at 601×889, DPR 1.33 — the SM-T290's real portrait viewport |
| **CROOKS Control** (macOS, SwiftUI) | **NO** | this machine has no macOS SDK. `swiftc -typecheck` fails at line 1 with "no such module SwiftUI". Not one pixel of this app has ever been drawn, by anyone, at any point in Phase 6. |
| **CROOKS Pad** (Android shell chrome — recovery cards, diagnostics, PIN sheet) | **NO** | no `/dev/kvm`, so no emulator; no SM-T290 attached. No screenshot of this app exists. |

So of the three surfaces Phase 6 delivers, **one was seen and two were not.**

That is not a small caveat and it is not softened anywhere below. §26's list of traps includes
*"WebView rendered vs controls physically tappable"*; the honest extension is **"logic
unit-tested vs anything at all drawn on a screen"**, and two thirds of this phase's visible
product is on the wrong side of it.

Anything said below about the two unrendered surfaces is **reasoning about code**, labelled as
such. It is worth something — a layout that cannot compile is worth knowing about early — and
it is not a visual review. The documents that close this gap are
`CROOKS_PAD_ACCEPTANCE.md` and `COLD_BOOT_ACCEPTANCE.md`, both of which require a person and
hardware.

## What the unrendered surfaces mean for confidence

For CROOKS Control specifically, the exposure is larger than "we have not seen it", because
nothing has type-checked it either:

* `swiftc -parse` proves the view files are **valid Swift** and nothing more. It does not
  resolve SwiftUI or AppKit and it does not type-check. **It will pass a view that calls a
  method that does not exist.**
* Therefore the first `xcodebuild` on a real Mac is the first moment anyone learns whether this
  app compiles. It is reasonable to expect compile errors on that first attempt, and finding
  some would not indicate the design is wrong.
* The mitigation built into the design is the split: **every decision the app makes lives in
  `CrooksControlCore`, which is Foundation-only, builds here, and is unit-tested here.** What
  is left in the view layer is layout. So a compile failure on the Mac is expected to be a
  layout fix, not a logic fix — but that expectation is a *prediction*, and it is recorded here
  as one so it can be checked.

`verify.sh` must therefore never report a clean run as evidence that the app builds. That it
did — exiting 0 while printing "the Mac app builds — NOT RUN" — was a defect found and fixed in
this phase, and it is the same defect as every other one in §26: a check that cannot measure
something reporting success because nothing happened.

---

# The surface that could be seen

46 shots at 601×889 (the SM-T290's real portrait viewport) and 800×1280, plus 4 written as
`…MISSING.png` so that a directory listing is itself the report. The four missing ones are
Phase 5/P3-era markers — progressive hydration stages with nothing promised-but-unread to
photograph, and a split half that never reached READY — **not Phase 6 regressions.** None of
the four workstreams touches `web/`, so this pass is valid for the integrated head.

## 1. The composition seam — checked, and it holds

The thing worth suspecting first: inside CROOKS Pad there are now **two** layers that both
have an opinion about being offline. The web page draws its own banner; the shell draws its
own recovery card. If both are on screen, the owner is being told two things at once by one
appliance.

It holds, and it holds by construction rather than by luck:

* `PadActivity` has **one** place where a view's visibility is set. Exactly one layer is
  visible; the WebView goes `INVISIBLE` — not `GONE`, so the page keeps its real bounds and
  stays laid out at 601×889 — whenever the shell is showing anything of its own.
* The recovery card is a full-screen, **opaque** layout, not a translucent scrim.
* `PadLayoutTest` enforces three rules against the layout XML on every build: `web_host` is
  the first child, every sibling declared after it carries `visibility="gone"`, and no view
  may be transparent and full-size. **A new overlay that ships visible, or with no declared
  visibility, fails the build.**

That last one is Phase 4's defect turned into a build-time gate on a layout file — the right
response to a class of bug that "cost a Phase, produced a false engineering priority, and was
invisible in every log the system had".

**One real gap remains and it is a window, not a hole.** The shell learns the backend is gone
when its probe notices. Between the backend dying and the probe noticing, the WebView is still
the visible layer and what the owner sees is finding 2 below. That window is bounded by the
probe cadence; it is not unbounded, and it is not nothing.

## 2. "The Mac cannot be reached" over "SYSTEM READY." — a real contradiction

![the offline state] `601x889-31-global-offline.png`

Top of the screen:

> **FAILED** — The Mac cannot be reached. Nothing is lost; it will answer when it is back.

Middle of the same screen, unchanged from the healthy state:

> **SYSTEM READY.**
> What do you need?
> *HOLD TO SPEAK*

And the **Split** button, and the four dock destinations, all drawn exactly as they are when
everything works. Two sentences on one screen that cannot both be true, and a microphone
control offered by a system that has just said it cannot reach the machine that would answer.

It is worth being precise about what this is and is not:

* It is **not** a Phase 6 regression. It is the web layer's own behaviour and it predates this
  phase.
* It is **not** a Phase 6 fix. §4 forbids rewriting the browser presentation architecture in
  this pass, and I have not.
* It **is** invariant 12 — *"no fake UI or control may be shown if the server cannot perform
  it"* — reading false on one specific screen, and this phase is the first time anyone has
  looked at that screen at the viewport of the device it will actually be on.

Inside the Pad its blast radius is the detection window from finding 1; on a plain browser it
is unbounded. The smallest honest fix is for the orb's label and the speak affordance to take
the global reachability state they already receive: **"SYSTEM READY" should not be the phrase
on a screen whose banner says the Mac is unreachable.** Recorded, owner named, not done here.

## 3. The tab strip clips with no affordance — minor, and consistent

![order detail] `601x889-04-order-detail.png` and `…-34-stress-collision-fixture.png`

`OVERVIEW · ITEMS · SHIPPING · CUSTOMER · EMAIL` — and **EMAIL is cut in half by the right edge
of the card** at 601px, in the ordinary case as well as the stress case. The strip scrolls
horizontally and there is no fade, no chevron and no partial-chip gutter to say so.

A clipped word is itself a fair affordance and a finger will find it. But this is glass: there
is no hover, no scrollbar, and nothing that appears on approach. On a fixture operated at arm's
length by someone in the middle of a job, a 4px fade on the trailing edge would cost nothing
and remove the question.

Minor. Web layer. Not fixed here.

## 4. What the pass found working, which is most of it

* **At 601×889 the stress fixture holds.** A 43-character customer name wraps cleanly, a
  60-character e-mail wraps rather than overflowing, £1,284,367.45 fits on the same line as
  `#1938`, and four action buttons sit in a 2×2 grid each comfortably above a 48px target. No
  overlap anywhere — consistent with the Phase 5 collision gate's zero interactive collisions
  at this viewport.
* **Invariant 12 is visibly honoured in the navigation rail.** On `#1927`, `Previous` is drawn
  dimmed and dashed while `Back`, `Next` and `Split` are solid. A control that cannot act is
  drawn as one that cannot act, on screen, where the owner sees it — not merely refused on the
  server.
* **The dock survives the shell.** `HOLD TO SPEAK` is a large pill centred between the four
  destinations at the very bottom of the viewport. That position is only safe because the Pad
  runs sticky-immersive with no Android navigation bar; with one, it would be underneath it.
  **That dependency has never been seen on hardware** and is the first thing to check in
  `CROOKS_PAD_ACCEPTANCE.md` part 1.2.
* **The `…MISSING.png` convention is the right pattern** and should survive into V2: a shot
  whose surface does not exist is written as a named placeholder with the reason and the owning
  workstream in the filename and the report line, so a directory listing cannot quietly look
  complete.

## What this pass could not tell me

Everything about the two native surfaces, which is most of what Phase 6 built — and, on the
one surface it could see, everything that needs a finger rather than a rectangle. A headless
browser at 601×889 measures geometry. It does not measure whether a control is reachable by a
thumb on a tablet held one-handed, whether the dock is under a navigation bar, or whether a tap
lands where the owner meant it to.
