# Theme Gauntlet v2 — The Buyer's Cut: annadenning.com

**Run:** 2026-08-19 · 20 in-character buyers, live agent-driven browser sessions (12 mobile / 8 desktop) · feature census · five-advisor council with anonymous peer review · chairman synthesis weighted by peer standing.

**Read this first — honesty box.** This was a **single-site** run, not the OLD-vs-NEW comparison the gauntlet was written for: the fill-in block arrived blank, the target turned out to be a Kajabi site (not Shopify), and no redesign preview exists (`data/decisions.md` D1). There is therefore no paired preference and no "what the new theme broke" evidence — those sections below say so rather than pretend. n=20 is directional, stated once here; every number is a count, never a percentage. Three buyer moments that depended on *other companies' servers* (a Cloudflare block on the members' login, an Instagram error, an Amazon bot-wall) are quarantined as probe-environment artifacts, not site defects (D11). And one figure needs a leash before anyone quotes it: **"10/20 errands completed" undercounts the site by three** — B02, B03 and B17 were recorded as failures only because the run forbids submitting payment; their own logs read "satisfied — would have completed this purchase" (B02 S9), "stopping here as instructed" (B03 S7), "errand effectively solved" (B17 S6). Scored behaviorally: **13/20 succeeded, 6 failures caused by the site** (B04, B05, B06, B09, B14, B16), 1 environment-tainted (B18).

---

## VERDICT

**The identity is sound. The buying machinery leaks at the last fifty feet. Do not redesign — fix.**

In gauntlet terms: **HOLD** any visual redesign (nothing aesthetic cost a single purchase in 20 sessions — 17/20 cold buyers read the site as a real brand, and the "homemade, spiritual, artsy" feel is the product working as intended), and **SHIP a fix sprint** on the specific, screenshot-proven breaks where money actually dies: the membership checkout's undisclosed card-capture trial, prices withheld until the card form, a catalog that doesn't use the site's own headline word "NeuroGraphica" on the one $59 product that carries it, and a four-figure certification tier with broken payment buttons, mixed currencies, a mislabeled checkout, and expired dates.

No REDESIGN_THESIS was supplied, so the council tested the site's own public claim (`data/brand-frame.md`): *calming, credible, premium, transformative*. The evidence: the **artwork earns "calming" and the shopping mechanics cancel it**. 18/20 cold reads landed in the right genre, but only 2 buyers said "calming" cold, zero said "premium" or "transformative" — and 13/20 buyers spent one of their three end-of-session recall words on a complaint ("roundabout", "confusing", "muddled-pricing", "pricey-to-find", "hard-to-reach", "date-confusing").

---

## The numbers (counts, n=20)

| Measure | Count | Notes |
|---|---|---|
| Errand completed (raw field) | 10/20 | B01 B07 B08 B10 B11 B12 B13 B15 B19 B20 |
| Behavioral success (rule-stops corrected) | 13/20 | + B02, B03, B17, who reached their goal and stopped per the no-payment rule |
| Site-caused failures | 6/20 | B04 (trial ambush) · B05, B16 (book has no on-site path) · B06 (no beginner/NeuroGraphica label) · B09 (stale/contradictory program dates) · B14 (no gift path) |
| Environment-tainted | 1/20 | B18 — third-party block on the login path (D11), not scored against the site |
| Reached a sales page | 18/20 | |
| Reached a checkout page | 8/20 | 5 typed identity into it; 2 were killed **on** the checkout page itself (B04, B14) |
| Buy-now core (6 buyers) | raw 1/6 · behavioral 3/6 | B01 bought; B02, B03 reached the pay point satisfied; B04, B05, B06 are genuine kills |
| Trust | avg 2.85/5 — eight 2s, seven 3s, five 4s, no 1s or 5s | the five 4s: B02, B08, B15, B17, B19 |
| Would return | 11/20 | |
| Five-second read | brand 17 · template 3 · reseller 0 | |

---

## Identity analysis — what buyers received vs what the site claims

**Received, decisively:** the genre and the person. 18/20 cold five-second reads used a spiritual-register word (6 "spiritual", 8 "new-agey/new-age", 4 "mystical"); 8/20 named Anna unprompted in their tell-a-friend sentence; 17/20 said "feels like a brand". B04's cold read is the received identity in one line: *"a sweet, artsy weekly drawing group run by one woman named Anna."*

**Claimed but not received:** of the site's own reached-for adjectives, **calming** came through cold for only 2/20 (3 at recall), **credible** 0 cold (earned later only via the graduates directory — 2 "credentialed" + 1 "trustworthy" at recall), **transformative** and **nurturing** 0/20 at both probes, **premium** 0/20 — and inverted: 4 buyers cold-read "homemade/handmade", and no buyer guessed above $300 for a course from the landing screen. The four-figure tier is invisible until a casual shopper trips over it as the biggest card on the catalog (B06, `b06-03-wrong-course-certification-price.png`).

**The contamination mechanism is sequencing, not styling** (Seat 2's thesis, peer-verified): the two assets that would earn the missing adjectives — the price and the proof — are positioned last. Prices surface at page-bottom or checkout; the 28-name graduates directory (the panel's single strongest trust asset, leaned on by 5 buyers: B01, B07, B08, B09, B19) is never borrowed by the pages that sell. Note the leash the skeptic put on the "no testimonials" version of this claim: named, job-titled testimonials **do** exist on the Spirals and membership pages (B12, B13 read them); what's true is that no star ratings or review counts exist anywhere, and the $59–$99 course pages B07 checked carried none.

**Audience:** in-target buyers self-recognized (B10: the Zendala "who this is for" section "made me feel like it was written for someone like me"; B11's midnight scroll was "exactly the mood the reel promised"). The one out-of-target read is on-frame targeting, not failure — B13, 20-something from TikTok: *"more like your aunt's wellness hobby than something I'd grab off a TikTok."* The genuine mismatch: B07, squarely the target hobbyist, found the nav-promoted flagship "built for therapists and coaches, not someone just wanting a relaxing hobby."

---

## Feature scorecard — every census feature, rated

WORKS / CLUNKY / BROKEN / MISSING / UNTESTED. Every non-WORKS rating pinned to a buyer moment and shot.

| Feature | Rating | Evidence pin |
|---|---|---|
| Header nav (desktop) | WORKS | B03, B07, B09, B12, B20 used it directly |
| Header nav (mobile hamburger) | CLUNKY | needed two taps for B06 (S3) and B11 (`b11-07-menu-retry.png`); no abandonments traced |
| Logo home link | WORKS | B12 used it to reset, as his card predicted |
| Social links | CLUNKY | header and footer link two different Instagram accounts (@neurographics.art vs @annadenningart) — B08; the Instagram error itself is quarantined (D11) |
| Homepage hero | WORKS | genre landed in 5 seconds for 18/20 |
| Homepage course tile grid | CLUNKY | card names don't match their pages: "Sacred Geometry" opens Power of Spirals, "Pattern Drawing" opens Tangle with Ann — B13 sev3 "is this even the same site?" (`b13-05-zendala-course.png`), B02 sev2 |
| "Basics of NeuroGraphica" pathway | BROKEN | resolves to a 404 (census, `census-basics-404-m.png`). Zero buyers clicked it — a loaded trap: B06, hunting exactly this, abandoned seven screens above it |
| Membership pathway | WORKS | B04 reached the membership page cleanly |
| Mid-page newsletter offer (10% off) | CLUNKY | contains the typo "excluses"; terms unclear (census); nobody could test the discount (no code is ever given on-site) |
| Footer newsletter | WORKS | present, ignorable; nobody was forced into it |
| Footer policy links | WORKS | B20 used Privacy Policy (to dig out an email address — see MISSING contact) |
| Course catalog `/store` | BROKEN as a shelf | six tiles, zero prices — 7 buyers hit that exact moment (`b12-02-course-catalog.png`, `b10-02-course-catalog.png`); nothing labeled "NeuroGraphica" or "beginner" — killed B06 (`b06-02-courses-list-no-basics.png`) |
| 7 Chakras course page | WORKS | the run's one completed buy-now sale: title matched the buyer's word, $59 struck from $159.99 (`b01-05`, `b01-06-price-59-good.png`) |
| Spirals course page | CLUNKY | B12 scrolled it five times and never found a price (`b12-09-spirals-long-scroll-no-price`); its named testimonials are real (B12, B13) |
| Zendala course page | CLUNKY | price at page bottom after ~10k px (B10 at 200% zoom, sev3, `b10-05-zendala-price-clear.png`); "Tangle with Ann / Ann Diane Tai" teacher switch unexplained at the top — confused 3 (B02, B13, B15), read as transparency by 1 (B08, `b08-03-zendala-teacher.png`) |
| AM Coaching Certification page | BROKEN | Mentored-tier payment buttons dead/circular — B03 clicked Split Payment twice, "snapped back to the top" (S6; corroborated by census DOM: `href=""` on the $1997 button, circular links on the £1497 tier); GBP and USD tiers stacked with no selector (B03 sev3 `b03-04-pricing-cards`, B09 sev2); £997 checkout bullets read "Mentored Certification Includes" (`b03-06-checkout-full-price-mislabel.png`) |
| AM Teachers Training page | BROKEN | "beginning January 9th, 2026" presented as live on Aug 19, 2026 (`b09-04-teacher-training-stale-date`); "by application only" contradicted by "course is full" on the same page (`b09-05-course-full-contradiction`) — abandoned the exact professional persona this tier courts |
| Upcoming AMM Programmes page | CLUNKY | interest-list email capture only; no dates or prices to cross-check (B09) |
| Membership page | BROKEN at conversion | 3/3 buyers who tapped a price hit an undisclosed 3-day trial + full card form (B04 abandoned, `b04-05-checkout-trial-surprise.png`; B12 `b12-07`; B15 `b15-05`); 0/3 who needed the live class time/timezone/topic found one ("Thursday" alone appears — B11 S8; time and zone never — B18 `b18-02`, B20 `b20-05`); "Get 3 Months free" annual badge computes to ~2 months ($38×12=$456 vs $375 — B04's own math, `b04-04-pricing-full.png`) |
| Checkout (Kajabi) | WORKS mechanically | praised as "refreshingly simple" (B01 `b01-09`); split-payment honesty note helped B03 (`b03-05`); £75/£997 held steady page-to-card-form (B02 `b02-05`, B15 `b15-06`); residue: Country defaults to United States with "ZIP code" even mid-GBP payment (B02, B15, sev1 each) |
| Coupon field | WORKS | invented codes correctly rejected: "Invalid coupon" (B01 `b01-04-coupon-invalid.png`, census `census-checkout-badcoupon-m.png`); B01 called it fair |
| Login page | WORKS | B17: found in menu, clean login, working Forgot Password (`b17-03`, `b17-04-login-clean`) |
| Library (members area) | UNTESTED beyond the gate | the only two probes stopped at the no-credentials rule (B17) and a third-party block (B18, quarantined per D11) |
| Graduates directory | WORKS | 5 buyers used it, 5 rated it "helped"; B19 completed her whole errand inside it. **Census correction:** it *does* have a search box and country chips (`b19-02-directory-found.png` falsifies the census's "no search" note — see D12). Minor: the "All" chip doesn't clear a typed search (B19 S5) |
| Blog | WORKS | earned B11's planned return visit (`b11-10-zendala-content.png`) |
| Resources page | WORKS as a tools page / MISSING as a book shop | 2/2 book buyers left: the book exists only as Amazon affiliate links inside Resources (B05 `b05-05-abandon-no-onsite-checkout.png`, B16 `b16-06-no-direct-purchase-path.png`) |
| About page | WORKS | B07, B08 both used it to identify who they'd be paying |
| 404 page | WORKS | clean, offers "Back to Home" (census) |
| Site search | MISSING | nowhere on the site; B05 looked for one while hunting the book (`b05-01-landing.png`) |
| Popups | MISSING — and that's good | no popup ever fired in 20 sessions; B11 and B13 were both primed to bail on one. Don't add one |
| Chat/support widget | MISSING | B20's hunt found nothing |
| Cookie banner | MISSING | observational; no buyer commented |
| Currency selector | MISSING globally | the per-page "Pay in £/$" buttons on consumer pages were the run's best trust device (both UK buyers trust 4); their absence on the certification page produced the stacked-currency confusion |
| Contact channel (pre-checkout) | MISSING | no contact link, form, FAQ, or email anywhere a shopper would look; B20 finally mined `anna@annadenning.com` out of the Privacy Policy's GDPR clause (`b20-03-email-found-in-privacy-policy.png`); the same address also appears on checkout pages (`b03-06`) — i.e. *after* the buying decision |
| Testimonials | CLUNKY | present with names/job titles on Spirals and membership pages; absent from the 7 Chakras and Zendala pages; no ratings or review counts anywhere (B07's "none anywhere" claim was killed in review — his shot shows a homepage grid) |
| Gift path | MISSING | 3/3 gift buyers blocked or improvising; B14 abandoned with $59 in budget at a checkout that says access goes to whatever email is typed (`b14-05`, `b14-06-abandon.png`) |

---

## Findings

### Surprises — things the owner likely doesn't know

1. **The membership checkout charges into a card-required 3-day trial that no page mentions.** All three buyers who tapped a membership price landed on "$38.00 USD Every month / 3-day trial / Due Now: Free" over full card fields, plus "your payment information will be stored… for future purchases" — with no trial wording on the sales page. One abandoned on the spot, one backed out "uneasy", one struck the membership off her gift list. (B04 `b04-05`, B12 `b12-07`, B15 `b15-05`.) This is the single best-evidenced commerce defect in the run — it survived every attack the skeptic mounted.
2. **The £997 checkout describes the wrong product.** "The AM Method™ Standard Coaching Certification £997" is bulleted as "Mentored Certification Includes" (`b03-06`). A four-figure buyer reading carefully at the moment of payment sees the site contradict itself.
3. **A buyer trying to pay £1,497 by installments cannot.** B03 clicked the Mentored tier's Split Payment button twice; it only snapped her to the top of the page. The census DOM check independently found the $1997 button has an empty link and the £1497-tier buttons circle back to the same page. (Flag: this severity-4 moment carries no screenshot — retest before building on it; the census corroboration is why it stays.)
4. **The catalog never says the site's own headline word.** The hero and page titles trade on "NeuroGraphica", but no catalog tile is labeled with it — B06, sent by a friend to "take the basics course", exhausted the homepage, nav and full catalog, hit the $997–$1997 certification as the most prominent card, and quit. The $59 product she wanted exists — B01 bought "7 Chakras NeuroGraphica Drawing Masterclasses" the moment its title matched her half-remembered word. **The stock was on the shelf; the label was wrong.** And the homepage's one "Basics of NeuroGraphica" card — the only beginner signpost on the site — links to a 404.
5. **The "Get 3 Months free" annual badge fails its own arithmetic.** $38×12 = $456 vs the $375 annual — about two months. B04, the exact buyer the badge targets, did the math and downgraded the whole site for it (`b04-04-pricing-full.png`).
6. **Teacher Training is selling with expired, self-contradicting dates.** "Beginning January 9th, 2026" presented as current in August 2026; "by application only" above "this course is full." It cost the run its art-therapist persona — the precise professional the tier courts (B09, abandoned).
7. **Your contact email is only discoverable inside the Privacy Policy** (and on checkout pages, after the decision point). B20's money-dependent pre-sales question died there.
8. **A correction in the site's favor:** the census initially recorded the graduates directory as having no search — buyer B19's session falsified that: it has a search box and country chips, and it works (`b19-02`). It is also the site's strongest trust asset: 5/20 buyers leaned on those 28 named, checkable facilitators; B07 called it "harder to fake than any testimonial."

### What the new theme broke

**Not applicable — there is no new theme.** This run had one live site and no redesign to regress against (decisions.md D1). The section exists so its absence is a recorded fact rather than an omission. If a redesign is ever built, this report's panel (`data/personas.json`) and scorecard are the baseline it must not regress from.

### Store problems — the confirmed spine, by buyers touched

1. **Prices are withheld until page-bottom or checkout — 10/20 buyers taxed** (B01, B02, B07, B08, B10, B11, B12, B13, B15, B16; 7 at the identical price-less catalog moment; 4 learned a number only from a live card form; 2 never found one at all). The skeptic's leash, adopted by this synthesis: the pattern is confirmed, but **no abandonment trigger cites it** — it nearly killed the run's only completed buy-now sale (B01, $99 vs $70 budget at the card form, `b01-03-price-shock-99.png`) and it manufactures the "pricey-to-find / spendy / roundabout" recall words, but it is the run's widest tax, not its proven killer.
2. **The membership funnel** — trial ambush (3/3) + missing class time/timezone/topic (0/3 who needed it found it) + dishonest annual badge. Two of the six genuine failures (B04 outright; B18's errand was unanswerable on-site regardless of his quarantined login block).
3. **Shelf labels don't match products** — 4 buyers confused (B02, B06, B13, B15), one ready buyer lost (B06), plus the 404'd beginner card.
4. **The certification tier (top of the price ladder) is the most defective real estate on the site** — dead/circular payment buttons, stacked currencies, mislabeled checkout, stale dates: B03 and B09, small count, biggest tickets.
5. **No gift path** — 3/3 gift buyers blocked or improvising; one $59 sale died at the payment form (B14).
6. **The book can't be bought here** — 2/2 book errands failed on-site; both buyers left "roundabout". Operator's caveat, adopted: for a Hay House title, Amazon links are fulfillment reality — the defect is that the book has no findable home (no store entry, no search to find it), not the absence of a cart.
7. **No pre-checkout contact route** — 1 buyer tested it exhaustively; the census makes it structural.

### The Do-nothing list — looks off, cost no one a purchase

- **The look.** "Homemade", busy backgrounds, hand-drawn hearts — 17/20 still read *brand*, and the aesthetic is the identity. No buyer bailed over it. Do not redesign it.
- **The long storytelling sales pages.** The friction on them was always the missing price, never the prose — B11's midnight read is the one thing that earned a planned return visit. Move the price up; keep the words.
- **The Cloudflare login block, Instagram error, Amazon bot-wall.** Third-party responses to a datacenter probe (D11). B17 walked the same login path cleanly. Don't touch the login system or the social icons over this report.
- **Checkout defaulting to United States/ZIP for UK payers.** Both UK buyers flagged it at severity 1 and both finished at trust 4.
- **Hamburger needing two taps** (2 buyers, zero consequences) · **coupon field rejecting invented codes** (working as designed; "fair" per B01) · **repeated inline email boxes** (ignored by both buyers who noticed) · **the absence of popups** (a feature — two personas were primed to bail on one).

---

## Prioritized fixes — each traceable to a confirmed finding

| # | Fix | Buyers affected | Effort |
|---|---|---|---|
| 1 | **Membership page, two sentences:** "Live class: Thursdays at [time, timezone] — this week: [topic]" and "Joining starts a 3-day free trial — card required, then $38/£28 a month." | 5 touched (B04, B12, B15, B18, B20); reverses the run's best-evidenced kill | copy, under an hour |
| 2 | **Print prices on catalog tiles and in the first screen of every course page.** | 10 taxed; 3 forced into checkouts to learn a number | copy/page edits, hours |
| 3 | **Label the $59 course "NeuroGraphica — beginner" on the shelf; point the homepage "Basics" card at it (or a real page) instead of the 404.** | B06's lost sale + every future beginner | copy + one link, under an hour |
| 4 | **Certification money pages:** fix or remove the Mentored tier's dead/circular payment buttons (retest B03's moment first); correct the £997 checkout's "Mentored" bullets; show one currency per viewer or an explicit selector; a date pass on both program pages (one accurate year-included next-intake line; reconcile "application only" vs "full"). | B03, B09 — the £997–£1497 ladder | half a day |
| 5 | **Make the annual badge honest** — "2 months free", or price annual at ~$342 if "3 months" must stand. | B04 and every annual considerer | minutes |
| 6 | **Contact link in the footer** (mailto is enough), email also on About. | B20; structural | minutes |
| 7 | **One checkout line + field: "Buying as a gift? Enter the recipient's email — the access link goes there."** | 3/3 gift buyers; B14's $59 was one sentence away | Kajabi checkout copy, hours |
| 8 | **Give the book a findable home:** a store tile + short page with the Amazon/Kindle/Audiobook buttons up front. | 2/2 book buyers | hours |
| 9 | Small: make catalog card names match their page titles (B02, B13); "All" chip clears the directory search (B19); align the two Instagram handles (B08); fix the "excluses" typo in the 10%-off offer. | 4+ | minutes each |

The operator's one-week structural bet, endorsed by the panel's evidence: **one "Courses & Pricing" shelf** where every offer carries the same name as the page it opens, teacher, level tag, price in both currencies — the pattern already proven by the single product that sold (name matched + price visible = the purchase).

---

## Council dissent — preserved, not papered over

- **Does price concealment *kill* or *tax*?** The CRO staked on "three copy changes would have converted at least 3 of the 5 lost buy-now sessions"; the skeptic showed zero abandon triggers cite hidden prices, and two peer reviewers independently struck the counterfactual (at most 2 of 5 trace to those fixes). This synthesis reports the tax with its 10-buyer breadth and strips the conversion promise.
- **Was B13 savable?** The UX seat ruled her bail predated the price reveal ("aunt energy", S5); a reviewer countered that S5 was her reaction to the *wrong page* (a mislabeled card had rerouted her) and her own verdict names the checkout-only price as what most hurt. Unresolved — both readings sit in the record.
- **The behavioral ledger's edge case.** The UX recount (13/20 success, 7 site-caused failures) includes B18, which its own quarantine ruling excludes. The chairman's ledger above uses 6 site-caused + 1 environment-tainted. Same data, one classification disagreement, now explicit.
- **The membership "0-for-5".** The operator's headline framing was rejected in review: with payment submission forbidden by protocol, zero completed signups was guaranteed for any site on earth. The surviving membership claims are the trial disclosure (3/3, artifact-proven) and the missing schedule (0/3) — which need no inflated denominator.

## Peer-review standings (weight applied in this synthesis)

Skeptic ranked 1st by all four of its reviewers; UX 2nd; CRO 3rd; Operator 4th; Brand 5th. Claims killed in review and **absent from this report's findings**: "returning members cannot get in (0/2)" · "no contact channel exists" (email exists — post-decision only) · "no testimonials anywhere" · "the $1997 button is dead" as a buyer-experienced event (census DOM fact; no buyer clicked it) · "14 buyers named Anna" (8 did) · "17/20 noted no price on the landing screen" (4–6 did) · membership "0-for-5".

---

## Appendix A — the obvious (kept out of the body)

Long sales pages are long on every device; the mobile hamburger takes two taps sometimes; there's no cookie banner; the checkout's US-centric defaults are cosmetic for UK payers; blog posts have no share buttons, comments, or related-post links; the interest-list pages capture email before giving dates. All observed, none decision-changing.

## Appendix B — method & instrument notes

20 personas (stable panel, `data/personas.json` v1-seed42) · fresh isolated browser per buyer, 390×844 mobile / 1440×900 desktop, ≤5 concurrent, human pacing · buyers stopped at checkout, never subscribed, never submitted forms · session logs `sessions/B*-live.md`, 139 screenshots in `shots/`, structured verdicts `data/verdicts.jsonl` · host-assertion integrity logs clean (504 on-site loads; 3 knowing off-site exits). Instrument notes for future runs: three buyer verdicts leaked harness vocabulary ("10,000 pixels of scrolling", "HTTP 429") — observations corroborated but never quoted here as buyer voice; B18's `features_used` rows lost their verdict fields (schema gap); B02's `completed:false` + `abandoned_at:null` coding hole is why the raw completion figure disagrees with the behavioral one. Census correction D12: the graduates directory has working search + country chips; the census's "no search/filter" note was wrong and is superseded by `b19-02-directory-found.png`.

**Evidence:** `report/contact-sheet.html` (all cited screenshots) · `data/council/seat1-cro.md … seat5-skeptic.md` (memos) · `data/aggregates.json` · `data/decisions.md` (all run adaptations).
