# raw-catalogue — the register (homepage, `/collections/denim`, `/collections/all`)

Staging theme `202053779799`, GB market, iPhone-sized viewport (390×844) unless a
check says otherwise. Every string below is quoted exactly as it appeared.

The register renders 12 cards on the homepage and on `/collections/all`, 4 on
`/collections/denim`. Card format, verbatim from card one:
`NO. 01 / SWEATS / CHARCOAL CELLBLOCK CREWNECK / £50.00 / AVAILABLE`.

---

### Category filters

**Should:** filter the register by product type, client side, with the active
category obvious at a glance.

**Did:** all five work, on the homepage and on `/collections/all`. Every one
narrowed the register correctly and the count above it followed:

| Tapped | Count shown | Products left standing |
|---|---|---|
| `ALL` | `12 ITEMS` | all twelve |
| `T-SHIRT` | `2 ITEMS` | MONEY CLIVE TEE, CRXST★RZ T-SHIRT |
| `DENIM` | `4 ITEMS` | both OG JEANS, both JORTS |
| `SWEATS` | `3 ITEMS` | CELLBLOCK CREWNECK, CELLBLOCK SHORTS, V2 BAGGIES |
| `ACCESSORIES` | `3 ITEMS` | both MOTIONTEC™ SOCKS, LARGE DUFFLE BAG |

The active state is unmistakable: the chosen button becomes a solid purple block
(`rgb(84, 37, 120)`) with a `>` prompt in front of the word — `> DENIM` — while
every other stays plain text on black. No squinting required.

**Verdict:** works

**Evidence:** audit/screens/catalogue-B20-filter-denim.png,
catalogue-B20-filter-t-shirt.png, catalogue-B20-filter-sweats.png,
catalogue-B20-filter-accessories.png

---

### Three different kinds of control, dressed identically

**Should:** a shopper should be able to tell "which view", "picture treatment"
and "which category" apart.

**Did:** on the homepage the register stacks three rows of buttons that share one
class and one look. At rest the page shows `> FLAT`, `> OUTLINE` and `> ALL` all
lit purple at the same time, in the same box, in the same type. Nothing labels
the rows, nothing groups them. It reads as one filter bar with three filters
already applied — and `OUTLINE`, alone on its row, reads like a category the
shop sells.

**Verdict:** partly

**Shopper cost:** the shopper's first read of the register is "something is
already filtered", which is exactly wrong — all twelve products are showing.

**Evidence:** audit/screens/catalogue-A10-outline-default-cards.png — three
purple blocks stacked, `> FLAT`, `> OUTLINE`, `> ALL`.

---

### The filter row is cut off on a phone — ACCESSORIES is off-screen with nothing to say so

**Should:** a shopper should be able to see every category on offer.

**Did:** the row of category buttons is 604px of content inside a 358px scroller.
What a phone shows is `> ALL   T-SHIRT   DENIM   SW` — `SWEATS` sliced through
its third letter, and `ACCESSORIES` (measured at 449–611px, i.e. beginning 91px
beyond the right edge) entirely absent. There is no arrow, no fade, no wrap: the
row ends on a clean vertical rule that reads as the end of the list. Swiping the
row does work; nothing suggests swiping it.

**Verdict:** partly

**Shopper cost:** a whole category — the socks and the duffle bag, three of
twelve products — is invisible on the device most people shop on. `DENIM` looks
like the last category in the shop.

**Evidence:** audit/screens/catalogue-A01-home-top.png,
audit/screens/catalogue-C02-all-fold.png

---

### `Flat` / `On model` — the picture changes on every card, to the same wrong picture

**Should:** show each product on a model.

**Did:** the toggle works mechanically. Pressing `ON MODEL` swaps the image on
all 12 cards; pressing `FLAT` swaps them back. Not one card fails to change. But
every one of the twelve swaps to **the same file** —
`crooksldn-charcoal-cellblock-shorts.png`, a full-length photo of a man in a
black graphic tee and grey shorts on a perspex plinth. In `ON MODEL`:

- `NO. 01 CHARCOAL CELLBLOCK CREWNECK £50.00` — a man in a **tee and shorts**.
  The crewneck being sold is not in the picture.
- `NO. 03 BLUE WASH OG JEANS £60.00` — same man, same shorts. No jeans.
- `NO. 10 BLACK/BLUE MOTIONTEC™ SOCKS £6.00` — same man. His socks are not visible.
- `NO. 12 LARGE DUFFLE BAG £18.00` — same man. No bag.

Every cell carries `data-crk-has-model="placeholder"`: no product has a real
model image, so the section placeholder answers for all twelve. The first four
cards side by side are four copies of one photograph.

The sting: model photography of the actual products already exists on the store.
`BLUE WASH OG JEANS` carries a model shot as its **second product image** — it
appears on the card on hover, a person wearing those jeans — and `ON MODEL`
ignores it in favour of the shorts placeholder.

**Verdict:** broken

**Shopper cost:** the one control that promises "show me this worn" answers every
question with a photograph of a different garment. Comparing the jeans against
the jorts on model produces two identical pictures of shorts. A shopper who
believes the picture is being shown the wrong product.

**Evidence:** audit/screens/catalogue-B11-onmodel-controls.png (cards 1–4, four
copies of one photo), catalogue-B12-card1-onmodel.png (crewneck card showing tee
and shorts), catalogue-B12-card3-onmodel.png (jeans card, same photo),
catalogue-B12-card10-onmodel.png (£6 socks card, same photo),
catalogue-C12-after-back.png (the jeans' own model image, on hover, in `FLAT`).

---

### `Outline` (O3) — the verdict

**Should:** an image treatment that makes products easier to read in the register.
O3 says the decision is pending, so this is the decision, judged on whether it
helps someone deciding to buy.

**What it does:** it draws a 1px cream (`rgb(221, 215, 201)`) keyline right
around the product cut-out — four stacked drop-shadows, one per direction. It is
**on by default** (`data-crk-outline-default="on"`, the button starts
`aria-pressed="true"`).

**Did:** on the products that need help it does help, and on everything else it
invents a design detail that the garment does not have.

- `LARGE DUFFLE BAG` and `BLACK/BLUE MOTIONTEC™ SOCKS` are black products on a
  near-black card panel (`rgb(14, 12, 19)`). With the outline on, their
  silhouettes are crisp. With it off they are dimmer — but still perfectly
  readable: the bag's white `CROOKS LONDON` badge, its own top-light and the
  socks' grey and blue panels carry the shape. Nothing became unbuyable.
- On `CHARCOAL CELLBLOCK SHORTS` the keyline traces the waistband, both side
  seams and the hem. It reads as **cream binding on the garment**. The shorts do
  have a real lighter hem, so the fake line lands right on top of a real one and
  thickens it.
- On `CHARCOAL CELLBLOCK CREWNECK` the same line traces collar, cuffs and hem —
  a crewneck that looks trimmed in cream. It is not.
- On both blue washes the line runs down the outseam and around the hem like
  white piping.
- On `WHITE/RED MOTIONTEC™ SOCKS` — a white product — it does nothing at all.

So the treatment's benefit falls on two of twelve products, and its cost falls on
at least six: it changes the apparent trim and edge colour of the garment, which
is precisely the attribute a clothing shopper decides on.

**Verdict:** partly — it is doing something real, and what it does is misdescribe
the product. Judged as a purchase decision, that is a cost, not a benefit, and
the fact that it is **on by default** means the register's normal state is the
one that shows the fake trim.

**Shopper cost:** a shopper reads "charcoal sweats with cream binding" and
"blue jeans with white piping" off the register. Neither exists.

**Recommendation, inside the design law:** default it off, or drop the control.
If the point was to stop black products dissolving into the card, the fix is on
the card, not on the garment — the media panel is already a separate 1px-bordered
box, and lifting that panel one step off the page ground separates a black
product without drawing on it. That needs no radius, no shadow, no gradient and
no new colour.

**Evidence, same cards, treatment on then off:**
audit/screens/catalogue-A10a-card1-outline-default.png vs
catalogue-A11a-card1-outline-toggled.png (crewneck);
catalogue-A10b-card2-outline-default.png vs
catalogue-A11b-card2-outline-toggled.png (shorts — clearest case);
catalogue-B09-card10-outline-ON.png vs catalogue-B2OFF-card10.png (black socks);
catalogue-B011-card12-outline-ON.png vs catalogue-B2OFF-card12.png (duffle);
catalogue-B22-grid-outline-on.png vs catalogue-B21-grid-outline-off.png (the
grid at real browse size).

---

### The `Outline` control lives on the homepage only; its effect lives everywhere

**Should:** if a treatment applies to a page, the shopper can change it on that
page.

**Did:** the homepage control bar reads `FLAT / ON MODEL / OUTLINE / ALL /
T-SHIRT / DENIM / SWEATS / ACCESSORIES`. On `/collections/all` and
`/collections/denim` the same bar reads `FLAT / ON MODEL / ALL / T-SHIRT / DENIM
/ SWEATS / ACCESSORIES` — no `OUTLINE` button — while the outline is still drawn
on every card there.

**Verdict:** partly

**Shopper cost:** a shopper who arrives on a collection page (the `CATALOGUE`
link, a search result, a shared link) sees the treatment and has no way to turn
it off; a shopper who turned it off on the homepage has no way to turn it back on
without returning there.

**Evidence:** audit/screens/catalogue-C01-denim-fold.png (denim page: only
`> FLAT` / `ON MODEL`), catalogue-B40-collection-outline-off.png

---

### Apply a filter, open a product, come back with Back

**Should:** the filter survives the round trip.

**Did:** it does, cleanly. Tapping `DENIM` on `/collections/all` rewrote the
address to `…/collections/all?cat=DENIM`, left 4 of 12 cards standing and the
count reading `4 ITEMS`. Opening `BLUE WASH OG JEANS`, then pressing the
browser's Back button, returned to `…/collections/all?cat=DENIM` with `> DENIM`
still lit, still four cards, still `4 ITEMS`. Nothing had to be re-tapped.

One small loss: the page comes back scrolled to the very top
(`window.scrollY === 0`), not to the card that was opened. With four to twelve
cards that costs a flick; with a bigger catalogue it would cost more.

**Verdict:** works

**Evidence:** audit/screens/catalogue-C10-all-filtered.png (before),
catalogue-C11-product-opened.png, catalogue-C12-after-back.png (after Back —
`> DENIM` still lit, `4 ITEMS`).

---

### Toggle Outline, navigate away, come back

**Should:** the choice persists.

**Did:** it persists everywhere and survives Back. Turning `OUTLINE` off on the
homepage set `crk-outline = off` in session storage and stamped
`data-crk-outline="off"` on the page; from there `/collections/all`, the
`CHARCOAL CELLBLOCK CREWNECK` product page and a browser Back to the collection
all rendered with the outline off. Returning to the homepage, the button was
still `aria-pressed="false"` and the cards were still plain.

**Verdict:** works

**Evidence:** audit/screens/catalogue-B40-collection-outline-off.png,
catalogue-B41-home-outline-persisted.png

---

### The status slot — does every card always state stock

**Should:** every card states stock; the drop date sits beside it, never instead
of it.

**Did:** all twelve cards state stock. Read from the cards themselves:

| # | Product | Status slot |
|---|---|---|
| 01 | CHARCOAL CELLBLOCK CREWNECK | `AVAILABLE` |
| 02 | CHARCOAL CELLBLOCK SHORTS | `AVAILABLE` |
| 03 | BLUE WASH OG JEANS | `AVAILABLE` |
| 04 | BLUE WASH JORTS | `AVAILABLE` |
| 05 | GREY WASH OG JEANS | `AVAILABLE` |
| 06 | GREY WASH JORTS | `AVAILABLE` |
| 07 | MONEY CLIVE TEE | `AVAILABLE` |
| 08 | CRXST★RZ T-SHIRT | `AVAILABLE` + `DROPPED 03.08` |
| 09 | V2 BAGGIES | `2 OF 5 SIZES LEFT` |
| 10 | BLACK/BLUE MOTIONTEC™ SOCKS | `AVAILABLE` |
| 11 | WHITE/RED MOTIONTEC™ SOCKS | `AVAILABLE` |
| 12 | LARGE DUFFLE BAG | `AVAILABLE` |

No card breaks the rule. The one card carrying a drop date — `NO. 08` — carries
it **in addition to** `AVAILABLE`, not instead of it. `V2 BAGGIES` is the only
card whose stock is anything other than plain availability and it says so in
plain English on the card, before any click.

The same holds on `/collections/all` and `/collections/denim`.

**Verdict:** works — protect it.

**Evidence:** _shot pending_ — plus the card strings above.

---

### Sold-out items — can you tell before clicking

**Should:** a sold-out product is obvious in the register.

**Did:** **this could not be tested as a shopper: nothing in the register is sold
out.** Every one of the twelve cards states `AVAILABLE` or `2 OF 5 SIZES LEFT`;
no card showed a sold-out state anywhere on the homepage, `/collections/all` or
`/collections/denim`. The closest real case is `V2 BAGGIES`, where three of five
sizes are gone — and the card says `2 OF 5 SIZES LEFT` before a shopper clicks,
which is the behaviour that matters.

**Verdict:** untested — not a defect found, a state that does not currently exist
in the catalogue.

---

### Colourway swatches on cards

**Did:** _pending_

---

### Image, title and price as three separate targets

**Did:** _pending_

---

### A collection page: is there a real heading, and does it open straight onto cards

**Should:** a heading a shopper reads, and something to orient them before the
grid.

**Did:** the heading is real and large. `/collections/denim` renders
`<h1>DENIM</h1>` with `4 ITEMS` beside it; `/collections/all` renders
`<h1>ALL</h1>` with `12 ITEMS`. One `h1` per page, first thing under the header.
No complaints there.

The page then goes **straight** into product cards. Everything a shopper reads on
`/collections/denim` before the first card is:

```
DENIM
4 ITEMS
FLAT
ON MODEL
```

Nothing else. No sentence about what the collection is.

And this is not the known "collections with no description" item: **the Denim
collection has a description in admin — `Jorts, jeans and denim.` — and the
register never renders it.** The theme has no slot for a collection description
at all, so the eight outstanding collection descriptions in the SEO plan would
put zero words on the page as things stand.

**Verdict:** partly — heading works, description is dropped on the floor.

**Shopper cost:** small on `/collections/denim`, where four pairs of jeans
explain themselves. Real on the owner's side: copy that has been written and paid
for is invisible, and writing more will not change that.

**Evidence:** audit/screens/catalogue-C01-denim-fold.png,
catalogue-C02-all-fold.png

---

### How many products a shopper sees before scrolling, on a phone

**Should:** land a shopper on the goods.

**Did:** measured on a 390×844 phone viewport, cards fully on screen at rest:

| Page | Whole cards visible before any scroll | First card starts at |
|---|---|---|
| Homepage | **0** | 757px down an 844px screen |
| `/collections/all` | **2** (plus the top strip of 2 more) | 376px |
| `/collections/denim` | **2** (plus the top strip of 2 more) | 304px |

On the homepage a shopper sees no product at all before scrolling. What fits on
the first screen is the shipping bar, the header, the status line
`> 12 PRODUCTS AVAILABLE TO PURCHASE`, the `CROOKSLDN / OWN THE STREETS™` hero
with its `CATALOGUE` button, the `CATALOGUE / 12 ITEMS` heading, and then three
stacked rows of controls — `FLAT / ON MODEL`, `OUTLINE`, and the category row —
which push the grid off the bottom. All that clears the fold is an 87px sliver
containing the words `NO. 01 SWEATS` and `NO. 02 SWEATS`. No image, no product
name, no price.

The collection pages are much better: two complete cards with picture, name,
price and stock, and enough of the next row to make it obvious there is more.

**Verdict:** partly

**Shopper cost:** on the homepage the three control rows cost the shopper the
entire first screen of product. The controls are for a shopper who has already
seen the goods; they are placed ahead of them.

**Evidence:** audit/screens/catalogue-A01-home-top.png (homepage, nothing but a
sliver of two card headers at the bottom), catalogue-C02-all-fold.png,
catalogue-C01-denim-fold.png

---

## Surprises

_pending_

## Missing

_pending_

## Contradictions

_pending_

## Works and must be protected

_pending_
