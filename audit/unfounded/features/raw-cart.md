# Feature sweep — Cart and the road to checkout (Unfounded Studios)

Live site https://www.unfoundedstudios.com, mobile 390x844 default, GB market
(note: the site geo-detects the audit egress IP as US and shows **USD** until
the market is switched — a UK shopper on UK IP sees GBP; all tests below pinned
to GB/£). Tested 2026-08-19. STRICT READ-ONLY observed: cart used freely,
checkout landing page reached and observed, nothing filled, no codes, no orders.

### Empty cart message & CTA
- **Should:** Tell me it's empty and point me somewhere useful.
- **Did:** `/cart` shows "IT'S A LITTLE *EMPTY* HERE — Your cart is currently
  empty" with a big "Start Shopping" button to `/collections`. Clear, on-brand,
  nicely typeset.
- **Verdict:** works
- **Screens:** uf-cart-01-empty

### Empty-cart recommendations ("You may also like")
- **Should:** If a recommendation section is shown, it should contain products
  and its links should work.
- **Did:** On the empty cart the "You may also like" heading and a "View All"
  pill render with **zero products** — just a blank white band above the
  footer. Worse, the View All link is literally `href="false"`: tapping it
  navigates to `/false` → "404 Not Found – Unfounded / Oops! We can't find
  what you're looking for here." The same `href="false"` View All also sits
  under the filled cart's recommendation row.
- **Verdict:** broken
- **Shopper impact:** The one tappable thing in the section dead-ends on a 404
  — a trust dent exactly where the store is trying to re-engage you.
- **Screens:** uf-cart-02-empty-recs, uf-cart-25-viewall-dest

### Add-to-cart feedback
- **Should:** Obvious confirmation that the item went in.
- **Did:** Added morocco-top £40 (size S) from the PDP. A cart **drawer slides
  in immediately**: "Your cart 1", line with photo thumbnail, MOROCCO TOP,
  £40.00, variant "S", quantity stepper, bin icon, "Subtotal £40.00 GBP",
  "Taxes included.", then a terms checkbox and View Cart / Checkout buttons.
  Header badge updates to "1". No page reload, no ambiguity.
- **Verdict:** works
- **Screens:** uf-cart-03-pdp-morocco, uf-cart-04-after-atc

### Cart line display (thumbnail, price, variant)
- **Should:** Each line identifiable at a glance.
- **Did:** Cart page shows a large product photo, name, unit price, variant
  (e.g. "XL", "XS"), quantity stepper with accessible labels ("Decrease
  quantity for Argentina Shorts"), bin icon, and line total. One oddity: the
  Italy Polo variant is displayed as "**XS - In Hand**" — stockroom jargon
  leaking into the shopper-facing variant name.
- **Verdict:** works
- **Screens:** uf-cart-05-cart3-top

### Quantity up / down with live totals
- **Should:** Steppers adjust quantity and the total stays right.
- **Did:** Built the 3-item cart: italy-polo £23 + portugal-polo £25 +
  argentina-shorts £18 = **Subtotal £66.00 — correct**. Italy + → qty 2,
  £89.00 (correct). + again → qty 3, £112.00 (correct). − back down → £89 →
  £66. Every step updated in place (AJAX), badge count tracked (3→4→5→…).
  Maths never slipped once across the whole session (incl. £48, £23, £106
  two-tab and £129 states).
- **Verdict:** works
- **Screens:** uf-cart-07-qty2, uf-cart-08-qty3-attempt

### Stock cap on quantity
- **Should:** Stop me (or warn me) when I ask for more than is in stock.
- **Did:** italy-polo is one of the last-units items in a store that is ~75%
  sold out, yet the cart accepted qty 3 of "XS - In Hand" with **no message,
  no cap, no stock hint** (£112 accepted). Whether stock actually covers 3
  is invisible to the shopper — nothing anywhere says how many are left.
- **Verdict:** partly
- **Shopper impact:** Risk of finding out at checkout/dispatch that the last
  size you fought for isn't really there in that quantity.
- **Screens:** uf-cart-08-qty3-attempt

### Remove item (minus at qty 1, and bin icon)
- **Should:** Both routes remove the line and re-total.
- **Did:** Minus at qty 1 on Argentina Shorts removed the line instantly
  (£66 → £48.00, badge 3→2, correct). Bin icon (`title="Delete"` link) on
  Portugal Polo removed it (£48 → £23.00, correct). No confirmation step in
  either case.
- **Verdict:** works
- **Screens:** uf-cart-12-minus-at-1-result, uf-cart-13-after-remove

### Undo after removal
- **Should:** A brief "removed — undo?" affordance, or at least a confirm.
- **Did:** Nothing. No undo, no toast, no confirm; the line is simply gone.
  One accidental tap on minus (at qty 1) silently deletes the item.
- **Verdict:** absent
- **Screens:** uf-cart-12-minus-at-1-result

### Interruption-free cart editing (newsletter popup)
- **Should:** Let me edit my cart without a modal landing on my thumbs.
- **Did:** ~10 seconds into the cart page (`data-delay="10"`), a bottom-sheet
  **"Sign up for our newsletter"** popup slides over the page, dims the cart
  and **blocks every control** — quantity buttons and bin icons were
  untappable until "NO THANKS" was pressed. In an automated pass it swallowed
  three consecutive taps; a human gets interrupted mid-edit exactly once per
  session. Dismiss works and it stays gone.
- **Verdict:** partly
- **Shopper impact:** Genuinely annoying placement — it fires while you are
  actively working the money page, not on entry or exit.
- **Screens:** uf-cart-09-minus-at-1 (taps blocked), uf-cart-11-newsletter-popup

### Free-shipping bar / threshold messaging
- **Should:** "£X away from free shipping" or similar, if a threshold exists.
- **Did:** Nothing anywhere — no announcement bar, no drawer meter, no cart
  message, no "free" mention on home, PDP, drawer or cart at all.
- **Verdict:** absent
- **Shopper impact:** Neutral-to-negative: no annoying meter, but also zero
  incentive signal and zero information about what delivery will cost.

### Upsell / cross-sell in the filled cart
- **Should:** Relevant, buyable suggestions that don't get in the way.
- **Did:** Below the filled cart, "You may also like" shows 5 product cards
  (Argentina Top £50, Spain Top, Germany Top, USA Top, Morocco Top £40 —
  all actually in stock, each "Available in 1 size") with one-tap "Add To
  Cart" buttons. Unobtrusive, at the bottom, genuinely purchasable — the
  best-curated shelf on the site given how much is sold out. Its "View All"
  pill, however, is the same `href="false"` → 404 as on the empty cart.
- **Verdict:** partly
- **Shopper impact:** Helps more than it annoys — sits below the summary and
  suggests only buyable stock — but the section's only navigation link 404s.
- **Screens:** uf-cart-06-cart3-bottom, uf-cart-25-viewall-dest

### Shipping cost findable BEFORE checkout
- **Should:** Cart, banner, PDP or policy page tells me delivery cost (or at
  least a starting rate) before I commit to checkout.
- **Did:** **Not findable at any number of taps.** The evidence trail:
  - Cart subtotal area says only "Taxes included." — the usual "shipping
    calculated at checkout" clause isn't even there.
  - PDP shows a marketing badge "FAST GLOBAL SHIPPING" — no price, no
    timescale.
  - Footer has Search / About us / Privacy Policy / Returns Policy — **no
    shipping link**; `/policies/shipping-policy` returns the store's 404
    ("Oops! We can't find what you're looking for here.").
  - The Returns Policy talks about "Original standard delivery charges" and
    "express or premium delivery" — so paid tiers exist — but never states
    a single figure.
  - Even the checkout landing page says "Enter your shipping address to view
    available shipping methods." Cost is revealed only after handing over an
    address (beyond this audit's stop line).
- **Verdict:** absent
- **Shopper impact:** A price-sensitive shopper cannot budget the order;
  "FAST GLOBAL SHIPPING" is a promise with no number behind it.
- **Screens:** uf-cart-14-shipping-policy, uf-cart-16-checkout-landing

### Discount-code field in the cart
- **Should:** A field in cart/drawer, or a clear pointer to where codes go.
- **Did:** No discount input anywhere in cart or drawer (0 matching fields;
  only quantity inputs, an Order note textarea, and the terms checkbox). The
  checkout landing page does have an "Add discount" control — codes exist,
  they're just invisible until checkout. (Observed only; nothing entered.)
- **Verdict:** absent
- **Screens:** uf-cart-26-mobile-summary, uf-cart-17-checkout-full

### Order note
- **Should:** Optional note field for the order.
- **Did:** "Order note" expander with a textarea (`name="note"`) sits under
  the subtotal. Present in cart page. (Not filled.)
- **Verdict:** works
- **Screens:** uf-cart-06-cart3-bottom

### Terms-of-sale gate before checkout
- **Should:** If a legal gate exists, it should be clear and not eat taps.
- **Did:** Both drawer and cart carry a required checkbox: "**Agree to terms
  of sale as per the merchants terms of service.**" (sic — "merchants").
  Tapping Checkout unticked keeps you on /cart with the browser-native
  message "Please check this box if you want to proceed." Tick it and
  Checkout proceeds instantly. The underlined "terms" links to the standard
  Shopify Terms of Service page (which exists). Note: the Shop Pay / G Pay
  wallet buttons sit *below* the Checkout button; whether they respect the
  gate was not tested (wallet sheets not opened under read-only rules).
- **Verdict:** works
- **Shopper impact:** An extra mandatory tap on the money path that most
  stores don't ask for; mildly off-brand grammar on a legal line.
- **Screens:** uf-cart-15-terms-gate, uf-cart-26-mobile-summary

### Express payment options before checkout
- **Should:** Wallet shortcuts where they help.
- **Did:** The cart page itself renders **Shop Pay and Google Pay** buttons
  (Shopify accelerated checkout) under the Checkout button — on mobile and
  desktop. Footer icon row advertises ~11 methods incl. Apple Pay, Visa,
  Mastercard, iDEAL/Wero, Bancontact, UnionPay. (Buttons observed, not
  tapped.)
- **Verdict:** works
- **Screens:** uf-cart-26-mobile-summary, uf-cart-23-zoom200-top

### Checkout landing page — brand hold
- **Should:** Reaching checkout shouldn't feel like leaving the shop.
- **Did:** Checkout is Shopify's standard one-page checkout at
  `/checkouts/cn/…`, titled "**Checkout - Unfounded**", with the Unfounded
  bird logo top-centre on the store's white/black palette. Order summary
  reads £66.00 — exactly matching the cart. "Express checkout" offers
  **Shop Pay** (purple) and **Google Pay** (black) above the OR divider;
  Contact ("Sign in" available), Delivery (Country pre-set to United
  Kingdom), Shipping method, Payment, and an "Add discount" control follow.
  It's recognisably stock Shopify in layout, but carries the brand cleanly.
  STOPPED here; nothing filled.
- **Verdict:** works
- **Screens:** uf-cart-16-checkout-landing, uf-cart-17-checkout-full

### Cart persistence — back, reload, two tabs
- **Should:** The cart survives leaving checkout, reloading, and stays
  consistent across tabs.
- **Did:** Browser-back from the checkout landing → cart intact (£66.00,
  badge 3). Reload → intact. Two tabs: tab B open on /cart (badge 3), added
  morocco-top in tab A (badge 4), reloaded B → badge 4, MOROCCO TOP present,
  subtotal £106.00 (66+40, correct).
- **Verdict:** works
- **Screens:** uf-cart-18-back-from-checkout, uf-cart-19-two-tab

### Landscape 844x390
- **Should:** Cart usable, nothing overlapping or unreachable.
- **Did:** No horizontal overflow, Checkout button reachable and uncovered.
  The add-to-cart drawer takes the right half; item list shows ~1 line at a
  time but subtotal, terms and both CTAs are all within the 390px height.
- **Verdict:** works
- **Screens:** uf-cart-20-landscape-top, uf-cart-21-landscape-checkoutbtn,
  uf-cart-22-landscape-drawer

### 200%-zoom-equivalent desktop (viewport 720x450)
- **Should:** Nothing overlaps; the money buttons stay reachable.
- **Did:** Clean single-column reflow, zero horizontal overflow, Checkout +
  Shop Pay + G Pay full-width and tappable, order-note expander intact.
- **Verdict:** works
- **Screens:** uf-cart-23-zoom200-top, uf-cart-24-zoom200-checkoutbtn

### Money-path consistency notes (exact quotes)
- PDP badge promises "**FAST GLOBAL SHIPPING**" while no shipping price or
  timescale exists anywhere pre-address; `/policies/shipping-policy` → 404.
- Returns Policy: "**Original standard delivery charges will be refunded
  where required by law. Any additional delivery costs, such as express or
  premium delivery, may not be refunded…**" — names delivery tiers the store
  never prices anywhere a shopper can see.
- Cart: "**Taxes included.**" with no shipping clause; checkout: "**Enter
  your shipping address to view available shipping methods.**"
- Geo-IP default shows USD (e.g. £23 polo listed at $32.00) until the
  country selector is used; UK-IP shoppers see GBP as expected.
- Cart variant label "**XS - In Hand**" (Italy Polo) is internal stock
  language on a customer receipt line.
