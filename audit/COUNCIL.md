# COUNCIL.md — CROOKSLDN storefront

**Question put to the council:** Where is this aesthetic costing sales, and where is it earning its keep? Be specific about which elements do which. What must change, what must not, and what is the highest-value single change?

**Method:** five advisors answered independently against `audit/AUDIT-CONTEXT.md`, `audit/evidence/METRICS.md` and the eight journey files, with read access to the theme source at `origin/claude/crooksldn-theme-init-bnen7a@1b6bc4c`. Responses were then anonymised A–E and peer-reviewed by five reviewers on different angles (accuracy, brand, feasibility, protection, commercial). The chairman verified every checkable claim against the source and against live Shopify data before synthesising.

**Guardrail applied:** no border-radius above 0, no gradient, no shadow, no third typeface, no new accent colour. No trust badges, reviews widgets, countdowns or urgency mechanics. Constraints challengeable only with named evidence.

---

## THE HEADLINE THE COUNCIL DID NOT SEE

The council reasoned from the evidence pack. During peer review, one reviewer objected that **every "highest-value" claim in the room was unfalsifiable because nobody had looked at a single commercial number.** That objection was correct, and acting on it changed the verdict.

Live Shopify data (pulled 2026-08-08):

| | |
|---|---|
| Lifetime orders | **764** |
| Last 90 days | **£11,103.68** |
| July 2026 | **£9,585.45 across 186 orders**, AOV £54.09 |
| June 2026 | **−£195.09** across 9 orders — refunds exceeded sales |
| Units sold, 365 days | 878 |

**Three things this exposes that no amount of storefront testing would have found:**

**1. Nine archived products and one draft hold 1,452 units of tracked inventory.**

| Product | Status | In stock | Price | Lifetime units sold |
|---|---|---|---|---|
| CRX GARMS T-SHIRT | ARCHIVED | 985 | £25 | 14 |
| BLACK CONVICT JOGGERS | ARCHIVED | 104 | £60 | **105** |
| OG JEANS | ARCHIVED | 93 | £60 | **46** |
| HYRDOCUFF WINDBREAKER | ARCHIVED | 73 | £85 | 15 |
| V1 HOODIE | ARCHIVED | 72 | £60 | 36 |
| PINK CRSDR JOGGERS | ARCHIVED | 41 | £60 | — |
| BLACK CONVICT HOODIE | ARCHIVED | 39 | £60 | 28 |
| CROOKS EXPRESS TEE | ARCHIVED | 33 | £25 | **146 — the #1 lifetime seller** |
| OG CROOK TEE | ARCHIVED | 4 | £25 | — |
| DOUBLE AGENT BALACLAVA | DRAFT | 8 | £25 | — |

Excluding CRX GARMS (985 units at £25 looks like an inventory-sync artefact — CRXST★RZ shows a near-identical 970 and should be checked by hand), the remainder is **467 units ≈ £28,270 at retail, invisible to every shopper.** BLACK CONVICT JOGGERS alone has 104 units in stock and has sold 105 lifetime. This is roughly two-and-a-half times the last 90 days of revenue, sitting in the admin.

**2. Three ACTIVE tees are overselling right now.** Every variant carries `inventoryPolicy: CONTINUE`:

| Product | Total inventory | Storefront says |
|---|---|---|
| MONEY CLIVE TEE | **−22** | `IN STOCK · Ships within 24 hours` |
| 3 CLIVES TEE | **−19** | `IN STOCK · Ships within 24 hours` |
| BROADCAST TEE | **−8** | `IN STOCK · Ships within 24 hours` |

**49 units have been sold that do not exist.** That is the most plausible explanation for June's −£195. It also directly contradicts the homepage's own WITNESS STATEMENT — *"When a run is gone it does not come back"* — because the store keeps selling after the run is gone.

**3. The First Principles Thinker's central premise is false.** Their argument was that conversion is "bounded above by supply that was fixed before the traffic arrived." It isn't. The store has ~£28k of archived stock and is overselling its active tees. Supply is not the binding constraint; **merchandising is.** Their *conclusion* — capture demand rather than chase conversion — survives, and is strengthened. Their *premise* does not.

---

## Where the Council Agrees

Five advisors, working independently, converged on four points.

**1. The visual system is not what loses sales. Unanimous, and evidenced.**
Persona 6 was *helped* by it — 0 unnamed controls out of 35, a 2 px purple focus ring at 5.88:1, `--crk-red` already raised from `#C4433F` to `#C95450` in a documented WCAG pass. Persona 1 read the aesthetic as deliberate in about a second. Persona 5 stayed because of it. `crooks.css:101` enforces `border-radius: 0` globally; `:428` enforces `border-radius: 0 !important; box-shadow: none !important`. The system is applied with unusual discipline. **No advisor argued for softening it, and none needed to be told not to.**

**2. The cart and the hosted account pages are the real breach — and they breach the brand's own written constraint.**
The cart runs Archivo Narrow, a third typeface the design system forbids; `friendsof.crooksldn.com` runs Times New Roman on white. Persona 7 step 6 and persona 8 step 4. The Outsider put it most sharply: the site changes identity at the exact moment a card number is about to be typed, and in their words that pattern means phishing. **Fixing this requires no new design decisions — only extending rules that already exist.**

**3. Sold-out state is the single most expensive defect.**
Three advisors independently nominated it as the highest-value change. Persona 2 step 6: `aria-disabled="true"` but `disabled === false`; tapping L on V2 BAGGIES silently keeps XS and adding to cart returns `"variant_title":"XS"`. The commercial data makes it worse than the audit knew: **V2 BAGGIES is the #2 lifetime seller at 127 units**, and its M variant is already at `inventoryQuantity: -1`.

**4. The best content is buried.**
CHAIN OF CUSTODY (courier, dispatch, delivery, returns) is collapsed at 1.7 viewports behind a label containing no shipping vocabulary. WITNESS STATEMENT is at 3.6 viewports. REGISTER AS INFORMANT at 4.6. Every advisor flagged some version of this.

---

## Where the Council Clashes

These are not smoothed over. Each is stated with what evidence would settle it.

### CLASH 1 — Can the evidence-log metaphor express recency at all?

**The Contrarian:** it structurally cannot. Persona 2 step 3 — `newInGrid: 0`, `anyDates: false`, every card stamped `AVAILABLE`, ordering `NO. 01…NO. 14`. An evidence log is by nature a static inventory; that is exactly what makes it pleasurable and exactly what makes it useless to a returning fan. `/collections/new` returns 9 of 14 — 64% of the catalogue is "new", which is no signal. On a no-restock catalogue, repeat buyers across drops *are* the business, so **the concept is why the highest-LTV persona leaves.**

**The rebuttal (peer review, brand angle):** real evidence logs carry filing dates. `FILED 08.08` is more in-voice than `NEW`, not less. The metaphor was never the constraint — the implementation was. The `AVAILABLE` slot already exists on every card and is currently spending itself on a constant.

**Chairman's read:** the rebuttal is stronger, and it is cheap to test. But the Contrarian's underlying charge — that the audit reclassified an information-architecture failure as "edges" to protect the design — lands, and is worth holding onto.

**What would settle it:** ship a filing date in the existing `AVAILABLE` slot on the 3 most recent products for two weeks. If returning-visitor product views on those SKUs don't move, the Contrarian is right that the format, not the label, is the problem.

### CLASH 2 — Is the leaderboard a cheap win or a project?

**The Expansionist:** the single most valuable fact in the pack — a complete leaderboard component ships in `crooks.css` (`.crk-lb__row`, `.crk-lb__skel`, `.crk-lb__res--escaped`) and renders nowhere. A designed, tokenless, guardrail-clean retention surface sitting unused.

**Verified, and it is not unused.** `sections/crooks-case-file.liquid:34-38` renders it, and lines 25-28 document the decision explicitly: *"There is no Liquid-side source for live scores, so the only honest options are ruled empty rows or nothing at all. Placeholder scores are never rendered."* The schema offers `leaderboard: none | ruled empty rows`. It is currently set to hidden. **This is not an oversight — it is the same principle that rejected fake stock counters, applied consistently.** Loading it needs a public scores endpoint on Base44, CORS, a fetch layer, and identity linking between register email and game handle. That is a project priced as CSS.

**Chairman's read:** the Expansionist is **wrong on cost and right on direction.** The strategic claim — that game traffic currently exits to `base44.app` permanently and could instead become owned audience — is the best long-range idea the council produced. It is a Q4 project, not a Monday task.

### CLASH 3 — Is CHAIN OF CUSTODY fixable, or is the naming the position?

**The Outsider:** fixable, cheaply. Append the function to the label — `CHAIN OF CUSTODY — SHIPPING & RETURNS`. Same font, same caps, same zero radius. Nothing is diluted.

**The Contrarian:** the naming *is* the position. Calling it a "naming choice" is precisely how the audit avoids indicting the concept.

**Chairman's read:** side with the Outsider, because the evidence shows the fiction is decoration on a conventional spine everywhere else — `£60.00`, `SIZE XS S M L XL`, `IN STOCK`, `ADD TO BAG` are all plain English, and persona 1 passed every first-viewport test because of it. CHAIN OF CUSTODY is the one place the fiction was allowed to replace the plain word instead of sitting beside it. That makes it an inconsistency, not a position.

**What would settle it:** the label change is a one-line edit. Measure accordion open-rate before and after.

### CLASH 4 — Where should the first screen go?

**The Contrarian:** the homepage optimises for the persona who doesn't buy. `firstProductImage` on the homepage: **never**. First card at 1.22 viewports. The one persona the first screen serves perfectly has, by its own definition, no purchase intent.

**The Expansionist:** don't shrink the board — *load* it. METRICS §5 proves it costs nothing (60 fps, 0 fps off-screen/blur/reduced-motion). Put the payoff where the attention already is.

**Chairman's read:** genuinely unresolved, and the commercial data tilts it. 764 orders and £9.6k in July says the current homepage is not failing catastrophically. The board is also the single most defensible thing on the site. **Do not touch the board.** But the Executor's proposed reorder of `templates/index.json` is a no-op — verified, the order is already `hero → exhibit_log → case_file → manifest → informant → lookbook`, so manifest and informant are already above the lookbook. Lifting the register meaningfully means moving it above `crooks_case_file`, which is the thing persona 5 stays for. That trade is real and nobody in the council priced it.

**What would settle it:** the homepage is not where the money is being lost. Defer.

---

## Blind Spots the Council Caught

Emerged only through peer review, and each was verified:

**1. The popup breaks the brand's own rules.** `snippets/crack-the-cuffs.liquid` ships `border-radius: 8px` (line 37), `box-shadow: 0 24px 70px rgba(0,0,0,.55)` (38), `border-radius: 999px` (55), `border-radius: 6px` (70). Meanwhile `crooks.css:101` and `:428` enforce zero radius and no shadow everywhere else. **The one element that interrupts every persona is the only one violating the design system.** Removing or restyling it is therefore *consistent* with the brand position, not a compromise of it.

**2. `font-display: swap → block` does not fix the CLS, and the council mis-cited my own evidence.** The measured drop from 0.2327 to 0.0013 came from **blocking the vt323 request entirely** — the font never arrives, so it never swaps. With `block`, VT323 still lands at 1,836 ms and still reflows. **The actual root cause is a URL mismatch:** `layout/theme.liquid:31-36` preloads `{{ 'vt323.woff2' | asset_url }}` (emits `?v=…`) while `crooks.css:13` uses `url('vt323.woff2')` (no query), so the font downloads **twice** and the preload is wasted. Fix the preload URL first; then `font-display: optional` or a metric-matched fallback closes the residual shift.

**3. The `image-backups/` folder is a trap, not a shortcut.** A reviewer proposed the top performance fix was drag-and-drop because 16 PNG masters sit in the repo. They do — but `image-backups/README.md` states they are the **pre-cut-out, white-background originals**, kept before the 2026-07 background-removal pass. Re-uploading them would restore white boxes and undo the cut-out work that lets products sit on the bone ground. **The correct source is the current cut-out artwork re-saved as PNG.**

**4. Two claims about the cart were misattributed.** The cart's 4,024 KB and 3,440 ms blocking time are caused by `pay.google.com` (418 KB) and `paypal.com/buttons` (178 KB), not by Archivo Narrow — fonts on the cart total 159 KB. The typeface breach is a brand problem, not a performance one.

**5. Nobody addressed the WCAG failure.** Persona 6 records 200% zoom on mobile producing horizontal scroll (308 / 195) — a WCAG 2.1 AA §1.4.10 breach, with `.crk-status__msg` (`crooks.css:143`, `white-space: nowrap`) and `.crk-table` as the offenders. Five advisors, zero mentions. It is also the same declaration causing the 320 px overflow.

**6. Nobody asked for a number.** Which produced everything in the section at the top of this document.

---

## The Recommendation

**The aesthetic is earning its keep almost everywhere, and it is not where the money is going.**

Where it earns: the first viewport of the PDP (price, size, stock and a sticky ADD TO BAG all visible without scrolling — persona 1's every test passed); the catalogue register (persona 5: *"the numbering makes me want to see all fourteen"*); the measurement chart with its working CM/IN toggle (persona 3, the hardest sale, converts); the accessibility profile, which is *better* because of the constraints, not worse; and the canvas board, which is the best-engineered thing on the site.

Where it costs, and it is a short list: `CHAIN OF CUSTODY` as a label that hides the shipping copy; the absence of a recency signal in the register format; and — the only genuine indictment — the fact that a brand which deliberately removed every conventional trust fallback has left unfilled template placeholders (`[LINK TO REFUND POLICY]`, `[Crooksldn LTD] [Crooksldn@gmail.com] [TW200JW]`) in its live legal pages. **If you refuse the safety net, the plumbing has to be perfect.** That is the real obligation the design position creates, and it is currently unmet.

But the storefront is not the biggest problem, and the council could not have known that from the storefront. **£28k of proven-selling inventory is archived and invisible, three active products are overselling into negative stock while displaying "IN STOCK · Ships within 24 hours", and the #2 lifetime seller has three sizes gone with no capture.** No amount of LCP work competes with that.

**What must not change:** the canvas board and its three pause guards. The catalogue register and its numbering. The measurement table and unit toggle. The WITNESS STATEMENT and informant-register copy. The focus-ring system. The refusal to render fake leaderboard scores. The zero-radius/no-shadow enforcement. The no-JavaScript fallback.

---

## The One Thing to Do First

**Audit the inventory, not the interface.**

Turn `inventoryPolicy` from `CONTINUE` to `DENY` on 3 CLIVES TEE, MONEY CLIVE TEE and BROADCAST TEE, and reconcile their negative counts. Then decide, product by product, which of the nine archived items goes back on sale.

It is a Shopify admin task, it takes under an hour, it stops the store selling 49 units it does not have, it ends the refund leakage that made June negative, it makes the WITNESS STATEMENT true again — and it puts a five-figure quantity of proven-selling stock back in front of the traffic the brand is already paying to acquire.

Everything in `audit/BACKLOG.md` is worth doing. None of it is worth doing first.
