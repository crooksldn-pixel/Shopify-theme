# FIX-PROMPTS.md — copy-paste prompts for the build chat

Everything in `BACKLOG.md` that **Claude Code can actually do in the theme repo**, written as
prompts you can paste one at a time. Admin-only items are listed at the bottom so you can see the
split — no prompt will fix those.

---

## READ THIS FIRST — two things that will waste your time if you skip them

### 1. The theme code is not on the audit branch

The audit branch (`claude/crooksldn-site-audit-eijmkd`) contains the audit only. It has **no**
`assets/crooks.css`, no `sections/crooks-exhibit-record.liquid`, no `crooks-exhibit-log.liquid`.
Those live on:

```
claude/crooksldn-theme-init-bnen7a   @ 1b6bc4c
```

Every line number in this file was re-verified against `1b6bc4c` on 2026-08-08 and is correct as
written. **Open the build chat with that branch checked out**, or paste this as the first thing:

```
git fetch origin claude/crooksldn-theme-init-bnen7a
git checkout claude/crooksldn-theme-init-bnen7a
git checkout -b claude/crooksldn-fixes
```

If you paste a prompt below into a session sitting on the audit branch, Claude will report the
files missing and may try to create them from scratch. Don't let it.

### 2. Read `audit/KEEP.md` before any of this lands

The audit's single most important finding: across eight persona journeys, **not one abandonment
was caused by the way the site looks.** The austere design is an asset. `KEEP.md` names the
load-bearing parts specifically — the canvas board, the PDP first viewport, the measurement
apparatus, the accessibility work, the no-JS fallback, the writing, the register format. The
prompts below all carry the relevant guardrail inline, but the file is the authority.

The two rules that matter most, repeated because they are the easiest to lose:

- **Never let `ADD TO BAG` become in-fiction.** Plain English on the commercial spine is why the
  aesthetic survives contact with a stranger.
- **Do not touch the canvas board to save weight.** Measured 60 fps in view, 0 fps off-screen /
  tab-hidden / reduced-motion, and CLS 0. The weight comes from images and JS, not from there.

### 3. Order matters — do PROMPT 1 before PROMPT 6

PROMPT 1 removes a full-viewport overlay that fires on every template including PDPs. There is
good reason to think that overlay is what corrupted the sold-out-size measurement in PROMPT 6
(see the note there). Fixing 1 first may shrink 6 from a session to a re-measurement.

---

## PROMPT 1 — Gate the game popup to the homepage · BACKLOG #5 · minutes · BLOCKS

```
Read audit/KEEP.md section 9 first, then fix the following.

snippets/crack-the-cuffs.liquid is a full-screen popup that currently renders on EVERY
template — product pages, cart, everything — 3 seconds after load, at 100% of viewport,
with scroll locked, and it pulls a 166 KB Base44 bundle onto every PDP and the cart. It
interrupted every one of the eight audited persona journeys.

It is also the only element on the site that breaks the design system: it sets
border-radius and a box-shadow, while assets/crooks.css:101 and :428 enforce zero radius
and no shadow everywhere else.

Two changes:

1. layout/theme.liquid:161 currently reads `{% render 'crack-the-cuffs' %}`. Gate it so it
   only renders on the homepage — wrap it in a template check for the index template.

2. In snippets/crack-the-cuffs.liquid delete these four declarations (verified line numbers,
   the file is 157 lines):
     - line 37  `border-radius: 8px;`        (.ctc-frame)
     - line 38  `box-shadow: 0 24px 70px rgba(0, 0, 0, 0.55);`  (.ctc-frame)
     - line 55  `border-radius: 999px;`      (.ctc-close)
     - line 70  `border-radius: 6px;`        (.ctc-frame, inside the max-width:749px block)
   Delete the declarations only. Do not touch .ctc-close's 44x44 size, its z-index, or the
   prefers-reduced-motion block at line 73 — all three are correct.

Removing those radii brings the popup into compliance with the site's own rules; it does not
compromise them. Do not otherwise redesign the popup, and do not remove it from the homepage
— persona 5 engages with the game.

Verify: the popup still appears on the homepage, does not appear on a product page or the
cart, and no Base44 request fires on a PDP. Report the PDP weight before and after.
```

---

## PROMPT 2 — Fix the double font download and the 0.23 PDP layout shift · BACKLOG #8 · minutes · BLOCKS

```
vt323.woff2 downloads twice and reflows the buy panel 28px at 1.84s. Measured PDP CLS on
mobile is 0.2327 — Google's "poor" threshold is 0.25. Desktop is 0.0062, so this is mobile
only.

Cause: layout/theme.liquid:34 preloads `{{ 'vt323.woff2' | asset_url }}`, which emits a
`?v=...` cache-busting query string. assets/crooks.css:13 requests the same file as
`url('vt323.woff2')` with no query. Different URLs, so the preload is wasted and the real
font lands at 1,836ms against an FCP of 968ms.

Two changes:

1. layout/theme.liquid:34 — strip the query string so the preload URL matches what the CSS
   actually requests: `{{ 'vt323.woff2' | asset_url | split: '?' | first }}`. The preload
   block is lines 31-37; leave `as="font"`, `type="font/woff2"` and `crossorigin` alone,
   they are all correct and required.

2. assets/crooks.css:16 currently reads `font-display: swap;`. Change it to
   `font-display: optional` for the residual shift.

`optional`, NOT `block`. Do not use block: VT323 still lands around 1.8s on the measured
mobile profile and block would still swap, plus give you invisible text before it. optional
tells the browser to use the fallback for this page load if the font isn't ready, which is
what kills the reflow.

Do not change --crk-font-display at crooks.css:47 or any of the .crk-h1 / .crk-h2 /
.crk-price / .crk-rec__title rules that consume it.

Verify: one vt323.woff2 request in the network panel, not two; re-measure PDP CLS on a
throttled mobile profile and report the before/after number.
```

---

## PROMPT 3 — One CSS pass: contrast, reflow, filter cue, tap target · BACKLOG #19, #15, #21, #22 · minutes

All four are in `assets/crooks.css` and all four stay inside existing tokens. Worth one prompt
and one commit.

```
Four small fixes in assets/crooks.css (624 lines). All four must stay inside the existing
token set — introduce no new colour, no new radius, no new typeface, and do not increase any
type size. Read audit/KEEP.md section 4 first: the accessibility work on this site is good
*because* of the constraints, and a "friendlier" palette would degrade the 5.88:1 focus ring.

1. BACKLOG #19 — the only contrast failure on the site. `--crk-micro` renders at 2.57:1 and
   needs 4.5:1. It is declared twice: line 62 `--crk-micro: #575063;` and line 96
   `--crk-micro: #93919B;`. In each block, set --crk-micro to the --crk-dim value already
   declared directly above it (line 61 `#8A8377`, line 95 `#62606B`). Introduce no new
   colour. Then confirm the 9px consumers still pass: `.crk-micro` at line 117 and its
   10px override at line 125.

2. BACKLOG #15 — 200% browser zoom on mobile causes horizontal scrolling (scrollWidth 308 vs
   clientWidth 195). That is a WCAG 2.1 AA 1.4.10 Reflow failure. Desktop passes. The
   offenders are `.crk-status__msg` (+164px), `.crk-header__actions` (+113px) and `.crk-table`
   (+111px). Remove `white-space: nowrap` from `.crk-status__msg` at line 143. Give
   `.crk-table` (line 308) its own horizontally scrollable container rather than letting it
   push the page. The same line 143 declaration is also the cause of the 320px homepage
   overflow (scrollWidth 334 vs 320), so re-check that too.
   Do NOT remove nowrap from line 110 (`.crk-sr`, screen-reader only), line 156
   (`.crk-boot__line`, the terminal type-out effect), line 334 (`.crk-buybar__title`, which
   pairs with text-overflow: ellipsis) or line 378 (`.crk-header__logo`, same). Those four are
   all deliberate.

3. BACKLOG #21 — `.crk-filters` at line 168 is `display: flex; overflow-x: auto`. Two of the
   five category chips (SWEATS, ACCESSORIES) sit off the right edge with no affordance that
   the row scrolls. Add an edge cue using existing tokens only. Keyboard focus already scrolls
   them into view correctly — do not change that behaviour, and do not convert the rail to
   wrapping.

4. BACKLOG #22 — the back link at sections/crooks-exhibit-record.liquid:61 (`← Catalogue`,
   default set in the schema at :494) renders 92x16px. It is the only theme-owned tap target
   meaningfully under 44px. Increase the hit area to at least 44px tall — padding or
   min-height, NOT font-size. The 16px type is correct for the label style.

Verify each: contrast ratio for the two token placements; scrollWidth vs clientWidth at 200%
zoom on mobile and at 320px; the filter rail's cue; the back link's measured box.
```

---

## PROMPT 4 — Surface the shipping copy and add order tracking · BACKLOG #13, #10 · minutes

```
Two changes that make existing good content findable. Read audit/KEEP.md section 6 first —
the writing on this site is the brand's substitute for the trust furniture it deliberately
refused, and the copy INSIDE these components must not be edited.

1. BACKLOG #13 — CHAIN OF CUSTODY hides the best trust copy on the site behind a collapsed
   accordion at 1.7 viewports, under a label containing no shipping vocabulary. Persona 1
   went hesitant at step 7 and only converted at step 8 after opening it.
   In sections/crooks-exhibit-record.liquid, the accordion head is at :414-416 and reads
   `section.settings.custody_heading`. Change that setting's default at :550 from
   "Chain of custody" to append the function, e.g.
   "CHAIN OF CUSTODY — SHIPPING & RETURNS".
   Same typeface, same caps, same zero radius. Do not expand it by default (:541
   custody_open stays false) and do not edit any of the four custody_step bodies at :568-571
   — that copy is what converted persona 1.

2. BACKLOG #10 — order tracking does not exist anywhere on the site. Not on the homepage, not
   in the menu, not in the footer. The footer's INFORMATION column already holds SHIPPING and
   REFUNDS and has a spare link slot; add a tracking entry to it.
   The column is defined in TWO places and you must change BOTH, because the section preset
   does not drive the live footer:
     - sections/footer-group.json:231-239 — this is the LIVE footer. INFORMATION currently
       holds label_1 SHIPPING, label_2 REFUNDS, label_3 CASE 001. Add label_4 / url_4.
     - sections/crooks-footer-log.liquid:97-100 — the section preset, for parity when the
       section is re-added.
   Slot 4 is confirmed working, so no schema or Liquid change is needed: the schema declares
   label_4/url_4 at :72-73 and label_5/url_5 at :74-75, and the render loop at :11-35 iterates
   (1..5) with case 4 handled at :23-25 and blank labels skipped at :32. Adding the two JSON
   keys is the whole change.
   Point it at the Shopify order-status lookup. Keep the label in house voice and caps.

Verify: the custody label reads with shipping vocabulary and the accordion still starts
closed; the new footer link renders in the live footer (footer-group.json path) and resolves.
```

---

## PROMPT 5 — Make the catalogue status slot carry information · BACKLOG #14 · hours

```
Read audit/KEEP.md section 7 before starting. The register format
(`NO. 01 / SWEATS / CHARCOAL CELLBLOCK CREWNECK / £50.00 / AVAILABLE`) is an ASSET, not a
problem. Persona 5: "the numbering makes me want to see all fourteen... it feels like
flipping through an evidence log rather than scrolling a shop, and that's the difference
between leaving and staying." This task is an ADDITION to that format, not a replacement.
Do not turn it into a conventional product grid.

Problem: there is no new-arrival signal anywhere on the site. Measured newInGrid: 0,
anyDates: false, every card stamped AVAILABLE, ordering is NO. 01 through NO. 14.
/collections/new returns 9 of 14 products — 64% of the catalogue, which is no signal at all.
The returning fan is the highest-LTV persona and currently cannot tell what changed.

In sections/crooks-exhibit-log.liquid the status slot already exists on every card at
:183-189 and currently renders a constant from `section.settings.available_label`
(schema :234, default "AVAILABLE") with a sold-out branch. Make that slot carry a filing
date instead of the constant when the product is available and recent.

A filing date is more in-voice than "NEW" — e.g. `FILED 08.08`. Match the existing card
micro-copy style exactly.

Constraints:
- Keep the sold-out branch at :186-188 working; it stays as-is.
- `--crk-red` is reserved for released/sold states — do not spend it here.
- Do not reorder the register. Do not add badges, ribbons, urgency copy or stock counters:
  the audit verified those are deliberately absent (starRatings 0, reviewBlocks 0,
  urgency false) and BACKLOG explicitly rules them out.
- Keep it working with JS disabled — the no-JS fallback (KEEP.md section 5) currently renders
  18 product links and 40 images on the homepage and is easy to break by accident.

Decide and state how "recent" is determined and make it a section setting rather than a
hardcoded window.
```

---

## PROMPT 6 — Sold-out sizes: instrument before you rewrite · BACKLOG #3 · session · BLOCKS

**Do PROMPT 1 first, and read this note before pasting.** The backlog attributes this to the
product-level `{% if product.available %}` gate. That is correct for the *missing notify block*,
but it does not explain the measured symptoms, and I re-checked the code:

`assets/crooks-record.js` already handles sold-out variants correctly on paper — `render()`
clears the hidden variant id at `:126`, writes a size-specific sold-out stock line at `:140`,
and disables the buy button at `:153`. The comment at `:181-182` states the intent explicitly.
`aria-disabled` was observed correctly set on M and L, which proves `render()` ran at least once.
No JS exceptions were recorded in `perf.json` — only 404s and a web-pixels CSP refusal.

But `checks.json → soldOutTapSequence` shows that across three taps (XS, M, L) the
`selectedVariantId` never changed off XS, the stickybar text never changed, and the stock line
never changed. A totally frozen DOM with no JS error is the signature of **clicks not reaching
the buttons** — which is exactly what PROMPT 1's full-viewport overlay does, and exactly the
signature the audit recorded for the footer links under the cookie banner (#4).

So: this may substantially dissolve once the overlays are gone. Re-measure first.

```
Read audit/KEEP.md section 10 first. This is NOT "build a notify feature" — a complete,
in-voice sold-out state and email capture already exists at
sections/crooks-exhibit-record.liquid:280-301 (RELEASED — NO LONGER IN CUSTODY, a contact
form carrying subject/handle/product_url, plus success and error branches). The task is to
surface what is already built, at the right granularity. Design nothing new. `--crk-red` is
already reserved for this state and is currently unused.

STEP 1 — REPRODUCE BEFORE CHANGING ANYTHING.
The recorded evidence is audit/evidence/checks.json, key `soldOutTapSequence`. It shows three
taps (XS, M, L) on V2 BAGGIES where selectedVariantId stayed 53075854197079 (XS), the
stickybar stayed "V2 BAGGIES £60.00 · XS ADD TO BAG", buyDisabled stayed false, and the stock
line stayed "IN STOCK". `soldOutAddAttempt` shows /cart/add.js returning 200 with
"variant_title":"XS".

But assets/crooks-record.js looks correct: render() at :105-153 clears the hidden input at
:126 when the variant is unavailable, sets a size-specific sold-out line at :140, and calls
setBuy(L.sold, true) at :153. Click listeners are bound at :175-196 and the initial render
fires at :198. No JS errors were logged.

A frozen DOM with no JS error suggests the taps never reached the buttons — likely the
full-viewport popup or the cookie banner intercepting. So FIRST: with the popup gated to the
homepage, load a PDP with a genuinely sold-out variant and tap it for real. Report what
actually happens to selectedVariantId, the buy button's disabled property, and the stock line.

Only rewrite variant logic if it is genuinely broken. Do not rewrite it blind.

STEP 2 — the real gate bug, which is confirmed by reading and independent of the above.
:142 is `{%- if product.available -%}`, a PRODUCT-level test. The sold-out + notify block at
:280-301 therefore only renders when the WHOLE product is gone. Variant-level availability is
already computed 91 lines later at :233 (`{%- if v.available -%}`, in the noscript block) and
is available in the variant matrix the JS reads from :152-165 (`data-crk-variants`, carrying
`data-available` per variant at :165). Surface the existing notify block when the SELECTED
VARIANT is unavailable, not only when the product is.

STEP 3 — two smaller confirmed issues:
- crooks-record.js:19 is `root.querySelectorAll('.crk-size[data-size]')`, assigned to `cells`.
  The Liquid at :205-214 emits `data-crk-opt` and `data-value` on those buttons, never
  `data-size`, so this selector matches nothing. `cells` is also never read anywhere else in
  the file. Confirm and remove it, or fix it if it was meant to do something.
- The stock line reports the product, not the variant, in the initial Liquid render at :220
  and :240 (both hardcode `section.settings.label_select`). Make the server-rendered state
  variant-accurate so it is correct before JS runs.

Commercial context for why this matters: V2 BAGGIES is the #2 lifetime seller at 127 units
and its M variant is already at inventoryQuantity -1.

CONSTRAINTS:
- ADD TO BAG stays plain English. Never in-fiction. This is the rule the whole aesthetic
  depends on (KEEP.md section 2).
- The no-JS fallback must keep working: a real /cart/add form on the PDP, sizes and prices
  rendered (KEEP.md section 5).
- Keep the existing a11y properties: aria-label="Size XS" and aria-pressed on size buttons,
  exactly one h1, 0 of 35 controls without an accessible name.
- If you make a sold-out size non-selectable, it must still be reachable and readable by
  keyboard and screen reader — aria-disabled with the arrow-key handler at :186-192 intact is
  preferable to the disabled property, which removes it from the tab order.

Verify by tapping a sold-out size and confirming: the buy button is genuinely disabled
(check the DOM property, not just the aria attribute), /cart/add.js is not reachable for it,
the stock line names the size, and the notify form appears.
```

---

## PROMPT 7 — Bring the cart into the design language · BACKLOG #9 · session · HESITATION

I checked: `sections/main-cart.liquid` contains **zero** `crk-` classes. It is stock Horizon, which
is why it looks like a different website. This is a real build, not a tweak.

```
The cart abandons the design language at the moment of payment. Measured: bone-coloured
ground, Archivo Narrow (a third typeface the system forbids — the system is two faces,
VT323 for display and CRX Mono for the rest), wallet buttons in Shop Pay purple / PayPal
blue / Google Pay black, all sitting under a dark terminal header. Persona 7 and the
outsider persona both flagged it.

It also holds the site's only *critical* axe violation (aria-required-children) and 5 of the
sub-44px tap targets.

sections/main-cart.liquid currently contains no crk- classes at all — it is stock Horizon.
templates/cart.json is auto-generated by the theme editor and carries that warning at the
top of the file; treat it as such and prefer changes that survive an editor save.

Extend the existing crk-* tokens over the cart: ground, typeface, zero radius, no shadow,
the existing focus-ring treatment (2px rgb(167,122,199), which measures 5.88:1 on the
near-black ground). Fix the aria-required-children violation and bring the 5 tap targets to
44px.

Known limit, do not fight it: the wallet button chrome (Shop Pay, PayPal, Google Pay) is
Shopify-owned and cannot be restyled. Frame it, don't fake it.

Do not introduce a third typeface. Do not soften corners. Do not add trust badges or
urgency messaging — the audit verified their absence is deliberate. Keep every commercial
label in plain English.

Verify: axe clean on the cart, no sub-44px tap targets, one typeface family beyond the
display face, and the checkout path still completes end to end including with keyboard only.
```

---

## What Claude Code cannot fix — admin only, live-on-save, no undo, no version control

These are the top of the backlog by value and **none of them is a theme change**. Items #1 and #2
outrank every prompt above.

| # | What | Where | Severity |
|---|---|---|---|
| 1 | 3 active products overselling into negative stock (−22, −19, −8) while showing "IN STOCK". 49 units sold that don't exist. Likely cause of June at −£195.09 | Products → each variant → uncheck "Continue selling when out of stock" | **BLOCKS** |
| 2 | 9 archived + 1 draft product hold 1,452 units. Excluding a suspected sync artefact, ~467 units ≈ **£28,270 retail** — vs £11,104 of revenue in the last 90 days. Includes the #1 lifetime seller (CROOKS EXPRESS TEE, 146 sold, archived) | Products → filter Archived | **BLOCKS** |
| 4 | Cookie banner makes 6 of 11 footer links physically unclickable on first visit | Settings → Customer privacy → Cookie banner → change position | **BLOCKS** |
| 6 | 8 image masters uploaded as `.webp` are never transcoded, ship 4.8× heavier. ≈933 KB off the homepage | Re-upload with a `.png` extension. **Not** from `image-backups/originals-white-bg/` — those are pre-cut-out. Re-drag to position 1, re-enter alt text | **BLOCKS** |
| 7 | Live legal pages contain unfilled placeholders — `[LINK TO REFUND POLICY]`, `[Crooksldn LTD]`, `[TW200JW]` — and a Gmail address contradicting the footer | Settings → Policies | **BLOCKS** |
| 11 | Measurements are placeholder data. V2 BAGGIES carries the identical table to 14oz denim; every column is a perfect arithmetic progression. Both jorts have none. Only 5 of 14 products have measurements | Measure 14 garments. **Nothing in the theme fixes fake numbers** | HESITATION |
| 12 | Four delivery claims on one PDP, two contradictory ("24HR DISPATCH" vs "9-16 days delivery uk") | Remove pasted lines from BLUE WASH OG JEANS, GREY WASH OG JEANS, V2 BAGGIES descriptions | HESITATION |
| 16 | The £60 jeans have one photograph each, back view, `PHOTO 1 OF 1` | Product media | HESITATION |
| 18 | Cookie banner takes the first four tab stops ahead of the skip link; `Manage preferences` has no focus indicator; its H2 precedes the page H1 | Same banner setting as #4 | HESITATION |
| 20 | The contact page contains no contact information at all | Pages → Contact | HESITATION |
| 23 | Return postage liability never stated — the deciding fact for a £60 order | Settings → Policies → Refund | HESITATION |

Item #17 (1.17 MB of JS) is mostly Shopify Horizon and not yours to fix; PROMPT 1 removes the
166 KB Base44 share of it. Item #25 (capturing game traffic) needs a Base44 endpoint before any
theme work is possible. Item #26 (archived runs as `RELEASED` on the storefront) depends on #2
being resolved first.

## Do not "fix" these

- **#24** — `RELEASE REQUEST` is a non-interactive `<span>` above ADD TO BAG. Recorded so it is
  not tidied away by accident. The outsider's verdict: leave it.
- The hidden leaderboard in `sections/crooks-case-file.liquid:25-28`. The comment documents a
  deliberate decision not to render placeholder scores. It is not an oversight — it is the same
  principle that rejected fake stock counters, applied consistently and written down.
- Trust badges, reviews widgets, countdown timers, stock counters, urgency messaging.
- Softening corners, warming the palette, adding a friendlier typeface.
- Reducing or removing the canvas board.
- Reordering `templates/index.json` to lift the informant register — already verified in place.
