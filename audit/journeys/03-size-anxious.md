# 03 — Femi, between a 32 and a 34, and once paid £8 to post a pair of jeans back

**Device:** mobile 390×844, ordinary 4G · **Goal:** buy the £60 jeans, in the size that will actually fit · **Mood:** wants them, doesn't trust himself to guess, will not press ADD TO BAG until the numbers say something

---

### Step 1 — Landed on the homepage and let it arrive
**Did:** Opened the site cold and waited a few seconds without touching anything.
**Got:** A thin bar across the top — `FREE UK SHIPPING OVER £20 — ORDER BY 18:00 FOR SAME-DAY DISPATCH` — then handcuffs, `CROOKSLDN`, `OWN THE STREETS™`, a purple `CATALOGUE` button and `> 12 PRODUCTS AVAILABLE TO PURCHASE`. Then a `COOKIE CONSENT` sheet climbed over the bottom of the screen, starting about 485px down an 844px phone, so a bit over 40% of it. Nothing else popped up while I stood there. (`audit/screens/03-01-home-cold.png`)
**Expected:** A shop, and a cookie thing.
**Felt:** Looks like a police terminal, which I liked immediately. The cookie text is Shopify's own paragraph — "We and our partners, including Shopify, use cookies and other technologies to personalize your experience, show you ads, and perform analytics…" — set in the site's typeface, which is a weird join. `Accept` and `Decline` are both proper buttons though, same size, neither hidden.
**Next:** continued

### Step 2 — Declined, because it was in my way
**Did:** Tapped `Decline`.
**Got:** Sheet gone. (`audit/screens/03-02-home-clear.png`)
**Expected:** That.
**Felt:** Nothing to say. It went away first time.
**Next:** continued

### Step 3 — Went looking for the baggy jeans and ended up in DENIM
**Did:** Tapped through to the catalogue and filtered to `DENIM`.
**Got:** `DENIM / 4 ITEMS` — `GREY WASH JORTS £50`, `BLUE WASH JORTS £50`, `BLUE WASH OG JEANS £60`, `GREY WASH OG JEANS £60`. (`audit/screens/03-03-denim.png`)
**Expected:** To see something called baggy jeans, because that's what I was sent for.
**Felt:** First small wobble. The only thing in this shop with "baggy" in the name is `V2 BAGGIES` at £60 — and that's filed under **SWEATS**, it's a pair of joggers. So the £60 "baggy jeans" is one of these two OG pairs. Not the site's fault exactly, but I've already got two products at £60 in my head that are not the same thing.
**Next:** continued

### Step 4 — Opened GREY WASH OG JEANS
**Did:** Tapped it.
**Got:** `PRODUCT 05 / 12`, `DENIM`, one image — `PHOTO 1 OF 1` — of the back of the jeans, then `GREY WASH OG JEANS`, `£60.00`, `SIZE` with `XS S M L XL`, the word `Select Size`, a `SIZE GUIDE` button, `Order before 18:00 and it ships today (Mon–Sat)` and `> Ordered now — leaves tomorrow`. (`audit/screens/03-04-jeans-top.png`, `03-05-size-row.png`)
**Expected:** Several photos, and a fit note.
**Felt:** One photo, and it's the back. For £60 that's thin. I can't see the front rise, I can't see them on a person, I can't see how they break over a shoe. The dispatch line is good and specific — I believed that instantly, more than I believed anything else on the page later.
**Next:** continued

### Step 5 — Read the description, and it argued with the photo
**Did:** Opened `ITEM DESCRIPTION`.
**Got:** "OG jeans — grey wash, for the record. 14oz denim, OG straight cut, mid rise. **Structured, not baggy.** Made in Portugal." (`audit/screens/03-30-jeans-says-vs-numbers.png`)
**Expected:** Confirmation of what I was looking at.
**Felt:** The picture is of a wide, heavy-looking jean. The words say "structured, not baggy". Those two things pull in opposite directions and they change what I'd buy: baggy I take the smaller one, structured I take the bigger one. So now I *need* the numbers, I'm not just being careful.
**Next:** continued

### Step 6 — Tapped MEASUREMENTS and nothing appeared to happen
**Did:** Scrolled to the block of four rows — `SPECIFICATION`, `ITEM DESCRIPTION`, `MEASUREMENTS`, `CHAIN OF CUSTODY — SHIPPING & RETURNS` — and tapped `MEASUREMENTS`, which was sitting right at the bottom edge of the screen. (`audit/screens/03-05b-accordion-stack.png`)
**Got:** The `+` turned into a `−` and the screen did not move. **Not one row of the table was on screen** — the header row opened 997px down a screen that's 844px tall, and the `XS` row at 1031px. (`audit/screens/03-06-measurements-tapped.png`)
**Expected:** To see a table.
**Felt:** I genuinely thought it was broken for a second. You tap the thing, a symbol flips somewhere near your thumb, and the content lands entirely below the edge of the phone. Every accordion I've ever used either scrolls to itself or opens where I can see it.
**Next:** hesitated

### Step 7 — Scrolled, found it, went back up, found the better button
**Did:** Scrolled down manually until the table appeared. Then went back up to the top and noticed `SIZE GUIDE` under the size buttons, which I'd skipped past. Tapped that instead.
**Got:** The page glided down — not jumped — and parked with the word `MEASUREMENTS` at the very top of the screen and the whole five-row table under it. One tap, no popup, no PDF. (`audit/screens/03-07-measurements.png`)
**Expected:** A modal, or worse, a PDF that opens sideways.
**Felt:** This is the best thing on the page. `SIZE GUIDE` is right where my thumb already is, it's a word not an icon, and it puts the table exactly where I can read it. The odd part is that the button labelled `MEASUREMENTS` is a *worse* way of getting to the measurements than the button labelled `SIZE GUIDE`.
**Next:** continued

### Step 8 — Read the method statement
**Did:** Read the grey line above the table before the numbers.
**Got:** `TRUE TO SIZE — WAIST, CHEST AND LEG MEASUREMENTS ARE TAKEN AROUND THE GARMENT. ALL MEASUREMENTS IN CENTIMETRES.`
**Expected:** Something telling me whether to compare against my body or against a pair of jeans laid on the floor.
**Felt:** Half a mark. "Taken around the garment" does tell me it's the garment and not my waist, and it tells me it's the full loop, not a flat half. But `TRUE TO SIZE` is an opinion sitting in the same sentence as the method, and "true to size" is what every brand says right before you find out it isn't. I'd rather it said nothing there.
**Next:** continued

### Step 9 — Read the numbers in centimetres
**Did:** Read the table. `SIZE / WAIST / INSEAM / LEG OPENING`:

| | WAIST | INSEAM | LEG OPENING |
|---|---|---|---|
| XS | 76.2cm | 73.7cm | 45.7cm |
| S | 81.3cm | 76.2cm | 48.3cm |
| M | 86.4cm | 77.5cm | 50.8cm |
| L | 91.4cm | 80.0cm | 53.3cm |
| XL | 96.5cm | 81.3cm | 55.9cm |

**Got:** Three columns, five sizes, one decimal place each. (`audit/screens/03-07-measurements.png`)
**Expected:** To find my number and stop worrying.
**Felt:** At first: relief, there are decimals, someone's used a tape. M is 86.4cm round the waist. I'm somewhere between a 32 and a 34, so that's the one.
**Next:** continued

### Step 10 — Hit `IN`, and the relief went away
**Did:** Tapped `IN` next to `CM`.
**Got:** Instant swap, no reload, the purple fill moved across, and the sentence above rewrote itself to `…ALL MEASUREMENTS IN INCHES.` The table became: waist `30 / 32 / 34 / 36 / 38in`, inseam `29 / 30 / 30.5 / 31.5 / 32in`, leg opening `18 / 19 / 20 / 21 / 22in`. (`audit/screens/03-08-measurements-inches.png`)
**Expected:** The centimetres, converted. Which is what I got, in the mechanical sense — the toggle works perfectly.
**Felt:** **This is where the table stopped being evidence and started being a size chart.** Look at it. 30, 32, 34, 36, 38. 18, 19, 20, 21, 22. Every single number a whole inch, no exceptions, across fifteen cells. Nothing you measure comes out like that. My own jeans, measured on the floor, are 33½ and a bit. What this means is that the centimetres aren't measurements at all — they're the inch ladder run through a converter. 76.2cm *is* 30 inches, dead on. 50.8cm *is* 20 inches, dead on. The `.2` and the `.4` and the `.8` I trusted thirty seconds ago are conversion crumbs, not tape marks.

And once you see that, the table tells me nothing I didn't already know: it says the M is a 34, which is just the letter M written out in numbers. It's the same chart every brand prints, which is precisely the chart that made me a 32 in one shop and a 34 in another.
**Next:** hesitated

### Step 11 — Went to check it against a different garment
**Did:** Opened `V2 BAGGIES` — the £60 joggers from the sweats page — and tapped its `SIZE GUIDE`. Its own description says: "V2 Baggies — **wide, full-length sweats** in 500gsm cotton, heavy enough to hang straight."
**Got:** `SIZE / WAIST / INSEAM / LEG OPENING` — `76.2cm 73.7cm 45.7cm` / `81.3cm 76.2cm 48.3cm` / `86.4cm 77.5cm 50.8cm` / `91.4cm 80.0cm 53.3cm` / `96.5cm 81.3cm 55.9cm`. **The same fifteen numbers as the jeans.** Same in inches too — 30/29/18 through 38/32/22. Description and table are in one screenful together. (`audit/screens/03-30-baggies-says-vs-numbers.png`, `03-12-baggies-measurements.png`, `03-13-baggies-inches.png`)
**Expected:** Different numbers, because it's a different garment made of different stuff in a different shape.
**Felt:** **This is the moment I decided not to buy, and I can name it exactly: 5 minutes 40 in, standing on the V2 BAGGIES page reading its leg opening.**

A 500gsm cotton sweatpant the shop calls *wide, full-length* and a 14oz denim jean the shop calls *structured, not baggy* cannot both have a 20-inch leg opening at M. They can't both be 34 in the waist to the millimetre either. One of those tables was not measured off that garment — and I have no way of knowing which one, so I have to assume neither was. Everything I'd worked out one screen earlier is now worthless, including the bit I liked.

Out loud: *"they've put the same chart on the joggers."*
**Next:** hesitated — kept going, but now checking rather than shopping

### Step 12 — Checked the other £60 jeans too
**Did:** Opened `BLUE WASH OG JEANS`.
**Got:** Identical table again — `76.2 / 73.7 / 45.7` down to `96.5 / 81.3 / 55.9`. Its description is the same paragraph with the colour swapped: "OG jeans — blue wash, for the record. 14oz denim, OG straight cut, mid rise. Structured, not baggy." (`audit/screens/03-21-other-jeans-measurements.png`)
**Expected:** By now, exactly that.
**Felt:** Fine, honestly — two colourways of the same cut *should* share a table. That one's legitimate. It's the joggers that did the damage.
**Next:** continued

### Step 13 — Noticed the table had forgotten I use inches
**Did:** Nothing. Just arrived on the blue pair after having switched the grey pair to `IN`.
**Got:** `CM` selected again, purple, table in centimetres.
**Expected:** To still be in inches. I chose inches. I'm the same person on the same phone eight seconds later.
**Felt:** Small, but I'm comparing three products by now and I've had to tap `IN` on every single one. Any shopper doing what the shop wants — comparing two pairs — pays this tax on every page.
**Next:** continued

### Step 14 — Checked a sweat, to see if *anything* is measured for real
**Did:** Opened `CHARCOAL CELLBLOCK SHORTS` and then `CHARCOAL CELLBLOCK CREWNECK`.
**Got:** The shorts have their own table, and a different column heading — `SIZE / **FITS WAIST** / LENGTH / LEG OPENING`, `71.1cm 49.5cm 58.4cm` up to `91.4cm 59.7cm 78.7cm`; in inches `28 / 30 / 32 / 34 / 36` waist and `23 / 25 / 27 / 29 / 31` leg opening — whole inches again, every cell. The crewneck's chest is `43 / 45 / 47 / 49 / 51in` — whole inches again — but its length comes out `25.7 / 26.5 / 27.2 / 28 / 28.7in`, which is ragged. (`audit/screens/03-14-sweat-shorts-measurements.png`, `03-15-sweat-shorts-inches.png`, `03-16-crewneck-measurements.png`)
**Expected:** By this point, more of the same.
**Felt:** Two things. One, at least the shorts and the crewneck have their *own* numbers, so it isn't one chart pasted over the whole shop — it's a handful of charts spread over fourteen products, which is somehow more confusing than one. Two, the shorts say `FITS WAIST`, which is my body, while the line directly above them says the measurements are `TAKEN AROUND THE GARMENT`, which isn't. Those are different measurements of different objects in the same box.
**Next:** continued

### Step 15 — Read the returns clause properly, since I now expected to use it
**Did:** Back on the jeans, opened `CHAIN OF CUSTODY — SHIPPING & RETURNS` and read to the bottom.
**Got:** Four steps. `04 DELIVERED` — "You have **14 days from delivery** to return unworn goods with tags attached. **Return postage is yours** unless we sent the wrong thing or it arrived faulty. Start a return by email: crooksldn@gmail.com." (`audit/screens/03-09-custody-returns.png`)
**Expected:** To find out who pays.
**Felt:** Clear, plain, no wriggling, and I respect that it says it straight instead of burying it. But it's the sentence I was afraid of. Last time this cost me £8. So the price of guessing wrong here is £60 out, £8 back to me, wait two weeks — and the only thing that would stop me guessing wrong is a table I've just decided I can't trust. That's the whole problem in two lines of text.
**Next:** hesitated

### Step 16 — Went to QUESTIONS to see if a human had written it down better
**Did:** Footer → `QUESTIONS` → `SIZING` → `HOW DO I KNOW WHAT SIZE TO BUY?`
**Got:** "Where a piece has been measured, its product page carries a measurements table — tap SIZE GUIDE next to the size buttons. **Everything is measured with the garment laid flat**, and you can switch the table between centimetres and inches. If the piece you want is not listed yet, message us and we will measure it for you." (`audit/screens/03-17-faq-sizing.png`)
**Expected:** The same method statement I'd read on the product page.
**Felt:** **This is worse than the duplicate table, and I want to be exact about why.** The product page says the waist is `TAKEN AROUND THE GARMENT`. This page, two taps away, says everything is `measured with the garment laid flat`. Those are not two ways of saying one thing — one is double the other.

If it's *around*, the M is a 34in waist and I'm probably an M. If it's *laid flat*, the M is 86.4cm across the waistband, which doubles to 172.8cm — a 68in waist — and the XS is 76.2cm flat, which is a **152cm** waist. Nobody has that. So a careful shopper who reads the FAQ, lays their own jeans on the floor and gets 43cm across the waistband compares 43 with 86.4, decides everything here is enormous, and orders the XS. Then pays the postage.

The two sentences are on the same website, written by the same shop, about the same table, and I had to be quite determined to find both of them. If I'd only read the FAQ I'd have ordered wrong and never known why.
**Next:** hesitated — this is where I stopped believing the size information as a whole

### Step 17 — Read the returns and exchanges answers while I was there
**Did:** Opened `DO YOU DO EXCHANGES?` and `CAN I RETURN SOMETHING?`.
**Got:** Exchanges — "Yes. You pay the postage sending the original back to us. There is no fee for the swap itself, and we cover the postage sending the new size out to you. Start it in the returns centre and say which size you want — swaps depend on that size being in stock, and if it is not we refund you instead." Returns — "…You have 14 days from delivery to tell us, and 14 days from then to post it back, unworn and with tags attached. Return postage is yours…" (`audit/screens/03-22-faq-exchanges.png`, `03-23-faq-returns.png`)
**Expected:** A flat no on exchanges, which is what most small labels say.
**Felt:** Genuinely better than I expected, and it nearly rescued the sale. A size swap where I only pay one way is a real answer to my problem — one leg of postage, call it £4, not £8. But **that sentence is on the FAQ page and not on the product page**, and the product page's own returns block never mentions exchanges at all. The one place I was standing when I had to choose between M and L, the site told me returns cost me money and said nothing about swaps.
**Next:** continued

### Step 18 — Read the refund policy, and met a company I'd never heard of
**Did:** Footer → `REFUNDS`.
**Got:** "Changed your mind or wrong size? You have 14 days from delivery to return or exchange any unworn item with tags on. Return postage is paid by you… There is no fee for a UK size swap itself, and we cover the postage sending the new size out to you. **For returns please return to: Oairo Uk Office, Bourne end Business Park, Bourne End, Buckinghamshire, United Kingdom, SL8 5AS.**" (`audit/screens/03-19-refund-policy.png`)
**Expected:** CROOKSLDN's address.
**Felt:** Who is Oairo? I've spent ten minutes on a site that's built its whole personality on chain of custody and evidence numbers, and the return address is a different company's office in Buckinghamshire, with "Bourne end" spelled two different ways in one line. I know in my head it's probably a fulfilment unit. It still made me go quiet.
**Next:** hesitated

### Step 19 — Looked for someone to ask
**Did:** Footer → `CONTACT`. The FAQ had said "message us and we will measure it for you", so I went to do exactly that.
**Got:** `CONTACT`, then `Name`, `Email*`, `Phone`, `Comment`, `Submit`. Nothing else — no reply time, no note about sizing, no mention of the offer that sent me there. (`audit/screens/03-24-contact.png`)
**Expected:** Somewhere it acknowledged that people write in about fit.
**Felt:** A bare four-field form after everything else on this site has a voice. And I'd be writing to ask "is the M actually a 34" about a product page that already claims to answer that. I'd feel daft sending it, and I'd be waiting 1–2 working days for a number that should be printed under the size buttons.
**Next:** hesitated

### Step 20 — Went back to the jeans, picked M, and didn't press it
**Did:** Back on `GREY WASH OG JEANS`. Tapped `M`. Then tapped `XL` to see what the little purple mark in its corner meant. Then back to `M`. Then looked at the table one more time.
**Got:** On `M` the line under the sizes changed from `Select Size` to `IN STOCK`, the dead grey `SELECT A SIZE` button became a purple `ADD TO BAG`, and the bar across the bottom filled in to read `GREY WASH OG … £60.00 · M` with `ADD TO BAG` and `CHECKOUT NOW`. On `XL` it said `3 LEFT IN SIZE XL`. (`audit/screens/03-25-size-m.png`, `03-27-xl.png`, `03-26-final-look.png`)
**Expected:** To buy.
**Felt:** The buying part of this page is excellent and I want to say so — `IN STOCK`, `£60.00 · M`, `ADD TO BAG`, all plain English, no cleverness where it would cost me, and the bar follows you down so the price and the size you picked are never off screen. If the table had been real I'd have been through checkout in forty seconds.

But I sat with my thumb over `ADD TO BAG` and thought: the only number I have is that the M is a 34, I already knew that from the letter M, one of the two garments carrying that number is definitely wrong, and the shop can't tell me whether it measured round or flat. Sixty quid, and £8 of my own money to find out. Bag stayed on `[0]`.
**Next:** gave up

---

## Outcome

**Bought / didn't:** Didn't. Not on price, not on the look, not on delivery — all three of those were fine and the dispatch promise was the most convincing thing on the site. I left because the measurements are the only reason I was there and they turned out to be a generic size chart, printed twice on two garments that are nothing like each other, with a stated method that the shop's own FAQ contradicts.

**Do the measurements look real or invented?** **Invented — and specifically, converted.** A shopper's read, with the numbers:

- In inches the jeans are **30 / 32 / 34 / 36 / 38** in the waist and **18 / 19 / 20 / 21 / 22** at the leg opening. Fifteen cells, every one a whole inch. Real garments measured with a tape do not do that once, let alone fifteen times.
- The centimetres are that ladder converted, not the other way round: **76.2cm is exactly 30in. 50.8cm is exactly 20in. 45.7cm is 18in.** The decimals that made me trust it — `.2`, `.4`, `.7` — are what a converter leaves behind, not what a tape measure reads.
- The `LEG OPENING` figures are 1 inch apart every size, exactly. The waist is 2 inches apart every size, exactly. That's a grading rule someone typed, not five garments someone laid out.
- The one table that *looks* measured is the crewneck's length — `25.7 / 26.5 / 27.2 / 28 / 28.7in` — and it only looks that way because it was written in centimetres and stepped by an even 1.9cm, so the inches came out ragged. It's the same trick facing the other way.
- The tell that closes it: the jeans and `V2 BAGGIES` — a 14oz denim the shop calls **"Structured, not baggy"** and a 500gsm sweatpant the shop calls **"wide, full-length"** — carry the same fifteen numbers to the millimetre, in both units. `BLUE WASH OG JEANS` makes it three products on one table.

**What that does to my confidence:** it doesn't dent it, it removes it. Before the comparison I had a table I half-believed and would probably have bought the M off. After it, I have to assume every table on the site might belong to something else, including the ones that look plausible. A wrong number I can adjust for; a number that might belong to a different garment I can't use at all. It also retroactively spoils the good parts — `TRUE TO SIZE` now reads as marketing, and `SIZE GUIDE`, which is a genuinely well-built button, is a very fast route to something that isn't information.

**The measured-how contradiction, and what it costs:** the product page says `WAIST, CHEST AND LEG MEASUREMENTS ARE TAKEN AROUND THE GARMENT`; `QUESTIONS` says "Everything is measured with the garment **laid flat**". For someone standing between two sizes that is not a wording nitpick, it is the entire decision, because the two readings are a factor of two apart. Read as *around*, the XS is a **76cm** waist and I'm an M. Read as *laid flat* — which is what the FAQ tells me, and the FAQ is where you go when you're unsure — the XS is a **152cm** waist, every size in the shop is enormous, and the correct move is to buy the smallest one. Two shoppers doing exactly as they're told, from two pages of the same site, will order two different sizes. And the one who follows the FAQ pays the return postage, because the site also tells him that's his.

**Total time:** about 12 minutes, which is roughly eight minutes longer than I'd normally give a pair of jeans.

**Worst moment:** Standing on the `V2 BAGGIES` page at 5:40 reading `50.8cm` in the leg-opening column, having read `50.8cm` in the leg-opening column of the jeans ninety seconds earlier. Out loud: *"they've put the same chart on the joggers — so which one is the tape measure from?"*

**Best moment:** `SIZE GUIDE`. One tap, from right beside the size buttons, no modal, no PDF, no pinch-zooming a sideways image, and it slides rather than jumps so you can see where you've been taken. Then the `CM`/`IN` toggle, which is instant and rewrites the sentence above the table as well as the numbers in it — most shops don't bother with the sentence. Both are better than the ones on sites twenty times this size. They are pointed at the wrong data.

**Would they come back?** For the clothes, yes — the jeans look good and the shop has a personality I'd tell someone about. To buy without seeing them in person, no, not until the numbers change. I'd go and try on a similar pair somewhere with a fitting room and then come back and order the size I'd learned, which is a slow way to lose a £60 sale you'd already won on everything except one accordion.

**One thing that would have changed the outcome:** Put the real, measured numbers for *this* pair of jeans in that table — even three of them, even ugly ones like `84.5cm` and `19.75in`, and make sure they don't match the joggers — and say once, in the same words on the product page and in the FAQ, whether that's around the garment or across it flat. I would have bought the M in the first ninety seconds. Failing that: move the exchange sentence off the FAQ and into the returns block on the product page, so the person hovering between two sizes reads "there is no fee for the swap itself" at the moment he's deciding, instead of ten minutes later when he's already gone.
