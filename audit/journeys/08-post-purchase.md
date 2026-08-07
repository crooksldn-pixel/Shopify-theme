# PERSONA 8 — Post-purchase

**Who:** Already ordered. Wants to track it, or return something.
**Conditions:** 390 × 844 throttled. Entered on the homepage.
**Recorded:** whether this is possible at all, and how many taps.

---

### Step 1 — Homepage, looking for "track my order"
**Screenshot:** screens/p8-step1.png
**On screen:** Canvas board, cookie banner, popup.
**Goal right now:** find out where my parcel is.
**Felt experience:** I've bought something and I'm back to check on it. I'm being shown an attract-mode animation and offered a discount game. Nothing here is aimed at me.
**Blocked by:** nothing yet.
**Would they continue?** yes.
**Seconds elapsed:** 7.0

### Step 2 — Scanning every link on the page
**Screenshot:** screens/p8-step2.png
**Measured across the entire homepage:** `trackWordPresent: false`. Every link in the footer:
```
NEW · TEES · DENIM · SWEATS · ACCESSORIES
SHIPPING → /policies/shipping-policy
REFUNDS  → /policies/refund-policy
CASE 001 → crooks-case-break.base44.app
INSTAGRAM · TIKTOK · EMAIL → mailto:info@crooksldn.com
```
**Goal right now:** find order tracking.
**Felt experience:** The words "track", "order status" and "my order" appear nowhere on this page. There's SHIPPING and REFUNDS, which are policies, not my order. I don't want to read a policy, I want to know where my jeans are.
**Blocked by:** **no order-tracking entry point exists on the homepage.**
**Would they continue?** hesitant.
**Seconds elapsed:** 7.8

### Step 3 — Opened MENU
**Screenshot:** screens/p8-step3.png
**Measured:** `SHOP · NEW · TEES · DENIM · SWEATS · ACCESSORIES · SHOP ALL · CONTACT · ACCOUNT · BAG [0]`. `hasTracking: false`.
**Goal right now:** anything resembling an order.
**Felt experience:** ACCOUNT. That'll be it — that's where orders live on every other shop.
**Blocked by:** nothing yet.
**Would they continue?** yes.
**Seconds elapsed:** 9.2 · 1 tap

### Step 4 — ACCOUNT
**Screenshot:** screens/p8-step4.png
**Measured:** redirects to **`friendsof.crooksldn.com/authentication/login`** — a different subdomain.

| | |
|---|---|
| `.crk-root` present | **no** |
| Typeface | **Times New Roman** |
| Background | `rgb(255, 255, 255)` — white |
| Order lookup on page | **no** |
| Text | `CROOKSLDN · Sign in · Sign in or create an account · Email · By continuing, you agree to our Terms of service · Submit` |

**Goal right now:** log in and see my order.
**Felt experience:** I've been thrown onto a plain white page in Times New Roman on a domain called `friendsof.crooksldn.com`. Nothing about it looks like the shop I bought from. If I were at all nervous about this brand, this is the screen that would convince me I'd been phished.
**Blocked by:** Shopify's hosted customer-accounts login, completely unstyled and on an unfamiliar subdomain. It also offers **no order lookup for guests** — only email sign-in.
**Would they continue?** **hesitant → would leave.** Most people who checked out as a guest have no account to sign into.
**Seconds elapsed:** 14.5 · 2 taps

### Step 5 — The refund policy
**Screenshot:** screens/p8-step5.png
**Measured:** `Last Updated: 20/3/2026` · 339 words · rendered in **Archivo Narrow** · `returnsPortal: false` · return window `within 14 days` · **who pays return postage: not stated** · contact address given as **`[crooksldn@gmail.com]`**, in square brackets.
**On screen:** `HOW TO REQUEST A REFUND — Contact us within 14 days of delivery at [crooksldn@gmail.com] or via Instagram [@crooksldn]. Provide your order number, proof of damage (if applicable)…`
**Goal right now:** send something back.
**Felt experience:** So the process is: email them, or DM them on Instagram. That's honest for a small brand and I don't mind it. But the address is in square brackets like it was never filled in, it's a Gmail address, and it isn't the address in the footer. And nobody has told me whether I'm paying to post it back.
**Blocked by:** placeholder brackets, an address that contradicts the footer's `info@crooksldn.com`, and no statement of return-postage liability.
**Would they continue?** hesitant — they'd email, and hope.
**Seconds elapsed:** 19.1 · 3 taps

---

## Verdict

**Order tracking: not possible. Returns: possible in 3 taps, but with contradictory instructions.**

| Task | Achievable? | Taps |
|---|---|---|
| Track an order as a guest | **No** — no entry point exists anywhere on the site | ∞ |
| Track an order with an account | Only via an unstyled third-party subdomain, and only if they registered | 2 + login |
| Find the returns process | Yes | 3 |
| Learn who pays return postage | **No** — never stated | ∞ |
| Learn which email address is real | **No** — footer says `info@`, all four policy pages say `crooksldn@gmail.com` | ∞ |

The PDP does say `Tracking issued by email` inside CHAIN OF CUSTODY, which is the correct answer — Royal Mail Tracked, tracking arrives by email. But a returning customer has no reason to open a product page, and that sentence is inside a collapsed accordion on a page they've already bought from.

**The fix is small and entirely inside the design language:** the footer already has an `INFORMATION` column containing SHIPPING and REFUNDS. A third entry — `TRACK` or `CASE STATUS`, pointing at the Shopify order-status lookup — would resolve the highest-frequency post-purchase question in one tap, in the brand's own vocabulary, with no new colour, corner or typeface.

**The `friendsof.crooksldn.com` login page is the single sharpest break in the whole experience** — Times New Roman on white, on a subdomain the customer has never seen. It is Shopify-hosted and can be branded from the admin; leaving it unstyled undoes a great deal of the credibility the rest of the site works hard to build.
