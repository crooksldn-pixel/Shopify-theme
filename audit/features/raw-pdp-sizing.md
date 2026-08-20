# raw-pdp-sizing — measurements, the size guide, and finding shipping & returns from a PDP

Phone (390×844), GB market, staging theme `202053779799`.
Walked as a shopper on `cb1-wash-jeans` (GREY WASH OG JEANS, £60), `charcoal-cellblock-crewneck`
and `v2-baggies`; the tables cross-checked against `cb2-wash-jeans`, both jorts and both tees.

Counting convention below: a **tap** is a finger on a control, a **swipe** is one thumb-flick
of roughly one screen. Page-load times are not reported — this audit's browser sits behind a
queue and a proxy, so a landing time here is the harness, not the shop.

---

### Finding the Measurements

**Should:** a shopper who wants numbers should get to them quickly and know they got there.

**Did:** the same everywhere — **one swipe and one tap**, on all three products. The
accordion stack sits directly under the buy box in the order `SPECIFICATION` /
`ITEM DESCRIPTION` / `MEASUREMENTS` / `CHAIN OF CUSTODY — SHIPPING & RETURNS`, about 44% of
the way down the page (jeans: measurements block at 1130px of a 2556px page; crewneck 1271
of 2716; baggies 1202 of 2648). One thumb-flick brings the row `MEASUREMENTS +` onto the
screen, one tap opens it. Measured from the moment the page was up: **~2 seconds** on the
jeans, and 1 swipe + 1 tap on each of the other two.

The catch is what you see after the tap. On a first visit the cookie sheet
(`COOKIE CONSENT … Accept / Decline / Manage preferences`) is anchored to the bottom of the
screen and occupies **43% of it** (measured: top edge at 485px of 844). The `MEASUREMENTS`
row is the last thing above that line, so tapping it opens the table *underneath the sheet*:
the only thing that changes on screen is `+` turning into `−`. It takes a second swipe before
a single number is visible. See the screenshot — the header says `MEASUREMENTS −`, the table
is not there.

**Verdict:** works
**Shopper cost:** on a first visit the tap looks like it did nothing; you need one more swipe
to learn it worked. Small, but it lands at exactly the moment the shopper is deciding whether
this shop can be trusted with £60.
**Evidence:** `audit/screens/pdp-sizing-jeans-measurements-closed.png`,
`audit/screens/pdp-sizing-jeans-measurements-open.png` (open, showing only `MEASUREMENTS −`
above the cookie sheet), `audit/screens/pdp-sizing-baggies-measurements-cm.png`,
`audit/screens/pdp-sizing-crew-sizeguide-after.png`.

---

### The cm / inch toggle

**Should:** convert correctly and say which unit you are looking at.

**Did:** correct on every cell I checked, on all three products, and the caption changes with
it. Jeans, before and after one tap on `IN`:

| size | CM view | IN view |
|---|---|---|
| XS | `76.2cm  73.7cm  45.7cm` | `30in  29in  18in` |
| S  | `81.3cm  76.2cm  48.3cm` | `32in  30in  19in` |
| M  | `86.4cm  77.5cm  50.8cm` | `34in  30.5in  20in` |
| L  | `91.4cm  80.0cm  53.3cm` | `36in  31.5in  21in` |
| XL | `96.5cm  81.3cm  55.9cm` | `38in  32in  22in` |

76.2 ÷ 2.54 = 30.0; 86.4 ÷ 2.54 = 34.0; 55.9 ÷ 2.54 = 22.0. All correct to one decimal.
Tapping `CM` again restores the centimetre values exactly. The caption switches with the
table: `… ALL MEASUREMENTS IN CENTIMETRES.` → `… ALL MEASUREMENTS IN INCHES.`

Crewneck, same tap: `109.2cm / 65.4cm / 47.0cm / 62.2cm` → `43in / 25.7in / 18.5in / 24.5in`.
Also correct.

**Verdict:** works
**Evidence:** `audit/screens/pdp-sizing-jeans-measurements-inches.png`,
`audit/screens/pdp-sizing-crew-measurements-in.png`,
`audit/screens/pdp-sizing-baggies-measurements-in.png`.

---

### Is the measuring method stated?

**Should:** a shopper comparing against a garment they own needs to know how these were taken.

**Did:** a method line sits above every table, and it is the **same line on every product**:

> `TRUE TO SIZE — WAIST, CHEST AND LEG MEASUREMENTS ARE TAKEN AROUND THE GARMENT. ALL
> MEASUREMENTS IN CENTIMETRES.`

Two problems, both visible without leaving the page:

1. It names columns that are not in the table and skips the ones that are. On the jeans the
   columns are `WAIST / INSEAM / LEG OPENING` — the line explains "chest". On the crewneck the
   columns are `CHEST / LENGTH / SHOULDER / SLEEVE` and the line explains "waist" and "leg",
   and says nothing about how `SHOULDER`, `SLEEVE` or `LENGTH` were taken. Those are precisely
   the three a shopper measures wrong: shoulder seam-to-seam or across the back? Length from
   the high point of the shoulder, or from the collar seam?
2. It contradicts the shop's own sizing answer on `QUESTIONS`, which is two taps away in the
   footer of the same product page — that page says `Everything is measured with the garment
   laid flat`. See **Contradictions**.

Also worth saying: `TRUE TO SIZE` is a fit claim, not a method. On the two products whose
tables are identical it cannot be true of both.

**Verdict:** partly
**Evidence:** `audit/screens/pdp-sizing-jeans-measurements-open.png`,
`audit/screens/pdp-sizing-crew-sizeguide-after.png` (identical caption over a table with no
waist and no leg), `audit/screens/pdp-sizing-faq-sizing-onscreen.png`.

---

### Do the numbers read as real, or as placeholder? *(known item — impact only)*

**Should:** the table is the last thing between a shopper and a £60 guess.

**Did:** **from a single product page a shopper cannot tell.** In centimetres the numbers wear
false precision — `76.2 / 81.3 / 86.4 / 91.4 / 96.5` looks measured to the millimetre by
someone with a tape. That is the trap: the decimal is not evidence of care, it is the residue
of a unit conversion.

Two tells exist, and both require the shopper to go looking:

**Tell one — press `IN`.** The ladder resolves to `30 / 32 / 34 / 36 / 38` waist and
`18 / 19 / 20 / 21 / 22` leg opening: exactly two inches per size and exactly one inch per
size, five sizes in a row. Real grading is linear too, so this alone proves nothing — but it
is the same generic ladder any size chart generator emits.

**Tell two — open two products.** `V2 BAGGIES`, described on its own page as
*"wide, full-length sweats in 500gsm cotton, heavy enough to hang straight"*, carries a table
that is **identical to the millimetre** to `GREY WASH OG JEANS`, described as
*"14oz denim, OG straight cut, mid rise. Structured, not baggy."*

| size | GREY WASH OG JEANS | V2 BAGGIES |
|---|---|---|
| XS | `76.2cm 73.7cm 45.7cm` | `76.2cm 73.7cm 45.7cm` |
| S | `81.3cm 76.2cm 48.3cm` | `81.3cm 76.2cm 48.3cm` |
| M | `86.4cm 77.5cm 50.8cm` | `86.4cm 77.5cm 50.8cm` |
| L | `91.4cm 80.0cm 53.3cm` | `91.4cm 80.0cm 53.3cm` |
| XL | `96.5cm 81.3cm 55.9cm` | `96.5cm 81.3cm 55.9cm` |

Same waist, same inseam, same leg opening, on two garments the shop itself describes as
opposites. Both were read off the screen, one after the other, in the same session, in both
units. The pattern repeats across the rest of the catalogue (read from the store's own product
data rather than page by page): `BLUE WASH OG JEANS` carries that same jeans table, the two
jorts share one table, and the two tees share one — nine products carry measurements, and
seven of those nine are running three tables between them.

A shopper's read: *the leg opening of a "wide, full-length" sweat cannot be the same as the
leg opening of a jean the same shop calls "structured, not baggy". One of these numbers is
not about this garment.* And the arithmetic backs it up — `50.8cm` is 20.0in dead on, the
same round number on both.

**Verdict:** partly — the component works perfectly and is being fed data that cannot be true
for both products at once.
**Shopper cost:** the table is presented as the answer to the size question and answers it
with the size letter restated in metric. A shopper between two sizes learns nothing; a shopper
buying the baggies *for the wide leg* is being told, precisely, that the leg is 20in around at
M. If that is wrong they pay to send it back — `Return postage is yours` (custody, step 04).
Worst case it costs a customer twice: once in the wrong size, once in the postage.
**Evidence:** `audit/screens/pdp-sizing-jeans-measurements-open.png` vs
`audit/screens/pdp-sizing-baggies-measurements-cm.png`;
`audit/screens/pdp-sizing-jeans-measurements-inches.png` vs
`audit/screens/pdp-sizing-baggies-measurements-in.png`.

---

### `SIZE GUIDE` — one tap, and you can see it happen

**Should (SPEC §3.5):** one tap, scrolls the Measurements heading to the top. No modal, no PDF.

**Did:** exactly that, on all three products. The button sits under the size row labelled
`SIZE GUIDE`; one thumb-flick from the top of the page brings it into view, and one tap:

- jeans: page glides from 675px to 1130px — `MEASUREMENTS` heading lands at y=0, first number
  (`76.2cm`) at 237px, accordion open;
- crewneck: 657 → 1271, heading at y=0, first number `109.2cm` at 237px;
- baggies: 675 → 1202, heading at y=0, first number `76.2cm` at 237px.

**Where the eye lands:** on the word `MEASUREMENTS` at the very top of the screen, with `CM`
`IN` under it and the whole five-row table below — the tap is unmistakable. The movement is
animated rather than instant (mid-glide at 130ms the page was at 878px of the 1130px target),
so the eye is carried down rather than teleported. The sticky header is not in the way at that
scroll position, and even on a first visit the whole table clears the cookie sheet.

The odd result is that **`SIZE GUIDE` is a better route to the table than tapping
`MEASUREMENTS` itself** — the button scrolls the heading to the top where the numbers are
visible, while the accordion tap opens the table under the cookie sheet.

**Verdict:** works
**Evidence:** `audit/screens/pdp-sizing-jeans-sizeguide-before.png` (before),
`audit/screens/pdp-sizing-jeans-sizeguide-130ms.png` (mid-glide),
`audit/screens/pdp-sizing-jeans-sizeguide-after.png` (after),
`audit/screens/pdp-sizing-crew-sizeguide-after.png`,
`audit/screens/pdp-sizing-baggies-sizeguide-after.png`.

---

### The fourth column falls off the screen (crewneck)

**Should:** if a table has four measurements, a shopper should be able to read all four.

**Did:** on the crewneck the table is `SIZE / CHEST / LENGTH / SHOULDER / SLEEVE` and the
`SLEEVE` column is cut by the right edge of the phone — the numbers are sliced mid-character:
`62.2cr`, `63.5cr`, `64.8cr`. The table scrolls sideways on its own, but nothing says so
beyond the clipped digits: no arrow, no fade, no second row of the numbers. Sleeve length is
the measurement people buying a heavy crewneck actually check.

The jeans and the baggies (three columns) fit the screen with room to spare, so this only
bites on the products with four or five measurements.

**Verdict:** partly
**Shopper cost:** a shopper who does not think to drag the table sideways reads three of the
four numbers and assumes that is all there is.
**Evidence:** `audit/screens/pdp-sizing-crew-sizeguide-after.png` — `SLEEVE` header truncated,
values reading `62.2cr / 63.5cr / 64.8cr / 66.0cr / 67.3cr` at the screen edge.

---

### Shipping cost, from the product page only

**Should:** a shopper should be able to find out what postage costs before committing.

**Did:** three levels, and yes — a real number is reachable **before checkout**.

- **0 taps.** The bar across the top of the product page already reads
  `FREE UK SHIPPING OVER £20 — ORDER BY 18:00 FOR SAME-DAY DISPATCH`, and the buy box carries
  `Order before 18:00 and it ships today (Mon–Sat)` with `> Ordered now — leaves today`.
- **1 swipe + 1 tap (~4 s).** `CHAIN OF CUSTODY — SHIPPING & RETURNS` → step `02 DISPATCHED`:
  `Shipped with Royal Mail Tracked. Free UK shipping over £20, and free Tracked 24 over £70.`
  Two thresholds, still no price. On a £60 jean this is enough (over £20 = free), but a
  £15 pair of socks tells you nothing.
- **3 swipes + 2 taps (~12 s).** All the way to the bottom of the product page, where the
  footer's `INFORMATION` column carries `SHIPPING` → the Shipping policy, first paragraph:
  `What it costs. Free UK shipping over £20, and free Tracked 24 over £70. Under that:
  standard £3, Tracked 24 £4.99.`

So the real postage numbers — **£3 and £4.99** — exist and are two taps from the product page,
but they are nowhere in the product page's own shipping accordion, which is the place a
shopper looks. International is worse: `Shipping internationally? add your items to cart and
your shipping is calculated at checkout based on item weight and location.` — no number
anywhere before the cart.

And whether you get the number at all depends on which footer link you pick. Two rows above
`SHIPPING` sits `QUESTIONS`, whose `HOW MUCH IS SHIPPING?` answer reads:
`Free on UK orders over £20. Over £70 you get Royal Mail Tracked 24 free. Below £20 it is
calculated at checkout before you pay.` — the same shop, the same question, one tap apart,
telling the shopper there is no price to be had until checkout.

**Verdict:** partly
**Shopper cost:** a shopper under £20 has to leave the product page and read a policy page to
learn that postage is £3 — and if they tap `QUESTIONS` instead of `SHIPPING` they are told to
go to checkout to find out. The accordion titled `SHIPPING & RETURNS` mentions money twice
without ever giving the price.
**Evidence:** `audit/screens/pdp-sizing-ship-01-pdp-closed.png`,
`audit/screens/pdp-sizing-ship-02-custody.png`, `audit/screens/pdp-sizing-ship-03-footer.png`,
`audit/screens/pdp-sizing-ship-04-policy.png`, `audit/screens/pdp-sizing-faq-sizing.png`.

---

### Returns policy, from the product page only

**Should:** findable, and the same story wherever you find it.

**Did:** **1 swipe + 1 tap (~11 s including reading)** gets the whole of it, in custody step
`04 DELIVERED`, quoted exactly:

> `You have 14 days from delivery to return unworn goods with tags attached. Return postage is
> yours unless we sent the wrong thing or it arrived faulty. Start a return by email:
> crooksldn@gmail.com.`

On a first visit, though, that is not what you read: the cookie sheet cuts the step off after
`You have 14 days from delivery to return unworn goods with tags` — the words that tell you
who pays the postage are underneath it until you dismiss it or scroll.

**2 taps** more reaches the full policy through the footer link labelled `REFUNDS`:

> `Changed your mind or wrong size? You have 14 days from delivery to return or exchange any
> unworn item with tags on. Return postage is paid by you — that covers a change of mind, the
> wrong size, a swap, or any other reason of your own. There is no fee for a UK size swap
> itself, and we cover the postage sending the new size out to you. For returns please return
> to: Oairo Uk Office, Bourne end Business Park, Bourne End, Buckinghamshire, United Kingdom,
> SL8 5AS.`

Checked against each other: **these two agree.** Same window (14 days from delivery), same
condition (unworn, tags on), same answer on who pays (you, unless it was our fault). The FAQ's
`CAN I RETURN SOMETHING?` says the same thing again — `Return postage is yours — change of
mind, wrong size, a swap, any reason of your own.` Three surfaces, one story.

The one thing the product page does not say is that an **exchange** is possible at all — the
custody step only offers "return", while the policy offers "return or exchange" and the FAQ's
`DO YOU DO EXCHANGES?` answers `Yes. You pay the postage sending the original back to us.
There is no fee for the swap itself, and we cover the postage sending the new size out to
you.` For a shopper hovering between M and L, that is the single most reassuring sentence on
the site, and it is two taps away from the moment they need it.

Note for the record: this clears open item **O5** — the live Refund policy no longer says
"Size swaps are free within the UK"; it now spells out that return postage is the customer's.

**Verdict:** works
**Shopper cost:** the free-size-swap promise is invisible at the moment of the size decision.
**Evidence:** `audit/screens/pdp-sizing-ret-01-custody-steps.png`,
`audit/screens/pdp-sizing-ret-02-refund-policy.png`,
`audit/screens/pdp-sizing-ret-03-all-accordions.png`.

---

### The cookie sheet over the buy controls *(first visit only)*

**Should:** nothing should sit on top of the controls a shopper needs.

**Did:** on a first visit the consent sheet covers the bottom 43% of the phone screen, and
what is under it includes the sticky buy bar and, at that scroll position, the `SIZE GUIDE`
button — a tap on either lands on the sheet, not the control. It is dismissable
(`Accept` / `Decline`), so it costs one tap, but the first tap a new shopper makes on this
page may well be an unresponsive one.

**Verdict:** partly (store-side, not theme code — and the known-items list says "no cookie
banner", so this is new since that list was written)
**Evidence:** `audit/screens/pdp-sizing-jeans-sizeguide-before.png`,
`audit/screens/pdp-sizing-ship-03-footer.png`.

---

## Surprises

- **The measuring method on the product page and the measuring method on `QUESTIONS` are not
  the same method** — see Contradictions. This is the one thing in this area that can make a
  shopper order the wrong size *by following the site's own instructions*.
- **`V2 BAGGIES` and `GREY WASH OG JEANS` publish identical measurements to the millimetre**,
  while their descriptions call them opposites ("wide… hang straight" vs "Structured, not
  baggy"). Nine products carry a table; seven of them are running three tables between them.
- **The cm column's decimals are conversion residue, not precision.** Every value in every
  table is a round inch figure multiplied by 2.54 — `76.2 = 30in`, `86.4 = 34in`,
  `50.8 = 20in`. The centimetre view is the one that looks forensic, and it is the one that
  is derived.
- **`SIZE GUIDE` is a better way into the table than the `MEASUREMENTS` accordion**, because
  it scrolls the heading to the top of the screen; tapping the accordion on a first visit
  opens the table underneath the cookie sheet and looks like nothing happened.
- **The postage prices £3 and £4.99 exist** and are well written — but only on the Shipping
  policy page, never in the accordion called `SHIPPING & RETURNS`, and the `QUESTIONS` page
  actively tells shoppers the price does not exist until checkout.
- **The crewneck's `SLEEVE` column is cut off by the edge of the phone** — `62.2cr`, `63.5cr`
  — with nothing but the sliced digits to say the table can be dragged sideways.
- **`QUESTIONS` offers something the product page never does:** `If the piece you want is not
  listed yet, message us and we will measure it for you.` That is a real answer to size
  anxiety, buried at the bottom of an FAQ answer.
- **A cookie consent sheet now exists** and eats the bottom 43% of the phone screen, including
  the sticky buy bar and the second half of the returns sentence.

## Missing

- A price for postage on the product page. The accordion gives two thresholds (`over £20`,
  `over £70`) and no price.
- Any mention on the product page that a size swap is possible, free, and posted back out at
  the shop's expense — the policy page says so, the buy decision never sees it.
- A method note for the columns that need one: `SHOULDER`, `SLEEVE`, `LENGTH`. The line on
  screen explains "waist, chest and leg" on a crewneck that has none of those columns.
- Any per-product method or fit note — one caption is doing duty for jeans, sweatpants,
  crewnecks and tees.
- Any sign that a four- or five-column table scrolls sideways.
- A "which size am I" prompt of any kind at the point of decision. The FAQ says
  `message us and we will measure it for you` and the Contact page says `message us your usual
  fit and we'll point you to the right one` — the product page, where the shopper is actually
  stuck, offers neither.

## Contradictions

**1. Laid flat vs measured around — the same shop, two taps apart.**

Product page, printed directly above every measurements table:

> `TRUE TO SIZE — WAIST, CHEST AND LEG MEASUREMENTS ARE TAKEN AROUND THE GARMENT. ALL
> MEASUREMENTS IN CENTIMETRES.`

`QUESTIONS` page, reached from the `QUESTIONS` link in that same product page's footer,
answering how sizing works:

> `Where a piece has been measured, its product page carries a measurements table — tap SIZE
> GUIDE next to the size buttons. Everything is measured with the garment laid flat, and you
> can switch the table between centimetres and inches.`

"Around the garment" and "laid flat" differ by a **factor of two**. A shopper who lays their
own jeans flat, measures 43cm across the waistband and compares it with the `86.4cm` on the M
row will conclude the M is twice their size and buy down — or, believing the FAQ, will read
`86.4cm` as a flat measurement and expect a 68in waist. Either way they order the wrong thing,
having done exactly what they were told. Both sentences are on screen in
`audit/screens/pdp-sizing-jeans-measurements-open.png` and
`audit/screens/pdp-sizing-faq-sizing-onscreen.png`.

**2. What shipping costs under £20.**

`QUESTIONS` → `HOW MUCH IS SHIPPING?`:

> `Free on UK orders over £20. Over £70 you get Royal Mail Tracked 24 free. Below £20 it is
> calculated at checkout before you pay.`

Shipping policy, linked two rows below it in the same footer:

> `What it costs. Free UK shipping over £20, and free Tracked 24 over £70. Under that:
> standard £3, Tracked 24 £4.99.`

One says there is no price before checkout; the other prints the price. A shopper who wanted
the number and asked the obvious question is sent away empty-handed.

**3. Jeans vs baggies, quoted above** — `Structured, not baggy` and `wide, full-length …
heavy enough to hang straight`, with the same `45.7 / 48.3 / 50.8 / 53.3 / 55.9` leg openings.

*(Checked and clear, no contradiction: custody step 04, the Refund policy and the FAQ's
`CAN I RETURN SOMETHING?` all agree — 14 days from delivery, unworn with tags, return postage
is the customer's unless the item was faulty or wrongly sent. The old "size swaps are free
within the UK" line from open item O5 is gone from the live Refund policy.)*

## Works and must be protected

- **`SIZE GUIDE` → one tap, no modal, no PDF, heading pinned to the top of the screen with the
  numbers under it.** It is the best-behaved control in this area, on all three products.
- **The cm/inch toggle.** Correct arithmetic in both directions, both button states shown, and
  the caption's unit word changes with the table — the shopper is never left guessing which
  unit they are reading.
- **Measurements one swipe and one tap below the buy box**, in a plain accordion stack with
  plain English headings.
- **Returns stated in plain, unhedged English on the product page**: `Return postage is yours
  unless we sent the wrong thing or it arrived faulty.` No weasel words, no "conditions apply".
  It is the sentence a shopper needs and it is one tap away.
- **`SHIPPING` and `REFUNDS` in the footer of every product page** — findable, correctly
  labelled, and they land on real, well-written policy pages.
