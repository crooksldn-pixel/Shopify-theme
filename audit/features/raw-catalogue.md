# raw-catalogue — the register (homepage, `/collections/denim`, `/collections/all`)

Audited on the staging theme `202053779799`, GB market, iPhone-sized viewport
(390×844) unless a check says otherwise. Every string below is quoted exactly as
it appeared on screen.

The register renders 12 cards on the homepage and on `/collections/all`, 4 on
`/collections/denim`. Card format, verbatim from card one:
`NO. 01 / SWEATS / CHARCOAL CELLBLOCK CREWNECK / £50.00 / AVAILABLE`.

---

### Category filters — do they work, is the active state obvious

**Should:** filter the register by product type, client side, with the current
category obvious at a glance.

**Did:** _pending_

**Verdict:** _pending_

---

### The filter row is cut off on a phone — ACCESSORIES is off-screen with nothing to say so

**Should:** a shopper should be able to see every category on offer.

**Did:** on the homepage and on `/collections/all` the row of category buttons is
604px of content inside a 358px-wide scroller (`overflow-x: auto`). What a
shopper sees is `> ALL   T-SHIRT   DENIM   SW` — `SWEATS` is sliced through the
third letter and `ACCESSORIES` is entirely off-screen. There is no arrow, no
fade, no second line: the row ends at a clean vertical edge that reads as the
end of the list. The socks and the duffle bag — the whole accessories category,
three of the twelve products — are behind a horizontal swipe a shopper has no
reason to attempt.

**Verdict:** partly

**Shopper cost:** an entire category is invisible on the device most shoppers
use. `T-SHIRT` and `DENIM` look like the last two options.

**Evidence:** audit/screens/catalogue-A01-home-top.png,
audit/screens/catalogue-C02-all-fold.png — the row reads `> ALL  T-SHIRT
DENIM  SW` and stops.

---

### `Flat` / `On model` — the picture changes on every card, to the same wrong picture

**Should:** show each product on a model.

**Did:** the toggle works mechanically — pressing `ON MODEL` swaps the image on
all 12 cards, and pressing `FLAT` swaps them back. But every one of the 12 cards
swaps to **the same file**, `crooksldn-charcoal-cellblock-shorts.png`: a
full-length photo of a man in a black graphic tee and grey shorts, standing on a
perspex plinth. So in `ON MODEL`:

- `NO. 01 CHARCOAL CELLBLOCK CREWNECK £50.00` shows a man in a **tee and shorts**
  — the crewneck being sold is not in the picture.
- `NO. 03 BLUE WASH OG JEANS £60.00` shows the same man in the same **shorts**.
- `NO. 10 BLACK/BLUE MOTIONTEC™ SOCKS £6.00` shows the same man again; his socks
  are not visible.
- `NO. 12 LARGE DUFFLE BAG £18.00` — same man, no bag.

Not one card differs. Every cell carries `data-crk-has-model="placeholder"`,
so no product has a real model image and the section placeholder answers for all
twelve.

The sting: real model photography of the actual products is **already on the
store**. `BLUE WASH OG JEANS` has a model shot as its second product image — it
appears on the card on hover, a woman wearing those jeans — and the `ON MODEL`
view ignores it in favour of the shorts placeholder.

**Verdict:** broken

**Shopper cost:** the one control that promises "show me this worn" answers every
question with a photograph of a different garment. A shopper comparing the jeans
and the jorts on model sees two identical pictures of shorts and learns nothing;
a shopper who trusts it is being shown the wrong product.

**Evidence:** audit/screens/catalogue-B12-card1-onmodel.png (crewneck card
showing tee + shorts), audit/screens/catalogue-B12-card3-onmodel.png (jeans card,
same photo), audit/screens/catalogue-B12-card10-onmodel.png (socks card, same
photo), audit/screens/catalogue-C12-after-back.png (the jeans' own model image,
revealed on hover in `FLAT`).

---

### `Outline` toggle (O3) — the verdict

**Should:** an image treatment that makes products easier to read in the register.

**Did:** _pending_

**Verdict:** _pending_

---

### The `Outline` control exists only on the homepage — its effect does not

**Should:** _pending_

**Did:** _pending_

---

### Filter, open a product, come back with Back

**Should:** the filter survives the round trip.

**Did:** _pending_

---

### The status slot — does every card state stock

**Should:** every card states stock; the drop date sits beside it, never instead
of it.

**Did:** _pending_

---

### Sold-out items — can you tell before clicking

**Did:** _pending_

---

### Colourway swatches on cards

**Did:** _pending_

---

### Image, title and price as three separate targets

**Did:** _pending_

---

### A collection page: heading, and what a shopper reads before the cards

**Did:** _pending_

---

### How many products a shopper sees before scrolling, on a phone

**Did:** _pending_

---

## Surprises

_pending_

## Missing

_pending_

## Contradictions

_pending_

## Works and must be protected

_pending_
