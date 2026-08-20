# raw-carriage — the carriage progress bar (Q2)

Area key: `carriage`. Section `crooks-cart-progress`, rendered first on `index.json`,
`product.json`, `collection.json`, `search.json`, `cart.json`.

**Evidence status, stated up front.** The store's bot protection escalated during this
run — the preview served HTTP 429 and a Cloudflare interstitial ("Your connection needs
to be verified before you can proceed") to eight consecutive session attempts and to
every navigation after a cart mutation. Two shopper states were captured on screen before
that started. The rest of this file is grounded in (a) the deployed staging theme's own
source, and (b) the store's live shipping rate card read from the Admin API. Every claim
below is tagged **[screen]**, **[code]** or **[admin]** so nothing is mistaken for
something I watched happen. Items I could not reach are marked **untested** rather than
guessed.

---

### Carriage bar — empty cart (the state most first visits are in)

**Should:** Per the brief, "the bar renders above everything on home, product, collection
and search", so an empty-cart shopper should see it saying how far they are from £20.

**Did:** Nothing. With an empty bag the section does not render at all — not on the
homepage, not on a product page. What a GB shopper actually lands on is the header
status line, then straight into the hero. The only shipping statement anywhere on that
first screen is the rotating status bar, which reads exactly:

> `FREE UK SHIPPING OVER £20 — ORDER BY 18:00 FOR SAME-DAY DISPATCH`

and which alternates every few seconds with `[count] PRODUCTS CURRENTLY ONLINE`, so it is
absent from the screen about half the time. It never mentions the second tier at all.

**[code]** The gate is `if crk_country == section.settings.country_code and cart.item_count > 0`
in `sections/crooks-cart-progress.liquid`. Item count zero, no section.

**Verdict:** works — but not the way the brief assumes. This is the single most important
fact about this feature and it is not written down in `SPEC.md §3.7`: **the bar costs a
shopper nothing until they have already added something.**

**Shopper cost:** None in space. There is a cost in information: the shopper who has not
yet added anything is the one who most needs to know that £20 is the line, and they are
told it only by a message that rotates itself off screen.

**Evidence:** `audit/screens/carriage-01-home-empty-cart-no-bar.png` (home, GB, empty bag,
`BAG [0]`, no bar), `audit/screens/carriage-02-pdp-empty-cart-no-bar.png` (WHITE/RED
MOTIONTEC SOCKS PDP, empty bag — the record header `← CATALOGUE  PRODUCT 11 / 12
ACCESSORIES` sits directly under the site header with nothing between).

---

### Two-tier wording — the exact strings

**Should:** Move through both tiers: free Tracked 48 over £20, free Tracked 24 over £70.

**Did / will:** **[code]** The three states and the strings the shopper is shown. These are
persisted values in `templates/index.json` and `templates/search.json`, and are the schema
defaults that `product.json`, `collection.json` and `cart.json` fall back to, so the wording
is identical on all five surfaces.

| Cart total | On-screen message | Bar fill |
|---|---|---|
| £0.00 | *(section absent)* | — |
| £6.00 (1pc socks) | `£14.00 to free Tracked 48` | 8% |
| £24.00 (+ £18 duffle) | `£46.00 to free Tracked 24` | 34% |
| £67.00 | `£3.00 to free Tracked 24` | 95% |
| £73.00 | `Free Tracked 24 — unlocked` | 100% |

The message carries a CSS `::before` of `> `, so on screen it reads `> £14.00 to free
Tracked 48` — consistent with the terminal fiction and, correctly, the amount and the
service name stay plain English.

Under the track sit two fixed labels, `Tracked 48 free` and `Tracked 24 free`, which gain a
`✓ ` prefix and the accent colour as each is met. The track itself is
`role="progressbar"` with `aria-label="Progress toward free carriage"` and a live
`aria-valuenow`, and there is a 1px tick at 28% marking where tier 1 lands.

Two details that are quietly right: fill is measured against the **top** tier, so the bar
keeps moving after £20 rather than filling up and stopping; and it is pinned at 99% until
the tier is genuinely met, so a shopper never sees a full bar next to `£0.01 to go`.

**Verdict:** works (wording and arithmetic) — **untested on screen** for the £6 / £24 /
£67 / £73 states; the run could not reach them.

**Evidence:** `sections/crooks-cart-progress.liquid` (the `crk_state` case block),
`templates/index.json` → `sections.carriage.settings`.

---

### Does it update after an add to cart, without a page reload?

**Should:** `SPEC.md §3.7`: *"the script only keeps it correct on AJAX cart updates
(`cart:update`, plus a `/cart.js` re-read)"* — i.e. the bar should move the moment you add.

**Did:** **[code]** It cannot, on the surface where it matters most. `crooks-cart-progress.js`
refreshes on exactly two triggers:

```js
document.addEventListener('cart:update', refresh);
document.addEventListener('crk:cart:update', refresh);
```

The theme's own PDP add-to-bag lives in `assets/crooks-record.js`. It POSTs `/cart/add.js`,
re-reads `/cart.js`, updates the bag count and prints the confirmation line — and it
**never dispatches `cart:update` or `crk:cart:update`.** `grep -n "dispatchEvent\|CustomEvent\|cart:update"` over
`assets/crooks-record.js` returns nothing. Horizon's own cart components do fire
`cart:update`, which is why the bar is live on `/cart` when you change a quantity there,
but nothing fires it on a product page.

So the sequence for a shopper is: tap `ADD TO BAG`, get `Added — [n] in bag` under the
button and the header count ticks over — and the carriage readout at the top of the page
keeps showing the number from before the add. On the very first add it is worse than
stale: the section was never rendered (empty cart), so there is no element for the script
to update even if the event did fire. The shopper adds their first item and the bar simply
does not appear until they navigate.

**What the shopper sees at the moment they add:** on a 390-wide phone the buy controls are
far down the PDP and there is a bottom sticky buy bar, so at the instant of tapping,
the carriage bar — which lives at the absolute top of the document — is off screen above.
Nothing scrolls, nothing opens (the cart drawer CSS is deliberately unloaded, `SPEC.md §9.9`).
The only feedback is the inline `Added — [n] in bag` line and the header count.

**Verdict:** partly. Correct on every full page load, and live on `/cart`. Not live on the
product page, which is the only place a shopper adds anything.

**Shopper cost:** The bar's whole reason to exist is to react. A shopper who adds a £14
item to a £6 bag, scrolls back up expecting to see the £20 line cleared, and sees
`£14.00 to free Tracked 48` unchanged, learns that the readout is not to be trusted.
`SPEC.md §3.7`'s claim that the theme's own add-to-cart path is covered is not true of the
deployed code.

**Fix inside the design law:** one line at the end of the success branch in
`crooks-record.js` — `document.dispatchEvent(new CustomEvent('crk:cart:update'))`. The
listener already exists. No CSS, no new markup. The first-add case additionally needs the
section to render an empty shell (or the script to inject one) when the cart is empty —
or, better, see the judgement below, where the empty-cart shell would be worth having
anyway.

**Evidence:** `assets/crooks-cart-progress.js:73-74`, `assets/crooks-record.js` (add
handler, ~line 122-160). **Untested on screen** — the add-to-bag click could not be
completed before the store started challenging.

---

### THE JUDGEMENT — does it earn its position?

**The position.** `crooks-cart-progress` is the **first** section in five templates. On the
homepage it sits above the hero; on a product page above the product; on collection and
search above the register. The round-2 council measured the cost as the first catalogue
card moving from **1.22 to 1.48 viewports** down the page — about **a quarter of a phone
screen** of vertical space, paid on every one of those five pages. That figure is recorded
in `audit/_ref/KEEP.md` and `SPEC.md §3.7`, and is why the bar is explicitly *not* on the
protect list. **My own re-measurement on 390×844 did not complete** — the store began
serving bot challenges before the £6 cart state could be reached, so I cannot put my own
number against theirs. Treat 0.26 of a screenful as the owner's figure, not mine.

**But the cost is conditional, and that changes the answer.** Because of the
`cart.item_count > 0` gate, that quarter-screen is charged **only to shoppers who already
have something in the bag**. So:

**On the HOMEPAGE, empty cart — the case the question asks about: the bar is not there.**
The shopper who has never seen a price is not shown a progress bar toward a threshold they
have no way to evaluate. That is the right call and it is already implemented. The question
"is it worth it on the homepage where the shopper has an empty cart and no idea what
anything costs" answers itself: there is nothing to be worth. Where it *does* appear on the
homepage — a returning shopper, mid-shop, bag already loaded — it is the only running total
of distance-to-free-shipping anywhere on the site, and a quarter screen above a hero the
shopper has already seen is cheap. **Earns it, marginally, and only in that second case.**

**On a PRODUCT page, mid-decision: no. This is where it is worst placed.** Not because the
message is wrong, but because the geometry and the message point in opposite directions.
The bar is at the very top of the document. The decision — size, price, `ADD TO BAG` — happens
most of a screen further down, and on mobile at the bottom sticky bar. So at the moment the
shopper is deciding, the bar is off screen; and at the moment they act, it does not update.
It charges its cost where the shopper's attention is not, and delivers its payload where
their attention will never return. Meanwhile the PDP's *own* statement of the same fact —
`Shipped with Royal Mail Tracked. Free UK shipping over £20, and free Tracked 24 over £70.` —
is real, accurate, and **sitting inside the Chain of custody accordion, which defaults
closed**. The information a mid-decision shopper needs is on the page twice: once above the
fold where they cannot act on it, and once where they will not open it.

**On a COLLECTION page: the best case of the four.** A shopper scanning a register of
prices is exactly the person deciding whether to add one more thing to clear £20, and
`£46.00 to free Tracked 24` next to a wall of £45–£60 items is a real, actionable prompt.
Same cost, materially more value than home or PDP.

**On a SEARCH page: no.** A shopper who typed a query is looking for one specific thing.
The bar pays the same quarter screen to push the results they asked for further down, and
adds nothing to the task. Worst value-per-pixel of the five.

**Where it genuinely earns its place: `/cart`.** It is the one surface where the message is
immediately actionable, where the shopper is already thinking about total spend, and — not
coincidentally — the one surface where it actually updates live, because Horizon's cart
components dispatch `cart:update`.

**Recommendation, implementable inside the design law** (no radius, no gradient, no shadow,
no third typeface, no new colour, no build step, no fabricated content):

1. Keep it on `cart.json` and `collection.json`.
2. Remove it from `search.json` and `index.json`. On the homepage the status bar already
   carries the £20 line; make that line permanent rather than rotating, and add the £70
   tier to it, and the homepage loses nothing.
3. On `product.json`, move the same one-line readout out of the top-of-page section and
   into the buy panel beside the delivery line. It is already a `crk-data` line — 1px
   border, mono, radius 0 — so it needs no new design vocabulary, and it would then sit
   next to `ADD TO BAG` where both the decision and the update happen.
4. Whatever else changes, fire `crk:cart:update` from `crooks-record.js`.

**Verdict:** partly. The readout is honest, well-built and commercially sound. Its
*position* is earned on two of the five templates it occupies.

**Evidence:** `templates/{index,product,collection,search,cart}.json` — `carriage` is first
in every `order` array. `audit/_ref/KEEP.md:154-156` for the 1.22 → 1.48 figure.
`audit/screens/carriage-01-home-empty-cart-no-bar.png` and
`carriage-02-pdp-empty-cart-no-bar.png` show the empty-cart baseline the bar is measured
against. **The with-bar landing screenshot and my own screenful measurement are untested.**

---

### Empty cart vs £3 short — which is doing commercial work?

**The empty-cart shopper is told:** by the carriage bar, nothing. By the status bar,
`FREE UK SHIPPING OVER £20 — ORDER BY 18:00 FOR SAME-DAY DISPATCH`, on screen roughly half
the time and silent about the £70 tier. That is a fact about the store, not a prompt: it
names a threshold with no anchor, before the shopper knows that a crewneck is £50 and a
pair of socks is £6, so "£20" carries no information about whether it is easy or hard to
reach.

**The £3-short shopper is told:** `£3.00 to free Tracked 24`, attached to a bag they have
already committed to, against a catalogue where the cheapest thing on the site is a £6 pair
of socks. That is a specific, closeable gap with an obvious way to close it — and closing
it saves them £4.99. It is the only piece of copy in this feature that is doing commercial
work.

**Which argues for the opposite of deleting the bar.** The gap-closing message is the
valuable half; the empty-cart half is already (correctly) suppressed. The problem is not
that the bar exists, it is that the valuable message is displayed at the top of pages where
the shopper cannot act on it, and not displayed at the point where they can.

**Verdict:** works (the near-threshold message), absent (any useful empty-cart equivalent).
**Untested on screen.**

---

### Collection and search — same cost, same value?

**Should:** Same section, same position, same cost on both.

**Did:** **[code]** Identical. `collection.json` and `search.json` both put `carriage` first
in `order`; `search.json` persists the same nine settings as `index.json`,
`collection.json` inherits the same values as schema defaults. So the cost is the same on
both and the same as the homepage.

The value is not. On a collection page the shopper is comparing prices and is a live
candidate to add one more item. On search they have asked a specific question and the bar
pushes the answer down. One further wrinkle: on `/search` with an empty query the register
deliberately stands down (`SPEC.md §9.8`) and renders nothing — but the carriage section is
a separate section and still renders above it if the cart is non-empty, so a shopper who
opens search with items in the bag gets a shipping progress bar sitting above a page with
no results on it.

**Verdict:** partly. Same cost; collection justifies it, search does not.

**Shopper cost:** A quarter screen of the results the shopper explicitly asked for, on
every search.

**Evidence:** `templates/collection.json`, `templates/search.json`. **Untested on screen.**

---

### What a shopper outside the UK gets

**Should:** The bar is gated to `country_code` GB because no other market has a free tier,
so an overseas shopper should not be chased toward a threshold that does not apply.

**Did:** **[code]** The gate is on `localization.country.iso_code`, so outside GB the
section does not render — correct, and the reasoning in the section's own comment block is
sound.

**[admin]** I read the live rate card from the Admin API to check the premise, and it holds
exactly:

| Zone | Rates |
|---|---|
| United Kingdom | Tracked 48 £3.00 · **£0.00 when total ≥ £20** · Tracked 24 £4.99 · **£0.00 when total ≥ £70** |
| Channel Islands (GG, JE) | Tracked 48 £3.99 · Tracked 24 £7.00 · **no free tier, at any value** |
| EU | Standard international £12.99 · no free tier |
| International (incl. US) | Standard international £18.99 · no free tier |

So the thresholds the bar promises are real, and hiding it elsewhere is right.

**But the gating stops at the bar and nothing else follows it.** The header status bar is
not gated by country and shows every shopper in the world
`FREE UK SHIPPING OVER £20 — ORDER BY 18:00 FOR SAME-DAY DISPATCH`. The PDP's Chain of
custody says `Shipped with Royal Mail Tracked. Free UK shipping over £20, and free Tracked
24 over £70.` Terms and the FAQ repeat it. A shopper in the US, browsing in dollars, is
told about a £20 free-shipping line in a currency they are not being charged in, with
nothing on the page to tell them it does not apply to them — and the one component that
knows about their country has responded by going silent rather than by saying so.

The sharpest version of this is the Channel Islands. A Jersey or Guernsey shopper is
served by a dedicated market, sees GBP prices and the same `FREE UK SHIPPING OVER £20`
status line — and their actual cheapest rate is £3.99, with no free tier at any basket
value, ever.

**Verdict:** works (the bar's own gating) / broken (everything around it).

**Shopper cost:** An overseas shopper builds a basket believing shipping is free over £20
and finds £12.99 or £18.99 at checkout. That is the exact failure the section's own comment
block says it exists to avoid — it just avoids it in one component out of five places the
claim is made.

**Evidence:** `sections/crooks-cart-progress.liquid` (the `crk_country` gate);
`sections/header-group.json` → `crooks_status_bar.blocks.m1.settings.message`;
`templates/product.json` custody step body; Admin `deliveryProfiles` query, read-only.
**Untested on screen** — the non-GB browser context could not be reached.

---

## Surprises

- **The bar does not exist on an empty cart.** `cart.item_count > 0` is in the render gate.
  Every discussion of this feature — including `SPEC.md §3.7` and the council note that
  took it off the protect list over the 1.22 → 1.48 viewport cost — reads as though it is
  always there. It is not: the space it takes is charged only to shoppers who already have
  something in the bag, which is a much better trade than the council's note implies, and
  it means the "homepage, empty cart" objection to this feature is already answered in code.
- **It cannot update after a product-page add to cart.** `crooks-cart-progress.js` listens
  for `cart:update` / `crk:cart:update`; `crooks-record.js` — the theme's own add-to-bag —
  dispatches neither. `SPEC.md §3.7` states the opposite. One `dispatchEvent` line fixes it.
- **On the first add there is nothing to update.** Empty cart means no section in the DOM,
  so even a correct event would find no element. The shopper's first add produces no
  carriage feedback at all until the next page load.
- **The homepage's only always-on shipping statement rotates itself off screen.** The status
  bar alternates `FREE UK SHIPPING OVER £20 — ORDER BY 18:00 FOR SAME-DAY DISPATCH` with
  `[count] PRODUCTS CURRENTLY ONLINE`, so a shopper landing at the wrong moment sees no
  shipping information at all. Combined with the empty-cart gate, a first-time visitor can
  browse the whole homepage without ever being told about free shipping.
- **The £70 tier is invisible until you have spent £20.** No always-on copy anywhere in the
  chrome mentions Tracked 24 — the status bar names only the £20 line, and the £70 line
  lives in the closed Chain of custody accordion and in Terms/FAQ.
- **The rate card actually matches.** UK free Tracked 48 at £20 and free Tracked 24 at £70
  are real, active rates in the delivery profile. This feature tells the truth, which is
  more than can be said for the copy around it.
- A Shopify cookie-consent banner covers roughly the bottom 45% of a 390×844 first view.
  Not this area's finding, but it is the first thing on screen and it intercepts taps, so
  it is noted here because it materially changes what "the landing view" looks like.

## Missing

- Any statement of the £70 tier that an empty-cart shopper will actually read.
- Any carriage feedback at the moment of the first add to bag — the one moment a shopper is
  most receptive to "spend £14 more and shipping is free".
- Any country-aware equivalent for non-GB shoppers. The bar goes silent, but nothing tells
  an EU or US shopper that the £20 line they can read in the status bar is not theirs, or
  what their shipping will actually cost (£12.99 / £18.99).
- A carriage readout anywhere near the buy controls on a product page.

## Contradictions

- **The status bar promises every country a UK threshold.**
  Header, all markets: `FREE UK SHIPPING OVER £20 — ORDER BY 18:00 FOR SAME-DAY DISPATCH`.
  Rate card, EU: `Standard international £12.99`, no free tier. International (incl. US):
  `Standard international £18.99`, no free tier. Channel Islands: `Tracked 48 £3.99`,
  `Tracked 24 £7.00`, no free tier at any value. The carriage bar correctly hides itself
  outside GB; the sentence above it does not.
- **`SPEC.md §3.7` vs the deployed script.** Spec: *"the script only keeps it correct on
  AJAX cart updates (`cart:update`, plus a `/cart.js` re-read)"* — presented as covering the
  theme's own add-to-bag path. Code: `crooks-record.js` dispatches no event the carriage
  script listens for, so an AJAX add leaves the bar stale.
- **The same shipping fact, told twice on a PDP, in two places a shopper cannot use.**
  Above the fold: `£46.00 to free Tracked 24`, off screen by the time they reach the buy
  controls. Below, inside an accordion that defaults closed: `Free UK shipping over £20,
  and free Tracked 24 over £70.` Neither is visible at the moment of decision.

## Works and must be protected

- **The `cart.item_count > 0` gate.** It is the reason this feature is defensible at all.
  Do not "fix" the bar by showing an empty-state version on the homepage.
- **The GB gate on `country_code`,** and the reasoning behind it. It is the one component in
  the build that refuses to make a shipping promise it cannot keep.
- **Thresholds that match the real delivery profile** (£20 / £70, verified against the live
  rate card). If these ever drift, the bar starts promising carriage that checkout withdraws.
- **Fill measured against the top tier, and held at 99% until a tier is genuinely met.**
  Both are the difference between an instrument and a sales gimmick.
- **Plain English inside the fiction.** `£14.00 to free Tracked 48` names a real Royal Mail
  service and a real number. No countdown, no colour escalation, no "only £14 away!!". This
  is `SPEC.md §0`'s rule holding under pressure and it should stay exactly as it is.
- **`aria-label="Progress toward free carriage"`, live `aria-valuenow`, `aria-live="polite"`
  on the message** — the accessibility profile in `SPEC.md §9.10` depends on it.

## Untested — could not be reached

The store began returning HTTP 429 and a Cloudflare interstitial partway through this run
and did not recover within the time available. The following were scripted and are ready to
re-run from `audit/_tools/carr5.mjs`:

- On-screen capture of the bar at £6.00, £24.00, £67.00 and £73.00.
- The no-reload behaviour observed rather than read from source.
- My own 390×844 measurement of how far down the first product card starts with the bar
  present, and the landing-view screenshot of that cost.
- The collection, search and cart surfaces with a loaded bag.
- The non-GB browser view.
