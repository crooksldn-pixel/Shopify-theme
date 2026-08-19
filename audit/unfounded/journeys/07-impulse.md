# 07 — Jamie, the impulse buy with £20 burning a hole
**Device:** iPhone-class mobile 390x844, normal 4G, one thumb, on the sofa half-watching the football · **Goal:** heard this brand does cheap football gear — wants the £18 Argentina shorts, in and out, tonight · **Mood:** decisive, impatient, budget hard-capped at about £20

*(Session note: the audit egress IP geo-detects as US and shows USD; the session was pinned with `?country=GB` as a real UK visitor would see it. Everything below is the GBP view. Tap count = physical screen taps; typing counted separately.)*

### Step 1 — Landed on the homepage and clocked the routes
**Did:** Opened unfoundedstudios.com. Loaded in ~4 seconds: black header with a bird logo, burger, search, account, bag; full-bleed "World Cup Drop Live! / Shop Now" hero; below it "Our latest collections" as a sideways-swiping carousel — first tile "England Set", with a "Nations Shorts" tile hanging half off the right edge of the screen.
**Got:** No prices anywhere above the fold, no sale bar, no "free shipping over £X" banner — actually no mention of shipping anywhere on the whole homepage (checked top to bottom).
**Expected:** Something like "FREE UK SHIPPING OVER £40" in an announcement bar — most shops my age group buys from have one.
**Felt:** "Shorts are probably under that Nations Shorts tile… but I'd have to swipe for it. Nah — I know what I want. Search."
**Next:** continued (u07-01, u07-06)

### Step 2 — TAP 1: search, typed "argentina" — and it just… worked
**Did:** Tapped the magnifier in the header (TAP 1, ~4s in). Search drawer opened instantly with the keyboard up. Typed "argentina" (9 keystrokes).
**Got:** Live results before I'd finished typing: ARGENTINA SHORTS £18.00 with a proper product photo and a black "+" quick-add button on the card, next to ARGENTINA TOP £50.00. Card says "Available in 5 size". Underneath, though: a COLLECTIONS section listing "Portugal Argentina Shorts 0" and "Portugal Argentina Tops 0" — two collections with literally zero items, decorated with a handbag clip-art icon. On a football brand.
**Expected:** A search box that finds the thing. It did — faster than most big retailers.
**Felt:** "There it is, £18, first result, and I can add it right off the card. Quality. (What's with the empty handbag collections though?)"
**Next:** continued (u07-04, u07-05)

### Step 3 — TAP 2: the newsletter popup landed on top of my search
**Did:** Was reaching for the "+" when, ~10 seconds into the visit, a "Sign up for our newsletter — Stay informed about new collections and discounts" sheet slid up over the bottom half of the SEARCH RESULTS, dimming the exact card I was about to tap.
**Got:** Email field + Subscribe + small underlined "NO THANKS". Tapped NO THANKS (TAP 2). It closed and stayed gone. (Read-only rule: nothing entered.)
**Expected:** To be left alone for the first sixty seconds of my first visit, especially mid-search.
**Felt:** "I'm literally trying to give you £18 and you body-block me for an email address."
**Next:** continued, mildly annoyed (u07-10)

### Step 4 — TAPS 3–5: quick-add, dodge the dead sizes, in the cart
**Did:** Tapped the "+" on the Argentina Shorts card (TAP 3). A "Choose options" bottom sheet slid up: big photo (and — nice — a size-chart image with inch measurements for Waist/Length/Leg Opening sitting right there in the sheet's photo slider), ARGENTINA SHORTS £18.00, SIZE row.
**Got:** The sheet opens with SIZE XS pre-selected — and XS is struck through, sold out, as are S, M and L. Four of five sizes are crossed-out decoys; the card's "Available in 5 size" was a lie, it's XL or nothing. The ADD TO CART button under the dead pre-selected XS still looks fully active, with a purple "Buy with shop" under it. Tapped XL (TAP 4) — the only live chip — then ADD TO CART (TAP 5). Cart drawer slid in immediately: "Your cart 1", ARGENTINA SHORTS, £18.00, XL, quantity stepper, Subtotal £18.00 GBP, "Taxes included."
**Expected:** Five sizes as advertised; at minimum, don't pre-select a sold-out size above a live-looking buy button.
**Felt:** "Lucky I'm alright with an XL in an elastic-waist short. If I were an M that's the whole trip dead. And it opened on a sold-out size with a working-looking button — one lazy tap and who knows what I'd have added."
**Next:** continued (u07-11, u07-12, u07-13)

### Step 5 — Hunted for the delivery cost before committing — nothing
**Did:** £18 shorts, ~£20 in the account. Before checkout I wanted the shipping number. Scanned the drawer: "Taxes included." — not even the standard "shipping calculated at checkout" line. No free-shipping meter, no threshold message, no "spend £X more" nudge anywhere in the session. Earlier, homepage: zero shipping mentions; the footer has no shipping-policy link at all.
**Got:** The delivery cost does not exist anywhere a shopper can reach before checkout. The only shipping words I'd seen all visit were the PDP badge "FAST GLOBAL SHIPPING" — a promise with no number.
**Expected:** "UK delivery £3.95" on the PDP, the cart, a policy page — anywhere. At £18 the postage could be 25% of the price.
**Felt:** "This is the one number that decides whether I'm under budget, and you won't tell me. Also — you've got my £18; there's no 'free shipping over £30' or anything tempting me to make it £41. Fine. Suppose I have to walk into checkout just to find out."
**Next:** hesitated, then continued — to get the number, not because I'd decided (u07-13, u07-14)

### Step 6 — TAPS 6–7: the terms toll-booth, then the checkout door
**Did:** In the drawer, a required checkbox: "Agree to terms of sale as per the merchants terms of service." (their apostrophe, not mine). Ticked it (TAP 6) — you can't proceed without it. Tapped Checkout (TAP 7).
**Got:** Shopify checkout, "Checkout - Unfounded", bird logo, Order summary £18.00, Express checkout Shop Pay / Google Pay, Contact with Sign in, Delivery pre-set to United Kingdom. And the answer to my question: "Shipping method — **Enter your shipping address to view available shipping methods.**" The price is behind a full address form. STOPPED HERE — nothing filled, per audit rules.
**Expected:** Checkout, one tap, no homework. The extra legal checkbox is a tap most shops don't charge, and the shipping number is still being withheld at the door.
**Felt:** "Seven taps and about a minute and a half — genuinely quick, credit where due. But I'm standing at the till and still don't know if this costs £18 or £24. In character, on the sofa: I'd probably grind through the address form because it's only £18 — but if shipping comes back over about £2.50 I'm abandoning at the shipping-method step, and this shop has no idea how close it came."
**Next:** stopped at the checkout landing (audit line) with intent alive but hostage to an unpriced delivery fee (u07-15)

### Epilogue — the route the homepage actually advertises (verified after the run)
The "Nations Shorts" tile Jamie skipped in Step 1: on one attempt the tap was swallowed outright by the newsletter popup sitting over it; when the collection is reached directly, it's titled "Shorts" over a gorgeous three-lads-on-an-estate hero photo — then "Showing 0 of 0 products. **No products in this collection**." The homepage carousel promotes an empty shelf while the store's cheapest live product, these £18 shorts, is findable only by search or the buried all-products grid. An impulse shopper who trusts the homepage navigation instead of the search box hits a wall and likely bounces. (u07-07, u07-16, u07-17)

## Outcome
**Bought / didn't:** Reached the checkout landing page with the £18 Argentina Shorts (XL) in the cart and genuine intent — conditional on a shipping fee the store refused to reveal at any earlier point. (Audit stop line; nothing entered.)
**Total time:** Fastest path landing → checkout door: **7 taps + 9 keystrokes, ~90 seconds**. With the shipping-cost hunt and dithering, ~3 minutes total.
**Worst moment:** A dead heat: the newsletter popup sliding over the search results ~10 seconds in, directly on top of the product being tapped; and reaching the checkout door still not knowing the delivery cost on an £18 order — "Enter your shipping address to view available shipping methods."
**Best moment:** The search flow: magnifier → "argentina" → photo, £18.00 and a quick-add "+" on the first result, with a size-chart image right inside the quick-add sheet. Landing to cart in 5 taps is genuinely elite for an indie store.
**Would they come back?** Yes, when the algorithm reminds them — the shorts are good value and the path is fast — but Jamie will arrive as a search-only user who ignores the homepage (its carousel points at an empty collection) and braces for the popup. If the eventual shipping fee had felt like a sting, no.
**One thing that would have changed the outcome:** A visible UK delivery price (or any free-shipping threshold) anywhere before checkout — one line in the cart drawer would have turned a conditional walk to the till into a done deal, and a "free shipping over £X" nudge might have upsold the second £20.
