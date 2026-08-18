# FEATURES.md — Phase 1: the real feature surface, worked as a shopper

Run 2026-08-18 (Tuesday evening, ~20:00–23:00 London) against staging theme
`202053779799` via the share-preview URL. **Staging verified in every browser
context** (`.crk-root` present + `crooks.css` requested) before any navigation;
the preview bar itself read "CROOKSLDN — Staging / Draft". Default conditions
390×844 @ DPR 3, Slow 4G + 4× CPU for load passes; desktop 1440×900. Eight
areas, 41 checklist items. Detail per item lives in `raw-*.md` beside this file;
this is the consolidated register.

**Three run caveats that colour individual verdicts:**

1. **The audit egress IP geo-locates to the US.** Shopify Markets therefore
   served USD prices until sessions were pinned with `?country=GB`. Everything
   below was verified in the GB market. The USD observations are real behaviour
   for any non-UK visitor and are noted where they matter.
2. **A cookie consent banner exists on staging.** The task brief's known-items
   table says "no cookie banner" — that is stale. Shopify's privacy banner is
   live, skinned convincingly on-theme, and on first visit covers ~40–60% of a
   phone viewport; its alertdialog intercepted taps on `ADD TO BAG` twice
   during testing until answered. Related to RUN3 B5, but the brief should
   stop saying the banner is missing.
3. **Preview-domain limits.** Three behaviours could not be fully verified and
   need a one-off retest on the live domain before anyone acts on them:
   Shopify Forms mounting (informant intake), the `10CROOKS` cart→checkout
   handoff, and hCaptcha frequency on the notify/contact forms.

---

## CHECKPOINT SUMMARY — what is broken

Ordered by what it costs a shopper.

| # | Broken thing | What a shopper hits | Evidence |
|---|---|---|---|
| B-1 | **Informant intake never renders its form.** The Shopify Forms block (`forms-root-923202`) never mounts: heading, copy and SMS small print render, then nothing — no phone field, no email field, no button. Three sessions, cookie-accepted, 10s waits. | The homepage's only signup mechanism is a headline over an empty box. Signup impossible. *Retest on live domain — Forms may refuse the preview host.* | `raw-homepage.md` §7 |
| B-2 | **The set's saving confirmation never shows in the normal case.** With only the £85 bundle in the cart — the outcome of the intended flow — the set-cart section renders nothing. "SET SAVING APPLIED — £10" appears only when a loose component sits *beside* the bundle, i.e. exactly the £130 duplicate-shorts cart where it is misleading. | The set buyer never gets the cart-side "you saved £10" moment; the confused buyer gets it while being overcharged. | `raw-set-feature.md` §6–7 |
| B-3 | **The half-set cart offer walks the shopper into £95 or £130.** Cart line "Complete the set — add the Cellblock Crewneck, save £10." links to the crewneck PDP; adding it plainly yields £95 with **no saving**; using the toggle instead yields the £85 set **plus** the original £45 shorts = £130 with duplicate shorts. Nothing says "remove your original item". | The one shopper who obeys the cart's own upsell ends up worse off than the promise, silently. | `raw-set-feature.md` §7 |
| B-4 | **Catalogue filter resets on back-navigation.** DENIM (4 cards) → open a product → browser back → ALL (14 cards). Nothing carries the filter. | Every product viewed from a filtered register costs a re-filter; the comparison shopper pays it repeatedly. | `raw-homepage.md` §4, corroborated `raw-toggles-edge.md` |
| B-5 | **`10CROOKS` evaporates between cart and checkout** (preview caveat). Applied in cart: £25 tee → £22.50; set → £76.50 (O1 confirmed live). At checkout the discount is gone (full £75 charged) and re-entering returns "Enter a valid discount code". Likely the preview→live-domain cart handoff — **must be retested on crooksldn.com**; if real, shoppers reach payment overcharged and told their code is invalid. | Worst-case: a code-holding shopper abandons at the payment screen, insulted. | `raw-cart-checkout.md` §6 |

## CHECKPOINT SUMMARY — expected to exist, couldn't find

| # | Missing thing | Why it was expected | Evidence |
|---|---|---|---|
| M-1 | **Gallery zoom, any form.** Tap, double-tap, click — nothing, mobile or desktop. Two photos per product and no way to get closer than pinch-zooming the page. | £60 garments bought on fabric and stitching detail. | `raw-product-record.md` §1 |
| M-2 | **A "select a size" state.** First available size (XS) is preselected on every load, so the "add without choosing" prompt SPEC implies is unreachable — a blind `ADD TO BAG` silently adds XS. | Spec'd check "ADD TO BAG without selecting a size — what are you told?" Answer: nothing, you bought XS. | `raw-product-record.md` §4 |
| M-3 | **The lookbook block.** `media-with-content` renders 0px — no image, no text. Homepage goes straight from (empty) intake to footer. | SPEC §2 route map lists it on the homepage. | `raw-homepage.md` §8 |
| M-4 | **Header wordmark.** No CROOKSLDN text in the header at any width; inner pages carry only the handcuffs logo (alt text aside). SPEC §3.1 says the header renders one. | Brand-name reinforcement on every non-home page. | `raw-header-drawer.md` §1 |
| M-5 | **ACCOUNT in the header.** Only entry point is the last row of the drawer, *below* the CASE 001 board. | SPEC §3.1 lists ACCOUNT among header elements. | `raw-header-drawer.md` §1 |
| M-6 | **Sub-threshold shipping prices anywhere pre-checkout.** Free tiers are advertised loudly (ticker + bar); the £3.00 / £4.99 prices below them appear only after entering an address at checkout — on the storefront they exist solely in the shipping policy. | A £6 socks buyer commits blind on a £3–£5 question. | `raw-cart-checkout.md` §7 |
| M-7 | **A "full policy" link inside the custody accordion.** Returns summary is excellent there, but reaching the full policy means a footer hunt. | One line would save the trip. | `raw-product-record.md` §10 |

---

## STAGING ≠ SPEC — build drift found while shopping

These matter beyond individual verdicts because `SPEC.md` is the audit's map.

1. **PDP accordions are not `<details name>`.** The served DOM has zero
   `<details>` elements; the accordions are JS `aria-expanded` buttons. Two
   consequences observed: opening one does **not** close the others (SPEC §3.5
   says mutually exclusive), and — the real cost — **with JS off the accordion
   bodies are unreachable**, so Specification, Measurements, Item description
   and Chain of custody are all unreadable, a regression against SPEC §9.11's
   no-JS contract (the *sell* path itself still works no-JS: noscript variant
   links + native `/cart/add` verified end to end).
2. **The crewneck PDP has no Measurements accordion at all** while the jeans
   PDP has one — either missing metafield data or template drift.
3. **The carriage bar is cart-gated.** It renders literally nothing on an
   empty cart, even for GB. SPEC §3.7 (and the round-2 council complaint about
   1.22→1.48 viewports) describes an always-present bar. Measured now: first
   catalogue card at **0.90 viewports** with an empty bag, 1.09 with items.
   The old real-estate complaint no longer reproduces — the gate defused it.
4. **The sold-out flow's copy differs from SPEC §3.5**: selecting a sold-out
   size gives plain "SIZE M IS SOLD OUT" + "TELL ME WHEN THIS SIZE IS BACK";
   "RELEASED — NO LONGER IN CUSTODY" is only the whole-product-sold-out branch.
   (Fine for shoppers — arguably clearer — recorded as drift, not a defect.)
5. **Un-specced additions present:** Shopify dynamic-checkout buttons ("Buy
   with Shop" / "More payment options") in the PDP buy stack; "More from this
   drop" on the PDP and "You may also like" on the cart.
6. **No-JS dispatch line is stale**: generic "order before 18:00, ships today"
   showing at 21:00 (the JS-computed line is correct: "leaves tomorrow").

---

## The feature register — verdicts

Format: item — verdict — the one thing worth knowing. Full should/did/verdict
per item in the named raw file.

### Header, drawer, board, status bar (`raw-header-drawer.md`) — 17 works · 4 partly · 1 absent

- Logo / CATALOGUE / SEARCH / BAG — **works**. BAG cell is fixed-width: count 0→1→3 with zero header reflow (x=144.8, w=61.3 constant).
- ACCOUNT — **partly**: absent from header; lives at the very bottom of the drawer, under the board.
- Wordmark — **absent** (see M-4).
- Drawer open/close — **works**: MENU relabels to CLOSE, `aria-expanded`, Escape closes, focus returns to trigger. Scrim-close exists only on desktop (mobile drawer is full-screen — no scrim to tap).
- Browser back with drawer open — **partly**: navigates away rather than closing the drawer; gesture-back Android users will lose the page they were on.
- CASE 001 panel — **works**: board injected on first open (0 requests before, 1 after), animates smoothly; `PLAY CASE:001 NOW` opens the game in a **new tab** so the shop survives. O4 shopper check: caption art implies coin-collecting, game says "recover 3 evidence packages" — same tileset, effectively unnoticeable. **But** the footer's "Play CROOKSLDN: The Getaway" link opens the same game in the **same tab** — that route strands a shopper off-site.
- Board-off-homepage judgement — nothing on the homepage now carries the board's playful weight; discovery is decent *for menu-openers* (the board peeks into the first drawer view) and zero for everyone else.
- Status bar — **works** as experienced: rotates at a clean 8.0s (D1 means the configured 5 is ignored — confirmed, costs nothing at 8s), real `[count]` = 14, pauses on hover, stops entirely under reduced motion.

### Homepage (`raw-homepage.md`) — 9 works · 2 partly · 2 broken · lookbook absent

- Slow-4G first paint — **protect**: ticker, header, wordmark, tagline and typing boot line readable within ~1s, no jumping. The brand moment survives bad data.
- Hero — **works**; only one of the two possible buttons is configured; CATALOGUE anchors precisely to the register.
- Category filters — **works** (instant, correct counts, unmistakable active state) **but** the "14 ITEMS" counter never updates when a filter narrows the register, and the filter resets on back-navigation (B-4).
- Flat / On model — **partly**: toggle works; all 14 cards share one placeholder model photo, so the CREWNECK card shows a man in a *t-shirt* — reads as a bug and misleads on fit. Not one product has a real `model_image`.
- Outline toggle — **works** as built: pre-paint, no flash, session-persisted. (Judgement deferred to O3/Q3.)
- Colourway swatches — decoration inside the card link (aria-hidden); tapping opens the PDP. Only the 4 tee cards have them.
- Packaging section — **works**, best block on the page: photo scene-markers 1/2/3 cross-reference the 01/02/03 manifest; "Nothing here is an extra you pay for."
- Informant intake — **broken** (B-1).
- Lookbook — **absent** (M-3).

### Register + search (`raw-register-search.md`) — 7 works · 1 partly

- Status slot on every card — **works** on all 14 + search cards; drop date always the separate, de-emphasised element.
- Sold-out telegraphing — **partly**: product-level only. V2 BAGGIES reads `AVAILABLE` while M/L/XL are gone — the mid-size shopper burns a click to find out. (Design is as SPEC'd; the size-level blindness is the recorded cost.)
- Card hit-area — **works**: whole-card single `<a>`; image, title, price all open the product.
- Collection h1 — **works** everywhere; `/search` is the only template without an h1 in any state (results heading is h2).
- Cosmetic: on odd-count collections (sweats, 3 items) the empty grid cell renders as a **solid bright-purple rectangle** — looks like a glitched tile.
- Search queries — **works**: "jeans" 8 sensible results; "BAGGIES" direct hit; misspelt "bagies" still ranks V2 BAGGIES first; gibberish states 0 clearly; empty query stands the register down exactly as designed (§9.8).
- Typeahead — **works**; direct links (TRACK YOUR ORDER, QUESTIONS, START A RETURN) show pre-typing; "terms"/"returns"/"privacy"/"track"/"refund" all reach their destinations — **search is a working route to Terms/FAQ/policies**, which Shopify alone cannot do.
- Rough edges: "N RESULTS" counts products only, so "terms" shows **"0 RESULTS"** directly above the PAGES & ANSWERS block that contains the answer; a matched direct link renders twice (matched block + always-on list).

### Product record (`raw-product-record.md`) — 7 works · 5 partly

- Gallery — **partly**: everything navigates (swipe, thumbs, arrow keys, counter) but two photos per product and **no zoom** (M-1).
- Size selection — **works**: price/stock/URL all update; `?variant=` survives history, reload and sharing. Sold-out size selection deliberately does not rewrite the URL (shared links reopen on an available size).
- Sold-out size flow — **protect**: aria-disabled sizes stay tappable, struck-through; red "SIZE M IS SOLD OUT"; disabled SOLD OUT button; per-size notify panel with the correct hidden variant. Invalid email blocked natively. **Valid submit triggers an hCaptcha drag-puzzle** — confirmation state unverifiable, silent-abandonment risk on the restock capture (preview caveat; retest live).
- Add without size — **the state doesn't exist** (M-2): XS preselected, blind add silently succeeds.
- Accordions — **partly**: work, default closed; not `<details>` (see drift §1); purchase-critical shipping/returns copy sits under the fiction-flavoured "CHAIN OF CUSTODY" heading where the "— SHIPPING & RETURNS" suffix does all the work.
- Measurements — component **protect**, data known-bad and **worse than logged**: v2-baggies and cb2-wash-jeans serve the *byte-identical* +2cm-ladder table — jeans and sweatpants cannot share measurements. cm→in verified (38→15), method stated, selected size pre-highlighted, findable in <10s.
- SIZE GUIDE — **works**: one tap, opens the accordion, heading lands at exactly y=0.
- Dispatch line — **works**: "Ordered now — leaves tomorrow" correct for 22:00 Tuesday against the 18:00 Mon–Sat cutoff; hides when a sold-out size is selected.
- Sticky bar — **works**: appears only while the real buy button is off-screen, carries live price + size, spacer keeps the footer clear, mobile-only. `CHECKOUT NOW` checks out the **whole bag**, not a solo buy-now.
- Shipping cost + returns from the PDP — **works**: returns answered in 1 tap (custody accordion: 14 days, unworn, tags); shipping thresholds same tap; the sub-threshold *price* needs footer → shipping policy (2 taps + scroll, ~20s) (M-6/M-7). **On the way, the shopper meets the description contradiction**: jeans "9-16 days delivery uk" one accordion above custody's "UK 1–2 working days"; baggies say "3-5 day delivery uk" — a *second* wrong number in the same defect family.
- Related products — **works**: strictly same-category, no filler.
- Low-stock honesty — "3 LEFT IN SIZE XL" from real inventory; O2's injected wishlist/"Only X in stock" **never appeared** in any session — possibly gone.

### Complete-the-set (`raw-set-feature.md`) — 7 works · 1 partly · 1 broken

- Collapsed line, tick, partner sizes, prices — **works** and reads honestly: partner size row appears with live stock, was/now prices correct, button relabels "ADD THE FULL FIT — £85" (no trailing .00 — style drift from SPEC's £85.00, consistent within the UI). Partner size **pre-mirrors the shopper's main size** until overridden — genuinely good.
- Add — **works**: ONE cart line, £85.00, naming both garments and both sizes.
- Untick / reload — **works**: exact restore; tick does not survive reload (the safe answer).
- Sold-out partner path — **unexercised** (all 25 bundle variants in stock); the built mechanism (aria-disabled + "pick another size" copy) is present in the DOM.
- Set-cart, bundle-only — **broken** (B-2). Set-cart, half-set offer — **partly/trap** (B-3).
- USD session note: all set prices converted cleanly ("Save $15") because every price is Liquid-prerendered — the guardrail working exactly as designed.

### Cart, carriage, checkout (`raw-cart-checkout.md`) — 7 works · 3 partly

- Carriage bar maths — **works** on any full page load and live-updates on cart-page operations: "£14.00 to free Tracked 48" → "£39.00 to free Tracked 24" → "Free Tracked 24 — unlocked", exact at every stage. **But** the PDP's own `ADD TO BAG` never updates it (§partly): after crossing a tier it shows stale copy until the next page load — the one moment the shopper unlocks free shipping, the bar disagrees.
- Bar position — the empty-cart stand-down means it costs nothing until the shopper is mid-purchase (first card 0.90 viewports empty-bag). The round-2 complaint is resolved in practice.
- Cart operations — **works**: totals exact through every op (three-item £91, qty×2, discounts −£2.50/−£8.50). Decrease at qty 1 is a **silent no-op**; Remove works, labelled, **no undo**.
- `10CROOKS` — cart **works** / checkout **fails on preview** (B-5). O1 confirmed as logged: set → £76.50.
- Checkout — **stock white Shopify skin**: plain-text CROOKSLDN, no logo, no dark anything — a real jolt after the darkest storefront imaginable (checkout branding settings, not theme code). "Keep me updated" email marketing arrives **pre-ticked**. Rate card at checkout matches the storefront promise to the penny (£3.00/£4.99, free at £20/£70, cheapest auto-selected).
- **New contradiction found at checkout:** Tracked 48's delivery estimate rendered "Fri 28 Aug" (once "Mon 24–Wed 26") for a Tue-evening order — 4–8 working days for a service named *48*, against custody's "UK 1–2 working days". Tracked 24's "Thu 20–Fri 21" is honest.
- Persistence — **works**: back-from-checkout intact; returning-session cart intact; two tabs consistent on reload.

### Content pages + 404 (`raw-content-pages.md`) — 2 works · 5 partly

- FAQ — **protect**: 14 questions, 4 groups, concrete and correct (delivery windows, thresholds, 14-day window, payment), working links. One-at-a-time accordions keep it short on mobile.
- Terms — **protect** for copy and structure (clause index with working anchors, LAST REVISED 13.08.2026 matching the legal ToS). **Contradiction**: Terms grants 14 days to *notify* + 14 to *post back* (~28 days effective); refund policy says "14 days from delivery to return". A day-20 shopper doesn't know which governs. Also: transit-damage window 48h (Terms) vs 14 days (shipping policy); three different return *routes* across surfaces (custody: email / FAQ+Terms: Aftership portal / refund policy: email or DM).
- Tracking signed-out — **RUN3 A6 unfixed**: FAQ still promises "look your order up on the tracking page — no account needed"; the page offers guests only SIGN IN and a pointer to the dispatch email. The page's own guest line is honest; the FAQ oversells it.
- Policies — **works**: all five dark, mono, on-brand, readable; emails now consistent `crooksldn@gmail.com` (the `.com.com` typo is gone; one capitalised variant remains). **New dead promise**: contact-information policy ends "Prefer a form? Drop your details below" — no form exists or can exist on a policy page, and `/pages/contact` isn't linked.
- Contact page — **partly**: the form works (hCaptcha-gated) but it's Horizon's **cream light template inside the dark site**, with zero supporting copy. The 404 is genuinely useful (real 404, Continue shopping, four live recommendations) but shares the same cream break.
- Governing law: the *legal* ToS has it (England and Wales, §18) — SPEC's "no governing-law line" applies only to the plain-English page.

### Toggles + edge conditions (`raw-toggles-edge.md`) — 5 works · 4 partly

- Light/dark — **works** across all 9 templates, pre-paint resolver, zero flash even on slow 4G, persists, scroll position preserved on mid-scroll toggle. **One real casualty: in light mode the search page's SEARCH submit button is near-invisible (contrast 1.38)** — a light-mode shopper loses the only visible way to submit a search.
- Outline in light mode — treatment deliberately suppressed but the button stays live: pressing it changes nothing visible while silently toggling state for dark mode later. Dead-control feel (evidence for O3).
- Reload/back-forward — **works**; `?variant=` URL rewriting makes size selection survive history, reload and sharing (protect).
- Direct-landing PDP — **works**: fresh session straight to product → size → add → cart. The Instagram path is self-sufficient.
- Landscape — **partly**: home/PDP survive; **cart line-item title renders on top of the product thumbnail** (rects confirmed overlapping) — usable but looks broken at the trust-sensitive review moment.
- 200% zoom — **works**: full purchase path completable, no horizontal scroll (cookie banner covers ~45% of short viewports until answered).
- JS off — the store still **sells** (14-card homepage with prices, noscript size links, native `/cart/add`) but the accordion regression (drift §1) makes all PDP copy unreadable and the dispatch line goes stale.
- Keyboard — **works**: skip-link first, visible 2px lavender ring throughout the buy path, drawer trap cycles correctly (30 Tabs never escape), Escape returns focus to MENU.

---

## Known items — the shopper cost, as instructed

| Ref | Confirmed shopper impact |
|---|---|
| D1 | Invisible. 8s rotation reads fine; nobody would guess a setting exists. Cost: zero (admin frustration only). |
| O1 | Real and live in cart: set → £76.50. The deeper problem is B-5: on preview the code then *dies at checkout*. If live behaves the same, O1's "stacking" worry is overtaken by "the code doesn't survive checkout at all". Retest live. |
| O2 | Wishlist / "Only X in stock" **never appeared** in any of ~30 sessions across 8 agents. The bestpush-101 injection looks gone or dormant. |
| O3 | Outline toggle works technically (pre-paint, persisted, honest). Light mode turns it into a dead control; it exists only on the homepage register while its state silently applies to collection/search registers that offer no control. Full judgement in Phase 3 Q3 with persona 11's evidence. |
| O4 | Confirmed cosmetically out of step (coins vs evidence packages) and confirmed **unnoticeable** — same tileset, same palette. No shopper cost found. The *footer* route to the game (same-tab) is the actual cost in that neighbourhood. |
| Placeholder measurements | Worse than logged: jeans and baggies serve byte-identical tables. A shopper who checks two products will see the same numbers on garments that cannot share them. |
| `.webp` masters | Not directly visible to shoppers in these tests; not re-measured (behavioural audit). |
| Cookie banner | The brief says none; **staging has one**. On-brand, correct behaviour, but 40–60% of a phone viewport and it intercepts buy-area taps until answered. |
| V2 BAGGIES delivery copy | Now says "3-5 day delivery uk" — different wrong number than the logged one; jeans still say "9-16 days". Both sit one accordion above "UK 1–2 working days". |
| Undescribed collections | Invisible to shoppers (registers render fine); no impact observed. |

---

## What Phase 1 says should go straight to the protect list

(Consolidated in `KEEP-ADDITIONS.md` at the end of the audit.)

1. The **empty-cart stand-down of the carriage bar** — it killed the round-2 real-estate complaint.
2. **`?variant=` URL rewriting** on size selection — history, reload and shared links all restore the size.
3. The **fixed-width BAG [n] cell** — zero header reflow on count change.
4. **Lazy board injection** on first drawer open (0 requests before, 1 after).
5. The **pre-paint theme resolver** — zero wrong-theme flash even at slow 4G.
6. **Partner-size pre-mirroring** in the set toggle.
7. The **empty-search stand-down + curated direct links** — the only working route from search to Terms/FAQ/policies.
8. **Liquid-prerendered prices in data attributes** — the reason a USD session converted cleanly instead of breaking.
9. The **404's path back** (real 404 + recommendations) — content, if not yet its cream skin.
10. The **sticky bar's appear/disappear logic** tied to the real buy button's visibility.
