# raw — toggles-edge (light/dark, the Outline toggle, edge conditions)

Phone unless stated: 390×844, GB market, staging theme 202053779799.
Dark is the default — a first visit carries no `data-crk-theme` and paints `rgb(11,10,14)`.
The control is a header button reading **`LIGHT MODE`**, which renames itself to `DARK MODE`
once light is on. It sits in the header row: `CATALOGUE  SEARCH  BAG [1]  LIGHT MODE  MENU`.

---

### Light/dark toggle — the control itself
**Should:** a shopper can find the switch, use it, and see the site change.
**Did:** it works instantly with no reload. Light repaints the ground to `rgb(250,250,251)`,
flips the handcuff logo to black, keeps the purple accents. The label states the destination,
not the current state, which is the right way round.
**Verdict:** works
**Evidence:** audit/screens/toggles-edge-01-header-dark.png, audit/screens/tg-home-light.png,
audit/screens/tg-home-dark.png

### Light/dark on every template
**Should:** every page a shopper can reach honours the choice.
**Did:** switched on home, product, collection, cart, search, `/pages/faq`, `/pages/terms`,
`/pages/tracking`, `/pages/contact`, `/policies/refund-policy` and a 404. Home, product,
collection, cart, search, FAQ, terms, tracking and the policy page all repaint correctly in
both themes, and an automated sweep for text that drops below 3.2:1 against its own background
found **nothing** on any of them in light. Two templates ignore the theme completely — below.
**Verdict:** partly
**Evidence:** audit/screens/tg-{home,product,collection,cart,search,faq,terms,tracking,policy}-{light,dark}.png

### The 404 page and `/pages/contact` ignore the theme entirely
**Should:** a mistyped URL or a dead link lands you somewhere that still looks like the shop.
**Did:** in **dark** — the default — the header is black and everything under it is Horizon's
cream `rgb(244,241,234)` in Horizon's own typeface: `PAGE NOT FOUND`, *"The link may be
incorrect, or the page has been removed."*, a black `Continue shopping` block, then a
`Discover something new` carousel. Pressing `LIGHT MODE` changes nothing below the header —
the dark and light screenshots are identical apart from the header strip. `/pages/contact` is
the same: body ground `rgb(244,241,234)` in both themes.
**Verdict:** broken (404 and `/pages/contact` only)
**Shopper cost:** on a phone at night, a dead link throws a full-screen cream page in a
different typeface at you — it reads as "wrong site", at the exact moment you were already
unsure. And the switch that works everywhere else silently stops working.
**Evidence:** audit/screens/tg-404-dark.png vs audit/screens/tg-404-light.png;
audit/screens/tg-contact-dark.png. Exact strings: `PAGE NOT FOUND`, `The link may be
incorrect, or the page has been removed.`, `Continue shopping`, `Discover something new`.

### The `SEARCH` button disappears in light mode
**Should:** the button that runs the search is visible.
**Did:** on `/search`, the submit button — the word `SEARCH` under the query box — computes to
`color rgb(221,215,201)` (cream), `background rgba(0, 0, 0, 0)`, `border 0px`. On the light
ground that is **1.38:1** — cream on white. Its class is `crk-btn crk-btn--fill
crk-query__go`; the "fill" never arrives, so dark gets away with it and light does not.
**Verdict:** broken (light mode only)
**Shopper cost:** you type `jeans`, and between the box and the line
`SEARCH BY ITEM, CATEGORY OR COLOUR` there is a blank gap where the button should be. You have
to guess that Enter works or that the empty space is tappable.
**Evidence:** audit/screens/tg-search-light.png (blank where the button is) vs
audit/screens/tg-search-dark.png (same button legible).

### The `Outline` toggle in LIGHT mode — audit question Q3
**Should:** a control called `OUTLINE` visibly changes how product images look.
**Did:** the treatment is a 1px cream keyline painted round the garment —
`filter: drop-shadow(rgb(221,215,201) 1px 0px 0px) drop-shadow(… -1px …) drop-shadow(… 1px)
drop-shadow(… -1px)` — and it is **on by default**: a brand-new session already has
`crk-outline = on` in storage with nobody having pressed anything, and a cold-landed PDP
already carries the keyline. In **dark** it does real work: the grey jeans, the jorts and the
black tees stand off the near-black card (`rgb(14,12,19)`) on a bright outline. In **light**
the filter is **not applied at all** — the same images compute `filter: none` whether the
button reads pressed or not. Pressing `OUTLINE` in light mode changes the button's own state,
writes `crk-outline` to storage, sets `data-crk-outline="off"` on `<html>` — and changes
nothing on screen.
Two further things a shopper meets: the button exists **only on the homepage register**
(`/collections/all` offers `FLAT` / `ON MODEL` and no `OUTLINE`), and the default is on, so
nobody chose the treatment they are looking at.
**Verdict:** partly — works in dark, inert in light
**Shopper cost:** in light mode the control appears broken rather than inapplicable. It is the
one purely cosmetic control on the page, so the "is this site working?" doubt it buys is paid
for nothing.
**Evidence:** audit/screens/tg-home-dark.png (cards NO. 05–08, keyline clearly visible) vs
audit/screens/tg-home-light.png (same cards, same outline state, no keyline);
audit/screens/tge-1-cold-pdp-top.png (cold landing already outlined);
measured `light+outline ON → filter "none"`, `light+outline OFF → filter "none"`,
`dark+outline ON → drop-shadow ×4`. Related to known item **O3**.

### Prose links in dark mode — the dimmest text on the page
**Should:** a link inside a paragraph is at least as readable as the paragraph.
**Did:** on `/pages/faq` in **dark**, the closing paragraph's links are `rgb(92,52,128)` on
`rgb(11,10,14)` — **2.12:1**, visibly darker than the text beside them. The paragraph reads:
*"Still stuck? Email crooksldn@gmail.com or DM @crooksldn with your order number. We reply
within 1–2 working days. The full trading terms are on the terms page."* Same colour on
`tracking page`, `the returns centre`, `Start your return here`. In light the same links are
fine.
**Verdict:** partly
**Shopper cost:** the FAQ's escape hatches — the email address and "Start your return here" —
are the least visible words in the answer, in the theme almost everyone sees.
**Evidence:** audit/screens/tg-faq-dark.png vs audit/screens/tg-faq-light.png

### There IS a flash on load — cream, in dark mode
**Should:** no flash of the wrong theme.
**Did:** the theme *attribute* is correct on the first rendered frame (no light→dark→light
flip). But the first thing actually painted is Horizon's cream `rgb(244,241,234)`, whole
screen. On a cold load of a product page in the default dark theme, the screenshot I could
take about a third of a second in is **entirely cream**; by the next one, about three-quarters
of a second in, the dark page has painted. In light mode the same cream frame is invisible
(cream → white).
**Verdict:** partly
**Shopper cost:** every cold page load in the default theme starts with a full-screen white
flash. On a phone in the dark that is the difference between "moody" and "ow".
**Evidence:** audit/screens/tg-darkflash-0-at298ms.png (full-screen cream) →
audit/screens/tg-darkflash-1-at731ms.png (dark page, cookie banner up).

### The choice persists across navigation — but only in that one tab
**Should:** pick light once, keep it.
**Did:** light survived every navigation tested (home → collection → product → cart → search →
policy → 404) and survives reload. It lives in `sessionStorage`, so a **new tab starts dark
again** (`data-crk-theme` null, storage empty) even though the **bag carries over** correctly
(`BAG [2]` in the fresh tab). Same next time the browser is opened.
**Verdict:** partly
**Shopper cost:** someone who needs light mode has to re-pick it in every tab and every
session, on a site that remembers their bag perfectly well.
**Evidence:** audit/screens/tge-4-tab3-new-tab.png — new tab, header reads `LIGHT MODE`
(i.e. dark), `BAG [2]`.

### Toggling mid-scroll costs you your place
**Should:** change the theme where you stand.
**Did:** the header is not sticky. Half-way down the homepage (scrollY 2412 of 4888) the
toggle sits **2,326px above the top of the screen**. To press it you must scroll back to the
top, and once pressed you are still at the top (scrollY 86) — the page does not put you back.
**Verdict:** partly
**Shopper cost:** deciding "this is too bright" nine cards into the register means losing your
place in the register to fix it.
**Evidence:** audit/screens/tg-midscroll-before.png, audit/screens/tg-midscroll-after.png

---

## Edge conditions

### Shopping with the theme's JavaScript unavailable
**Method note.** `session({ js: false })` cannot be used: the harness asserts theme identity
by evaluating in the page, which JavaScript-off makes impossible, so the session never opens
(it returns `ok:false` with every field missing). Substituted: a normal session with **every
external `.js` request blocked** (70 blocked on the homepage). The theme's behaviour scripts
are all external `defer` files, so the shopper condition is the same; only the one inline
pre-paint theme resolver still runs.

**Should:** SPEC §9.11 — product links and images on the homepage, prices and sizes rendered,
a working `/cart/add` on the PDP.
**Did — what survives:** the homepage renders fully: 12 product links, 14 images shown, 13
prices, the hero (`CROOKSLDN` / `OWN THE STREETS™` / `CATALOGUE`), the boot line
`> 12 PRODUCTS AVAILABLE TO PURCHASE`, the register, the footer. The PDP renders
`PRODUCT 01 / 12`, `CHARCOAL CELLBLOCK CREWNECK`, `£50.00`, the photo, the five size boxes,
`SIZE GUIDE`, `Order before 18:00 and it ships today (Mon–Sat)`, and the cart page reads
correctly.
**Did — what is lost:**
1. **The ticker prints every message on top of itself.** At the very top of every page,
   `FREE UK SHIPPING OVER £20 — ORDER BY 18:00 FOR SAME-DAY DISPATCH` is painted over
   `12 PRODUCTS CURRENTLY ONLINE`, both clipped, both unreadable. SPEC §3.2 says "with JS
   absent the first message shows"; both show, superimposed. It is the first thing on the page.
2. **You cannot choose a size.** The size controls are `<button type="button">`; activating
   `M` changes nothing (`aria-pressed` stays false on all five, `input[name="id"]` stays
   empty, the URL gains no `?variant=`). The submit button stays labelled `SELECT A SIZE`
   for ever.
3. **Submitting anyway dead-ends on a Shopify error page:** `Something went wrong.` /
   `What happened?` / `Cart Error: Cannot find variant` / `What can I do?` /
   `Return to the previous page.` plus a Request ID. Nothing on that page leads back to the
   shop except the browser's Back button.
4. **All four PDP panels stay shut.** `SPECIFICATION`, `ITEM DESCRIPTION`, `MEASUREMENTS` and
   `CHAIN OF CUSTODY — SHIPPING & RETURNS` are `<button>`s, not `<details>` (0 `<details>`
   elements on the PDP even with JS on). Activating all four changed the page's text length by
   nothing at all (865 characters before, 865 after). So: no measurements, no description, no
   shipping or returns terms.
5. The menu drawer will not open, the theme toggle is dead, `OUTLINE` is dead, the catalogue
   filters are dead — all expected, all silent.
6. The sticky bottom bar still shows a purple `ADD TO BAG` and `CHECKOUT NOW`, so the buy
   controls look live while the form behind them cannot be completed.
**Did — the one path that does work:** arriving on a **variant URL**
(`/products/…?variant=53936235282775`) the server pre-fills `input[name="id"]`, marks `M`
pressed, and the button reads `ADD TO BAG`; submitting it lands on `/cart` with the line
`CHARCOAL CELLBLOCK CREWNECK / Size: M / £50.00` and the carriage line
`£20.00 to free Tracked 24`. So `/cart/add` itself is fine — it is size selection that is
JavaScript-only.
**Verdict:** partly (browsing survives; buying from a normal product URL does not)
**Could you be confident you were buying the right size?** No. You cannot pick a size at all,
and `MEASUREMENTS` will not open, so even the sizes you can see are unexplained. On the one
route that works — a variant link — the size was chosen by the link, not by you, and the only
sign of it is one of five boxes looking pressed.
**Evidence:** audit/screens/tgj-home-nojs.png (overlapping ticker),
audit/screens/tgj-pdp-nojs.png, audit/screens/tgj2-size-clicked-noJS.png,
audit/screens/tgj2-after-submit-noJS.png (`Cart Error: Cannot find variant`),
audit/screens/tgj2-accordions-noJS.png, audit/screens/tgj2-cart-noJS.png

### 200% zoom
**Should:** you can still buy.
**Did:** yes — the whole purchase completes at 200%: homepage → register → PDP → size `M` →
`ADD TO BAG` → `BAG [1]` → `/cart` (`Cart 1`, `Size: M`, `£50.00 GBP`) → `Check out` →
Shopify checkout (`CROOKSLDN Checkout`, `Express checkout`, `Contact`, `Delivery`,
`Country/Region United Kingdom`). Abandoned there; nothing submitted. No page scrolls
sideways anywhere (horizontal overflow 0 on home, PDP and cart). Two blemishes:
- **`CHECKOUT NOW` in the PDP's sticky bar runs off the right edge** — its box starts at x=331
  and is 245 wide in a 390-wide screen, so roughly 185px of the button, including the end of
  the word, is off-screen.
- The promo modal's close **×** overlaps the headline at 200%: the × box sits on top of
  `CROOKSLDN:` in `CROOKSLDN: THE GETAWAY`. At 100% they are well clear of each other. It is
  still tappable.
**Verdict:** works, with two clipping blemishes
**Evidence:** audit/screens/tgz-pdp-zoom2.png, audit/screens/tgz-cart-zoom2.png,
audit/screens/tgz-checkout-zoom2.png, audit/screens/tgz-home-zoom2.png (× over the title)

### Landscape phone (844×390)
**Should:** the layout survives and nothing is unreachable.
**Did:** home, product and cart all fit — horizontal overflow 0, no control covered by
anything, no control off the right edge. Buying works: size `M`, `ADD TO BAG` (a 754px-wide
button), `BAG [1]`. Light mode works. The **menu drawer** is the pinch point: its panel is
1,129px of menu in a 390px-tall window, so on opening, seven of sixteen items are below the
edge — `TRACKING`, `QUESTIONS`, `TERMS`, `CONTACT`, `PLAY CASE:001 NOW`, `ACCOUNT`, `BAG`.
It does scroll (the panel, not the page), and one scroll gesture brought all but `ACCOUNT` and
`BAG` into view, so nothing is truly unreachable — but in landscape the menu is a three-screen
scroll with no visible hint that anything is below.
**Verdict:** works
**Evidence:** audit/screens/tgl-home-landscape.png, audit/screens/tgl-product-landscape.png,
audit/screens/tgl-added-landscape.png, audit/screens/tgl-drawer-landscape.png,
audit/screens/tgl-drawer-landscape-after-scroll.png

### Reloading the main pages
**Should:** nothing lost.
**Did:** reloaded home, collection, product, cart and search. Each came back identical to a
shopper — same headings, same `BAG [1]`, same images (0 broken), same carriage line
`£20.00 to free Tracked 24`. 3.5–4.7s each.
**Verdict:** works

### Back and forward through five pages
**Should:** the trail works and the bag stays honest.
**Did:** home → collection → product → search → cart, then Back ×5 and Forward ×5. Every step
restored the right page with its heading, images and price, and `BAG [1]` was correct at every
step. Each step took about 2.8–3.4s — these are real loads, not instant restores.
**Verdict:** works
**Evidence:** audit/screens/tge-3-back-1..5.png

### Landing directly on a product URL, cold
**Should:** the PDP stands on its own.
**Did:** with storage cleared so the PDP was the first page the browser rendered, it came up
in 4.8s complete: `PRODUCT 01 / 12`, `CHARCOAL CELLBLOCK CREWNECK`, `£50.00`, five sizes,
`SIZE GUIDE`, `Order before 18:00 and it ships today (Mon–Sat)`, the four panels,
`MORE FROM THIS DROP`, and the sticky bar reading `SELECT A SIZE` / `CHECKOUT NOW`. Picking
`M` and adding worked: `BAG [0]` → `BAG [1]`.
**Verdict:** works
**Evidence:** audit/screens/tge-1-cold-pdp-top.png, audit/screens/tge-1-cold-added.png

### Two tabs
**Should:** after a reload they agree.
**Did:** tab B on `/cart` showed `Cart 1`. Tab A added a second item. Tab B, untouched, still
said `Cart 1` and `£20.00 to free Tracked 24` — nothing marks it stale. After a reload it
agreed exactly: `Cart 2`, and the carriage line changed to `Free Tracked 24 — unlocked`.
**Verdict:** works — with the usual caveat that an untouched second tab will let you press
`Check out` believing there is one item in the bag when the server holds two.
**Evidence:** audit/screens/tge-4-tab2-stale.png, audit/screens/tge-4-tab2-after-reload.png

---

## Surprises

- **A cookie consent banner now exists.** The standing brief lists "No cookie banner" as
  known-absent. There is one: a panel headed `COOKIE CONSENT` with `Accept` / `Decline` /
  `Manage preferences`, covering the bottom **43%** of the phone screen (390×359 of an 844-tall
  viewport) on first load, and sitting *over* the open menu drawer, hiding the CASE 001 panel
  until it is dismissed. Exact text: *"We and our partners, including Shopify, use cookies and
  other technologies to personalize your experience, show you ads, and perform analytics, and
  we will not use cookies or other technologies for these purposes unless you accept them.
  Learn more in our Privacy Policy"*. Evidence:
  audit/screens/toggles-edge-00-home-dark-cookiebanner.png, audit/screens/toggles-edge-B-drawer-dark.png
- **A full-screen promo modal fires on the homepage** — `CROOKSLDN: THE GETAWAY` / *"Crack the
  cuffs. 10% off your first order — code sent by text. Attempts unlimited."* / `RUN IT` /
  `NOT NOW` / *"One code per player. Code expires 20 minutes after you win."* It covers the
  whole page, which is how two of my screenshot pairs came back pixel-identical. Whatever it
  is for, it lands on top of the register with the cookie banner already in play.
  Evidence: audit/screens/tg-outline-dark-default.png, audit/screens/tgz-home-zoom2.png
- **The white-outline treatment is on by default**, not off (see Q3 above) — the first thing a
  new visitor sees is a styling choice nobody made, and in light mode the control that would
  undo it does nothing.
- **The PDP's four panels are buttons, not `<details>`.** SPEC §9.4 leans on `<details name>`
  for no-JS exclusivity; on the product page there are zero `<details>` elements, so the panels
  are JavaScript-only.
- The packaging section's image frame is empty on the homepage in both themes. On dark it reads
  as a deliberate empty frame; in light it is a large blank white panel that reads as a failed
  image.

## Missing

- No way to keep the light-mode choice past the tab or the session.
- No `OUTLINE` control anywhere except the homepage register.
- No way to change theme without scrolling back to the top of the page.
- Nothing tells a no-JS shopper that they must pick a size in a way the page cannot accept —
  the label says `SELECT A SIZE` and there is no way to obey it.

## Contradictions

- The header button says `LIGHT MODE` on every page, but on the 404 and `/pages/contact`
  pressing it changes nothing — those pages are cream in "dark" and cream in "light".
- The homepage register offers `OUTLINE`; the collection page showing the same products does
  not. Same shopper, same products, two different sets of controls.
- Without JavaScript the PDP's own submit button says `SELECT A SIZE` while the sticky bar
  below it says `ADD TO BAG` — one says you have not finished, the other says you have.
- SPEC §3.2: *"with JS absent the first message shows"* — with JS absent all the ticker
  messages show, printed on top of each other.

## Works and must be protected

- The theme switch itself: instant, no reload, no wrong-theme flip, label states the
  destination.
- Reload, Back/Forward, and cold-landing straight on a product URL: all clean, bag count
  honest at every step.
- Two tabs reconcile exactly on reload, including the carriage line.
- 200% zoom is genuinely usable — the full purchase completes to checkout.
- Landscape holds together: no sideways scrolling, no covered controls, buying works.
- Product photography suits both grounds; the light register is as legible as the dark one, and
  the contrast sweep found no unreadable text on any crooks-built template in light.
