# PERSONA 4 — The sceptic

**Who:** Small label, no reviews, £60 jeans, a website that looks deliberately strange. Wants to know this isn't a scam before entering card details.
**Conditions:** 390 × 844 throttled. Cold browser. Entered on the homepage.
**Route:** homepage → hunt for contact details, a returns policy, shipping info, any social proof, any sign a human runs this.
**Recorded specifically:** taps to an email address, taps to a returns policy, evidence other people have bought here.

---

### Step 1 — Homepage
**Screenshot:** screens/p4-step1.png
**On screen:** Canvas board filling the screen, `CRACK THE CUFFS` overlay on top, cookie banner across the bottom 40%.
**Goal right now:** work out whether this is a real business.
**Felt experience:** A game I didn't ask for, over a cookie wall, on a site I've never heard of, being asked for £60. That is not the opening I need. My guard is up before I've seen a product.
**Blocked by:** two stacked overlays.
**Would they continue?** hesitant.
**Seconds elapsed:** 24.2

### Step 2 — Straight to the footer
**Screenshot:** screens/p4-step2.png · **screens/check-footer-vs-cookiebanner.png**
**Measured — and this is the finding of this journey.** With the cookie banner still present, `document.elementFromPoint` at the centre of each footer link returns the banner, not the link:

| Footer link | Target | Clickable on first visit? |
|---|---|---|
| NEW / TEES / DENIM / SWEATS / ACCESSORIES | collections | clickable |
| **SHIPPING** | `/policies/shipping-policy` | **BLOCKED by cookie banner** |
| **REFUNDS** | `/policies/refund-policy` | **BLOCKED by cookie banner** |
| **CASE 001** | the companion game | **BLOCKED by cookie banner** |
| **INSTAGRAM** | `instagram.com/crooksldn` | **BLOCKED by cookie banner** |
| **TIKTOK** | `tiktok.com/@crooksldn` | **BLOCKED by cookie banner** |
| **EMAIL** | `mailto:info@crooksldn.com` | **BLOCKED by a wallet iframe** |

A real click on REFUNDS **times out and does not navigate**. After clicking Accept on the banner, the identical click navigates immediately.

**Goal right now:** find a human, a policy, a postcode — anything.
**Felt experience:** I'm tapping the returns link and nothing is happening. I've tapped it three times. Either this site is broken or it doesn't want me reading that page.
**Blocked by:** **every trust link on the site is physically unclickable until the cookie banner is dismissed.** Shipping, refunds, both socials and the only email address. The one email link on the entire site is 5.88 viewports down, and the address never appears as readable text on the homepage.
**Would they continue?** **would leave.** This persona's stated threshold is three taps; here the count is unbounded because the taps don't register.
**Seconds elapsed:** 26.0 · 1 tap

### Step 3 — Refund policy (reached only after accepting cookies)
**Screenshot:** screens/p4-step3.png
**On screen:** `REFUND POLICY` · `Refund Policy for Crooksldn LTD` · `Last Updated: 20/3/2026` · 339 words. Rendered in **Archivo Narrow** — a typeface used nowhere in the design system.
**Measured text:** `HOW TO REQUEST A REFUND — Contact us within 14 days of delivery at [crooksldn@gmail.com] or via Instagram [@crooksldn]. … [Crooksldn LTD] reserves the right to update this policy at any time.`
**Goal right now:** can I get my money back.
**Felt experience:** There is a real policy, dated, with a company name — that's reassuring. And then it tells me to email a **gmail.com** address, in **square brackets**, like nobody finished editing it. The site's own footer says `info@crooksldn.com`. Which one is real? A £60 order and I can't tell which address reaches them.
**Blocked by:** the placeholder brackets and the address mismatch.
**Would they continue?** hesitant.
**Seconds elapsed:** 58.5 · 2 taps

### Step 4 — Looking for evidence other people have bought here
**Screenshot:** screens/p4-step4.png
**Measured on a PDP, strictly:** `starRatings: 0` · `reviewBlocks: 0` · `urgency: false` · `companyNo: false` · `postcode: false` · socials: Instagram + TikTok · `mailto: info@crooksldn.com`.
**Goal right now:** has anyone actually received an order from these people.
**Felt experience:** Nothing. No reviews, no ratings, no "as seen in", no order count, no photos from customers. I understand a small brand won't have hundreds of reviews — but there's *nothing*, not even a hint that a single order has ever shipped.
**Blocked by:** no social proof of any kind — which is a deliberate brand decision, and it is landing on this persona as absence rather than as confidence.
**Would they continue?** hesitant.
**Seconds elapsed:** 58.7

### Step 5 — The contact page
**Screenshot:** screens/p4-step5.png
**On screen:** `CONTACT` · `Name` · `Email*` · `Phone` · `Comment` · `Submit`. 624 characters total.
**Measured:** no email address displayed · no postal address · no response time · no company number.
**Goal right now:** confirm a person exists.
**Felt experience:** A blank form with no address, no name, no "we reply within 24 hours", no location. I have no idea whether this goes to a person in London or into a void. A contact page that can't tell me who I'm contacting doesn't reassure me — it does the opposite.
**Blocked by:** the contact page contains no contact information.
**Would they continue?** **would leave.**
**Seconds elapsed:** 64.1 · 3 taps

---

## The legal pages are unedited template

Extracted directly from the rendered pages:

**Terms of service:**
> "…subject to return or exchange only according to our Refund Policy: **[LINK TO REFUND POLICY]**"
> "…governed by our Privacy Policy, which can be viewed here: **[LINK TO PRIVACY POLICY]**"
> "Our contact information is posted below: **[Crooksldn LTD] [Crooksldn@gmail.com] [TW200JW]**"

**Refund policy:**
> "Contact us within 14 days of delivery at **[crooksldn@gmail.com]** or via Instagram **[@crooksldn]**"

`[LINK TO REFUND POLICY]` and `[LINK TO PRIVACY POLICY]` are literal, unfilled placeholders sitting in the live legal text. `[TW200JW]` is a bracketed, malformed postcode. This is precisely the artefact a sceptic is scanning for.

**Two different contact addresses are in use across the site:**

| Address | Where |
|---|---|
| `info@crooksldn.com` | footer mailto (every page), PDP CHAIN OF CUSTODY |
| `crooksldn@gmail.com` | refund policy, shipping policy, privacy policy, terms of service |

---

## Verdict

**Would leave — and this is the journey that loses the most money.**

The cruelty of it is that **the trust material already exists and is good.** The PDP's CHAIN OF CUSTODY names the courier, the dispatch window, the delivery window and the return window. The homepage's WITNESS STATEMENT explains short runs and no restocks in the brand's own voice. The refund policy is dated and names a limited company. This site is *not* short of substance.

It fails this persona on delivery mechanics, not on substance:

1. **Every trust link is unclickable on first visit** because the cookie banner sits on top of the footer.
2. **The legal pages contain visible unfilled template placeholders** and route customers to a Gmail address that contradicts the site's own footer.
3. **The contact page contains no contact information** — no address, no email, no response time.
4. **The only email address on the site is 5.88 viewports down**, and never appears as readable text.
5. The homepage's opening move on a stranger is a **game popup asking them to play for a discount**, which reads to a suspicious visitor as a gimmick, not a brand.

None of this requires a reviews widget or a trust badge. Every one of these five is a plumbing fix.
