# RAW — Product record (PDP)

Audited on the UNPUBLISHED STAGING THEME (202053779799) via the Shopify preview
URL. Staging verified by the harness on every session (`.crk-root` + `crooks.css`).
Main subjects: `/products/v2-baggies` (2 of 5 sizes available) and
`/products/cb2-wash-jeans` (full run). Mobile 390×844 first; one slow-4G pass;
desktop 1440×900 pass at the end. Tested Tue 2026-08-18, ~21:45–23:00 London.

**Session context that colours everything below:** the audit session is
geo-detected outside the UK, so every price renders in **USD** ($83.00 for the
£60 jeans/baggies — Shopify Markets conversion working correctly), while the
status bar, shipping policy and free-carriage copy all speak in **£**. A UK
shopper sees £ throughout; an international one sees the mix. Also: a **cookie
consent banner now exists** (Accept / Decline / Manage preferences) and covers
the bottom ~360px of the 844px mobile viewport on first visit — SPEC §10 still
lists "no cookie banner" as missing store work, so this has been added since the
SPEC was written. All interactions below were done after Accepting, as a normal
shopper would.

Slow-4G first load feel: product title, price and size row readable at ~1.0s,
buy button present at ~1.0s, first product photo painted at ~3.2s. The page is
shoppable before the photo lands; nothing jumps around while it loads. Feels
quick for the connection.

---

### 1. Gallery — every image, thumbnails, swipe, arrows, zoom
- **Should:** All photos viewable via thumbnails and touch swipe on mobile, arrow keys on desktop; some form of zoom for a garment close-up.
- **Did:** Both products carry exactly **2 photos**. Counter reads `PHOTO 1 OF 2` and updates on every change. Thumbnails: tap switches slide, active thumb gets a visible border (`data-active` flips, aria-labels "Photo 1 of 2"). Touch swipe works both directions (left → photo 2, right → back to 1). Gallery is a labelled `role="group"` ("Evidence photographs"), tabbable. **Zoom does not exist anywhere**: tap, double-tap (mobile) and click (desktop, cursor stays `auto`) all do nothing — no lightbox, no scale, no dialog. Browser pinch-zoom is still available (viewport meta is `width=device-width,initial-scale=1`, not locked), which is the only way to inspect fabric.
- **Verdict:** partly
- **Shopper impact:** Navigation is flawless, but two photos and no zoom is thin evidence for a £60 garment — you cannot check the denim wash or stitching without pinch-zooming the whole page. On desktop there is no recourse at all.
- **Screens:** f-product-record-gallery-initial, f-product-record-thumbs-1, f-product-record-thumbs-2, f-product-record-gallery-after-swipe, f-product-record-gallery-after-imgtap

### 2. Select every available size — price, stock line, URL
- **Should:** Each tap updates the selected state, price, stock line and `?variant=` in the URL.
- **Did:** On cb2-wash-jeans, tapped XS→S→M→L→XL in turn. Every tap: `aria-pressed` moves, hidden form id and URL `?variant=` update to the correct variant id (verified all five ids distinct), price stays $83.00 (single-price product — correct), stock line stays `IN STOCK` for XS–L and switches to **`3 LEFT IN SIZE XL`** for XL (real low-stock, threshold 3; the XL button also carries a small corner dot). Dispatch line unchanged ("Ordered now — leaves tomorrow"). Same behaviour on v2-baggies' two available sizes.
- **Verdict:** works
- **Shopper impact:** Copy/paste the URL and the right size is preserved. The "3 LEFT" line is real scarcity stated plainly — earns trust.
- **Screens:** f-product-record-jeans-sizes-initial, f-product-record-jeans-size-selected

### 3. Sold-out size on v2-baggies — selectable, notify form, valid + invalid email
- **Should:** SPEC §9.3 sold-out sizes stay selectable (`aria-disabled`); buy button swaps for the notify form; form accepts a valid address and rejects an invalid one.
- **Did:** M, L, XL are sold out and carry `aria-disabled="true"` while staying tappable and in the tab order (confirmed, matches SPEC §9.3 — not a bug). Tapping M: sizes render struck-through with dashed borders, stock line goes red **`SIZE M IS SOLD OUT`**, the buy button stays visible but becomes disabled **`SOLD OUT`**, the Shop Pay button disappears, both dispatch lines hide, and a red-bordered notify panel appears: **`TELL ME WHEN THIS SIZE IS BACK`** + "email address" + `NOTIFY ME`. (The `RELEASED — NO LONGER IN CUSTODY` copy is reserved for a fully sold-out product — the size-level flow is deliberately plain English; a shopper never sees fiction here.) The hidden `contact[variant]` field correctly carries "M". **Invalid submit** ("notanemail"): the browser's native validation blocks it — "Please include an '@' in the email address" — no reload, no data lost. **Valid submit** (audit-notify@example.com): an **hCaptcha puzzle modal appears over the page — "Drag the shape into its outline"** (Shopify contact-form bot protection). The harness cannot solve a captcha, so the confirmation state ("Logged. We will email you when this exhibit returns.", per the section setting) was **not observed** — a human completes one drag puzzle first. Small extra: selecting a sold-out size does not update `?variant=` (URL keeps the last available size), so a shared link reopens on S, not M.
- **Verdict:** partly
- **Shopper impact:** The sold-out treatment is the best-looking state on the page and completely unambiguous. But the notify signup costs a captcha puzzle after the tap — some shoppers will abandon there, and nobody at the store will know. Confirmation-after-captcha remains unverified.
- **Screens:** f-product-record-soldout-notify-panel, f-product-record-notify-invalid, f-product-record-notify-valid-panel (captcha visible)

### 4. ADD TO BAG with no size selected
- **Should:** A clear "select a size" prompt (common expectation).
- **Did:** The state cannot occur: **on every fresh load the first available size is already selected** (XS on both test products; the URL even gains `?variant=` before you touch anything). Tapping ADD TO BAG on a fresh v2-baggies load added **size XS** immediately — feedback "Added — 1 in bag  View bag", header count `BAG [0]`→`[1]`, no navigation. No warning, no prompt, because from the theme's point of view a size *is* selected.
- **Verdict:** partly
- **Shopper impact:** You can never be scolded — but you can absolutely buy XS without ever choosing a size. On a phone the size row is visible right above the button, so the risk is moderate, but a hurried shopper tapping the sticky bar (which also defaults to `· XS`) never sees the size row at all. Wrong-size orders become the store's returns problem.
- **Screens:** f-product-record-buy-area-before-add, f-product-record-after-blind-add

### 5. The four accordions
- **Should:** SPEC: Specification / Measurements / Item description / Chain of custody, all default closed, opening one closes the others (`<details name>`).
- **Did:** Four accordions in order: **SPECIFICATION, ITEM DESCRIPTION, MEASUREMENTS, CHAIN OF CUSTODY — SHIPPING & RETURNS.** All default closed (deliberate per SPEC §9.4 — not reported as a bug). Each opens on one tap with a +/− icon and correct `aria-expanded`. **Opening one does NOT close the others** — I opened all four and all four stayed open. The build uses buttons + `hidden`, not `<details name>`; the SPEC's mutual-exclusivity claim does not match the deployed behaviour. No shopper cost — independent panels are arguably friendlier. What hides behind them: Specification = real data (500gsm cotton, Made in Portugal, care). Item description = the raw product description **including the delivery-time contradictions and the odd height chart** (see 6/10). Custody = the four-step Logged/Dispatched/In transit/Delivered log that quietly contains the shipping and returns answers.
- **Verdict:** partly
- **Shopper impact:** Nothing breaks, but the single most purchase-critical copy (shipping cost basis, 14-day returns) sits closed by default under the fiction-flavoured heading "CHAIN OF CUSTODY" — a shopper scanning headings may not guess that's where returns live; the "— SHIPPING & RETURNS" suffix is doing all the work.
- **Screens:** f-product-record-accordion-specification, f-product-record-accordion-provenance, f-product-record-accordion-measurements, f-product-record-accordion-custody

### 6. Measurements — find time, cm/inch toggle, method, realness
- **Should:** Findable quickly; toggle converts correctly; method stated; numbers credible.
- **Did:** From the top of the page: the MEASUREMENTS heading sits ~1.5 viewports down (y≈1284 of a 2641px page) — two swipes plus one tap, under 10 seconds; via the SIZE GUIDE button it is one tap (see 7). Toggle: CM→IN converts correctly — spot-checked 38cm→15in and 76cm→29.9in (÷2.54 ✓), and the caption swaps to "ALL MEASUREMENTS IN INCHES." Method is stated: **"GARMENT LAID FLAT."** The row for the selected size is highlighted (`data-active`). Realness: **v2-baggies (sweatpants) and cb2-wash-jeans (denim) show the *identical* table** — WAIST 38/40/42/44/46, INSEAM 76–84, RISE 27–31, HEM 19–23, every column a perfect +2/+1cm arithmetic ladder. Two different garment types with byte-identical laid-flat measurements reads as generated placeholder data, exactly as the known open item says (both products checked here are affected).
- **Verdict:** partly
- **Shopper impact:** The component is genuinely good — better than most size-guide PDFs. But a shopper who owns one CROOKSLDN piece and cross-checks will spot the duplicate table and stop trusting the numbers; anyone ordering jeans off a 38cm laid-flat waist for XS is trusting fiction. Replace the data, not the component.
- **Screens:** f-product-record-measurements-cm, f-product-record-measurements-in

### 7. SIZE GUIDE control
- **Should:** One tap scrolls to Measurements.
- **Did:** SIZE GUIDE button sits directly under the stock line (visible one small scroll from load). One tap: the Measurements accordion opens itself and the page scrolls so the **heading lands at exactly y=0** (top of viewport, nothing covering it — the header does not stick). The currently selected size's row arrives pre-highlighted. No modal, no PDF, no new page.
- **Verdict:** works
- **Shopper impact:** This is the fastest size-guide pattern I have seen on a small store — question to answer in about a second.
- **Screens:** f-product-record-sizeguide-landed

### 8. Dispatch line
- **Should:** ~22:00 Tuesday, cutoff 18:00, dispatch Mon–Sat → "leaves tomorrow".
- **Did:** Two lines: a static "Order before 18:00 and it ships today (Mon–Sat)" and beneath it the computed **"> Ordered now — leaves tomorrow"** — correct for 21:45–23:00 London on a Tuesday. Both hide when a sold-out size is selected (no false promise next to SOLD OUT — good detail). The pairing reads slightly at odds for a beat ("ships today… leaves tomorrow?") until you parse the first line as the rule and the second as your case; the `>` prefix helps.
- **Verdict:** works
- **Shopper impact:** Honest, current, and specific — this is the line that converts a hesitant late-evening buyer.
- **Screens:** f-product-record-firstload-slow4g-top (both lines visible), f-product-record-desktop-top

### 9. Sticky bottom bar
- **Should:** Appears when the main buy control is off-screen; carries the selected size; doesn't bury content.
- **Did:** Mobile only (display:none on desktop, confirmed). Because the buy button sits just below the fold, the bar is **visible from the moment the page loads**, disappears when you scroll the real buy button into view (verified hidden at scrollY≈600), and returns everywhere else — top, accordions, related, footer. It carries title + live price + selected size ("V2 BAGGIES | $83.00 · S" after choosing S) and both actions. 69px tall; at page end an 88px spacer un-hides so the last footer links sit clear above it — nothing is permanently covered. Sticky ADD works (bag [1]→[2], "Added — 2 in bag"); sticky **CHECKOUT NOW goes straight to a real Shopify checkout** (landed on checkout - CROOKSLDN, cart carried the chosen size; audit stopped immediately at that first page, nothing entered).
- **Verdict:** works
- **Shopper impact:** You are never more than one tap from buying, and the `· XS` default in the bar is the visible symptom of finding 4 — someone can check out from the footer having never seen the size row.
- **Screens:** f-product-record-stickybar-down, f-product-record-stickybar-with-size, f-product-record-stickybar-pageend, f-product-record-stickybar-added, f-product-record-checkoutnow-landing

### 10. From the PDP: shipping cost and returns policy
- **Should:** Both findable in a few taps.
- **Did:** **Path actually taken (shipping):** opened CHAIN OF CUSTODY — SHIPPING & RETURNS (1 tap, ~5s) → free thresholds stated ("Free UK shipping over £20, free Tracked 24 over £70", Royal Mail Tracked, UK 1–2 working days) but **not the price under £20** → scrolled to footer (one long swipe) → SHIPPING link (2nd tap) → `/policies/shipping-policy` states it: **"standard £3, Tracked 24 £4.99"**. Total 2 taps + 1 scroll, ~20s. **Returns:** already answered inside the same custody accordion (1 tap: "14 days from delivery, unworn, tags attached, email crooksldn@gmail.com"); the full policy is footer → REFUNDS (1 tap) → `/policies/refund-policy` with the return address and free-UK-size-swaps detail. No links inside the custody accordion itself — a "full policy" link there would save the footer trip. **The contradiction a shopper hits on the way:** the ITEM DESCRIPTION accordion one tap above says **"9-16 days delivery uk / 16-21 days international"** on the jeans and "3-5 day delivery uk" on the baggies, flatly contradicting custody's "UK 1–2 working days" and the policy (known open item — confirmed a shopper meets it, one accordion apart, and the odd "5,1-5,4 XS" height chart sits in the baggies description too).
- **Verdict:** works
- **Shopper impact:** Both answers are reachable and consistent between custody, status bar and policies. The description contradiction is the real cost: a jeans buyer reading "9-16 days uk" two centimetres above "UK 1–2 working days" now doesn't know which to believe — that's a trust wobble at the exact moment of deciding.
- **Screens:** f-product-record-accordion-custody, f-product-record-footer-links, f-product-record-shipping-policy, f-product-record-returns-page, f-product-record-jeans-description

### 11. Related products
- **Should:** Same category / sensible.
- **Did:** Heading **"MORE FROM THIS DROP"**. v2-baggies (sweats) → Charcoal Cellblock Crewneck + Charcoal Cellblock Shorts (both sweats). cb2-wash-jeans (denim) → Blue Wash Jorts, Grey Wash OG Jeans, Grey Wash Jorts (all denim). Cards show image, name, price; sold-out related items would carry a SOLD OUT tag (none were).
- **Verdict:** works
- **Shopper impact:** Genuinely same-category, no filler — a denim buyer sees only denim.
- **Screens:** f-product-record-related-v2-baggies, f-product-record-related-cb2-wash-jeans

### 12. Desktop pass — cb2-wash-jeans
- **Should:** Arrow keys work in the gallery; sticky bar behaves; nothing materially broken.
- **Did:** Clean two-column layout (gallery 637px left, buy panel 455px right). Focus the gallery and **ArrowRight/ArrowLeft change slides** with the counter updating; no wrap at the ends (Right on photo 2 stays put). There are no on-screen prev/next arrow buttons on either device — keyboard, thumbs or swipe only. Sticky bar correctly absent at every scroll depth. Tab order through the buy panel is exactly XS→S→M→L→XL→SIZE GUIDE. Click on the photo does nothing (no zoom, cursor `auto`). Buy panel shows ADD TO BAG + "Buy with shop" + "More payment options". Nothing materially different or broken versus mobile.
- **Verdict:** works
- **Shopper impact:** Fine but forgettable in the best way — the desktop page is the mobile page with room to breathe.
- **Screens:** f-product-record-desktop-top, f-product-record-desktop-arrowkeys, f-product-record-desktop-bottom

---

## Off-checklist observations

- **Cookie banner (new since SPEC):** present on first visit, ~360px tall on a 844px phone, covering the buy area and sticky bar until answered. It also intercepted taps in testing. Not in SPEC's build map; SPEC §10 lists "no cookie banner" as pending store work — so this is store-side progress, but its mobile footprint is heavy.
- **Currency mix for non-UK sessions:** prices convert to USD (Markets working), but the status-bar ticker ("FREE UK SHIPPING OVER £20"), custody copy and policies stay in £. A US shopper reads $83.00 next to a £20 threshold. UK shoppers unaffected.
- **Notify-form captcha:** Shopify-level, not theme code, but it is real friction on the restock capture path.
- **No wishlist / "Only X in stock" injection seen** (known O2, app bestpush-101): neither element appeared in any of my PDP sessions — either the app is quiet on staging preview or it has been removed.
- **10CROOKS / set toggle:** not exercised here (cart/set is another agent's area); the set toggle did not appear on either test product, correct since neither is a set member.
