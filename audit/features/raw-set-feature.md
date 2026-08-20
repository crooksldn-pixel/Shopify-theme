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

The shorts in M were not sold out. There were **19** of them. The message fires
for a shorts size whenever no crewneck size has been chosen yet, because the
lookup for "crewneck ? + shorts M" finds no pairing and the panel falls back to
its sold-out copy. Doing what it tells you — picking another size — produces the
same sentence with a different letter in it, for every size in the row.

While that sentence is on screen the buy button reads `SELECT A SIZE` and is
dead, so the shopper is holding two contradictory instructions ("this size is
gone" / "choose a size") and neither of them says the true one: *choose your own
size first*.

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

**Did:** with the set on and a valid pair chosen the sticky bar reads

> `CHARCOAL CELLBLOCK CREWNECK` / `£50.00 · M` / `ADD THE FULL FIT — £85` /
> `CHECKOUT NOW`

`£50.00` sits directly above a button that charges `£85`. The bar's product name
is still the crewneck alone. The page's own price line at the top of the record
also stays `£50.00` for as long as the set is on.

**Verdict:** partly

**Shopper cost:** the sticky bar is the control most likely to be used on a
phone, because it follows you down the page while the panel scrolls away. It is
the one surface that states a price and a size for the thing you are about to
buy, and while the set is on it states the wrong price and only half the sizes.

**Evidence:** `audit/screens/set-11b-about-to-add-viewport.png` plus the read-back
of `.crk-stickybar`

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
