# CROOKSLDN — full build specification

Written 2026-08-18 against branch `claude/crooksldn-theme-init-bnen7a`.
Everything below was read out of the code and the store, not from memory. Where a
number appears, the command that produced it is named so it can be re-run.

**Purpose of this file:** give an auditing chat a complete, checkable map of the
site — every section, every setting, every store-side dependency, every piece of
behaviour that is deliberate — so it can inspect features without having to
rediscover them, and so it can tell a deliberate decision apart from a defect.

Read `audit/KEEP.md` on branch `claude/crooksldn-site-audit-eijmkd` alongside this.
That file names what is load-bearing and must not be "improved" away.

---

## 0. Ground rules the build obeys

These are the owner's standing rules. An audit that recommends breaking one of
them is recommending a regression.

**Safety (non-negotiable, owner-enforced):**

- No `shopify theme push` without an explicit `--theme` id given in-session. No
  bare push, no `--live`, no `--allow-live`.
- No `shopify theme publish`. Publishing is the owner's command.
- No `shopify theme delete`, ever.
- All work happens on an unpublished staging theme. The live theme is read-only.
- Existing theme files are never deleted or rewritten unless explicitly asked.
  New work goes in new files with a `crooks-` prefix. Changes to `theme.liquid`
  or `templates/index.json` are shown as a diff and approved first.

**Design law:**

- *The fiction stops where it would cost a sale.* Flavour lives in chrome —
  never in sizes, stock, price, add-to-cart, shipping or returns. `ADD TO BAG`,
  `£60.00`, `SIZE M`, `IN STOCK` are always plain English.
- Radius `0`, borders `1px`, no shadows, no gradients. Enforced in CSS
  (`crooks.css:101` and `:428`), not left to discipline.

**Code conventions:**

- Every class is `crk-*`. Every custom property is `--crk-*`. Everything is
  scoped under `.crk-root`.
- **No Liquid inside `<script>` or `<style>` tags.** Configuration reaches JS
  through `data-*` attributes only. There is one inline script in
  `theme.liquid` (the pre-paint theme resolver) and it contains no Liquid.
- No build step, no npm, no framework, no Tailwind. Vanilla ES2019.
- Every customer-facing string is a schema setting. No hardcoded product handles
  anywhere.
- No fabricated content: no fake stock counters, no countdown timers, no
  invented reviews or scores.

**Two traps this codebase has been bitten by, recorded so they are not repeated:**

1. **Liquid filter precedence.** Filters chain left to right with no grouping.
   `{{ a | b: x | c }}` does not do what a parenthesised reading suggests.
   Format into a variable *first*. This has caused four separate bugs
   (`FILED [date]`, carriage money, `© [year]`, the set toggle's saving).
2. **Push order.** A section group or template JSON that carries a *new* setting
   must be pushed *after* the section schema that declares it. Push it first and
   Shopify silently strips the setting with no error.

---

## 1. Stack and identity

| | |
|---|---|
| Platform | Shopify Online Store 2.0 |
| Base theme | **Horizon 3.5.0** (Shopify) |
| Shop | CROOKSLDN — `5wn03t-nm.myshopify.com` |
| Live domain | `https://crooksldn.com` |
| Currency / timezone | GBP / Europe/London |
| Staging theme id | `202053779799` (unpublished) |
| Customer accounts | hosted, `friendsof.crooksldn.com` (new customer accounts) |

The redesign does **not** fork Horizon. It adds `crooks-*` sections and repoints
templates at them. Horizon's own sections are still present and still work; the
`*.horizon.json` templates below are kept as intact fallbacks.

---

## 2. Route map — what renders on each URL

Order is render order. `crooks-*` entries are ours; unprefixed entries are Horizon's.

| Template | Sections, in order |
|---|---|
| `index.json` (home) | `crooks-cart-progress` → `crooks-hero-intake` → `crooks-exhibit-log` → `crooks-packaging` → `crooks-informant-intake` → `media-with-content` (lookbook) → `_blocks` |
| `product.json` | `crooks-cart-progress` → `crooks-exhibit-record` |
| `collection.json` | `crooks-cart-progress` → `crooks-exhibit-log` |
| `search.json` | `crooks-cart-progress` → `crooks-search` → `crooks-exhibit-log` |
| `cart.json` | `crooks-cart-progress` → `crooks-set-cart` → `main-cart` → `product-list` |
| `page.terms.json` | `crooks-terms` |
| `page.faq.json` | `crooks-faq` |
| `page.tracking.json` | `crooks-tracking` |
| `page.json`, `page.contact.json` | Horizon `main-page` (+ contact form) |
| `404.json`, `blog.json`, `article.json`, `list-collections.json`, `password.json`, `gift_card.liquid` | Horizon, untouched |
| **Section group `header-group`** | `crooks-status-bar` → `crooks-header` → `header-announcements` → `header` → `_blocks` |
| **Section group `footer-group`** | `crooks-footer-log` → `footer` → `footer-utilities` |

**Alternate templates kept as fallbacks, currently unreferenced by any product or
collection:** `product.horizon.json`, `collection.horizon.json`,
`search.horizon.json`. `product.crooks.json` is a second Crooks PDP template
(same section, fewer persisted settings) available as a `template_suffix`.

**Sections that exist but are in no template** — dormant, not dead:
`crooks-board-test` (the canvas board's isolated harness),
`crooks-case-file` (CASE 001 promo block with the leaderboard deliberately
hidden), `crooks-manifest` (WITNESS STATEMENT). All three are installable from
the theme editor via their presets.

**There is no `policy` template in OS 2.0.** `/policies/*` renders Shopify's bare
`.shopify-policy__container` inside `theme.liquid` and cannot take sections. It
is skinned by CSS only (`crooks.css:852`).

---

## 3. Section catalogue

17 sections. Settings counts are schema-declared settings, not persisted values.

### 3.1 `crooks-header` — Crooks — Header
26 settings · no blocks · in `header-group` · `assets/crooks-drawer.js`, `crooks-theme.js`

The site's only header (Horizon's `header` section is present in the group but
disabled). Renders: logo (with `logo_invert_dark` flip), wordmark, `CATALOGUE`
link, `SEARCH`, `ACCOUNT`, `BAG [n]`, `MENU` button.

The drawer is a hand-built modal dialog — no library. It implements
`role="dialog"` + `aria-modal`, focus move-in, Tab/Shift-Tab trap, Escape to
close, focus return to trigger, body scroll lock, and `aria-hidden` on siblings.

**CASE 001 panel** sits at the bottom of the drawer: the animated canvas board
plus a `PLAY CASE:001 NOW` button. `crooks-board.js` is **not** in the page —
it is injected on first drawer open, read from `data-crk-board-src`. Verified:
0 requests before open, 1 after.

Header headroom fix (`crooks.css`): below 429px the bar wraps and pads to 10px;
`.crk-header__count` reserves `min-width: 5ch` with tabular numerals so the cart
count never reflows the row.

### 3.2 `crooks-status-bar` — Crooks — Status Bar
3 settings · blocks: `message` · in `header-group` · `crooks-terminal.js`

Rotating one-line ticker above the header. `[count]` is substituted from the
configured collection. Rotation stops under `prefers-reduced-motion`, on hover,
and when `rotate` is off; with JS absent the first message shows.

> **Known defect (D1).** `interval_ms` is labelled *Seconds per message*
> (range 3–20, default 8) but is passed raw into `data-crk-interval`, which
> `crooks-terminal.js` reads as **milliseconds** and rejects below 1000, falling
> back to 8000. The persisted value is `5`, so the setting currently does
> nothing and every install runs at 8s. One-line fix: multiply by 1000 in the
> section. Not yet applied.

### 3.3 `crooks-hero-intake` — Crooks — Hero Intake
18 settings · blocks: `boot_line` · homepage · `crooks-terminal.js`

Wordmark, tagline, boot lines (typed on load, plain text without JS), and up to
two buttons. `[count]` in a boot line reads live product count.

`show_board` is currently **false** — the attract board was moved to the menu
drawer at the owner's request; the homepage no longer carries it.

### 3.4 `crooks-exhibit-log` — Crooks — Catalogue
38 settings · no blocks · homepage, collection, search · `crooks-terminal.js`

The register. One card per product: `NO. 01 / SWEATS / CHARCOAL CELLBLOCK
CREWNECK / £50.00 / AVAILABLE`.

- **Status slot always states stock.** Order: sold out → low stock → available.
  The drop date (`DROPPED 03.08`) is rendered as a *separate, de-emphasised*
  element beside it, never instead of it. `low_stock` sums real inventory across
  purchasable variants against `low_stock_threshold` (3).
- **Filters** derive from product type, ordered by `category_order`, all client
  side. Without JS every card renders and the buttons simply do nothing.
- **View toggle** `Flat` / `On model`, backed by the `crooks.model_image`
  metafield with a section-level placeholder.
- **Outline toggle** (`Outline`) — a white-outline treatment for product images,
  persisted in `sessionStorage` under `crk-outline` and applied pre-paint.
- **Colourway swatches** on cards, from option names listed in
  `colour_option_names`.
- **Headings:** `<h1>` on a collection template, `<h2>` elsewhere (the hero owns
  the h1 on the homepage). Collection pages previously had no h1 at all.
- **Search behaviour:** on `/search` with an empty query the section **stands
  down entirely** — it renders nothing rather than an empty register. With a
  query it lists product results, and separately lists any page/article results
  Shopify returned under `PAGES & ANSWERS`.
- **Structured data:** `CollectionPage` + `ItemList` of the products actually
  rendered + `BreadcrumbList`. Suppressed on search results, which must not be
  indexed.

### 3.5 `crooks-exhibit-record` — Crooks — Product Record
82 settings · blocks: `@app`, `custody_step` · product template ·
`crooks-record.js`, `crooks-set.js`

The PDP, and the largest surface in the build.

**Buy spine (never in-fiction, per KEEP.md §2):** title, `PRODUCT 09 / 14`,
category, price, size row, `IN STOCK`, `ADD TO BAG`, `CHECKOUT NOW`. A sticky
bottom bar repeats product, price, selected size and both actions.

**Variant handling:** multi-option picker; a size that is sold out gets
`aria-disabled` and stays selectable and in the tab order (deliberate — do not
swap for the `disabled` property). Choosing it swaps the buy button for the
variant-level notify form (`RELEASED — NO LONGER IN CUSTODY` + email capture,
subject `Restock request`).

**Delivery / dispatch:** an in-stock line, a made-to-order line gated on a tag,
and a computed dispatch state — cutoff hour 18, dispatch days `1,2,3,4,5,6`
(Mon–Sat), shop timezone — producing *leaves today / leaves tomorrow / leaves
Monday*. Grounded in measured fulfilment data, not invented.

**Four accordions, all `<details name>` so they are mutually exclusive with no
JS, and all default closed** (owner request):
`Specification`, `Measurements`, `Item description`, `Chain of custody — shipping & returns`.

**Measurements** come from the `crooks.measurements` JSON metafield, with a
working cm/inch toggle (verified 38cm → 15in) and the method stated
(`GARMENT LAID FLAT`). `SIZE GUIDE` scrolls the Measurements heading to y=0 —
one tap, no modal, no PDF.

**Chain of custody** is four `custody_step` blocks: `01 Logged / 02 Dispatched /
03 In transit / 04 Delivered`. *(Stage 04 was `RELEASED` — changed to `Delivered`
by explicit owner override of KEEP.md §6.)*

**Complete-the-set toggle** sits between the dispatch line and `ADD TO BAG` —
see §5.

**No-JS fallback:** the server-selected variant is already in the form's hidden
id input; accordion bodies are visible; a `<noscript>` block renders `?variant=`
links for every size; `/cart/add` posts normally.

**Structured data:** `snippets/crooks-schema-product.liquid`.

### 3.6 `crooks-search` — Crooks — Query bar
10 settings · blocks: `link` · search template · `crooks-search.js`

The search field, replacing Horizon's `search-header`.

Typeahead has two sources: products from Shopify's own
`/search/suggest.json` (no app needed), and a curated **direct links** list
rendered into `[data-crk-linkdata]` as data attributes and matched in the
browser. The second source exists because **Shopify's search cannot reach
Terms, Questions or the policies** — policy pages are not indexed at all, and
the Terms/FAQ text lives in section settings rather than `page.content`. Nine
link blocks are configured, keyword-matched, with `Track your order` and
`Questions` shown before anything is typed.

The field's box was restored with `.crk-root input.crk-input` — specificity over
Horizon's input reset, plus `appearance: none`, `min-height: 56px`.

Form submits normally with the JS absent.

### 3.7 `crooks-cart-progress` — Crooks — Carriage status
10 settings · home, product, collection, search, cart · `crooks-cart-progress.js`

Two-tier free-carriage readout grounded in the real rate card: free Tracked 48
over £20, free Tracked 24 over £70. Gated to `country_code` GB. Money is
formatted through Shopify's `money_format`, never assembled in JS. Correct on
every full page load without the script; the script only keeps it correct on
AJAX cart updates (`cart:update`, plus a `/cart.js` re-read).

Note from the round-2 council: this bar is explicitly **not** on the protect
list — it pushed the first catalogue card from 1.22 to 1.48 viewports.

### 3.8 `crooks-packaging` — Crooks — Packaging
6 settings · blocks: `item` · homepage

Replaced the old CASE 001 box on the homepage. A packaging photograph with a
numbered manifest beside it (`Evidence tag`, `Security seal`, `Cuff keyring`),
heading `EVERY ORDER SHIPS LIKE THIS`, and a footnote asterisk carried per item
(`* CONTRABAND 03 SHIPS WITH SWEAT BOTTOMS ONLY.`).

### 3.9 `crooks-informant-intake` — Crooks — Informant Intake
19 settings · blocks: `@app` · homepage

SMS-first signup, email optional. **Two paths, by design:**

1. **App block (active).** A Shopify Forms block is installed in this section
   (`form_id 923202`). It writes a real customer with a real
   `smsMarketingConsent`.
2. **Fallback.** With no app block, the fields post as a `contact` form: the
   number reaches the store inbox, but no customer and no consent record is
   created.

The schema says this in a `paragraph` so nobody "simplifies" it. A
`{% form 'customer' %}` with a phone field would silently discard the number —
that form takes `contact[email]` only.

### 3.10 `crooks-terms` — Crooks — Terms
9 settings · blocks: `clause` · `/pages/terms`

Nine clauses in plain English — Carriage, Dispatch, Returns, Size swaps, Faults,
Refunds, Lost parcels, Orders we cancel, Contact — with a clause index and a
`LAST REVISED` date (13.08.2026). Links out to the real legal policies rather
than restating them.

### 3.11 `crooks-faq` — Crooks — Questions
5 settings · blocks: `qa`, `group` · `/pages/faq`

14 questions in 4 groups (Delivery, Sizing, Returns and refunds, Orders and
payment). Emits `FAQPage` structured data. `heading_level` is a setting so the
page owns its h1.

### 3.12 `crooks-tracking` — Crooks — Order Tracking
38 settings · `/pages/tracking`

Signed-in order lookup: order picker, three-stage timeline
(`01 Logged / 02 In transit / 03 Delivery`), courier record with
carrier + tracking number + a track button, and a custody log. States for
signed-out and no-orders. Everything on the page is real order data; the JS only
picks which record is on screen.

### 3.13 `crooks-set-cart` — Crooks — Set (cart)
3 settings · cart template

Cart-side half of the set offer. Two server-rendered states, no modal, no
script: one half of a set in the cart → a single line offering the other; the
bundle in the cart → the saving confirmed in words. Membership is read from the
same `crooks.*` metafields, identified **by reference, never by handle or
title**.

### 3.14 `crooks-footer-log` — Crooks — Footer Log
1 setting · blocks: `column` (6 link slots each) · `footer-group`

Four columns: SHOP, INFORMATION, CONTACT, GAME. Base line carries `© [year]`
substituted from a pre-formatted variable (filter-precedence trap). Renders
`crooks-schema-site`.

### 3.15–3.17 Dormant
`crooks-manifest` (WITNESS STATEMENT, 3 settings), `crooks-case-file`
(11 settings; leaderboard deliberately hidden because there is no Liquid-side
source for real scores — see KEEP.md §8), `crooks-board-test` (3 settings, the
board's isolated harness).

---

## 4. Snippets

| Snippet | Rendered by | Job |
|---|---|---|
| `crooks-schema-product` | `crooks-exhibit-record` | `ProductGroup` + one `Product` per variant, each with a full `Offer`; plain `Product` when single-variant; `BreadcrumbList` falling back to the product's own collection (skipping `all`/`frontpage`/`new`) so a direct landing still gets a middle crumb. Every value through `| json`. |
| `crooks-schema-site` | `crooks-footer-log` | `Organization` + `WebSite`/`SearchAction`, built from footer settings. `sameAs` is **allowlisted to social hosts** — without that filter the CASE 001 game link was being published as a brand profile. The SearchAction URL's `{search_term_string}` braces are assembled from single-character variables because Shopify's parser rejects literal braces inside a Liquid tag argument. |
| `crooks-set-toggle` | `crooks-exhibit-record` | The complete-the-set control — see §5. |
| `crooks-title` | log + record | Shared title/heading-level helper. |

---

## 5. The complete-the-set feature (end to end)

**Wiring: a real Shopify bundle, one variant per size pair.** Not a cart
transform, not two line items, not a discount function.

**Metafields that make a product a set member** (namespace `crooks`, all
`PUBLIC_READ`):

| Key | Type | Meaning |
|---|---|---|
| `set_partner` | product_reference | the other garment |
| `set_bundle` | product_reference | the bundle product that sells both |
| `set_partner_option` | single_line_text | the **name** of the bundle option holding the *partner's* size — stated explicitly so the theme never guesses which of the bundle's two size options belongs to which garment |
| `set_short_name` | single_line_text | how this product is named in its partner's copy |

**Currently configured on exactly two products:**

- `charcoal-cellblock-crewneck` (£50) ↔ `charcoal-cellblock-shorts` (£45)
- both point at `cellblock-set` (£85, 25 variants = 5 × 5 size pairs, 201 units)
- saving £10; the bundle sits in the `sets` collection

**Behaviour.** Collapsed by default, one line: *"Cop the full fit — add the
matching Cellblock Shorts. Save £10."* Ticking it reveals the partner's size
row, live partner stock, was/now prices, and relabels the button
`ADD THE FULL FIT — £85.00`. `crooks-set.js` swaps the form's hidden variant id
to the matching bundle variant and dispatches `crk:rerender`; unticking restores
whatever `crooks-record.js` decided. One add to cart, one line, no second
request.

**Guardrails:** no modal, no popup, no countdown, no "customers also bought".
Every price is pre-rendered by Liquid through `money` and carried in a data
attribute — JS never assembles a currency string, so presentment currency and
geo conversion stay Shopify's job. With `crooks-set.js` absent the panel stays
`hidden` and inert and the page still sells the single item. No product handle
appears in any file; adding a second set is four metafields and a bundle, with
no code change.

**Integration hook:** `crooks-record.js` calls `root._crkAfterRender({selected,
variant, complete, setBuy, idInput})` at the end of every render, and listens
for `crk:rerender`. That is the entire contract between the two files.

> **Open commercial decision (O1).** Discount code `10CROOKS` is ACTIVE, 10% off,
> with all three `combinesWith` flags **true**. It therefore stacks on the
> bundle, taking the £85 set to £76.50 — below the £85 the set copy states.
> Two clean options: tighten the code's combination settings, or exclude the
> bundle product from it. **No live discount has been touched.**

---

## 6. Assets

### Stylesheets

| File | Bytes | Loaded |
|---|---|---|
| `crooks.css` | 71,200 | every `crooks-*` section (single source of truth) |
| `crooks-cart.css` | 12,461 | `theme.liquid`, cart template only |
| `crooks-cart-drawer.css` | 8,382 | **deliberately not loaded** — see below |
| `crooks-tracking.css` | 3,973 | tracking section |
| `crooks-cart-progress.css` | 1,642 | carriage section |
| `crx-mono.css` | 989 | `theme.liquid` |

`crooks-cart-drawer.css` is kept but never linked: `settings_data.json` says
`cart_type: "drawer"`, but the Crooks header replaced Horizon's and does not
render `header-actions`, so `<cart-drawer-component>` appears zero times on any
template and the bag link goes straight to `/cart`. Loading it would be a
request per page for dead rules. The reasoning is in `theme.liquid` as a comment.

### Scripts (all vanilla ES2019, all `defer`, all `data-*` configured)

| File | Bytes | Loaded by | Job |
|---|---|---|---|
| `crooks-record.js` | 22,031 | PDP | variant selection, price/stock lines, gallery, accordions, sticky bar, notify panel, unit toggle |
| `crooks-board.js` | 18,869 | menu drawer (injected on first open), `crooks-board-test` | CASE 001 attract board, canvas |
| `crooks-search.js` | 7,463 | search | typeahead |
| `crooks-terminal.js` | 7,189 | status bar, hero, log | ticker, boot lines, filters, view/outline toggles |
| `crooks-drawer.js` | 5,924 | header | modal drawer |
| `crooks-set.js` | 5,551 | PDP | set toggle |
| `crooks-cart-progress.js` | 3,690 | carriage | AJAX cart updates |
| `crooks-theme.js` | 2,136 | header | light/dark |
| `crooks-tracking.js` | 2,027 | tracking | record picker |

### Fonts

`crx-mono.woff2` (16,520) + `crx-mono-bold.woff2` (16,724) — **CRX Mono is Space
Mono renamed**, SIL OFL, licence in `OFL-SpaceMono.txt`. VT323 is the display
face, `font-display: optional`, licence in `OFL-VT323.txt`.

**Metric-matched fallbacks, measured with fontTools, not guessed.** CRX Mono is
612/1000 = 0.612 em per character; DejaVu Sans Mono is 1233/2048 = 0.60205;
Liberation Mono 0.60010. That 1.7% gap was the header CLS. The fix:

```css
@font-face {
  font-family: 'CRX Mono Fallback';
  src: local('DejaVu Sans Mono'), local('Menlo'), local('Roboto Mono'),
       local('Liberation Mono'), local('Courier New');
  size-adjust: 101.653%;
  ascent-override: 110.179%;
  descent-override: 35.513%;
  line-gap-override: 0%;
}
```

(`VT323 Fallback` uses `size-adjust: 66.440%`. Overrides are divided by
`size-adjust`.) Result: the audit's reproduced 48px MAIN shift at 383px went to
**0px across 356–428px in both font states**.

The VT323 preload strips `asset_url`'s `?v=` query, because `crooks.css`
requests `url('vt323.woff2')` with no query and a relative `url()` resolves
against the stylesheet's directory — same file, two URLs, wasted preload. That
had the real font landing at 1,836ms against an FCP of 968ms and reflowing the
buy panel 28px.

### Theming

`data-crk-theme` on `<html>`, resolved before first paint by an inline
Liquid-free script in `theme.liquid` from `sessionStorage['crk-theme']`. Same
mechanism for `data-crk-outline` / `crk-outline`. Tokens are defined for three
surfaces:

```css
.crk-root,
main:has(> .shopify-policy__container),
body:has(main [data-crk-section]) { /* --crk-* tokens */ }
```

The third selector also paints the page ground on `body` and `main`, which is
what fixed the pale band showing through Horizon's `body` at `rgb(244,241,234)`.
Verified: dark `rgb(11,10,14)`, light `rgb(250,250,251)`, zero light surfaces
over 200px remaining.

---

## 7. Store-side dependencies

The theme is data-driven; these are the store objects it needs.

### Product metafields (namespace `crooks`, all `PUBLIC_READ`)

| Key | Type | Consumed by |
|---|---|---|
| `measurements` | json | PDP measurement table |
| `fabric`, `cut`, `origin`, `care`, `wash_code`, `case_ref` | text | PDP Specification |
| `model_image` | file_reference | catalogue "On model" view |
| `set_partner`, `set_bundle`, `set_partner_option`, `set_short_name` | see §5 | set toggle + cart line |

Also present store-side but **not** consumed by the theme: `shopify.*`
taxonomy metafields, and `reviews.rating` / `reviews.rating_count` — no reviews
app is installed, so no `aggregateRating` is emitted (deliberate, see §8).

### Catalogue

14 active products, plus the `cellblock-set` bundle and 1 draft. 10 products
archived, ~£28k of stock, still counted in admin inventory. Collections:
`frontpage` (23), `new` (11), `all` (14), `sweats` (5), `tees` (4), `denim` (4),
`accessories` (3), `tracksuits` (4), `sets` (1). Three collections have no
description at all: `frontpage`, `tracksuits`, `all`.

### Menus

`main-menu`: SHOP (→ ALL, NEW, TEES, DENIM, SWEATS, TRACKSUITS, ACCESSORIES),
TRACKING, QUESTIONS, TERMS, Contact.
`footer`: Search, Your Privacy Choices.
`customer-account-main-menu`: Orders, Profile (hosted account domain).

### Pages and policies

Pages: `contact`, `tracking`, `terms`, `faq`, `data-sharing-opt-out`.
Policies: Contact information, Privacy, Refund, Shipping, Terms of service —
all live, all CSS-skinned only.

### Apps

Only two app embeds are enabled in `settings_data.json`:

- **Shopify Forms** — provides the informant intake's real customer + SMS consent
- **Omnisend email marketing & SMS**

> **Open item (O2).** An "Add to wishlist" control and an "Only X in stock" line
> appeared on the storefront and were traced to app `bestpush-101`
> (`restock-sdk-loader.js`). It is **not** in `settings_data.json`'s embed list,
> so it is not a theme-app-extension embed this theme controls. The owner
> cancelled that investigation before it was resolved; nothing in the theme adds
> either element.

### Aftership

Returns are routed to `https://5wn03tnm.aftership.com` from the search direct
links and the FAQ.

---

## 8. Structured data surface

All server-rendered in Liquid, never injected by JS. Every interpolated value
passes through `| json`.

| Page | Emitted | Source |
|---|---|---|
| Product | `ProductGroup` + one `Product` per variant with full `Offer` (price, currency, availability, condition, seller) | `crooks-schema-product` |
| Product | `BreadcrumbList` — Home > Collection > Product | same |
| Collection | `CollectionPage` + `ItemList` of products actually rendered | `crooks-exhibit-log` |
| Collection | `BreadcrumbList` — Home > Collection | same |
| Every page | `Organization` + `WebSite`/`SearchAction` | `crooks-schema-site` |
| Questions | `FAQPage`, 14 Q&As | `crooks-faq` |
| Search results | **nothing** — deliberately, they must not be indexed | — |

**Deliberately not emitted:** `aggregateRating` / `review` (no reviews app;
inventing ratings is a manual action) and `OfferShippingDetails` (the rate card
is tiered and country-dependent; wrong shipping data in schema is worse than
none).

**Why this mattered.** The live theme emits `ProductGroup` from Horizon's
`sections/product-information.liquid`, which the Crooks PDP does not use, and
`Organization` from `sections/header.liquid`, which is disabled here. The
staging homepage carried **zero** JSON-LD blocks. Publishing the redesign before
this snippet existed would have deleted every product rich result and all Google
Shopping free-listing eligibility.

Verified on deployed pages: jeans PDP `ProductGroup`, 5 variants, £60.00 GBP,
InStock, `variesBy=size`, breadcrumb Home > Denim > BLUE WASH OG JEANS; socks
PDP 4 variants £6.00; collection `CollectionPage` numberOfItems 4; every page
`Organization sameAs [instagram, tiktok]`; exactly one h1 on home, collection
and product.

Full SEO baseline, owner task list and measurement plan: `SEO-PLAN.md`.

---

## 9. Behaviour that is deliberate — do not "fix" these

Condensed from `audit/KEEP.md` plus this build's own decisions. Each is a thing
an audit is likely to flag as a fault.

1. **The canvas board's three pause guards** (`matchMedia`, `document.hidden` +
   `visibilitychange`, `IntersectionObserver`) — measured 60.0 fps in view,
   57.5 fps under 4× CPU throttle while scrolling, **0 fps** off-screen, tab
   hidden, or under reduced motion. It contributes CLS 0. Shrinking or removing
   it gains nothing.
2. **`ADD TO BAG` / `CHECKOUT NOW` / `IN STOCK` / prices / sizes are never
   in-fiction.** This rule is why the aesthetic survives contact with a stranger.
3. **Sold-out sizes stay selectable** with `aria-disabled`, not the `disabled`
   property, which would remove them from the tab order.
4. **Accordions default closed** — owner request; `<details name>` gives
   exclusivity with no JS.
5. **The status slot shows stock, always**; the drop date is an addition to the
   register format, never a replacement, and never a badge.
6. **The hidden leaderboard is not an oversight** — there is no Liquid-side
   source for real scores, and placeholder scores are never rendered.
7. **No fake urgency** — no counters, no timers, no invented scarcity.
8. **The empty-search stand-down** is intentional: an empty register is worse
   than no register.
9. **`crooks-cart-drawer.css` unloaded** — see §6.
10. **Accessibility profile to preserve:** 0 of 35 interactive controls without
    an accessible name; exactly one h1 per page; `header`/`nav`/`main`/`footer`
    landmarks present; size buttons carry `aria-label` + `aria-pressed`; gallery
    is a labelled `role="group"`; focus ring 2px `rgb(167,122,199)` at 5.88:1;
    25 of 26 contrast pairs pass. The notify email field has its own label
    specifically so the "0 without an accessible name" number holds.
11. **No-JS fallback:** 18 product links and 40 images on the homepage, prices
    and sizes rendered, a working `/cart/add` on the PDP.

Anything touching `.crk-meta` or the display-font stack must re-run the no-JS
and 200%-zoom checks — the two things proven easiest to break silently.

---

## 10. Known open items

**Defects in theme code**

- **D1** — `crooks-status-bar.interval_ms` is seconds in the schema and
  milliseconds in the JS; the setting is inert. See §3.2.

**Decisions waiting on the owner**

- **O1** — `10CROOKS` stacks on the £85 set (§5).
- **O2** — wishlist / "Only X in stock" from app `bestpush-101` (§7).
- **O3** — the catalogue's `Outline` toggle is still present pending an
  aesthetic call on whether it stays.
- **O4** — the CASE 001 link points at `crooks-case-break.base44.app`, which
  serves the **old** build (appId `6a6fbf06…`). The board artwork was ported
  from the newer Copy (`6a734d61…`), for which no public URL was found. Art and
  link are therefore out of step.

**Store/admin work, not theme code**

- Three product image masters are `.webp` served under the wrong extension.
- ~£28k of archived stock still in inventory.
- No cookie banner.
- Placeholder measurement numbers on several products — *replace the data, not
  the component* (KEEP.md §3).
- The V2 BAGGIES description contains `5,1-5,4 XS` and the jeans say
  "9-16 days delivery uk", contradicting custody's "UK 1–2 working days".
- No governing-law line in Terms.
- SEO owner tasks: Search Console + sitemap, GA4, 14 product descriptions,
  8 collection descriptions, SEO title/description on all 22, homepage title and
  meta description, start the blog, a reviews app, SKUs on variants, Merchant
  Center. Detail and ordering in `SEO-PLAN.md`.

**Publishing is reserved to the owner. Nothing in this repo publishes a theme.**

---

## 11. How to re-derive everything here

```bash
# section inventory: name, settings count, block types
for f in sections/crooks-*.liquid; do …  # schema block between {% schema %} tags

# which template renders which section
for s in sections/crooks-*.liquid; do grep -l "\"$(basename $s .liquid)\"" templates/*.json sections/*-group.json; done

# persisted settings (these WIN over schema defaults)
python3 -c "import json,re; print(json.load(open('templates/index.json')))"

# store side
#   metafieldDefinitions(ownerType: PRODUCT), menus, pages, shopPolicies,
#   products{metafields(namespace:"crooks")}, codeDiscountNodes
#   — Admin GraphQL, read-only

# the protect list
git show origin/claude/crooksldn-site-audit-eijmkd:audit/KEEP.md
git show origin/claude/crooksldn-site-audit-eijmkd:audit/RUN3-FINDINGS.md
```

Decision log with the reasoning behind each change: `NOTES.md` (70KB, dated
sections). SEO baseline and owner task list: `SEO-PLAN.md`.
