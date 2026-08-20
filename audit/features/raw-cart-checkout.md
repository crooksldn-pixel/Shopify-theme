# raw-cart-checkout — DRAFT IN PROGRESS

(Findings written as they are verified. Store-wide bot throttling — Cloudflare
429s while six other audit browsers were on the store — cost roughly 20 minutes
of this run; every claim below is from a request that returned 200 and has a
screenshot.)

### Cart page — what a shopper sees
**Should:** the same shop they were just on.
**Did:** the chrome is CROOKSLDN — near-black ground, mono type, status bar,
handcuff logo, `BAG [n]`, the carriage bar, the full footer. Everything between
the carriage bar and the footer is Horizon's stock cart with the terminal's
colours poured into it, and it still speaks Shopify's voice, in sentence case:
`Cart`, `Discount`, `Estimated total`, `Duties and taxes included. Shipping is
calculated at checkout.`, `Check out`. The site's own voice is uppercase mono
everywhere else (`ADD TO BAG`, `CATALOGUE`, `IN STOCK`).
**Verdict:** partly
**Evidence:** audit/screens/cc-40-cart-one-item.png

### Quantity up and down
**Should:** press +, the cart says two.
**Did:** works, and fast — within 1.5s the line total, `Cart total`, `Estimated
total` and the carriage bar had all moved from £60.00 to £120.00 and the bar's
message changed from `£10.00 to free Tracked 24` to `Free Tracked 24 —
unlocked`. Pressing − reverses it just as cleanly.
**Verdict:** works
**Evidence:** audit/screens/cc-41-qty-2.png, cc-63-plus-after-reload.png

### The header's BAG count after any cart change
**Should:** agree with the cart it is sitting above.
**Did:** it does not move until the page is reloaded. With the cart showing two
jeans and £120.00, the header still read `BAG [1]` — still `BAG [1]` nine and a
half seconds later. After a reload it read `BAG [2]`. Pressing − then left the
header reading `BAG [2]` over a one-item £60.00 cart, and removing the last line
left `BAG [2]` sitting over the words `Your cart is empty`.
**Verdict:** broken
**Shopper cost:** the two numbers on screen disagree about what you are buying.
**Evidence:** audit/screens/cc-69-removing-900ms.png — `BAG [2]` in the header,
`Your cart is empty` in the page.
