# AUDIT-CONTEXT.md — what an advisor needs that the evidence files don't frame

This file frames the evidence pack for the council. It deliberately does not
restate `SPEC.md` (the build map — read it, trust it) or the findings
themselves. Evidence: `features/FEATURES.md` + eight `features/raw-*.md`,
twenty journey logs in `journeys/` + `journeys/SUMMARY.md`, and
`QUESTIONS.md` (the four open design questions, answered from evidence).

## Commercial reality

14 active products, £6–£60 (one £85 bundle). Short runs that do not restock —
sold out is usually forever, which makes "notify me" copy and drop timing
strategically odd in ways a generic ecommerce lens will miss. No reviews, no
press, no retail presence, no paid acquisition mentioned. Traffic is almost
entirely Instagram and TikTok: mobile, one-handed, young, cold. Every sale is
a stranger trusting an odd-looking site with up to £60. The audit ran twenty
such strangers: 15 reached checkout; zero abandoned over the way it looks.

## The design law (quoted from SPEC.md §0)

> *The fiction stops where it would cost a sale.* Flavour lives in chrome —
> never in sizes, stock, price, add-to-cart, shipping or returns. `ADD TO
> BAG`, `£60.00`, `SIZE M`, `IN STOCK` are always plain English.
> Radius `0`, borders `1px`, no shadows, no gradients. Enforced in CSS, not
> left to discipline.

## Deliberately rejected — decisions, not oversights

Trust badges, reviews widgets, countdown timers, fake stock counters,
"17 people viewing", live chat, exit-intent popups, stock photography,
models, rounded cards. The proposition is that the store does not look like a
Shopify store. The refusal to fabricate extends to data: the CASE 001
leaderboard stays hidden because no real score source exists; placeholder
scores are never rendered.

## The protect list

`SPEC.md §9` (eleven deliberate behaviours that look like faults) and
`audit/KEEP.md` on branch `claude/crooksldn-site-audit-eijmkd` are the
authority. Recommending against an item there requires a specific journey
step showing a real shopper cost — general preference for convention is not
evidence. `FEATURES.md` ends with ten Phase-1 candidates for *additions* to
that list.

## The tension the council exists to resolve

The design is doing real brand work — the journeys prove it converts sceptics
and survives every accessibility profile — and it may still be doing real
conversion damage in specific places. Both can be true. The question is not
"should it look normal" (it shouldn't; that argument is settled by evidence
here three audits running) but **which specific elements cost sales, which
earn their keep, and what is the single highest-value change.**

Three framing facts the evidence pack supports strongly:

1. **The brand's substitute for social proof is exact numbers and
   self-consistency** — so contradictions (delivery copy, returns windows,
   fit copy) are not copy bugs, they are direct hits on the trust mechanism.
2. **The worst shopper moments are third-party, not theme:** the Crack the
   Cuffs popup (12/20 journeys complained; its prize mechanism is broken),
   the hCaptcha on notify/contact forms, the stock white checkout, the
   unbranded login domain, AfterShip's conflicting 30-day policy. The
   terminal fiction itself never cost a sale.
3. **Several money-adjacent mechanics have real bugs** (CHECKOUT NOW
   double-add, discount lost at checkout handoff, set-cart saving line absent
   in the normal case, stale carriage copy on PDP adds) that no amount of
   design debate touches.

## Constraints on recommendations

Every recommendation must be implementable without adding: a border-radius
above 0, a gradient, a shadow, a third typeface, a new accent colour,
fabricated content, or a build step. Known defects and open decisions
(D1, O1–O4 in `SPEC.md §10`, plus the admin items in RUN3 §B) are already
logged — do not propose them as discoveries; do build on them.
