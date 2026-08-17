# PHASE 2 — PERSONA JOURNEYS: SUMMARY (RUN 3)

Same eight walkthroughs, same conditions as runs 1–2, against theme `d0363ee` (thirteen commits
past run 2). Run-2 verdicts in brackets.

## Outcome by persona

| # | Persona | Run 3 outcome | Run 2 | What moved |
|---|---|---|---|---|
| 1 | Cold Instagram click | **Would buy — but the page jumps under their thumb** | Would buy | LCP fine (2.8 s); journey CLS **0.59** — header shift + stacking. New risk, not a blocker |
| 2 | Returning fan | **Stays** | Stays | FILED dates confirmed by fixed instrument; sold-out logic verified again |
| 3 | Size-anxious buyer | **Would buy — and can finally read the returns terms** | Would buy | TERMS states return window AND postage liability; measurements still placeholder |
| 4 | The sceptic | **Materially moved — hesitates instead of leaving** | Would leave | Placeholders GONE, policies skinned, terms complete, FAQ real. Still: Gmail everywhere + `gmail.com.com` typo, banner untouched |
| 5 | Aimless browser | **Returns, follows** | Returns, follows | Game now one tap away in the menu with a live pitch; packaging manifest adds a read |
| 6 | Accessibility user | **Would buy** | Would buy | axe/zoom/keyboard all held through 13 commits; header shift hits them too |
| 7 | Slow connection | **Continues; cart unchanged, everything now jumps** | Continues | Same weights; CLS 0.33–0.39 on every page; INP ~1.1 s everywhere |
| 8 | Post-purchase | **Can track AND self-serve answers** | Can track | FAQ covers tracking/returns; TRACK ORDER in footer; account page still hosted/unbranded |

**Run 1: 3 of 8 leave. Run 2: 1 of 8. Run 3: 0 of 8 leave outright — but 8 of 8 now ride a
page that visibly jumps at ~2 s on mobile.** The sceptic's exit is closed by the terms/FAQ/
policy work; their residual hesitation is one email string and a cookie banner.

## The three worst moments now

1. **The header grows a line under every mobile visitor** — CLS 0.325–0.39 site-wide (journey
   stacking to 0.59), CRX Mono swap wrapping the new control row. One reserved header height
   (or the long-prescribed `size-adjust` fallback) ends it. Theme, hours.
2. **The size row fell to the fold on V2 BAGGIES** — the exact surface where the sold-out
   honesty apparatus lives. Geometry, not logic. Same fix family as (1).
3. **`crooksldn@gmail.com.com`** on the shipping policy — a dead address on a legal page, on
   the brand's best-ever trust surface. Minutes, admin.

## What the journeys agreed on

The paperwork era is over: policies, terms, FAQ and search — the things two audits said made
the sceptic leave — are done and in-voice. What replaced them at the top of the list is a
single typographic mechanic the council already named in round 2: **fonts with unmatched
fallback metrics doing layout-critical work**. It has now caused the top theme defect in two
consecutive audits (VT323 meta-row in run 2, CRX Mono header in run 3). Until the font stacks
carry size-adjusted fallbacks, every new mono-set surface is a CLS regression waiting to ship.
