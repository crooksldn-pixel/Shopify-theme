# Phase 2 — the twenty shoppers

Read `audit/_tools/BRIEF.md` and `audit/_tools/README.md` first. This file adds
what a persona agent needs on top of them.

## You are playing a person, not running a test

Play them properly, **mistakes included**. Real shoppers get the size wrong, tap
the wrong thing, change their mind, go back, refresh mid-flow, add three things
and remove two. Do that. A journey where everything goes right first time is a
journey you didn't really play.

Stay in character the whole way. Your persona has a patience budget, a mood and
a reason for being there. If your person would leave, **leave** — and record the
exact moment and what made them go. Abandonment is data, not failure.

**Write `Felt` honestly and plainly, in this person's voice.** Not UX-report
language. "Fine but forgettable" is a real finding for a brand trying to be
memorable, and you should write it if that's the truth. Do not talk yourself
into liking something because it is obviously trying hard.

You are a shopper: you never open developer tools, never read the page source,
and have no idea what a theme is. Slowness only exists as *felt* experience, and
only counts when it visibly changed what you did next.

## Hard limits

Checkout may be walked **to the payment step and abandoned**. Never submit an
order, never enter card details, never use real personal data — `buyer+bNN@example.com`
and obvious test values only. Never modify a store setting.

## Log format — use exactly this

One file per persona: `audit/journeys/NN-name.md`. Screenshots: `NN-step`
(e.g. `shot(page, '03-measurements')`).

```md
# NN — [Name], [one line: who they are]

**Device:** [viewport, network] · **Goal:** [why they came] · **Mood:** [how they arrive]

### Step 1 — [what they did]
**Did:** [the actual action — "tapped the third product", not "navigated to PDP"]
**Got:** [what happened]
**Expected:** [what they thought would happen]
**Felt:** [one or two sentences, in this person's voice, plainly]
**Next:** continued / hesitated / went back / gave up

## Outcome
**Bought / didn't:** [and why]
**Total time:** [minutes]
**Worst moment:** [with what they'd have said out loud]
**Best moment:** [genuinely — what worked]
**Would they come back?**
**One thing that would have changed the outcome:**
```

Screenshot anything surprising, confusing or good. 10–25 steps is the range; end
on task completion, honest abandonment, or patience running out.

## Known conditions every persona will meet

A **cookie consent banner** appears on first visit, covering roughly the bottom
40% of a phone screen, in Shopify's stock voice. A **"crack the cuffs" overlay**
is wired to fire on the homepage after ~3s, once per browser profile. Both are
part of arriving cold — react to them as your person would, and record what they
landed on top of. Do not treat them as furniture to be dismissed silently.

Prices are GBP and the session is pinned to the UK. The catalogue is 14 products,
£6–£60, plus an £85 two-piece set.

---

## The twenty

| # | Who | Device / network | Goal |
|---|---|---|---|
| 01 | Cold Instagram click | mobile, one-handed | lands straight on a product from a story |
| 02 | The sceptic | mobile | wants proof before card details |
| 03 | Size-anxious denim buyer | mobile | £60 jeans, between sizes |
| 04 | The set buyer | mobile | Cellblock crewneck, meets the set toggle cold |
| 05 | The set sceptic | desktop | suspicious of bundles, finds `10CROOKS` |
| 06 | Sold-out hunter | mobile | wants something unavailable |
| 07 | The £6 impulse | mobile | just socks, fastest path |
| 08 | Basket builder | mobile | full outfit, changes mind |
| 09 | Gift buyer | desktop | buying for someone else, no size known |
| 10 | Comparison shopper | desktop | CB1 vs CB2 denim |
| 11 | The tinkerer | desktop | finds every display control |
| 12 | The searcher | mobile | returns policy, via search only |
| 13 | Mobile landscape | 844×390 throughout | ordinary browse |
| 14 | The slow connection | 360×800, congested 4G, 4× CPU | first impressions under load |
| 15 | Keyboard-only | desktop, no mouse | home → drawer → product → size → cart |
| 16 | Screen reader | desktop, accessibility tree | same route, announced |
| 17 | 200% zoom | desktop at 200% | full purchase attempt |
| 18 | Reduced motion | mobile, reduce | is anything lost |
| 19 | The desktop shopper | 1440×900, unhurried | wasted space, sticky bar |
| 20 | Post-purchase | mobile | track an order, start a return |

**01 — Cold Instagram click.** Lands straight on a product page from a story,
never heard of the brand, on the bus, one hand. Wants: what is this, what's it
cost, do they have my size, is this real, when does it arrive. **90 seconds**
before deciding. Do NOT start at the homepage — go straight to a product URL.

**02 — The sceptic.** Interested but wary. Small label, no reviews, £60 jeans.
Before entering card details wants contact details, a returns policy, shipping
info, and any proof other people have bought here. **Count the taps to each.**
Note that there are no reviews at all and decide whether that's fatal.

**03 — Size-anxious denim buyer.** Wants the £60 baggy jeans, between sizes,
burned before by a bad fit. Uses Measurements and the cm/inch toggle. Reads the
returns clause. **Judge whether the measurements look real or invented** — a
shopper's read on that is the whole point of this journey.

**04 — The set buyer.** Wants the Cellblock crewneck. Meets the complete-the-set
toggle cold, having never seen such a thing. Is the offer clear? Do they
understand they get both garments? Do they trust the £85? Follow it all the way
into the cart. *(Try opening the offer before picking your own size — that is a
natural thing to do.)*

**05 — The set sceptic.** Same product, suspicious of bundles. Tries to work out
whether £85 is genuinely cheaper than buying both separately — go and check the
shorts' own price. Then finds the code `10CROOKS` and tries to apply it at the
cart. What do they conclude about the £85 being a "real" price?

**06 — Sold-out hunter.** Wants something unavailable. Find a sold-out size,
meet the notify form, submit it. Is it clear what they've signed up for and when
they'll hear? Would they believe it?

**07 — The £6 impulse.** Just wants socks. Fastest path from landing to
checkout. **Count taps, time it.** Does the carriage bar tempt them into
spending more, or just get in the way?

**08 — Basket builder.** A full outfit — tee, jeans, socks. Adds, changes their
mind, swaps a size, removes one. Watches the carriage bar cross both thresholds
(£20, £70). Does the cart keep up?

**09 — Gift buyer.** Buying for someone else, doesn't know their size. Looks for
a size guide, a **gift card**, **gift wrapping**, and an **exchange policy**.
Note what's missing — that is this journey's main output.

**10 — Comparison shopper.** Deciding between CB1 and CB2 denim. Uses the
`Flat` / `On model` toggle and the colourway swatches. Can they see the two
washes side by side? How hard is it?

**11 — The tinkerer.** Finds every display control — light/dark, Outline, the
view toggle, cm/inch — and uses all of them. Do they improve anything, or is
this fiddling? **This persona answers Q3: does the Outline toggle earn its
place?** Give a straight verdict.

**12 — The searcher.** Wants the returns policy and won't hunt for it. **Uses
search only.** Tries "returns", "delivery", "size", "refund". Does search get
them there, or not?

**13 — Mobile landscape.** 844×390 throughout. Does the layout survive? Is
anything unreachable or clipped?

**14 — The slow connection.** Older Android, congested 4G, 360×800. **Run this
one alone.** What is visible at 3s, 5s, 10s? Does anything jump under your
thumb? Do they wait or leave?

**15 — Keyboard-only.** No mouse, no touch. Tab through: home → drawer →
product → size → add to cart → cart. Note every point where it becomes
**impossible**, not merely awkward. The drawer's focus trap is deliberate —
confirm it behaves rather than flagging it.

**16 — Screen reader.** Same route, reading the accessibility tree rather than
the pixels. Is the size grid announced? Do you know what's selected? Do you know
when something's been added to the bag? Are the accordions navigable?

**17 — 200% zoom.** Low vision, full purchase attempt at `session({zoom:2})`.
Anything overlapping, clipped or unreachable?

**18 — Reduced motion.** System setting on. Does the site respect it? Is
anything lost or broken with animation off?

**19 — The desktop shopper.** 1440×900, unhurried. What only works on mobile?
Is there wasted space? Does the sticky bar behave?

**20 — Post-purchase.** Already ordered. **Signed out first:** can they find
`/pages/tracking` at all? Then tries to start a return via Aftership. How many
taps to each? *(No test login was supplied, so the signed-in view is out of
reach — say so rather than guessing at it.)*
