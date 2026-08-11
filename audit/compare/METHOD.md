# COMPARISON AUDIT — METHOD AND SCORING

## Sites
Six competitor sites (URLs supplied) + the CROOKSLDN crooks theme measured by the **same
generic toolkit** — the staging preview if alive, else the live site once the theme ships.
The crooks run-2 deep audit supplies depth; the generic pass supplies apples-to-apples numbers.

## Instruments (all per-site, identical order)
`run-site.sh <tag> <homeUrl> [pdpUrl]` → recon (shape, platform, SEO surface, overlays,
bot-wall detection) → perf (home + PDP mobile throttled, PDP desktop) → a11y (axe wcag2a/aa +
21a/aa, tab order, 200% zoom) → commerce (first-viewport answers, size guide → measurement
quality, delivery claims, sold-out signals, non-destructive add-to-cart, trust pages) →
ten persona journeys.

Rules of engagement: cookie banners are dismissed the way a shopper would (Accept). Add-to-cart
at most; never checkout, never account creation, never form submission. One measurement pass
per site (bot-politeness); bot walls recorded honestly, and blocked instruments marked
`unmeasured`, never estimated.

## Scoring — ten dimensions, 0–5 each, evidence-cited
Every score must cite a number or artefact from `evidence/`. No vibes.

| Dimension | Fed by |
|---|---|
| 1. First-viewport answers (PDP) | commerce.fv, perf |
| 2. Mobile speed | perf: LCP / CLS / INP / weight |
| 3. Interruption load | recon overlays, cookie banner size, popup timing |
| 4. Size & fit apparatus | p3: guide, units, dimensions, method, model info |
| 5. Scarcity honesty | sold-out signals, urgency/countdown detection (true scarcity vs manufactured) |
| 6. Trust plumbing | p4: policies, contact, placeholders, email/address |
| 7. Accessibility | a11y: axe, focus, keyboard ATC, zoom |
| 8. Brand consistency to payment | cart/checkout identity vs site (screens + commerce.atc) |
| 9. Search surface | recon.seo: titles, meta, h1, JSON-LD, vocabulary |
| 10. Post-purchase path | p8: tracking, returns, account, FAQ |

## Report structure (`REPORT.md`)
1. Executive verdict — where crooks wins, where it loses, the three moves that matter.
2. The scoreboard — 7 sites × 10 dimensions with the evidence line per cell.
3. Per-site profiles — one page each: what this competitor does best, worst, and the one
   thing worth stealing (reworked in-voice, never copied).
4. Persona narratives — for each of the ten: who serves them best, who worst, where crooks
   ranks, with the felt-experience note.
5. The steal list — concrete backlog items for crooks, each with evidence, effort, and a
   KEEP.md check (nothing that sands off what the audit proved load-bearing).
6. The moat list — what crooks does that no competitor does, i.e. what must not be traded.
