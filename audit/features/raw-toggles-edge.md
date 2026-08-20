# raw — toggles-edge (light/dark, the Outline toggle, edge conditions)

Device unless stated: iPhone-class phone, 390×844, GB market, preview theme 202053779799.
Dark is the default: a first visit has no `data-crk-theme` and paints `rgb(11,10,14)`.
The control is a header button reading **`LIGHT MODE`** (it renames itself to `DARK MODE`
once light is on), sitting in the header row next to `MENU`, on every template.

---

### Light/dark toggle — the control itself
**Should:** a shopper can find the switch, use it, and see the site change.
**Did:** the switch is plain text in the header — `CATALOGUE  SEARCH  BAG [1]  LIGHT MODE  MENU` —
and it works instantly with no reload. In light the ground becomes `rgb(250,250,251)`, the
handcuff logo flips to black, purple accents stay purple. The button's own label is the
state you will get, not the state you are in, which is the right way round.
**Verdict:** works
**Evidence:** audit/screens/toggles-edge-01-header-dark.png, audit/screens/tg-home-light.png,
audit/screens/tg-home-dark.png

### Light/dark on every template
**Should:** every page a shopper can reach honours the choice.
**Did:** switched on home, product, collection, cart, search, `/pages/faq`, `/pages/terms`,
`/pages/tracking`, `/pages/contact`, `/policies/refund-policy` and a 404. Home, product,
collection, cart, search, FAQ, terms and tracking all repaint correctly in both themes and
nothing became unreadable in light. `/policies/refund-policy` repaints correctly too (the
policy body is painted even though the underlying page ground stays Horizon's cream).
**Two templates ignore the theme completely** — see the 404 entry below.
**Verdict:** partly
**Evidence:** audit/screens/tg-{home,product,collection,cart,search,faq,terms,tracking,policy}-{light,dark}.png

### The 404 page (and `/pages/contact`) ignore the theme
**Should:** a mistyped URL or a dead link lands you somewhere that still looks like the shop.
**Did:** in **dark** mode — the default — the header is black, and everything below the header
is Shopify Horizon's cream `rgb(244,241,234)` in Horizon's own typeface: a large
`PAGE NOT FOUND`, the line *"The link may be incorrect, or the page has been removed."*, a
black `Continue shopping` block and a `Discover something new` carousel. Pressing
`LIGHT MODE` changes nothing below the header; the two screenshots are identical apart from
the header. `/pages/contact` is the same story — body ground `rgb(244,241,234)` in both themes.
**Verdict:** broken (for the 404 and `/pages/contact` only)
**Shopper cost:** on a phone in a dark room, a dead link throws a full-screen cream page at
you. It reads as "wrong site / something broke", which is the worst possible moment to look
like a different company — and the theme switch, which works everywhere else, silently stops
working there.
**Evidence:** audit/screens/tg-404-dark.png vs audit/screens/tg-404-light.png (identical below
the header), audit/screens/tg-contact-dark.png. Exact strings: `PAGE NOT FOUND`,
`The link may be incorrect, or the page has been removed.`, `Continue shopping`,
`Discover something new`.

### The `SEARCH` button disappears in light mode
**Should:** the button that runs the search is visible.
**Did:** on `/search`, the submit button — the word `SEARCH` under the query field — is
`rgb(221,215,201)` (cream) text with **no background at all** (`rgba(0,0,0,0)`, border width
`0px`), on the light ground `rgb(250,250,251)`. That is a contrast ratio of **1.38:1**: cream
on white. Its class is `crk-btn crk-btn--fill crk-query__go` — the "fill" never arrives, so
in dark mode it happens to read as cream-on-black and in light mode it vanishes.
**Verdict:** broken (light mode only)
**Shopper cost:** in light mode you type "jeans", see the box and the helper line
`SEARCH BY ITEM, CATEGORY OR COLOUR`, and there is no visible button between them — you have
to guess that pressing Enter works, or that the blank gap is clickable.
**Evidence:** audit/screens/tg-search-light.png (button region blank) vs
audit/screens/tg-search-dark.png (same button legible). Computed: `color rgb(221,215,201)`,
`background rgba(0, 0, 0, 0)`, `border 0px`.

### Prose links in dark mode (the default) are the dimmest text on the page
**Should:** a link inside a paragraph is at least as readable as the paragraph.
**Did:** on `/pages/faq`, in **dark**, the closing paragraph's links —
`crooksldn@gmail.com`, `@crooksldn`, `terms page` — are `rgb(92,52,128)` on `rgb(11,10,14)`,
**2.12:1**, noticeably darker than the body text beside them. The same links in **light** are
fine (dark purple on white). Same colour appears on the returns links: `tracking page`,
`the returns centre`, `Start your return here`.
**Verdict:** partly
**Shopper cost:** the FAQ's escape hatches — the email address and "Start your return here" —
are the least visible words in the answer, in the theme almost everyone will see.
**Evidence:** audit/screens/tg-faq-dark.png (paragraph *"Still stuck? Email crooksldn@gmail.com
or DM @crooksldn with your order number. We reply within 1–2 working days. The full trading
terms are on the terms page."*) vs audit/screens/tg-faq-light.png

### The choice persists across navigation — but only in that one tab
**Should:** pick light once, keep it.
**Did:** light survived every navigation tested (home → collection → product → cart → search →
policy → 404 and back), and survives reload. It is stored in `sessionStorage`, so:
opening the store in a **new tab** starts dark again (`data-crk-theme` null, storage empty)
even though the **bag carried over correctly** (`[2]` in the new tab). Closing the browser
and coming back tomorrow will also be dark again.
**Verdict:** partly
**Shopper cost:** small but real — a shopper who needs light mode (glare, low vision) has to
re-select it every session and in every tab they open, while the same site remembers their bag.
**Evidence:** audit/screens/tge-4-tab3-new-tab.png — new tab reads `LIGHT MODE` in the header
(i.e. dark) with `BAG [2]`.

### Flash of the wrong theme on load
**Should:** no flash.
**Did:** with light stored, the theme attribute is already `light` on the first rendered
frame, so the page never flips light→dark→light. The first painted frame does carry the
Horizon ground `rgb(244,241,234)` before settling to `rgb(250,250,251)` — cream to white,
which is not perceptible. Dark-mode cold-load flash: see the tgfinal run (below).
**Verdict:** works (light); dark cold-load recorded separately
**Evidence:** audit/screens/tg-flash-0..2-*.png, probe `{atStart:null, ss:"light",
firstFrame:"light", firstFrameBg:"rgb(244, 241, 234)"}`

---

## Edge conditions

### Reloading the main pages
**Should:** nothing lost.
**Did:** reloaded home, collection, product, cart and search. Every one came back byte-for-byte
the same to a shopper — same headings, same bag count `[1]`, same images (0 broken), same
carriage line `£20.00 to free Tracked 24`. Felt duration 3.5–4.7s each on this connection.
**Verdict:** works

### Back and forward through five pages
**Should:** the trail works and the bag stays honest.
**Did:** walked home → collection → product → search → cart, then Back five times and Forward
five times. Every step restored the right page with its heading, images and price, and the bag
count stayed `[1]` throughout — no stale "bag is empty" on a restored page. Each step took
about 2.8–3.4s (these are real loads, not instant restores).
**Verdict:** works

### Landing directly on a product URL, cold
**Should:** the PDP stands on its own.
**Did:** with storage cleared so the PDP was the first page the browser rendered, the product
page came up in 4.8s complete: `PRODUCT 01 / 12`, `CHARCOAL CELLBLOCK CREWNECK`, `£50.00`,
the five size buttons, `SIZE GUIDE`, `Order before 18:00 and it ships today (Mon–Sat)`, the
accordions, `MORE FROM THIS DROP`, and the sticky bar showing `SELECT A SIZE` / `CHECKOUT NOW`.
Picking `M` and adding worked; the header went `BAG [0]` → `BAG [1]`.
**Verdict:** works
**Evidence:** audit/screens/tge-1-cold-pdp-top.png, audit/screens/tge-1-cold-added.png

### Two tabs
**Should:** after a reload they agree.
**Did:** tab B on `/cart` showed `Cart 1`. Tab A added a second item. Tab B, untouched, still
said `Cart 1` and `£20.00 to free Tracked 24` — nothing tells it that it is stale. After a
reload it agreed exactly: `Cart 2`, and the carriage line changed to
`Free Tracked 24 — unlocked`.
**Verdict:** works (with the usual stale-tab caveat: an untouched second tab will let you press
`Check out` believing there is one item in the bag when the server has two)
**Evidence:** audit/screens/tge-4-tab2-stale.png, audit/screens/tge-4-tab2-after-reload.png

---

## Surprises

- **A cookie consent banner now exists.** The standing brief lists "No cookie banner" as known.
  There is one: a panel headed `COOKIE CONSENT` with `Accept` / `Decline` / `Manage preferences`
  covering the bottom **43% of the phone screen** (390×359 of an 844-tall viewport) on first
  load. It sits *over* the open menu drawer, hiding the `PLAY CASE:001 NOW` panel until
  dismissed. Evidence: audit/screens/toggles-edge-00-home-dark-cookiebanner.png,
  audit/screens/toggles-edge-B-drawer-dark.png.
- **The `OUTLINE` button only exists on the homepage catalogue.** `/collections/all` shows
  `FLAT` / `ON MODEL` and no `OUTLINE`. A shopper who finds the treatment on the homepage
  cannot find the control again from a collection page.
- **The white-outline treatment is on by default**, not off: a fresh session already has
  `crk-outline = on` in storage, and the cold-landed PDP image carries the white keyline
  (audit/screens/tge-1-cold-pdp-top.png). Nobody chose it.
- The packaging section's image frame is empty on the homepage in both themes — an empty
  bordered box under `EVERY ORDER SHIPS LIKE THIS`. On the dark ground it reads as a deliberate
  empty frame; in light mode it is a large blank white panel that reads as a failed image.

## Missing

- No way to keep the light-mode choice beyond the tab (see persistence entry).
- No `OUTLINE` control on collection pages, only on the homepage.

## Contradictions

- The header button says `LIGHT MODE` on every page including the 404 and `/pages/contact`,
  but on those two pages pressing it changes nothing — the page stays cream in dark mode and
  cream in light mode.

## Works and must be protected

- The theme switch itself: instant, no reload, no flash, label states the destination.
- Reload, Back/Forward and cold-landing on a product URL: all clean, bag count honest at every
  step.
- Two tabs reconcile exactly on reload, including the carriage line.
- Product photography suits both grounds — the light catalogue is as legible as the dark one.
