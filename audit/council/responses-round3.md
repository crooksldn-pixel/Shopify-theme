# COUNCIL ROUND 3 — RAW RESPONSES AND PEER REVIEWS

Advisors A-E in workflow order (Outsider, Contrarian, Executor, Expansionist, First Principles).
Reviewer slots are labelled by their content below, as workflow labels shuffle by completion.


===== ADVISOR: OUTSIDER =====

**THE OUTSIDER — ROUND 3**

Round 2 I said the shop reads as real everywhere I can see. Round 3 the paperwork caught up — and the page started jumping under my thumb.

**Vocabulary, third pass:**

- **PRODUCT 04 / 14 — helps, hold.** Round 2's wobble (the VT323 meta-row jump) is gone — METRICS §1.1 confirms the 0.2315 shift "no longer occurs." The words stay; the disease moved (below).
- **CHAIN OF CUSTODY — earning outright.** It's a tracking page with a boot line (`> CHAIN OF CUSTODY DATABASE ONLINE`, crooks-tracking.liquid:195), a TERMS section, and a FAQ answer. Persona 8 "can track AND self-serve answers" (SUMMARY row 8). The label that once hid shipping now delivers it three ways.
- **RELEASE REQUEST — harmless, still, respected.** Flavour above, ADD TO BAG below, panels collapsed cleanly (97e1e01). Never fiction-ify the button.
- **ACCESS BREACH DETECTED — now redundant, finish the move.** The game got what I asked for: an opt-in menu entry with an honest pitch ("PLAY CASE:001 NOW…", newtabs.json menu). That IS the invitation mechanic. The uninvited homepage popup therefore no longer justifies itself — retire it. Also: the manifest replaced CASE 001 on the homepage but "CASE 001 text also still present (both render)" (METRICS §3) — a seam showing.
- **Evidence framing — carried the trust work it promised.** QUERY THE REGISTER works end-to-end first time in three runs (typeahead, prices, pages, no-JS — METRICS §3). TERMS: nine sections, 654 words, zero placeholders, states return window AND postage (newtabs.json). The sceptic stopped leaving *because* the paperwork got real, in-voice (journeys/04). The fiction survived being made functional — that was the open question, and it's answered.

**The moment my guard goes up:** I read the shipping policy — the brand's best legal surface — and the contact address is **`crooksldn@gmail.com.com`** (newtabs.json line 179). A stranger emails a shipping question from a legal page and gets a bounce. Nothing on this site reads as fake anymore except its own email address. Second flinch: at ~1.9 s the header grows a line and everything drops 48 px — if my thumb is over a size, I tap the wrong thing (journeys/01, journey CLS 0.59).

**Council answer.** Costing sales now: one typographic mechanic and old admin debt. The CRX Mono header swap puts CLS 0.325–0.39 on **every** mobile page (METRICS §1.1, ablation: block crx-mono → CLS 0) and pushes the V2 BAGGIES size row to y=844 — the fold — on the exact surface where the sold-out honesty lives (§1.2). The cart still hauls `cellcrew.webp`, 976 KB, third audit (§2). The banner blocks the footer, third audit. Earning its keep: the plain-English buy spine (first viewport answers everything at 1.5 s, journeys/01), custody-as-tracking, honest sold-out + notify, search, TERMS/FAQ — and the whole system beats six live competitors 39/50 at 4–8× lighter (compare/REPORT.md §1). Zero of eight personas now leave (SUMMARY). Must not change: the buy spine, RELEASE REQUEST as a span, the refusal list, the register numbering.

**Highest-value single change: reserve the header height and ship the `size-adjust` fallback for both fonts.** One fix family closes two of the three worst moments (SUMMARY) — the site-wide jump *and* the fold regression — for all eight personas, and ends the pattern that has now produced the top theme defect in two consecutive audits (VT323 run 2, CRX Mono run 3). Until fallback metrics match, every new mono surface ships a mistap.

**Standing escalation, not demotion:** the DENY flip was my highest-value change in round 2. Three pulls, three audits, still `CONTINUE` on all three tees — and they're now depleting on live trade, variants at 8–9 units (commercial-run3.json). The storefront finally tells the truth everywhere; the backend is counting down to the same lie that sold 49 phantom shirts. Minutes. Do it before the header, if only one thing happens Monday.

===== ADVISOR: CONTRARIAN =====

Round-1 self-audit first, because the fresh evidence cuts both ways. My claim that the register metaphor cannot express recency is **falsified**: `FILED 03.08` flipped persona 2 to "stays" (DELTA #14), and compare/REPORT.md §6 records it as the field's only card-level recency signal. My claim that the naming is the position survives only in its weak form: every naming fix that worked was bilingual retreat — `CHAIN OF CUSTODY — SHIPPING & RETURNS`, plain `QUESTIONS`, plain `TRACK ORDER`, plain `SEARCH` in the header (newtabs.json). The fiction converts exactly where it is subtitled in plain English. Keep that rule; it is the load-bearing concession.

Now what the pack is still protecting.

**1. The typeface tax is a concept cost being filed as an implementation edge — for the second consecutive audit.** Run 2's top theme defect was VT323 fallback metrics (CLS 0.2315); round 2's council prescribed `size-adjust` fallbacks (COUNCIL.md §3). Thirteen commits later, `size-adjust` appears **zero times** in served-crooks.css (grepped), and run 3's headline is the same mechanism in the other face: CRX Mono wraps the new header row, 48 px drop at 1.9 s, CLS 0.325–0.391 on every mobile page, 0.59 on the cold-click journey, ablation-proven (METRICS §1.1). The system enforces `border-radius:0` in code (crooks.css:101) but leaves its font physics to discipline. A defect class that tops two audits running is not an "edge"; it is what the two-typeface constraint structurally costs until the fallback stacks are fixed *in the token layer, enforced like the radius is*. SUMMARY.md finally says this; DELTA and the context file spent two rounds saying "theme, minutes."

**2. The fiction's furniture keeps accreting, against a standing ruling.** Round 2: "stop stacking" (COUNCIL.md, blind spots). Run 3: the header grew a control row and the size buttons fell to y=844 — off-tappable — on V2 BAGGIES, the top active seller, 127 units/365d (METRICS §1.2, COMMERCIAL.md). And a17d4b3 claims the manifest "replaces CASE 001", yet newtabs.json records both rendering. Every in-fiction artefact demands a viewport; the pack logs each addition as a feature and each displacement as a separate bug.

**3. Costs booked next round, benefits booked this round.** The game's menu move is scored as persona-5 upside; INP doubled to 1,032–1,208 ms with the menu-hosted game assets named as suspect and "not isolated this run" (METRICS §1.3).

**4. The competitive verdict is stale.** 39/50 was scored against db96aa3. REPORT.md mocks Corteiz's CLS 0.3522 as "worse than crooks ever measured" — run-3 crooks cart is 0.3906. The weight moat (2.7 MB vs 11.7–22 MB) is real; the stability lead died in commit 9025814.

**5. "Admin, minutes," third audit.** DENY still armed with tee variants at 8–9 units under live trade of 22 orders/9 days (commercial-run3.json); the email mess *grew a typo* — `crooksldn@gmail.com.com` on a legal page (newtabs.json). When "minutes" survives three audits, "minutes" means "unowned."

**Where the aesthetic earns:** the weight moat, first-viewport answers (5/5, compare row 1), and the honesty apparatus nobody in the field has — variant-level sold-out + notify, FILED dates, zero urgency (Ultralight, 14/50, is the measured control for urgency theatre). Corteiz at 30/50 proves the territory converts at scale. **Where it costs:** the site-wide jump under every thumb; the size row at the fold on the product that needs it; and insularity to acquisition — one-word title, no meta description, `faqSchema: false` (compare row 9: 1/5 against a field that all ship meta descriptions). The register speaks only to people already inside the room. Note also: all trading data is from the live site scored 14/50 — this theme's conversion is still inference, not receipts.

**Must not change:** bilingual naming, plain-English buy spine, the board, notify pattern, FILED slot, the urgency refusal, sub-3 MB weight.

**Highest-value single change:** one commit — fixed header height plus `size-adjust`ed fallbacks on *both* font stacks, enforced in tokens. It retires the only defect class to top two audits, restores the size row above the fold, and makes REPORT.md's "ship it" true again. And a process ruling: no fourteenth theme commit until the three-audit-old checkbox flips to DENY.

===== ADVISOR: EXPANSIONIST =====

**Verdict on the new work: it held, and it's the moat now.** Search works end-to-end on first measurement — field, typeahead with prices, page results, no-JS (METRICS §3; newtabs.json search.noJs 4 results). FAQ: 14 in-voice Q&As covering delivery/sizing/returns/tracking. TERMS: 654 words, zero placeholders, states return window AND postage liability — backlog #8 closed by copy. Result: 0/8 personas abandon (SUMMARY, from 3/8 in run 1), the sceptic converted from leaver to hesitater, and the trust surface now exceeds Mertra and Phase — the only dimension the field beat us on (compare/REPORT §2 row 6). Against a field scoring 14–30, this theme sits at 39/50.

**What it cost: one font mechanic, twice warned, never fixed.** CLS 0.325–0.391 on every mobile page, journey stacking 0.59 (METRICS §1.1) — the CRX Mono swap wraps the new header row, MAIN drops 48px at t≈1.9s, ablation-proven. Round 2 prescribed `size-adjust` fallbacks; no `size-adjust` exists in deployed CSS (DELTA-3WAY §2.8). Worse: the 48px growth pushed V2 BAGGIES' size row to exactly y=844 — the fold — on the #2 lifetime seller (127 units, COMMERCIAL.md), degrading the protected first-viewport answer. INP doubled to ~1,050ms (METRICS §1.3). This is the only place the aesthetic is currently costing sales, and it isn't the terminal fiction — it's the implementation of the type. The fiction itself is measured upside: 5/5 first-viewport answers, 5/5 mobile speed, persona 5 returns *because* of it, and Corteiz proves the austere territory converts at 10× scale with worse plumbing (REPORT §3).

**The unpriced upside, priced honestly this time:**

1. **The archive: ~£28,270 at retail, invisible for three consecutive pulls** (commercial-run3.json: 1,452 units unchanged; ~467 real excluding the CRX GARMS artefact). It contains the #1 lifetime seller — CROOKS EXPRESS TEE, 146 units (COMMERCIAL.md). Honest price: **days**, not minutes — hand-count first (counts lie: CRXST★RZ 970→98), archived products carry no `crooks.*` metafields, and the council-ruled closed-case register keeps the WITNESS STATEMENT true. Still the largest number in the pack by an order of magnitude against £937.75/9 days of trade.

2. **The DENY flip arms the audience machine.** Variants at 8–9 units, 22 orders in 9 days (commercial-run3.json denyFlip). The next sell-out either fires the variant-notify capture the theme already built — the field's only demand-capture mechanic (REPORT moat list) — or sells phantom stock a third time. Minutes. Third audit. Do it this week.

3. **SMS intake: built, unverified, therefore unpriced.** Commit d0363ee hosts the app block that can record real SMS consent (Shopify Forms + Omnisend confirmed enabled), but the commit says plainly: "Not verified: the rendered result on staging." Run-4 must verify a subscriber lands with consent before anyone books this as the owned-audience win. The fallback contact form saves the number but creates no consent record.

4. **Cheap and claimed by nobody:** FAQPage JSON-LD absent (newtabs.json faqSchema: false) — free rich result, hours. Homepage title still one word, no meta description (REPORT row 9, our only 1/5). Gift cards — Mertra is alone in the field; Shopify-native, before Q4 (steal list #2).

**Must not change:** the board and its 0-fps guards, FILED dates (only card-level recency signal measured anywhere), sold-out honesty + notify, prose-as-trust, sub-3MB pages, and the leaderboard stays hidden until real scores exist — that ruling was right.

**Must change, in order:** (1) **[T] Reserve the header height + `size-adjust` both font stacks** — ends a defect class that has now produced the top theme finding in two consecutive audits and restores V2 BAGGIES' size row. Hours. (2) **[A] CONTINUE→DENY.** Minutes. (3) **[A] The email find-and-replace** — `crooksldn@gmail.com.com` is a dead address on a legal page, the last flaw on the brand's best trust surface (SUMMARY worst-moment 3). Minutes.

**Highest-value single change:** within the aesthetic, the size-adjust fix — it protects every mobile session of a business trading ~£200/day. On the full ledger, the closed-case register: five figures of proven-selling stock in front of traffic already paid for, gated only behind a hand-count and three checkboxes.

===== ADVISOR: EXECUTOR =====

THE MONDAY LIST — ROUND 3. Ranked by value ÷ effort. [A] = Shopify admin, live-on-save, no undo. [T] = theme code, PR-able. All verified against `d0363ee` source and run-3 evidence.

1. **[A] Flip `inventoryPolicy` CONTINUE→DENY — three tees.** Admin → Products → each variant → untick "Continue selling when out of stock." Third audit. Now urgent, not chronic: `commercial-run3.json` — `denyFlip.done: false`, 22 orders in 9 days, MONEY CLIVE at 9 units in three sizes, 3 CLIVES S/BLACK at 8. Days from firing. The next sell-out either triggers the notify capture the theme built or sells phantom stock — one checkbox decides which. Decide CRX GARMS (985, archived, CONTINUE) while there.
2. **[T] Kill the site-wide header CLS.** CLS 0.325–0.391 on **every** mobile page, journey-stacked 0.59 (METRICS §1.1); ablation: block `crx-mono.woff2` → 0. Mechanism verified in source: `assets/crx-mono.css:7,14` declare `font-display: swap` with **no `size-adjust` anywhere in the deployed CSS** (grep confirms — the round-2 council prescription was never implemented); `crooks.css:431–434` lets `.crk-header__bar`/`__actions` wrap at ≤429px, so the wider loaded face adds a line at t≈1.9s. Edits: add `size-adjust`ed local-fallback `@font-face`s into `crx-mono.css` and the stacks at `crooks.css:47–48`; reserve the bar's wrapped height at `crooks.css:397`. This same fix returns V2 BAGGIES' size row from y=844 to the viewport (§1.2) — the #2 seller's first-viewport answer.
3. **[A] Email find-and-replace.** `crooksldn@gmail.com.com` — undeliverable, on the shipping policy (newtabs.json). Unify on one address across terms/refund/privacy/footer. Note: the theme's footer default is already `info@crooksldn.com` (`sections/crooks-footer-log.liquid:123`); the live `gmail` footer link is a customizer override. Minutes; completes the sceptic.
4. **[A] Three image masters, third audit.** `cellcrew.webp` (976 KB) still rides the cart — the money page's 10.3s LCP (METRICS §2). Same re-upload that took 3 CLIVES 13,876→2,404ms.
5. **[T] FAQPage JSON-LD.** `sections/crooks-faq.liquid` has no `ld+json` block (only `{% schema %}` at :64); `newtabs.json faqSchema: false`. ~20 lines, free rich result.
6. **[T] Isolate the INP doubling** (~600→~1,050ms, §1.3). Named suspect, structurally confirmed: `sections/crooks-header.liquid:4` now loads `crooks-board.js` site-wide for the drawer canvas (:150) — run 2 had it homepage-only. Measure before cutting.
7. **[A] Banner position; archive decision.** Unchanged, as previously specified. The banner is now also what pushed the size row to the fold's edge in combination with #2.

ROUND-2 MONDAY LEDGER: **#1 DENY flip — OPEN**, third audit, depleting live. **#2 masters — OPEN**, third audit, cart unchanged. **#3 banner — OPEN**, third audit. **#4 meta-row reserve — HALF-DONE, the dangerous kind:** the r2 symptom is gone (§1.1) but the prescribed systemic fix (`size-adjust`) was never applied — and the armed cause fired again, bigger, in the new header. Two consecutive audits' top theme defect from one un-implemented line-class. **#5 placeholders/contact — DONE-plus** (placeholders 0, terms states return window AND postage, FAQ real, search built) **except email, which got worse.** **#6 archive — OPEN**, byte-identical third pull. Residual round-1 opens: measurements table, `9-16 days` jeans contradiction — both untouched three audits (DELTA-3WAY §2).

COUNCIL QUESTION. The aesthetic now has a competitive scoreboard, not just journeys: 39/50 against a field of 14–30 (compare/REPORT.md), and the moat list is the aesthetic's output — sub-3MB pages in an 11–22MB field, the only variant-level sold-out honesty measured anywhere, the only card-level recency signal, one of two keyboard-completable purchases. 0 of 8 personas leave. Nothing attributable to the look costs a sale. What costs now: (a) the font-fallback mechanic — a tax of the two-mono constraint, payable once via `size-adjust`, currently being paid per-surface per-sprint; (b) an admin list that hasn't moved through nine days of live trading while the theme out-shipped it twice. **Must not change:** buy spine, `PRODUCT NN / 14`, FILED dates, witness statement, board pause guards, and the urgency-refusal — now evidence-backed as differentiation (scarcity honesty 5/5 vs field ≤3; Ultralight's urgency theatre scores 14). Guardrail unchallenged; the pack strengthens it. **Highest-value single change:** #1. Still minutes, still three checkboxes, and for the first time on a measured countdown.

===== ADVISOR: FIRST PRINCIPLES =====

Rebuilt premise, round 3: with supply restocked and the archive frozen, the storefront's job is to convert cold social taps and hold the audience between drops. On that job the evidence is now unambiguous — **the aesthetic caused zero of the abandonments across three runs** (journeys/SUMMARY: 3→1→0 leavers), and it out-scores six competitors 39/50 (compare/REPORT §1). The binding constraint is still merchandising: 1,452 archived units (~£28k) identical across three pulls, and the three `CONTINUE` tees selling back down to 8–9/variant on live trade (commercial-run3.json: 22 orders, £938 in 9 days; 3 CLIVES 100→95). The theme has out-shipped the shop twice.

**Where the aesthetic earns its keep — measured, not felt:**
- The refusal of heavyweight furniture *is* the speed advantage: 2.7 MB homepage vs 11.7–22 MB field; Ultralight's homepage takes 88 s on the same throttle (REPORT §1.1). Austerity is a conversion asset on Instagram-arrival mobile.
- The rejected urgency mechanics scored 5/5 on scarcity honesty — variant-level `SIZE M IS SOLD OUT` + notify + FILED dates is a differentiator "nobody in the field has" (REPORT row 5). The guardrail is earning revenue, not costing it.
- The system absorbed thirteen new commits without dilution: search, TERMS (654 words, zero placeholders, postage liability stated), 14-Q FAQ — all in-voice, no-JS-safe, first-measurement clean (METRICS §3, newtabs.json). Corteiz at 30/50 proves the territory converts at 10× scale.

**Where it is costing sales — three specific elements:**
1. **The typographic system's implementation, not its constraint.** CRX Mono with `font-display: swap` in a header allowed to wrap (`crooks.css:432 flex-wrap: wrap`, `min-height` not fixed at :397) drops MAIN 48 px at t≈1.9 s: **CLS 0.325–0.391 on every mobile page, 0.59 on the cold-click journey** (METRICS §1.1) — and pushed V2 BAGGIES' size row to y=844, untappable at the fold, on the #2 lifetime seller carrying the sold-out apparatus (§1.2). This is the top theme defect for the *second consecutive audit* (VT323 meta-row in run 2), from one cause: fonts with unmatched fallback metrics doing layout-critical work. The prescribed `size-adjust` exists nowhere in deployed CSS (grep-verified). Two typefaces is defensible; two typefaces without metric-matched fallbacks is a bug factory.
2. **Trust-in-prose raises the price of plumbing errors.** Having removed every fallback signal, the prose is load-bearing — so `crooksldn@gmail.com.com` on the shipping policy (METRICS §3) is a dead address on a legal page, and the Gmail/info@ split survives a third audit. The sceptic now hesitates instead of leaving on exactly this (SUMMARY row 4).
3. **Austerity misapplied to metadata.** Search surface 1/5 vs field: no meta descriptions, homepage title "CROOKSLDN", no FAQPage JSON-LD on 14 in-voice Q&As (REPORT row 9; METRICS §3). Minimalism where no shopper sees it costs acquisition and buys nothing.

**Must not change:** the canvas board (60 fps in view, 0 fps hidden/reduced-motion, CLS 0 — KEEP §1); the plain-English spine under the fiction — `ADD TO BAG` never goes in-fiction (KEEP §2); the measurement *apparatus* (replace the placeholder arithmetic, not the component — KEEP §3); the no-JS fallback; the urgency refusal, now competitively priced at 5/5.

**Backlog ruling:** (1) `CONTINUE`→`DENY`, three checkboxes — admin, minutes, third audit, days from re-arming the oversell→refund loop (June −£195, Aug −£64); (2) the header/size-adjust fix; (3) email find-and-replace; (4) the three masters (`cellcrew` 976 KB rides the cart — LCP 10.3 s, METRICS §2); (5) isolate the INP doubling (~1,050 ms, search index + menu game suspects); then FAQ schema + meta descriptions; then the £28k archive decision, which is the actual growth lever.

**Highest-value single change:** if the council may reach into admin, the three checkboxes — nothing the theme does matters if the shop sells phantom stock again. Within the aesthetic's own ledger: **fixed header height + `size-adjust`-matched fallback stacks for both faces** — one change that ends the site-wide CLS, restores the size row to the viewport on the product that needs it most, and retires the defect class that has produced the top theme bug two audits running. The concept has now been vindicated three times; what remains is enforcing its two invariants in code, not review (DELTA-3WAY §3).

===== REVIEWER: BRAND =====

**BRAND REVIEW — ROUND 3**

The baseline every advisor must be judged against: KEEP.md's headline ("not one abandonment was caused by the way this site looks"), SUMMARY's 0/8 leavers, and compare/REPORT.md's moat list — sub-3 MB pages, variant sold-out honesty, FILED dates, writing-as-trust, 39/50 vs a 14–30 field, with Corteiz (30) proving the territory and Ultralight (14) the control for urgency theatre. All five correctly blame the CLS on font *implementation*, not the type system — METRICS §1.1's ablation (block crx-mono → 0) licenses exactly that and nothing more. Nobody proposes a fiction-ectomy. Three brand risks remain.

**1. B's commit freeze is the only recommendation that would actively damage the working system.** "No fourteenth theme commit until the checkbox flips to DENY" would hold the header/`size-adjust` fix — SUMMARY's worst moment #1, a theme commit — hostage to an admin task that has already survived three audits unowned (DELTA-3WAY §1). The austere system's measured asset is speed *and stability* (REPORT §1.1); freezing the theme leaves CLS 0.325–0.391 live on every mobile page degrading precisely that asset. The leverage instinct is right; the mechanism punishes the brand's best surface.

**2. D's archive elevation needs a guardrail nobody wrote down.** Making the closed-case register the "highest-value change on the full ledger" is commercially argued (£28k, commercial-run3.json), and D does honour the hand-count and WITNESS STATEMENT. But the register's moat is its tightness: `PRODUCT NN / 14` numbering (KEEP §2) and FILED dates as "the only card-level recency signal" in the field (REPORT §6). Reintroducing ~467 units must not renumber the live register or blur FILED recency — D prices the work but never states this constraint. Flag it before Monday.

**3. A's popup retirement is a cut into fiction furniture — and the evidence supports it.** The menu entry now carries the invitation (newtabs.json `PLAY CASE:001 NOW`; persona 5 "Returns, follows" via menu, SUMMARY row 5), the homepage seam is real ("CASE 001 text also still present — both render," METRICS §3), the interruption score is the theme's weakest design row (3/5, REPORT row 3, "homepage popup + 338 px banner" cited), and COUNCIL.md:126 already ruled "Stop stacking." This is subtraction the standing ruling asked for.

Everything else is clean. C's must-not-change list is the most complete brand fence in the pack (buy spine, `PRODUCT NN / 14`, FILED, witness statement, board guards, urgency-refusal). B's "bilingual retreat is the load-bearing concession" is the round's best brand insight — newtabs.json confirms every converting surface is subtitled in plain English. E's "austerity misapplied to metadata" correctly separates shopper-invisible minimalism (REPORT row 9, 1/5) from the aesthetic itself. D's gift-card naming follows the bilingual rule verbatim (steal list #2).

**Verdicts:**
- **A:** Sound; its one fiction cut (the popup) is evidence-backed subtraction, not sanding.
- **B:** Best analysis, worst remedy — drop the commit freeze; it damages the stability the brand is measured on.
- **C:** The safest hands; brand fence complete, every fix plumbing.
- **D:** Approve, conditional on an explicit no-renumbering/closed-case guardrail for the archive.
- **E:** Clean separation of constraint from implementation; no brand risk.

===== REVIEWER: FEASIBILITY =====

FEASIBILITY REVIEW — verified against `d0363ee` source and run-3 evidence.

**The shared mispricing: "one fix restores both."** A, C, D and E all claim the header fix simultaneously kills the site-wide CLS *and* returns V2 BAGGIES' size row above the fold. The source says these trade off. METRICS §1.1: "the fallback metrics fit one line, the real font wraps it to two" — two lines is the loaded-font steady state. `size-adjust` alone makes the header wrapped from first paint: CLS→0, but the size row stays at y=844. C is internally contradictory: "reserve the bar's **wrapped** height at crooks.css:397" permanently spends the 48 px, then claims "this same fix returns" the row to the viewport. Restoring the fold needs a second, different edit — make five controls fit one line at 390 px (condense the CATALOGUE label/tracking or relocate a control). And that edit is constrained: the wrap at ≤429 px exists specifically for 200 % zoom ("At 200% zoom a 390px phone is 195 CSS px… Wrap rather than shrink the targets", crooks.css ~:425), and METRICS §2's a11y pass ("zoom reflow 195==195") depends on it. A blunt fixed height or no-wrap regresses WCAG reflow. Honest price: two edits, the second design-constrained. Nobody priced this; E even quotes the wrap line, then prescribes the fixed height it warns against.

**Admin/theme classification.** C's [A]/[T] tags all verify: policy email is Settings→Policies; the gmail footer is a customizer override over the theme's `info@crooksldn.com` default (crooks-footer-log.liquid preset, ~:123, confirmed). Shared unpriced dependency: "unify on one address" assumes `info@crooksldn.com` is a live mailbox — nobody verified it. Unifying legal pages onto a dead domain address is worse than the typo.

**INP isolation is cheaper than priced.** `crooks-board.js` is gated (`crooks-header.liquid:3`, `if section.settings.show_case`) — ablation is a customizer toggle, minutes, not theme surgery.

**A's hidden dependency.** A conflates two artefacts: the menu entry is CASE 001 (attract board); the "uninvited homepage popup" is Crack the Cuffs — the *first-visit discount* popup, app-hosted (snippets/crack-the-cuffs.liquid:2, :133 app close-message). "Retire it" removes the discount-capture mechanic, not a duplicate invite. The homepage CASE 001 leftover is `templates/index.json:32` — editor removal, cheap, unclassified by A.

**Correctly priced.** FAQ JSON-LD: Q&As live in section blocks, so the ~20-line liquid loop is real (C/D; richtext answers need `strip_html`). D's archive at "days" is honest — exhibit-record guards missing metafields (`crooks-exhibit-record.liquid:35–41`), so republish thins content rather than breaking. D alone prices SMS intake as unverified, matching the commit. `size-adjust` absence: grep-confirmed, 0 hits in source and served CSS. DENY flip as admin-minutes: correct, all five.

**Verdicts:**
- A: Best instincts, worst pricing — popup retirement silently kills discount capture, and buys the two-for-one header myth.
- B: Sharpest process reasoning; "enforce in tokens like the radius" is feasible; still sells the bundled fold restore.
- C: Most accurate [A]/[T] classifier in the pack, but Monday item 2 contradicts itself on wrapped-height vs fold.
- D: Honest pricing throughout (archive days, SMS unverified); inherits the bundled header claim uncritically.
- E: Correct mechanism diagnosis, but its own cited zoom-guard evidence refutes its prescribed fixed height.

===== REVIEWER: ACCURACY =====

**ACCURACY REVIEW — ROUND 3**

Verified against the pack and `d0363ee` source. Only genuine faults listed; everything unlisted checked out.

**A — no factual errors found.** Spot-checks all exact: METRICS §1.1 quote "no longer occurs" (0.2315); `> CHAIN OF CUSTODY DATABASE ONLINE` at crooks-tracking.liquid:195; `gmail.com.com` at newtabs.json line 179 precisely; journeys/01's 1.5 s / t≈1.9 s / 48 px / CLS 0.59; 49 phantom units (COMMERCIAL.md); variants 8–9 (commercial-run3.json). One nuance: states 39/50 as current without noting REPORT scored `db96aa3` — B's staleness point applies to A too.

**B — facts sound, two miscites.** (1) "FILED 03.08 flipped persona 2 to 'stays' (DELTA #14)": DELTA #14 records FILED dates live, not the persona flip — that lives in journeys/02 (r2) and responses-round2.md:31, and round 2's own review ruled the flip was credited to dates *plus* sold-out honesty, not dates alone. (2) `CHAIN OF CUSTODY — SHIPPING & RETURNS` cited to newtabs.json — the string is not in that file (it's DELTA #13 and exhibit-record.liquid:700). Also, "the pack spent two rounds saying theme, minutes" is only half-true: DELTA.md:137 says "Theme, minutes," but COUNCIL.md §3 already priced the size-adjust fix "hours… not minutes." Verified correct and load-bearing: crooks.css:101; zero `size-adjust` in all nine theme CSS files and served-crooks.css; 0.3906 vs Corteiz 0.3522; "Stop stacking" is under COUNCIL.md's blind-spots paragraph.

**C — most accurate response; every citation exact.** crx-mono.css:7,14 (`font-display: swap`); crooks.css:47–48 (stacks), :397 (`min-height: 56px` bar), :431–434 (≤429px wrap); footer-log.liquid:123 (`info@crooksldn.com` default); faq.liquid `{% schema %}` at :64, no `ld+json`; header.liquid:4 loads crooks-board.js (conditional on `show_case`, but header renders site-wide — fair), canvas at :150; `db96aa3` header confirmed board-free ("run 2 homepage-only" true); 13,876→2,404 (DELTA #6); `denyFlip.done: false`; MONEY CLIVE "XS/S/M BLACK 9". One stretch: #7's claim the banner co-caused the fold regression — METRICS §1.2 measures y=844 *after* banner dismissal; header growth is the sole measured cause.

**D — three errors.** (1) "The only dimension the field beat us on": REPORT §1 names two — trust plumbing *and* search surface (row 9: crooks 1 vs field 3–4). (2) "Trust surface now exceeds Mertra and Phase" is real (DELTA-3WAY §2.3) but the citation given, REPORT §2 row 6, shows the opposite (2 vs 4). (3) "~£200/day" is unsupported: £937.75/9d ≈ £104/day, Aug-to-17 ≈ £110/day, 90-day ≈ £123/day. Minor: "22 orders" sits in `trading.delta_9_days`, not `denyFlip`. SMS claims are verbatim from d0363ee's commit message, including "Not verified: the rendered result on staging" — correctly quoted.

**E — accurate, two trivialities.** crooks.css:432 and the :397 min-height reading are exact; "June −£195, Aug −£64" both in pack (commercial-repull.json: "~£64 reversed"); KEEP §1 (60/0 fps, CLS 0) exact. The "nobody in the field has" quote sits in REPORT §1.2, not row 5; "1,452 units (~£28k)" repeats DELTA-3WAY's shorthand where COMMERCIAL.md attaches £28,270 to the 467-unit remainder.

**Verdicts:**
- A: Clean — every checked claim verified; carries the stale 39/50 uncaveated.
- B: Substantively right, sloppily cited — two wrong pointers, one overreach on "minutes."
- C: Flawless citation discipline; one causal stretch on the banner.
- D: Three real errors (only-dimension, row-6 miscite, ~£200/day); quotes otherwise exact.
- E: Accurate throughout; two cosmetic citation slips.

===== REVIEWER: PROTECTION =====

Verified against KEEP.md (rounds 1+2 addendum), served-crooks.css (zero `size-adjust` — B/C/E's grep claim checks out), and METRICS §3.

**PROTECTION REVIEW — ROUND 3**

**A.** "Retire the popup" is safe: KEEP §9 protects only the popup's *compliance* (radii/shadow, fixed in r2), never its existence, and the menu entry (73d24e1) now carries the invitation. "Finish the move" on the CASE 001 seam is also clean — KEEP §8 protects the fake-data *principle* (leaderboard hidden until real scores), not the section's homepage tenancy; removal doesn't reverse the principle. A's must-not-change list correctly covers the spine, the span rule (§2), and register numbering (§7). No violations.

**B.** One real protection hazard: the process ruling "no fourteenth theme commit until the checkbox flips to DENY" would freeze the very commit B names highest-value — the fix that returns V2 BAGGIES' size row from y=844 into the viewport. That row *is* KEEP §2's protected first-viewport answer ("does it come in my size," found in ~2s). Gating repair of a §2-protected surface behind an admin action owned by nobody sands off something load-bearing by neglect. Everything else — bilingual-retreat rule, token-layer enforcement modeled on §9 — is KEEP-aligned.

**C.** Cleanest technically. #6 (INP isolation) brushes KEEP §1 — crooks-board.js and its three pause guards are the protect-list's crown — but C's "measure before cutting" is the correct hedge; any cut must target the site-wide *load* (header:4), never the homepage board or its guards. #7 banner: explicitly fair game per the r2 addendum ("NOT on this list"). One gap: C's prescribed edits touch the font stacks at crooks.css:47–48, and the r2 addendum mandates re-running no-JS and 200% zoom checks for any display-font-stack change. C doesn't attach that check.

**D.** The archive revival is priced with the right guards — hand-count first, closed-case framing "keeps the WITNESS STATEMENT true" (KEEP §6), leaderboard ruling upheld (§8). One caution: the r2 addendum's furniture rule ("new furniture must earn its viewport — the carriage bar didn't") applies to both the closed-case register and gift cards; D books neither against it. Not a violation, but the accretion pattern B diagnoses is exactly what this rule exists for.

**E.** Only respondent to cite KEEP by section (§1, §2, §3) and the only one to restate §3's replace-the-data-not-the-component rule. "Two typefaces is defensible" correctly protects the constraint while attacking its implementation. INP item hedged as "isolate." No violations.

**Shared gap, all five:** every respondent prescribes the header-height + `size-adjust` fix; none attaches the r2 addendum's mandatory re-check (no-JS + 200% zoom) for display-font-stack changes — the two things "the last sprint proved are easiest to break silently." The synthesis must carry that rider. Also unanimous and correct: nobody touches ADD TO BAG (§2), aria-disabled (r2 addendum #2), FILED (r2 #1), or the urgency refusal.

**Verdicts:**
- A: Clean — popup retirement and CASE 001 cleanup both verified outside KEEP's protection.
- B: Sharpest self-audit, but the commit-freeze ruling would hold a §2-protected surface hostage — strike it.
- C: KEEP-safest execution plan; add the mandatory font-stack re-check rider.
- D: Sound, with §6/§8 guards explicit; price the new furniture against the r2 accretion rule.
- E: The protection benchmark — cites KEEP by section and violates nothing.

===== REVIEWER: COMMERCIAL =====

COMMERCIAL REVIEW — ROUND 3 (angle: expected revenue impact)

The ledger, verified: £937.75/22 orders in 9 days ≈ £104/day (commercial-run3.json delta_9_days); archived stock 1,452 units, byte-identical third pull, ~467 real ≈ £28,270 at retail incl. the #1 lifetime seller at 146 units (COMMERCIAL.md top-sellers table, archive table); DENY still unflipped with 3 CLIVES S/BLACK at 8 and MONEY CLIVE XS/S/M BLACK at 9 (run3 denyFlip). The biggest number in the pack is the archive — 2.5× the last 90 days' revenue — and the second-biggest risk is the re-armed oversell that already produced June's −£195.09 and August's £64 reversal (COMMERCIAL.md, commercial-repull.json 2026-08 note).

**Ranking:**

1. **D.** The only advisor who priced the money. Names the archive the largest number "by an order of magnitude," prices it (£28,270), and — critically — prices its cost honestly: hand-count first because CRXST★RZ 970→98 proved counts lie (commercial-repull.json syncArtefactResolved). Also the only one refusing to book SMS revenue until a consent record is verified. One ding: "~£200/day" — measured run-rate is ~£104–110/day; that's July's rate, not today's.
2. **C.** Best downside protection and only genuine value÷effort discipline: DENY at #1 with a measured countdown, cart masters at #4 (976 KB cellcrew on a 10.3 s money-page LCP, METRICS §2), CRX GARMS decision bundled into the same admin visit. But the £28k archive is a sub-clause of item #7 — C protects revenue superbly and under-weights growing it.
3. **E.** Correct at both ends — DENY first, archive explicitly "the actual growth lever" — then self-contradicts by ranking that lever behind FAQ schema and meta descriptions, which are acquisition pennies for a brand whose demand arrives via Instagram, not search.
4. **A.** The final call is commercially right ("DENY before the header, if only one thing happens Monday") and correctly cites the 8–9-unit countdown. But A's ledger stops at defect prevention: zero mention of the archive, three rounds running. Half the money is invisible to A.
5. **B.** Chasing pennies. Leads with font-token process rulings; its unique adds (meta descriptions, stale 39/50, faqSchema) are rounding errors against £104/day. Never mentions the 1,452 units/£28k — B reproduces the storefront's own blindness. Two redeeming contributions: the "no fourteenth theme commit until DENY flips" rule is the only *mechanism* anyone proposed for a checkbox that has survived three audits, and "trading data is from the live site scored 14/50; this theme's conversion is still inference" (verified: compare/REPORT.md scores live crooksldn.com 14/50) is the most honest commercial sentence in the round.

**Inventory answer:** nobody ignores the DENY flip anymore. The *archive* inventory — the actual money — is still ignored by A and B.

**Verdicts:**
- A: Right final priority, but half the ledger — the £28k half — doesn't exist for A.
- B: Sharpest process critic, weakest merchant; pennies up front, £28k unmentioned.
- C: The best revenue-protection list on the table; growth demoted to item #7.
- D: Found the money, priced it, and priced its cost honestly — top of the round.
- E: Names the growth lever, then files it last; ordering contradicts its own analysis.