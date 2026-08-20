# Header, drawer and the CASE 001 board — raw findings

Area key `header-drawer`. Mobile 390×844 (dpr 3), GB market, staging theme
`202053779799`, unless stated. Every quoted string is copied off the screen.
All screenshots cited were taken in this pass (`hdr-a*`, `hdr-d*`, `hdr-e*`).
The older `header-drawer-*` files in `audit/screens/` are from earlier aborted
runs; none of them is cited here.

---

### The header bar — what is in it and where each thing goes

**Should:** logo (with dark-mode flip), wordmark, `CATALOGUE`, `SEARCH`,
`ACCOUNT`, `BAG [n]`, `MENU`.

**Did:** on a 390px phone the bar wraps to two rows. Row one is the logo alone —
a white handcuffs mark, no text beside it. Row two, left to right:

> `CATALOGUE`  `SEARCH`  `BAG [0]`  `LIGHT MODE`  `MENU`

Walked, every destination:

| Control | Goes to | What you land on |
|---|---|---|
| handcuffs logo | `/` | homepage |
| `CATALOGUE` | `/collections/all` | h1 `ALL`, `12 ITEMS` |
| `SEARCH` | `/search` | a whole page, not an overlay |
| `BAG [0]` | `/cart` | `Your cart is empty` |
| `LIGHT MODE` | nothing — flips the theme | **not in the brief's list at all** |
| `MENU` | opens the drawer | a text trigger, no hamburger |

Two things the brief expected in the header are not in it:

- **There is no wordmark anywhere in the header.** The `CROOKSLDN` wordmark is a
  *fallback for when no logo is uploaded*, and a logo is uploaded, so it never
  renders. On the homepage the name is rescued by the hero `h1` (`CROOKSLDN`),
  but on a collection page, a product page, the cart, Questions or Terms the
  only thing naming the shop above the fold is a pair of handcuffs.
- **`ACCOUNT` is not in the header.** It is in the drawer's foot at `y=1044` in
  an 844-tall viewport — 200px below the fold of an already-opened drawer.

**Verdict:** partly

**Shopper cost:** a returning customer looking for their orders taps `MENU`,
scrolls past twelve category links and a video game, and only then finds
`ACCOUNT`. On every page except the homepage the shop is unnamed at the top.

**Evidence:** `audit/screens/hdr-a05-header-bar.png` — bar reads
`CATALOGUE SEARCH BAG [0] LIGHT MODE MENU`, status line above reads
`12 PRODUCTS CURRENTLY ONLINE`.

---

### Two type sizes in one header row

**Should:** one row of controls, one type treatment.

**Did:** the row is set at two different sizes, and the split follows whether
something happens to be a link or a button:

| Control | Element | Rendered size | Weight |
|---|---|---|---|
| `CATALOGUE` | `<a>` | **9px** | 500 |
| `SEARCH` | `<a>` | **9px** | 500 |
| `BAG [0]` | `<a>` | **9px** | 500 |
| `LIGHT MODE` | `<button>` | **13px** | 400 |
| `MENU` | `<button>` | **13px** | 400 |

Same typeface, 44% bigger, one notch lighter — sitting side by side in the same
44px-tall row. `MENU` and `LIGHT MODE` visibly loom over `CATALOGUE` and
`SEARCH`. The same split runs through the drawer: its heading `MENU` is 10px
while the `CLOSE` button beside it is 13px, and the drawer's own `ACCOUNT` and
`BAG` links at the foot drop back to 9px.

**Verdict:** broken (cosmetic, but in the one place the design cannot afford it)

**Shopper cost:** in a store whose entire pitch is typographic discipline —
`radius 0`, one mono face, everything aligned — the header reads as if two
people built it. It is the kind of detail that quietly withdraws the "this is
not a Shopify store" claim.

**Evidence:** `audit/screens/hdr-e01-header-row.png` and
`audit/screens/hdr-a12-after-escape.png` — compare `SEARCH` with `MENU` in the
same row; also `audit/screens/hdr-e02-drawer-head.png` for the drawer's
`MENU` (10px) beside `CLOSE` (13px).

---

### The drawer — opening it

**Should:** `MENU` opens a modal drawer; the trigger relabels to `CLOSE`; focus
moves in; the page behind locks.

**Did:** all of that. Tapping `MENU` opens a full-width panel; the header
trigger relabels to `CLOSE`; focus lands on the drawer's own `CLOSE` button;
`document.body` gets the scroll lock; the dialog carries
`role="dialog" aria-modal="true" aria-label="Main menu"`. The panel is
`390px` wide on a `390px` screen — it covers the whole viewport.

Read top to bottom, as first seen:

> `MENU` … `CLOSE`
> `SHOP` `ALL` `NEW` `TEES` `DENIM` `SWEATS` `TRACKSUITS` `ACCESSORIES`
> `TRACKING` `QUESTIONS` `TERMS` `CONTACT`
> [CASE 001 board] `PLAY CASE:001 NOW`
> `ACCOUNT` `BAG [0]`

**Verdict:** works

**Evidence:** the drawer as first seen on a genuine first visit, cookie banner
and all: `audit/screens/hdr-a07-drawer-first-seen.png`. The same drawer once
the banner has been answered: `audit/screens/hdr-e03-drawer-first-seen-clean.png`.

---

### Every link in the drawer, followed

**Should:** twelve menu links, a game panel, an account link and a bag link,
all landing somewhere real.

**Did:** all fourteen resolve. Nothing 404s, nothing lands on an empty page.

| Label | Goes to | Lands on |
|---|---|---|
| `SHOP` | `/collections/frontpage` | h1 `PRODUCTS`, `12 ITEMS` |
| `ALL` | `/collections/all` | h1 `ALL`, `12 ITEMS` |
| `NEW` | `/collections/new` | h1 `NEW`, `7 ITEMS` |
| `TEES` | `/collections/tees` | h1 `TEES`, `2 ITEMS` |
| `DENIM` | `/collections/denim` | h1 `DENIM`, `4 ITEMS` |
| `SWEATS` | `/collections/sweats` | h1 `SWEATS`, `3 ITEMS` |
| `TRACKSUITS` | `/collections/tracksuits` | h1 `TRACKSUITS`, `1 ITEMS` |
| `ACCESSORIES` | `/collections/accessories` | h1 `ACCESSORIES`, `3 ITEMS` |
| `TRACKING` | `/pages/tracking` | `CHAIN OF CUSTODY DATABASE ONLINE` |
| `QUESTIONS` | `/pages/faq` | h1 `COMMONLY ASKED QUESTIONS` |
| `TERMS` | `/pages/terms` | h1 `TERMS` |
| `CONTACT` | `/pages/contact` | h1 `CONTACT` |
| `PLAY CASE:001 NOW` | `crooks-case-break.base44.app` | new tab, see below |
| `ACCOUNT` | `/account` | redirects off-site to `friendsof.crooksldn.com` |
| `BAG [0]` | `/cart` | `Your cart is empty` |

Three things a shopper meets on the way:

- **`SHOP` and `ALL` are the same twelve products** under two names — `SHOP`
  arrives at a page headed `PRODUCTS`, `ALL` at a page headed `ALL`. The menu
  offers a choice that isn't one, and neither label matches the heading you land
  on in the first case.
- **`TRACKSUITS` reads `1 ITEMS`.**
- **`ACCOUNT` leaves the store's design entirely.** It redirects off-domain to
  `friendsof.crooksldn.com/authentication/…` and lands on a Shopify-hosted page
  titled `Sign in - CROOKSLDN`: white background, a generic bold sans `CROOKSLDN`
  centred at the top, `Sign in`, `Sign in or create an account`, a rounded
  blurple `Continue with shop` button, an `Email` field, and
  `By continuing, you agree to our Terms of service`. No CROOKSLDN header, no
  drawer, no mono, no black — and no link back to the shop. This is Shopify's
  hosted account surface and cannot be styled from the theme, but it is what
  two taps from the menu actually delivers, and it is the sharpest break with
  the design law a shopper can reach.

**Verdict:** works, with the three notes above

**Evidence:** `audit/screens/hdr-a07-drawer-first-seen.png`,
`audit/screens/hdr-d12-shop-tab-after-play.png` (drawer foot showing
`ACCOUNT BAG [0]`), `audit/screens/hdr-e11-account.png` (the sign-in page)

---

### Closing the drawer, four ways

**Should:** the close control, tapping the scrim, Escape, and browser Back.

**Did:** two of the four work, one is impossible on a phone, and the fourth
takes you off the page.

**(a) The `CLOSE` control — works.** Tapping `CLOSE` in the drawer head shuts
it, the header trigger relabels back to `MENU`, and the page is where you left
it. `audit/screens/hdr-a10-after-close-control.png`

**(b) Tapping the scrim — impossible on a phone.** The scrim element exists and
covers `0,0 → 390×844`, but the drawer panel is *also* `390` wide, so the scrim
is 100% behind it. I swept the whole scrim rectangle at 8px intervals looking
for a single point where a tap would land on the scrim rather than the panel:
there is none. On a 390px phone there is **no "tap outside to dismiss"** — the
gesture most people try first. The drawer stayed open.
`audit/screens/hdr-a11-after-scrim-tap.png` (drawer still open after the
attempt).

**(c) Escape — works.** Closes the drawer and returns focus to `MENU`, with a
visible lavender focus ring on it. `audit/screens/hdr-a12-after-escape.png`

**(d) Browser Back — does NOT close the drawer. It leaves the page.** Opening
the drawer does not push a history entry. From `/collections/all` with the
drawer open, Back navigated to the homepage: the drawer was gone, but so was
the collection. The shopper who opened the menu, changed their mind, and hit
Back has lost the page they were reading, not the menu.
`audit/screens/hdr-a13-drawer-open-on-collection.png` →
`audit/screens/hdr-a14-after-back.png`

**And on a first visit it is worse.** I opened a completely fresh tab, went
straight to the homepage (history length: 2 — the blank tab, then the store),
opened the drawer, and pressed Back. The result was **`about:blank`**. Not the
homepage with the drawer closed — a blank page, the site gone.
`audit/screens/hdr-d20-freshtab-drawer-open.png` →
`audit/screens/hdr-d21-freshtab-after-back.png`

**Verdict:** partly

**Shopper cost:** this is exactly the one-handed phone case, and the answer is
that Back does not close the drawer — it leaves. A shopper deep in
`/collections/denim` opens the menu to check something, decides not to, and
reaches for the two dismissals a phone user reaches for first: tap outside
(does nothing at all here) and the Back swipe (takes them off the page). Either
they hunt for the word `CLOSE` in the corner, or they lose their place. A
first-time visitor who lands on the homepage, opens the menu out of curiosity
and swipes back is off the site entirely, on a blank screen, with the shop
one more tap away than they expected.

---

### Closing it on a desktop — where the scrim does exist

**Should:** same four ways.

**Did:** on 1440×900 the drawer panel is 420px wide and pinned right, so there
are **1020px of exposed scrim** to the left of it. Clicking there closes the
drawer, as expected. So "tap outside to dismiss" is a desktop-only feature of
this drawer: it works on the device where people use Escape, and does not exist
on the device where it is the primary gesture.

**Verdict:** works on desktop, absent on mobile

**Evidence:** `audit/screens/hdr-d23-desktop-drawer.png` →
`audit/screens/hdr-d24-desktop-after-outside-click.png`

---

### The CASE 001 panel — the board

**Should:** an animated canvas board at the bottom of the drawer, loaded only on
first drawer open.

**Did:** exactly that, and it is genuinely good. `crooks-board.js` is **not**
requested until the drawer is first opened (0 requests before, 1 after), and the
board then animates: a pixel alley/cell grid in brick and purple, a thief moving
a fixed route, a helmeted officer patrolling below in hi-vis, gold `£` coins
being collected, an exit lit at the top right. Sampling the whole canvas ten
times over four seconds gave ten different frames, and the page was running a
full 61 frames per second. Two screenshots 3.4 seconds apart show the thief
moved from mid-board to the top-left corner and a coin was collected.

**Verdict:** works — and is the single best-crafted thing in this area

**Evidence:** the board panel in full —
`audit/screens/hdr-e04-case-panel-clean.png` (board, `PLAY CASE:001 NOW`, and
the `ACCOUNT BAG [0]` foot beneath it). Movement:
`audit/screens/hdr-d09-board-t0.png` and
`audit/screens/hdr-d11-board-t3400.png` — same panel 3.4s apart, thief moved
from mid-board to the top-left, a coin gone, the officer shifted left.

---

### `PLAY CASE:001 NOW` — where it lands and how you get back

**Should:** the button takes you to CASE 001.

**Did:** the whole panel is one link to `https://crooks-case-break.base44.app`
with `target="_blank" rel="noopener noreferrer"`. Tapping it opens a **new tab**
and the shop tab is untouched — still on `/`, drawer still open. So "getting
back to the shop" means using the browser's tab switcher; there is no link back.

The destination loads and is on-brand — mono type, purple, 1px rules:

> `> CROOKS PROPERTY DATABASE`
> `> UNAUTHORISED ACCESS DETECTED`
> `> CASE 001 AVAILABLE`
> `CASE 001: THE GETAWAY`
> `STATUS: DECLASSIFIED`
> `START CASE` · `LEADERBOARD` · `SOUND: ON`
> `EVIDENCE TERMINAL v0.1 // CROOKS UK`

Its only three controls are `START CASE`, `LEADERBOARD` and `SOUND: ON`. There
is **no link back to the shop from the game at all** — not a logo, not a "shop"
button, nothing. On a phone, closing that tab is the only route home, and a
shopper who arrived by tapping the panel may not realise a second tab was
opened.

**On O4 (art and destination out of step) — would a shopper actually notice?
No.** I followed it through. The destination's first screen is a title card with
no game art on it at all; pressing `START CASE` gives a second text screen, a
briefing panel, before any board appears. So there is nothing on screen to
compare with the picture they just tapped until they are two screens deep and
have stopped thinking about it.

Two small tells exist for anyone who looks:

- The game footer reads `EVIDENCE TERMINAL v0.1 // CROOKS UK`; the shop's own
  footer reads `EVIDENCE TERMINAL v0.2`.
- The drawer's board draws gold **£ coins**, and its own description calls them
  coins — while the game's briefing says `> Recover 3 evidence packages.`

Neither costs a sale and neither is likely to be spotted. As a shopper-facing
problem, O4 is not one.

**Verdict:** works, with no way back

**Shopper cost:** low for the tab (it survives), real for the game: someone who
plays and wants to buy has to know to close a tab. And the CTA sends people
*away* from the shop at the exact moment they were in the menu looking for
somewhere to go.

**Evidence:** `audit/screens/hdr-d12-shop-tab-after-play.png` (shop tab intact,
drawer still open), `audit/screens/hdr-d13-case001-landing.png` (the destination
and its three controls) and `audit/screens/hdr-e09-game-play.png` (the briefing
screen behind `CLEARANCE ACCEPTED`, still no board art visible).

---

### Q1 — the board is off the homepage. Does anything carry its weight, and would anyone find it?

**Should:** `show_board: false` on the hero; the board now lives in the drawer.

**Did:** the homepage hero is now three lines of type and one button, on a large
field of black:

> `> 12 PRODUCTS AVAILABLE TO PURCHASE`
> `CROOKSLDN`
> `OWN THE STREETS™`
> `[ CATALOGUE ]`

The hero occupies 321px of the 844px first screen and roughly half of that is
empty — the column the board used to fill has collapsed, and nothing moved in.
There is exactly one `<canvas>` left on the homepage and it belongs to the
drawer, not the page. **Nothing on the homepage carries the board's weight.**
The first screen is now a wordmark, a tagline and a purple button; the only
motion above the fold is the one-line status ticker rotating between
`FREE UK SHIPPING OVER £20 — ORDER BY 18:00 FOR SAME-DAY DISPATCH` and
`12 PRODUCTS CURRENTLY ONLINE`.

**Would a first-time visitor find the board?** Judged as a shopper: **almost
certainly not.**

1. Nothing on the homepage mentions CASE 001. The only other pointer to the game
   anywhere on the page is a footer link, `Play CROOKSLDN: The Getaway`, at
   `y=4769` of a `4890`-tall page — the last 2.5% of a page that is 5.8 screens
   long.
2. To find it in the drawer you must open the menu — which people do to *go
   somewhere*, and the first eight things in it are the eight places they wanted.
3. The panel is the **thirteenth** item in the drawer — twelve menu links come
   first. Measured: the drawer's full content is 1104px tall in an 844px
   viewport, so it scrolls by 260px. The board's art starts at `y=658`, so on
   opening you see only its top third, cut off by the bottom edge. **The
   `PLAY CASE:001 NOW` button sits at `y=962` — 118px below the fold. Yes, you
   have to scroll.** It is a short scroll, but it is one a shopper has no reason
   to make: everything they opened the menu for is already on screen above it.
   There is also no heading on the panel — no `CASE 001` line, no caption a
   shopper can read. The only words belong to the button, and the button is the
   part below the fold.
4. And on a first visit it is not merely below the fold — it is behind the cookie
   banner. See the next entry.

**Verdict:** partly (the board works; its discoverability does not)

**Shopper cost:** the best-made thing on the site is now three deliberate actions
deep — open a menu you only open to leave, scroll past everything you came for,
and notice a panel with no heading on it. The drawer panel has no label above the
art: there is no `CASE 001` text a shopper can read, only the picture and the
button. First-time visitors will not see it.

**Evidence:** `audit/screens/hdr-a06-home-fold.png` (the whole first screen, no
board), `audit/screens/hdr-a07-drawer-first-seen.png` (the drawer as first seen —
the panel is not on it), `audit/screens/hdr-d09-board-t0.png` (the board panel,
reached only after scrolling).

---

### A cold arrival, in order

**Should:** the shopper meets the store.

**Did:** on a fresh browser profile, in this order:

**First look, ~1.2s in.** The page has painted — status bar, header, hero,
catalogue grid — and a **`COOKIE CONSENT`** panel is already on it, fixed to the
bottom of the screen at `y=485` in an 844px viewport: **43% of the first
screen**. It was there at my first observation and at every observation after
it, so effectively it is part of the arrival, not something that lands later.
It reads, in full:

> `COOKIE CONSENT`
> `We and our partners, including Shopify, use cookies and other technologies to
> personalize your experience, show you ads, and perform analytics, and we will
> not use cookies or other technologies for these purposes unless you accept
> them. Learn more in our Privacy Policy`
> `Accept` · `Decline` · `Manage preferences`

On the homepage it stops just short of the hero's `CATALOGUE` button (button
ends at ~460, banner starts at 485) and swallows the top of the product grid.
Getting rid of it takes one tap on `Accept` or `Decline`; it lingers on screen
for about a second afterwards, and while it is focused it draws Shopify's own
**blue** focus ring, not the theme's lavender one.

**This is the collision.** With the banner up, opening the menu gives you a
drawer whose bottom 43% is cookie text. You can read `SHOP` down to `TRACKING`
and no further — `QUESTIONS`, `TERMS`, `CONTACT`, the CASE 001 board, the
`PLAY CASE:001 NOW` button, `ACCOUNT` and `BAG` are all behind it. Scrolling the
drawer to the bottom does not help: the banner is fixed, so the board slides up
under it and only its top 90px is ever visible. I hit-tested the
`PLAY CASE:001 NOW` button in that state: it is nominally on screen at `y=702`,
and the thing that actually receives the tap is
`div.shopify-pc__banner__btns` — the banner's `Accept`/`Decline` row. **A
first-time visitor who finds the board and taps Play gets the cookie banner
instead.**

**t ≈ 9s after answering the banner.** A second full-screen interruption:
**`CRACK THE CUFFS`**. It blacks out the whole page behind a 90%-opaque scrim
and shows an iframe. For the first ~4 seconds that iframe is empty — a black
rectangle with a single `×` in the top-left corner and nothing else. Then the
content arrives, in the lower half of the frame, leaving the top ~44% dead
black:

> `CRACK THE CUFFS.`
> `10% off your first order if you do. Three tumblers. Tap each one at the right
> moment.`
> `RUN IT`
> `NOT NOW`
> `One code per player. Attempts unlimited. Code expires in 20 minutes.`
> `(this drop closes 15.09)`

There are now **two `×` close controls on screen at once** — the theme's, at the
top-left of the overlay, and the app's own, inside the panel. Escape closes it.
So does the theme's `×`. It fires once per browser profile.

**Did the crack-the-cuffs overlay appear? Yes** — but not at the advertised ~3s.
It waits for the cookie banner to be answered first, then takes another ~9
seconds (about 6 of which are a blank black screen while the iframe loads). In
my first run I watched a cold arrival for a full 10.6 seconds without answering
the banner and nothing appeared at all; it only came after I dismissed the
banner. So the sequence a real first-time shopper meets is: page → cookie wall
(43% of the screen) → tap → ~6 seconds of black nothing → discount game →
tap → shop.

**Verdict:** partly

**Shopper cost:** two full-attention interruptions before a first-time visitor
has looked at a single product, and roughly six seconds of an unexplained black
screen between them. The one that costs something concrete is the banner over
the drawer: it makes the CASE 001 panel not just hard to find but *impossible to
press* on exactly the visit — the first one — that the panel exists to charm.

**Contradiction worth naming:** the overlay tells a shopper
`Code expires in 20 minutes.` and `(this drop closes 15.09)` — a countdown and a
deadline — inside a store that has deliberately refused countdown timers, stock
counters and manufactured scarcity everywhere else. It is served by the Base44
app rather than written into the theme, but the shopper does not know that; they
see it on CROOKSLDN, eight seconds in, before anything else.

**Evidence:** `audit/screens/hdr-a01-arrival-1200ms.png` (banner at 1.2s),
`audit/screens/hdr-a04-arrival-10600ms.png` (still nothing else at 10.6s),
`audit/screens/hdr-d02-drawer-under-consent.png` (drawer cut off at `TRACKING`),
`audit/screens/hdr-d03-case-panel-under-consent.png` (drawer scrolled to the
bottom — the board is a 90px sliver and `Accept` sits where `PLAY CASE:001 NOW`
should be), `audit/screens/hdr-d05-ctc-overlay.png` (the black frame with one
`×`), `audit/screens/hdr-d06-ctc-overlay-4s-later.png` (the panel, four seconds
later).

---

### `BAG [n]` — does the row jump as the number changes?

**Should:** the count reserves space so it never reflows the header row.

**Did:** it holds for one and two digits and breaks at three.

| Cart | Count reads | Count width | `CATALOGUE` at | `BAG` at | `MENU` at | Bar height |
|---|---|---|---|---|---|---|
| 0 | `[0]` | 27.5px | x=10, y=86 | x=144.8, y=86 | x=321.3, y=86 | 110px |
| 1 | `[1]` | 27.5px | x=10, y=86 | x=144.8, y=86 | x=321.3, y=86 | 110px |
| 9 | `[9]` | 27.5px | x=10, y=86 | x=144.8, y=86 | x=321.3, y=86 | 110px |
| **103** | `[103]` | **39.5px** | x=10, y=86 | x=144.8, y=86 | **x=10, y=134** | **158px** |

Going 0 → 1 → 9, **nothing moves at all** — not by a pixel. The reserved slot
and the tabular figures do exactly what they were built to do.

At three digits the reserve (27.5px, five characters) is no longer enough for
` [103]` (six), the `BAG` link widens by 12px, and the header row — which on a
390px phone has only about 8px of slack — **wraps to a third line**. `MENU`
leaves the top-right corner and reappears at the far left, 48px lower, and the
header grows from 110px to 158px, pushing the page down. On the screen where I
saw it, `MENU` had moved diagonally across the header.

**Verdict:** works to 99, breaks at 100

**Shopper cost:** small in practice — a clothing order of 100+ units is rare —
but it is worth knowing that the guard is sized one character short, and that
the row has under 10px of headroom, so any future label change moves `MENU`
too.

**Evidence:** `audit/screens/hdr-d15-bag-0.png`, `audit/screens/hdr-d16-bag-1.png`,
`audit/screens/hdr-d17-bag-9.png` (identical row) and
`audit/screens/hdr-d18-bag-103.png` — `MENU` alone on its own line. Measured
twice in two separate browser sessions with identical numbers
(`audit/screens/hdr-e12-bag-0.png` … `audit/screens/hdr-e15-bag-103.png`).

---

### `LIGHT MODE` — the header control nobody mentioned

**Should:** (not in the brief's list of header elements.)

**Did:** it is there, it is the second-widest control in the row at 107px, and
it works: tapping it turns the whole store from near-black
(`rgb(11, 10, 14)`) to bone (`rgb(250, 250, 251)`) and relabels itself
`DARK MODE`. It occupies more of the header row than `SEARCH` and `BAG`
combined.

**Verdict:** works

**Shopper cost:** none functionally, but it is worth noticing that on a 390px
phone the header's widest control is a theme switch, and it is one of the two
things that pushes `MENU` to within 8px of wrapping.

**Evidence:** `audit/screens/hdr-d25-light-mode.png`

---

## Surprises

Things the owner probably does not know:

1. **The cookie banner covers the bottom 43% of the open menu drawer**, and it is
   fixed, so scrolling the drawer does not get past it. On a first visit the
   menu ends at `TRACKING`; `QUESTIONS`, `TERMS`, `CONTACT`, the CASE 001 board,
   `PLAY CASE:001 NOW`, `ACCOUNT` and `BAG` are all behind cookie text.
2. **Tapping `PLAY CASE:001 NOW` on a first visit presses `Accept` on the cookie
   banner instead.** I hit-tested it: the button is nominally on screen and the
   element that receives the tap is `div.shopify-pc__banner__btns`.
3. **There is no tap-outside-to-close on a phone.** The panel is exactly as wide
   as the viewport, so the scrim is 100% covered. I swept every point of it.
   The feature exists only on desktop, where nobody needs it.
4. **Browser Back on a first visit lands on `about:blank`** — the drawer does not
   push history, so Back exits the site rather than closing the menu.
5. **The crack-the-cuffs overlay does not fire at 3 seconds.** It waits for the
   cookie banner to be answered and then shows about 9 seconds later — roughly 6
   of which are a completely black screen with a single `×` while the app loads.
6. **The header row is set at two sizes**: `<a>` controls at 9px/500,
   `<button>` controls at 13px/400, side by side.
7. **The wordmark never renders.** The header shows only the handcuffs mark, so
   on every page except the homepage nothing above the fold says CROOKSLDN.
8. **The board itself is excellent and nobody will see it** — 61fps, loads only
   on first drawer open, and sits thirteenth in a menu, below the fold.

## Missing

Expected as a shopper, could not find:

- **A way back to the shop from the CASE 001 game.** Its only three controls are
  `START CASE`, `LEADERBOARD` and `SOUND: ON`. It opens in a new tab, so the
  shop survives, but a phone user who does not realise a tab was opened has no
  route home from that screen.
- **`ACCOUNT` in the header.** It is 200px below the fold of an opened drawer.
- **Any sign on the homepage that CASE 001 exists.** The only pointer outside
  the drawer is a footer link at `y=4769` of a `4890`-tall page.
- **A label on the CASE 001 panel.** The art has no heading; the only words are
  on the button, which is below the fold.
- **A closing gesture that works on a phone.** Neither tapping outside nor Back
  closes the drawer; only the `CLOSE` word and the hardware Escape key do, and
  phones do not have Escape.

## Contradictions

- **The overlay sells urgency the store refuses everywhere else.** Eight seconds
  into a first visit, CROOKSLDN says `Code expires in 20 minutes.` and
  `(this drop closes 15.09)` — a countdown and a deadline — in a store that has
  deliberately banned countdown timers, stock counters and manufactured scarcity
  from every other surface. The shopper cannot tell that one of these is a
  Base44 app and the rest is the theme; they see one shop saying two things.
- **Version numbers.** The shop footer says `EVIDENCE TERMINAL v0.2`; the CASE
  001 game it links to says `EVIDENCE TERMINAL v0.1 // CROOKS UK`. Same fiction,
  two build numbers, one tap apart. (This is the visible face of O4.)
- **`SHOP` and `ALL` in the menu are the same twelve products.** `SHOP` goes to
  `/collections/frontpage`, whose heading reads `PRODUCTS` — so the menu word,
  the URL and the page heading are three different names for one thing, sitting
  directly above a second link to the same twelve items.
- **The header count is reserved so it "never reflows the row"** — and at
  `[103]` it reflows the row, moving `MENU` to a new line.

## Works and must be protected

- **The board.** Loaded only on first drawer open (0 requests before, 1 after),
  animates at 61fps, art is detailed and on-brand — brickwork, barred windows,
  a helmeted officer in hi-vis, gold `£` coins. It is the best thing in this
  area and the pause guards do not get in a shopper's way.
- **The count's reserved slot and tabular figures.** 0 → 1 → 9 moves nothing by
  a single pixel. Keep it; just widen it by one character.
- **Escape and focus return.** Escape closes the drawer and puts a clearly
  visible lavender focus ring back on `MENU`.
- **The drawer's link set.** All fourteen destinations resolve, every collection
  has products in it, and nothing 404s.
- **`PLAY CASE:001 NOW` opening in a new tab.** It is the only reason the game
  does not strand people — the shop tab stays exactly where it was, drawer still
  open.
- **The text `MENU` trigger instead of a hamburger**, and the fact that the
  trigger is hidden until JS upgrades it, so it is never a dead control.
