# RAW — content pages and the 404

Audited 2026-08-18, ~21:00–22:00 London time, staging theme 202053779799 via preview URL.
Staging verified on every session (.crk-root + crooks.css). Device: mobile 390x844 DPR3.
FAQ first load run under slow4g with cache cleared; interaction runs unthrottled.

**Session context note:** the audit browser egresses from a US IP, so Shopify Markets
geo-converted every product price to USD ($70.00 for the £50 crewneck etc.) across the
whole session — collection pages and 404 alike. This is consistent site-wide behaviour,
not a defect of any page below; a UK shopper sees £. Where a $ price appears in a
screenshot, that is why. (Side observation for whoever owns Markets copy: for a US
visitor the status bar and FAQ still talk in £ thresholds — "FREE UK SHIPPING OVER £20"
next to $ prices.)

**Cookie consent banner:** SPEC's open items say "no cookie banner", but the staging
storefront now shows Shopify's COOKIE CONSENT banner (Accept / Decline / Manage
preferences) on first visit. It covers roughly the bottom 40% of the mobile viewport —
on the FAQ it sits over the first question until dismissed. Dismissal sticks. Recording
as "apparently since fixed/added", not as a defect.

---

### 1. /pages/faq — count, groups, does it answer a £60 shopper's questions
- **Should:** 14 questions in 4 groups (SPEC §3.11); answers a shopper's pre-order questions on delivery time, returns, sizing, payment.
- **Did:** Exactly 14 questions in 4 groups (DELIVERY 6, SIZING 2, RETURNS AND REFUNDS 3, ORDERS AND PAYMENT 3), h1 "COMMONLY ASKED QUESTIONS". Under slow4g the page was readable in ~3s, fully settled ~5.3s — text first, nothing jumped, felt fine. All accordions default closed; opening one closes the other (verified: tapping HOW MUCH IS SHIPPING closed HOW LONG DOES DELIVERY TAKE) — deliberate per SPEC §9.4, and it kept the page short. The four core questions are all answered concretely: delivery "1–2 working days in the UK, 7–14 working days internationally"; cost "Free on UK orders over £20. Over £70 you get Royal Mail Tracked 24 free"; returns "14 days from delivery to tell us, and 14 days from then to post it back... Return postage is yours unless the item was faulty"; sizing points at the PDP measurements table and cm/in toggle; payment "Shop Pay, Apple Pay and Google Pay, plus all major debit and credit cards". Answers link out usefully: "tracking page" → /pages/tracking, "the returns centre" / "Start your return here" → https://5wn03tnm.aftership.com, "terms page" → /pages/terms#returns. Footer line: "Still stuck? Email crooksldn@gmail.com or DM @crooksldn... We reply within 1–2 working days."
- **Verdict:** works
- **Shopper impact:** Genuinely good — a nervous £60 first-timer gets dispatch cutoff, delivery window, free-shipping thresholds, the exact return window and who pays postage, without leaving the page. Questions I'd still ask that are missing: **"Will sold-out sizes restock?"** (the PDP has a notify-me form, the FAQ never mentions restocks — and this is a drops brand), and **"Do you take Klarna/Clearpay?"** (BNPL is the default expectation for streetwear buyers at £60+; the payment answer is silent on it, so the shopper only finds out at checkout). Minor: "message us" in the intro has no link — you have to scroll to the footer to find how.
- **Screens:** f-content-pages-01-faq-top, f-content-pages-02-faq-delivery-open, f-content-pages-03-faq-shipping-open

### 2. /pages/terms — 9 clauses, index, LAST REVISED, plain-English vs legal policies
- **Should:** 9 clauses with a working index and a LAST REVISED date; the plain-English version should not contradict the linked legal policies (SPEC §3.10).
- **Did:** All present: 9 clauses (CARRIAGE, DISPATCH, RETURNS, SIZE SWAPS, FAULTS AND WRONG ITEMS, REFUNDS, LOST PARCELS, ORDERS WE CANCEL, CONTACT), 9-item index whose anchors work on mobile (tapped "03 RETURNS" — the clause heading landed 96px from the top), "LAST REVISED 13.08.2026" (matches the legal ToS "Effective date: 13th August 2026"). All four legal policies linked at the bottom. Returns address stated in full. Followed the REFUND POLICY link and compared:
  - **Return window — soft contradiction.** Terms clause 03: *"You have 14 days from delivery to tell us you want to return something, and 14 days from then to post it back."* Refund policy: *"You have 14 days from delivery to return or exchange any unworn item with tags on."* The plain-English page grants notify-within-14 **plus** 14 more to post (up to ~28 days); the legal text reads as 14 days total. A shopper on day 20 doesn't know which governs.
  - **Who pays postage — consistent.** Terms: *"Return postage is paid by you unless the item was faulty or we sent the wrong thing"*; *"we cover the postage sending the new size out to you. You cover the postage sending the original back."* Refund policy: *"Size swaps are free within the UK — however return postage is covered by the customer."* Same story both sides.
  - **Refund timing — consistent.** Both say 5–7 days to the original payment method.
  - **Transit damage window — contradiction with the shipping policy.** Terms clause 05: *"For transit damage, tell us within 48 hours of delivery so we can raise it with the courier while the claim is still open."* Shipping policy: *"Lost or damaged? That's on us to sort. Message us within 14 days and we'll chase the courier or send a replacement or refund."* 48 hours vs 14 days.
  - **Lost parcels — tension.** Terms clause 07: *"We cannot refund or replace before that investigation closes"* (Royal Mail, up to 10 working days). Shipping policy reads as immediate: *"Message us within 14 days and we'll chase the courier or send a replacement or refund."*
  - Terms clause 06 mentions *"Items marked final sale are labelled as such on the product page"* — matched by the refund policy, so no conflict, but no product on the store currently carries such a label (nothing to trip over).
- **Verdict:** partly
- **Shopper impact:** The page itself is the best-written terms page I've seen on a store this size — but the return window discrepancy is the one that costs money: a shopper who trusts the friendly version and posts back on day 25 can be refused under the legal version. The 48h-vs-14-days damage window is the same trap in miniature.
- **Screens:** f-content-pages-04-terms-top, f-content-pages-16-terms-returns-anchor

### 3. /pages/tracking signed out — what a guest gets, vs the FAQ's promise
- **Should:** A useful signed-out state; the FAQ's promise about tracking should match what the page does (known RUN3 item A6 — verify current build).
- **Did:** Signed out, the page shows "CROOKSLDN PROPERTY TRANSFER NETWORK / IDENTIFICATION REQUIRED / Order records are released to the account they were filed under. Sign in to view the chain of custody for your orders." with a SIGN IN button (→ hosted accounts) and the line "NO ACCOUNT? THE TRACKING LINK IN YOUR DISPATCH EMAIL OPENS YOUR ORDER WITHOUT ONE." There is **no guest lookup form** — no order-number/email fields, nothing to type. The FAQ meanwhile promises: *"You can also look your order up on the tracking page — no account needed."* That is not what the page does for a guest: **A6 is NOT fixed in the current build.** (The FAQ's other claim — "check out as a guest and still track your order" — is honest only via the dispatch-email link, which the page does explain.)
- **Verdict:** partly
- **Shopper impact:** A guest follows the FAQ's exact instruction, lands here, and hits "IDENTIFICATION REQUIRED" — a dead end unless they go dig out the dispatch email they were trying to avoid finding. The signed-out state itself is honest and well-written; it's the FAQ sentence that lies. One-line fix on the FAQ side.
- **Screens:** f-content-pages-08-tracking-signedout

### 4. The five policy pages — same site? readable? contact emails now
- **Should:** Dark/mono, skinned like the rest of the site (CSS-only skin per SPEC §2); readable; correct contact emails (a past issue was a typo'd email).
- **Did:** All five (/policies/privacy-policy, refund-policy, shipping-policy, terms-of-service, contact-information) render fully on-brand: near-black ground, CRX Mono body, pixel-display headings (REFUND POLICY etc.), Crooks status bar/header/footer intact. No pale band, no unreadable text anywhere I scrolled — light-on-dark body copy and bold subheads all legible. Emails as they stand NOW, exactly:
  - privacy-policy: `crooksldn@gmail.com`
  - refund-policy: `crooksldn@gmail.com`
  - shipping-policy: `crooksldn@gmail.com`
  - terms-of-service: `crooksldn@gmail.com` (Section 20, three occurrences incl. the address block)
  - contact-information: `Crooksldn@gmail.com` (capital C, twice — functionally identical, cosmetically inconsistent with everywhere else)
  No typo'd domain anywhere — the past defect is gone.
  **One broken promise:** the contact-information policy ends *"Prefer a form? Drop your details below and we'll come back to you at the email you give us."* — and below it is only the footer. Policies can't take sections (SPEC §2), so no form can ever render there; the actual form lives at /pages/contact and is not linked. Verified: zero form elements on the page.
  Also noted: refund policy's returns address is the same as Terms' but sloppily cased ("Oairo Uk Office, Bourne end Business Park"), and the legal ToS names the entity "Crooks Clothing Company LTD... Unit M, Oairo Uk Office, Bourne End, SL8 5AS" and carries a governing-law clause (England and Wales) — so the SPEC note "no governing-law line in Terms" applies only to the plain-English page.
- **Verdict:** partly
- **Shopper impact:** The skin work has paid off — the legal pages feel like the same shop, which builds exactly the trust they exist for. The dead "form below" promise is a genuine annoyance: a shopper who prefers forms scrolls, finds nothing, and concludes the page is broken. Either link the words to /pages/contact or cut the sentence.
- **Screens:** f-content-pages-05-policy-privacy-policy, f-content-pages-05-policy-refund-policy, f-content-pages-05-policy-shipping-policy, f-content-pages-05-policy-terms-of-service, f-content-pages-05-policy-contact-information, f-content-pages-07-contact-info-bottom-nobanner

### 5. Cross-check: shipping times and costs across five sources (for CONTRADICTIONS.md)
- **Should:** Custody accordion, Terms, FAQ, shipping policy and product descriptions should tell one story.
- **Did:** Quotes verbatim, by source:
  - **(a) PDP custody accordion** (v2-baggies, identical structure on cb2-wash-jeans): 01 Logged: *"Orders placed before 18:00 are dispatched the same day, Monday to Saturday. After 18:00, the next dispatch day."* 02 Dispatched: *"Shipped with Royal Mail Tracked. Free UK shipping over £20, and free Tracked 24 over £70."* 03 In transit: *"Tracking issued by email. UK 1–2 working days. International 7–14 working days."* 04 Delivered: *"You have 14 days from delivery to return unworn goods with tags attached. Start a return by email: crooksldn@gmail.com."*
  - **(b) Terms**: *"UK shipping is free on orders over £20, and free Royal Mail Tracked 24 over £70. Below £20 it is charged at checkout before you pay."* / *"Once dispatched, UK orders arrive in 1–2 working days. International orders take 7–14 working days."*
  - **(c) FAQ**: *"Once it has left us: 1–2 working days in the UK, 7–14 working days internationally."* / *"Free on UK orders over £20. Over £70 you get Royal Mail Tracked 24 free. Below £20 it is calculated at checkout before you pay."*
  - **(d) Shipping policy**: *"Free UK shipping over £20, and free Tracked 24 over £70. Under that: standard £3, Tracked 24 £4.99."* / *"Once dispatched: UK 1–2 working days, international 7–14."* (The £3 / £4.99 sub-£20 rates appear ONLY here — extra detail, not a contradiction.)
  - **(e) Product descriptions**: **V2 BAGGIES**: *"3-5 day delivery uk / 7-14 days international"* (plus the *"5,1-5,4 XS"* height-range block). **BLUE WASH OG JEANS (cb2-wash-jeans)**: *"9-16 days delivery uk / 16-21 days international."*
  Sources (a)–(d) agree with each other on every number. Both product descriptions contradict them — the jeans page states "9-16 days delivery uk" in its own description while its own custody accordion two taps below says "UK 1–2 working days"; its "16-21 days international" fights the site-wide "7–14". Note the baggies figure is "3-5", not the "9-16" the SPEC logged for the jeans — both defects live in product descriptions (store data, already-logged family), and both are shopper-visible on the same screen as the contradicting custody copy. **One more route inconsistency for the record:** custody step 04 says start a return **by email**; FAQ and Terms say start it in **the returns centre** (Aftership); the refund policy says **email or DM**. Three different front doors to the same process.
- **Verdict:** partly
- **Shopper impact:** The four theme-owned surfaces are impressively consistent — the damage is entirely in the two product descriptions. Cost is concrete: a shopper reading "9-16 days delivery uk" on an in-stock pair of £60 jeans, ordered for the weekend, either bounces or orders elsewhere; one who reads both lines just stops trusting the page. The three-way return-route split is cheaper: nobody is blocked, but the Aftership portal (which needs order number + email) and the "just email us" line will produce mismatched return records.
- **Screens:** f-content-pages-15-custody-accordion

### 6. /products/does-not-exist and /pages/does-not-exist — is the 404 useful?
- **Should:** Branded, with a path back to the shop, real 404 status.
- **Did:** Both URLs return HTTP 404 with an identical page: h1 "PAGE NOT FOUND", "The link may be incorrect, or the page has been removed.", a "Continue shopping" button → /collections/all, and a "Discover something new" block with four real product cards (images, names, prices, working links incl. ?variant=). Dark Crooks status bar/header above and dark footer below. Not a dead end at all. **But** the 404 body itself is Horizon's untouched light template (SPEC §2 lists 404.json as "Horizon, untouched"): cream background, black sans-serif type, none of the terminal styling — the page reads as a different site sandwiched between the dark header and footer. Copy is generic Shopify, not in-fiction (which per design law is fine for function, but here even the chrome is off-brand).
- **Verdict:** works
- **Shopper impact:** Functionally strong — a dead link costs the shopper one tap to be back among products. The cream flash is a brand pothole rather than a behaviour problem: a shopper briefly wonders if they've left the site. Worth a skin pass someday; nothing here blocks anyone.
- **Screens:** f-content-pages-09-404-product, f-content-pages-10-404-page, f-content-pages-12-404-usd-prices

### 7. /pages/contact — does the form render and what does it ask?
- **Should:** A working contact form asking sensible fields.
- **Did:** Renders Horizon's main-page + contact form: h1 "CONTACT", fields Name, Email* (only required field), Phone, Comment, black "Submit" button. Filled it as AUDIT TEST / audit-contact@example.com / a please-ignore message and submitted: Shopify's hCaptcha challenge appeared (bottom-right widget, page stays on /pages/contact, **all typed values preserved** — nothing lost). Automation can't and shouldn't pass a captcha, so the final "thanks" state wasn't observable; the captcha is Shopify's standard bot protection, not a theme defect, and a human just ticks it. Two observations that ARE the theme's: (1) like the 404, the whole page body is Horizon's light look — cream background, black sans type, off the terminal skin, and the only h1 styling is Horizon's; (2) the page is bare — just "CONTACT" and four fields, no email address, no reply-time promise, no link to FAQ/tracking (all of which the contact-information *policy* page has, and which in turn promises a form it doesn't have — the two pages each hold the other's missing half).
- **Verdict:** partly
- **Shopper impact:** The form works and loses nothing to the captcha — that's the load-bearing part. But this is the page angry-parcel-missing shoppers land on, and it's the least on-brand, least reassuring page on the site: no human copy, no expectations set, cream Horizon default inside a dark terminal shop. Merging the contact-information policy's copy ("Real people read every message... We reply within 1–2 working days") onto this page would fix both pages at once.
- **Screens:** f-content-pages-11-contact-top, f-content-pages-13-contact-filled, f-content-pages-14-contact-after-submit

---

## Extra observations

- **PDP accordions are not `<details>` in the served DOM.** SPEC §3.5 says the four PDP accordions are `<details name>` for JS-free exclusivity, but `document.querySelectorAll('details')` returns **zero** nodes on /products/v2-baggies (checked while extracting custody text; the accordions render with "+" toggles and work). Either the SPEC is stale or something rewrites them at render. Flagging for the product-record agent — if real, the no-JS accordion fallback (§3.5, §9.11) may not hold.
- FAQ/Terms/policy pages all show the FILED-style consistency you'd hope for: FAQ's "1–2 working days" reply promise matches Terms clause 09 and both policy contact blocks word-for-word.
- The Shopify preview bar and the cookie banner both overlay the bottom of mobile pages on first visit; the cookie banner is real (see header note), the preview bar was removed as a preview artifact per harness instructions.
