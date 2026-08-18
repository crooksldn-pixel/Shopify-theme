# RAW — Catalogue-as-register + search (staging theme 202053779799, verified `.crk-root` + `crooks.css` every session)

Tested 2026-08-18 ~21:00–22:00 London, mobile 390x844 DPR3. First-load pass of /collections/all under slow 4G; functional runs unthrottled. Note: the audit egress is US, so Shopify geo-converted every price to USD ($70 for the £50 crewneck etc.) — the theme's own copy (ticker "FREE UK SHIPPING OVER £20") stays in GBP. All observations below are currency-independent unless noted.

### 1. Status slot on every card on /collections/all, date beside it
- **Should:** Every card's status slot states stock (AVAILABLE / LOW STOCK / SOLD OUT); the drop date is a separate de-emphasised element beside it, never a replacement (SPEC §3.4).
- **Did:** All 14 cards carry a status — every one currently reads AVAILABLE (no product in the register is fully sold out or under the low-stock threshold right now, so LOW STOCK/SOLD OUT never appear in live data). Drop dates appear on exactly 3 cards (CRXST★RZ "DROPPED 03.08", both socks "DROPPED 19.07") and each time as a separate `crk-card__dropped` line under the price/status row — status always present alongside. Zero cards fail the rule. Search-result cards use the identical format.
- **Verdict:** works
- **Shopper impact:** The register format is consistent enough that you stop reading it consciously — price and stock are always in the same place. Caveat: the good states (LOW STOCK, SOLD OUT) are untestable in current store data.
- **Screens:** f-register-search-all-top, f-register-search-dropdate-card

### 2. Sold-out telegraphing before the click (V2 BAGGIES)
- **Should:** A shopper should be able to tell an item/size situation is sold out before committing a click.
- **Did:** The V2 BAGGIES card reads plain "AVAILABLE" — identical to every other card — while on the PDP the three most common sizes (M, L, XL) are gone (aria-disabled, confirmed); only XS and S remain. Nothing on the card hints at it: no LOW STOCK (remaining XS+S stock is above the threshold of 3), no size strike-through, no "2 sizes left".
- **Verdict:** partly
- **Shopper impact:** A mid-size shopper taps V2 BAGGIES on the promise of AVAILABLE, lands, finds M/L/XL dead, and backs out — a wasted click and a small trust ding ("available for whom?"). Card-level status is honest for full sellouts, but the majority-sizes-gone case is invisible until the PDP. This is the design as SPEC'd (status = product-level), so it's a cost to record, not a defect to fix blindly.
- **Screens:** f-register-search-v2baggies-card

### 3. Card click targets: image, title, price
- **Should:** All three open the product.
- **Did:** Three separate clicks on the BLUE WASH OG JEANS card (image, then title, then price, fresh page load each time) all landed on /products/cb2-wash-jeans. The whole card is one `<a class="crk-card">`, so there are no dead zones between the elements either.
- **Verdict:** works
- **Screens:** —

### 4. Collection page h1s and difference from the homepage register
- **Should:** Exactly one h1 naming the collection; collection pages read as the same register a shopper met on the homepage.
- **Did:** /collections/all → one h1 "ALL"; /collections/denim → one h1 "DENIM" (4 ITEMS); /collections/sweats → one h1 "SWEATS" (3 ITEMS). Cards renumber per collection (denim runs NO. 01–04). Differences from the homepage register a shopper can notice: (a) homepage heads the register "CATALOGUE" (h2) after the hero, collections lead with the collection name + item count; (b) the OUTLINE toggle exists **only on the homepage register** — collections and search offer just FLAT/ON MODEL; (c) single-category collections (denim, sweats) drop the category chip row entirely — sensible; (d) on sweats (3 items) the empty 4th grid cell renders as a solid bright-purple rectangle (the grid's `rgb(58,47,74)` gap-colour background showing through) — reads as a glitchy blank tile next to the V2 BAGGIES card. Sweats shows 3 items where SPEC's store data counts 5 in the collection; on-page label and cards agree so no shopper sees a contradiction.
- **Verdict:** works
- **Shopper impact:** Collections feel like filtered views of the same register — no re-learning. The purple empty tile is the one blemish; on any odd-count collection it's the last thing in view.
- **Screens:** f-register-search-collections-denim, f-register-search-collections-sweats, f-register-search-sweats-emptyslot, f-register-search-home-register

### 5. Search result quality: jeans / BAGGIES / bagies / xyzzy / empty
- **Should:** Category words and real names hit; misspellings recover; gibberish fails cleanly; empty query stands the register down (SPEC §9.8).
- **Did:**
  - "jeans" → 4 results, exactly the 4 denim pieces. Clean.
  - "BAGGIES" → 6 results, V2 BAGGIES first, then jeans/jorts/duffle as loose matches. Target on top, noise below the fold.
  - "bagies" (misspelt) → 5 results, **V2 BAGGIES still first**. The misspelling costs nothing.
  - "xyzzy" → "SEARCH: XYZZY / 0 RESULTS / NO ITEMS IN THE REGISTER MATCH THAT QUERY." No empty grid, no error tone. (No suggestions offered either — dead end, but a graceful one; the search box is right there.)
  - "" (empty submit from the field) → Shopify redirects to /search?q= and the page shows only the query bar + DIRECT LINKS block (START A RETURN, TRACK YOUR ORDER, QUESTIONS). No register, no "0 results", no scolding. The stand-down reads as "the terminal is waiting", which fits.
- **Verdict:** works
- **Shopper impact:** Fat-finger tolerance is the standout — a shopper who half-remembers a name still lands on it first.
- **Screens:** f-register-search-q-jeans, f-register-search-q-baggies, f-register-search-q-bagies, f-register-search-q-xyzzy, f-register-search-q-emptysubmit, f-register-search-search-empty

### 6. Typeahead: pre-typing direct links and "ba" suggestions
- **Should:** Curated links (Track your order, Questions) before typing; product suggestions while typing.
- **Did:** On focus, before any keypress, three curated links show under DIRECT LINKS: START A RETURN → Aftership returns centre, TRACK YOUR ORDER → /pages/tracking, QUESTIONS → /pages/faq (one more than SPEC promises — the returns link is there too). Typing "ba" slowly: after the second character an ITEMS block appears with LARGE DUFFLE BAG $25 and V2 BAGGIES $83 (Shopify suggest links), direct links staying beneath. No flicker, no lag worth noticing.
- **Verdict:** works
- **Screens:** f-register-search-typeahead-ba

### 7. THE KEY TEST — Terms, FAQ and legal policies through search alone
- **Should:** "terms", "returns", "privacy", "track" each route to the right destination via search, since Shopify's own search cannot reach these pages (SPEC §3.6).
- **Did:** Both in the typeahead (typing) and on the submitted results page (DIRECT LINKS block persists above results), every word routes:
  - **"terms"** → TERMS → /pages/terms (typeahead PAGES block; submitted page also lists TERMS under PAGES & ANSWERS). **works**
  - **"returns"** → START A RETURN → Aftership returns centre. Submitted page: 0 product results but the direct link sits right above the heading. **works** — note it routes to the returns *portal*, not the Refund policy text; a shopper wanting the policy gets it by typing "refund" (→ /policies/refund-policy, verified) so the set is fully covered.
  - **"privacy"** → PRIVACY POLICY → /policies/privacy-policy, plus YOUR PRIVACY CHOICES (/pages/data-sharing-opt-out) as a second hit. **works**
  - **"track"** → TRACK YOUR ORDER → /pages/tracking (typeahead also surfaces SHIPPING POLICY above it — slightly odd ordering, but the tracking link is one row down and clearly labelled). **works**
  - Cosmetic: when a direct link matches, it renders in the matched block AND again in the always-on DIRECT LINKS list below — "START A RETURN" appears twice on the "returns" panel. Harmless duplication, mildly amateur-looking.
- **Verdict:** works
- **Shopper impact:** This routing genuinely rescues the store's weakest discoverability spot. Every "boring but critical" page is reachable by typing the obvious word — with JS on. (The submitted page's DIRECT LINKS block is server-rendered into the results page too, so an Enter-presser is equally served.)
- **Screens:** f-register-search-typeahead-terms, -returns, -privacy, -track, f-register-search-submit-terms, -returns, -privacy, -track

### 8. Results page structure: products vs PAGES & ANSWERS
- **Should:** Product results and page/article results are visibly separated and the page reads clearly.
- **Did:** Verified with "track" (3 products + tracking page) and "delivery" (9 products + shipping policy in direct links): the page stacks query bar → DIRECT LINKS (when matched) → "SEARCH: TRACK / 3 RESULTS" → category chips → **PAGES & ANSWERS** (labelled, each entry tagged PAGE) → the product register. Sections are ruled off and labelled in the register voice; nothing interleaves. Two nits: the "N RESULTS" count counts *items only*, so "terms" shows "0 RESULTS" directly above a PAGES & ANSWERS block that contains the answer — a literal-minded shopper reads "nothing found" first; and the results heading is an h2 with no h1 anywhere on /search (empty or with query), unlike every other page.
- **Verdict:** works
- **Shopper impact:** Clear at a glance; the "0 RESULTS but here's your answer" wording is the only moment of friction.
- **Screens:** f-register-search-submit-track, f-register-search-submit-delivery

---

## Extra observations (not on the checklist)

### Cookie consent banner exists now
- SPEC's open items list "no cookie banner", but a Shopify cookie-consent banner ("We and our partners, including Shopify…" with Accept / Decline / Manage preferences) appeared on first load and covered roughly the bottom half of the mobile viewport, including the first register cards, until dismissed. Store-side change since SPEC was written. Once dismissed it stays gone for the session.
- **Screens:** f-register-search-all-top

### Currency split for non-UK visitors
- With a US egress, all prices geo-convert to USD while the status ticker stays "FREE UK SHIPPING OVER £20" — a US shopper sees $ prices under a £ shipping promise on the same screen. Shopify behaviour + hard-coded ticker copy, not a theme bug, but the mixed currencies are noticeable.

### OUTLINE toggle is homepage-only and its state travels
- The homepage register has FLAT / ON MODEL / OUTLINE (outline defaults ON — the white sticker-edge treatment on card images). Collection and search registers have only FLAT / ON MODEL, yet the sessionStorage outline state set on the homepage carries to them with no control to change it there. A shopper who toggles it off on the homepage has no way back except returning home. This is O3 territory (already logged as pending); the cost recorded here is the inconsistency, not the toggle's existence.
- **Screens:** f-register-search-outline-on-home, f-register-search-outline-carry-collection

### Slow-4G first load of /collections/all
- Ticker and header paint first, register heading and toggles next, card images stream in lazily. Fully settled around the 5-second mark; nothing jumped or reflowed while reading, and the status/price text was there before the images. Felt like a heavy-ish but steady terminal boot, in keeping with the fiction; never felt broken.
