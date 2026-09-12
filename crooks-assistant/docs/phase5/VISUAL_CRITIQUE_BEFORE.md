# Visual critique — the BEFORE state

§31 asks for a dedicated visual critique pass, judged as a high-end product designer would. This
is that pass run on the PRE-Phase-5 tree, from `docs/screens/phase5-before/`, so the after-pass
has something honest to be compared against.

The screen examined in most detail is `tab-03-divided.png` — 601×889 at DPR 1.33, the orb
divided, an order list on screen. It is as close as the capture gets to what the owner was
looking at when he said *"why is there bullshit on the screen right now?"*

---

## The finding that should govern this pass

**The visual language is not the problem.** The dark ground, the restrained type, the glass
panels, the gold accent, the three stat tiles, the order rows — these are good. A high-end
designer would keep almost all of it. §11 says "do not turn it into a generic admin dashboard",
and the honest answer is that it is not one; it is a well-drawn interface with a badly organised
screen.

So the work is **subtraction and hierarchy**, not restyling. Everything below is a redundancy, a
contradiction, or a thing that does not earn its space.

---

## What is wrong, in order of how much it costs the owner

### 1 · The same label three times in 120 vertical pixels
```
nav chip   ORDERS  To go out
band       ORDERS  To go out                      half 1 of 2
card       ORDERS
           To go out
           3 orders
```
Three headings, near-identical, stacked. §26 forbids "four equally prominent headings" and this
is three. The band and the card are saying the same thing; one of them is redundant, and the nav
chip already said it.

**This is the mechanism of "sparse AND too tall" (§12).** The screen is tall because it repeats
itself, and it feels sparse because after the repetition there is little room left for content.

### 2 · Six heterogeneous controls in one navigation row, and it overflows
```
[‹ Assistant] [Back] [‹] [Next] [ORDERS To go out] [EMPTY To go out ⟶ clipped
```
- four different KINDS of control in one row: a landing, a trail step, an unlabelled `‹`, a set
  cursor, and two branch chips
- two are greyed with no stated reason
- a tiny unlabelled `‹` chip sits between Back and Next, meaning nothing to anyone
- **the second branch chip is cut off by the right edge of the viewport**

§8 requires VOICE / NAVIGATION / SPLIT-BRANCH to occupy clearly distinct interaction zones. They
are currently in one horizontal strip, competing, and the strip is too narrow for its contents at
the authoritative viewport.

The horizontal overflow is a genuine defect the collision gate did not catch, because the gate
looks for overlapping rectangles and `document_overflow_x`, not for a flex row whose last child
is clipped by its own container.

### 3 · "EMPTY To go out" — a chip that contradicts itself
The second half holds nothing, so its chip says EMPTY. It is also labelled with its parent's
area, "To go out". A control cannot usefully say both. And "EMPTY" as a user-facing word is a
database state, not language.

### 4 · "CANNOT HEAR YOU" in amber, permanently, in the header
On an idle screen this is the first thing the eye lands on, next to an amber diamond, in the most
prominent horizontal band on the page. It reads as a fault. It is presumably a microphone state,
but the owner cannot tell whether it means "not listening right now" (normal) or "your microphone
is broken" (alarming). §27: a resting state is not an error state, and this is a resting state
dressed as one.

### 5 · A 60-pixel notification stating what the screen plainly shows
```
DONE   Divided. Tap a half to talk to it; the other keeps working.
```
The orb has visibly divided. Two chips have appeared. §10's example is literally this case:
*"Split completed — the UI itself visibly becoming split is sufficient."* It also opens with
"DONE", which is a strange word for a state change, in green, which is a strange colour for one.

### 6 · "THESE 3 orders"
The working-set card, clipped at the bottom of the viewport, headed with the word **THESE**.
That is not language. §26: prefer human words.

### 7 · The row chevron crowds the status badge
In each order row the `›` affordance sits immediately above and right of the `UNFULFILLED`
badge, close enough that at 601 px they read as one cluttered corner. Not a geometric overlap —
the gate is right that they do not intersect — but visually cramped, which is the §31 question
("is anything cramped?") rather than the §9 one.

---

## What is genuinely good and must survive

Listing this explicitly, because a pass told to "restore the wow factor" can easily throw away
the things that already work:

- **The three stat tiles** (`3 ORDERS` / `£195.00` / `3 TO SHIP`). Real information design:
  large value, small label, equal weight, one row. This is the pattern the rest of the product
  should borrow for §12's sales and product surfaces.
- **The order rows.** Number, name, amount, date, status badge. Scannable, correctly weighted,
  the number and the money emphasised. Nearly right.
- **The dock.** `ORDERS · INBOX · [HOLD TO SPEAK] · SALES · PRODUCTS`, with the current area lit.
  Unambiguous, finger-sized, and the voice target reads as the primary action without shouting.
- **The type scale and the palette.** Restrained, legible at arm's length on a dim screen, with
  one accent colour used sparingly. Do not touch this.
- **The spoken summary line** at the top ("3 orders to go out; the oldest is 1927 at 14 days")
  paired with the small orb. Voice and text agreeing, in one line, is the product's whole idea.

---

## The direction this sets for §11

1. **Delete the repetition before adding anything.** One heading per screen. The band or the
   card, not both.
2. **Split the navigation strip into zones** (§8), and fix its overflow at 601 px.
3. **Turn states into words** — no EMPTY, no THESE, no DONE.
4. **Demote resting states out of the alarm position** — "CANNOT HEAR YOU" is not a headline.
5. **Remove the notifications that narrate the screen** (§10).
6. **Then** spend the space won back on §12's richer first viewport, using the stat-tile pattern
   that already works.

The sequence matters. Every one of those six is a subtraction, and together they return roughly
180 vertical pixels and one entire screen region — which is where the rich workspace goes.
