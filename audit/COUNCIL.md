# COUNCIL.md — full record

Method (Karpathy-style LLM council): five advisors with fixed thinking lenses
answered independently against the evidence pack (`AUDIT-CONTEXT.md`,
`QUESTIONS.md`, `journeys/SUMMARY.md`, `features/FEATURES.md`, `SPEC.md`
§0/§9/§10, selected journey logs). Their responses were anonymized (A–E,
randomized) and peer-reviewed by five independent reviewers; a chairman then
synthesized the verdict. Disagreements are preserved below, not averaged away.
Guardrails enforced in every prompt: recommendations must fit the design law
(no radii, gradients, shadows, new typefaces/colours, fabricated content,
build steps); SPEC §9 behaviours challengeable only with journey evidence.

**On the conditional second council (trust):** the brief said to run a
narrower trust council *if trust emerged as the dominant blocker*. It did not.
The evidence acquitted the aesthetic (15/20 checkouts, both sceptics bought,
zero look-driven abandonments) and located the damage in machinery and
self-consistency — the council's unanimous first agreement. Q4's answer stands
as the trust verdict: the no-reviews position is affordable while the site
never contradicts itself. No second council was convened; running one against
this evidence would have manufactured a problem the journeys refute.

---

# THE VERDICT (Chairman)

## Where the Council Agrees

Five advisors, working independently, converged hard on four points — treat these as settled.

**The aesthetic is acquitted.** 15 of 20 personas reached checkout; zero abandoned over the look; both sceptics (02, 05) arrived to catch a scam and bought. The Outsider, The Contrarian and The First Principles Thinker all say the same thing in different registers: the austerity *is* the trust signal. Nothing gets softened.

**The damage is machinery contradicting the fiction, not the fiction.** Everyone's casualty list overlaps: the "9-16 days" AliExpress line, the 14-vs-30-day returns clash, the £76.50 bag becoming an £85 till, the double-add overcharge, the hCaptcha eating both warm £60 leads, and REVEAL MY CODE taking phone + SMS consent and paying nothing.

**The do-not-touch list is unanimous:** the plain-English buy spine, the measurement apparatus and SIZE GUIDE anchor (the proven closer — 03, 11), the set toggle's purchase flow, the honest sold-out state, the evidence bag.

**Every fix is deletion, config, or copy.** Nothing anyone proposed strains the design law. And The Executor's live-retest gate — verify the preview-caveated bugs (B-5, B-1, captcha) on crooksldn.com before shipping code — drew no objection and two endorsements.

## Where the Council Clashes

**Repair vs. growth.** The Expansionist says the highest-value move is minting more sets: a sceptic-proof £50→£85 engine live on 2 of 14 products, four metafields per pair. Review 4 backs this as the only answer to "where does this move the business furthest." Three reviewers push back: the extrapolation from two scripted personas on one pair to eleven unminted pairs is unevidenced, and it scales a machine whose cart half (B-2/B-3) and till (B-5, double-add) currently overcharge the customers it converts. Both sides are right about different clocks: the Expansionist describes the best month-two move; the others the mandatory month-one. Settled by: fixing B-2/B-3/B-5 first, then real Shopify data on attach rate, margin and stock depth per candidate pair.

**Is conversion even the constraint?** The First Principles Thinker reframes: no-restock drops mean supply binds, so conversion fixes only change *who* buys — the list is what compounds. The audit confirms the drop model but contains zero sell-through data; three reviewers caught that the premise is asserted, never evidenced. If drops don't sell out, the mispricing bugs are direct revenue losses. Settled by one Shopify query: days-to-sellout per SKU across past drops. The conclusion (fix the demand-capture stack, 0-for-3 broken) survives either way — only its *priority relative to the till* depends on the answer.

**The single highest-value change** splits four ways — pause the popup (Executor), delete the delivery lines (Outsider), full reconciliation pass (Contrarian), demand-capture stack (First Principles). The Contrarian's framing subsumes the Outsider's; Review 1's legal finding breaks the remaining tie.

## Blind Spots the Council Caught

Peer review surfaced six collective misses:

1. **In-app webviews.** The traffic is Instagram/TikTok, where popups and hCaptcha behave worse than in Safari — no journey tested the actual entry surface.
2. **UK GDPR/PECR exposure.** Collecting phone numbers and SMS consent via a prize mechanic that pays nothing is a legal liability, not merely a trust inversion. Pausing the popup is legally urgent.
3. **No ground truth.** Every priority rests on twenty scripted personas; nobody proposed checking real Shopify funnel data, notify submissions, or discount redemptions before ranking.
4. **No post-fix measurement loop** — no advisor proposed verifying that any fix moved anything.
5. **The past.** Customers already overcharged by the double-add or vanished discount are live liabilities for a brand whose moat is exact arithmetic. Audit orders; refund proactively, unprompted.
6. **The shareable surface.** Link-in-bio landing, OG previews of a near-black terminal as a story card, the register as a screenshot-ready collection object — the cheapest acquisition lever a drops brand has, unexamined.

## The Recommendation

Adopt The Contrarian's diagnosis, sequenced by The Executor's plan, with The First Principles Thinker's capture stack as the second wave — and defer The Expansionist entirely until the till is honest. Concretely: (1) pause the popup and run the live retest gate; (2) the reconciliation pass — delete every contradicting number in one sitting: delivery lines, returns windows, duplicate tables, portal copy; (3) fix the double-add and discount handoff; (4) rebuild demand capture with honest drop-model copy ("runs don't restock — first notice of the next drop"), a visible confirmation, and the informant intake mounted; (5) audit past orders and refund overcharges; (6) pull real analytics before and after each wave. Only then mint sets and the gift card — the Expansionist's ideas are good, and premature. All of it is deletion, config and copy; the design law and SPEC §9 behaviours stay untouched.

## The One Thing to Do First

Today, before anything else: open the Crack the Cuffs app admin and pause the popup. Five minutes, no code, no retest needed — its broken payout was reproduced across sessions, 12 of 20 journeys complained, and it is simultaneously the worst trust inversion on the site and an open GDPR/PECR exposure. Everything else can wait for Monday; this can't.

---

# THE FIVE ADVISORS (full responses, de-anonymized)


## The Outsider

This reads as a real shop. That surprised me, and it should reassure you: the thing insiders worry about most — "will a stranger think the police-terminal bit is a scam?" — is the one fear the evidence kills. Jordan (01), cold off a story link on bus 4G, had name, price, sizes and both buy buttons on one screen inside 40 seconds and said it "doesn't feel like a scam template." Dan (02) arrived hostile and bought. The fiction is earning its keep everywhere it touches chrome: the austerity reads as confidence, and the absence of countdowns and "17 people viewing" is *why* the sceptics stayed. Do not touch that.

What a stranger actually notices in 90 seconds is everything stacked on top of the shop and everything that contradicts it. Named moments:

- **01, Step 7:** Jordan tried to hand over his email for a restock — the only conversion that session could produce — and got a full-screen animal-clicking captcha. He closed it. You paid Instagram for that lead and your own form shredded it. He also tapped a glowing CHECKOUT NOW next to SOLD OUT and got silence (Step 5) — a lit button that does nothing reads as broken, not austere.
- **02, Step 4:** "9-16 days delivery uk," lowercase, one accordion above "UK 1–2 working days." Dan called it "the AliExpress line" and it nearly ended the evening. A stranger can't tell your deliberate minimalism from a dropshipper's forgotten template — your only tell is whether the numbers agree, and here they don't.
- **05, Step 9:** Marcus applied 10CROOKS in the bag, saw £76.50, and the till said £85 with the code gone. His words: a trusting shopper "would have paid the difference without ever knowing." For a brand whose entire trust substitute is exact arithmetic, the bag and the till disagreeing is the worst possible sentence.

The gap between belief and experience: the brand thinks its risk is the aesthetic. All three personas shrugged at the aesthetic and flinched at the *machinery* — captcha, contradiction, vanishing discount, gmail returns inbox, a lit dead button. Every flinch is self-inflicted and none requires softening anything.

**Single highest-value change:** delete the stale delivery lines from product descriptions ("9-16 days," "3-5 day"). It's a one-line deletion, it hit three shoppers at the exact decision moment, and it repairs the load-bearing wall — self-consistency — that everything else leans on. Immediately behind it: make the bag's discount survive to checkout (05), and let the notify email through without a visible puzzle (01). Fix those three and the terminal sells itself.

---

## The Expansionist

THE EXPANSIONIST'S READ

Everyone else will tell you what's broken. Look at what's idle.

**The set engine is a proven money machine running at one-fourteenth capacity.** SPEC §5 says adding a set is "four metafields and a bundle, with no code change." That engine took persona 04 from £50 intent to £85 checkout, did the same to 19, and survived 05 — a man who arrived specifically to catch it lying — because the £95 anchor is verifiable on the same page. That's a ~70% AOV lift mechanism, built, audited, sceptic-proof, and configured on exactly two products. Jeans + tee. Jorts + tee. Baggies + crewneck. Every pair minted is pure upside on zero new code. This is the single highest-value change: replicate the set. (While minting them, fix B-2/B-3 — the cart-side half currently walks the one shopper who obeys it into £95 or £130, which is the engine sabotaging itself.)

**The register format is a collection mechanic nobody's cashing.** NO. 01–14 made the desktop shopper want to see everything (19); drops that never restock make each number a one-time exhibit. A conventional shop can't say "gone is gone" without it reading as failure — this fiction makes finality *provenance*. Say it out loud on sold-out records. That's true urgency from a brand whose whole moat (Q4) is never faking any.

**The packaging section is unmarketed gift wrap, and the gift buyer proved the segment.** Persona 09 arrived with £56, left £31, and called the evidence bag "better than any wrapping I'd do." A gift card — a real Shopify product, NO. 15 in the register, zero fabrication, zero design-law breach — recovers her segment: "who do you think pays for teenagers?"

**The compounding play is the list, and all three mouths that feed it are broken.** This is a drop brand: with no restocks, the pre-drop list IS the revenue pipeline. The brand built three capture machines — informant intake (renders an empty box, B-1), notify-me (hCaptcha ate both warm £60 leads, 01/06), and CASE 001's REVEAL MY CODE (takes phone + SMS consent + email, pays out nothing, 17). Three list engines, three leaks. Worse: the dead reveal converts the honesty moat into its opposite, silently, among teenagers who talk — on the exact channels the traffic comes from. Fix the payout, demote the popup back to the drawer board's invitation posture (Q1 already showed the polite version works), and the game becomes what it wants to be: native TikTok content that acquires for free.

Must not change: the plain-English buy spine, the verifiable anchor, the refusal to fake, the evidence bag.

---

## The Contrarian

The aesthetic argument is settled — 15/20 reached checkout, zero left over the look — so stop congratulating the terminal and look at what it's mortgaged. This brand replaced social proof with a single promise: *every number we print is exact.* That is the whole trust budget. And the store is currently in default on it.

**Q4: no-reviews is affordable; the collateral is self-consistency, and it's being spent.** The sceptic (02) bought, but PayPal-only, 25 minutes, screenshot folder open — "9-16 days delivery uk" one inch above "UK 1–2 working days" is the AliExpress line on a site whose only credential is exactness. The searcher (12) postponed a £50 order over 14-vs-30-day returns. Worse: jeans and baggies serve *byte-identical* measurement tables — and the measurement apparatus is the audit's proven closer (03, 11). A two-product shopper who catches that doesn't lose one sale; the closer becomes the tell. Note where SPEC §10 files all this: "store/admin work." Misfiled. For this store, copy reconciliation *is* conversion work, and it's ranked behind SEO chores.

**Notify/restock is the honesty machine running in reverse.** Two of five non-purchases (01, 06) were warm £60 leads whose emails died in an hCaptcha with no confirmation state — form sits untouched, no tick, no error. On a brand where sold out is forever, the notify list is the *only* retention asset, and 06 nailed the deeper fraud: "when this size is BACK" is a cheque a no-restock brand can't cash — fabricated content by implication, from the brand that refuses to fake a leaderboard. 06 followed Instagram *because she didn't believe the email exists.* Fix: honest conditional copy, one FAQ line on how drops work, a visible confirmation, captcha retested live.

**Complete-the-set converts best and betrays its converts.** Two personas upgraded £50→£85 (04, 19) — then B-2 hides "SET SAVING APPLIED" in the honest cart and shows it only in the £130 duplicate-shorts cart; B-3's own upsell line walks the obedient shopper into £95 or £130; and 05 watched £76.50 become £85.00 at the till (B-5/O1). The sceptic caught it. A trusting buyer pays the £8.50 and never knows — until they do.

**Highest-value change:** the reconciliation pass — delete/fix every contradicting number (delivery lines, returns windows, duplicate tables) in one sitting. Pure deletion, zero design cost, and it repairs the load-bearing wall everything else leans on. Then retest B-5 live before another code ships.

---

## The First Principles Thinker

Wrong question. "Where is the theme costing sales?" assumes sales are the binding constraint. They are not. This is a 14-SKU label running short runs that never restock: supply is the constraint; demand is the perishable asset. The converting half already works — 15 of 20 reached checkout, zero abandoned over the look, the two sceptics built to fail (02, 05) both bought. When a run sells through regardless, a marginal conversion gain mostly changes *who* gets the stock, not revenue. What compounds across drops is the list.

So the site has two jobs: sell the current run (working, minus mechanical bugs already logged — CHECKOUT NOW double-add, the discount handoff) and bank the demand it cannot serve for the next run. The second job is where everything is broken, simultaneously:

- The notify form: hCaptcha ate both warm £60 leads (01, 06). 06's log is the whole case in one line — "the sale was lost to stock; the *relationship* was lost to an unconfirmed form."
- Crack the Cuffs: takes phone, SMS consent and email; REVEAL MY CODE returns nothing (17).
- The informant intake — the homepage's only signup — renders a headline over an empty box (B-1).

That is the entire demand-capture stack, 0 for 3. For a drops brand this is not a leak; it is the business failing at its actual job while the storefront performs flawlessly in front of it.

Q1 through this lens: the board question is mis-framed too. The homepage's job in a drop model is not attract-mode entertainment — it is recruiting for the next drop. The board should not come back; the intake must mount. QUESTIONS.md's verdict is right but under-prioritised: B-1 is not "a dead section", it is the strategic organ.

One more ground-up finding: "TELL ME WHEN THIS SIZE IS BACK" on a no-restock model is the site breaking its own honesty law. 06 sensed it — "writing cheques it'll never cash" — and 06 spent half the visit hunting for a restock answer the site never gives. The brand's substitute for social proof is exact truth; this is an inexact promise. Say what is true: "Runs don't restock. Leave your email — first notice of the next drop." Reconciliation, not fabrication; zero CSS.

Must not change: the sold-out state itself (06's best-designed-thing verdict), the plain-English buy spine, the exact-numbers apparatus, the carriage bar's empty-cart stand-down.

Single highest-value change: make demand capture land and confirm — notify submit without the captcha ambush, a visible "you're on the list for M", honest drop-model copy, intake mounted in the same pass. Everything else optimises the half of the machine that already works.

---

# THE PEER REVIEWS


## Review 1
1. Strongest: A. It converts the evidence into a sequenced, ownable plan — a live-retest gate before code ships, changes bucketed by who can execute them (app toggle vs. theme code vs. owner-supplied facts), and an explicit do-not-touch list protecting the proven closers (size guide, set toggle). Every item carries persona citations. D has the best thesis (exactness is the entire trust budget); A operationalizes it.
2. Biggest blind spot: E. Its reframe — supply-constrained, so conversion fixes only change *who* buys — rests on an unverified assumption that every run sells through. No sell-through data appears in the pack. If drops don't sell out, the vanishing discount (£76.50→£85), the double-charge bug, and the AliExpress line are real revenue losses E waves off as "already logged." Elegant premise, unchecked.
3. All five missed: the traffic arrives via Instagram/TikTok in-app browsers, where popups, hCaptcha, and full-screen overlays behave measurably worse than in Safari/Chrome — none of the scripted journeys or fixes account for webview behavior. Also: collecting phone numbers and SMS consent via a prize mechanic that pays out nothing isn't just a trust inversion — it's UK GDPR/PECR exposure. That makes pausing the popup legally urgent, not merely reputational.

## Review 2
1. Strongest: D. It names the mechanism — exactness is the entire trust budget — and every claim is anchored to cited journeys (02, 12, 03/11, 04/19, 05). Its sharpest, genuinely supported point: byte-identical jeans/baggies tables risk poisoning the proven closer. A is the best execution plan (and rightly gates on live retest of preview-caveated bugs), but D supplies the diagnosis A sequences.
2. Biggest blind spot: C. Its "~70% AOV lift" extrapolates from two scripted personas on one product pair to eleven unminted pairs — no evidence other pairings convert, no margin or stock-depth check, and it urges scaling an engine whose cart half (B-2/B-3) it admits sabotages buyers. Rhetoric outruns evidence. E's premise deserves the same scepticism: "supply is the constraint" is asserted, never evidenced.
3. All five missed: the entire evidence base is 20 scripted personas, not real shoppers. Nobody proposed validating against actual store data — Shopify funnel analytics, discount-code redemption, notify-form submission counts, real drop sell-through — before prioritising, nor any post-fix measurement to confirm the fixes moved anything.

## Review 3
1. Strongest: D. It answers all five parts of the question, and it alone identifies the unifying mechanism — exact arithmetic is the store's entire trust substitute, so contradictions (delivery lines, returns windows, duplicate tables, £76.50→£85) are conversion failures, not "admin work." Its highest-value change (one reconciliation pass) is coherent, cheap, and design-law-safe. A is the best execution plan but reads like a punch list; D explains *why* the list is ordered.
2. Biggest blind spot: C. It answers a different question — growth opportunities rather than "where is this costing sales." It never engages with the trust-arithmetic breakage except parenthetically, and its highest-value change (replicate sets) scales an engine D shows is actively betraying its converts (B-2/B-3, B-5). Expansion before repair.
3. All five missed: the mobile/social context they were handed. Nobody tested the Instagram/TikTok entry surface itself — link-in-bio landing, OG/share previews, how a near-black monospace terminal renders as a story-link card, in-app-browser quirks (hCaptcha inside Instagram's webview is likely worse). Also: no one proposed measuring anything post-fix — no verification loop.

## Review 4
1. Strongest: C. It's the only response that answers "where does this move the business furthest" rather than "what's broken." The set-engine replication is the standout: a proven AOV mechanism (04, 05, 19), sceptic-tested, deployable via metafields with zero code, live on 2 of 14 products. That's leverage, not repair. C also monetises the fiction itself (finality-as-provenance, gift cards as NO. 15) — genuine upside inside the design law.
2. Biggest blind spot: A. It's an excellent repair manifest and the worst growth document. Every item restores the store to par; nothing compounds. Its "highest-value change" is pausing a popup — defensive, capped upside. A treats the audit as a bug tracker and never asks what the machine could earn once fixed.
3. All five missed distribution. The traffic is Instagram/TikTok, yet nobody examined the landing path from those channels: link-in-bio destination, share/OG previews of the terminal aesthetic, whether product "records" are screenshot-ready for Stories. The register itself as a shareable object is the cheapest acquisition lever a drops brand has, and it's unexamined.

## Review 5
1. Strongest: A. It is the only response a solo owner can execute as written — sequenced by dependency (live retest gate first, since three findings are preview-caveated), split by who can act, with a do-not-touch list guarding the code being edited nearby. B and D diagnose better prose-wise; A ships Monday.
2. Biggest blind spot: C. It prescribes scaling AOV — minting new sets — on top of a till that misprices (05's £76.50 becoming £85, the double-add overcharge C never mentions). Scaling a machine that overcharges scales refunds and TikTok complaints. It also treats set replication as "zero code" while ignoring the real cost: owner inventory pairing, margin math, and photography. E shares a smaller version: "sales aren't the constraint" rests on unverified sell-through.
3. All five missed: the past, and the ground truth. Nobody says audit existing orders for customers already overcharged by the double-add or vanished discount and refund them proactively — for a brand whose entire moat is exact arithmetic, historical overcharges are live liabilities. And nobody proposes checking real Shopify analytics to size any of this; every priority ranking rests on twenty scripted personas.
