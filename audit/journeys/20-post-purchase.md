# 20 — Marcus, paid £60 for jeans four days ago and wants to know where they are

**Device:** mobile 390×844, ordinary 4G · **Goal:** find out where the parcel is — and, because he's started to worry they'll be too big, find out how to send them back · **Mood:** not angry, mildly twitchy. Doing this standing up, one hand, expecting it to take thirty seconds

---

### Step 1 — Opened the site cold, on a phone, wanting one number: a delivery date
**Did:** Typed the shop in from my order confirmation and waited.
**Got:** About nine seconds of near-nothing, then everything at once. Top strip: `FREE UK SHIPPING OVER £20 — ORDER BY 18:00 FOR SAME-DAY DISPATCH`. Under it the handcuffs, then `> 12 PRODUCTS AVAILABLE TO PURCHASE`, `CROOKSLDN`, `OWN THE STREETS™`, a purple `CATALOGUE` button. Then a `COOKIE CONSENT` panel rose over the bottom of the screen — it starts 485px down an 844px screen, so it eats the bottom 43%, and it lands on top of the catalogue grid. (`audit/screens/20-01-arrival.png`, `20-00-home-11s.png`)
**Expected:** A shop with a "track my order" link somewhere near the top.
**Felt:** Everything on this page is aimed at someone who hasn't bought yet. Free shipping over £20, order by 18:00, 12 products available — I've already done all that. I'm the one customer this homepage has nothing to say to. I sat there for eleven seconds to see if anything else would appear and nothing did, just the cookie panel.
**Next:** continued

### Step 2 — Declined the cookies to get my screen back
**Did:** Tapped `Decline`.
**Got:** Panel gone. Homepage, catalogue starting underneath. (`audit/screens/20-02-home-clear.png`)
**Expected:** That.
**Felt:** Fine — `Accept` and `Decline` are both proper buttons, same size, no hidden "manage preferences" maze. But it is Shopify's own wording sitting in this shop's typeface — "We and our partners, including Shopify, use cookies…" — and after four days of waiting for a parcel it's one more thing between me and the answer.
**Next:** continued

### Step 3 — Scanned the header for anything that means "my order"
**Did:** Read the top row without tapping: `CATALOGUE  SEARCH  BAG [0]  LIGHT MODE  MENU`.
**Got:** Nothing about orders. The nearest thing is `BAG [0]`.
**Expected:** An "Orders" or "Track" word in the header, or an account icon.
**Felt:** Small thing that landed harder than it should: I gave this shop £60 four days ago and the only thing on screen that refers to me says `[0]`. There is no word up there for a person who has already bought.
**Next:** continued

### Step 4 — Opened MENU (tap 1)
**Did:** Tapped `MENU`.
**Got:** A drawer: `SHOP`, then `ALL NEW TEES DENIM SWEATS TRACKSUITS ACCESSORIES`, then `TRACKING`, `QUESTIONS`, `TERMS`, `CONTACT`, then `PLAY CASE:001 NOW`, then `ACCOUNT` and `BAG [0]`. (`audit/screens/20-04-menu-open.png`)
**Expected:** To have to hunt.
**Felt:** Relief. `TRACKING` is right there, spelled out as a word, ninth item down but unmissable because the seven above it are all collections. This is the one part of the whole journey that behaved exactly as I hoped.
**Next:** continued

### Step 5 — Tapped TRACKING (tap 2)
**Did:** Tapped `TRACKING`.
**Got:** Four seconds, then `/pages/tracking`:

> `CROOKSLDN PROPERTY TRANSFER NETWORK`
> `> CHAIN OF CUSTODY DATABASE ONLINE`
> **`IDENTIFICATION REQUIRED`**
> "Order records are released to the account they were filed under. Sign in to view the chain of custody for your orders."
> `SIGN IN`
> `NO ACCOUNT? THE TRACKING LINK IN YOUR DISPATCH EMAIL OPENS YOUR ORDER WITHOUT ONE.`

(`audit/screens/20-05-tracking.png`, `20-05b-tracking-full.png`)
**Expected:** A box. Order number, email, Track. That is what every shop does.
**Felt:** Two taps to get here and then a locked door. There is **no form on this page.** Not a box, not a field, nothing to type into — I checked twice, and the only thing on the whole page you can tap is the purple `SIGN IN`. And the page is *empty*: five lines of text, then a long stretch of black nothing, then the footer. It reads like a screen that was built for signed-in people and never finished for the rest of us.

The wording is the other problem. `IDENTIFICATION REQUIRED` is a great line on a T-shirt. Aimed at someone who has already paid and is anxious, it's a bouncer. I know it's a bit, I still felt told off.
**Next:** hesitated

### Step 6 — Read the small line at the bottom twice
**Did:** Squinted at the grey line under the button: `NO ACCOUNT? THE TRACKING LINK IN YOUR DISPATCH EMAIL OPENS YOUR ORDER WITHOUT ONE.`
**Got:** That, in 9px type — the smallest text on the page by some distance. The `IDENTIFICATION REQUIRED` headline above it is enormous by comparison.
**Expected:** —
**Felt:** This is the only good news on the page and it's set smaller than everything else, including the fiction. The one sentence that tells me I'm not locked out is the one I nearly missed. Also — it's an instruction to go and use a different app. The site's answer to "where is my parcel" is "look in your email".
**Next:** continued

### Step 7 — Tapped SIGN IN anyway (tap 3), because I might have an account and not remember
**Did:** Tapped the purple `SIGN IN`.
**Got:** Eight seconds — long enough that I checked the top of the screen — then a page on a **different address**, `friendsof.crooksldn.com`: `CROOKSLDN` / `Sign in` / "Sign in or create an account" / an `Email` field / "By continuing, you agree to our Terms of service" / `Submit`. (`audit/screens/20-06-signin.png`)
**Expected:** Email and password.
**Felt:** Two things. One, `friendsof.crooksldn.com` is not a name I recognise from anything I've been sent, and I'm on a page about my money — I looked at it a beat longer than I'd like to admit. Two, and this is the killer: **there's no password. It emails you a code.** So the route is: go to my email, wait for a code, come back, sign in, find the order. Versus the route the small print already gave me: go to my email, find the dispatch email, tap the tracking link. The account is strictly *more* steps than the email, for the same information. I stopped here.
**Next:** went back

### Step 8 — Tried ACCOUNT in the menu, on the off-chance it was different
**Did:** Back, `MENU`, `ACCOUNT`.
**Got:** The same `friendsof.crooksldn.com` sign-in page. (`audit/screens/20-19-account.png`)
**Expected:** Maybe an order lookup.
**Felt:** Same door, second handle. Fine, that's normal — but it confirms there is exactly one way in and I don't have the key on me.
**Next:** continued

### Step 9 — Went to the FAQ, because I was now sure I'd missed something
**Did:** `MENU` → `QUESTIONS`, then tapped `HOW DO I TRACK MY ORDER?` under `DELIVERY`.
**Got:**

> "Tracking is emailed the moment your parcel is dispatched. **You can also look your order up on the tracking page — no account needed.**"

(`audit/screens/20-07b-faq-tracking-answer.png`)
**Expected:** Confirmation of what the tracking page told me.
**Felt:** I read that sentence, then went back to the page I'd just left, which says, in the biggest type it has:

> `IDENTIFICATION REQUIRED` — "Order records are released to the account they were filed under. **Sign in** to view the chain of custody for your orders."

Those two things cannot both be true. The FAQ says *look your order up on the tracking page, no account needed*. The tracking page has **nothing to look anything up with** — no order number field, no email field, no form of any kind, one button and that button is `SIGN IN`. So I didn't miss it. It isn't there.

That's the moment my mood changed. Up to then I was mildly inconvenienced. After that I was being told something that wasn't so, by the shop, about my own £60.
**Next:** hesitated

### Step 10 — Checked the guest-checkout answer, since I checked out as a guest
**Did:** Opened `DO I NEED AN ACCOUNT TO ORDER?`
**Got:** "No. **You can check out as a guest and still track your order.** An account just saves your details and keeps your order history in one place." (`audit/screens/20-07c-faq-account-answer.png`)
**Expected:** —
**Felt:** Same promise, second time, and this one is aimed *specifically* at me. I did exactly what it invited me to do — checked out as a guest — and the tracking page's first line is that records are released to the account they were filed under. I don't have an account for them to be filed under. Nothing on this site will ever show me this order.
**Next:** continued

### Step 11 — Tapped "the tracking page" inside the FAQ answer (tap 4 from home)
**Did:** The words "the tracking page" in that answer are a link, so I took it.
**Got:** `IDENTIFICATION REQUIRED`. Again. (`audit/screens/20-05c-tracking-from-footer.png` is the same page reached from the footer)
**Expected:** Given the sentence I'd just read — a lookup form.
**Felt:** The FAQ walked me into the wall itself. That's worse than the FAQ being vague, because I trusted the sentence enough to take its link.

**What I'd have done next in real life:** given up on the website, opened my email app and searched "CROOKSLDN" for the dispatch mail. If that hadn't turned it up, emailed `crooksldn@gmail.com` — which is the only contact the site offers — and, per their own FAQ, waited "1–2 working days" for a reply about a parcel that's already four days out. That is the actual support cost of this page.
**Next:** continued, but now I was just testing the site rather than trusting it

### Step 12 — Tried search, as the third route in (2 taps)
**Did:** Home, `SEARCH`, typed `where is my order`.
**Got:** The search page opens with the keyboard already up and a `DIRECT LINKS` block *before* you type anything: `START A RETURN — RETURNS CENTRE`, `TRACK YOUR ORDER — TRACKING`, `QUESTIONS — FAQ`. Typing `where is my order` produced one suggestion under `PAGES`: `TRACK YOUR ORDER — TRACKING`. (`audit/screens/20-09-search.png`, `20-10-search-whereismyorder.png`)
**Expected:** Nothing useful — search boxes usually only know products.
**Felt:** Genuinely impressive, and completely wasted. It understood a whole sentence of ordinary English, and the destination it's so confident about is the door I can't open. Two taps to the same wall.
**Next:** continued

### Step 13 — Checked the footer, which is where I'd have looked third
**Did:** Scrolled to the bottom of the homepage.
**Got:** Four columns. `INFORMATION` holds `QUESTIONS`, `TERMS`, `SHIPPING`, `REFUNDS`, `TRACK ORDER`. (`audit/screens/20-03-footer.png`, `20-18-footer-again.png`)
**Expected:** A tracking link, maybe a returns one.
**Felt:** `TRACK ORDER` is there and it's one tap once you're at the bottom — good. But there is **no "start a return" anywhere in the footer**. `REFUNDS` takes you to the policy *text*, which tells you the rules and gives you nothing to do. If I were a footer person — and post-purchase people are footer people, it's where "contact" and "orders" always live — I'd have concluded this shop has no returns process at all.
**Next:** continued

### Step 14 — Started the return: search → START A RETURN (2 taps)
**Did:** `SEARCH`, typed `return`, tapped `START A RETURN`.
**Got:** One suggestion, `START A RETURN — RETURNS CENTRE` (`audit/screens/20-11-search-return.png`), and tapping it opened a **new tab on another company's website**: `5wn03tnm.aftership.com`. Seven seconds to load.
**Expected:** A returns page on the shop.
**Felt:** Two taps is fast, I'll give it that — faster than tracking, which is funny, because returning is the thing that costs them money.
**Next:** continued

### Step 15 — Looked at where I'd landed
**Did:** Read the page.
**Got:** Light grey background, big white rounded card, chunky condensed capitals, pill-shaped buttons. `Back to shop` top left, a hamburger top right. The handcuffs logo, then `Returns Center`, `ORDER NUMBER`, `EMAIL`, `Verify by postal code or phone number`, a greyed-out `FIND YOUR ORDER`, and at the very bottom "We accept returns of unused and undamaged items according to our return policy." with `VIEW RETURN POLICY`. (`audit/screens/20-12-returns-portal.png`, `20-12b-returns-portal-full.png`)
**Expected:** Something that looked like the shop.
**Felt:** It's the opposite of the shop in every respect — where CROOKSLDN is black, square-cornered and typewriter-ish, this is pale grey with rounded everything and a completely different typeface. The handcuffs at the top are the only reason I believed I hadn't been phished. That logo is doing an enormous amount of work.
**Next:** continued

### Step 16 — Hit a second cookie banner, on top of the form
**Did:** Went to type my order number.
**Got:** A cookie panel in red buttons covering the bottom 39% of the screen — `Accept all cookies`, `Reject non-essential cookies`, `Manage preferences`, over text about "first-party and third-party cookies" and a `Cookie Policy` link that goes to automizely.com. It sits **directly over the Email field and the FIND YOUR ORDER button** — only the top of `ORDER NUMBER` is visible above it. (`audit/screens/20-12d-portal-consent.png`)
**Expected:** To type.
**Felt:** Second cookie consent in one journey, in a completely different design, from a company whose name I've now seen three of (CROOKSLDN, AfterShip, Automizely). I tapped `Reject non-essential cookies` without reading it. If I'd been in a hurry I'd have assumed the form was broken, because the button you need is underneath the thing you have to dismiss.
**Next:** continued

### Step 17 — Filled it in as far as I could and pushed the button
**Did:** Put in an order number I part-remembered (`1001`) and my email, then `FIND YOUR ORDER`. The button goes from grey to blue when both fields are full, which is at least honest about what it needs. (`audit/screens/20-13-returns-filled.png`)
**Got:** An amber box above the fields:

> "**We couldn't find that order. Please check your order number or email address.**"

(`audit/screens/20-14-returns-error.png`)
**Expected:** That, since I guessed the number.
**Felt:** The message is clear and polite, no complaints there. But look where I am: the *only* route to a return needs the order number, and the order number is in — the same email I was told to go and find for tracking. Everything this shop can do for me after I've paid lives in my inbox, not on the site. And this door doesn't even offer the "we'll email you a link" escape hatch that the tracking page at least mentions.
**Next:** continued

### Step 18 — Tapped VIEW RETURN POLICY, at the very bottom of the card
**Did:** Scrolled to the last line and tapped `VIEW RETURN POLICY`.
**Got:** `Return and Exchange policy FAQ` — "Frequently asked questions about returns, refunds, and exchanges." Items are returnable "**Within 30 days from the date of purchase**". If damaged, "reach out to us within **7 days** of the delivered date". Non-refundable: "**Gift cards**", "**Discounted items (if applicable)**". Refunds "processed within 5 - 7 working days after approval". (`audit/screens/20-15-portal-policy.png`)
**Expected:** CROOKSLDN's returns terms.
**Felt:** Nothing on that page sounds like the shop I bought from. It's a template — it offers "Refund to store credit (if applicable)" and mentions gift cards, and I never saw a gift card anywhere on this site. And the numbers are wrong. I had already read the shop's own `TERMS`, and it says something different.
**Next:** continued

### Step 19 — Went back and read the shop's own terms to be sure I hadn't imagined it
**Did:** `MENU` → `TERMS` → clause `03 RETURNS`.
**Got:** (`audit/screens/20-17-terms.png`, `20-17b-terms-returns-clause.png`)

> `03 RETURNS` — "You have **14 days from delivery** to tell us you want to return something, and 14 days from then to post it back. Start your return here: **the returns centre**. It takes your order number and email… Return postage is paid by you."
> `05 FAULTS AND WRONG ITEMS` — "For transit damage, tell us within **48 hours** of delivery…"

And the shop's `REFUND POLICY` page: "**You have 14 days from delivery** to return or exchange any unworn item with tags on… **Message us within 14 days** and we'll refund or replace it in full" for faulty items. (`audit/screens/20-16-refund-policy.png`)
**Expected:** The same numbers as the portal.
**Felt:** So I have been given, by one shop, in one sitting:

- **14 days** to return (shop's terms + refund policy) vs **30 days** (the portal the shop's own terms link me to).
- Faulty: **14 days** (refund policy), **48 hours** for transit damage (terms clause 05), **7 days** (portal).
- Non-returnable: "**final sale**, clearly labelled" (shop) vs "**Discounted items (if applicable)**" (portal).

That last one is the one that would actually cost them. If I'd used a discount code, the page they sent me to says my jeans might not be returnable at all, and their own terms say nothing of the kind. I would not know which set of rules I'd be held to, and I'd have screenshotted both before posting anything back.

The wording in clause 03 is also quietly optimistic: "It takes your order number and email, **and issues the return**". It didn't issue anything. It said it couldn't find me.
**Next:** done

---

## Outcome

**Tracked / didn't:** **Didn't — and can't.** For a signed-out guest there is no way to see this order on this website at all. The tracking page has no lookup, only `SIGN IN`, and signing in needs an emailed code, which means opening the inbox that already contains the tracking link. The site's own advice, in 9px, is to go and use my email instead. It is honest advice and it is a website telling me it can't help me.

**Started a return / didn't:** **Didn't.** I got to the portal and to the error message, which is as far as anyone gets without the order number from their email. The portal itself works — it took my input, validated it and told me plainly what was wrong.

**The tap counts, which were the point:**

| | Taps from the homepage | Does it work signed out? |
|---|---|---|
| Reach `/pages/tracking` via `MENU` → `TRACKING` | **2** | No — sign-in wall |
| via `SEARCH` → `TRACK YOUR ORDER` | **2** | No — same wall |
| via the footer `TRACK ORDER` (once scrolled down) | **1** | No — same wall |
| via `MENU` → `QUESTIONS` → the tracking Q → "the tracking page" | **4** | No — same wall, and the FAQ promised otherwise |
| **Actually see where the parcel is** | **∞** | **No. Not possible.** |
| Reach the returns portal via `SEARCH` → `START A RETURN` | **2** | Yes, it opens |
| via `MENU` → `TERMS` → "the returns centre" | **3** | Yes |
| via `MENU` → `QUESTIONS` → the returns Q → "Start your return here" | **4** | Yes |
| via the footer | **not there at all** | — |
| **Actually start a return** | **4** (2 + dismiss its cookie wall + `FIND YOUR ORDER`) | **Only with the order number from the email** |

**Not tested, and I want to be straight about it:** I never saw the signed-in view. No login was available to me, so the three-stage timeline (`01 Logged / 02 In transit / 03 Delivery`), the courier record with the carrier and tracking number and its track button, and the custody log are **untested** — I can't say whether they're good, bad or broken, only that nothing a signed-out customer can do will reveal them. The dispatch-email tracking link is **untested** too: no order, no email, no way to check whether that promise holds either.

**Total time:** About seven minutes, of which maybe forty seconds was useful.

**Worst moment:** Step 9. Reading "You can also look your order up on the tracking page — **no account needed**" in the FAQ, and then looking at a tracking page whose only interactive element is `SIGN IN`. Out loud: *"There's nothing to look it up **with**."* It's not that the feature is missing — plenty of small shops make you use the email link. It's that I was told twice, in writing, that I could do a thing this site cannot do, and one of those times was on a link that took me straight to the proof.

Close behind: `IDENTIFICATION REQUIRED` in huge letters at a paying customer who just wants a delivery date. Everywhere else this shop's fiction is a pleasure. Here it's a locked door with a joke written on it, and I'd already paid.

**Best moment:** Genuinely — the routes in. `TRACKING` written out as a word in the menu, `TRACK ORDER` in the footer, `SEARCH` spelled out in the header, and a search box that took "where is my order" as a whole sentence and answered it correctly. Nobody hunts for anything on this site. Two taps to everything. It's the destinations that let the routes down. The AfterShip error message was clear and blame-free too.

**Would they come back?** To buy again — probably yes, if the jeans fit, because the shop itself is good and I like it. To find out where a parcel is — no, never again. I'd go straight to my email, and if that failed I'd DM the Instagram. I have learned that this website cannot tell me anything about my own order, and I won't spend seven minutes finding that out twice.

**One thing that would have changed the outcome:** Put a real order-number + email lookup on `/pages/tracking` — the returns portal already proves the shop can do exactly that lookup, and the FAQ already promises it. Same black screen, same 1px boxes, two fields and a button where the empty black gap currently is.

If that can't be built, then **delete the promise and raise the small print**: the FAQ must stop saying "no account needed" and "you can check out as a guest and still track your order", and `NO ACCOUNT? THE TRACKING LINK IN YOUR DISPATCH EMAIL OPENS YOUR ORDER WITHOUT ONE.` needs to be the size of the headline, not 9px — with `crooksldn@gmail.com` under it for people who've lost the email. Right now the page's biggest words are a refusal and its smallest words are the answer.

And while it's open: get the 14-day/30-day, 48-hour/7-day/14-day and "final sale"/"discounted items" contradictions off the portal, because the shop's own `TERMS` sends people there and tells them it "issues the return".
