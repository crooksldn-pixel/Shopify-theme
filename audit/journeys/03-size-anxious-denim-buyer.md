# PERSONA 3 — Size-anxious denim buyer

**Who:** Wants the £60 baggy jeans. Between sizes. Has been burned before by baggy fits.
**Conditions:** 390 × 844 throttled, **and** 1440 × 900 desktop. Entered on `/products/cb2-wash-jeans` (BLUE WASH OG JEANS, £60).
**Route:** product page → find measurements → work out their size → check returns → decide.

> Note for the record: `cb1-wash-jeans` is **GREY** WASH. The blue pair is `cb2-wash-jeans`. The handles and the wash codes do not correspond in the order you would guess.

---

### Step 1 — Arrival
**Screenshot:** screens/p3-step1.png
**On screen:** `← CATALOGUE  PRODUCT 04 / 14  DENIM` · one photograph of the jeans, back view · `PHOTO 1 OF 1` · `BLUE WASH OG JEANS` · **£60.00** · `SIZE XS S M L XL` · `IN STOCK` · sticky `ADD TO BAG`. Cookie banner over the bottom 40%.
**Goal right now:** see the jeans.
**Felt experience:** Good photograph, clean cut-out, and the price is right there. But `PHOTO 1 OF 1` is doing me no favours — one back-view shot of £60 jeans and no idea how they sit on an actual leg.
**Blocked by:** **one image, and it's the back.** No front, no side, no on-body, no stack detail. For "baggy, stacked fit" this is the one thing this shopper needs most.
**Would they continue?** hesitant.
**Seconds elapsed:** 16.9

### Step 2 — Popup cleared
**Screenshot:** screens/p3-step2.png
**Goal right now:** find measurements.
**Felt experience:** Fine.
**Blocked by:** nothing.
**Would they continue?** yes.
**Seconds elapsed:** 19.4

### Step 3 — Tapped SIZE GUIDE
**Screenshot:** screens/p3-step3.png
**Measured:** button is **114 × 44 px** (passes the tap-target minimum), sits at 762 px from the top — inside the first viewport. Tapping it scrolls the page **1,230 px** and lands with the `MEASUREMENTS` heading at exactly y = 0.
**Goal right now:** get the numbers.
**Felt experience:** That worked properly. One tap and I'm looking at the measurement chart. No modal to fight with, no PDF, no "contact us for sizing".
**Blocked by:** nothing. One small friction: because it scrolls rather than opening a panel, the size buttons are now off-screen — I can read the table or tap a size, not both.
**Would they continue?** yes.
**Seconds elapsed:** 22.0 · 1 tap

### Step 4 — Reading the table
**Screenshot:** screens/p3-step4.png
**On screen:**
```
GARMENT LAID FLAT. ALL MEASUREMENTS IN CENTIMETRES.
SIZE  WAIST  INSEAM  RISE  HEM
XS    38cm   76cm    27cm  19cm
S     40cm   78cm    28cm  20cm
M     42cm   80cm    29cm  21cm
L     44cm   82cm    30cm  22cm
XL    46cm   84cm    31cm  23cm
```
**Goal right now:** work out whether I'm an M or an L.
**Felt experience:** This is exactly what I wanted and almost nobody at this size of brand provides it. It even says *garment laid flat*, so I know to double the waist. I can measure a pair I already own and compare. Genuinely reassuring.
**Blocked by:** nothing — at this moment the shopper is satisfied.
**Would they continue?** yes.
**Seconds elapsed:** 23.0

### Step 5 — Switched to inches
**Screenshot:** screens/p3-step5.png
**Measured:** `XS 15in 29.9in 10.6in 7.5in · S 15.7in 30.7in 11in 7.9in · M 16.5in 31.5in 11.4in 8.3in · L 17.3in 32.3in 11.8in 8.7in · XL 18.1in 33.1in 12.2in 9.1in`. Conversion is correct (38 cm → 15 in).
**Goal right now:** compare against a pair I own, which I think of in inches.
**Felt experience:** There's a CM/IN toggle and it actually works. That's a thoughtful detail — most brands twice this size don't bother.
**Blocked by:** nothing.
**Would they continue?** yes.
**Seconds elapsed:** 24.0 · 2 taps

### Step 6 — Checking returns
**Screenshot:** screens/p3-step6.png
**On screen (CHAIN OF CUSTODY, expanded):** `You have 14 days from delivery to return unworn goods with tags attached. Start a return by email: info@crooksldn.com.`
**Goal right now:** what happens if they don't fit.
**Felt experience:** Fourteen days, unworn, tags on, email to start. Clear. I'd want to know who pays the return postage, because on a £60 order that's the difference between risking it and not — and it doesn't say.
**Blocked by:** **the refund policy never states who pays return postage** (checked directly: no match for return shipping cost on `/policies/refund-policy`).
**Would they continue?** hesitant → **yes**, on balance.
**Seconds elapsed:** 25.1 · 3 taps

---

## The measurements are placeholder data — and here is the proof

The brief asked whether a real shopper could tell. **Looking at one product: no.** The numbers are precise, plausible, and correctly framed as laid-flat. **Comparing two products: instantly.**

| Product | Fabric | Cut | WAIST | INSEAM | RISE | HEM |
|---|---|---|---|---|---|---|
| BLUE WASH OG JEANS | 14oz denim | OG straight, mid rise | 38–46 | 76–84 | 27–31 | 19–23 |
| GREY WASH OG JEANS | 14oz denim | OG straight, mid rise | 38–46 | 76–84 | 27–31 | 19–23 |
| **V2 BAGGIES** | **500gsm cotton** | **Wide, full length** | **38–46** | **76–84** | **27–31** | **19–23** |

A 500 gsm cotton wide-leg sweatpant does not share waist, inseam, rise **and** hem to the centimetre with a straight-leg 14 oz denim jean. Every column is also a perfect arithmetic progression (+2, +2, +1, +1 per size) across all four measurements — the signature of generated data, not a measured garment.

**Worse, coverage is thin and skewed the wrong way:**

| Has a measurement table | No measurement table |
|---|---|
| BLUE WASH OG JEANS · GREY WASH OG JEANS · V2 BAGGIES (wrong data) · 3 CLIVES TEE · BROADCAST TEE | **BLUE WASH JORTS · GREY WASH JORTS** · CHARCOAL CELLBLOCK CREWNECK · CHARCOAL CELLBLOCK SHORTS · CRXST★RZ · MONEY CLIVE TEE · duffle · both socks |

**The jorts have none.** "Baggy, below knee" £50 shorts — the single hardest garment on the site to judge from a cut-out photograph — offer no measurements at all.

And V2 BAGGIES contradicts itself: its measurement table is copied from the denim, while its own product description carries genuine height-based sizing — `5,1-5,4 XS · 5,5-5,7 S · 5,8-5,10 M · 5,11-6,1 L · 6,1+ XL`. Two different sizing systems on one page, one of them wrong.

---

## Desktop (1440 × 900)

Materially the same journey, 3 taps, same content. Two differences worth recording: the SIZE GUIDE button sits at 370 px instead of 762 px (higher in the layout), and **CLS drops from 0.233 to 0.0062** — the meta row never wraps at desktop width, so the font swap has nothing to reflow. The size-anxiety problem is identical on both.

---

## Verdict

**Would buy — and this is the strongest journey on the site.**

This is the hardest sale in the catalogue and the page very nearly nails it: real laid-flat measurements, a working unit toggle, a fabric weight, a country of origin, a stated return window, and a one-tap route from the buy panel to the chart. That is better sizing support than most brands ten times this size offer, and it is doing it *inside* the austere design language, not in spite of it.

Three things stop it being decisive:
1. **One photograph, back view only, on a £60 garment sold on its fit.**
2. **The measurement data is placeholder** — provably, via V2 BAGGIES — and the jorts have none at all.
3. **Return postage liability is unstated.**

Fix 2 and 3 and this persona converts without hesitation. Fix 1 and they convert at a higher size-confidence, which is the same thing as a lower return rate.
