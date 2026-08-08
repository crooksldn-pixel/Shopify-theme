# AUDIT CONTEXT — CROOKSLDN

**This file exists to stop generic ecommerce advice.** Anything recommended here must be reasoned from the evidence pack in `audit/`, not from general knowledge about how online shops usually work. The design constraints below are decisions, not oversights, and the guardrail at the end is binding.

---

## 1. THE BRAND

CROOKSLDN is an independent streetwear label operating out of London. Short runs. When a run is gone it does not come back, and it is not restocked to order — this is stated on the homepage in the brand's own voice, not buried in a policy.

**Catalogue:** 14 products, £6–£60 (the original brief said thirteen; the staging catalogue has fourteen).

| Price | Products |
|---|---|
| £6 | BLACK/BLUE MOTIONTEC™ SOCKS · WHITE/RED MOTIONTEC™ SOCKS |
| £18 | LARGE DUFFLE BAG |
| £25 | 3 CLIVES TEE · BROADCAST TEE · MONEY CLIVE TEE · CRXST★RZ T-SHIRT |
| £45 | CHARCOAL CELLBLOCK SHORTS |
| £50 | BLUE WASH JORTS · GREY WASH JORTS · CHARCOAL CELLBLOCK CREWNECK |
| £60 | BLUE WASH OG JEANS · GREY WASH OG JEANS · V2 BAGGIES *(M, L, XL sold out)* |

**Vocabulary:** heist and incarceration. CELLBLOCK, MOTIONTEC™, CB1/CB2 wash codes, a recurring character called Clive. Products are "exhibits", the catalogue is a "case file", shipping is "CHAIN OF CUSTODY", the newsletter is the "informant register", the copyright line reads `EVIDENCE TERMINAL V0.2 // CROOKSLDN // OWN THE STREETS™`. Trademark line: **OWN THE STREETS™**.

**Traffic:** overwhelmingly Instagram and TikTok. Mobile, one-handed, young, often on cellular and often on an older phone. Mobile is not a secondary case; it is the case.

**Companion property:** `crooks-case-break.base44.app` — CASE 001: THE GETAWAY, a turn-based escape game. Scores are logged publicly. A pixel-art "attract mode" board from the same game runs on the storefront homepage, and a second mini-game (`CRACK THE CUFFS`) is served as a first-visit popup offering a discount code.

---

## 2. THE DESIGN SYSTEM, STATED AS CONSTRAINTS

The storefront is a fictional **police property store terminal**. Products are exhibits logged into evidence. The rules are deliberate:

| Rule | Implementation |
|---|---|
| **Zero border-radius** | no rounded corners anywhere in `crk-*` |
| **No gradients** | flat fills only |
| **No shadows** | borders and rules do the separation work |
| **Two typefaces** | `VT323` (bitmap display) and `CRX Mono` (monospace) |
| **Near-black ground** | `rgb(11, 10, 14)` dark / `rgb(244, 241, 234)` bone in light mode |
| **One accent** | purple `rgb(167, 122, 199)` |
| **Warning red reserved** | `--crk-red` for errors and sold-out only |
| **Minimal stepped motion** | no easing curves, no parallax |
| **Canvas pixel-art board** | homepage attract mode, carried over from the companion game |

There is a working light/dark toggle (`LIGHT MODE` in the header). Both modes are part of the system.

**Measured evidence that the system is well executed** (`evidence/METRICS.md`): 3 failing pairs out of 26 on the homepage — two of them the same 9 px `--crk-micro` token at 2.53:1 and 2.57:1, the third a transparent-text element needing eyeballing. Every other page has exactly one failure, the same token. A consistent 2 px purple focus ring at **5.88 : 1**. Zero unnamed interactive controls out of 35 on a product page. The canvas board holds 60 fps, drops to **0 fps** off-screen, on tab blur, and under `prefers-reduced-motion`. The shop is fully usable with JavaScript disabled.

---

## 3. WHAT WAS DELIBERATELY REJECTED, AND WHY

None of the following are absent by accident. The brand's entire proposition is that it does not look like a Shopify store.

- No trust badges
- No reviews widget
- No countdown timers
- No fake stock counters
- No "17 people are viewing this"
- No live chat
- No exit-intent popup
- No stock photography
- No models
- No rounded cards

**Confirmed by measurement on a product page:** `starRatings: 0` · `reviewBlocks: 0` · `urgency: false`. The rejection is real and consistently applied.

Instead, the brand does its trust work in **prose**, in its own register:

> *"CROOKSLDN is an independent label operating out of London. Everything is produced in short runs. When a run is gone it does not come back, and we do not restock it to order. Garments are cut for wear, not for display. If you need the fit explained, the size guide is on every product page. Own the streets."*
> — WITNESS STATEMENT, homepage. Signed `FILED BY THE PROPRIETOR. NO FURTHER COMMENT OFFERED.`

> *"01 LOGGED — Orders are logged same day. Dispatch within 24 hours, Monday to Saturday. 02 DISPATCHED — Shipped with Royal Mail Tracked. Free UK shipping on every order. 03 IN TRANSIT — Tracking issued by email. UK 1–2 working days. International 7–14 working days. 04 RELEASED — You have 14 days from delivery to return unworn goods with tags attached."*
> — CHAIN OF CUSTODY, every product page.

> *"Drops go to the register before they go public. One message per drop, nothing else. Unsubscribe at any time. We do not sell the register."*
> — REGISTER AS INFORMANT, homepage.

This is the substitute for conventional trust furniture, and on the evidence it is **good writing that is badly placed** (see §5).

---

## 4. THE COMMERCIAL REALITY

- 14 SKUs. Short runs that do not restock.
- **No reviews.** No press. No retail presence. No wholesale.
- Prices £6–£60. The margin products are the £45–£60 denim and sweats.
- Every sale is a **first-time buyer trusting a strange website with up to £60**.
- One product already has three of five sizes sold out, with no restock and no notify mechanism.
- Two contact addresses are in circulation: `info@crooksldn.com` (footer, product pages) and `crooksldn@gmail.com` (all four policy pages).
- Customer accounts are hosted on `friendsof.crooksldn.com`, unstyled.
- There is **no order-tracking entry point** anywhere on the site.

---

## 5. THE EVIDENCE, IN BRIEF

Full data in `evidence/METRICS.md` and the eight files in `journeys/`. The load-bearing numbers:

**Performance (390 × 844, Slow 4G, 4× CPU):**

| | Home | PDP tee | PDP denim | Cart |
|---|---|---|---|---|
| LCP | 4,432 ms | **13,876 ms** | 3,388 ms | 7,948 ms |
| CLS | 0.0017 | **0.2333** | **0.2327** | 0.0218 |
| Transfer | 3,103 KB | 2,591 KB | 1,936 KB | 4,024 KB |
| JavaScript | 1,168 KB | 1,169 KB | 1,171 KB | 1,463 KB |

Three root causes, each isolated:
1. **Masters uploaded with a `.webp` filename are never transcoded by Shopify's CDN.** A/B on one master: `…shorts.png` → 78 KB WebP; `cellcrew.webp` → 969 KB PNG. Eight files across six products. ~933 KB avoidable on the homepage alone.
2. **`vt323.woff2` downloads twice.** `theme.liquid:31-36` preloads `{{ 'vt323.woff2' | asset_url }}` (emits `?v=…`); `crooks.css:13` uses `url('vt323.woff2')` (no query). The preload is wasted; the real font lands at 1,836 ms, after FCP at 968 ms, and the swap reflows the buy panel **28 px upward**. Blocking VT323 drops PDP CLS from 0.2327 to 0.0013.
3. **1.17 MB of JavaScript on every page**, including a 166 KB `crack-cuff-codes.base44.app` bundle on product pages and the cart.

**Journeys — 3 of 8 personas abandon, and none abandons because of how the site looks:**

- **Sold-out sizes are a silent no-op.** `aria-disabled="true"` but `disabled === false`. Tapping L on V2 BAGGIES leaves the selection on XS with the buy button live; adding to cart returns `"variant_title":"XS"`. The panel says `IN STOCK` because the stock line reports the product, not the variant. No notify option.
- **Every trust link is unclickable on first visit.** Hit-testing with the cookie banner present (338 px, 40% of viewport, `z-index: 2000000`) shows SHIPPING, REFUNDS, CASE 001, INSTAGRAM, TIKTOK and EMAIL all blocked. A real click on REFUNDS times out; after Accept it navigates.
- **The legal pages contain unfilled template placeholders**: `[LINK TO REFUND POLICY]`, `[LINK TO PRIVACY POLICY]`, `[Crooksldn LTD] [Crooksldn@gmail.com] [TW200JW]`.
- **The measurements are placeholder data.** V2 BAGGIES (500 gsm cotton, "wide, full length") carries the identical waist/inseam/rise/hem table to 14 oz denim jeans; every column is a perfect arithmetic progression. **Both jorts have no table at all.** Only 5 of 14 products have measurements.
- **Four delivery claims on one product page**, two contradictory: `24HR DISPATCH AVAILABLE` / `Ships within 24 hours` / `UK 1–2 working days` / and in the description, `9-16 days delivery uk`.
- **The £60 jeans have one photograph each**, back view, `PHOTO 1 OF 1`.
- **The first-visit game popup fires on every template**, including product pages, 3 s after load, at 100% viewport with scroll locked.
- **The homepage's first full screen is the canvas board.** First product card at 1.22 viewports. CASE 001 at 2.6, WITNESS STATEMENT at 3.6, REGISTER AS INFORMANT at 4.6, socials at 5.9.
- **200% zoom on mobile causes horizontal scrolling** (308 / 195) — WCAG 2.1 AA §1.4.10 failure. Desktop passes.
- **No order tracking exists.** The account link lands on `friendsof.crooksldn.com` in Times New Roman on white.

**The pattern underneath all of it:** defects cluster almost entirely where CROOKSLDN's own design system stops and inherited Shopify Horizon components start. The cart (bone ground, Archivo Narrow — a third typeface — and Shop Pay purple / PayPal blue / Google Pay black), the policy pages, the collection filters, and the hosted login are where every persona flinched. The `crk-*` surfaces are consistently the best-built parts of the site.

---

## 6. THE TENSION TO BE EXAMINED

**The design is doing real brand work and may be doing real conversion damage. Both can be true simultaneously. That is the actual question.**

Where the evidence currently points — and what the council should pressure-test rather than accept:

- Persona 1 (cold Instagram click) read the aesthetic as deliberate within about a second, and the first viewport passed every one of their tests: price, size, stock and a persistent ADD TO BAG all visible without scrolling.
- Persona 5 (aimless browser) stayed *because* of the aesthetic and would plausibly follow.
- Persona 6 (accessibility) was *helped* by it: high contrast, no gradients washing out focus rings, one saturated accent making the focus indicator unusually visible.
- Persona 4 (the sceptic) abandoned — but on blocked links, bracketed placeholders and an empty contact page, not on the absence of reviews.

So the honest reading of the evidence is that **the concept is not the problem and the execution of the concept is not the problem; the problem is everything around the edges of it.** The council's job is to test whether that reading is right, or whether it is the audit being too kind to a striking piece of design work.

Specific questions worth arguing over:
1. Is spending the entire first screen of the homepage on an attract-mode animation defensible, when the first product card is at 1.22 viewports and every trust and retention hook is between 2.6 and 5.9 viewports down?
2. Is the in-fiction vocabulary (CHAIN OF CUSTODY for shipping, RELEASE REQUEST above the buy button, CASE 001 for the game) costing comprehension at the moments that matter — or is it the reason anyone remembers the brand?
3. With 14 SKUs and runs that sell out, is "make the shop convert better" even the right objective, versus "make the shop capture and hold an audience between drops"?
4. Does a brand that has deliberately refused conventional trust furniture have an *obligation* to be flawless on the plumbing — because it has removed every fallback signal a nervous buyer would otherwise use?

---

## 7. THE GUARDRAIL — BINDING

**Not acceptable as findings:**
- "Make it look more like a normal ecommerce site."
- "Add trust badges / a reviews widget / a countdown / social proof counters."
- "Soften the corners, warm up the palette, use a friendlier typeface."
- "Add lifestyle photography of models."
- Anything that would be recommended to any store without looking at this one.

**Wanted:**
- "This specific element is costing conversion, here is the evidence from persona N or metric X, and here is a fix that works inside the design language."
- "This constraint is defensible but the way it is implemented is not."
- "This is working and should be protected."
- "The concept is fine and the execution is the problem" — or the reverse.

**A constraint may be challenged if, and only if, the challenge is evidenced.** Cite a specific journey step or a specific measurement. A general preference for conventional design is not evidence. If an advisor genuinely believes the whole position is wrong, they must argue it from this evidence pack — and that argument is welcome.

**Every recommendation must be implementable without introducing:** a border-radius above 0 · a gradient · a shadow · a third typeface · a new accent colour.

---

## 8. ATTACHED EVIDENCE

```
audit/evidence/METRICS.md          Phase 1 — full instrumented evidence
audit/evidence/perf.json           per-page vitals, transfer, per-image detail
audit/evidence/image-formats.json  what each <img> actually received (magic bytes)
audit/evidence/image-ab.json       Accept-header A/B proving the .webp filename failure
audit/evidence/layout.json         scroll depth, tap targets, overflow, board fps
audit/evidence/a11y.json           contrast, axe, reduced motion, no-JS, zoom
audit/evidence/keyboard.json       corrected tab traversals with focus-ring contrast
audit/evidence/cls-taps.json       layout-shift sources with before/after rects
audit/evidence/catalogue.json      14 products, GBP, variants, descriptions
audit/evidence/checks.json         measurements, sold-out behaviour, delivery claims
audit/evidence/p2-fix.json         footer-vs-cookie-banner hit testing
audit/evidence/policy-text.json    bracketed placeholders, verbatim
audit/evidence/emails.json         contact-address usage per page

audit/journeys/01-cold-instagram-click.md      would buy, if they survive 25s
audit/journeys/02-returning-fan.md             WOULD LEAVE
audit/journeys/03-size-anxious-denim-buyer.md  would buy — strongest journey
audit/journeys/04-the-sceptic.md               WOULD LEAVE
audit/journeys/05-aimless-browser.md           would return, would follow
audit/journeys/06-accessibility-user.md        would buy; fails 200% zoom mobile
audit/journeys/07-slow-connection.md           continues, unsettled at the cart
audit/journeys/08-post-purchase.md             CANNOT TRACK AN ORDER AT ALL
audit/journeys/SUMMARY.md                      three worst moments, cross-persona

audit/screens/                     117 screenshots, named by persona and step
```
