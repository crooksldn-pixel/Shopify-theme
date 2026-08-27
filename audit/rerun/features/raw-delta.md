# Delta check — did this week's changes land? (run 2, staging preview)

Device: mobile 390x844 (dpr 3). Staging verified (.crk-root + crooks.css) on every
session. Date of run: 2026-08-27. All screenshots prefixed `rDELTA-` in
`audit/rerun/screens/`. Popup observed only — no phone number entered anywhere.

---

## 1 — Item descriptions

### cb2-wash-jeans
- **Should:** "OG jeans — blue wash, for the record. / 14oz denim, OG straight cut, mid rise. Structured, not baggy. / Made in Portugal."
- **Did:** ITEM DESCRIPTION accordion opens to exactly: "OG jeans — blue wash, for the record." / "14oz denim, OG straight cut, mid rise. Structured, not baggy." / "Made in Portugal." Three paragraphs, verbatim. (rDELTA-desc-cb2-wash-jeans)
- **Verdict:** LANDED.

### cb1-wash-jeans (the grey mirror)
- **Should:** The grey mirror of the above — three lines ending "Made in Portugal."
- **Did:** "OG jeans — grey wash, for the record." / "14oz denim, OG straight cut, mid rise. Structured, not baggy." — and stops. The third paragraph "Made in Portugal." is missing from the description (the SPECIFICATION accordion still lists Origin: Made in Portugal). (rDELTA-desc-cb1-wash-jeans)
- **Verdict:** LANDED WITH DRIFT — two paragraphs instead of three; "Made in Portugal." absent from the grey pair's description.

### charcoal-cellblock-crewneck
- **Should:** No delivery-times lines; mentions the Cellblock Set.
- **Did:** "Cellblock crewneck in charcoal — 450gsm brushed fleece, relaxed cut, 3D embroidery." / "Pairs with the Cellblock Shorts; sold together as the Cellblock Set." / "Made in Portugal." No delivery times anywhere in the description. (rDELTA-desc-charcoal-cellblock-crewneck)
- **Verdict:** LANDED.

### charcoal-cellblock-shorts
- **Should:** Same rules as the crewneck.
- **Did:** "Cellblock shorts in charcoal — 450gsm brushed fleece, relaxed cut finishing above the knee, 3D embroidery." / "Pairs with the Cellblock Crewneck; sold together as the Cellblock Set." / "Made in Portugal." No delivery times. (rDELTA-desc-charcoal-cellblock-shorts)
- **Verdict:** LANDED.

### evil-clive-tee
- **Should:** Says 220gsm and boxy.
- **Did:** "Money Clive tee — bold front graphic on 220gsm cotton." / "Boxy, drop-shoulder cut. Printed in London." Both present. (rDELTA-desc-evil-clive-tee)
- **Verdict:** LANDED.

### cellblock-set
- **Should:** Says "£85 against £95".
- **Did:** "The full Cellblock fit — charcoal crewneck and shorts in 450gsm brushed fleece, one line in the cart, a size chosen for each." / "£85 against £95 bought separately." (rDELTA-desc-cellblock-set)
- **Verdict:** LANDED.

### v2-baggies
- **Should:** "wide, full-length sweats… hang straight".
- **Did:** "V2 Baggies — wide, full-length sweats in 500gsm cotton, heavy enough to hang straight." / "Made in Portugal." (rDELTA-desc-v2-baggies)
- **Verdict:** LANDED.

### white-socks / black-socks
- **Should:** Mention packs, "Counted, not estimated".
- **Did:** White: "MotionTec™ socks in white and red — cotton blend, reinforced heel, made for constant movement." / "One pair, or packs of 3, 6 or 12. Counted, not estimated." Black: identical structure ("in black and blue"). (rDELTA-desc-white-socks, rDELTA-desc-black-socks)
- **Verdict:** LANDED (both).

---

## 2 — Measurements (accordion + SIZE GUIDE + cm/in toggle)

Checked on cb2-wash-jeans, charcoal-cellblock-crewneck, crxst-rz-t-shirt,
cb1-wash-jorts, charcoal-cellblock-shorts, v2-baggies.

### Caption
- **Should:** "True to size — waist, chest and leg measurements are taken around the garment…" (per MEASUREMENTS.md revision 2).
- **Did:** On all six products the visible caption reads, verbatim: "True to size. These are the garment's own full measurements." (rendered uppercase by CSS). No "taken around the garment" clause, no "All measurements in centimetres/inches" tail — on any product, in either unit.
- **Verdict:** DRIFT — the true-to-size intent landed but the wording is a different, shorter sentence than the one the fix documented. "The garment's own full measurements" is arguably *less* clear about girth-vs-flat than the documented line.

### IN toggle numbers
- **Should:** Clean industry numbers — jeans waist 30/32/34/36/38; crewneck chest 43–51; tee chest 39.5–47.
- **Did:**
  - cb2-wash-jeans IN: waist 30/32/34/36/38, inseam 29/30/30.5/31.5/32, leg opening 18–22. Exact.
  - v2-baggies IN: identical to the jeans chart (per the "denim chart" ruling). Exact.
  - crewneck IN: chest 43/45/47/49/51, length 25.7–28.7, shoulder 18.5–22.5, sleeve 24.5–26.5. Exact.
  - crxst-rz-t-shirt IN: chest 39.5/41.5/43.5/45.5/47. Exact.
  - cb1-wash-jorts IN: waist 30–38, hip 40–48, thigh 27.5–31.5, leg opening 23–27, length 21.5–24.6. Clean.
  - cellblock-shorts IN: fits waist 28/30/32/34/36, length 19.5–23.5, leg opening 23–31. Clean.
- **Verdict:** LANDED — every IN cell is a clean industry number, matching the documented charts.

### CM view + toggle behaviour
- **Should:** CM shows one-decimal values; toggle actually converts; rows render with headers.
- **Did:** CM default shows one-decimal values (e.g. jeans waist 76.2/81.3/86.4/91.4/96.5cm — exactly IN × 2.54). Tapping IN converts every cell and marks IN pressed (aria-pressed flips); tapping CM converts back to the identical original values — round-trip exact. Tables render as real tables with header rows: SIZE/WAIST/INSEAM/LEG OPENING (jeans, baggies), SIZE/CHEST/LENGTH/SHOULDER/SLEEVE (crewneck), SIZE/CHEST/LENGTH/SHOULDER (tee), SIZE/WAIST/HIP/THIGH/LEG OPENING/LENGTH (jorts), SIZE/FITS WAIST/LENGTH/LEG OPENING (shorts). (rDELTA-meas-*-default / -in)
- **Verdict:** LANDED.

### SIZE GUIDE button
- **Should:** Usable route into the measurements.
- **Did:** The buy-area "SIZE GUIDE" text button scrolls to and opens the MEASUREMENTS accordion in place — there is no separate modal. Same table, same toggle. (rDELTA-sizeguide-*)
- **Verdict:** WORKS (as an anchor, not a modal).

### NEW products — pink-crsdr-joggers, black-joggers
- **Should:** (Presence check only — absence is a finding, not a failure of the fix.)
- **Did:**
  - pink-crsdr-joggers ("PINK CONVICT SWEATS"): NO measurements accordion, NO specification, NO item description, NO size guide button. The only accordion on the page is Chain of Custody. Size row is bare XS–XL letters with nothing behind them. (rDELTA-meas-pink-crsdr-joggers-none, rDELTA-pdp-pink-crsdr-joggers)
  - black-joggers ("BLACK CONVICT JOGGERS"): NO measurements accordion, NO specification, NO size guide. It has an ITEM DESCRIPTION, but it is raw old-store text, verbatim: "500GSM - 100% cotton 14-25 days delivery uk 16-27 days international 5,1-5,4 XS 5,5-5,7 S 5,8-5,10 M 5,11-6,1 L 6,1+ XL" — i.e. the exact delivery-times lines that were scrubbed from the rest of the catalogue, contradicting the custody accordion one tap above it (UK 1–2 working days), plus comma-decimal height-range sizing in place of a chart. (rDELTA-meas-black-joggers-none, rDELTA-pdp-black-joggers)
- **Verdict:** FINDING — the two new products missed the whole descriptions + measurements pass. Black-joggers actively reintroduces the delivery-times contradiction the pass removed.

---

## 3 — Returns email

- **Should:** Custody accordion's returns line says crooksldn@gmail.com.
- **Did:** On every PDP sampled (all 11 in this check), step "04 Delivered" ends: "Start a return by email: crooksldn@gmail.com." No info@ anywhere in the accordion.
- **Verdict:** LANDED.

---

## 4 — "CROOKSLDN: The Getaway" popup (observe-only; nothing submitted)

### Appearance & load feel
- **Should:** Appear on a fresh session without the run-1 "empty box" load.
- **Did:** Fresh session, homepage, no interaction: the popup appeared **~33.7s after navigation** (sampled at 250ms intervals; not present at the 3.5s mark — the old 3s delay is gone, replaced by something in the ~30s region). It arrives as a full-screen theme-native sheet with **instant text** — title, copy and both buttons render in the same frame it appears; no empty box, no spinner, no iframe yet. (rDELTA-popup-t0-appear)
- **Verdict:** LANDED (load feel fixed; note the long ~30s fuse).

### Offer screen (verbatim)
- **Did:** "CROOKSLDN: THE GETAWAY" / "Crack the cuffs. 10% off your first order — code sent by text. Attempts unlimited." / [RUN IT] / [NOT NOW] / "One code per player." — 10% is stated up front; SMS delivery is stated up front ("code sent by text"). (rDELTA-popup-1-offer)
- **Verdict:** OFFER IS HONEST UP FRONT — but see the mismatch below: the code is actually delivered on-screen, not by text.

### Entering the game
- **Did:** Tapping RUN IT swaps the sheet to "OPENING THE LOCK-UP…" and lazy-loads the game iframe (crackthecuffs.base44.app); the game's own intro renders ~1.3–1.5s later. That intro is a **second, near-duplicate offer screen**: "CRACK THE CUFFS." / "10% off your first order if you do. Three tumblers. Tap each one at the right moment." / [RUN IT] / [NOT NOW] / "One code per player. Attempts unlimited. Code expires in 20 minutes." / "(this drop closes 15.09)". A shopper must press RUN IT twice on two different-looking screens to reach the game. (rDELTA-popup-2-game, rDELTA-popup-4-game-hydrated)
- **Verdict:** WORKS, one wrinkle — the doubled intro. Also the 20-minute expiry and drop close date are only disclosed on this second screen.

### The game
- **Did:** Three tumblers cycling digits, a draining timer bar, "TAP TO STOP" / "Tap each tumbler before the bar drains." / "0/3 LOCKED". Fully playable with taps only — no data entry of any kind before or during play. Tapped all three; "CUFFS OPEN", 3/3 LOCKED, straight to the win screen. Won first try. (rDELTA-popup-5-tumblers, rDELTA-popup-6-after-taps)
- **Verdict:** PLAYABLE, quick, no gate.

### Win screen — code/seal state, EXACTLY
- **Did:** For roughly the **first second after winning, the freshly-won code renders as expired**: the stamped card ("EVIDENCE Nº / GTWY-4FCN / 10% off. One use.") sits above a red line reading, verbatim, "CODE EXPIRED", and the copy button is disabled and reads "EXPIRED". Screenshot captured (rDELTA-popup-8-expired-flash). At ~1s it flips to the true state: "Expires in 19:58" counting down from 20:00, and the button becomes COPY CODE. Timed on three plays: expired-state window ≈0.9–1.0s in normal motion (visible from ~0.0s of the win screen), ≈0.9s under reduced motion (visible ~1.8s–2.7s after the taps, following the CUFFS OPEN transition). After the flash, the expiry line is fully legible, plain text, no gibberish, and counts down correctly ("Expires in 19:57… 19:46" observed over 12s). Full win screen verbatim: "EVIDENCE Nº / GTWY-SQ3H / 10% off. One use. / Expires in 19:46 / COPY CODE / Want it kept on file? Phone number goes in the evidence log — one message per drop, nothing else. Same promise as the register. / [07XXXXXXXXX] / FILE IT / Text me when the next drop lands — one message, then silence until the next one. / No need — I've got it". (rDELTA-popup-7-win-state)
- **Verdict:** ONE REAL BUG — every winner is shown "CODE EXPIRED" on their brand-new code for ~1 second before the countdown initialises. Everything after that is clean and legible.

### The SMS promise vs reality
- **Did:** The theme offer screen says "code sent by text", but on winning the code is displayed directly on screen with a COPY CODE button; the phone number is an optional *marketing* opt-in ("kept on file… one message per drop"), not the delivery mechanism. No phone number was entered or submitted at any point; the field was left untouched.
- **Verdict:** COPY MISMATCH between the outer offer ("code sent by text") and the actual flow (code on screen, SMS optional).

### Dismissal
- **Did:** "No need — I've got it" collapses the phone opt-in but leaves the popup open on the code card (rDELTA-popup-9-after-no-need); the theme's × closes the whole overlay and returns the page (rDELTA-popup-10-dismissed). Nothing was submitted.
- **Verdict:** DISMISSIBLE, two-step if you start from the opt-in.

### Reduced motion (fresh session, reducedMotion: true)
- **Did:** prefers-reduced-motion propagates into the iframe (matchMedia matches inside it). Theme overlay: transition 0s, no animation. In-game: zero Web Animations / CSS animations running at intro, during play, or on the win screen; the decorative cuff-spring / stamp-down animation elements of the normal win screen are absent. The tumbler digits still cycle (~2–3 ticks/s, JS content updates) — that is the game mechanic itself, not decoration. The ~1s CODE EXPIRED flash occurs in reduced motion too. (rDELTA-popup-rm-game, rDELTA-popup-rm-win, rDELTA-popup-rm-win-final)
- **Verdict:** REDUCED MOTION HONORED (decorative motion off; only the playable tumbler tick remains).

### Minor
- The game document's hidden SEO block is titled "Crack the Cuffs (Copy)" — a dev artifact; visually hidden but present in the DOM for screen readers.
- Codes are per-play (GTWY-SQ3H, GTWY-4FCN, GTWY-SFAX across three contexts) under "One code per player."

---

## 5 — Quick re-checks

### 404 page
- **Should:** (Re-check) Is /products/does-not-exist still the cream Horizon template?
- **Did:** Yes — dark crk header and announcement bar, then a cream (rgb 244,241,234) Horizon block in Horizon's own type: "PAGE NOT FOUND / The link may be incorrect, or the page has been removed. / Continue shopping / Discover something new". Same skin break as run 1. (rDELTA-404)
- **Verdict:** UNCHANGED — still the cream break.

### Light-mode SEARCH submit
- **Should:** (Re-check) Run 1 measured the SEARCH submit at 1.38:1 — near-invisible in light mode.
- **Did:** Toggled the header LIGHT MODE control (data-crk-theme="light"), opened /search: the submit is now a solid purple (rgb 84,37,120) fill with cream text — text-on-button 7.65:1, button-on-page 10.52:1. Clearly visible. (rDELTA-light-search)
- **Verdict:** FIXED.
