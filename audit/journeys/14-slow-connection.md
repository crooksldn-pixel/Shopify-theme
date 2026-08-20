# 14 — Kez, on the bus with one bar, saw the brand on TikTok twenty minutes ago

**Device:** 360×800 on an older Android, congested 4G, one bar · **Goal:** find out whether the thing from the video is real and what it costs · **Mood:** curious, thumb already moving, zero patience — if it makes me wait I'm back on the app

---

### Step 1 — Opened the link from the video. First second: nothing.
**Did:** Tapped the link. Held the phone up. Waited.
**Got:** A black screen. Completely empty — no logo, no strip of text, no spinner, nothing to say anything was coming.
**Expected:** A shop. Some kind of spinner at the very least.
**Felt:** This is the bit nobody who built it will ever see. It isn't a white flash you barely notice, it's a black rectangle that sits there. And because the actual site is also black, there is no way to tell "still coming" from "arrived and it's rubbish". About a second, which doesn't sound like anything until you're the one holding the phone on a bus. **Would I have thought it was broken?** Not yet — but I was already deciding.
**Next:** continued

### Step 2 — Three seconds in: all the words, none of the clothes
**Did:** Kept holding it.
**Got:** Everything textual arrived in one go, and it arrived properly: the handcuffs logo, `CROOKSLDN`, `OWN THE STREETS™`, a purple `CATALOGUE` button, `> 12 PRODUCTS AVAILABLE TO PURCHASE`, and below it `CATALOGUE  12 ITEMS` with `FLAT  ON MODEL`, `OUTLINE`, `ALL  T-SHIRT  DENIM  SWEATS  ACCESSORIES`. Scroll down and every product is there in words — `NO. 01  SWEATS  CHARCOAL CELLBLOCK CREWNECK  £50.00  AVAILABLE`. **But the pictures weren't there.** One picture out of the whole page. The register was a column of empty boxes with names and prices in them. (`audit/screens/14-arrive-3s.png`; on another go a few more had turned up by this point — `audit/screens/14-home-3s.png`)
**Expected:** Clothes. I came from a video of the clothes.
**Felt:** Two opposite things. The words being there this fast is genuinely good — I know what it is, I know it's £50, I know it's in stock, and I know it isn't a normal Shopify shop, all before the photos exist. Most sites give you a grey skeleton and tell you nothing. But I came off TikTok to *look at clothes*, and at three seconds there are no clothes. The other thing I noticed: the strip along the very top had two different sentences printed on top of each other, half-cut-off — `FREE UK SHIPPING OVER £20 — ORDER BY 18:00 FOR SAME-DAY DISPATCH` and `12 PRODUCTS CURRENTLY ONLINE` in the same place at the same time, unreadable. It does that on the product pages too. It's the first thing on the screen and for the first few seconds it's a mess. **Broken?** No — this is the point where I stopped worrying.
**Next:** continued

### Step 3 — Five seconds in: the one button I was reaching for got covered
**Did:** Read `CROOKSLDN`, read `OWN THE STREETS™`, moved my thumb towards the purple `CATALOGUE` button — the only actual thing to press on the screen.
**Got:** A grey `COOKIE CONSENT` sheet slid up and took the **bottom half of the phone**. Its top edge lands almost exactly on the top edge of that purple button — the button is not partly covered, it is *gone*. What's left above it is the logo, the header, and the two lines of the wordmark. (`audit/screens/14-cookie-over-cta.png`, `audit/screens/14-arrive-5s.png`, `audit/screens/14-home-5s.png`)

The wording: "We and our partners, including Shopify, use cookies and other technologies to personalize your experience, show you ads, and perform analytics, and we will not use cookies or other technologies for these purposes unless you accept them. Learn more in our Privacy Policy", then `Accept`, `Decline`, `Manage preferences`.
**Expected:** To press the button I was looking at.
**Felt:** This is the single worst piece of timing on the site. The button is live and readable at about two seconds. The sheet lands on it at about five. That is a three-second window where the site shows you one thing to do and then takes it away, and three seconds is *exactly* how long it takes to read two lines and decide. It's not that there's a cookie banner — everyone has one. It's that it waits until you've committed to the tap.
**Next:** hesitated

### Step 4 — Ten seconds in: identical
**Did:** Waited to see if anything else was coming.
**Got:** The same screen as at five seconds. Same sheet, same half a page behind it, same number of missing pictures. Nothing improved between five and ten. (`audit/screens/14-arrive-10s.png`, `audit/screens/14-home-10s.png`)
**Expected:** The photos to fill in.
**Felt:** Ten seconds is where I'd normally be gone. What kept me was that I could already read everything — I wasn't waiting to find out *what* the site was, only to be allowed to use it. Waiting for permission is a different, more annoying kind of waiting than waiting for a page. **Broken?** No. In the way. Different problem.
**Next:** continued

### Step 5 — Tapped where the button was. Got the words `COOKIE CONSENT`.
**Did:** Went for the purple `CATALOGUE` button anyway, because that's where my thumb was already going.
**Got:** My thumb landed on the heading `COOKIE CONSENT`. Nothing happened at all — no page change, no scroll, no acknowledgement. (`audit/screens/14-thumb-aim.png` is what I aimed at, `audit/screens/14-thumb-landed.png` is what was there when I got there.)
**Expected:** The products.
**Felt:** Out loud: *"I pressed the button, why am I reading about analytics."* This is the finding of the whole journey for me. I meant `CATALOGUE`. I got a paragraph about cookies. Same pixel, two seconds apart.

I gave it another go from scratch and got my tap in just before the sheet dropped — and the reward for winning that race was the page jumping down to the products and then the bottom half of them being swallowed by the sheet a moment later. `NO. 01` and `NO. 02` visible from the waist up, everything below cut off. (`audit/screens/14-tap-after.png`) So both ways round, the answer is the same: the first thing this site does when you try to use it is cover it up.
**Next:** hesitated

### Step 6 — Tapped `Decline`
**Did:** Hit `Decline`. Didn't read it. It was in the way.
**Got:** The sheet went. (`audit/screens/14-cookie-declined.png`)
**Expected:** To finally see the shop.
**Felt:** Credit where it's due — `Accept` and `Decline` are both real buttons, the same size, next to each other, and `Decline` isn't buried behind `Manage preferences`. One tap out. That's better than most.
**Next:** continued

### Step 7 — Two seconds of freedom, then the whole screen went black again
**Did:** Started to look at the products.
**Got:** The entire screen went to a black sheet: `CROOKSLDN: THE GETAWAY` — "Crack the cuffs. 10% off your first order — code sent by text. Attempts unlimited." with `RUN IT` and `NOT NOW`, and underneath, "One code per player. Code expires 20 minutes after you win." The close `×` is up in the **top-left** corner. (`audit/screens/14-overlay.png`)
**Expected:** Products.
**Felt:** *"Oh, come on."* Two full-screen interruptions back to back, and I still haven't looked at a single item of clothing. The second one arrived within about two seconds of me clearing the first — as if it had been queuing behind it. On a good connection you'd have browsed for a bit before this showed up and it might have felt like a nice bit of business; here it reads as the third thing standing between me and the shop.

And I'd have to be fair: the offer itself is decent and the writing is in the brand's voice, unlike the cookie sheet. But the `×` being top-*left* on a phone is wrong — my thumb goes top-right without asking me, and on a 360-wide screen the top-left corner is the furthest point from a right thumb. **This is where I nearly closed the tab.** What stopped me was that I'd already seen the prices in step 2 and wanted to check one thing.
**Next:** hesitated — genuinely close to gone

### Step 8 — Closed it, and the page moved under me
**Did:** Reached across for the `×`. Then flicked down towards the products.
**Got:** The sheet went (`audit/screens/14-overlay-closed.png`). The flick didn't land where I put it — I pushed the page down and it settled noticeably higher than where I'd left my thumb, then shifted again about a second later. The page also kept getting taller for a while after it looked finished — about another third of a screen appeared underneath, twice, after everything in front of me had stopped changing.
**Expected:** To stay where I put it.
**Felt:** Small, but it's the sort of thing that makes a phone feel cheap. You put the page somewhere and it argues with you.
**Next:** continued

### Step 9 — The register, finally, with pictures
**Did:** Scrolled the products properly.
**Got:** Two-across cards, each one `NO. 01  SWEATS` / photo / `CHARCOAL CELLBLOCK CREWNECK` / `£50.00` / `AVAILABLE`. Images in, white-outlined on black. (`audit/screens/14-register-filling.png`)
**Expected:** This, ten seconds ago.
**Felt:** This is the good bit and it's worth saying plainly: it looks like nothing else, the price and whether it's in stock are on every card without me tapping anything, and it stayed readable the whole way down. If this had been the second screen instead of the fifth I'd have been in a much better mood. The pictures do turn up as you scroll rather than all at once, so you're never staring at empty boxes for long once you're moving.
**Next:** continued

### Step 10 — Tapped a pair of jeans
**Did:** Tapped `NO. 05  DENIM  GREY WASH YARD JEANS  £60.00`.
**Got:** Black screen again for a beat over a second, then the product page.
**Expected:** The jeans.
**Felt:** Same black gap as the first time. Second time you know it's coming, so it bothers you less.
**Next:** continued

### Step 11 — Three seconds on the product page: the photo, the price, and a purple `ADD TO BAG`
**Did:** Looked.
**Got:** `← CATALOGUE`, `PRODUCT 05 / 12`, `DENIM`, the jeans photographed flat, `PHOTO 1 OF 1`, `GREY WASH YARD JEANS`, `£60.00`, and the word `SIZE` — and then, pinned across the bottom of the screen, a bar reading `GREY WASH…  £60.00` with a **purple `ADD TO BAG`** and `CHECKOUT NOW` next to it. (`audit/screens/14-pdp-3s.png`, `audit/screens/14-pdp-earlyadd.png`, `audit/screens/14-btn-add.png`)
**Expected:** Exactly this. This is a good product page and it got there quickly.
**Felt:** Better than the homepage by a mile. Picture, name, price, buy button, all inside three seconds, no scrolling. Honestly impressive on this connection. **Broken?** Not for a second.

One thing though — the sizes. `SIZE` is the last word I can see before that bottom bar starts, and the row of `XS S M L XL` is directly underneath it, hidden behind the bar. At the top of the page the only buy control you can see is the one in the bar.
**Next:** continued

### Step 12 — Five seconds: the button changed into a different button
**Did:** Went for `ADD TO BAG`.
**Got:** By the time I got there, the same rectangle in the same place was a **greyed-out, dead `SELECT A SIZE`**. Not moved. Not disabled-looking-but-still-purple. Swapped. (`audit/screens/14-pdp-thumb-landed.png`, `audit/screens/14-btn-select.png` — compare with `14-btn-add.png`, identical position)
**Expected:** To add some jeans to a bag.
**Felt:** *"It said add to bag."* This is worse than the cookie sheet, because the cookie sheet at least announced itself. This one is the same shape, the same size, in the same spot, and it quietly becomes something else while you're reaching for it. On a fast phone the swap happens before you've seen the first version. On mine it sat there looking live and pressable for a good couple of seconds.
**Next:** continued

### Step 13 — Pressed it anyway, in the window. Nothing at all happened.
**Did:** Went straight for the purple `ADD TO BAG` the instant it appeared, no hesitation.
**Got:** The phone didn't respond to the press for about two seconds — that dead patch where you don't know if it registered. Then: nothing. No item added, `BAG [0]` still `BAG [0]`, no message, no error, no jump to the sizes, no "pick a size first". Silence. (`audit/screens/14-live-add.png`, `audit/screens/14-live-add-6s.png`)
**Expected:** Either the jeans in my bag, or being told what I'd done wrong.
**Felt:** The good news, and it is genuinely good news, is that it didn't sneak a random size into my bag — I checked, the bag was empty. The bad news is that pressing the most important button on the page produced no reaction whatsoever. I pressed it twice before I accepted that it wasn't going to do anything, and on a slow phone you can't tell "that did nothing" from "that hasn't caught up yet". A shopper less stubborn than me leaves here believing the buy button is broken.
**Next:** continued

### Step 14 — Went looking for the sizes and had to scroll to find them
**Did:** Scrolled down a bit, because whatever the button wanted was clearly further down.
**Got:** `SIZE`, then `XS  S  M  L  XL`, then `SIZE GUIDE`, `Order before 18:00 and it ships today (Mon–Sat)` and `> Ordered now — leaves tomorrow`.
**Expected:** To have seen the sizes without hunting.
**Felt:** Once you scroll it's obvious and the sizes are big enough to hit properly. But the layout put the *word* `SIZE` on screen and the actual sizes behind the bottom bar, which is the one arrangement guaranteed to make you press the wrong thing first. The dispatch line is a nice touch — "leaves tomorrow" is a real answer, not marketing.
**Next:** continued

### Step 15 — Tapped `M`, then `ADD TO BAG`. This bit was excellent.
**Did:** Tapped `M`. Then the big purple `ADD TO BAG`.
**Got:** `M` went purple and outlined straight away, `IN STOCK` appeared under the sizes, and both buy buttons changed from the grey `SELECT A SIZE` to a live `ADD TO BAG`. I pressed it and within about a second the bottom bar said `> Added — 1 in bag` and the header counter flipped to `BAG [1]`. (`audit/screens/14-size-m.png`, `audit/screens/14-bag-1s.png`)
**Expected:** A wait, honestly.
**Felt:** *That* was quick. Quicker than everything else on the site. And the confirmation is in the bottom bar — right where my thumb already was — not up at the top where I'd have missed it. Whoever did that bit understood phones. This is the best moment of the visit by a distance.
**Next:** continued

### Step 16 — Went to the bag, and paid for it in waiting
**Did:** Tapped `BAG [1]`.
**Got:** A long wait — long enough that I checked the signal bar and then checked whether the tap had registered at all. The phone went completely unresponsive partway through; nothing on screen moved for several seconds. Then the bag: `> £10.00 to free Tracked 24` with a purple bar most of the way across, `✓ TRACKED 48 FREE` and `TRACKED 24 FREE`, then `Cart 1`, the jeans with `M` under the name and `£60.00`, a quantity stepper, `Estimated total  £60.00 GBP`, "Pay in 3 interest-free instalments of £20.00 with shop". (`audit/screens/14-bag-final.png`)
**Expected:** After the last few pages — a wait.
**Felt:** Worst wait of the whole visit, and it comes at the point where I'm most committed and least willing to be messed about. If I'd been getting off the bus I'd have lost it. But the page it eventually gives you is good: `£10.00 to free Tracked 24` is a real, specific reason to add something else, and the size is written next to the name so I don't have to trust myself. The bag itself looks like a normal shop rather than the black terminal, which is a jolt after everything before it, but I care less about that than about it being clear.
**Next:** stopped there — didn't go into paying

---

## Outcome

**Bought / didn't:** Got as far as £60 of jeans sitting in the bag in the right size, and stopped there — not because of anything at the end, but because by then I'd used up the goodwill I'd arrived with. I'd finish it later at home, on wifi, which for a TikTok impulse means probably never.

**Total time:** Roughly four minutes, of which about the first forty seconds were spent getting things off the screen rather than looking at clothes.

**Worst moment:** Step 5. I reached for the purple `CATALOGUE` button — the only thing to press on the screen — and by the time my thumb arrived the same spot was the words `COOKIE CONSENT` and nothing happened. Runner-up, and only just: the bottom-bar button that says `ADD TO BAG` in purple for a couple of seconds and then turns into a dead grey `SELECT A SIZE` in exactly the same place, and gives you nothing at all if you hit it in between. *"It said add to bag."*

**Best moment:** Tapping `M` and then `ADD TO BAG` and getting `> Added — 1 in bag` right there under my thumb inside a second. Close second: everything on the homepage being **readable** at three seconds — names, prices, `AVAILABLE` on every item — before a single photo existed. Most shops give you a grey skeleton and no information at all; this gives you the whole catalogue in words. On a bad connection that is a real advantage and it should be protected.

**Would they come back?** Yes, but not soon and not from a link. The clothes and the look are worth coming back for — I remembered the name, which is more than I can say for most things I tap out of a video. What I'd remember alongside it is a site that made me fight two full-screen panels before it let me look at anything.

**One thing that would have changed the outcome:** Stop things arriving on top of a thumb that's already moving. Two specific changes, both small: put the cookie sheet up **immediately**, before the purple `CATALOGUE` button is readable, instead of three seconds after it — if it's there before I've decided to tap, it costs me one tap and no temper; and never let the bottom bar say `ADD TO BAG` until it means it. Show it as `SELECT A SIZE` from the very first moment, or make the early press do something honest — scroll me to the size row — instead of nothing.
