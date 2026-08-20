# Complete-the-set — raw findings

Area key `set-feature`. Configured on `charcoal-cellblock-crewneck` (£50) ↔
`charcoal-cellblock-shorts` (£45), bundling to `cellblock-set` at £85.
Mobile 390×844 unless stated. Every quoted string is copied off the screen.

Stock at the time of the audit (so the stock claims below can be judged):
crewneck XS 10 / S 11 / M 17 / L 4 / XL 4 · shorts XS 30 / S 30 / M 19 / L 14 /
XL 4 · bundle 25 variants, 201 units, **nothing sold out anywhere**.

---

### The collapsed line

**Should:** one line, collapsed by default, saying what you get and what you save.

**Did:** exactly one line, with a thumbnail of the shorts and a checkbox, sitting
between the dispatch line and the buy button:

> `Cop the full fit — add the matching Cellblock Shorts. Save £10.`

Nothing else. It names the other garment and the saving. It never says the shorts
cost £45, never says the pair costs £85, and never says a shorts size will be
needed. The £50 above it is the only price on screen, so the shopper's arithmetic
from this line alone is "£50, plus an unknown, minus £10".

**Verdict:** partly

**Shopper cost:** the one number a shopper wants before opening a bundle control —
what the total becomes — is the one number the collapsed line withholds. £85 only
appears after ticking, i.e. after committing to look.

**Evidence:** `audit/screens/set-01-collapsed-row.png`

---

### Ticking it — the partner size row

**Should:** ticking reveals the partner's size row, live partner stock, was/now
prices, and relabels the button.

**Did:** ticking reveals a row headed `CELLBLOCK SHORTS SIZE` with five buttons
`XS S M L XL`, then a stock line, then the price pair, then
`FREE UK TRACKED 24 INCLUDED`. With no shorts size chosen yet the stock line
reads:

> `Pick a Cellblock Shorts size`

Once a valid pair is chosen the price pair reads `£95` struck through, then
`£85 for the set`, and the button relabels. The arithmetic is right: 50 + 45 = 95,
set 85, saving 10, matching the collapsed line's "Save £10".

**Verdict:** works, with two exceptions recorded separately (the stock line and
the button's price format)

**Evidence:** `audit/screens/set-06-own-M-partner-L.png` —
`£95` `£85 for the set` `FREE UK TRACKED 24 INCLUDED`

---

### The button relabel

**Should:** `ADD THE FULL FIT — £85.00`.

**Did:** the button reads

> `ADD THE FULL FIT — £85`

No pence. Every other price in the same journey carries them: the product price
above it is `£50.00`, the shorts are `£45.00` in "MORE FROM THIS DROP", and the
cart line is `£85.00`. The struck price in the panel is `£95`, not `£95.00`.
So on one screen a shopper reads `£50.00`, `£95`, `£85`, and then `£85.00` in the
cart.

**Verdict:** partly

**Shopper cost:** small but real — `£85` next to `£50.00` reads as a different
kind of number, and a shopper checking that the cart charged what the button
promised is comparing `£85` with `£85.00`.

**Evidence:** `audit/screens/set-11b-about-to-add-viewport.png` —
`ADD THE FULL FIT — £85`

---

### "Live partner stock"

**Should:** ticking reveals live partner stock.

**Did:** when a valid pairing is selected the stock line is **empty** — the panel
says nothing at all about the shorts' availability. I checked the two extremes:
shorts XS (30 units) and shorts XL (4 units, the lowest pairing in the whole
matrix) both produce an empty line. The only stock sentence the panel can produce
is a sold-out one, and today it produces it wrongly (next entry).

This is not a request for a stock counter — `SPEC §9.7` forbids invented scarcity
and that is right. But the panel currently gives a shopper no positive signal at
all that the shorts in their size exist, while the garment they are already
looking at says `IN STOCK` two inches above.

**Verdict:** partly

**Evidence:** `audit/screens/set-07-partner-XL-lowstock.png` (4 units left,
nothing said) vs `audit/screens/set-06-own-M-partner-L.png`

---

### Tick the set BEFORE choosing your own size — the false sold-out

**Should:** if you tick first and pick a shorts size, the panel should wait for
your own size, or ask for it.

**Did:** it tells you the shorts are sold out. In red:

> `Cellblock Shorts sold out in M — pick another size`

The shorts in M were not sold out. There were **19** of them. I swept the whole
row with no crewneck size chosen and got the same sentence five times:

> `Cellblock Shorts sold out in XS — pick another size`
> `Cellblock Shorts sold out in S — pick another size`
> `Cellblock Shorts sold out in M — pick another size`
> `Cellblock Shorts sold out in L — pick another size`
> `Cellblock Shorts sold out in XL — pick another size`

So the instruction it gives — pick another size — cannot be obeyed. Every size in
the row is "sold out" until you touch a control the message never mentions.

While that sentence is on screen the buy button reads `SELECT A SIZE` and is
dead, so the shopper holds two contradictory instructions ("this size is gone" /
"choose a size") and neither states the true one: *choose your own size first*.

It does recover — going back up and picking a crewneck size clears the message
and the button becomes `ADD THE FULL FIT — £85`. Nothing on screen suggests that
is the way out.

The shorts page already contains the right sentence for this situation: when a
size is chosen on that page and the partner's is not, the buy button becomes
`Pick a Cellblock Crewneck size`. The crewneck page needs the same words when the
shopper picks the partner's size first, instead of the sold-out sentence — copy
that already exists, no new component, nothing outside the design law.

**Verdict:** broken

**Shopper cost:** the worst kind — a false out-of-stock. A shopper who opens the
offer before picking their own size is told, in the store's own error colour,
that the item they came to buy the matching half of is unavailable in their size.
The honest response to that message is to give up on the set.

**Evidence:** `audit/screens/set-03-partner-only-no-own-size.png`,
`audit/screens/set-03b-partner-only-viewport.png`

---

### The sticky bar disagrees with the button

**Should:** the sticky bottom bar repeats product, price, selected size and both
actions (`SPEC §3.5`).

**Did:** the bar's action does relabel — it carries `ADD THE FULL FIT — £85`
correctly. Everything to the left of it does not. Scrolled past the buy area with
the set on and crewneck M + shorts L chosen, the bar reads:

> `CHARCOAL CELLBLOCK CREWNECK` / `£50.00 · M` / `ADD THE FULL FIT — £85` /
> `CHECKOUT NOW`

`£50.00` for a purchase that charges £85, and one size where two were chosen.
The page's own price line at the top of the record also stays `£50.00` for as
long as the set is on.

On a 390px phone it is worse than wrong, it is mangled: the longer button label
squeezes the text column until the product name truncates to `CH…` and the price
wraps and clips into `£50.0` on one line and `· M` on the next — a cut-off price
sitting against a button charging a different one.

**Verdict:** partly

**Shopper cost:** the sticky bar is the control most likely to be used on a
phone, because it follows you down the page while the panel scrolls away. It is
the one surface that states a price and a size for the thing you are about to
buy, and while the set is on it states the wrong price, half the sizes, and a
clipped product name.

**Evidence:** `audit/screens/set-42-stickybar-visible.png`,
`audit/screens/set-43-stickybar-element.png` — `CH…` / `£50.0` / `· M` /
`ADD THE FULL FIT — £85` / `CHECKOUT NOW`

---

### Unticking — does everything come back?

**Should:** unticking restores whatever the page decided before.

**Did:** cleanly, on every axis I could measure. Button back to `ADD TO BAG`;
hidden variant id back to the crewneck M variant (53936235282775, identical to
the pre-tick value); price line `£50.00`; own size M still selected and still
pressed; panel hidden; sticky bar back to `£50.00 · M` / `ADD TO BAG`. The stale
`£95` / `£85 for the set` text and the previous partner selection stay in the
hidden panel, invisible, and are overwritten next time it opens.

**Verdict:** works

**Evidence:** `audit/screens/set-09-unticked-restored.png`,
`audit/screens/set-09b-unticked-restored-row.png`

---

### THE KEY TEST — one line item at £85 in the cart

**Should:** one add, one line, £85.00, no second request.

**Did:** exactly that. Added crewneck M + shorts L. `cart.js` reports
`item_count: 1`, `total_price: 8500`, one line. The cart line describes itself:

> `CELLBLOCK SET`
> `CHARCOAL CELLBLOCK CREWNECK - M`
> `CHARCOAL CELLBLOCK SHORTS - L`
> `£85.00`

with a quantity stepper showing `1` and a line total `£85.00`.

Would a shopper reading that line know they are getting two garments in two
sizes? **Yes** — this is the clearest thing in the whole feature. Both garments
are named in full and each carries its own size, on its own line, under a title
that says SET. Nothing has to be inferred.

Two smaller things on the same line: the thumbnail is the crewneck only, and the
line never restates the saving — no `£95` struck through, no "saved £10" — so the
one place a shopper checks their money is also the one place the deal disappears.
The add confirmation on the PDP reads `Added — 1 in bag`, and the header counter
goes to `BAG [1]`, which is literally true of line items and slightly odd for
someone who just bought two garments.

**Verdict:** works

**Evidence:** `audit/screens/set-14-cart-line.png`,
`audit/screens/set-13b-cart-viewport.png`, `audit/screens/set-12-after-add.png`

---

### The set section on /cart, with the set in the cart

**Should:** `SPEC §3.13` — "the bundle in the cart → the saving confirmed in
words."

**Did:** nothing renders. With `CELLBLOCK SET` in the cart, the `set-cart`
section is not present in the page at all — no wrapper, no text. The cart runs
straight from the carriage bar to `Cart`. The line item itself does not restate
the saving either, so between pressing `ADD THE FULL FIT — £85` and paying,
**the £10 is never mentioned again.**

**Verdict:** absent

**Shopper cost:** the saving is the entire reason to buy the set, and the cart —
the screen where people check they got what they thought — never confirms it. A
shopper reconsidering at the cart has `£85.00` and no reminder that the parts
come to £95.

**Evidence:** `audit/screens/set-20-cart-shorts-side.png` — the cart with the set
in it, no set section; compare `audit/screens/set-16b-cart-one-half-viewport.png`
where the offer state does render

---

### One half in the cart — the offer for the other half

**Should:** `SPEC §3.13` — one half of a set in the cart → a single line offering
the other.

**Did:** it renders, above the cart heading, as an underlined accent-coloured
link:

> `Complete the set — add the Cellblock Shorts, save £10.`

The link points at `/products/charcoal-cellblock-shorts`.

**Verdict:** works as a line of copy — but see the next entry for where it leads.

**Evidence:** `audit/screens/set-16b-cart-one-half-viewport.png`,
`audit/screens/set-17-cart-offer-other-half.png`

---

### Following that offer does not save £10

**Should:** a link that says "save £10" should end in a cart £10 cheaper than the
alternative.

**Did:** I did exactly what the line says. Crewneck M in the cart (£50.00), tapped
`Complete the set — add the Cellblock Shorts, save £10.`, landed on
`/products/charcoal-cellblock-shorts`, picked a size and pressed the button —
which on that page reads `Add to bag`. Result:

> `Cart 2` · `CHARCOAL CELLBLOCK SHORTS  Size: L  £45.00`
> `CHARCOAL CELLBLOCK CREWNECK  Size: M  £50.00`
> `Estimated total £95.00 GBP`

`total_discount: 0`. **£95.00, not £85.00.** The £10 the link promised is not
applied, not offered, and not mentioned — with both halves sitting in the cart in
matching sizes, the set section does not render at all, so nothing says "these
two are £85 together".

The landing page does carry the toggle (`Cop the full fit — add the matching
Cellblock Crewneck. Save £10.`), but using it there adds a **£85 SET line on top
of the £50 crewneck already in the cart** — £135, with two crewnecks — so the
only route to the advertised price is: tick the toggle, choose a crewneck size,
add the set, then delete the crewneck you already had. Nothing anywhere says so.
*(The £135 end-state is the arithmetic consequence of the two behaviours I did
test — the toggle adds a separate £85 SET line, and the standalone crewneck line
stays — I did not run that combination itself.)*

**Verdict:** broken

**Shopper cost:** the store makes a specific money promise, links to a page, and
the obvious action on that page charges £95. A shopper who trusts the link pays
£10 more than the store just told them they would. This is the one finding here
that could reach a complaint.

**Evidence:** `audit/screens/set-34-followed-offer-landing.png`,
`audit/screens/set-35-cart-after-following-offer.png`, and the read-back above

---

### The shorts side (the partner product)

**Should:** identical behaviour from the partner's page.

**Did:** a mirror image, and slightly better behaved than the crewneck side.
Collapsed line:

> `Cop the full fit — add the matching Cellblock Crewneck. Save £10.`

Ticked with a shorts size already chosen, the size row is headed
`CELLBLOCK CREWNECK SIZE` and — this is the good bit — **the buy button itself
becomes the instruction**:

> `Pick a Cellblock Crewneck size`

disabled, with the same words on the stock line. That is exactly the guidance the
crewneck side fails to give when a shopper ticks first. It appears here only
because the shopper's own size was already chosen.

Shorts S + crewneck XL produced `£95` / `£85 for the set` /
`ADD THE FULL FIT — £85`, hidden variant `54377206514007`, which is the bundle's
`XL / S`. The cart then read:

> `CELLBLOCK SET`
> `CHARCOAL CELLBLOCK CREWNECK - XL`
> `CHARCOAL CELLBLOCK SHORTS - S`
> `£85.00`

The sizes are attached to the right garments from either direction. One line,
`item_count: 1`, `total_price: 8500`.

**Verdict:** works

**Evidence:** `audit/screens/set-18-shorts-collapsed.png`,
`audit/screens/set-19-shorts-S-crew-XL.png`,
`audit/screens/set-20-cart-shorts-side.png`

---

### The bundle's own product page

**Should:** not specified — but `/products/cellblock-set` is published, sits in
the `Sets` collection, and a shopper can reach it.

**Did:** `/collections/sets` renders `SETS` / `1 ITEMS` / `NO. 01` /
`CELLBLOCK SET` / `£85.00` / `AVAILABLE` / `DROPPED 18.08`, and the product page
loads with **two size rows**:

> `SIZE`  XS S M L XL
> `CHARCOAL CELLBLOCK SHORTS (SIZE)`  XS S M L XL

The second row names its garment. The first is bare `SIZE`. Nothing else on the
visible page says what the two garments are — the hero image is the crewneck
alone, and the only sentence that explains the product ("The full Cellblock fit —
charcoal crewneck and shorts… £85 against £95 bought separately") is inside the
`ITEM DESCRIPTION` accordion, which is closed by default (deliberate, `SPEC §9.4`).
There are no `SPECIFICATION` or `MEASUREMENTS` accordions on this page at all, so
a shopper choosing two sizes has no measurements for either garment.

`Sets` is in no menu — `SHOP` lists ALL / NEW / TEES / DENIM / SWEATS /
TRACKSUITS / ACCESSORIES and nothing else. Search does find it: `/search?q=set`
returns `NO. 01 CELLBLOCK SET £85.00 AVAILABLE DROPPED 18.08` at the top of three
results, and `cellblock` returns it third. So the set exists for anyone who
already knows to look for it, and for nobody who is browsing.

**Verdict:** partly

**Shopper cost:** a shopper who arrives here — the one page in the store actually
called a SET — must guess that the first `SIZE` row is the crewneck, with the
struck-through pricing and the "save £10" framing that the PDP toggle gives them
nowhere in sight.

**Evidence:** `audit/screens/set-25-bundle-pdp.png`,
`audit/screens/set-26-sets-collection.png`

---

### Desktop

**Did:** identical at 1440×900 — same copy, same panel, same
`ADD THE FULL FIT — £85`, same restore on untick. No layout difference worth a
shopper's attention.

**Verdict:** works

**Evidence:** `audit/screens/set-27-desktop-collapsed.png`,
`audit/screens/set-28-desktop-open.png`

---

### No measurements for the garment you are being asked to size

**Should:** not specified — but the panel asks a shopper to choose a size for a
garment they are not looking at.

**Did:** the accordions on the crewneck page are `SPECIFICATION`,
`ITEM DESCRIPTION`, `MEASUREMENTS`, `CHAIN OF CUSTODY` — all four about the
crewneck, and `SIZE GUIDE` scrolls to the crewneck's measurements. The shorts'
measurements (`fits waist`, `length`, `leg opening`) exist as data on the shorts
product, and are not reachable from the panel. There is no link to the shorts
page from inside the offer either — the thumbnail is not a link.

**Verdict:** partly

**Shopper cost:** a shopper who knows they are an M on top and an L on the bottom
is fine. Anyone else is guessing a size for an unseen garment, on a set that is
one line item and therefore, on a change of mind, one thing to send back rather
than two.

**Evidence:** `audit/screens/set-06b-own-M-partner-L-viewport.png`,
`audit/screens/set-23b-false-soldout-viewport.png` — accordion titles visible
below the panel

---

## JUDGEMENT — would a stranger understand it?

**Would they understand they are buying two garments for £85?** Once they tick
it, yes — but only once they tick it, and only if they tick it in the right
order.

**Where the wording helps, specifically:**

- `Cop the full fit — add the matching Cellblock Shorts. Save £10.` names the
  other garment in full and states the saving. No jargon, no fiction, no
  countdown. It reads like a shop assistant, which is the point.
- The revealed size row is headed `CELLBLOCK SHORTS SIZE`, not "Size". That one
  decision removes the commonest bundle confusion outright — you are never in
  doubt whose size you are picking. It works identically in reverse
  (`CELLBLOCK CREWNECK SIZE` on the shorts page).
- `£95` struck through followed by `£85 for the set` does the arithmetic for the
  shopper and, crucially, the words "for the set" say that the £85 covers both.
  This is the one place the whole proposition is stated properly.
- `ADD THE FULL FIT — £85` puts the price on the control that charges it.
- The cart line spells out `CHARCOAL CELLBLOCK CREWNECK - M` and
  `CHARCOAL CELLBLOCK SHORTS - L` under `CELLBLOCK SET`. Nobody could misread
  that.

**Where it leaves them guessing:**

- **The collapsed line never says £85.** A shopper deciding whether this offer is
  worth opening knows only "£50, plus something, minus £10". The two numbers that
  make the case — £95 and £85 — are both behind the tick. "Save £10" without a
  total is the weakest possible version of a strong offer.
- **It never says the shorts are £45**, so "Save £10" cannot be checked. The £45
  does appear further down the page in `MORE FROM THIS DROP`, but not in the
  offer.
- **The page argues with itself at the moment of purchase.** The price at the top
  stays `£50.00` and the sticky bar reads `£50.00 · M` while the button says
  `ADD THE FULL FIT — £85`. The shopper is being asked to trust the button over
  the two prices around it.
- **"The full fit" is brand language, not a description.** Nowhere does the offer
  say "two garments" or "2 items". A shopper who does not read "fit" as "outfit"
  has only the thumbnail to go on.
- **Order of operations is punished, not explained.** Tick before choosing your
  own size and the store tells you, in red, that the shorts are sold out in every
  size. That is the single most damaging sentence in the feature.
- **The saving evaporates after the PDP.** No £95, no "you saved £10" in the cart
  — the confirmation state that `SPEC §3.13` promises does not render at all.

**Does £85 obviously beat £50 + £45?** Only inside the open panel, and only for
about as long as it takes to press the button. Before ticking: not stated. After
adding: not restated. The proof exists on exactly one screen.

---

## Not tested — recorded so nobody assumes it passed

- **With JavaScript off.** The preview host answered a JavaScript-disabled
  context with `Your connection needs to be verified before you can proceed /
  Enable JavaScript and cookies to continue` instead of the store, so the
  no-JS behaviour of the toggle could not be observed at all. That is the
  preview URL's bot protection, not the theme.
- **`Buy with Shop`.** The express button sits directly under
  `ADD THE FULL FIT — £85` and shows no price of its own. Whether it carries the
  bundle or the single crewneck was not tested, because testing it means entering
  a Shop Pay checkout.
- **The sticky bar's `CHECKOUT NOW` with the set on.** Whether it carries the £85
  bundle or the £50 crewneck into checkout is unknown: in the preview, Shopify's
  own preview bar sits over that corner of the screen and swallowed every tap.
  Given the bar's label says `£50.00 · M`, this is the one remaining path worth
  confirming on a real theme.
- **The £135 combination.** Ticking the toggle on the shorts page while the
  standalone crewneck is already in the cart should produce a £50 crewneck line
  plus an £85 SET line. Both halves of that were observed separately; the
  combination itself was not run.

---

## Surprises

1. **A cart line that says "save £10" leads to a £95 cart.** Following
   `Complete the set — add the Cellblock Shorts, save £10.` and doing the obvious
   thing on the page it opens produces `Estimated total £95.00 GBP`,
   `total_discount: 0`, and no mention of the set anywhere.
2. **The store tells shoppers the shorts are sold out when they are not.** Tick
   the box before choosing your own size, pick any shorts size, and you get
   `Cellblock Shorts sold out in <SIZE> — pick another size` in red. All five
   sizes, every time — there were 19 shorts in M and 30 in S at the time. The
   panel is reporting "no size chosen yet" as "out of stock".
3. **The cart never confirms the £10.** `SPEC §3.13`'s bundle-in-cart state does
   not render at all, and the line item does not restate `£95`. After the button
   is pressed, the saving is never mentioned again.
4. **The sticky bar shows £50.00 next to a button that charges £85** — and on a
   phone the set's longer button label squeezes that text until it reads
   `CH…` / `£50.0` / `· M`. The sticky bar is the control a phone shopper
   actually uses.
5. **The set panel drops the pence.** `£95` and `£85` in a store that writes
   `£50.00`, `£45.00` and `£85.00` everywhere else, including in the cart the
   button leads to.
6. **`/products/cellblock-set` is public and reachable** (`/collections/sets`,
   linked from no menu) with a bare `SIZE` row for the crewneck, a crewneck-only
   hero image, no measurements and no size guide for either garment.
7. **A shopper picking a shorts size has no access to the shorts' measurements**
   without leaving the page; the thumbnail in the offer is not a link.
8. **`Added — 1 in bag` / `BAG [1]`** after buying two garments.
9. The panel's only stock sentence is a negative one. When the pairing is
   genuinely fine, the stock line is blank — including for the pairings with only
   four sets left.

## Missing

- The total (`£85`) in the collapsed line — the number that would make a shopper
  open the control is the one thing the control does not say until it is opened.
- The partner's price (`£45`) anywhere in the offer, so "Save £10" can be checked.
- Any restatement of the saving in the cart — no struck `£95`, no "saved £10".
- Measurements or a size guide for the partner garment, at the moment its size is
  being asked for.
- Any route to *browse* sets: `Sets` is in no menu, and the crewneck and shorts
  pages never link to `CELLBLOCK SET`. Search finds it; browsing never will.
- Any statement that this is **two garments** — "the full fit" is doing that job
  alone until the cart.
- Any offer to convert two separate halves already in the cart into the £85 set.
  With `CHARCOAL CELLBLOCK CREWNECK - M` and `CHARCOAL CELLBLOCK SHORTS - L`
  sitting in the cart in matching sizes at £95.00, the store says nothing.

## Contradictions

- `Cellblock Shorts sold out in M — pick another size` — while the same page's
  `MORE FROM THIS DROP` row shows `CHARCOAL CELLBLOCK SHORTS £45.00`, and the
  shorts page sells M perfectly happily.
- Sticky bar `CHARCOAL CELLBLOCK CREWNECK` / `£50.00 · M` — versus the button
  beside it in the same bar, `ADD THE FULL FIT — £85`, for two garments in sizes
  M and L.
- Panel prices `£95` / `£85` — versus `£50.00` on the same screen and `£85.00`
  in the cart it leads to.
- `SPEC §5`: ticking reveals "live partner stock" — versus a stock line that is
  empty for every buyable pairing, including 4-unit ones.
- `SPEC §3.13`: "the bundle in the cart → the saving confirmed in words" —
  versus no such section on the cart page at all.

## Works and must be protected

- **One line item, `£85.00`, reading `CELLBLOCK SET` /
  `CHARCOAL CELLBLOCK CREWNECK - M` / `CHARCOAL CELLBLOCK SHORTS - L`.** This is
  the best thing in the feature and the hardest part to get right. Do not let a
  cart redesign flatten those component lines into `M / L`.
- **The partner size row is headed with the partner's name**
  (`CELLBLOCK SHORTS SIZE` / `CELLBLOCK CREWNECK SIZE`), not "Size".
- **Untick restores everything** — button, variant id, price, and the shopper's
  own size selection, exactly as it was.
- **The mapping is right from both directions** — shorts S + crewneck XL from the
  shorts page produced the bundle's `XL / S`, with the sizes on the correct
  garments in the cart.
- **`£95` struck, `£85 for the set`** — the arithmetic shown, in words that say
  what the £85 buys.
- **On the shorts side the button itself becomes the instruction**
  (`Pick a Cellblock Crewneck size`, disabled). That is the pattern the crewneck
  side needs when a shopper ticks first.
- **No modal, no popup, no countdown, no "customers also bought".** One quiet
  line that stays collapsed. The restraint is the reason the offer is credible.
