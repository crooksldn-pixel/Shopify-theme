# Decision log — theme gauntlet run 2026-08-11

## Preflight
- OLD theme: https://crooksldn.com — Shopify theme id **202044309847** ("CROOKSLDN — Dev", role: main, schema Horizon 3.5.0)
- NEW theme: https://caijh1httspvte6b-100410786135.shopifypreview.com — theme id **202053779799** ("CROOKSLDN — Staging", role: unpublished, schema Horizon 3.5.0)
- Same base framework (Horizon 3.5.0) but materially different builds: OLD uses stock Horizon components (`header-component`, `cart-drawer-component`); NEW is a custom build with `crk-*` prefixed markup and its own header/drawer. Homepage payload differs 5× (OLD 957KB vs NEW 193KB HTML). **Not a colors-only restyle — panel is justified.**
- No storefront password (both URLs return 200 with content).
- Chromium-through-proxy required two fixes: (1) proxy CA imported into NSS db (`certutil -A -n ccr-agent-proxy -t "C,," -i /root/.ccr/agent-proxy-ca.crt -d sql:/root/.pki/nssdb`), (2) launch arg `--ssl-version-max=tls1.2` — the proxy's TLS terminator resets on Chromium 141's post-quantum ClientHello and the ML-KEM feature flags are expired no-ops in this build. TLS 1.2 to the local MITM proxy, verification still on. Logged so reruns work.
- Environment artifact for evidence review: third-party requests (analytics, pixels) may fail with proxy/egress errors in captures — `failedRequests` entries pointing at non-store hosts are environment noise, not theme bugs. Store-host failures are real findings.

## Catalog / fill-in-block resolution (store facts via /products.json + /collections.json)
- `KEY_PRODUCTS[0]` "Charcoal crewneck" → **charcoal-cellblock-crewneck** (CHARCOAL CELLBLOCK CREWNECK, £50, 5 sizes). Used by J1, J3.
- `KEY_PRODUCTS[1]` "jeans" → search term **"jeans"**, target **cb2-wash-jeans** (BLUE WASH OG JEANS, £60). Used by J2.
- `KEY_PRODUCTS[2]` "jorts" → exact-name search **"BLUE WASH JORTS"** → **cb1-wash-jorts** (£50). Used by J7.
- J3 comparison product: **charcoal-cellblock-shorts** (£45).
- J5 gift PDP target: browse under budget; gift budget £60–100 clears the entire catalog (max price £60), so the gift constraint is trivially satisfiable — noted for synthesis.
- `HERO_COLLECTION` "Charcoal" **does not exist as a collection**. Collections: accessories, all(ALL), denim, new(New), frontpage(PRODUCTS), sweats, tees, tracksuits. The charcoal cellblock products live in `sweats` (3 products) and `new` (9–11). Decision: J4 uses **/collections/all** (the store's main catalogue link in NEW's nav, 14 products — enough for filter/sort to be meaningful); the charcoal line is verified present in it.
- Out-of-stock edge case: **v2-baggies** (V2 BAGGIES, 3 of 5 variants unavailable).
- Currency: GBP. Store support pages that exist: /policies/shipping-policy, /policies/refund-policy, /policies/privacy-policy, /pages/contact, /pages/tracking. **No size-guide page, no FAQ page** (404) — size guidance, if any, must live on PDPs. `/account/login` returns 406 to curl; `/account` 302 (new customer accounts) — browser behavior checked in J7.

- **Currency as captured:** the storefront geo-detects our egress IP and renders **USD** (crewneck $69, jeans $83, shorts $63), not the GBP admin prices. All capture evidence and persona price perceptions are in USD; the £60–100 gift budget is treated as ≈$76–127 for task realism. This is itself evidence for the international-shopper angle. Logged, not asked (per run rules).

## Capture conventions
- Screenshots are full-page **JPEG q60** with extension `.jpg` (not `.png` as the spec's examples show) to keep ~350 full-page captures pushable in git. Evidence pointers use the real paths.
- Mobile = 390×844 touch; Desktop = 1440×900. Think-time 300–800ms between actions; ≤2 concurrent pages (one per theme, different domains).
- Theme-ID assertion on every page load into each session's `meta.jsonl`. Checkout pages don't expose `Shopify.theme` (checkout is theme-independent) — logged as `themeId: null, note: checkout` and not treated as poisoned.
- Preview-bar (`preview-bar-modules.js` iframe on the shopifypreview domain) hidden/removed before every screenshot.

## Platform constraint discovered during captures
- **Checkout is blocked on Shopify preview share-links**: clicking checkout on the NEW theme navigates to Shopify's "Checkout isn't available in preview" page; direct `/checkout` returns 403. Evidence: `captures/new/j1/mobile/step-07-checkout-click-failed.jpg`. Treatment: for NEW, "checkout reached" = the theme's cart→checkout action fires and navigates (it does); the block page is Shopify's, not the theme's. Checkout-page comparisons (discount field location etc.) are only measurable on OLD — and checkout is theme-independent anyway. Panel instructed accordingly.

## Firewall
- BRAND_INTENT and REDESIGN_THESIS are held in the orchestrator conversation only. They are not written into `data/` and do not appear in any persona card, capture script, or panel-batch prompt. They first touch disk in `report/report.md` at synthesis.
- Firewall verification: scanned all 200 verdicts for the intended adjectives used as quoted-back brand language — 0 leaks (incidental use of common words like "cool" reflects independent shopper vocabulary, not brief contamination; the intended-adjective *coverage* metric in the report is computed at synthesis, not fed to personas). No batch required a rerun for leakage.

## Panel execution note
- First attempt ran the 10 batches via the Workflow tool; all 10 agents failed at the structured-output return step due to a harness-level permission-callback bug that stripped tool-call parameters (the shopper analysis itself was unaffected). Re-ran the identical batch instructions as 10 standard subagents (Agent tool) — all 10 returned 20 verdicts + 10 compares each = 200 verdicts / 100 comparisons, 0 malformed, all 200 persona-theme cells present. Logged so the rerun path is reproducible.
- Skeptic pass: 1 adversarial subagent attacked the top-10 findings → 5 CONFIRMED (F2,F4,F5,F9,F10), 5 WEAKENED (F1,F3,F6,F7,F8), 0 KILLED. Verdicts in `data/skeptic-verdicts.json`; caveats folded into `report/report.md`. It caught a mis-cited popup screenshot (F7) and the live-vs-preview checkout confound behind the buy-now gap (F1) — both corrected in the report.
