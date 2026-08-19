# Seat 4 — UX Researcher: patterns across 20 buyers, and what the data actually says

Single-site run per decisions.md D1. n=20, one site, counts not percentages throughout.

## Three strongest calls

**1. The price is the site's best-hidden piece of information, and it touches every intent.** 10 of 20 buyers logged a friction or "looked for but missing" item about price visibility (B01, B02, B05, B08, B10, B11, B12, B13, B15, B16). Seven hit the same exact moment: a course catalog listing six courses with no price on any tile (B01 S3 "NO prices shown anywhere on this list"; same scene in B02, B10, B12, B13, B14, B15 — shot b12-02-course-catalog.png shows the shelf, priceless). Four buyers ended up on a page with card-number fields as the only way to learn a number: B01 (b01-03-price-shock-99.png, $99 against a $70 budget), B12 (b12-04-price-found-at-checkout), B13 (b13-06-checkout-price.png), B14 (b14-02-checkout-price.png). Two never found a price at all: B12 quit the Spirals page after five scrolls (b12-09-spirals-long-scroll-no-price), B11 ended a 10,375px sales page still priceless (b11-13-endless-salespage.png).

**2. The membership funnel springs a trial-plus-card-form on everyone who touches it, and tells nobody when the class meets.** All 3 buyers who clicked a membership price hit an undisclosed 3-day trial with a full card form: B04 (b04-05-checkout-trial-surprise.png — "$38.00 USD Every month / 3-day trial / Due Now: Free" over card fields, verified), B12 (b12-07-membership-checkout-trial), B15 (b15-05-membership-subscription-trap.png). B04 abandoned on it; B15 struck the membership off her gift shortlist because of it; B12 backed out "uneasy." Separately, all 3 buyers who needed the live session's day/time (B04 buy-now, B18 returning member, B20 pre-sales question) read the membership page end to end and found none — B20 logged 11,000+px of scroll with no time, timezone, or FAQ (b20-05-membership-bottom-no-faq); 2 of those 3 abandoned their whole errand.

**3. The aggregate "10/20 completed" undersells the site, and "buy-now 1/6" misleads outright.** Three of the ten recorded failures are harness-rule stops whose logs read as successes: B02 ("satisfied — would have completed this purchase," S9), B03 ("satisfied I found my answer... stopping here as instructed," S7), B17 ("errand effectively solved," S6). All three carry `trigger: null`. Scored behaviorally, buyer success is 13/20 and site-caused failure is 7/20 (B04, B05, B06, B09, B14, B16, B18) — and buy-now moves from 1/6 to 3/6. Any council math on the raw completion field inherits this inconsistency: B15 and B01 stopped at the identical point and were scored `completed: true`.

## (a) Frictions that cluster

- **Catalog/course pages hide prices** — 10 buyers, detailed above. Spans 5 of 6 intents (only returning buyers were spared) and both devices.
- **Membership trial disclosure + missing schedule** — 5 distinct buyers engaged the membership seriously (B04, B12, B15, B18, B20); 3 of 3 checkout-clickers hit the surprise trial; 0 of the 3 who needed a session time found one.
- **Certification currency stack** — both desktop researchers who read the certification pricing hit GBP and USD prices stacked with no selector: B03 (severity 3, b03-04-pricing-cards) and B09 (severity 2, b09-02-certification-page). Contrast: the consumer course pages' explicit "Pay in US dollars / Pay in British pounds" buttons *helped* both UK buyers (B02, B15 — both trust 4, both would return). Same site, two presentations, opposite outcomes. Residue even on the good path: checkout Country defaults to United States with a "ZIP code" label after choosing pounds (B02, B15, sev 1 each).
- **Teacher/brand name switch (Anna Denning site → "Tangle with Ann" / Ann Diane Tai)** — 5 buyers touched it, split by intent: negative for B02 (sev 2), B13 (sev 3, "is this even the same site?"), B15 (sev 1); *positive* for B08, the credibility-checker, who read per-course teacher credits as transparency (b08-03-zendala-teacher); factual note for B10. Not broken — unexplained at the top of the page.
- **Missing testimonials on the pages that sell** — 4 buyers (B01 sev 2, B02 missing, B07 sev 3 with b07-07-no-testimonials-found.png, B08 missing). The inverse cluster is the Graduates directory: 5 users (B01, B07, B08, B09, B19), 5 "helped" ratings, named most-helpful by four. The site's entire social proof lives on one page the sales pages never borrow from.
- **The book has no on-site purchase path** — 2 of 2 book-errand buyers (B05, B16) abandoned; the "buy" is an Amazon affiliate link inside Resources (b05-02, b16-03). Small cell, 100% failure for the intent.
- **No gift path** — B14 abandoned at two checkouts (b14-05: $99, email/name/card, no gift field — verified; the checkout's own copy says access goes to the payer's email), B15 completed only by planning to type her friend's email as her own. 2 of 3 gift buyers blocked or improvising.

## (b) Said-vs-did divergences

- **B13** — verdict says the $99 price "killed it instantly" and names the checkout price reveal as the feature that most hurt. The log shows the exit decision landed two steps earlier, before any price existed: S5 "this is not it... aunt energy for sure," S6 "is this even the same site?" The price confirmed a bail already underway; fixing price display would not have saved B13.
- **B01** — persona bail trigger is "can't find the price after 3 screens"; the log records exactly that moment (S4: "I had to go 3 screens deep... just to see a number") and she didn't bail — she kept hunting and found the $59 course. B01's completion is a buyer out-performing her own stated rule, not the funnel working.
- **B06** — errand said "under 8 steps, five minutes"; the verdict records 13 steps before abandoning. Even over-persistence couldn't surface a beginner NeuroGraphica course — the failure is a catalog-labeling fact, not an impatience artifact.
- **B05** — stated rule "I won't buy on another site," yet clicked Buy on Amazon (S3 "to see if I could actually buy it") and then rated the link "broken" when Amazon bot-checked our datacenter IP. The artifact behind that broken rating exists only because the buyer broke his own rule.
- **B18** — a four-month member whose errand said "you're already sold" reports `would_return: false`. The driver is the Cloudflare block on the mykajabi.com login, which decisions.md D11 says not to read as a site defect. Quarantine B18's sentiment as environment-tainted, not churn.
- **B02** (mild) — names the teacher-name mismatch as the feature that most hurt, yet behaved barely dented: "a little thrown" (S3), trust 4, reached checkout satisfied.

## (c) Feature-verdict audit (broken / got_in_the_way)

Of the 7 rows in `features_broken`:
- **Uphold:** B09's two stale-date ratings — shot b09-04 verified ("beginning January 9th, 2026 ... This round is by application only," visited 2026-08-19) and b09-05 shows the same page's "course is full" contradiction.
- **Uphold with a retest flag:** B03's Mentored-tier Split Payment button (two clicks, two scroll positions, no checkout — S6). It is the run's only on-site mechanical failure and the only severity-4 claim with **no screenshot**. Retest before it anchors a fix list.
- **Downgrade (third-party, per D11):** B05's Amazon link (bot-check on a datacenter IP; B16 clicked the identical link and rated it "helped," affiliate tag working as disclosed) and B08's Instagram icon (HTTP 429 rate-limit). What survives on-site from B08: the nav/footer handle mismatch (@neurographics.art vs @annadenningart) — real but unshot.
- **Reclassify broken → missing:** B07's "testimonials/reviews search" (nothing malfunctioned; the absence is real and corroborated by B01, B02, B08) and B14's checkout email field (the field worked; the gift capability doesn't exist — moment stands at severity 4 with b14-05).
- **Upgrades I'd make:** B19's directory "All" button not clearing typed search (S5, live-verified behavior) is a genuine mechanism defect sitting only in friction; and B03's checkout tier mislabel — b03-06 verified: heading "Standard Coaching Certification £997," bullet list "Mentored Certification Includes" — is checkout-content error on a £997 purchase, filed as only severity 2.
- Data-quality note: B18's `features_used` rows carry no verdict fields at all, so his Library dead-end never reached the broken tally the aggregates count.

## (d) Device split (12 mobile / 8 desktop)

- **Hamburger needing two taps:** 2 of 12 mobile (B06 S3, B11 S12 with b11-07-menu-retry.png); 0 of 8 desktop, who click the persistent top nav directly (B03, B07, B09, B12, B20 logs).
- **Checkout as the price tag:** 3 of the 4 buyers who learned a price from a card form were mobile (B01, B13, B14; B12 desktop).
- **Mobile landing gives no way in but the menu:** 10 of 12 mobile buyers open the hamburger as their first or second step; B17 logged the absence of any login/account icon on the first screen (sev 1).
- **Honestly not device-specific:** long-page price burial hit both — mobile B04 (a dozen+ scrolls), B10 (8 scrolls at 200% zoom, sev 3), B11 (10,375px); desktop B07, B12, B20 (11,000+px). The pages are long for everyone.

## (e) Three findings I'd defend under cross-examination

1. Price concealment is systemic: 10 of 20 buyers, 7 at the identical catalog moment, 4 forced into card forms to learn a number, 2 who never found one — every claim shot-pinned above.
2. The membership checkout's undisclosed trial has a 3-for-3 hit rate with a screenshot per buyer; with 0-for-3 on finding the class time, it accounts for 2 of the 7 genuine abandonments.
3. The completion aggregate misclassifies 3 harness-rule stops (B02, B03, B17) as failures; behavioral success is 13/20, site-caused failure 7/20, buy-now 3/6 not 1/6.

## What I would stake my reputation on

That this site's failures are almost entirely *information withholding*, not mechanism: across 20 live sessions the only confirmed on-site breakages are one dead split-payment button (unshot, needs retest), one mislabeled checkout bullet list, one directory filter quirk, and one page of expired dates — while ten buyers fought to learn a price, three were surprised by a trial at the card form, three couldn't learn when the class meets, and two couldn't buy the book the site itself promotes. The panel's most load-bearing trust artifact is the Graduates directory — 5 uses, 5 helped, four "most helpful" citations — which the selling pages never reference. I stake equally on the caveats: B18's block, B08's Instagram error, and B05's Amazon wall are datacenter-IP artifacts that must not be sold to the site owner as her defects, and the 10/20 completion figure should never be quoted without the three rule-stop corrections.
