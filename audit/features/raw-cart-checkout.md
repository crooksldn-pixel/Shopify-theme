# raw-cart-checkout

Mobile 390×844, GB market, staging theme `202053779799`. Checkout was walked to
the payment step and abandoned — no order placed, no card details entered.

---

### The cart page's voice

**Should:** read like the shop the shopper has been walking through.
**Did:** the frame holds — near-black ground, mono type, status bar, handcuff
logo, `BAG [n]`, carriage bar, full footer, and the cart's own furniture (line
borders, stepper, bin) is squared off with no radius. What sits inside that frame
still speaks Shopify's stock sentence case: `Cart`, `Discount`, `Estimated
total`, `Duties and taxes included. Shipping is calculated at checkout.`, and the
primary button reads `Check out`. Everywhere else the site says `ADD TO BAG`,
`CATALOGUE`, `IN STOCK`, `TRACKED 48 FREE` in uppercase mono. One line of
non-CROOKSLDN colour sits in the summary: `Pay in 3 interest-free instalments of
£20.00 with shop`.
**Verdict:** partly
**Shopper cost:** small but constant — the bag is the one page where the terminal
voice drops and Shopify's own voice answers.
**Evidence:** audit/screens/cc-99-fake-code-error.png, cc-40-cart-one-item.png

### Quantity up and down

**Should:** press `+`, the cart says two and the money follows.
**Did:** works, and quickly. Within about a second and a half of pressing `+` on
a £60 line, the line total, `Cart total £120.00 GBP` and `Estimated total
£120.00 GBP` had all moved, and the carriage bar above rewrote itself from
`£10.00 to free Tracked 24` to `Free Tracked 24 — unlocked`. `−` reverses it
just as cleanly, and the bar drops back to `£10.00 to free Tracked 24`.
**Verdict:** works
**Evidence:** audit/screens/cc-61-plus-1500ms.png, cc-64-minus.png

### The header's `BAG [n]` after any change made in the cart

**Should:** agree with the cart it is sitting directly above.
**Did:** it does not move until the page is reloaded. With the cart showing two
jeans and £120.00, the header still read `BAG [1]` — and still read `BAG [1]`
nine and a half seconds later. Reloading fixed it to `BAG [2]`. Pressing `−`
then left `BAG [2]` above a one-item £60.00 cart. Emptying the cart entirely left
`BAG [2]` sitting directly above the words `Your cart is empty`. Every other
piece of the page (totals, carriage bar) updates live; only the bag count is
stale.
**Verdict:** broken
**Shopper cost:** the two numbers on screen disagree about what you are buying,
at the exact moment a shopper is checking they got it right. On an emptied cart
it reads as "something is still in there" and invites a second look.
**Evidence:** audit/screens/cc-70-after-remove.png — `BAG [2]` in the header,
`Your cart is empty` in the page. Also cc-61-plus-1500ms.png / cc-62-plus-9500ms.png.

### Taking a quantity to zero

**Should:** either work, or say why not.
**Did:** it cannot be done and nothing says so. The `−` button is disabled at 1.
Typing `0` into the quantity box and pressing Enter fires no request at all;
typing `0` and tapping away fires a request and then silently rewrites the box
back to `1` — cart unchanged at 3 items and £155.00. The shopper's `0` simply
disappears.
**Verdict:** absent
**Shopper cost:** anyone who reaches for the number box to drop a line has to
work out for themselves that the bin is the only route.
**Evidence:** audit/screens/cc-82-zero-by-blur.png (box back at `1`, cart still
£155.00), cc-67-zero-after-reload.png

### Removing an item, and undo

**Should:** remove it; ideally offer a way back.
**Did:** the bin (labelled `Remove GREY WASH OG JEANS - XS` to a screen reader)
removes the **whole line**, both units of a quantity-2 line, with no
confirmation. It is fast and quiet: 900ms after the tap the row has folded to
nothing and the page has already become the empty-cart page. There is **no undo,
no "removed" message and no toast** — the only thing announced to a screen
reader afterwards was the carriage bar's `£20.00 to free Tracked 48`. The word
"undo" does not exist anywhere in the theme.
**Verdict:** works (removal) · undo **absent**
**Shopper cost:** a misplaced tap on the bin costs the item and the size choice,
and the only way back is to find the product again.
**Evidence:** audit/screens/cc-69-removing-900ms.png, cc-70-after-remove.png

### Three different items — does the total add up?

**Should:** add up.
**Did:** exactly. `CHARCOAL CELLBLOCK SHORTS £45.00` + `BLUE WASH JORTS £50.00`
+ `GREY WASH OG JEANS £60.00`, each showing its own line total, `Cart total
£155.00 GBP`, `Estimated total £155.00 GBP`. Carriage bar: `Free Tracked 24 —
unlocked` with both tiers ticked. Header `BAG [3]` (correct, because the page had
been loaded fresh).
**Verdict:** works
**Evidence:** audit/screens/cc-81-three-items-full.png, cc-90-fake-code.png
(all three lines and `Subtotal £155.00` in one frame)

### Shipping costs before checkout

**Should:** a shopper should be able to find out what carriage costs before they
hand over an address.
**Did:** partly. The carriage bar states the *free* thresholds and progress
towards them — `£20.00 to free Tracked 48`, `£10.00 to free Tracked 24`, `Free
Tracked 24 — unlocked`, with `TRACKED 48 FREE` / `TRACKED 24 FREE` ticked off.
What is never shown anywhere in the cart is the **price** of either service if
you do not reach the threshold (the real card is £3.00 and £4.99). The summary
says only `Duties and taxes included. Shipping is calculated at checkout.` There
is **no estimator, no postcode field, no country selector** anywhere on the cart
page. At checkout, with a £155 cart, both options came back `Tracked 24 · Mon,
24 Aug–Tue, 25 Aug · FREE` and `Tracked 48 · Wed, 26 Aug–Fri, 28 Aug · FREE`,
which honours the bar's promise.
**Verdict:** partly
**Shopper cost:** a shopper with a £15 bag is told what free carriage would cost
them to reach, but not what carriage costs if they don't — they have to go to
checkout, or the shipping policy, to find out.
**Evidence:** audit/screens/cc-99-fake-code-error.png (bar + summary line),
cc-86-payment-step.png (the rates, finally)

### The discount field

**Should:** be findable and behave.
**Did:** it is a closed accordion labelled `Discount` with a `+`, sitting under
the last line item. Opening it gives a field placeheld `Discount code` and a
purple `Apply`. `10CROOKS` on a normal £155 cart produced, immediately and
cleanly: `Subtotal £155.00` / `10CROOKS  −£15.50` / `Estimated total £139.50
GBP`, plus a removable `10CROOKS ×` pill. The `Subtotal` row only appears once a
discount exists. Removing the pill restored £155.00.
**Verdict:** works
**Evidence:** audit/screens/cc-89-10crooks-normal-full.png, cc-97-discount-open.png

### `10CROOKS` on a cart holding the £85 `cellblock-set` (O1)

**Should:** the set is sold as a £10 saving at £85; the cart should not undercut
the price the product page just promised.
**Did:** it does. The product page's own words, on the crewneck PDP, are `Cop the
full fit — add the matching Cellblock Shorts. Save £10.`, then `£95` struck
through beside `£85 for the set`, then `FREE UK TRACKED 24 INCLUDED`, and the
button relabels itself `ADD THE FULL FIT — £85`. In the cart the line reads
`CELLBLOCK SET / CHARCOAL CELLBLOCK CREWNECK - XS / CHARCOAL CELLBLOCK SHORTS -
XS / £85.00`. Type `10CROOKS` and the summary becomes:

> `Subtotal £85.00` · `10CROOKS −£8.50` · `Estimated total £76.50 GBP`

The line item still says `£85.00`; only the summary carries the £76.50. It
survives a reload. So the shopper is charged **£76.50 for a set the product page
promised at £85**, and the saving against buying the two garments separately is
£18.50, not the £10 the page states. Known as **O1** — recorded here only for
what a shopper sees.
**Verdict:** works as coded, contradicts the copy
**Shopper cost:** none to the shopper (they gain £8.50); the loss is the
merchant's, and the set's whole pricing story stops being true the moment a
public code is in play.
**Evidence:** audit/screens/cc-80-set-pdp-promise.png (the promise),
cc-92-10crooks-on-set.png (`Subtotal £85.00`, `10CROOKS −£8.50`),
cc-93-set-discount-reloaded.png

### The cart-side confirmation of the set saving (`SPEC §3.13`, state 2)

**Should:** per the spec, "the bundle in the cart → the saving confirmed in
words".
**Did:** nothing renders. With `CELLBLOCK SET` in the cart the page goes straight
from the carriage bar to `Cart`; there is no `SET SAVING APPLIED` line, no `£95`,
no mention of £10 anywhere. The *other* state works perfectly — with only the
shorts in the cart the line `Complete the set — add the Cellblock Crewneck, save
£10.` appears above the cart title and links to the crewneck.
**Verdict:** broken (one of the section's two states never appears)
**Shopper cost:** the shopper who just took the offer sees `£85.00` with nothing
to confirm they saved anything — the moment the bundle is supposed to pay off is
silent. And with `10CROOKS` applied, the only saving the cart ever names is the
code's `−£8.50`, never the set's £10.
**Evidence:** audit/screens/cc-91-set-in-cart-full.png (no confirmation line),
cc-81-three-items.png (the offer state, working)

### An obviously fake code

**Should:** say the code is not real.
**Did:** typing `FREESTUFF123` and pressing `Apply` clears the field and shows,
in the site's own mono with a red dot, exactly:

> `Discount code cannot be applied to your cart`

Any code already applied stays applied. The message never says the code does not
exist — "cannot be applied to your cart" reads like the code is real but wrong
for these items, which invites a shopper to go and change their cart.
**Verdict:** partly
**Shopper cost:** wrong diagnosis, and the typed code is wiped so a typo cannot
be corrected — it has to be retyped from scratch.
**Evidence:** audit/screens/cc-99-fake-code-error.png

### Checkout — where the fiction ends

**Should:** the handover should not feel like landing on a different company.
**Did:** pressing `Check out` left the browser sitting on the cart for about
**eleven seconds**, then the page changed to
`crooksldn.com/checkouts/cn/…`, titled `Checkout - CROOKSLDN`. The evidence
terminal is gone completely: white ground, black Helvetica/system sans, blue
links (`Order summary`, `Sign in`), rounded input fields, a blue tick, grey
express-checkout placeholders loading in. The only thing that survives the jump
is the word `CROOKSLDN` set in bold sans at the top left, and the `£155.00`.
Headings read `Express checkout`, `Contact`, `Delivery`. A checkbox reading
`Keep me updated.` is **pre-ticked**.

The payment step (this checkout is one page — no `Continue to payment` step
exists) shows `Shipping method` → `Tracked 24 · Mon, 24 Aug–Tue, 25 Aug · FREE`
and `Tracked 48 · Wed, 26 Aug–Fri, 28 Aug · FREE`, then `Payment` / `All
transactions are secure and encrypted.` / `Credit card` with Visa, Mastercard and
Maestro marks and `+5`, `Card number`, `Expiration date (MM / YY)`, `Security
code`, `Name on card`, `Use shipping address as billing address`, then `Klarna`
and `Shop Pay — Pay in full or in installments`. **Stopped there; nothing
submitted, no card details entered.**

After forty minutes of black screens, mono type and evidence-log language, the
last screen before paying is an ordinary blue-and-white Shopify form. It reads as
a handoff to a third party. Nothing on it is wrong — it is fast, honest and
familiar, and the shipping options match what the cart promised — but the shop
you were in stops existing at that click.
**Verdict:** works (functionally) · the brand ends at the door
**Evidence:** audit/screens/cc-83-checkout-first-screen.png,
cc-86-payment-step.png, cc-84-checkout-filled.png

### Back from checkout

**Should:** the cart should still be there.
**Did:** one press of Back landed on `/cart` with all three lines intact —
`£45.00`, `£50.00`, `£60.00`, `Cart total £155.00 GBP`, `BAG [3]` correct,
carriage bar still `Free Tracked 24 — unlocked`. Nothing lost, nothing
duplicated.
**Verdict:** works
**Evidence:** audit/screens/cc-87-after-back.png, cc-88-cart-after-back.png

### Coming back later, and a genuinely new session

**Should:** a returning shopper keeps their bag; a stranger on a new device does
not inherit one.
**Did:** both behave. A brand-new browser session opened `/cart` to `BAG [0]` and
an empty cart. Restoring the previous session's cookies (the same shopper,
returning in the same browser) brought the bag back exactly as left — one
`CELLBLOCK SET - XS / XS`, £76.50, **with the `10CROOKS` code still attached**.
**Verdict:** works
**Shopper cost:** none, though the persisting discount code is worth knowing
about: it stays on the cart across visits until it is removed by hand.
**Evidence:** audit/screens/cc-30-empty-cart-newsession.png,
cc-32-cart-cookie-replay.png

### The empty cart page

**Should:** look like the same website.
**Did:** it mostly does, and then it doesn't. The ground is still `rgb(11,10,14)`,
the type is still CRX Mono, the status bar, handcuff logo, `CATALOGUE SEARCH BAG
[0] LIGHT MODE MENU` header and the whole `SHOP / INFORMATION / CONTACT / GAME`
footer with `EVIDENCE TERMINAL V0.2 // CROOKSLDN // OWN THE STREETS™ // © 2026`
are all present and correct. What sits in the middle is Shopify's stock empty
state, word for word:

> `Your cart is empty`
> `Have an account? Log in to check out faster.`
> `Continue shopping`

All three in sentence case, centred, with `Continue shopping` as a solid purple
filled block — the same purple as `Check out`. Below it, Horizon's own
`You may also like` / `View all` grid of four products. There is no page title,
no `BAG` heading, nothing in the site's register at all; the carriage bar renders
nothing on a freshly-loaded empty cart (though it reappears saying `£20.00 to
free Tracked 48` if you arrive at empty by removing your last item).
`Continue shopping` goes to `/collections/all`, which lands correctly on the
catalogue with the h1 `ALL`.

How jarring is it? Less than the quick look suggested — it is not a generic white
Shopify page, and the colours and fonts are the site's own. What breaks is the
**voice**: three sentences of ordinary Shopify English in a shop that has spent
every other screen writing in uppercase evidence-log register. It reads like the
site handed the page to someone else for four seconds.
**Verdict:** partly
**Shopper cost:** low, but this is the screen every shopper sees first if they
tap `BAG` out of curiosity, and it is the least CROOKSLDN thing on the site
except the checkout.
**Evidence:** audit/screens/cc-30-empty-cart-newsession.png,
cc-30-empty-cart-newsession-full.png, cc-01-empty-cart.png,
cc-95-continue-shopping-landing.png

---

## Surprises

- **The header `BAG [n]` never updates from the cart page.** Add, subtract or
  remove — the count only changes on a reload. `BAG [2]` sitting over `Your cart
  is empty` is the worst version of it. Everything else on the page (totals,
  carriage bar) does update live, which makes the stale number look deliberate.
- **The set's cart-side confirmation never renders.** `SPEC §3.13` promises the
  saving "confirmed in words" when the bundle is in the cart; nothing appears.
  The sibling state (half a set → `Complete the set — add the Cellblock
  Crewneck, save £10.`) works, so the feature looks fine until you actually buy
  the set.
- **A quantity of `0` is silently rewritten to `1`.** No message, no explanation,
  and `−` is disabled at 1 — the bin is the only way out and nothing says so.
- **Checkout runs on `crooksldn.com`, not the preview host.** Pressing `Check
  out` on the staging theme hands straight to the live store's checkout, and it
  took about eleven seconds to appear.
- **`Keep me updated.` arrives pre-ticked at checkout**, and the delivery block
  carries `Text me with discounts and latest drops.` — marketing opt-ins on a UK
  checkout, and the first one is on by default. Store settings, not theme.
- **`Pay in 3 interest-free instalments of £20.00 with shop`** sits in the cart
  summary — the only piece of another brand's colour on the page.
- **The discount code survives across visits.** A cart restored days later still
  carries `10CROOKS` and its `−£8.50`.
- **The fake-code message clears the field.** A shopper who mistypes a real code
  cannot correct it; they have to retype the whole thing.

## Missing

- Any undo, or any confirmation at all, after removing a line.
- Any way to zero a line from the quantity box.
- Any shipping estimator, and any statement of what carriage *costs* (£3.00 /
  £4.99) if the shopper does not reach a free tier — the cart only ever names
  the free thresholds.
- Any confirmation in the cart that the set saved £10.
- A cart note field (a shopper cannot say "leave with a neighbour").
- Any CROOKSLDN framing on the empty cart — no title, no register line, nothing
  in the site's voice.

## Contradictions

- Carriage bar: `Free Tracked 24 — unlocked` — summary, four lines below it:
  `Duties and taxes included. Shipping is calculated at checkout.` One says
  carriage is settled, the other says it isn't.
- Product page: `£85 for the set` / `Save £10.` / `ADD THE FULL FIT — £85` —
  cart with `10CROOKS`: `Estimated total £76.50 GBP`. The £85 promise stops
  being true the moment a public code is used (O1).
- Header: `BAG [2]` — same screen, same moment: `Your cart is empty`.
- `SPEC §3.13`: the bundle in the cart means "the saving confirmed in words" —
  the cart with the bundle in it says `£85.00` and nothing else.
- Fake code message: `Discount code cannot be applied to your cart` — for a code
  that does not exist at all. The wording blames the cart.

## Works and must be protected

- **The carriage bar's live rewrite on every cart change** — `£10.00 to free
  Tracked 24` → `Free Tracked 24 — unlocked` within a second and a half, and
  it matched the real rates at checkout (`Tracked 24 FREE`, `Tracked 48 FREE`).
- **The arithmetic.** £45 + £50 + £60 = `£155.00`, line totals, `Cart total` and
  `Estimated total` all agreeing, before and after a discount.
- **The discount mechanism** — apply, a removable `10CROOKS ×` pill, `Subtotal` /
  `−£15.50` / `Estimated total` breakdown, in the site's own type.
- **Back from checkout returns an intact cart** in one press.
- **The cart survives a return in the same browser**, code and all.
- **The set offer line in the cart** — `Complete the set — add the Cellblock
  Crewneck, save £10.` — quiet, one line, correctly named, links to the partner.
- **The bin's accessible name** — `Remove GREY WASH OG JEANS - XS` — names the
  size as well as the product.

---

*Method note: the store's bot protection (429s and a challenge page) was tripped
repeatedly by the other audit browsers during this run and cost about twenty
minutes. Every claim above comes from a request that returned 200; the network
status of each cart call was logged for exactly this reason, and screenshots from
throttled attempts are not cited.*
