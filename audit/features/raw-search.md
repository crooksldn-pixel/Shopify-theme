# raw-search.md — Search, typeahead and the curated direct links

Area key `search`. Staging theme `202053779799`, GB/GBP, mobile 390×844 unless stated.
Three browser runs: `audit/_tools/srch1.mjs`, `srch2.mjs`, `srch3.mjs`.

---

### Reaching search at all
**Should:** A shopper who wants to search can find the field.
**Did:** The header carries a plain `SEARCH` link (`/search`) next to `CATALOGUE` and `BAG [0]`.
One tap from the homepage lands on the query page. The field is the first thing under the
header, at y=187 of an 844-tall screen — no scrolling, no modal, no icon-only guessing.
**Verdict:** works
**Evidence:** `audit/screens/search-00-home-header.png`, `audit/screens/search-01-empty-query.png`

---

### The query field on mobile
**Should:** Visible, tappable, obvious how to submit, keyboard behaves.
**Did:** Box is 358×56 px, full width inside 16px gutters, bordered, unmistakably a field.
It **autofocuses on arrival** (`document.activeElement` is the field on load), so the keyboard
is already up and the shopper can type without a tap. Placeholder: `Item, category or question`.
A filled `SEARCH` button (132×48) sits directly under it — no hunting for a magnifier icon.
Pressing Enter submits and lands on the same results URL as the button.
Tapping the box after load re-focuses it correctly.
One risk I could not verify in this harness: the field renders at **13px**. iOS Safari zooms the
whole page whenever a focused input is under 16px, and this field focuses itself on arrival — so
on a real iPhone the search page probably jumps/zooms the instant it opens. Worth one check on a
handset; the fix (a 16px input) is inside the design law.
**Verdict:** works
**Evidence:** `audit/screens/search-50-mobile-field.png`, `audit/screens/search-31-enter-submit.png`

---

### The empty-query stand-down (SPEC §9.8 — deliberate, not filed as a bug)
**Should:** A blank search page must not read as broken.
**Did:** It doesn't. With no query the page shows, top to bottom, exactly this:

> `Item, category or question` *(placeholder in the field)*
> `SEARCH` *(the button)*
> `SEARCH BY ITEM, CATEGORY OR COLOUR`
> `DIRECT LINKS`
> `START A RETURN` · `RETURNS CENTRE`
> `TRACK YOUR ORDER` · `TRACKING`
> `QUESTIONS` · `FAQ`

No empty grid, no "0 results", no orphaned heading. Three useful destinations are offered
before a single key is pressed, so the page has a job even when it has no query. The
stand-down reads as a landing page, not as a failure. This is the right call and it works.
Two notes that are *not* the stand-down itself:
- Three links show before typing, not two — `START A RETURN` (AfterShip, new tab) as well as
  `TRACK YOUR ORDER` and `QUESTIONS`.
- On a first visit Shopify's `COOKIE CONSENT` panel occupies the bottom ~40% of the screen and
  covers `QUESTIONS` (see Surprises).
**Verdict:** works
**Evidence:** `audit/screens/search-01-empty-query.png`, `search-01-empty-query-full.png`

---

### Typeahead — products
**Should:** Suggest products as you type.
**Did:** Yes, and well. From 2 characters, a `PAGES` group and an `ITEMS` group appear under the
field, each item with a thumbnail, the product title and the price in GBP:
`CHARCOAL CELLBLOCK SHORTS £45`, `V2 BAGGIES £60`, `CELLBLOCK SET £85`. Prices match the
catalogue. Typing `jeans` gave `BLUE WASH OG JEANS £60 / GREY WASH OG JEANS £60 / BLUE WASH
JORTS £50 / GREY WASH JORTS £50` — correct and in a sane order.
**Verdict:** works
**Evidence:** `audit/screens/search-10-typeahead-size.png`, `search-20-typeahead-jeans.png`

---

### Typeahead — the suggestion list blinks out mid-word
**Should:** Suggestions narrow as you type; they should not vanish and come back.
**Did:** Typing `denim` one letter at a time, five times over two runs, identically:

| typed | panel |
|---|---|
| `d` | closed (under the 2-character minimum — fine) |
| `de` | open: `SHIPPING POLICY`, `TRACK YOUR ORDER` |
| `den` | **closed — nothing at all** |
| `deni` | open: 4 denim products |
| `denim` | open: 4 denim products |

So the shopper watches the panel open, then snap shut mid-word, then reopen. Nothing is
broken and nothing is lost, but the field looks like it stopped working for one keystroke.
It happens because at `den` neither the curated keywords nor Shopify's suggestions have a hit,
and the panel's only two states are "rows" and "gone".
**Verdict:** partly
**Shopper cost:** Small but real — a flicker at exactly the moment someone is deciding whether
the search box is any good. A "no matches yet" row, or simply holding the previous rows until
new ones arrive, would remove it without a single new pixel of chrome.
**Evidence:** `audit/screens/search-30-typeahead-growth.png`; run 3 log, section A2.

---

### Typeahead — reliability when Shopify's suggestion endpoint doesn't answer
**Should:** The curated links are the one part of search that does not depend on Shopify's
index. They should still appear when the product suggestions fail.
**Did:** Five consecutive `size` queries in run 3 all returned the full panel
(`SIZE GUIDE` + 6 products) with `suggest.json` answering 200 each time. But in run 2, under
load, the same `size` query produced **no panel at all** — not even `SIZE GUIDE`, which is
matched in the browser and needs no network call. Observed once; the panel's fetch treats a
non-OK response as "render nothing" rather than falling back to the curated links.
**Verdict:** partly
**Shopper cost:** On a bad connection the feature's whole justification — that questions reach
answers even when the search index can't help — silently switches off, and the shopper just
sees a search box that suggests nothing.
**Evidence:** run 2 log section C (`typeahead rows: []` for `size`) vs run 3 section A
(5/5 full panels for the identical query).

---

### THE CRITICAL TEST — can a shopper reach TERMS, QUESTIONS and the POLICIES through search?
**Should:** Yes. This is the entire reason the curated links exist.
**Did:** Mostly yes, and the mechanism is sound: every one of the six required queries surfaced
at least one correct destination, in the typeahead *and* on the results page. Exact results,
with taps counted from the homepage (tap 1 = header `SEARCH`):

| query | typeahead offers | results page offers | taps to the destination | taps to the actual answer |
|---|---|---|---|---|
| `returns` | `START A RETURN` · `RETURNS CENTRE` | same, only that | 2 | off-site — see below |
| `refund` | `START A RETURN`, `REFUND POLICY` · `POLICY` | `REFUND POLICY` | 2 | **2 — answer is on the page** |
| `delivery` | `SHIPPING POLICY` + 6 products | `SHIPPING POLICY` + 7 products | 2 | **2 — answer is on the page** |
| `size` | `SIZE GUIDE` · `SIZING` + 6 products | `SIZE GUIDE` + 10 products | 2 | 3 + a scroll |
| `contact` | `CONTACT US` · `CONTACT` | `CONTACT US` **and** `PAGES & ANSWERS → CONTACT` | 2 | **2** |
| `shipping` | `SHIPPING POLICY` + 1 product | `SHIPPING POLICY` + 1 product | 2 | **2** |
| `terms` | `TERMS` · `TERMS` | `TERMS` **and** `PAGES & ANSWERS → TERMS` | 2 | **2** |
| `help` | `QUESTIONS` · `FAQ` | `QUESTIONS` | 2 | 3 + a scroll |
| `where is my order` | `TRACK YOUR ORDER` · `TRACKING` | `TRACK YOUR ORDER` | 2 | sign-in wall — see below |
| `exchange` | `START A RETURN` only | `START A RETURN` only | 2 | off-site |
| `cancel my order` | `REFUND POLICY`, `TERMS` | both | 2 | **2** |
| `how do i return something` | — | `START A RETURN`, `QUESTIONS` | 3 | 4 + a scroll |

Every keyword hit was correct — no wrong link was ever offered. Two taps to a policy page is
genuinely good, and better than most Shopify stores manage.
**Verdict:** works — with the three qualifications below, which are all about *what the link
lands on*, not about the matching.
**Evidence:** `audit/screens/search-10-typeahead-{returns,refund,delivery,size,contact,shipping}.png`,
`search-11-results-*.png`, `search-70-{terms,help,where_is_my_order,exchange,cancel_my_order}.png`

---

### Qualification 1 — "returns" and "exchange" reach a third-party portal, never the policy
**Should:** Someone asking about returns *before* buying wants to read the terms. Someone
asking *after* buying wants the portal. Search should offer both.
**Did:** `returns` returns exactly one link, in both the typeahead and the results page:
`START A RETURN` / `RETURNS CENTRE`, pointing at `https://5wn03tnm.aftership.com` in a new tab.
`exchange` behaves identically. Neither offers `TERMS` (which has a `03 RETURNS` and an
`04 SIZE SWAPS` section), nor `QUESTIONS` (which has `CAN I RETURN SOMETHING?` and
`DO YOU DO EXCHANGES?`), nor the `REFUND POLICY`. The AfterShip portal is live (responds 200)
but it is an order-lookup app on someone else's domain, carrying its own fonts and colours
rather than the terminal's, and it opens in a new tab. It is a wall, not a policy: a shopper
who has not bought anything yet has nothing to type into it.
**Verdict:** partly
**Shopper cost:** The pre-purchase question "what's your returns policy?" — the single most
common reason to search a clothing site before a first order — is answered by being thrown
off the site into an order-lookup form. That is the exact query the feature was built for.
Adding `terms,questions` to the l1 keyword list, or adding `returns,returning,send back` to
the Terms and Questions blocks, is a settings-only change.
**Evidence:** `audit/screens/search-11-results-returns.png`, `search-70-exchange.png` —
`DIRECT LINKS / START A RETURN / RETURNS CENTRE` and nothing else.

---

### Qualification 2 — the FAQ links drop the shopper at the top of a 14-question page, all closed
**Should:** `SIZE GUIDE` and `QUESTIONS` should land on the answer.
**Did:** Both point at `/pages/faq` with no anchor. Landing state, measured: `scrollY 0`,
page 2416px tall on an 844px screen, **0 of 14 accordions open** (deliberate, SPEC §9.4).
- `size` → tap `SIZE GUIDE` (2 taps) → the `HOW DO I KNOW WHAT SIZE TO BUY?` row sits at
  y=821 — just below the fold — and must then be tapped to open. Answer = 3 taps + a scroll.
- Homepage → `SEARCH` → `QUESTIONS` → the `CAN I RETURN SOMETHING?` row is at y=946, so past
  eight other questions. Answer = 3 taps + a scroll of more than a full screen.

The `SIZE GUIDE` row also promises something the destination doesn't have. Its answer reads:
"Where a piece has been measured, its product page carries a measurements table — **tap SIZE
GUIDE next to the size buttons**." So a link labelled `SIZE GUIDE` lands on a page that tells
you the size guide is somewhere else.
**Verdict:** partly
**Shopper cost:** Two of the three pre-typed links, and the sizing route, all end one tap and
one scroll short of the answer. On sizing that tap sits between a shopper and a purchase
decision. `shopify://pages/faq#sizing` (and `#returns`) in the block URLs would close the gap
with no new markup — the group headings already exist on the page.
**Evidence:** `audit/screens/search-80-faq-landing.png`, `search-81-faq-returns-open.png`,
`search-82-sizeguide-landing.png`

---

### Qualification 3 — `TRACK YOUR ORDER`, offered before anything is typed, is a sign-in wall
**Should:** The most prominent pre-typed link should do the thing it says.
**Did:** Tapping `TRACK YOUR ORDER` (2 taps from the homepage) lands on `/pages/tracking`,
whose entire content is:

> `CROOKSLDN PROPERTY TRANSFER NETWORK`
> `> CHAIN OF CUSTODY DATABASE ONLINE`
> `IDENTIFICATION REQUIRED`
> `Order records are released to the account they were filed under. Sign in to view the chain of custody for your orders.`
> `SIGN IN`
> `NO ACCOUNT? THE TRACKING LINK IN YOUR DISPATCH EMAIL OPENS YOUR ORDER WITHOUT ONE.`

Shopify lets you check out as a guest — the FAQ says so ("You can check out as a guest and
still track your order"). A guest who searches `where is my order` is therefore routed, in two
taps, to a page that asks for an account they do not have and then tells them to go back to
their email. The fallback line is at least there and is in plain English.
**Verdict:** partly (the tracking page itself belongs to another area — recorded here because
search is the route that leads to it, and it is one of only three links shown before typing)
**Shopper cost:** The anxious "where is my parcel" shopper — the one most likely to email or
DM if the site stalls them — is stalled.
**Evidence:** `audit/screens/search-83-tracking-landing.png`

---

### The results page says "0 RESULTS" while showing links that matched
**Should:** One screen should not report success and failure at once.
**Did:** On every answers-type query the page renders, in this order: the matched `DIRECT
LINKS`, then the register heading, then the register's empty state. Searching `terms` shows,
top to bottom:

> `DIRECT LINKS`
> `TERMS` `TERMS`
> `SEARCH: TERMS`
> `0 RESULTS`
> `PAGES & ANSWERS`
> `TERMS` `PAGE`
> `NO ITEMS IN THE REGISTER MATCH THAT QUERY.`

Three links to the Terms page, and between them the words `0 RESULTS` and `NO ITEMS IN THE
REGISTER MATCH THAT QUERY.` The same shape appears for `returns`, `refund`, `contact`, `help`,
`exchange` and `cancel my order`.
Also visible here: the Terms link is printed as its own note — `TERMS` `TERMS` — and the
indexed page result duplicates the curated one, so the same destination appears twice
(`contact` does this too: `CONTACT US` in DIRECT LINKS and `CONTACT` under `PAGES & ANSWERS`).
**Verdict:** partly
**Shopper cost:** `SEARCH: TERMS` is the biggest thing on the screen, `NO ITEMS IN THE REGISTER
MATCH THAT QUERY.` runs full width below it, and the links that did match are set small above.
A shopper who scans rather than reads takes the failure line and leaves, having been told
nothing matched on a screen where three things matched. Suppressing the register's count and empty
line when curated links or page results are present is a Liquid-side condition, no new UI.
**Evidence:** `audit/screens/search-70-terms.png`, `search-11-results-contact.png`

---

### Empty results — a genuine dead end
**Should:** A failed search should offer a way out.
**Did:** It offers none. Gibberish `qwzzptx` produces the whole page:

> `SEARCH: QWZZPTX`
> `0 RESULTS`
> `NO ITEMS IN THE REGISTER MATCH THAT QUERY.`

No suggestions, no "did you mean", no direct links, no link to the catalogue — the only routes
out are the header and the burger menu. Note the asymmetry: the **blank** search page offers
three helpful links; the **failed** search page offers zero. The worse state gives the shopper
less help than the neutral one. Same for `DEIM` (a typo for DENIM) and for the misspelling test
in Missing, below.
**Verdict:** broken
**Shopper cost:** Every misspelling that Shopify's fuzzy matching doesn't catch ends the
session, on a 12-product store where showing the whole catalogue would almost always be the
right answer. The three `always` links already exist and are already rendered on the blank
page; showing them (or `CATALOGUE`) when `results_count == 0` is a one-condition change and
adds nothing to the design.
**Evidence:** `audit/screens/search-21-results-qwzzptx.png`, `search-21-results-DEIM.png`

---

### Misspellings and partial words
**Should:** A shopper who types badly should still find the garment.
**Did:** Better than expected. Every realistic misspelling landed:

| typed | first result |
|---|---|
| `jeens` | `GREY WASH OG JEANS` (4 results) |
| `blue wash og jeens` | `BLUE WASH OG JEANS` (4 results) |
| `bagies` | `V2 BAGGIES` (5 results) |
| `clve tee` | `MONEY CLIVE TEE` (2 results) |
| `BLUE WASH OG JEANS` (exact) | `BLUE WASH OG JEANS` (3 results) |
| `hoodie` (not stocked) | `CHARCOAL CELLBLOCK CREWNECK`, then two tees |

Only a mangled single word with no near neighbour (`DEIM`, `qwzzptx`) fails, and that failure
is the dead end above.
**Verdict:** works
**Evidence:** `audit/screens/search-70-{bagies,clve_tee,blue_wash_og_jeens,BLUE_WASH_OG_JEANS,hoodie}.png`,
`search-21-results-jeens.png`

---

### Category and colour words
**Should:** The hint under the field promises `SEARCH BY ITEM, CATEGORY OR COLOUR`.
**Did:** Category works: `jeans` → 4 denim pieces, correct and complete. Colour is where the
promise breaks. `black` returns 7 results in this order:

> `NO. 01 DENIM GREY WASH OG JEANS` · `NO. 02 SWEATS V2 BAGGIES` · `NO. 03 DENIM GREY WASH
> JORTS` · `NO. 04 T-SHIRT MONEY CLIVE TEE` · `NO. 05 ACCESSORIES LARGE DUFFLE BAG` ·
> `NO. 06 ACCESSORIES BLACK/BLUE MOTIONTEC™ SOCKS` · `NO. 07 T-SHIRT CRXST★RZ T-SHIRT`

The first three hits for "black" are grey. The only product with `BLACK` in its name is sixth.
The typeahead for the same word does better (`BLACK/BLUE MOTIONTEC™ SOCKS` first), so the
shopper sees the right answer while typing and the wrong order after pressing SEARCH.
`grey` behaves sensibly (5 results, both grey washes first). The register already knows
colourways — `MONEY CLIVE TEE` prints `Colourways: BLACK, WHITE` on its card — but that data
does not reach the ranking.
**Verdict:** partly
**Shopper cost:** A promise made 40px under the field and broken on the next screen. Either the
hint stops saying `COLOUR`, or colour lands in the product tags where Shopify's relevance can
see it (store-side data, not theme code).
**Evidence:** `audit/screens/search-70-black.png`, `search-70-grey.png`, `search-21-results-jeans.png`

---

### The field's own two descriptions disagree
**Should:** One promise.
**Did:** The placeholder inside the box reads `Item, category or question`. The hint 40px below
reads `SEARCH BY ITEM, CATEGORY OR COLOUR`. One invites questions and omits colour; the other
invites colour and omits questions. Questions are the feature's reason to exist and the hint —
the line rendered in the terminal's own voice, and the one a shopper reads as instruction —
is the one that leaves them out.
**Verdict:** partly
**Shopper cost:** Nobody is blocked, but the one surface that could teach a shopper "you can
ask this box a question here" spends its words on colour, which is the thing that works least
well.
**Evidence:** `audit/screens/search-01-empty-query.png` — both strings visible in one shot.

---

### Desktop
**Should:** Not a mobile-only field.
**Did:** At 1440px the input is 620px wide with the `SEARCH` button beside it on the same row,
both 56px tall, field autofocused, typeahead identical (`refund` → `START A RETURN`,
`REFUND POLICY`).
**Verdict:** works
**Evidence:** `audit/screens/search-90-desktop-typeahead.png`

---

## Surprises

- **A `COOKIE CONSENT` panel now exists and it covers the direct links.** On first arrival at
  `/search` it occupies the bottom ~40% of the phone screen and sits over `QUESTIONS`, the
  third of the three pre-typed links; on a results page it covers `NO ITEMS IN THE REGISTER
  MATCH THAT QUERY.` entirely. The standing brief lists "No cookie banner" as a known item —
  that is no longer true, and its landing spot is unlucky for this area.
  Evidence: `audit/screens/search-01-empty-query.png`, `search-11-results-returns.png`.
- **Shopify *does* index the Terms and Contact pages.** `terms` and `contact` both return a
  `PAGES & ANSWERS` row alongside the curated link — so the same destination is listed twice
  on one screen. The build note that Terms "cannot be indexed" is out of date for the title
  match at least.
- **`0 RESULTS` is printed under links that matched**, on every answers query.
- **The failed-search page is less helpful than the blank one.** Blank offers three links;
  0 results offers none.
- **The suggestion panel closes completely at `den`** and reopens at `deni`, every time.
- **`SIZE GUIDE` lands on a page that says the size guide is elsewhere** ("tap SIZE GUIDE next
  to the size buttons").
- **The `refund` route is now clean.** `/policies/refund-policy` reads "Return postage is paid
  by you… There is no fee for a UK size swap itself, and we cover the postage sending the new
  size out to you" — consistent with Questions q8. Known item **O5** ("Size swaps are free
  within the UK") appears to have been resolved in the live policy; worth confirming in admin.

## Missing

- **Any way out of a zero-result search.** No "did you mean", no popular searches, no
  `CATALOGUE` link, nothing.
- **A route from `returns`/`exchange` to the returns *policy*.** Only the third-party portal.
- **Anchors on the FAQ links.** `#sizing` / `#returns` would turn "3 taps and a scroll" into
  two taps.
- **A pre-typed link to `TERMS`.** Only `START A RETURN`, `TRACK YOUR ORDER` and `QUESTIONS`
  show before typing; Terms — the page carrying carriage, dispatch, returns and refunds in
  plain English — has to be guessed at.
- **A heading on the search page.** `/search` renders no `h1` at all, blank or with results
  (`SEARCH: JEANS` is a lower-level heading). SPEC §9.10 lists "exactly one h1 per page" as a
  property to preserve; this template has none.
- **No-JS behaviour was not re-tested here** — SPEC §3.6 says the form submits normally without
  the script, and run 3 of the previous audit verified it.

## Contradictions

- **`Item, category or question`** (placeholder) vs **`SEARCH BY ITEM, CATEGORY OR COLOUR`**
  (hint, 40px below it).
- **`0 RESULTS` / `NO ITEMS IN THE REGISTER MATCH THAT QUERY.`** printed on the same screen as
  `DIRECT LINKS / TERMS` and `PAGES & ANSWERS / TERMS`.
- **`SIZE GUIDE`** (search's promise) vs the destination's own answer, **"tap SIZE GUIDE next
  to the size buttons"** (i.e. it is on the product page, not here).
- **`SEARCH BY ITEM, CATEGORY OR COLOUR`** vs searching `black` and getting
  `NO. 01 GREY WASH OG JEANS`.
- **Two different returns processes, one query apart.** `returns` → the AfterShip portal;
  `refund` → a policy that says "email crooksldn@gmail.com or DM @crooksldn with your order
  number" and "For returns please return to: Oairo Uk Office, Bourne end Business Park…".
- **`TRACK YOUR ORDER`** offered to everyone before they type, vs the destination's
  **`IDENTIFICATION REQUIRED … Sign in to view the chain of custody`**, on a store whose FAQ
  says "You can check out as a guest and still track your order."

## Works and must be protected

- **The curated direct links themselves.** Twelve question-shaped queries, twelve correct
  destinations, zero wrong matches, two taps each. This is the feature's justification and it
  is met — every problem above is about what happens *after* the link, not about the matching.
- **The empty-query stand-down (§9.8).** A blank page carrying three real destinations and a
  hint reads as a landing page, not a fault. Do not replace it with a "no results" message or
  a product grid.
- **The typeahead's two-group layout** — `PAGES` above `ITEMS`, answers ranked above garments.
  A shopper asking a question sees the answer before the merchandise, which is the correct
  priority and the opposite of what most stores do.
- **The field itself:** 56px tall, autofocused, visible without scrolling, with a labelled
  `SEARCH` button and a working Enter key. No modal, no icon-only trap.
- **Prices in the suggestions** (`V2 BAGGIES £60`) — plain English money in a fiction-heavy
  theme, per §0.
- **Fuzzy matching on product names.** `bagies`, `clve tee`, `jeens` all land.
