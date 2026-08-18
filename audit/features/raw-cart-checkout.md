# RAW — Cart, carriage progress bar, checkout (staging theme 202053779799)

Audited 2026-08-18, ~21:00–22:30 London, mobile 390x844 DPR3 via the preview URL.
Staging verified on every session (`.crk-root` + `crooks.css`). All shopping done as a
GB shopper (the preview session geo-detects as US by default and had to be switched to
GB via the localization form — see the geo note under item 3 and Surprises).

Rate card as actually offered at checkout (London SW1A 1AA), for reference throughout:

| Cart value | Tracked 48 | Tracked 24 |
|---|---|---|
| under £20 | £3.00 | £4.99 |
| £20–£70 | FREE | £4.99 |
| £70+ | FREE | FREE |

This matches the bar's two-tier story exactly.

### 1. Empty cart — what /cart and the bar say
- **Should:** An empty /cart tells you it's empty and routes you back to shopping; the carriage bar states the offer.
- **Did:** "Your cart is empty / Have an account? Log in to check out faster / Continue shopping" (→ /collections/all), then a "You may also like" row of four products. The carriage bar renders **nothing at all** while the cart is empty — verified in a GB session on home, collection, PDP, search and cart: the section emits only its CSS/JS links, zero visible content. The only pre-add shipping message is the status ticker: "FREE UK SHIPPING OVER £20 — ORDER BY 18:00 FOR SAME-DAY DISPATCH". On slow 4G the empty cart page was readable ~3.5s in and settled ~6.5s — text lands first, tolerable.
- **Verdict:** works
- **Shopper impact:** The empty-state suppression is a quiet win: a new visitor pays zero screen space for a progress bar they can't use yet.
- **Screens:** f-cart-checkout-empty-cart, f-cart-checkout-empty-cart-gb

### 2. Add £6 socks — what ADD TO BAG actually does; bar on cart and home
- **Should:** Add works with clear feedback; the bar picks up the £6 and says what's left to the £20 tier.
- **Did:** ADD TO BAG is an AJAX add: `POST /cart/add.js`, **no navigation, no drawer, stays on the PDP**. Feedback arrives ~1.5s after the tap: an in-theme line "> Added — 1 in bag  View bag" appears under the buy buttons (aria-live, so screen readers hear it too) and the header count flips BAG [0] → BAG [1] without a reload. The button label itself never changes. The carriage bar **on that PDP does not appear** after the add (it wasn't server-rendered because the cart was empty at page load, and the JS never builds it) — the shopper first sees the bar on their next page: cart and homepage both read "£14.00 to free Tracked 48" (20 − 6 = 14, correct), over a segmented progress track with a tick at the first tier.
- **Verdict:** works
- **Shopper impact:** The "Added — 1 in bag / View bag" line is honest and calm — no drawer ambush. The cost is that the free-shipping nudge itself is invisible until the next page load (see item 3).
- **Screens:** f-cart-checkout-added-toast, f-cart-checkout-bar-stage1-6, f-cart-checkout-home-bar-socks, f-cart-checkout-cart-socks

### 3. Tier progression £6 → £31 → £91 — copy and maths
- **Should:** Bar copy moves through both tiers and the arithmetic is right; it stays correct on AJAX adds (its script's one job).
- **Did:** On full page loads the copy is exact at every stage — £6: "£14.00 to free Tracked 48"; £31 (added £25 tee): "£39.00 to free Tracked 24" (70 − 31 = 39); £91 (added £60 jeans): "Free Tracked 24 — unlocked", track full, ✓ on both "TRACKED 48 FREE" and "TRACKED 24 FREE" chips. **But the bar does not update on the PDP's own AJAX add**: with the bar server-rendered at "£14.00 to free Tracked 48", tapping ADD TO BAG on the £25 tee (cart → £31, tier crossed) left the bar unchanged — polled every 250ms for 5s, still "£14.00 to free Tracked 48" while the header already showed BAG [2]. On the **cart page** the AJAX path does work: removing items took the bar from "Free Tracked 24 — unlocked" to "£39.00 to free Tracked 24" in place, no reload. So the update wiring works, but the PDP add — the exact moment a shopper crosses a tier — never fires it.
- **Verdict:** partly
- **Shopper impact:** The one moment the bar could reward you ("free shipping unlocked") it instead shows stale, now-wrong copy telling you to spend £14 more. Corrects itself on the next page, so the damage is confusion rather than a wrong charge — but it's the bar's single JS job, half done.
- **Screens:** f-cart-checkout-bar-stage2-31 (stale bar over the tee PDP, BAG [2]), f-cart-checkout-bar-stage3-91

### 4. Does the bar earn its place above everything?
- **Should:** Judge as a shopper whether the space before the first product is well spent.
- **Did:** Order on every template is status ticker → header → carriage bar → content (home hero, collection register, search query bar, cart heading). Measured on the homepage: with an **empty cart the bar is absent** and the first catalogue card top sits at 757px = 0.90 viewports; with anything in the bag the bar takes **160px** (~19% of the screen) and the first card moves to 917px = 1.09 viewports. One-line judgement: **it earns the space** — it charges nothing until you've started a bag, and from then on "£14.00 to free Tracked 48" is the most commercially useful line on the page; the first card still clears within ~1.1 viewports. (The round-2 council's 1.22 → 1.48-viewport complaint no longer reproduces; the empty-state suppression fixed it.)
- **Verdict:** works
- **Screens:** f-cart-checkout-home-top-nobar, f-cart-checkout-home-top-withbar

### 5. Cart operations — qty up/down/zero, remove, undo, three-item maths
- **Should:** Quantity controls and remove work, totals stay exact, ideally an undo.
- **Did:** Three items (£6 socks + £25 tee + £60 jeans): every line price correct, "Estimated total £91.00 GBP" exact. Increase on the jeans → qty 2, displayed total £151.00, all via AJAX with no reload; decrease → back to £91. **Decrease at qty 1 is a silent no-op** — the button does nothing, no hint that Remove is the intended path. Remove (a labelled control per line, e.g. "Remove BLUE WASH OG JEANS - XS") deletes the line and re-totals correctly. **No undo anywhere** after remove — the row is just gone; recovery is re-finding the product. Cart also shows "Duties and taxes included. Shipping is calculated at checkout."
- **Verdict:** works
- **Shopper impact:** Maths is trustworthy, which is what matters. The dead decrease-at-1 button is a small confusion; no undo is standard Shopify but stings on a fat-thumb remove of a size you'd hunted for.
- **Screens:** f-cart-checkout-cart-3items, f-cart-checkout-cart-after-zero, f-cart-checkout-cart-after-remove

### 6. Discount — 10CROOKS on a normal cart, then on the £85 set
- **Should:** A discount field exists on the cart; 10CROOKS gives 10%; on the set it shows £76.50 (known O1).
- **Did:** Cart page has a "Discount" accordion in the summary — "Discount code" field + Apply. On a £25 tee: "10CROOKS −£2.50", Estimated total £22.50 GBP. With the cellblock-set: "10CROOKS −£8.50", **£76.50** — O1 confirmed exactly as logged (the code even persisted when I rebuilt the cart around it). The shopper *gains* here (set already −£10, then −10% on top), so O1 costs margin, not trust. **The genuinely new problem is downstream:** the applied code does not survive into checkout. `cart.js` carries `discount_codes: [{code: "10CROOKS", applicable: true}]` and the cart says £67.50 (on a £75 test cart), but the checkout that opens from "Check out" shows subtotal £75.00 with no discount — and typing 10CROOKS into checkout's own discount field returns red "**Enter a valid discount code**". So through the preview, a shopper who applied a working code in the cart reaches payment being charged the undiscounted price and is told their code is invalid. Caveat: the preview cart is handed to checkout cross-domain (preview host → crooksldn.com), which may be what drops/blocks the code; this MUST be re-verified on the live theme before publish, because if it reproduces there it is a checkout-abandonment machine.
- **Verdict:** partly
- **Shopper impact:** Cart-side flawless; checkout-side (as testable here) the discount silently disappears — the worst kind of price surprise, at the worst moment.
- **Screens:** f-cart-checkout-discount-field, f-cart-checkout-discount-tee, f-cart-checkout-discount-set, f-cart-checkout-boundary-after-code (the "Enter a valid discount code" rejection)

### 7. Shipping costs visible before checkout?
- **Should:** A shopper can find what delivery costs before committing to checkout.
- **Did:** The *free* tiers are everywhere: status ticker ("FREE UK SHIPPING OVER £20…") on every page, and the carriage bar names both tiers once the bag has anything in it. The cart says only "Shipping is calculated at checkout." The actual sub-threshold prices (£3.00 / £4.99) appear **nowhere** before the checkout's shipping-method step — a shopper with a £15 bag knows shipping isn't free but not what it costs until they've entered an address.
- **Verdict:** partly
- **Shopper impact:** Minor — the thresholds are cheap (£20) and loudly advertised, so most carts clear them; but the sub-£20 shopper commits to checkout blind on a £3–£5 question.

### 8. Checkout to the payment step (stopped there)
- **Should:** Checkout works, ideally holds the brand; shipping options and prices are sane.
- **Did:** "Check out" leads to Shopify checkout at `https://crooksldn.com/checkouts/…` — **completely stock light Shopify skin**: white ground, system sans-serif, blue accents, "CROOKSLDN" as plain text, no logo, no dark terminal anything. Coming from the darkest storefront imaginable, the flash to white is a genuine jolt. One-page checkout: express buttons (Shop Pay / PayPal / Google Pay), contact email with a **pre-ticked "Keep me updated"** marketing checkbox, delivery form, an SMS opt-in ("Text me with discounts and latest drops", unticked). Shipping methods (see rate card above) auto-select the sensible option, and the maths held every time (sock: £6.00 + £3.00 = £9.00; £91 cart: shipping FREE, total £91.00). **Delivery estimates are the sore point:** Tracked 24 honestly says "Thu 20 Aug–Fri 21 Aug" (correct for a Tuesday-21:45 order), but Tracked 48 says "Estimated delivery Fri 28 Aug" on most passes (once "Mon 24–Wed 26 Aug") — 4–8 working days for a service named "48" on a site whose custody copy promises UK 1–2 working days. Payment step: reached — "Payment / All transactions are secure and encrypted / Credit card (+5 others)" — and **stopped**; no payment fields touched, no order placed.
- **Verdict:** works
- **Shopper impact:** Functionally clean and the totals are exact. Two costs: the brand evaporates at the moment of maximum commitment (fixable with checkout branding settings — colours/logo, not theme code), and the Tracked 48 estimate quietly tells sub-£20/£70 shoppers the cheap option means waiting until the 28th, which contradicts the storefront's 1–2-day story and pushes them to £4.99 or out.
- **Screens:** f-cart-checkout-coA-shipping (stock skin, form), f-cart-checkout-coB2-methods (both methods FREE with estimates), f-cart-checkout-sock-methods (£3.00/£4.99), f-cart-checkout-midband-methods (FREE/£4.99), f-cart-checkout-coA2-summary, f-cart-checkout-coB2-summary, f-cart-checkout-coA2-payment-stop (where I stopped)

### 9. Back from checkout; returning later; fresh browser
- **Should:** Back keeps the cart; a returning shopper in the same browser finds their bag.
- **Did:** Browser back from checkout landed on /cart (or the PDP for the CHECKOUT NOW route) with the cart fully intact every time. Closed the context and reopened with preserved cookies (returning shopper, same browser): /cart still held all 3 items on the staging theme. A truly fresh context (new browser / incognito): cart empty, as expected — carts are cookie-scoped. (Preview caveat: "same browser" was simulated by restoring storageState, since every plain new context re-bootstraps a fresh preview cookie.)
- **Verdict:** works
- **Screens:** —

### 10. Two tabs
- **Should:** An add in tab A shows up when tab B's cart is reloaded.
- **Did:** Tab A added black socks via AJAX; tab B reloaded /cart and showed all three lines and "Estimated total £91.00", matching `cart.js` exactly.
- **Verdict:** works
- **Screens:** —

---

## Also observed (this area, not on the checklist)

**CHECKOUT NOW (PDP sticky bar)** takes the *whole bag*: with a tee already in the bag, CHECKOUT NOW on the jeans PDP added the jeans and opened checkout at £85 (both items). Not a solo buy-now — sensible, but a shopper expecting "buy just this now" gets their whole bag at checkout. Back returned to the PDP with the cart intact. The PDP buy stack also carries Shopify dynamic-checkout buttons ("Buy with Shop" + "More payment options") that SPEC §3.5 doesn't mention. Screens: f-cart-checkout-added-toast (shows the Shop button), f-cart-checkout-checkout-now-landing.

**A cookie banner now exists** (SPEC's open-items list says "No cookie banner"). It's Shopify's Privacy banner, skinned to match the terminal look — genuinely handsome — but on mobile it covers the bottom ~60% of the viewport as an alertdialog that **intercepts taps on the buy area**: ADD TO BAG and Check out were physically unclickable until Accept/Decline was answered (my automation hit this twice; a thumb would too). One forced decision on first visit, then gone. Screens: f-cart-checkout-cart-3items, f-cart-checkout-home-top-withbar (banner over content).

**Geo/currency note.** The preview egress geo-detects as US: fresh sessions price in USD ($9.00 socks, $70.00 crewneck — USD market pricing is live on the store). Twice, a US-currency session rendered the carriage bar as "**$11.00 to free Tracked 48**" with $9.00 in the cart — the £20 threshold formatted as $20 against a USD total (cross-currency arithmetic); a controlled re-test showed the GB gate hiding the bar for a US session, so the sightings are most likely the preview's per-request geo flapping mid-session rather than a broken gate. Worth one owner-side sanity check on live (visit with a US VPN: the bar should not render), because if it ever shows, the promise is false — the US rate card is not "free over $20". Screen: f-cart-checkout-bar-usd-session.

**Free-shipping vs discount boundary — untestable here.** The bar computes against the pre-discount subtotal (£75 cart with 10CROOKS applied → cart total £67.50, bar still "Free Tracked 24 — unlocked"). Whether checkout honours free Tracked 24 on a post-discount £67.50 could not be tested because the code never survives into checkout through the preview (item 6). If the live checkout applies the code and evaluates thresholds post-discount, the bar will over-promise near the boundary. Re-test on live together with item 6's handoff check.
