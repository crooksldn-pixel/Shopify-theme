# CROOKSLDN — PHASE 1: INSTRUMENTED EVIDENCE — RUN 2 (RE-AUDIT)

Generated 2026-08-08 (evening), against preview `kbwcga0qjjqhdh2w-100410786135.shopifypreview.com`,
staging theme id 202053779799 — the **same theme** as run 1, which has since received twenty fix
commits (`1b6bc4c → db96aa3`). Run 1's numbers (morning of the same day, commit `15ef712`) are
shown as *(r1: …)* throughout. Same harness, same devices, same throttle profile as run 1.

**What this run is:** the verification pass. Between the two runs, the build chat implemented
most of `BACKLOG.md` in theme code, and the store owner restocked the three overselling tees and
re-uploaded five of the eight mis-named image masters. This document measures what actually held.

---

## 0. How these numbers were produced, and where to distrust them

Same instruments as run 1 (`audit/p1-*.mjs`), Playwright + local TLS bridge, mobile 390×844 @ 3×,
Slow-4G + 4× CPU throttle unless stated. Same caveats: preview-bar overhead is present in both
runs and cancels in comparison; the egress proxy exits in the US so GBP is pinned by cookie.

Two run-2-specific cautions:

- **The board fps sample read lower this run (45.7–51 vs 60) with all three pause guards still
  verified working.** The board code did not change between runs; the container's CPU load did.
  Treat the run-1 numbers as the truer steady-state and this as sampling variance, not a regression.
- **`p2-checks`' overlay-removal selector never matched the cookie banner in either run** (it
  removed `.shopify-pc__banner`; the real class is `shopify-pc__banner__dialog`). Every
  centre-point tap in its sold-out sequence landed on the banner's button row, both runs. See §10
  — this rewrites one of run 1's headline findings. Corrected evidence: `checks-corrected.json`.

---

## 1. THE THREE WORST NUMBERS, RE-MEASURED

### 1.1 — The 13.9 s LCP is gone: 3 CLIVES TEE PDP now paints product at **2.4 s** *(r1: 13,876 ms)*

The four mis-named masters on this PDP were re-uploaded with `.png` extensions and the CDN now
transcodes them. LCP element is the same hero `IMG.crk-main-img`, now `df150894…_webp.png`
served as AVIF/WebP. Page weight 1,680 KB *(r1: 2,591)*. This was run 1's single worst number
and it is closed by an admin action, exactly as the backlog predicted.

**Still open:** three masters remain mis-named and untranscoded — `cellcrew.webp` (969 KB),
`v2baggies.webp`, `crooksldn-white-red-motiontec-socks.webp` — all on the homepage, and
`cellcrew.webp` now also ships to the cart (see §1.3).

### 1.2 — PDP CLS is **unchanged at 0.232–0.235** — but it is a NEW shift, not the old one

*(r1: 0.2327/0.2333 from the vt323 double-download and font swap at t≈2.0 s.)*

The round-1 font fix landed and works: **one** `vt323.woff2` request *(r1: two)*, preload URL
matches, `font-display: optional` deployed. The old t=2 s swap-reflow is gone.

What replaced it, at almost the identical value: a single **0.2315** shift at **t≈5.5 s** on both
PDPs. Mechanism, verified by DOM probe and ablation:

- The PDP meta row (`header.crk-meta`) contains `← Catalogue`, then
  `<span class="crk-display crk-meta-exh">PRODUCT NN / 14</span>` — **display-face type (VT323)
  in a wrapping flex row**.
- At first paint the font is not yet available; `optional` correctly holds the fallback — which
  is wider, so the row wraps and the category tag drops to a second line.
- At ~5.5 s (throttled), deferred JS mutates the DOM; the re-laid text now uses the loaded VT323,
  the row un-wraps, the row above the grid loses 28 px, and everything below shifts up: **0.2315**.
- Ablation: block `vt323.woff2` → CLS 0.001. Block `crx-mono.woff2` → CLS 0.2317 (no effect).

So `optional` stopped the *swap* but not the *late re-layout through a JS mutation*. The fix is
theme-side and cheap: reserve the meta row against font width variance (single-line guarantee for
`.crk-meta`, or width-stable rendering for `.crk-meta-exh`). This is the top theme-code item in
the new backlog. Desktop remains fine (0.0115).

### 1.3 — The cart is now the heaviest, slowest page: **4,215 KB, LCP 9.4 s, INP 1,096 ms** *(r1: 4,024 KB / 7.9 s / 760 ms)*

Wallet iframes are unchanged (pay.google.com 418 KB, paypal 178 KB — Shopify-owned). What is new:
`cellcrew.webp` (976 KB, served as PNG) now ships to the cart — the crewneck appears in the cart's
recommendation/line context, so one of the three remaining mis-named masters lands on the money
page. Cart image weight 1,340 KB *(r1: 946)*. Re-uploading that one master takes ~400 KB and the
LCP regression with it.

Homepage: 2,560 KB *(r1: 3,103)* — down 543 KB, mostly the re-uploaded masters transcoding.
`newInGrid`-style wins landed elsewhere; the homepage is still image-heaviest (910 KB) with the
three broken masters accounting for the bulk of what remains avoidable (~700 KB).

---

## 2. PERFORMANCE, FULL TABLE (mobile 390×844, Slow 4G, 4× CPU)

| Page | TTFB | FCP | LCP | CLS | INP | Transfer | Requests |
|---|---|---|---|---|---|---|---|
| Homepage | 228 | 1,416 | **4,528** *(r1 4,432)* | 0.001 | 1,144* | 2,560 KB *(r1 3,103)* | 174 |
| PDP — 3 CLIVES TEE | 509 | 1,164 | **2,404** *(r1 13,876)* | **0.2349** | 608 | 1,680 KB *(r1 2,591)* | 170 |
| PDP — BLUE WASH OG JEANS | 249 | 884 | 4,196 *(r1 3,388)* | **0.2324** | 584 | 1,857 KB | 171 |
| Cart | 415 | 1,560 | **9,444** *(r1 7,948)* | 0.0113 | 1,096* | **4,215 KB** | 240 |
| Homepage (desktop) | 810 | 1,512 | 1,512 | 0.0005 | 656 | 2,249 KB | 159 |
| PDP denim (desktop) | 426 | 1,044 | 3,752 | 0.0115 | 560 | 1,826 KB | 159 |

*INP on home/cart measured while the popup (home) and wallet iframes (cart) initialise; run-1
comparison values 656/760. Long tasks: 15–30 per page, 2.0–4.3 s total blocking — dominated by
Horizon bundles, unchanged.

### JavaScript — ~1.08–1.17 MB per page, the Base44 share now homepage-only

PDPs: 1,082 KB *(r1: 1,171)* — the 166 KB `crack-cuff-codes.base44.app` bundle no longer loads on
PDPs or the cart (popup gated to the homepage, verified in transfer logs). Homepage keeps it by
design. The rest is Horizon platform code (258 KB + 188 KB bundles), unchanged and not theme-owned.

### Fonts

217–240 KB per page *(r1: 236)*. `vt323.woff2` requested **once** *(r1: twice)*, initiator
`link` (preload URL now matches). Cart fonts 369 KB *(r1: 409)* — Archivo Narrow still loads there
(see §6 cart note).

---

## 3. IMAGES

**5 of 8 mis-named masters fixed** (all four on 3 CLIVES TEE + one more). Still broken — uploaded
with `.webp` filenames, so the CDN serves the original PNG bytes regardless of `Accept`:

| Master | Raw size | Where it ships |
|---|---|---|
| `cellcrew.webp` | 969 KB | Homepage + **cart** |
| `v2baggies.webp` | ~large | Homepage |
| `crooksldn-white-red-motiontec-socks.webp` | ~large | Homepage |

A/B verified again this run: a `.png`-named master serves as AVIF/WebP at a fraction of the bytes;
a `.webp`-named master serves `image/png` at full size under every `Accept` header.

Also still true: the two jeans PDPs carry 1.3–1.6 MB *raw* masters (`crooksldn-*-wash-baggy-jean*`)
that the CDN does transcode for delivery — correctly named, no action needed, recorded so nobody
"fixes" them.

---

## 4. LAYOUT AND REACH

- **320 px horizontal overflow: FIXED.** Homepage scrollWidth 320 == 320 *(r1: 334/320)*. The one
  remaining offender is a `.crk-filter` chip 10 px past the edge — which is the deliberate
  scroll-affordance cue added by the round-1 fix (a peeking chip), not a defect.
- **200% zoom reflow (WCAG 1.4.10): FIXED.** scrollWidth 195 == clientWidth 195, no horizontal
  scroll *(r1: 308/195, failing)*.
- **Tap targets:** no theme-owned target under 44 px found this run *(r1: `← CATALOGUE` at
  92×16)*. Size buttons measure 58×52.
- **Scroll depths (mobile):** PDP doc height grew to 4.03 viewports *(r1: 3.32)* — the
  description accordion now opens by default and the notify/dispatch furniture adds length. ADD
  TO BAG sits at 1.37 vh *(r1: 1.04)*; the sticky buy bar (now with ADD TO BAG + CHECKOUT NOW)
  still covers the bottom of every screen, so reach is preserved. Homepage first product card at
  1.48 vh *(r1: 1.22)* — the carriage bar and free-shipping progress line pushed content down
  slightly.
- **New since r1:** the sticky bar carries two actions (`ADD TO BAG` / `CHECKOUT NOW`), and a
  free-shipping progress readout (`£45.00 to free…`) renders at 0.16 vh on PDPs.

---

## 5. THE CANVAS BOARD

Pause guards re-verified: **0 fps off-screen, 0 fps tab-hidden** — both intact. In-viewport
sample read 45.7–51 fps this run *(r1: 60)* under a container whose CPU was also running the
audit; the board code is unchanged between runs, so treat as environmental variance and re-check
in any future run before claiming a regression. Homepage CLS remains ~0 (0.001), so the board
still reserves its space correctly.

---

## 6. ACCESSIBILITY

### Contrast — **clean**

The `--crk-micro` 2.53:1/2.57:1 failures are **gone on every page** *(r1: 3 fails on home, 1 per
other page)*. The token now carries the `--crk-dim` values in both modes, verified in the deployed
CSS. The only remaining flag is the known transparent-text "London" eyeball case (ratio 1.0 by
measurement, not a real rendering).

### axe-core

| Page | Run 1 | Run 2 |
|---|---|---|
| Cart | `aria-required-children` (**critical**), `aria-allowed-role`, `frame-title`, `heading-order`, `region` | `frame-title`, `heading-order`, `region` |
| Home / PDPs / Collection | 2–3 minor/moderate each | unchanged |

**The site's only critical violation is fixed.** What remains on the cart is wallet-iframe
`frame-title` (Shopify-owned) and `heading-order`/`region` from the cookie banner's H2 (admin).

### Keyboard

Unchanged from run 1: the cookie banner still takes the first **4** tab stops on every page
(admin item, not addressed), one invisible-focus element remains, and the preview-bar iframe
(`#PBarNextFrame`) still traps focus — a preview-environment artefact, not a storefront defect.
Size buttons keep `aria-label`/`aria-pressed`; arrow-key navigation intact.

### Sold-out semantics (new since r1)

Sold-out sizes now carry `aria-disabled="true"` AND behave: selecting one announces
`SIZE M IS SOLD OUT` via the `aria-live` stock line, disables the buy button, and reveals the
notify form. Note: `aria-disabled` on a still-activatable button is the *correct* pattern here
(stays in tab order, state readable), but automated tools (and Playwright) treat it as
non-interactive — see §10.

---

## 7. THE PATTERN UNDERNEATH THE NUMBERS — RUN 2 VERSION

Run 1's pattern was: *quality drops where CROOKSLDN stops and Shopify Horizon starts.* Still
true (wallet chrome, Horizon bundles, hosted account pages). The run-2 addition:

**Every remaining theme-owned defect is new code from the fix sprint.** The meta-row CLS
(§1.2) came in with the fix sprint's own PDP additions; the cart's 976 KB image regression
rides on a still-broken master reaching a new surface; the deeper ADD TO BAG comes from the
opened accordion. None of these outweigh what the sprint fixed — but the sprint introduced the
only new theme defects on the list, which is the strongest argument for running this
verification pass after every sprint.

---

## 8. THE COOKIE BANNER — unchanged, and now provably the tap-blocker

338 px tall, 40% of the viewport, `z-index 2000000`, first 4 tab stops, H2 before H1 — all
identical to run 1. This run adds one decisive fact: with the popup now gated off PDPs, the
banner is the only remaining first-visit overlay, and hit-testing shows it covering **all five
size buttons' centres** on the V2 BAGGIES PDP at scroll 0. It was the cause of run 1's
"frozen taps" evidence (§10). Still admin-only. Still item #1 on the storefront list.

---

## 9. CATALOGUE FACTS (GBP)

14 products, unchanged roster, GBP verified. Register format intact. Sticky bar now shows both
buy actions. The menu gained TRACKING and CONTACT entries; the footer INFORMATION column carries
the tracking link. `/collections/all` now backs the catalogue register.

---

## 10. CORRECTION TO RUN 1 — the "silently sells the wrong size" finding

Run 1's worst finding (#3, BLOCKS) said tapping a sold-out size silently kept the previous size
and sold it. Re-instrumentation shows that measurement was **contaminated**:

- `p2-checks` removed overlays with the selector `.shopify-pc__banner`, which matches nothing —
  the banner's class is `shopify-pc__banner__dialog`. The banner stayed up during the tap
  sequence in **both** runs.
- The banner covers the entire size row at first visit; every centre-point `click({force:true})`
  landed on the banner's button row. The DOM was "frozen" because the taps never reached it.
- Its `pressed` capture is also unusable in both runs (operator-precedence bug renders every
  button as "sel").

What was **real** in run 1: the notify block only rendered when the whole product was gone
(product-level gate), the stock line reported the product not the variant, and a first-visit
shopper genuinely could not tap sizes under the banner. What was **not real**: the variant
logic itself silently selling the wrong size to a shopper who had dismissed the banner.

Run 2, corrected measurement (`checks-corrected.json`, banner dismissed via Accept, real taps):
selecting M → `SIZE M IS SOLD OUT`, buy button disabled, variant id cleared (form disarmed),
notify form shown (`TELL ME WHEN THIS SIZE IS BACK`). **BACKLOG #3 is fixed and verified**, and
run 1's headline should be read with this correction attached.

---

## FILES

Same evidence filenames as run 1, overwritten in place — run 1 versions live at commit
`15ef712`. New this run: `commercial-repull.json`, `checks-corrected.json`, this document's
run-2 rewrite. `p2-checks-corrected.mjs` is the fixed instrument.
