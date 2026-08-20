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

**Did:** all five work, on the homepage and on `/collections/all`. Each one
narrowed the register correctly and the count above it followed:

| Tapped | Count | Products left standing |
|---|---|---|
| `ALL` | `12 ITEMS` | all twelve |
| `T-SHIRT` | `2 ITEMS` | MONEY CLIVE TEE, CRXST★RZ T-SHIRT |
| `DENIM` | `4 ITEMS` | both OG JEANS, both JORTS |
| `SWEATS` | `3 ITEMS` | CELLBLOCK CREWNECK, CELLBLOCK SHORTS, V2 BAGGIES |
| `ACCESSORIES` | `3 ITEMS` | both MOTIONTEC™ SOCKS, LARGE DUFFLE BAG |

The active state is unmistakable: the chosen button becomes a solid purple block
(`rgb(84, 37, 120)`) with a `>` prompt in front of the word — `> DENIM` — while
the rest stay plain text on black. No squinting needed.

The choice is also written into the address (`/collections/all?cat=DENIM`), and
loading that address cold reproduces the filtered view with `> DENIM` already
lit. A filtered link can be shared or bookmarked and it works.

**Verdict:** works

**Evidence:** audit/screens/catalogue-B20-filter-denim.png,
catalogue-B20-filter-t-shirt.png, catalogue-B20-filter-sweats.png,
catalogue-B20-filter-accessories.png, catalogue-D41-cold-load-filtered.png

---

### Filtering to an odd number of products leaves a purple slab where a product should be

**Should:** a filtered register shows the products and nothing else.

**Did:** the grid's 1px rules are made by letting a purple ground show between
the cards. When a filter leaves a count that does not fill the last row, that
ground shows through the empty slot as a **solid lavender rectangle the exact
size of a product card**. Tapping `SWEATS` (3 items) or `ACCESSORIES` (3 items)
on a phone produces one; on a 1440px screen the grid is four across, so
`ACCESSORIES` leaves the same slab and `T-SHIRT` (2 items) leaves two slots of it.

Nothing else on the site is a solid block of colour that size. It reads as a
product whose image failed, or as something withheld.

**Verdict:** broken

**Shopper cost:** the shopper who narrows to the category they want is the most
committed shopper on the site, and the register answers by showing them one
broken-looking tile next to three real ones.

**Evidence:** audit/screens/catalogue-B20-filter-accessories.png,
catalogue-B20-filter-sweats.png, catalogue-E03-desktop-odd-count.png

---

### Three different kinds of control, dressed identically

**Should:** a shopper can tell "which view", "picture treatment" and "which
category" apart.

**Did:** the homepage stacks three rows of buttons that share one class and one
look. At rest a shopper sees `> FLAT`, `> OUTLINE` and `> ALL` all lit purple at
once, in the same box, in the same type, with no labels and no grouping. It reads
as one filter bar with three filters already applied — and `OUTLINE`, alone on
its row, reads like a category the shop sells.

**Verdict:** partly

**Shopper cost:** the first read of the register is "something is already
filtered", which is exactly wrong — all twelve products are showing.

**Evidence:** audit/screens/catalogue-A10-outline-default-cards.png — three
purple blocks stacked: `> FLAT`, `> OUTLINE`, `> ALL`.

---

### The filter row is cut off on a phone — ACCESSORIES is off-screen with nothing to say so

**Should:** a shopper can see every category on offer.

**Did:** the category row is 604px of content inside a 358px scroller. A phone
shows `> ALL   T-SHIRT   DENIM   SW` — `SWEATS` sliced through its third letter,
and `ACCESSORIES` (measured at 449–611px, so starting 91px past the right edge)
not visible at all. No arrow, no fade, no wrap: the row ends on a clean vertical
rule that reads as the end of the list. Swiping the row does work. Nothing
suggests swiping it.

**Verdict:** partly

**Shopper cost:** a whole category — the socks and the duffle bag, three of
twelve products — is invisible on the device most people shop on. `DENIM` looks
like the last category in the shop.

**Evidence:** audit/screens/catalogue-A01-home-top.png,
catalogue-C02-all-fold.png, catalogue-D20-filterrow-asfound.png

---

### `Flat` / `On model` — the picture changes on every card, to the same wrong picture

**Should:** show each product on a model.

**Did:** the toggle works mechanically. `ON MODEL` swaps the image on all 12
cards and `FLAT` swaps them back; not one card fails to change. But all twelve
swap to **the same file** — `crooksldn-charcoal-cellblock-shorts.png`, a
full-length photo of a man in a black graphic tee and grey shorts on a perspex
plinth. In `ON MODEL`:

- `NO. 01 CHARCOAL CELLBLOCK CREWNECK £50.00` — a man in a **tee and shorts**.
  The crewneck being sold is not in the picture.
- `NO. 03 BLUE WASH OG JEANS £60.00` — same man, same shorts. No jeans.
- `NO. 10 BLACK/BLUE MOTIONTEC™ SOCKS £6.00` — same man. His socks are not visible.
- `NO. 12 LARGE DUFFLE BAG £18.00` — same man. No bag.

Every cell carries `data-crk-has-model="placeholder"`, so no product has a real
model image and the section placeholder answers for all twelve. On screen, the
first four cards are four copies of one photograph.

The sting: model photography of the actual products already exists on the store.
`BLUE WASH OG JEANS` carries a model shot as its **second product image** — on a
desktop hover the card swaps to it, a person wearing those jeans — and `ON MODEL`
ignores it in favour of the shorts placeholder.

**Verdict:** broken

**Shopper cost:** the one control that promises "show me this worn" answers every
question with a photograph of a different garment. Comparing the jeans against
the jorts on model gives two identical pictures of shorts. A shopper who believes
the picture is being shown the wrong product at the moment they are deciding.

**Evidence:** audit/screens/catalogue-B11-onmodel-controls.png (cards 1–4, four
copies of one photo), catalogue-B12-card1-onmodel.png (crewneck card showing tee
and shorts), catalogue-B12-card3-onmodel.png (jeans card, same photo),
catalogue-B12-card10-onmodel.png (£6 socks card, same photo),
catalogue-C12-after-back.png (the jeans' own model image, on hover, in `FLAT`).

---

### `Outline` (O3) — the verdict

**Should:** an image treatment that makes products easier to read in the
register. O3 says the aesthetic call is pending; this is the call, judged as a
shopper deciding whether to buy rather than as taste.

**What it is:** a 1px cream (`rgb(221, 215, 201)`) keyline drawn right around the
product cut-out — four stacked drop-shadows, one per direction. It is **on by
default** (`data-crk-outline-default="on"`, button starts `aria-pressed="true"`)
and it applies to the product page's main image too, not only the register.

**Did:** three things a shopper would notice.

**1. It invents a garment detail that is not on the garment.** On
`CHARCOAL CELLBLOCK SHORTS` the keyline traces the waistband, both side seams and
the hem, and reads as cream binding — worse because the shorts have a real
lighter hem, so the drawn line lands on a real one and thickens it. On
`CHARCOAL CELLBLOCK CREWNECK` it traces collar, cuffs and hem: a crewneck that
looks trimmed in cream. On both blue washes it runs down the outseam like white
piping. Turn it off and all four are plainly what they are. That is a
misdescription of the exact attribute a clothing shopper decides on, and because
it is on by default it is the normal state of the shop.

**2. Where it genuinely helps, the help is small.** `LARGE DUFFLE BAG` and
`BLACK/BLUE MOTIONTEC™ SOCKS` are black products on a near-black card panel
(`rgb(14, 12, 19)`). With the outline they are crisper. Without it they are
dimmer but entirely readable — the bag's white `CROOKS LONDON` badge and its own
top-light hold the shape, and the socks' grey and blue panels do the same.
Nothing became unbuyable. And on the white product, `WHITE/RED MOTIONTEC™
SOCKS`, the cream line does nothing at all.

**3. In light mode the control is inert.** Switched to light mode, `> OUTLINE`
on and `OUTLINE` off are pixel-identical — a cream keyline on a white ground is
invisible. The button still lights up purple when pressed, so a shopper in light
mode presses a control that visibly does nothing.

**Verdict:** partly — it is not doing nothing, and what it does is worth less
than what it costs. It buys a marginal gain on two of twelve products and pays
for it by drawing fake trim on at least six, in the default state, all the way
through to the product page.

**Shopper cost:** a shopper reads "charcoal sweats with cream binding" and "blue
jeans with white piping" off the register and off the product page. Neither
exists. That is the kind of gap that comes back as a return.

**Recommendation, inside the design law:** default it off, or take the control
out. If the point was to stop black products dissolving into the card, fix the
card, not the garment — the media panel is already a separate 1px-bordered box,
and lifting that panel one step off the page ground separates a black product
without drawing on it. No radius, no shadow, no gradient, no new colour.

**Evidence — same cards, treatment on then off:**
audit/screens/catalogue-A10a-card1-outline-default.png vs
catalogue-A11a-card1-outline-toggled.png (crewneck);
catalogue-A10b-card2-outline-default.png vs
catalogue-A11b-card2-outline-toggled.png (shorts — the clearest case);
catalogue-B09-card10-outline-ON.png vs catalogue-B2OFF-card10.png (black socks);
catalogue-B011-card12-outline-ON.png vs catalogue-B2OFF-card12.png (duffle);
catalogue-B22-grid-outline-on.png vs catalogue-B21-grid-outline-off.png (the grid
at real browse size); catalogue-D10-light-outline-on.png vs
catalogue-D12-light-outline-off.png and catalogue-D11-light-duffle-outline-on.png
vs catalogue-D13-light-duffle-outline-off.png (light mode — identical);
catalogue-D14-pdp-image-outline-on.png (the treatment on the product page).

---

### The `Outline` control lives on the homepage only; its effect lives everywhere

**Should:** if a treatment applies to a page, the shopper can change it there.

**Did:** the homepage control bar reads `FLAT / ON MODEL / OUTLINE / ALL /
T-SHIRT / DENIM / SWEATS / ACCESSORIES`. On `/collections/all` and
`/collections/denim` the same bar reads `FLAT / ON MODEL / ALL / T-SHIRT / DENIM
/ SWEATS / ACCESSORIES` — no `OUTLINE` — while the outline is still drawn on
every card there and on every product page.

**Verdict:** partly

**Shopper cost:** a shopper who arrives on a collection page — the `CATALOGUE`
link, a search result, a shared link — sees the treatment and has no way to turn
it off; one who turned it off on the homepage cannot turn it back on without
going home.

**Evidence:** audit/screens/catalogue-C01-denim-fold.png (denim page: only
`> FLAT` / `ON MODEL`), catalogue-B40-collection-outline-off.png

---

### Apply a filter, open a product, come back with Back

**Should:** the filter survives the round trip.

**Did:** it does, cleanly. Tapping `DENIM` on `/collections/all` rewrote the
address to `…/collections/all?cat=DENIM`, left 4 of 12 cards standing and the
count reading `4 ITEMS`. Opening `BLUE WASH OG JEANS` and pressing the browser's
Back button returned to `…/collections/all?cat=DENIM` with `> DENIM` still lit,
still four cards, still `4 ITEMS`. Nothing had to be re-tapped.

One small loss: the page comes back scrolled to the top (`window.scrollY === 0`),
not to the card that was opened.

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
`CHARCOAL CELLBLOCK CREWNECK` product page, and a browser Back to the collection
all rendered with the outline off. Returning to the homepage the button was still
`aria-pressed="false"` and the cards were still plain.

**Verdict:** works

**Evidence:** audit/screens/catalogue-B40-collection-outline-off.png,
catalogue-B41-home-outline-persisted.png

---

### The status slot — does every card always state stock

**Should:** every card states stock; the drop date is beside it, never instead of
it.

**Did:** all twelve cards state stock. Read off the cards:

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

**No card breaks the rule.** Price and status share one line — `£25.00` in 22px
cream on the left, `AVAILABLE` in 9px purple on the right. The one card carrying
a drop date, `NO. 08 CRXST★RZ T-SHIRT`, keeps `AVAILABLE` where it belongs and
puts `DROPPED 03.08` on its own line 3px underneath, same 9px size but in a
muted grey (`rgb(138, 131, 119)` against the status's `rgb(167, 122, 199)`), in
a separate `crk-card__dropped` element. It is plainly an addition, never a
replacement, and never a badge. `V2 BAGGIES` is the only card whose stock is
anything other than plain availability, and it says `2 OF 5 SIZES LEFT` on the
card before any click.

Same on `/collections/all` and `/collections/denim`.

**Verdict:** works — protect it.

**Evidence:** audit/screens/catalogue-B20-filter-sweats.png (V2 BAGGIES card
reading `£60.00` / `2 OF 5 SIZES LEFT`), catalogue-F08-card8.png,
catalogue-F10-cards-7-to-10.png, plus the card strings above.

---

### Sold-out items — can you tell before clicking

**Should:** a sold-out product is obvious in the register.

**Did:** **could not be tested as a shopper — nothing in the register is sold
out.** Every one of the twelve cards states `AVAILABLE` or `2 OF 5 SIZES LEFT`;
no sold-out card appeared on the homepage, `/collections/all` or
`/collections/denim`. (Checked against the store: 13 active products, none with
every variant at zero.) The closest real case is `V2 BAGGIES`, where three of
five sizes are gone, and its card does say `2 OF 5 SIZES LEFT` before a click,
which is the behaviour that matters.

**Verdict:** untested — a state that does not currently exist in the catalogue,
not a defect found.

---

### Colourway swatches on cards

**Should:** if a card shows colours, tapping one should do something with that
colour.

**Did:** two cards carry them — `MONEY CLIVE TEE` and `CRXST★RZ T-SHIRT`. What a
sighted shopper sees is two 12×12px squares under the product name, one black,
one white, each with a 1px border and no caption. They look exactly like the
colour chips a shopper taps everywhere else on the web. (The words
`Colourways: Black, White` exist only in a screen-reader-only span; the visible
card carries no label.)

Tapping the **white** square on `MONEY CLIVE TEE` opened
`/products/evil-clive-tee` — the product page with no variant chosen, which
presents the tee in black. The swatch is not a control at all: it is decoration
inside the card's link (`<span class="crk-card__sw" aria-hidden="true">`, no
role, no tab stop, no label of its own). Tapping the black square does the same
thing.

**Verdict:** partly — they open the product, so nothing is dead, but the colour
the shopper picked is silently dropped.

**Shopper cost:** the shopper who taps white to see the white tee lands on the
black one and has to find the colour control again on the product page. Small,
but it is a promise the card makes and does not keep.

**Evidence:** audit/screens/catalogue-D00-swatch-card.png,
catalogue-D01b-after-swatch-tap.png — tap on the white swatch →
`/products/evil-clive-tee`, no variant in the address.

---

### Image, title and price as three separate targets

**Should:** all three open the product.

**Did:** all three do. The whole card is one `<a href="/products/…">`, so clicking
the picture, clicking `CHARCOAL CELLBLOCK CREWNECK` and clicking `£50.00` each
landed on `/products/charcoal-cellblock-crewneck`. The image target alone is
152×152px, the title 152×34px — big, forgiving targets on a phone.

**Verdict:** works

**Evidence:** three separate clicks logged to the same product URL; card markup
`<a class="crk-card" href="/products/charcoal-cellblock-crewneck">` wrapping top
line, media, name, price and status.

---

### A collection page: is there a real heading, and does it open straight onto cards

**Should:** a heading a shopper reads, and something to orient them before the
grid.

**Did:** the heading is real and large. `/collections/denim` renders
`<h1>DENIM</h1>` with `4 ITEMS` beside it; `/collections/all` renders
`<h1>ALL</h1>` with `12 ITEMS`. One `h1` per page, immediately under the header.
No complaints there.

The page then goes **straight** into product cards. Everything a shopper reads on
`/collections/denim` before the first card is:

```
DENIM
4 ITEMS
FLAT
ON MODEL
```

Nothing else. Not a sentence about what the collection is.

And this is not the known "collections with no description" item: **the Denim
collection has a description in admin — `Jorts, jeans and denim.` — and the
register never renders it.** There is no slot for a collection description in the
section at all, so the eight outstanding collection descriptions in the SEO plan
would put zero words on the page as things stand.

**Verdict:** partly — heading works, description is dropped on the floor.

**Shopper cost:** small on `/collections/denim`, where four pairs of jeans
explain themselves. Real on the owner's side: copy that has been written is
invisible, and writing more will not change that.

**Evidence:** audit/screens/catalogue-C01-denim-fold.png,
catalogue-C02-all-fold.png; admin `descriptionHtml` for `denim` reads
`Jorts, jeans and denim.`

---

### How many products a shopper sees before scrolling, on a phone

**Should:** land a shopper on the goods.

**Did:** measured on a 390×844 phone viewport, whole cards on screen at rest:

| Page | Whole cards before any scroll | First card starts at |
|---|---|---|
| Homepage | **0** | 757px down an 844px screen |
| `/collections/all` | **2** (plus the top strip of two more) | 376px |
| `/collections/denim` | **2** (plus the top strip of two more) | 304px |

On the homepage a shopper sees no product at all before scrolling. The first
screen holds the shipping bar, the header, the status line `> 12 PRODUCTS
AVAILABLE TO PURCHASE`, the `CROOKSLDN / OWN THE STREETS™` hero with its
`CATALOGUE` button, the `CATALOGUE / 12 ITEMS` heading — and then three stacked
rows of controls (`FLAT / ON MODEL`, `OUTLINE`, and the category row) which push
the grid off the bottom. All that clears the fold is an 87px sliver reading
`NO. 01 SWEATS` and `NO. 02 SWEATS`. No image, no name, no price.

The collection pages are much better: two complete cards with picture, name,
price and stock, and enough of the next row to prove there is more.

**Verdict:** partly

**Shopper cost:** on the homepage the three control rows cost the shopper the
entire first screen of product. Controls are for a shopper who has already seen
the goods; they are placed ahead of them.

**Evidence:** audit/screens/catalogue-A01-home-top.png (homepage — nothing below
the controls but a sliver of two card headers), catalogue-C02-all-fold.png,
catalogue-C01-denim-fold.png

---

## Surprises

- **`ON MODEL` shows one photograph of a man in charcoal shorts on all twelve
  cards** — on the £6 socks, on the duffle bag, on both pairs of jeans. It is not
  "some products lack a model shot": no product has one, and the stand-in is a
  picture of a different product.
- **Real model photography is already on the store and the toggle ignores it.**
  `BLUE WASH OG JEANS` has a model shot as its second image; it shows on hover in
  `FLAT` and is not what `ON MODEL` uses.
- **Filtering to a category with an odd count leaves a solid lavender slab the
  size of a card** in the grid — visible on `SWEATS` and `ACCESSORIES` on a phone,
  and on `T-SHIRT` and `ACCESSORIES` on desktop.
- **The Denim collection's description is written and stored and the theme has
  nowhere to put it.** So does every other collection description, written or
  not.
- **`ACCESSORIES` is off the right edge of the phone's category row** with
  nothing indicating the row scrolls — a third of the catalogue behind an
  unadvertised swipe.
- **`Outline` is on by default, applies to product pages too, and cannot be
  turned off from any page except the homepage.**
- **In light mode `Outline` does nothing** — both states are pixel-identical —
  but the button still lights up when pressed.
- **The card number is a position, not a product's number.** `GREY WASH JORTS` is
  `NO. 06` on the homepage and `NO. 01` on `/collections/denim`. In a register
  that presents itself as an evidence log, the case number moves.
- **On the homepage a shopper sees zero products before scrolling.**

## Missing

- Any collection description on any collection page — no slot exists.
- Any hint that the category row continues past the right edge of a phone.
- The `OUTLINE` control on collection pages, where the treatment still applies.
- Any effect from a colourway swatch: tapping the white chip does not get you the
  white tee.
- Return to the shopper's place in the list after Back — the filter survives, the
  scroll position does not.
- A sold-out card state that could be observed at all; nothing in the catalogue
  is currently sold out, so the register's most important status has never been
  seen in the wild.

## Contradictions

- The two colourway cards spell the same thing two ways, in the same register,
  eight cards apart: `NO. 07 MONEY CLIVE TEE — Colourways: BLACK, WHITE` against
  `NO. 08 CRXST★RZ T-SHIRT — Colourways: Black, White`.
- The same product carries two case numbers: `GREY WASH JORTS` is `NO. 06` on the
  homepage register and `NO. 01` on `/collections/denim`.
- Filtering `/collections/all` to denim leaves the heading reading `ALL` while
  the count beside it reads `4 ITEMS` and only denim is on screen.
- The register (and the product page) draw cream trim on garments that the
  garments do not have — the pictures contradict the goods.

## Works and must be protected

- **The status slot.** Twelve of twelve cards state stock in plain English;
  `DROPPED 03.08` is an addition beside `AVAILABLE`, never a replacement.
  `2 OF 5 SIZES LEFT` tells a shopper the truth before they click.
- **Filters and their counts.** All five correct, counts follow, and the choice
  is written into the address so a filtered link survives Back, a bookmark and a
  share.
- **The active-state styling.** A filled purple block with a `>` prompt — nobody
  will wonder which category is on.
- **Outline persistence.** Turn it off once and it stays off across collections,
  product pages and Back.
- **One `h1` per collection page**, large, first thing, matching the collection.
- **The whole card is one link.** Picture, title and price all open the product,
  with 152px-wide targets.
- **No fake urgency anywhere in the register** — no counters, no timers, no
  "only 2 left" theatre. `2 OF 5 SIZES LEFT` is real inventory.
