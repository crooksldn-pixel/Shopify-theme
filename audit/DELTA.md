# DELTA.md — RE-AUDIT, RUN 1 → RUN 2

**Run 1:** 2026-08-08 morning, theme `1b6bc4c`, preview `ezvw3xrffzdt93es…`, evidence at commit `15ef712`.
**Run 2:** 2026-08-08 evening, theme `db96aa3` (twenty fix commits), fresh preview `kbwcga0qjjqhdh2w…`, same staging theme id `202053779799`, same harness, same throttles.
**Between the runs:** the build chat implemented most of `BACKLOG.md` and `FIX-PROMPTS.md` in theme code; the store owner restocked the three overselling tees, reset the CRXST★RZ artefact, and re-uploaded five of the eight mis-named image masters.

**Headline: run 1 said 3 of 8 personas leave. Run 2 measures 1 of 8 — and every blocker that
remains is a Shopify-admin surface, not theme code.**

---

## 1. SCOREBOARD — every backlog item, re-measured

`CLOSED` = verified fixed by measurement this run · `PARTIAL` = symptom moved, cause remains ·
`OPEN` = byte-identical to run 1 · `REGRESSION` = new defect introduced since run 1.

### The run-1 top five

| # | Finding (run 1) | Status | Evidence, run 2 |
|---|---|---|---|
| 1 | Three tees overselling into negative stock | **PARTIAL** | Counts reset to exactly 10/variant (−22/−19/−8 → 100 each). **Every variant still carries `inventoryPolicy: CONTINUE`** — the mechanism re-arms the moment any size hits zero. The restock treated the symptom; one checkbox per product remains. |
| 2 | 1,452 units invisible in archived products | **OPEN** | Identical to the unit. Same eleven products, same counts. ~£28k of proven sellers still off sale. CRXST★RZ was reset 970→98 — confirming run 1's "sync artefact" suspicion — but CRX GARMS (985, archived, still `CONTINUE`) was not touched. |
| 3 | "Tapping a sold-out size silently sells the wrong one" | **CLOSED — and corrected** | Real taps (banner dismissed) now produce `SIZE M IS SOLD OUT`, disabled buy, disarmed form, notify capture (`checks-corrected.json`). **Correction:** run 1's dramatic version was contaminated — the tap harness never removed the banner (wrong selector) and its taps hit the banner in both runs. The real run-1 defects (product-level gate, no notify, product-level stock line) were real and are fixed. |
| 4 | Cookie banner makes footer links unclickable | **OPEN** | Unchanged: 338 px, 40% of viewport, first 4 tab stops, H2-before-H1. Run 2 adds proof it covers all five size-button centres at scroll 0 — it was the cause of the #3 contamination. Admin: one setting. |
| 5 | Game popup on every template | **CLOSED** | Popup fires on the homepage only (verified in transfer logs: no Base44 on PDPs/cart). Its border-radii and box-shadow are gone from the deployed styles — the design system now has zero violations of its own rules. |

### High value

| # | Finding | Status | Evidence |
|---|---|---|---|
| 6 | 8 mis-named `.webp` masters | **PARTIAL** | 5 re-uploaded (all of 3 CLIVES TEE — its LCP fell 13,876 → 2,404 ms). Still broken: `cellcrew.webp` (969 KB), `v2baggies.webp`, `crooksldn-white-red-motiontec-socks.webp`. **`cellcrew.webp` now also ships on the cart** (see regression R2). |
| 7 | Legal-page placeholders + Gmail | **OPEN** | Byte-identical placeholder set; 8 Gmail mentions, 0 `info@` in policy text. |
| 8 | vt323 double-download, PDP CLS 0.233 | **PARTIAL — superseded** | Double-download fixed (one request, preload matches, `font-display: optional` deployed). But PDP CLS is unchanged (0.2324/0.2349) because a **new** shift replaced it — see regression R1. |
| 9 | Cart abandons the design language | **CLOSED** (brand) | `crk-*` cart deployed: dark ground, house type, tracked-shipping options, free-shipping progress. The **critical** axe violation (`aria-required-children`) and `aria-allowed-role` are gone. Wallet chrome remains Shopify-owned (accepted limit). Weight regressed for an unrelated reason (R2). |
| 10 | No order tracking anywhere | **CLOSED** (theme side) | `/pages/tracking` exists; TRACKING in menu and footer; `trackWordPresent: true`. The hosted account page (Times New Roman, no order lookup) is still unbranded — admin. |
| 11 | Placeholder measurements | **OPEN** | Identical arithmetic-progression table, still shared between denim and baggies. |
| 12 | Contradictory delivery claims | **OPEN** | `9-16 days delivery uk 16-21 days international` still in the jeans descriptions against `UK 1–2 working days` in custody. Admin copy edit. |

### Worth doing

| # | Finding | Status | Evidence |
|---|---|---|---|
| 13 | Custody label hides shipping | **CLOSED** | Live label: `CHAIN OF CUSTODY — SHIPPING & RETURNS`. Copy inside untouched. |
| 14 | No new-arrival signal | **CLOSED** | `FILED 03.08 / 13.07 / 19.07×2` live on exactly the four products inside the 30-day window; the other ten read `AVAILABLE`. In-voice, format preserved. |
| 15 | 200% zoom reflow (WCAG 1.4.10) | **CLOSED** | scrollWidth 195 == 195, no horizontal scroll; 320 px overflow also gone. |
| 16 | Jeans: one photo, back view | **PARTIAL** | Now `Photo 1 of 2`. Better; not a gallery. |
| 17 | 1.17 MB JS everywhere | **PARTIAL** | Base44's 166 KB off PDPs/cart via #5. Horizon bundles unchanged (platform). |
| 18 | Banner takes first 4 tab stops | **OPEN** | Same 4 stops, same invisible focus on `Manage preferences`. Same admin setting as #4. |
| 19 | `--crk-micro` contrast 2.57:1 | **CLOSED** | Token now carries `--crk-dim` values in both modes; zero real contrast failures site-wide. |
| 20 | Contact page empty | **OPEN** | Still a bare form. |
| 21 | Filter chips scroll unsignalled | **CLOSED** | A deliberate 10 px peeking-chip cue is present (it appears in the overflow scan — that is the cue working, not a defect). |
| 22 | `← CATALOGUE` 92×16 tap target | **CLOSED** | No theme-owned target under 44 px found this run. |
| 23 | Return postage liability unstated | **OPEN** | `whoPaysPostage: null` on the refund policy. |
| 24 | RELEASE REQUEST span | **RESPECTED** | Still a non-interactive `crk-label` span; nobody "fixed" it. |
| 25 | Game traffic exits permanently | OPEN (long-range) | Unchanged. |
| 26 | Retired runs deleted not archived | OPEN (depends on #2) | Unchanged. |

**Score: 11 CLOSED, 5 PARTIAL, 9 OPEN (8 of them admin-only), 1 respected non-fix.**

---

## 2. REGRESSIONS — new since run 1, both from the fix sprint's own footprint

### R1 — PDP CLS 0.2315: the meta row re-wraps when VT323 arrives late *(theme, cheap)*

The font fix worked; the number didn't move. `header.crk-meta` sets `PRODUCT NN / 14` in
`crk-display` (VT323) inside a wrapping row. Under `font-display: optional` the first paint uses
the wider fallback → the row wraps → at ~5.5 s (throttled) deferred JS mutates the DOM, the
re-laid row picks up the loaded VT323, un-wraps, and the grid below jumps 28 px. Ablation:
block vt323 → CLS 0.001; block crx-mono → 0.2317. Fix: guarantee the row a single line
(nowrap + min-width reservation for `.crk-meta-exh`, or a metric-compatible fallback stack).
**This is the top theme-code item in the new backlog.**

### R2 — The cart inherited a broken master *(admin, minutes)*

`cellcrew.webp` (976 KB served as PNG) now renders on the cart. Cart transfer 4,215 KB
*(r1: 4,024)*, LCP 9,444 ms *(r1: 7,948)*, image weight 1,340 KB *(r1: 946)*. One re-upload
fixes the money page and the homepage simultaneously.

### Watch list (not regressions yet)

- ADD TO BAG sits deeper (1.37 vh, was 1.04) with the description accordion open by default —
  the sticky buy bar covers it, but watch scroll-to-buy on real analytics.
- Homepage INP sampled 1,144 ms (r1 656) with the popup initialising; cart INP 1,096 (wallet
  iframes). Both third-party-driven; re-sample before treating as trend.
- Board in-viewport fps sampled 45.7–51 (r1 60) under audit CPU load; guards all intact.
  Code unchanged — assume variance until a quiet-container run says otherwise.

---

## 3. COMMERCIAL DELTA (Admin API, both pulls same day)

| Metric | Run 1 (morning) | Run 2 (evening) |
|---|---|---|
| Lifetime orders | 764 (CROOKS-1764) | 764 (unchanged — no new orders between runs) |
| August to date | £994.66 / 16 orders | £930.67 / 16 orders (**−£63.99 reversed** on an existing order) |
| MONEY CLIVE TEE | −22 total | **100** (10/variant) — `CONTINUE` still set |
| 3 CLIVES TEE | −19 | **100** — `CONTINUE` still set |
| BROADCAST TEE | −8 | **100** — `CONTINUE` still set |
| CRXST★RZ | 970 (suspected artefact) | **98** — artefact confirmed and corrected |
| CRX GARMS (archived) | 985, `CONTINUE` | 985, `CONTINUE` — untouched |
| V2 BAGGIES / M | −1, `DENY` | −1, `DENY` — untouched |
| Archived+draft inventory | 1,452 units | 1,452 units — untouched |

The June −£195.09 month and the fresh −£64 reversal are both consistent with the oversell→refund
loop. The restock stopped today's bleeding; the `CONTINUE` policy keeps the wound openable.

---

## 4. CORRECTIONS TO THE RUN-1 RECORD

1. **BACKLOG #3's headline mechanism was wrong** (and FIX-PROMPTS repeated a second wrong
   theory). The frozen-tap evidence came from the harness's own overlay-removal selector never
   matching the cookie banner — taps landed on the banner in both runs. Not variant logic
   (run 1's claim), not the popup (FIX-PROMPTS' claim — the popup class *was* removed
   correctly). The banner alone. The underlying code gaps were real and are now fixed.
2. **The journey instrument cannot see filing dates** (`AVAILABLE|SOLD OUT|NEW|LOW` whitelist)
   — its `anyDates: false` in run 2 is false. Verified by direct fetch: four cards carry dates.
3. **The `pressed` field in both runs' checks.json is unreadable** (operator-precedence bug).
   Ignore it in any future reading of either file.
4. Run 1's METRICS attributed the PDP CLS wholly to the font swap. Correct for run 1 —
   but the persistence of 0.232 into run 2 is a different mechanism (R1). The number's
   stability across runs is a coincidence of geometry (same 28 px row, same viewport).

---

## 5. THE NEW TOP FIVE

1. **Flip `CONTINUE` → `DENY` on the three tees** (+ decide CRX GARMS). Admin, minutes. The
   restock without the policy change is a countdown, not a fix.
2. **Decide the archived catalogue.** Admin, hours. Unchanged since run 1: ~£28k of proven
   sellers invisible, including the #1 lifetime seller.
3. **Re-upload the three remaining masters** (`cellcrew`, `v2baggies`, white/red socks).
   Admin, minutes. Closes the cart regression and ~700 KB of the homepage.
4. **Fill the legal placeholders, fix the contact page, move the cookie banner.** Admin,
   under an hour. Persona 4 — the only persona still leaving — is entirely these three items.
5. **Reserve the PDP meta row against font-width variance** (R1). Theme, minutes. The last
   theme-owned defect above POLISH grade.

Everything else theme-side is done and verified. The storefront has caught up with its own
backlog; the admin hasn't.
