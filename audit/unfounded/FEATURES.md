# FEATURES.md — Unfounded Studios: the feature surface, worked as a shopper

Run 2026-08-19 against the LIVE site https://www.unfoundedstudios.com (Shopify,
en-GB, GBP; "Unfounded Limited", VAT GB 514170427). Same battery as the
CROOKSLDN staging audit, with a stricter scope for a third-party store:
**strict read-only** — no form submitted anywhere, no discount codes, no
checkout fields, sessions stopped at the checkout landing page. Site identity
verified per session. Detail per item in `features/raw-*.md`; journeys in
`journeys/`; screenshots in `screens/`.

**Context that frames everything:** 44 products, £18–£50 — and **only 12 have
any purchasable variant**. The flagship "Bird" line (the TikTok-known
products) is 0-available across every size *including all pre-order slots*.
At audit time not one size-M variant was purchasable in the entire store.

---

## What is broken

| # | Broken thing | What a shopper hits | Evidence |
|---|---|---|---|
| U-B1 | **No back-in-stock/notify mechanism exists anywhere** on a store where 73% of the catalogue is dead. Sold-out PDPs offer a greyed Sold Out button — beside a fully-lit purple "Buy with shop" button and a "MORE PAYMENT OPTIONS" link that both silently do nothing. | Warm leads (01, 06) hunt for anywhere to leave an email and are never offered it; the dead-but-lit buttons "teach you to distrust every button on the site" (11). | raw-pdp, journeys 01/06/11 |
| U-B2 | **"Only 0 left in stock. Order soon."** renders on the fully sold-out flagship hoodie. | Urgency furniture contradicting itself on the store's most-wanted product. | raw-pdp |
| U-B3 | **Product descriptions contain zero product information.** Every PDP body is a single dispatch line ("Please Allow 2-5 Working Days…"), and those lead times contradict between products (2-5 vs 5-7 days) with no shipping policy to arbitrate — `/policies/shipping-policy` is a **404**. | No fabric, fit, care, origin, or colour text anywhere — on a brand whose Google meta claims "heavyweight… 100% Organic Cotton" (a claim that appears nowhere on the site itself). | raw-pdp, raw-home-trust |
| U-B4 | **Shipping cost is unknowable before surrendering a full address.** No price in drawer, cart, footer, PDP or checkout landing; the policy page 404s. | Nearly flipped an £18 impulse decision (07); a £94 basket reached the door with unknowable postage (08). | raw-cart, journeys 07/08 |
| U-B5 | **Empty and misleading sale machinery.** "Black Friday Discounted Items" and "End Of Month Sale" are live-but-EMPTY collections in August; three SALE-titled collections (45 products) contain **zero** actual discounts (no compare-at prices site-wide); the homepage carousel promotes "Nations Shorts" — also empty. | The deal hunter concluded the SALE labels "lowered trust rather than raised it" (05); the homepage-trusting impulse shopper hits a wall (07). | raw-home-trust, journeys 05/07 |
| U-B6 | **Duplicate live products at different prices.** Germany Top £50 (sold out) vs public `germany-top-copy` £40 (in stock); Spain Top £50/£40; twin Germany and Spain Shorts. | "Reads as relist-cheaper-and-forget, torching price credibility" (05); trust-denting for the gift buyer (09). | raw-home-trust, journeys 05/09 |
| U-B7 | **"Follow Us" on the homepage links to the theme developer's Instagram (@digifist)**, not the brand. | The one social-proof pointer on the homepage goes to a stranger. | raw-home-trust |
| U-B8 | **Hidden "VARIANT SOLD OUT OR UNAVAILABLE" text is attached to EVERY size, including in-stock ones.** | A screen-reader user is told her size is simultaneously available and unavailable (16, verified in the accessibility tree). | raw-edge, journey 16 |
| U-B9 | **The newsletter popup is a broken modal**: aria-labelledby points at a non-existent id (no accessible name), focus never moves in, Escape is ignored, its controls are tab stops 80–82 of 87 (68 presses to dismiss, Subscribe one stop before NO THANKS), it fires ~10-15s in on whatever you're doing — over the search results being tapped (07), over the PDP buy box mid-read (14), stacked ON TOP of the open cart drawer (15, 16) — and re-arrives on every page until formally dismissed. | The single most-complained-about object across their journeys — structurally the same villain as CROOKSLDN's popup, worse in accessibility, milder in payload (no data toll, no broken prize). | raw-edge, journeys 07/14/15/16 |
| U-B10 | **Cart "You may also like → View All" is `href="false"`** → lands on /false, a 404. Empty-cart version renders zero products around the dead button. | A 404 wired into the money page. | raw-cart |
| U-B11 | **Reduced motion is at least partly ignored** (edge sweep: hero autoplays under the setting; tinkerer saw otherwise — persona 18 arbitrates; final verdict in its journey). | Vestibular users get animation they asked not to have. | raw-edge, journey 18 |
| U-B12 | **JS-off shoppers silently get the default variant** — the ticked size never syncs to the hidden input, so any size choice adds the wrong size. | Silent wrong-size orders for the no-JS cohort. | raw-edge |
| U-B13 | **The cart page's order-note field is unwired** — typed text never persists to the cart. | Decorative furniture on the money page (11). | journey 11 |

## Expected and missing

- **Any size guidance for tops/hoodies.** A real measurements chart EXISTS —
  but only as an unlabelled, alt-less final gallery image on *some* bottoms
  (track pants, shorts). Nothing for hoodies or nation tops; `/pages/size-guide`
  404s; search can't find it. The store did the work, then buried it (03).
- **A gift card** — search returns only the returns policy's disclaimer for
  "gift cards, if offered" — a disclaimer for a product that doesn't exist (09).
- **A contact email in print** — the Contact page has hours + a form but no
  address; `info@unfoundedstudios.com` appears only inside the returns policy.
- **Typeahead on the standalone /search page** (the header drawer HAS full
  predictive search — the page greets you with "Oh no! No results found."
  before you've typed).
- **Any explanation of drops/restocks**, pre-order semantics ("XS - In Hand" /
  "XS - Pre order" warehouse jargon leaks into size pills, cart lines and
  checkout), or the price gaps between identical-looking colourways
  (Bird shorts black £30 vs grey £27, unexplained).
- **A "notify me" — see U-B1.** The one email-capture mechanism (newsletter
  popup) promises "new collections and discounts", not restocks.

## What genuinely works — the fair ledger

1. **Photography and zoom where they bothered**: the flagship hoodie carries
   5–11 real photos including on-model street shots, and the lightbox's
   double-tap zoom serves the true 4284×5712 original — a shopper really can
   judge the fleece. (The catch: the *buyable* products are the
   worst-photographed — Morocco Top has exactly one flat-lay.)
2. **Add-to-cart feedback is excellent**: branded cart drawer slides in ~1.5s
   even on slow 4G with thumbnail, size, stepper and running subtotal; badge
   updates; quick-add "+" on cards and in search results.
3. **Cart maths is bulletproof**: nine subtotal states through adds, swaps and
   removals, penny-perfect at the checkout door (£94.00 = £94.00); honest
   stock-cap message when qty exceeded stock (with one cosmetic stepper desync).
4. **Checkout holds the brand**: bird logo, black/white palette, Shop Pay +
   Google Pay, UK pre-set — where CROOKSLDN's drops to a stock white skin.
5. **Honest SOLD OUT badges on collection/search cards** — you know before
   the click (though "Available in 5 size" chips on in-stock cards count
   variants that *exist*, not variants you can buy).
6. **The in-stock filter is flawless** — 44 dead-heavy products collapse to
   exactly the buyable 12, with removable chips and shareable URLs (11 called
   it the best control on the site).
7. **The returns policy is genuinely written and self-consistent**: 14+14
   days, a named Surrey return address, who-pays stated, both copies agree.
   Persona 12 reached it from search in 2 taps.
8. **Real legitimacy markers**: Companies House-registered "Unfounded
   Limited", VAT number in the footer, a sincere founder story on About.
9. **Keyboard and zoom fundamentals**: skip link, visible focus rings, a
   textbook cart-drawer focus trap, arrow keys that skip dead sizes, zero
   horizontal scroll at 200% and landscape.
10. **Slow-4G image pipeline**: stable above-fold, progressive images — though
    the page is *wordless* for 8–10s because text waits for JS entrance
    animations.
