# SUMMARY.md — run 2, the same twenty shoppers on the new build

2026-08-27, fresh preview of staging theme `202053779799`, GB market,
staging verified per session. Compares against run 1 (2026-08-18/19) and the
Unfounded baseline. Persona 19 (desktop) results pending at time of writing;
19 journeys + a delta-check agent complete.

## Outcomes vs run 1

Committed to buy (built a basket with clear intent, stopped at the audit
line): 02, 03, 04, 05, 07, 08, 09, 10*, 11, 13, 14, 15, 16, 18 — with 09 now
buying the £50 crewneck she abandoned in run 1 (the size guide flipped her),
and 14 explicitly reversing his run-1 walkout ("would finish the order this
time"). Didn't: 01 and 06 (stock + the captcha, unchanged), and a NEW loss —
**17 walked on principle when her freshly-won Getaway code was rejected at
checkout.** 12 and 20 were service visits (both satisfied this run).
*10 decided (blue) without checking out.

**The loss profile changed shape: run 1's theme bugs (double-add, silent
adds, XS-preselect) stopped costing sales; what costs now is the popup's
unreliable code backing and inventory.**

## CONFIRMED FIXED since run 1 (persona-verified)

1. CHECKOUT NOW double-add — dead; one tap, correct £6 basket (14).
2. Silent add-to-bag — button answers "ADDING…" in 0.2s + inline confirm (14).
3. Silent XS preselect — gone; "Select Size, disabled" until chosen (16).
4. Filter reset on back-navigation — persists via ?cat= (10).
5. Landscape cart title/thumbnail overlap — clean 14px gap (13).
6. Light-mode search button — 1.38:1 → 7.65:1 (delta).
7. Tracking page signed-out lookup — EXISTS; FAQ promise now true (20).
8. Footer RETURNS link — returns route 7 taps → 1 (20).
9. Search "0 RESULTS" shouting — in-voice empty state + direct-link reorder (12).
10. Outline toggle — retired, treatment baked in per Q3 (11).
11. The whole content layer — descriptions verbatim, true-to-size tables with
    clean inch values, canonical email (delta, 03, 09, 16).
12. Legal identity — "Crooks Clothing Company LTD, England & Wales" in ToS (02).
13. Card-level size telegraphing — "2 OF 5 SIZES LEFT" (01, 06).
14. Popup vs the old Crack the Cuffs: instant-text offer naming 10% up front,
    focus-managed named dialog, keyboard/SR playable ("she'd tell the
    access-tech group chat"), reduced-motion mode ("No timer — take your
    time"), consent-gated timing, NOT NOW 14-day snooze (multiple).

## THE GETAWAY punch-list (evidence-ranked; maps to the staged UX plan)

1. **Code backing is unreliable** — 17's fresh code REJECTED at checkout
   (£45 cart → £50 till) while 11's and 13's codes redeemed fine when typed
   at checkout: minting sometimes has no real Shopify discount behind it.
   Stage 4's server-side mint with loud failure is the fix. Related: codes
   applied in the CART never survive the checkout hop (05, 09, 13 — retype
   works, single-use not burned).
2. **Win→loss race**: "CUFFS OPEN — cutting your code" resolving to CUFFS
   HOLD (13; systematic on throttled CPUs, 14). Expired-flash (~1s CODE
   EXPIRED before the countdown) reproduced by delta, 13, 16.
3. **Tumblers unresponsive on a throttled phone** — 10 taps, nothing locked
   (14): "the only part of the site still hostile to an old Android."
4. **COPY CODE hard-navigates to live crooksldn.com/collections/all** (15) —
   hardcoded production URL; ejects the shopper mid-session.
5. **Winners get re-pitched** — a win sets no flag (11, 15, 17); only NOT
   NOW sets the snooze (20 confirmed the snooze holds).
6. **"Code sent by text" is now false** and scares privacy-wary players (6
   journeys); "expires in 20 minutes" is a bluff — code worked past 20 (9):
   fake urgency AND factually wrong. Name exists in three variants
   (GETAWAY / CRACK THE CUFFS / PLAY CROOKS: THE GETAWAY) + "(Copy)" dev
   artifact in the DOM.
7. Double intro, dead black void, detached close-X (fat-finger kills the
   game, 9), win screen overflows a 450px viewport hiding FILE IT (17),
   perpetual tumbler tick with no pause under reduced motion (18).

## New store-side items

- **black-joggers shipped with the old template disease**: "14-25 days
  delivery uk … 5,1-5,4 XS" verbatim — new wrong numbers one tap above
  custody's 1–2 days; both new joggers lack spec/measurements entirely.
  The reconciliation needs a new-product checklist or it decays.
- **Rename drift**: GREY CONVICT SWEATS vs description "V2 Baggies —" and
  old alts (06, 16); YARD JEANS vs "OG jeans" copy (10).
- **Fit-truth conflict**: "Structured, not baggy" vs the worn photo, the
  alts ("baggy fit") and 18–22in leg openings (03, 10) — needs an owner
  ruling; the cut metafield may be wrong upstream.
- Grey jeans still 1 photo vs blue's 2 (10); ON MODEL still one placeholder
  man on 13 cards (10, 11); sub-£30 shipping price still invisible
  pre-checkout at the new threshold (07); 6-pack £25 lands £5 short of the
  £30 bar (07); ACCESSORIES chip off-screen at 390px (07, 11); cart-edit
  cluster escalated to a near-miss wrong basket (08); carriage bar still
  page-load-static (08); refund policy still the email/DM decoy (20);
  caption edited to "garment's own full measurements" — no longer says
  around-vs-flat (delta); checkout marketing pre-tick persists (09);
  "IDENTIFICATION REQUIRED" sits over a form needing none (20); tracking
  lookup GETs Aftership's ROOT url — owner must verify it lands on tracking
  (20); express-pay buttons still grey slabs on slow 4G (14).
