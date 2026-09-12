# Visual critique — the AFTER state

§31 asks for the critique to be run again on the result, and for the pass not to stop because
tests are green if the screenshots still look mediocre. This is that second pass, on
`docs/screens/phase5-after/`, judged the same way and against the same seven findings.

The screen examined in most detail is `601x889-21-split-independent-left-right.png` — the orb
divided, an inbox open on one half, at 601 × 889 and DPR 1.33. It is the nearest the capture
gets to the state the owner was in when he said *"I cannot click the merge or close button."*

---

## The seven findings of the before-pass, settled

| # | Before | After | By |
|---|--------|-------|----|
| 1 | The same label three times in 120 px | **Partly.** The exact duplicate is gone: the card no longer prints `3 orders` under a tile reading `3 / ORDERS`. The area kicker and the set chip can still coincide. | me |
| 2 | Six heterogeneous controls in one row, overflowing | **Fixed.** The halves and their un-divide control have their own band; the navigation row holds the trail and the list cursor and nothing else. Both bands fit 601 px. | A |
| 3 | "EMPTY To go out" — a chip contradicting itself | **Fixed**, on the chip and then on the band above the cards, which had the same fault. | A, me |
| 4 | "CANNOT HEAR YOU" in amber, permanently | **Fixed** as far as it should be. The check really is failing, so the amber is honest; the WORDS now name the service — "Speech offline", the shape its four siblings use — instead of implying the assistant is refusing to listen. | me |
| 5 | A 60 px notification stating what the screen shows | **Fixed.** `divided`/`merged`/`opened`/`tab changed` produce nothing at all. | F |
| 6 | "THESE 3 orders" | **Fixed.** "This list", on the same axis as its two siblings (Narrowed, Cross-referenced) and a phrase rather than a dangling pronoun. | me |
| 7 | The row chevron crowds the status badge | **Not fixed**, deliberately — see below. | — |

## What the pictures show that the before-pass could not

Three defects that only became visible once the screens above them were fixed:

### 1 · A four-fact blob where a name should be
```
HALF 1
ORDER
#1927 Fionn Doherty28 Aug, 23:00£83.0…
```
The half chip's second line is the record's LABEL, and the label was built by scraping the
tapped row's `textContent` — every span on it, in DOM order, with nothing between them,
because adjacent spans have no separator in `textContent`. The number, the customer, the date
and the money ran together and were then cut at 40 characters by `Branch.headline`.

It reached three places from there: the chip, the band above the cards, and the trail. Fixed
at both ends — the row now SAYS what the record is called (`data-label`), and the fallback for
a shape nobody has enumerated joins with a separator, so the worst case is a label that says
too much rather than one that says "Doherty28".

### 2 · The correlator's own grade, printed at the owner
```
Mia Jones — Order 1938 — can I add to it?
#1938 · confident
```
`confident` and `possible` are how `app/families/order_email.py` grades the link between a
person and an order. Neither is a thing a person says. A certain link needs no adjective — the
order number is the claim — and an uncertain one has to be visibly uncertain, because the row
is a decision to reply and a wrong link is a reply to the wrong question. So it reads `#1938`,
or `maybe #1938`.

Same defect class as EMPTY and THESE: a machine word on the glass. That is now three of them
found by looking at pictures, and none by a test.

### 3 · A customer workspace with no way to write to the customer

Shot 10 of the §32 matrix came back `MISSING — the customer surface has no write`, which is
the owner's own sentence from the timeline:

> *"I'm not seeing any UI here except email where there's nothing. I want to also be seeing
> his orders and his history and like an email write box"*

The orders and the history landed in this pass. The write did not, and the cause was one
argument: the workspace ABOUT a person called its action builder without passing the person
in, so the only offers it could make were its two doors out — to their last order and their
newest thread. A reading surface with no way to do the obvious thing is the sparse half of
§12, and no test could have said so, because nothing was broken.

It now offers **Email Mia Jones**, and the offer is conditional on the Mac actually HOLDING
that record rather than merely having permission for it — because the write does not re-read,
and an offer resting on permission alone would outlive the record and become the
refusal-under-a-finger §18 forbids. The `open.entity` door to the workspace you are already
standing on was suppressed at the same time (§25).

The photograph is the point of this one. The first screenful now answers what he asked, in
this order: who he is and whether he is returning, four numbers, the two things that need
attention, three things he can DO, then the tabs. That is §12's brief, and the previous
version of this card opened on an empty Email panel.

### 4 · A card the Mac had already taken away
Not in a screenshot — in the click-path matrix, and worth listing here because it is the same
mistake as a visual one. Cancel on a composer said "Gone. Nothing was saved." and the composer
stayed on the screen. §19: visual state outranks the spoken claim, and the spoken claim was
the only thing that changed.

---

## What is genuinely good, checked again

Every item the before-pass said must survive has survived, and the two the pass was told to
restore are visibly better:

- **The three stat tiles.** Unchanged. Still the best information design on the product, and
  now not competing with a line of text repeating one of them.
- **The order rows.** Unchanged. Number, name, amount, date, badge.
- **The dock.** Unchanged, and now the only thing in the bottom band, because the un-divide
  controls have their own home above it.
- **The type scale and the palette.** Untouched. No restyling was done in this pass and none
  was needed — the before-pass's governing finding was that the visual language is not the
  problem, and that held up.
- **The spoken summary line** paired with the small orb. Unchanged.
- **New, and the point of §8:** the halves now read as a region rather than as two chips lost
  in a strip of eight controls. `HALF 1 / ORDER / #1927 Fionn Doherty` beside
  `HALF 2 / EMAIL / Order 1938 — can I add to it?`, with Merge and Close under them, both
  wholly on the glass. That is the premium feature §17 asks for, and it is the first build in
  which a photograph of it looks deliberate.

---

## What was NOT fixed, and why

**The row chevron (finding 7).** The `›` sits at the vertical centre of the row, between the
amount and the status badge, and at 601 px that corner reads as three elements in one place.
It overlaps nothing — measured, not assumed — so it is a matter of taste rather than a defect,
and the taste argument cuts both ways: it is the only thing on the row that says a row can be
pressed. Removing it to win 26 px of width would be trading a real affordance for a tidier
corner. Left alone, and named here so the next pass can disagree with a photograph in hand.

**The working-set strip's overlap with the stat tiles.** `THIS LIST · 3 orders` carries
`£195.00 VALUE`, which the tile above it already shows. §25 says a surface that does not earn
its space comes off, and on the orders listing this one arguably does not. It was left because
`tests/test_flows.py:268` asserts the card exists, the forensics does not call it wrong, and
suppressing it would mean changing a green expectation on a debatable basis rather than a
provable one — which is exactly what §2 forbids. The strip is right on the surfaces it was
built for (a filtered or correlated set, where the arithmetic is the only thing it carries).

**Four stat tiles at 601 px.** On the customer workspace the third tile's value
(`#1938 · 12 Sep`) breaks across two lines, because `.stats.counts` is
`repeat(auto-fit, minmax(88px, 1fr))` and an 88 px floor lets four tiles onto a 549 px row at
133 px each. Raising the floor to put three on a row — the arrangement the before-pass
praised — leaves a lone fourth tile stretched across the full width, which is worse. The
value is legible on two lines and nothing is clipped or overlapping, so this is a typographic
wrap in an otherwise good card rather than a defect. Named here with the numbers so the next
pass can decide it with a measurement instead of a re-derivation.

**The area kicker beside a lit dock button.** On a single-card deck, `ORDERS` on the card says
what the lit dock button and the set chip have already said. Suppressing it needs the current
area threaded into every card head, and on a MIXED deck the kicker is the only thing telling
two cards apart. Judged not worth a change that touches twenty renderers for one line of small
uppercase; the exact duplicate inside one card was the part worth removing, and it was.
