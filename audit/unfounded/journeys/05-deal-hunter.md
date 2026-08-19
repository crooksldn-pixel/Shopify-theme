# 05 — Marcus, 31, the deal hunter who never pays full price and doesn't believe your "sale" sign
**Device:** iPhone-class mobile 390x844, normal 4G · **Goal:** the homepage promised sales — find what's actually marked down, sniff out a signup discount, pay as little as possible · **Mood:** arrives suspicious by default; every "SALE" label is guilty until a strikethrough proves it innocent

*(Session note: audit egress geo-detects as US so first paints can render USD; sessions were pinned `?country=GB` — everything below is the GBP view a real UK shopper gets. One search run rendered "$35.00" before pinning; noted, not held against the store.)*

### Step 1 — Landed on the homepage and waited for the bribe
**Did:** Opened the homepage. Hero: "All Nation Items Available Now!" / "World Cup Drop Live!". Waited out the newsletter popup — deal hunters *want* the popup, that's where the "10% off your first order" usually lives.
**Got:** ~15 seconds in it slid up: "Sign up for our newsletter — Stay informed about new collections and discounts", email field, Subscribe, NO THANKS. That's it. No percentage, no welcome code, no "unlock X% off". (Read-only rule: nothing entered, nothing submitted — tapped NO THANKS.)
**Expected:** A concrete bribe. Every indie store popup on earth offers 10%.
**Felt:** "You interrupted me to promise… vague future 'discounts'? That's a no from me. Zero cost to you, zero value to me."
**Next:** continued (u05-01, u05-10, u05-02)

### Step 2 — Followed the SALE signs
**Did:** Scrolled "Our latest collections": three cards literally prefixed SALE — "SALE Black + Grey Items" (6), "SALE Nation Polo Sets" (10), "SALE Nation Items" (28). Also opened the burger menu looking for a Sale tab.
**Got:** The menu has no sale link at all — just Home / Shop all / Contact / England Set / Nations Shorts. The SALE-prefixed collections are only reachable from the homepage cards. Tapped into SALE Nation Polo Sets.
**Expected:** A sale section in the nav, and red prices behind it.
**Felt:** "Three shouty SALE cards but the menu's never heard of a sale. Fine, show me the markdowns."
**Next:** continued (u05-03, u05-04)

### Step 3 — Audited "SALE Nation Polo Sets" like a tax inspector
**Did:** Went card by card through all 10 products looking for strikethroughs / was-now prices.
**Got:** Not one. Italy Polo £23, France/Portugal Polo £25, track pants £30-£43 — every price a plain black number, no compare-at, no badge, and the banner over this "SALE" collection just says "Latest Drop". Same story in "SALE Black + Grey Items": six Bird items, no markdowns — and all six sold out anyway. Checked "SALE Nation Items" too: 29 products, zero compare-at prices. Even funnier, the product cards' own label reads "£40.00 REGULAR PRICE £40.00" — the theme announces the sale price IS the regular price.
**Expected:** A sale collection to contain at least one reduced item.
**Felt:** "So 'SALE' here is a word, not a price. 45-odd items across three SALE collections and not a single penny off anything. That word is doing marketing, not maths."
**Next:** continued, trust dropping (u05-08, u05-09, u05-14)

### Step 4 — Hunted the named events: Black Friday and End Of Month Sale
**Did:** Searched the store for "sale" and "black friday", then opened the collections directly (/collections/black-friday-discounted-items, /collections/end-of-month-sale).
**Got:** Search "sale" returns two *policy pages* (Returns Policy, "Do not sell or share my personal information") and no products; "black friday" returns "Oh no! No results found". The Black Friday Discounted Items page: "Showing 0 of 0 products — No products in this collection." End Of Month Sale: identical — empty, under the same recycled "Latest Drop" hero. It's the 19th of August; "End Of Month Sale" has nothing in it, and Black Friday is nine months away in either direction.
**Expected:** Dead events to be unpublished, not left up as empty husks.
**Felt:** "An empty Black Friday page in August is the shop-window equivalent of a 'CLOSING DOWN SALE' banner that's been up for three years. This is theme-setup debris, and it's public."
**Next:** continued (u05-23, u05-06, u05-07)

### Step 5 — The Germany Top that exists twice at two prices
**Did:** Searched "germany" — 7 results, including GERMANY TOP twice. Opened both.
**Got:** Same shirt, same photos, same name. One at **£50** (size XS, sold out). One at **£40** (size S, in stock — and its public URL ends in "-copy"). No explanation anywhere; both sit in the same "SALE Nation Items" collection a few rows apart. Also spotted: Spain Top twice (£50 sold out / £40 in stock), Germany Shorts twice (both £50, both sold out), Spain Shorts twice. The pattern is clear from the data: the £50 originals died, cheaper "-copy" relistings went up, and nobody deleted the originals.
**Expected:** One product, one price — or a visible "was £50, now £40".
**Felt:** "Which would I get? The £40 one, obviously — it's the only one you can actually buy. But that's not a discount, that's an accident I had to discover myself. And it tells me the £50 was never a real price wall — the same shirt quietly became £40. If prices are this loose, I trust none of them. Ironically the one search for 'discount' returns a single product — France Polo — which is also not discounted."
**Next:** continued (u05-11, u05-12, u05-13)

### Step 6 — Took the genuinely cheap thing: Argentina Shorts, £18
**Did:** The one price that needed no sale label: Argentina Shorts £18 when every sibling shorts is £50. Opened the PDP.
**Got:** £18, "Only 1 left in stock. Order soon", ship in 2-5 working days. Only XL is live — and bizarrely every size chip, including the buyable XL, carries the text "VARIANT SOLD OUT OR UNAVAILABLE". Two photos (product + a size-chart image). Added to cart — the drawer slid in: Argentina Shorts XL, £18.00, "Taxes included."
**Expected:** Cheapest item in the shop to be picked over — it is; one XL left.
**Felt:** "£18 against £50 siblings is a real deal, no badge needed. XL's a size up but at £18, baggy is a feature. The 'SOLD OUT OR UNAVAILABLE' sticker on a size I can literally buy is peak this-website though."
**Next:** continued (u05-15, u05-16)

### Step 7 — Hunted the discount field in the cart
**Did:** Checked the cart drawer, then the full cart page, for anywhere to enter a code.
**Got:** Nothing. Drawer: item, subtotal, terms tick-box, View Cart / Checkout — no code field. Cart page: an "Order note" accordion and the same terms checkbox — no discount field, no shipping estimate either; subtotal £18, "Taxes included." So even if that popup had given me a code, the cart offers nowhere to use it.
**Expected:** A discount/promo field at cart level, and ideally a shipping estimator.
**Felt:** "A store whose popup says 'discounts' but whose cart has no discount box. Everything about this shop's sale story is furniture."
**Next:** continued (u05-16, u05-17)

### Step 8 — Through the blocked door to checkout, and STOP
**Did:** Tapped Checkout. Nothing happened — a browser tooltip pointed at the small checkbox: "Please check this box if you want to proceed" ("Agree to terms of sale as per the merchants terms of service"). Ticked it, tapped Checkout again.
**Got:** Real Shopify checkout, Unfounded logo held, Order summary: Argentina Shorts XL £18.00 — and there, finally, a "Discount code / Apply" field (checkout only). Shipping: "Enter your shipping address to view available shipping methods" — so the true landed cost is unknowable until you hand over an address. Total: GBP £18.00 + mystery shipping. Express Shop Pay / Google Pay offered. Stopped here — nothing typed, no code tried, per the rules.
**Expected:** Checkout to have the code field (it does — Shopify default) and some hint of shipping cost before the address form (it doesn't).
**Felt:** "£18 in, £18 at the door, taxes included — the maths held. But I'm at the till and I still don't know if shipping is £3 or £8, which on an £18 item is the whole deal. And the code field finally exists — for the code nobody ever offered me."
**Next:** stopped at the checkout landing page with intent (u05-20, u05-21, u05-22)

## Outcome
**Bought / didn't:** "Bought" — took the £18 Argentina Shorts (XL, the last one) to the checkout landing page with real intent and stopped there per the audit rules. It was the only item in the shop that felt like an actual deal — and it carried no sale label at all.
**Total time:** ~13 minutes, most of it spent proving a negative.
**Worst moment:** Opening "Black Friday Discounted Items" in August and finding "Showing 0 of 0 products" — after three homepage "SALE" collections had already yielded 45 products with zero markdowns between them (not one compare-at/strikethrough anywhere in the store's own price data).
**Best moment:** The £18 Argentina Shorts next to £50 siblings — a genuine bargain — and a checkout whose total stayed an honest £18.00 with taxes included.
**Would they come back?** Only via a price-tracker or a genuinely advertised markdown, and they'd screenshot the price first. The "SALE" labels made this shopper trust the store *less*, not more: sale-titled collections with no discounts, empty seasonal sale pages, and the same shirt listed twice at £50 and £40 read as a shop that uses "sale" as decoration and manages prices by accident. The store neither rewards nor punishes a bargain hunter — it simply wastes their time: the real deals (£18 shorts, £23 polo, the £40 "-copy" relistings) are unlabelled, while everything labelled is a dead end.
**One thing that would have changed the outcome:** Make one honest markdown exist: put real compare-at "was" prices behind the SALE labels (and delete the empty Black Friday/End-of-Month collections and the £50 duplicate listings). Failing that, a popup that actually offers a % code — plus a cart-level field to redeem it — would have captured this shopper's email in five seconds.
