# BACKLOG.md — CROOKSLDN — REFRESHED AFTER RE-AUDIT (RUN 2)

The run-1 backlog is preserved in git history (`15ef712`); its item-by-item outcome is scored in
`DELTA.md §1`. This file is the **live** list: what is still worth doing, ranked, after twenty
fix commits (`1b6bc4c → db96aa3`) and the run-2 verification pass. Council round-2 verdict:
`COUNCIL.md`.

**Severity:** `BLOCKS` · `HESITATION` · `POLISH`. **Effort:** `minutes` · `hours` · `days` ·
`project`. `[A]` = Shopify admin, live-on-save, no undo. `[T]` = theme code, PR-able.

---

## THE TOP FIVE

| # | Item | Severity | Effort | Where |
|---|---|---|---|---|
| 1 | **[A] Flip `inventoryPolicy: CONTINUE → DENY`** on MONEY CLIVE TEE, 3 CLIVES TEE, BROADCAST TEE — restocked to 10/variant but the oversell mechanism re-arms at zero. The only item all five round-2 advisors listed. While there: decide CRX GARMS (phantom 985, archived, still CONTINUE) and reconcile V2 BAGGIES/M at −1. | **BLOCKS** | minutes | Products → variant → untick "Continue selling when out of stock" |
| 2 | **[A] The archive: hand-count, then open the closed cases properly.** 1,452 units / ~467 real ≈ **£28,270** unchanged since run 1, incl. the #1 lifetime seller. Council-ruled path: (1) DENY first, (2) hand-count — the repull proves counts lie (CRXST★RZ 970→98), (3) trial a **separate closed-case register** (the collection-page register from `1892419` does most of the build) — NOT a plain unarchive: `/14` stays honest, the WITNESS STATEMENT stays untouched. Archived products carry no `crooks.*` metafields — records need filling before they render properly. | **BLOCKS** | days | Products → Archived + one collection + metafields |
| 3 | **[A] Re-upload the three remaining mis-named masters** — `cellcrew.webp` (976 KB, homepage **and cart**), `v2baggies.webp`, `crooksldn-white-red-motiontec-socks.webp` — with `.png` filenames. Same fix took the tee PDP 13.9 s → 2.4 s this run. Closes the cart regression and ~700 KB of homepage. Re-drag to position, re-enter alt text; do **not** use `image-backups/` (pre-cut-out originals). | **BLOCKS** | minutes | Products → media |
| 4 | **[A] The sceptic bundle: placeholders, contact page, banner position.** The only persona still leaving, and this is their entire checklist. `[Crooksldn LTD] [Crooksldn@gmail.com] [TW200JW]` byte-identical to run 1; 8 Gmail mentions vs 0 `info@` in policy text; contact page still a bare form; banner still 40% of viewport / first 4 tab stops / covering all five size-button centres at scroll 0 (proven the cause of run 1's worst finding). | **BLOCKS** | ~1 hour | Settings → Policies · Pages → Contact · Customer privacy → banner position |
| 5 | **[T] Retire the VT323 layout tax: `size-adjust` fallback in the display stack.** The 0.2315 PDP CLS is `PRODUCT NN / 14` (display face) inside `flex-wrap: wrap` (`crooks.css:500`); the wider fallback wraps the row, deferred JS un-wraps it at ~5.5 s. `white-space: nowrap` on the span is a **no-op** (it's flex wrap) and `flex-wrap: nowrap` risks re-breaking the 200% zoom fix. Correct fix: a `size-adjust`ed local fallback in `--crk-font-display` (`crooks.css:47`) — retires the hazard for every VT323 surface at once. Verify: CLS < 0.05 on both PDPs, 200% zoom still 195==195, no-JS fallback intact. | **HESITATION** | hours | `assets/crooks.css` |

---

## WORTH DOING

| # | Item | Severity | Effort | Where |
|---|---|---|---|---|
| 6 | **[A] Delete the pasted delivery lines** — `9-16 days delivery uk 16-21 days international` still sits in the jeans descriptions against custody's `UK 1–2 working days`. The last on-page contradiction a shopper can find unaided. | HESITATION | minutes | Product descriptions |
| 7 | **[A] Measure 14 garments.** The table is still the identical arithmetic-progression placeholder it was in run 1, on denim and 500 gsm cotton alike. The apparatus around it is excellent and untouched — replace the data only. | HESITATION | hours | Product metafields |
| 8 | **[A] State who pays return postage** on the refund policy (`whoPaysPostage: null`) — the deciding fact on a £60 order. | HESITATION | minutes | Settings → Policies → Refund |
| 9 | **[T+A] Route the notify capture.** The variant-level restock form works and posts via `form 'contact'` — intent arrives as unstructured inbox email, no consent flag, no per-variant list. Note: **Shopify Flow has no contact-form trigger** — this is a real integration (list tooling, consent copy, and the no-JS/a11y surface must survive). The owned-audience machine, currently unplugged. | HESITATION | project | `sections/crooks-exhibit-record.liquid` + app/tooling |
| 10 | **[T] Stop stacking above the register.** First product card drifted 1.22 → 1.48 viewports as the carriage bar accreted. The board earned its viewport; new furniture hasn't. Review what sits above the fold before anything else is added. | POLISH | minutes | `templates/index.json` order |
| 11 | **[A] Brand the hosted account surface** — `friendsof.crooksldn.com` is still Times New Roman on white with no order lookup, now the least branded surface a paying customer sees. | HESITATION | hours | Settings → Customer accounts |
| 12 | **[A] Photography for the £60 garments** — now `Photo 1 of 2` (was 1 of 1). Better; not a gallery for a fit-sold product. | HESITATION | days | Product media |
| 13 | **[harness] Fix the instruments before run 3:** badge-capture regex is blind to `FILED …`; `p2-checks.mjs` overlay selector and `pressed` field (both wrong in both runs — corrected instrument is `p2-checks-corrected.mjs`); re-sample board fps and INP on a quiet container. | — | minutes | `audit/` |

---

## LONG RANGE (unchanged from run 1)

- **#25 Game traffic capture** — Base44 endpoint + CORS + identity linking before any leaderboard renders. The hidden-leaderboard principle holds: real scores or nothing.
- **#26 Retired runs as `RELEASED` register entries** — now partially absorbed into item 2's closed-case register; the `--crk-red` slot remains reserved for it.

## Explicitly not recommended — unchanged and re-affirmed by round 2

Trust badges, reviews, countdowns, stock counters, urgency copy (their measured absence is
load-bearing — "honesty is the differentiator"). Softening the palette or type. Touching the
board. Editing the WITNESS STATEMENT (last resort only, per COUNCIL round 2 — make the backend
true first). Placeholder leaderboard scores. "Fixing" the `RELEASE REQUEST` span.

---

## CLOSED AND VERIFIED IN RUN 2 — do not re-open

Popup scope + design-rule compliance (#5) · variant-level sold-out + notify (#3, with corrected
diagnosis — see `DELTA.md §4`) · cart brand pass + critical axe (#9) · order tracking page,
menu and footer (#10) · font double-download (#8's fix landed; residual CLS is item 5 above,
a different mechanism) · custody label (#13) · filing dates (#14) · 200% zoom + 320 px reflow
(#15) · contrast token (#19) · filter-rail cue (#21) · back-link tap area (#22).
