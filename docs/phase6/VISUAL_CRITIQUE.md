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

<!-- The critique of the rendered surface follows, written after the integrated head was
     built. Nothing above is contingent on it. -->
