# RAW — Homepage (top to bottom)

Audited 2026-08-18 ~21:00–22:00 London, staging theme 202053779799 via preview URL.
Staging verified on every session (`.crk-root` + `crooks.css`). Device: mobile 390x844 DPR3.
Note on geography: the audit egress is non-UK, so the store geo-converted prices to USD
and hid GB-gated content by default. All functional runs below used `?country=GB`, which
restored £ prices. A genuinely non-UK shopper sees $ prices next to a ticker and carriage
copy that still say "£20" — recorded under surprises, not re-tested per item.

### Throttled first load (slow4g, cold cache)
- **Should:** Page arrives progressively and feels usable within a few seconds on a slow connection.
- **Did:** At ~1s the top of the page was already complete and readable: status ticker ("FREE UK SHIPPING OVER £20 — ORDER BY 18:00 FOR SAME-DAY DISPATCH"), cuffs logo, full nav row, and the hero — wordmark, tagline, CATALOGUE button — all painted, boot line mid-type. At ~3s nothing above the fold was still missing; catalogue images below the fold trickled in lazily (9/37 imgs at 1s, 11/37 at 9s — the rest load on scroll). The `load` event landed ~9.2s but a shopper is never waiting on it; the page feels usable at ~1s. No layout jumping observed between the 1s/2s/3s frames. The one real event of first load is the COOKIE CONSENT sheet squatting on the bottom ~43% of the screen (359px of 844) until dismissed — it reappears on every page until Accept/Decline is tapped.
- **Verdict:** works
- **Shopper impact:** Feels fast even on bad mobile data — the brand moment (wordmark + typing boot line) is fully delivered in the first second. The cookie sheet is the only thing between the shopper and the page.
- **Screens:** f-homepage-load-1000ms, f-homepage-load-3000ms, f-homepage-load-settled

### Hero — boot lines type out
- **Should:** Boot lines type out on load (SPEC §3.3), reading live product count.
- **Did:** Watched it character by character: "> " at ~0.4s, "> 14 PRO" at ~0.6s, full "> 14 PRODUCTS AVAILABLE TO PURCHASE" by ~1.1s. Count matches the real 14-product catalogue. sessionStorage gains `crk_booted:"1"` after the first run.
- **Verdict:** works
- **Screens:** f-homepage-hero

### Hero — wordmark
- **Should:** CROOKSLDN wordmark clearly visible.
- **Did:** Large pixel-face "CROOKSLDN" (h1, 56px tall) with "OWN THE STREETS™" tagline beneath, visible from first paint even on slow4g.
- **Verdict:** works
- **Screens:** f-homepage-hero, f-homepage-load-1000ms

### Hero — buttons
- **Should:** Up to two buttons (SPEC §3.3); brief expected both to be tappable with sensible destinations.
- **Did:** Only ONE button exists: "CATALOGUE" → `#products`. Tapping it jumps cleanly to the catalogue heading with the filter row and first cards in view — no page reload, no disorientation. There is no second button configured (no SHOP NEW / drops link).
- **Verdict:** partly
- **Shopper impact:** The one button does its job well. A second action (e.g. straight to NEW) is simply not offered; the hero is single-exit.
- **Screens:** f-homepage-hero-btn-catalogue

### Catalogue — category filter buttons
- **Should:** Filters derived from product type narrow the register client-side.
- **Did:** Tapped every filter. ALL→14 cards, T-SHIRT→4, DENIM→4, SWEATS→3, ACCESSORIES→3 (4+4+3+3=14, every product in exactly one bucket). Instant, no reload, active state clearly marked ("> " prefix + purple fill, aria-pressed). One wrinkle: the "14 ITEMS" counter next to the CATALOGUE heading never updates — it says 14 ITEMS while 3 cards are showing.
- **Verdict:** works
- **Shopper impact:** Filtering feels immediate. The stale "14 ITEMS" label is a small trust nick — the register says 14 while showing 3.
- **Screens:** f-homepage-filter-accessories

### Catalogue — Flat / On model view toggle
- **Should:** Swaps card imagery to model shots (crooks.model_image metafield, section-level placeholder for gaps).
- **Did:** The toggle works mechanically — every card's image swaps. But ALL 14 cards swap to the IDENTICAL photo (`crooksldn-charcoal-cellblock-shorts.png` — one model in a black tee and grey shorts on a pedestal). Jeans, socks, duffle bag, tees: every one shows the same man in the same outfit. Not a single product has its own model image; the placeholder is carrying the entire view. Card NO. 01 "CHARCOAL CELLBLOCK CREWNECK" shows a model wearing a t-shirt.
- **Verdict:** partly
- **Shopper impact:** Actively misleading. A shopper tapping ON MODEL to see fit gets a wall of 14 identical photos that match almost none of the products — it reads as a bug, and the crewneck card showing a t-shirt could seed a wrong-item worry. Worse than not offering the toggle. (Data problem, not component problem — the metafield is empty on all 14.)
- **Screens:** f-homepage-onmodel

### Catalogue — Outline toggle
- **Should:** White-outline treatment on product images (O3: pending an aesthetic call — do not treat existence as a bug).
- **Did:** Defaults ON in a fresh session. ON: garments carry a cream sticker-style outline (die-cut look). Tapping OUTLINE turns it off — plain product photos, button unpressed, change applies to all cards instantly with no reflow. Purely cosmetic; nothing else changes.
- **Verdict:** works
- **Shopper impact:** Subtle either way; a shopper likely never touches it, and if they do, nothing breaks. The sticker look is part of the register's character.
- **Screens:** f-homepage-outline-on, f-homepage-outline-off

### Catalogue — colourway swatches on cards
- **Should:** Colourway swatches on cards from option names (SPEC §3.4); brief asked what tapping one changes.
- **Did:** Only the 4 tee cards have swatches — two small colour dots plus a text line "Colourways: BLACK, WHITE". The dots are `aria-hidden` spans inside the card link: tapping one does nothing swatch-specific, it simply opens the product page like tapping anywhere on the card. No image swap, no variant preselection.
- **Verdict:** works
- **Shopper impact:** Honest passive indicators — nobody will be misled, but anyone expecting Shopify-standard tap-to-preview gets the PDP instead, which is where they were going anyway. Fine.
- **Screens:** f-homepage-swatch-before

### Filter persistence (filter → product → browser back)
- **Should:** Shopper returns from a product to the register in the state they left it.
- **Did:** Applied DENIM (4 cards), opened BLUE WASH OG JEANS from the filtered set, hit browser back. The filter was gone: ALL active, 14 cards showing. Nothing in the URL carries the filter, so back restores the default state.
- **Verdict:** broken
- **Shopper impact:** Comparison shopping across the denim rack costs a re-filter (and re-orientation) after every product viewed. On mobile that is the difference between checking 4 jeans and checking 2.
- **Screens:** f-homepage-filter-after-back

### Outline persistence (toggle → navigate away → return)
- **Should:** sessionStorage-backed (`crk-outline`), survives navigation within the session.
- **Did:** Toggled Outline OFF, went to a product page, came home via the header logo: still OFF, button unpressed, applied pre-paint (no flash of outlined images). A brand-new tab resets to the default ON — session-scoped exactly as SPEC says.
- **Verdict:** works
- **Screens:** f-homepage-outline-roundtrip

### Packaging — "EVERY ORDER SHIPS LIKE THIS"
- **Should:** Packaging photo + numbered manifest + asterisk footnote that makes sense.
- **Did:** Lands. Eyebrow "PROPERTY BAG", bold claim "EVERY ORDER SHIPS LIKE THIS", subline "Sealed, tagged and numbered before it leaves us. Nothing here is an extra you pay for." The photo shows crime-scene markers 1/2/3 next to the actual items, and the manifest below numbers them 01 EVIDENCE TAG / 02 SECURITY SEAL / 03 CUFF KEYRING * — photo and list cross-reference perfectly. The footnote "* CONTRABAND 03 SHIPS WITH SWEAT BOTTOMS ONLY." sits directly under item 03 and reads clearly (the keyring only comes with sweat bottoms). All legible at mobile width. Photo lazy-loads a beat after the text but within a second of scrolling to it.
- **Verdict:** works
- **Shopper impact:** Earns its scroll — it converts the fiction into a concrete "you get free stuff in the box" promise. "Nothing here is an extra you pay for" is doing real reassurance work.
- **Screens:** f-homepage-packaging, f-homepage-packaging-2

### Informant intake — form renders
- **Should:** SMS-first signup: phone field + submit (Shopify Forms app block, form_id 923202), email optional.
- **Did:** The section renders its chrome — "REGISTER AS INFORMANT", "Drops go to the register before they go public. One message per drop, nothing else.", a divider, and the small print "One text per drop. Reply STOP to leave the register at any time. We do not sell it." — and NOTHING ELSE. No phone field, no email field, no button. The Shopify Forms root div (`data-forms-id="forms-root-923202"`) is in the served HTML and the Forms app scripts (`shopify-forms-loader.js` + `index.js`) load, but the form never mounts: 0px tall after cookie Accept, 10s of waiting, and scrolling it into view. Verified across three separate sessions.
- **Verdict:** broken
- **Shopper impact:** The homepage's only capture mechanism is a dead promise: copy that talks about texts and STOP replies with no way to give a number. Shopper shrugs, scrolls past; the drop list gains nobody. (App-side mount failure, not theme markup — the theme's side of the contract is present.)
- **Screens:** f-homepage-informant-view, f-homepage-intake-after-accept

### Informant intake — submit valid number (07700 900123)
- **Should:** Accepts the number, confirms registration.
- **Did:** Impossible — there is no field to type into and no submit control anywhere in the section.
- **Verdict:** absent

### Informant intake — submit malformed number ("12345")
- **Should:** Rejects with a readable error.
- **Did:** Impossible — no field exists.
- **Verdict:** absent

### Informant intake — empty submit
- **Should:** Blocks with a prompt to fill the field.
- **Did:** Impossible — no submit control exists.
- **Verdict:** absent

### Informant intake — same valid number twice
- **Should:** Either dedupes gracefully or confirms again — but says something.
- **Did:** Impossible — no form.
- **Verdict:** absent

### Informant intake — optional email path (audit-intake@example.com)
- **Should:** Optional email field accepts and confirms.
- **Did:** Impossible — no email field renders either.
- **Verdict:** absent

### Lookbook block at the bottom
- **Should:** `media-with-content` section between informant intake and footer — some visual payoff.
- **Did:** It renders zero pixels. The section markup is in the page (Horizon `media-with-content` scaffolding, ~5 empty wrapper divs) but contains no image, no text, no link — computed height 0px. A shopper scrolling to the bottom goes straight from the intake box to the footer and never knows a lookbook was intended.
- **Verdict:** absent
- **Shopper impact:** Costs nothing visually (no broken frame, no gap) and earns nothing. Invisible dead weight.
- **Screens:** f-homepage-after-informant

### Top of page — carriage bar + first-card depth (observation)
- **Should:** Record whether a carriage/free-shipping bar renders at the very top and how deep the first product card sits.
- **Did:** With an EMPTY bag the carriage section renders literally nothing (0px, even with `?country=GB`) — the free-shipping fact instead reaches the shopper through the status ticker's rotating line at the very top ("FREE UK SHIPPING OVER £20 — ORDER BY 18:00 FOR SAME-DAY DISPATCH", alternating with "14 PRODUCTS CURRENTLY ONLINE"). Once something is in the bag, a 160px carriage block appears between header and hero with correct arithmetic: £6 sock in bag → "> £14.00 to free Tracked 48" with a two-tier progress bar (TRACKED 48 FREE / TRACKED 24 FREE); £66 in bag → "£4.00 to free Tracked 24". Page anatomy on first visit (390x844): status ticker 0–28px, header 28–139px, hero 139–460px, catalogue heading at 460px, first product card's top edge at 757px — so the first card just peeks over the first fold (~0.9 viewports down) and its image sits in viewport two.
- **Verdict:** works
- **Shopper impact:** Empty-bag visitors never see the carriage bar (SPEC reads as though it is always present) — arguably tidy, since the ticker covers the message without spending 160px. First product is one short scroll away.
- **Screens:** f-homepage-carriage-with-item, f-homepage-carriage-over20, f-homepage-gb-top, f-homepage-load-settled

## Surprises (not in the checklist)

- **A cookie-consent banner exists** — SPEC §10 lists "No cookie banner" as an open item, but Shopify's privacy banner (`shopify-pc__banner__dialog`) now renders: styled on-theme (dark, mono, squared buttons — it genuinely looks like part of the site), 359px tall, covering the bottom ~43% of the phone screen on every page until Accept/Decline is tapped. Decline dismisses it cleanly.
- **Non-UK visitors see mixed currencies:** the audit egress geo-converted all prices to USD ($70.00 on the crewneck) while the status ticker and carriage copy still speak in hardcoded £ ("FREE UK SHIPPING OVER £20"). UK shoppers (`?country=GB` / real GB IPs) see consistent £. Overseas shoppers get $ prices under a £ shipping promise.
- **Carriage bar is cart-gated** — nothing renders with an empty bag; the SPEC describes it as present on full page load with no such caveat. Recorded above; a shopper never notices.
- **On-model view has zero real data** — all 14 products fall back to one identical placeholder photo (detailed above; the loudest single finding in the catalogue).
