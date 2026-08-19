# Edge conditions & accessibility — Unfounded Studios (unfoundedstudios.com)

Live Shopify store, theme "Release" v2.0.5 (theme store id 2698). Site identity verified by
harness on every session. Note: the audit egress IP geo-detects as US, so every session saw
USD prices ($32 Italy Polo = £23 etc.) with a "UNITED STATES" country selector; switching
country requires submitting the /localization form, which the read-only rules forbid, so all
observations are in the USD presentation. STRICT READ-ONLY observed: cart/checkout-landing
only, no form submissions other than the permitted native /cart/add.

### Keyboard-only purchase path (desktop 1440x900)
- **Should:** Tab from the top with visible focus; open nav, reach a product, pick a size, add
  to cart, reach the cart, land on checkout entry — without a mouse.
- **Did:** First Tab hits a working "Skip To Content" link. Every control shows a real 2px
  outline focus ring (verified on nav links, product cards — boxed outline on "ITALY POLO" —
  and a double-ring on Add To Cart). Desktop nav is plain inline links (HOME / SHOP ALL /
  COLLECTIONS / CONTACT), no drawer needed; a product card is reachable ~21 tabs from the top
  (two swiper prev/next buttons sit in the tab order on the way). Enter opens the PDP. Size
  radios are reachable by Tab; Arrow keys move selection and **skip disabled sold-out sizes**
  (XS → XL directly on Italy Polo, S/M/L struck out), updating the URL ?variant. Enter on Add
  To Cart opens the cart drawer with focus moved onto its Close button; Tab cycles cleanly
  inside the drawer (item link → qty −/input/+ → remove → terms checkbox → terms link → View
  Cart → Checkout → Close, properly trapped). Escape closes the drawer and — unusually good —
  **returns focus to the Add To Cart button**. Hurdle: the drawer (and cart page) has an
  "Agree to terms of sale" checkbox; Enter on Checkout while unticked does nothing except a
  native browser bubble "Please check this box if you want to proceed." Space ticks it, Enter
  then lands on the real Shopify checkout (Checkout – Unfounded). Cart page is equally
  keyboard-clean: 29 tabs from top to Checkout, well-labelled qty buttons, order-note
  accordion, same terms gate, and Enter lands on checkout entry. Nothing was IMPOSSIBLE.
  Awkward: remove-item is an unlabelled bare link; the quick-buy size chips on product cards
  ("XS/S/M") are focusable `div`s, not buttons, so Enter does nothing on them; the swiper
  arrows add noise to the tab order.
- **Escape behaviour:** cart drawer — closes, focus returned (excellent). Search drawer —
  opens with focus in the input, Escape closes but drops focus to BODY. **Mobile menu drawer —
  Escape does NOT close it** and focus never moves into it on open; you must Tab to its close
  button. Newsletter popup exists in the DOM but never actually displayed in any session, so
  its Escape behaviour was unobservable.
- **Verdict:** works
- **Shopper impact:** A keyboard user can genuinely buy. The terms checkbox is the one stumble
  — if the native bubble is missed, Checkout just silently does nothing.
- **Screens:** uf-edge-kbd-01-first-tabs, uf-edge-kbd-02-skiplink, uf-edge-kbd-05-product-focus,
  uf-edge-kbd-07-size-focus, uf-edge-kbd-08-atc-focus, uf-edge-kbd-15-drawer-tabs,
  uf-edge-kbd-18-terms-unticked, uf-edge-kbd-19-checkout-entry, uf-edge-kbd-21-cart-page,
  uf-edge-kbd-23-search-open, uf-edge-kbd-24-menu-open-mobile

### Screen-reader semantics (ARIA/roles/labels inspection — no live SR used)
- **Should:** Sizes announced with availability state; add-to-cart confirmed audibly; cart
  controls labelled; sane landmarks/headings; one h1 per page; honest image alts.
- **Did:** Genuinely good on the PDP: exactly one h1; size radios live in a fieldset with
  legend "SIZE + current choice"; disabled sold-out radios carry visually-hidden text
  "VARIANT SOLD OUT OR UNAVAILABLE" — an SR user hears both the size and its state; price sits
  in a role=status region; "Only N left in stock" is a role=status live region; qty buttons are
  labelled per-product ("Decrease quantity for Italy Polo"). Add-to-cart has no aria-live
  announcement, but focus is programmatically moved into the opened drawer (whose visible
  heading is "Your cart 1"), which is an acceptable announcement pattern. Landmarks are sane
  (header/nav×4/main/footer) and a skip link exists. The rot: **homepage has zero h1** and the
  **cart page has zero h1** ("Your cart" is styled text, not a heading); two homepage product-
  card H3s contain leaked raw CSS ("England Track Pants :root { --color-badge-discount-
  background:#EF2D2D;…") that a screen reader would read aloud as heading text; hero/banner
  image alts contain raw HTML markup (alt="<p>World Cup Drop Live!</p>",
  alt="<h2>All Nation Items Available Now!</h2>"); the header cart link has no label (an SR
  hears just the badge number "2, link"); remove-item links in drawer and cart have no
  accessible name at all; the newsletter-close, back-to-top and sticky-bar submit buttons are
  unlabelled; and the terms checkbox id #Terms-Conditions is duplicated (cart page + drawer),
  breaking label association. All content imgs do have alt attributes (0 missing site-wide).
- **Verdict:** partly
- **Shopper impact:** A screen-reader user can pick a size and knows what's sold out — better
  than many stores — but navigates by headings into CSS soup on the homepage and can't tell
  which unlabelled link removes an item.
- **Screens:** uf-edge-recon-home, uf-edge-recon-pdp

### 200% zoom (desktop viewport 720x450)
- **Should:** Full home → product → size → add → cart → checkout-entry path with no overlap,
  clipping or horizontal scroll.
- **Did:** At 720px the layout drops cleanly to the mobile breakpoint (hamburger replaces the
  inline nav). Zero horizontal overflow on home, PDP, open drawer, cart, and the checkout
  entry. Buy box fully usable; the cart drawer at this size keeps item, terms checkbox and
  Checkout all on-screen (drawer 360px wide); ticking terms and pressing Checkout landed on
  Shopify checkout. Only nit: scroll-reveal headings ("Our latest collections") sit at low
  opacity until their fade-in triggers.
- **Verdict:** works
- **Shopper impact:** None negative — a low-vision shopper at 200% gets the well-tested mobile
  layout and can buy end-to-end.
- **Screens:** uf-edge-zoom-01-home, uf-edge-zoom-03-pdp, uf-edge-zoom-04-pdp-buybox,
  uf-edge-zoom-05-drawer, uf-edge-zoom-06-cart, uf-edge-zoom-08-checkout

### Landscape mobile (844x390)
- **Should:** Homepage, PDP and cart remain usable in a short, wide viewport.
- **Did:** No horizontal overflow anywhere. PDP shows image left / buy box right with the size
  chips and sold-out strikethroughs intact. The cart drawer fits the 390px height with item,
  terms and Checkout all visible without inner scrolling. Cart page fine. Cost: the sticky
  header is 96px (~25% of the height) and a sticky add-to-cart bar takes another ~81px on the
  PDP, so the actual content window gets tight — awkward, not broken.
- **Verdict:** works
- **Shopper impact:** Phone-sideways shoppers lose some window to sticky chrome but nothing
  breaks or clips.
- **Screens:** uf-edge-land-01-home, uf-edge-land-03-pdp, uf-edge-land-04-buybox,
  uf-edge-land-05-drawer, uf-edge-land-06-cart

### Reduced motion (prefers-reduced-motion: reduce)
- **Should:** Auto-playing motion stops or calms when the OS asks for reduced motion.
- **Did:** Ignored outright. With reducedMotion emulated (media query confirmed matching), the
  hero carousel still auto-advanced within 9s, its circular progress animation kept running,
  and the running-animation census was identical to the no-preference run (5 running: swiper
  transform transitions, bullet fades, circle-progress). The same swiper component drives the
  PDP gallery and recommendation carousels. Nothing is lost content-wise — slides remain
  reachable via arrows/pagination — the site simply never reduces motion.
- **Verdict:** broken
- **Shopper impact:** Motion-sensitive shoppers get the full auto-playing hero regardless of
  their OS setting.
- **Screens:** uf-edge-rm-01-home

### JavaScript disabled
- **Should:** Page renders; ideally a native form fallback can still add to cart.
- **Did:** Surprisingly strong rendering: homepage fully renders with 31/31 images loaded (no
  lazy-load skeletons), and the hamburger menu opens natively because it's a details/summary
  element. PDP renders title, price, size chips (sold-out slashes included), qty and Add To
  Cart. The form posts natively to /cart/add and the server redirects to a fully working cart
  page (item, qty input, subtotal, checkout button). Two real losses: (1) the size radios are
  associated to the form but /cart/add only reads the hidden variant id that JS normally
  syncs — so **whatever size you tick, the default variant (XS) is what gets added**; (2) the
  Shop Pay button renders as an empty dead grey pill.
- **Verdict:** partly
- **Shopper impact:** A no-JS (or failed-JS) shopper can browse everything and can add to cart
  — but silently gets the wrong size unless the default happens to be theirs.
- **Screens:** uf-edge-nojs-01-home, uf-edge-nojs-03-menu, uf-edge-nojs-05-pdp-buybox,
  uf-edge-nojs-07-cart, uf-edge-nojs-08-pdp-italy

### Slow-4G cold load (oldAndroid 360x800, throttled)
- **Should:** Progressive, stable render; usable within a tolerable wait.
- **Did:** t=3s: header, hamburger, hero photo AND headline ("World Cup Drop Live!") already
  painted, fonts still loading but text visible (no invisible-text flash), 6/31 images in —
  it already looks like a shop. t=5s: fonts loaded, collection card images streaming in
  (22/30). Load event at 8.6s; t=10s and t=15s identical to 5s (remaining images are
  below-fold lazyloads). Layout: total page height shifted below the fold between 3s and 5s
  (3679→3252px) but the above-fold hero never jumped. Tapping through to a PDP on the same
  throttle: usable at ~3s, load event 4.3s, all 24 images in by 6s, Add To Cart enabled.
  Feels usable at ~3s, comfortable by 5s.
- **Verdict:** works
- **Shopper impact:** A cheap-phone/slow-network shopper gets a stable, shoppable page in
  about 3 seconds — genuinely good.
- **Screens:** uf-edge-slow4g-3s, uf-edge-slow4g-5s, uf-edge-slow4g-10s, uf-edge-slow4g-15s,
  uf-edge-slow4g-pdp-3s, uf-edge-slow4g-pdp-loaded

### Reload + back/forward through a 5-page trail
- **Should:** History restores each page with state (cart count, scroll) intact.
- **Did:** Trail: home → /collections/all (scrolled to 1000px) → PDP (size clicked, added to
  cart, badge 1) → cart → contact. Reload on contact: fine, badge 1. Back ×4: every URL and
  title correct, scroll positions restored exactly (collections back at 1000px, PDP at 737px)
  — but the **cart badge renders stale from cache: PDP/collections/home all show badge 0**
  even though the cart holds 1 item. Forward ×2: same correct pages, same stale 0 badge. The
  cart page itself always shows the truth. Variant selection uses replaceState, so Back never
  wades through size changes — good.
- **Verdict:** partly
- **Shopper impact:** After adding to cart, pressing Back tells you your cart is empty. A
  shopper who trusts the badge re-adds (duplicate) or assumes the site lost their item.
- **Screens:** uf-edge-hist-01-after-backs, uf-edge-hist-02-after-fwds

### Direct-land on a product URL, fresh session (the Instagram path)
- **Should:** A cold visitor from a shared link gets a self-sufficient product page.
- **Did:** Fresh context straight to /products/morocco-top: full PDP in 4.2s — photo, "Morocco
  Top", $56.00 (USD geo-pricing), "Taxes included", shipping note, size chips, enabled Add To
  Cart. No cookie banner, no popup obstruction (the newsletter modal exists in DOM but never
  displayed). Header, logo-home link and hamburger all present for onward browsing. Cold
  add-to-cart worked first tap: drawer opened, badge 1.
- **Verdict:** works
- **Shopper impact:** The Instagram tap-through lands on a page that sells itself; no gates in
  the way.
- **Screens:** uf-edge-direct-01-land, uf-edge-direct-02-buybox, uf-edge-direct-03-atc

## Comparison hooks captured
- Sold-out signalling on PDP: disabled, struck-through size chips + hidden SR text "VARIANT
  SOLD OUT OR UNAVAILABLE"; no notify/back-in-stock mechanism seen on tested PDPs. Product
  cards claim "Available in 5 size" even when 3 of 5 are sold out.
- Add-to-cart feedback: side drawer ("Your cart N") + header badge; focus moved into drawer.
- Checkout gate: "Agree to terms of sale" checkbox in BOTH drawer and cart page (duplicate
  element id); unticked Checkout yields only the native browser bubble.
- Checkout branding: standard Shopify checkout titled "Checkout – Unfounded" with express
  wallets — brand held.
- Shipping cost before checkout: not shown anywhere pre-checkout; only "Taxes included" and a
  PDP note "Please Allow 2-5 Working Days For Item To Be Shipped".
- Currency: geo-defaults to USD for US visitors; GBP only via the country selector
  (/localization form).
