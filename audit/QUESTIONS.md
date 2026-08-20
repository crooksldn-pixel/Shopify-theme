# The four live questions, answered from evidence

Written from the feature census (`audit/features/FEATURES.md`) and the twenty
journeys (`audit/journeys/`). Every claim below is tied to a named journey or a
screenshot. Where the evidence contradicted the question's own premise, that is
said rather than worked around.

---

## Q1 — The board's move to the drawer

**Was it a net gain or a loss?**

**A loss, and nothing replaced it — but the board is not what a first-time
shopper needed anyway, so the fix is not to move it back.**

**Does anyone find it?** Effectively no. It is the **thirteenth item** in the
drawer. Its artwork begins at y=658 and `PLAY CASE:001 NOW` sits at y=962 —
**118px below the fold of a 390×844 phone**, inside a panel that carries no
heading and gives no cue that it scrolls. The only other route is a footer link
in the last 2.5% of a page 5.8 screens long. Not one of the twenty personas
found the board by browsing; the two who reached it were sent there
(`19-desktop`, `18-reduced-motion`).

Worse, at the moment the drawer is most likely to be opened — a first visit —
**the consent banner covers the bottom 43% of it**, so everything from
`QUESTIONS` down is behind cookie text, and **tapping `PLAY CASE:001 NOW`
presses `Accept` on the banner instead**. That was hit-tested, not inferred
(`raw-header-drawer.md`).

**Does the homepage still have anything memorable?** No. The hero is three lines
of text and one button, and that button (`#products`) jumps to a heading already
on screen. Persona 01 — the cold Instagram click, the highest-volume visitor —
described the landing as *"a cropped photo and the words `PRODUCT 05 / 12`"*
because the consent sheet covered everything else.

**But the premise deserves challenge.** The board was never what won anyone
over. What the evidence says actually earns this brand its stranger's trust is
the **writing** (persona 02: *"the copy volunteers bad news unasked… more
convincing than any badge"*) and the **plain-English buy spine** (persona 01:
*"had the `£60.00` been styled as `EXHIBIT VALUE: 60` I'd have gone"*). The
homepage's strongest asset today is the **packaging block** — *"Sealed, tagged
and numbered before it leaves us. Nothing here is an extra you pay for."* —
which persona 09 called the best gift-buyer content on the site.

**So:** the homepage lost its signature element and gained nothing, which is a
real loss of memorability. But restoring the board would spend the first screen
of the highest-bounce page on a game. The higher-value move is to give the
homepage something that *sells* — a photograph of a garment on a person, which
the store already owns and cannot currently show (see Q3) — and to fix the
drawer so the game is reachable at all: give the CASE 001 panel a heading, and
stop the consent banner sitting on its button.

---

## Q2 — The carriage bar's position

**Does it earn 0.26 viewports at the top of every page?**

**The question's premise is wrong, and the real problem is worse than the one it
asks about.**

**It does not cost a first-time visitor anything, because it does not render for
them.** The section is gated on `cart.item_count > 0`. An empty-cart shopper —
every first visit, and every one of the personas' opening screens — never sees
it. Nobody had written that down.

**Measured**, on a 390×844 phone: the bar is **160px, 0.19 of a screen**, on all
five templates. The homepage's first product card sits at **757px (0.90
screenfuls) without it and 917px (1.09) with it**. So the cost is real but is
paid only by shoppers who already have something in the bag.

**The real finding: it never updates after an add to bag on a product page** —
the one thing it exists to do. Persona 08 watched a bag go from £25 to £85,
crossing **both** thresholds, while the bar kept reading `> £45.00 to free
Tracked 24` above a header showing `BAG [2]`. It corrects only on the next page
load. On `/cart` the same bar reacts to a removal within a second.

**And the £20 tier is never announced at all.** It is crossed on the first add,
and first mentioned later as a small `✓` beside a message about a larger
threshold — while the top strip is still advertising `FREE UK SHIPPING OVER £20`
to someone who has already passed it.

**Does any persona change what they spend because of it?** **No — and persona 07
shows why it is not fixable with copy.** On a £6 order he is £14 short. The next
cheapest item is the other £6 socks (still short). The cheapest item that clears
£20 is the **£18 duffle** — £18 spent to save £3. **Nothing exists between £6 and
£18.** His verdict: *"next time I'd wait until I wanted something bigger — which
is precisely the behaviour the threshold is meant to cause, and the £20 bar never
actually asked me for."*

**Verdict:** it earns its place on **`/cart`**, where it is actionable and where
it is the only surface that updates live, and on **collection** pages. It does
not earn it on **home**, **product** (it sits 555px above the shopper's screen at
the moment they tap `ADD TO BAG`) or **search**. Fix the live update before
moving anything: a bar that lies is worse than a bar in the wrong place.

---

## Q3 — The `Outline` toggle (O3)

**Does it improve legibility enough to justify a control?**

**No. Ship it on permanently and delete the button — or point it at real
photography instead.** Three findings, all screenshotted, from two independent
personas:

1. **In light mode it does literally nothing.** Persona 11 captured the same
   three cards with the toggle on and off in light mode and the files are
   **byte-identical** (matching md5s on the card 1, card 3 and card 10 pairs).
   The equivalent dark pair genuinely differs. So half the time a shopper presses
   it, the button lights up and the page does not change.
2. **It is not taste-neutral — it changes what the garment appears to be.** The
   cream keyline traces the shorts' waistband, seams and hem and reads as
   **binding**; on the crewneck as collar and cuff **trim**; on both blue washes
   as **white piping**. None of those exist on the garment. And it follows
   through to the product page at full size, where the buying decision is made.
3. **The button is homepage-only.** `/collections/all`, `/collections/denim` and
   `/search` render the outline treatment but carry **no `Outline` button** — the
   setting applies where the switch isn't.

Its one genuine benefit — separating the black duffle and black socks from the
near-black card — is small, and both are readable without it.

**The more useful reframing:** the control next to it, `Flat` / `On model`, is
the one that matters and it is broken in a way that makes this whole question
secondary. See Q1's closing note and `FEATURES.md §2.3`: `ON MODEL` puts **one
photograph of a man in charcoal shorts on all twelve cards**, including the £6
socks and the £18 duffle. Meanwhile **hovering** a card reveals a real second
photograph on **4 of 12** — including the only picture of a human wearing
anything — which phone shoppers can never reach. The photography exists. The
control built to show it points somewhere else.

---

## Q4 — Trust, with no reviews at all

**Is the absence fatal, survivable, or consistent with the brand?**

**Consistent with the brand — genuinely fine, and conditionally so. The
condition is currently being breached.**

Persona 02, the sceptic, is the primary evidence and reached this unprompted:

> *"A five-star widget would be the least believable object on this page. This
> site has no countdown timer, no '17 people are viewing', no fake stock counter,
> no trust-badge strip. Against that consistency a review carousel would stick
> out as the one thing bought in rather than written, and I would trust it
> **less**. The absence reads as* they haven't faked anything*, not as* nobody
> has bought this*."*

And then the condition, which is the most important sentence in this audit:

> *"That only holds because nothing **else** on the site is faked either. If a
> single fake-urgency line ever appears on this site, the missing reviews
> immediately start looking like a cover-up instead of a principle."*

**The first-visit overlay says `Code expires in 20 minutes.` and
`(this drop closes 15.09)`.** That is a countdown, on the store's own rejected
list, and it is the **first full-screen thing a stranger meets**, before they
have seen a product. The one mechanic that invalidates the no-reviews position is
already deployed at the top of the funnel.

**The strongest thing the site does to earn trust** is the writing, specifically
that it volunteers bad news before being asked: *"Return postage is yours —
change of mind, wrong size, a swap, any reason of your own."* · *"Original
shipping charges are not refunded."* · *"We cannot refund or replace before that
investigation closes."* · *"Any import duties your country charges on arrival…
aren't included at checkout — just so there's no surprise on the doorstep."*
Persona 02: *"Shops that are about to rob you write the opposite of that."*

Two more, unprompted, from other personas: **the shipping promise switches off
when a sold-out size is picked** (persona 06: *"that's the difference between a
shop that's out of stock and a shop that's lying to you"*), and **`2 OF 5 SIZES
LEFT` on the register** warns before the tap without inventing a countdown.

**The weakest is the contact route**, and it is three compounding failures:
- The footer's `CONTACT` is a **dead heading** that swallows a tap.
- `MENU → CONTACT`, the two most obvious taps on the site, reaches an
  **unbranded cream form** with no email, no name, no address and no reply time.
- `/policies/contact-information` — which carries *"Real people read every
  message, usually the same ones packing your order… we reply within 1–2 working
  days"* — is **linked from nowhere**. Persona 02 found it by accident on the
  fourth attempt, nineteen minutes in.

For a shopper whose entire question is *"is there a human here"*, the site's
answer is: yes, but only if you happen to open an accordion called *chain of
custody*, or read to the bottom of a policy page.

**The real caveat, and it is not about reviews as social proof:** reviews answer
a second question this site cannot answer at all — *does the denim feel like £60,
and do the sizes run true on a body*. There is **not one photograph of a human
being wearing anything** anywhere a phone shopper can reach. Persona 01 lost the
sale on exactly that, and persona 10 chose between two £60 jeans on nothing but
which one had a model shot.

**So the answer is not "get reviews".** It is: keep the position, remove the one
thing that breaks it, print the contact details where a sceptic looks first, and
put a photograph of the clothes on a person — which is not a trust widget, is
not on the rejected list, and is the thing reviews would have been standing in
for.
