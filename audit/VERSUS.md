# VERSUS.md — CROOKSLDN vs Unfounded Studios, head to head

Same battery, same personas, same harness. CROOKSLDN was audited on its
staging theme (2026-08-18, forms exercised with owner authorisation);
Unfounded on its live site (2026-08-19, strict read-only — forms observed,
never submitted, sessions stopped at the checkout landing). That scope
difference is noted where it matters. Evidence: `features/`, `journeys/`,
`unfounded/` in this directory.

## The headline

**Both stores' shoppers abandoned for the same reason, and it was never the
design.** CROOKSLDN: 15/20 reached checkout; every loss was stock, a captcha,
a self-contradiction or a cart bug. Unfounded: 14/20; every true loss was
stock — compounded by having built *no* machinery to capture the demand it
turns away. The comparison is not "which looks better"; it's two different
failure modes of the same drops business:

> **CROOKSLDN built the right machines and several are broken.
> Unfounded never built the machines at all.**
> Repair beats construction — CROOKSLDN's gap is days of fixes;
> Unfounded's is missing organs.

## The scoreboard — 14 dimensions

| Dimension | CROOKSLDN | Unfounded | Winner |
|---|---|---|---|
| **Stock reality** | 14/15 products buyable; 1 with dead sizes | **12/44 buyable; zero size-M in the store**; flagship line 0/10 incl. pre-orders | **CROOKSLDN**, decisively |
| **Sold-out handling** | Honest per-size states, red "SIZE M IS SOLD OUT", per-size notify form (its captcha is the defect) | No notify anywhere; dead-but-lit Buy-with-Shop buttons; "Only 0 left. Order soon." | **CROOKSLDN** — its worst version of this is their missing best |
| **Sold-out telegraphing on cards** | Blanket `AVAILABLE` until the PDP (personas 1, 6 burned a click) | **SOLD OUT badges pre-click**; but "Available in 5 size" oversells live cards | **Unfounded** — the one honesty dimension they win |
| **Product information** | Measurement tables + cm/in + SIZE GUIDE anchor — *closed two sales*; data gaps known | Descriptions are one shipping line; chart buried as an unlabelled photo; no fabric/fit/care text on a "heavyweight organic cotton" brand | **CROOKSLDN**, decisively |
| **Photography & zoom** | 1–2 photos, no zoom of any kind | 5–11 photos with on-model shots on the flagship; full-res double-tap zoom (mobile); but buyable items often 1 photo, desktop zoom-cursor dead, lightbox shrinks the size chart | **Unfounded** on assets; split on delivery |
| **Add-to-bag feedback** | Quiet aria-live line + badge; silent from sticky bar and on desktop → 3 double-adds, one £12-for-£6 near-abandonment | **Cart drawer with certainty in ~1.5s even on slow 4G**; quick-add from cards and search | **Unfounded**, decisively |
| **Cart correctness** | Exact through 7 edits; decrease-at-1 no-op; badge stale during cart ops | Penny-perfect through 9 states incl. honest stock-cap; one stepper desync; note field unwired; `href="false"` 404 button | Tie on maths; both flawed at the edges |
| **Upsell / set machinery** | £85 set converted two £50 intents and survived a sceptic (cart-side confirmation bugged) | No bundle mechanic; three EMPTY set collections (one in the main menu); ONE same-size two-piece purchasable store-wide | **CROOKSLDN**, decisively |
| **Shipping-cost transparency** | Tiers advertised everywhere; £3/£4.99 findable (2 taps; should be 0) | **Unknowable before an address** — policy page 404s, no number exists on the site | **CROOKSLDN** |
| **Promise consistency** | Theme surfaces agree to the penny; contradictions live in stale descriptions, returns windows, third parties | 2-5 vs 5-7 day dispatch lines with no policy to arbitrate; empty "Black Friday" in August; SALE labels with zero markdowns; duplicates at £50 vs £40 | **CROOKSLDN** — its contradictions are copy bugs; theirs are structural |
| **Checkout & payments** | Rate card matches promise to the penny; **stock white skin, no logo** — the "costume change" | **Branded door** (logo, palette), Shop Pay/G Pay, penny-perfect totals; terms checkbox silently blocks with a typo | **Unfounded** on brand; CROOKSLDN on price honesty |
| **Trust anchors (no reviews on either)** | Exact numbers, honest states, no fake urgency; but gmail support, no legal identity, unexplained "Oairo" | **Companies House + VAT + founder story + real return address**; but 404 policies, theme-dev's Instagram as "Follow Us", Bosnia map pin, typos | Split — each holds the other's missing half |
| **Accessibility & conditions** | Clean sweep: keyboard, SR, 200%, landscape (one cart overlap), **zero animation under reduced motion**; slow-4G readable at 3s | Keyboard/zoom fundamentals good; SR poisoned by "sold out" text on every size + nameless Escape-proof popup; **reduced motion respected by nothing**; slow-4G wordless 8–10s | **CROOKSLDN**, decisively |
| **Desktop** | Second-class: no hover states, half-empty hero, no sticky bar | **Their best surface**: hover image-swap, quick-add, sticky buy bar, predictive search | **Unfounded**, decisively |
| **Post-purchase** | Tracking page + branded AfterShip portal (FAQ oversells the former) | Nothing on-site; "track order" search returns track pants; email-only returns | **CROOKSLDN** |

**Tally: CROOKSLDN 9 · Unfounded 4 · split/tie 2.**

## What each store should steal from the other

**CROOKSLDN should take (all compatible with the design law):**
1. **The add-to-cart drawer moment** — not their drawer necessarily, but the
   *certainty in 1.5s where your eyes are*. Their best mechanic; your
   biggest recurring friction (7 journeys, 3 double-adds).
2. **Pre-click sold-out truth on cards** — their SOLD OUT badges spared
   shoppers the wasted click your blanket AVAILABLE costs. (SPEC §9.5
   protects the status slot's *format*; a size-aware status is an addition,
   argued from personas 1 and 6 — exactly the journey evidence §8 demands.)
3. **A branded checkout** — they prove a small Shopify store can hold its
   identity through the door. Yours is config, not code.
4. **A legal identity line** — their Companies House number + founder story
   did in seconds what your sceptic spent 25 minutes assembling.
5. **An in-stock filter** — trivial on your 15 products today, load-bearing
   the day your catalogue grows.
6. **Photography ambition** — on-model shots and real zoom sold their
   flagship; your two-flat-photos-no-zoom is the biggest gap between your
   product page's words (excellent) and its pictures.

**Unfounded would need from CROOKSLDN** (recorded for completeness): the
entire information layer (measurements, specs, honest dispatch maths), a
notify mechanism, a set mechanic, shipping transparency, reduced-motion
respect, and copy that agrees with itself. That is not a list of features —
it is most of a storefront.

## The strategic read

Unfounded is a live demonstration of the drops model running without demand
capture: 32 unbuyable products displayed as a museum, sale theatre nobody
priced, and every turned-away shopper leaving no trace. CROOKSLDN's audit
found its three capture machines broken (intake unmounted, notify behind a
captcha, game payout dead) — **the difference is that yours exist.** Fix the
three (days of work, mostly config) and CROOKSLDN holds every dimension that
decides a drops brand's future: information that closes sales, promises that
reconcile, demand that gets banked. Then steal their drawer, their badges,
their branded checkout, and their photography ambition — all of it
implementable without a single rounded corner.

---

# RUN 2 — the rematch (2026-08-27)

The same twenty personas re-ran against the NEW CROOKSLDN build (fresh
preview of staging `202053779799`; Getaway popup observed, never fed a phone
number). Unfounded was NOT re-audited — the baseline stands. Full run-2
evidence: `rerun/journeys/`, `rerun/SUMMARY.md`, `rerun/features/raw-delta.md`.
Persona 19 (desktop) was still in flight at write-up; the desktop dimension
below keeps its run-1 verdict pending that log.

## Chips that moved

| Dimension | Was | Now | Why it moved |
|---|---|---|---|
| Add-to-bag feedback | **Unfounded**, decisively | **TIE** | "ADDING…" answers in 0.2s + inline confirm; CHECKOUT NOW double-add dead; persona 14 ("Twelve quid? For socks?") returned and bought clean. Their drawer still wins quick-add from cards; certainty itself is now equal. |
| Sold-out on cards | **Unfounded** | **TIE** | Register cards now say "2 OF 5 SIZES LEFT" pre-click (personas 1, 6 both cited it as the best moment). MORE FROM THIS DROP cards are still blind — that last gap keeps it from flipping fully. |
| Trust anchors | Split | **CROOKSLDN** | "Crooks Clothing Company LTD, England & Wales" now in the terms — the sceptic called it "the single strongest thing on this site" and passed his vetting. Canonical email + true-to-size tables compound it. Their Companies House record still stands opposite gmail + the Oairo mystery, but the halves are no longer even. |

Everything else held: CROOKSLDN keeps stock reality, sold-out handling,
product information (now stronger — council descriptions + measurements on
every garment checked), set machinery, shipping transparency, promise
consistency, accessibility (now stronger — the popup is keyboard/SR/PRM
playable) and post-purchase (now stronger — signed-out tracking lookup,
1-tap RETURNS). Unfounded keeps photography & zoom, checkout branding, and
(pending 19) desktop.

**Run-2 tally by chip: CROOKSLDN 9 · Unfounded 3 · split/tie 3** (run 1 by
the same per-row count: 8 · 5 · 2).

## The shopper ledger, run over run

Run 1: 15/20 reached checkout; losses 1, 6, 12, 14; service 20.
Run 2: 14/19 decided-or-checkout so far (19 pending); losses 1, 6, **17**;
service 12 and 20, both satisfied.

- **12 flipped loss → satisfied** — every search query landed; the empty
  state now answers in voice.
- **14 flipped loss → buy** — "the two things that beat him last week —
  the dead button and the phantom second pair — both gone."
- **9 upgraded** — bought the £50 crewneck she abandoned in run 1; the new
  measurements table flipped her.
- **17 flipped buy → loss, the run's one regression** — her freshly-won
  Getaway code was rejected at Shopify checkout (£45 cart vs £50 till,
  reproduced twice). She walked on principle. The popup's back office is
  now the single most expensive defect on the site.

## The steal list, revisited

1. Add-to-bag certainty — **TAKEN** (own idiom: inline, not a drawer).
2. Pre-click sold-out truth — **TAKEN** on the register; related-product
   cards still owe it.
3. Branded checkout — **still open** (stock white skin unchanged).
4. Legal identity line — **TAKEN**, and it converted the sceptic.
5. In-stock filter — still open.
6. Photography ambition — **still open, and now the biggest gap**: ON MODEL
   still shows one placeholder man on 13 cards while real on-model shots
   exist on the jeans PDP; grey jeans still 1 photo vs blue's 2 (it steered
   persona 10's £60 to blue).

## Run-2 verdict

Run 1's sentence — right machines, several broken — is spent. The theme-side
machines are repaired and persona-verified; what costs sales now is (a) the
Getaway's unreliable code backing and its seven-item punch-list
(`rerun/SUMMARY.md`), (b) stock depth, and (c) the photography gap that
Unfounded still wins. Fix the popup's mint, wire the real photos, and the
scoreboard reads 11–2.
