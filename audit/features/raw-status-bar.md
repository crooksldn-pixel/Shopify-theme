# raw — status-bar

The rotating one-line ticker above the header (`crooks-status-bar`).
Shopped on a 390×844 phone unless stated; also desktop 1440×900, landscape phone,
reduced motion, and JavaScript off. Preview theme 202053779799, GB/GBP confirmed
on every run.

**Everything it says, verbatim — there are only two lines:**

1. `FREE UK SHIPPING OVER £20 — ORDER BY 18:00 FOR SAME-DAY DISPATCH`
2. `12 PRODUCTS CURRENTLY ONLINE`

That is the complete cycle. It repeats every 16 seconds, on every page I opened
(homepage, catalogue, product, cart).

---

### Rotation, and how the cadence feels
**Should:** Rotate between the configured messages.
**Did:** It rotates. I watched the bar for 46 seconds without touching anything and
timed the gaps between changes: `7952, 7999, 7999, 8000, 8000` ms — eight seconds a
line, sixteen seconds for the whole loop. The swap is instant, no fade, no slide: one
line is replaced by the other between blinks. With only two messages, a shopper
who glances up twice in half a minute sees the same two sentences.

On the D1 cadence question (known defect, not re-reported): **8 seconds is too
slow, not too fast.** The longer line is 63 characters of monospace caps; reading
it takes about three seconds, so roughly five seconds of every eight are spent
staring at a line already read. The shorter line — `12 PRODUCTS CURRENTLY ONLINE`,
28 characters — holds the slot for the same eight seconds. Nothing is ever cut
off mid-read. If the seconds/milliseconds bug were fixed and the persisted `5`
took effect, the bar would read *better*, not worse.
**Verdict:** works
**Evidence:** audit/screens/status-bar-x-h-m-bar1.png (`FREE UK SHIPPING OVER £20 — ORDER BY 18:00 FOR SAME-DAY DISPATCH`), audit/screens/status-bar-x-h-m-bar2.png (`12 PRODUCTS CURRENTLY ONLINE`)

### `[count]` — is 12 the real number?
**Should:** `[count]` substitutes the live product count of the configured collection.
**Did:** It renders `12 PRODUCTS CURRENTLY ONLINE`, and 12 is the number a shopper
can verify by counting. The catalogue header says `12 ITEMS` and renders exactly 12
cells (`NO. 01` … `NO. 12`). The homepage boot line says `> 12 PRODUCTS AVAILABLE TO
PURCHASE`. Product pages agree: `PRODUCT 01 / 12` on the Charcoal Cellblock Crewneck,
`PRODUCT 05 / 12` on the Blue Wash OG Jeans. **The bar and the product-page footer
agree.**

One nuance for the owner rather than the shopper: the store actually has 13 published
products. The thirteenth is `cellblock-set` (`CELLBLOCK SET`, £85), which never appears
in the register, is only reachable through the set toggle on a product page, and its own
page carries no `PRODUCT n / N` line at all — so nothing on screen contradicts "12".
The number is right against everything a shopper can see and count.
**Verdict:** works
**Evidence:** audit/screens/status-bar-x-count-vs-register.png (`12 PRODUCTS CURRENTLY ONLINE` in the bar and `12 ITEMS` in the register, one frame), audit/screens/status-bar-x-pdp-top.png (ticker + `PRODUCT 05 / 12` in one frame), audit/screens/status-bar-x-pdp-index.png (`PRODUCT 01 / 12`), audit/screens/status-bar-x-set-pdp.png (`CELLBLOCK SET £85.00`, no index line)

### Pause on hover
**Should:** Rotation stops while the pointer is on the bar.
**Did:** It stops, properly. I parked the pointer in the middle of the bar on the
catalogue page — confirming the bar itself was the thing under the cursor, not an
overlay — and held it there for 26 seconds, i.e. three rotations' worth. The line
never changed: still `FREE UK SHIPPING OVER £20 — ORDER BY 18:00 FOR SAME-DAY
DISPATCH` at the end. I moved the pointer away and within nine seconds it had
flipped to `12 PRODUCTS CURRENTLY ONLINE`.

Worth knowing: my first attempt at this test on the *homepage* appeared to fail —
the bar kept rotating under the cursor — because the `CRACK THE CUFFS.` discount
modal was sitting on top of it (see below). The pause is real; it just cannot save
a shopper from a bar that is behind a dimmer.
**Verdict:** works
**Evidence:** audit/screens/status-bar-x-h-coll-bar.png (start of hover) and audit/screens/status-bar-x-h-hover-end.png (same line, 26 s later), audit/screens/status-bar-x-h-hover-page.png

### Reduced motion
**Should:** Rotation is disabled for visitors who prefer reduced motion.
**Did:** Correct — and completely still. With `prefers-reduced-motion: reduce` the bar
showed `FREE UK SHIPPING OVER £20 — ORDER BY 18:00 FOR SAME-DAY DISPATCH` and held it
for the full 25 seconds I watched; the second message stayed hidden the whole time.
The right message won: the useful one (shipping) is message 1, so the reduced-motion
shopper keeps the delivery promise and loses only the product count — which the
homepage boot line and the catalogue header both tell them anyway.
**Verdict:** works
**Shopper cost:** none today, but it is a standing trap: anything the owner puts in
message 2 or later is invisible to a reduced-motion shopper, permanently. If a returns
or cut-off line ever lands in slot 2, that audience never sees it.
**Evidence:** audit/screens/status-bar-x-rm-t0.png and audit/screens/status-bar-x-rm-t25.png (identical, 25 s apart), audit/screens/status-bar-x-rm-page.png

### With JavaScript off
**Should:** With JS absent the first message shows (the bar clips the rest).
**Did:** Not quite — it shows both, colliding. The two messages sit side by side in
a 28px-tall strip. Message 1 wraps onto two lines (`FREE UK SHIPPING OVER £20 — ORDER` /
`BY 18:00 FOR SAME-DAY DISPATCH`) and message 2 is squeezed into a narrow column
beside it as three lines — `12 PRODUCTS` / `CURRENTLY` / `ONLINE` — of which the top
line is cropped by the top edge and `ONLINE` is sliced in half by the bottom border.
The very first thing on the page reads as garbled text. Nothing changes after 20
seconds of waiting, so it is not a mid-load flicker — it is the finished state.
**Verdict:** partly (renders, but not as the spec describes, and not legibly)
**Shopper cost:** a no-JS shopper's first impression of the site is a broken-looking
top line — on a store whose entire proposition is that it looks deliberate. Worse, the
delivery promise itself is the sentence being mangled.
**Evidence:** audit/screens/status-bar-x-h-nojs-bar.png, audit/screens/status-bar-x-h-nojs-1.png, audit/screens/status-bar-x-h-nojs-after20s.png (unchanged after 20 s)

### Legibility on a phone — the two-line squeeze
**Should:** A one-line ticker.
**Did:** On a 390px phone it is not one line. `FREE UK SHIPPING OVER £20 — ORDER BY
18:00 FOR SAME-DAY DISPATCH` wraps onto two lines inside a bar that is 28px tall and
clips its overflow: the text block measures 28.78px, so the bar shaves the bottom of
`SAME-DAY DISPATCH`, which sits flush against the header's border with no breathing
room. It is readable, but it reads as cramped rather than composed. The count line,
being short, sits on one line with room to spare — so the bar visibly changes shape
as it rotates. On desktop (1440px) message 1 is a comfortable single line occupying
the leftmost third of the bar.
**Verdict:** partly
**Shopper cost:** the one line carrying real information is the one that looks squashed,
on the device most shoppers arrive on.
**Evidence:** audit/screens/status-bar-x-h-m-bar1.png (two lines, bottom shaved), audit/screens/status-bar-x-home-top.png, audit/screens/status-bar-x-pdp-top.png, versus audit/screens/status-bar-x-d-crop1.png (desktop, one line)

### Something else lands on top of it
**Should:** n/a — this is what actually happens to the bar in use.
**Did:** On my first homepage load the bar rendered clean; by the time I had watched
three rotations, the `CRACK THE CUFFS.` modal (`10% off your first order if you do.
Three tumblers. Tap each one at the right moment.`) had opened over the whole page,
dimming the ticker to near-invisibility and putting its own close button exactly where
the bar sits. The same thing happened on desktop. While it is up, hovering the bar does
nothing, because the pointer is on the overlay. The cookie consent sheet takes the bottom
of the screen at the same time.
**Verdict:** partly — the bar works; it just is not on screen when a first-time shopper
is looking at the homepage.
**Shopper cost:** the free-shipping threshold is delivered on the one screen where it is
guaranteed to be covered up.
**Evidence:** audit/screens/status-bar-x-msg1.png (mobile home, modal over the bar), audit/screens/status-bar-x-d-hover-26s.png (desktop, ticker dimmed behind the modal, close button occupying the bar)

### Where it sits, and what it costs
**Should:** Sit above the header without doing damage.
**Did:** It occupies 28px at the very top: 3.3% of a portrait phone screen, 7.2% of a
landscape one. It is not sticky — less than a screen's worth of scrolling (I checked at
700px and again at 900px) takes both it and the header off the top for good, so
the shipping promise exists only in the first screenful and never comes back. On the
catalogue the first product card starts at 376px on a portrait phone; the ticker is 28
of those 376, so it is not what keeps product off the fold. On a landscape phone the
picture is worse but not mainly its fault: bar, header and the `ALL / 12 ITEMS` band
fill the top, and the cookie sheet takes the rest, leaving no product visible at all.
**Verdict:** works (the vertical cost is real but small)
**Evidence:** audit/screens/status-bar-x-h-landscape.png (nothing purchasable above the fold), audit/screens/status-bar-x-scrolled-clean.png and audit/screens/status-bar-x-scrolled-clean-9s.png (bar and header gone after a 900px scroll, and still gone nine seconds later), audit/screens/status-bar-x-collection-all.png (bar and `12 ITEMS` on the catalogue)

---

## JUDGEMENT — does a shopper read this, or is it wallpaper?

**Mostly wallpaper, with one line in it that is doing real work by accident.**

It is 9px type — the bottom of this theme's type scale — in `rgb(138,131,119)` on
`rgb(14,12,19)`, letter-spaced, above the logo, in the strip every shopper alive has
been trained to treat as a marketing banner. Measured on the same page, the header links
beneath it compute to 20px and the card prices to 22px. Half of its airtime goes to
`12 PRODUCTS CURRENTLY ONLINE`, which on the homepage duplicates the boot line about
200px below it (`> 12 PRODUCTS AVAILABLE TO PURCHASE`) and on the catalogue duplicates
the register header (`12 ITEMS`) in the very same frame. That half is pure decoration:
it tells a shopper something already on their screen.

The other half is not decoration at all. `FREE UK SHIPPING OVER £20 — ORDER BY 18:00
FOR SAME-DAY DISPATCH` is the only place on the shopping path where the free-delivery
threshold appears. I scanned the full visible text of the homepage, the catalogue, a
product page **with every accordion forced open — including `CHAIN OF CUSTODY — SHIPPING
& RETURNS`** — and the cart, and `£20` appears nowhere except in this ticker. The product
page carries the cut-off in its own words (`Order before 18:00 and it ships today
(Mon–Sat)`) but never the threshold. So the single commercial fact most likely to make
someone add a second item is being delivered, at 9px, in a rotating strip, for eight
seconds out of every sixteen, only above the fold, and on the homepage it is behind a
modal.

That is the finding: **the bar is the wrong home for the only copy of the £20 line.**
It belongs where the decision is made — beside the price and the buy button on the
product page (where the 18:00 cut-off already lives, in the same voice), and in the bag.
The ticker can keep it as a repeat. Both fixes are plain text in existing components:
no new colour, no badge, no radius, no timer, nothing fabricated.

**Does it push anything important down the page?** Not meaningfully — 28px, and the
first product card is not what it displaces. The genuine cost is not vertical, it is
attentional: it spends half its life repeating a number and the other half hiding a
promise.

---

## Surprises

- **The `[count]` line is redundant on both pages it appears on.** `12 PRODUCTS CURRENTLY
  ONLINE` sits ~280px above `> 12 PRODUCTS AVAILABLE TO PURCHASE` on the homepage and
  above `12 ITEMS` on the catalogue. Half the ticker's airtime restates what is already
  on screen. (audit/screens/status-bar-x-count-vs-register.png, audit/screens/status-bar-x-home-top.png)
- **The `£20` free-shipping threshold exists nowhere else on the shopping path.** Not on
  the product page, not inside the opened `CHAIN OF CUSTODY — SHIPPING & RETURNS`
  accordion, not on the empty cart page. (audit/screens/status-bar-x-pdp-custody-open.png,
  audit/screens/status-bar-x-cart-loaded.png)
- **With JavaScript off the bar is visibly broken**, not gracefully truncated: two
  messages collide and `ONLINE` is cut in half. The spec and the code comment both say
  the first message simply shows. (audit/screens/status-bar-x-h-nojs-bar.png)
- **On a phone the useful message is two lines in a 28px bar**, bottom shaved, jammed
  against the header rule. (audit/screens/status-bar-x-h-m-bar1.png)
- **The homepage modal covers the bar within a minute of landing**, taking the hover
  pause with it. (audit/screens/status-bar-x-msg1.png, audit/screens/status-bar-x-d-hover-26s.png)
- Only **two** message blocks are installed. The section's own preset ships three (the
  third being `PROPERTY STORE — UNIT 7, LONDON`); this install does not have it, so the
  loop is a two-beat, back-and-forth at 16 seconds.

## Missing

- Any repeat of the free-shipping threshold at the moment of decision — the product page
  and the bag both go without it.
- Anything a shopper needs that a ticker is genuinely good at: returns window, dispatch
  days, stock. The bar says `SAME-DAY DISPATCH` with no days named.
- A way to see message 2 at all under reduced motion (by design), and no control — no
  pause button, no dots, no way to re-read a line you half-caught other than waiting 16
  seconds.
- The bar never returns after a scroll, so a shopper who lands deep (an Instagram link
  to a product) and scrolls has no second chance at the £20 line.

## Contradictions

- **Dispatch days.** The ticker: `FREE UK SHIPPING OVER £20 — ORDER BY 18:00 FOR SAME-DAY
  DISPATCH`. The product page, two screens down: `Order before 18:00 and it ships today
  (Mon–Sat)`. A shopper ordering at 17:00 on a Sunday reads the top line and expects it
  to leave that day. (audit/screens/status-bar-x-pdp-top.png,
  audit/screens/status-bar-x-socks-pdp.png)
- **Product count vs the store.** The bar says `12 PRODUCTS CURRENTLY ONLINE`; the store
  serves 13 published products, the thirteenth being `CELLBLOCK SET` at `£85.00`, which
  has a live page a shopper can reach and buy from but appears in no register and carries
  no `PRODUCT n / N` line. Nothing on screen contradicts itself — but "currently online"
  is not literally true of the catalogue. (audit/screens/status-bar-x-set-pdp.png)
- Ticker (`SAME-DAY DISPATCH`) against the known V2 BAGGIES / jeans description claim of
  `9-16 days delivery uk` — already on the known list, flagged here only because the two
  sit on the same screen as each other on those product pages.

## Works and must be protected

- **The hover pause genuinely works** — 26 seconds held, resumed within 9 of leaving. Rare
  and correct; do not let a refactor lose it.
- **Reduced motion parks on message 1** — the shipping line, not the count. That ordering
  is load-bearing and should survive any future edit to the block order.
- **`[count]` is honest.** 12 in the ticker, 12 in the register, 12 in the hero, `/ 12` in
  every product footer. No inflation, no fake "now viewing", no counter theatre — exactly
  what this store's proposition needs.
- **The bar is present and consistent everywhere** — homepage, catalogue, product, cart —
  with the same wording. No page-specific drift.
- **No fake urgency in it.** It says a shipping threshold and a stock-neutral fact. Keep it
  that way; the temptation with a rotating bar is to fill it with countdowns.
