# PERSONA 2 — Returning fan hunting the new drop

**Who:** Follows the brand. Saw a teaser. Wants to see what's new, and whether the thing they missed is back.
**Conditions:** 390 × 844, DPR 3, Slow 4G, 4× CPU. Entered on the homepage.
**Route:** homepage → look for "new" → scan the grid → check V2 BAGGIES (M, L and XL are sold out).

---

### Step 1 — Homepage
**Screenshot:** screens/p2-step1.png
**On screen:** Announcement bar, header, and the canvas board filling the whole first screen. Cookie banner across the bottom 40%.
**Goal right now:** what's new.
**Felt experience:** I like the board, I've seen it before. But I'm here for the drop and the first thing I get is the game and a cookie wall.
**Blocked by:** nothing yet.
**Would they continue?** yes — they know the brand, they'll scroll.
**Seconds elapsed:** 21.9

### Step 2 — The popup
**Screenshot:** screens/p2-step2.png
**On screen:** `CRACK THE CUFFS` overlay at 100% of viewport, scroll locked.
**Goal right now:** get past it.
**Felt experience:** I've seen this. It's showing me again because I cleared my browser. Fine, close it.
**Blocked by:** the overlay, momentarily.
**Would they continue?** yes.
**Seconds elapsed:** 27.3

### Step 3 — Looking for what's new
**Screenshot:** screens/p2-step3.png
**Measured:** `newInGrid: 0` · grid badges are `["AVAILABLE"]` and nothing else · `anyDates: false` · the word NEW appears **only** as a footer link and a menu item, both pointing at `/collections/new`.
**Goal right now:** find the drop.
**Felt experience:** There's nothing telling me what's new. Every card says AVAILABLE. No dates, no NEW flag, no "just landed". I follow this brand and I still can't tell which of these fourteen things I haven't seen before.
**Blocked by:** **no new-arrival signal anywhere on the homepage.** The catalogue is ordered `NO. 01 … NO. 14` — an inventory numbering, not a recency ordering.
**Would they continue?** hesitant — they'll scroll the grid manually and try to spot something unfamiliar.
**Seconds elapsed:** 28.3 · 1 tap

### Step 4 — The catalogue grid
**Screenshot:** screens/p2-step4.png
**On screen:** `NO. 01 SWEATS CHARCOAL CELLBLOCK CREWNECK £50.00 AVAILABLE` · `NO. 02 … £45.00 AVAILABLE` · `NO. 03 DENIM BLUE WASH JORTS £50.00 AVAILABLE` …
**Goal right now:** spot the new thing.
**Felt experience:** The grid itself is lovely — the numbering, the category, the AVAILABLE stamp. It reads like a property register and I like that a lot. But it's a register, not a feed. It tells me what exists, not what changed.
**Blocked by:** as above.
**Would they continue?** yes — they've spotted V2 BAGGIES.
**Seconds elapsed:** 30.1

> **Checked separately:** `/collections/new` exists and returns 9 of the 14 products — but it carries no dates, no badges and no ordering cue either, and it renders in the Horizon collection template rather than the terminal catalogue. Reaching it takes 2 taps (MENU → NEW) and tells the fan nothing the homepage didn't.

### Step 5 — V2 BAGGIES, the one they missed
**Screenshot:** screens/p2-step5.png
**On screen:** `PRODUCT 10 / 14  SWEATS` · `V2 BAGGIES` · `£60.00` · `SIZE XS S M L XL` · `IN STOCK` · `In stock · Ships within 24 hours` · `ADD TO BAG`.
**Measured:** M, L and XL render with `text-decoration: line-through` and a dimmed `rgb(138,131,119)`. XS and S are full-brightness `rgb(221,215,201)`.
**Goal right now:** is my size back.
**Felt experience:** The struck-through sizes are clear enough — I can see M, L and XL are gone. But the page says IN STOCK in big letters and "Ships within 24 hours" right underneath, which is only true for the two sizes nobody my size wears.
**Blocked by:** the stock line reports the **product**, not the **selected variant**.
**Would they continue?** hesitant.
**Seconds elapsed:** 39.2 · 2 taps

### Step 6 — Tapped L anyway
**Screenshot:** screens/p2-step6.png
**Measured:** `aria-disabled="true"` but `disabled === false`. After tapping L: sticky bar still reads **`V2 BAGGIES £60.00 · XS  ADD TO BAG`**, `variantId` unchanged at `53075854197079` (= XS), ADD TO BAG still enabled. Adding to cart with that state returns `"variant_title":"XS"`. `notifyOffered: false`.
**Goal right now:** register interest, or find out when it's back.
**Felt experience:** I tapped L and nothing happened. No message, no "sold out", nothing greyed out further — it just quietly stayed on XS. If I hadn't been watching the little bar at the bottom I'd have added an extra-small to my basket and not found out until it arrived.
**Blocked by:** **two things.** (a) Tapping an unavailable size produces no feedback at all and silently leaves the previous selection active, with the buy button live. (b) **There is no restock or notify option anywhere** — and the homepage WITNESS STATEMENT says runs never come back, so the honest answer is "never", but the page doesn't say so at the moment it matters.
**Would they continue?** **would leave** — and worse, a distracted version of this person buys the wrong size.
**Seconds elapsed:** 40.5 · 3 taps

---

## Verdict

**Would leave, having learned nothing about the drop.**

The two failures are precise and both are cheap to fix inside the design language:

1. **No new-arrival signal.** The grid has a status slot already — it renders `AVAILABLE` on every card. That slot could carry `NEW` or `JUST FILED` on recent products without adding a single new colour, corner radius or typeface.
2. **Tapping a sold-out size does nothing.** The design system already reserves warning red for "errors and sold-out only" — and the sold-out state currently uses grey strikethrough, not that red. The variant-level state exists in the DOM (`aria-disabled`); it just isn't wired to the stock line, the sticky bar, or any feedback on tap.

The silent-revert-to-XS behaviour is the most serious single defect found anywhere in this audit, because it does not merely lose a sale — it can produce a wrong-size order, a refund, and a first-time buyer who now distrusts the brand.

**What's working and should be protected:** the struck-through sold-out styling itself is correct and legible; the catalogue register with `NO. 01 / SWEATS / AVAILABLE` is distinctive and genuinely pleasurable to scan.
