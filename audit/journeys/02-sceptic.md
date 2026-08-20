# 02 — Dean, likes the jeans, has been burned by a small label before, and won't type a card number on faith

**Device:** mobile 390×844, ordinary 4G · **Goal:** find contact details, a returns policy, shipping info, and any sign that other people have actually bought here — before the card comes out · **Mood:** interested but braced. Last time it was £45 of "premium" hoodie that never arrived and an email address that bounced.

---

### Step 1 — Landed on the homepage and let it draw itself in
**Did:** Opened the link cold and waited.
**Got:** About four and a half seconds of near-nothing, then it all arrived together: a thin grey strip reading `FREE UK SHIPPING OVER £20 — ORDER BY 18:00 FOR SAME-DAY DISPATCH`, a white handcuffs mark, `CROOKSLDN`, `OWN THE STREETS™`, one purple `CATALOGUE` button on near-black. Then a `COOKIE CONSENT` panel slid up and took the bottom 40% of the phone. (`audit/screens/02-01-arrival.png`)
**Expected:** A shop, and probably a popup demanding my email before I'd seen a single product.
**Felt:** It doesn't look like a scam store and it doesn't look like a Shopify store, which are two different reassurances and I clocked both. The cookie panel is the odd bit — it's in the site's typeface but Shopify's voice: "We and our partners, including Shopify, use cookies and other technologies to personalize your experience, show you ads, and perform analytics…". Seeing the word Shopify in there was, honestly, the first thing that made me relax slightly. A platform is a platform.
**Next:** continued

### Step 2 — Waited to see what else was going to jump me
**Did:** Sat on the homepage for a full quarter of a minute without touching anything, because in my experience the email-capture modal turns up about now.
**Got:** Nothing. The top strip flipped from the shipping line to `12 PRODUCTS CURRENTLY ONLINE` and back. No overlay, no popup, no "WAIT! 10% OFF". (`audit/screens/02-02-overlay.png`)
**Expected:** A modal.
**Felt:** Good, and I want to be clear that this is not a small thing for someone like me. Nothing grabbed at me. That buys a shop about thirty seconds of extra patience before I start looking for reasons to leave.
**Next:** continued

### Step 3 — Declined cookies
**Did:** Tapped `Decline`.
**Got:** Panel gone. `Accept` and `Decline` are the same size, side by side, both plain buttons, with `Manage preferences` underneath as a link. (`audit/screens/02-03-home-clear.png`)
**Expected:** Decline buried inside "Manage preferences" like everywhere else.
**Felt:** They didn't try it on. Noted.
**Next:** continued

### Step 4 — Went straight to the bottom of the page, before looking at a single product
**Did:** Thumb-flicked to the footer. This is what I always do. If a shop is going to be a problem, the footer tells you in about four seconds — either there's a proper set of links down there or there's nothing.
**Got:** A single tall column: `SHOP` (NEW, TEES, DENIM, SWEATS, ACCESSORIES), `INFORMATION` (QUESTIONS, TERMS, SHIPPING, REFUNDS, TRACK ORDER), `CONTACT` (INSTAGRAM, TIKTOK, EMAIL), `GAME` (Play CROOKSLDN: The Getaway). Base line: `EVIDENCE TERMINAL V0.2 // CROOKSLDN // OWN THE STREETS™ // © 2026`. (`audit/screens/02-04-footer.png`)
**Expected:** Either five links or fifty.
**Felt:** Encouraging at a glance. `SHIPPING`, `REFUNDS`, `TERMS`, `TRACK ORDER` all sitting there in the open — that's four of the things a dodgy shop hides, not hidden. The headings are purple and the links grey, so `CONTACT` reads as a heading you can tap. I'll come back to that.
**Next:** continued

### Step 5 — Tapped the £60 jeans
**Did:** Scrolled back up and tapped `NO. 03 DENIM BLUE WASH OG JEANS £60.00 AVAILABLE`.
**Got:** A product page in about three and a half seconds. `PRODUCT 03 / 12`, `DENIM`, `PHOTO 1 OF 2`, `BLUE WASH OG JEANS`, `£60.00`, a row of size buttons `XS S M L XL`, `Select Size`, `SIZE GUIDE`, then two lines I did not expect: `Order before 18:00 and it ships today (Mon–Sat)` and `Ordered now — leaves tomorrow`. Then four closed accordions and a sticky bar at the bottom. (`audit/screens/02-05-pdp-top.png`, `audit/screens/02-06-pdp-full.png`)
**Expected:** A photo, a price, a size dropdown, and nothing else useful.
**Felt:** **Shipping info, item one of four, before I'd tapped anything.** Not a badge, not an icon — a sentence telling me when the thing leaves the building. And the strip up top flipping to `12 PRODUCTS CURRENTLY ONLINE` while this page says `PRODUCT 03 / 12` means the catalogue is twelve items and they're not pretending otherwise. A shop with twelve products and no lies about it is a more believable object than a shop with four thousand.
**Next:** continued — **shipping: found, 0 taps**

### Step 6 — Opened the last accordion first, because of what it's called
**Did:** Ignored `SPECIFICATION`, `ITEM DESCRIPTION` and `MEASUREMENTS` and tapped `CHAIN OF CUSTODY — SHIPPING & RETURNS`.
**Got:** Four numbered steps. `01 LOGGED` — "Orders placed before 18:00 are dispatched the same day, Monday to Saturday. After 18:00, the next dispatch day." `02 DISPATCHED` — "Shipped with Royal Mail Tracked. Free UK shipping over £20, and free Tracked 24 over £70." `03 IN TRANSIT` — "Tracking issued by email. UK 1–2 working days. International 7–14 working days." `04 DELIVERED` — "You have 14 days from delivery to return unworn goods with tags attached. Return postage is yours unless we sent the wrong thing or it arrived faulty. Start a return by email: crooksldn@gmail.com." (`audit/screens/02-b-acc-chain-of-custody.png`)
**Expected:** Flannel. A cute in-character paragraph about evidence lockers that tells me nothing.
**Felt:** This is the best thing on the site and I'd say so out loud. One tap, without leaving the jeans, and I've got the courier, the cutoff, the delivery window, the returns deadline **and** who pays return postage — which is the bit shops lie about by omission. It tells me the bad news ("Return postage is yours") in the same breath as the good news. Nobody planning to take my sixty quid and vanish volunteers that. It's also the only place on the whole site where a contact address and a returns rule sit in the same eyeful.
**Next:** continued — **returns: found, 1 tap. Contact: technically found, 1 tap, but I had to already be inside an accordion called "chain of custody" to get it.**

### Step 7 — Opened the other three, because detail is evidence
**Did:** Tapped `SPECIFICATION`, `ITEM DESCRIPTION`, `MEASUREMENTS`.
**Got:** `FABRIC 14oz denim` · `CUT OG straight, mid rise` · `ORIGIN Made in Portugal` · `CARE Cold wash inside out. Hang dry.` The description: "OG jeans — blue wash, for the record. 14oz denim, OG straight cut, mid rise. Structured, not baggy. Made in Portugal." And a real measurements table with a `CM`/`IN` toggle — XS 76.2cm waist through XL 96.5cm. (`audit/screens/02-b-acc-specification.png`, `audit/screens/02-b-acc-measurements.png`)
**Expected:** "Premium quality fabric. Comfortable fit."
**Felt:** Specific enough to be checkable, which is the whole point. "14oz" and "Made in Portugal" are claims you can be caught on; "premium quality" isn't. The measurements are clean converted inches (76.2 / 81.3 / 86.4 — that's 30/32/34), which reads to me like someone actually working off a garment rather than a random number generator. One sloppy line: the note above the table says "WAIST, **CHEST** AND LEG MEASUREMENTS ARE TAKEN AROUND THE GARMENT" and there is no chest column on a pair of jeans. Boilerplate. Tiny, but I notice boilerplate.
**Next:** continued

### Step 8 — Went looking for reviews on the product page. Scrolled the whole thing.
**Did:** Scrolled the jeans page top to bottom twice, looking for stars, a rating number, a "customers also said", a photo of a real person, anything.
**Got:** `MORE FROM THIS DROP` with three other products, then the footer. No reviews. No rating. No count. Nothing. (`audit/screens/02-18-pdp-all-open.png`)
**Expected:** At minimum a fake-looking widget with 4.8 and 212 reviews.
**Felt:** First proper pause of the visit. Not alarm — I'd noticed by now that there are no countdown timers, no "9 people are viewing this", no scarcity nonsense either. So the absence didn't read as *hidden*, it read as *not installed*. But it does leave a hole, and the hole isn't "will they rob me", it's "do these actually fit anyone and is the denim any good". Nothing on this site can answer that.
**Next:** hesitated

### Step 9 — Back to the footer for contact details, and tapped the word CONTACT
**Did:** Flicked to the bottom of the jeans page and tapped `CONTACT` — purple, capitalised, spaced out, sitting above three links exactly like `INFORMATION` sits above five.
**Got:** Nothing. Absolutely nothing happened. It isn't a link, it's a heading. (`audit/screens/02-08-pdp-footer.png`)
**Expected:** A contact page.
**Felt:** *"Is this thing broken or am I?"* I tapped it twice more to check it wasn't my thumb. A wasted tap is a small thing on a good day; on a page where I am specifically hunting for evidence that a human exists at the other end, tapping the word CONTACT and getting silence is the single worst-timed dead end this site could have.
**Next:** hesitated

### Step 10 — Tapped EMAIL underneath it instead
**Did:** Tapped `EMAIL`, the third link in that column.
**Got:** The browser tried to hand me to my mail app with a blank message. No address shown on the page — the footer says the word `EMAIL` and nothing else. Nowhere in that column is an actual address printed where I can read it. (`audit/screens/02-08-pdp-footer.png`)
**Expected:** To be able to *read* an email address.
**Felt:** Wrong way round. I don't want to write to them, I want to see who they are. An address I can look at tells me something — is it a domain, is it a gmail, is it info@somethingelseentirely. Being thrown into a compose window tells me nothing and costs me the tab. I backed out.
**Next:** hesitated

### Step 11 — Opened MENU and took the obvious route: CONTACT
**Did:** Tapped `MENU`, then `CONTACT` in the panel. Two taps, and the most obvious two taps on the site.
**Got:** A menu listing `SHOP / ALL / NEW / TEES / DENIM / SWEATS / TRACKSUITS / ACCESSORIES / TRACKING / QUESTIONS / TERMS / CONTACT / PLAY CASE:001 NOW` — then a page that is a **cream-white slab** between the black header and the black footer. A heading `CONTACT` in a bold typeface I hadn't seen anywhere else on the site, then four plain boxes: `Name`, `Email*`, `Phone`, `Comment`, and a black `Submit`. (`audit/screens/02-10-menu-open.png`, `audit/screens/02-11-contact-page.png`, `audit/screens/02-20-contact-form-full.png`)
**Expected:** An email address, a company name, a location, some indication of how long they take to reply.
**Felt:** This is where I nearly closed the tab, and I want to be exact about why. It isn't that it's a form. It's that **there is not one word on it.** No address. No name. No "we reply within X". No town. Nothing that says a person exists. It's four boxes and a Submit, and it's in a completely different colour and a completely different typeface from every other page — after ten minutes of black terminal I've been dropped onto what looks like a half-built page from a different website. Out loud: *"who am I even emailing?"* Everything the last ten minutes bought this brand, this page spent.
**Next:** hesitated — very close to gave up

### Step 12 — Went to REFUNDS instead, straight from the footer
**Did:** Scrolled down and tapped `REFUNDS`. One tap.
**Got:** A real page in the site's own black and monospace. `REFUND POLICY` / "Returns & Refunds" / "We want you in the right fit. If something's not right, we'll sort it." Then: "**You have 14 days from delivery to return or exchange any unworn item with tags on. Return postage is paid by you** — that covers a change of mind, the wrong size, a swap, or any other reason of your own. There is no fee for a UK size swap itself, and we cover the postage sending the new size out to you." And at the bottom, finally, the thing I'd been hunting: "**How: email crooksldn@gmail.com or DM @crooksldn with your order number. We reply within 1–2 working days;** approved refunds land on your original payment method within 5–7 days." (`audit/screens/02-10-refund-policy.png`)
**Expected:** Thirty days, five clauses of hedging, and no email.
**Felt:** Recovered a lot of ground in one tap. It's short, it's in English, it tells me who pays and how long they take to answer. The size-swap line is genuinely generous — they cover sending the replacement out. **This is where I actually got contact details**, on the returns page, two thirds of the way down, having failed at both places labelled contact.
**Next:** continued — **returns: found, 1 tap. Contact: found properly, but on the fourth attempt.**

### Step 13 — Read the return address twice
**Did:** Re-read one line: "For returns please return to: **Oairo Uk Office, Bourne end Business Park, Bourne End, Buckinghamshire, United Kingdom, SL8 5AS.**"
**Got:** That, as written.
**Expected:** CROOKSLDN's name on the address.
**Felt:** Two hits at once. Good: there is a real UK address and a real postcode, which is more than the last lot that took my money had. Bad: it's a company I've never heard of called "Oairo", and "Bourne end" is written with a lower-case e in the middle of a capitalised address. Combined with a **gmail.com** address rather than anything@crooksldn.com, the picture I'm forming is one or two people and a shared unit — which is *fine*, plenty of good small labels are exactly that, but it is not the picture the rest of the site is painting, and unproofread small print is the exact texture of the site that burned me.
**Next:** continued

### Step 14 — Tapped SHIPPING from the footer
**Did:** One tap on `SHIPPING`.
**Got:** "Free UK shipping over £20, and free Tracked 24 over £70. Under that: standard £3, Tracked 24 £4.99." … "Order before 18:00 (Mon–Sat) and it goes out the same day" … "Once dispatched: UK 1–2 working days, international 7–14." … "Heading overseas? Any import duties your country charges on arrival are set by local customs and aren't included at checkout — just so there's no surprise on the doorstep." … "Lost or damaged? That's on us to sort." (`audit/screens/02-11-shipping-policy.png`)
**Expected:** The same numbers I'd already been given on the product page.
**Felt:** And it *is* the same numbers, which is the point — I'd been told 1–2 working days three times now by three different pages and they all agreed. Consistency is the cheapest trust there is and most small shops fail it. The customs line is the sort of thing you only write if you've had the argument before.
**Next:** continued — **shipping: confirmed, 1 tap**

### Step 15 — Went hunting for proof in earnest: FAQ, then terms, then search
**Did:** `QUESTIONS` from the footer, opened every returns and delivery question. Then `TERMS`. Then the search box, where I typed `reviews`.
**Got:** Fourteen questions, all closed by default, grouped `DELIVERY / SIZING / RETURNS AND REFUNDS / ORDERS AND PAYMENT`, and every one I opened answered properly — "You have 14 days from delivery to tell us, and 14 days from then to post it back, unworn and with tags attached. Return postage is yours"; "we will open a courier investigation. Royal Mail take up to 10 working days to complete one." The terms page has nine numbered clauses ending `09 CONTACT — Email crooksldn@gmail.com or DM @crooksldn with your order number. We reply within 1–2 working days.` Search for `reviews` returned: `SEARCH: REVIEWS` / `0 RESULTS` / `NO ITEMS IN THE REGISTER MATCH THAT QUERY.` (`audit/screens/02-13-faq-open.png`, `audit/screens/02-14-terms.png`, `audit/screens/02-23-search-reviews.png`)
**Expected:** Somewhere, one testimonial. One "as featured in". One customer photo.
**Felt:** The written stuff keeps getting better — "Drops are for people, not scripts" in the cancellation clause made me laugh, and "we would rather pack every order properly than promise a cutoff we cannot hold" is a sentence a human wrote about their own shop. But on my fourth thing I have found **nothing**. No review, no rating, no count of orders, no name of a single other customer, no photo of anyone wearing these. The only outward evidence offered anywhere is `INSTAGRAM` and `TIKTOK` in the footer, and following either means leaving the shop to go and check whether the shop is real.
**Next:** continued — **proof other people have bought here: gave up, after five separate looks**

### Step 16 — Checked the tracking page, on the theory that it might imply orders exist
**Did:** Tapped `TRACK ORDER`.
**Got:** `CROOKSLDN PROPERTY TRANSFER NETWORK` / `> CHAIN OF CUSTODY DATABASE ONLINE` / `IDENTIFICATION REQUIRED` — "Order records are released to the account they were filed under. Sign in to view the chain of custody for your orders." and `SIGN IN`, with a line under it: "NO ACCOUNT? THE TRACKING LINK IN YOUR DISPATCH EMAIL OPENS YOUR ORDER WITHOUT ONE." (`audit/screens/02-22-tracking.png`)
**Expected:** A box to paste an order number into.
**Felt:** Fair enough, and the no-account line is a decent thing to say. But it's a locked door, which is what I'd expect, and it tells me nothing about whether anyone has ever walked through it.
**Next:** continued

### Step 17 — Picked M, added to the bag, and looked at the cart
**Did:** Tapped `M` (the row changed from `Select Size` to `IN STOCK` and the button from `SELECT A SIZE` to `ADD TO BAG`), tapped `ADD TO BAG`, then opened the bag. A small line appeared under the button: `Added — 1 in bag View bag`.
**Got:** A cart in the site's own black. A purple progress bar across the top: `> £10.00 to free Tracked 24`, with `✓ TRACKED 48 FREE` on the left and `TRACKED 24 FREE` on the right. Then the jeans with a real photo, `Size: M`, `£60.00`, a quantity stepper, `Discount +`, `Estimated total £60.00 GBP`, "Pay in 3 interest-free instalments of £20.00 with **shop**", "Duties and taxes included. Shipping is calculated at checkout." and three buttons: a purple `Check out`, a blue **Shop Pay**, and a white **G Pay**. (`audit/screens/02-24-size-m.png`, `audit/screens/02-26-cart.png`)
**Expected:** A cart.
**Felt:** And *there* is my proof, sort of. Not proof that other people have bought — proof that I'm not alone if it goes wrong. Shop Pay and Google Pay are third parties with a complaints process, and they don't hand those buttons to a shop that doesn't exist. The carriage bar telling me I'm £10 off free Tracked 24 is also the first thing all visit that felt like it wanted more money from me, and even that was a plain sentence rather than a countdown.
**Next:** continued

### Step 18 — Tapped Check out and stopped at the card field
**Did:** Tapped `Check out`. Waited about twelve seconds.
**Got:** A standard white Shopify checkout on **crooksldn.com** — their own domain, not a myshopify address. `CROOKSLDN` at the top, `Order summary £60.00`, `Express checkout` with **Shop Pay**, **PayPal** and **Google Pay** side by side, then `Contact`, `Delivery` with `United Kingdom` already selected, and further down `Payment` — "All transactions are secure and encrypted." — `Credit card +5`, `Klarna`, `Shop Pay`, `PayPal`. Footer links: `Refund policy · Shipping · Privacy policy · Terms of service · Cancellations · Contact`. (`audit/screens/02-27-checkout.png`, `audit/screens/02-28-checkout-bottom.png`)
**Expected:** Shopify checkout, and that's what I got.
**Felt:** This is the moment the reviews question stopped mattering. Own domain, platform checkout, PayPal on the front page of it. Two small things I still clocked: the `Keep me updated.` box under the email field is **already ticked** — I untick those on principle and I mildly resent having to — and it is faintly funny that the checkout footer has a working `Contact` link when the shop's own footer doesn't. I stopped here. I don't put card numbers into a label I met twenty minutes ago; I'd have gone back and paid with PayPal, precisely so I've got a lever.
**Next:** stopped at the payment step — deliberately, with the bag full

---

## Outcome

**Bought / didn't:** Didn't complete — walked to the payment step with the £60 jeans in the bag and stopped at the card field. But I'd have paid. Via **PayPal**, not card, and that distinction is the whole finding: the site got me to the point of paying, and the thing that closed it was the express-checkout row, not anything the site said about itself.

**The four things, counted, from standing on the £60 jeans page:**

| What I wanted | Where I looked first | Taps | Result |
|---|---|---|---|
| **Shipping info** | Didn't have to look — top strip, and under the size row | **0** | **Found.** `Order before 18:00 and it ships today (Mon–Sat)` before any tap; the full policy 1 tap away in the footer |
| **Returns policy** | Footer | **1** (`REFUNDS`) | **Found.** Also 1 tap without leaving the product page, inside `CHAIN OF CUSTODY` |
| **Contact details** | Footer — tapped `CONTACT` | **1 wasted** (dead heading), then `EMAIL` threw me out of the browser, then `MENU → CONTACT` (**2**) reached a form with no information on it. Got the actual address on the **fourth** attempt, on the refund policy page | **Found, badly.** 4 attempts. The email + reply time is 1 tap away inside `CHAIN OF CUSTODY` on the product page, but nothing tells you to look there |
| **Proof anyone else has bought** | Footer, product page, catalogue, FAQ, search | **Gave up after 5 looks** | **Not found.** Nothing. The only offer is Instagram/TikTok, which means leaving the shop |

**Total time:** About nineteen minutes, which is long, and most of the extra was the contact hunt.

**Worst moment:** Step 9 — tapping the word `CONTACT` in the footer and having nothing happen, then Step 11 landing on a cream-coloured page with `Name / Email* / Phone / Comment / Submit` and not one word of anything else. *"Who am I even emailing?"* Two routes both labelled CONTACT, and neither gives you a human. On top of that, the page that *does* say it properly — "Real people read every message, usually the same ones packing your order… Email — Crooksldn@gmail.com… We reply within 1–2 working days (Mon–Sat)" — exists on this site and **is linked from nowhere at all.** I only saw it by accident. The single best sentence anyone has written for a customer like me is on a page a customer like me cannot reach. (`audit/screens/02-15-contact-policy.png`, `audit/screens/02-21-contact-policy-full.png`)

**Best moment:** Step 6 — `CHAIN OF CUSTODY — SHIPPING & RETURNS` on the product page. One tap, no navigation, and it gave me the courier, the cutoff, the delivery window, the 14-day return deadline, **who pays return postage**, and an email address. Runner-up: fifteen seconds of sitting on the homepage and nothing popping up at me.

### Is having no reviews anywhere fatal, survivable, or actually fine?

**Actually fine — with one caveat, and only because of what stands in for them.**

Fine, first, because a five-star widget would be the least believable object on this page. This site has no countdown timer, no "17 people are viewing", no fake stock counter, no trust-badge strip. Against that consistency, a review carousel would stick out as the one thing that had been bought in rather than written, and I would trust it *less*, not more — I know exactly how those get filled. The absence of reviews here reads as *they haven't faked anything*, not as *nobody has bought this*, and that only holds because nothing **else** on the site is faked either. That's the trade, and I think it's the right one. If a single fake-urgency line ever appears on this site, the missing reviews immediately start looking like a cover-up instead of a principle.

Second, because reviews aren't actually what I came for. My question was "will these people take my sixty quid and disappear," and the things that answer that are a returns deadline with a number on it, a named UK return address with a postcode, a stated reply time, and a checkout I recognise. All four exist, and three of the four are one tap from the jeans.

**The caveat**, and it's real: reviews answer a *second* question that this site has no answer to at all — does the denim feel like £60, and do the sizes run true on an actual body. The measurements table is good and the spec is specific, but a table can't tell me the fit is right, and there is not one photograph of a human being wearing these anywhere on the site. On a £60 pair of jeans I'd have liked one voice that wasn't the brand's. I bought anyway. Someone less interested in the jeans wouldn't have.

**The strongest thing this site does to earn my trust:** the writing tells me the bad news without being asked. "Return postage is yours — change of mind, wrong size, a swap, any reason of your own." "Original shipping charges are not refunded." "We cannot refund or replace before that investigation closes." "Any import duties your country charges on arrival… aren't included at checkout — just so there's no surprise on the doorstep." Every one of those is a sentence that costs the shop something, written plainly, before I asked. Shops that are about to rob you write the opposite of that. It's more convincing than any badge, and it's more convincing than reviews would have been.

**The weakest:** the contact route, in three compounding parts. The footer's `CONTACT` is a dead heading that swallows a tap. `MENU → CONTACT` — the most obvious two taps on the site — reaches an unbranded cream form with no email, no name, no address and no reply time, and it looks like it belongs to a different website. And the page that carries the actual reassurance is orphaned. For a shopper whose entire question is "is there a human here", the site's answer is: yes, but only if you happen to open an accordion called *chain of custody*, or read to the bottom of the refund policy.

**Would they come back?** Yes — and I'd come back knowing to read the product page's own accordion rather than trusting anything labelled contact. That's a shame, because the accordion is excellent and the contact page is the first thing anyone like me will try.

**One thing that would have changed the outcome:** print the email address and the reply time as readable text in the footer's `CONTACT` column — `crooksldn@gmail.com` and `REPLY IN 1–2 WORKING DAYS` as two grey lines where the word `EMAIL` currently sits, with the heading pointing at the contact page. It's the first place I looked, it's already the right column, and it would have answered my first question in **zero taps** instead of four attempts and nineteen minutes. Second, half the size and free: put the "Real people read every message, usually the same ones packing your order" paragraph on `/pages/contact` above the form, where it was clearly written to go.
