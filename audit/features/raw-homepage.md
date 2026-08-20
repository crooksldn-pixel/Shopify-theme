# raw-homepage — CROOKSLDN homepage, shopped on a 390×844 phone

All measurements are in **screenfuls of 390×844** (1 screenful = 844px).
Everything below was observed through the browser against the deployed staging
theme, GB market, GBP.

---

### Cold arrival — what is on screen in the first ten seconds

**Should:** the shopper lands on a terminal, the boot line types itself in, the
page becomes readable quickly.

**Did:** in order —

| When | What arrives |
|---|---|
| ~0.7s | Status bar `FREE UK SHIPPING OVER £20 — ORDER BY 18:00 FOR SAME-DAY DISPATCH`, the cuffs mark, `CATALOGUE SEARCH BAG [0] LIGHT MODE MENU`, and the boot line **mid-type**: `> 12 PRODUCTS AVAIL`. The wordmark area is still blank. **The cookie notice is already up**, covering the bottom 359px of the 844px screen. |
| ~1.5s | Boot line complete — `> 12 PRODUCTS AVAILABLE TO PURCHASE` — plus `CROOKSLDN`, `OWN THE STREETS™` and the `CATALOGUE` button. **The page is readable at about a second and a half.** No blank-screen wait. |
| ~8s | The status bar swaps to `12 PRODUCTS CURRENTLY ONLINE` (ref D1 — 8s, setting inert). |
| 10s | Nothing else has happened. The cookie notice has not moved. |
| **~39s** | With no interaction at all, a full-screen overlay takes the page: `CRACK THE CUFFS.` (its own entry below). |

So a cold arrival's first ten seconds are: shipping promise → shop controls →
typed boot line → wordmark → one button → **and a cookie notice sitting over the
bottom 43% of the screen the entire time**.

**Verdict:** works (the hero itself is fast and clean) — but see the cookie
notice entry, which owns most of the landing screen.

**Evidence:** `audit/screens/homepage-03-cold-700ms.png` (boot line mid-type,
wordmark not yet drawn), `audit/screens/homepage-03-cold-1500ms.png` (complete),
`audit/screens/homepage-01-landing.png`, `audit/screens/homepage-02-at-10s.png`.

---

### Hero — boot line, wordmark, tagline

**Should:** wordmark, tagline, boot lines typed on load, `[count]` reading live
product count (SPEC §3.3).

**Did:** exactly one boot line, `> 12 PRODUCTS AVAILABLE TO PURCHASE`, and the
count is real (12 products are in the register below). It types character by
character — at 700ms it reads `> 12 PRODUCTS AVAIL` — and finishes by ~1.5s.
`CROOKSLDN` is the page's `h1`, plain text, not a link. `OWN THE STREETS™` sits
under it. The whole hero is 0.16→0.55 screenfuls tall.

**Verdict:** works.

**Evidence:** `audit/screens/homepage-A1-fold-clean.png`,
`audit/screens/homepage-03-cold-700ms.png`.

---

### Hero — the buttons

**Should:** up to two buttons (SPEC §3.3).

**Did:** there is **one** button, labelled `CATALOGUE`. It is an in-page jump
(`href="#products"`) to the catalogue section on the same page. Following it
leaves the shopper on the homepage; the destination has the same headings
(`CROOKSLDN`, `CATALOGUE`, `EVERY ORDER SHIPS LIKE THIS`, `REGISTER AS
INFORMANT`) and the same 12 product links. The second button is not configured.

**Verdict:** partly.

**Shopper cost:** the hero's only call to action moves the page about half a
screen, to a heading (`CATALOGUE`, `12 ITEMS`) that is **already visible on the
landing screen** once the cookie notice is gone. A shopper who taps it gets
almost nothing they did not already have. There is no hero route to NEW, to a
drop, or to anything the shopper hasn't already been shown — the one navigational
decision the homepage offers above the fold is a no-op.

**Evidence:** `audit/screens/homepage-A1-fold-clean.png` (the `CATALOGUE` button
and the `CATALOGUE / 12 ITEMS` heading are both on the first screen),
`audit/screens/homepage-60-dest-catalogue.png`.

---

### Packaging — `EVERY ORDER SHIPS LIKE THIS`

**Should:** a packaging photograph with a numbered manifest beside it, heading
`EVERY ORDER SHIPS LIKE THIS` (SPEC §3.8).

**Did:** reads, in full:

```
PROPERTY BAG
EVERY ORDER SHIPS LIKE THIS
Sealed, tagged and numbered before it leaves us. Nothing here is an extra you pay for.

01  EVIDENCE TAG      Numbered, seized by CROOKS LDN, QR to verify.
02  SECURITY SEAL     Pull-tight, stamped with the cuffs.
03  CUFF KEYRING *    Miniature cuffs, on the ring.

* CONTRABAND 03 SHIPS WITH SWEAT BOTTOMS ONLY.
```

The photograph is the three real items on black with yellow evidence tents
numbered **1, 2, 3** — the tents map one-to-one onto the manifest numbers, so the
list and the picture teach each other without a caption. Alt text is written
properly. The section is 0.82 screenfuls tall and needs no interaction.

**Verdict:** works — and the line doing the selling is
`Nothing here is an extra you pay for.` That single sentence turns three props
into three free things you get, which is the only "reason to buy" argument
anywhere on the homepage.

**Evidence:** `audit/screens/homepage-A3-packaging-clean.png`,
`audit/screens/homepage-A4-packaging-manifest.png`.

---

### Packaging — the footnote asterisk

**Should:** a footnote carried per item (SPEC §3.8).

**Did:** the asterisk sits on `CUFF KEYRING *` and resolves to
`* CONTRABAND 03 SHIPS WITH SWEAT BOTTOMS ONLY.`, set in the dimmest grey on
the page, smaller than everything above it.

**Verdict:** partly — the mechanism works, the sentence does not.

**Shopper cost:** two words in it refer to things a first-time shopper has never
seen.

1. **`CONTRABAND 03`** — nothing in the section, or on the homepage, is called
   "contraband". The list is labelled `01 / 02 / 03`. The shopper has to guess
   that "CONTRABAND 03" means "item 03 in the list you just read", i.e. the cuff
   keyring.
2. **`SWEAT BOTTOMS`** — no product on this site is called that. The register
   lists `CHARCOAL CELLBLOCK SHORTS` (SWEATS), `V2 BAGGIES` (SWEATS) and
   `CHARCOAL CELLBLOCK CREWNECK` (SWEATS). A shopper who wants the keyring
   cannot tell which of those qualifies — shorts? baggies? both? — and the
   footnote is where they would have to work it out, in the smallest, faintest
   type in the section.

The net effect is that the one item with a condition attached is the one item a
shopper cannot act on. Naming the qualifying products in plain words
(`* THE CUFF KEYRING ONLY SHIPS WITH SWEAT SHORTS AND BAGGIES.`) fits the design
law exactly — it is a copy change, nothing else.

**Evidence:** `audit/screens/homepage-A4-packaging-manifest.png` — the exact
string is `* CONTRABAND 03 SHIPS WITH SWEAT BOTTOMS ONLY.`

---

### Informant intake — what it asks for, and what it promises

**Should:** SMS-first signup, email optional, real customer + SMS consent via the
Shopify Forms app block (SPEC §3.9).

**Did:** the theme's own copy is good and honest:

- `REGISTER AS INFORMANT`
- `Drops go to the register before they go public. One message per drop, nothing else.`
- below the form: `One text per drop. Reply STOP to leave the register at any time. We do not sell it.`

The form itself is the app block, and it reads, top to bottom: a violet
**`Continue with Shop`** button, `or`, a UK-flag country picker, a white rounded
field labelled **`NUMBA`** pre-filled `+44`, a white rounded field `Email`, then a
filled purple **`ENTER`**.

**Verdict:** partly.

**Shopper cost:** what you're signing up *for* is clear (one text per drop, early
access, STOP to leave). What you *get* is not — there is no incentive named, no
"first look at 12 pieces", nothing. And the email field is unlabelled as
optional and never says what the email would be used for, so a cautious shopper
has no basis to fill it in. `NUMBA` is a joke that costs nothing until something
goes wrong — see below.

**Evidence:** `audit/screens/homepage-A5-intake-clean.png`,
`audit/screens/homepage-A6-intake-lower.png`.

---

### Informant intake — tested with bad input

Every attempt below was typed key-by-key into the live form and submitted with
`ENTER`. Quoted strings are exactly what appeared.

| What I typed | What the form said back |
|---|---|
| nothing at all (field left at `+44 `) | **`Phone number is required`** — red, under the field; the country picker gets a red outline |
| `1234` (field showed `+44 1234`) | **nothing.** No message at 3s, none at 8s, none at 10s. |
| `abcdefg` | the letters are silently refused, the field is left showing `+44`; on `ENTER`, **nothing** — not even `Phone number is required` |
| `07700900123` — a valid UK mobile (field showed `+44 07700 900123`) | **nothing.** No confirmation, no thank-you, no "check your phone". The number is still sitting in the box. |
| the **same number a second time**, on a fresh page load | **nothing** — identical to the first time |
| `07700900124` + `buyer+test@example.com` | **nothing** |
| `07700900125` + `buyer@` | **`Email is invalid`** |
| email only, no number | **`Phone number is required`** |

So the only two things the intake ever says are `Phone number is required` and
`Email is invalid`. **A good number and a junk number produce exactly the same
result: silence.**

**Verdict:** broken.

**Shopper cost:** you type your mobile number into a brand you have just met,
press the button, and the page does not change. There is no way to tell whether
you joined. The natural next move is to press `ENTER` again, and then to give up
and assume the site is broken — having handed over a phone number either way.
And `+44 1234` is accepted as readily as a real number, so a mistyped digit is
never caught.

**And the field sets the shopper up to get it wrong.** It is pre-filled `+44`.
Type your number the way every British person types it — `07700900123` — and the
box ends up reading **`+44 07700 900123`**: country code *and* the trunk zero, a
number that is not dialable in that form. The form accepts it without a murmur.
The two ways a shopper is most likely to enter a UK mobile (with the leading 0,
or without) produce different values and neither is checked.

Two smaller cuts in the same place: the field is labelled `NUMBA` but the error
calls it `Phone number` — the form is telling you to fix a field that is not on
screen under that name. And the error is the only red on the homepage, in a
sans-serif face that appears nowhere else.

**Evidence:** `audit/screens/homepage-21-intake-empty.png`
(`Phone number is required`), `audit/screens/homepage-D1-email-invalid.png`
(`Email is invalid`, whole section in one screen),
`audit/screens/homepage-B2-good-number-1-typed.png`
(`+44 07700 900123` in the field), `audit/screens/homepage-B2-good-number-3-after-8s.png`
and `audit/screens/homepage-B3-same-again-3-after-8s.png` (eight seconds after
`ENTER`, nothing has been said).

---

### Informant intake — the bot check that swallows the submission

**Should:** press `ENTER`, get signed up.

**Did:** pressing `ENTER` dims the whole page and opens a **blank white panel**
over the section. It is the form's bot check — an hCaptcha challenge box. In this
audit environment it never draws anything and never resolves: the page stays
dimmed with an empty white rectangle where the form was, and forty seconds later
the form is still sitting there unchanged.

**Verdict:** broken *as seen*, with one honest caveat.

**Caveat:** this environment's egress could not reach hCaptcha
(`401 api.hcaptcha.com/authenticate`, and a blocked asset request), so I cannot
say what a shopper on a clean network sees inside that box. What is *not*
environment-specific: the store puts a bot check between a shopper and a phone
number signup, it opens as a large blank panel with no words around it, and if it
fails for any reason — blocked, slow, ad-blocker, poor signal — the shopper is
left staring at an empty white rectangle with no message at all.

**Shopper cost:** on any connection where that check does not complete, the
signup silently cannot be completed and nothing on screen says so.

**Evidence:** `audit/screens/homepage-B1-wrong-number-2-after-3s.png` and
`audit/screens/homepage-B2-good-number-3-after-8s.png` — the greyed page and the
empty white panel; `audit/screens/homepage-C2-after-enter-40s.png` at forty
seconds.

---

### Informant intake — it is the most Shopify-looking thing on the site

**Should:** radius 0, 1px borders, no shadows, no gradients, monospace on
near-black; the proposition is that it does not look like a Shopify store.

**Did:** the intake contains a full-width **`Continue with Shop`** button in Shop
violet with the Shop wordmark, two **white rounded-cornered** input boxes with
floating sans-serif labels, a rounded purple `ENTER`, a red error message and a
blue focus ring. It sits inside a 1px-bordered black monospace panel, directly
under a heading in the terminal face.

**Verdict:** partly (it functions as a form; it breaks the house style outright).

**Shopper cost:** this is the one place on the homepage where the illusion drops.
Everything above it is a police evidence terminal; the signup is a stock Shopify
form with a Shop Pay button on top. It is also the only element on the page with
rounded corners.

**Evidence:** `audit/screens/homepage-D1-email-invalid.png` — the whole section in
one screen: terminal heading, Shop-violet button, two white rounded boxes, red
error, purple `ENTER`. Also `audit/screens/homepage-A5-intake-clean.png`.

---

### Lookbook block

**Should:** (assigned as an area to check.)

**Did:** **there is no lookbook on the homepage.** The word does not appear in
any text, any link or anywhere in the page's markup. The homepage carries, in
order: status bar, header, a carriage section that renders nothing, hero,
catalogue, packaging, informant intake, an empty section, footer. No editorial
block, no "world of CROOKSLDN", no second photograph.

**Verdict:** absent.

**Shopper cost:** the only photograph on the entire homepage is the packaging
shot. Every product is a flat cut-out on black. Nothing shows the clothes being
worn, in London, on a person — so a shopper who wants to know what the label
*looks like* has no answer on the homepage. (The catalogue's `On model` toggle
exists, but that is the catalogue area's call.)

**Evidence:** `audit/screens/homepage-A9-full.png` (whole page),
`audit/screens/homepage-A7-footer.png`.

---

### The order a shopper meets things, and where the first product appears

**Did:** the homepage is **4890px — 5.79 screenfuls** on a 390×844 phone.

| Screenfuls | Section | What it says |
|---|---|---|
| 0.00 – 0.03 | Status bar | `FREE UK SHIPPING OVER £20 — ORDER BY 18:00 FOR SAME-DAY DISPATCH` ↔ `12 PRODUCTS CURRENTLY ONLINE` |
| 0.03 – 0.16 | Header | cuffs mark, `CATALOGUE SEARCH BAG [0] LIGHT MODE MENU` |
| 0.16 – 0.55 | Hero | `> 12 PRODUCTS AVAILABLE TO PURCHASE`, `CROOKSLDN`, `OWN THE STREETS™`, `CATALOGUE` |
| 0.55 – 3.09 | Catalogue | `CATALOGUE / 12 ITEMS`, `FLAT · ON MODEL`, `OUTLINE`, filter chips, 12 cards |
| 3.09 – 3.91 | Packaging | `EVERY ORDER SHIPS LIKE THIS` |
| 3.91 – 4.70 | Informant intake | `REGISTER AS INFORMANT` |
| 4.70 – 5.79 | Footer | `SHOP / INFORMATION / CONTACT / GAME`, `EVIDENCE TERMINAL V0.2 // CROOKSLDN // OWN THE STREETS™ // © 2026` |

**The first product appears at 0.90 screenfuls.** The `NO. 01 SWEATS` and
`NO. 02 SWEATS` card headers are in the *first* screenful — the last 87px of it —
with the product images, names and prices arriving in the second. That is an
unusually short run-up for a fashion homepage and it is the right decision.

**But on a cold arrival the shopper sees no product at all**, because the cookie
notice covers everything below 485px — the whole first product row sits behind
it. The first product is only in view once the notice has been answered.

The carriage section renders nothing on the homepage (0px tall), so the only
mention of shipping before the footer is the rotating status-bar line.

**Verdict:** works, conditional on the cookie notice.

**Evidence:** landing view `audit/screens/homepage-01-landing.png` (with the
notice) and `audit/screens/homepage-A1-fold-clean.png` (without);
first-product view `audit/screens/homepage-04-first-product.png` (with the
notice on top of the cards) and `audit/screens/homepage-A2-first-product-clean.png`.

---

### Cookie consent notice

**Should:** the standing brief lists "No cookie banner" as a known item.

**Did:** there **is** one, Shopify's own, and it is the largest single thing on
the landing screen. It occupies the bottom **359px of 844** — 43% of the phone —
from the moment the page paints, and reads:

```
COOKIE CONSENT
We and our partners, including Shopify, use cookies and other technologies to
personalize your experience, show you ads, and perform analytics, and we will
not use cookies or other technologies for these purposes unless you accept them.
Learn more in our Privacy Policy
Accept
Decline
Manage preferences
```

It does not auto-dismiss (still there at 10.5s). `Decline` removes it and it does
not come back on the next load. It follows the shopper down the page, so it also
covers the packaging manifest and, at the natural reading position, the intake's
`ENTER` button.

**Verdict:** works mechanically; costs the landing screen.

**Shopper cost:** a cold arrival is asked to make a legal decision before it is
shown a single product, and 43% of the first screen — the half that would
otherwise hold the first two cards — is spent on it. It also lands on top of the
one button the intake needs the shopper to press.

**Evidence:** `audit/screens/homepage-01-landing.png`,
`audit/screens/homepage-04-first-product.png`,
`audit/screens/homepage-20-intake-with-cookie-banner.png` (the `ENTER` button is
behind the notice at that scroll position).

---

### `CRACK THE CUFFS.` overlay at ~39 seconds

**Did:** with no interaction whatsoever, **38.9 seconds** after landing, a
full-screen overlay takes the page (it is an embedded third-party app,
`crackthecuffs.base44.app`, sized to the whole viewport). It reads:

```
CRACK THE CUFFS.
10% off your first order if you do. Three tumblers. Tap each one at the right moment.
RUN IT
NOT NOW
One code per player. Attempts unlimited. Code expires in 20 minutes.
(this drop closes 15.09)
```

It does not appear in the first ten seconds, and it did not return on the next
page view. It is drawn in house style — mono, square, near-black — so it does not
break the design law.

**Verdict:** works (it fires, it closes) — but the *timing* is the problem.

**Shopper cost:** thirty-nine seconds is almost exactly how long it takes to read
the register, reach the packaging section and start filling in the informant
form. In three separate runs it landed on top of the packaging manifest or on the
intake, once arriving while the form was being filled in. It is a discount offer interrupting
the two sections that do the selling. (The overlay itself belongs to the
drawer/game area; recorded here because it is what a homepage shopper meets.)

**Evidence:** `audit/screens/homepage-95-ctc-overlay.png`,
`audit/screens/homepage-84-packaging-manifest.png` and
`audit/screens/homepage-92-duplicate.png` — the same overlay sitting over the
packaging manifest and over the intake mid-form.

---

### Status bar

**Did:** rotates between `FREE UK SHIPPING OVER £20 — ORDER BY 18:00 FOR
SAME-DAY DISPATCH` and `12 PRODUCTS CURRENTLY ONLINE` on an ~8s cycle (ref D1).
Both lines are facts, not urgency theatre.

**Verdict:** works.

**Evidence:** `audit/screens/homepage-A1-fold-clean.png`.

---

## Surprises

- **A good phone number gets nothing back.** Type a real UK mobile, press
  `ENTER`, and the page says nothing — no confirmation, ever. The only two
  messages the intake can produce are `Phone number is required` and
  `Email is invalid`. The owner almost certainly believes this form confirms.
- **The submit button opens a blank white box.** `ENTER` triggers the form's
  hCaptcha bot check, which renders as a large empty white panel over a dimmed
  page with no words anywhere near it. In this environment it never resolved.
- **The intake is the one place the Shopify mask slips**: a Shop-violet
  `Continue with Shop` button, two white rounded input boxes, a blue focus ring
  and red sans-serif error text, in the middle of a black monospace terminal.
- **The phone field is labelled `NUMBA`** while its own error message calls it
  `Phone number`.
- **`+44 1234` is accepted exactly like a real number** — no shape check at all.
- **There is a cookie notice**, contradicting the standing brief's known-items
  list, and it owns 43% of the landing screen and hides the entire first product
  row on arrival.
- **The `CRACK THE CUFFS.` overlay fires at 38.9 seconds** — i.e. right when the
  shopper reaches the packaging section or the signup form, not on arrival.
- **The hero's only button goes nowhere new** — `#products`, to a heading already
  visible on the same screen.
- **The carriage section is on the homepage but renders nothing at all.**

## Missing

- Any confirmation after signing up to the register — a line as short as
  `LOGGED. WATCH YOUR PHONE.` would close the loop.
- Any statement of what the informant register *gives* you beyond early notice —
  no incentive, no number, no "first look".
- A second hero route. One button, and it is an in-page anchor.
- Any sentence on the homepage saying what CROOKSLDN is or where it ships from.
  `OWN THE STREETS™` is a slogan; the only prose on the page is the packaging
  paragraph.
- Any photograph other than the packaging shot — no lookbook, no clothes on a
  person, nothing at all between the register and the footer.
- A plain-English resolution of `CONTRABAND 03` and `SWEAT BOTTOMS` in the
  packaging footnote.

## Contradictions

- The field says **`NUMBA`**; the error under it says **`Phone number is
  required`**. Two names for one box, and the name in the error is not on screen.
- The manifest item says **`03  CUFF KEYRING *`**; the footnote calls the same
  thing **`CONTRABAND 03`**. The word "contraband" appears nowhere else on the
  homepage.
- The footnote says the keyring ships with **`SWEAT BOTTOMS`**; the register
  sells `CHARCOAL CELLBLOCK SHORTS`, `V2 BAGGIES` and `CHARCOAL CELLBLOCK
  CREWNECK`, all filed under `SWEATS`. Nothing on the site is called "sweat
  bottoms".
- The status bar promises **`FREE UK SHIPPING OVER £20`** flat; SPEC §3.7's real
  rate card is two tiers — free Tracked 48 over £20, free Tracked 24 over £70.
  The homepage states the cheaper half as though it were the whole offer.
  (Carriage is another area's call; flagged here because the homepage is where
  the single-tier claim is made.)

## Works and must be protected

- **The packaging section.** `EVERY ORDER SHIPS LIKE THIS`, a real photograph
  with numbered evidence tents that match the numbered manifest, and the line
  `Nothing here is an extra you pay for.` It is the only argument-to-buy on the
  homepage and it is a good one.
- **The first product at 0.90 screenfuls.** `NO. 01` and `NO. 02` are on the
  first screen; every card states price and stock in words. No carousel, no
  hero-image tax.
- **The boot line typing.** Readable at ~1.5s, no blank-screen wait, and the
  count in it is real.
- **The intake's own copy** — `One text per drop. Reply STOP to leave the
  register at any time. We do not sell it.` — which is more honest than most SMS
  signups. It deserves a form that works underneath it.
- **The status bar carrying two facts** instead of a countdown.
