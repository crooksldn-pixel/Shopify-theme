# DESCRIPTIONS.md — the rewrite, the council's rulings, and the record

2026-08-19. All 13 active products' descriptions rewritten via the Shopify
Admin API, verified rendering on crooksldn.com. Before-state in `BEFORE.json`
(committed prior to any write). Debated by a five-advisor council
(Contrarian / First Principles / Expansionist / Outsider / Executor) with
anonymized peer review (5 reviewers) and a chairman synthesis; working papers
in the session scratchpad, verdict reproduced here.

## The rules the copy now obeys (from the 40-journey evidence)

1. **No delivery times in descriptions** — the custody accordion owns them.
   The "9–16 days delivery UK" lines on crewneck and shorts are deleted.
2. **Fit words match the spec metafield** — "baggy, stacked" is gone from
   jeans specced "OG straight, mid rise"; now "Structured, not baggy."
3. **The wash/colour is named in words** — "grey wash, for the record." /
   "blue wash, for the record." (persona 10's answer; persona 16's image).
4. **No overclaims** — "premium heavyweight cotton" on a 220gsm tee is now
   "220gsm cotton"; every material claim traces to a store data field.
5. **Weight-entailed drape claims only** — "heavy enough to hang straight"
   (500gsm) and "heavy enough to hold its shape" (14oz) ship; "stacked",
   "stands away from the leg" and "all day" were cut by the council.
6. **Numbers live once** — the £85/£95 arithmetic appears only on the set's
   own page, beside the live price that verifies it (ruled 4–1 over the
   no-numbers position; the reprice contract is owner flag 2).
7. **Voice only where it carries a fact** — "for the record" (restates the
   wash), "Counted, not estimated" (restates the pack counts) survived;
   "Nothing further to declare" and friends were cut as garnish.
8. **Mirrored pairs differ only where the products differ** — jeans, jorts
   and socks twins are one-token diffs by construction.

## Before → after (all 13)

| Product | Was | Is now |
|---|---|---|
| V2 BAGGIES | "500GSM - 100% cotton" (+ stray empty span) | "V2 Baggies — wide, full-length sweats in 500gsm cotton, heavy enough to hang straight. / Made in Portugal." |
| LARGE DUFFLE BAG | "55CM LENGTH" | "A 55cm holdall in ballistic nylon. / From Unit 7, London." |
| BLACK/BLUE MOTIONTEC SOCKS | "…engineered for constant movement. / Same/Next-Day Dispatch." | "MotionTec™ socks in black and blue — cotton blend, reinforced heel, made for constant movement. / One pair, or packs of 3, 6 or 12. Counted, not estimated." |
| WHITE/RED MOTIONTEC SOCKS | same as black (incl. dispatch line) | mirror of black — "in white and red" |
| CRXST★RZ T-SHIRT | "…Wokstar energy only. / Boxy fit with a clean structure." | "CRXST★RZ tee — Wokstar energy only." ("boxy" dropped 4–1: no data behind it; see owner flag 1) |
| GREY WASH OG JEANS | "…Heavyweight denim with a baggy, stacked fit." | "OG jeans — grey wash, for the record. / 14oz denim, OG straight cut, mid rise. Structured, not baggy. / Made in Portugal." |
| BLUE WASH OG JEANS | identical to grey (copy-paste) | one-token mirror: "blue wash, for the record." |
| BLUE WASH JORTS | "…Premium heavyweight denim with a baggy fit and signature back pocket artwork." | "Blue wash jorts — baggy 14oz denim shorts, finishing below the knee, with the signature back-pocket artwork. / Heavy enough to hold its shape." |
| GREY WASH JORTS | mirror | mirror ("Grey wash jorts…") |
| CHARCOAL CELLBLOCK CREWNECK | "…Premium heavyweight fabric… / **9–16 days delivery UK / 16–21 days international**" | "Cellblock crewneck in charcoal — 450gsm brushed fleece, relaxed cut, 3D embroidery. / Pairs with the Cellblock Shorts; sold together as the Cellblock Set. / Made in Portugal." |
| CHARCOAL CELLBLOCK SHORTS | same pattern + "3D embroidered" + delivery lines | "Cellblock shorts in charcoal — 450gsm brushed fleece, relaxed cut finishing above the knee, 3D embroidery. / Pairs with the Cellblock Crewneck; sold together as the Cellblock Set. / Made in Portugal." |
| MONEY CLIVE TEE | "…Premium **heavyweight** cotton with a **relaxed** fit…" (spec: 220gsm, boxy) | "Money Clive tee — bold front graphic on 220gsm cotton. / Boxy, drop-shoulder cut. Printed in London." |
| CELLBLOCK SET | **(empty)** | "The full Cellblock fit — charcoal crewneck and shorts in 450gsm brushed fleece, one line in the cart, a size chosen for each. / £85 against £95 bought separately." |

## Owner flags from the council (data gaps — not copy problems)

1. **CRXST★RZ tee (blocking):** zero `crooks.*` metafields — the
   SPECIFICATION accordion is empty on a live £25 product. Add
   fabric/cut/origin/care; confirm "boxy" before a fit word returns. *Applier's
   note: the variant data shows Black and White colourways — a colour sentence
   is unlockable as soon as the owner confirms which the photos show.*
2. **Reprice contract:** if crewneck (£50), shorts (£45) or set (£85) ever
   reprice, the set description's "£85 against £95" must change the same day —
   it is deliberately the only price figure in prose.
3. **Embroidery placement:** "on the chest" is unverified — confirm to unlock
   it; also confirm the crewneck/shorts embroideries match before "to match"
   returns.
4. **V2 Baggies colourway:** unknown from data; name it to satisfy the
   colour-in-words rule.
5. **Socks:** height and size range unknown — add to metafields before any
   size claim; white socks have no care metafield (do not copy-paste black's).
6. **Crewneck/shorts measurements metafield missing** — already cost a £50
   sale in the audit (persona 9/11).
7. **Money Clive tee:** graphic content undescribed — one verified visual
   sentence would give screen-reader shoppers their image.

## Verification

- All 13 mutations returned the stored HTML byte-identical to the council's
  final copy.
- Live-render spot check on crooksldn.com: "for the record" (jeans), "sold
  together as the Cellblock Set" + no "9–16 days" (crewneck), "£85 against
  £95" (set), "Counted, not estimated" + "white and red" (socks).
- The staging share-preview link has expired; descriptions are product data
  and render identically under both themes.
