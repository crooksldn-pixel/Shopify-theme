# raw-pdp-core — the product record

Shopped on the staging theme (`202053779799`), GB market, GBP. Mobile is an iPhone-class
390×844 at 3× unless a line says desktop. Products used: **`cb1-wash-jeans`** (GREY WASH OG
JEANS, £60), **`charcoal-cellblock-crewneck`** (£50), **`v2-baggies`** (£60 — the only
product in the shop with sold-out sizes), plus `charcoal-cellblock-shorts` (£45) and sweeps
across all twelve products where a count was needed.

Clock during the run: **Thursday 20 August 2026, 16:47–17:40 British Summer Time.**

---

### Gallery — how many photos, and whether you can see the fabric

**Should:** A £60 garment sold with no fitting room should be photographed enough times, and
at enough resolution, that a stranger can decide what it is made of.

**Did:** The gallery is a single large square photo, a line reading `PHOTO 1 OF 3`, and a row
of thumbnails underneath. It is clean, it reads well, and the controls all work (see the next
entry). Two things are wrong with what it is showing.

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

**Swiping** works on a phone. A real left swipe across the shorts' photo took it
`PHOTO 1 OF 3` → `2 OF 3` → `3 OF 3`, a right swipe went back to `2 OF 3`, and it stops at
the last photo rather than wrapping round. The thumbnail highlight follows the swipe. Tap
targets on the thumbnails are 64×64 — comfortably thumb-sized.

Two notes. The main photo is not a horizontal scroller, so a *mouse drag* on desktop moves
nothing (that is the right call — mouse users have the arrow keys and the thumbnails). And
where a product has only one photo, no thumbnail row renders at all and `PHOTO 1 OF 1` is
the only cue that there is nothing more to see. Honest, if bleak.

**Verdict:** works

**Evidence:** `audit/screens/pdpcore-120-swipe-left1.png`,
`audit/screens/pdpcore-120-swipe-left2.png`, `audit/screens/pdpcore-121-swipe-right.png`,
`audit/screens/pdpcore-130-thumbtap-1.png`,
`audit/screens/pdpcore-102-desktop-shorts-gallery.png`,
`audit/screens/pdpcore-80-gal-charcoal-cellblock-shorts.png`.

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

**Verdict:** works

**Evidence:** `audit/screens/pdpcore-30-crewneck-size-XL.png`,
`audit/screens/pdpcore-31-jeans-size-L.png`, `audit/screens/pdpcore-32-jeans-deeplink.png`.

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

**(2) The sticky bar physically clips the `NOTIFY ME` button.** With M selected and the
notify panel open, the purple `NOTIFY ME` button runs from y=724 to y=776 on an 844-px
screen and the sticky bar starts at y=775 — its bottom edge disappears under the bar. The
one control the page wants pressed in this state is the one being sat on by furniture.

*(Checked and cleared: the sticky bar's `CHECKOUT NOW` beside `SOLD OUT` is greyed and inert —
pressing it does nothing and adds nothing to the bag. It reads as dead rather than as a trap.)*

**Verdict:** partly

**Shopper cost:** The shopper is told "sold out" and "leaves today" in the same eyeful, and
the button they need is clipped by the bar.

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
an hCaptcha badge in the bottom-right corner and the words `Protected by hCaptcha` at the
foot of the page. In this audit environment the challenge itself never rendered — the box
stayed empty — so I could not complete it. I tried it on a fresh session as the first thing I
did on the page, waited eighteen seconds, and got the same empty panel. **The form never
posted anything**: I watched the traffic and nothing left the browser for `/contact` at all,
only Shopify's own telemetry. **I never reached a confirmation of any kind.** The page is
unchanged afterwards: the same `SIZE XL IS SOLD OUT`, the same open panel, my address still
sitting in the field, no thank-you, no error, no e-mail promised.

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
`audit/screens/pdpcore-74b-notify-valid-after-full.png`,
`audit/screens/pdpcore-111-notify-clean-after.png` and
`audit/screens/pdpcore-112-notify-clean-18s.png` (clean session, first action on the page,
eighteen seconds later — nothing has happened).

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
is the button's own label `SELECT A SIZE`, and a small line reading `Select Size` —
sentence case, and a dimmer grey than the body text around it — sitting **168 pixels above**
the button, immediately under the size row.

Where does the eye go? Nowhere. The tap produces no event to follow. The message *is* near
the size row, which is the right place for it — but it was already there before the tap, and
it does not change, flash, or move when you press. A shopper who has just tapped a dead
button taps it again.

Keyboard shoppers get a better deal by accident: because the button is genuinely disabled,
tabbing down the page steps `SIZE GUIDE` → the set checkbox → `SPECIFICATION`, skipping the
buy button entirely. It is never reachable until it is real.

**Verdict:** partly — it is honest and it cannot mis-sell, but a tap on it is a completely
silent event.

**Shopper cost:** Small but real: a second and third tap on a dead control before the eye
travels back up to the size squares. Flashing the existing grey `Select Size` line, or
outlining the size row, on the dead tap would close it — no new colour, no radius, no shadow,
no new string.

**Evidence:** `audit/screens/pdpcore-21-jeans-after-nosize-press.png` and
`audit/screens/pdpcore-21b-jeans-nosize-viewport.png` — taken immediately after the tap; the
`SELECT A SIZE` button and the grey `Select Size` line are exactly as they were before it.

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

All four end up open at once. They do default closed, each opens on the first tap and closes
again on a second, so nothing is unreachable or stuck — but a shopper who opens all four
(exactly what someone deciding on a £60 purchase does) pushes `MORE FROM THIS DROP` a long
way down the page and has to scroll back up past four open panels to reach the size row.

Contents are real and specific, and different per product. `SPECIFICATION` on the jeans:
`FABRIC 14oz denim / CUT OG straight, mid rise / ORIGIN Made in Portugal / CARE Cold wash
inside out. Hang dry.` On the crewneck: `450gsm brushed fleece / Relaxed / Made in Portugal /
Cold wash. Do not tumble dry.` On the baggies: `500gsm cotton / Wide, full length`. No
lorem, no filler.

**One data problem inside them.** `V2 BAGGIES` (£60 wide sweatpants) and `GREY WASH OG JEANS`
(£60 straight denim) publish **byte-identical measurement tables** — the same
`XS 76.2 / 73.7 / 45.7` through `XL 96.5 / 81.3 / 55.9`, under the same column headings
`WAIST · INSEAM · LEG OPENING`. Two garments in different fabrics and different cuts cannot
have the same leg opening at every size. The crewneck's table is genuinely its own
(`CHEST · LENGTH · SHOULDER · SLEEVE`), so this is per-product data, not a broken component.
*(This is the placeholder-measurements item already on the known list — recording it here
because a shopper sizing the baggies is reading the jeans' numbers.)*

**Verdict:** partly — they work, they are not exclusive, and the spec says they should be.

**Evidence:** `audit/screens/pdpcore-40-acc-specification.png`,
`audit/screens/pdpcore-40-acc-item-description.png`,
`audit/screens/pdpcore-40-acc-measurements.png`,
`audit/screens/pdpcore-40-acc-chain-of-custody.png` — the last one shows all four panels open
simultaneously; `audit/screens/pdpcore-153-accordions-all-open.png`.

---

### `SIZE GUIDE` and the cm / inch toggle

**Should:** One tap, no modal, no PDF — and numbers a shopper can act on.

**Did:** Tapping `SIZE GUIDE` scrolled from 328 to 1212 and parked the `MEASUREMENTS`
heading at the very top of the screen with the panel already open. No modal, no overlay, no
download, nothing to dismiss — and the back-scroll to the size row is a short one because the
heading is at the top rather than the bottom. This is the best-executed control on the page.

The `CM` / `IN` toggle inside it works and converts honestly: `XS 76.2cm / 73.7cm / 45.7cm`
becomes `XS 30in / 29in / 18in`, and the method line rewrites itself from `…ALL MEASUREMENTS
IN CENTIMETRES.` to `…ALL MEASUREMENTS IN INCHES.` The method is stated —
`TRUE TO SIZE — WAIST, CHEST AND LEG MEASUREMENTS ARE TAKEN AROUND THE GARMENT` — which is
the one thing most size guides leave out.

**Verdict:** works

**Evidence:** `audit/screens/pdpcore-151-sizeguide.png`,
`audit/screens/pdpcore-152-measurements-inches.png`.

---

### Low stock

**Should:** Tell the truth about scarcity without inventing it.

**Did:** On `cb1-wash-jeans`, XL carries a **4×4-pixel purple square** in its top-right
corner and nothing else — no legend, no key, no tooltip anywhere on the page. Selecting XL
reveals what it meant: the stock line reads **`3 LEFT IN SIZE XL`**, in the same quiet grey
as the neutral `Select Size` text rather than the red used for sold out. That restraint is right and is exactly what §9.7 asks for — it is a real
number from real inventory, not a counter. But a shopper who never taps XL never learns that
the mark means anything, and four pixels is below the threshold at which anyone notices.

**Verdict:** partly

**Evidence:** `audit/screens/pdpcore-150-lowstock-xl.png`,
`audit/screens/pdpcore-101-desktop-jeans.png` (the unexplained mark on XL, nothing selected).

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
150, 300, 500, 800, 900, 1100, 1200, 1300, 1600, 1800 and the page bottom: at every single
one it is pinned at `top: 775` of an 844-px screen, 69 px tall, fully opaque. It is already
there before the shopper has scrolled at all.

The give-away is that the page *knows* it should be hiding. At scroll 500, 900 and 1100 the
real `ADD TO BAG` button is plainly on screen (its top at y=567, y=167, y=-33) and the theme
correctly marks the bar as hidden — and the bar stays visible anyway, because its own layout
rule outranks the hide. So the shopper gets both buttons at once: the screenshot of a
successful add shows the inline `ADD TO BAG` mid-screen and the sticky `ADD TO BAG` at the
foot of the same screen. This is a one-line CSS fix and the behaviour it restores is already
written.

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
on screen at the same time**), `audit/screens/pdpcore-140-sticky-doubled.png`,
`audit/screens/pdpcore-51-sticky-page-bottom.png`,
`audit/screens/pdpcore-11-baggies-soldout-M.png` (bar clipping `NOTIFY ME`).

---

### `MORE FROM THIS DROP` — and whether the product lists itself

**Should:** Related products that are actually related, and never the product you are already
looking at.

**Did:** **The product never lists itself.** I opened the tray on all twelve products and
compared every tile's link against the page's own path: zero self-links, everywhere.

It looks like it does, though, and that is worth knowing. Read the jeans page from the top
and it appears to end `…GREY WASH JORTS £50.00 / GREY WASH OG JEANS £60.00` — the product's
own name and price, immediately after the related tray. That last line is the **sticky bar**
sitting over the bottom of the tray, not a fourth tile. On a phone the bar covers the first
related tile at exactly the moment the shopper reaches the tray, so the section reads as one
tile short and one self-reference long.

The relations themselves are sound — they follow the collection. `cb1-wash-jeans` → the
other three denim pieces (`BLUE WASH OG JEANS`, `BLUE WASH JORTS`, `GREY WASH JORTS`);
`charcoal-cellblock-crewneck` → `CHARCOAL CELLBLOCK SHORTS` and `V2 BAGGIES` (both SWEATS);
`white-socks` → `BLACK/BLUE MOTIONTEC™ SOCKS` and `LARGE DUFFLE BAG` (accessories). Two or
three tiles each; nothing random, nothing from a different category.

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
back on the next page, and does not reappear later in the session. On desktop the same banner
takes 155 px of a 900-px window — 17% — and lands on empty space below the buy panel, so this
is a phone problem specifically.

This is not in the theme — it is Shopify's own privacy banner, and `SPEC.md §10` still lists
"No cookie banner" as an open item, so it has appeared since that file was written.

**Verdict:** partly — it works as a consent banner and it is one tap to clear, but on a phone
product page it covers the price.

**Shopper cost:** Every first-time mobile visitor landing on a product page — which is most
paid and social traffic — has the price and size row hidden until they interact with a legal
notice.

**Evidence:** `audit/screens/pdpcore-01-first-visit-banner.png`,
`audit/screens/pdpcore-02-banner-over-buybox.png`,
`audit/screens/pdpcore-03-after-accept.png` (one tap and it is gone),
`audit/screens/pdpcore-100-desktop-banner.png` (the desktop version, for contrast).

---

## Surprises

- **Seven of twelve products have exactly one photograph** — including `cb1-wash-jeans` at
  £60 and `charcoal-cellblock-crewneck` at £50, the two the brief names. Nothing in the shop
  has more than three. Both single-photo garments show one flat cut-out and no second angle.
- **There is no way to enlarge a photo at all** — not by tapping, double-tapping, hovering or
  clicking, on either device. Shopify is holding a 2048-px master for these images; the page
  never lets a shopper near it.
- **The notify form cannot be completed and never posts.** Pressing `NOTIFY ME` raises a
  blank hCaptcha panel over the phone screen. Three attempts across two sessions, one of them
  the first action on a clean page: no confirmation, no error, address left in the field, and
  nothing sent to `/contact` at all.
- **The four accordions are not mutually exclusive**, contrary to `SPEC.md §3.5` — and they
  are not `<details>` elements either. All four sit open at once.
- **The sticky bar's appear-on-scroll never happens.** The theme correctly marks it hidden
  while the real `ADD TO BAG` is on screen; a layout rule keeps it visible anyway, so both
  buttons are on screen together. One CSS line away from the behaviour that was designed.
- **The two t-shirts have no `MORE FROM THIS DROP` at all** — no tiles and no heading, on the
  two cheapest and most shareable garments.
- **`V2 BAGGIES` and `GREY WASH OG JEANS` publish identical measurement tables** — same
  waist, same inseam, same leg opening at every size, for a pair of wide sweats and a pair of
  straight jeans.
- **A 4-pixel purple square** is the only low-stock cue until you select the size, and there
  is no legend for it anywhere.
- **A consent banner now covers 43% of a first-visit phone product page**, including the
  title, price and size row. `SPEC.md §10` still records "No cookie banner".

## Missing

- Any way to enlarge a product photo — no zoom, no lightbox, no tap-to-expand.
- Front / detail / on-body photography on the two most expensive garments.
- Any statement of **when** a restock notification would arrive. The whole promise is
  `TELL ME WHEN THIS SIZE IS BACK`; there is no "we'll email you when it returns", no
  timeframe, and no word about what happens to the address.
- Any shop-authored validation message on the notify form. Both errors I saw were Chrome's
  own bubbles, in Chrome's typeface, in a rounded white box — the only non-CROOKSLDN pixels
  on the page.
- Any acknowledgement at all after a notify submission.
- A returns line or the "free UK shipping over £20" threshold anywhere in the buy spine — the
  first lives only inside a closed accordion, the second only in the status bar.
- Onward navigation from `evil-clive-tee` and `crxst-rz-t-shirt`.
- Any feedback when the disabled `SELECT A SIZE` button is tapped.

## Contradictions

- **"Sold out" vs "leaves today."** With `SIZE M IS SOLD OUT` on screen in red, the two lines
  directly above it still read `Order before 18:00 and it ships today (Mon–Sat)` and
  `> Ordered now — leaves today`.
- **The spec vs the page on accordions.** `SPEC.md §3.5`: "all `<details name>` so they are
  mutually exclusive with no JS". On the page they are buttons and all four stay open
  together.
- **The spec vs the page on the sticky bar.** Built to show "only while the primary control
  is off-screen"; observed on screen at every scroll position tested, including three where
  the primary control was plainly visible.
- **The spec vs the store on cookies.** `SPEC.md §10`: "No cookie banner". There is one, and
  on a phone it covers the price.
- **Two products, one size chart.** `V2 BAGGIES` and `GREY WASH OG JEANS` — different
  fabrics, different cuts, identical `WAIST · INSEAM · LEG OPENING` numbers at all five sizes.
  One of them is wrong and a shopper cannot tell which.
- *(Checked, no longer present)* The known "9-16 days delivery uk" line does not appear in
  any accordion on the three products I opened; `ITEM DESCRIPTION` on all three is clean and
  the custody step's `UK 1–2 working days` stands unchallenged on the PDP.

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
- **The dispatch line as a live readout, not a countdown.** Correct at 17:38 on a Thursday,
  computed in the shop's timezone, with no manufactured urgency.
- **`ADD TO BAG` staying on the page**, with the count moving `[0]` → `[1]` and a
  `View bag` link rather than an interstitial drawer.
- **`SIZE GUIDE`.** One tap, no modal, no PDF, lands the heading at the top of the screen
  with the panel already open — and the `CM` / `IN` toggle converts correctly (`76.2cm` →
  `30in`) and rewrites the method line with it.
- **The gallery's keyboard and touch handling.** Thumbnails are the first three stops in the
  tab order, labelled `Photo 1 of 3` / `Photo 2 of 3` / `Photo 3 of 3`; arrow keys walk the
  focused gallery and stop cleanly at both ends; a real phone swipe moves it and the active
  thumbnail follows. The component is better than the pictures in it.
- **Low stock stated as a number, not a scare.** `3 LEFT IN SIZE XL`, in neutral grey.
- **`PHOTO 1 OF n`.** It tells the truth, including when the truth is `1 OF 1`.
