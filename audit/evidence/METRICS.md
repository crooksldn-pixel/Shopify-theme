# CROOKSLDN — PHASE 1: INSTRUMENTED EVIDENCE

**Target:** `https://ezvw3xrffzdt93es-100410786135.shopifypreview.com`
**Theme:** `CROOKSLDN — Staging`, id `202053779799`, role `unpublished` — `.crk-root` present, `crooks.css` loaded. Verified on every page load.
**Source of truth:** the staging theme is byte-identical in structure to `origin/claude/crooksldn-theme-init-bnen7a` @ `1b6bc4c` (184/184 `.crk-*` selectors match, zero diff). File paths in this audit refer to that branch.
**Date:** 2026-08-07

---

## 0. How these numbers were produced, and where to distrust them

| | |
|---|---|
| Browser | Playwright Chromium 151, `--proxy-server` → local TLS bridge → session egress proxy |
| Primary viewport | 390 × 844, DPR 3, iOS Safari UA |
| Secondary | 360 × 800 (Android), 320 × 568, desktop 1440 × 900 |
| Network | CDP `emulateNetworkConditions` — 1.6 Mbps down, 750 Kbps up, 150 ms RTT |
| CPU | CDP `setCPUThrottlingRate` 4× |
| Market | **GBP pinned** via `cart_currency` cookie set before first navigation |

**Three caveats, stated up front:**

1. **Absolute timings are pessimistic.** Every request crosses a local TLS bridge and the session's egress proxy. Unthrottled TTFB through that path is **266–360 ms** before throttling is applied. Real-world TTFB will be lower. Treat LCP/TTFB as *comparative* between pages, and treat the byte counts — which are exact, taken from CDP `encodedDataLength` — as absolute.

2. **Two things in the evidence are preview-only artefacts, not site defects.** They are excluded from all findings:
   - `iframe#PBarNextFrame` — the Shopify preview bar. It is the *only* thing that catches keyboard focus at the end of a tab traversal. **There is no keyboard trap in the theme.** My first traversal reported one on every page; that was my detector mistaking six consecutive `<a>` footer links for a stuck focus. Corrected and re-run.
   - Omnisend `wt.omnisendlink.com` CORS failures on every page — the preview hostname isn't allow-listed. Will not occur on the published domain.

3. **Chromium could not reach the site directly.** The egress proxy resets Chromium's TLS handshake (node's is fine). All traffic is bridged through a local HTTP/1.1 MITM (`audit/bridge.mjs`). This forces HTTP/1.1 rather than the h2 a real visitor gets, which makes the 172–196 request counts cost *more* than they would in production. Another reason the timings are an upper bound.

---

## 1. THE THREE WORST NUMBERS

### 1.1 — LCP **13.9 s** on the 3 CLIVES TEE product page

| Page | LCP | LCP element |
|---|---|---|
| PDP — 3 CLIVES TEE | **13,876 ms** | `IMG.crk-main-img` → `9dbaee36…_webp.webp` |
| PDP — BLUE WASH OG JEANS | 3,388 ms | `IMG.crk-main-img` → `crooksldn-blue-wash-baggy-jeans.png` |
| Homepage | 4,432 ms | `P` (status line) |
| Cart | 7,948 ms | `P` |
| Homepage [desktop] | 1,048 ms | `H1.crk-h1` |

Two product pages, same template, same viewport, same throttle — **4× difference in LCP**. The only variable is the master image's filename. See §3.

### 1.2 — CLS **0.233** on both product pages

Google's "good" threshold is 0.1; "poor" starts at 0.25. Both PDPs sit at **0.2327**, just under poor.

It is a single shift, and I isolated the cause by request-blocking:

| Condition | CLS |
|---|---|
| Baseline | **0.2327** |
| `crx-mono.woff2` blocked | 0.2317 *(no change — not the cause)* |
| `vt323.woff2` blocked | **0.0013** *(shift disappears)* |
| all theme woff2 blocked | 0 |

**VT323 causes 99.4% of the layout shift.** At 1,840 ms the meta row `← CATALOGUE · PRODUCT 04 / 14 · DENIM` reflows from two lines to one as VT323 swaps in, pulling `DIV.crk-grid` — the entire buy panel, price, size buttons and all — **28 px upward**:

```
0.2315 @ 1840ms
   DIV.crk-grid  "PHOTO 1 OF 1 BLUE WASH OG JEANS £60.00 S"
                 [16,184,358,660] -> [16,156,358,688]   (-28px)
   SPAN.crk-data.crk-dim "DENIM"
                 [16,131,40,20]   -> [275,102,40,20]    (-29px)
```

**Why it happens.** `vt323.woff2` is downloaded **twice**:

```
+352ms  /cdn/shop/t/7/assets/vt323.woff2?v=74139476643975517521786013959   initiator=link  → done 1142ms  [NEVER USED]
+868ms  /cdn/shop/t/7/assets/vt323.woff2                                    initiator=css   → done 1836ms  [the one that renders]
```

Chrome confirms it: *"The resource …vt323.woff2?v=… was preloaded using link preload but not used within a few seconds."*

`layout/theme.liquid:31-36` preloads `{{ 'vt323.woff2' | asset_url }}`, which emits a `?v=` cache-buster. `assets/crooks.css:13` declares `src: url('vt323.woff2')`, which resolves **without** the query string. Different URLs → the preload is a wasted 18 KB, and the font the page actually uses doesn't start downloading until the CSS is parsed at 868 ms, landing at 1,836 ms — well after FCP at 968 ms. The shift lands 4 ms later.

The buy panel moves 28 px under the user's thumb, 1.8 seconds in.

### 1.3 — Homepage ships **3.1 MB**, of which **~933 KB is avoidable**, and no product image is painted in the first viewport

| Page | Transfer | Requests | Images | Scripts | Fonts | CSS |
|---|---|---|---|---|---|---|
| Homepage | **3,103 KB** | 176 | 1,434 KB | 1,168 KB | 236 KB | 194 KB |
| PDP — 3 CLIVES TEE | 2,591 KB | 172 | 901 KB | 1,169 KB | 236 KB | 194 KB |
| PDP — BLUE WASH OG JEANS | 1,936 KB | 172 | 187 KB | 1,171 KB | 236 KB | 194 KB |
| Cart | 4,024 KB | 196 | 946 KB | 1,463 KB | 159 KB | 188 KB |

`firstProductImage` on the homepage: **never** — no product image is painted inside the first viewport at any point, because the entire first screen is the canvas board (§5).

---

## 2. PERFORMANCE, FULL TABLE (mobile 390×844, throttled)

| Metric | Home | PDP tee | PDP denim | Cart |
|---|---|---|---|---|
| TTFB | 266 ms | 363 ms | 374 ms | 397 ms |
| FCP | ~1,020 ms | 1,224 ms | 1,116 ms | 1,204 ms |
| **LCP** | 4,432 ms | **13,876 ms** | 3,388 ms | 7,948 ms |
| **CLS** | 0.0017 | **0.2333** | **0.2327** | 0.0218 |
| DOMContentLoaded | 4,294 ms | 5,588 ms | 4,605 ms | 6,529 ms |
| Load event | 17,086 ms | 14,223 ms | 10,961 ms | 17,482 ms |
| Long tasks > 50 ms | 16 | 15 | 16 | **25** |
| Total blocking (long-task ms) | 1,887 ms | 2,018 ms | 2,055 ms | **3,440 ms** |
| First product image visible | never | 3,009 ms | 3,347 ms | 2,366 ms |

**INP** could not be measured meaningfully — the first-visit popup intercepts the first interaction on the homepage, and `event` timing entries stayed under the 16 ms reporting threshold on the PDPs once it was dismissed. Interaction latency is not a problem on this site; the 4× CPU throttle produced no interaction over 16 ms on any theme control.

**Desktop (1440×900, same throttle):** Homepage LCP 1,048 ms / CLS 0.0007. PDP denim LCP 3,296 ms / CLS 0.0062. **The CLS problem is mobile-only** — on a wide viewport the meta row never wrapped, so the font swap has nothing to reflow.

### JavaScript — 1.17 MB on every single page

| Asset | Bytes | Origin |
|---|---|---|
| `index.js` | 258 KB | Shopify Horizon |
| `vendor-DfR6YY9mO42n.js` | 188 KB | Shopify Horizon |
| `index-BZt26T72.js` | **166 KB** | `crack-cuff-codes.base44.app` |
| `app-ClXuvt2052vC.js` | 76 KB | Shopify Horizon |
| `vendor.css` | 99 KB | Shopify Horizon |

The 166 KB Base44 companion-app bundle loads on **every page including the cart and PDP**, not just where the game runs. On the denim PDP, third-party + platform JS (1,171 KB) outweighs the product imagery (187 KB) by 6×.

### Cart adds 600 KB of wallet iframes

`pay.google.com/pay` 418 KB + `www.paypal.com/buttons` 178 KB. This is the price of offering wallets and is largely non-negotiable, but it is why the cart has the worst blocking time on the site (3,440 ms).

### Fonts — 236 KB for a two-typeface design system

| Face | Bytes | Used by |
|---|---|---|
| `vt323.woff2` | 18 KB **× 2 (double-fetched)** | design system — display |
| `crx-mono.woff2` | 17 KB | design system — mono |
| `archivo_n4` | 45 KB | Horizon default |
| `archivonarrow_n4` + `n7` | 26 KB | Horizon default |
| Inter, Space Mono | ~40 KB | third-party wallet / app iframes |

The design system needs **35 KB**. Archivo and Archivo Narrow are Horizon defaults that the CROOKSLDN surfaces never use — but the cart page does, because the cart was never restyled (§7).

---

## 3. IMAGES — the largest single finding

**Shopify's CDN transcodes PNG masters to WebP on request. It does not transcode masters whose *filename* ends in `.webp` — those are served as raw PNG at full weight, regardless of the `Accept` header.**

Same CDN, same `?width=1400`, two masters:

| Master filename | `Accept: image/webp` | `Accept: */*` |
|---|---|---|
| `crooksldn-charcoal-cellblock-shorts.png` | **78 KB WebP** | 653 KB PNG |
| `cellcrew.webp` | **969 KB PNG** | 969 KB PNG |

Verified by magic bytes on the response body, not by `Content-Type` alone.

### What the `<img>` tags actually receive

Homepage, all fifteen product cards, `?width=600`:

| Served as WebP (correct) | KB | | Served as PNG (mislabelled masters) | KB |
|---|---|---|---|---|
| `crooksldn-charcoal-cellblock-shorts…png` | 32 | | `cellcrew.webp` | **255** |
| `crooksldn-blue-wash-denim-jorts.png` | 46 | | `9dbaee36…_webp.webp` | **186** |
| `crooksldn-blue-wash-baggy-jeans.png` | 49 | | `crooksldn-white-red-motiontec-socks.webp` | **181** |
| `crooksldn-grey-wash-denim-jorts.png` | 29 | | `7087223b…_webp.webp` | **172** |
| `crooksldn-grey-wash-baggy-jeans.png` | 36 | | `v2baggies.webp` | **149** |
| `blacksock.png` | 34 | | `IMG-3994.webp` | **122** |
| `crooksldn-large-black-duffle-bag.png` | 18 | | `5dfb353c…_webp.webp` | **113** |
| **7 files** | **244 KB** | | **7 files** | **1,178 KB** |

Identical rendered box (152 × 152 CSS px). **Average 35 KB vs 168 KB — 4.8× heavier for no visible benefit.**

**Estimated saving from re-uploading 8 masters under a `.png` filename:**
- Homepage: 1,178 KB → ~245 KB = **≈ 933 KB saved (30% of total page weight)**
- PDP 3 CLIVES TEE hero: 635 KB → ~180 KB = **≈ 455 KB saved**, and its 13.9 s LCP with it
- PDP related-product strip: 223 KB → ~50 KB = ≈ 173 KB saved

**The eight files to re-upload** (product → master):
`cellcrew.webp` (CHARCOAL CELLBLOCK CREWNECK) · `9dbaee36…_webp.webp` + `df150894…_webp.webp` (3 CLIVES TEE) · `7087223b…_webp.webp` (BROADCAST TEE) · `5dfb353c…_webp.webp` (MONEY CLIVE TEE) · `v2baggies.webp` (V2 BAGGIES) · `IMG-3994.webp` (CRXST★RZ T-SHIRT) · `crooksldn-white-red-motiontec-socks.webp` (WHITE/RED MOTIONTEC SOCKS)

This is a Shopify admin task, not a code change. No file in the theme needs editing.

### Resolution

`srcset` and `sizes` are correctly implemented throughout (`200w,300w,400w,600w,800w` on cards; `400w…1400w` on PDP heroes). Two minor overscales:

| Context | Rendered | Device px needed @3× | Delivered | Ratio |
|---|---|---|---|---|
| Homepage card | 152 px | 456 px | 600 px | 1.32× |
| PDP hero | 332 px | 996 px | 1400 px | 1.41× |
| Header logo | 48 px | 144 px | 241 px | 1.67× |
| PDP thumbnail | 54 px | 162 px | 128 px | **0.79× (under-resolved)** |

Nothing here is worth fixing before the format problem — the 1.41× hero overscale costs ~30% while the format costs 480%.

---

## 4. LAYOUT AND REACH

### Scroll depth, in viewport heights (390 × 844)

| Page | Page length | First product card | Add-to-cart | Footer |
|---|---|---|---|---|
| Homepage | 6.03 vh | **1.22 vh** | — | 5.15 vh |
| PDP tee | 3.51 vh | 2.27 vh | 1.24 vh | 2.64 vh |
| PDP denim | 3.32 vh | 2.08 vh | 1.04 vh | 2.44 vh |
| Cart | 2.46 vh | 0.18 vh | 0 vh | 1.59 vh |
| Collection | 3.71 vh | 0.24 vh | — | 2.84 vh |

**The homepage requires a full viewport of scrolling before the first product appears.** The first screen is entirely the canvas board; brand name, OWN THE STREETS™ and the CATALOGUE button land at ~500–570 px, just inside the fold.

**The PDPs are better than the raw number suggests.** The in-page ADD TO BAG sits at 1.04–1.24 vh, but `.crk-stickybar` is present from first paint and carries product name, price, selected size and a full-width ADD TO BAG in the bottom 9% of the viewport. Product image, title, **£60.00**, size selector and IN STOCK are all in the first viewport without scrolling. Persona 1's "price must be visible without scrolling" test **passes** — provided the cookie banner isn't there (§4.3).

### Thumb zone

| Page | Primary action | Position |
|---|---|---|
| PDP (both) | `.crk-stickybar` ADD TO BAG | **bottom 9% — ideal** |
| Homepage | `a.crk-btn--fill` CATALOGUE | ~67% — reachable |
| Cart | `#checkout` | top of page, then scrolls |
| Collection | first card | 0.24 vh |

### Tap targets under 44 × 44

48 interactive elements audited on the homepage, 40–44 on other pages. **The theme's own `crk-*` controls pass almost universally** — size buttons are 58 × 52, ADD TO BAG is full-width × 56.

Genuine failures, theme-owned:

| Size | Element | Page |
|---|---|---|
| 92 × **16** | `a.crk-label` "← CATALOGUE" | both PDPs |
| **22** × 44 | `a` "NEW" | footer, all pages |
| **29** × 44 | `a` "TEES" | footer, all pages |
| **36** × 44 | `a` "DENIM" | footer, all pages |
| 1 × 1 | `label.crk-sr` "Email address" | homepage — visually-hidden label, correct, not a defect |

Failures in Horizon-inherited components:

| Size | Element | Page |
|---|---|---|
| 36 × **28** | quantity `input` | cart |
| 178 × **26** | `a.cart-items__title` | cart |
| 40 × **22** | `a.size-style.link` "View all" | cart |
| 51 × **22** | `button.facets-toggle__button` "Filter" | collection |
| 358 × **42** | `summary.cart-discount__summary` | cart |

Excluded as Shopify-owned: the four cookie-banner controls (33–35 px tall) present on every page.

### Horizontal overflow

| Width | Result |
|---|---|
| 320 px | **Homepage overflows: `scrollWidth` 334 vs 320.** Offenders: `p.crk-status__msg` (+39 px), `li.crk-log__cell` (+14 px) |
| 320 px | Collection: `slideshow-slide.product-media-container` +142 px — inside an intentional carousel, not a break |
| 360 / 390 px | No page-level horizontal scroll |
| 360 / 390 px | `div.crk-filters` scrolls 597 px in a 358 px rail — intentional, and it **does** scroll focused chips into view (verified: `scrollLeft` 0 → 239). But 2 of 5 chips (SWEATS, ACCESSORIES) are off-screen with no visual affordance that more exist |

### 200% browser zoom (WCAG 1.4.10 Reflow)

At 195 CSS px of layout width, the PDP produces **horizontal scrolling: `scrollWidth` 308 vs `clientWidth` 195**. This is a WCAG 2.1 AA failure.

---

## 5. THE CANVAS BOARD — measured, and it is exemplary

| Condition | Frames | FPS |
|---|---|---|
| Board in viewport, idle | 180 / 3,000 ms | **60.0** |
| Full-page scroll, board running, 4× CPU throttle | 136 / 2,367 ms | **57.5** |
| Board scrolled off-screen | 0 / 3,000 ms | **0** |
| Tab hidden (`Emulation.setPageVisibilityOverride`) | 0 / 2,500 ms | **0** |
| `prefers-reduced-motion: reduce` | 0 / 3,000 ms | **0** |

`assets/crooks-board.js:166,190,199,211-218` guards on `matchMedia('(prefers-reduced-motion: reduce)')`, `document.hidden` + `visibilitychange`, and an `IntersectionObserver`, and calls `cancelAnimationFrame` on each. **All three guards work.** The board costs nothing when it isn't visible and holds 57.5 fps during scroll under a 4× CPU penalty.

This is the best-engineered thing on the site. It is not a performance problem and must not be treated as one.

---

## 6. ACCESSIBILITY

### Contrast — near-clean

Every rendered text/background pair was computed with alpha compositing against the true effective background.

| Page | Pairs | Failing |
|---|---|---|
| Homepage | 26 | 3 |
| PDP tee | 31 | 1 |
| PDP denim | 31 | 1 |
| Cart | 19 | 1 |
| Collection | 12 | 1 |

**One token accounts for nearly all of it:**

| Ratio | Need | Size | Element | Sample |
|---|---|---|---|---|
| **2.57:1** | 4.5 | 9 px | `p.crk-footer__base.crk-micro` | "EVIDENCE TERMINAL V0.2 // CROOKSLDN // OWN THE STREETS™" |
| **2.53:1** | 4.5 | 9 px | `p.crk-micro` | "CASE 001 — ATTRACT MODE" |

`rgb(87, 80, 99)` on `rgb(11, 10, 14)`. The `--crk-*` dim token used for 9 px micro-copy is the only palette value that fails. Everything else — body text, prices, size buttons, the purple accent, the warning red — passes. The palette is well-built; one variable is too dim.

The third homepage "failure" (`em` "London", 1:1, `rgba(0,0,0,0)`) is transparent text, almost certainly a deliberate effect. Flagged for eyeballing, not counted.

### axe-core (wcag2a/aa, wcag21a/aa, best-practice)

| Page | Types | Nodes | Violations |
|---|---|---|---|
| Homepage | 2 | 3 | `frame-title` (serious) ×1, `region` (moderate) ×2 |
| PDP tee | 2 | 3 | same |
| PDP denim | 2 | 3 | same |
| Cart | 5 | 6 | + `aria-required-children` (**critical**), `heading-order`, `aria-allowed-role` |
| Collection | 3 | 4 | + `page-has-heading-one` |

`frame-title` is the Shopify preview bar iframe — preview-only. `region` (content outside landmarks) and the cart's `aria-required-children` are real. **The cart is the only page with a critical violation, and every incremental violation on the site lives on the cart or collection page** — the two Horizon-inherited surfaces.

### Keyboard

No traps. 44–50 stops per page, logical order, focus reaches every control.

**Focus rings:**

| Ring | Contrast vs its ground | Where |
|---|---|---|
| `2px rgb(167,122,199)` (the purple accent) | **5.88 : 1** | every `crk-*` control |
| `2px rgb(167,122,199)` on purple fill | 3.27 : 1 | filled buttons — passes 3:1 |
| `1px rgb(10,10,10)` | 17.55 : 1 | Horizon controls on the bone ground |

I initially read the cart's checkout button as having an invisible 1:1 ring. **That was wrong** — the outline sits at `outline-offset: 2px`, outside the button, on the bone `rgb(244,241,234)` page ground: 17.55:1. Visible. The focus indicator system on this site is genuinely good.

Two real defects:
- `button#shopify-pc__banner__btn-manage-prefs` — **no focus indicator at all**. Shopify-owned.
- Cart: `shopify-payment-terms`, `shop-pay-wallet-button`, `shopify-google-pay-button` and a wallet `iframe` — no focus indicator. Shopify-owned.

**The one real keyboard finding is the cookie banner: it occupies the first four tab stops on every page**, ahead of the skip link. A keyboard user tabs Privacy Policy → Manage preferences (no visible focus) → Accept → Decline before reaching any site content.

### prefers-reduced-motion

Canvas board stops completely (0 fps). One CSS animation still runs: `div.resource-card` `fadeIn 0.15s` ×1 — a single 150 ms non-looping fade, harmless.

### JavaScript disabled

| | Homepage | PDP |
|---|---|---|
| Visible text | 2,093 chars | 1,024 chars |
| Product links | 18 | 14 |
| `<img>` in HTML | 40 | 10 |
| Price rendered | ✅ | ✅ |
| `/cart/add` form present | — | ✅ |

**The shop works without JavaScript.** Products, prices, sizes, images and a functioning add-to-cart form are all server-rendered. The canvas board degrades to its `<canvas>` container with the caption text intact. This is a real and uncommon strength.

---

## 7. THE PATTERN UNDERNEATH THE NUMBERS

Sorting every defect by which surface it lives on:

| | CROOKSLDN-designed surfaces (`crk-*`) | Horizon-inherited surfaces (cart, collection filters, wallets) |
|---|---|---|
| Tap targets < 44 px | 1 real (`← CATALOGUE`) + 3 narrow footer links | 5 |
| axe violations beyond baseline | 0 | 4, including the only critical one |
| Contrast failures | 1 token, 9 px micro-copy | 0 |
| Focus rings | 2 px purple, 5.88:1, consistent | 1 px, visible but off-system |
| Typefaces | 2 (VT323, CRX Mono) | Archivo + Archivo Narrow, 71 KB |
| Design language | held | **abandoned — light ground, third typeface, wallet buttons in blue/yellow/black** |

The austere terminal design is *not* where the quality problems are. The measured defects cluster almost entirely in the parts of the theme that were never brought into the design system. The cart — the last screen before payment — is the clearest example: bone background, Archivo sans-serif, Shop Pay purple, PayPal blue and Google Pay black, sitting under a dark terminal header. (`audit/screens/cart.png`)

---

## 8. THE COOKIE BANNER

Measured on the PDP at 390 × 844:

```
banner:      top 506  bottom 844  height 338px  position fixed  z-index 2000000
sticky bar:  top 767  bottom 844  height  77px  position fixed  z-index      40
overlaps:    true
```

**The cookie consent banner is 338 px tall — 40% of the viewport — and completely covers the sticky ADD TO BAG bar.** Until a first-time visitor accepts or declines, the primary purchase control on the site is not visible. On the homepage the banner sits behind the first-visit game popup (`DIV.ctc-overlay`, z-index 2,147,483,647, covering 100% of the viewport), so a cold arrival meets **two full-width overlays before any product**.

This is Shopify's own consent banner, configured in admin, not theme code — but its cost is real and it is measurable.

---

## 9. CATALOGUE FACTS (GBP)

14 products, £6–£60. One product has sold-out variants.

| Product | Price | Images | Description | Sold out |
|---|---|---|---|---|
| BLACK/BLUE MOTIONTEC™️ SOCKS | £6 | 1 | 74 ch | |
| WHITE/RED MOTIONTEC™️ SOCKS | £6 | 1 | 74 ch | |
| LARGE DUFFLE BAG | £18 | 1 | **48 ch** | |
| 3 CLIVES TEE | £25 | 2 | 162 ch | |
| BROADCAST TEE | £25 | 2 | 163 ch | |
| CRXST★RZ T-SHIRT | £25 | 2 | **67 ch** | |
| MONEY CLIVE TEE | £25 | 2 | 165 ch | |
| CHARCOAL CELLBLOCK SHORTS | £45 | 3 | 179 ch | |
| BLUE WASH JORTS | £50 | 1 | 180 ch | |
| GREY WASH JORTS | £50 | 1 | 180 ch | |
| CHARCOAL CELLBLOCK CREWNECK | £50 | 1 | 180 ch | |
| BLUE WASH OG JEANS | £60 | **1** | 142 ch | |
| GREY WASH OG JEANS | £60 | **1** | 142 ch | |
| V2 BAGGIES | £60 | 2 | 117 ch | **M, L, XL** |

**The £60 jeans have one photograph each and a 142-character description.** Product 04 of 14 announces "PHOTO 1 OF 1". Descriptions across the catalogue run 48–180 characters.

Note for Phase 2: `cb1-wash-jeans` is **GREY** WASH; BLUE WASH OG JEANS is `cb2-wash-jeans`. The handles and the wash codes do not correspond in the order you'd guess.

---

## FILES

```
audit/evidence/METRICS.md         this document
audit/evidence/perf.json          per-page vitals, transfer, per-image detail
audit/evidence/images.json        ground-truth dimensions/bytes per rendered image
audit/evidence/image-formats.json what each <img> actually received (magic bytes)
audit/evidence/image-ab.json      Accept-header A/B on the CDN
audit/evidence/layout.json        scroll depth, tap targets, overflow, board fps
audit/evidence/a11y.json          contrast, axe, reduced motion, no-JS, zoom
audit/evidence/keyboard.json      corrected tab traversals with focus-ring contrast
audit/evidence/cls-taps.json      layout-shift sources with before/after rects
audit/evidence/catalogue.json     14 products, GBP, variants, descriptions
audit/evidence/verify.json        focus ring, rails, cookie banner, preview bar
audit/screens/                    screenshots
```
