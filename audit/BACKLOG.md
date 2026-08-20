# BACKLOG — sorted by severity ÷ effort

Every row traces to a shopper moment in `audit/journeys/` or `audit/features/`.
Severity: **blocks a purchase** / **causes hesitation** / **costs polish**.
Effort: **minutes** / **hours** / **a session**.
Type: broken · missing · confusing · contradictory · slow.

**Read `COUNCIL.md` before this file.** The council's verdict is that publishing
outranks most of what follows, and that the top fix needs a tape measure rather
than a developer — so it never blocks a deployment. Items already logged as
**D1** or **O1–O4** are marked and are not raised as new.

**Read theme code with `git show origin/claude/crooksldn-theme-init-bnen7a:<path>`.**
This working tree is a different, month-old branch; a fix applied here would
edit a file that is not deployed. See `RUN-NOTES.md`.

---

## The top five — do these first

| # | Finding | Evidence | Severity | Effort | Type | Where |
|---|---|---|---|---|---|---|
| 1 | **Three variants still set to keep selling when out of stock.** The only item that gets *worse* the moment the better theme publishes — it sells more of them. Logged as **RUN3 B1**, third audit running. | `_ref/RUN3-FINDINGS.md` B1 | blocks a purchase | minutes | broken | Admin → Products → variant |
| 2 | **The set panel reports a false out-of-stock on every size.** Tick the offer before choosing your own size and the shop says `Cellblock Shorts sold out in M — pick another size` against 201 units. The instruction cannot be obeyed — every size lies. The fix is copy that already exists on the shorts side: `Pick a Cellblock Shorts size`. | `journeys/04-set-buyer.md`; `screens/verify-set-B-false-soldout.png` | blocks a purchase | minutes | broken | `snippets/crooks-set-toggle.liquid` |
| 3 | **Measurements are a generic inch chart, printed on three different garments.** Fifteen cells, every one a whole inch; the same table on a 14oz jean and a 500gsm sweatpant. Fabricated content inside the zone `SPEC.md §0` says is never in-fiction. **Interim, free, today:** delete any unmeasured table and print the promise the FAQ already makes. **Real fix:** a tape measure. | `journeys/03-size-anxious.md`, `11-tinkerer.md`; 5 journeys | blocks a purchase | a session | broken | Admin → metafields (`crooks.measurements`) |
| 4 | **The cart's own upsell is the most expensive route you sell.** `Complete the set — add the Cellblock Shorts, save £10.` links to the shorts page; doing what that page says produces a **£95** cart with no discount. Three prices exist for the same two garments — £85, £76.50, £95 — and the site recommends the worst. | `journeys/05-set-sceptic.md` | blocks a purchase | hours | broken | `sections/crooks-set-cart.liquid` |
| 5 | **The buy button changes under the thumb on a slow connection.** An enabled purple `ADD TO BAG` shows for ~2.7s, then flips to a disabled `SELECT A SIZE` in the identical position. Pressed, it does nothing and says nothing. **This is A1**, the layout-shift defect run 3 called the only BLOCKS-class theme fault and run 2 already prescribed. | `journeys/14-slow-connection.md` | blocks a purchase | hours | broken | `assets/crx-mono.css`, `crooks.css:47–48`, `:397` — **already specified in RUN3 A1** |

---

## Theme code

| # | Finding | Evidence | Severity | Effort | Type | Where |
|---|---|---|---|---|---|---|
| 6 | **The cart line item prints the photo over the words.** Title, size and price all render inside the image box — reads `ACK` and `00` — and `+` overlaps the delete bin by 20–40px. The one page whose job is confirmation. Checkout lays the same three facts out correctly; port that. | `journeys/13-landscape.md`, `17-zoom.md` | blocks a purchase | hours | broken | `snippets/cart-items-component.liquid` (Horizon stock markup) |
| 7 | **`0 RESULTS` printed under links that matched.** Searching `terms` shows three working links to Terms with `NO ITEMS IN THE REGISTER MATCH THAT QUERY.` between them. One shopper read the zero first and concluded the shop has no returns information. And a *failed* search offers fewer routes out than a *blank* one. | `journeys/12-searcher.md` | causes hesitation | hours | confusing | `sections/crooks-exhibit-log.liquid`, `crooks-search.liquid` |
| 8 | **`returns` and `exchange` send a pre-purchase shopper off-site.** Both return only the AfterShip portal — an order-lookup form for someone with no order — whose own policy says 30 days against your 14. `refund` already offers the shop's own policy: copy that list. | `journeys/12-searcher.md`, `20-post-purchase.md` | causes hesitation | minutes | confusing | `sections/crooks-search.liquid` link blocks |
| 9 | **The first-visit overlay.** Six separate costs: countdown copy on your own rejected list; it takes the tap meant for `PLAY CASE:001 NOW`; it traps keyboard focus and its offer needs a mouse; the game ignores reduced motion; it fires before a price has been seen; and it does not fire consistently, so the worst first impression is a coin flip. Delete the render or gate it behind a first *product* view. | `journeys/07`, `09`, `13`, `14`, `15`, `18` | causes hesitation | minutes | confusing | `layout/theme.liquid` → `crack-the-cuffs` |
| 10 | **The carriage bar never updates after an add on a product page.** A bag going £25 → £85 crosses both tiers while the bar still asks for £45 more. The PDP add path dispatches neither event the script listens for, though `SPEC.md §3.7` says it does. The £20 tier is never announced at all. | `journeys/08-basket-builder.md`; `features/raw-carriage.md` | causes hesitation | minutes | broken | `assets/crooks-record.js` — one `dispatchEvent` |
| 11 | **The header bag count is stale after every removal.** `BAG [2]` sits above `Your cart is empty`. It overstates, so it reads as "your deletion didn't work", and it goes wrong only on the cart page — the one page opened to check. | `journeys/08`, `16` | causes hesitation | hours | broken | `assets/cart-icon.js` / cart section events |
| 12 | **`SELECT A SIZE` when size is not what's missing.** On socks there is no size at all — the row is headed `QUANTITY`. On the tee it says it after a size has been picked and a colour has not. Six journeys. The one place the plain-English rule is plainly wrong. | `journeys/07`, `08`, `11`, `13`, `18`, `19` | causes hesitation | minutes | confusing | `assets/crooks-record.js` button label |
| 13 | **The `Outline` toggle should be removed** (**O3**, now answered). In light mode the two states are byte-identical files; it draws binding, trim and piping the garments do not have; and the button is absent from the collection pages the treatment still applies to. Ship it on, delete the control. | `journeys/11-tinkerer.md` | costs polish | minutes | confusing | `sections/crooks-exhibit-log.liquid` |
| 14 | **`ON MODEL` shows a photograph of a different garment.** One image of charcoal shorts on all twelve cards, including £6 socks and an £18 duffle — and it behaves differently on three different pages. Point it at the model images that exist and hide the toggle for products without one. Scope honestly: only 4 of 12 cards have a second image. | `journeys/10`, `11`, `19` | causes hesitation | hours | broken | `sections/crooks-exhibit-log.liquid`, `crooks.model_image` |
| 15 | **The skip link has no visible text** — the first tab stop on every page is a blank rectangle. Its accessible name is correct, so it passes automated checks and passed the screen-reader journey; only a sighted keyboard user meets it. | `journeys/15-keyboard.md` | causes hesitation | minutes | broken | `snippets/skip-to-content-link.liquid` |
| 16 | **The `SEARCH` submit button is invisible in light mode** — cream on white, no fill, no border, 1.38:1. | `features/raw-toggles-edge.md` | causes hesitation | minutes | broken | `assets/crooks.css` |
| 17 | **404 and `/pages/contact` ignore the theme entirely** — Horizon's cream body in both light and dark, with the theme toggle present and inert. `/pages/contact` is also two of the most obvious taps on the site and carries no email, name, address or reply time. | `journeys/02-sceptic.md`; `features/raw-toggles-edge.md` | causes hesitation | hours | broken | `templates/404.json`, `page.contact.json` |
| 18 | **`SIZE GUIDE` ignores reduced motion** — the smooth scroll is unguarded, so the glide is identical with the setting on. Destination is perfect; the journey there is not. | `journeys/18-reduced-motion.md` | costs polish | minutes | broken | `assets/crooks.css` scroll-behavior |
| 19 | **Tapping `MEASUREMENTS` shows nothing.** From a natural scroll position it opens the table with every data row below the fold and does not move the page. `SIZE GUIDE` is a strictly better route to the same content than the control named after it. | `journeys/03-size-anxious.md` | causes hesitation | minutes | confusing | `assets/crooks-record.js` |
| 20 | **No zoom on any product photograph**, though Shopify holds a 2048px master, and seven of twelve products carry exactly one image. | `journeys/01`, `19` | causes hesitation | hours | missing | `sections/crooks-exhibit-record.liquid` |
| 21 | **A quantity of `0` is silently rewritten to `1`**, the bin is the only route to removal and nothing says so, and there is no undo anywhere. | `features/raw-cart-checkout.md` | costs polish | hours | confusing | cart quantity component |
| 22 | **The set's saving is never confirmed in the cart.** `SPEC.md §3.13`'s second state does not render, so the shopper who takes the offer is the only one never told they saved anything — while `You may also like` below shows both halves at full price. | `journeys/04`, `05` | costs polish | hours | missing | `sections/crooks-set-cart.liquid` |
| 23 | **The `ACCESSORIES` filter sits 91px off the right edge** of a phone with no scroll cue — a third of the catalogue is hidden. | `features/raw-catalogue.md` | causes hesitation | minutes | broken | `assets/crooks.css` |
| 24 | **Filtering to an odd count leaves a solid lavender slab** where a product card would be. Reads as a failed image. | `features/raw-catalogue.md` | costs polish | minutes | broken | `sections/crooks-exhibit-log.liquid` |
| 25 | **Collection descriptions have nowhere to render.** `/collections/denim` has one in admin and the register has no slot for it — so the eight outstanding SEO collection descriptions would put zero words on the page. Distinct from the known "three collections have no description". | `features/raw-catalogue.md` | costs polish | minutes | missing | `sections/crooks-exhibit-log.liquid` |

---

## Store admin — no developer needed

| # | Finding | Evidence | Severity | Effort | Type | Where |
|---|---|---|---|---|---|---|
| A1 | **Send the restock form once from a phone on mobile data** and confirm a `Restock request` email arrives. The audit cannot settle this — the form sits behind a bot check that refuses automated browsers, and the blank panel it produces also appears on the store's own contact form, so it is **not** a theme defect. Ten minutes decides whether a feature needs building at all. | `features/raw-notify-verify.md` | blocks a purchase | minutes | unknown | your phone |
| A2 | **Real measurements on thirteen garments**, and one measuring method stated. The product page says `TAKEN AROUND THE GARMENT`; the FAQ says *"laid flat"*. That is a factor of two — read one way XS is a 76cm waist, read the other it is 152cm. | `journeys/03`, `09` | blocks a purchase | a session | contradictory | Admin → metafields; FAQ copy |
| A3 | **The tracking page has no form and the FAQ promises one twice.** *"You can also look your order up on the tracking page — no account needed"* against `IDENTIFICATION REQUIRED`. Either add the guest lookup the returns portal already performs, or reword the FAQ. Logged as **RUN3 A6**, still open. | `journeys/20-post-purchase.md` | blocks a purchase | hours | contradictory | `sections/crooks-tracking.liquid` or FAQ copy |
| A4 | **The consent banner covers 43% of a phone screen** — 50% in landscape — landing on the price, the size row and the buy bar, and taking the tap meant for `PLAY CASE:001 NOW`. At 200% zoom `Decline` is clipped off the right edge while `Accept` sits comfortably inside. Seven journeys. | `journeys/01`, `07`, `09`, `13`, `14`, `17`, `20` | causes hesitation | minutes | broken | Admin → Customer privacy |
| A5 | **The returns portal contradicts your own terms at three points** — 30 days against 14, faulty at 7 days against 14, and it excludes "discounted items" where you exclude "final sale". With a public 10% code in circulation a customer can reasonably read that as *my jeans are not returnable*. | `journeys/20-post-purchase.md` | causes hesitation | minutes | contradictory | AfterShip settings |
| A6 | **Put the contact email and reply time in the footer's `CONTACT` column** — where the word `EMAIL` currently sits, under a heading that is presently a dead tap. The best support copy on the site (`/policies/contact-information`) is linked from nowhere; one shopper found it by accident nineteen minutes in. | `journeys/02-sceptic.md` | causes hesitation | minutes | missing | footer settings; page links |
| A7 | **Decide `10CROOKS` against the £85 set** (**O1**). It takes the set to £76.50, so the price the product page calls the set price is not the floor. The bundle still beats its own code, so this reads as an oversight rather than deception — but it is the one number a sceptic is asked to trust. | `journeys/05-set-sceptic.md` | causes hesitation | minutes | contradictory | Admin → Discounts |
| A8 | **Add a restock answer to the FAQ.** Fourteen questions, none about restocks or drops, on a store whose sold-out sizes stay visible by design. Serves everyone, not only the shoppers who press the button. | `journeys/06-sold-out.md` | causes hesitation | minutes | missing | FAQ content |
| A9 | **One worn photograph per garment over £50**, and promote the jeans' existing model shot to image 1. Not a trust widget and not on the rejected list — it is the thing reviews would have been standing in for. | `journeys/01`, `10` | causes hesitation | a session | missing | Admin → Products → media |
| A10 | **Put `£3 / £4.99` and the free size-swap line into the shipping accordion.** The page currently states what is free and never what it costs when it isn't; a £6 order becomes £9 at the last screen. | `journeys/07-impulse.md` | causes hesitation | minutes | missing | product accordion content |
| A11 | **Rename with care.** Two products were renamed during this audit and one now contradicts its own description — `GREY CONVICT SWEATS` still opens *"V2 Baggies — wide, full-length sweats…"*. | `RUN-NOTES.md` | costs polish | minutes | contradictory | Admin → Products |

---

## Already logged — not raised as new

**D1** status-bar interval (inert; the audit adds only that the resulting 8s
cadence is too *slow* to reward, not too fast) · **O1** `10CROOKS` on the set
(A7 above) · **O2** wishlist and "Only X in stock" from app `bestpush-101` ·
**O3** the `Outline` toggle (answered: remove the control — #13) · **O4** the
CASE 001 link pointing at the old build (a shopper would not notice: the
destination opens on a title card with no art to compare) · placeholder
measurements (#3, A2) · three `.webp` masters under the wrong extension ·
`RUN3 A1` the header layout shift (#5) · `RUN3 A6` the tracking promise (A3) ·
`RUN3 B1` the oversell checkboxes (#1).

**Two known items came back clean and must not be worked again:** the doubled
`crooksldn@gmail.com.com` on the shipping policy, and the V2 BAGGIES
"9-16 days delivery uk" line. **O5** also appears resolved — worth one glance in
admin to close it.
