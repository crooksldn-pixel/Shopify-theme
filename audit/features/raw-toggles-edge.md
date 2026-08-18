# RAW — Theme/display toggles and edge conditions

Staging theme verified via harness on every session (.crk-root + crooks.css). Tested 2026-08-18 ~21:00–23:00 London, default mobile 390x844 DPR3; desktop 1440x900 and 720x450 for zoom; slow-4G throttle for the flash/first-load pass. Audit egress is non-UK so prices rendered in USD ($70 for the £50 crewneck) — already logged by other areas; nothing below depends on currency. A Shopify cookie-consent banner is live on staging (SPEC's open-items list still says "no cookie banner" — it has since been added); it is dark-styled, readable over both themes, keyboard-dismissable, and stays dismissed once genuinely clicked. It does eat roughly half of a 390px-tall landscape or zoomed viewport until answered.

### Light/dark toggle: find it, switch on every template, persistence, flash
- **Should:** A findable control that switches the whole site, keeps the choice as you browse, leaves nothing unreadable in light mode, and never paints the wrong theme first on a slow load.
- **Did:** Found immediately — a header text button labelled with what it will do ("LIGHT MODE" in dark, "DARK MODE" in light). Switched on all nine templates: home, collection, product, search, cart, faq, terms, tracking and /policies/refund-policy — present and working on every one, including the CSS-only policy page (its light ground is a slightly different off-white, rgb(244,241,234) vs rgb(250,250,251), unnoticeable in practice). Choice persisted onto every one of the nine pages on arrival. Programmatic contrast scan of visible text on all nine light pages found exactly ONE failure: the search page's SEARCH submit button renders beige-on-near-white (text rgb(221,215,201) on rgb(250,250,251), ratio 1.38) — its colours are identical in dark mode where they read fine; in light mode the button is a ghost you can barely see (screenshot). The field itself and Enter still submit, so search isn't blocked, but the only visible "go" affordance effectively vanishes. Everything else — buy spine, register cards, accordions, cart line, FAQ, terms clauses, policy text — legible in light. Throttled slow-4G loads: the theme attribute lands ~750ms, first paint ~1,100ms — no flash of dark-before-light on navigation or reload, twice verified. New tab in the same browser returns to dark: the choice is sessionStorage (per tab, per visit) by design.
- **Verdict:** partly
- **Shopper impact:** The toggle itself is flawless. The one real cost: a light-mode shopper on the search page loses the SEARCH button — they either know to press Enter or they stall. One-line CSS fix territory.
- **Screens:** f-toggles-edge-light-home, f-toggles-edge-light-product, f-toggles-edge-light-policy, f-toggles-edge-light-cart, f-toggles-edge-light-faq, f-toggles-edge-light-searchbar

### Outline toggle in LIGHT mode
- **Should:** Either a legible outline treatment on a light ground, or the control absent/inert when the treatment doesn't apply.
- **Did:** The Outline button exists only on the homepage register (Flat / On model / Outline row) — not on collection or search registers. CSS deliberately suppresses the outline in light mode (`:root[data-crk-theme="light"] .crk-product-image { filter: none }`, schema info says "Dark mode only"). But the BUTTON stays visible and active in light mode: pressing it flips aria-pressed and writes `crk-outline: off` to sessionStorage while changing nothing on screen (image filter "none" before and after — verified computed styles). Worse, that invisible press carries over: switch back to dark and the outlines are now off with no obvious reason why.
- **Verdict:** partly
- **Shopper impact:** A light-mode shopper taps "Outline", sees nothing happen, taps again, concludes the site is broken — and may have silently changed how dark mode looks. Small audience, but a dead control is a trust papercut. (SPEC O3 already has the whole toggle pending an aesthetic call — this is one more datum for that call: hide or disable it in light mode if it stays.)
- **Screens:** f-toggles-edge-outline-light-home, f-toggles-edge-outline-dark-after

### Toggle theme mid-scroll on a long page
- **Should:** Scroll position survives the switch.
- **Did:** Verified on terms (scrolled to 1500, stable across two 1.2s checks, toggled light, toggled back — scrollY 1500 → 1500 → 1500) and on the PDP (anchor element at viewport top moved 0px, scrollY delta 0). An earlier apparent 96px jump was harness noise from lazy images, retested clean. One note: the header (and its toggle) does not stay pinned once you scroll — mid-page you must scroll back to the top to reach the toggle at all, which is ordinary behaviour but means "toggle mid-scroll" is really "scroll up, toggle, scroll back", and the scroll-back lands exactly where you were.
- **Verdict:** works
- **Screens:** f-toggles-edge-midscroll-light-terms

### Reload every main template; back/forward through a 5-page trail
- **Should:** Nothing breaks on reload; history restores pages, queries and reasonable state.
- **Did:** Reloaded home, collection, product, search, cart, faq, terms, tracking with an item in the bag: every one came back whole — .crk-root present, sections rendered, no Liquid errors, no broken images, bag count [1] intact everywhere. Trail collection → PDP (size L picked) → search?q=jorts → faq → cart, then back x4 and forward x2: every path and query restored, collection scroll position restored (900px), search query kept. Genuinely good: picking a size rewrites the URL to ?variant=…, so back/forward (and a shared link) restores the exact size — size L was still selected on both back and forward visits. Two small resets: the register's category chip (T-SHIRT) reverts to ALL when you come back from a product (client-side filter, not persisted — re-filter needed), and open accordions re-close (they default closed anyway, so barely noticeable).
- **Verdict:** works
- **Shopper impact:** The one cost is the filter reset — browse tees, open one, come back, and you're facing all 14 products again. Mild friction on a 14-product catalogue; would grow with the range.
- **Screens:** f-toggles-edge-back-collection

### Land DIRECTLY on a product URL in a fresh session (Instagram-click path)
- **Did:** Fresh context straight to /products/charcoal-cellblock-crewneck. Everything present and working: title, price, 4 gallery images, all five size buttons, IN STOCK, dispatch line, set toggle, accordions, header/nav for onward browsing. Picked size M (URL gained ?variant=…), added to bag — count [1] — and the cart showed the line. Nothing assumed a prior homepage visit.
- **Should:** The PDP must fully work as the first page a shopper ever sees.
- **Verdict:** works
- **Screens:** f-toggles-edge-direct-pdp-landing, f-toggles-edge-direct-pdp-cart

### Rotate to landscape (844x390) on home + PDP + cart; rotate back
- **Should:** Layout survives; nothing unreachable.
- **Did:** Home and PDP: clean — no horizontal scroll, header intact, size pick + ADD TO BAG worked in landscape (bag went to [1]). Cart: the line item breaks — the product title ("BLUE WASH OG JE/ANS", wrapping mid-word) renders ON TOP of the product thumbnail, with the unit price floating beside it; bounding boxes confirmed overlapping (image x40–160, title starts x109) at 844px width; portrait at the same moment is clean. Everything is still readable enough to proceed — quantity, total, Check out all present and working — but the overlap looks glitchy. Rotating back to portrait: layout recovers fully, nothing stuck.
- **Verdict:** partly
- **Shopper impact:** A landscape-phone (or narrow-tablet) shopper hits the mess exactly at the trust-sensitive moment — reviewing the cart. Nothing is lost functionally; it just looks broken where "looks broken" costs the most.
- **Screens:** f-toggles-edge-landscape-home, f-toggles-edge-landscape-pdp, f-toggles-edge-landscape-cart-top, f-toggles-edge-portrait-back-cart

### 200% zoom (desktop 720x450): full purchase attempt
- **Should:** No clipping/overlap; the whole buy path works at 200%.
- **Did:** Full run: home → CATALOGUE link → register → crewneck card → size M (?variant set) → ADD TO BAG (full-width, fully on-screen) → bag [1] → BAG link → cart (line item clean at this width, no overlap) → Check out → landed on the real checkout page (stopped there, nothing entered). Zero horizontal scroll on any page; the only "off-screen control" the scan found was the deliberate skip-link. The cookie banner covers ~45% of the 450px-tall viewport until answered but never blocked the path.
- **Verdict:** works
- **Screens:** f-toggles-edge-zoom-home, f-toggles-edge-zoom-pdp-buy, f-toggles-edge-zoom-cart, f-toggles-edge-zoom-checkout

### JavaScript OFF: homepage catalogue, PDP, actually add to cart
- **Should:** Catalogue renders with prices; PDP sizes visible; noscript ?variant= links + native /cart/add still sell (SPEC §9.11).
- **Did:** Homepage: all 14 product cards render with images, prices and stock lines — the register is fully shoppable. PDP: the JS size buttons render (inert) and directly below them a labelled "CHOOSE A SIZE:" row of ?variant= links — followed the M link, hidden form id updated to the M variant, submitted the form, native POST landed on /cart, the line was there and Check out was present. The site sells with JS off, end to end. Two costs: (1) the four accordions — Specification, Item description, Measurements, Chain of custody — are aria-expanded BUTTONS on staging (not the `<details name>` elements SPEC §5/§9.11 describes), so with JS off their bodies never open: a no-JS shopper cannot read fabric, measurements or the shipping/returns terms at all. That's a regression against the SPEC's stated no-JS contract ("accordion bodies are visible"). (2) The dispatch line shows only the static "Order before 18:00 and it ships today (Mon–Sat)" — read at 21:00 that promise is already stale (with JS it correctly says "leaves tomorrow"). Cosmetic: an empty grey box below ADD TO BAG (the accelerated-payment placeholder), and the status ticker renders two overlapping messages at the very top edge.
- **Verdict:** partly
- **Shopper impact:** Selling survives, which is the headline. But the no-JS (and script-blocked, and script-failed-on-flaky-3G) shopper loses every word of product information beyond the title/price — measurements and returns terms included, which for a fit-sensitive garment is the difference between adding and bouncing.
- **Screens:** f-toggles-edge-nojs-home, f-toggles-edge-nojs-pdp, f-toggles-edge-nojs-cart

### Keyboard-only pass on desktop
- **Should:** Visible focus from the first Tab; menu drawer operable (trap + Escape per SPEC); product → size → add → cart possible without a mouse; note only what's impossible.
- **Did:** Nothing is impossible. First Tab hits "Skip to content"; the theme's 2px lavender focus ring (rgb(167,122,199)) was present on every theme control sampled (10/10 plus all buy-path stops). The cookie banner takes the first few tab stops on a fresh visit but Decline is reachable and Enter dismisses it (its own "Manage preferences" button shows no ring — Shopify's banner, not the theme). Drawer: MENU at tab 7, Enter opens (aria-modal), focus lands on CLOSE, 30 Tabs cycle SHOP → … → PLAY CASE:001 → ACCOUNT → round again without ever escaping, Escape closes and focus returns to MENU — textbook. Buy path: register card (visible ring on the whole card), Enter → PDP, "Size M" button at tab 12, Enter selects (aria-pressed + URL variant), "Add to bag" 4 tabs later, Enter → bag [1] with focus kept in place, BAG link → cart, "Check out" at tab 15 of a sensible order (set-offer line → line item → quantity → remove → discount → Check out). Only nit: the Check out button's focus ring computes to dark purple (rgb(84,37,120)) on a purple button — present but low-contrast (Horizon's, not crooks.css).
- **Verdict:** works
- **Screens:** f-toggles-edge-kbd-drawer, f-toggles-edge-kbd-added, f-toggles-edge-kbd-checkout-focus

---

## Cross-checks and notes for the merge

- **Staging vs SPEC divergence (feeds several areas):** the PDP accordions on staging are aria-expanded button/panel pairs, not `<details name>`. Consequences seen in this area: no-JS bodies unopenable (above). The crewneck PDP also has no Measurements accordion at all (the jeans PDP does) — data gap on that product, for the product-record area's ledger.
- **Cookie banner (new since SPEC):** exists, behaves correctly (persists dismissal, keyboard-operable), but takes the first tab stops and a big slice of short viewports. SPEC's "no cookie banner" open item is stale.
- **Theme choice is per-tab/per-visit** (sessionStorage) — a returning shopper's light preference is forgotten. Matches the prototype design; noted as behaviour, not a bug.
- **USD prices for non-UK egress** corroborated here (search cards $70.00, cart $83.00 USD under a "£20" ticker) — already logged by other areas.
- **Not rediscovered, confirmed only in passing:** O3 outline pending (its light-mode dead-control behaviour measured above); "More from this drop" on PDP and "You may also like" on cart exist on staging (neither in SPEC's route map — sprint additions, other areas' scope).
