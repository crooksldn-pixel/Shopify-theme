# raw-pdp-core — the product record

Shopped on the staging theme (`202053779799`), GB market, GBP. Mobile is an iPhone-class
390×844 at 3× unless a line says desktop. Products used: **`cb1-wash-jeans`** (GREY WASH OG
JEANS, £60), **`charcoal-cellblock-crewneck`** (£50), **`v2-baggies`** (£60 — the only
product in the shop with sold-out sizes), plus `charcoal-cellblock-shorts` (£45) and sweeps
across all twelve products where a count was needed.

Clock during the run: **Thursday 20 August 2026, 16:47–17:35 British Summer Time.**

---

### Gallery — how many photos, and whether you can see the fabric

**Should:** A £60 garment sold with no fitting room should be photographed enough times, and
at enough resolution, that a stranger can decide what it is made of.

**Did:** The gallery is a single large square photo, a line reading `PHOTO 1 OF 3`, and a row
of thumbnails underneath. It is clean and it reads well. Two things are wrong with it.

**First, the photo counts.** Read off the on-screen `PHOTO 1 OF n` counter on all twelve
products:

| Photos | Products |
|---|---|
| **1** | **GREY WASH OG JEANS £60**, **CHARCOAL CELLBLOCK CREWNECK £50**, GREY WASH JORTS £50, BLUE WASH JORTS £50, BLACK/BLUE SOCKS £6, WHITE/RED SOCKS £6, LARGE DUFFLE BAG £18 |
| 2 | BLUE WASH OG JEANS £60, V2 BAGGIES £60, EVIL CLIVE TEE £25, CRXST RZ T-SHIRT £25 |
| 3 | CHARCOAL CELLBLOCK SHORTS £45 |

**Seven of twelve products have exactly one photograph**, and four of those seven are
garments at £50–£60. Nothing in the shop has more than three. Both products the brief names
are single-photo products, one of them the joint most expensive item on the site.

On `cb1-wash-jeans` that one photo is a flat cut-out of the **back** of the jeans on black.
You can see the handcuff pocket graphic and nothing else. There is no front, no side, no
waistband, no hem, no leg-opening, nothing on a body and no scale reference. The
`SPECIFICATION` panel says `14oz denim` and the shopper has to take that entirely on faith,
because the single photograph never shows the cloth close enough to read it. The crewneck is
the same at £50 — a flat front, no back, no detail.

**Second, there is no zoom of any kind.** Tapping the photo on mobile does nothing — no
lightbox, no overlay, nothing changes. On desktop the cursor stays `auto` over it, hovering
does nothing, clicking does nothing and double-clicking does nothing. So the largest view of
a £60 pair of jeans a shopper can obtain is the 332-pt square on a phone or the 611-px column
on a 1440 desktop, and pinch-zoom on the phone just magnifies what is already rendered.

That is what makes the fabric unreadable. It is not that the pictures are bad files —
Shopify holds a 2048-px master for these images and will serve it on request. The detail
exists; the page gives the shopper no way to reach it.

**Verdict:** partly — the component works; the pictures inside it are not allowed to do the
selling job.

**Shopper cost:** On a £60 pair of jeans the single un-enlargeable photo is the entire
product description. A shopper who wants to know how the leg falls, what the front looks
like, or how 14oz reads in the hand has no second photo to click and no way to get closer.
Two separate fixes: shoot and upload more angles (store work), and let the existing 2048-px
master be opened (theme work, and it can be done with a plain full-screen image on black —
no rounded modal, no gallery library, nothing outside the design law).

**Evidence:** `audit/screens/pdpcore-80-gal-cb1-wash-jeans.png` and
`audit/screens/pdpcore-101-desktop-jeans.png` (counter `PHOTO 1 OF 1`, no thumbnail row at
all — a £60 product page with one picture), `audit/screens/pdpcore-80-gal-charcoal-cellblock-crewneck.png`
(`PHOTO 1 OF 1`), `audit/screens/pdpcore-80-gal-charcoal-cellblock-shorts.png`
(`PHOTO 1 OF 3` with three thumbnails), `audit/screens/pdpcore-82-after-photo-tap.png` and
`audit/screens/pdpcore-105-after-click-photo.png` (tapping / clicking the photo changes
nothing).

---

### Gallery — moving between photos

**Should:** Thumbnails, a swipe on a phone, arrow keys on a desktop.

**Did:** All three routes exist and the keyboard one is unusually good.

**Thumbnails** are the reliable route: proper `<button>`s labelled `Photo 1 of 3`,
`Photo 2 of 3`, `Photo 3 of 3`, the active one outlined in purple, the counter updating with
them. They are also the **first three stops in the tab order** on the whole page, ahead of
the sizes — so a keyboard shopper meets the photographs before anything else.

**Arrow keys** work on desktop. The gallery is a focusable `role="group"` labelled
`Evidence photographs`; with it focused, `ArrowRight` took the counter `PHOTO 1 OF 3` →
`PHOTO 2 OF 3` → `PHOTO 3 OF 3` and `ArrowLeft` walked it back, stopping cleanly at both
ends rather than wrapping.

The main photo is **not** a horizontal scroller — the track is exactly as wide as its frame —
so dragging it with a mouse moves nothing; the theme listens for a real touch gesture
instead. Where a product has only one photo no thumbnail row renders at all, and
`PHOTO 1 OF 1` is the only cue that there is nothing more to see. That is honest, if bleak.

**Verdict:** works

**Evidence:** `audit/screens/pdpcore-102-desktop-shorts-gallery.png`,
`audit/screens/pdpcore-80-gal-charcoal-cellblock-shorts.png`,
`audit/screens/pdpcore-81-shorts-photo1.png`.

---

### Selecting a size — price, stock line, URL

**Should:** Picking a size should settle the buy state and be shareable.

**Did:** All five sizes on the crewneck, in order:

| Tapped | Price | Stock line | URL |
|---|---|---|---|
| (nothing) | `£50.00` | `Select Size` | `/products/charcoal-cellblock-crewneck` |
| XS | `£50.00` | `IN STOCK` | `…?variant=53936235217239` |
| S | `£50.00` | `IN STOCK` | `…?variant=53936235250007` |
| M | `£50.00` | `IN STOCK` | `…?variant=53936235282775` |
| L | `£50.00` | `IN STOCK` | `…?variant=53936235315543` |
| XL | `£50.00` | `IN STOCK` | `…?variant=53936235348311` |

The **price does not change**, and it should not — every size of this garment is £50. The
**stock line does change**, from `Select Size` to `IN STOCK`. The **URL updates on every
tap** and the link is real: pasting `…/products/cb1-wash-jeans?variant=53639819329879` into a
fresh page comes back with L already selected, `IN STOCK`, and `ADD TO BAG` live. The buy
button relabels from `SELECT A SIZE` to `ADD TO BAG`, and Shopify's wallet row
(`Buy with Shop` / `More payment options`) only appears once a size is chosen. The sticky bar
picks the size up as `£50.00 · M`.

One quiet thing: on `cb1-wash-jeans` the **XL button carries a 4-pixel purple square** in its
top-right corner with no legend anywhere on the page. It means low stock — selecting XL is
what surfaces the wording. Nobody will read a 4px dot as "nearly gone".

**Verdict:** works

**Evidence:** `audit/screens/pdpcore-30-crewneck-size-XL.png`,
`audit/screens/pdpcore-31-jeans-size-L.png`, `audit/screens/pdpcore-32-jeans-deeplink.png`,
`audit/screens/pdpcore-21b-jeans-nosize-viewport.png` (the purple mark on XL, unexplained).

---

### A sold-out size

**Should:** Per `SPEC.md §3.5` and §9.3, a sold-out size stays selectable and swaps the buy
button for a notify form.

**Did:** Exactly that, and it is the best-behaved control on the page. On `v2-baggies`,
M / L / XL are sold out: they render with a dashed border and struck-through text, and a real
thumb still selects them. Tapping M gives, verbatim:

- stock line, in red: **`SIZE M IS SOLD OUT`**
- buy button, greyed: **`SOLD OUT`**
- a red-bordered panel below it: **`TELL ME WHEN THIS SIZE IS BACK`**, a field placeheld
  **`email address`**, and a purple button **`NOTIFY ME`**
- the sticky bar mirrors it: **`V2 BAGGIES  £60.00 · M   SOLD OUT   CHECKOUT NOW`**

Two problems sit on top of this good behaviour.

**(1) The dispatch promise does not switch off.** With `SIZE M IS SOLD OUT` on screen in red,
the two lines above it still read `Order before 18:00 and it ships today (Mon–Sat)` and
`> Ordered now — leaves today`. The page is simultaneously telling the shopper this size
cannot be bought and that ordering now gets it out the door today.

**(2) The sticky bar still offers `CHECKOUT NOW`.** The inline button correctly greys to
`SOLD OUT`, but the bar pinned to the bottom of the screen keeps a live-looking
`CHECKOUT NOW` beside it.

**(3) The sticky bar physically covers the `NOTIFY ME` button.** With M selected and the
notify panel open, the purple `NOTIFY ME` button's lower edge runs underneath the sticky bar.
It is visibly clipped in the screenshot. The one control the page wants the shopper to press
in this state is the one partly hidden by furniture.

**Verdict:** partly

**Shopper cost:** The shopper is told "sold out" and "leaves today" in the same eyeful, and
the button they need is half-covered by a bar advertising checkout for the thing they cannot
buy.

**Evidence:** `audit/screens/pdpcore-11-baggies-soldout-M.png` (all of the above in one
frame — `SIZE M IS SOLD OUT`, `SOLD OUT`, `TELL ME WHEN THIS SIZE IS BACK`, and the sticky
bar clipping `NOTIFY ME` while offering `CHECKOUT NOW`),
`audit/screens/pdpcore-70-notify-invalid-typed.png`.

---

### The notify form — submitting it

**Should:** Take an address, say thank you, and say when you will hear back.

**Did:** I submitted it four times across two sessions.

**Invalid address (`not-an-email`).** The page does not move. The only thing shown is the
**browser's own** validation bubble, verbatim:

> **`Please include an '@' in the email address. 'not-an-email' is missing an '@'.`**

Left empty and submitted, the same bubble mechanism gives:

> **`Please fill out this field.`**

Neither of those is the shop's wording — they are Chrome's defaults, in Chrome's typeface,
in a rounded white bubble that is the only non-CROOKSLDN pixel on the page. There is no
theme-authored error text anywhere in the panel, and searching the rendered page for any
error, invalid or problem wording returns nothing.

**Valid address (`buyer+test@example.com`).** Pressing `NOTIFY ME` throws up a **blank white
hCaptcha panel covering most of the phone screen**, greying out the product behind it, with
an hCaptcha badge in the bottom-right corner. In this audit environment the challenge itself
never rendered — the box stayed empty — so I could not complete it. I waited, retried on a
clean session, and got the same panel. **I never reached a confirmation of any kind.** After
the attempt the page is unchanged: the same `SIZE L IS SOLD OUT`, the same open panel, my
address still sitting in the field, no thank-you, no error, no e-mail promised.

**What am I promised, and when will I hear back?** The panel's entire copy is
`TELL ME WHEN THIS SIZE IS BACK` / `email address` / `NOTIFY ME`. That is it. There is **no
statement of when you would hear back**, no "we'll email you when it returns", no note on
what happens to the address, no privacy line. The theme does carry a success line for this
form — it renders only after a completed round-trip POST, which the captcha prevented me
from reaching, so no shopper wording for the success or failure case was ever shown to me.

**Verdict:** broken — as a shopper I could not get this form to complete, twice, and it never
told me what it would do.

**Shopper cost:** The one thing a shopper can still give you when their size is gone is their
e-mail. The form takes it, throws a blank captcha box over the page, and returns them to an
unchanged screen. Most people will read that as "it didn't work" and leave.

**Evidence:** `audit/screens/pdpcore-71-notify-invalid-after.png` (invalid address, no theme
error), `audit/screens/pdpcore-72-notify-empty.png`,
`audit/screens/pdpcore-73-notify-valid-typed.png`,
`audit/screens/pdpcore-74-notify-valid-after.png` (**the blank white hCaptcha panel over the
greyed product page, hCaptcha badge bottom-right**),
`audit/screens/pdpcore-74b-notify-valid-after-full.png`.

---

### Pressing the buy button without choosing a size

**Should:** Tell the shopper what is missing, near their thumb.

**Did:** **You cannot press `ADD TO BAG` without a size, because the button never says
`ADD TO BAG` until you pick one.** With nothing selected it reads, verbatim,
**`SELECT A SIZE`**, greyed out, and it is genuinely inert — I parked it dead centre of the
screen and tapped it, and *nothing at all happened*: no message, no movement, no scroll, no
highlight on the size row, no focus jump, the bag count stayed `[0]`. Same for the sticky
bar's copy of it.

So the answer to "what exactly are you told" is: **nothing new**. What is already on screen
is the button's own label `SELECT A SIZE`, and a small grey line reading `Select Size`
(sentence case, colour `rgb(138,131,119)` — dimmer than the body text) sitting **168 pixels
above** the button, immediately under the size row.

Where does the eye go? Nowhere. The tap produces no event to follow. The message *is* near
the size row, which is the right place for it — but it was already there before the tap and
it does not change, flash, or move when you press. A shopper who has just tapped a dead
button typically taps it again.

**Verdict:** partly — it is honest and it cannot mis-sell, but a tap on it is a completely
silent event.

**Shopper cost:** Small but real: a second and third tap on a dead control before the eye
travels back up to the size squares. A one-word change — making the grey `Select Size` line
flash or the size row outline on the dead tap — would close it, and needs no new colour,
radius or shadow.

**Evidence:** `audit/screens/pdpcore-20-jeans-before-nosize-press.png`,
`audit/screens/pdpcore-21-jeans-after-nosize-press.png` and
`audit/screens/pdpcore-21b-jeans-nosize-viewport.png` — before and after are the same frame.

---

### The four accordions

**Should:** `SPEC.md §3.5`: four `<details name>` panels, all default closed, **mutually
exclusive** — "Opening one should close the others."

**Did:** They are not `<details>` at all. They are `<button class="crk-section-head">` with
`aria-expanded`, and **they are not mutually exclusive.** Opening them in order:

```
opened SPECIFICATION      -> SPECIFICATION=true | ITEM DESCRIPTION=false | MEASUREMENTS=false | CHAIN OF CUSTODY=false
opened ITEM DESCRIPTION   -> SPECIFICATION=true | ITEM DESCRIPTION=true  | MEASUREMENTS=false | CHAIN OF CUSTODY=false
opened MEASUREMENTS       -> SPECIFICATION=true | ITEM DESCRIPTION=true  | MEASUREMENTS=true  | CHAIN OF CUSTODY=false
opened CHAIN OF CUSTODY   -> SPECIFICATION=true | ITEM DESCRIPTION=true  | MEASUREMENTS=true  | CHAIN OF CUSTODY=true
```

All four end up open at once. They do default closed, and each one does open on the first
tap, so nothing is unreachable — but a shopper who opens all four (which is exactly what
someone deciding on a £60 purchase does) pushes `MORE FROM THIS DROP` a long way down the
page and has to scroll back up past four open panels to reach the size row again.

Contents are real and good. `SPECIFICATION` on the jeans: `FABRIC 14oz denim / CUT OG
straight, mid rise / ORIGIN Made in Portugal / CARE Cold wash inside out. Hang dry.`
`MEASUREMENTS` carries a `CM` / `IN` toggle, the method line
`TRUE TO SIZE — WAIST, CHEST AND LEG MEASUREMENTS ARE TAKEN AROUND THE GARMENT. ALL
MEASUREMENTS IN CENTIMETRES.` and a five-row table.

**Verdict:** partly — they work, they are not exclusive, and the spec says they should be.

**Evidence:** `audit/screens/pdpcore-40-acc-specification.png`,
`audit/screens/pdpcore-40-acc-item-description.png`,
`audit/screens/pdpcore-40-acc-measurements.png`,
`audit/screens/pdpcore-40-acc-chain-of-custody.png` — the last one shows all four panels open
simultaneously.

---

### Chain of custody — the delivery promise, verbatim

**Should:** Say what happens after the money leaves, in plain English.

**Did:** Four steps, quoted exactly as they appear on `cb1-wash-jeans`:

> **01 LOGGED**
> Orders placed before 18:00 are dispatched the same day, Monday to Saturday. After 18:00, the next dispatch day.
>
> **02 DISPATCHED**
> Shipped with Royal Mail Tracked. Free UK shipping over £20, and free Tracked 24 over £70.
>
> **03 IN TRANSIT**
> Tracking issued by email. UK 1–2 working days. International 7–14 working days.
>
> **04 DELIVERED**
> You have 14 days from delivery to return unworn goods with tags attached. Return postage is yours unless we sent the wrong thing or it arrived faulty. Start a return by email: crooksldn@gmail.com.

This is the strongest copy on the page: specific, unhedged, and it names a real return route.
It is also, on this product, the **only** place the shopper is told the return window exists —
the buy spine never mentions returns.

**Verdict:** works — protect this wording.

**Evidence:** `audit/screens/pdpcore-40-acc-chain-of-custody.png`.

---

### The dispatch line

**Should:** Say *leaves today / leaves tomorrow / leaves Monday* and be true when it is read.

**Did:** Two lines sit under the size row:

> `Order before 18:00 and it ships today (Mon–Sat)`
> `> Ordered now — leaves today`

At the time of the run — **Thursday 20 August 2026, 16:47 to 17:35 BST**, a dispatch day,
before the 18:00 cutoff — `leaves today` is the correct answer and matches both the custody
step and the status bar's `FREE UK SHIPPING OVER £20 — ORDER BY 18:00 FOR SAME-DAY DISPATCH`.
The line is computed live in the browser against the shop's own timezone, not baked into a
cached page, so it will not go stale at 18:01. It is not a countdown and does not manufacture
urgency, which is right.

The one flaw is the one recorded above: the line does **not** stand down when the selected
size is sold out, so `SIZE M IS SOLD OUT` and `Ordered now — leaves today` appear together.

**Verdict:** works (with the sold-out contradiction filed under the sold-out entry)

**Evidence:** `audit/screens/pdpcore-21b-jeans-nosize-viewport.png`,
`audit/screens/pdpcore-11-baggies-soldout-M.png`.

---

### The sticky bottom bar

**Should:** `SPEC.md §3.5` — a bar repeating product, price, selected size and both actions,
which by design appears "only while the primary control is off-screen".

**Did:** **It never goes away.** I traced it down the crewneck page at scroll positions 0,
150, 300, 500, 800, 1200, 1800 and the page bottom: at every one of them it is pinned at
`top: 775` of an 844-px screen, 69 px tall, fully opaque. It is already there before the
shopper has scrolled at all, and it is still there when the real `ADD TO BAG` button is in
the middle of the screen — the screenshot of a successful add shows the inline `ADD TO BAG`
and the sticky `ADD TO BAG` on screen together.

It does carry the selected size correctly:
`CHARCOAL CELLBLOCK CREWNECK  £50.00 · M   ADD TO BAG   CHECKOUT NOW`, and after an add it
flashes `Added — 1 in bag` in the same slot (losing the `· M` while it does).
There is an 88-px spacer at the foot of the page so it does not cover the footer.

What it covers everywhere else, on a 390×844 phone: **the bottom 69 px of every screen**. In
practice that means the first tile of `MORE FROM THIS DROP`, the lower edge of the
`Buy with Shop` wallet row, and — the one that matters — **the `NOTIFY ME` button** in the
sold-out state.

**Verdict:** partly — it carries the right information; its appear-on-scroll behaviour does
not happen, so it is permanent furniture.

**Shopper cost:** 8% of a phone screen is spent on a duplicate of a button that is often
already visible, and it clips the notify form's only control.

**Evidence:** `audit/screens/pdpcore-50-sticky-with-size.png` (`£50.00 · M` carried),
`audit/screens/pdpcore-90-added-to-bag.png` (**inline `ADD TO BAG` and sticky `ADD TO BAG`
on screen at the same time**), `audit/screens/pdpcore-51-sticky-page-bottom.png`,
`audit/screens/pdpcore-11-baggies-soldout-M.png` (bar clipping `NOTIFY ME`).

---

### `MORE FROM THIS DROP` — and whether the product lists itself

**Should:** Related products that are actually related, and never the product you are already
looking at.

**Did:** **The product never lists itself.** I checked the tray on all twelve products and
compared every link against the page's own path: zero self-links. The heading text seen in a
casual read — the jeans page appears to end with `GREY WASH OG JEANS £60.00` right after the
related tray — is the **sticky bar**, not a fourth related tile. That is a real trap for the
eye and worth knowing, but it is not a self-listing.

The relations themselves are sound: they follow the collection. `cb1-wash-jeans` → the other
three denim pieces; `charcoal-cellblock-crewneck` → `charcoal-cellblock-shorts` and
`V2 BAGGIES` (both SWEATS); `white-socks` → `black-socks` and `LARGE DUFFLE BAG`
(accessories).

**But two products have no related tray at all.** On **`evil-clive-tee`** and
**`crxst-rz-t-shirt`** — the two t-shirts, £25 each — there are zero tiles and the
`MORE FROM THIS DROP` heading does not render. The page simply ends at the accordions. Those
are the two cheapest garments, the natural add-on and the natural entry point, and they are
the two pages with no onward route except the browser's back button.

**Verdict:** partly

**Shopper cost:** A shopper who lands on a tee from search or Instagram hits a dead end.

**Evidence:** `audit/screens/pdpcore-60-related.png`,
`audit/screens/pdpcore-95-evilclive-related.png` (full page — no `MORE FROM THIS DROP`
section exists).

---

### `ADD TO BAG` — the happy path

**Should:** Add the thing, say so where the thumb is.

**Did:** Picked M on the crewneck, tapped `ADD TO BAG`. The header count went `[0]` → `[1]`,
and a line appeared under the button reading, verbatim, **`> Added — 1 in bag  View bag`**
with `View bag` as a link. The sticky bar simultaneously flashed
`CHARCOAL CELLBLOCK CREWNECK  Added — 1 in bag  ADD TO BAG  CHECKOUT NOW`. Four seconds later
both revert to `IN STOCK` / `ADD TO BAG`. No drawer, no modal, no interception — you stay on
the product.

One layout note: the confirmation line lands *below* Shopify's `Buy with Shop` and
`More payment options` block, so on the crewneck it is roughly 300 px beneath the button that
was tapped, not directly under it.

**Verdict:** works

**Evidence:** `audit/screens/pdpcore-90-added-to-bag.png`,
`audit/screens/pdpcore-91-added-4s-later.png`.

---

### The cookie / consent banner on a product page

**Should:** Not stand between a first-time shopper and the price.

**Did:** On a first visit to `/products/cb1-wash-jeans` a Shopify consent banner
(`#shopify-pc__banner`) occupies the bottom **359 px of the 844-px screen — 43% of the phone
— and it is not dismissible by tapping away.** It reads, verbatim:

> **COOKIE CONSENT**
> We and our partners, including Shopify, use cookies and other technologies to personalize
> your experience, show you ads, and perform analytics, and we will not use cookies or other
> technologies for these purposes unless you accept them. Learn more in our Privacy Policy

with two visible buttons, **`Accept`** and **`Decline`** (a third, `Manage preferences`, is in
the markup but does not appear on a 390-px screen). There is no × and no close affordance.

I measured what is directly underneath it on a product page at first paint. In order:

- the bottom half of the product photograph
- the `PHOTO 1 OF 1` counter
- the `<h1>` — **`GREY WASH OG JEANS`**
- the price — **`£60.00`**
- the whole size row — `XS S M L XL`
- the sticky buy bar, including `CHECKOUT NOW`

In other words, on a phone a first-time visitor arriving on a product page sees a photograph
and a cookie notice. **The product's name, its price, its sizes and both buy buttons are all
behind the banner.** They have to deal with the banner before they can see what the thing
costs.

Getting rid of it is one tap on `Accept` or `Decline`; it goes immediately, does not come
back on the next page, and does not reappear later in the session.

This is not in the theme — it is Shopify's own privacy banner, and `SPEC.md §10` still lists
"No cookie banner" as an open item, so it has appeared since that file was written.

**Verdict:** partly — it works as a consent banner and it is one tap to clear, but on a phone
product page it covers the price.

**Shopper cost:** Every first-time mobile visitor landing on a product page — which is most
paid and social traffic — has the price and size row hidden until they interact with a legal
notice.

**Evidence:** `audit/screens/pdpcore-01-first-visit-banner.png`,
`audit/screens/pdpcore-02-banner-over-buybox.png`,
`audit/screens/pdpcore-03-after-accept.png` (one tap and it is gone).

---

## Surprises

- **The two headline products have one photograph each.** `cb1-wash-jeans` at £60 and
  `charcoal-cellblock-crewneck` at £50 both read `PHOTO 1 OF 1`. Six of twelve products have
  a single image.
- **The image masters are ~390 pixels square.** The theme requests `width=1400` and gets a
  390-px file back, so every product photo on a modern phone is upscaled roughly 2.5×. No
  amount of theme work fixes this; the originals have to be re-uploaded.
- **The notify form cannot be completed.** Pressing `NOTIFY ME` raises a blank hCaptcha
  panel over the phone screen. Two attempts, two sessions, no confirmation, no error, address
  left sitting in the field.
- **The four accordions are not mutually exclusive**, contrary to `SPEC.md §3.5` — and they
  are not `<details>` elements either.
- **The sticky bar's appear-on-scroll never happens.** It is on screen from scroll position
  zero and stays there even when the real `ADD TO BAG` is centre-screen.
- **The two t-shirts have no `MORE FROM THIS DROP` at all** — no tiles and no heading.
- **A 4-pixel purple square** marks the low-stock size with no legend anywhere.
- **A consent banner now covers 43% of a first-visit phone product page**, including the
  price and the size row. `SPEC.md §10` still records "No cookie banner".

## Missing

- Any way to enlarge a product photo. No zoom, no lightbox, no tap-to-expand, and no larger
  master behind the one that is served.
- Front / detail / on-body photography on the two most expensive garments.
- Any statement of **when** a restock notification would arrive — the panel promises nothing
  beyond `TELL ME WHEN THIS SIZE IS BACK`.
- Any shop-authored validation message on the notify form. Both errors I saw were Chrome's
  own bubbles.
- A returns or "free UK shipping over £20" line anywhere in the buy spine — it exists only
  inside a closed accordion and in the status bar.
- Onward navigation from `evil-clive-tee` and `crxst-rz-t-shirt`.

## Contradictions

- **"Sold out" vs "leaves today."** With `SIZE M IS SOLD OUT` on screen in red, the page
  still says `Order before 18:00 and it ships today (Mon–Sat)` and
  `> Ordered now — leaves today`, and the sticky bar still offers `CHECKOUT NOW` next to the
  greyed `SOLD OUT`.
- **The spec vs the page on accordions.** `SPEC.md §3.5`: "all `<details name>` so they are
  mutually exclusive with no JS". On the page all four stay open together.
- **The spec vs the page on the sticky bar.** Built to show "only while the primary control
  is off-screen"; observed on screen at every scroll position including alongside the primary
  control.
- **The spec vs the store on cookies.** `SPEC.md §10`: "No cookie banner". There is one, and
  on a phone it covers the price.
- *(Known, ref: SPEC §10)* The custody step promises `UK 1–2 working days` while a product
  description elsewhere quotes 9–16 days; confirmed the custody wording is the one shown on
  the PDP.

## Works and must be protected

- **The sold-out size behaviour itself.** Dashed border, struck-through label, still
  tappable, red `SIZE M IS SOLD OUT`, button swaps to `SOLD OUT`, notify panel appears —
  this is better than most shops manage and §9.3 is right to protect it.
- **The chain-of-custody copy.** All four steps, verbatim above. Specific, unhedged, names a
  real return address and a real courier. Do not soften it.
- **Plain-English buy controls.** `£60.00`, `SIZE`, `XS S M L XL`, `IN STOCK`,
  `SELECT A SIZE`, `ADD TO BAG`, `SOLD OUT`, `> Added — 1 in bag  View bag`. Not one word of
  fiction in the part of the page that takes money — exactly as `§0` and `§9.2` require.
- **Deep-linkable sizes.** Every size tap writes `?variant=` and the link reopens with that
  size selected and in stock. Shareable, and it survives a reload.
- **The dispatch line as a live readout, not a countdown.** Correct at 17:0x on a Thursday,
  computed in the shop's timezone, with no manufactured urgency.
- **`ADD TO BAG` staying on the page**, with the count moving `[0]` → `[1]` and a
  `View bag` link rather than an interstitial drawer.
- **`PHOTO 1 OF n`.** It tells the truth, including when the truth is `1 OF 1`.
