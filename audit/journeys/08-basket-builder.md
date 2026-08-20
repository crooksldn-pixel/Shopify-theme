# 08 — Femi, building a whole fit in one go and in no particular hurry

**Device:** mobile 390×844, ordinary 4G, one thumb on the sofa · **Goal:** a tee, a pair of jeans and socks, all in one order · **Mood:** relaxed, Sunday evening, browsing properly — expects to change his mind and doesn't mind doing it

---

### Step 1 — Landed on the homepage and let it settle
**Did:** Opened the site cold. Didn't touch anything for a few seconds.
**Got:** A black terminal-looking page. Top strip: `FREE UK SHIPPING OVER £20 — ORDER BY 18:00 FOR SAME-DAY DISPATCH`, which after a moment flips to `12 PRODUCTS CURRENTLY ONLINE`. Handcuffs logo, then `CATALOGUE  SEARCH  BAG [0]  LIGHT MODE  MENU`. Big `CROOKSLDN`, `OWN THE STREETS™`, a purple `CATALOGUE` button. Then a grey panel slid up and took the bottom half of the screen: `COOKIE CONSENT` — "We and our partners, including Shopify, use cookies and other technologies to personalize your experience, show you ads, and perform analytics, and we will not use cookies or other technologies for these purposes unless you accept them. Learn more in our Privacy Policy", with `Accept`, `Decline`, `Manage preferences`. (`audit/screens/08-01-arrival.png`)
**Expected:** A shop, and a cookie thing.
**Felt:** The site looks like nothing else and I liked it immediately. The cookie panel is the odd one out — it's Shopify's own paragraph, sentence case, "personalize" with a z, sitting under a header that shouts in mono capitals. It reads like someone else's furniture dropped into the room. But both buttons are real buttons and `Decline` isn't hidden, so it took one tap.
**Next:** continued

### Step 2 — Declined the cookies, started scrolling, and something else took the whole screen
**Did:** Tapped `Decline`. Started scrolling down into the product list.
**Got:** A few seconds later the entire screen went over to a black panel with an `×` in the top-left corner: `CROOKSLDN: THE GETAWAY` — "Crack the cuffs. 10% off your first order — code sent by text. Attempts unlimited." Two buttons, `RUN IT` and `NOT NOW`, and underneath in grey: "One code per player. Code expires 20 minutes after you win." It landed on top of the catalogue I'd just started reading — the products were gone, top to bottom. (`audit/screens/08-02c-getaway-overlay.png`)
**Expected:** To carry on scrolling.
**Felt:** Two minds about this. It's the best-looking popup I've been shown in a while — it's in the site's own voice, it's a game rather than "JOIN THE FAMILY 💜", and 10% off what I was about to spend is real money. But it wants my phone number, and it wants it thirty seconds after I arrived, before I've seen a single price or decided I like anything. I closed it with the `×`. So the shop dangled about nine quid off in front of the biggest basket it was going to get all evening, and I turned it down mostly because of *when* it asked. If it had waited until I had £91 in the bag I'd probably have played it.
**Next:** continued

### Step 3 — Read the register properly
**Did:** Scrolled the homepage list, now that I could see it.
**Got:** Twelve numbered products, `NO. 01` to `NO. 12`, each with a category, a name, a price and `AVAILABLE`. `CHARCOAL CELLBLOCK CREWNECK £50.00`, `BLUE WASH OG JEANS £60.00`, `GREY WASH JORTS £50.00`, `MONEY CLIVE TEE £25.00` with two little colour chips under it, `BLACK/BLUE MOTIONTEC™ SOCKS £6.00`. One of them says `2 OF 5 SIZES LEFT` instead of `AVAILABLE`. A filter row `ALL T-SHIRT DENIM SWEATS ACCESSORIES` and toggles `FLAT / ON MODEL / OUTLINE`. (`audit/screens/08-02-home-clear.png`, `08-02b-home-register.png`)
**Expected:** A grid of photos.
**Felt:** This is the best thing about the site. Every price is on the list, no "from £", nothing hidden behind a tap, and it tells you when something's running out of sizes without making a drama of it. I could plan the whole outfit off one screen: tee 25, jeans 60, socks 6. I knew I was spending about ninety quid before I'd opened a single product.
**Next:** continued

### Step 4 — Went to the tees
**Did:** Went through to the T-shirts.
**Got:** `TEES  2 ITEMS`, `FLAT / ON MODEL`, and two shirts: `MONEY CLIVE TEE £25.00` and `CRXST★RZ T-SHIRT £25.00 DROPPED 03.08`. (`audit/screens/08-03-tees.png`)
**Expected:** More than two.
**Felt:** Two tees is a small shop and it says so plainly — `2 ITEMS`. I'd rather that than a page pretending to have forty.
**Next:** continued

### Step 5 — Opened the MONEY CLIVE TEE and tapped M
**Did:** Opened it, read the price, tapped `M`.
**Got:** `MONEY CLIVE TEE`, `£25.00`, a `SIZE` row `XS S M L XL`, and under it a `COLOUR` row `BLACK WHITE`. M lit up purple. The line under the swatches changed to `Select Colour` — but the big button underneath still said **`SELECT A SIZE`**, and so did the button in the bar stuck to the bottom of the screen. (`audit/screens/08-04-tee-size-m-still-says-select-a-size.png`)
**Expected:** After picking a size, the button says something about adding it.
**Felt:** Mildly annoying and briefly confusing. I *have* selected a size — it's glowing at me. The small grey line knows what's actually missing; the two big buttons don't, and the big buttons are the ones you read. I tapped the greyed-out one anyway, got nothing, then found `Select Colour` on the second read. Ten seconds lost, no harm done, but if I'd been on a train I'd have decided the site was broken.
**Next:** continued

### Step 6 — Picked BLACK and added it
**Did:** Tapped `BLACK`, then `ADD TO BAG`.
**Got:** `IN STOCK` appeared, both buttons became `ADD TO BAG`, and after the tap a line printed under the button: `> Added — 1 in bag  View bag`. Header went `BAG [0]` → `BAG [1]`. No drawer flew out, nothing covered the screen. (`audit/screens/08-05-tee-ready.png`, `08-06-tee-added.png`)
**Expected:** A cart drawer sliding over everything.
**Felt:** Genuinely good. Quiet, instant, and it tells me the number that matters — one in bag — with a link if I want it. I stayed where I was, which is what I wanted. One thing does jar: right under `ADD TO BAG` there's a bright blue `Buy with Shop` button with rounded corners, and it's the only thing on the entire site that looks like every other Shopify shop. It's like a sticker on a nice piece of furniture.
**Next:** continued

### Step 7 — Scrolled back up to see how close I was to free shipping
**Did:** The strip at the top had told me free shipping starts at £20, and I'd just spent £25. So I scrolled up to look for the confirmation.
**Got:** Nothing. Header, then straight into the product. No shipping line anywhere between the top of the page and the photo. The strip at the top was still cycling `FREE UK SHIPPING OVER £20 — ORDER BY 18:00 FOR SAME-DAY DISPATCH`. (`audit/screens/08-07-tee-added-top-no-bar.png`)
**Expected:** Something saying I'd cleared £20.
**Felt:** Slightly deflating, in a small way. I'd just crossed the line the site had been advertising at me since I arrived and the site didn't notice. And the strip is still telling me about £20 as if I haven't done it — it's an advert, not a status. Not enough to stop me, but the one moment I was owed a small "nice one" and I didn't get it.
**Next:** continued

### Step 8 — Went to the denim, and *now* a progress bar appeared
**Did:** Navigated to `DENIM`.
**Got:** A new band across the top of the page that hadn't existed before: `> £45.00 to free Tracked 24`, a segmented purple bar about a third filled, and under it `✓ TRACKED 48 FREE` on the left in purple and `TRACKED 24 FREE` on the right in grey. Below it: `DENIM 4 ITEMS`, jorts at £50.00 and jeans at £60.00. (`audit/screens/08-08-denim-bar-after-tee.png`)
**Expected:** Just the jeans.
**Felt:** So *that's* where the shipping thing lives. Two reactions at once. First: this is a good instrument — a real number, a real service name, no "ONLY £45 AWAY!!!". Second: it's the first I'm hearing of a second tier, and it turned up already telling me I'm £45 short of it. The £20 line I did clear is recorded as a tick I nearly didn't notice. So I was never congratulated for the first threshold and I was immediately shown a bigger one. It's honest, but it's a bit of a "well done, now do it again".
**Next:** continued

### Step 9 — Bought the jeans
**Did:** Opened `BLUE WASH OG JEANS £60.00`, tapped `M`, tapped `ADD TO BAG`.
**Got:** Straight to `ADD TO BAG` this time — jeans only have a size, no colour, so one tap did it. `> Added — 2 in bag  View bag`, header `BAG [2]`. (`audit/screens/08-09-jeans-pdp-bar.png`, `08-10-jeans-added.png`)
**Expected:** Done, and I'm now well past £70.
**Felt:** Easy. £25 and £60 is £85 and I know the second tier is £70, so I'd just earned the good delivery. I scrolled up to watch the bar fill.
**Next:** continued

### Step 10 — Scrolled up to watch it cross £70, and it hadn't moved
**Did:** Scrolled to the top of the same page, without going anywhere.
**Got:** `BAG [2]` in the header, and directly under it the bar still reading **`> £45.00 to free Tracked 24`**, still a third full, still `TRACKED 24 FREE` in grey. (`audit/screens/08-11-jeans-added-top-STALE-BAR.png`)
**Expected:** `Free Tracked 24 — unlocked`, or at worst a smaller number.
**Felt:** This is the moment I stopped trusting the bar. Two numbers on one screen, both from the same shop, and they can't both be right: the header says two items in the bag, and I know those two items are £25 and £60, so it's £85 — and the bar is telling me I'm £45 short of £70. It's not just late, it's *wrong in the direction that costs the shop money*. If I'd been the kind of shopper who adds a pair of socks specifically to clear a threshold, I'd have added the socks, seen nothing change, and concluded the whole thing was decoration. As it was I just thought "that's not right" and carried on.
**Next:** continued

### Step 11 — Loaded the accessories page and it was suddenly fine
**Did:** Went to `ACCESSORIES` to get the socks.
**Got:** Same band, now reading `> Free Tracked 24 — unlocked`, bar completely full, and both labels ticked: `✓ TRACKED 48 FREE` and `✓ TRACKED 24 FREE`. (`audit/screens/08-12-accessories-unlocked.png`)
**Expected:** By this point, honestly, anything.
**Felt:** So it does work — it just only ever tells you on the *next* page. Which means the bar is never news. By the time it congratulates you, you've already moved on and done the thing. And it makes the earlier screen worse in hindsight, not better: it wasn't broken, it just couldn't be bothered until I navigated.
**Next:** continued

### Step 12 — The socks page told me to select a size, and there wasn't one
**Did:** Opened `WHITE/RED MOTIONTEC™ SOCKS £6.00`.
**Got:** A row headed `QUANTITY` with `1pc  3pc  6pc  12pc`, a grey line saying `Select Quantity`, and then the big button — and the button in the sticky bar at the bottom — both saying **`SELECT A SIZE`**. There is no size on this product at all. (`audit/screens/08-13-socks-select-a-size.png`)
**Expected:** `SELECT A QUANTITY`, or just `ADD TO BAG`.
**Felt:** Second time the same button has lied to me. On the tee it told me to pick a size I'd already picked; here it's telling me to pick a size that doesn't exist. It's the one control on the page you can't afford to have wrong. Also, `£6.00` sits above `1pc / 3pc / 6pc / 12pc` and I couldn't tell whether three pairs is £18 or a bundle price without tapping each one — I couldn't be bothered, so the shop got £6 instead of possibly £15.
**Next:** continued

### Step 13 — Took one pair
**Did:** Tapped `1pc`, then `ADD TO BAG`.
**Got:** `> Added — 3 in bag  View bag`. Header `BAG [3]`. (`audit/screens/08-14-socks-added.png`)
**Expected:** That.
**Felt:** Fine. Three things in, outfit done, about ninety quid, delivery free. Time to check it.
**Next:** continued

### Step 14 — Opened the bag
**Did:** Tapped `BAG [3]`.
**Got:** `> Free Tracked 24 — unlocked` with both ticks, then `Cart 3`, then `Cart total £91.00 GBP`, then three rows, each with a photo, a variant line, a price, a `− 1 +` box and a bin:
`WHITE/RED MOTIONTEC™ SOCKS / 1pc / £6.00`
`BLUE WASH OG JEANS / M / £60.00`
`MONEY CLIVE TEE / M,  BLACK / £25.00`
then `Discount`, `Estimated total £91.00 GBP`, `Duties and taxes included. Shipping is calculated at checkout.` and `Check out`. Header `BAG [3]`, page heading `Cart 3`. (`audit/screens/08-15-cart-three.png`, `08-16-cart-top.png`)
**Expected:** Three lines and ninety-one pounds.
**Felt:** Everything agrees and I could see it agreeing in one look — bag count, cart count, three prices, one total. The variant line under the tee reads `M,  BLACK` with a stray comma and a double space, which is scruffy on a site this precise, but I knew what it meant. The cart is the one screen on the site where all the numbers were right at the same time.
**Next:** continued

### Step 15 — Decided M was wrong and went looking for a way to change it
**Did:** Changed my mind — I want the tee in L. Looked for a size control on the cart row.
**Got:** Nothing. The row has a photo, the words `Size: M, Colour: BLACK` as plain text, a quantity stepper, and a bin. No dropdown, no "edit", no link back to the product. The only way out of M is the bin.
**Expected:** Tap the size, change it to L.
**Felt:** This is the single most irritating thing in the whole trip, and it's the most ordinary thing a person does. Getting the size wrong is not an edge case — it's the normal reason anyone opens their bag again. To fix a letter I have to delete the line, remember which product it was, find it, pick the size, pick the colour again, and add it back. Nothing about it is hard — it's about fifteen seconds and four taps — but it treats a wrong letter as though I'd changed my mind about the whole shirt, and it walks me past the broken bag count on the way.
**Next:** continued

### Step 16 — Binned the tee, and the header stopped telling the truth
**Did:** Tapped the bin on the tee row.
**Got:** Row gone, no confirmation, no undo, no "removed" message. The bar above rewrote itself live and immediately: `Free Tracked 24 — unlocked` became **`> £4.00 to free Tracked 24`**, bar dropped to nearly-but-not-quite full. Page heading became `Cart 2`, `Cart total £66.00 GBP`. And the header, an inch above it, still said **`BAG [3]`**. (`audit/screens/08-17-tee-removed-bagcount.png`, `08-18-tee-removed-full.png`)
**Expected:** Both counts to say 2.
**Felt:** I said "did that actually delete?" out loud. Two numbers, same screen, about a centimetre apart, disagreeing — `BAG [3]` sitting directly over `Cart 2`. I counted the rows to settle it. And note what the good half of the screen just did: the shipping bar reacted *instantly* to the removal and told me exactly what binning the tee had cost me — £4 short of free next-day. That's the same bar that couldn't be bothered when I added £60 on a product page. So it can do it. It just doesn't do it where I add things.
**Next:** hesitated

### Step 17 — Waited to see if the header would catch up
**Did:** Sat there for a bit, doing nothing.
**Got:** Eight seconds later: `BAG [3]`, `Cart 2`, `£66.00`. Unchanged. It only came right when I left the page — the moment I opened the tee again the header read `BAG [2]`. (`audit/screens/08-19-tee-removed-8s-later.png`)
**Expected:** A second or two of lag, then agreement.
**Felt:** It's not lag, it's just wrong until you leave. The cart page is *the* page where you go to check you've got it right, and it's the one page where the two counts can disagree. If I'd binned something and then gone straight to checkout without looking down, I'd have gone in believing I still had three items.
**Next:** continued

### Step 18 — Bought the tee again, in L
**Did:** Back to `MONEY CLIVE TEE`. Tapped `L` — button said `SELECT A SIZE` again, grey line said `Select Colour` again — tapped `BLACK`, tapped `ADD TO BAG`.
**Got:** `> Added — 3 in bag  View bag`, `BAG [3]`. (`audit/screens/08-20-tee-l-added.png`)
**Expected:** Fine.
**Felt:** Knew the trick this time so it took fifteen seconds. It's still fifteen seconds and four taps to change one letter.
**Next:** continued

### Step 19 — Checked the bag again
**Did:** Opened the cart.
**Got:** `> Free Tracked 24 — unlocked`, `Cart 3`, `MONEY CLIVE TEE / L,  BLACK / £25.00`, socks £6.00, jeans £60.00, `Cart total £91.00 GBP`, `Estimated total £91.00 GBP`. `BAG [3]`. (`audit/screens/08-21-cart-after-swap.png`)
**Expected:** Same total as before, different letter.
**Felt:** Good — it says `L` where it said `M`, same £91.00, and everything lines up again. The swap worked. It just shouldn't have been a swap.
**Next:** continued

### Step 20 — Decided the socks were an indulgence and binned them
**Did:** Second thoughts about £6 of socks I don't need. Tapped the bin on the socks row.
**Got:** Row gone. `Cart 2`, `Cart total £85.00 GBP`, `Estimated total £85.00 GBP`. Bar stayed `> Free Tracked 24 — unlocked` with both ticks, correctly — £85 is still over £70. And the header said **`BAG [3]`** again, over `Cart 2`. (`audit/screens/08-22-socks-removed-bagcount.png`, `08-23-socks-removed-full.png`)
**Expected:** `BAG [2]`.
**Felt:** Same fault, second time, and now I know to ignore the header. But "learn to ignore a number on the screen" is a bad thing to have taught a customer. Reloading the page fixed it to `BAG [2]` instantly, which tells me the count is only ever computed when the page is drawn. (`audit/screens/08-24-cart-reloaded.png`)
**Next:** continued

### Step 21 — Put the socks back
**Did:** Changed my mind again. Back to the socks, `1pc`, `ADD TO BAG`.
**Got:** `> Added — 3 in bag  View bag`, `BAG [3]`. (`audit/screens/08-25-socks-re-added.png`)
**Expected:** Back where I was.
**Felt:** Painless, because adding is the thing this site is good at. It's only *un*-deciding that costs you.

Worth saying: the shipping bar never once tempted me into spending more, in either direction. It told me I was £4 short after I removed something, and I ignored it, because I'd removed the thing on purpose. It's a readout, not a salesman — which I like, but the owner should know it isn't earning its keep as a nudge.
**Next:** continued

### Step 22 — Did the maths against what the product pages told me
**Did:** Counted it up myself before paying. Tee £25.00 on its page, jeans £60.00 on theirs, socks £6.00 on theirs.
**Got:** £25 + £60 + £6 = £91. Cart rows: `£6.00`, `£25.00`, `£60.00`, each repeated as its own line total. `Cart total £91.00 GBP`. `Estimated total £91.00 GBP`. Nothing added, nothing sneaked in. (`audit/screens/08-26-cart-final.png`, `08-27-cart-final-top.png`)
**Expected:** £91.00.
**Felt:** The money is completely straight and that matters more than everything above it. Every price I was shown on a product page is the price in the bag, the lines add up to the total, and the total didn't change between the cart and the checkout. **The prices never disagreed with each other once. The only numbers that ever disagreed were the counters** — and both times it was the header `BAG [n]` against the cart, never money against money.
**Next:** continued

### Step 23 — Checkout, and stopped there
**Did:** Tapped `Check out`. Waited.
**Got:** A pause, then a completely different website: white, blue links, rounded boxes, a `CROOKSLDN` wordmark in a normal sans-serif at the top. `Order summary` with `£91.00` beside it. `Express checkout`, `OR`, `Contact`, `Email or mobile phone number` with `Keep me updated.` already ticked for me, then `Delivery`, `Country/Region — United Kingdom`, name and address fields. (`audit/screens/08-28-checkout.png`, `08-29-checkout-full.png`)
**Expected:** The £91, and a form.
**Felt:** Two things. The £91.00 is right at the top and matches, which is the only thing I actually needed. But everything the last ten minutes built — the black, the mono, the evidence-log thing — is gone at the door, and it goes from "small London label with a strong idea" to "a Shopify store" in one tap. It's still trustworthy, it's just not *theirs* any more. And the marketing tick-box being pre-ticked is a small cheek on a site that has otherwise been notably straight with me.
**Next:** stopped here deliberately — nothing entered, nothing submitted

---

## Outcome
**Bought / didn't:** Reached the checkout page with the full outfit at **£91.00** — `MONEY CLIVE TEE / L / BLACK £25.00`, `BLUE WASH OG JEANS / M £60.00`, `WHITE/RED MOTIONTEC™ SOCKS / 1pc £6.00` — and stopped at the payment step without entering anything. Nothing in the journey would have stopped me paying; the money was right at every screen.

**Total time:** about eleven minutes, unhurried. Two of those were spent re-buying a t-shirt in a different size and twice counting cart rows to work out whether the header was lying.

**Worst moment:** binning the tee and seeing `BAG [3]` sitting directly above `Cart 2` and `£66.00`. Out loud: *"Did that actually delete? It still says three."* It happened again when I removed the socks, and it never fixed itself — eight seconds later it was still wrong, and only a page change put it right.

**Best moment:** the shipping bar on the cart page rewriting itself the instant I removed the tee — `Free Tracked 24 — unlocked` → `> £4.00 to free Tracked 24`. That is exactly what I wanted it to do: tell me what my change just cost me, straight away, in a real number with a real service name and no shouting. Close second, the `> Added — 1 in bag  View bag` line under the button — no drawer thrown over the screen, no interruption, just the fact.

**Would they come back?** Yes. The catalogue puts every price in front of you, the buying is quick, the totals are honest, and it looks like nobody else. I'd come back and I'd expect to get the size wrong again.

**One thing that would have changed the outcome:** let me change a size *in the cart*. Everything I found difficult flowed from that one gap — the delete-and-rebuy, the two wrong bag counts I met on the way, and the only real time I lost. A size control on the cart line would have removed the whole middle of this journey.

---

## The two things I was watching

### The carriage bar — what it said, and when

| My bag | What the bar said | When it said it |
|---|---|---|
| £0.00, empty | **nothing — no bar at all** | — |
| £25.00 — tee in, **£20 crossed** | still nothing on that page | never announced the crossing |
| £25.00, next page load | `> £45.00 to free Tracked 24` · `✓ TRACKED 48 FREE` / `TRACKED 24 FREE` | one page late |
| £85.00 — jeans in, **£70 crossed**, same page | **`> £45.00 to free Tracked 24`**, bar a third full | wrong, and stayed wrong until I navigated |
| £85.00, next page load | `> Free Tracked 24 — unlocked` · `✓ TRACKED 48 FREE` `✓ TRACKED 24 FREE` | one page late |
| £66.00 — tee removed **on the cart page** | `> £4.00 to free Tracked 24` | **instantly, live, correct** |
| £91.00, final cart | `> Free Tracked 24 — unlocked` | correct |

**The answer to "does it tell you at the moment it happens":** no, not once, in the place where it happens. Both thresholds were crossed by tapping `ADD TO BAG` on a product page, and on a product page the bar does not move — it kept saying `£45.00 to free Tracked 24` while my bag held £85. It only ever corrects itself on the next page I load, by which point the news is stale. The one place it *is* live is the cart page, where it reacted to a removal within a second and told me precisely what I'd given up. So the machinery works; it is simply deaf on the two pages where a shopper actually changes their basket.

**And the £20 threshold was never announced at all.** I crossed it with my first item and no screen ever said so. The first time the site mentioned the tier again, it was a small `✓` beside `TRACKED 48 FREE` on a page whose main message was that I was £45 short of a *different* threshold I hadn't heard of until that second. Meanwhile the strip at the very top of every page was still advertising `FREE UK SHIPPING OVER £20 — ORDER BY 18:00 FOR SAME-DAY DISPATCH` long after I'd passed £20 — so at one point the top of the screen was selling me a threshold I'd cleared, and the band below it was pointing at a bigger one.

### The bag count in the header — did it agree with the cart?

| What I did | Header | Cart really held | Agreed? |
|---|---|---|---|
| added the tee (product page) | `BAG [1]` | 1 | yes, instantly |
| added the jeans (product page) | `BAG [2]` | 2 | yes, instantly |
| added the socks (product page) | `BAG [3]` | 3 | yes, instantly |
| **removed the tee (cart page)** | **`BAG [3]`** | **`Cart 2` · £66.00** | **no** |
| …eight seconds later | `BAG [3]` | `Cart 2` · £66.00 | still no |
| navigated to a product page | `BAG [2]` | 2 | yes |
| **removed the socks (cart page)** | **`BAG [3]`** | **`Cart 2` · £85.00** | **no** |
| reloaded the cart | `BAG [2]` | 2 | yes |

**The pattern:** the header is right after every add and wrong after every remove. It never self-corrects — not after eight seconds of sitting still — and only comes good when the page is drawn again. The place it goes wrong is the cart page, which is the one page a shopper opens *specifically* to check what they've got, and the wrong number sits about a centimetre above the right one. On both occasions it overstated my basket, which reads as "your deletion didn't work" and made me count the rows by hand.

### The numbers that disagreed — and which I'd believe

Only one kind of disagreement, and it happened twice. Both times it was **the header `BAG [3]` against the cart's own `Cart 2` and `Cart total £66.00 GBP` / `£85.00 GBP`** (`08-17-tee-removed-bagcount.png`, `08-22-socks-removed-bagcount.png`). **I would believe the cart, every time** — it lists the rows, each row shows its own price, and the rows add up to the total it prints. The header shows a number with nothing to check it against.

A third disagreement is the same fault wearing different clothes: on the jeans page, `BAG [2]` in the header sat directly above `> £45.00 to free Tracked 24`, when the two things in the bag were a £25 tee and £60 jeans (`08-11-jeans-added-top-STALE-BAR.png`). **Believe the bag** — £85 was the truth and the bar was £60 behind.

**The money itself never disagreed with anything.** £25.00 / £60.00 / £6.00 on the product pages, the same three figures as line totals in the cart, `Cart total £91.00 GBP`, `Estimated total £91.00 GBP`, and `£91.00` at the top of the checkout. Four screens, one number. Whatever else is loose here, the prices are not.
