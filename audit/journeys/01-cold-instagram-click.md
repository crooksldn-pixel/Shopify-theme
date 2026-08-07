# PERSONA 1 — Cold click from Instagram

**Who:** Never heard of CROOKSLDN. Tapped a story link, landed straight on a product page. On the tube, one hand, half-attention.
**Wants to know, in order:** what is this · what does it cost · does it come in my size · is this shop real · when would it arrive.
**Conditions:** 390 × 844, DPR 3, Slow 4G (1.6 Mbps / 150 ms), 4× CPU. Cold browser — no cookies, no localStorage. Landed on `/products/3-clives-tee`.
**Measured page behaviour:** TTFB 867 ms · FCP 1,684 ms · **LCP 14,252 ms** · **CLS 0.3528** · load event 14,499 ms.

> Elapsed times below are from the instrumented walkthrough and include deliberate reading pauses. The page's own load milestones are the line above.

---

### Step 1 — First paint, 1.5 s after tapping the link
**Screenshot:** screens/p1-step1.png
**On screen:** `FREE UK SHIPPING * — 24HR DISPATCH AVAILABLE` · `14 PRODUCTS CURRENTLY ONLINE` · `SEARCH  BAG [0]  LIGHT MODE  MENU` · `← CATALOGUE  PRODUCT 09 / 14  T-SHIRT` · `PHOTO 1 OF 2` · product title, **£25.00**, size row, `IN STOCK`. No product image yet — the hero frame is drawn but empty.
**Goal right now:** work out what I'm looking at.
**Felt experience:** Genuinely striking. It doesn't look like a Shopify store, it looks like a terminal, and the price is right there without me doing anything. I don't know what this brand is yet but I can tell someone made it on purpose.
**Blocked by:** nothing.
**Would they continue?** yes — the first screen does its job.
**Seconds elapsed:** 3.0

### Step 2 — The image finally arrives
**Screenshot:** screens/p1-step2.png
**On screen:** Same, plus the shirt. The cookie consent panel now occupies the bottom 338 px — **40% of the screen**.
**Goal right now:** see the actual product.
**Felt experience:** That took ages. The frame sat empty for what felt like forever and then the shirt appeared all at once. And now there's a cookie wall over the bottom of everything.
**Blocked by:** the hero is a **635 KB PNG** — the single largest asset on the site — because the master was uploaded as `9dbaee36…_webp.webp` and Shopify won't transcode a file whose name ends in `.webp`. LCP 14.3 s.
**Would they continue?** hesitant — on a real tube commute this is where a fair number of people back out.
**Seconds elapsed:** 19.7 (page load event: 14.5 s)

### Step 3 — A full-screen game takes over the page
**Screenshot:** screens/p1-step3.png
**On screen:** `ACCESS BREACH DETECTED` · `CRACK THE CUFFS` · `ESCAPE WITH A PRIVATE DISCOUNT` · `BEGIN`. A 100%-viewport overlay at z-index 2,147,483,647. Scroll is locked (`documentElement.style.overflow = 'hidden'`). Underneath it, the cookie banner is still there.
**Goal right now:** read the product.
**Felt experience:** I haven't even worked out what this shop is and it's asking me to play a game. I came from a story about a t-shirt. I don't want a puzzle, I want to know if it comes in medium.
**Blocked by:** `snippets/crack-the-cuffs.liquid` — a 3-second timer rendered in `layout/theme.liquid:161`, so it fires **on every template, not just the homepage**. Two stacked overlays before the product has been read.
**Would they continue?** hesitant — the concept is on-brand, the timing is not.
**Seconds elapsed:** 26.2

### Step 4 — Popup dismissed
**Screenshot:** screens/p1-step4.png
**On screen:** The product, at last. Title, **£25.00**, `SIZE XS S M L XL BLACK WHITE`, `IN STOCK`, and a sticky bar pinned to the bottom reading `3 CLIVES TEE £25.00 · XS · BLACK  ADD TO BAG`.
**Goal right now:** price and size.
**Felt experience:** Right — that's better. Price is obvious, sizes are right under it, and there's a buy button following me down the page. This bit is actually good.
**Blocked by:** nothing, once the overlays are gone.
**Would they continue?** yes.
**Seconds elapsed:** 27.4 · 1 tap

### Step 5 — Finding the size
**Screenshot:** screens/p1-step5.png
**On screen:** Size row measured at 746 px from the top of the document — **inside the first viewport, no scrolling needed**. Seven buttons: XS S M L XL BLACK WHITE. Each 58 × 52 px.
**Goal right now:** is there a medium.
**Felt experience:** Found in about two seconds. Easily inside the 15-second limit. Slightly odd that colour and size are in one undifferentiated row — XL sits next to BLACK with nothing telling me they're different kinds of choice.
**Blocked by:** nothing.
**Would they continue?** yes.
**Seconds elapsed:** 27.8

### Step 6 — Tapped M
**Screenshot:** screens/p1-step6.png
**On screen:** M highlights in purple; sticky bar updates.
**Goal right now:** confirm it's available.
**Felt experience:** Immediate, no lag, and the bar at the bottom updated so I can see what I've picked. Fine.
**Blocked by:** nothing.
**Would they continue?** yes.
**Seconds elapsed:** 29.9 · 2 taps

### Step 7 — Hunting for the delivery cost
**Screenshot:** screens/p1-step7.png
**On screen:** Scrolled 1.58 viewports. Visible: `STATEMENT OF PROVENANCE +` · `MEASUREMENTS −` · `CM  IN` · the measurement table. **No shipping information anywhere on screen.** The `FREE UK SHIPPING` announcement scrolled off the top a full screen ago.
**Goal right now:** how much is postage and when does it come.
**Felt experience:** I've scrolled past a spec list and a measurement chart and there's still nothing about delivery. I saw something about free UK shipping at the very top but it's gone now and I'm not sure if it applied to this or was just a banner.
**Blocked by:** shipping is inside a **collapsed** accordion named `CHAIN OF CUSTODY`. The label doesn't contain the words shipping, delivery or postage.
**Would they continue?** hesitant.
**Seconds elapsed:** 31.7

### Step 8 — Opened CHAIN OF CUSTODY
**Screenshot:** screens/p1-step8.png
**On screen:** `01 LOGGED — Orders are logged same day. Dispatch within 24 hours, Monday to Saturday.` `02 DISPATCHED — Shipped with Royal Mail Tracked. Free UK shipping on every order.` `03 IN TRANSIT — Tracking issued by email. UK 1–2 working days. International 7–14 working days.` `04 RELEASED — You have 14 days from delivery to return unworn goods with tags attached.`
**Goal right now:** decide.
**Felt experience:** That's a really good answer, and it's written in the brand's voice without being coy about the facts. Free UK shipping, 1–2 days, tracked, 14 days to send it back. If I'd seen that at the top I'd have bought already. Why is it hidden behind a name that doesn't say shipping?
**Blocked by:** nothing — but it took a scroll of 1.7 viewports and a tap on a deliberately-obscure label to reach the single most persuasive block of copy on the page.
**Would they continue?** **yes** — and this is the step that converts them.
**Seconds elapsed:** 32.8 · 3 taps

---

## Verdict

**Would buy — but only if they get past the first 25 seconds.**

What works: the first viewport passes every one of this persona's tests. Price, size, stock and a persistent ADD TO BAG are all visible without a scroll. The terminal aesthetic reads as deliberate, not broken, within about a second. The CHAIN OF CUSTODY copy is genuinely excellent — it answers "is this real" and "when does it arrive" better than a trust badge ever would.

What loses them, in order of cost:
1. **14.3 s to see the product** on a 635 KB PNG hero that should be ~180 KB.
2. **A full-screen game popup on a product page**, 3 s after arrival, scroll locked.
3. **A cookie banner eating 40% of the screen** and covering the sticky ADD TO BAG bar.
4. **CLS 0.353** — the buy panel jumps 28 px at 1.84 s, as the VT323 font swaps in.
5. **The best trust copy on the site is behind a collapsed accordion called CHAIN OF CUSTODY.**

Notably, *none of the top five is caused by the austere design.* Four are loading and overlay problems; the fifth is a naming choice that could be fixed without changing a single visual rule.
