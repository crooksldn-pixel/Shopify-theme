# 11 — Marcus, the tinkerer who pokes every control before he'll trust a shop with money
**Device:** iPhone-class 390x844 first, then desktop 1440x900, good connection · **Goal:** stress every interactive control — filters, sort, currency, search, gallery, quick-add, cart — and only buy if the machinery holds up · **Mood:** playful-sceptical; "show me what breaks"

### Step 1 — Landed on the homepage and poked the hero slideshow
**Did:** Let the page settle, watched the hero for 8 seconds, then tapped the "02" pagination dot. Also scrolled far enough to make the floating back-to-top circle appear and tapped that.
**Got:** Two slides ("World Cup Drop Live!" / "All Nation Items Available Now!") with numbered dots 01/02, no arrows. It never auto-advanced in 8s with my reduced-motion setting on — which is actually the correct behaviour. Dot tap swapped slides cleanly. Back-to-top zipped me to scrollY 0.
**Expected:** Dots that work, autoplay that respects my motion settings. Both delivered.
**Felt:** "Off to a decent start — the slideshow respects reduced motion, most sites don't bother." The "All Nation Items Available Now!" claim I already distrust, but that's copy, not a control.
**Next:** continued
*(screens: u11-01-home-arrive, u11-02-hero-after-8s, u11-04-hero-after-tap)*

### Step 2 — The newsletter popup interrupted, as it would three more times
**Did:** ~15s in, a full-screen-dimming "Sign up for our newsletter" sheet slid up over the bottom third. Dismissed with NO THANKS. (It reappeared in EVERY fresh browsing session I opened — and later it fired on top of my open cart drawer and over the hoodie buy box mid-poke.)
**Got:** Dismiss works and it stays gone for the session. But its 10-second timer doesn't care what you're doing — it landed over the cart drawer once, exactly where the checkout button sits.
**Expected:** If you must popup, don't cover the money buttons.
**Felt:** "First tap of every visit is NO THANKS. The one time it dropped over my cart drawer I genuinely thought the drawer had broken."
**Next:** continued
*(screens: u11-03-popup, u11-15-quickadd-added — popup over cart drawer, u11-41-buy-area — popup over buy box)*
**Verdict: fix** (timing/placement, not existence)

### Step 3 — Opened the search drawer and found the best control on the site
**Did:** Tapped the header magnifier. A full-screen search drawer opened in place (no page navigation). Typed "polo" slowly. Then typed "bird" and hit the CLEAR pill. Then pressed Enter on a query.
**Got:** Live predictive results as I typed: POPULAR SEARCHES, matching COLLECTIONS, and product cards with photo, price, size chips and a quick-add "+" — all inside the drawer. CLEAR empties the box and keeps the drawer open. Enter lands on a proper results page… with a monster of a URL: `?q=polo&id=57332093944140&predictive-search-15710557176140-option%5B1%5D=XS+-+In+Hand&…` — the drawer's size-radio state leaks into the submitted query string.
**Expected:** A search icon that navigates to a bare search page (that's what the store's own /search page does — it has NO typeahead at all, oddly).
**Felt:** "This drawer is genuinely great — I could shop entirely from it. The wet-dog URL it hands the results page is the kind of thing only I would notice, but it tells me nobody's looking closely."
**Next:** continued
*(screens: u11-09-search-open, u11-10-search-typed, u11-11-search-results, u11-16-search-cleared)*
**Verdict: keep** (drawer + predictive + CLEAR); **fix** the leaked form params in the submitted URL; **fix** that the standalone /search page lacks the same typeahead

### Step 4 — Quick-add "+" from a card, all the way into the cart
**Did:** In the search drawer, tapped the "+" on the Italy Polo card.
**Got:** A "Choose options" bottom sheet — a proper mini-PDP: photo (with the size-chart image peeking as slide 2), price, all five size pills with sold-out ones struck through, first available size preselected, ADD TO CART. Tapping it dropped "Italy Polo XS - In Hand £23.00" into the cart and slid the cart drawer in. /cart.js confirmed the line.
**Expected:** Either straight-add of a random size (bad) or a size prompt (good). Got the good one.
**Felt:** "Textbook. Though 'XS - IN HAND' as a size name is warehouse language on my receipt, and the sheet preselecting XS means a lazy thumb buys an XS by accident."
**Next:** continued
*(screens: u11-12-search-italy, u11-13-quickadd-sheet, u11-15-quickadd-added)*
**Verdict: keep** (flow); **fix** the "- In Hand / - Pre Order" variant naming

### Step 5 — Sort dropdown on /collections/all
**Did:** Opened the custom sort dropdown (default "Alphabetically, A-Z"), picked "Price, Low To High".
**Got:** Nine options (Featured, Most Relevant, Best Selling, A-Z, Z-A, price both ways, date both ways). Grid reordered correctly — £18 Argentina Shorts first — and the URL took `?sort_by=price-ascending`, so it's shareable and survives refresh. Pagination links (1 2 3) carry the sort along.
**Expected:** Exactly this.
**Felt:** "No notes. Why is the default A-Z though? 'Featured' exists and nobody shops alphabetically."
**Next:** continued
*(screens: u11-18-sort-open, u11-19-sorted-asc, u11-27-pagination)*
**Verdict: keep**; **don't care** about the A-Z default, though Featured would sell better

### Step 6 — The filter drawer, aka the control this store needs most
**Did:** Opened Filters → Availability accordion → ticked IN STOCK → Apply Filters. Then added a Price band £20–£30. Then Clear All.
**Got:** "Showing 12 of 44 products", zero SOLD OUT badges — the exact dozen buyable items in one tap, out of a catalogue that is otherwise ~73% graveyard. Price band stacked correctly (6 of 44: both polos at £23/£25 and the three £30 track pants…). Removable chips appeared for each active filter ("In stock ×", "£20.00 - £30.00 ×"). Clear All reset the filters and kept my sort. URL carries everything (`filter.v.availability=1&filter.v.price.gte=20…`).
**Expected:** Filters that half-work, like most small stores.
**Felt:** "This is the single most valuable control on the site and it's flawless — it turns a mostly-dead catalogue into a real shop. It should not be hiding in a drawer; 'In stock' deserves to be a default or a one-tap toggle on the grid."
**Next:** continued
*(screens: u11-20-filter-drawer, u11-21-availability-open, u11-23-instock-applied, u11-24-price-band, u11-25-price-filtered, u11-26-cleared)*
**Verdict: keep, and promote it** — surface an "In stock only" toggle on the grid itself

### Step 7 — Country/currency selector: GBP↔USD round trip
**Did:** On mobile the control hides in the hamburger menu ("United Kingdom"). Tapped it → a full-screen "Change country" page containing exactly one pill dropdown. Opened it — an unsearchable A-Z list of ~200 countries starting at Afghanistan (AFN|؋) — scrolled to United States (USD|$), picked it. Checked prices, then switched back. Desktop: the same picker sits in the header with a flag.
**Got:** Italy Polo flipped £23.00 → $32.00 (correct £×1.38 rounded), collection cards followed ($25 Argentina Shorts), cart.js currency switched to USD, and the choice persisted across navigation. Back to UK: £23.00 again. Nothing desynced.
**Expected:** Currency that half-changes and a cart that keeps the old one — the classic bug. Didn't happen.
**Felt:** "The maths is airtight. But a whole full-screen page for one dropdown, and no search box on a 200-country list, is a lot of ceremony on mobile. Two taps of scrolling to find the U."
**Next:** continued
*(screens: u11-29-menu-country, u11-30-country-list, u11-30b-country-open, u11-31-pdp-usd, u11-33-collection-usd, u11-32-pdp-back-gbp)*
**Verdict: keep** (correctness); **fix** the mobile ergonomics (searchable list, skip the interstitial panel)

### Step 8 — Gallery and lightbox on the flagship hoodie
**Did:** On bird-grey-hoodie (5 photos): tapped thumbnails, tapped the main image, used the lightbox arrows, double-tapped to zoom, closed with X.
**Got:** Thumbnail strip works; tap opens a full-screen PhotoSwipe lightbox; double-tap zooms into the actual 4284px original — I could count the heather flecks in the fleece. Arrows page through, X closes, position preserved.
**Expected:** A cramped mobile zoom that fights my fingers.
**Felt:** "Best-in-class for a store this size. Shame the £40 Morocco Top — a thing you can actually BUY — gets one single photo while this sold-out hoodie gets five."
**Next:** continued
*(screens: u11-34-hoodie-top, u11-36-lightbox, u11-37-lightbox-zoomed, u11-38-lightbox-next)*
**Verdict: keep** (the control); the photo-coverage imbalance is a catalogue problem, not a UI one

### Step 9 — The dead controls on the sold-out PDP
**Did:** Still on the hoodie (0 of 10 variants buyable): tapped a struck-out "M - IN HAND" pill. Tapped the fully-coloured purple "Buy with shop" button. Tried "MORE PAYMENT OPTIONS".
**Got:** Sold-out pill: absolutely nothing — no message, no shake, no explanation. Purple Shop button: nothing — URL unchanged, no sheet, no iframe, no error, on a button that looks 100% live under a greyed-out "Sold Out". "MORE PAYMENT OPTIONS" renders as a normal underlined link but is actually disabled — the tap is swallowed. The quantity stepper meanwhile happily counts 1, 2, 3 of a product that cannot be bought. Ten size pills say the same five sizes twice ("IN HAND" row + "PRE ORDER" row), all struck.
**Expected:** Dead things should look dead; live-looking things should do something. Here it's inverted.
**Felt:** "This is the part where the shop lies to my thumbs. Three tappable-looking controls, zero responses. If I hadn't been testing deliberately I'd have blamed my phone."
**Next:** continued — but this is where a real version of me starts distrusting the store
*(screens: u11-39-size-row, u11-40-soldout-tap, u11-41-buy-area, u11-42-shoppay-tap, u11-43-mpo-tap)*
**Verdict: fix, urgently** — hide/disable the payment buttons on sold-out products, and make sold-out pill taps say something (ideally "email me when it's back", which doesn't exist anywhere)

### Step 10 — Cart drawer: steppers, note field, terms gate
**Did:** Added Italy Polo XL - In Hand (£23, the size that's actually in stock) from the PDP. In the drawer: + stepper, − stepper, closed with X, reopened via the header cart icon. Hunted for the note field, found it only on the /cart page behind an "Order note" expander; typed a test line, then cleared it. Tapped Checkout with the terms box unticked, then ticked it and went through.
**Got:** Drawer slides in on add with correct line and subtotal. Steppers: £23.00 → £46.00 → £23.00, quantity input tracks, all AJAX — though the drawer rebuilds its DOM on every tap (my automation caught stale elements; a fast human thumb can feel the buttons "replace" under it). Header cart icon opens the drawer, not the page — good. No note field in the drawer; the /cart "Order note" textarea accepted my text but /cart.js kept `note: ""` even after a change event — as far as I can tell that field isn't wired to anything. Unticked Checkout: silent-looking, but a native bubble does pop: "Please check this box if you want to proceed." Ticked → checkout.
**Expected:** Steppers that re-total (yes), a note that saves (apparently no), a checkout button that explains itself (borderline).
**Felt:** "The maths never slipped once, which is what I actually care about. The note field being decorative is very on-brand for this site: nice furniture, wires missing. And 'Agree to terms of sale as per the merchants terms of service.' — the missing apostrophe on a legal line is free character."
**Next:** continued
*(screens: u11-44-xl-picked, u11-45-drawer-open, u11-58-drawer-qty2, u11-47-cart-reopen, u11-48-cart-page, u11-49-note-typed, u11-51-checkout-blocked)*
**Verdict: keep** steppers/drawer; **fix** the unwired order note; **fix** the terms gate (pre-tap hint or drop it — an extra mandatory tap on the money path)

### Step 11 — Desktop pass: hover states and sticky things
**Did:** Re-ran the tour at 1440x900: scrolled the home, hovered product cards, hovered the PDP gallery, scrolled the PDP, opened search, redid a drawer add.
**Got:** Sticky header (position:sticky, stays at top). Country picker promoted to the header with a Union Jack. Product cards hover-swap to a second image (opacity crossfade) and the quick-add is simply always visible rather than hover-revealed. PDP: BOTH columns sticky, so the buy box rides along while you scroll the gallery — the Sold Out button was still parked at the top of my viewport 900px down. Gallery cursor becomes nwse-resize (zoom affordance) and the same lightbox opens. Search drawer identical to mobile, predictive included. Collection page shows "Showing 12 of 44 products" beside the Filters pill with my "In stock ×" chip — tidier than mobile.
**Expected:** Mobile-first themes often ship desktop as an afterthought.
**Felt:** "Desktop is actually the more polished surface — sticky buy column is a nice touch. Nothing new broke, nothing mobile-broken got fixed either."
**Next:** continued
*(screens: u11-53-desktop-home, u11-54-desktop-scrolled, u11-55-card-hover, u11-56-desktop-pdp-sticky, u11-57-desktop-search)*
**Verdict: keep**

### Step 12 — The machinery held, so I bought the thing
**Did:** The controls that matter to a purchase — filters, currency, cart maths, steppers — all passed. Kept my Italy Polo XL £23 (one of 2 sizes genuinely left), ticked the terms box, hit Checkout.
**Got:** Branded "Unfounded Checkout" door: bird logo, Order summary £23.00 (matching the cart exactly), Shop Pay + Google Pay express buttons, Contact/Delivery form with Country pre-set to United Kingdom. Stopped at the door as always. Shipping cost still unknown — the page wants my address before it will name a price, and no page on the site ever names one.
**Expected:** A subtotal that matched. It did, in two currencies, all session.
**Felt:** "I trust their arithmetic completely and their sold-out UI not at all. I'm buying because the polo's £23 and the cart never lied to me — but I still don't know what delivery costs, which is the one number no amount of poking could extract."
**Next:** stopped at the checkout door, per the rules
*(screens: u11-50-before-checkout, u11-52-checkout-door)*

### Control scorecard (tinkerer's verdicts)
| Control | Verdict |
|---|---|
| Hero slideshow dots (reduced-motion-aware) | keep |
| Back-to-top button | keep |
| Newsletter popup | fix — 10s timer fires over cart drawer/buy box |
| Header search drawer + predictive + CLEAR | keep (best control on the site) |
| Search submit URL leaking predictive params | fix |
| /search page having no typeahead (drawer does) | fix |
| Quick-add "+" → "Choose options" sheet | keep |
| Variant names "XS - In Hand / Pre Order" in UI & cart | fix |
| Sort dropdown (9 options, URL param) | keep |
| Filter drawer: availability + price, chips, Clear All | keep — and promote "In stock" to the grid |
| Pagination carrying sort/filters | keep |
| Country/currency selector correctness (GBP↔USD) | keep |
| Country selector mobile UX (interstitial + unsearchable 200-entry list) | fix |
| Gallery thumbnails / PhotoSwipe lightbox / full-res zoom | keep |
| Sold-out size pill (dead tap, no message) | fix |
| Active-looking "Buy with shop" + disabled-but-styled-live "More payment options" on sold-out PDP | fix urgently |
| Qty stepper active on sold-out product | fix |
| Cart drawer steppers + live totals | keep |
| Header cart icon opening drawer | keep |
| Order note field (doesn't persist to cart) | fix or remove |
| Terms-of-sale checkbox gate | fix (or at least pre-empt the dead tap) |
| Theme/display toggles | none exist — don't care |
| Desktop stickies + hover image swap + zoom cursor | keep |

## Outcome
**Bought / didn't:** Bought — Italy Polo, XL - In Hand, £23.00; reached the branded checkout door with the correct total and stopped.
**Total time:** ~40 minutes (25 mobile, 12 desktop, 3 changing countries for sport).
**Worst moment:** The sold-out hoodie's buy box: a greyed "Sold Out" button sitting directly above a fully-lit purple "Buy with shop" button and an underlined "MORE PAYMENT OPTIONS" link — and all three of my taps died in silence. A page that ignores taps teaches you not to trust any button on the site.
**Best moment:** Ticking "IN STOCK" in the filter drawer and watching 44 mostly-dead products collapse to exactly the 12 real ones — instantly, with a removable chip and a shareable URL. Honourable mention: double-tap zoom serving the true 4284px photo.
**Would they come back?** Yes — of the poke-everything crowd, this store passes the tests that guard your money (cart maths, currency, filters) and fails only the ones that guard its own reputation (dead buttons, decorative note field, popup timing). Marcus returns, but he'll filter to in-stock first thing, every time.
**One thing that would have changed the outcome:** Nothing was needed to convert *me* — but killing the live-looking payment buttons on sold-out pages (and putting a notify-me there instead) is the difference between "quirky indie shop" and "is this site even maintained?" for every less patient shopper.
