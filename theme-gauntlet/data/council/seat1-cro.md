# SEAT 1 — CRO LEAD MEMO
Single-site run, annadenning.com, n=20 (decisions.md D1). All counts recomputed from data/verdicts.jsonl.

## Three strongest calls

**1. The store hides every price until the checkout page, and the checkout is doing the catalog's job.** 10 of 20 buyers logged missing/late pricing as friction or a missing feature (B01, B02, B07, B08, B10, B11, B12, B13, B15, B16). Three buyers ended up on a live card-entry form *just to learn a number*: B01 discovered the Zendala course was $99 — over her $70 budget — only at checkout, three screens in (b01-03-price-shock-99.png); B12 clicked "Pay in US dollars" and "dropped straight into a payment form with a card number box" (b12-04-price-found-at-checkout.png); B13 learned "$99" beside a wall of terms on the checkout itself (b13-06-checkout-price.png). B12 scrolled the Spirals page five times and never found its price at all (b12-09-spirals-long-scroll-no-price).

**2. The revenue core converted 1 of 6 — and two of the five misses were killed by things a real buyer cannot route around.** B04 (membership, money ready) hit an undisclosed 3-day trial with a full card form at checkout — "Due Now: Free" badge, never mentioned on the sales page (b04-05-checkout-trial-surprise.png) — and left, would-not-return. B06 (beginner NeuroGraphica, 8-step patience) exhausted homepage, nav, and full catalog without finding any course labeled "NeuroGraphica" or "beginner" (b06-02-courses-list-no-basics.png); the most prominent card was a $997–$1997 certification (b06-03-wrong-course-certification-price.png). The brutal part: the product she wanted exists — B01 bought the "$59 7 Chakras NeuroGraphica Drawing Masterclasses" (b01-05-neurographica-chakras.png). B06 was killed by a label, not by inventory.

**3. What actually sells here is verifiable specificity, and the one completed buy-now purchase shows the whole formula.** B01 closed because a page title literally matched the word from her TikTok (b01-05), the checkout showed $59 struck from $159.99 (b01-06-price-59-good.png), the Graduates directory showed 28 named people (b01-08-graduates-directory.png), and the form asked only email + name + card (b01-09-checkout-filled.png). Five buyers total leaned on the Graduates directory (B01, B07, B08, B09, B19); B07 called it "harder to fake than any testimonial" (b07-03-graduates-directory.png) and B08 verified a facilitator's live site herself (b08-04-facilitators-directory.png). The site's best conversion asset is already built — it's just three clicks from the money.

## (a) Funnel, in counts, by intent

Errand completed (recomputed; matches aggregates.json completed_by_intent exactly):

| Intent | Completed | Reached an offer/sales page | Reached a checkout page | Abandoned — where |
|---|---|---|---|---|
| buy-now (6) | 1/6 (B01) | 6/6 | 4/6 (B01, B02, B03, B04) | B04 membership checkout (trial surprise); B05 Resources page (no on-site store, b05-05); B06 cert course page (no beginner course); B02, B03 stopped at checkout by the never-pay rule |
| research (4) | 3/4 (B07, B08, B10) | 4/4 | 0/4 | B09 Teacher Training waitlist (stale dates, b09-04/b09-05) |
| browse (3) | 3/3 | 3/3 | 2/3 (B12, B13 — both by accident, price-hunting) | — |
| gift (3) | 1/3 (B15) | 3/3 | 2/3 (B14, B15) | B14 Zendala checkout (no gift path, b14-06-abandon.png); B16 Resources page (book is Amazon-only, b16-06) |
| returning (2) | 0/2 | 1/2 | 0/2 | B18 blog, after Library login blocked twice by Cloudflare (shots/b18-03-library-blocked.png); B17 rules-stop at a *working* login (not a site failure — b17-04-login-clean) |
| lookup (2) | 2/2 (B19, B20) | 1/2 | 0/2 | — |
| **Total** | **10/20** | **18/20** | **8/20** | 5 typed identity into a checkout (B01, B03, B04, B14, B15); 2 were killed *on* the checkout page itself (B04, B14) |

**Disagreement flag:** aggregates.json lists 10 completed and only 9 abandons — B02 is coded `completed:false` with `abandoned_at:null`, so 1 of 20 is unaccounted. Behaviorally B02 reached the £75 checkout with the price "completely unambiguous" (b02-05-checkout-gbp.png) and stopped only at the never-pay rule — the same stopping point coded as *completed* for B01 and B15. Coded consistently, buy-now is arguably 2/6, and B02 is the panel's cleanest near-purchase (trust 4, would return).

## (b) Five purchase-decision moments / five purchase-killers

**Sells:**
1. **$59 struck from $159.99 on 7 Chakras** — closed B01 (b01-06), was B14's "most helped" ($59 vs $60 budget, b14-02-checkout-price.png), decided B10's comparison (b10-03-chakras-price.png). 3 buyers.
2. **"Pay in British pounds" carrying £75 unchanged to the card form** — B02 (b02-03, b02-05), B15 ("no dollar sign in sight once I'd chosen pounds," shots/b15-06-checkout-filled.png). Both UK buyers scored trust 4 — tied for highest in the panel.
3. **Our Graduates directory, 28 named facilitators** — B01, B07, B08, B09, B19; B19 completed her entire errand inside it (b19-02-directory-found.png); it was the *only* delight in B09's abandoned session (b09-06). 5 buyers.
4. **Named-teacher credentials on course pages** — B08's trust-4 verdict hung on "CZT #11" specificity (b08-03-zendala-teacher.png); B15 said it "made the £75 feel justified"; B10 counted it as trust. 3 buyers. (It cuts both ways — see brand-confusion under killers.)
5. **The split-payment honesty note at checkout** — plain text that installments total more than paying in full let B03 confirm £997 beats 4×£282; her named most-helpful feature (b03-05-checkout-split-payment.png).

**Kills:**
1. **No price before checkout / page-bottom** — 10 buyers (IDs above); near-killed the run's only completed buy-now sale (B01, b01-03).
2. **Membership checkout springs a 3-day trial + card form** — killed B04 (b04-05, b04-06-terms-wall-before-bail.png); made B12 "uneasy" (b12-07-membership-checkout-trial.png); made the membership ungiftable for B15 (shots/b15-05-membership-subscription-trap.png). 3 buyers touched the membership's pay page; 0 joined.
3. **The beginner ask dead-ends at a four-figure certification** — killed B06 (b06-03); cost B16 a wasted detour into the same $997–$1997 page; B07 said finding a hobby-level course "took real digging" (shots/b07-05-coaching-cert-price.png). 3 buyers.
4. **The book cannot be bought here** — killed B05 (Amazon link landed on a bot-check screen, shots/b05-03-redirected-to-amazon.png; abandon shot b05-05) and B16 (b16-06-no-direct-purchase-path.png). 2 of 20 arrived cash-in-hand for the book; both left as would-not-return.
5. **Gift-blind checkout** — killed B14 at the payment form with an in-budget $59 item: "access link goes to whatever email is typed in," no gift field anywhere (b14-05-zendala-price-and-email-note.png, b14-06). B15 lost the membership as a gift option too. 2 of 3 gift buyers hit it.

Also on the paid path, verdict-logged: B03's Mentored-tier Split Payment button did nothing on two tries (severity 4, no shot exists), and the Standard checkout is mislabeled "Mentored Certification Includes" (b03-06-checkout-full-price-mislabel.png).

## (c) The six buy-now buyers, one by one

- **B01 ($70 budget, "neurographica") — COMPLETED.** Survived a $99 price shock (b01-03) only because a second course happened to be titled with her exact search word and priced $59 (b01-05, b01-06). The completion was luck-adjacent: one more hidden price and she was gone.
- **B02 (UK, Zendala) — lost to coding, not to the site.** Clean £75 GBP path to the card form (b02-05), trust 4, would return. Only real wobbles: teacher-name mismatch on the course page (b02-02) and the checkout defaulting to United States/ZIP while charging pounds. The nearest missed conversion in the panel — and the run's strongest proof the checkout can sell when the price is visible early.
- **B03 (certification, biggest ticket) — reached £997 checkout, typed her email (b03-07).** But her session logged the site's most expensive defect: a buyer trying to give the school £1497 by installments cannot — the Mentored Split Payment button is dead (verdict, 2 attempts). Add stacked GBP/USD with no selector (b03-04) and the mislabeled checkout (b03-06). She stopped per the rules; a real Mentored-tier buyer stops because the button doesn't work.
- **B04 (membership) — KILLED at checkout.** Undisclosed trial + card form (b04-05), never found the class day/time despite reading the full page, "Get 3 Months free" that her own math scored at ~2 months ($38×12=$456 vs $375; b04-04-pricing-full.png), terms wall before the pay button (b04-06). Would not return.
- **B05 (book) — KILLED before any product page.** No store link, no search box (b05-01-landing.png), and the only buy path bounced him to an Amazon bot-check (b05-03). The site converted a ready buyer into, at best, an affiliate commission — and in this session not even that. Would not return.
- **B06 (beginner course, 5 minutes) — KILLED by findability.** 13 steps, no course labeled NeuroGraphica/beginner anywhere (b06-02), top card a $997–$1997 cert (b06-03). Same want as B01; B01's 18-step patience found the $59 answer, B06's 8-step patience could not. Would not return.

Net: of 5 non-completions in the revenue core, 3 are outright site kills (B04, B05, B06), 1 is a broken paid path waiting to kill (B03), and 1 is a scoring artifact (B02). The money is bleeding worst at exactly two places: the membership's checkout page, and the catalog's refusal to name and price its own entry-level product.

## (d) Shortest evidence-backed path to more completed purchases

1. **Print prices on the catalog tiles and at the top of each course page.** A text change; answers the single most-logged friction (10 buyers) and removes the accidental-checkout price hunt (B01, B12, B13).
2. **Put "NeuroGraphica" and "beginner" on the $59 course's card.** The site's own headline word (brand-frame.md) sold B01 the moment she saw it in a title (b01-05); its absence from the catalog killed B06.
3. **One sentence on the membership page: "3-day free trial, card required, £28/$38 a month after — live class Thursdays at [time/zone]."** That single line reverses B04's kill trigger, B12's and B15's flinch, and answers the exact question B18 (blocked member, shots/b18-03) and B20 (found the contact email only inside the Privacy Policy, b20-03-email-found-in-privacy-policy.png) each failed to resolve. Five buyers touched, one sentence.
4. **Fix the two defects sitting directly on the £997–£1997 ladder:** the dead Mentored Split Payment button (B03) and the Teacher Training page's stale "Jan 9, 2026" date plus "by application only" vs "course is full" contradiction that killed B09 (b09-04-teacher-training-stale-date.png, b09-05-course-full-contradiction.png).
5. **Add one line + one field at checkout: "Buying for someone else? Enter their email."** B14's stated minimum, with $59 in budget and her card effectively out (b14-05).
6. **Give the book a real on-site page with a price and a working buy path** (B05, B16 — two cold kills).

## What I would stake my reputation on

On this evidence, annadenning.com does not have a demand problem or a trust problem at the moment of payment — it has a visibility problem before it. Every buyer who saw a clear price early and a matching product name either completed or stopped only because the test forbade paying (B01, B02, B15, B03-Standard), while every outright kill in the revenue core traces to information withheld until too late or absent entirely: the price (B01 nearly, 10 buyers logged), the trial (B04, b04-05), the beginner label (B06, b06-02/03), the store itself (B05, b05-05). I will stake my name on this: printing prices on the catalog, labeling the $59 course with the site's own word "NeuroGraphica," and disclosing the trial and class time on the membership page — three copy-level changes, no redesign — would have converted at least 3 of the 5 lost buy-now sessions in this panel, and the £997 tier's dead split-payment button (B03) is silently costing more per incident than everything else in this report combined.
