# COUNCIL ROUND 2 — RAW RESPONSES AND PEER REVIEWS

Advisors answered independently and were anonymised A-E for review (A=Outsider, B=Contrarian,
C=Executor, D=Expansionist, E=First Principles — order preserved from the workflow).
Reviewer sections are labelled by their content; the workflow's own labels were shuffled by
completion order and have been corrected here.


===== OUTSIDER =====

**THE OUTSIDER — ROUND 2**

Round 1, I said the PDP passed in a second and the cart was where the shop stopped being real. The cart is fixed — dark ground, house type, tracked-shipping options; persona 7's "handoff to somewhere else" moment is gone (journeys/07, "the cart no longer changes identity"). That was my highest-value change and it landed. New verdict: this now reads as a real shop everywhere I can see — and the remaining lie is somewhere I can't.

**Vocabulary, re-audited:**

- **PRODUCT 04 / 14 — helps, but now it moves.** Still the only element proving a finite, real catalogue. But the fix sprint set it in VT323 inside a wrapping flex row, and it is the entire remaining 0.2315 CLS: the fallback face wraps the row, deferred JS re-lays it at ~5.5 s, and the page jumps 28 px — "can move the size row mid-tap" (METRICS §1.2; journeys/01). Keep the words, reserve the row. It should not cost a mistap to be told the catalogue is small.
- **CHAIN OF CUSTODY — upgraded from "costs" to "earns."** The rename (`— SHIPPING & RETURNS`, commit d0d4dec/ecbbb21) made shipping findable by name — persona 1's round-1 "hesitant" step is gone (journeys/01, steps 7–8). Better: the four custody steps are now a literal tracking page (commits 60410e6, a8b906a); persona 8 went from "cannot track at all" to "can track" (journeys/SUMMARY). The fiction acquired a function. That is the model for every other in-fiction label.
- **RELEASE REQUEST — harmless, still.** The buttons underneath say ADD TO BAG / CHECKOUT NOW, in plain English, now both in the sticky bar (METRICS §4). Flavour above, function below. Leave it, and keep the rule: the button itself is never in-fiction.
- **ACCESS BREACH DETECTED — half-fixed.** Gated to homepage only; it no longer ambushes me on a product page, and its 166 KB bundle is off PDPs and cart (METRICS §2). But it still fires 3 s into the homepage, full-viewport, before I've decided anything. I asked for exit or second visit; homepage-only is a compromise, not the fix. Demoted from "costs trust" to "costs trust once."
- **Evidence framing overall — earning harder than round 1.** Filing dates give the register recency (persona 2 now stays); sold-out sizes announce `SIZE M IS SOLD OUT`, disarm the form, and offer notify in-voice (METRICS §6, §10). The fiction is doing retention and honesty work, not just decoration.

**The moment my guard goes up now:** the jeans PDP description still says `9-16 days delivery uk` directly beneath custody steps saying `UK 1–2 working days` (journeys/01, "Still in the way"; BACKLOG #12). A slow page reads as slow; two contradictory delivery claims read as a lie. That is the one surviving on-page moment.

**Council answer.** Costing sales: nothing aesthetic anymore, but the aesthetic work carries stowaways — the cart brand pass brought `cellcrew.webp` (976 KB served as PNG) onto the money page, making it the slowest page on the site at 4,215 KB / 9.4 s LCP (METRICS §1.3; journeys/07 pays "13 s to open the bag"); the meta-row CLS above; the popup timing. Earning its keep: custody-as-tracking, the honest sold-out capture, filing dates, PRODUCT NN/14, and the cart finally in-language. Must not change: the plain-English buy spine, the register numbering, the board's pause guards (0 fps off-screen, re-verified, METRICS §5). Must change: three mis-named masters, the meta row, policy placeholders and the bare contact page (the sceptic still leaves on these alone — journeys/04), banner position, the 9-16-days line.

**Highest-value single change:** flip `inventoryPolicy` CONTINUE→DENY on the three tees. They were restocked to 10/variant but CONTINUE is unchanged, "so overselling re-arms at zero" (commercial-repull.json) — the mechanism that already sold **49 units that do not exist** (COMMERCIAL.md) is still armed. My test was "will it take my money and send me trousers." The storefront now says yes everywhere; the backend still says "maybe not, but it will take the money regardless." One admin toggle, zero design cost, and it makes the WITNESS STATEMENT — "when a run is gone it does not come back" — true instead of copy.

===== CONTRARIAN =====

Round 1, I claimed the register metaphor cannot express recency and that the naming is the position. Both claims lost on the evidence, and I'll say so precisely: `FILED 03.08` in the status slot (journeys/02, verified by direct fetch after the instrument's own regex went blind to it) gives the register recency without breaking format — persona 2 flipped from "would leave" to "stays." The custody rename made shipping findable by name and persona 1 now buys (SUMMARY, row 1). One status-slot line and one label each. But note what that concession implies: if "concept costs" keep dissolving into one-line fixes, the ones still standing are choices, and the pack is still laundering three of them as edges.

**1. VT323 is a recurring CLS engine, not a fix-sprint footprint.** METRICS §7 frames the 0.232–0.235 PDP shift as "new code from the fix sprint." Read §1.2's ablation instead: block `vt323.woff2` → CLS 0.001; block the mono face → no effect. Two runs, two different mechanisms (swap at t≈2s, un-wrap at t≈5.5s), same font, same ~0.23 — a 28px jump at the moment a Slow-4G shopper is reading the buy panel, on both measured PDPs. A bitmap display face with wildly mismatched fallback metrics means *every* VT323 surface is a layout hazard until explicitly reserved. That is a standing tax of the typeface constraint. Cheap to pay per-surface — reserve `.crk-meta` now — but stop booking it to the sprint.

**2. The theme/admin split is the pack's protective frame.** SUMMARY: "the theme ran out of things to fix; the admin backlog did not." Convenient jurisdiction. The cookie banner — 40% of viewport, first four tab stops, provably covering all five size buttons at scroll 0 (METRICS §8, §10) — has now been "item #1" through two full audits and twenty commits with zero action. Persona 4 still leaves. The shopper does not experience departments. And the cart brand pass (#9) is scored a win while the money page got *worse* on every vital — 4,215 KB, 9.4s LCP, INP 1,096ms (§1.3) — and Archivo Narrow, the third typeface the guardrail forbids me, still ships there (§2, fonts). It reads as one system and loads like two.

**3. The fiction's central sentence is now provably false, and nobody has priced it.** The trust architecture is prose: "When a run is gone it does not come back" (crooks-manifest.liquid, untouched by all twenty commits). The repull perjures it three ways: 49 phantom units sold under `CONTINUE` (COMMERCIAL.md); the three tees *restocked* to 10/variant this week with `CONTINUE` still set, so overselling re-arms at zero (commercial-repull.json) — primed to detonate in the next July-shaped spike (186 orders); and 467 real archived units ≈ £28,270 retail — 2.5× the last 90 days' revenue (£11,040) — including the year's #1 seller (EXPRESS TEE, 146 sold) and #3 (CONVICT JOGGERS: 105 sold, 104 sitting in stock). A brand that swapped trust furniture for a sworn statement has exactly one failure mode: the statement being untrue. It already is. COMMERCIAL.md says "relist the stock" without noticing the homepage forbids it. That's where the aesthetic is costing sales: the pledge is the wall around £28k.

**Earning its keep, protect:** the plain-English PDP spine (persona 1, 2.4s LCP), variant-honest sold-out + notify (checks-corrected.json — capture at proven demand), filing dates, the board's 0fps guards, the measured refusal list — persona 4's checklist failures are placeholders and the banner, never missing reviews. The absence holds.

**Must change:** reserve the meta row; re-upload `cellcrew.webp` (~400 KB and the cart LCP regression, §1.3); flip the three tees to `DENY`; banner position. Also flag: the sprint pushed the first product card *down*, 1.22→1.48 vh (§4) — the attract-mode-first ordering absorbed the carriage bar unquestioned.

**Highest-value single change:** reopen the archive inside the fiction — RE-FILED entries in the register for the proven sellers, and amend the witness statement one sentence toward the truth. £28k of demand-verified stock against a £11k quarter; no radius, no gradient, no badge, one honest sentence. The register is an evidence log; evidence logs don't delete closed cases — the concept supports this better than the pledge does.

===== EXECUTOR =====

THE MONDAY LIST — ranked by value ÷ effort. [A] = Shopify admin, live-on-save, no undo. [T] = theme code, PR-able.

1. **[A] Flip `inventoryPolicy: CONTINUE → DENY` on MONEY CLIVE TEE, 3 CLIVES TEE, BROADCAST TEE.** Admin → Products → each variant → untick "Continue selling when out of stock". Round-1's oversell was restocked to exactly 10/variant (commercial-repull.json: −22/−19/−8 → 100 each) but **every variant still carries CONTINUE** — the mechanism re-arms at zero. 49 phantom units sold, June at −£195.09, a fresh −£64 reversal between pulls (DELTA §3). Symptom fixed, cause armed. While there: decide CRX GARMS (985 units, archived, still CONTINUE) and V2 BAGGIES/M at −1.
2. **[A] Re-upload three masters with `.png` filenames:** `cellcrew.webp` (969 KB, ships homepage **and cart**), `v2baggies.webp`, `crooksldn-white-red-motiontec-socks.webp`. The A/B is re-proven this run (METRICS §3); the same fix took 3 CLIVES TEE LCP 13,876→2,404 ms (§1.1). This single upload closes the cart regression (4,215 KB, 9.4 s LCP on the money page — §1.3) and ~700 KB of homepage.
3. **[A] Move the cookie banner off bottom-overlay.** One consent-app setting. 338 px, z-index 2000000, covers all five size-button centres and every footer trust link at scroll 0, takes the first 4 tab stops, causes the heading-order violation (METRICS §8). Run 2 proved it — not variant logic — manufactured round-1's "frozen taps" (§10).
4. **[T] Reserve the PDP meta row against font-width variance.** `assets/crooks.css:500–501` (`.crk-record .crk-meta` / `.crk-meta-exh`); markup at `sections/crooks-exhibit-record.liquid:64–69`. Add `white-space: nowrap` to `.crk-meta-exh` plus a min-width sized to the VT323-rendered string (or a `size-adjust`ed fallback on the stack at `crooks.css:47`). Mechanism verified by ablation: block vt323 → CLS 0.001; current 0.2315 shift at t≈5.5 s (§1.2). The only theme-owned defect above polish grade.
5. **[A] Fill the legal placeholders, populate the contact page, pick one email.** `[Crooksldn LTD] [Crooksldn@gmail.com] [TW200JW]` byte-identical to round 1; 8 Gmail mentions, 0 `info@` in policy text (journeys/04). Persona 4 is the **only remaining leaver of eight**, and this is their entire checklist. ~1 hour.
6. **[A] Decide the archived catalogue.** 1,452 units untouched since round 1; excluding the CRX GARMS artefact, ~467 units ≈ £28k retail invisible, including the #1 lifetime seller CROOKS EXPRESS TEE (146 units) (COMMERCIAL.md).

ROUND-1 MONDAY STATUS: **DONE** — popup scope, variant sold-out+notify (verified, `checks-corrected.json`), cart brand pass + critical axe, tracking page, 200% zoom, contrast token, custody label, filing dates. **HALF-DONE (symptom fixed, cause armed)** — oversell (restock yes, CONTINUE no); images (5/8 masters, and one survivor spread to the cart); font double-download (fixed, but CLS 0.232 persists via the new meta-row mechanism). **OPEN** — banner, placeholders, contact, measurements table, delivery-claim contradiction (`9-16 days` vs `UK 1–2`), archived stock, return-postage line. All eight opens are admin.

COUNCIL QUESTION: The aesthetic is now measurably **earning its keep and costing nothing attributable**. Run 2: 1 of 8 personas leaves, on bracketed legal text — not on the fiction. The `crk-*` system delivers the audit's best numbers: focus ring 5.88:1, zero unnamed controls, board at 0 fps when hidden, full no-JS fallback, and after the sprint zero violations of its own rules. Personas 1, 5, 6 convert *because* of it. What was costing sales was never the aesthetic — it was where it stops: inherited cart chrome (now fixed), broken image masters, consent-app defaults, and template placeholders that read as fraud on a site that deliberately removed every fallback trust signal. **Must not change:** the WITNESS STATEMENT prose, the sticky two-action buy bar, the untouched `RELEASE REQUEST` span (DELTA #24), the board's pause guards. **Highest-value single change:** #1 — it is minutes, it protects revenue directly, and it is the only item where the store currently contradicts its own founding sentence: "when a run is gone it does not come back," while CONTINUE quietly keeps selling it. No finding here challenges the guardrail; the evidence supports it.

===== EXPANSIONIST =====

The aesthetic is now largely exonerated on conversion — and round 2 finally proves it with money attached.

**Where it earns its keep.** Run 2 journeys: 1 of 8 abandons, down from 3, and persona 4's remaining blockers are all Shopify-admin surfaces — placeholders, contact page, banner position (journeys/SUMMARY.md, outcome table). The strongest evidence is persona 2: the highest-LTV visitor was converted from "would leave" to "stays" by `FILED 03.08` dates *inside* the evidence-log fiction (02-returning-fan.md) — the register format did recency-signal work that a NEW badge does elsewhere, at zero cost to the system. The sold-out state is now the honest version of the fiction: `SIZE M IS SOLD OUT` via live region, disarmed form, notify capture (METRICS §6, §10 corrected instrument). Protect: register format, filing dates, WITNESS STATEMENT prose, board pause guards (0 fps off-screen re-verified, §5), and the popup's homepage-only gating, which took 166 KB off every PDP (§2).

**Where it still costs.** Two places, one of them genuinely the aesthetic. (1) The PDP's 0.232 CLS is now *caused by the display face*: VT323's wider fallback wraps the `PRODUCT NN / 14` meta row, then un-wraps 28 px at ~5.5 s when the loaded font lands (METRICS §1.2, ablation-verified). The constraint is defensible; the implementation is not — reserve the row's width. Hours of theme work, top of the list. (2) The cart: 4,215 KB, 9.4 s LCP on the money page (§1.3) — but that is one mis-named master (`cellcrew.webp`, 976 KB) plus two homepage siblings. Three admin re-uploads, ~1.4 MB back. Neither justifies touching the design language.

**The unpriced upside — priced honestly this time.** (I proposed the leaderboard cheaply in round 1 and was rightly corrected; nothing below is a "flick a switch" claim.)

1. **The archive: ~£28,270 at retail, still invisible.** Unchanged between pulls — 1,452 units, 467 real excluding the CRX GARMS artefact (COMMERCIAL.md; commercial-repull.json `archivedInventory.unchanged: true`). The all-time #1 seller, CROOKS EXPRESS TEE at 146 units, is archived with 33 in stock. The fiction has a native home for this — closed cases with real sales history are *provenance*, not clearance — and the fix sprint accidentally cut the build cost: the collection-page register now exists (commit 1892419), so a CASE CLOSED collection renders itself. Honest price: product-by-product hand-count first (the repull proves counts lie — CRXST★RZ 970→98), photography check, republish, one collection. Days of admin work, not hours. Largest single pool of unpriced revenue on the books.

2. **The notify capture leaks its asset.** `crooks-exhibit-record.liquid:370-395` posts restock intent through `form 'contact'` — each capture arrives as an inbox email subject "Restock request", unstructured, no marketing consent, no per-variant list. At drop cadence this is the owned-audience machine, and it currently produces mail, not a list. Price: Flow rule or back-in-stock app to tag and route; admin work, no theme change, no new UI.

3. **The oversell trap has re-armed.** All three tees restocked to 10/variant but every variant still carries `inventoryPolicy: CONTINUE` — "overselling re-arms at zero" (commercial-repull.json, `oversellRepair.note`). Last cycle that meant 49 phantom units and June at −£195.09 (COMMERCIAL.md).

**Highest-value single change: flip CONTINUE→DENY on those variants.** Minutes in admin. The reasoning is the aesthetic's own: the entire system — filing dates, notify forms, "when a run is gone it does not come back" — is a scarcity fiction that is commercially valuable only while it is *true*. CONTINUE makes the store's backend contradict its homepage under load, precisely at sell-out, precisely when the drop is working. DENY is what makes the notify capture fire instead of a phantom sale, which is what feeds the register, which is what the next drop is sold to. Second place: the cookie banner position (admin) — §8 now proves it covers all five size-button centres at scroll 0 and manufactured run 1's worst finding.

The aesthetic is not costing sales anymore. Untrue scarcity, an unmerchandised archive, and intent-mail rotting in an inbox are.

===== FIRSTPRINCIPLES =====

Rebuilt premise. Round 1 I argued conversion was capped by fixed supply. The commercial data falsified that in both directions at once: the store sells stock it doesn't have (49 oversold units, `inventoryPolicy: CONTINUE`; COMMERCIAL.md) and hides stock it does have (1,452 archived units, ~467 real ≈ £28,270 retail ≈ 2.5× the last 90 days' revenue; COMMERCIAL.md). Supply isn't fixed — it's misfiled. The binding constraint is merchandising: what gets put in front of paid IG/TikTok traffic, and whether what's said about it is true. Three things follow.

**1. The aesthetic is the merchandising engine, and it now demonstrably works.** Run 2: 1 of 8 personas leaves, down from 3, and that one (the sceptic) leaves entirely on admin plumbing — placeholders, contact page, banner position — not on the look (SUMMARY, journey 04 row). The cold Instagram click converts in ~3 taps at LCP 3.0 s (journeys/01; METRICS §1.1: 13,876→2,404 ms). The register's `FILED 03.08` dates turned the highest-LTV persona from "would leave" to "stays" *in-format* (journeys/02). The honest sold-out state (`SIZE L IS SOLD OUT`, disarmed form, notify capture) is scarcity fiction executed truthfully (checks-corrected.json via journeys/02). Earning its keep, by element: the register format, the FILED status slot, the sticky two-action buy bar (METRICS §4), the WITNESS-STATEMENT prose-as-trust, the board (persona 5 returns *because* of it, and "the commercial data still says the homepage is not where money is lost" — journeys/05). Protect all of it. DELTA #24 shows the discipline holding: nobody "fixed" RELEASE REQUEST.

**2. Where the aesthetic costs sales — two places, both specific.** (a) The PDP meta row sets `PRODUCT NN / 14` in VT323 inside a wrapping flex row; the wider fallback wraps it, deferred JS un-wraps it at ~5.5 s, CLS 0.2315 on every mobile PDP — the surface where *all* social traffic lands — and it "can move the size row mid-tap" (METRICS §1.2; journeys/01). Ablation is conclusive: block vt323 → 0.001. That is display type doing layout-critical work, a genuine aesthetic-owned defect. Fix inside the language: nowrap + width reservation. Minutes. (b) The board's first-viewport claim has quietly deepened: first product card now 1.48 vh, was 1.22 (METRICS §4) — the carriage bar accreted *above* the register. The board earned its viewport; new furniture hasn't. Stop stacking.

**3. The fiction's biggest cost is not visual — it's that the back office contradicts it.** "When a run is gone it does not come back" sits over a catalogue where three tees were quietly restocked to 10/variant and *still* carry `CONTINUE`, so overselling re-arms at zero (commercial-repull.json), while the June −£195.09 month and the fresh −£63.99 reversal trace the oversell→refund loop (DELTA §3). A brand that replaced all trust furniture with prose has one obligation: the prose must be true. Meanwhile the archive — including the #1 lifetime seller, CROOKS EXPRESS TEE, 146 units, 33 in stock — is invisible (COMMERCIAL.md). Note the irony: an *evidence terminal* is the one retail fiction that natively supports an archive, and DELTA #26 records retired runs being deleted instead.

**Must not change:** register format, board with its pause guards, prose trust blocks, the sold-out/notify pattern, zero-radius/no-urgency guardrail — the measured absence of urgency mechanics is now load-bearing, since honesty is the differentiator.

**Must change:** meta-row font reservation (theme, minutes — the last theme defect above polish, DELTA §5); flip `CONTINUE`→`DENY` (integrity prerequisite); the three remaining `.webp`-named masters, one of which alone is 976 KB on a 9.4 s-LCP cart (METRICS §1.3).

**Highest-value single change:** re-file the archived proven sellers into the register. It requires *zero* theme work — the register, filing dates, and sold-out semantics already handle it, as run 2 verified — which is precisely the point: the theme has out-built its catalogue. £28k of demonstrated demand versus £11k of trailing-90-day revenue, reachable by an admin unarchive. The aesthetic isn't the constraint; it's the shelf. Stock it.

===== REVIEWER: BRAND =====

**BRAND REVIEW — ROUND 2**

Nobody breaches the guardrail, and all five protect the load-bearing set: buy spine, register format, pause guards, the untouched RELEASE REQUEST span (DELTA #24). The brand risk hides in three places.

**1. The archive recommendations are where damage lives.** E's headline — re-file proven sellers into the register, "zero theme work" — would quietly break two evidenced assets. First, `PRODUCT NN / 14` is the element A correctly identifies as the only proof of a finite catalogue (AUDIT-CONTEXT §1: 14 products); re-filing ~8 archived sellers makes it /22 and dilutes the smallness signal on every PDP. Second, it falsifies the WITNESS STATEMENT *in public* while leaving the sentence up — runs visibly coming back under "when a run is gone it does not come back" is worse than the current backend-only contradiction, which no journey shows a shopper detecting (COMMERCIAL.md; commercial-repull.json — both admin-side evidence). B is more honest: amend the sentence. But B's "one honest sentence" spends the scarcity position for every future drop to recover £28k once, when DENY (A/C/D convergence) makes the oversell half of the perjury true for the cost of three checkboxes. D's CASE CLOSED collection is the only archive route that survives brand review: separate register (the collection-page register from commit 1892419), provenance framing, and honestly priced — the hand-count caveat matters because commercial-repull.json proves counts lie (CRXST★RZ 970→98). C's "decide the archived catalogue" delegates with no in-fiction guardrail attached — a plain unarchive would land as E's version.

**2. A's popup escalation exceeds its evidence.** A demands exit-intent or second-visit gating; but journeys/05 line 9 records the homepage firing as "correctly, since this is" the browsing surface, and no run-2 persona leaves over it (SUMMARY outcome table). Homepage-only is measured as sufficient; "costs trust once" is preference, not a finding.

**3. Two genuinely brand-protective moves deserve adoption.** E and B both catch the carriage bar accreting above the register (first card 1.22→1.48 vh, METRICS §4) — the board earned its viewport (journeys/05); new furniture didn't. "Stop stacking" is brand defense. And B's reframe of the meta-row CLS as a standing tax of VT323 rather than a sprint footprint (ablation, METRICS §1.2) *defends* the typeface constraint by pricing it per-surface — the opposite of challenging it. Everyone's nowrap fix is in-language.

Finally: the DENY flip is brand work, not ops. D states it best — the system is "commercially valuable only while it is true" — and it is the only recommendation that makes the founding sentence true instead of editing it.

**Verdicts:**
- **A:** Brand-safe and observant, but the popup demand overruns journeys/05, which calls the homepage firing correct.
- **B:** Sharpest argument on the table; adopt the diagnosis, hold the sentence-amendment until DENY plus a CASE CLOSED trial fail.
- **C:** Maximally protective Monday list; its one hole is delegating the archive decision with no in-fiction constraint.
- **D:** Brand-safest response — the only archive plan that preserves /14, and DENY argued from the aesthetic's own logic.
- **E:** Right protections, wrong headline: "zero theme work" re-filing would dilute PRODUCT NN / 14 and publicly falsify an unamended pledge.

===== REVIEWER: FEASIBILITY =====

FEASIBILITY REVIEW — claims checked against `git show origin/claude/crooksldn-theme-init-bnen7a` source.

**1. Meta-row CLS: mispriced by C and E.** `crooks.css` (~500): `.crk-meta` is `display:flex; flex-wrap:wrap` — the 28 px jump is the *flex row* wrapping, not text wrap. C's `white-space:nowrap` on `.crk-meta-exh` is therefore a no-op, and C's "min-width sized to the VT323-rendered string" points the wrong way: min-width is a floor, so the wider fallback still wraps the row. The working fixes are reserving the *fallback's* width (cost: a permanent second line) or C's parenthetical — a `size-adjust` fallback in the display stack (`crooks.css:47`), which also retires B's correctly-diagnosed "standing tax": `.crk-title`, `.crk-price`, `.crk-h` all share `crk-display`. E's "minutes… nowrap + width reservation" is the worst pricing — read as `flex-wrap:nowrap` it regresses the just-fixed 200% zoom reflow (dadd842; METRICS §4). D's "hours" is the honest price.

**2. Archive re-file: E's "zero theme work" is narrowly true, materially misleading.** Verified: `crk_total = crk_col.products_count` (the "/14" renumbers itself) and the register stamps `FILED [date]` from `product.published_at` (exhibit-log.liquid:246–260), so a republish self-labels in-format. Hidden dependencies E omits: the PDP reads `product.metafields.crooks` (measurements, case_ref) — archived products carry none, so they'd render half-empty records; counts are proven liars (CRXST★RZ 970→98) and CRX GARMS sits archived with CONTINUE+985; and republishing contradicts the pledge unless the statement is amended first. D's "days of admin, hand-count first" is the correct price. B's distinct "RE-FILED" state needs new theme logic — the status slot knows only sold-out/filed/available; relabeling `filed_label` would mislabel genuinely new drops. B's "amend the statement one sentence" is verified cheap: the prose is a richtext section setting (crooks-manifest.liquid schema), an editor edit, no PR.

**3. Notify routing: D's "no theme change, no new UI" is mispriced.** The capture is a native `form 'contact'` (exhibit-record.liquid ~368–395), deliberately server-correct before JS (panel `hidden` unless the server-selected variant is unavailable). Shopify Flow has no contact-form trigger, so "Flow rule" doesn't exist; a back-in-stock app means a JS widget replacing the one sold-out surface that currently works no-JS. Real price: theme integration, consent copy, and a no-JS/a11y re-verify.

**4. Correctly priced everywhere:** CONTINUE→DENY (pure admin; theme reads only `variant.available`, no interaction) — all five right. The three `.webp` re-uploads (precedent: five fixed the same way this run, METRICS §3). Banner reposition (admin). One note on A: the popup's 3 s timer and once-per-browser localStorage gate are *theme-owned* (crack-the-cuffs.liquid), so A's "exit or second visit" ask is a cheap snippet edit, not a Base44 dependency — A underclaims feasibility rather than overclaims.

**Verdicts:**
- **A** — sound judgment, no mispricing; misses that its own popup ask is a trivial theme edit.
- **B** — best mechanism diagnosis (font-stack tax); RE-FILED state underpriced, statement amendment correctly cheap.
- **C** — best citations and [A]/[T] discipline, but its one theme fix names the wrong CSS lever.
- **D** — most honestly priced overall; the Flow/no-theme-change notify claim is its one real mispricing.
- **E** — right strategy, worst pricing: "minutes" risks a WCAG regression and "zero theme work" hides days of admin.

===== REVIEWER: ACCURACY =====

All checkable claims were verified against the pack and `git show origin/claude/crooksldn-theme-init-bnen7a`. The shared numbers are sound: cart 4,215 KB / 9,444 ms / INP 1,096 (METRICS §1.3), CLS shift 0.2315 at ~5.5 s with ablation vt323→0.001 (§1.2), restock to 10/variant with CONTINUE unchanged and CRXST★RZ 970→98 (commercial-repull.json), 49 oversold units, June −£195.09, archived 1,452/467 ≈ £28,270 vs £11,039.69 90-day (COMMERCIAL.md/repull), 1-of-8 leaver (SUMMARY), banner 338 px/z-2000000/4 tab stops covering all five size centres (§8). Commits d0d4dec (custody rename), 60410e6/a8b906a (tracking), 1892419 (collection register) all real; `sections/crooks-manifest.liquid` is indeed untouched by the twenty commits and carries the quoted sentence.

Errors and miscites:

**A.** (1) "The cart brand pass brought `cellcrew.webp` onto the money page" — contradicts the pack: DELTA #9 says cart weight "regressed for an unrelated reason (R2)"; the master reached the cart via the crewneck recommendation image, not the brand pass. (2) Popup "still fires 3 s into the homepage, full-viewport" — no run-2 measurement exists; the 3 s / 100%-viewport figures are run-1 PDP data (journeys/01); run 2 only records that it fires on the homepage (journeys/05).

**B.** (1) "Persona 1, 2.4 s LCP" — journey 01 measured 3,024 ms; 2,404 ms is METRICS §1.1's separate instrument run. (2) Quotes COMMERCIAL.md as saying "relist the stock" — not in the file; actual wording is "putting five figures of proven-selling stock back in front of traffic". (3) "Worse on every vital" is numerically true but omits DELTA's caution that cart INP is wallet-iframe sampling, "re-sample before treating as trend".

**C.** Near-flawless: every line reference checks out exactly (crooks.css:47 fallback stack, :500–501 meta rules; exhibit-record.liquid:64–69 markup, notify form at ~374–397). One slip: "All eight opens are admin" — DELTA scores 9 OPEN, 8 admin-only (#25 game-traffic and #26 retired-runs are open and not admin). "Personas 1, 5, 6 convert" stretches persona 5, whose outcome is "returns, follows", not conversion.

**D.** (1) "~1.4 MB back" from three re-uploads — evidence supports ~400 KB (cart, §1.3) + ~700 KB (homepage, §1.3) ≈ 1.1 MB. (2) "Hours of theme work" for the meta-row reserve — DELTA §5 prices it "Theme, minutes". (3) Attributes persona 2's flip to filing dates alone; journeys/02 credits both dates and the honest sold-out state. Subject "Restock request" and `form 'contact'` verified (exhibit-record.liquid:673, :375).

**E.** No factual errors found. "SIZE L IS SOLD OUT" matches checks-corrected.json and journeys/02; the journeys/05 quote is verbatim; DELTA #24/#26 and §3/§5 citations exact. Only stretch: "every mobile PDP" generalises from the two measured (same template — defensible).

Verdicts:
- A: Accurate on numbers; one causal claim contradicts DELTA #9 and one popup detail is uninstrumented carry-over.
- B: Strong, with one LCP misattribution and one invented quotation.
- C: The most precise response; only the opens-count slips.
- D: Sound core; inflates one savings figure and one effort estimate.
- E: Fully accurate; every checked claim survives verification.

===== REVIEWER: PROTECTION =====

**PROTECTION REVIEW — round 2**

The convergent slate (DENY flip, meta-row reservation, image re-uploads, banner move, placeholders) touches nothing in KEEP.md. The meta-row fix is itself protective of §2's first viewport, and KEEP protects the words `PRODUCT NN / 14`, not the wrap behaviour. Discipline elsewhere held: no one touches the board (§1), the plain-English buy spine (§2), the measurement apparatus (§3), the fake-data refusal (§8), or radius enforcement (§9); DELTA.md:54 confirms RELEASE REQUEST survived untouched.

Three findings:

**1. B's highest-value change violates §6 (The writing).** "Amend the witness statement one sentence toward the truth" edits the prose block KEEP §6 names as the brand's substitute for all trust furniture — persona 5's "best writing on the site" — and which round 1's verdict listed as must-not-change (COUNCIL.md:148). B's premise is real: the statement is falsified by the restock-under-CONTINUE (commercial-repull.json), and AUDIT-CONTEXT.md:71's "we do not restock it to order" was already broken by the merchant. But the protection ordering matters: make the backend true first (DENY, C#1) and the prose may need no edit at all. Prose surgery on §6 is a last resort, not a headline recommendation.

**2. The archive re-filing (B, D, E) is §7-compliant — E's version is cleanest.** §7 explicitly permits additions to the register format ("an addition, not a replacement"); RE-FILED/CASE CLOSED entries are format-native, and since the 467 real units never sold out (COMMERCIAL.md), re-filing does not falsify "when a run is gone it does not come back" — those runs were never gone, only hidden (DELTA.md:22, :56). E requires zero theme work and leaves §6 untouched; D adds the honest hand-count precondition; only B couples it to the §6 prose edit. D's notify routing also explicitly honours §10's "do not design anything new here."

**3. Blind spot: §5, the no-JS fallback.** KEEP calls it "easy to break by accident during any of the backlog work." Twenty commits landed; only C names it (re-verified at journeys/SUMMARY.md:76 — 18 links / 40 images held). A, B, D, and E propose further theme CSS work without once checking the section KEEP flags as most fragile. Any accepted meta-row change should carry a no-JS regression check.

Minor: B's and E's carriage-bar critiques (first card 1.22→1.48 vh, METRICS via DELTA.md:145) target new furniture, not the §1 board — E explicitly re-affirms "the board earned its viewport," so neither slides toward demoting board-first ordering, which §1 and persona 5 protect. A's demand for popup exit-intent targets the one element §9 names as the site's own rule-violator; nothing protected there. C's "fill the measurements table" respects §3's "replace the data, do not touch the component."

**Verdicts:**
- **A:** Fully KEEP-compliant; protects the buy-spine rule by name; misses §5.
- **B:** Sharpest evidence, but its headline recommendation is the round's only §6 violation — resequence behind DENY.
- **C:** Zero violations; the only response that re-checks §5; the model protection posture.
- **D:** Compliant, and uniquely prices §10-respecting work honestly; misses §5.
- **E:** Compliant; achieves the archive goal without touching §6 prose; misses §5.

===== REVIEWER: COMMERCIAL =====

COMMERCIAL REVIEW — ROUND 2

The pack prices three pools: (1) oversell integrity — 49 phantom units, June −£195.09 (COMMERCIAL.md), a fresh −£63.99 reversal (DELTA §3), restock to 10/variant with CONTINUE intact so it re-arms at zero (commercial-repull.json); (2) the archive — 1,452 units unchanged, ~467 real ≈ £28,270 vs £11,039.69 trailing 90 days (repull `trading90d.total`), including the #1 seller EXPRESS TEE (146 sold, 33 held) and #3 CONVICT JOGGERS (105 sold, 104 held); (3) demand capture at sell-out. Pool 2 is ~2.5× a quarter's revenue; pool 1 is hundreds of pounds plus trust. That asymmetry decides the ranking.

**D — 1st.** Only advisor covering all three pools with honest prices. Archive costed correctly: hand-count first because the repull proves counts lie (CRXST★RZ 970→98; CRX GARMS 985 untouched), days not hours, build cost cut by commit 1892419 (verified: "Render the catalogue register on collection pages"). Found new money nobody else saw: the notify capture posts via `form 'contact'` (verified, crooks-exhibit-record.liquid ~370–395) — restock intent arriving as unstructured email, no consent, no list. Its DENY-first pick is the smaller pound figure, but the reasoning (DENY makes notify fire instead of a phantom sale, feeding the next drop) is a revenue system, not a checkbox.

**B — 2nd.** Deepest on the two biggest items. Priced the re-arm against the July shape (186 orders), and spotted the one thing COMMERCIAL.md itself missed: the pledge is the wall around the £28k — "relist the stock" contradicts the untouched manifest (verified: zero commits touched crooks-manifest.liquid across 1b6bc4c..db96aa3). Its RE-FILED single change targets the largest pool and clears the blocker. Loses to D only on the uncounted third pool.

**E — 3rd.** Right reframe ("supply misfiled") and right single change, but underpriced: "reachable by an admin unarchive" ignores that counts provably lie — unarchiving CRX GARMS at a phantom 985 under CONTINUE would recreate the oversell at 20× scale. Correct target, thin execution.

**C — 4th.** Nothing wrong, everything ranked by effort instead of magnitude: the £28k archive sits at #6, below an hour of placeholders, and its own "highest-value single change" is the minutes-cheap DENY flip. Most implementable list; captures the least upside. Best inventory hygiene (CRX GARMS, V2 BAGGIES/M −1).

**A — 5th, and the answer to "still ignoring the inventory."** Its DENY pick is sound, but the archive — the largest number in the pack — appears nowhere in A's response. Paragraphs on popup timing, meta-row CLS and vocabulary; zero words on £28,270 of demand-proven stock. Chasing pennies while £28k sits filed under "archived."

VERDICTS:
- A: Sound on the trap, blind to the vault — the only advisor with no line item for the £28k.
- B: Found the wall around the money; the one commercially complete diagnosis of pool 2.
- C: A perfect Monday list that ranks the quarter's biggest number sixth of six.
- D: Best commercial counsel — three pools, honest prices, and the only new asset discovered.
- E: Right vault, no locksmith — relisting unverified counts under CONTINUE is the oversell reborn.