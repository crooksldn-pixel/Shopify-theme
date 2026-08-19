# Raw feature sweep — Product page (PDP), Unfounded Studios

Audited 2026-08-19 (mobile 390x844 first, desktop pass on bird-grey-hoodie).
Products studied: /products/bird-grey-hoodie (£35, ALL sizes sold out),
/products/italy-track-pants (£30, 1/5 sizes), /products/morocco-top (£40,
single variant S, in stock), /products/argentina-shorts (£18, 1/5, XL only).
Note on currency: the store geolocated our US egress IP and displayed USD with
a header country picker ("UNITED STATES"). All observed prices are the GBP
prices converted at 1.3829 and rounded up to whole dollars (£35→$49, £40→$56,
£30→$42, £23→$32, £18→$25). Maths are internally consistent; UK shoppers see
GBP.

### Gallery — photo count and quality (flagship)
- **Should:** Enough photos, at good enough quality, to judge a garment you cannot touch.
- **Did:** Bird Grey Hoodie: 5 photos — front flat lay, back flat lay, two on-model street shots (golden-hour estate backdrop), one more flat. Source files are genuinely high-res (up to 4284x5712). Italy Track Pants: 5 (flat lays showing the zip-off legs converting shorts→pants, one on-model, one colourways+size-chart image). All images have `alt: null`.
- **Verdict:** works
- **Shopper impact:** The flagship looks like a real brand shot it. A shopper can see drape, cuffs, panel seams, and how the hood sits.
- **Screens:** uf-pdp-hoodie-01-top, uf-pdp-italy-01-top

### Gallery — photo coverage across the catalogue
- **Should:** Every product gets comparable coverage.
- **Did:** Morocco Top (£40, in stock, buyable NOW): exactly 1 photo — a front flat lay. No back view, no on-model, nothing. Argentina Shorts: 2 photos (front flat lay + colourways/size-chart image). The products you can actually buy are the worst-photographed.
- **Verdict:** partly
- **Shopper impact:** £40 for a jumper you have seen only the front of.
- **Screens:** uf-pdp-morocco-01-top, uf-pdp-argentina-01-top

### Gallery — swipe and thumbnails (mobile)
- **Should:** Swipeable gallery with thumbnails.
- **Did:** Swiper carousel, horizontal swipe works, thumbnail strip below the main image with current-thumb highlighted. Grey placeholder tiles are visible around the photo while adjacent slides lazy-load — slightly scruffy on slower loads but functional.
- **Verdict:** works
- **Screens:** uf-pdp-hoodie-01-top, uf-pdp-italy-01-top

### Gallery — zoom
- **Should:** Tap to zoom close enough to judge fabric.
- **Did:** Tap opens a full-screen PhotoSwipe lightbox with prev/next arrows and close X. Double-tap zooms in and loads the full 4284x5712 original — heather flecks in the fleece are individually visible. This genuinely answers "is it heavyweight/soft-looking?" as far as any photo can. (No written fabric spec anywhere, though — see Descriptions.)
- **Verdict:** works
- **Screens:** uf-pdp-hoodie-05-after-tap-image, uf-pdp-hoodie-08-lightbox-zoom

### Size presentation and preselection
- **Should:** One row of sizes; the first available size selected or a deliberate "choose a size" state.
- **Did:** Sizes are outlined pill radios under a "SIZE" legend. The first AVAILABLE size is auto-preselected (Italy: S preselected; Argentina: XL preselected) and the legend echoes it. BUT on Bird Grey Hoodie the size row is 10 pills: "XS - IN HAND" … "XL - IN HAND" then "XS - PRE ORDER" … "XL - PRE ORDER" — fulfilment mode is baked into the variant names (with a stray double space in "XL  - Pre order"). On sold-out products the preselected pill is a disabled sold-out size (XS), i.e. the page "selects" something you cannot buy.
- **Verdict:** partly
- **Shopper impact:** Ten crossed-out pills that say the same five sizes twice reads as clutter, and "In Hand" vs "Pre Order" is never explained beyond one shipping line.
- **Screens:** uf-pdp-hoodie-02-sizes-buy, uf-pdp-italy-02-sizes, uf-pdp-argentina-02-sizes

### Sold-out size appearance and tap behaviour
- **Should:** Sold-out sizes visibly distinct; tapping one either explains itself or offers notify.
- **Did:** Sold-out sizes are greyed with a diagonal strikethrough — visually unmistakable. Tapping one does absolutely nothing: no selection change, no message, no button change (verified on Italy M/L and hoodie L). Hidden accessibility text on EVERY size label — including the in-stock ones — reads "VARIANT SOLD OUT OR UNAVAILABLE", so a screen reader hears the available S announced as sold out too.
- **Verdict:** partly
- **Shopper impact:** Sighted shoppers get a clear signal; anyone tapping expecting an explanation gets dead air, and screen-reader users are actively told lies.
- **Screens:** uf-pdp-italy-02-sizes, uf-pdp-italy-04-soldout-tap

### Stock level visibility
- **Should:** Some sense of urgency/stock where relevant.
- **Did:** In-stock PDPs show an alarm-clock line "Only 3 left in stock. Order soon." (Italy) / "Only 1 left in stock. Order soon." (Morocco, Argentina). Genuine per-variant counts.
- **Verdict:** works
- **Screens:** uf-pdp-italy-02-sizes, uf-pdp-morocco-02-buy

### "Only 0 left in stock. Order soon."
- **Should:** The scarcity widget should not render on a fully sold-out product.
- **Did:** Bird Grey Hoodie (0/10 variants available) displays "Only 0 left in stock. Order soon." in the buy column.
- **Verdict:** broken
- **Shopper impact:** Comic; undermines every other "Only N left" on the site.
- **Screens:** uf-pdp-hoodie-02-sizes-buy (line renders below payment area)

### Fully sold-out product — what does the page offer?
- **Should:** A notify-me/back-in-stock path, or at least a clear "gone, here's what's next".
- **Did:** "SOLD OUT" badge above the title, greyed disabled "Sold Out" button — and directly beneath it a fully-coloured, active-looking purple "Buy with shop" button plus a "MORE PAYMENT OPTIONS" link. Clicking Buy-with-shop (tested mobile and desktop) does nothing observable: no navigation, no sheet, no error. No notify form, no email capture, no restock date, no message of any kind. The only email capture on the page is the generic newsletter popup that interrupts ~30s in.
- **Verdict:** broken
- **Shopper impact:** The flagship product line (all Bird items) is a dead end with a live-looking payment button that silently ignores taps — the worst of both worlds: no capture of demand, plus a button that feels broken.
- **Screens:** uf-pdp-hoodie-02-sizes-buy, uf-pdp-hoodie-07-shoppay-tap, uf-pdp-desktop-05-shoppay-click

### Back-in-stock / notify mechanism
- **Should:** Exists for a store where 32 of 44 products are unbuyable.
- **Did:** None anywhere. No form, no link, no "DM us" hint.
- **Verdict:** absent
- **Screens:** uf-pdp-hoodie-02-sizes-buy

### Add to cart — feedback
- **Should:** Obvious confirmation.
- **Did:** Morocco Top: tap "Add To Cart" → cart drawer slides in from the right within ~2.5s showing item thumb, name, size, price, qty stepper, bin icon, subtotal "$56.00 USD, Taxes included."; header cart badge updates to 1. /cart.js confirms 1x Morocco Top S at 5600. Maths correct.
- **Verdict:** works
- **Screens:** uf-pdp-morocco-03-after-atc

### Cart drawer — terms-of-sale gate
- **Should:** Checkout button takes you to checkout.
- **Did:** Drawer contains an unticked checkbox: "Agree to terms of sale as per the merchants terms of service." (sic — missing apostrophe). Tapping Checkout without it does not navigate; a native browser bubble appears: "Please check this box if you want to proceed." After ticking, checkout loads normally, branded "Unfounded Checkout".
- **Verdict:** partly
- **Shopper impact:** One extra mandatory tap with a slightly amateur sentence; the native bubble does rescue it from being a silent failure.
- **Screens:** uf-pdp-ship-01-checkout-no-terms, uf-pdp-ship-02-checkout-landing

### Product descriptions
- **Should:** What it is, what it's made of, how it fits, how to care for it.
- **Did:** Every description on all four PDPs is a shipping lead time and nothing else. Bird Grey Hoodie, in full: "Shipping - In Hand Please Allow 5-7 Working Days From Purchase / Pre Order - Please Allow 3-4 Weeks For Your Item". Italy/Morocco/Argentina, in full: "Please Allow 2-5 Working Days For Item To Be Shipped". Zero words about fabric, weight, fit, origin, or care on any product. No "heavyweight", "cotton", "organic" or "gsm" appears anywhere on the PDPs, homepage, about page or collection pages — any such claim lives off-site (socials). The two lead-time regimes (5-7 days vs 2-5 days) are never reconciled.
- **Verdict:** broken
- **Shopper impact:** A £35-£50 garment sold with literally no product information. The gallery has to do all the persuading.
- **Screens:** uf-pdp-hoodie-01-top, uf-pdp-morocco-01-top

### Size guide / measurements
- **Should:** A size chart or measurements, findable within a minute.
- **Did:** No "Size Guide" link, page, accordion, or menu entry exists anywhere (menu, footer, PDP scanned — footer has only Search/About/Privacy/Returns). BUT a proper measurements table (INCH; Waist 28-36, Length 22-24.5, Leg Opening 11-15, XS-XL) exists as the LAST gallery image on Argentina Shorts (image 2 of 2) and Italy Track Pants (image 5 of 5) — unlabelled, alt-less, shrunk into a colourways group shot. Nothing on Bird Hoodie or Morocco Top. Hunt time as a shopper: ~1 minute of scrolling/menu/footer produces "there is none"; you only find the chart if you happen to swipe to the final photo and squint.
- **Verdict:** partly
- **Shopper impact:** The store DID the measuring work and then hid it. Hoodie buyers (the flagship) get nothing at all — no "model wears" either, despite on-model shots.
- **Screens:** uf-pdp-argentina-04-sizechart-img, uf-pdp-italy-05-sizechart-img, uf-pdp-argentina-03-menu

### Delivery / shipping info from the PDP
- **Should:** Lead time plus a way to learn the shipping cost before checkout.
- **Did:** Lead time doubles as the product description (see above), inconsistent across products. A rotating trust tile under the buy button claims "FAST GLOBAL SHIPPING" / "100% SECURE PAYMENTS". There is no shipping page: /policies/shipping-policy and /pages/shipping are 404; footer offers only a Returns (refund) policy. Shipping COST appears nowhere on the site: PDP → Add to Cart (1 tap) → tick terms (2) → Checkout (3) lands on a checkout that says "Enter your shipping address to view available shipping methods." Cost is unknowable without surrendering an address.
- **Verdict:** partly
- **Shopper impact:** "Fast global shipping" with an unknowable price; basket-abandonment fuel.
- **Screens:** uf-pdp-ship-02-checkout-landing, uf-pdp-hoodie-07-shoppay-tap (trust tile)

### Related / recommendation block
- **Should:** Relevant alternatives, ideally rescuing sold-out dead ends.
- **Did:** "You may also like" renders 4 products on every PDP tested (hoodie: USA Top, Germany Top, Italy Polo, Italy Track Pants). Cards show image, name, price, and on desktop hover expose a quick-add trigger. Recommendations are same-store, same-aesthetic; on the sold-out hoodie they do at least point at buyable items, though nothing hoodie-like (all Bird hoodies are sold out, so fair enough). Below it sits an on-model lifestyle banner.
- **Verdict:** works
- **Screens:** uf-pdp-desktop-02-related, uf-pdp-desktop-03-related-hover

### Price display and maths
- **Should:** Clear price, honest sale handling, sane currency.
- **Did:** Price + "TAXES INCLUDED." on every PDP. No compare-at prices anywhere (the "Black Friday"/"End Of Month Sale" collections contain no actually-discounted PDPs — no fake strikethroughs, to their credit). Multi-currency geolocation works: our US session saw £35→$49, £40→$56, £30→$42, £23→$32, £18→$25 — all exactly £×1.3829 rounded up to whole dollars; cart and checkout agree ($56.00 end to end). Minor: the theme prints "Regular price $49.00" twice next to the price in the DOM/accessibility tree.
- **Verdict:** works
- **Screens:** uf-pdp-hoodie-01-top, uf-pdp-morocco-03-after-atc

### URL / variant behaviour, back/forward
- **Should:** Selecting a size updates the URL (?variant=) so links/refresh/back keep state.
- **Did:** Selecting a size never changes the URL on any product. No history entry is created; Back from the PDP leaves the page entirely (to the homepage in our run), Forward returns with the default preselection. You cannot deep-link a size.
- **Verdict:** partly
- **Shopper impact:** Sharing "get the S" links is impossible; refresh loses nothing only because the theme auto-picks the first available size anyway.
- **Screens:** uf-pdp-italy-03-selected

### Newsletter popup interrupting the PDP
- **Should:** Not interrupt mid-consideration, or at least be easy to dismiss.
- **Did:** ~30-60s into a session a centred "Sign up for our newsletter" modal (email field + Subscribe + "NO THANKS") appears over the PDP — it fired while we were mid-interaction on desktop and swallowed a click. Dismissible via NO THANKS. (Form observed only, never submitted.)
- **Verdict:** partly
- **Screens:** uf-pdp-desktop-05-shoppay-click

### Reviews / social proof on PDP
- **Should:** Reviews, ratings, UGC, or press.
- **Did:** None on any PDP. Only Instagram/TikTok icons in the footer.
- **Verdict:** absent
- **Screens:** uf-pdp-hoodie-01-top

### Desktop quick pass (bird-grey-hoodie)
- **Should:** Layout scales; hover states exist.
- **Did:** Clean two-column layout; BOTH columns sticky so the buy panel stays put while you scroll. Single next-arrow on the gallery (appears on the media column), nwse-resize zoom cursor on hover, lightbox same as mobile. Country picker with US flag in the header (mobile hides it in the menu). Related cards reveal quick-add on hover. Same sold-out contradictions (active purple Buy-with-shop under a greyed Sold Out). Newsletter popup fired mid-pass and blocked a click on "MORE PAYMENT OPTIONS" (untestable this run).
- **Verdict:** works
- **Screens:** uf-pdp-desktop-01-top, uf-pdp-desktop-04-gallery-hover, uf-pdp-desktop-03-related-hover

## Comparison hooks (numbers)
- Photo counts: bird-grey-hoodie 5, italy-track-pants 5 (incl. size-chart image), morocco-top 1, argentina-shorts 2 (incl. size-chart image). Alt text: none (all null).
- Size guidance: no link/page anywhere; measurements table hidden as final gallery image on 2 of 4 products; nothing for hoodies. "Model wears": nowhere.
- Sold-out handling: badge on PDP + struck-through pills; NO notify mechanism; disabled Sold Out button but live-looking Shop Pay button that does nothing.
- ATC feedback: slide-in cart drawer + header badge, ~2.5s.
- Taps from PDP to a visible shipping cost: unreachable — 3 taps to checkout, which still demands a full address first. No shipping policy page (404).
- Checkout branding: standard Shopify, titled "Unfounded Checkout", logo present.
- Reviews/social proof: none.
- Currency: geo multi-currency (GBP base, USD shown to US IPs at 1.3829, rounded up); "TAXES INCLUDED" everywhere.
