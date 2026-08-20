# CONTRADICTIONS — where the site tells a shopper two different things

For a brand with no reviews, no press and no retail, self-contradiction is the
fastest way to lose trust: the shopper has nothing else to check against. This
is the highest-value file in the audit and the cheapest to act on — almost every
line is a copy edit, and none of it requires a design decision.

Grouped so each cluster can be fixed in one pass. Both sides of every mismatch
are quoted from the screen. Evidence lives in `audit/features/FEATURES.md §4`
and in the journeys named against each group.

**Two things to know before reading.** First, **two previously logged
contradictions came back clean** and must not be re-opened: the doubled
`crooksldn@gmail.com.com` on the shipping policy, and the V2 BAGGIES
"9-16 days delivery uk" line. Both verified gone. Second, **the store was being
edited during this audit** — two products were renamed mid-run, and one of them,
`V2 BAGGIES` → `GREY CONVICT SWEATS`, now contradicts its own description, which
still opens *"V2 Baggies — wide, full-length sweats…"*. That mismatch was
created during the run, not found by it.

---

## 4. Contradictions

The highest-value section. Every one of these is the site telling a shopper two different
things, with both sides quoted. Grouped so each cluster can be settled in one pass.

### Group A — Returns: five surfaces, five stories

1. **How long you have.** Terms c3: *"You have 14 days from delivery to tell us you want to
   return something, **and 14 days from then to post it back**."* Product page, chain of custody,
   every product: *"You have **14 days from delivery to return** unworn goods with tags
   attached."* Refund policy: *"14 days from delivery to return or exchange."* A shopper reading
   the product page thinks the parcel must be back within 14 days; a shopper reading the Terms
   has 28. The strictest version is the one shown **before** buying.
2. **The third-party page says 30.** The portal that `returns` sends people to:
   *"Within 30 days from the date of purchase"*, and *"reach out to us within **7 days** of the
   delivered date"* for faulty items. `audit/screens/12-06b-return-policy-from-portal.png`.
3. **How to start one.** Product page, every product: *"**Start a return by email:
   crooksldn@gmail.com.**"* Terms c3: *"**Start your return here: the returns centre.** It takes
   your order number and email, and issues the return so we can match the parcel to you."* FAQ
   q9: *"Start your return here."* Contact-information policy: *"**Start it by emailing**
   Crooksldn@gmail.com."* A return started the way the product page says arrives unmatched, by
   the Terms' own explanation.
4. **Damage: 48 hours or 14 days.** Terms c5 and FAQ q11: *"For transit damage, tell us **within
   48 hours** of delivery."* Refund policy and Shipping policy: *"Message us **within 14 days**."*
   A shopper reporting damage on day 3 has either complied or missed the deadline depending which
   page they read.
5. **Lost parcel: replacement now, or nothing yet.** Shipping policy: *"Message us within 14 days
   and we'll chase the courier **or send a replacement or refund**."* Terms c7: *"**We cannot
   refund or replace before that investigation closes**"* — up to 10 working days.
6. **Size swaps: free, or free only in the UK.** Terms c4 and FAQ q8 state the swap is free with
   **no geography named**; the Refund policy says *"no fee for a **UK** size swap itself"*. An
   international shopper reading the Terms believes their outbound swap postage is covered.
7. **The returns centre asks for more than the FAQ says.** FAQ q9 and Terms c3: *"It takes your
   order number and email."* The portal: `ORDER NUMBER / EMAIL / VERIFY BY POSTAL CODE OR PHONE
   NUMBER / FIND YOUR ORDER`.
8. **One address, four spellings, none of them CROOKSLDN.** Terms c3: *"Oairo UK Office, Bourne
   End Business Park, Bourne End, Buckinghamshire, SL8 5AS, United Kingdom"*. Refund policy:
   *"Oairo Uk Office, Bourne end Business Park… United Kingdom, SL8 5AS"*. Terms of service:
   *"Unit M, Oairo Uk Office, Bourne End, SL8 5AS"*. Privacy policy: *"Unit M ,, SL8 5as, United
   Kingdom"* — double comma, lower-case postcode, no town. Journey 12's shopper put it plainly:
   she would be posting £60 of denim to a company called "Oairo" she had never heard of, at an
   address written half in capitals. That address ends up on a returns label.

### Group B — Shipping: what it costs, and when it leaves

9. **Is there a price before checkout?** FAQ q3 and Terms c1: *"Below £20 it is calculated at
   checkout before you pay."* Shipping policy: *"Under that: **standard £3, Tracked 24 £4.99**."*
   Two pages say the price cannot be known in advance; a third prints it. Reached from the same
   product page footer, two rows apart.
10. **One tier or two.** Status bar, every page: `FREE UK SHIPPING OVER £20 — ORDER BY 18:00 FOR
    SAME-DAY DISPATCH`. The real card is two tiers — free Tracked 48 over £20, free Tracked 24
    over £70. The chrome states the cheaper half as though it were the whole offer, and the £70
    tier is invisible until you have already spent £20.
11. **A UK threshold promised to every country.** The status bar is not gated by country and
    shows every shopper in the world the £20 line. The live rate card: EU `Standard international
    £12.99`, no free tier; International including the US `£18.99`, no free tier; Channel Islands
    `Tracked 48 £3.99` / `Tracked 24 £7.00`, **no free tier at any basket value, ever** — served
    by a dedicated market that shows GBP prices and the same status line. The carriage bar
    correctly hides itself outside GB; the sentence above it does not. An overseas shopper builds
    a basket believing shipping is free over £20 and meets £12.99 or £18.99 at checkout.
12. **Same-day, or same-day where possible.** Ticker: `ORDER BY 18:00 FOR SAME-DAY DISPATCH`, no
    days named — so a shopper ordering at 17:00 on a Sunday expects it to leave that day. Product
    page: `Order before 18:00 and it ships today (Mon–Sat)`. Terms c2 and FAQ q1: *"dispatched the
    same day **where possible** … After a drop, **allow up to two working days**."* The
    unconditional version is the one shown at the moment of purchase.
13. **Settled, or not settled.** Cart carriage bar: `Free Tracked 24 — unlocked`. Cart summary,
    four lines below: `Duties and taxes included. Shipping is calculated at checkout.`

### Group C — Sizing: two methods, and two garments sharing one table

14. **Around the garment, or laid flat.** Product page, printed directly above every measurements
    table: `TRUE TO SIZE — WAIST, CHEST AND LEG MEASUREMENTS ARE TAKEN AROUND THE GARMENT.`
    `QUESTIONS`, reached from that same page's footer: *"**Everything is measured with the garment
    laid flat**, and you can switch the table between centimetres and inches."* Those differ by a
    factor of two. A shopper who lays their own jeans flat, measures 43cm across the waistband and
    compares it with `86.4cm` on the M row concludes the M is twice their size and buys down.
    **Note for whoever fixes it:** `SPEC.md §3.5` states the method as `GARMENT LAID FLAT`, so the
    spec and the FAQ agree and the product-page caption is the outlier. This is the one thing in
    the audit that can make a shopper order the wrong size *by following the site's own
    instructions*. `audit/screens/pdp-sizing-jeans-measurements-open.png` and
    `audit/screens/pdp-sizing-faq-sizing-onscreen.png`.
15. **The caption names columns the table does not have.** On the jeans the columns are
    `WAIST / INSEAM / LEG OPENING` and the line explains "chest". On the crewneck the columns are
    `CHEST / LENGTH / SHOULDER / SLEEVE` and the line explains "waist" and "leg", and says nothing
    about how shoulder, sleeve or length were taken — precisely the three people measure wrong.
16. **Opposite garments, identical numbers.** `V2 BAGGIES`, described on its own page as *"wide,
    full-length sweats in 500gsm cotton, heavy enough to hang straight"*, against `GREY WASH OG
    JEANS`, *"14oz denim, OG straight cut, mid rise. Structured, not baggy."* Same waist, same
    inseam, same leg opening at all five sizes. (Placeholder measurements — known item, impact
    only.) `TRUE TO SIZE` is a fit claim, not a method, and it cannot be true of both.

### Group D — Tracking: a lookup promised and refused

17. FAQ q5: *"**You can also look your order up on the tracking page — no account needed.**"*
    `/pages/tracking`, in full: `IDENTIFICATION REQUIRED` / *"Sign in to view the chain of custody
    for your orders."* / `SIGN IN` — and not one field on the page. FAQ q13 compounds it:
    *"You can check out as a guest and still track your order."*
18. Search offers `TRACK YOUR ORDER` to **everyone before they have typed anything**, and it
    lands on that wall.

### Group E — The set: what the page promises against what the cart charges

19. Cart: `Complete the set — add the Cellblock Shorts, save £10.` → following it, doing the
    obvious thing: `Estimated total £95.00 GBP`, no discount, no mention of the set.
20. Panel, in red: `Cellblock Shorts sold out in M — pick another size` → the same page's
    `MORE FROM THIS DROP` row shows `CHARCOAL CELLBLOCK SHORTS £45.00`, and the shorts page sells
    M perfectly happily.
21. Sticky bar: `CHARCOAL CELLBLOCK CREWNECK` / `£50.00 · M` → the button beside it in the same
    bar: `ADD THE FULL FIT — £85`, for two garments in sizes M and L.
22. Panel prices `£95` and `£85` → `£50.00` on the same screen and `£85.00` in the cart it leads
    to. The set panel is the only place in the shop that drops the pence.
23. `SPEC.md §5`: ticking reveals "**live partner stock**" → an empty stock line for every
    buyable pairing, including the 4-unit ones.
24. `SPEC.md §3.13`: "the bundle in the cart → **the saving confirmed in words**" → no such
    section on the cart page at all.
25. Product page: `£85 for the set` / `Save £10.` / `ADD THE FULL FIT — £85` → cart with
    `10CROOKS`: `Estimated total £76.50 GBP` (**O1**). The saving against buying the parts
    separately becomes £18.50, not the £10 the page states.

### Group F — The register against the goods

26. **`ON MODEL` against the products themselves** — twelve cards, one photograph of a man in
    charcoal shorts (§2.3).
27. **The pictures against the garments** — the cream keyline draws trim on garments that do not
    have it, in the default state, all the way through to the product page (**O3**).
28. **Two case numbers for one product.** `GREY WASH JORTS` is `NO. 06` on the homepage register
    and `NO. 01` on `/collections/denim`. In a register that presents itself as an evidence log,
    the case number moves.
29. **A heading that does not match its own count.** Filtering `/collections/all` to denim leaves
    the heading reading `ALL` while the count beside it reads `4 ITEMS` and only denim is on
    screen.
30. **Two spellings of the same two colours, eight cards apart.** `Colourways: BLACK, WHITE` on
    `NO. 07 MONEY CLIVE TEE` against `Colourways: Black, White` on `NO. 08 CRXST★RZ T-SHIRT`.
    Only a screen-reader shopper meets it, since the text is not shown on the card.
31. **A swatch that is not a control.** Two 12×12px chips sit under two product names, looking
    exactly like the colour chips a shopper taps everywhere else on the web. Tapping the white
    chip on `MONEY CLIVE TEE` opens the product with no colour chosen, presenting the tee in
    black. Evidence: `audit/screens/catalogue-D01b-after-swatch-tap.png`.
32. **`12 PRODUCTS CURRENTLY ONLINE` against 13 published products.** The thirteenth is
    `CELLBLOCK SET` at `£85.00`, with a live page a shopper can reach and buy from, appearing in
    no register and carrying no `PRODUCT n / N` line. Nothing on screen contradicts itself — but
    "currently online" is not literally true. Evidence: `audit/screens/status-bar-x-set-pdp.png`.

### Group G — Search says two things at once

33. Placeholder `Item, category or question` against the hint 40px below,
    `SEARCH BY ITEM, CATEGORY OR COLOUR`. One invites questions and omits colour; the other
    invites colour and omits questions — and questions are the feature's reason to exist.
34. `SEARCH BY ITEM, CATEGORY OR COLOUR` against searching `black`, whose first three results are
    `GREY WASH OG JEANS`, `V2 BAGGIES` and `GREY WASH JORTS`. The only product with `BLACK` in its
    name is sixth. The typeahead for the same word gets it right, so the shopper sees the right
    answer while typing and the wrong order after pressing SEARCH.
35. `SIZE GUIDE` — search's promise — against the destination's own answer: *"tap SIZE GUIDE next
    to the size buttons."* A link labelled `SIZE GUIDE` lands on a page that says the size guide
    is somewhere else.
36. `0 RESULTS` / `NO ITEMS IN THE REGISTER MATCH THAT QUERY.` printed on the same screen as
    `DIRECT LINKS / TERMS` and `PAGES & ANSWERS / TERMS` (§2.6).
37. **Two different returns processes, one word apart.** `returns` → the third-party portal;
    `refund` → the shop's own policy page.

### Group H — The cart against its own header

38. Header `BAG [2]` against, on the same screen at the same moment, `Your cart is empty`.
39. `Discount code cannot be applied to your cart` — for a code that does not exist at all. The
    wording blames the cart.

### Group I — Sold out against leaves today

40. `SIZE M IS SOLD OUT` in red, with `Order before 18:00 and it ships today (Mon–Sat)` and
    `> Ordered now — leaves today` directly above it (§2.11).

### Group J — The store's own rules against what it shows

41. **The overlay sells the urgency the store bans everywhere else.** Eight seconds into a first
    visit, CROOKSLDN says `Code expires in 20 minutes.` and `(this drop closes 15.09)` — a
    countdown and a deadline — in a store that has deliberately refused countdown timers, stock
    counters and manufactured scarcity on every other surface. The shopper cannot tell that one
    of these is a third-party app and the rest is the theme; they see one shop saying two things.
42. **Two build numbers, one tap apart.** Shop footer `EVIDENCE TERMINAL V0.2`; the CASE 001 game
    it links to, `EVIDENCE TERMINAL v0.1 // CROOKS UK` (**O4**).
43. **Two names for one box.** The field is labelled `NUMBA`; the error under it reads
    `Phone number is required`. The name in the error is not on screen.
44. **Two names for one item.** The manifest says `03  CUFF KEYRING *`; the footnote calls the
    same thing `CONTRABAND 03`, and says it ships with `SWEAT BOTTOMS`, which is not the name of
    anything the shop sells.
45. **Three names for one page.** The menu word `SHOP`, the address `/collections/frontpage`, and
    the heading you land on, `PRODUCTS` — sitting directly above a second link, `ALL`, to the same
    twelve products.
46. **A count reserved so it "never reflows the row"** — and at `[103]` it does, widening `BAG`
    by 12px and moving `MENU` out of the top-right corner onto a new line 48px lower. Holds
    perfectly to 99: 0 → 1 → 9 moves nothing by a single pixel. Evidence:
    `audit/screens/hdr-d18-bag-103.png`.
47. **A theme switch on two pages it cannot switch.** `LIGHT MODE` appears in the header of the
    404 and `/pages/contact`; pressing it changes nothing below the header (§2.20).
48. **`TRACKSUITS` reads `1 ITEMS`.**
49. **Spec against page: the accordions and the sticky bar.** `SPEC.md §3.5` says four
    `<details name>` panels, mutually exclusive; the product page has four buttons that all stay
    open. The same section says the sticky bar shows "only while the primary control is
    off-screen"; it is on screen at every position tested, including three where the primary
    control was plainly visible. (See §2.29 — the FAQ *does* behave as the spec describes.)
50. **Spec against page: the notify panel's own words.** `SPEC.md §3.5` describes the sold-out
    capture as `RELEASED — NO LONGER IN CUSTODY`; the panel on screen reads `TELL ME WHEN THIS
    SIZE IS BACK`. The page's version is the plainer one and is the right call under §9.2 — worth
    correcting the spec rather than the page.

---