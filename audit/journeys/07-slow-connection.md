# PERSONA 7 — The slow connection

**Who:** Older Android, congested 4G.
**Conditions:** 360 × 800, DPR 3, Android UA, Slow 4G (1.6 Mbps / 150 ms RTT), **6× CPU throttle** (harsher than the standard 4×, to model an older handset).
**Route:** homepage → product → cart.
**Recorded:** what is visible at 3 s, 5 s and 10 s; whether anything jumps as it loads; whether the canvas board makes the page unusable while it initialises.

---

### Step 1 — At 3 seconds
**Screenshot:** screens/p7-step1.png
**Measured:** 2,080 characters of text rendered · 1 image loaded · canvas element present but **not yet painted** · **CLS 0** · no overlays yet · fonts loaded.
**On screen:** Announcement bar, header, the board frame with `CASE 001 — ATTRACT MODE` and `REF 001 / 13×11 / DECLASSIFIED`, the caption text, `> 14 PRODUCTS AVAILABLE TO PURCHASE`.
**Goal right now:** see something.
**Felt experience:** There's text and structure already, which is more than most sites give me at three seconds. The big box in the middle is empty but it's clearly a frame waiting for something, not a broken image.
**Blocked by:** nothing.
**Would they continue?** yes.
**Seconds elapsed:** 3.2

### Step 2 — At 5 seconds
**Screenshot:** screens/p7-step2.png
**Measured:** 2,338 characters · 1 image · **canvas now painted** · **CLS 0** · fonts `loading`.
**Goal right now:** work out what this is.
**Felt experience:** The pixel map has appeared and it's animating smoothly. Nothing has jumped or shifted while I've been looking at it. It feels like the page is arriving in order rather than falling over itself.
**Blocked by:** nothing.
**Would they continue?** yes.
**Seconds elapsed:** 5.9

### Step 3 — At 10 seconds
**Screenshot:** screens/p7-step3.png
**Measured:** 2,372 characters · **15 images loaded** but **only 1 of them in the viewport** · canvas painted · **CLS 0** · `ctc-overlay` now present.
**Goal right now:** see a product.
**Felt experience:** Ten seconds in and I still haven't seen a single item of clothing — because the whole first screen is the game board. Everything has loaded, it's just all below where I'm looking. And now there's a popup over it.
**Blocked by:** **the first viewport contains no product image by design.** 14 product images have downloaded and are sitting off-screen.
**Would they continue?** hesitant.
**Seconds elapsed:** 10.6

### Step 4 — Fully loaded
**Screenshot:** screens/p7-step4.png
**Measured homepage vitals at 6× CPU:** TTFB 825 ms · FCP 1,944 ms · LCP 5,028 ms · **CLS 0** · **INP 944 ms** · load event 13,078 ms · 19 long tasks totalling 3,033 ms.
**Felt experience:** It got there. Thirteen seconds is a long time but nothing broke and nothing moved.
**Seconds elapsed:** 17.1

### Step 5 — Product page
**Screenshot:** screens/p7-step5.png
**Measured:** navigation took **4,151 ms**.
**Felt experience:** Four seconds to change page. Tolerable on this connection.
**Blocked by:** nothing.
**Would they continue?** yes.
**Seconds elapsed:** 22.3 · 1 tap

### Step 6 — Cart
**Screenshot:** screens/p7-step6.png
**Measured:** navigation took **13,265 ms**. Total bytes across the whole journey: **4,798 KB**.
**On screen:** the bone-coloured Horizon cart with Shop Pay, PayPal and Google Pay wallet buttons.
**Goal right now:** check out.
**Felt experience:** Thirteen seconds to open my own basket, and when it arrives it looks like a completely different website. White background, different typeface, big coloured payment buttons. For a second I wondered if I'd been redirected somewhere.
**Blocked by:** the cart pulls in `pay.google.com` (418 KB) and `www.paypal.com/buttons` (178 KB) on top of the theme, and carries the site's worst blocking time (3,440 ms of long tasks).
**Would they continue?** hesitant — the visual break is more alarming than the wait.
**Seconds elapsed:** 37.7 · 3 taps

---

## The brief's specific question: does the canvas board make the page unusable while it initialises?

**No. Measured, and it is the opposite.**

| | 3 s | 5 s | 10 s |
|---|---|---|---|
| Text rendered | 2,080 chars | 2,338 chars | 2,372 chars |
| Canvas painted | no | yes | yes |
| **Cumulative layout shift** | **0** | **0** | **0** |

The board paints *after* the text, reserves its own space so nothing reflows around it, and contributes **zero** layout shift on the homepage across the entire load. Under a 6× CPU penalty it still renders at 60 fps once painted and holds 57.5 fps during scroll.

**The homepage is the most stable page on the site.** The CLS problem (0.233) is on the *product* pages, and it is caused by the VT323 webfont being fetched twice, not by the canvas.

---

## Verdict

**Would continue, but slowly, and would be unsettled at the cart.**

What this persona proves:
- **The board is not a performance liability.** It is text-first, shift-free, and pauses when it isn't visible. This is the clearest evidence in the whole audit that the distinctive thing is also the well-built thing.
- **CLS 0 on the homepage** across ten seconds of loading on a throttled old Android is a genuinely good result.
- **INP 944 ms** is the real interaction cost — nearly a second before a tap feels acknowledged, driven by 3 seconds of long tasks from 1.17 MB of JavaScript (including a 166 KB Base44 bundle that this persona never uses).
- **13.3 s to open the cart**, and the cart is where the design language breaks.

The load times here are dominated by JavaScript and by images that don't need to be as heavy as they are — not by anything the design is doing.
