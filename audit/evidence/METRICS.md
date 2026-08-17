# CROOKSLDN — PHASE 1: INSTRUMENTED EVIDENCE — RUN 3

Generated 2026-08-17 against preview `bbushaa5dr2elw8f…`, staging theme id 202053779799, now
carrying thirteen further commits (`db96aa3 → d0363ee`) on top of run 2's twenty. Run 2 numbers
*(r2: …)* are from 2026-08-08 (commit `3b9bba7`); run 1 *(r1: …)* from the same morning
(`15ef712`). Same harness, devices, throttles across all three runs. The share-link failure that
voided the first attempt is documented in the git log; this run completed on one priming with
persisted session cookies.

---

## 1. THE HEADLINE: one regression now owns the mobile experience

### 1.1 — CLS 0.325 on EVERY mobile page — a new, single, site-wide shift

| Page | r1 | r2 | **r3** |
|---|---|---|---|
| Homepage | 0.0017 | 0.001 | **0.3252** |
| PDP tee | 0.2333 | 0.2349 | **0.3269** |
| PDP denim | 0.2327 | 0.2324 | **0.3252** |
| Cart | 0.0218 | 0.0113 | **0.3906** |
| Desktop (all) | ≤0.006 | ≤0.012 | ≤0.0033 ✔ |

Mechanism, probe-verified: at t≈1.9 s `MAIN.content-for-layout` drops **48 px** because the
header above it grows a line. The new header control row (CATALOGUE · SEARCH · BAG · LIGHT
MODE · MENU, commit `9025814`) is set in CRX Mono with `font-display: swap` and sits in a
`min-height: 56px` flex bar; the fallback metrics fit one line, the real font wraps it to two.
Ablation: block `crx-mono.woff2` → **CLS 0**; block `vt323.woff2` → no change.

Two run-2 findings resolve inside this one: the VT323 meta-row shift (r2's 0.2315 at t≈5.5 s)
**no longer occurs** — but its replacement is bigger, earlier, and on every page including the
homepage and cart. On the cold-click journey profile the stacking reaches **CLS 0.59**.

**Fix:** reserve the header (`.crk-header__bar` fixed height + no-wrap discipline for the
actions row), and/or the `size-adjust` fallback for CRX Mono that round-2's council prescribed
for the display face — no `size-adjust` exists anywhere in the deployed CSS. Theme, hours.

### 1.2 — The size row reached the fold on the product that needs it most

After banner dismissal on V2 BAGGIES (390×844), the size buttons sit at **y=844** — the exact
bottom edge; centre-point taps land outside the viewport. On 3 CLIVES TEE the row remains
visible. The 48 px header growth spends exactly the margin that kept KEEP §2's first-viewport
answer ("does it come in my size") on screen for the fuller PDPs. The sold-out logic itself is
**intact** (probe: M → `SIZE M IS SOLD OUT`, buy disabled, form disarmed, notify shown) — the
regression is geometry, not behaviour.

### 1.3 — INP degraded everywhere

INP now 1,032–1,208 ms across all mobile pages *(r2: 584–1,144, PDPs ~600)*. The PDPs roughly
doubled. Suspects: the menu-hosted game assets and the typeahead's link index arriving in the
main thread. Not isolated this run — flagged for the next.

---

## 2. WHAT HELD (measured, unchanged or better)

- **Weights stable:** home 2,725 KB (r2: 2,560), tee 1,673, denim 1,831, cart 4,218. Still
  4–8× lighter than every measured competitor. The cart's `cellcrew.webp` (976 KB) is still
  there — the three mis-named masters remain un-fixed for the third audit.
- **LCP:** tee 3,684 (r2: 2,404 — image-order variance, same master), denim 4,860, home 4,608.
  No material change; cart 10,308 still the worst page, unchanged cause.
- **axe:** identical violation sets to run 2 on every page — the fix sprint's a11y ground held
  through thirteen more commits. Zoom reflow still passes (195==195). Keyboard order unchanged.
- **Sold-out + notify, FILED dates, custody label, popup gating:** all re-verified working.
  The re-instrumented badge capture now reads `FILED 03.08 / 19.07` directly.

---

## 3. THE NEW SURFACES (`newtabs.json`)

| Surface | Verdict |
|---|---|
| **Search** | **Works end to end, first time in three runs.** Header link → real field → typeahead (products with prices) → results for "jeans" (4, relevant) → surfaces pages for "returns" → renders without JS. |
| **QUESTIONS (FAQ)** | Linked in footer + menu, in design system, 14 Q&As covering delivery/sizing/returns/tracking, readable no-JS. **No FAQPage JSON-LD** — free rich-result unclaimed. |
| **TERMS** | Nine sections, 654 words, zero placeholders, in design system. **States the return window AND who pays return postage** — backlog #8 closed by copy. No governing-law clause (minor). |
| **Policy pages** | All three skinned into the design system; **placeholders GONE** (run 1 #7 finally closed). |
| **Menu** | Game lives here now (`PLAY CASE:001 NOW`), plus QUESTIONS/TERMS/TRACKING/CONTACT and a new TRACKSUITS category. |
| **Homepage** | Packaging manifest present; CASE 001 text also still present (both render). |

**The email problem survives a third audit, and grew a typo:** terms, refund and privacy pages
say `crooksldn@gmail.com`; the shipping policy says **`crooksldn@gmail.com.com`** — a dead
address on a legal page. The footer still says `info@crooksldn.com`. One find-and-replace.

---

## 4. INSTRUMENT NOTES

`p2-fix`/`p2-fix2` timed out waiting for the measurement table — it now sits inside the
deliberately-collapsed PDP panels (`97e1e01`); the same data landed via `checks.json`. The
corrected sold-out check reported false-negative taps because the size row sits at the fold
(§1.2) — behaviour verified by direct dispatch instead. Badge regex fixed this run (sees
FILED). Board fps: guards intact; in-viewport sample again environment-bound.
