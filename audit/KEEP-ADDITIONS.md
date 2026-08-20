# KEEP-ADDITIONS — what this audit found working that is not yet protected

`audit/_ref/KEEP.md` already protects the board's pause guards, the product
page's first viewport, the measurement apparatus, the accessibility profile, the
no-JS fallback, the writing, the register, the refusal to fake data, the radius
enforcement, the sold-out/notify pattern, the FILED status slot and the
two-action sticky bar. **None of that is repeated here.**

This file adds what twenty journeys and a twelve-area census found load-bearing
that nobody had written down. Audits that only list faults get acted on badly —
the distinctive things get sanded off because nobody recorded that they were
holding something up.

---

## The nine additions

### 1. The quiet add-to-bag confirmation — and specifically the *absence* of a cart drawer

`> Added — 1 in bag  View bag`, a header counter, and nothing thrown over the
screen. **Ten journeys.** It is the reason three of the four hardest journeys in
the set have a best moment at all.

> 13, sideways on a 390-tall screen: *"On a screen this short, a cart drawer
> would have been a disaster and they didn't build one."*
> 14, on one bar of signal, got it inside a second, in the bottom bar where his
> thumb already was.
> 18, reduced motion: *"Nothing here was carried by an animation, so nothing was
> lost when the animation didn't happen."*

`SPEC.md §6` records `crooks-cart-drawer.css` as deliberately unloaded. That
decision is now evidenced from the shopper side. **Do not add a cart drawer.**

### 2. Text before pictures on a bad connection

At three seconds on congested 4G, the **entire catalogue is readable** — every
product as a numbered line with category, name, price and stock — with one
photograph of thirty-one loaded (journey 14). She never once thought the site
was broken. Most shops give a skeleton; this one gives the shop.

This is a direct consequence of the austere design, and it is the single
clearest case of the aesthetic *paying* rather than costing.

### 3. Price and stock word inside the link itself

Nine journeys. It works three different ways at once: readable at three seconds
on a bad connection (14), announced inside the link name to a screen reader
(16), and scannable as a whole catalogue in two wheel-flicks (19).

> 16: *"the price and whether it's in stock are inside the link — I know what a
> thing costs before I open it, which decides whether I bother."*

### 4. The dispatch promise switches itself off when a size is sold out

Nobody had recorded this. Pick a sold-out size and `Order before 18:00 and it
ships today` disappears rather than sitting above a dead button.

> 06: *"that's the difference between a shop that's out of stock and a shop
> that's lying to you."*

Verified independently in `raw-notify-verify.md` after one census pass reported
the opposite. It holds.

### 5. `Decline` the same size and weight as `Accept`

Ten journeys, and every one of them expected the opposite.

> 02: *"They didn't try it on. Noted."* — and he explicitly banked extra
> patience for the rest of the site on it.

**Caveat that makes this urgent rather than merely nice:** at 200% zoom
`Decline` is the button whose edge runs off the screen while `Accept` sits
comfortably inside, and journey 17 accepted tracking she did not want. The
protection is worth keeping and currently breaks at one zoom level.

### 6. The £45 that is £45 in three places

The set sceptic (05) arrived specifically to prove the individual prices had
been inflated to manufacture the £10 saving, and could not.

> *"£45 is £45 on its own page, on the crewneck's rail, and later in the cart's
> own recommendations — the same number in three separate places, none of them
> dressed up as a discount. That is the single most trust-building thing on this
> site and they probably don't know it's doing any work."*

No compare-at price anywhere. **Never introduce one.**

### 7. The set's cart line names both garments and both sizes

`CELLBLOCK SET` / `CHARCOAL CELLBLOCK CREWNECK - M` / `CHARCOAL CELLBLOCK
SHORTS - L` / `£85.00`. Two journeys called it the clearest thing in the build —
nothing has to be inferred. Everything *around* the bundle leaks; this line does
not. **Protect it while fixing the rest.**

### 8. The drawer's focus trap — now verified three times

Twenty Tab presses cycle sixteen controls and wrap; zero land outside; Shift-Tab
stays inside; Escape returns focus to `MENU`. One run reported the opposite and
was wrong — see `RUN-NOTES.md`. It is on `SPEC.md §9`'s list already, but the
*evidence* is new and it nearly got "fixed" on a false report. **Leave it alone.**

### 9. The sticky bar standing down entirely on a wide screen

At 1440 the bottom bar never appears at all — checked at seven scroll positions.
The real buy panel and a floating copy are never on screen together.

> 19: *"Good. Leave it exactly as it is."* — the opposite of what most shops do
> to a laptop.

**Condition, not device:** at 200% zoom the same absence costs journey 17 a
scroll up and back every time, because her size row and `ADD TO BAG` can never
share a screen. Any change here must be conditional on the zoom, and 19's
version must not be sacrificed to 17's.

---

## And the sentence that should govern any fix pass

From the coldest reader in the panel — journey 01, a stranger who arrived from
an Instagram story and did not buy:

> *"The terminal thing is a reason to remember them, not a reason to distrust
> them. That only holds because the money words are plain: had the second
> `£60.00` been styled as `EXHIBIT VALUE: 60` I'd have gone."*

`KEEP.md §2` asserted this. Twenty strangers have now tested it. **Not one of
the eight abandonments was caused by the way the site looks.**

---

## The full census list

Everything the feature census rated load-bearing, with the reasoning, follows
verbatim from `audit/features/FEATURES.md §5`.

---

## 5. What works and is load-bearing

These are the things a fix pass must not sand off. Each one earns protection for a stated
reason, not because it is nice.

- **The status slot on every card.** Twelve of twelve state stock in plain English —
  `AVAILABLE`, and `2 OF 5 SIZES LEFT` on `V2 BAGGIES`, which tells a shopper the truth *before*
  they click. `NO. 08` carries `DROPPED 03.08` on its own line 3px under `AVAILABLE`, in a
  quieter grey — plainly an addition, never a replacement, never a badge. **Why it is
  load-bearing:** this is the one thing in the register that a conventional shop would replace
  with a scarcity badge, and it is doing the work of one without lying.
- **The chain-of-custody copy, all four steps.** *"Orders placed before 18:00 are dispatched the
  same day, Monday to Saturday"* … *"Free UK shipping over £20, and free Tracked 24 over £70"* …
  *"Tracking issued by email. UK 1–2 working days"* … *"You have 14 days from delivery to return
  unworn goods with tags attached. Return postage is yours unless we sent the wrong thing or it
  arrived faulty."* **Why:** it is the only place on the product page the return window is
  mentioned at all, it names a real courier and a real return route, and it is unhedged. Any
  softening pass would turn the best paragraph on the site into boilerplate.
- **Return-postage honesty, stated four times without a euphemism.** Terms, FAQ, product page and
  refund policy all say the shopper pays return postage unless the fault is the store's. **Why:**
  it is the least flattering fact on the site and it is never hidden. On a brand with no reviews
  this is what "trustworthy" actually looks like.
- **Plain-English buy controls (§9.2).** `£60.00`, `SIZE`, `XS S M L XL`, `IN STOCK`,
  `SELECT A SIZE`, `ADD TO BAG`, `SOLD OUT`, `> Added — 1 in bag  View bag`. Not one word of
  fiction in the part of the page that takes money. **Why:** this is the rule that lets the
  aesthetic survive contact with a stranger, and it holds under pressure everywhere it was tested.
- **The sold-out size behaviour (§9.3).** Dashed border, struck-through label, still tappable by a
  real thumb, red `SIZE M IS SOLD OUT`, button swaps to `SOLD OUT`, notify panel appears, and the
  sticky bar's `CHECKOUT NOW` beside it is greyed and genuinely inert — it reads as dead, not as a
  trap. **Why:** better than most shops manage, and the two problems around it (the dispatch line
  and the clipped button) are faults *on top of* it, not faults in it.
- **The menu drawer's focus trap — tested three times, and it works.** Opening the drawer and
  pressing Tab twenty times cycles sixteen controls (`SHOP ALL NEW TEES DENIM SWEATS TRACKSUITS
  ACCESSORIES TRACKING QUESTIONS TERMS Contact PLAY CASE:001 NOW ACCOUNT BAG CLOSE`) and wraps back
  to `SHOP` on the seventeenth. **Zero presses land outside the panel.** Shift-Tab stays inside,
  and Escape closes it and returns focus to `MENU`.
  **This one nearly became a false finding, so the record matters.** The screen-reader run reported
  the opposite — that Tab pins to `CLOSE` and the fourteen links between are unreachable — and it
  reported it twice. The keyboard persona could not reproduce that across four opens on two pages
  in two sessions, and an independent tiebreaker driving real Tab keypresses confirms the trap
  behaves. **Nobody should "fix" this.** Evidence: `audit/screens/tiebreak-trap.png`, plus
  `15-46`…`15-49`.
  The disagreement is not just adjudicated, it is explained, and both explanations are worth
  keeping because the next audit will hit them too:
  1. **There are two controls named `BAG`** — the header's `BAG [n]` and the drawer's own
     `BAG [0]` in its footer. Shift-Tab off `CLOSE` correctly wraps to the *drawer's* one, which
     by accessible name alone is indistinguishable from having escaped the panel.
  2. **The first-visit overlay pins Tab in a three-control loop** (`RUN IT` → `NOT NOW` → `×`)
     and makes `MENU` unreachable while it is up. That looks exactly like "Tab is stuck on a
     Close button". It wrecked three of the keyboard persona's own runs before they identified
     it, and it is the most likely source of the screen-reader reading.
  **Why:** it is the difference between the drawer being a navigation route and a dead end for a
  keyboard-only shopper, and it is already right.
- **Deep-linkable sizes.** Every size tap writes `?variant=`, and pasting that address into a
  fresh page comes back with the size selected, `IN STOCK`, and `ADD TO BAG` live. **Why:** it is
  what makes a size shareable in a DM, which is how this brand's traffic moves.
- **`SIZE GUIDE`.** One tap, no modal, no PDF; the `MEASUREMENTS` heading lands at the top of the
  screen with the panel already open and the first number 237px below it, on all three products
  tested, animated so the eye is carried down rather than teleported. **Why:** it is the
  best-behaved control on the product page — and it is a *better* route to the table than tapping
  the accordion, which on a first visit opens it underneath the cookie sheet.
- **The cm / inch toggle.** Correct in both directions on every cell checked (`76.2cm` → `30in`,
  `86.4` → `34`, `55.9` → `22`), both button states shown, and the caption's unit word rewrites
  with the table. **Why:** the shopper is never left guessing which unit they are reading — which
  matters more here than usual, because the numbers themselves are under suspicion.
- **The gallery's keyboard and touch handling.** Thumbnails are proper buttons labelled
  `Photo 1 of 3` / `Photo 2 of 3` / `Photo 3 of 3` and are the **first three stops in the tab
  order on the page**; arrow keys walk the focused group and stop cleanly at both ends rather than
  wrapping; a real phone swipe moves it and the active thumbnail follows; targets are 64×64.
  **Why:** the component is markedly better than the pictures inside it, so a photography fix must
  not come with a component rewrite.
- **`PHOTO 1 OF n`.** It tells the truth, including when the truth is `1 OF 1`. **Why:** honest,
  if bleak — and it is the only thing telling a shopper there is nothing more to see.
- **The dispatch line as a live readout, not a countdown.** Correct at 17:38 on a Thursday,
  computed against the shop's own timezone rather than baked into a cached page, so it will not go
  stale at 18:01. **Why:** it is the exact place where a normal shop would put a ticking clock, and
  it doesn't.
- **Low stock stated as a number, not a scare.** `3 LEFT IN SIZE XL`, in the same quiet grey as
  neutral text rather than the red used for sold out. **Why:** real inventory, no escalation —
  §9.7 holding in the hardest place to hold it.
- **The carriage bar's empty-cart gate.** With an empty bag the section does not appear at all, on
  any of its five surfaces. **Why:** it is the reason this feature is defensible. The quarter-screen
  it costs is charged only to shoppers who already have something in the bag, which answers the
  "homepage, empty cart" objection in advance. Do **not** "fix" it by adding an empty state.
- **The carriage bar's GB gate, and thresholds that match the real rate card.** £20 and £70 are
  live rates in the delivery profile, verified. **Why:** it is the one component in the build that
  refuses to make a shipping promise it cannot keep — every other surface makes that promise to
  every country. Also protect the fill being measured against the *top* tier (so the bar keeps
  moving past £20) and held at 99% until a tier is genuinely met, so a shopper never sees a full
  bar next to `£0.01 to go`.
- **`£14.00 to free Tracked 48`.** A real number and a real Royal Mail service, inside the
  fiction, with no countdown and no "only £14 away!!". **Why:** this is §0 holding under commercial
  pressure and it should stay exactly as it is.
- **The carriage bar's live rewrite on the cart.** `£10.00 to free Tracked 24` → `Free Tracked 24
  — unlocked` within a second and a half of pressing `+`, and it matched the real rates at
  checkout. **Why:** the one surface where the message is immediately actionable is the one where
  it actually moves.
- **Filters, counts, and the address bar.** All five categories narrow correctly, the count above
  follows, the choice is written into the address (`?cat=DENIM`), a cold load of that address
  reproduces the filtered view with `> DENIM` already lit, and the whole thing survives opening a
  product and pressing Back. **Why:** a filtered link can be shared and bookmarked, which almost
  no small store gets right.
- **The active-state styling.** A filled purple block with a `>` prompt in front of the word.
  **Why:** nobody will wonder which category is on. No squinting, no faint underline.
- **The whole card is one link.** Picture, title and price all open the product, with 152px-wide
  targets. **Why:** forgiving on a phone, and the price is a target rather than decoration.
- **`Outline` persistence.** Turn it off once and it stays off across collections, product pages
  and Back, for the whole shopping trip. **Why:** whatever is decided about O3, the persistence
  itself is correct behaviour and should survive the decision.
- **One `h1` per collection page**, large, first thing, matching the collection.
- **The empty-search stand-down (§9.8).** A blank query gives a placeholder, a `SEARCH` button,
  the hint, and three real destinations under `DIRECT LINKS`. **Why:** it reads as a landing page
  rather than a failure, and journey 12's shopper — who was braced for a blank grid — said so.
  Do not replace it with a "no results" message or a product grid. (The *failed*-search page
  needing the same three links is a separate fix, §2.7.)
- **The curated direct links themselves.** Twelve question-shaped queries, twelve correct
  destinations, **zero wrong matches**, two taps each. **Why:** this is the feature's entire
  justification and the matching meets it. Every problem in search is about what happens *after*
  the link, not about the matching — so a rework would be throwing away the part that works.
- **The typeahead's two-group order.** `PAGES` above `ITEMS` — answers ranked above garments.
  **Why:** a shopper asking a question sees the answer before the merchandise, which is the
  correct priority and the opposite of what most stores do.
- **Prices in the suggestions.** `V2 BAGGIES £60`, `CHARCOAL CELLBLOCK SHORTS £45`. **Why:** plain
  English money in a fiction-heavy theme, and journey 12's shopper named it unprompted as a reason
  she would come back.
- **The search field itself.** 56px tall, full width, autofocused on arrival so the keyboard is
  already up, visible without scrolling, with a labelled `SEARCH` button and a working Enter key.
  And the header carries the word `SEARCH` written out, next to `CATALOGUE` — not an icon, not
  inside a hamburger. **Why:** journey 12's best moment. One tap saved and four seconds of
  not-thinking, on the device where both are scarce.
- **Fuzzy matching on product names.** `jeens`, `bagies`, `clve tee`, `blue wash og jeens` all
  land on the right garment.
- **The set's cart line.** `CELLBLOCK SET` / `CHARCOAL CELLBLOCK CREWNECK - M` /
  `CHARCOAL CELLBLOCK SHORTS - L` / `£85.00`, one line item, `item_count: 1`. **Why:** the hardest
  part of a bundle to get right, and it is right from both directions — shorts S + crewneck XL
  from the shorts page produced the bundle's `XL / S` with the sizes on the correct garments. Do
  not let a cart redesign flatten those component lines into `M / L`.
- **The partner size row is headed with the partner's name** — `CELLBLOCK SHORTS SIZE`, and
  `CELLBLOCK CREWNECK SIZE` in reverse. **Why:** one decision that removes the commonest bundle
  confusion outright; you are never in doubt whose size you are picking.
- **`£95` struck, `£85 for the set`.** **Why:** the arithmetic is done for the shopper and the
  words "for the set" say what the £85 buys. It is the one screen where the whole proposition is
  stated properly — which is also why its absence from the cart hurts.
- **Untick restores everything** — button, price line, the shopper's own size still selected and
  still pressed, sticky bar, and the underlying selection. **Why:** a shopper can look at the
  offer without committing to it.
- **On the shorts side the button itself becomes the instruction** — `Pick a Cellblock Crewneck
  size`, disabled. **Why:** it is exactly the pattern the crewneck side needs (§2.2), so it is
  both good and the fix.
- **No modal, no popup, no countdown, no "customers also bought" in the set offer.** One quiet
  collapsed line. **Why:** the restraint is the reason the offer is credible at all.
- **The CASE 001 board.** Loaded only on first drawer open, then animating at 61fps — ten
  different frames sampled over four seconds, a thief on a fixed route, a helmeted officer in
  hi-vis, gold `£` coins, brickwork and barred windows. **Why:** the best-crafted thing in the
  build, and its three pause guards (§9.1) never get in a shopper's way. Its problem is
  discoverability, not the board.
- **`PLAY CASE:001 NOW` opening in a new tab.** **Why:** the only reason the game does not strand
  people — the shop tab stays exactly where it was, drawer still open.
- **Escape and focus return.** Escape closes the drawer and puts a clearly visible lavender ring
  back on `MENU`. **Why:** the one dismissal that works reliably, and the focus return is the part
  most rebuilds lose.
- **The bag count's reserved slot and tabular figures.** 0 → 1 → 9 moves nothing by a single pixel.
  **Why:** it was deliberately built and it works; it needs widening by one character, not
  replacing.
- **The text `MENU` trigger instead of a hamburger**, hidden until it is upgraded so it is never a
  dead control.
- **The drawer's link set.** All fourteen destinations resolve, every collection has products in
  it, nothing 404s.
- **`ADD TO BAG` staying on the page.** The count moves `[0]` → `[1]`, a line appears reading
  `> Added — 1 in bag  View bag`, and both revert four seconds later. No drawer, no modal, no
  interception. **Why:** the shopper stays on the product they were deciding about.
- **The cart arithmetic.** £45 + £50 + £60 = `£155.00`, with line totals, `Cart total` and
  `Estimated total` all agreeing, before and after a discount.
- **The discount mechanism.** Apply, a removable `10CROOKS ×` pill, and a
  `Subtotal` / `−£15.50` / `Estimated total` breakdown in the site's own type.
- **Back from checkout returns an intact cart** in one press — three lines, correct total, correct
  count, carriage bar still `Free Tracked 24 — unlocked`. And the cart survives a return in the
  same browser while a genuinely new session correctly starts empty.
- **The bin's accessible name** — `Remove GREY WASH OG JEANS - XS` — names the size as well as the
  product.
- **The FAQ's writing.** Fourteen answers with actual numbers in them — £20, £70, 18:00, 1–2 days,
  7–14 days, 5–7 days, 48 hours, 10 working days. **Why:** it refuses to hide behind "please
  contact us", which on a brand with no reviews is worth more than a reviews widget. Its
  accordions also behave exactly as the spec describes — one open at a time.
- **The Terms page as a whole.** Nine plain-English clauses, a working clause index (tapping
  `03 RETURNS` puts that clause at the top of the screen), a `LAST REVISED 20.08.2026` date, a real
  returns address, a working `#returns` deep link, and links out to all four legal texts.
  **Why:** better than what most stores this size have, and the deep link is what makes the FAQ's
  "full detail is on the terms page" real.
- **`"Drops are for people, not scripts."`** (Terms c8) — flavour in the clause about cancelling
  bot orders, not in the clause about refunds. **Why:** it shows the fiction knows where it is
  allowed to speak.
- **The policy pages carrying the full skin.** Header, status bar, the same display face at the
  same size as the FAQ, the same body type and ground, full footer. **Why:** the seam where most
  themes give the game away is invisible here — a shopper cannot tell these pages are a different
  system.
- **The 404 keeps the header, the footer and four buyable products with prices.** Nobody gets
  stranded; only the look is wrong (§2.20).
- **The tracking page's honesty.** It does not pretend. If the FAQ's promise is removed or the
  page gains a real lookup, keep the plain `IDENTIFICATION REQUIRED` / `Sign in` framing and the
  dispatch-email line — just make that line legible.
- **The packaging section.** `EVERY ORDER SHIPS LIKE THIS`, a real photograph whose yellow
  evidence tents numbered 1, 2, 3 map one-to-one onto the numbered manifest so the list and the
  picture teach each other with no caption, and the line **`Nothing here is an extra you pay
  for.`** **Why:** that single sentence turns three props into three free things you get, and it
  is the only argument-to-buy anywhere on the homepage.
- **The first product at 0.90 screenfuls.** `NO. 01` and `NO. 02` card headers are in the first
  screenful. **Why:** an unusually short run-up for a fashion homepage and the right decision — the
  thing costing the shopper that screen is the three stacked control rows and the cookie sheet, not
  the ordering.
- **The boot line typing.** Readable at ~1.5s, no blank-screen wait, and `> 12 PRODUCTS AVAILABLE
  TO PURCHASE` is a real count.
- **The intake's own copy.** `Drops go to the register before they go public. One message per
  drop, nothing else.` and `One text per drop. Reply STOP to leave the register at any time. We do
  not sell it.` **Why:** more honest than most SMS signups. It deserves a form that works
  underneath it.
- **The status bar's hover pause.** Held for 26 seconds under the pointer — three rotations' worth
  — and resumed within nine of leaving. **Why:** rare, correct, and easy to lose in a refactor.
- **Reduced motion parks on message 1** — the shipping line, not the count. **Why:** that ordering
  is load-bearing: anything placed in slot 2 is permanently invisible to that audience, so the
  useful message must stay first.
- **`[count]` is honest.** 12 in the ticker, 12 in the register, 12 in the hero, `/ 12` in every
  product footer. No inflation, no "17 people viewing".
- **No fake urgency anywhere in the theme (§9.7).** No counters, no timers, no invented scarcity —
  `2 OF 5 SIZES LEFT` and `3 LEFT IN SIZE XL` are real inventory. **Why:** the only surface that
  breaks this is the third-party overlay, which is the exception that proves how consistently the
  theme holds the line.
- **The theme switch.** Instant, no reload, no flash of the wrong theme, and the label states the
  destination rather than the current state.
- **Reload, Back/Forward through five pages, and cold-landing on a product URL** all come back
  clean with the bag count honest at every step; two tabs reconcile exactly on reload, carriage
  line included.

---