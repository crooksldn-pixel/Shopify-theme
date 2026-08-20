# raw-content-pages — FAQ, Terms, tracking, policies, 404

Area key: `content-pages`. Mobile (390×844), GB market, staging theme `202053779799`
(`CROOKSLDN — Staging`, unpublished) — identity asserted on every run.
Signed out throughout; no test login was supplied.

Scripts: `audit/_tools/content-pages.mjs`, `-2.mjs`, `-3.mjs`, `-4.mjs`.
Raw transcripts: `audit/_tools/.content-pages.log` … `.content-pages-4.log`.

---

### `/pages/faq` — 14 questions, 4 groups

**Should:** 14 questions in 4 groups (Delivery, Sizing, Returns and refunds, Orders and
payment), accordions closed by default (deliberate, `SPEC §9.4`), page owns its h1.

**Did:** All 14 render, in the 4 groups, all closed. Tapping a question opens it and
closes the previous one (`<details name>` exclusivity — one open at a time). The page is
fully on-brand: VT323 headline at 56px, CRX Mono body on `rgb(11,10,14)`, header and
footer present. Copy is genuinely good — short, plain English, no waffle, and it names
prices and timeframes instead of dodging them.

Verbatim, all four delivery answers plus tracking:

> **WHEN WILL MY ORDER BE DISPATCHED?** — "Orders placed before 18:00 are dispatched the
> same day where possible, Monday to Saturday. After 18:00, or on a Sunday, they go out on
> the next dispatch day. Allow up to two working days after a drop."
>
> **HOW LONG DOES DELIVERY TAKE?** — "Once it has left us: 1–2 working days in the UK, 7–14
> working days internationally."
>
> **HOW MUCH IS SHIPPING?** — "Free on UK orders over £20. Over £70 you get Royal Mail
> Tracked 24 free. Below £20 it is calculated at checkout before you pay."
>
> **DO YOU SHIP INTERNATIONALLY?** — "Yes. International orders take 7–14 working days. Any
> customs duties or import taxes are set by your country and are payable by you — we have
> no control over them and cannot refund them."
>
> **HOW DO I TRACK MY ORDER?** — "Tracking is emailed the moment your parcel is dispatched.
> You can also look your order up on the tracking page — no account needed."
>
> **TRACKING SAYS DELIVERED BUT I HAVE NOTHING.** — "Check with neighbours and your safe
> place first, then message us within 14 days of the expected delivery date and we will open
> a courier investigation. Royal Mail take up to 10 working days to complete one."

Verbatim, the returns answers:

> **DO YOU DO EXCHANGES?** — "Yes. You pay the postage sending the original back to us.
> There is no fee for the swap itself, and we cover the postage sending the new size out to
> you. Start it in the returns centre and say which size you want — swaps depend on that
> size being in stock, and if it is not we refund you instead."
>
> **CAN I RETURN SOMETHING?** — "Yes. Start your return here — it takes your order number
> and email. You have 14 days from delivery to tell us, and 14 days from then to post it
> back, unworn and with tags attached. Return postage is yours — change of mind, wrong size,
> a swap, any reason of your own. We only cover it if the item was faulty or we sent the
> wrong thing. Full detail is on the terms page."
>
> **WHEN WILL I GET MY REFUND?** — "Within 5–7 days of us receiving the item, back to the
> payment method you used. Original shipping charges are not refunded unless the item was
> faulty or wrongly sent, and neither is the postage you paid to send it back."
>
> **MY ITEM IS FAULTY OR YOU SENT THE WRONG THING.** — "That is on us. Message us with your
> order number and a photo and we will refund or replace it in full and cover the postage
> both ways. For transit damage, tell us within 48 hours of delivery so we can raise it with
> the courier."

Closing line: *"Still stuck? Email crooksldn@gmail.com or DM @crooksldn with your order
number. We reply within 1–2 working days. The full trading terms are on the terms page."*

**Verdict:** works (with one false promise — see the tracking entry).

**Evidence:** `audit/screens/content-pages-faq-closed-vp.png`,
`content-pages-faq-q1-open.png`, `content-pages-faq-all-open.png`,
`content-pages-faq-clean.png`.

---

### FAQ — questions a shopper would ask that are not answered

**Should:** cover the things that stop a stranger from buying.

**Did:** Fourteen good answers, and these gaps. Each is a real question I had while
shopping the site:

1. **"I checked out as a guest and lost the dispatch email — how do I find my order?"**
   The FAQ answers this with a lookup that does not exist (see the tracking entry). This
   is the single most damaging gap because the FAQ actively points at a dead end.
2. **"How much is international shipping?"** Q4 says international takes 7–14 days but
   never says what it costs. Only the shipping policy answers, and only as *"add your items
   to cart and your shipping is calculated at checkout based on item weight and location."*
   An Irish or Dutch shopper cannot find out what postage costs without building a cart.
3. **"It's sold out in my size — will you restock, and how do I get told?"** Sold-out sizes
   stay selectable by design (`SPEC §9.3`) and there is a notify field on the PDP, but the
   FAQ never mentions restocks, drops or a waitlist. This is the most likely question on a
   12-product drop store.
4. **"I have a discount code — where does it go, and can I use it on the set?"** No
   question about codes at all, on a store that runs `10CROOKS` and an £85 two-piece set.
5. **"How do I wash it?"** Care lives inside the PDP SPECIFICATION accordion
   ("Cold wash inside out. Hang dry.") but a shopper looking in the FAQ finds nothing.
6. **"Who are you and where are you?"** There is no About page anywhere in the nav or
   footer. For a brand with no reviews, the FAQ is the only place that could carry it.
7. **"Can I return a sale item?"** Final-sale exclusions appear in Terms c6 and the refund
   policy but never in the FAQ, which is where a shopper looks before buying.
8. **"Is there a phone number?"** The FAQ offers email and Instagram DM. A phone number
   (+44 7449 010089) exists, but only inside the privacy policy — see below.

**Verdict:** partly.

**Shopper cost:** items 1 and 3 are the ones that lose a sale or generate a support email;
the rest are friction.

**Evidence:** `audit/screens/content-pages-faq-all-open.png` (the full set of 14).

---

### `/pages/terms` — 9 clauses, clause index, LAST REVISED

**Should:** nine clauses in plain English with a clause index and a `LAST REVISED` date,
linking out to the real legal policies.

**Did:** All nine present and in order — 01 CARRIAGE, 02 DISPATCH, 03 RETURNS, 04 SIZE
SWAPS, 05 FAULTS AND WRONG ITEMS, 06 REFUNDS, 07 LOST PARCELS, 08 ORDERS WE CANCEL,
09 CONTACT. Header reads **"LAST REVISED 20.08.2026"** (today — `SPEC §3.10` still says
13.08.2026, so it was revised after the spec was written). The clause index works: tapping
`03 RETURNS` moved the page from scrollY 0 to 1352 and put the RETURNS clause at the top of
the screen; the deep link `/pages/terms#returns` (which the FAQ uses) lands in the same
place. Footer of the page links out to all four legal policies under "THE FULL LEGAL TEXTS".

Clause 03 carries the returns address: *"Returns go to: Oairo UK Office, Bourne End Business
Park, Bourne End, Buckinghamshire, SL8 5AS, United Kingdom."* Clause 08 ends
*"Drops are for people, not scripts."* — the one flourish, and it is on-brand and harmless.

Two things a shopper would notice as missing from a page called TERMS: there is **no
governing-law or company-identity line** (that lives only in the Shopify Terms of Service),
and **no order-cancellation / cooling-off wording framed as a right** — c3 reads as a
returns policy, not as the statutory cancellation right.

**Verdict:** works.

**Evidence:** `audit/screens/content-pages-terms-top.png` (LAST REVISED 20.08.2026),
`content-pages-terms-full.png`, `content-pages-terms-anchor-returns.png`,
`content-pages-terms-deeplink-returns.png`.

---

### `/pages/tracking` — signed out

**Should:** a signed-out state for a page whose real job is the signed-in order lookup.

**Did:** The whole page, signed out, is five lines and one button:

> `> CHAIN OF CUSTODY DATABASE ONLINE`
> **IDENTIFICATION REQUIRED**
> "Order records are released to the account they were filed under. Sign in to view the
> chain of custody for your orders."
> **[ SIGN IN ]**
> "NO ACCOUNT? THE TRACKING LINK IN YOUR DISPATCH EMAIL OPENS YOUR ORDER WITHOUT ONE."

There is **no input, no form, no select — zero form controls on the page**
(`inputs: [], buttons: [], forms: []`). The only link is SIGN IN, which leaves the store for
`https://crooksldn.com/customer_authentication/redirect?...`. There is no link to the FAQ,
no link to the returns centre, and no email address.

**Can a signed-out shopper do anything useful?** No. The only actionable thing is signing
in — and the FAQ has already told them (correctly) that they can check out as a guest, so
many of them have no account to sign into. The one genuinely useful sentence — that the
dispatch email's tracking link works without an account — is set in the smallest type on
the page, in the low-contrast purple, all-caps, below the button, and it is not a link to
anything.

**Is there ANY way to track an order without an account?** Only the dispatch email. Nothing
on the site will find an order from an order number. Ironically the returns centre the FAQ
and Terms both link to (`https://5wn03tnm.aftership.com`) **does** do exactly that lookup —
its form is "ORDER NUMBER / EMAIL / VERIFY BY POSTAL CODE OR PHONE NUMBER / FIND YOUR
ORDER" — so the capability exists on a page the shopper is never sent to when they want
tracking.

**Verdict:** partly (it is an honest, well-written wall, but it is a wall).

**Shopper cost:** a guest whose dispatch email went to spam has no route to their order
except emailing and waiting 1–2 working days. On a site with no reviews, "where is my
order" with no self-serve answer is where trust goes.

**Evidence:** `audit/screens/content-pages-tracking-signedout.png`,
`content-pages-tracking-signedout-full.png`, `content-pages-returns-centre.png`.

---

### Signed-in tracking: timeline + courier record — **UNTESTED**

**Should:** order picker, three-stage timeline (`01 Logged / 02 In transit / 03 Delivery`),
courier record with carrier + tracking number + track button, and a custody log
(`SPEC §3.12`, 38 settings).

**Did:** Not exercised. No test login was supplied and no order may be placed, so none of
the timeline, the courier record, the track button or the custody log was seen. The
signed-out state is the only state confirmed. `/account/login` was reached but the store
answered with a Cloudflare verification page (`"Your connection needs to be verified before
you can proceed"`), which this environment cannot complete.

**Verdict:** UNTESTED — record only.

**Evidence:** `audit/screens/content-pages-account-login.png`.

---

### The policy pages — do they look like the same site?

**Should:** `/policies/*` cannot take sections and is CSS-skinned only (`SPEC §2`).

**Did:** They look like the same site. All five render inside the full Crooks chrome —
announcement bar, status bar, handcuff logo, CATALOGUE / SEARCH / BAG / LIGHT MODE / MENU
header, and the four-column footer. The headline uses the same VT323 display face at the
same 56px as the FAQ h1; body copy is CRX Mono in the same `rgb(221,215,201)` on near-black.
A shopper would not know these pages are a different system.

Two tells, both minor: policy body copy is 13px against the FAQ's 10px (the policy pages are
actually the more readable), and `<body>` on a policy page computes to
`rgb(244,241,234)` — cream — while the FAQ's body computes to `rgb(11,10,14)`. The dark
ground on the policy pages is painted by a wrapper, not the body, so anything that renders
outside that wrapper falls back to the light palette. The visible symptom today is the
cookie-consent sheet, which renders in monospace on the FAQ and in a plain sans-serif on the
policy pages.

**Verdict:** works.

**Evidence:** `audit/screens/content-pages-policy-shipping-clean.png` (full page — the
requested screenshot), plus `content-pages-policy-refund-policy.png`,
`content-pages-policy-privacy-policy.png`, `content-pages-policy-terms-of-service.png`,
`content-pages-policy-contact-information.png`.

---

### `/policies/contact-information` — the best contact page on the site, linked from nowhere

**Should:** be findable, since it is the page that answers "how do I reach you".

**Did:** It is the strongest customer-service copy on the store — reply times, what to
include, and three quick answers:

> "BEST WAY TO REACH US — Email — Crooksldn@gmail.com
> We reply within 1–2 working days (Mon–Sat). To get help fastest, include your order number
> and a quick line on what's up — plus a photo if it's about a faulty or wrong item."

And it is unreachable. I checked every link on `/`, `/pages/faq`, `/pages/terms` and
`/pages/contact`: **none links to `/policies/contact-information`**. The footer's CONTACT
column contains INSTAGRAM, TIKTOK and EMAIL only. Terms c9 links to the other four policies
under "THE FULL LEGAL TEXTS" and skips this one. A shopper reaches it only by typing the URL
or by finding it in Shopify's checkout footer.

Worse, the page ends with:

> "Prefer a form? Drop your details below and we'll come back to you at the email you give
> us."

**There is no form below it.** Policy pages cannot hold sections, so below that sentence is
the site footer. The page invites an action it cannot offer.

**Verdict:** partly (excellent content, unreachable, and it promises a form that isn't
there).

**Shopper cost:** the store looks like it has no contact information because the page that
has it is invisible.

**Evidence:** `audit/screens/content-pages-policy-contact-clean.png` — the "Prefer a form?"
line with the footer directly beneath it.

---

### `/pages/contact` — the page the menu actually sends you to

**Should:** be where a shopper who taps CONTACT gets help.

**Did:** It is Horizon's untouched `page.contact` template. The whole page, top to bottom,
is: `CONTACT / Name / Email* / Phone / Comment / Submit`. I probed `main` for any contact
detail: `hasAt: false, hasPhone: false`. **No email address, no postal address, no phone, no
reply-time, and no confirmation of what happens after Submit.**

It also does not look like the site. The header above it is the dark evidence terminal; the
page itself is cream with a sans-serif "CONTACT" heading and grey rounded form boxes. The
two pages a worried shopper is most likely to land on — this one and the 404 — are the two
that break the design law.

**Verdict:** partly.

**Shopper cost:** a shopper who wants to *know* how to reach the brand (not fill in a form)
taps CONTACT and gets less information than before they tapped.

**Evidence:** `audit/screens/content-pages-cold-02-contact.png`,
`content-pages-contact.png`.

---

### `/products/does-not-exist` — the 404

**Should:** get a lost shopper back to shopping.

**Did:** Status 404, title `404 Not Found – CROOKSLDN`, single h1 `PAGE NOT FOUND`. The copy
is *"The link may be incorrect, or the page has been removed."* with a `Continue shopping`
button to `/collections/all`, followed by a **"Discover something new"** row of four real
products with prices (Charcoal Cellblock Crewneck £50.00, Cellblock Shorts £45.00, Blue Wash
OG Jeans £60.00, Blue Wash Jorts £50.00), all linking to live PDPs. The Crooks header and
footer are both there, so CATALOGUE, SEARCH, MENU and every footer link still work.

So functionally it is **not** a dead end — you can get back to shopping in one tap, and four
of the twelve products are on screen.

The problem is that it does not look like this store. Horizon's default body renders cream
with sans-serif type and a solid black button, sandwiched between the dark monospace header
and the dark monospace footer. The one page whose job is to say "something went wrong"
is the page that looks like something went wrong — as if the shopper had been bounced onto a
different site. There is also no search box in the body, which is the obvious thing to offer
someone who followed a broken product link.

**Verdict:** partly.

**Shopper cost:** low on navigation, real on trust — a mis-typed or stale link (an old
Instagram post, a dead drop URL) is exactly when a stranger is deciding whether this store is
real.

**Evidence:** `audit/screens/content-pages-404-vp.png`, `content-pages-404-full.png`.

---

### Finding the contact details from a cold start

**Should:** a shopper should be able to find out how to reach the brand.

**Did:** Timed from the homepage, signed out, nothing in the bag.

| Route | Taps | What you end up with |
|---|---|---|
| MENU → CONTACT | **2** | A form. No email, no phone, no address. |
| Scroll to footer → EMAIL | **1** | Opens the mail app with the address pre-filled. The address is **never displayed on screen** — if no mail client is configured, the tap does nothing and you learn nothing. |
| MENU → QUESTIONS → scroll past 14 questions to the last line | **2 + a long scroll** | "Email crooksldn@gmail.com or DM @crooksldn" — the first time an address is legible. |
| MENU → TERMS → scroll to clause 09 | **2 + a longer scroll** | Same address. |
| `/policies/contact-information` | **not reachable by tapping** | The page that actually answers the question. |

So: **two taps to a contact page, and zero taps to a contact detail.** The shortest route to
a readable email address is two taps plus scrolling to the bottom of a long page. There is no
phone number anywhere a shopper would look — the only one on the site, **+44 7449 010089**,
is in the last paragraph of the privacy policy, while `/pages/contact` collects a Phone
number without offering one.

**Verdict:** partly.

**Evidence:** `audit/screens/content-pages-cold-00-home.png`,
`content-pages-cold-01-menu.png`, `content-pages-cold-02-contact.png`,
`content-pages-home-footer.png`.

---

### The email address — every occurrence checked

**Should:** one address, spelled the same way everywhere.

**Did:** I extracted every email string and every `mailto:` from the homepage, footer,
`/pages/faq`, `/pages/terms`, `/pages/tracking`, `/pages/contact`, three PDPs, and all five
policy pages. Result:

| Where | What it says |
|---|---|
| Footer EMAIL link (every page) | `mailto:crooksldn@gmail.com` (address not shown as text) |
| FAQ closing line | `crooksldn@gmail.com` (linked) |
| Terms clause 09 | `crooksldn@gmail.com` (linked) |
| PDP chain-of-custody, all products | `crooksldn@gmail.com` |
| Refund policy | `crooksldn@gmail.com` (plain text, not a link) |
| Shipping policy | `crooksldn@gmail.com` (plain text, not a link) |
| Privacy policy | `crooksldn@gmail.com` (plain text) |
| Terms of service §20 | `crooksldn@gmail.com` (plain text, twice) |
| Contact information policy | **`Crooksldn@gmail.com`** — capital C, twice, plain text |

**The doubled domain suffix is gone.** The reported `crooksldn@gmail.com.com` on the
shipping policy is not there any more — that page now reads *"How: email
crooksldn@gmail.com or DM @crooksldn with your order number."* My extractor would have
caught a doubled `.com` and did not, on any of the twelve surfaces. Worth telling the owner
it is clean, because it is the kind of fix that gets reverted by a copy-paste.

What remains: one capitalisation variant (`Crooksldn@`) on the contact-information page, and
the fact that on all five policy pages **the address is plain text, not a `mailto:` link** —
on a phone that means select-and-copy instead of tap-to-email.

Also worth flagging: `info@crooksldn.com` appears nowhere on the live storefront, so
whichever surface still carries it as a default is not being seen by shoppers.

**Verdict:** works, with a capitalisation nit.

**Evidence:** `audit/screens/content-pages-policy-shipping-clean.png` (single `.com`),
`content-pages-policy-contact-clean.png` (`Crooksldn@gmail.com`), plus the extraction dumps
in `audit/_tools/.content-pages.log`.

---

### THE CROSS-CHECK — Terms vs FAQ vs chain of custody vs product pages vs the real policies

**Should:** every surface tells a shopper the same thing.

**Did:** Five surfaces, six claims. The FAQ and Terms agree with each other almost
everywhere — the drift is between those two and the PDP chain-of-custody accordion, and
between those two and the Shopify policy pages.

| Claim | Terms | FAQ | PDP chain of custody | Policy pages |
|---|---|---|---|---|
| Return window | 14 days to tell + 14 to post | 14 days to tell + 14 to post | "14 days from delivery to return" | Refund: "14 days from delivery to return or exchange"; Contact info: same |
| Who pays return postage | You, unless faulty/wrong | You, unless faulty/wrong | You, unless faulty/wrong | Refund: you, unless faulty/wrong |
| Size swaps | Free, no geography named | Free, no geography named | not mentioned | Refund: "no fee for a **UK** size swap" |
| How to start a return | Returns centre (AfterShip) | Returns centre (AfterShip) | **"Start a return by email"** | Refund: email or DM; Contact info: "Start it by emailing" |
| Dispatch | "same day **where possible**" + "allow up to two working days" after a drop | same hedge | "**are dispatched** the same day" | Shipping: "Order before 18:00 (Mon–Sat) and it goes out the same day" |
| Delivery | UK 1–2, intl 7–14 | UK 1–2, intl 7–14 | UK 1–2, intl 7–14 | UK 1–2, intl 7–14 |
| Faulty / damaged | refund or replace, postage both ways; transit damage **within 48 hours** | same, **48 hours** for transit damage | "unless we sent the wrong thing or it arrived faulty" | Refund + Shipping: "Message us **within 14 days**" |
| Lost parcel | investigation first; "we cannot refund or replace before that investigation closes" | investigation, up to 10 working days | not mentioned | Shipping: "Message us within 14 days and we'll chase the courier **or send a replacement or refund**" |

Delivery times are the one claim that is identical on all five surfaces. Everything else
drifts. Details and both sides of each are quoted in **Contradictions** below.

Two known items I can report as clean: the **V2 BAGGIES description no longer says
"9-16 days delivery uk"** — it now reads *"V2 Baggies — wide, full-length sweats in 500gsm
cotton, heavy enough to hang straight. Made in Portugal."*, which contradicts nothing. And
the refund policy no longer says "Size swaps are free within the UK" as a blanket statement
(O5) — it now says *"There is no fee for a UK size swap itself"*, which is closer, but see
Contradiction 4.

The placeholder measurements (known item) do have a shopper cost here, because FAQ q7 sends
shoppers straight to them: BLUE WASH OG JEANS, GREY WASH OG JEANS and V2 BAGGIES all show
the **identical** table — `XS 76.2cm / 73.7cm / 45.7cm … XL 96.5cm / 81.3cm / 55.9cm`. A
shopper comparing 14oz jeans against 500gsm sweats sees the same waist, inseam and leg
opening to the millimetre, which reads as invented.

**Verdict:** partly.

**Evidence:** `audit/screens/content-pages-pdp-custody-open.png`,
`content-pages-pdp-baggies-open.png`, `content-pages-terms-full.png`,
`content-pages-faq-all-open.png`, `content-pages-policy-refund-policy-full.png`,
`content-pages-policy-shipping-policy-full.png`.

---

## Surprises

- **The FAQ promises an order lookup that does not exist.** FAQ q5 sends the shopper to a
  page that has no form on it at all. This is the one finding I would fix before any other.
- **`/policies/contact-information` — the best support copy on the store — is linked from
  no page on the site**, and it ends by inviting the shopper to use a form that a policy
  page structurally cannot contain.
- **The product page tells shoppers to start a return by email; the Terms and FAQ tell them
  to use the returns centre.** Terms explains the returns centre "issues the return so we
  can match the parcel to you" — so a return started the way the PDP says arrives unmatched.
- **The chain-of-custody accordion is the shortest version of the returns policy and the
  strictest** — "14 days from delivery to return" against the Terms' 14 + 14. It is also the
  version a shopper reads *before* buying.
- The only phone number on the site (+44 7449 010089) is in the final paragraph of the
  privacy policy, while `/pages/contact` asks the shopper for theirs.
- The returns address appears in four different spellings across four pages, one of which
  (privacy policy) reads `Unit M ,, SL8 5as, United Kingdom` — double comma, lower-case
  postcode, no town. That address ends up on a returns label.
- Terms says LAST REVISED **20.08.2026**; the Terms of Service it links to as the "full
  legal text" is dated **13th August 2026**; the privacy policy says **July 11, 2026**. The
  plain-English page is a week ahead of the legal one it defers to.
- The cookie-consent sheet covers the bottom half of the first screen on every content page.
  On the FAQ it lands directly over the first question; on Terms it covers clauses 03
  onward. (Known: "No cookie banner" is listed as an open item — there is one now, and it is
  the first thing on these pages.)
- The `EMAIL` link in the footer is the only contact affordance on most pages, and it never
  shows the address — it only fires a `mailto:`.

## Missing

- Any way for a guest to find an order without the dispatch email.
- A phone number anywhere a shopper would look (FAQ, Terms c9, `/pages/contact`).
- International shipping *cost* — named on no page; "calculated at checkout" is the answer
  on all three.
- Restock / drop-notification answer in the FAQ, on a store where sold-out sizes stay
  visible.
- Any FAQ answer about discount codes, on a store running `10CROOKS` and a set offer.
- An About page — nothing in the header menu, nothing in the footer, nothing in the FAQ.
- Care instructions outside the PDP SPECIFICATION accordion.
- A search box on the 404 body.
- A link from `/pages/contact` (the form) to any actual contact detail.
- A governing-law / company-identity line on `/pages/terms` (it exists only in the Shopify
  Terms of Service).

## Contradictions

**1. The FAQ promises a tracking lookup the tracking page does not have.**
FAQ q5: *"Tracking is emailed the moment your parcel is dispatched. **You can also look your
order up on the tracking page — no account needed.**"*
`/pages/tracking`, in full: *"**IDENTIFICATION REQUIRED.** Order records are released to the
account they were filed under. Sign in to view the chain of custody for your orders."* —
with `SIGN IN` as the only control on the page and zero form fields. The only concession is
the small line *"NO ACCOUNT? THE TRACKING LINK IN YOUR DISPATCH EMAIL OPENS YOUR ORDER
WITHOUT ONE."*
Compounded by FAQ q13: *"No. You can check out as a guest and still track your order."*

**2. Two different ways to start a return.**
PDP chain of custody, on every product: *"04 DELIVERED — You have 14 days from delivery to
return unworn goods with tags attached. Return postage is yours unless we sent the wrong
thing or it arrived faulty. **Start a return by email: crooksldn@gmail.com.**"*
Terms c3: *"**Start your return here: the returns centre.** It takes your order number and
email, and issues the return so we can match the parcel to you."*
FAQ q9: *"**Start your return here** — it takes your order number and email."*
Contact-information policy: *"**Start it by emailing Crooksldn@gmail.com.** Full details on
our Refund Policy page."*

**3. Two different return windows.**
Terms c3: *"You have 14 days from delivery to tell us you want to return something, **and 14
days from then to post it back**."*
Refund policy: *"You have **14 days from delivery to return or exchange** any unworn item
with tags on."*
PDP chain of custody: *"You have **14 days from delivery to return** unworn goods with tags
attached."*
A shopper reading the product page thinks the parcel must be back within 14 days; a shopper
reading the Terms has 28.

**4. Size swaps: free, or free only in the UK?**
Terms c4: *"You pay the postage sending the original back to us. **We do not charge a fee for
the swap itself, and we cover the postage sending the new size out to you.**"* (no geography)
FAQ q8: *"There is no fee for the swap itself, and we cover the postage sending the new size
out to you."* (no geography)
Refund policy: *"There is no fee for a **UK** size swap itself, and we cover the postage
sending the new size out to you."*
An international shopper reading the Terms believes their outbound swap postage is covered.

**5. Damaged parcel: 48 hours, or 14 days?**
Terms c5: *"For transit damage, tell us **within 48 hours** of delivery so we can raise it
with the courier while the claim is still open."* (FAQ q11 says the same.)
Refund policy: *"Faulty or wrong item? That's on us. Message us **within 14 days** and we'll
refund or replace it in full."*
Shipping policy: *"Lost or damaged? That's on us to sort. Message us **within 14 days** and
we'll chase the courier or send a replacement or refund."*
A shopper who reports damage on day 3 has either complied or missed the deadline, depending
which page they read.

**6. Lost parcel: replacement now, or nothing until the investigation closes?**
Shipping policy: *"Message us within 14 days and we'll chase the courier **or send a
replacement or refund**."*
Terms c7: *"We will open an investigation with the courier. Royal Mail allow up to 10 working
days to complete one. **We cannot refund or replace before that investigation closes.**"*

**7. Dispatch: a promise on the product page, a hedge in the Terms.**
PDP, above the buy button: *"Order before 18:00 and it ships today (Mon–Sat)"* and
*"Ordered now — leaves today"*. Chain of custody: *"Orders placed before 18:00 **are
dispatched** the same day, Monday to Saturday."*
Terms c2: *"Orders placed before 18:00 are dispatched the same day **where possible** …
After a drop, **allow up to two working days**."* (FAQ q1 carries the same hedge.)
The unconditional version is the one shown at the moment of purchase.

**8. Shipping price: knowable, or only at checkout?**
FAQ q3 and Terms c1: *"Below £20 it is calculated at checkout before you pay"* /
*"Below £20 it is charged at checkout before you pay."*
Shipping policy: *"Under that: **standard £3, Tracked 24 £4.99**."*
Two pages say the price cannot be known in advance; a third prints it.

**9. The returns centre asks for more than the FAQ says it will.**
FAQ q9 and Terms c3: *"It takes your order number and email."*
The returns centre itself: `ORDER NUMBER / EMAIL / **VERIFY BY POSTAL CODE OR PHONE
NUMBER** / FIND YOUR ORDER`.

**10. One address, four spellings.**
Terms c3: *"Oairo UK Office, Bourne End Business Park, Bourne End, Buckinghamshire, SL8 5AS,
United Kingdom"*.
Refund policy: *"Oairo Uk Office, Bourne end Business Park, Bourne End, Buckinghamshire,
United Kingdom, SL8 5AS"*.
Terms of service, overview: *"Unit M, Oairo Uk Office, Bourne End, SL8 5AS"*; §20: *"Crooks
Clothing Company Ltd / Oairo Uk Office, SL8 5AS"*.
Privacy policy: *"contact us at Unit M ,, SL8 5as, United Kingdom"*.

**11. The contact-information page offers a form it cannot show.**
*"Prefer a form? Drop your details below and we'll come back to you at the email you give
us."* — below it is the site footer.

## Works and must be protected

- **The FAQ's writing.** Fourteen answers with actual numbers in them — £20, £70, 18:00,
  1–2 days, 7–14 days, 5–7 days, 48 hours, 10 working days. It refuses to hide behind
  "please contact us". That is worth more than a reviews widget on a brand with no reviews.
- **The Terms page as a whole.** A nine-clause plain-English trading policy with a working
  clause index, a `LAST REVISED` date, a real returns address and links out to the legal
  texts is better than what most Shopify stores of this size have. The clause index and the
  `#returns` deep link both work.
- **Return postage honesty.** Every surface — Terms, FAQ, PDP, refund policy — says the
  shopper pays return postage unless the fault is the store's. It is the least flattering
  fact on the site and it is stated four times without a euphemism. Do not soften it.
- **The policy pages carrying the full skin.** Header, status bar, VT323 headline, CRX Mono
  body, footer. The seam where most themes give the game away is invisible here.
- **The 404 keeps the header, the footer and four buyable products** — nobody gets stranded.
- **"Drops are for people, not scripts."** (Terms c8) — flavour in the right place: in the
  clause about cancelling bot orders, not in the clause about refunds.
- **The tracking page's honesty.** It does not pretend. If the FAQ's promise is removed or
  the page gains a real lookup, keep the plain "IDENTIFICATION REQUIRED / Sign in" framing
  and the dispatch-email line — just make the dispatch-email line legible.
