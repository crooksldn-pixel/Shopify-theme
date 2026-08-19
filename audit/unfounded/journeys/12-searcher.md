# 12 — Priya, the searcher who refuses to hunt menus — if search can't answer it, the site doesn't know it
**Device:** iPhone-class mobile 390x844, normal network · **Goal:** about to order a football polo for the first time; wants the returns policy, delivery time/cost, size info and a contact route — and will ONLY use the search bar to find them · **Mood:** businesslike, mildly stubborn: "every shop hides this stuff in different menus; search is the same everywhere"

*(Tap-count convention: taps counted from the moment she goes for search — search icon = tap 1, the keyboard's search/enter key = a tap, each result/link tapped = a tap. Typing itself isn't counted. Session pinned `?country=GB` like the rest of the audit.)*

### Step 1 — Found the search, and it behaved
**Did:** Landed on the homepage, swatted away the newsletter popup ("NO THANKS" — nothing entered), and tapped the magnifier in the black header.
**Got:** A clean search drawer slid down over the top of the page: big "Search for..." input, already focused so the keyboard is instantly ready, an X to close. No trending/popular suggestions until you type.
**Expected:** Exactly this.
**Felt:** "Good start. Cursor's already in the box — someone thought about this."
**Next:** continued (u12-01-home, u12-02-search-open)

### Step 2 — "returns": the dream version of site search
**Did:** Typed `returns`.
**Got:** While typing, a panel appeared: "POPULAR SEARCHES — Returns Policy" with the page linked, plus "View Results For 'Returns'". Tapped the suggestion — straight onto /pages/returns-policy. A real, thorough, human-written policy: 14 days to notify from delivery + 14 more to send back, condition rules, how to start (email info@unfoundedstudios.com with order number), a full Surrey return address, customer pays return postage unless faulty, refunds within 14 days of receipt, no automatic exchanges, sale items returnable. Pressing Enter instead also works: results page shows exactly one hit, a tidy "PAGE — Returns Policy — VIEW PAGE" card.
**Expected:** Some hit buried under products, if anything.
**Felt:** "Two taps and I'm reading the actual policy. And it's a proper policy — dates, address, who pays postage. This is the best answer this query has ever given me on an indie shop." (Small snort at the results page calling it "Showing 1 of 1 products" — a page is not a product, but fine.)
**Next:** continued, impressed (u12-typed-returns, u12-results-returns, u12-returns-policy) — **2 taps to answer**

### Step 3 — "delivery": the suggestions said "nothing here". They lied.
**Did:** Back to search, typed `delivery`.
**Got:** The predictive panel flipped to "Oh no! No results found for 'delivery'. Please try again with a different query." Pressed Enter anyway out of spite — and the full results page found **29 results**. But: a wall of product cards (Italy Polo, Portugal Polo, track pants… including SOLD OUT items). The only non-product hit is a "PAGE — Returns Policy" card sitting in slot 12, two and a half screens down, just before the pagination (1 2 3 →). No delivery/shipping page exists. Tapped the first product instead: the Italy Polo PDP says "Please Allow 2-5 Working Days For Item To Be Shipped". Delivery *cost*: nowhere on the entire route.
**Expected:** A shipping/delivery info page, or at least suggestions that agree with the results page.
**Felt:** "The search told me 'no results', then showed me 29. Which of you is lying? And the honest answer to 'delivery' turned out to be hidden inside a product listing — I only found '2-5 working days' because I gambled a tap on a polo. Still no idea what postage costs."
**Next:** continued, trust in the suggestions gone (u12-typed-delivery, u12-results-delivery, u12-delivery-pagecard, u12-delivery-pdp-answer) — **partial: 3 taps + 2.5 screens of noise to a dispatch line on a PDP; cost = dead end**

### Step 4 — "size": forty results, zero answers
**Did:** Typed `size`.
**Got:** Predictive again: "Oh no! No results found for 'size'." Enter: **40 results** — practically the whole 44-product catalogue, because every product's size option matches the word. No size guide page, no measurements, nothing labelled "size chart" anywhere on the results page. The lone page card, slot 12 again: Returns Policy — which is not a size guide.
**Expected:** A size guide page, the standard thing every clothing shop has.
**Felt:** "Forty results and not one of them is an answer. If I want measurements I'd have to open products one by one and hope for a chart photo. For a clothes shop, 'size' being unanswerable is a bad sign."
**Next:** continued, patience thinning (u12-typed-size, u12-results-size) — **dead end (product noise only)**

### Step 5 — "refund": right answer, wrong signposting
**Did:** Typed `refund`.
**Got:** Predictive: "Oh no! No results found for 'refund'." Enter: exactly **1 result** — the Returns Policy page card. Tapped it; the Refunds section is right there in the policy (refund to original payment method within 14 days of receiving the return).
**Expected:** The suggestions to find the same page the results page finds.
**Felt:** "So the answer existed all along — the little dropdown just couldn't be bothered. If I'd trusted it I'd have walked away thinking they don't do refunds."
**Next:** continued (u12-typed-refund, u12-results-refund) — **3 taps to answer, but only if you ignore the suggestion panel saying there's nothing**

### Step 6 — "shipping": the whole catalogue, and no answer at all
**Did:** Typed `shipping`.
**Got:** Predictive: "Oh no! No results." Enter: **43 results — every one a product, zero pages** (the products' own "…For Item To Be Shipped" dispatch lines match the query). Filters and a Relevance sort are offered — for a question no product can answer. No shipping policy page exists on this site as far as search can see, and shipping cost appears nowhere before checkout.
**Expected:** A shipping page with prices and timescales.
**Felt:** "This is the worst one. I asked the site's own search what shipping costs and it offered me 43 polos, half of them sold out. The site literally cannot answer the question."
**Next:** hesitated (u12-typed-shipping, u12-results-shipping) — **dead end**

### Step 7 — "contact": search redeems itself
**Did:** Typed `contact`.
**Got:** Predictive woke up again: "POPULAR SEARCHES — Contact", linked. Tapped it — /pages/contact: opening hours (Mon–Fri 9am–9pm GMT, Sat 10–6, Sun 10–4) and a proper form (first/last name, how-to-contact-you checkboxes for email/phone/SMS, email, message, Send Message). Observed only — nothing filled, nothing sent. No email address printed on the page itself; the info@ address only lives in the returns policy. Enter-route also fine: 2 results, Contact + Returns Policy.
**Expected:** A contact page or at least an email address.
**Felt:** "Two taps, real opening hours — seven days a week, evenings — that's more reachable than most big shops. Odd that the page itself hides the email address, but the form plus the info@ from the policy will do."
**Next:** done searching (u12-typed-contact-sugg, u12-results-contact, u12-contact-page) — **2 taps to answer**

## Outcome
**Bought / didn't:** Didn't — this was a pre-purchase verification visit. Returns and contact verified to her satisfaction; delivery time only found by luck inside a product page; shipping cost and size guidance flatly unanswerable by search (or, in fact, by the site).
**Total time:** ~8 minutes for six queries.
**Worst moment:** The predictive panel saying "Oh no! No results found" for `refund` and `delivery` while the full results page held the answer — a shopper who trusts the suggestions (most do) leaves believing the shop has no refund policy. Close second: `shipping` returning 43 products and zero answers, with sold-out items padding the noise.
**Best moment:** `returns` — two taps from search icon to one of the most complete, honest returns policies she'd seen on an indie store (14+14 days, named return address, who pays postage, 14-day refund clock). The drawer itself (instant focus, clean results cards for pages) is genuinely well built.
**Would they come back?** As a shopper, cautiously yes — the returns policy and seven-day contact hours bought real trust, and for HER main question search delivered in two taps. But she'd order knowing she won't learn the postage cost until checkout, which she resents on principle. Verdict on search as a route to answers: reliable ONLY when a page with the right word in its title exists (returns, contact); for everything else it collapses into product noise or a false "no results".
**One thing that would have changed the outcome:** A shipping/delivery info page (even three lines: cost, courier, timescale) — it would have turned the two total dead ends (`shipping`, `delivery`) into two-tap answers the way `returns` already works, and fixed the predictive panel's false negatives for the most-asked pre-purchase question of all: "what will this cost me to receive?"
