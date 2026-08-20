# SUMMARY — twenty shoppers, what they did, and what happened more than once

Twenty journeys, twenty personas, one staging store. This file reports the five worst
moments and every pattern that turned up in three or more journeys. Nothing here is new
evidence — every quote and every screenshot is lifted from the file it came from, so any
line can be traced back and argued with.

Read the counts as counts. Twenty is a small number of shoppers and the store was being
edited underneath several of them (`RUN-NOTES.md`), so a pattern in three journeys is a
signal to go and look, not a measurement.

---

## 1. Outcomes at a glance

| # | Persona | Device | Bought? | The one-line reason |
|---|---|---|---|---|
| 01 | Cold click out of an Instagram story | phone | **No** | One flat photo of the back of a £60 jean he'd just watched someone wear |
| 02 | Burned by a small label before | phone | **Yes** | Nothing on the site stopped him; he'd have paid by PayPal, not card |
| 03 | Between a 32 and a 34 | phone | **No** | The measurements turned out to be a generic chart, printed on the joggers too |
| 04 | Wants the crewneck, meets the set offer | phone | **Yes** | £85 set — but only because he refused to believe a false sold-out |
| 05 | Won't buy a bundle until he's done the sums | laptop | **Yes** | Checked the £85 and it held; bought at £76.50 with a public code |
| 06 | Came for the V2 BAGGIES in M | phone | **No** | M sold out, and the notify button never once said a word back |
| 07 | In and out for £6 socks | phone | **Yes** | Would have paid £9 grudgingly; £3 postage appeared at the last screen |
| 08 | Building a whole fit | phone | **Yes** | £91, money right on every screen; lost time re-buying a tee to change one letter |
| 09 | Buying her brother a present | laptop | **No** | No gift card, no gift note, and garment measurements can't size an absent person |
| 10 | Stuck between the grey and the blue | laptop | **Yes** | Bought the blue: the only one of the two she'd seen on a body |
| 11 | Presses every switch before deciding | laptop | **Yes** | Crewneck yes; trousers no, because two garments share one measurement table |
| 12 | Wants the returns policy before her card | phone | **No** | Four search words and a third-party site to read it, then 14 days vs 30 days |
| 13 | Phone sideways on the sofa | phone, landscape | **No** | Cart line item collapsed: photo printed over the words, `+` touching the bin |
| 14 | One bar of signal, off a TikTok | phone, congested | **No** | Two full-screen blockers and a buy button that changed under his thumb |
| 15 | Keyboard only, no mouse | laptop, keys only | **Yes** | Home to filled cart end to end; only the discount was out of reach |
| 16 | Blind, shops with a screen reader | laptop, reader | **Yes** | "On any normal day this is a purchase"; only the menu and the add-confirmation fought him |
| 17 | Browses everything at 200% | laptop, 200% | **Yes** | Shopped end to end; could not read her own bag page |
| 18 | Reduce-motion on at the phone level | phone | **No** | Tee in the bag; left over the 10% she physically cannot win |
| 19 | Laptop, coffee, no hurry | laptop | **Yes** | £65 and would have gone through; twice as long as he'd normally give a shop |
| 20 | Paid four days ago, wants his parcel | phone | *n/a* | Already a customer; could neither track the order nor start a return |

**Eleven** reached a filled cart or the payment step with nothing left standing in the way —
02, 04, 05, 07, 08, 10, 11, 15, 16, 17, 19. Per the brief, no order was ever submitted.

**Eight** abandoned. Where:

- **Three on the product page** — 01 (bag filled, then left), 03 (thumb over `ADD TO BAG`,
  never pressed), 06 (stranded at the notify form).
- **Three at the cart** — 13 (couldn't read the line item), 14 (goodwill gone by the time
  the bag loaded), 18 (tee in the bag, left over the unreachable discount).
- **One at the payment page** — 09.
- **One before reaching a product at all** — 12, still hunting for the returns policy.

**One was already a customer** and the site could do nothing for him — 20.

Worth holding next to that: of the eight who left, **six say they would come back**, and
four name the clothes or the look as the reason. Nobody abandoned because the shop is
austere. They abandoned on numbers, photographs and buttons.

---

## 2. The five worst moments

Ranked by what they cost, not by how bad they look.

### 1. He reads `50.8cm` on the joggers, ninety seconds after reading `50.8cm` on the jeans

**03 — size-anxious, phone.** He had already decided to buy. He opened `V2 BAGGIES` to
sanity-check the jeans' table against another garment and found the same fifteen numbers,
to the millimetre, in both units — on a 500gsm sweatpant the shop calls *wide, full-length*
and a 14oz denim it calls *structured, not baggy*.

> *"they've put the same chart on the joggers — so which one is the tape measure from?"*

`audit/screens/03-30-baggies-says-vs-numbers.png`

**Cost:** the £60 sale, and every other table on the site with it. His own words: it doesn't
dent confidence, it removes it — after that he has to assume any table might belong to a
different garment, including the ones that look plausible. Four more shoppers reached the
same conclusion independently (06, 09, 10, 11). It also spoils the two best-built controls
on the site, because `SIZE GUIDE` and the `CM`/`IN` toggle are a very fast route to it.

### 2. He is told the shorts are sold out in four sizes running, while they sit in stock

**04 — set buyer, phone.** He ticked the set box before choosing his own size, obeyed the
panel's own instruction — `Pick a Cellblock Shorts size` — and got a red line for M, then L,
then XL, then S. He had seen `CHARCOAL CELLBLOCK SHORTS £45.00 AVAILABLE` on the catalogue
ninety seconds earlier.

> *"they're not, though — I literally just saw them."*

`audit/screens/04-08-shorts-M.png`, `audit/screens/04-22-false-soldout-viewport.png`

**Cost:** £35 every time a shopper opens the offer before picking their own size, which is
the natural order for anyone the offer actually catches. He recovered it only by going to the
shorts' own page to call the shop's bluff — *"In real life I would not have done this step."*
And the sentence he'd pass to a friend is the one no shop wants passed around: *"pick your
size first or it'll tell you it's sold out."*

### 3. He presses `NOTIFY ME` four times and the shop never says one word back

**06 — sold out, phone.** M was gone and he was willing to wait. Twice he got a blank white
rectangle over a greyed page for about ten seconds, no text on it, then nothing. Twice he got
no reaction at all. His address stayed sitting in the field throughout. A deliberately
mistyped address was swallowed exactly as silently as the good one.

> *"Did that do anything?"* — and, on the way out, *"they've got a button for telling you when
> it's back and pressing it does nothing."*

`audit/screens/06-11-after-submit-1-11s.png`, `audit/screens/06-31-fourth-attempt.png`

**Cost:** £60 leaves and there is no route back in — and the shop never learns there was
demand for an M. The `QUESTIONS` page has fourteen entries and not one about restocks, so the
form is the only channel that exists for the question.

*Qualification, and it matters:* `raw-notify-verify.md` establishes that the blank panel is a
bot check refusing an automated browser — the identical panel appears on the store's own stock
contact form — so this **must not** be written up as a dead feature. What is confirmed and
shopper-facing is everything around it: no message when the check does not complete, no
statement of when a shopper would hear back, and no way to tell success from silent failure.
One send from a real phone settles the rest.

### 4. He opens the tracking page and finds nothing to type into

**20 — post-purchase, phone.** Four days after paying £60. Two taps to `/pages/tracking`, and
the page's only tappable thing is `SIGN IN`. The FAQ had told him twice — once on a link that
took him straight there — *"You can also look your order up on the tracking page — no account
needed"* and *"You can check out as a guest and still track your order."*

> *"There's nothing to look it up **with**."*

`audit/screens/20-05-tracking.png`, `audit/screens/20-07b-faq-tracking-answer.png`

**Cost:** a customer who has already paid cannot see his own order on this website at all, and
was told in writing, twice, that he could. The page's largest words are a refusal
(`IDENTIFICATION REQUIRED`) and its smallest words — 9px — are the only useful sentence on it.
His real next step is an email to a gmail address and a stated wait of 1–2 working days about a
parcel that is already four days out.

### 5. He opens the cart and the photograph is printed over the words

**13 — phone held sideways.** Right item, right size, one tap from paying. The line item drew
the picture on top of the text: the title reading with its first letter behind the photo, the
size and colour line showing as `ACK`, the price showing as `00`, and the `+` control
overlapping the delete bin by about twenty pixels.

> *"That's just broken."*

`audit/screens/13-31-cart-line-close.png`

The 200% shopper hit the same collapse — the photo sitting on the name so it reads `CHARCOAL`,
`LLBLOCK`, `ECK`, with `Size: M` and the line price completely underneath it, and `+` overlapping
the bin by 40px. `audit/screens/17-15c-cart-line.png`

> *"Well, what have I actually bought?"*

**Cost:** the only outright abandonment that happened at the final step with everything else
right. Both shoppers noticed that the page whose entire job is confirmation is the one page
they could not read — and the fix is on the site already: the checkout page shows the same
photograph *beside* the name, the size and the price, perfectly legibly.

*Just outside:* following the cart's own `save £10.` link and landing on `Cart total £95.00 GBP`
(05); reaching for `CATALOGUE` and hitting the words `COOKIE CONSENT` (14); four attempts to
find a human (02); the spinning tumblers (18).

---

## 3. What appeared in three or more journeys

This is the part no single journey contains. Each pattern below was counted against the files;
the tally is named so it can be re-counted.

### The size numbers are a chart, not a garment — 5 journeys

**03 · 06 · 09 · 10 · 11.** Three separate shoppers found two different garments carrying
identical tables; two more spotted the giveaway without comparing anything.

> 03: *"In inches the jeans are 30 / 32 / 34 / 36 / 38 in the waist and 18 / 19 / 20 / 21 / 22 at
> the leg opening. Fifteen cells, every one a whole inch."*
> 11: *"A baggy sweatpant and a pair of jeans do not have the same waist, inseam and leg opening
> across all five sizes. That's the one thing here that would actually stop me buying the trousers."*
> 09: *"The centimetres are all things like 76.2 and 86.4, which are just inches converted."*

Two shoppers also caught the shop stating two incompatible methods: the product page says
measurements are `TAKEN AROUND THE GARMENT`, `QUESTIONS` says *"Everything is measured with the
garment laid flat"* (03, 09). Those readings are a factor of two apart. Read as *around*, the M
is a 34in waist; read as *laid flat*, the XS is a 152cm waist and the correct move is to buy the
smallest thing in the shop.

**Cost:** two abandoned sales outright (03, and 11's trousers), one shopper who says she'd have
had a fifty-fifty chance of ordering something twice the right size (09), and — because the
return postage is the shopper's, stated plainly — the price of guessing wrong is theirs too.

### `SELECT A SIZE` when size is not what's missing — 6 journeys

**07 · 08 · 11 · 13 · 18 · 19.** Two shapes, one button. On the socks there is no size at all:
the heading says `QUANTITY`, the boxes say `1pc / 3pc / 6pc / 12pc`, the grey line says
`Select Quantity`, and the two largest controls on the screen say `SELECT A SIZE`. On the tee, a
shopper who has picked a size and not a colour is told to pick a size.

> 07: *"Size? They're socks. Where's the size?"* — he scrolled back up the page hunting for a row
> that doesn't exist.
> 13: *"I'd just tapped M and watched it go purple, and the biggest thing on the screen was telling
> me I hadn't."*
> 08: *"The small grey line knows what's actually missing; the two big buttons don't, and the big
> buttons are the ones you read."*

**Cost:** nobody abandoned over it, and that is exactly why it is dangerous — it costs seconds and
a flicker of "is this site broken" at the point of purchase, six times out of twenty. The landscape
version is the expensive one: sideways, the size row and the button cannot be on screen together,
so he scrolled back up to check he'd really pressed M. The plain-English buy controls are this
build's best asset (see §4); this is the one place the plain English is plainly wrong.

### The consent panel lands on what the thumb was already moving towards — 7 journeys

**01 · 07 · 09 · 13 · 14 · 17 · 20.** It arrives a beat *after* the page, which is what makes it
a trap rather than a nuisance.

> 14: *"I pressed the button, why am I reading about analytics."* The purple `CATALOGUE` button was
> readable at about two seconds; the panel landed on it at about five.
> 01: it covered the product's name, the `£60.00`, the whole size row and the buy bar at once —
> *"Three of the five things I came to find out were behind a grey panel written by Shopify."*
> 13, sideways: *"It isn't a banner at this angle, it's a lid."*

The 200% version costs something different and worse: the panel takes almost the whole window and
`Decline` is the one button whose edge runs off the right-hand side, while `Accept` sits comfortably
inside it. *"I accepted tracking I didn't want because the decline button looked broken."*
(`audit/screens/17-01-arrive.png`)

**Cost:** the first sentence of English the brand ever shows a stranger is written in someone else's
voice and names Shopify twice, and on a phone it lands on the price and the buy controls. It costs
no sale on its own — every shopper cleared it — but it is the first impression for every mobile
arrival. The three laptop shoppers who met it as a bottom strip (10, 15, 19) all said it cost them
nothing, so this is a phone-and-zoom problem, not a consent problem.

### The first-visit overlay arrives before a garment has been seen — 10 journeys, and not to everyone

**07 · 08 · 09 · 11 · 13 · 14 · 15 · 17 · 18 · 19 saw it. 02, 10 and 16 sat and waited and it never came.**

> 14: *"Oh, come on."* Two full-screen interruptions back to back, still no clothes.
> 15, keyboard only: *"I haven't seen a single item yet and I'm already trapped in an advert."*
> Ten Tab presses, three destinations — `RUN IT` → `NOT NOW` → `×`.
> 09: *"I'm at work, I'm buying a birthday present, and it wants me to play a minigame with a
> twenty-minute timer."*

07 counted it: five taps from landing to a live checkout, and **two of the five were spent closing
things he never asked for**. 11 had a click swallowed by it mid-press. 19 watched it repaint into
a *different* version of the same offer while he read — one promising the code by text, one not; one
clock starting when you win, one already running — *"Hang on — is the code a text or isn't it? And
which twenty minutes are we talking about?"* 18 took the offer and met three continuously spinning,
motion-blurred reels: *"I can't look at that."* 15 read *"Click each one at the right moment"* and
knew the discount wasn't for her before she'd tried.

**Cost:** the only 10% this shop offers is, in practice, gated behind a game that a keyboard shopper
is told she can't play and a reduced-motion shopper physically cannot watch — and 18 left the tee in
the bag partly over that £2.50. Two further points the council should hold: the overlay carries
`Code expires in 20 minutes` and `(this drop closes 15.09)`, which is a countdown on the store's own
rejected list, arriving before any product; and **it does not fire consistently**, so the site's worst
first impression is one nobody can reliably reproduce.

### A control that acknowledges the press and does nothing — 6 journeys

**02 · 04 · 06 · 10 · 11 · 19.**

> 02, tapping the word `CONTACT` in the footer: *"Is this thing broken or am I?"* It is a heading,
> not a link. He tapped it twice more to check it wasn't his thumb.
> 10, on `ON MODEL`: *"It's a button that highlights itself and does nothing else — and it's the one
> control on the page that promises the thing I came for."*
> 11, on `OUTLINE` in light mode: *"Pressing a control and getting a confirmed nothing is worse than
> not having the control."*

Also in the set: the shorts thumbnail inside the set offer is a picture, not a link (04); the greyed
`CHECKOUT NOW` beside `SOLD OUT` (06); the main product photograph, which neither zooms nor opens on
a laptop (19); and the early `ADD TO BAG` on a slow connection, which produces no item, no message and
no error (14).

**Cost:** 11 names it exactly — *"it teaches the shopper that the toggles on this site are
decorative."* For a store whose whole proposition is that it is not a generic shop, its controls have
to be **more** trustworthy than a normal shop's, not less.

### The site tells the shopper two things and leaves them to pick — 8 journeys

**03 · 04 · 05 · 06 · 09 · 12 · 19 · 20.** This is the single most common fault in the set and it
appears in a different place each time.

> 12: *"I have now been told 14 days by this shop's own policy and 30 days by the page this shop's own
> search sent me to first. Both can't be right."*
> 05: the cart's own line says `Complete the set — add the Cellblock Shorts, save £10.`; following it
> and doing what the next page asks produces `Cart total £95.00 GBP` — *"I've just paid ten quid extra
> for taking their advice."*
> 09: `DIRECT LINKS — SIZE GUIDE` and `0 RESULTS / NO ITEMS IN THE REGISTER MATCH THAT QUERY.` on the
> same screen. *"I know which one I believed for about two seconds — the big heading that says zero."*

The full list found: 14 days (shop) vs 30 days (returns portal), and 48 hours vs 7 days vs 14 days on
faults (12, 20); "final sale" vs "discounted items" on what can't be returned (20); the FAQ's *"no
account needed"* against `IDENTIFICATION REQUIRED` (20); `£50.00` at the top of the page while the
button says `ADD THE FULL FIT — £85` (04, 05); `Save £10.` against a public code that takes the set to
£76.50 (05); "Structured, not baggy" against a 20in leg opening (03, 10); same-day dispatch at the top
of a screen that says `SOLD OUT` at the bottom (06); the description opening *"V2 Baggies — wide,
full-length sweats"* on a product renamed mid-run.

**Cost:** two shoppers changed what they'd do (12 stopped buying; 05 would tell a friend the price on
the page isn't the price), and every one of them lost the specific thing this shop has otherwise
earned — the belief that when it says a number, that's the number.

### No photograph of a garment on a person that a phone shopper can reach — 6 journeys

**01 · 02 · 03 · 10 · 11 · 19.** Several products carry exactly one photograph and it is the back of
the garment, flat, on black.

> 01, arriving from a video of somebody wearing them: *"£60 is not a lot of money but it is enough that
> I want to see the thing on a human, and there is nothing here. `PHOTO 1 OF 1` is honest, and it is
> also the page telling me it has nothing else to show me."*
> 10, choosing between two £60 jeans: *"I picked blue because it's the one I've seen on a person — not
> because I decided the blue was better. The photograph made the decision."*
> 19: *"There's a real model photograph of the jeans and it only exists if your mouse happens to drift
> over the right square. I found it by accident."*

The twist is that some of the pictures exist. 19 found second photographs on four of twelve cards by
sliding a cursor across them; a phone has no equivalent. The button labelled for exactly this job did
three different things for three laptop shoppers (see §5).

**Cost:** the single named reason journey 01 didn't buy, and the sole basis on which journey 10 chose
between two products. 02 files it as the one question this site cannot answer at all: *"a table
can't tell me the fit is right, and there is not one photograph of a human being wearing these anywhere
on the site."* This is not a theme change and it does not require a badge or stock photography —
it requires one more frame of a garment being worn, of the kind the shorts and the blue jeans already have.

### The answer exists, is well written, and is filed where the shopper isn't — 7 journeys

**01 · 02 · 03 · 07 · 09 · 12 · 20.**

> 01: *"UK 1–2 working days"* — *"the one sentence I have been looking for the whole time is the third
> of four blocks inside the fourth of four strips, all of which are shut when you land."*
> 02, on `/policies/contact-information`: *"The single best sentence anyone has written for a customer
> like me is on a page a customer like me cannot reach."*
> 09, on the packaging block: *"That paragraph is doing more gift-buyer work than the rest of the site
> combined, and nobody has noticed, because it's sitting on the homepage instead of anywhere near the bag."*

Same shape elsewhere: the exchange terms — *"there is no fee for the swap itself, and we cover the
postage sending the new size out to you"* — live on the FAQ and never appear on the product page where
the size decision is actually made (03); the free-carriage bar lives on store pages only, so the fastest
buying route never loads one (07); `returns` in the search box produces a third-party order-number wall
while `refund` produces the shop's own excellent policy page (12); and the tracking page's only helpful
sentence is its smallest text (20).

**Cost:** journey 02 took nineteen minutes to find a contact detail that could have sat in the footer;
journey 12 took four different search words and a trip to another company's website. Both of them then
rated the writing they eventually found as the best thing on the site. That is the shape of this fault
— it isn't missing content, it's shelving.

### The shop stops being itself at the moments that decide the sale — 9 journeys

**02 · 07 · 08 · 09 · 12 · 13 · 15 · 19 · 20.**

> 08: *"everything the last ten minutes built — the black, the mono, the evidence-log thing — is gone at
> the door, and it goes from 'small London label with a strong idea' to 'a Shopify store' in one tap."*
> 09, on the bag page: *"It's like walking through a very carefully done door into a Travelodge lobby."*
> 15, keyboard: *"The wording drops out of the shop's voice here — `Check out`, `Decrease quantity`,
> `You may also like` in ordinary sentence case, after a whole site of `ADD TO BAG` and `IN STOCK`."*

Three grades of cost, and they are not equal:

- **The checkout itself: leave it.** Every shopper who reached it said the change was jarring and none
  of them lost trust — 02 read the own-domain checkout and the express row as the moment the
  reviews question stopped mattering. 07 checked the name at the top for half a second and carried on.
- **The cart, in the shop's own house: fixable and worth fixing.** `Cart`, `Check out`, `Estimated total`,
  `You may also like` sit one tap from `PRODUCT 07 / 12`. Nine shoppers noticed the seam and it starts here.
- **The two third-party destinations: expensive.** The returns portal and the contact form both read as
  a different company. 12 and 20 both said the handcuffs logo was the only reason they believed they
  hadn't been handed off, and 02 nearly closed the tab on the contact page — *"who am I even emailing?"*

**Cost:** nobody stopped buying over the checkout. Two stopped over the destinations that look like
somebody else's website while asking for their money or their order number.

### Checked against the files and *not* reaching three

Named because they were on the candidate list and the council will look for them:

- **Postage price only discoverable at checkout — one journey (07).** He typed six fields before
  meeting `£3.00` on a £6 order. The mechanism he identifies is real and general — the product-page
  accordion says *"Free UK shipping over £20, and free Tracked 24 over £70"*, which tells a shopper what
  is free and never what it costs if it isn't — but 02 and 12 both found the shipping policy with
  `standard £3, Tracked 24 £4.99` on it in one tap, and nobody else raised it. One journey.
- **The header bag count disagreeing with the cart — two journeys (08, 16).** Real, reproducible and
  reported by two independent personas including the screen-reader run. 08 tabulated it: right after
  every add, wrong after every remove, never self-correcting — *"Did that actually delete? It still says
  three."* 16 met it after a quantity change: `BAG [1]` against a cart of 2 and `Estimated total
  £120.00 GBP`. Two, not three.
- **The contact route failing — two journeys (02, 03),** and it is the worst moment of one of them.
  The footer's `CONTACT` is a dead heading; `MENU → CONTACT` reaches a cream form with no address, no
  name and no reply time; the page that carries *"Real people read every message, usually the same ones
  packing your order"* is linked from nowhere. 03 went there because the FAQ told him to — *"message
  us and we will measure it for you"* — and found nothing acknowledging that offer. Two, not three, but
  do not read the count as a measure of severity.

---

## 4. What worked in three or more journeys

More journeys praised these than complained about anything, and several of them are load-bearing —
remove one and a fault above becomes a lost sale instead of an irritation.

### The add-to-bag confirmation that does not take the screen — 10 journeys

**01 · 04 · 08 · 09 · 10 · 13 · 14 · 17 · 18 · 19.** A line under the button reading `> Added — 1 in
bag  View bag`, a header counter, and nothing thrown over the page.

> 13, sideways on a screen 390 tall: *"Best moment of the journey... On a screen this short, a cart
> drawer would have been a disaster and they didn't build one."*
> 01: *"Quiet, and I liked it. Nothing covered the screen... two things agreeing is more convincing than
> a big animation."*
> 18, reduced motion: *"Three separate written confirmations, all of them still true a minute later...
> Nothing here was carried by an animation, so nothing was lost when the animation didn't happen."*

**Protect it.** It is the reason three of the hardest journeys in the set (13, 14, 18) have a best moment
at all. 14, on one bar of signal, got it inside a second, in the bottom bar where his thumb already was.

### Plain English exactly where money is involved — 10 journeys

**01 · 03 · 06 · 07 · 13 · 14 · 16 · 17 · 18 · 19.** `IN STOCK`. `£60.00 · M`. `ADD TO BAG`. `SOLD OUT`.
`2 OF 5 SIZES LEFT`.

> 01: *"`IN STOCK` in plain capitals is exactly the right two words — I know where I stand."*
> 16, screen reader: *"they're called* Size M*, not* M*. That one word is the difference between guessing
> and knowing. And the buy button telling me it's unavailable* and why *means I'm never left pressing a
> dead button wondering what I did wrong."*
> 03, who did not buy: *"The buying part of this page is excellent and I want to say so... If the table
> had been real I'd have been through checkout in forty seconds."*

01 draws the line the council should hold: the terminal fiction is a reason to remember the shop
*only because* the money words are boring. *"Had the second £60.00 been styled as `EXHIBIT VALUE: 60`
I'd have gone."*

### Every price and a stock word on the register, before a single tap — 9 journeys

**06 · 07 · 08 · 10 · 12 · 14 · 16 · 17 · 19.**

> 08: *"Every price is on the list, no 'from £', nothing hidden behind a tap... I knew I was spending
> about ninety quid before I'd opened a single product."*
> 14, on one bar of signal: *"the whole catalogue in words"* — names, prices and `AVAILABLE` on every
> item were readable at three seconds, before a single photograph existed. *"On a bad connection that is
> a real advantage and it should be protected."*
> 16: *"the price and whether it's in stock are* inside the link *— I know what a thing costs before I
> open it, which decides whether I bother."*

10 got the whole comparison she came for in two clicks because the two £60 jeans sit adjacent in
the same row at the same size. 19 saw the entire stock in two turns of the wheel.

### `SIZE GUIDE`: one press, no pop-up, no PDF, table already open — 6 journeys

**03 · 04 · 06 · 09 · 11 · 17**, with 18 endorsing the destination and objecting only to the glide.

> 03: *"One tap, from right beside the size buttons, no modal, no PDF, no pinch-zooming a sideways image...
> Both are better than the ones on sites twenty times this size. They are pointed at the wrong data."*
> 11: *"Best thing on the site so far. One press and the numbers are just* there*."*

Note where it sits in the file order: the control is excellent and the data behind it is the worst fault
in the audit. Fixing the numbers converts this from a fast route to a problem into the best size
experience most of these shoppers have had.

### The `CM` / `IN` toggle rewrites the sentence, not just the digits — 5 journeys

**03 · 10 · 11 · 16 · 17.**

> 11: *"That's the single best-built thing here. Somebody remembered to change the sentence too. That's
> the detail that tells me a real person built this and cared."*
> 17, at 200%: *"It changed the words as well as the digits."*

One gripe, from the one shopper testing for it: it is the only setting that doesn't follow you to the
next product, while light/dark and outline both do (11) — which taxes anyone comparing garments (03).

### Nothing is faked, and the "was" price is honest addition — 7 journeys

**01 · 02 · 05 · 06 · 07 · 08 · 19.** No countdown, no fake stock counter, no invented reviews, no
"17 people are viewing".

> 05, who arrived specifically to catch them out: *"£45 is £45 on its own page, on the crewneck's rail,
> and later in the cart's own recommendations — the same number in three separate places, none of them
> dressed up as a discount... That is the single most trust-building thing on this site and they probably
> don't know it's doing any work."*
> 06: *"`2 OF 5 SIZES LEFT`... I was warned before I tapped in, without a fake countdown or a scarcity
> gimmick, and that is exactly the right amount of information at exactly the right moment."*
> 02: *"The absence of reviews here reads as* they haven't faked anything*, not as* nobody has bought
> this*, and that only holds because nothing else on the site is faked either."*

02 states the condition plainly, and it is the sharpest sentence in the twenty files: **if a single
fake-urgency line ever appears on this site, the missing reviews immediately start looking like a
cover-up instead of a principle.** The first-visit overlay's `Code expires in 20 minutes` and
`(this drop closes 15.09)` are already sitting on the wrong side of that line.

### `Decline` is a real button, the same size as `Accept` — 10 journeys

**01 · 02 · 03 · 04 · 06 · 12 · 13 · 14 · 18 · 20**, with 17 dissenting because at 200% it is the button
whose edge runs off the screen.

> 02: *"They didn't try it on. Noted."*
> 14: *"Credit where it's due... One tap out. That's better than most."*

Every one of them expected the opposite, and several banked goodwill on it — 02 explicitly gives the
shop extra patience for it. It costs one clipped edge at 200% to lose that entirely.

### The writing volunteers the bad news before it's asked for — 5 journeys

**01 · 02 · 03 · 12 · 19.**

> 02: *"Every one of those is a sentence that costs the shop something, written plainly, before I asked.
> Shops that are about to rob you write the opposite of that. It's more convincing than any badge, and
> it's more convincing than reviews would have been."*
> 03, who did not buy: *"Clear, plain, no wriggling, and I respect that it says it straight instead of
> burying it."*
> 12: *"Short, plain, tells me the cost, and the size-swap line is actually generous."*

`CHAIN OF CUSTODY — SHIPPING & RETURNS` is named the best thing on the site by 02 and gives four
shoppers the courier, the cutoff, the delivery window, the 14-day deadline and who pays return postage
without leaving the product page.

### The detail panels stay open together — 3 journeys

**10 · 16 · 19.** Opening one does not close the last.

> 19: *"This is where the wide screen genuinely pays. Everything I need to decide with is open at once
> and I'm not clicking back and forth."*
> 16: *"nothing closed itself when I opened the next one, which is the thing that usually makes me lose
> my place."*

### The menu panel handles focus properly — 3 journeys

**15 · 16 · 17.** Focus goes into it, the page behind goes quiet, `Escape` closes it and puts the shopper
back on `MENU`.

> 15: *"Genuinely good. I could read the menu with my hands."* Sixteen controls cycling inside, Shift-Tab
> wrapping to the bottom rather than falling out.
> 16: *"textbook. Someone thought about this."*

This is protect-list material with one open question against it — see §5.

---

## 5. Where personas disagreed

### The menu drawer — **settled by a third pass: the trap works**

**16 (screen reader)** reported Tab pinned to `CLOSE` — five presses, five `CLOSE` — Shift-Tab
jumping out to `BAG`, and the fourteen links between readable but not reachable. *"If I were less
patient I'd have assumed the menu was broken and closed it."*

**15 (keyboard only)** was asked to test rather than confirm it and could not reproduce it in
four opens across two pages and two sessions: twelve to twenty-two distinct links, zero presses leaving
the panel, and she used the drawer as a real navigation route to two different collections.

**An independent tiebreaker driving real Tab keypresses settles it in 15's favour**: twenty presses
cycle sixteen controls and wrap back to the first, zero land outside the panel, Shift-Tab stays inside,
Escape closes and returns focus to `MENU` (`audit/screens/tiebreak-trap.png`).

15 named the two things that produce 16's symptom exactly, and both are worth keeping on record: the
first-visit overlay pins Tab in a three-control loop and makes `MENU` unreachable while it is up — it
wrecked three of her own runs before she identified it — and the panel has its own `ACCOUNT` and
`BAG [0]` in its footer, so Shift-Tab off `CLOSE` correctly wraps to the *panel's* BAG, which by
accessible name alone is indistinguishable from escaping to the header's. **Nothing in the drawer
should be changed.**

### Whether the dispatch line stands down on a sold-out size — **settled: it does**

**06** picked a sold-out `M` and both lines — `Order before 18:00 and it ships today (Mon–Sat)`
and `> Ordered now — leaves tomorrow` — disappeared. He checked twice because he expected the opposite,
and made it one of his two best moments:

> *"The shop stopped promising me a delivery date for a thing it can't send... that's the difference
> between a shop that's out of stock and a shop that's lying to you."*

Against him, an earlier feature pass (`raw-pdp-core.md`) recorded both lines still on screen beside
`SIZE M IS SOLD OUT`. The re-run in `raw-notify-verify.md` could not reproduce that at any point — same
product, same size, same phone size, same day — and reports the lines absent on every attempt.

**Settled in 06's favour: two independent runs against one, and the shopper who most wanted it to be
false checked it twice.** What survives from the other side, unchanged: the strip along the top of the
page keeps advertising `FREE UK SHIPPING OVER £20 — ORDER BY 18:00 FOR SAME-DAY DISPATCH` while the
screen below it says `SOLD OUT`. *"It's the only bit of the sold-out screen that isn't straight with me."*

### What `ON MODEL` actually does — **unsettled, and the inconsistency is the finding**

Three laptop shoppers pressed the same button and got three different answers:

- **11:** all twelve cards changed to the same photograph of one man in a black tee and grey
  shorts, under headings reading `SWEATS`, `DENIM` and `ACCESSORIES` and prices from £6 to £60.
  *"That's not the jeans. That's not any of them."*
- **19:** exactly one card of twelve changed — and not one of the four he had already found real
  model photographs on. *"The button is a light switch wired to nothing."*
- **10, on the denim page:** none of the four cards changed at all. She pressed it, pressed
  `FLAT`, pressed it again, and photographed both states to be sure.

Nobody's account contradicts the others' evidence; the button simply does not behave the same way twice.
All three agree on the consequence: the model photographs exist, and the control that promises them is
the one route that does not deliver them.

### The absent sticky buy bar on a laptop — **settled by naming the condition**

**19, at ordinary size:** *"Good. Leave it exactly as it is."* He checked seven scroll positions,
never had two buy buttons on screen at once, and calls the absence the opposite of what most shops do
to a laptop.

**17, at 200%:** the same absence costs her a scroll up and back every single time, because her
size row and `ADD TO BAG` can never be on screen together. *"The only way to be sure is to look twice."*

Both are right about their own screen. The condition is the zoom, not the device — so any change here has
to be conditional on it, and 19's version must not be sacrificed to 17's.

### Whether the first-visit overlay appears at all — **unsettled**

Ten journeys met it. Three deliberately waited for it and it never came: 02 sat on the homepage
for a quarter of a minute — *"Nothing. No overlay, no popup, no 'WAIT! 10% OFF'"* — and banked real
goodwill on its absence; 16 *"sat there several seconds waiting for the pop-up everyone warns me
about and none arrived"*; 10 reports no pop-up on the homepage at all.

This matters more than it looks. The three who missed it rate the shop's restraint as a reason to trust
it, and 02's whole defence of having no reviews rests on nothing else on the site being pushy. The ten
who met it lost two of five taps to dismissing things, had clicks swallowed, and in one case were shown
a countdown before a single garment. **Whichever of those two shops a stranger meets is currently down
to chance**, and the audit cannot say which is more common.
