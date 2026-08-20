# raw-cart-checkout — IN PROGRESS

Run interrupted by store-wide bot throttling (Cloudflare challenge, HTTP 429) at
16:08–16:18 while six other audit browsers were on the store. Findings below are
only those verified with a screenshot. This file is rewritten when the remaining
checks land.

### Empty cart page
**Should:** look like the same shop the shopper was just on.
**Did:** the chrome holds — near-black ground, mono type, status bar, CROOKSLDN
header, full footer. The middle of the page is stock Shopify: "Your cart is
empty", "Have an account? Log in to check out faster." and a filled purple
"Continue shopping" button, all in sentence case.
**Verdict:** partly
**Evidence:** audit/screens/cc-01-empty-cart.png, cc-01-empty-cart-full.png
