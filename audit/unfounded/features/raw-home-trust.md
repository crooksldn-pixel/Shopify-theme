# RAW — Homepage, Navigation, Search & Trust Surfaces (unfoundedstudios.com)

Audited 2026-08-19, mobile 390x844 (Playwright, GB market pinned via `?country=GB` — the
audit egress IP geo-detects as US and flips the storefront to USD; UK shoppers see GBP).
Site identity verified on every session (title "UnfoundedStudios"). Strict read-only:
no form submitted anywhere; the newsletter popup was dismissed only via its NO THANKS
link; checkout was reached and observed, never filled.

---

### Slow-4G first load of the homepage
- **Should:** Something meaningful within ~3s; usable soon after; no layout jumps.
- **Did:** On slow 4G + 4x CPU throttle, the hero was already fully rendered ~3s in:
  header (burger / bird logo / search / account / cart), campaign photo, "UNFOUNDED /
  World Cup Drop Live!" and a Shop Now pill. DOMContentLoaded at ~7.1s, load at ~13.4s,
  but the page was visually complete and tappable well before that. No visible layout
  shift between the 3s/6s/10s snapshots. First thing the page says: "World Cup Drop
  Live!" (slide 1 of 2; slide 2: "All Nation Items Available Now!").
- **Verdict:** works
- **Shopper impact:** Genuinely fast feel on a bad connection; strong first impression.
- **Screens:** uf-home-slow4g-3s, uf-home-slow4g-10s, uf-home-slow4g-settled

### Newsletter popup
- **Did:** ~15s after load (between the 11.6s and 18.8s snapshots on slow 4G) a
  newsletter modal slides up: "Sign up for our newsletter / Stay informed about new
  collections and discounts / EMAIL / Subscribe / NO THANKS". The panel itself is
  390x287px (bottom third) but its overlay is 390x844 — the full screen dims and
  nothing behind it is tappable until dismissed. NO THANKS dismisses cleanly and it
  did not reappear within the session. The footer asks for the same email again on
  every page.
- **Verdict:** partly
- **Shopper impact:** Full-screen interruption on mobile mid-browse; at least the
  escape hatch is obvious.
- **Screens:** uf-home-slow4g-settled (popup visible), uf-home-newsletter-popup

### Header
- **Should:** Logo home link, menu, search, account, cart with count.
- **Did:** Fixed black header: hamburger, bird logo (→ /), search icon (→ /search
  page), account icon (→ Shopify customer auth), cart icon (→ cart drawer).
  Cart count badge is hidden at 0 and shows "1" after an add — verified.
- **Verdict:** works
- **Screens:** uf-home-header, uf-home-badge-1item

### Menu drawer
- **Did:** Clean full-screen drawer: Home / Shop all / Collections (chevron →
  England Set, Nations Shorts, All products) / Contact, then Account, a United
  Kingdom country selector, Instagram + TikTok icons. All links land correctly.
  (A theme `<style>` leak puts raw CSS text in the Collections link's DOM text —
  `.icon.icon--rotate-90 path { stroke-width : calc(1.5 * 1.5); }` — but it does
  NOT render visibly; screenshot is clean.)
- **Verdict:** works
- **Shopper impact:** Sparse and legible; but see "Collection discoverability".
- **Screens:** uf-home-menu-open

### Homepage top-to-bottom story
- **Did:** Order: (1) hero slideshow — "World Cup Drop Live!" / "All Nation Items
  Available Now!"; (2) "Our latest collections" — three tiles: "SALE Black + Grey
  Items 6", "SALE Nation Polo Sets 10", "SALE Nation Items 28" + Explore All;
  (3) "Latest arrivals" product carousel (SALE Nation Polo Sets / "World Cup Range"
  marquee); (4) full-width banner "Clothing designs to make everyone feel truely
  unique" + View More; (5) an empty dual-tiles section (renders 0px — invisible);
  (6) "The story continues..." photo grid + Follow Us; (7) newsletter + footer.
  The story is coherent: football-nation drop brand with campaign photography.
  Strongest block as a shopper: the hero + "Latest arrivals" carousel (real product
  photos, prices, size chips, one-tap quick-add). Weakest: "The story continues..."
  — four photos that link nowhere except a Follow Us button pointing at the WRONG
  Instagram (below).
- **Verdict:** works
- **Screens:** uf-home-full, uf-home-scroll-02, uf-home-scroll-03, uf-home-scroll-05

### "The story continues..." / Follow Us link
- **Should:** Link to the brand's Instagram.
- **Did:** The only link in the section goes to https://www.instagram.com/digifist/ —
  Digifist is the theme developer's account, not Unfounded's. (The correct
  @unfoundedstudios links exist in the menu and footer icons.)
- **Verdict:** broken
- **Shopper impact:** A shopper tapping Follow Us lands on a Shopify theme agency's
  profile — confusing and trust-denting.
- **Screens:** uf-home-scroll-05

### Sold-out products on the homepage
- **Did:** "Latest arrivals" leads with 6 buyable items (Italy/France/Portugal polos
  and track pants, Brazil track pants) and ends with 2 SOLD OUT England items
  (England Track Pants, England Polo) — badge shown, so sold-out stock is present
  but not dominant on the homepage. However cards say "Available in 5 size" with
  chips like "XS - IN HAND" even when most variants are gone (Italy Polo shows
  "Available in 5 size" but only XS and S are actually purchasable — M/L/XL chips
  are disabled with hidden text "VARIANT SOLD OUT OR UNAVAILABLE"). Hero slide 2
  claims "All Nation Items Available Now!" while 32 of 44 catalogue products have
  no purchasable variant.
- **Verdict:** partly
- **Shopper impact:** The homepage flatters availability; disappointment is deferred
  to the PDP.
- **Screens:** uf-home-scroll-02, uf-home-latest-arrivals-end

### /collections/all browsing
- **Did:** Hero titled "Latest Drop" (breadcrumb "Home / Products"), Filters +
  sort ("Alphabetically, A-Z" default; options incl. Featured, Most relevant, Best
  selling), "Showing 20 of 44 products", 2-col cards with quick-add "+", price, and
  clear SOLD OUT badges on unavailable items (e.g. BIRD SHORTS pair). Numbered
  pagination 1 2 3 → at the bottom (20/page).
- **Verdict:** works
- **Shopper impact:** You can tell sold-out items before the PDP — badge on every
  card, also in search results.
- **Screens:** uf-home-all-top, uf-home-all-scrolled, uf-home-all-pagination-end

### Filters and sorting
- **Did:** Filter drawer: Availability (IN STOCK / OUT OF STOCK) and Price
  (£ FROM / £ TO), Clear All / Apply Filters; sort dropdown present on collections
  and search.
- **Verdict:** works
- **Screens:** uf-home-all-filters

### Collections index / discoverability
- **Should:** A way to browse the catalogue's collections.
- **Did:** /collections lists just three entries: All products, England Set, Nations
  Shorts — the same three as the nav. The store actually has 34 public collections
  (collections.json), including the three "SALE …" tiles on the homepage and oddities
  like "Waffles 20£ Per Item" and "Black And Grey Sweaters Left Over Limited Stock";
  31 of 34 are unreachable through navigation.
- **Verdict:** partly
- **Screens:** uf-home-collections-index

### "Black Friday Discounted Items" collection (August)
- **Should:** Either not exist in August, or contain discounted products.
- **Did:** /collections/black-friday-discounted-items renders hero "Latest Drop",
  breadcrumb "Black Friday Discounted Items", then "Showing 0 of 0 products" and
  "No products in this collection". (Admin-side count says 7, storefront serves 0.)
  Not linked from any nav — reachable only by URL — but public and indexed.
- **Verdict:** broken
- **Shopper impact:** A dead "Black Friday" page in August reads as an abandoned shop.
- **Screens:** uf-home-coll-blackfriday

### "End Of Month Sale" collection
- **Did:** Same as above: "Showing 0 of 0 products / No products in this collection"
  (admin count 26, storefront 0). Created March 2026, still live mid-August.
- **Verdict:** broken
- **Screens:** uf-home-coll-endofmonth

### Do "SALE" collections contain actual discounts?
- **Should:** SALE label ⇒ compare-at price with a visible reduction.
- **Did:** No. The three homepage tiles are literally TITLED "SALE Black + Grey
  Items", "SALE Nation Polo Sets", "SALE Nation Items", but every product card
  everywhere shows price = "REGULAR PRICE" with identical values (e.g. "ITALY POLO
  £23.00 REGULAR PRICE £23.00"). A JSON sweep of the sale collections' products
  found zero compare-at prices. There is no strikethrough price anywhere on the site.
- **Verdict:** broken
- **Shopper impact:** "SALE" is decoration, not a discount — shoppers who click
  through looking for reductions find none.
- **Screens:** uf-home-scroll-02, uf-home-coll-england

### Named collection: England Set
- **Did:** Proper hero photo + real title "England Set", sort "Most Relevant",
  "Showing 2 of 2 products" — ENGLAND POLO £35.00 and ENGLAND TRACK PANTS £43.00,
  BOTH with SOLD OUT badges. A nav-linked collection made 100% of sold-out stock.
- **Verdict:** partly
- **Screens:** uf-home-coll-england

### Search — product queries
- **Did:** /search?q=hoodie → 21 results ("SEARCH RESULTS FOR hoodie 21"), including
  both Bird hoodies (though nation polos outrank the actual hoodies). "bird" → 7/7
  bird items (plus Brazil Track Pants oddly first). "joggers" → 13. Misspelling
  "hodie" → the same 21 results, so fuzzy matching works. Sold-out items appear with
  SOLD OUT badges; Filters + Relevance sort present; paginated "Showing 12 of 21".
- **Verdict:** works
- **Screens:** uf-home-search-results-hoodie, uf-home-search-bird, uf-home-search-misspelt

### Search — typeahead / predictive
- **Should:** Suggestions while typing.
- **Did:** None. The header search icon does a full navigation to the /search page;
  typing "hoodie" there produces no live suggestions — the page keeps saying "Oh no!
  No results found." until you press Enter, which then correctly submits
  (?q=hoodie, 21 results).
- **Verdict:** absent
- **Screens:** uf-home-search-open, uf-home-search-live-hoodie, uf-home-search-enter-hoodie

### Search — empty / gibberish states
- **Did:** Bare /search greets you with headline "Oh no! No results found." before
  you've typed anything. "xzqvbn" → "Oh no! No results found for “xzqvbn”. Please
  try again with a different query." — polite, but no suggestions, no popular
  products, no links out.
- **Verdict:** partly
- **Screens:** uf-home-search-gibberish, uf-home-search-empty

### Reaching answers through search (returns / delivery / size)
- **Did:** "returns" → 1 result: PAGE "Returns Policy" with a VIEW PAGE button —
  policies are indexed and reachable. "delivery" → 29 products (their descriptions
  mention shipping) + the Returns Policy page; no shipping page exists to find.
  "size" → 40 products, no size guide (none exists).
- **Verdict:** works
- **Screens:** uf-home-search-returns, uf-home-search-delivery

### Contact (taps + what you find)
- **Should:** Contact details within a couple of taps.
- **Did:** 2 taps: hamburger → Contact (/pages/contact). The page shows opening
  hours — "Monday to Friday 9am to 9pm (GMT), Saturday 10am to 6pm, Sunday 10am to
  4pm" — and a message form (FIRST NAME / LAST NAME / HOW DO YOU WANT US TO CONTACT
  YOU? EMAIL PHONE SMS / EMAIL / MESSAGE / Send Message). NOT submitted. There is
  no email address, phone number, or postal address on the Contact page itself; the
  direct email ("Get in touch: info@unfoundedstudios.com") lives on About Us, and
  the returns address in the returns policy.
- **Verdict:** partly
- **Shopper impact:** You can reach a form fast, but a shopper who wants an actual
  address/email must hunt on other pages.
- **Screens:** uf-home-contact

### Returns policy
- **Should:** A real, filled-in policy.
- **Did:** 1 tap (footer "Returns Policy" → /policies/refund-policy). Fully
  written, store-specific, not a Shopify default: "You have 14 days from the date
  your order is delivered to let us know… a further 14 days to send the item back";
  contact "info@unfoundedstudios.com"; return address "Unfounded Studios Returns,
  11 Oxted Green, Milford, Surrey, GU8 5DA, United Kingdom"; customer pays return
  postage unless faulty; refunds within 14 days; no automatic exchanges. A second,
  near-identical copy exists at /pages/returns-policy (found via search) — the two
  agree with each other.
- **Verdict:** works
- **Screens:** uf-home-refund-policy, uf-home-returns-page

### Shipping costs before checkout
- **Should:** Shipping cost or at least a rate table somewhere pre-checkout.
- **Did:** Nowhere. /policies/shipping-policy → 404. No shipping/FAQ page. The cart
  drawer shows only "Subtotal £23.00 GBP / Taxes included." — no shipping line. The
  checkout landing page (reached in 5 taps: product card → size → Add To Cart →
  tick "Agree to terms" → Checkout) says "Enter your shipping address to view
  available shipping methods." So the cost is not visible until personal data is
  entered — we stopped there. The only delivery info anywhere is per-product
  description lines (which contradict each other — see consistency sweep).
- **Verdict:** absent
- **Screens:** uf-home-taps-cart-drawer, uf-home-checkout-landing

### Checkout terms gate (observed en route)
- **Did:** The cart drawer has an unticked checkbox "Agree to terms of sale as per
  the merchants terms of service." Tapping Checkout without it does NOTHING — no
  error, no highlight, the drawer just sits there. Tick it and Checkout proceeds to
  a standard Shopify checkout ("Unfounded Checkout", Order summary £23.00).
- **Verdict:** partly
- **Shopper impact:** A silent dead button is a classic abandonment point.
- **Screens:** uf-home-checkout-unticked, uf-home-checkout-landing

### About / brand story
- **Did:** /pages/about-us (footer, 1 tap): real story — "Our Founder Jack O'Connor
  started Unfounded when he was 16…", ethos copy, "Open for Collaborations", and a
  direct email. Notably it does NOT substantiate the homepage meta claim of
  "heavyweight… 100% Organic Cotton" — no materials/quality story anywhere on the
  site; the claim only exists in the meta description Google shows.
- **Verdict:** works
- **Screens:** uf-home-about

### Social proof (reviews / UGC / press / socials)
- **Should:** Some evidence other people buy: reviews, ratings, UGC, press.
- **Did:** Zero reviews or ratings anywhere; no press; no testimonials. The only
  proof mechanism is social: Instagram/TikTok icons (menu + footer, 1 tap) — and
  the dedicated homepage social section links to the wrong account (@digifist).
- **Verdict:** absent
- **Screens:** uf-home-scroll-05, uf-home-footer

### Footer
- **Did:** Newsletter block ("Sign up to find out about future releases and
  promotions."), "Unfounded" link group: Search / About us / Privacy Policy /
  Returns Policy, Instagram + TikTok icons, then "UNFOUNDED STUDIOS / Copyright ©
  2026 Unfounded Limited All rights reserved. VAT No. GB 514170427" and ~14 payment
  icons (Visa, Mastercard, Amex, Apple Pay, Google Pay, Shop Pay, Maestro, UnionPay,
  Discover, Diners, Bancontact, iDEAL, Wero…). All four links + both socials resolve
  (Instagram returns a login-wall to bots but the account is right). Missing from
  the footer: Contact, any shipping info, Terms of Service (which exists, filled,
  at /policies/terms-of-service but is linked only from the cart drawer's "terms"
  checkbox line).
- **Verdict:** partly
- **Screens:** uf-home-footer, uf-home-scroll-05, uf-home-tos

### Trust signals present
- **Did:** VAT number, registered company name (Unfounded Limited), full payment
  icon row, real return address, GB country selector, GBP/auto-currency for
  international visitors, filled privacy policy ("Last updated: April 23, 2026").
- **Verdict:** works
- **Screens:** uf-home-footer, uf-home-privacy

---

## Consistency sweep — exact quotes

1. **Meta description (homepage + og:description):** "We Design Hoodies That Are
   heavyweight and super soft for a affordable price All made out of 100% Organic
   Cotton." — "a affordable price", stray capitalisation, no full stops; and the
   organic-cotton claim appears nowhere on the site itself.
2. **Homepage banner:** "Clothing designs to make everyone feel truely unique" —
   "truely".
3. **Product cards sitewide:** "Available in 5 size" — singular "size", and shown
   even when most variants are sold out (Italy Polo: only XS/S buyable).
4. **Hero slide 2:** "All Nation Items Available Now!" vs 32 of 44 products with no
   purchasable variant, and the nav's own England Set 100% sold out.
5. **Hero slide 1:** "World Cup Drop Live!" — still "Live!" a month after the 2026
   final (July 19); paired with sale names "Black Friday Discounted Items" and "End
   Of Month Sale" (created 27 Nov 2025 and 26 Mar 2026) still published in August,
   both empty: "No products in this collection".
6. **Duplicate products (public):** two "Germany Shorts" (handles germany-shorts-1,
   germany-shorts-copy — both £50), two "Germany Top" (germany-top £50 vs
   germany-top-copy £40 — same name, £10 apart), two "Spain Top" (£50 vs £40), two
   "Spain Shorts" (both £50). The "-copy" handles are live URLs a shopper can land on.
7. **Colourway price mismatch:** BIRD SHORTS - BLACK £30.00 vs BIRD SHORTS - GREY
   £27.00 (same product line, no explanation).
8. **Delivery promises disagree, no policy to arbitrate:** Italy Polo description:
   "Please Allow 2-5 Working Days For Item To Be Shipped"; Bird Hoodie - Grey:
   "Shipping - In Hand Please Allow 5-7 Working Days From Purchase / Pre Order -
   Please Allow 3-4 Weeks For Your Item". /policies/shipping-policy is a 404.
9. **Two returns documents:** /policies/refund-policy ("Refund Policy") and
   /pages/returns-policy ("Returns Policy") — content matches today, but it's
   duplicated maintenance.
10. **Cart drawer:** "Agree to terms of sale as per the merchants terms of service."
    — missing apostrophe ("merchant's"), and the gate fails silently.
11. **Collection hero reuse:** /collections/all, and the empty sale collections all
    display the same hero title "Latest Drop" regardless of what the breadcrumb says.
12. **Variant naming exposed:** size chips read "XS - IN HAND", with hidden a11y text
    "VARIANT SOLD OUT OR UNAVAILABLE" on disabled chips — inventory jargon in the UI.
13. **Site title:** "UnfoundedStudios" (no space) as the tab title on every page.

## Tap counts (comparison hooks)
- Landing → contact: **2** (menu → Contact; but no direct details there — email is
  1 further tap on About us)
- Landing → returns policy: **1** (footer link)
- Landing → shipping cost: **unreachable** — 5 taps get you to the checkout landing
  which still says "Enter your shipping address to view available shipping methods";
  no cost is ever shown pre-address (no shipping policy page exists)
- Landing → proof others bought: **1** (footer Instagram icon — external; on-site
  proof does not exist)
- Sold-out visible pre-PDP: yes — SOLD OUT card badges in collections and search
- Add-to-cart feedback: cart drawer opens with item, header badge shows count
- Popup: newsletter modal ~15s after load, full-screen overlay (panel bottom third)
