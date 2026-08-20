# raw-carriage — the carriage progress bar (Q2)

Area key: `carriage`. Section `crooks-cart-progress`, rendered **first** on `index.json`,
`product.json`, `collection.json`, `search.json` and `cart.json`.
All measurements on a 390×844 phone, GB market, GBP.

---

### The bar on an empty cart

**Should:** Per the brief, it "renders above everything on home, product, collection and
search", so an empty-cart shopper should see it telling them how far they are from £20.

**Did:** Nothing. **With an empty bag the section does not render at all.** Not on the
homepage, not on a product page, not on a collection. What a GB shopper actually lands on
is the status line, the header, then straight into the hero. On the homepage the first two
product cards — `NO. 01 SWEATS CHARCOAL CELLBLOCK CREWNECK £50.00 AVAILABLE` and `NO. 02` —
are the last thing on the landing screen, at **757px, 0.90 screenfuls** down.

The only shipping statement on that first screen is the rotating status bar:

> `FREE UK SHIPPING OVER £20 — ORDER BY 18:00 FOR SAME-DAY DISPATCH`

which is one of two messages the status bar rotates between. I caught the other one on
screen mid-run — `12 PRODUCTS CURRENTLY ONLINE`
(`carriage-43-pdp-top-stale-bar-after-add.png`, top line) — so the shipping sentence is
genuinely absent from the top of the page for stretches at a time, and it never mentions
the second tier at all. (The rotation interval is the known `D1` setting.)

The gate is `if crk_country == section.settings.country_code and cart.item_count > 0`.

**Verdict:** works — but not the way the brief or `SPEC.md §3.7` describes. This is the most
important fact about this feature and it is written down nowhere: **the bar costs a shopper
nothing until they have already put something in the bag.**

**Shopper cost:** None in space. There is a cost in information: the person who has not yet
added anything is the one who most needs to know £20 is the line, and they are told it only
by a message that rotates itself off screen.

**Evidence:** `audit/screens/carriage-01-home-empty-cart-no-bar.png` (home, `BAG [0]`, no
bar, NO. 01 and NO. 02 on screen), `carriage-02-pdp-empty-cart-no-bar.png`,
`carriage-03-pdp-empty-cart-duffle.png`.

---

### The two tiers — exact wording at every stage

**Should:** Move through both tiers: free Tracked 48 over £20, free Tracked 24 over £70.

**Did:** It does, and the wording is consistent on all five templates. Read off the screen:

| Cart | Message on screen | Fill | `aria-valuenow` |
|---|---|---|---|
| £0.00 | *(no bar at all)* | — | — |
| £18.00 | `> £2.00 to free Tracked 48` | 25% | 25 |
| £50.00 | `> £20.00 to free Tracked 24` | 71% | 71 |
| £61.00 | `> £9.00 to free Tracked 24` | 87% | 87 |
| £67.00 | `> £3.00 to free Tracked 24` | 95% | 95 |
| £75.00 | `> Free Tracked 24 — unlocked` | 100% | 100 |

The `> ` is a CSS `::before`, so that is exactly what a shopper reads. Under the track sit
two labels that read `TRACKED 48 FREE` and `TRACKED 24 FREE`, each gaining a `✓ ` and the
accent colour when its tier is met — at £75 the line reads `✓ TRACKED 48 FREE` /
`✓ TRACKED 24 FREE`. The track is `role="progressbar"`, `aria-label="Progress toward free
carriage"`, with a 1px tick at 28% where tier 1 lands.

Two details are quietly right: the fill is measured against the **top** tier so the bar
keeps moving after £20 rather than filling up and stopping; and it is held at 99% until a
tier is genuinely met, so a full bar never sits next to `£0.01 to go`. And the numbers are
true — I read the live rate card from the Admin API and the UK zone carries `Tracked 48
£3.00`, `Tracked 48 £0.00 when total ≥ £20`, `Tracked 24 £4.99`, `Tracked 24 £0.00 when
total ≥ £70`. The bar promises nothing checkout will withdraw.

**Verdict:** works.

**Evidence:** `carriage-11-home-bar-18-two-pounds-short.png`, `carriage-12-home-bar-61.png`,
`carriage-13-home-bar-67-three-pounds-short.png`,
`carriage-44-pdp-bar-unlocked-after-reload.png`, `carriage-45-home-bar-unlocked.png`.

---

### Does it update after an add to cart, without a page reload?

**Should:** `SPEC.md §3.7` — *"the script only keeps it correct on AJAX cart updates
(`cart:update`, plus a `/cart.js` re-read)"*. The bar should move the moment you add.

**Did: no. Tested explicitly, twice, and it does not move.**

*Case 1 — the bar is already on the page.* Bag at £50, CRXST★RZ T-SHIRT page, bar reading
`> £20.00 to free Tracked 24` at 71%. I picked size M, scrolled down to `ADD TO BAG` and
tapped it. The bag went to £75 — both tiers now met, free Tracked 24 earned. The bar
carried on reading **`> £20.00 to free Tracked 24`, fill still 71%**. I scrolled back to the
top to look at it: unchanged. Only a page reload turned it into
`> Free Tracked 24 — unlocked` at 100%. So the shopper who has just qualified for free
next-day carriage is being told, at the top of the page, that they are still £20 short of it.

*Case 2 — the first add of the session.* Empty bag, tap `ADD TO BAG` on a £50 crewneck.
No bar appears at all, because with an empty cart the section was never rendered, so there
is nothing on the page for the script to update. Same on a second product. The bar only
turns up on the next page load.

**Why:** `crooks-cart-progress.js` refreshes on exactly two triggers —
`document.addEventListener('cart:update', …)` and `('crk:cart:update', …)`. The theme's own
PDP add-to-bag lives in `assets/crooks-record.js`, which POSTs `/cart/add.js`, re-reads
`/cart.js`, updates the bag count and prints the confirmation — and dispatches **neither**
event. `grep -n "dispatchEvent\|CustomEvent\|cart:update" assets/crooks-record.js` returns
nothing at all. Horizon's cart components do fire `cart:update`, which is why the bar is
live on `/cart` when a quantity changes there — but nothing fires it on a product page,
and the product page is the only place a shopper adds anything.

**What the shopper actually sees at the moment they add:** at the instant of tapping I was
scrolled 854px down the page — the bar occupies y 139–299, so it was **more than a full
screen above the fold**. Nothing scrolls, nothing opens (the cart drawer CSS is
deliberately unloaded, `SPEC.md §9.9`). The feedback is one line under the button,
`Added — 2 in bag  View bag`, and the header count ticking `BAG [1]` → `BAG [2]`. That line
is clear and calm and does its job. The carriage bar contributes nothing to the moment.

**Verdict:** broken. Correct on every full page load; live on `/cart`; dead on the product
page, and absent entirely for the add that matters most — the first one.

**Shopper cost:** A readout whose whole purpose is to react does not react. Worse than
stale: at £75 it actively understates what the shopper has earned, and a shopper who adds
one more item specifically to clear a threshold gets no confirmation that they did.

**Fix inside the design law:** one line at the end of the success branch in
`crooks-record.js` — `document.dispatchEvent(new CustomEvent('crk:cart:update'))`. The
listener already exists. No CSS, no markup, no new dependency. The first-add case needs the
section to render a shell when the cart is empty (or the script to insert one) — see the
judgement below, where that shell earns its keep anyway.

**Evidence:** `carriage-40-pdp-bar-present-before-add.png` (`£20.00 to free Tracked 24`,
71%), `carriage-41-pdp-moment-of-tap-bar-offscreen.png` (scrolled 854px, bar nowhere in
sight), `carriage-42-pdp-after-add-no-reload.png` and
`carriage-43-pdp-top-stale-bar-after-add.png` (bag now £75, bar still says `£20.00 to free
Tracked 24`), `carriage-44-pdp-bar-unlocked-after-reload.png` (reload → `Free Tracked 24 —
unlocked`, 100%). First-add case: `carriage-21-pdp-moment-of-tap.png`,
`carriage-22-pdp-after-add-no-reload.png`, `carriage-04-moment-of-first-add.png`,
`carriage-05-top-after-first-add-still-no-bar.png`.

---

### THE JUDGEMENT — does it earn its position?

**What it costs, measured.** The section occupies **y 139–299 — exactly 160px, 0.19 of a
390×844 screen** — identically on all five templates. On the homepage:

| | first product card (`NO. 01`) | |
|---|---|---|
| bar absent (empty bag, or any non-GB shopper) | **757px — 0.90 screenfuls** | on the landing screen |
| bar present | **917px — 1.09 screenfuls** | off the landing screen |

That is the whole finding in one line: **0.19 of a screenful is exactly the amount that
tips the first product off the first screen.** With an empty bag a shopper lands on
CROOKSLDN and can see two products without moving a finger. Put one thing in the bag and
the landing view becomes status line, header, carriage bar, boot line, wordmark, tagline,
CATALOGUE button, CATALOGUE heading, view toggles — and no product at all. The council's
recorded figure of 1.22 → 1.48 viewports is the same effect measured to a different
landmark; my number is to the card itself.

Same 160px on the other surfaces: the product record starts at 139px without the bar and
299px with it; the collection register at 139 → 299; search results at 314 → 474; the cart
lines at 379.

**On the HOMEPAGE, empty cart — the case the question asks about: the bar is not there.**
A shopper who has never seen a price is not shown a progress bar toward a threshold they
have no way to evaluate, and their landing view keeps its two product cards. That is the
right call and it is already in the code. The question answers itself. Where it *does*
appear on the homepage — a returning shopper with a loaded bag — it is buying 0.19 of a
screen, and what it pushes off is the register. **That is a poor trade even for the good
case:** the homepage's job is to get someone into the catalogue, and this is the one
component that stops the catalogue being visible on arrival. Worth noting alongside it that
`SPEC.md §3.3` records the attract board being taken off the homepage (`show_board` false);
the space that freed is now spent here.

**On a PRODUCT page, mid-decision: no — this is the worst placement of the five.** Not
because the message is wrong but because the geometry and the message point in opposite
directions. The bar is pinned to the top of the document. The decision — size, price,
`ADD TO BAG` — happens 850px further down, and on mobile at a sticky bar at the very
bottom. Measured: at the moment of tapping, the shopper was 854px down and the bar was
555px above the top of their screen. So it charges its cost where the attention is not, and
then fails to update at the one moment attention might come back to it. Meanwhile the PDP's
*own* statement of the same fact — `Shipped with Royal Mail Tracked. Free UK shipping over
£20, and free Tracked 24 over £70.` — is accurate and sitting inside `CHAIN OF CUSTODY —
SHIPPING & RETURNS`, which defaults closed. The information a mid-decision shopper needs is
on the page twice: once above the fold where they cannot act on it, once where they will
not open it. Neither is beside the buy button.

**On a COLLECTION page: the best of the four.** Someone scanning a register of £45–£60
prices is exactly the person weighing whether to add one more thing to clear £20, and
`> £3.00 to free Tracked 24` above that register is a real prompt. Same 160px, materially
more value.

**On a SEARCH page: no.** A shopper who typed `jorts` asked a specific question; the bar
spends 0.19 of a screen pushing the answer down and adds nothing to the task. Worst
value-per-pixel of the five.

**Where it genuinely earns its place: `/cart`.** The message is immediately actionable, the
shopper is already thinking about total spend, and — not coincidentally — it is the only
surface where the thing actually updates live.

**Recommendation, implementable inside the design law** (radius 0, 1px borders, no shadow,
no gradient, no third typeface, no new colour, no fabricated content, no build step):

1. Keep it on `cart.json` and `collection.json`.
2. Remove it from `index.json` and `search.json`. The homepage already carries the £20 line
   in the status bar — stop that message rotating, add the £70 tier to it, and the homepage
   loses nothing while getting its first product card back above the fold.
3. On `product.json`, move the same one-line readout out of the top-of-page section and into
   the buy panel beside the delivery line, where `Order before 18:00 and it ships today` and
   `Ordered now — leaves today` already live. It is already a `crk-data` line — mono, 1px,
   radius 0 — so it needs no new design vocabulary, and it would then sit next to
   `ADD TO BAG`, where both the decision and the update happen.
4. Whatever else changes, dispatch `crk:cart:update` from `crooks-record.js`.

**Verdict:** partly. The readout is honest, well built and commercially sound. Its
*position* is earned on two of the five templates it occupies.

**Evidence:** `carriage-01-home-empty-cart-no-bar.png` vs
`carriage-11-home-bar-18-two-pounds-short.png` and `carriage-45-home-bar-unlocked.png` —
the same landing view with and without the bar, product cards present and then gone.
`carriage-16-pdp-bar-67.png`, `carriage-14-collection-bar-67.png`,
`carriage-15-search-bar-67.png`, `carriage-17-cart-bar-67.png`.

---

### Empty cart vs £3 short — which is doing the commercial work?

**The empty-cart shopper is told,** by the carriage bar, nothing at all. By the status bar,
`FREE UK SHIPPING OVER £20 — ORDER BY 18:00 FOR SAME-DAY DISPATCH`, on screen roughly half
the time and silent about the second tier. That is a fact, not a prompt: it names a
threshold before the shopper knows a crewneck is £50 and a pair of socks is £6, so "£20"
carries no information about whether it is easy or hard to reach.

**The £3-short shopper is told** `> £3.00 to free Tracked 24`, with the bar 95% filled,
attached to a bag they have already committed to, in a store whose cheapest item is a £6
pair of socks. A specific, closeable gap, an obvious way to close it, and £4.99 saved by
closing it. That is the only copy in this feature doing commercial work — and the same is
true one tier down, where £18 in the bag reads `> £2.00 to free Tracked 48`.

**Which argues against deleting the bar, and for moving it.** The gap-closing message is
the valuable half, and the empty-cart half is already correctly suppressed. The problem is
that the valuable message is displayed at the top of pages where the shopper cannot act on
it, and is missing from the two places where they can — beside the buy button, and in the
moment immediately after an add.

**Verdict:** works (the near-threshold message) / absent (any useful empty-cart equivalent).

**Evidence:** `carriage-13-home-bar-67-three-pounds-short.png` (`> £3.00 to free Tracked
24`, 95%), `carriage-11-home-bar-18-two-pounds-short.png` (`> £2.00 to free Tracked 48`),
`carriage-01-home-empty-cart-no-bar.png`.

---

### Collection and search — same cost, same value?

**Should:** Same section, same position, same cost.

**Did:** Same cost exactly — 160px, y 139–299, identical wording, on both. The value is not
the same. On `/collections/all` the register block moves 139 → 299px and the shopper is
mid-comparison, a live candidate to add one more item; the prompt fits the task. On
`/search?q=jorts` the results move 314 → 474px — the shopper asked a specific question and
the bar is 0.19 of a screen of delay on the answer.

One wrinkle worth naming: on `/search` with an empty query the register deliberately stands
down and renders nothing (`SPEC.md §9.8`), but the carriage section is a separate section
and still renders. A shopper who opens search with items in the bag gets a shipping progress
bar sitting on top of a page with nothing else on it.

**Verdict:** partly — same cost, collection justifies it, search does not.

**Shopper cost:** 0.19 of a screen of the results the shopper explicitly asked for, on every
search.

**Evidence:** `carriage-14-collection-bar-67.png`, `carriage-15-search-bar-67.png`.

---

### What a shopper outside the UK gets

**Should:** The bar is gated to `country_code` GB because no other market has a free tier,
so an overseas shopper should not be chased toward a threshold that cannot apply to them.

**Did:** Correct, and I checked it as a shopper. In a US context — `Shopify.country` `US`,
currency `USD`, prices rendering `$70.00` / `$63.00` / `$84.00` — with **two items and
$140.00 in the bag**, no carriage bar renders on the homepage or on a product page. The
premise holds too: the live rate card has no free tier anywhere outside the UK zone.

| Zone | Rates |
|---|---|
| United Kingdom | Tracked 48 £3.00 · **£0.00 at ≥ £20** · Tracked 24 £4.99 · **£0.00 at ≥ £70** |
| Channel Islands (GG, JE) | Tracked 48 £3.99 · Tracked 24 £7.00 · **no free tier at any value** |
| EU | Standard international £12.99 · no free tier |
| International (incl. US) | Standard international £18.99 · no free tier |

**But the gating stops at the bar, and nothing else follows it.** In that same US session,
the header still reads `FREE UK SHIPPING OVER £20 — ORDER BY 18:00 FOR SAME-DAY DISPATCH`
directly above a wall of dollar prices, and the product page's Chain of custody still reads
`Shipped with Royal Mail Tracked. Free UK shipping over £20, and free Tracked 24 over £70.`
Terms and the FAQ repeat it. So the one component that knows about the shopper's country
responds by going silent, while every component that does not know carries on promising a
£20 free-shipping line to someone who will be charged £18.99.

The sharpest version is the Channel Islands, which has its own market: a Jersey or Guernsey
shopper sees GBP prices and the same `FREE UK SHIPPING OVER £20` header, and their cheapest
real rate is £3.99, with no free tier at any basket value, ever.

**Verdict:** works (the bar's own gating) / broken (everything around it).

**Shopper cost:** An overseas shopper builds a basket believing shipping is free over £20
and meets £12.99 or £18.99 at checkout. That is precisely the failure the section's own
comment block says it exists to prevent — it just prevents it in one component out of five
places the claim is made.

**Evidence:** `carriage-30-nongb-home.png` (US, `BAG [2]`, `$70.00` prices, no bar, header
still promising free UK shipping over £20), `carriage-31-nongb-pdp.png`,
`carriage-32-nongb-pdp-custody.png` (custody step 02, in a dollar store). Rate card from a
read-only Admin `deliveryProfiles` query.

---

## Surprises

- **The bar does not exist on an empty cart.** `cart.item_count > 0` is in the render gate.
  Every discussion of this feature — `SPEC.md §3.7`, and the round-2 council note that took
  it off the protect list over its viewport cost — reads as though it is always present. It
  is not. The space is charged only to shoppers who already have something in the bag, which
  is a far better trade than the note implies, and it means the "homepage, empty cart"
  objection is already answered in code.
- **It never updates after a product-page add to bag.** Confirmed on screen: bag goes £50 →
  £75, both tiers met, and the bar keeps reading `£20.00 to free Tracked 24` at 71% until a
  reload. `crooks-cart-progress.js` listens for `cart:update` / `crk:cart:update`;
  `crooks-record.js` dispatches neither. `SPEC.md §3.7` states the opposite. One
  `dispatchEvent` line fixes it.
- **On the first add of a session there is nothing to update.** Empty cart means no section
  in the DOM, so even a correct event would find no element. A shopper's first add produces
  no carriage feedback whatsoever until the next page load.
- **0.19 of a screenful is exactly the difference between seeing a product on the homepage
  and not.** First card 757px with no bar, 917px with it, on a 390×844 phone. Empty bag: two
  products on the landing screen. One item in the bag: none.
- **The store's only always-on shipping statement rotates itself off screen** — caught in the
  act in `carriage-43-pdp-top-stale-bar-after-add.png`, where the top line reads
  `12 PRODUCTS CURRENTLY ONLINE` instead of `FREE UK SHIPPING OVER £20 — ORDER BY 18:00 FOR
  SAME-DAY DISPATCH`. Combined with the empty-cart gate, a first-time visitor can browse the
  whole homepage and never be told about free shipping at all.
- **The £70 tier is invisible until you have already spent £20.** No always-on copy anywhere
  in the chrome mentions Tracked 24 — the status bar names only the £20 line, and the £70
  line lives in a closed accordion and in Terms/FAQ.
- **The thresholds are true.** UK free Tracked 48 at £20 and free Tracked 24 at £70 are live,
  active rates in the delivery profile. This feature tells the truth, which is more than the
  copy around it does.
- A Shopify cookie-consent banner covers roughly the bottom 45% of a 390×844 first view and
  intercepts taps. Not this area's finding, but it is the first thing on screen and it
  changes what "the landing view" is.

## Missing

- Any statement of the £70 tier that an empty-cart shopper will actually read.
- Any carriage feedback at the moment of an add to bag — the one moment a shopper is most
  receptive to "spend £2 more and carriage is free".
- Any carriage readout near the buy controls on a product page. At the moment of tapping
  `ADD TO BAG` the bar is 555px above the top of the shopper's screen.
- Any country-aware equivalent for non-GB shoppers. The bar goes silent, but nothing tells
  an EU or US shopper that the £20 line still printed above them is not theirs, or that
  their shipping will be £12.99 or £18.99.

## Contradictions

- **The store promises every country a UK threshold.** Header, every market, verified in a US
  session with dollar prices on screen: `FREE UK SHIPPING OVER £20 — ORDER BY 18:00 FOR
  SAME-DAY DISPATCH`. Rate card: EU `Standard international £12.99`, no free tier;
  International incl. US `Standard international £18.99`, no free tier; Channel Islands
  `Tracked 48 £3.99` / `Tracked 24 £7.00`, no free tier at any value. The carriage bar
  correctly hides itself outside GB; the sentence directly above it does not.
- **The bar contradicts the bag it is reporting on.** After an add to bag the page shows
  `Added — 2 in bag` (bag = £75, free Tracked 24 earned) and, 555px above it,
  `> £20.00 to free Tracked 24`. Both on screen in the same document, from the same cart.
- **`SPEC.md §3.7` vs the deployed script.** Spec: *"the script only keeps it correct on AJAX
  cart updates (`cart:update`, plus a `/cart.js` re-read)"*, presented as covering the
  theme's own add-to-bag path. Observed: it does not fire, so an AJAX add leaves the bar
  stale until a reload.
- **The same shipping fact told twice on a PDP, in two places a shopper cannot use.** Above
  the fold: `> £20.00 to free Tracked 24`, off screen by the time they reach the buy
  controls. Below, inside `CHAIN OF CUSTODY — SHIPPING & RETURNS`, which defaults closed:
  `Free UK shipping over £20, and free Tracked 24 over £70.` Neither is visible at the moment
  of decision.

## Works and must be protected

- **The `cart.item_count > 0` gate.** It is the reason this feature is defensible at all, and
  it is worth 0.19 of a screen to every first-time visitor. Do not "fix" the bar by giving it
  an empty-cart state on the homepage.
- **The GB gate on `country_code`,** and the reasoning in its comment block. It is the one
  component in the build that refuses to make a shipping promise it cannot keep.
- **Thresholds that match the real delivery profile** (£20 / £70, checked against the live
  rate card). If these ever drift, the bar starts promising carriage that checkout withdraws.
- **Fill measured against the top tier, and held at 99% until a tier is genuinely met.** Both
  are the difference between an instrument and a sales device.
- **Plain English inside the fiction.** `£3.00 to free Tracked 24` names a real Royal Mail
  service and a real number. No countdown, no colour escalation, no "only £3 away!!". This is
  `SPEC.md §0` holding under pressure and it should not be touched.
- **The segmented meter and the `✓ TRACKED 48 FREE` / `✓ TRACKED 24 FREE` labels.** They read
  as instrumentation rather than a sales widget, which is the entire proposition of the site.
- **`aria-label="Progress toward free carriage"`, live `aria-valuenow`, `aria-live="polite"`
  on the message.** The accessibility profile in `SPEC.md §9.10` depends on them.

---

*Scripts: `audit/_tools/carr5.mjs`, `carr6.mjs`, `carr7.mjs`. The store returned HTTP 429 and
a Cloudflare interstitial for a stretch of this run; `nav()` in those scripts backs off and
retries, and every figure quoted above comes from a page that passed the `.crk-root` +
theme-id assertion.*
