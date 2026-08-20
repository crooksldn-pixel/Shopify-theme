# 12 — Nadia, wants to read the returns policy before she spends £60, and will only use the search box

**Device:** mobile 390×844, ordinary 4G · **Goal:** find out what happens if the jeans don't fit, *before* entering a card · **Mood:** decided, mildly impatient, not browsing — she has one question and expects one answer

---

### Step 1 — Landed on the homepage and waited for it to settle
**Did:** Opened the site cold. Sat there while it drew itself in.
**Got:** Roughly six seconds of mostly-nothing, then the whole thing arrived at once: `12 PRODUCTS CURRENTLY ONLINE` across the top, a handcuffs logo, `CROOKSLDN`, `OWN THE STREETS™`, a purple `CATALOGUE` button. Then a `COOKIE CONSENT` panel slid up over the bottom half of the screen — it starts at 485px down an 844px screen, so it takes the bottom 43%. Nothing else popped up. (`audit/screens/12-01-arrived.png`)
**Expected:** A shop. Maybe a popup asking for my email.
**Felt:** The wait was long enough that I checked my signal. Once it landed it looks like nothing else I've seen — I'd have stayed just to find out what it was. The cookie thing is Shopify's own wording, in the site's typeface, which is a strange half-and-half: "We and our partners, including Shopify, use cookies and other technologies to personalize your experience, show you ads, and perform analytics…" That is not this brand's voice at all.
**Next:** continued

### Step 2 — Declined cookies to get the panel off the screen
**Did:** Tapped `Decline`. Not because I read it — because it was covering half the phone.
**Got:** Panel gone, homepage back. (`audit/screens/12-02-home-clear.png`)
**Expected:** Exactly that.
**Felt:** Fine. Two buttons, `Accept` and `Decline`, both real buttons, both easy to hit. No dark pattern where Decline is hidden in `Manage preferences`. I noticed that, and I notice it because most sites do the opposite.
**Next:** continued

### Step 3 — Looked in the header for a search box, not a menu
**Did:** Scanned the top strip. Did **not** open `MENU`. I never do — menus are someone else's filing system.
**Got:** A row of plain words: `CATALOGUE  SEARCH  BAG [0]  LIGHT MODE  MENU`. `SEARCH` is the second one, written out as a word, not a magnifying glass.
**Expected:** A magnifier icon somewhere I'd have to hunt for.
**Felt:** Genuinely good. It says SEARCH. I don't have to guess which squiggle means search, and I don't have to open a hamburger to find the search inside it. That is one tap saved and about four seconds of not-thinking.
**Next:** continued

### Step 4 — Tapped SEARCH
**Did:** Tapped `SEARCH`.
**Got:** A search page. The box is right under the header, wide, boxed, obvious. **The keyboard came up on its own** — the cursor was already in the field. Under it: `SEARCH BY ITEM, CATEGORY OR COLOUR`, then a `DIRECT LINKS` heading with three things already listed before I'd typed anything — `START A RETURN` (`RETURNS CENTRE`), `TRACK YOUR ORDER` (`TRACKING`), `QUESTIONS` (`FAQ`). The placeholder reads `Item, category or question`. (`audit/screens/12-03-search-empty.png`)
**Expected:** An empty box and nothing else.
**Felt:** Better than I expected. It didn't waste my time with a blank grid or a "no results" before I'd done anything, and one of the three things it offered unprompted was about returns. Keyboard already up is a small mercy on a phone.
**Next:** continued

### Step 5 — Typed `returns`
**Did:** Typed the word I always type: `returns`.
**Got:** A suggestion list appeared with **exactly one thing in it**: `START A RETURN` — `RETURNS CENTRE`. No policy. No FAQ. No terms. One row. (`audit/screens/12-04-type-returns.png`)
**Expected:** A returns policy. Or two or three things, one of which would be the policy.
**Felt:** Slightly wrong-footed. "Start a return" is not what I asked. I don't have anything to return — I haven't bought anything. I want to *read* the rules before I'm in a position to need them.
**Next:** hesitated

### Step 6 — Hit Enter anyway, thinking the full results page would have more
**Did:** Pressed the go key instead of tapping that one suggestion. A one-row dropdown made me assume it was truncated and the real list was behind Enter.
**Got:** A page that says, in this order, top to bottom: `DIRECT LINKS`, `START A RETURN / RETURNS CENTRE`, then `SEARCH: RETURNS`, then `0 RESULTS`, then `NO ITEMS IN THE REGISTER MATCH THAT QUERY.` (`audit/screens/12-05-results-returns.png`)
**Expected:** More links than the dropdown had.
**Felt:** This one actually stung. The page tells me **zero results** and shows me a result in the same eyeful. I read the big `0 RESULTS` first because it's the biggest thing on the screen, and for a second I concluded the site has no returns information at all. I understand it means "no *products* called returns" — but I wasn't shopping for a product called returns, and nothing on the screen says the two lists are different things. If I'd been on the bus I'd have closed the tab here.
**Next:** hesitated

### Step 7 — Tapped `START A RETURN`, since it was the only thing on offer
**Did:** Tapped it.
**Got:** A **new tab** on a completely different website — `5wn03tnm.aftership.com`. Light grey, white rounded card, chunky condensed capitals, pill-shaped buttons. `Returns Center`. Two empty boxes: `ORDER NUMBER` and `EMAIL`. Under them `VERIFY BY POSTAL CODE OR PHONE NUMBER` and a big greyed `FIND YOUR ORDER`. (`audit/screens/12-06-aftership.png`)
**Expected:** The returns policy.
**Felt:** This is where I nearly left, and I want to be precise about why. It isn't that it's a form — it's that **I have nothing to put in it.** It's asking me for an order number when the entire reason I'm here is that I haven't ordered yet. It's asking me to prove I'm a customer in order to find out whether I want to become one. And it's on someone else's website, in a new tab, in a completely different design — rounded corners and a soft grey, after ten minutes of a black terminal. The handcuffs logo is at the top, so I believed it was still them, but every other signal said I'd been handed off. My honest reaction, out loud, was *"I don't have an order number, that's the whole point."*
**Next:** hesitated — very close to gave up

### Step 8 — Found one line at the very bottom and tapped it out of stubbornness
**Did:** Before closing the tab I scrolled the last inch and read the small print under the button: "We accept returns of unused and undamaged items according to our return policy." with `VIEW RETURN POLICY` underlined below it. It sits at the very bottom of the phone screen, 790px down an 844px screen — one line above the fold's edge. I tapped it.
**Got:** `Return and Exchange policy FAQ` — "Frequently asked questions about returns, refunds, and exchanges." And it says: items are returnable "**Within 30 days from the date of purchase**"; if faulty, "reach out to us within **7 days** of the delivered date"; non-returnable items are "Gift cards" and "Discounted items (if applicable)". (`audit/screens/12-06b-return-policy-from-portal.png`)
**Expected:** CROOKSLDN's returns policy.
**Felt:** At the time: relief, I finally had numbers. Twenty minutes later, when I read the actual CROOKSLDN policy and it said **14 days**, not 30 — that relief turned into distrust. This page is generic. "Gift cards" and "discounted items" and "store credit" are mentioned; this shop doesn't visibly sell gift cards. It reads like a template nobody filled in, and it is the *only* returns text the word "returns" ever put in front of me. Two different numbers from two pages the same shop sent me to is the sort of thing that makes you screenshot it and not buy.
**Next:** went back

### Step 9 — Closed the tab, landed back on `0 RESULTS`
**Did:** Closed the AfterShip tab.
**Got:** Straight back to `SEARCH: RETURNS / 0 RESULTS / NO ITEMS IN THE REGISTER MATCH THAT QUERY.`
**Expected:** —
**Felt:** Coming back to a screen that says zero results, after a round trip to a stranger's site, is a bleak little moment. Nothing about it invites another go.
**Next:** continued — but this was my last unit of goodwill

### Step 10 — Tried a different word: `delivery`
**Did:** Cleared the box, typed `delivery`. Reasoning: if it won't tell me about sending things back, maybe the page about sending things out mentions it.
**Got:** A much fuller list — `SHIPPING POLICY` (`POLICY`) at the top under a `PAGES` heading, then six products with prices under `ITEMS`: `BLUE WASH JORTS £50`, `CHARCOAL CELLBLOCK SHORTS £45`, `V2 BAGGIES £60`, and so on. (`audit/screens/12-07-type-delivery.png`)
**Expected:** Something. Anything more than one row.
**Felt:** Immediately better. Prices next to the names, which is more than most search boxes give you. The one policy link is at the top where I'd look.
**Next:** continued

### Step 11 — Tapped `SHIPPING POLICY`
**Did:** Tapped it.
**Got:** A real page, in the site's own black-and-monospace, headed `SHIPPING POLICY` / "Shipping & Delivery" / "We ship fast and keep you tracked the whole way." Then plain paragraphs: "Free UK shipping over £20, and free Tracked 24 over £70. Under that: standard £3, Tracked 24 £4.99." … "Order before 18:00 (Mon–Sat) and it goes out the same day" … "Once dispatched: UK 1–2 working days, international 7–14." (`audit/screens/12-08-shipping-policy.png`)
**Expected:** Delivery times.
**Felt:** This is the first time all journey that a search actually **answered** me. Two taps, real information, written like a person wrote it rather than a lawyer. "Lost or damaged? That's on us to sort" is a good sentence. The word "refund" does appear — but only for lost or damaged parcels, not for "these don't fit." So: a proper answer to a question I hadn't asked, and still nothing on the one I had.
**Next:** continued

### Step 12 — Tried `size`
**Did:** Back to search, typed `size`. Half looking for the returns clause that usually sits next to sizing advice, half wanting the measurements anyway.
**Got:** `SIZE GUIDE` (`SIZING`) at the top, then six products. (`audit/screens/12-09-type-size.png`)
**Expected:** A size chart.
**Felt:** Promising. `SIZE GUIDE` is exactly the label I wanted.
**Next:** continued

### Step 13 — Tapped `SIZE GUIDE` and got a wall of closed questions
**Did:** Tapped it.
**Got:** Not a size guide — the FAQ page, at the very top, scrolled to zero. `COMMONLY ASKED QUESTIONS`. Fourteen questions, **every single one closed**, each a line of text with a `+` on the right. The page is roughly three phone screens tall. The first six are all about delivery. `SIZING` is the second group heading, below the fold. (`audit/screens/12-10-faq-landing.png`)
**Expected:** A measurements table, given the link said `SIZE GUIDE`.
**Felt:** Deflating. I tapped a link labelled SIZE GUIDE and got dropped at the top of a list of fourteen headlines I now have to read through, none of which is showing me anything. It didn't take me *to* the size guide, it took me to the building the size guide is in and left me in the lobby. On a phone that is a scroll, then a squint, then a tap, and I've already spent my patience twice today.
**Next:** hesitated

### Step 14 — Scrolled the FAQ and spotted a group heading called RETURNS AND REFUNDS
**Did:** Scrolled down past `DELIVERY` and `SIZING` and saw `RETURNS AND REFUNDS`, with `CAN I RETURN SOMETHING?` under it — about a screen and a bit down. Tapped it open.
**Got:** It opened, and finally: "Yes. Start your return here — it takes your order number and email. **You have 14 days from delivery to tell us, and 14 days from then to post it back, unworn and with tags attached. Return postage is yours** — change of mind, wrong size, a swap, any reason of your own. We only cover it if the item was faulty or we sent the wrong thing." and then "Full detail is on the terms page." (`audit/screens/12-11-faq-scrolled.png`, `audit/screens/12-12-faq-returns-open.png`)
**Expected:** By now, honestly, nothing.
**Felt:** *There* it is. Clear, complete, no weasel words, tells me the bad news (I pay return postage) without hiding it. This is a good answer. And I got to it by searching for the word **size**, on a page I reached through a link labelled **SIZE GUIDE**, having scrolled past six questions about delivery. Nothing about that route was designed for me; I found it by wandering.
**Next:** continued

### Step 15 — Tried the last word I had: `refund`
**Did:** Back to search. Typed `refund`, mostly to see if the site had been hiding something under a word I hadn't thought of.
**Got:** Two rows this time: `START A RETURN` (`RETURNS CENTRE`) and — there it is — `REFUND POLICY` (`POLICY`). (`audit/screens/12-13-type-refund.png`)
**Expected:** The same single AfterShip link as `returns`.
**Felt:** Mild disbelief. It has had a `REFUND POLICY` page this whole time. `returns` didn't offer it. `refund` does. The difference between reaching the answer in two taps and being thrown onto a third-party form is one letter and a guess.
**Next:** continued

### Step 16 — Tapped `REFUND POLICY`
**Did:** Tapped it.
**Got:** `REFUND POLICY` / "Returns & Refunds" / "We want you in the right fit. If something's not right, we'll sort it." Then: "Changed your mind or wrong size? **You have 14 days from delivery to return or exchange any unworn item with tags on. Return postage is paid by you** — that covers a change of mind, the wrong size, a swap, or any other reason of your own. **There is no fee for a UK size swap itself, and we cover the postage sending the new size out to you.**" Plus faulty items covered both ways, "approved refunds land on your original payment method within 5–7 days", and "Items marked final sale are clearly labelled and can't be returned." (`audit/screens/12-14-refund-policy.png`)
**Expected:** The answer.
**Felt:** This is the page I came for, and it's a good page. Short, plain, tells me the cost, and the size-swap line is actually generous — they pay to send the replacement out. Two taps from the search box. If `returns` had shown me this I'd have been done in forty seconds and probably buying by now.
**Next:** continued

### Step 17 — Read the returns address twice
**Did:** Re-read the paragraph: "For returns please return to: **Oairo Uk Office**, Bourne end Business Park, Bourne End, Buckinghamshire, United Kingdom, SL8 5AS."
**Got:** That address, as written. (`audit/screens/12-14b-refund-policy-full.png`)
**Expected:** The shop's own name on the address.
**Felt:** Small thing, but it lands wrong. I'd be posting £60 of denim back to a company called "Oairo" that I've never heard of, at an address written half in capitals and half not ("Bourne end"). I know third-party warehouses exist. It still reads like the policy was copied from somewhere and not proofread, which is exactly the doubt a small unknown label can least afford.
**Next:** continued

### Step 18 — Noticed the footer, and did the sums on what I'd been told
**Did:** Scrolled to the bottom of the refund policy page.
**Got:** A footer with `QUESTIONS · TERMS · SHIPPING · REFUNDS · TRACK ORDER · CONTACT` sitting there, `REFUNDS` pointing straight at the page I was already on.
**Expected:** —
**Felt:** Two things at once. One: it was in the footer the entire time, and I'd have found it in one tap if I were a footer person — I'm not, and neither is anyone on a phone. Two, and worse: I have now been told **14 days** by this shop's own policy and **30 days** by the page this shop's own search sent me to first. Both can't be right. I don't know which one I'd be held to, and I'm not going to email to find out.
**Next:** gave up on buying today

---

## Outcome

**Bought / didn't:** Didn't. Not because of the policy — the policy is fine, arguably better than fine — but because it took four different words and a trip to a stranger's website to read it, and the first version I was shown says something different from the real one. I got my answer; I lost my confidence on the way to it.

**Total time:** About five minutes, of which the first ninety seconds felt like the site had nothing at all.

**Worst moment:** Step 7, the `Returns Center` form. *"I don't have an order number, that's the whole point."* The single word `returns` — which is what everybody types — produces exactly one destination, and that destination is a locked door on another company's website that asks me to prove I'm already a customer. That is the one query this search box most needs to answer, and it's the only one that ends off-site.

Runner-up, and nearly as bad: `SEARCH: RETURNS` sitting directly under `0 RESULTS` and `NO ITEMS IN THE REGISTER MATCH THAT QUERY`. I believed the zero before I believed the link above it.

**Best moment:** Typing `refund` and having `REFUND POLICY` appear before I'd finished the word — then two taps to a genuinely well-written page that told me the cost of returning something in one sentence, in normal English, with no small print. Also the header: the word `SEARCH` written out, next to `CATALOGUE`, no icon-guessing, no hamburger. And the search page having three useful links on it *before* I typed anything, instead of an empty grid.

**Would they come back?** Yes, for the clothes — the catalogue looks like nothing else and the prices are right there in the search suggestions, which I liked. But I'd come back and go straight to the footer, because I now know search can't be trusted with the word "returns". That's a shame: the search box is the best-built part of this site and I've learned to route around it.

**One thing that would have changed the outcome:** Make `returns` show `REFUND POLICY` — the shop's own page, in the shop's own voice — at the top, with `START A RETURN` beneath it for people who actually have an order. Same list, same design, one extra row. `refund` already does exactly this. That single change turns my worst moment into my best one and saves five minutes, a third-party tab, and a contradiction about whether I have 14 days or 30.
