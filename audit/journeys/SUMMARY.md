# PHASE 2 — PERSONA JOURNEYS: SUMMARY

Eight scripted walkthroughs on the CROOKSLDN staging theme, 390 × 844 at Slow 4G with 4× CPU throttle (persona 7 at 360 × 800 / 6× CPU), personas 1, 3 and 6 repeated at 1440 × 900. Every run started from a cold browser with the first-visit popup flag cleared.

---

## Outcome by persona

| # | Persona | Outcome | Taps | Blocked by |
|---|---|---|---|---|
| 1 | Cold Instagram click | **Would buy, if they survive 25 s** | 3 | 14.3 s LCP · game popup on a PDP · cookie banner over the buy bar |
| 2 | Returning fan | **Would leave** | 3 | No new-arrival signal · tapping a sold-out size silently keeps the old size |
| 3 | Size-anxious denim buyer | **Would buy** | 3 | Placeholder measurements · 1 photo · return postage unstated |
| 4 | The sceptic | **Would leave** | 3 | Every trust link unclickable on first visit · `[LINK TO REFUND POLICY]` placeholders · contact page with no contact details |
| 5 | Aimless browser | **Would return, would follow** | 1 | Every return-hook is 2.6–5.9 viewports down |
| 6 | Accessibility user | **Would buy; fails at 200% zoom on mobile** | 1 | WCAG 1.4.10 reflow failure (308 / 195) |
| 7 | Slow connection | **Would continue, unsettled at the cart** | 3 | 13.3 s to open the cart · INP 944 ms · cart breaks the design language |
| 8 | Post-purchase | **Cannot track an order at all** | 3 | No tracking entry point · unstyled `friendsof.crooksldn.com` login |

**3 of 8 would leave or fail. None of the three leaves because of how the site looks.**

---

## The three worst moments across all personas

### 1. Persona 2 — tapping a sold-out size silently sells you the wrong one

On V2 BAGGIES (M, L and XL sold out), the unavailable sizes are correctly struck through and dimmed. But they carry `aria-disabled="true"` while `disabled === false`. Tapping L produces **no feedback of any kind** — no message, no state change — and the selection **stays on XS**. The sticky bar still reads `V2 BAGGIES £60.00 · XS`, the buy button stays enabled, and adding to cart in that state returns `"variant_title":"XS"`. Meanwhile the panel says `IN STOCK` and `In stock · Ships within 24 hours`, because the stock line reports the product rather than the selected variant. There is no restock or notify option anywhere.

This is the worst finding in the audit because it does not merely lose a sale — it produces a wrong-size order, a refund, and a first-time buyer who now distrusts the brand. The design system already reserves warning red for "errors and sold-out only", and that red is not currently used for this.

### 2. Persona 4 — every trust link on the site is physically unclickable on first visit

With the cookie banner present (338 px, 40% of the viewport, `z-index: 2000000`, fixed), `elementFromPoint` at the centre of each footer link returns the banner. **SHIPPING, REFUNDS, CASE 001, INSTAGRAM, TIKTOK and EMAIL are all blocked.** A real Playwright click on REFUNDS times out and does not navigate; after clicking Accept, the identical click navigates immediately. The one email address on the site sits 5.88 viewports down and never appears as readable text.

Compounding it, the legal pages contain unfilled template placeholders in the live text — `[LINK TO REFUND POLICY]`, `[LINK TO PRIVACY POLICY]`, `[Crooksldn LTD] [Crooksldn@gmail.com] [TW200JW]` — and route customers to a **Gmail address that contradicts the footer's `info@crooksldn.com`**. The contact page is a bare form with no address, no email, no response time.

For the one persona whose entire job is deciding whether this is a real business, every single verification path is either blocked, bracketed, or empty.

### 3. Persona 1 — 14.3 seconds to see the product, then a game over the top of it

The 3 CLIVES TEE hero is a **635 KB PNG** — the largest asset on the site — because its master was uploaded as `9dbaee36…_webp.webp`, and Shopify's CDN will not transcode a file whose name ends in `.webp`. LCP 14,252 ms. Then at 3 seconds the `CRACK THE CUFFS` overlay covers 100% of the viewport at `z-index: 2147483647` and locks scroll — and because it is rendered in `layout/theme.liquid`, **it fires on product pages, not just the homepage**. Underneath it, the cookie banner covers the sticky ADD TO BAG bar. CLS on this journey measured **0.353**.

Three interruptions stacked on top of a shopper who arrived with intent, in the first twenty-five seconds.

---

## What the journeys agreed on

**The austere design is not what loses the sales.** Across eight personas, not one abandonment was caused by the near-black ground, the zero border-radius, the monospace type, the absence of reviews, or the terminal fiction. Persona 1 read the aesthetic as deliberate within about a second. Persona 5 stayed because of it. Persona 6 was *helped* by it — high contrast, no gradients, a single saturated accent that makes the 2 px purple focus ring unusually visible at 5.88 : 1.

Every abandonment traced to one of four things: **load weight, overlays, missing product data, or the parts of the theme that were never brought into the design system.**

**The content is better than its placement.** CHAIN OF CUSTODY answers courier, dispatch, delivery and returns better than any trust badge — and it is collapsed, 1.7 viewports down, behind a label that does not contain the word "shipping". The WITNESS STATEMENT explains the entire commercial model in four sentences — at 3.6 viewports. REGISTER AS INFORMANT is the best-written email capture on the site — at 4.6 viewports. The homepage spends its first full screen on an attract-mode animation and its persuasive material four screens below.

**Quality drops precisely where CROOKSLDN stops and Shopify Horizon starts.** The cart (bone background, Archivo Narrow, wallet buttons in blue/yellow/black), the policy pages (Archivo Narrow), the collection filters, and the `friendsof.crooksldn.com` login (Times New Roman on white) are where every persona flinched. The `crk-*` surfaces are consistently well built.

**Two contradictions a shopper can find unaided.** On the BLUE WASH OG JEANS page: `24HR DISPATCH AVAILABLE`, `Ships within 24 hours`, `UK 1–2 working days` — and, in the product description, `9-16 days delivery uk`. And V2 BAGGIES carries a measurement table copied from the denim while its own description gives height-based sizing.

---

## Corrections made during Phase 2

Recorded because they changed conclusions:

- **The "keyboard trap on every page" is not real.** It is `iframe#PBarNextFrame`, the Shopify preview bar, which exists only in the share-preview session.
- **Sold-out sizes *are* visually marked** (line-through + dimmed). An earlier check that read only `className` missed it. The defect is the silent no-op on tap, not the styling.
- **The CM/IN toggle works correctly** (38 cm → 15 in). An earlier null result was a regex error in the harness.
- **SIZE GUIDE lands correctly** — it scrolls 1,230 px and puts the MEASUREMENTS heading at y = 0.
- **The cart's checkout focus ring is visible** (`outline-offset: 2px` puts a near-black ring on the bone ground at 17.55 : 1), not invisible as first measured.

---

## Files

```
audit/journeys/01-cold-instagram-click.md
audit/journeys/02-returning-fan.md
audit/journeys/03-size-anxious-denim-buyer.md
audit/journeys/04-the-sceptic.md
audit/journeys/05-aimless-browser.md
audit/journeys/06-accessibility-user.md
audit/journeys/07-slow-connection.md
audit/journeys/08-post-purchase.md

audit/evidence/journeys-1-5.json   step-by-step captured facts
audit/evidence/journeys-6-8.json
audit/evidence/recon.json          PDP anatomy, menu, footer, content pages
audit/evidence/checks.json         measurements, sold-out behaviour, delivery claims
audit/evidence/p2-fix.json         footer-vs-cookie-banner hit testing
audit/evidence/policy-text.json    bracketed placeholders, verbatim
audit/evidence/emails.json         contact-address usage per page
audit/screens/p1-step1.png …       every step, every persona
```
