# PERSONA 1 — COLD INSTAGRAM CLICK (RUN 2)

Mobile 390×844, Slow 4G, 4× CPU. Landed directly on the 3 CLIVES TEE PDP from a story link.
Run 1 verdict: *would buy, if they survive 25 s.* Run 2 verdict: **would buy — the 25 s survival
test is gone.**

## What happened this time

**Step 1, 1.5 s — the first viewport already answers all four questions.** Title, `£25.00`,
`SIZE XS S M L XL`, a new `Colour` row, `IN STOCK`, and BOTH buy actions (`Add to bag`,
`Checkout now`). LCP on this journey measured **3,024 ms** *(run 1: 14,252 ms)* — the re-uploaded
hero master transcodes properly now.

**The game popup did not fire.** It is gated to the homepage *(run 1: fired over this PDP at 3 s,
100% of viewport, scroll locked)*. The scripted step "popup fires on a 3 s timer" recorded no
overlay this run.

**The cookie banner is now the only interruption** — still 338 px, still over the size row and
sticky bar until dismissed. Run 1 stacked three interruptions on this shopper; run 2 has one,
and it is the one the theme cannot fix (admin setting).

**Step 7–8 — shipping is findable by name.** The accordion label now reads
`CHAIN OF CUSTODY — SHIPPING & RETURNS` *(run 1: unlabelled fiction; this persona went
"hesitant" here)*. A dispatch line (`Order before 18:00 and it ships today`) sits on the PDP.

## Still in the way

- The description on the jeans PDPs still carries `9-16 days delivery uk 16-21 days
  international`, contradicting `UK 1–2 working days` in the custody steps (admin, BACKLOG #12).
- At ~5.5 s the page bumps once (CLS 0.2315, the meta-row/VT323 re-wrap — new finding this run).
  It lands after the buy decision is on screen but can move the size row mid-tap.

**Outcome: converts, ~3 taps, no dead seconds.** The r1 abandonment risk (14 s of nothing, then
an overlay) is closed.
