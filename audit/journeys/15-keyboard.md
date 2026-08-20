# 15 — Nadia, shops with the keyboard only; a wrist injury put the mouse away two years ago

**Device:** desktop 1440×900, normal connection, no mouse and no touch — Tab, Shift-Tab, Enter, Space, arrows and Escape · **Goal:** buy a pair of the grey jorts · **Mood:** patient, but braced. Most shops make her Tab forty times to find out they don't want her money.

---

### Step 1 — Landed on the homepage and pressed nothing
**Did:** Waited a few seconds to see what the page did on its own before touching a key.
**Got:** The shop loaded. Nothing was focused — no ring anywhere on the screen. Across the bottom, a black panel: `COOKIE CONSENT` / "We and our partners, including Shopify, use cookies and other technologies to personalize your experience, show you ads, and perform analytics, and we will not use cookies or other technologies for these purposes unless you accept them. Learn more in our Privacy Policy", with `Manage preferences`, `Accept` and `Decline`.
**Expected:** Something in the way, and it was.
**Felt:** Fine. At least it's at the bottom and not covering the shop. The type is the same monospace as the rest of the site, which surprised me — most consent bars look bolted on.
**Next:** continued · *Evidence:* `audit/screens/15-01-arrival.png`

### Step 2 — First Tab
**Did:** Pressed Tab once.
**Got:** Focus went straight into the consent panel, onto the `Privacy Policy` link in the body text. A clear blue box round it — I could see exactly where I was.
**Expected:** To land on the buttons, not in the middle of a sentence.
**Felt:** Slightly odd order but I can see it, so I don't care much.
**Next:** continued

### Step 3 — Tab again, and pressed the wrong thing
**Did:** Tab (stop 2 = `Manage preferences`), and pressed Enter, because I don't want the marketing ones.
**Got:** A full dialog opened over the middle of the page: `COOKIE AND PRIVACY PREFERENCES` / `Accept all` `Decline all` `Save my choices` / `YOU CONTROL YOUR DATA` with `Required`, `Personalization`, `Marketing`, `Analytics`. Focus was moved into it, onto a `Close dialog` ×, with a blue ring.
**Expected:** Exactly this, actually.
**Felt:** Good — it took me into the box rather than leaving me stranded behind it.
**Next:** continued · *Evidence:* `audit/screens/15-03-prefs-dialog.png`

### Step 4 — Tried to Tab my way back out and couldn't
**Did:** Kept pressing Tab, thinking I'd come out the other side of the dialog and get to the shop.
**Got:** Seven controls round and round: Accept all → Decline all → Save my choices → three toggles → the × → Accept all again. **Thirty-four presses and I was still in there.** Each one *was* visible — the toggles are 1px things but the ring lands on the drawn box, so you can see the ring.
**Expected:** To eventually loop out to the page. That is not how a modal works, and I know that, but it's what tired fingers try first.
**Felt:** This is the part where I usually give up on a shop. Not the shop's fault yet — it's Shopify's box — but it's my wrists paying for it.
**Next:** hesitated

### Step 5 — Escape, and it worked
**Did:** Pressed Escape.
**Got:** The dialog closed and focus went back to `Manage preferences`, exactly where I'd left it.
**Expected:** Nothing, honestly.
**Felt:** Relief. Escape is my emergency exit and it did its job. **Awkward, not impossible** — but only if you know to press it.
**Next:** continued · *Evidence:* `audit/screens/15-04-prefs-after-escape.png`

### Step 6 — Accepted, to get it off the screen
**Did:** One more Tab (stop 3 = `Accept`), Enter.
**Got:** Banner gone. **And focus went nowhere** — no ring on the page at all.
**Expected:** To be put back near the top of the shop.
**Felt:** Standard. It costs me a Tab or two to find my place again.
**Next:** continued · *Evidence:* `audit/screens/15-02-accept-focused.png`

### Step 7 — The whole shop disappeared behind a game
**Did:** Went to Tab towards the menu.
**Got:** A black sheet over everything: `CROOKSLDN: THE GETAWAY` / "Crack the cuffs. 10% off your first order — code sent by text. Attempts unlimited." / `RUN IT` / `NOT NOW` / "One code per player. Code expires 20 minutes after you win." On a later visit the same panel read "10% off your first order if you do. Three tumblers. **Click each one at the right moment.**"
**Expected:** To be tabbing through the header by now.
**Felt:** "Click each one at the right moment." Right — so the discount isn't for me. That sentence tells me, before I've even tried, that the 10% is for people with a mouse. I never found out whether the game itself can be played on a keyboard; I wasn't going to spend my wrists finding out.
**Next:** hesitated · *Evidence:* `audit/screens/15-44-homepage-after-cookies.png`

### Step 8 — Tabbing while the offer is up goes nowhere
**Did:** Pressed Tab ten times to get past it.
**Got:** Three controls, forever: `RUN IT` → `NOT NOW` → `×` → `RUN IT`. **While that panel is up the entire shop is unreachable by keyboard** — the header, the products, all of it. Ten presses, three destinations.
**Expected:** To be able to tab past an ad.
**Felt:** This is the single worst moment of the trip. It is a correct modal — it holds focus like it should — but it arrives uninvited and it swallows the shop. `NOT NOW` is only two presses away, so it is escapable; it just doesn't feel like it while you're in it.
**Next:** hesitated

### Step 9 — Escape again
**Did:** Escape.
**Got:** Panel gone, and the shop behaved normally from then on. It did not come back this visit.
**Felt:** Two Escapes in the first minute, before I've seen a single garment.
**Next:** continued · *Evidence:* `audit/screens/15-45-after-escape.png`

### Step 10 — Tabbing the header
**Did:** Tab from the top of the page.
**Got:** Seven stops, and from stop 2 onwards every one of them wore a clear 2px lavender box:
a blank white rectangle at the top-left (1) → the handcuffs logo (2) → `CATALOGUE` (3) → `SEARCH` (4) → `BAG [0]` (5) → `LIGHT MODE` (6) → `MENU` (7).
**Expected:** Fifteen stops of social icons and a search box. Got seven.
**Felt:** **This is the best-behaved header I've tabbed through in months.** Short, in a sensible order, and I could see myself the whole way. The logo has no name on it, so stop 2 is a ring round a picture with nothing said about it, but I knew where I was from the position.
**Next:** continued · *Evidence:* `audit/screens/15-07-menu-focused.png`

### Step 11 — Went back to find out what that first white box was
**Did:** Shift-Tabbed back to stop 1 and looked at it properly, then did the same on the product page and the cart.
**Got:** A cream rectangle about 145px wide in the top-left corner **with nothing written in it.** On the cart page it's an empty outlined box instead — same thing, no words. It's the shop's skip link (Enter takes you past the header to the content), but the label is the same colour as the panel it's printed on, so there is nothing to read on any page I visited.
**Expected:** To read the words "Skip to content", which is the entire point of a skip link — it exists to be seen.
**Felt:** This one annoyed me more than it should. The first thing I meet on every page of this shop is a blank white box, and the only way to find out what it does is to press Enter and see where I end up. I'd have said: *"What am I about to activate?"* It isn't fatal — I just tab past it — but it's the one bit of the keyboard experience that's actively unreadable, and it's the very first thing.
**Next:** continued · *Evidence:* `audit/screens/15-50-skip-link-focused-home.png`, `audit/screens/15-52-skip-link-focused-pdp.png` (solid cream, no text), `audit/screens/15-51-skip-link-focused-cart.png` (empty outlined box) — in all three the skip link is the focused element

### Step 12 — Hit the wrong key and repainted the shop
**Did:** Pressed Enter one stop early, on `LIGHT MODE`.
**Got:** The whole site flipped to light. The button became `DARK MODE`. The focus ring went from lavender to a darker purple — still perfectly visible.
**Expected:** The menu.
**Felt:** My fault, and easily undone. Worth knowing that the one control sitting between my bag and my menu repaints the entire shop.
**Next:** went back (Enter again, back to dark)

### Step 13 — Opened MENU
**Did:** Enter on `MENU`.
**Got:** A panel slid in from the right. **Focus moved into it**, onto `CLOSE` at the top of the panel, ringed.
**Expected:** To be left behind the panel hunting for it. That's the usual.
**Felt:** It put me inside. That's the whole game for me and this one got it right.
**Next:** continued · *Evidence:* `audit/screens/15-46-drawer-open-fresh.png`

### Step 14 — Tabbed through the menu
**Did:** Tab twelve times.
**Got:** Twelve different links, in the order they're drawn, all ringed, none of them behind the panel:
`SHOP` `ALL` `NEW` `TEES` `DENIM` `SWEATS` `TRACKSUITS` `ACCESSORIES` `TRACKING` `QUESTIONS` `TERMS` `CONTACT`. Keep going and you get `PLAY CASE:001 NOW`, `ACCOUNT`, `BAG [0]`, `CLOSE`, and then it comes round to `SHOP` again — **16 controls, cycling, and not one press escaped to the page behind.**
**Expected:** To fall out into the page and have to fight my way back.
**Felt:** Genuinely good. I could read the menu with my hands.
**Next:** continued · *Evidence:* `audit/screens/15-48-after-12-tabs.png`

### Step 15 — Went backwards from the top of the menu
**Did:** Shift-Tab straight off `CLOSE`.
**Got:** `BAG [0]` — **the menu's own bag link, down in the panel's footer**, then `ACCOUNT` above it. Still inside. The panel stayed open.
**Expected:** To be spat out into the header.
**Felt:** It wrapped round to the bottom of the menu, which is right. Worth saying out loud: the menu has its *own* `ACCOUNT` and `BAG [0]` at the bottom, and the header has a `BAG [n]` too. Going backwards off CLOSE lands you on a thing called "BAG" that is *not* the header's — same name, different place.
**Next:** continued · *Evidence:* `audit/screens/15-47-after-two-shift-tabs.png`

### Step 16 — Escaped out of the menu
**Did:** Escape.
**Got:** Panel closed, and focus was **put back on the `MENU` button** with its ring on.
**Expected:** To be dumped at the top of the document and have to tab the header again.
**Felt:** Correct, and rare. Whoever built this menu has done this before.
**Next:** continued · *Evidence:* `audit/screens/15-49-escape-returns-focus.png`

### Step 17 — Menu → denim
**Did:** Enter on MENU again, Tab five times to `DENIM`, Enter.
**Got:** `/collections/denim`, `DENIM` / `4 ITEMS`. Focus dropped to nothing on the new page, as it does everywhere.
**Felt:** Six presses from a closed menu to a category. Fine.
**Next:** continued · *Evidence:* `audit/screens/15-10-denim-focused.png`, `audit/screens/15-11-denim-collection.png`

### Step 18 — Collection to a product
**Did:** Tab down the collection page.
**Got:** Seven header stops, then `FLAT` (8) and `ON MODEL` (9) — the picture toggles — then the first product at stop 10: one ring round the whole card, reading `NO. 01 DENIM GREY WASH JORTS £50.00 AVAILABLE`. Enter took me to it.
**Expected:** Each card to be three or four stops — image, title, price. It's one. Good.
**Felt:** Ten presses to the first item is fair. And the card is one ring, not four — that's twelve products I can skim instead of forty-eight stops I have to sit through.
**Next:** continued · *Evidence:* `audit/screens/15-12-product-card-focused.png`

### Step 19 — The size row
**Did:** Tabbed down the product page counting.
**Got:** Ten stops to the first size: header (7), `← CATALOGUE` (8), the photographs as **one** stop announced `Evidence photographs` (9), then `XS` (10). Every size is its own stop — `XS S M L XL` — each with a lavender ring. Then I tried the arrow keys on a hunch: **ArrowRight moved me along the row without selecting anything.** Space selected the one I was on, and did not scroll the page.
**Expected:** To have to Tab five times and pray Space didn't scroll me to the footer.
**Felt:** Both idioms work — arrows to browse, Space or Enter to pick. That's the mark of somebody who tested it. And the gallery being one stop instead of six saved me real effort.
**Next:** continued · *Evidence:* `audit/screens/15-14-size-focused.png`, `audit/screens/15-21-space-selects-xs.png`

### Step 20 — Picked L
**Did:** Tab to `L`, Enter.
**Got:** `L` filled in purple with a light border; the other four stayed hollow. The line under the row changed from `SELECT A SIZE` to `IN STOCK`, and the buy button changed from `SELECT A SIZE` to `ADD TO BAG`.
**Expected:** To have to guess what I'd selected.
**Felt:** I can tell selected from focused at a glance — one is filled, the other is a ring round the outside. That distinction is the thing most shops get wrong and this one doesn't.
**Next:** continued · *Evidence:* `audit/screens/15-15-size-chosen.png`

### Step 21 — Added to bag
**Did:** Three more Tabs — `XL`, `SIZE GUIDE`, `ADD TO BAG` — and Enter.
**Got:** `BAG [0]` became `BAG [1]` up in the header, and a small line appeared under the buttons: `> Added — 1 in bag  View bag`. **And my focus was gone** — no ring anywhere on the page.
**Expected:** To be left on the button I'd just pressed.
**Felt:** The confirmation is real, it's in plain English, and it's *small* — one line of purple text under a big blue Shop Pay button. The worse bit is losing my place: the ring vanished and for a second I didn't know if the press had registered. The bag counter is what told me, not the message.
**Next:** continued · *Evidence:* `audit/screens/15-16-add-focused.png`, `audit/screens/15-17-after-add.png`

### Step 22 — Found the way to the cart
**Did:** Pressed Tab to see where I'd been left.
**Got:** It picked up from where I was: `Buy with Shop` (1), `More payment options` (2), `View bag` (3) — ringed and underlined. Enter took me to `/cart`.
**Expected:** To have to Shift-Tab all the way back up to the header bag. (That way round is 12 presses; forwards it's 3.)
**Felt:** Better than I feared. The confirmation link is right in the path, which is the correct place for it.
**Next:** continued · *Evidence:* `audit/screens/15-23-forward-from-add.png`

### Step 23 — The cart, and where I stopped
**Did:** Tabbed the cart page to the checkout button.
**Got:** Fifteen stops: the seven header ones, the product thumbnail (8) and its title (9) — two stops for the same jorts — `Quantity` (10), `Increase quantity` (11), `Remove` (12), `Discount` (13), the Shop Pay `?` (14), and `Check out` at 15. Above it all: `£20.00 to free Tracked 24`, `TRACKED 48 FREE`, `TRACKED 24 FREE`.
**Expected:** Worse.
**Felt:** Two things. The wording drops out of the shop's voice here — `Check out`, `Decrease quantity`, `You may also like` in ordinary sentence case, after a whole site of `ADD TO BAG` and `IN STOCK`. And the ring on the last two things that matter — `Remove` and `Check out` — goes from lavender to a **much darker purple**. It's there, I can see it, but they're the dimmest rings on the whole journey and they're on the two buttons where being sure matters most.
**Next:** stopped here — no order placed · *Evidence:* `audit/screens/15-24-cart.png`, `audit/screens/15-25-checkout-focused.png`

---

## Outcome

**Bought / didn't:** Got to a filled cart with `Check out` under my finger and stopped there deliberately. Nothing on the route from the homepage to the cart was impossible by keyboard — which, for me, is a pass most shops don't get.

**Total time:** About four minutes end to end. Counted out: **48 key presses from landing to a full bag** (4 for the cookie banner, 1 Escape for the game, 8 to open the menu, 6 to a category, 11 to a product, 14 to the size, 4 to `ADD TO BAG`), **4 more** to reach the cart, **15 more** to reach `Check out`. Five of the first thirteen presses were spent on things that weren't the shop.

**Worst moment:** The `CROOKSLDN: THE GETAWAY` sheet. It arrives on its own, it takes the whole screen, and while it's up Tab does nothing but cycle `RUN IT` → `NOT NOW` → `×` for as long as you press it. I'd have said out loud: *"I haven't seen a single item yet and I'm already trapped in an advert."* And the offer's own instruction — *"Click each one at the right moment"* — tells me the 10% isn't available to me before I've tried. **(Untested: whether the game itself can be played by keyboard. I read the word "click" and pressed NOT NOW.)**

**Best moment:** The MENU panel. Focus went into it, sixteen controls cycled inside it, Shift-Tab wrapped round to the bottom instead of falling out, Escape closed it and **put me back on the MENU button**. Then the size row, where the arrow keys moved me along without selecting and the selected size is filled while the focused one is ringed. Both of those are things people build wrong constantly.

**Would they come back?** Yes. Once the two pop-ups are behind you the shop itself is one of the better keyboard experiences I've had this year — a seven-stop header, a product card that's one stop instead of four, a gallery that's one stop instead of six, plain-English buy controls, and a ring I can see on essentially everything except the very first box.

**One thing that would have changed the outcome:** Don't let the discount pop-up take the screen before I've seen a product — or at minimum, make its offer claimable without a mouse. Everything else on the route I could do; that one thing is the only place the shop actively told me it wasn't built for me.

**Nothing on the route was impossible.** For the record, because the difference matters: home → menu → product → size → bag → cart is completable by keyboard end to end, and I did it. What was *awkward* — recoverable, but it cost me: the consent dialog you can only leave by Escape or by finding its × (34 Tabs got me nowhere); the game overlay that owns the whole screen until Escape or `NOT NOW`; focus being dropped to nothing after the cookie banner, after `ADD TO BAG`, and on every page load; and the two dimmest rings on the site sitting on `Remove` and `Check out`. What is *unreadable*: the skip link on every page. What is genuinely **out of reach**: the 10% discount, by the offer's own instruction to click. I never established whether the game behind it can be played on a keyboard — that is the one thing I could not test and somebody should.

---

## Note on the drawer focus trap — tested, not assumed

I was asked to test rather than confirm this, because the screen-reader persona reports that Tab pins to `CLOSE`, that Shift-Tab jumps out to BAG, and that the 14 links between are unreachable. **I could not reproduce that.** Four separate opens, two pages, two sessions:

| Run | Page | What happened |
|---|---|---|
| clean run, homepage | `/` | Focus in → `CLOSE`. Tab ×22 → SHOP, ALL, NEW, TEES, DENIM, SWEATS, TRACKSUITS, ACCESSORIES, TRACKING, QUESTIONS, TERMS, CONTACT, PLAY CASE:001 NOW, ACCOUNT, BAG [0], CLOSE, then round to SHOP. **0 presses left the panel.** |
| same run, reopened | `/` | Tab ×5 → `DENIM`, Enter → landed on `/collections/denim`. |
| product page | `/products/cb2-wash-jorts` | Focus in → `CLOSE`. Tab ×8 → 8 distinct links. Tab ×6 → `SWEATS`, Enter → landed on `/collections/sweats`. |
| second session, homepage | `/` | Tab ×12 from a fresh open → **12 distinct links, 0 escapes.** Shift-Tab off `CLOSE` → `BAG [0]` then `ACCOUNT`, both still inside. Escape → focus back on `MENU`. |

I used the drawer as a real navigation route twice and it worked both times, so for a keyboard-only shopper it is **not** a dead end.

Two things might explain the disagreement, and both are worth checking before anyone changes code:

1. **There are two links called "BAG".** The panel has its own `ACCOUNT` and `BAG [0]` in its footer (at 1115,840 on a 1440×900 screen) as well as the header's `BAG [n]` (at 1031,36). Shift-Tab off `CLOSE` correctly wraps to the **panel's** BAG. By name alone that is indistinguishable from escaping to the header's.
2. **The `CROOKSLDN: THE GETAWAY` overlay pins Tab in a three-control loop** — `RUN IT` → `NOT NOW` → `×` (aria-label `Close`, and on other visits `Close Crack the Cuffs`). While it is up, `MENU` cannot be reached at all: I hit this four times and each time it looked exactly like "Tab is stuck on a Close button." Three of my own runs were wrecked by it before I worked out what it was. If the screen-reader run met that overlay, it would read as a drawer that pins to CLOSE.

If both runs are sound, the disagreement is real and worth a third opinion. My evidence says the trap behaves: `audit/screens/15-46-drawer-open-fresh.png`, `15-47-after-two-shift-tabs.png`, `15-48-after-12-tabs.png`, `15-49-escape-returns-focus.png`, `15-34-drawer-pdp-tabbed.png`, `15-35-drawer-link-used.png`.
