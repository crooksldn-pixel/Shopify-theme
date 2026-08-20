# FEATURES — what CROOKSLDN actually does when a stranger shops it

Phase 1 of the behavioural audit. Twelve feature areas, walked as a shopper on a
390×844 phone in the GB market unless a line says otherwise. Every claim below is
tied to a screenshot in `audit/screens/` and to a string quoted off the screen.

---

## 1. What a shopper actually meets here

A shopper arriving on a phone meets a black terminal that names twelve products, states
its free-shipping threshold in a rotating strip at 9px, and puts the first two product
cards behind a cookie sheet that owns the bottom 43% of the screen from the moment the
page arrives. What they get once they clear it is genuinely unusual and largely excellent:
every card states its stock in plain English, filters write themselves into the address so
a filtered link survives a share, sizes deep-link, and one accordion tells them in four
unhedged steps who pays for what when it goes wrong. What they do not get is a second
photograph of a £60 pair of jeans, any way at all to enlarge the one they have, a straight
answer to "what is your returns policy" from the search box, or any acknowledgement that
they signed up to the drop register. Where the store makes a specific money promise —
`Save £10.`, `£85 for the set`, `FREE UK SHIPPING OVER £20` — it is at least as likely to
charge them £95, £76.50 or £18.99 as the number they were shown. And on almost every
question a careful shopper asks, the site answers twice: the product page and the
`QUESTIONS` page describe two different ways to measure a garment, the Terms and the
product page give two different return windows, and the returns link the search box offers
hands them to a third-party site whose own policy says 30 days where CROOKSLDN says 14.

---

## Already fixed — nobody needs to work these again

Two items on the known list came back **clean** in this run. Stated explicitly so they are
not re-opened:

- **The doubled email on the shipping policy is gone.** Every email string and every
  `mailto:` on the homepage, footer, FAQ, Terms, tracking, contact, three product pages and
  all five policy pages was extracted. The shipping policy now reads
  *"How: email crooksldn@gmail.com or DM @crooksldn with your order number."* — a single
  `.com`, on every surface. Evidence: `audit/screens/content-pages-policy-shipping-clean.png`.
- **The V2 BAGGIES delivery line is gone.** The description now reads *"V2 Baggies — wide,
  full-length sweats in 500gsm cotton, heavy enough to hang straight. Made in Portugal."*
  The `9-16 days delivery uk` claim does not appear in any accordion on the products opened,
  and the custody step's `UK 1–2 working days` stands unchallenged on the product page.
  Evidence: `audit/screens/content-pages-pdp-baggies-open.png`.

**A third, less certain:** open item **O5** also appears resolved. The live Refund policy no
longer carries the blanket *"Size swaps are free within the UK"*; it now reads *"Return
postage is paid by you… There is no fee for a UK size swap itself, and we cover the postage
sending the new size out to you."* Two agents reached this independently
(`audit/screens/pdp-sizing-ret-02-refund-policy.png`, `audit/screens/12-14-refund-policy.png`).
Worth one confirmation in admin before closing it — and note the geography word it introduced
is itself a contradiction, in group A below.

---

## 2. What is broken

Worst first. Items already logged carry their ref and are reported for shopper impact only.

### 2.1 A cart line promises "save £10" and the obvious next action charges £95

**Should:** a link that says `save £10.` ends in a cart £10 cheaper than the alternative.
**Did:** with `CHARCOAL CELLBLOCK CREWNECK - M` in the cart at £50.00, the cart shows
`Complete the set — add the Cellblock Shorts, save £10.` Following it lands on the shorts
page; picking a size and pressing the button there — which reads `Add to bag` — produces
`CHARCOAL CELLBLOCK SHORTS  Size: L  £45.00` / `CHARCOAL CELLBLOCK CREWNECK  Size: M  £50.00`
/ `Estimated total £95.00 GBP`, with no discount applied and no mention of the set anywhere.
With both halves in the cart in matching sizes, the store says nothing. Using the *toggle* on
that landing page instead adds an £85 set line **on top of** the £50 crewneck already there.
**Cost:** the store makes a specific money promise, links to a page, and the obvious action on
that page charges £10 more than it just said. This is the one finding here that reaches a
complaint rather than a shrug.
**Evidence:** `audit/screens/set-34-followed-offer-landing.png`,
`audit/screens/set-35-cart-after-following-offer.png`

### 2.2 The store tells a shopper the shorts are sold out in every size when 201 units are in stock

**Should:** tick the set box before choosing your own size, pick a partner size, and the panel
either waits or asks for the missing choice.
**Did:** it says, in the store's error red, `Cellblock Shorts sold out in M — pick another
size`. There were **19** shorts in M. Sweeping the whole row with no crewneck size chosen gave
the same sentence five times, once per size — so the instruction it gives cannot be obeyed.
Meanwhile the buy button reads `SELECT A SIZE` and is dead, so the shopper holds two
contradictory instructions and neither states the true one: *choose your own size first.*
**Cost:** a false out-of-stock, in the error colour, at the moment of decision. The honest
response to that message is to abandon the set. The shorts side of the same feature already
has the right words — its button becomes `Pick a Cellblock Crewneck size` — so the fix is copy
that exists inside the feature already.
**Evidence:** `audit/screens/set-03-partner-only-no-own-size.png`,
`audit/screens/set-03b-partner-only-viewport.png`

### 2.3 `ON MODEL` shows a photograph of a different garment on all twelve cards

**Should:** show each product on a person.
**Did:** the toggle works on every card and swaps all twelve to **one file** — a full-length
photo of a man in a black tee and grey shorts. `NO. 01 CHARCOAL CELLBLOCK CREWNECK £50.00`
shows a tee and shorts. `NO. 03 BLUE WASH OG JEANS £60.00` shows the same shorts.
`NO. 10 BLACK/BLUE MOTIONTEC™ SOCKS £6.00` and `NO. 12 LARGE DUFFLE BAG £18.00` show the same
man again. The first four cards become four copies of one photograph.
**Cost:** the one control that promises "show me this worn" answers every question with a
picture of something else, at the moment a shopper is comparing. Comparing the jeans against
the jorts on model gives two identical pictures of shorts. Worse, model photography of the
real products already exists on the store — `BLUE WASH OG JEANS` carries one as its second
image and a desktop hover shows it — and the toggle ignores it.
**Evidence:** `audit/screens/catalogue-B11-onmodel-controls.png`,
`audit/screens/catalogue-B12-card10-onmodel.png`, `audit/screens/catalogue-C12-after-back.png`

### 2.4 Typing `returns` — the word everybody types — ends off-site on a form the shopper cannot fill

**Should:** someone asking about returns before buying wants to read the terms; someone asking
after buying wants the portal. Offer both.
**Did:** `returns` produces exactly one destination, in the suggestions and on the results
page: `START A RETURN` / `RETURNS CENTRE`, opening a new tab on `5wn03tnm.aftership.com`.
`exchange` behaves identically. Neither offers `REFUND POLICY`, `TERMS` (which has
`03 RETURNS` and `04 SIZE SWAPS`) or `QUESTIONS` (which has `CAN I RETURN SOMETHING?`).
Typing `refund` instead — one word apart — offers `REFUND POLICY` immediately.
**Cost:** documented in full in `audit/journeys/12-searcher.md`, whose shopper said out loud
*"I don't have an order number, that's the whole point."* The portal asks a pre-purchase
shopper to prove they are already a customer. Five minutes, four different search words and a
trip to a stranger's website to read a policy that is two taps away under a different noun —
and the shopper did not buy.
**Evidence:** `audit/screens/12-06-aftership.png`,
`audit/screens/search-11-results-returns.png`, `audit/screens/12-13-type-refund.png`

### 2.5 The third-party returns page says 30 days; CROOKSLDN says 14

**Should:** one return window.
**Did:** the portal that `returns` sends people to carries its own policy: items are returnable
*"Within 30 days from the date of purchase"* and faulty items must be raised *"within 7 days of
the delivered date"*. The store's own answer, on four surfaces, is 14 days and — for transit
damage — 48 hours.
**Cost:** this is the first and often only returns text a searching shopper is shown, and it is
wrong by a factor of two on the number that matters most. The shopper in journey 12 found the
real policy afterwards and described the effect precisely: *"that relief turned into distrust."*
**Evidence:** `audit/screens/12-06b-return-policy-from-portal.png` against
`audit/screens/12-14-refund-policy.png`

### 2.6 `0 RESULTS` is printed directly under the links that matched

**Should:** one screen should not report success and failure at once.
**Did:** searching `terms` gives, top to bottom: `DIRECT LINKS` / `TERMS` `TERMS` /
`SEARCH: TERMS` / `0 RESULTS` / `PAGES & ANSWERS` / `TERMS` `PAGE` / `NO ITEMS IN THE REGISTER
MATCH THAT QUERY.` Three links to the Terms page, and between them the words `0 RESULTS`. The
same shape appears for `returns`, `refund`, `contact`, `help`, `exchange` and `cancel my order`.
**Cost:** `SEARCH: TERMS` is the biggest thing on the screen and the failure line runs full
width beneath it, while the links that matched are set small above. Journey 12's shopper read
the zero first and concluded the site had no returns information at all.
**Evidence:** `audit/screens/search-70-terms.png`, `audit/screens/12-05-results-returns.png`

### 2.7 A failed search is a dead end — and gets less help than a blank one

**Should:** a failed search offers a way out.
**Did:** `qwzzptx` produces the entire page: `SEARCH: QWZZPTX` / `0 RESULTS` / `NO ITEMS IN THE
REGISTER MATCH THAT QUERY.` No suggestions, no catalogue link, no direct links. `DEIM` (a typo
for DENIM) does the same. The **blank** search page offers three real destinations; the
**failed** one offers zero.
**Cost:** on a twelve-product store, showing the whole register would almost always be the right
answer. The three links already exist and already appear on the blank page. (This is not the
empty-search stand-down, which is deliberate and works — see §5.)
**Evidence:** `audit/screens/search-21-results-qwzzptx.png`

### 2.8 The header bag count never moves when you change the cart

**Should:** the count agrees with the cart it is sitting directly above.
**Did:** with the cart showing two jeans and £120.00, the header still read `BAG [1]`, and still
read it nine and a half seconds later. Pressing `−` then left `BAG [2]` above a one-item
£60.00 cart. Emptying the cart left **`BAG [2]` sitting directly above the words `Your cart is
empty`**. Only a reload corrects it. Totals and the carriage bar on the same page do update
live, which makes the stale number read as deliberate.
**Cost:** two numbers on one screen disagreeing about what a shopper is buying, at the exact
moment they are checking they got it right.
**Evidence:** `audit/screens/cc-70-after-remove.png`, `audit/screens/cc-61-plus-1500ms.png`

### 2.9 The drop register takes a phone number and says nothing back

**Should:** press `ENTER`, get told you joined.
**Did:** across seven attempts, the intake produced exactly two messages ever:
`Phone number is required` and `Email is invalid`. A valid UK mobile (`07700900123`), the same
number a second time, and a junk number (`+44 1234`) all produced **identical silence** — no
confirmation at 3s, 8s or 40s, the number still sitting in the box. The field is pre-filled
`+44`, so typing a UK mobile the normal way leaves it reading `+44 07700 900123` — country code
*and* trunk zero — and nothing objects. Pressing `ENTER` dims the page behind a **blank white
panel** where the bot check should be.
**Qualification, and it matters:** that bot check is designed to refuse automated browsers, so
this session failing it is close to expected and is **not by itself** a shopper-facing fault.
What is confirmable regardless: when the check does not complete the shopper is shown **no
message of any kind** — no error, no explanation, no retry, input still in the field — and
there is no confirmation state on success either, so nothing distinguishes "signed up" from
"silently failed".
**Cost:** you hand a brand you just met your mobile number and the page does not change. The
natural next move is to press `ENTER` again and then assume the site is broken — having given
up the number either way.
**Evidence:** `audit/screens/homepage-B2-good-number-3-after-8s.png`,
`audit/screens/homepage-C2-after-enter-40s.png`, `audit/screens/homepage-21-intake-empty.png`

### 2.10 The cart never confirms the set saving

**Should:** `SPEC.md §3.13` — "the bundle in the cart → the saving confirmed in words".
**Did:** nothing appears. With `CELLBLOCK SET` in the cart the page runs straight from the
carriage bar to `Cart`; no `£95`, no "saved £10", nothing. The line item does not restate it
either. The sibling state works perfectly — with only the shorts in the cart, `Complete the set
— add the Cellblock Crewneck, save £10.` appears above the cart title — so the feature looks
fine until someone actually buys the set.
**Cost:** between pressing `ADD THE FULL FIT — £85` and paying, the £10 is never mentioned
again. The screen where people check they got what they thought is the screen where the deal
disappears. With `10CROOKS` applied (**O1**), the only saving the cart ever names is the code's
`−£8.50`.
**Evidence:** `audit/screens/cc-91-set-in-cart-full.png`,
`audit/screens/set-16b-cart-one-half-viewport.png` (the state that does work)

### 2.11 "Sold out" and "leaves today" in the same eyeful

**Should:** the dispatch promise stands down when the chosen size cannot be bought.
**Did:** with `SIZE M IS SOLD OUT` on screen in red on `v2-baggies`, the two lines directly
above it still read `Order before 18:00 and it ships today (Mon–Sat)` and `> Ordered now —
leaves today`.
**Cost:** the page tells a shopper this size cannot be bought and that ordering now gets it out
the door today, in the same glance. It reads as carelessness on the one screen where the store
is asking to be trusted with £60.
**Evidence:** `audit/screens/pdpcore-11-baggies-soldout-M.png`

### 2.12 The sticky bar never goes away, and it sits on the one button the sold-out state needs

**Should:** `SPEC.md §3.5` — the bar appears "only while the primary control is off-screen".
**Did:** traced down the crewneck page at twelve scroll positions including the very top: it is
present at every one, 69px tall, fully opaque. At three of those positions the real `ADD TO BAG`
is plainly on screen and the theme correctly marks the bar as hidden — and it stays visible
anyway. One screenshot shows the inline `ADD TO BAG` mid-screen and the sticky `ADD TO BAG` at
the foot of the same screen. In the sold-out state the purple `NOTIFY ME` button runs to y=776
and the bar starts at y=775, so its bottom edge disappears underneath.
**Cost:** 8% of every phone screen spent on a duplicate of a button that is often already
visible, and the one control the sold-out state wants pressed is clipped by furniture. It also
covers the first tile of `MORE FROM THIS DROP`, which is why the jeans page appears to list
itself (it does not — zero self-links on all twelve products).
**Evidence:** `audit/screens/pdpcore-90-added-to-bag.png`,
`audit/screens/pdpcore-140-sticky-doubled.png`, `audit/screens/pdpcore-11-baggies-soldout-M.png`

### 2.13 The sticky bar states the wrong price while the set is on

**Should:** the bar repeats the price and size of the thing about to be bought.
**Did:** with the set ticked and crewneck M + shorts L chosen, the bar reads
`CHARCOAL CELLBLOCK CREWNECK` / `£50.00 · M` / `ADD THE FULL FIT — £85` / `CHECKOUT NOW`. On a
390px phone the longer button label squeezes the text until the name truncates to `CH…` and the
price clips to `£50.0` on one line and `· M` on the next.
**Cost:** the sticky bar is the control a phone shopper actually uses, because it follows them
down the page while the set panel scrolls away. While the set is on it states the wrong price,
one size where two were chosen, and a cut-off product name.
**Evidence:** `audit/screens/set-42-stickybar-visible.png`,
`audit/screens/set-43-stickybar-element.png`

### 2.14 The FAQ sends shoppers to an order lookup that does not exist

**Should:** the tracking page does what the FAQ says it does.
**Did:** FAQ q5: *"You can also look your order up on the tracking page — no account needed."*
The whole of `/pages/tracking`, signed out, is five lines and one button: `IDENTIFICATION
REQUIRED` / *"Order records are released to the account they were filed under. Sign in to view
the chain of custody for your orders."* / `SIGN IN` / `NO ACCOUNT? THE TRACKING LINK IN YOUR
DISPATCH EMAIL OPENS YOUR ORDER WITHOUT ONE.` There is not one field on the page. FAQ q13
compounds it: *"You can check out as a guest and still track your order."*
**Cost:** a guest whose dispatch email went to spam has no route to their order except emailing
and waiting 1–2 working days. The bitter part: the returns portal the FAQ and Terms both link to
*does* do exactly this lookup (`ORDER NUMBER / EMAIL / VERIFY BY POSTAL CODE OR PHONE NUMBER /
FIND YOUR ORDER`) — the capability exists on a page nobody is sent to when they want tracking.
Search also offers `TRACK YOUR ORDER` to everyone before they have typed anything.
**Evidence:** `audit/screens/content-pages-tracking-signedout.png`,
`audit/screens/search-83-tracking-landing.png`, `audit/screens/content-pages-returns-centre.png`

### 2.15 The best support page on the store is linked from nowhere and offers a form it cannot show

**Should:** the page that answers "how do I reach you" is reachable.
**Did:** `/policies/contact-information` carries the strongest customer-service copy on the site
— *"BEST WAY TO REACH US — Email — Crooksldn@gmail.com. We reply within 1–2 working days
(Mon–Sat). To get help fastest, include your order number and a quick line on what's up — plus a
photo if it's about a faulty or wrong item."* Every link on `/`, `/pages/faq`, `/pages/terms` and
`/pages/contact` was followed: **none reaches it.** The footer's CONTACT column holds INSTAGRAM,
TIKTOK and EMAIL only. The page then ends *"Prefer a form? Drop your details below and we'll come
back to you at the email you give us."* — below it is the site footer.
**Cost:** the store looks like it has no contact information because the page that has it is
invisible. Meanwhile `/pages/contact` — where the menu actually sends people — is a bare
`Name / Email* / Phone / Comment / Submit` with no email, no address, no phone and no reply-time.
A shopper who taps CONTACT to *find out* how to reach the brand learns less than before they
tapped.
**Evidence:** `audit/screens/content-pages-policy-contact-clean.png`,
`audit/screens/content-pages-cold-02-contact.png`

### 2.16 On a phone the menu cannot be closed the two ways a phone user tries first

**Should:** the close control, tapping outside, Escape, Back.
**Did:** `CLOSE` works and Escape works. **Tapping outside is impossible** — the panel is
exactly as wide as the screen, so there is nothing outside it; every point of the area was swept
at 8px intervals and the drawer stayed open. **Back does not close the drawer, it leaves the
page**: from `/collections/all` with the drawer open, Back went to the homepage — drawer gone,
collection gone. On a fresh tab it is worse: homepage → open drawer → Back lands on
**`about:blank`**, the site gone. On a desktop, where the panel is 420px on a 1440px screen,
clicking outside works fine.
**Cost:** tap-outside-to-dismiss exists only on the device where people use Escape, and does not
exist on the device where it is the primary gesture. A first-time visitor who opens the menu out
of curiosity and swipes back is off the site entirely.
**Evidence:** `audit/screens/hdr-a11-after-scrim-tap.png`,
`audit/screens/hdr-d21-freshtab-after-back.png`,
`audit/screens/hdr-d24-desktop-after-outside-click.png`

### 2.17 Filtering to a category leaves a purple slab where a product should be

**Should:** a filtered register shows the products and nothing else.
**Did:** when a filter leaves a count that does not fill the last row, the unfilled slot appears
as a **solid lavender rectangle the exact size of a product card**. `SWEATS` (3 items) and
`ACCESSORIES` (3 items) both produce one on a phone; `ACCESSORIES` produces one on a 1440px
screen too, standing beside the duffle bag. Nothing else on the site is a solid block of colour
that size.
**Cost:** the shopper who narrows to the category they want is the most committed shopper on the
site, and the register answers by showing them one broken-looking tile next to three real ones.
**Evidence:** `audit/screens/catalogue-B20-filter-accessories.png`,
`audit/screens/catalogue-E03-desktop-odd-count.png`

### 2.18 A whole category is off the right edge of the phone with nothing saying so

**Should:** a shopper can see every category on offer.
**Did:** the category row holds 604px of content in a 358px strip. A phone shows
`> ALL   T-SHIRT   DENIM   SW` — `SWEATS` sliced through its third letter and `ACCESSORIES`
starting 91px past the right edge, invisible. No arrow, no fade, no wrap: the row ends on a
clean vertical rule that reads as the end of the list. Swiping works; nothing suggests it.
**Cost:** three of twelve products — the socks and the duffle bag — are hidden behind an
unadvertised swipe on the device most people shop on. `DENIM` looks like the last category in
the shop.
**Evidence:** `audit/screens/catalogue-A01-home-top.png`,
`audit/screens/catalogue-D20-filterrow-asfound.png`

### 2.19 In light mode the button that runs the search is invisible

**Should:** the button that submits the search can be seen.
**Did:** on `/search` in light mode the `SEARCH` submit is cream text with no background at all
on a near-white ground — a contrast of 1.38:1. In dark mode the same button happens to read as
cream on black and is perfectly legible.
**Cost:** in light mode a shopper types "jeans", sees the box and the line `SEARCH BY ITEM,
CATEGORY OR COLOUR`, and there is no visible button between them — they have to guess that Enter
works or that the blank gap is tappable.
**Evidence:** `audit/screens/tg-search-light.png` against `audit/screens/tg-search-dark.png`

### 2.20 Two pages ignore the theme switch — and they are the two a worried shopper lands on

**Should:** a mistyped URL or a dead link still looks like the shop.
**Did:** in dark mode — the default — the 404 shows a black header above a full-screen cream
body in Horizon's own typeface: `PAGE NOT FOUND`, *"The link may be incorrect, or the page has
been removed."*, a black `Continue shopping` block and a `Discover something new` row. Pressing
`LIGHT MODE` changes nothing below the header; the two captures are identical. `/pages/contact`
behaves the same way.
**Cost:** on a phone in a dark room a dead link throws a full-screen cream page at you, which
reads as "wrong site / something broke" at the worst possible moment. Functionally the 404 is
fine — header, footer and four buyable products with prices — but it looks like the failure it
is reporting. The theme switch, which works everywhere else, silently stops working there.
**Evidence:** `audit/screens/tg-404-dark.png` against `audit/screens/tg-404-light.png`,
`audit/screens/tg-contact-dark.png`

### 2.21 The header row is set at two sizes

**Should:** one row of controls, one type treatment.
**Did:** the split follows nothing a shopper can see: `CATALOGUE`, `SEARCH` and `BAG [0]` are
9px; `LIGHT MODE` and `MENU` are 13px and a notch lighter — 44% bigger, side by side in the same
44px row. `MENU` and `LIGHT MODE` visibly loom over the rest. The same split runs into the
drawer: heading `MENU` at 10px beside a `CLOSE` at 13px, and the drawer's `ACCOUNT` and `BAG` at
9px.
**Cost:** cosmetic, but in the one place this design cannot afford it. In a store whose entire
pitch is typographic discipline, the header reads as if two people built it — which quietly
withdraws the claim the whole build rests on.
**Evidence:** `audit/screens/hdr-a05-header-bar.png`, `audit/screens/hdr-a12-after-escape.png`

### 2.22 With JavaScript off, the first line of the page is garbled

**Should:** the first message shows and the bar clips the rest.
**Did:** both messages appear at once, colliding in a 28px strip. Message one wraps to
`FREE UK SHIPPING OVER £20 — ORDER` / `BY 18:00 FOR SAME-DAY DISPATCH` and message two is
squeezed beside it as `12 PRODUCTS` / `CURRENTLY` / `ONLINE`, the top line cropped by the edge
above and `ONLINE` sliced in half by the border below. Unchanged after 20 seconds, so it is the
finished state.
**Cost:** a no-JS shopper's first impression is a broken-looking top line — on a store whose
whole proposition is that everything is deliberate — and the sentence being mangled is the
delivery promise.
**Evidence:** `audit/screens/status-bar-x-h-nojs-bar.png`,
`audit/screens/status-bar-x-h-nojs-after20s.png`

### 2.23 A quantity of `0` is silently rewritten to `1`

**Should:** either work, or say why not.
**Did:** `−` is disabled at 1. Typing `0` and pressing Enter does nothing at all; typing `0` and
tapping away rewrites the box back to `1` with the cart unchanged at 3 items and £155.00. There
is no message. Removing a line works — the bin is fast and quiet, 900ms — but there is **no
undo, no "removed" line and no toast** anywhere, and the word "undo" is in none of the theme's
English.
**Cost:** anyone who reaches for the number box to drop a line has to work out for themselves
that the bin is the only route, and a misplaced tap on the bin costs the item and the size
choice with no way back but finding the product again.
**Evidence:** `audit/screens/cc-82-zero-by-blur.png`, `audit/screens/cc-70-after-remove.png`

### 2.24 The fake-code message blames the cart and wipes what was typed

**Should:** say the code is not real.
**Did:** `FREESTUFF123` clears the field and shows, in the site's own mono with a red dot:
`Discount code cannot be applied to your cart`.
**Cost:** wrong diagnosis — "cannot be applied to your cart" reads as *the code is real but wrong
for these items*, which invites a shopper to go and change their cart. And because the field is
cleared, a mistyped real code has to be retyped from scratch.
**Evidence:** `audit/screens/cc-99-fake-code-error.png`

### 2.25 The two cheapest garments have no way onward

**Should:** related products on every product page.
**Did:** `MORE FROM THIS DROP` works well everywhere else — relations follow the collection, two
or three tiles, nothing random, and zero self-links across all twelve products. On
`evil-clive-tee` and `crxst-rz-t-shirt` — the two t-shirts at £25 — there are no tiles and the
heading does not appear at all. The page ends at the accordions.
**Cost:** the two cheapest, most shareable garments — the natural entry point from Instagram —
are the two pages with no onward route except the browser's back button.
**Evidence:** `audit/screens/pdpcore-95-evilclive-related.png`

### 2.26 In dark mode the FAQ's escape hatches are the dimmest words in the answer

**Should:** a link inside a paragraph is at least as readable as the paragraph.
**Did:** in dark — the default — the closing paragraph's links `crooksldn@gmail.com`,
`@crooksldn` and `terms page` are noticeably darker than the body text beside them (2.12:1). The
same treatment lands on `tracking page`, `the returns centre` and `Start your return here`. In
light mode the same links are fine.
**Cost:** the email address and `Start your return here` are precisely the words a stuck shopper
is scanning for, and they are the least visible ones on the page in the theme almost everyone
sees.
**Evidence:** `audit/screens/tg-faq-dark.png` against `audit/screens/tg-faq-light.png`

### 2.27 The discount overlay lands on the two sections that do the selling

**Should:** not interrupt the moment of decision.
**Did:** with no interaction at all, a full-screen overlay takes the page. On the homepage run it
arrived at **38.9 seconds**; on the cold-arrival run it waited for the cookie sheet to be
answered and then took another ~9 seconds, about 6 of which are a completely black screen with a
single `×` while it loads. It reads: `CRACK THE CUFFS.` / `10% off your first order if you do.
Three tumblers. Tap each one at the right moment.` / `RUN IT` / `NOT NOW` / `One code per player.
Attempts unlimited. Code expires in 20 minutes.` / `(this drop closes 15.09)`. In three separate
runs it landed on the packaging manifest or on the intake, once arriving while the form was being
filled in. Two `×` controls are on screen at once while it is up, and it dims the status bar to
near-invisibility on the one screen where the £20 line is guaranteed to be covered.
**Cost:** thirty-nine seconds is almost exactly how long it takes to read the register, reach the
packaging section and start filling in the register form. It is a discount offer interrupting the
only two sections on the homepage that argue for a purchase.
**Evidence:** `audit/screens/homepage-95-ctc-overlay.png`,
`audit/screens/homepage-92-duplicate.png`, `audit/screens/hdr-d05-ctc-overlay.png`,
`audit/screens/status-bar-x-msg1.png`

### 2.28 Known-item impacts (not discoveries — tags only)

- **Cookie sheet (known: "No cookie banner").** There is one, and it owns the bottom 359px of
  844 on every first visit. On a product page it covers the `<h1>`, the price, the whole size row
  and both buy buttons — a first-time mobile visitor sees a photograph and a legal notice, and
  must deal with the notice before learning what the thing costs. In the open menu it cuts the
  drawer off at `TRACKING`, and a tap on `PLAY CASE:001 NOW` in that state lands on the banner's
  `Accept` instead. On the FAQ it lands over the first question; on Terms it covers clauses 03
  onward; on `/search` it covers the third pre-typed link; tapping `MEASUREMENTS` on a first
  visit opens the table underneath it, so the only thing that changes on screen is `+` becoming
  `−`. One tap on `Accept` or `Decline` clears it and it does not return.
  Evidence: `audit/screens/pdpcore-02-banner-over-buybox.png`,
  `audit/screens/hdr-d03-case-panel-under-consent.png`,
  `audit/screens/pdp-sizing-jeans-measurements-open.png`.
- **D1 — status bar cadence.** Runs at 8s per line, 16s per loop, on every page. Judged as a
  shopper: 8 seconds is too *slow*, not too fast — the longer line takes about three seconds to
  read, so five of every eight are spent on a line already read. If the persisted `5` ever took
  effect the bar would read better, not worse.
- **O1 — `10CROOKS` on the set.** `Subtotal £85.00` / `10CROOKS −£8.50` / `Estimated total
  £76.50 GBP`, surviving a reload. No cost to the shopper (they gain £8.50); the cost is that the
  set's entire pricing story — `£95` struck, `£85 for the set`, `Save £10.` — stops being true
  the moment a public code is in play. The code also persists on a restored cart across visits
  until removed by hand. Evidence: `audit/screens/cc-92-10crooks-on-set.png`.
- **O3 — the `Outline` treatment.** It is **on by default** and it applies to product pages, not
  just the register. On `CHARCOAL CELLBLOCK SHORTS` the cream keyline traces waistband, side
  seams and hem and reads as cream binding; on the crewneck it traces collar, cuffs and hem and
  reads as ribbed trim, at the size where a shopper studies the garment before pressing
  `ADD TO BAG`; on both blue washes it runs down the outseam like white piping. Where it helps —
  the black socks and the duffle on a near-black panel — the gain is marginal and both are
  entirely readable without it. In light mode both states are identical, yet the button still
  lights up when pressed. Shopper cost: reading "charcoal sweats with cream binding" and "blue
  jeans with white piping" off the register and the product page, when neither exists. That is
  the kind of gap that comes back as a return. Evidence:
  `audit/screens/catalogue-A11b-card2-outline-toggled.png`,
  `audit/screens/catalogue-D14-pdp-image-outline-on.png`,
  `audit/screens/catalogue-D10-light-outline-on.png`.
- **O4 — CASE 001 art and link out of step.** A shopper would not notice on arrival: the
  destination's landing screen is a title card with no game art to compare. The one visible tell
  is the version number — the shop footer says `EVIDENCE TERMINAL V0.2`, the game footer says
  `EVIDENCE TERMINAL v0.1 // CROOKS UK`, one tap apart. Evidence:
  `audit/screens/hdr-d13-case001-landing.png`.
- **Placeholder measurements.** Impact only: `V2 BAGGIES` and `GREY WASH OG JEANS` publish
  byte-identical tables — `XS 76.2 / 73.7 / 45.7` through `XL 96.5 / 81.3 / 55.9` under
  `WAIST · INSEAM · LEG OPENING` — for a wide 500gsm sweat and a "structured, not baggy" 14oz
  jean. Nine products carry a table and seven of those nine are running three tables between
  them. A shopper buying the baggies *for the wide leg* is told the leg is 20in around at M; if
  that is wrong they pay to send it back, because `Return postage is yours`. Evidence:
  `audit/screens/pdp-sizing-jeans-measurements-open.png` against
  `audit/screens/pdp-sizing-baggies-measurements-cm.png`.

### 2.29 Two places where the raw notes disagree — recorded, not resolved

- **The packaging photograph.** The homepage pass describes a real photograph — three items on
  black with yellow evidence tents numbered 1, 2, 3 mapping one-to-one onto the manifest — and
  the capture confirms it (`audit/screens/homepage-A3-packaging-clean.png`). The toggles pass
  reports the frame **empty in both themes**. Checked against the evidence: in dark mode the
  photograph is plainly there; in the light-mode capture the same bordered frame is blank
  (`audit/screens/tg-home-light.png`). So it is not "empty in both themes" — but the light-mode
  state needs one look on a handset before anyone concludes the picture is missing there. If it
  is, it is the only argument-to-buy on the homepage disappearing for half the audience.
- **The four product accordions.** `SPEC.md §3.5` and §9.4 say four `<details name>` panels,
  default closed and **mutually exclusive** — "opening one should close the others". The product
  page pass found them to be buttons and found all four open at once, in order
  (`audit/screens/pdpcore-40-acc-chain-of-custody.png` shows the four-open state). The FAQ's
  fourteen accordions *do* behave as the spec describes — one open at a time. So the exclusivity
  the spec claims exists on the FAQ and not on the product page. Nothing is stuck or unreachable;
  the cost is that a shopper who opens all four — exactly what someone deciding on a £60 purchase
  does — pushes `MORE FROM THIS DROP` a long way down and has to scroll back past four open
  panels to reach the size row.

---

## 3. What I expected to exist and could not find

Absences, not faults. These need copy, data or a decision — not a repair.

**On the goods**

- **Any way to enlarge a product photograph.** Not by tapping, double-tapping, hovering or
  clicking, on either device. The largest view of a £60 pair of jeans a shopper can obtain is a
  332-pt square. The detail exists — the store holds a 2048px master — and the page never lets a
  shopper near it. Evidence: `audit/screens/pdpcore-82-after-photo-tap.png`,
  `audit/screens/pdpcore-105-after-click-photo.png`.
- **A second angle on the expensive garments.** Seven of twelve products have exactly one
  photograph, four of those seven at £50–£60. `GREY WASH OG JEANS` (£60) is one flat cut-out of
  the **back**; there is no front, no waistband, no hem, no leg opening, nothing on a body and no
  scale reference — while `SPECIFICATION` says `14oz denim` and asks to be taken on faith.
  Evidence: `audit/screens/pdpcore-101-desktop-jeans.png`.
- **Any photograph of the clothes on a person, anywhere.** No lookbook on the homepage — the
  word appears in no text and no link. The only photograph on the whole homepage is the packaging
  shot. Evidence: `audit/screens/homepage-A9-full.png`.
- **A legend for the low-stock mark.** A 4×4px purple square sits on XL of `cb1-wash-jeans` with
  no key, no tooltip, nothing. Select XL and it resolves to `3 LEFT IN SIZE XL` — a real number,
  quietly stated, which is right. A shopper who never taps XL never learns the mark means
  anything. Evidence: `audit/screens/pdpcore-150-lowstock-xl.png`.
- **A sold-out card state that could be observed at all.** Nothing in the register is currently
  sold out, so the register's most important status has never been seen in the wild.

**On copy the theme has nowhere to put**

- **Any collection description on any collection page.** This is *not* the known "three
  collections have no description" item — it is worse. The Denim collection **has** a description
  in admin (`Jorts, jeans and denim.`) and the register never shows it, because there is no slot
  for one. `/collections/denim` reads, in full, before the first card: `DENIM` / `4 ITEMS` /
  `FLAT` / `ON MODEL`. The eight outstanding collection descriptions in the SEO plan would put
  zero words on the page as things stand. Evidence: `audit/screens/catalogue-C01-denim-fold.png`.
- **Any sentence on the homepage saying what CROOKSLDN is or where it ships from.**
  `OWN THE STREETS™` is a slogan; the only prose above the footer is the packaging paragraph.
- **An About page.** Nothing in the header, the drawer, the footer or the FAQ. On a brand with no
  reviews, there is nowhere to learn who this is.
- **A plain-English resolution of the packaging footnote.** `* CONTRABAND 03 SHIPS WITH SWEAT
  BOTTOMS ONLY.` — nothing on the site is called "contraband", and no product is called "sweat
  bottoms"; the register sells `CHARCOAL CELLBLOCK SHORTS`, `V2 BAGGIES` and `CHARCOAL CELLBLOCK
  CREWNECK`, all filed under `SWEATS`. The one item with a condition attached is the one item a
  shopper cannot act on. Evidence: `audit/screens/homepage-A4-packaging-manifest.png`.

**On answers a shopper needs before paying**

- **A price for postage on the product page.** The accordion titled `SHIPPING & RETURNS` mentions
  money twice — `over £20`, `over £70` — and never gives a price. `£3` and `£4.99` exist, well
  written, on the Shipping policy, two taps away and never in the place a shopper looks.
- **International shipping cost, on any page.** "Calculated at checkout" is the answer on all
  three surfaces that address it. An Irish or Dutch shopper cannot find out what postage costs
  without building a cart.
- **The £20 free-shipping threshold anywhere on the shopping path except the rotating strip.**
  The full visible text of the homepage, the catalogue, a product page with every accordion
  forced open, and the cart were scanned: `£20` appears nowhere else. The single commercial fact
  most likely to make someone add a second item is delivered at 9px, for eight seconds out of
  every sixteen, only above the fold, and on the homepage it is behind an overlay.
- **Any statement that a size swap is possible, free, and posted back out at the shop's
  expense** — at the moment of the size decision. It is the single most reassuring sentence on
  the site for a shopper hovering between M and L, and it lives two taps away on a policy page.
- **A "which size am I" prompt at the point of decision.** `QUESTIONS` offers *"If the piece you
  want is not listed yet, message us and we will measure it for you."* and Contact offers
  *"message us your usual fit and we'll point you to the right one"*. The product page, where the
  shopper is actually stuck, offers neither.
- **A method note for the columns that need one** — `SHOULDER`, `SLEEVE`, `LENGTH`. One caption
  is doing duty for jeans, sweatpants, crewnecks and tees, and it names columns those tables do
  not have.
- **Any sign that a four- or five-column measurements table can be dragged sideways.** On the
  crewneck the `SLEEVE` values are sliced mid-character at the phone's edge — `62.2cr`, `63.5cr`,
  `64.8cr` — and sleeve length is exactly what someone buying a heavy crewneck checks. Evidence:
  `audit/screens/pdp-sizing-crew-sizeguide-after.png`.
- **A restock or drops answer in the FAQ**, on a store where sold-out sizes stay visible by
  design and a notify field sits on the product page.
- **Any FAQ answer about discount codes**, on a store running `10CROOKS` and an £85 set.
- **Care instructions outside the product page's `SPECIFICATION` accordion.**
- **A phone number anywhere a shopper would look.** The only one on the site, `+44 7449 010089`,
  is in the last paragraph of the privacy policy — while `/pages/contact` asks the shopper for
  theirs.
- **Any guest route to an order.** Only the dispatch email.

**On the set**

- **The total (`£85`) in the collapsed line.** A shopper deciding whether to open the offer knows
  only "£50, plus something, minus £10". The two numbers that make the case — £95 and £85 — are
  both behind the tick. Evidence: `audit/screens/set-01-collapsed-row.png`.
- **The partner's price (`£45`) anywhere in the offer**, so `Save £10.` can be checked.
- **Any positive stock signal for the partner.** The panel's only stock sentence is a negative
  one; for every genuinely buyable pairing — including the 4-unit ones — the line is blank, while
  the garment on screen says `IN STOCK` two inches above.
- **Measurements or a size guide for the partner garment**, at the moment its size is being
  asked for. The thumbnail in the offer is not a link.
- **Any statement that this is two garments.** "The full fit" is doing that job alone until the
  cart.
- **Any offer to convert two halves already in the cart into the £85 set.**
- **Any route to browse sets.** `Sets` is in no menu; the crewneck and shorts pages never link to
  `CELLBLOCK SET`. Search finds it; browsing never will. Its own page shows two size rows, the
  second named (`CHARCOAL CELLBLOCK SHORTS (SIZE)`) and the first bare (`SIZE`), a crewneck-only
  hero image, and no measurements for either garment. Evidence:
  `audit/screens/set-25-bundle-pdp.png`.

**On the cart and checkout**

- **Any undo, or any confirmation, after removing a line.**
- **Any statement of what carriage *costs* if the free tier is not reached.** The cart names only
  the free thresholds, then `Duties and taxes included. Shipping is calculated at checkout.`
- **A cart note field.** A shopper cannot say "leave with a neighbour".
- **Any CROOKSLDN framing on the empty cart.** No title, no register line — Shopify's stock
  `Your cart is empty` / `Have an account? Log in to check out faster.` / `Continue shopping`,
  in sentence case, in a shop that writes in uppercase evidence-log register everywhere else.
  Evidence: `audit/screens/cc-30-empty-cart-newsession.png`.

**On navigation**

- **A wordmark in the header.** The `CROOKSLDN` wordmark only appears when no logo is uploaded,
  and one is — so on every page except the homepage the only thing naming the shop above the fold
  is a pair of handcuffs.
- **`ACCOUNT` in the header.** It is at the foot of the drawer, 200px below the fold of an
  already-opened menu. A returning customer looking for their orders taps `MENU`, scrolls past
  twelve category links and a video game, and only then finds it.
- **Any sign on the homepage that CASE 001 exists.** The only pointer outside the drawer is a
  footer link at y=4769 of a 4890-tall page — the last 2.5%.
- **A label on the CASE 001 panel.** The art has no heading; the only words are on the button,
  and the button is 118px below the fold of the opened drawer.
- **A way back to the shop from the CASE 001 game.** Its only three controls are `START CASE`,
  `LEADERBOARD` and `SOUND: ON`. It opens in a new tab, so the shop survives — but a phone user
  who does not realise a tab was opened has no route home.
- **Anchors on the search page's FAQ links.** `SIZE GUIDE` and `QUESTIONS` both land at the top
  of a fourteen-question page; the sizing answer is at y=821 and the returns answer at y=946.
- **A pre-typed link to `TERMS`** on the blank search page — the page carrying carriage,
  dispatch, returns and refunds in plain English has to be guessed at.
- **Any heading on `/search`.** The template has none, blank or with results.
- **A second hero route.** One button, `CATALOGUE`, and it is an in-page jump to a heading
  already visible on the same screen once the cookie sheet is gone.
- **Return to the shopper's place in the list after Back.** The filter survives perfectly; the
  scroll position does not.
- **The `OUTLINE` control on collection pages**, where the treatment still applies. It exists on
  the homepage only, so a shopper arriving from `CATALOGUE`, a search result or a shared link
  sees the treatment with no way to turn it off.
- **A carriage readout anywhere near the buy controls.**

---

## 4. Contradictions

The highest-value section. Every one of these is the site telling a shopper two different
things, with both sides quoted. Grouped so each cluster can be settled in one pass.

### Group A — Returns: five surfaces, five stories

1. **How long you have.** Terms c3: *"You have 14 days from delivery to tell us you want to
   return something, **and 14 days from then to post it back**."* Product page, chain of custody,
   every product: *"You have **14 days from delivery to return** unworn goods with tags
   attached."* Refund policy: *"14 days from delivery to return or exchange."* A shopper reading
   the product page thinks the parcel must be back within 14 days; a shopper reading the Terms
   has 28. The strictest version is the one shown **before** buying.
2. **The third-party page says 30.** The portal that `returns` sends people to:
   *"Within 30 days from the date of purchase"*, and *"reach out to us within **7 days** of the
   delivered date"* for faulty items. `audit/screens/12-06b-return-policy-from-portal.png`.
3. **How to start one.** Product page, every product: *"**Start a return by email:
   crooksldn@gmail.com.**"* Terms c3: *"**Start your return here: the returns centre.** It takes
   your order number and email, and issues the return so we can match the parcel to you."* FAQ
   q9: *"Start your return here."* Contact-information policy: *"**Start it by emailing**
   Crooksldn@gmail.com."* A return started the way the product page says arrives unmatched, by
   the Terms' own explanation.
4. **Damage: 48 hours or 14 days.** Terms c5 and FAQ q11: *"For transit damage, tell us **within
   48 hours** of delivery."* Refund policy and Shipping policy: *"Message us **within 14 days**."*
   A shopper reporting damage on day 3 has either complied or missed the deadline depending which
   page they read.
5. **Lost parcel: replacement now, or nothing yet.** Shipping policy: *"Message us within 14 days
   and we'll chase the courier **or send a replacement or refund**."* Terms c7: *"**We cannot
   refund or replace before that investigation closes**"* — up to 10 working days.
6. **Size swaps: free, or free only in the UK.** Terms c4 and FAQ q8 state the swap is free with
   **no geography named**; the Refund policy says *"no fee for a **UK** size swap itself"*. An
   international shopper reading the Terms believes their outbound swap postage is covered.
7. **The returns centre asks for more than the FAQ says.** FAQ q9 and Terms c3: *"It takes your
   order number and email."* The portal: `ORDER NUMBER / EMAIL / VERIFY BY POSTAL CODE OR PHONE
   NUMBER / FIND YOUR ORDER`.
8. **One address, four spellings, none of them CROOKSLDN.** Terms c3: *"Oairo UK Office, Bourne
   End Business Park, Bourne End, Buckinghamshire, SL8 5AS, United Kingdom"*. Refund policy:
   *"Oairo Uk Office, Bourne end Business Park… United Kingdom, SL8 5AS"*. Terms of service:
   *"Unit M, Oairo Uk Office, Bourne End, SL8 5AS"*. Privacy policy: *"Unit M ,, SL8 5as, United
   Kingdom"* — double comma, lower-case postcode, no town. Journey 12's shopper put it plainly:
   she would be posting £60 of denim to a company called "Oairo" she had never heard of, at an
   address written half in capitals. That address ends up on a returns label.

### Group B — Shipping: what it costs, and when it leaves

9. **Is there a price before checkout?** FAQ q3 and Terms c1: *"Below £20 it is calculated at
   checkout before you pay."* Shipping policy: *"Under that: **standard £3, Tracked 24 £4.99**."*
   Two pages say the price cannot be known in advance; a third prints it. Reached from the same
   product page footer, two rows apart.
10. **One tier or two.** Status bar, every page: `FREE UK SHIPPING OVER £20 — ORDER BY 18:00 FOR
    SAME-DAY DISPATCH`. The real card is two tiers — free Tracked 48 over £20, free Tracked 24
    over £70. The chrome states the cheaper half as though it were the whole offer, and the £70
    tier is invisible until you have already spent £20.
11. **A UK threshold promised to every country.** The status bar is not gated by country and
    shows every shopper in the world the £20 line. The live rate card: EU `Standard international
    £12.99`, no free tier; International including the US `£18.99`, no free tier; Channel Islands
    `Tracked 48 £3.99` / `Tracked 24 £7.00`, **no free tier at any basket value, ever** — served
    by a dedicated market that shows GBP prices and the same status line. The carriage bar
    correctly hides itself outside GB; the sentence above it does not. An overseas shopper builds
    a basket believing shipping is free over £20 and meets £12.99 or £18.99 at checkout.
12. **Same-day, or same-day where possible.** Ticker: `ORDER BY 18:00 FOR SAME-DAY DISPATCH`, no
    days named — so a shopper ordering at 17:00 on a Sunday expects it to leave that day. Product
    page: `Order before 18:00 and it ships today (Mon–Sat)`. Terms c2 and FAQ q1: *"dispatched the
    same day **where possible** … After a drop, **allow up to two working days**."* The
    unconditional version is the one shown at the moment of purchase.
13. **Settled, or not settled.** Cart carriage bar: `Free Tracked 24 — unlocked`. Cart summary,
    four lines below: `Duties and taxes included. Shipping is calculated at checkout.`

### Group C — Sizing: two methods, and two garments sharing one table

14. **Around the garment, or laid flat.** Product page, printed directly above every measurements
    table: `TRUE TO SIZE — WAIST, CHEST AND LEG MEASUREMENTS ARE TAKEN AROUND THE GARMENT.`
    `QUESTIONS`, reached from that same page's footer: *"**Everything is measured with the garment
    laid flat**, and you can switch the table between centimetres and inches."* Those differ by a
    factor of two. A shopper who lays their own jeans flat, measures 43cm across the waistband and
    compares it with `86.4cm` on the M row concludes the M is twice their size and buys down.
    **Note for whoever fixes it:** `SPEC.md §3.5` states the method as `GARMENT LAID FLAT`, so the
    spec and the FAQ agree and the product-page caption is the outlier. This is the one thing in
    the audit that can make a shopper order the wrong size *by following the site's own
    instructions*. `audit/screens/pdp-sizing-jeans-measurements-open.png` and
    `audit/screens/pdp-sizing-faq-sizing-onscreen.png`.
15. **The caption names columns the table does not have.** On the jeans the columns are
    `WAIST / INSEAM / LEG OPENING` and the line explains "chest". On the crewneck the columns are
    `CHEST / LENGTH / SHOULDER / SLEEVE` and the line explains "waist" and "leg", and says nothing
    about how shoulder, sleeve or length were taken — precisely the three people measure wrong.
16. **Opposite garments, identical numbers.** `V2 BAGGIES`, described on its own page as *"wide,
    full-length sweats in 500gsm cotton, heavy enough to hang straight"*, against `GREY WASH OG
    JEANS`, *"14oz denim, OG straight cut, mid rise. Structured, not baggy."* Same waist, same
    inseam, same leg opening at all five sizes. (Placeholder measurements — known item, impact
    only.) `TRUE TO SIZE` is a fit claim, not a method, and it cannot be true of both.

### Group D — Tracking: a lookup promised and refused

17. FAQ q5: *"**You can also look your order up on the tracking page — no account needed.**"*
    `/pages/tracking`, in full: `IDENTIFICATION REQUIRED` / *"Sign in to view the chain of custody
    for your orders."* / `SIGN IN` — and not one field on the page. FAQ q13 compounds it:
    *"You can check out as a guest and still track your order."*
18. Search offers `TRACK YOUR ORDER` to **everyone before they have typed anything**, and it
    lands on that wall.

### Group E — The set: what the page promises against what the cart charges

19. Cart: `Complete the set — add the Cellblock Shorts, save £10.` → following it, doing the
    obvious thing: `Estimated total £95.00 GBP`, no discount, no mention of the set.
20. Panel, in red: `Cellblock Shorts sold out in M — pick another size` → the same page's
    `MORE FROM THIS DROP` row shows `CHARCOAL CELLBLOCK SHORTS £45.00`, and the shorts page sells
    M perfectly happily.
21. Sticky bar: `CHARCOAL CELLBLOCK CREWNECK` / `£50.00 · M` → the button beside it in the same
    bar: `ADD THE FULL FIT — £85`, for two garments in sizes M and L.
22. Panel prices `£95` and `£85` → `£50.00` on the same screen and `£85.00` in the cart it leads
    to. The set panel is the only place in the shop that drops the pence.
23. `SPEC.md §5`: ticking reveals "**live partner stock**" → an empty stock line for every
    buyable pairing, including the 4-unit ones.
24. `SPEC.md §3.13`: "the bundle in the cart → **the saving confirmed in words**" → no such
    section on the cart page at all.
25. Product page: `£85 for the set` / `Save £10.` / `ADD THE FULL FIT — £85` → cart with
    `10CROOKS`: `Estimated total £76.50 GBP` (**O1**). The saving against buying the parts
    separately becomes £18.50, not the £10 the page states.

### Group F — The register against the goods

26. **`ON MODEL` against the products themselves** — twelve cards, one photograph of a man in
    charcoal shorts (§2.3).
27. **The pictures against the garments** — the cream keyline draws trim on garments that do not
    have it, in the default state, all the way through to the product page (**O3**).
28. **Two case numbers for one product.** `GREY WASH JORTS` is `NO. 06` on the homepage register
    and `NO. 01` on `/collections/denim`. In a register that presents itself as an evidence log,
    the case number moves.
29. **A heading that does not match its own count.** Filtering `/collections/all` to denim leaves
    the heading reading `ALL` while the count beside it reads `4 ITEMS` and only denim is on
    screen.
30. **Two spellings of the same two colours, eight cards apart.** `Colourways: BLACK, WHITE` on
    `NO. 07 MONEY CLIVE TEE` against `Colourways: Black, White` on `NO. 08 CRXST★RZ T-SHIRT`.
    Only a screen-reader shopper meets it, since the text is not shown on the card.
31. **A swatch that is not a control.** Two 12×12px chips sit under two product names, looking
    exactly like the colour chips a shopper taps everywhere else on the web. Tapping the white
    chip on `MONEY CLIVE TEE` opens the product with no colour chosen, presenting the tee in
    black. Evidence: `audit/screens/catalogue-D01b-after-swatch-tap.png`.
32. **`12 PRODUCTS CURRENTLY ONLINE` against 13 published products.** The thirteenth is
    `CELLBLOCK SET` at `£85.00`, with a live page a shopper can reach and buy from, appearing in
    no register and carrying no `PRODUCT n / N` line. Nothing on screen contradicts itself — but
    "currently online" is not literally true. Evidence: `audit/screens/status-bar-x-set-pdp.png`.

### Group G — Search says two things at once

33. Placeholder `Item, category or question` against the hint 40px below,
    `SEARCH BY ITEM, CATEGORY OR COLOUR`. One invites questions and omits colour; the other
    invites colour and omits questions — and questions are the feature's reason to exist.
34. `SEARCH BY ITEM, CATEGORY OR COLOUR` against searching `black`, whose first three results are
    `GREY WASH OG JEANS`, `V2 BAGGIES` and `GREY WASH JORTS`. The only product with `BLACK` in its
    name is sixth. The typeahead for the same word gets it right, so the shopper sees the right
    answer while typing and the wrong order after pressing SEARCH.
35. `SIZE GUIDE` — search's promise — against the destination's own answer: *"tap SIZE GUIDE next
    to the size buttons."* A link labelled `SIZE GUIDE` lands on a page that says the size guide
    is somewhere else.
36. `0 RESULTS` / `NO ITEMS IN THE REGISTER MATCH THAT QUERY.` printed on the same screen as
    `DIRECT LINKS / TERMS` and `PAGES & ANSWERS / TERMS` (§2.6).
37. **Two different returns processes, one word apart.** `returns` → the third-party portal;
    `refund` → the shop's own policy page.

### Group H — The cart against its own header

38. Header `BAG [2]` against, on the same screen at the same moment, `Your cart is empty`.
39. `Discount code cannot be applied to your cart` — for a code that does not exist at all. The
    wording blames the cart.

### Group I — Sold out against leaves today

40. `SIZE M IS SOLD OUT` in red, with `Order before 18:00 and it ships today (Mon–Sat)` and
    `> Ordered now — leaves today` directly above it (§2.11).

### Group J — The store's own rules against what it shows

41. **The overlay sells the urgency the store bans everywhere else.** Eight seconds into a first
    visit, CROOKSLDN says `Code expires in 20 minutes.` and `(this drop closes 15.09)` — a
    countdown and a deadline — in a store that has deliberately refused countdown timers, stock
    counters and manufactured scarcity on every other surface. The shopper cannot tell that one
    of these is a third-party app and the rest is the theme; they see one shop saying two things.
42. **Two build numbers, one tap apart.** Shop footer `EVIDENCE TERMINAL V0.2`; the CASE 001 game
    it links to, `EVIDENCE TERMINAL v0.1 // CROOKS UK` (**O4**).
43. **Two names for one box.** The field is labelled `NUMBA`; the error under it reads
    `Phone number is required`. The name in the error is not on screen.
44. **Two names for one item.** The manifest says `03  CUFF KEYRING *`; the footnote calls the
    same thing `CONTRABAND 03`, and says it ships with `SWEAT BOTTOMS`, which is not the name of
    anything the shop sells.
45. **Three names for one page.** The menu word `SHOP`, the address `/collections/frontpage`, and
    the heading you land on, `PRODUCTS` — sitting directly above a second link, `ALL`, to the same
    twelve products.
46. **A count reserved so it "never reflows the row"** — and at `[103]` it does, widening `BAG`
    by 12px and moving `MENU` out of the top-right corner onto a new line 48px lower. Holds
    perfectly to 99: 0 → 1 → 9 moves nothing by a single pixel. Evidence:
    `audit/screens/hdr-d18-bag-103.png`.
47. **A theme switch on two pages it cannot switch.** `LIGHT MODE` appears in the header of the
    404 and `/pages/contact`; pressing it changes nothing below the header (§2.20).
48. **`TRACKSUITS` reads `1 ITEMS`.**
49. **Spec against page: the accordions and the sticky bar.** `SPEC.md §3.5` says four
    `<details name>` panels, mutually exclusive; the product page has four buttons that all stay
    open. The same section says the sticky bar shows "only while the primary control is
    off-screen"; it is on screen at every position tested, including three where the primary
    control was plainly visible. (See §2.29 — the FAQ *does* behave as the spec describes.)
50. **Spec against page: the notify panel's own words.** `SPEC.md §3.5` describes the sold-out
    capture as `RELEASED — NO LONGER IN CUSTODY`; the panel on screen reads `TELL ME WHEN THIS
    SIZE IS BACK`. The page's version is the plainer one and is the right call under §9.2 — worth
    correcting the spec rather than the page.

---

## 5. What works and is load-bearing

These are the things a fix pass must not sand off. Each one earns protection for a stated
reason, not because it is nice.

- **The status slot on every card.** Twelve of twelve state stock in plain English —
  `AVAILABLE`, and `2 OF 5 SIZES LEFT` on `V2 BAGGIES`, which tells a shopper the truth *before*
  they click. `NO. 08` carries `DROPPED 03.08` on its own line 3px under `AVAILABLE`, in a
  quieter grey — plainly an addition, never a replacement, never a badge. **Why it is
  load-bearing:** this is the one thing in the register that a conventional shop would replace
  with a scarcity badge, and it is doing the work of one without lying.
- **The chain-of-custody copy, all four steps.** *"Orders placed before 18:00 are dispatched the
  same day, Monday to Saturday"* … *"Free UK shipping over £20, and free Tracked 24 over £70"* …
  *"Tracking issued by email. UK 1–2 working days"* … *"You have 14 days from delivery to return
  unworn goods with tags attached. Return postage is yours unless we sent the wrong thing or it
  arrived faulty."* **Why:** it is the only place on the product page the return window is
  mentioned at all, it names a real courier and a real return route, and it is unhedged. Any
  softening pass would turn the best paragraph on the site into boilerplate.
- **Return-postage honesty, stated four times without a euphemism.** Terms, FAQ, product page and
  refund policy all say the shopper pays return postage unless the fault is the store's. **Why:**
  it is the least flattering fact on the site and it is never hidden. On a brand with no reviews
  this is what "trustworthy" actually looks like.
- **Plain-English buy controls (§9.2).** `£60.00`, `SIZE`, `XS S M L XL`, `IN STOCK`,
  `SELECT A SIZE`, `ADD TO BAG`, `SOLD OUT`, `> Added — 1 in bag  View bag`. Not one word of
  fiction in the part of the page that takes money. **Why:** this is the rule that lets the
  aesthetic survive contact with a stranger, and it holds under pressure everywhere it was tested.
- **The sold-out size behaviour (§9.3).** Dashed border, struck-through label, still tappable by a
  real thumb, red `SIZE M IS SOLD OUT`, button swaps to `SOLD OUT`, notify panel appears, and the
  sticky bar's `CHECKOUT NOW` beside it is greyed and genuinely inert — it reads as dead, not as a
  trap. **Why:** better than most shops manage, and the two problems around it (the dispatch line
  and the clipped button) are faults *on top of* it, not faults in it.
- **Deep-linkable sizes.** Every size tap writes `?variant=`, and pasting that address into a
  fresh page comes back with the size selected, `IN STOCK`, and `ADD TO BAG` live. **Why:** it is
  what makes a size shareable in a DM, which is how this brand's traffic moves.
- **`SIZE GUIDE`.** One tap, no modal, no PDF; the `MEASUREMENTS` heading lands at the top of the
  screen with the panel already open and the first number 237px below it, on all three products
  tested, animated so the eye is carried down rather than teleported. **Why:** it is the
  best-behaved control on the product page — and it is a *better* route to the table than tapping
  the accordion, which on a first visit opens it underneath the cookie sheet.
- **The cm / inch toggle.** Correct in both directions on every cell checked (`76.2cm` → `30in`,
  `86.4` → `34`, `55.9` → `22`), both button states shown, and the caption's unit word rewrites
  with the table. **Why:** the shopper is never left guessing which unit they are reading — which
  matters more here than usual, because the numbers themselves are under suspicion.
- **The gallery's keyboard and touch handling.** Thumbnails are proper buttons labelled
  `Photo 1 of 3` / `Photo 2 of 3` / `Photo 3 of 3` and are the **first three stops in the tab
  order on the page**; arrow keys walk the focused group and stop cleanly at both ends rather than
  wrapping; a real phone swipe moves it and the active thumbnail follows; targets are 64×64.
  **Why:** the component is markedly better than the pictures inside it, so a photography fix must
  not come with a component rewrite.
- **`PHOTO 1 OF n`.** It tells the truth, including when the truth is `1 OF 1`. **Why:** honest,
  if bleak — and it is the only thing telling a shopper there is nothing more to see.
- **The dispatch line as a live readout, not a countdown.** Correct at 17:38 on a Thursday,
  computed against the shop's own timezone rather than baked into a cached page, so it will not go
  stale at 18:01. **Why:** it is the exact place where a normal shop would put a ticking clock, and
  it doesn't.
- **Low stock stated as a number, not a scare.** `3 LEFT IN SIZE XL`, in the same quiet grey as
  neutral text rather than the red used for sold out. **Why:** real inventory, no escalation —
  §9.7 holding in the hardest place to hold it.
- **The carriage bar's empty-cart gate.** With an empty bag the section does not appear at all, on
  any of its five surfaces. **Why:** it is the reason this feature is defensible. The quarter-screen
  it costs is charged only to shoppers who already have something in the bag, which answers the
  "homepage, empty cart" objection in advance. Do **not** "fix" it by adding an empty state.
- **The carriage bar's GB gate, and thresholds that match the real rate card.** £20 and £70 are
  live rates in the delivery profile, verified. **Why:** it is the one component in the build that
  refuses to make a shipping promise it cannot keep — every other surface makes that promise to
  every country. Also protect the fill being measured against the *top* tier (so the bar keeps
  moving past £20) and held at 99% until a tier is genuinely met, so a shopper never sees a full
  bar next to `£0.01 to go`.
- **`£14.00 to free Tracked 48`.** A real number and a real Royal Mail service, inside the
  fiction, with no countdown and no "only £14 away!!". **Why:** this is §0 holding under commercial
  pressure and it should stay exactly as it is.
- **The carriage bar's live rewrite on the cart.** `£10.00 to free Tracked 24` → `Free Tracked 24
  — unlocked` within a second and a half of pressing `+`, and it matched the real rates at
  checkout. **Why:** the one surface where the message is immediately actionable is the one where
  it actually moves.
- **Filters, counts, and the address bar.** All five categories narrow correctly, the count above
  follows, the choice is written into the address (`?cat=DENIM`), a cold load of that address
  reproduces the filtered view with `> DENIM` already lit, and the whole thing survives opening a
  product and pressing Back. **Why:** a filtered link can be shared and bookmarked, which almost
  no small store gets right.
- **The active-state styling.** A filled purple block with a `>` prompt in front of the word.
  **Why:** nobody will wonder which category is on. No squinting, no faint underline.
- **The whole card is one link.** Picture, title and price all open the product, with 152px-wide
  targets. **Why:** forgiving on a phone, and the price is a target rather than decoration.
- **`Outline` persistence.** Turn it off once and it stays off across collections, product pages
  and Back, for the whole shopping trip. **Why:** whatever is decided about O3, the persistence
  itself is correct behaviour and should survive the decision.
- **One `h1` per collection page**, large, first thing, matching the collection.
- **The empty-search stand-down (§9.8).** A blank query gives a placeholder, a `SEARCH` button,
  the hint, and three real destinations under `DIRECT LINKS`. **Why:** it reads as a landing page
  rather than a failure, and journey 12's shopper — who was braced for a blank grid — said so.
  Do not replace it with a "no results" message or a product grid. (The *failed*-search page
  needing the same three links is a separate fix, §2.7.)
- **The curated direct links themselves.** Twelve question-shaped queries, twelve correct
  destinations, **zero wrong matches**, two taps each. **Why:** this is the feature's entire
  justification and the matching meets it. Every problem in search is about what happens *after*
  the link, not about the matching — so a rework would be throwing away the part that works.
- **The typeahead's two-group order.** `PAGES` above `ITEMS` — answers ranked above garments.
  **Why:** a shopper asking a question sees the answer before the merchandise, which is the
  correct priority and the opposite of what most stores do.
- **Prices in the suggestions.** `V2 BAGGIES £60`, `CHARCOAL CELLBLOCK SHORTS £45`. **Why:** plain
  English money in a fiction-heavy theme, and journey 12's shopper named it unprompted as a reason
  she would come back.
- **The search field itself.** 56px tall, full width, autofocused on arrival so the keyboard is
  already up, visible without scrolling, with a labelled `SEARCH` button and a working Enter key.
  And the header carries the word `SEARCH` written out, next to `CATALOGUE` — not an icon, not
  inside a hamburger. **Why:** journey 12's best moment. One tap saved and four seconds of
  not-thinking, on the device where both are scarce.
- **Fuzzy matching on product names.** `jeens`, `bagies`, `clve tee`, `blue wash og jeens` all
  land on the right garment.
- **The set's cart line.** `CELLBLOCK SET` / `CHARCOAL CELLBLOCK CREWNECK - M` /
  `CHARCOAL CELLBLOCK SHORTS - L` / `£85.00`, one line item, `item_count: 1`. **Why:** the hardest
  part of a bundle to get right, and it is right from both directions — shorts S + crewneck XL
  from the shorts page produced the bundle's `XL / S` with the sizes on the correct garments. Do
  not let a cart redesign flatten those component lines into `M / L`.
- **The partner size row is headed with the partner's name** — `CELLBLOCK SHORTS SIZE`, and
  `CELLBLOCK CREWNECK SIZE` in reverse. **Why:** one decision that removes the commonest bundle
  confusion outright; you are never in doubt whose size you are picking.
- **`£95` struck, `£85 for the set`.** **Why:** the arithmetic is done for the shopper and the
  words "for the set" say what the £85 buys. It is the one screen where the whole proposition is
  stated properly — which is also why its absence from the cart hurts.
- **Untick restores everything** — button, price line, the shopper's own size still selected and
  still pressed, sticky bar, and the underlying selection. **Why:** a shopper can look at the
  offer without committing to it.
- **On the shorts side the button itself becomes the instruction** — `Pick a Cellblock Crewneck
  size`, disabled. **Why:** it is exactly the pattern the crewneck side needs (§2.2), so it is
  both good and the fix.
- **No modal, no popup, no countdown, no "customers also bought" in the set offer.** One quiet
  collapsed line. **Why:** the restraint is the reason the offer is credible at all.
- **The CASE 001 board.** Loaded only on first drawer open, then animating at 61fps — ten
  different frames sampled over four seconds, a thief on a fixed route, a helmeted officer in
  hi-vis, gold `£` coins, brickwork and barred windows. **Why:** the best-crafted thing in the
  build, and its three pause guards (§9.1) never get in a shopper's way. Its problem is
  discoverability, not the board.
- **`PLAY CASE:001 NOW` opening in a new tab.** **Why:** the only reason the game does not strand
  people — the shop tab stays exactly where it was, drawer still open.
- **Escape and focus return.** Escape closes the drawer and puts a clearly visible lavender ring
  back on `MENU`. **Why:** the one dismissal that works reliably, and the focus return is the part
  most rebuilds lose.
- **The bag count's reserved slot and tabular figures.** 0 → 1 → 9 moves nothing by a single pixel.
  **Why:** it was deliberately built and it works; it needs widening by one character, not
  replacing.
- **The text `MENU` trigger instead of a hamburger**, hidden until it is upgraded so it is never a
  dead control.
- **The drawer's link set.** All fourteen destinations resolve, every collection has products in
  it, nothing 404s.
- **`ADD TO BAG` staying on the page.** The count moves `[0]` → `[1]`, a line appears reading
  `> Added — 1 in bag  View bag`, and both revert four seconds later. No drawer, no modal, no
  interception. **Why:** the shopper stays on the product they were deciding about.
- **The cart arithmetic.** £45 + £50 + £60 = `£155.00`, with line totals, `Cart total` and
  `Estimated total` all agreeing, before and after a discount.
- **The discount mechanism.** Apply, a removable `10CROOKS ×` pill, and a
  `Subtotal` / `−£15.50` / `Estimated total` breakdown in the site's own type.
- **Back from checkout returns an intact cart** in one press — three lines, correct total, correct
  count, carriage bar still `Free Tracked 24 — unlocked`. And the cart survives a return in the
  same browser while a genuinely new session correctly starts empty.
- **The bin's accessible name** — `Remove GREY WASH OG JEANS - XS` — names the size as well as the
  product.
- **The FAQ's writing.** Fourteen answers with actual numbers in them — £20, £70, 18:00, 1–2 days,
  7–14 days, 5–7 days, 48 hours, 10 working days. **Why:** it refuses to hide behind "please
  contact us", which on a brand with no reviews is worth more than a reviews widget. Its
  accordions also behave exactly as the spec describes — one open at a time.
- **The Terms page as a whole.** Nine plain-English clauses, a working clause index (tapping
  `03 RETURNS` puts that clause at the top of the screen), a `LAST REVISED 20.08.2026` date, a real
  returns address, a working `#returns` deep link, and links out to all four legal texts.
  **Why:** better than what most stores this size have, and the deep link is what makes the FAQ's
  "full detail is on the terms page" real.
- **`"Drops are for people, not scripts."`** (Terms c8) — flavour in the clause about cancelling
  bot orders, not in the clause about refunds. **Why:** it shows the fiction knows where it is
  allowed to speak.
- **The policy pages carrying the full skin.** Header, status bar, the same display face at the
  same size as the FAQ, the same body type and ground, full footer. **Why:** the seam where most
  themes give the game away is invisible here — a shopper cannot tell these pages are a different
  system.
- **The 404 keeps the header, the footer and four buyable products with prices.** Nobody gets
  stranded; only the look is wrong (§2.20).
- **The tracking page's honesty.** It does not pretend. If the FAQ's promise is removed or the
  page gains a real lookup, keep the plain `IDENTIFICATION REQUIRED` / `Sign in` framing and the
  dispatch-email line — just make that line legible.
- **The packaging section.** `EVERY ORDER SHIPS LIKE THIS`, a real photograph whose yellow
  evidence tents numbered 1, 2, 3 map one-to-one onto the numbered manifest so the list and the
  picture teach each other with no caption, and the line **`Nothing here is an extra you pay
  for.`** **Why:** that single sentence turns three props into three free things you get, and it
  is the only argument-to-buy anywhere on the homepage.
- **The first product at 0.90 screenfuls.** `NO. 01` and `NO. 02` card headers are in the first
  screenful. **Why:** an unusually short run-up for a fashion homepage and the right decision — the
  thing costing the shopper that screen is the three stacked control rows and the cookie sheet, not
  the ordering.
- **The boot line typing.** Readable at ~1.5s, no blank-screen wait, and `> 12 PRODUCTS AVAILABLE
  TO PURCHASE` is a real count.
- **The intake's own copy.** `Drops go to the register before they go public. One message per
  drop, nothing else.` and `One text per drop. Reply STOP to leave the register at any time. We do
  not sell it.` **Why:** more honest than most SMS signups. It deserves a form that works
  underneath it.
- **The status bar's hover pause.** Held for 26 seconds under the pointer — three rotations' worth
  — and resumed within nine of leaving. **Why:** rare, correct, and easy to lose in a refactor.
- **Reduced motion parks on message 1** — the shipping line, not the count. **Why:** that ordering
  is load-bearing: anything placed in slot 2 is permanently invisible to that audience, so the
  useful message must stay first.
- **`[count]` is honest.** 12 in the ticker, 12 in the register, 12 in the hero, `/ 12` in every
  product footer. No inflation, no "17 people viewing".
- **No fake urgency anywhere in the theme (§9.7).** No counters, no timers, no invented scarcity —
  `2 OF 5 SIZES LEFT` and `3 LEFT IN SIZE XL` are real inventory. **Why:** the only surface that
  breaks this is the third-party overlay, which is the exception that proves how consistently the
  theme holds the line.
- **The theme switch.** Instant, no reload, no flash of the wrong theme, and the label states the
  destination rather than the current state.
- **Reload, Back/Forward through five pages, and cold-landing on a product URL** all come back
  clean with the bag count honest at every step; two tabs reconcile exactly on reload, carriage
  line included.

---

## 6. The full feature table

`works` · `partly` · `broken` · `absent`. Every feature touched, including the ones that were
fine.

### Homepage

| feature | should | did | verdict |
|---|---|---|---|
| Cold arrival | Page readable quickly | Boot line mid-type at 0.7s, complete and readable at ~1.5s, no blank-screen wait | works |
| Hero — boot line, wordmark, tagline | Typed boot line, live count | One line, `> 12 PRODUCTS AVAILABLE TO PURCHASE`, count real; `CROOKSLDN` is the page's h1 | works |
| Hero — buttons | Up to two | One, `CATALOGUE`, an in-page jump to a heading already on the same screen | partly |
| Packaging section | Photo + numbered manifest | Both, tents matching the manifest, `Nothing here is an extra you pay for.` | works |
| Packaging footnote | A per-item footnote | Mechanism works; `CONTRABAND 03` and `SWEAT BOTTOMS` name nothing on the site | partly |
| Informant intake — copy | Say what you're signing up for | Honest and clear: one text per drop, STOP to leave, not sold on | works |
| Informant intake — submission | Take a number, confirm it | Only two messages ever; junk and valid numbers both produce silence; no confirmation state | broken |
| Informant intake — house style | Radius 0, mono, no shadows | Shop-violet `Continue with Shop`, two white rounded boxes, blue focus ring, red sans-serif error | partly |
| Lookbook | — | Does not exist on the homepage | absent |
| Section order / first product | Land a shopper on the goods | First product at 0.90 screenfuls; zero whole cards before scrolling, three control rows in the way | partly |
| Cookie consent | Known item | Owns 43% of the landing screen, covers the first product row and the intake's button | (known) |
| `CRACK THE CUFFS.` overlay | — | Fires unprompted; lands on the packaging manifest or the intake | partly |

### Catalogue / register

| feature | should | did | verdict |
|---|---|---|---|
| Category filters | Narrow the register, active state obvious | All five correct, counts follow, `> DENIM` unmistakable, choice written into the address | works |
| Odd-count grid | Products and nothing else | A solid lavender slab the size of a card in the empty slot | broken |
| Three control rows | Tell view / treatment / category apart | `> FLAT`, `> OUTLINE`, `> ALL` all lit at once, one look, no labels | partly |
| Filter row on a phone | See every category | Cut at `SW`; `ACCESSORIES` off-screen with nothing saying the row scrolls | partly |
| `Flat` / `On model` | Show the product worn | All twelve swap to one photo of a different garment | broken |
| `Outline` (**O3**) | Help black products read | Draws cream trim on garments that lack it, on by default, inert in light mode | partly |
| `Outline` control placement | Changeable where it applies | Homepage only; the treatment applies on collections and product pages | partly |
| Filter → product → Back | Filter survives | It does, cleanly; scroll position does not | works |
| Outline persistence | The choice sticks | Survives collections, product pages, Back and a return home | works |
| Card status slot | Always states stock | Twelve of twelve; `DROPPED 03.08` an addition, never a replacement | works |
| Sold-out card state | Obvious before clicking | Nothing in the catalogue is currently sold out | untested |
| Colourway swatches | Tapping a colour does something with it | Opens the product with no colour chosen | partly |
| Image / title / price targets | All three open the product | All three do; 152px targets | works |
| Collection heading | A real heading and orientation | `<h1>DENIM</h1>` + `4 ITEMS`, then straight into cards; the written description is never shown | partly |
| Products before scrolling | Land on the goods | Homepage 0, `/collections/all` 2, `/collections/denim` 2 | partly |

### Product page — core

| feature | should | did | verdict |
|---|---|---|---|
| Gallery — count and detail | Enough photos to decide | Seven of twelve have one; no zoom of any kind on either device | partly |
| Gallery — moving between photos | Thumbnails, swipe, arrow keys | All three, cleanly, stopping at both ends; thumbnails first in the tab order | works |
| Size selection | Settle the buy state, be shareable | Stock line changes, address updates on every tap, deep link reopens with the size selected | works |
| Sold-out size | Selectable, swaps to notify | Exactly that — but the dispatch line does not stand down and the bar clips `NOTIFY ME` | partly |
| Notify form | Take an address, say thank you | Could not be completed; see §7 | untested |
| Buy button with no size | Say what is missing | `SELECT A SIZE`, genuinely inert; a tap produces nothing at all | partly |
| Four accordions | Four `<details>`, mutually exclusive | Four buttons, all four open at once; contents real and per-product | partly |
| `SIZE GUIDE` + cm/in | One tap, no modal | Heading to the top with the panel open; conversion correct both ways | works |
| Low stock | True without inventing | `3 LEFT IN SIZE XL` in neutral grey; the 4px mark that precedes it has no legend | partly |
| Chain of custody | Plain English after the money | Four specific, unhedged steps naming a real courier and return route | works |
| Dispatch line | Live and true | Correct at 17:38 Thursday, computed in the shop's timezone, no countdown | works |
| Sticky bottom bar | Only while the buy control is off-screen | On screen at every position tested; carries the size correctly | partly |
| `MORE FROM THIS DROP` | Related, never itself | Zero self-links on all twelve; absent entirely on the two t-shirts | partly |
| `ADD TO BAG` happy path | Add it, say so | `[0]` → `[1]`, `> Added — 1 in bag  View bag`, no interception | works |
| Consent banner on a product page | Not stand between shopper and price | Covers title, price, size row and both buy buttons on a first mobile visit | (known) |

### Product page — sizing

| feature | should | did | verdict |
|---|---|---|---|
| Finding the measurements | Quick, and you know you got there | One swipe, one tap, ~2s — but on a first visit it opens under the cookie sheet | works |
| cm / inch toggle | Convert and label correctly | Correct on every cell on three products; caption's unit word follows | works |
| Measuring method stated | So a shopper can compare | One line on every product, naming columns those tables do not have, and contradicting the FAQ | partly |
| Do the numbers read as real | The last thing before a £60 guess | Two garments the shop calls opposites share a table to the millimetre (known item) | partly |
| `SIZE GUIDE` | One tap, heading to the top | Exactly that on all three products; better than tapping the accordion | works |
| Four-column table on a phone | All four readable | `SLEEVE` sliced mid-character with nothing saying it drags sideways | partly |
| Shipping cost from the product page | Findable before committing | Two thresholds on the page, the real prices two taps away on a policy page | partly |
| Returns from the product page | Findable, same story everywhere | One swipe, one tap to the whole of it; product page, policy and FAQ agree | works |

### Complete-the-set

| feature | should | did | verdict |
|---|---|---|---|
| Collapsed line | One line, what you get and save | `Cop the full fit — add the matching Cellblock Shorts. Save £10.`; never states £85 or £45 | partly |
| Ticking — partner size row | Reveal size row, stock, was/now, relabel | Row appears headed with the partner's name; arithmetic correct | works |
| Button relabel | `ADD THE FULL FIT — £85.00` | `ADD THE FULL FIT — £85` — the only place in the shop dropping pence | partly |
| Live partner stock | Show it | Blank for every buyable pairing, including 4-unit ones | partly |
| Tick before choosing your own size | Wait, or ask | `Cellblock Shorts sold out in <SIZE> — pick another size`, all five sizes, all false | broken |
| Sticky bar with the set on | Repeat the right price and sizes | `£50.00 · M` beside a button charging £85; name clipped to `CH…` on a phone | partly |
| Unticking | Restore what was there | Everything restored, including the shopper's own size | works |
| One line at £85 in the cart | One add, one line | Exactly that, both garments named with their own sizes | works |
| Set section on `/cart` with the set in it | Saving confirmed in words | Nothing appears | absent |
| One half in the cart | Offer the other | `Complete the set — add the Cellblock Shorts, save £10.` appears and links correctly | works |
| Following that offer | End £10 cheaper | `Estimated total £95.00 GBP`, no discount, no mention of the set | broken |
| The shorts side | Mirror behaviour | Mirrors it, and better — the button becomes `Pick a Cellblock Crewneck size` | works |
| The bundle's own page | — | Public and reachable; bare `SIZE` row, crewneck-only image, no measurements, in no menu | partly |
| Partner measurements from the panel | — | Not reachable; the thumbnail is not a link | partly |
| Desktop | Same | Identical at 1440×900 | works |

### Cart and checkout

| feature | should | did | verdict |
|---|---|---|---|
| The cart page's voice | Sound like the shop | Frame holds; `Cart`, `Discount`, `Estimated total`, `Check out` are Shopify's sentence case | partly |
| Quantity up / down | Money follows | Line total, cart total and the carriage bar all move within ~1.5s | works |
| Header `BAG [n]` after a cart change | Agree with the cart below it | Never moves until a reload; `BAG [2]` over `Your cart is empty` | broken |
| Quantity to zero | Work, or say why not | Silently rewritten to `1`; `−` disabled at 1; nothing says the bin is the only route | absent |
| Removing an item | Remove it; ideally offer undo | Removal works, fast and quiet; no undo, no message, no toast | works / undo absent |
| Three-item total | Add up | £45 + £50 + £60 = `£155.00`, every row agreeing | works |
| Shipping cost before checkout | Knowable | Free thresholds and progress only; no estimator, no price, no country selector | partly |
| Discount field | Findable, behaves | Clean apply, removable pill, correct breakdown | works |
| `10CROOKS` on the £85 set (**O1**) | Not undercut the page's promise | `£76.50` — the set's pricing story stops being true | partly |
| Fake code | Say it is not real | `Discount code cannot be applied to your cart`, and the field is wiped | partly |
| Checkout handover | Not feel like a different company | Functionally fine, rates match the cart's promise; the terminal ends entirely at that click | works / brand ends |
| Back from checkout | Cart still there | All three lines, correct total, correct count, in one press | works |
| Returning later / new session | Keep the bag; strangers don't inherit one | Both correct; the discount code persists across visits | works |
| Empty cart page | Look like the same website | Chrome correct; the middle is Shopify's stock empty state in sentence case | partly |

### Carriage progress bar

| feature | should | did | verdict |
|---|---|---|---|
| Empty cart | — | Does not appear at all on any surface | works |
| Two-tier wording | Move through both tiers | Wording and arithmetic correct; on-screen capture of the middle states not reached | works (partly untested) |
| Update after a product-page add | Move the moment you add | Does not; and on a first add there is nothing on the page to move. Untested on screen | partly |
| Position on the homepage | Earn its place | Suppressed on an empty cart, so the objection is already answered; marginal otherwise | partly |
| Position on a product page | Earn its place | Off screen at the moment of decision, silent at the moment of action | partly |
| Position on a collection page | Earn its place | The best of the four — a closeable gap beside a wall of prices | works |
| Position on a search page | Earn its place | Pushes the answer the shopper asked for down the page and adds nothing | partly |
| Non-GB shoppers | Do not chase a threshold that does not apply | The bar hides itself correctly; every other surface still promises the £20 line | works / broken around it |

### Search

| feature | should | did | verdict |
|---|---|---|---|
| Reaching search | Findable | `SEARCH` written as a word in the header, one tap, field first under the header | works |
| The query field | Visible, obvious, keyboard behaves | 358×56, autofocused, labelled `SEARCH` button, Enter submits | works |
| Empty-query stand-down (§9.8) | Not read as broken | Hint plus three real destinations before a key is pressed | works |
| Typeahead — products | Suggest as you type | From two characters, with thumbnails and correct GBP prices | works |
| Typeahead — mid-word blink | Narrow, not vanish | Closes completely at `den`, reopens at `deni`, every time | partly |
| Typeahead — fallback | Curated links survive a failure | Observed once returning nothing at all, including the locally-matched link | partly |
| Curated links — the critical test | Reach Terms, Questions, policies | Twelve queries, twelve correct destinations, zero wrong matches, two taps each | works |
| `returns` / `exchange` | Reach the policy | Only the third-party portal | partly |
| FAQ links | Land on the answer | Land at the top of a fourteen-question page with no anchor | partly |
| `TRACK YOUR ORDER` | Do what it says | A sign-in wall, offered to everyone before they type | partly |
| `0 RESULTS` under matched links | Not report success and failure at once | It does, on every answers query | partly |
| Empty results | Offer a way out | Nothing at all — less help than the blank page gives | broken |
| Misspellings | Still find the garment | `jeens`, `bagies`, `clve tee` all land | works |
| Category and colour words | As the hint promises | Category works; `black` returns three grey products first | partly |
| The field's two descriptions | One promise | Placeholder and hint disagree about questions and colour | partly |
| Desktop | Not mobile-only | 620px field, button beside it, identical suggestions | works |

### Header, drawer, CASE 001

| feature | should | did | verdict |
|---|---|---|---|
| Header contents | Logo, wordmark, nav, bag, menu | No wordmark ever appears; `ACCOUNT` is not in the header | partly |
| Header type | One treatment | 9px links beside 13px buttons in the same 44px row | broken |
| Opening the drawer | Modal, relabel, focus, lock | All four, correctly | works |
| Every drawer link | Land somewhere real | All fourteen resolve, nothing 404s; `SHOP`/`ALL` are the same twelve; `TRACKSUITS` reads `1 ITEMS` | works |
| Closing — `CLOSE` | Works | Closes, relabels, page unmoved | works |
| Closing — tap outside | Works | Impossible on a phone; works on desktop | absent (mobile) |
| Closing — Escape | Works | Closes and returns focus with a visible ring | works |
| Closing — Back | Close the drawer | Leaves the page; `about:blank` on a first visit | broken |
| CASE 001 board | Animated, loaded on first open | Exactly that, at 61fps, and it is excellent | works |
| `PLAY CASE:001 NOW` | Take you to the game | New tab, shop tab intact; no route back from the game | works / no way back |
| Board discoverability | Findable | Thirteenth in the drawer, below the fold, no heading, and behind the cookie sheet on a first visit | partly |
| `BAG [n]` stability | Never reflow the row | Holds to 99; at `[103]` `MENU` moves to a new line | works to 99 |
| `LIGHT MODE` | — | Works; the widest control in the row | works |

### Content pages

| feature | should | did | verdict |
|---|---|---|---|
| `/pages/faq` | 14 questions, 4 groups, closed | All present, exclusive accordions, numbers in every answer | works |
| FAQ coverage | Cover what stops a stranger buying | Eight real gaps, two of which cost a sale | partly |
| `/pages/terms` | Nine clauses, index, revision date | All nine, working index, `LAST REVISED 20.08.2026`, working deep link | works |
| `/pages/tracking` signed out | An honest signed-out state | Honest, well written, and a wall — zero fields on the page | partly |
| Signed-in tracking | Timeline + courier record | Not exercised — see §7 | untested |
| Policy pages | Look like the same site | Full skin; a shopper would not know they are a different system | works |
| `/policies/contact-information` | Findable | Best support copy on the store, linked from nowhere, promising a form it cannot show | partly |
| `/pages/contact` | Where a shopper gets help | A bare form with no email, address, phone or reply-time; does not look like the site | partly |
| 404 | Get a lost shopper back to shopping | Header, footer, four buyable products — and a cream body that looks like the failure | partly |
| Finding contact details cold | Reachable | Two taps to a contact page, zero taps to a contact detail | partly |
| The email address | One address, spelled the same | Consistent; one capitalisation variant, and plain text rather than tappable on policy pages | works |
| Cross-check across five surfaces | One story | Delivery times agree everywhere; everything else drifts (§4 A and B) | partly |

### Status bar

| feature | should | did | verdict |
|---|---|---|---|
| Rotation and cadence (**D1**) | Rotate between messages | 8s a line, 16s a loop, instant swap, nothing cut mid-read | works |
| `[count]` | Live product count | 12, agreeing with register, hero and every product footer | works |
| Pause on hover | Stop under the pointer | Held 26s, resumed within 9s of leaving | works |
| Reduced motion | Rotation disabled | Still for the full 25s watched, parked on the shipping line | works |
| With JavaScript off | First message shows | Both collide in a 28px strip; `ONLINE` sliced in half | partly |
| Legibility on a phone | One line | Message one wraps to two and the bar shaves the bottom | partly |
| What lands on top of it | — | The overlay dims it to near-invisibility and puts its close control on the bar | partly |
| Vertical cost | No damage | 28px; not what keeps product off the fold | works |

### Toggles and edge conditions

| feature | should | did | verdict |
|---|---|---|---|
| Light/dark control | Findable, works, visible change | Instant, no reload, label states the destination | works |
| Light/dark on every template | Every page honours it | All but two | partly |
| 404 and `/pages/contact` | Honour the theme | Cream in both themes; the switch silently does nothing | broken |
| `SEARCH` button in light mode | Visible | Cream on white, 1.38:1 | broken |
| Prose links in dark mode | As readable as the paragraph | 2.12:1 — the dimmest text in the answer | partly |
| Theme choice persistence | Pick light once, keep it | Survives navigation and reload; lost in a new tab and next session, while the bag carries over | partly |
| Flash of the wrong theme | None | None in light; the first frame is cream-to-white, not perceptible | works |
| Reloading main pages | Nothing lost | Identical to a shopper on all five | works |
| Back / Forward through five pages | Trail works, bag honest | Every step correct, count stable | works |
| Cold landing on a product URL | Stand on its own | Complete page, size selection and add both worked | works |
| Two tabs | Agree after a reload | They do, carriage line included | works |

---

## 7. Untested, and why

Listed honestly. None of these is a pass.

- **Signed-in tracking — the timeline, the courier record, the track button and the custody log.**
  No test login was supplied; the field arrived as the literal placeholder
  `<PASTE-OR-LEAVE-BLANK>`, and no order may be placed. Only the signed-out state is confirmed.
  `/account/login` was reached and the store answered with a verification page this environment
  cannot complete. Evidence of the attempt: `audit/screens/content-pages-account-login.png`.
- **The restock-notify form on a sold-out size.** Submitted four times across two sessions,
  including as the very first action on a clean page. An invalid address produced only the
  browser's own bubble — `Please include an '@' in the email address. 'not-an-email' is missing an
  '@'.` — and a valid address raised a **blank white bot-check panel** over the greyed product
  page that never resolved; nothing was posted and no confirmation was ever reached. **This is
  filed as untested, not broken:** that check exists specifically to refuse automated browsers, so
  a scripted session failing it is close to expected, and no follow-up verification file
  (`audit/features/raw-notify-verify.md`) exists to settle it. **The restock-notify claim is
  therefore unsettled** and needs one attempt by a person on a real handset. Two things about the
  panel are confirmable regardless of the check: when it does not complete the shopper is left
  with no message of any kind and their address still in the field; and the panel's entire copy is
  `TELL ME WHEN THIS SIZE IS BACK` / `email address` / `NOTIFY ME` — there is **no statement of
  when a shopper would hear back**, no word on what happens to the address, and no shop-authored
  error text anywhere in it. Evidence: `audit/screens/pdpcore-74-notify-valid-after.png`,
  `audit/screens/pdpcore-112-notify-clean-18s.png`.
- **The carriage bar at £6.00, £24.00, £67.00 and £73.00, on screen.** The store's rate limiting
  escalated mid-run — eight consecutive session attempts and every navigation after a cart change
  came back refused or challenged — so the middle states, the no-reload behaviour after a
  product-page add, the collection/search/cart surfaces with a loaded bag, and an independent
  measurement of the space the bar costs were all read from the build rather than watched. The
  scripts are ready to re-run. **Partly covered from another run:** the toggles pass captured the
  bar on screen with a loaded bag, showing `> £10.00 to free Tracked 24` with `TRACKED 48 FREE`
  and `TRACKED 24 FREE` beneath it, and `£20.00 to free Tracked 24` after a reload
  (`audit/screens/tg-home-light.png`). The wording and the live rewrite on `/cart` are therefore
  seen; the product-page staleness is not.
- **The non-GB browser view.** The rate limiting stopped it. The rate card itself was read from the
  store and is quoted in §4 group B, so the contradiction stands on the store's own data; what was
  not watched is what an EU or US shopper's screen actually shows.
- **The set toggle with JavaScript off.** The preview answered a JavaScript-disabled session with
  a verification page instead of the store, so this could not be observed at all.
- **`Buy with Shop` with the set ticked.** The express button sits directly under
  `ADD THE FULL FIT — £85` and shows no price of its own. Whether it carries the bundle or the
  single crewneck was not tested, because testing it means entering a Shop Pay checkout.
- **The sticky bar's `CHECKOUT NOW` with the set on.** Whether it carries the £85 bundle or the
  £50 crewneck is unknown — the preview bar sat over that corner and swallowed every tap. Given
  the bar's own label reads `£50.00 · M`, this is the one remaining path worth confirming.
- **The £135 combination.** Ticking the toggle on the shorts page while the standalone crewneck is
  already in the cart should produce a £50 crewneck line plus an £85 set line. Both halves were
  observed separately; the combination itself was not run.
- **A sold-out product card in the register.** Nothing in the catalogue is currently sold out — 13
  active products, none with every variant at zero — so the register's most important status has
  never been seen. `V2 BAGGIES` with `2 OF 5 SIZES LEFT` is the closest real case.
- **The typeahead's behaviour when the suggestion service does not answer.** Seen once returning
  nothing at all, including the link that needs no lookup; five consecutive attempts at the same
  query afterwards all returned the full panel. Not reproducible in the time available.
- **Whether the search field zooms a real iPhone.** The field is 13px and focuses itself on
  arrival; iOS Safari zooms a focused input under 16px. Could not be verified without a handset.
  The fix — a 16px field — is inside the design law.
- **Checkout beyond the payment step.** Walked to `Shipping method` → `Tracked 24 · Mon, 24
  Aug–Tue, 25 Aug · FREE` and `Tracked 48 · Wed, 26 Aug–Fri, 28 Aug · FREE`, then `Payment` /
  `Credit card` / `Klarna` / `Shop Pay`. Stopped there. Nothing submitted, no card details
  entered, no order placed. Worth recording from that screen: a checkbox reading `Keep me
  updated.` arrives **pre-ticked**, and the delivery block carries `Text me with discounts and
  latest drops.` — store settings, not theme.
- **The packaging photograph in light mode.** The light-mode capture shows an empty bordered frame
  where the dark-mode capture shows the photograph. One look on a handset settles whether the
  picture is genuinely absent there or the capture caught it early (§2.29).

---

## If you only do five things

Ordered by shopper cost divided by effort. All five fit the design law: no radius above 0, no
gradient, no shadow, no third typeface, no new accent colour, no fabricated content, no build step.

1. **Stop the set panel telling shoppers the shorts are sold out when they are not.** When a
   shopper ticks the box before choosing their own size, show the words the *shorts side of the
   same feature already uses* — `Pick a Cellblock Shorts size` — instead of
   `Cellblock Shorts sold out in M — pick another size`. Copy that exists, in a component that
   exists, replacing a false out-of-stock in the store's error colour at the moment of purchase.

2. **Make `returns` and `exchange` offer the shop's own refund policy, above the portal.**
   `refund` already does exactly this. Same list, same design, one extra row: `REFUND POLICY`
   first, `START A RETURN` beneath it for people who actually have an order. This is the single
   change that turns journey 12's worst moment into its best one, and it stops a pre-purchase
   shopper being handed to a third-party page whose own policy says 30 days where CROOKSLDN says
   14.

3. **Settle the measuring method — one caption.** The product page says
   `TAKEN AROUND THE GARMENT`; `QUESTIONS` says *"measured with the garment laid flat"*; the spec
   says `GARMENT LAID FLAT`. Two of three agree. This is the only thing in the audit that can make
   a shopper order the wrong size *by following the site's own instructions*, and every one of
   those costs the customer return postage — which the store, correctly and repeatedly, tells them
   is theirs. While the caption is open, name the columns each table actually has.

4. **Fix both ends of the search results page.** Stop printing `0 RESULTS` and `NO ITEMS IN THE
   REGISTER MATCH THAT QUERY.` when curated links or page results are on the same screen; and when
   nothing matches at all, show the three links the *blank* search page already shows. Two
   conditions, no new anything, and it removes the moment where a shopper reads the biggest words
   on the screen and concludes the site has no returns information.

5. **Stop `ON MODEL` showing a photograph of a different garment.** Right now the control that
   promises "show me this worn" puts one picture of a man in charcoal shorts on the £6 socks, the
   £18 duffle and both pairs of £60 jeans. Point it at the model images that already exist on the
   store — `BLUE WASH OG JEANS` has one — and hide the toggle for products that have none, rather
   than substituting a different product.

**The one that is not cheap, and should be next:** the cart line that says
`Complete the set — add the Cellblock Shorts, save £10.` and leads to a £95 cart. It has the
highest single-shopper cost on this list — a specific broken money promise, the kind that arrives
as a complaint rather than a bounce — but making the bundle-in-cart state appear, and offering the
£85 conversion when both halves are already in the bag, is real work rather than a copy change.
Until it is done, the honest interim is to stop the line promising a number the next screen will
not honour.
