# BACKLOG.md — CROOKSLDN — REFRESHED AFTER RUN 3

Run-1 and run-2 lists live in git history; `DELTA-3WAY.md` scores all three runs. Council
round-3 verdict: `COUNCIL.md`. **Standing rule adopted from the council: no further theme
commits beyond item 2 until item 1 flips.**

---

## THE TOP FIVE (post-run-3)

| # | Item | Severity | Effort | Where |
|---|---|---|---|---|
| 1 | **[A] CONTINUE → DENY on the three tees** — third audit, now a countdown: variants at 8–9 units on live trade (22 orders/9 days). The next sell-out fires the notify capture or sells phantom stock; one checkbox decides. Decide CRX GARMS (985, archived, CONTINUE) in the same visit. | **BLOCKS** | minutes | Products → variants |
| 2 | **[T] Reserve the header; `size-adjust` fallbacks for BOTH faces.** CLS 0.325–0.391 on every mobile page (journey 0.59); V2 BAGGIES size row at the fold. `crx-mono.css:7,14` (swap, no fallback), `crooks.css:397` (min-height, not fixed), `:431–434` (wrap), stacks at `:47–48`. Fixes the site-wide jump, the fold regression, and the defect class that topped two audits. Verify: CLS < 0.05 all pages, size row back in viewport, zoom + no-JS intact. | **BLOCKS** | hours | `assets/` |
| 3 | **[A] Email find-and-replace** — `info@crooksldn.com` everywhere; kill `crooksldn@gmail.com.com` (undeliverable, on the shipping policy). Completes the sceptic. | **BLOCKS** | minutes | Settings → Policies + pages |
| 4 | **[A] The three image masters** — `cellcrew.webp` (976 KB) still on the cart, third audit. | BLOCKS | minutes | Products → media |
| 5 | **[A] The archive decision** — ~£28,270, frozen across three pulls, includes the #1 lifetime seller. Hand-count first; closed-case register per council round 2. The largest number in the pack vs ~£104/day of trade. | **BLOCKS** | days | Products → Archived |

**Then ship the theme.** All trading data still comes from the live site (14/50 in the
competitive field). The theme's measured advantages become receipts only in production.

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
