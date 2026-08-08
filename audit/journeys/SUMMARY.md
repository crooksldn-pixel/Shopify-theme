# PHASE 2 — PERSONA JOURNEYS: SUMMARY (RUN 2, RE-AUDIT)

Same eight scripted walkthroughs as run 1, same devices and throttles, against the fixed theme
(`db96aa3`) on a fresh preview. Run-1 outcomes in brackets.

---

## Outcome by persona

| # | Persona | Run 2 outcome | Run 1 outcome | What changed |
|---|---|---|---|---|
| 1 | Cold Instagram click | **Would buy** | Would buy *if they survive 25 s* | LCP 14.3 s → 3.0 s; popup gone from PDPs; shipping findable by name |
| 2 | Returning fan | **Stays** | Would leave | Filing dates on 4 cards; honest sold-out state + notify |
| 3 | Size-anxious denim buyer | **Would buy** | Would buy | 2nd photo on jeans; measurements still placeholder (admin) |
| 4 | The sceptic | **Would leave** | Would leave | Nothing on their checklist changed — all admin items |
| 5 | Aimless browser | **Returns, follows** | Returns, follows | Unchanged by design; filing dates add a return hook |
| 6 | Accessibility user | **Would buy** | Would buy; fails 200% zoom | Zoom reflow FIXED; contrast FIXED; cart critical axe FIXED |
| 7 | Slow connection | **Continues; cart still the worst moment** | Continues, unsettled at cart | Cart now in design language but heavier (cellcrew.webp) |
| 8 | Post-purchase | **Can track** | Cannot track at all | Tracking page + menu/footer entries |

**Run 1: 3 of 8 would leave or fail. Run 2: 1 of 8** — and persona 4's blockers are entirely
Shopify-admin surfaces (policy placeholders, contact page, cookie banner position).

---

## The three worst moments now

### 1. The cookie banner is the last overlay standing — and this run proved what it costs

With the popup gated to the homepage, the banner is the only thing between a first-visit shopper
and the page. It still covers 40% of the viewport, still takes the first four tab stops, still
physically covers the PDP size row and the footer trust links at scroll 0. Run 2 additionally
established (METRICS §10) that the banner — not variant logic — was what made run 1's sold-out
taps look broken. One admin setting (banner position) resolves persona 4's click-blocking, the
tab order, and the heading-order violation at once.

### 2. The cart pays for one file

4,215 KB and a 9.4 s LCP on the money page, of which 976 KB is `cellcrew.webp` — a master
uploaded under a `.webp` name that the CDN refuses to transcode, newly present on the cart via
the crewneck image. Two more masters like it remain on the homepage. Re-uploading three files
closes the single largest avoidable weight left on the site.

### 3. The PDP still shifts 0.23 — but it is a NEW shift

The round-1 font fix landed and works. What replaced it: the PDP meta row sets
`PRODUCT NN / 14` in display type (VT323) inside a wrapping row; the fallback face is wider, the
row wraps at first paint, and when deferred JS touches the DOM at ~5.5 s the row un-wraps in the
by-then-loaded font and the page jumps 28 px. Theme-owned, introduced by the fix sprint's own
PDP additions, cheap to fix (reserve the row), and the only new theme defect of consequence.

---

## What run 2 corrects about run 1

**The "silently sells the wrong size" headline was contaminated.** The tap harness's overlay
removal used a selector that never matched the cookie banner (`.shopify-pc__banner` vs actual
`shopify-pc__banner__dialog`), so its centre-point taps landed on the banner in both runs, and
its `pressed` capture was unreadable (precedence bug). What was real in run 1: the notify block
only existed at product level, the stock line reported the product not the variant, and a
first-visit shopper genuinely could not reach the size row under the banner. What was not real:
working variant logic silently swapping sizes. Corrected instrument: `p2-checks-corrected.mjs`;
corrected evidence: `checks-corrected.json`; both runs' original captures kept for the record.

**The badge capture cannot see `FILED …`.** The journey script whitelists
`AVAILABLE|SOLD OUT|NEW|LOW`, so it reported `anyDates: false` while four cards visibly carry
filing dates. Fix the regex before run 3.

---

## What the journeys agreed on, run 2 edition

**The fix sprint held where it counted.** Every theme-code fix verified: popup scope, font
single-load, contrast token, zoom reflow, custody label, tracking page, filing dates, variant
sold-out + notify, the cart brand pass. No fix broke anything load-bearing: the board's guards,
the no-JS fallback (18 links / 40 images re-verified), the register format and the measurement
apparatus all intact.

**Everything still failing a persona is in Shopify admin, not the theme** — policy placeholders,
contact page, banner position, measurements, delivery-claim contradictions, the hosted account
page, return-postage liability. The theme ran out of things to fix; the admin backlog did not.

**The new defects are the sprint's own footprints** — the meta-row CLS and the cart's cellcrew
regression. Small, cheap, and exactly why a verification pass follows a fix sprint.
