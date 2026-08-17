# DELTA-3WAY.md — THREE AUDITS OF THE CROOKS THEME, COMPARED

**Run 1** · 2026-08-08 morning · theme `1b6bc4c` (pre-fix) · evidence `15ef712`
**Run 2** · 2026-08-08 evening · theme `db96aa3` (+20 fix commits) · evidence `3b9bba7`
**Run 3** · 2026-08-17 · theme `d0363ee` (+13 more: FAQ, terms, search, menu/homepage rework) · evidence this commit

Same harness, same devices (390×844 @3x mobile, 1440×900 desktop), same Slow-4G / 4× CPU
throttle, same eight personas, across all three runs. Instrument corrections are recorded where
they affect comparability (sold-out tap methodology from run 2; FILED-aware badge capture from
run 3).

---

## 1. THE VERDICT IN ONE TABLE

| | Run 1 | Run 2 | Run 3 | Trajectory |
|---|---|---|---|---|
| Personas abandoning | **3 of 8** | **1 of 8** | **0 of 8** | ✅ solved in two sprints |
| Worst LCP (mobile) | 13.9 s (tee PDP) | 9.4 s (cart) | 10.3 s (cart) | ✅ then ≈ flat |
| Homepage weight | 3,103 KB | 2,560 KB | 2,725 KB | ✅ then ≈ flat |
| Mobile CLS, worst page | 0.233 (PDPs only) | 0.235 (PDPs only) | **0.391 (every page)** | ❌ **regressed site-wide** |
| Mobile INP, PDPs | ~640 ms | ~600 ms | **~1,050 ms** | ❌ regressed |
| axe serious/critical (theme-owned) | 1 critical (cart) | 0 | 0 | ✅ held |
| WCAG zoom reflow | FAIL | PASS | PASS | ✅ held |
| Trust placeholders on legal pages | 6 kinds | 6 kinds | **0** | ✅ closed in run 3 |
| Return-postage liability stated | No | No | **Yes (TERMS)** | ✅ closed in run 3 |
| Working site search | No field at all | No field at all | **Full: field + typeahead + pages + no-JS** | ✅ new in run 3 |
| FAQ / self-serve answers | None | None | **14 Q&As, in-voice, no-JS** | ✅ new in run 3 |
| Sold-out honesty | Product-level only, no notify | Variant-level + notify, verified | Verified again | ✅ held |
| Recency signal | None | FILED dates (4 cards) | FILED dates (instrument-confirmed) | ✅ held |
| Order tracking | None | Page + menu + footer | + FAQ answers | ✅ compounding |
| Oversell policy (admin) | CONTINUE, −49 units | CONTINUE, restocked | **CONTINUE, depleting again (8–9 left)** | ❌ three audits, untouched |
| Archived stock (admin) | 1,452 units / ~£28k | identical | identical | ❌ three audits, untouched |
| Mis-named image masters | 8 | 3 | 3 | ✅ then stalled |
| Cookie banner (admin) | blocks size row + footer | same | same | ❌ three audits, untouched |
| Contact email consistency | Gmail vs info@ | same | same **+ `gmail.com.com` typo** | ❌ got worse |
| Lifetime orders at pull | 764 | 764 | 786 | trading through all of it |

**Grade: the storefront's *content* problem is solved — the theme now answers every question a
shopper, a sceptic, or a returning customer can ask, which no measured competitor manages. The
storefront's *stability* problem was re-created by the newest sprint: one font-metrics
mechanic has now produced the top theme defect in two consecutive audits, and in run 3 it
reaches every mobile page. And the admin list has not moved in nine days of active trading.**

---

## 2. IMPROVEMENT LEVEL, DIMENSION BY DIMENSION

### Massively improved across the three runs
1. **Persona survival: 3 leavers → 1 → 0.** Run 1's leavers went over inventory lies, overlays
   and bracketed placeholders. Run 2 closed the mechanics (variant sold-out + notify, tracking,
   custody label, popup scope). Run 3 closed the paperwork (policies, terms, FAQ) and the
   sceptic — the last leaver — now stays. No measured abandonment cause remains except the
   admin items.
2. **The tee PDP arrival: 13.9 s → 2.4 s → ~2.8–3.7 s.** The single worst number in run 1 has
   stayed dead for two runs (admin re-upload + theme diet).
3. **Trust surface: from `[LINK TO REFUND POLICY]` to a nine-section terms page** that states
   the return window, postage liability, faults and lost-parcel handling — in the site's own
   design system, findable by search, backed by a 14-question FAQ. Runs 1–2 scored trust
   plumbing 2/5 against competitors' 4/5; run 3's surface now exceeds what Mertra and Phase
   ship — one email string short of clean.
4. **Findability: no search field at all → complete search.** Field, typeahead with prices,
   product and page results, no-JS fallback. Two audits listed it as absent; run 3 verified it
   end to end on the first try.
5. **Accessibility: 1 critical + zoom failure → clean and stable.** The run-2 ground survived
   thirteen further commits byte-identical: same (minor) axe sets, zoom passing, keyboard path
   intact, new pages readable without JS.

### Improved, then stalled
6. **Page weight:** −543 KB in run 2, +165 KB in run 3 (noise). Still 4–8× lighter than every
   competitor measured — but the same three mis-named masters (`cellcrew` on the cart at
   976 KB) have now survived three audits unchanged.
7. **Post-purchase:** run 2 built tracking; run 3 added FAQ answers; the hosted account page
   (Times New Roman, no order lookup) is untouched across all three.

### Regressed
8. **Layout stability — the headline downgrade.** Runs 1–2: CLS ~0.23, PDPs only, two
   different font-swap mechanisms. Run 3: **0.325–0.391 on every mobile page** (journey
   stacking 0.59): the new header control row wraps when CRX Mono lands (`font-display: swap`,
   flex bar free to grow, probe-verified 48 px MAIN drop at t≈1.9 s; ablation: block CRX Mono
   → 0). The pattern is now structural: **fonts with unmatched fallback metrics doing
   layout-critical work** caused the top theme defect in run 2 (VT323 meta row — since fixed)
   and again in run 3 (CRX Mono header). The council's round-2 prescription — `size-adjust`ed
   fallbacks in the font stacks — was applied to neither face; no `size-adjust` exists in the
   deployed CSS. Until it does, every new mono-set surface ships this bug again.
9. **Responsiveness: INP ~600 ms → ~1,050 ms on PDPs**, ~1.1–1.2 s everywhere. Arrived with
   the search index + menu-hosted game sprint; not yet isolated to a single cause.
10. **First-viewport size access on fuller PDPs:** V2 BAGGIES' size row now sits exactly at
    the 844 px fold after the header growth — the protected KEEP §2 answer degraded on the #2
    lifetime seller (logic intact, geometry regressed).
11. **The email string got worse:** three audits of Gmail-vs-info@ inconsistency, now plus a
    literally undeliverable `crooksldn@gmail.com.com` on the shipping policy.

### Untouched through all three audits — every one of them admin, none of them design
- `inventoryPolicy: CONTINUE` on the three tees — restocked between runs 1–2, **now selling
  back down toward the trap** (variants at 8–9 units on live trade, 22 orders in 9 days).
- The archive: 1,452 units (~£28k retail at hand-count-pending figures), identical three pulls.
- The cookie banner: 40% of viewport, first four tab stops, still the only thing standing
  between a first visit and the size row.
- The measurement tables: same placeholder arithmetic in all three runs.
- The jeans descriptions' `9-16 days delivery` contradiction.
- Product photography (1→2 photos in run 2, nothing since).

---

## 3. WHAT EACH SPRINT TEACHES

**Sprint 1 (runs 1→2)** fixed what the audit measured, and its two regressions were its own
footprints (meta-row CLS, cellcrew-on-cart). Verification caught both within hours.

**Sprint 2 (runs 2→3)** built new surfaces to a visibly higher standard — search, terms and
FAQ arrived complete, in-voice, accessible and no-JS-safe on first measurement — but repeated
sprint 1's exact class of regression at larger scale, because the systemic fix (font fallback
metrics) was prescribed and not implemented. The lesson is not "stop shipping": it is that
**this codebase now needs its two standing invariants enforced in code, not in review**:
1. No font with unmatched fallback metrics above the fold (size-adjust fallbacks for both
   faces, once, ends the recurring defect class).
2. No new surface above the register/first viewport without re-measuring the fold
   (header +48 px cost V2 BAGGIES its size row).

**The admin story is the same story three times.** The theme has now out-shipped its own shop
twice over. Nine days of live trading sold the three CONTINUE tees down to single digits per
variant. The next sell-out event will either fire the notify capture the theme built — or
sell phantom stock again, depending entirely on three checkboxes nobody has ticked since the
first audit named them.

---

## 4. THE LIST NOW (post-run-3 priorities)

1. **[A] The three checkboxes.** CONTINUE→DENY. Third audit. Variants at 8–9 units. Days, not
   weeks, from mattering.
2. **[T] Reserve the header + `size-adjust` both font stacks.** Ends the site-wide CLS and the
   recurring defect class, and restores V2 BAGGIES' size row to the viewport. Hours.
3. **[A] One find-and-replace on the email** (`info@crooksldn.com` everywhere; kill
   `gmail.com.com`). Minutes, and it completes the sceptic's conversion three audits in the
   making.
4. **[A] The three masters** (`cellcrew` rides the cart). Minutes. Third audit.
5. **[T] Chase the INP doubling** (search index + menu game are the suspects). Then the FAQ's
   missing FAQPage schema, the banner position, the archive decision — all as previously
   specified in BACKLOG.md.
