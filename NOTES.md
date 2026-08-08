# CROOKSLDN theme — build notes

Running log of decisions and of upstream (store-side) issues that theme code must
not paper over. Anything under "Upstream fixes" is data to be corrected in the
Shopify admin — the theme deliberately does **not** code around it.

---

## Decisions

### Mono face: CRX Mono (Space Mono), not IBM Plex Mono

The prototypes were designed and validated on **IBM Plex Mono**. The live theme
already ships a self-hosted face called **CRX Mono**, loaded globally by
`assets/crx-mono.css`.

Inspecting the binaries (`assets/crx-mono.woff2`, `assets/crx-mono-bold.woff2`)
shows CRX Mono is **Space Mono** — Colophon Foundry for Google Fonts, SIL Open
Font License 1.1 — renamed. It is not a bespoke commissioned face.

- **Embedding is permitted.** OS/2 `fsType = 0` (installable/unrestricted), and
  the OFL expressly allows embedding and redistribution.
- **OFL obligations:** the licence must travel with the font, and the original
  copyright notice must be retained. `OFL-SpaceMono.txt` is committed at the repo
  root for this reason. Note the renaming to "CRX Mono" is *permitted* (OFL §3
  only reserves names the copyright holder marks as Reserved Font Names, and
  Space Mono declares none), but the copyright notice must still be preserved —
  it is, in `OFL-SpaceMono.txt`.

**Decision (George, Phase 1): keep Space Mono.** Using the store's existing face
avoids re-cutting every label, price and body line, and avoids the `!important`
conflict that swapping the face would create with `crx-mono.css`. The visual
difference from IBM Plex Mono is real but modest — both are grotesque monos on
a ~0.6 em advance; Space Mono has more idiosyncratic terminals and a slightly
narrower lowercase.

Single flip point if this is ever revisited: `--crk-font-mono` in
`assets/crooks.css`. Nothing else references the mono face.

Display face is **VT323** (unchanged from the prototypes), used only for
`.crk-h1`, `.crk-h2`, `.crk-price`, `.crk-rec__title`, `.crk-hero__tag`,
`.crk-custody__num`.

---

### VT323 was never loaded — the display face silently fell back

The brief's §4 called for font links for VT323 and IBM Plex Mono. The mono
decision was resolved in favour of the store's existing CRX Mono, but **VT323
itself was never actually loaded**: `--crk-font-display` named it, no
`@font-face` or link ever existed, so every display element silently fell back
to `ui-monospace`.

Affected everything set in the display face — the CROOKSLDN wordmark, the
header logo, section headings (EXHIBIT LOG, CASE 001), every price, exhibit
numbers, product titles on the record, and the custody step numerals. The CSS
was correct throughout; only the font was missing, which is why it looked
generically monospaced rather than like a terminal.

Fixed by self-hosting the Latin subset at `assets/vt323.woff2` with an
`@font-face` in `crooks.css` using the same relative-URL pattern as
`crx-mono.css`, plus a `preload` in `theme.liquid`. Licence in `OFL-VT323.txt`
(SIL OFL 1.1; note VT323 *does* declare a Reserved Font Name, unlike Space
Mono, so the family must not be renamed).

One known gap: the Latin subset does not include U+2605 BLACK STAR, so the star
in `CRXST★RZ` falls back to a system glyph inside display-face headings. It
renders correctly everywhere set in the mono face.

A separate audit confirmed **no other loss**: every selector in the prototype's
`crooks-terminal.css` is present in `assets/crooks.css`.

---

### Contrast: one token corrected, one left as a design decision

Measured every token pair in both modes during the Phase 5 verification pass.
Two fell below the §8 gate (body text >= 4.5:1); both come from the prototype's
own values.

**Corrected — `--crk-red` (dark mode): #C4433F -> #C95450.**
3.91:1 on panel, below AA. This colour carries SOLD OUT and the sold-out stock
line, which is information a customer needs in order to buy, so it falls on the
"costs a sale" side of the governing principle. The new value is the minimal
hue-preserving lift that reaches 4.50:1 on panel and 4.57:1 on ground. Light
mode was already fine at 6.48:1.

**Not changed — `--crk-micro`: 2.57:1 dark, 2.98:1 light.**
Deliberately left alone pending a decision. `.crk-micro` is pure chrome — EXH
numbers, "EVIDENCE PHOTOGRAPHY", photo counters — and its faintness is the
point. Raising it changes the look. If it should meet AA anyway:

| | current | 3.0:1 | 4.5:1 (full AA) |
|---|---|---|---|
| dark | `#575063` | `#615A6F` | `#7F7590` |
| light | `#93919B` | `#92909B` | `#74727E` |

Everything else passes in both modes, including body text (13.8:1 dark /
17.4:1 light) and the label on the purple buy button (7.65:1 in both).

---

### Variant picker rendered only one option — colours were unreachable

The exhibit record picked "the first option that is not Title" and rendered that
alone, so any product with more than one option lost the rest. Live option data
shows why a hardcoded assumption could never work — names, spelling and ORDER
all vary per product:

| Handle | Options, in the product's own order |
|---|---|
| `3-clives-tee` | `Size`, `Colour` |
| `crxst-rz-t-shirt` | `Color`, `Size` |
| `black-socks` | `Quantity` |
| `large-duffle-bag` | `size` (lowercase) |
| `v2-baggies` | `Size` |

So the tees rendered Size and never Colour, while CRXST*RZ rendered **Color as
if it were the size grid** and never showed Size at all. Both colourways were
unbuyable except via a direct ?variant= link.

Rewritten generically: every entry in `product.options_with_values` renders its
own labelled group, whatever it is called and in whatever order it appears.
Nothing in the theme names an option.

The variant matrix reaches JS as one `<span>` per variant carrying
`data-o1/o2/o3`, availability, quantity and price — DOM data attributes rather
than a JSON blob, because the house rule forbids Liquid inside `<script>`.
Selection resolves by matching every chosen option against that matrix, so it
works for one, two or three options.

Availability is still computed from `variant.available`, never the count: a
value is offered when some *available* variant carries it given the other
current selections, which means impossible combinations grey out as you choose.
A sold-out value stays visible and clickable — it reports its own state — but
never arms the form.

Verified in a browser against live markup, CSS and JS: options selected in
reverse order still resolve (proving no order dependence), price updates per
variant (socks 1pc GBP 6 -> 12pc GBP 45), and on v2-baggies the three
unavailable sizes each set SOLD OUT with no variant id while the two available
ones arm the form.

---

### Card double-render: `.crk-root img` outranked the hide rule

Two garments composited on every product card with a second image. The cause was
CSS specificity, not the hover logic:

```
.crk-root img         (0,1,1)  class + element   <-- won
.crk-card__img--alt   (0,1,0)  class only
```

`.crk-root img { display: block }` overrode `.crk-card__img--alt { display: none }`,
so the second image was painted **at rest, on every device** — no hover involved.
That is why it was worst on touch: there is no hover state there, so the rest
state is all you ever see. An earlier fix corrected only the hover case (hiding
the main image when the alt appears) and left the real fault untouched.

Fixed by prefixing the rules with `.crk-root` so they reach (0,2,1) and (0,3,1)
and win. Verified with computed styles on live markup + live CSS: exactly one
image painted per card, at rest and on hover, at 1280px and 390px, across all
seven multi-image products.

A follow-up fix gates the swap itself. The hover rule hid the main image
unconditionally, but Liquid only renders a second `<img>` when the product has
one — so hovering a single-image product hid its only image and left an empty
panel. The card now carries `crk-card--swap` only when `product.images[1]`
exists, and the hover rules require it. Eight of the fourteen products have a
single image, so this affected most of the grid.

This is the third instance of the same trap in this stylesheet — the others were
the anchor buttons (`.crk-root a` beating `.crk-btn--fill`) and the same on
ghost buttons. Any rule competing with a `.crk-root <element>` base rule needs
the `.crk-root` prefix to win.

---

### Product image source audit (Fault 3 deliverable)

Every image on the 14 active products, downloaded and inspected pixel-by-pixel:
alpha channel, corner opacity, share of opaque area, and how much of that
opaque area is near-white. "Baked" = a large opaque region that is
overwhelmingly white, i.e. a background burned into the file.

| Product | Handle | Images | Transparent? | Issue |
|---|---|---|---|---|
| 3 CLIVES TEE | `3-clives-tee` | 3 | 1,2 yes · **3 NO** | image 3 is JPEG, 100% opaque, 86% white — **re-cut** |
| BROADCAST TEE | `broadcast-tee` | 3 | 1,2 yes · **3 NO** | image 3 is JPEG, 100% opaque, 86% white — **re-cut** |
| MONEY CLIVE TEE | `evil-clive-tee` | 3 | all yes | — |
| GREY WASH OG JEANS | `cb1-wash-jeans` | 1 | yes | — |
| BLUE WASH OG JEANS | `cb2-wash-jeans` | 1 | yes | — |
| BLUE WASH JORTS | `cb1-wash-jorts` | 1 | yes | — |
| GREY WASH JORTS | `cb2-wash-jorts` | 2 | 1 yes · **2 NO** | image 2 is JPEG, 100% opaque, 69% white — **re-cut**. Also a two-item group shot where every other product is a single garment |
| V2 BAGGIES | `v2-baggies` | 2 | all yes | — |
| CHARCOAL CELLBLOCK CREWNECK | `charcoal-cellblock-crewneck` | 1 | yes | — |
| CHARCOAL CELLBLOCK SHORTS | `charcoal-cellblock-shorts` | 2 | all yes | — |
| CRXST★RZ T-SHIRT | `crxst-rz-t-shirt` | 2 | all yes | — |
| BLACK/BLUE MOTIONTEC SOCKS | `black-socks` | 1 | yes | — |
| WHITE/RED MOTIONTEC SOCKS | `white-socks` | 1 | yes | — |
| LARGE DUFFLE BAG | `large-duffle-bag` | 1 | yes | — |

**Three files to re-cut**, all JPEG: `3-clives-tee` #3, `broadcast-tee` #3,
`cb2-wash-jorts` #2. Nothing in CSS fixes a baked-in background — they need new
files with real transparency.

**The white box you saw on GREY WASH JORTS was not its main image.** That file
is a clean cut-out (35% opaque, 0% white). The white box was its *second* image
— a full-bleed white-background JPEG — revealed by the Fault 1 stacking bug.
With Fault 1 fixed it no longer composites, but hovering that card on desktop
still swaps to a white rectangle until the file is re-cut.

**Gating rule: exclude JPEG, not "include PNG".** Sources here are mixed PNG and
WebP, and WebP carries alpha perfectly well — an initial `.png`-only test wrongly
excluded six cut-out WebP files. JPEG cannot hold an alpha channel at all, so a
JPEG product shot always has a baked background. The audit confirms the
correlation exactly: every baked image is JPEG, every non-JPEG is a clean
cut-out. Currently 20 of 21 card images carry the outline; the sole exclusion is
the GREY WASH JORTS JPEG.

### Outline performance: drop-shadow beat feMorphology

Measured in Chromium at 390px, DPR 3, 120 cards (12x the real catalogue),
scripted scroll, frames counted over a fixed 4s window:

| CPU throttle | baseline | 4x drop-shadow | SVG feMorphology |
|---|---|---|---|
| 6x (mid-tier mobile) | 60.4 fps | 60.2 fps | 60.4 fps |
| 20x (extreme) | 60.1 fps | **59.7 fps** | 58.0 fps |

Zero frames over 50ms in any configuration. At realistic mid-tier throttling the
three are indistinguishable; only under extreme load does a gap open, and
drop-shadow is the *faster* of the two — the opposite of the expectation that one
filter pass would beat four. Drop-shadow shipped: faster under load, simpler, and
no inline SVG.

Two earlier measurement attempts were discarded as invalid and are recorded here
so the numbers above are not over-trusted: a rAF-paced scroll pins every variant
to exactly 16.67ms (it measures vsync, not filter cost), and CDP main-thread task
time showed filters as *faster* than baseline because filter raster does not run
on the main thread.

---

## Upstream fixes (for George — store data, not theme code)

### 1. CB1 / CB2 denim prefixes are crossed — CONFIRMED

Verified against live product data:

| Handle | Actual title | Wash |
|---|---|---|
| `cb1-wash-jorts` | BLUE WASH JORTS | **blue** |
| `cb1-wash-jeans` | GREY WASH OG JEANS | **grey** |
| `cb2-wash-jorts` | GREY WASH JORTS | **grey** |
| `cb2-wash-jeans` | BLUE WASH OG JEANS | **blue** |

The `cb1`/`cb2` prefix means the opposite thing for jorts than it does for jeans.
There is no rule that recovers wash from the handle.

**Consequence for the theme:** never resolve a product, or a wash sibling, by
hardcoded handle. Derive links from `product.url`, and resolve wash siblings by
**tag** or by an explicit metafield. Changing these handles later would break
existing inbound links, so it is a decision to take deliberately (with
redirects), not a quick rename.

### 2. Charcoal Cellblock crewneck/shorts swap — NOT REPRODUCED

The brief flagged `charcoal-cellblock-crewneck` and `charcoal-cellblock-shorts`
as swapped. **They are currently correct** and no fix is needed:

| Handle | Title | Featured image | Depicts |
|---|---|---|---|
| `charcoal-cellblock-crewneck` | CHARCOAL CELLBLOCK CREWNECK | `cellcrew.webp` | a crewneck sweatshirt |
| `charcoal-cellblock-shorts` | CHARCOAL CELLBLOCK SHORTS | `cellshorts1.png` | shorts |

Handle, title and image agree in both cases (images inspected directly, not just
by filename). Either this was fixed upstream already or the brief was mistaken.
Flagging rather than silently dropping it, in case the swap lives somewhere not
yet examined — e.g. in non-featured gallery images, or in the Kiwi size chart
assignments.

### 3. Product titles contain U+FE0F — CONFIRMED

`BLACK/BLUE MOTIONTEC™️ SOCKS` and `WHITE/RED MOTIONTEC™️ SOCKS` contain:

```
idx 20  U+2122  TRADE MARK SIGN
idx 21  U+FE0F  VARIATION SELECTOR-16   <- forces emoji presentation
```

The variation selector forces colour-emoji rendering, which shows as a grey/black
box in a monospace face. Strip it in one shared snippet, not inline:
`{{ product.title | replace: '️', '' }}` (the argument is the bare U+FE0F).

Also present: `CRXST★RZ T-SHIRT` contains `U+2605 BLACK STAR` at index 5. This one
is **intentional and must be preserved** — it is part of the product name, has no
variation selector, and renders as a normal glyph.

### 4. Negative inventory + mixed inventory policy — NEW, not in the brief

Several variants carry **negative** `inventory_quantity` (oversold), and
inventory policy is **not uniform across variants of the same product**:

- `3-clives-tee`, `broadcast-tee`, `evil-clive-tee` — every variant is
  `CONTINUE` (oversell allowed) with quantities down to **-7**. All still
  `availableForSale: true`, i.e. genuinely purchasable.
- `v2-baggies` — **mixed within one product**:

  | Size | Qty | Policy | Purchasable? |
  |---|---|---|---|
  | XS | 76 | DENY | yes |
  | S | 54 | DENY | yes |
  | M | **-1** | DENY | **no** |
  | L | **-2** | CONTINUE | **yes** |
  | XL | 0 | DENY | no |

**Consequences for the exhibit-record size grid (Phase 4):**

1. **Buyability must come from `variant.available`, never from
   `inventory_quantity > 0`.** On `v2-baggies`, L (-2) is buyable while M (-1) is
   not. A grid keyed on quantity would mark L sold out and block a real sale —
   precisely the failure mode the "fiction stops where it would cost a sale"
   principle exists to prevent.
2. **Never render a raw negative count.** "-7 IN CUSTODY" is nonsense. Show real
   counts only when `inventory_quantity > 0`.
3. The low-stock signal should fire only for `0 < qty <= threshold`; oversold
   `CONTINUE` variants get the normal available treatment with no count shown.

This is a data-hygiene issue worth correcting at source (the tees are selling
past zero), but the theme must handle it correctly regardless.

### 5. `crooks.*` metafield definitions — CREATED, values still empty

No product metafield definitions exist in the `crooks` namespace. The only
product definitions on the store are Shopify's standard taxonomy
(`shopify.color-pattern`, `shopify.size`, `shopify.accessory-size`).

Missing, all required by the exhibit record's spec panel:
`crooks.fabric`, `crooks.cut`, `crooks.origin`, `crooks.care`,
`crooks.wash_code`, `crooks.case_ref`, `crooks.measurements` (JSON).

**Status: the seven definitions now exist** (created via the Admin API in
Phase 4): `fabric`, `cut`, `origin`, `care`, `wash_code`, `case_ref` (text) and
`measurements` (JSON), all product-scoped with storefront read access.

**What remains is merchandising:** no product has any *value* set yet. Because
"a row with no data does not render", the spec panel renders
empty today. Definitions must be created **and populated per product** before
Phase 4 can be verified against anything real.

---

## Pre-existing exceptions to the house rules

Noted so they are conscious choices rather than surprises:

- `snippets/crack-the-cuffs.liquid` (rendered globally from `theme.liquid`)
  injects a fixed overlay using `border-radius` and `box-shadow`, and loads an
  iframe from `crack-cuff-codes.base44.app` — a non-Shopify, non-Google origin.
  This predates the terminal redesign and conflicts with both the "radius 0 / no
  shadows" rule and the "requests only to Shopify's CDN and Google Fonts" check.
- `assets/crx-mono.css` styles `.price`, `.sku`, `.product-inventory__text`,
  `.delivery-message__text` and `.product-badges` globally with `!important`.
  It is unscoped, so it reaches inside `.crk-root` wherever those Horizon class
  names appear. The Crooks sections use `crk-`-prefixed classes throughout and so
  are unaffected in practice, but this is why the terminal system must not reuse
  Horizon class names.
- `locales/*.json` carry 181 pre-existing `MatchingTranslations` offenses from
  the stock Horizon theme. `shopify theme check` therefore exits non-zero on a
  clean tree; judge Crooks work by the absence of *new* offenses.

---

### 6. Wash-comparison tags (CB1 / CB2) do not exist — feature is dormant

The wash comparison resolves siblings **by tag**, per the brief, because the
handle prefixes are crossed (issue 1). But no denim product carries a wash tag:

| Handle | Title | Tags |
|---|---|---|
| `cb1-wash-jeans` | GREY WASH OG JEANS | `new` |
| `cb2-wash-jeans` | BLUE WASH OG JEANS | `new` |
| `cb1-wash-jorts` | BLUE WASH JORTS | `new` |
| `cb2-wash-jorts` | GREY WASH JORTS | `new` |

`sections/crooks-exhibit-record.liquid` looks for a `CB1` or `CB2` tag and a
matching sibling of the same product type carrying the opposite tag. With no
such tags the panel simply does not render — which is the correct, non-
fabricating behaviour, but it means the feature is invisible today.

**To switch it on:** tag each denim product with its true wash — `CB1` for grey,
`CB2` for blue, or any pair of names, as long as the two siblings carry
*opposite* tags. Note the tag must describe the actual wash, not repeat the
handle prefix, since the prefixes are the thing that is wrong.

Deliberately not worked around by hardcoding handles.

---

## Specificity / selector trap #5 — shared class, shared handler

The Product/Model view buttons reuse `class="crk-filter"` so they match the
category chips exactly, pixel for pixel, without a second set of style rules.
That is fine for CSS and was a bug for JS: `initLog` bound its click handler to
every `.crk-filter` in the section, so clicking PRODUCT or MODEL also ran the
category filter with `data-crk-filter === null`. Null matches no category, so
every cell was hidden and the empty state took over — MODEL view rendered
"NO EXHIBITS MATCH THIS CATEGORY." against blank space.

Fix is one selector: `initLog` now reads `.crk-filter[data-crk-filter]`. The
class stays shared for presentation; the *data attribute* is what identifies a
category filter. `initViews` was already scoped to `[data-crk-view-btn]`, so the
collision only ever ran in one direction.

**Test lesson worth keeping.** The first pass called this feature working
because it measured `display` on the `<img>` elements inside each cell — and
those were correct. It never checked whether the *cells* were still visible.
Measuring the thing you changed will confirm you changed it; measuring what the
customer sees is a different assertion. The harness now reports cell count,
visible count and empty-state flag on every transition, and asserts the two axes
are independent:

    initial          14 visible, all `main`
    MODEL            14 visible, all `model`
    PRODUCT          14 visible, all `main`
    filter T-SHIRT    4 visible, all `main`
      + MODEL         4 visible, all `model`     <- filter survives view switch
      ALL            14 visible, all `model`     <- view survives filter reset

Verified against the assets actually deployed to staging (#202053779799), not
just the working copy.

## Audit remediation — theme-check exception

`layout/theme.liquid` trips `AssetPreload` ("prefer the preload_tag filter") on the VT323
preload. It is left as a hand-written `<link>` on purpose: `preload_tag` emits the URL from
`asset_url`, which carries the `?v=` cache-buster, and a mismatch between that URL and the
`url('vt323.woff2')` the stylesheet actually requests is precisely the bug BACKLOG #8 is
about — the font downloaded twice and reflowed the buy panel 28 px. The warning predates
this change; the raw `<link>` was already there.

## BACKLOG #15 — the reflow failure was bigger than the audit's diagnosis

The audit attributed the 200% zoom failure (scrollWidth 308 vs clientWidth 195) to three
offenders: `.crk-status__msg`, `.crk-header__actions` and `.crk-table`. Removing the first
`white-space: nowrap` and giving the table a scrollport took the PDP from 308 to 298 and the
homepage from 375 to 375 — i.e. almost nothing. The real cause was structural and appeared
in five places, all the same bug:

**Grid and flex items default to `min-width: auto`, so the widest unbreakable child sets the
floor and the container refuses to shrink.**

| Where | Floor set by | Fix |
|---|---|---|
| `.crk-log__cell` | longest product name | `min-width: 0` |
| `.crk-hero__type` | `.crk-boot__line` (nowrap) + the display `h1` | `min-width: 0` |
| `.crk-grid > *` | case + intake panels | `min-width: 0` |
| `.crk-input` | `flex: 1 1 220px` basis | `min-width: 0` |
| `.crk-spec` | `minmax(96px, auto)` term column left the value ~1px | stack below 360px |

Plus wrapping for rows that genuinely cannot fit tracked uppercase on one line at 195 CSS px:
`.crk-card__top`, `.crk-card__row`, `.crk-views`, and `.crk-header__bar` below 360px.

Measured after: homepage **195/195** and **320/320**, PDP **195/195** and **320/320**. Both
templates were re-shot at 390 and 1440 to confirm nothing moved at normal widths.

**Method note.** The first verification run reported all of this still broken, because the
harness fetched `crooks.css` from the bare asset path and Shopify's CDN served a stale build
for it. The `?v=` cache-buster has to stay on the request *and* in the local cache key. A
harness that silently tests yesterday's CSS reports confident nonsense.

## BACKLOG #3 — the worst finding was a symptom of BACKLOG #5

The audit recorded that tapping a sold-out size on V2 BAGGIES did nothing: `selectedVariantId`
stayed on XS, the sticky bar stayed on XS, the buy button stayed enabled, and `/cart/add.js`
returned `"variant_title":"XS"`. It read as broken variant logic. It was not.

Proven by A/B against the pre-audit fallback theme (#203044159831) kept as a control:

| | pre-audit build | after the popup was gated |
|---|---|---|
| `elementFromPoint` at the sold-out chip | `iframe.ctc-frame` | `button.crk-size` |
| after a **real** pointer click | stays XS, "Add to bag", enabled | cleared, "SOLD OUT", `disabled === true` |

The CRACK THE CUFFS overlay at `z-index: 2147483647` was swallowing the taps. `crooks-record.js`
had been correct the whole time.

**Method note that matters.** A programmatic `element.click()` dispatches straight to the node and
ignores hit-testing, so it "passes" underneath a full-screen overlay. Only `page.mouse.click()` at
the element's centre — plus an `elementFromPoint` check — reproduces what a thumb does. The first
run here used `.click()` and would have declared the bug fixed without FIX 1 having anything to do
with it.

### What was genuinely broken, and is now fixed

- **The notify block was gated at product level.** `{% if product.available %}` meant the existing
  RELEASED + email-capture block only rendered when *every* variant was gone, so the shopper whose
  size was sold out while others remained was offered nothing. A second instance of the same
  component now renders inside the available branch, hidden until the chosen combination is
  unavailable. It sits outside the product form because HTML forbids nested forms, and it carries
  the chosen size in `contact[variant]` so a restock request says which size.
- **`--crk-red` is now used for the state it was reserved for**, and only that.
- **The server render was variant-blind.** The size buttons were pre-selected from `crk_var` while
  the stock line always said "Select a size" and ADD TO BAG was enabled — so a JS-off shopper
  landing on `?variant=<sold out>` got an enabled buy button carrying that variant's id. Stock
  line, buy label and `disabled` are now all derived from `crk_var`.
- **Dead selector removed.** `crooks-record.js:19` queried `.crk-size[data-size]`; the Liquid emits
  `data-crk-opt` / `data-value` and never `data-size`, so it matched nothing and was never read.

### Found while fixing it, not in the audit

`In stock · Ships within 24 hours` is product-level and sat two lines under `SIZE L IS SOLD OUT`.
Now hidden whenever the chosen variant is unavailable, server-side and in JS.

Verified end to end on the deployed staging build: L / XL / M / XS / S each tapped with a real
pointer, every state consistent, no JS errors, one `h1`, size buttons keep `aria-label` and
`aria-pressed`, and the noscript size list still renders only buyable sizes.

## BACKLOG #14 — filing dates in the register

The status slot rendered `AVAILABLE` on all fourteen cards, so the register could not tell a
returning shopper what had changed. It now carries `FILED dd.mm` for anything published inside
a window, falling back to `AVAILABLE` outside it. The sold-out branch is untouched and
`--crk-red` is not spent here.

`product.published_at`, not `created_at`: several products were created months before they went
on the storefront (V2 BAGGIES created 22 March, published 13 July), and it is the storefront
date a shopper is being told about. Caveat: `published_at` moves if a product is unpublished and
republished, so it can overstate freshness.

**The window is a setting, not a constant, because it is an editorial call.** Measured against
the real catalogue on 8 August:

| Window | Cards stamped |
|---|---|
| 30 days (default) | **4 of 14 (29%)** — V2 BAGGIES, CRXST★RZ, both MOTIONTEC socks |
| 35 days | 11 of 14 (79%) — seven products share a 4 July publish date |
| 75 days | 14 of 14 — no signal at all |

`/collections/new` returns 9 of 14 (64%), which is why the audit called it no signal. 30 days
lands the register on the right side of that; 35 falls off a cliff because of the 4 July batch.

**Liquid trap worth recording.** This first rendered as `13.07` with the label gone:

    {{ filed_label | replace: '[date]', product.published_at | date: fmt }}

Filters chain left to right with no grouping, so `date:` was applied to the *result of the
replace* — it reformatted the whole `FILED 2026-07-13...` string and swallowed the label. The
date has to be formatted into its own variable first.

## BACKLOG #9 — the cart, brought into the design language

The cart is Horizon's, assembled from `content_for 'block'`, and its wallet buttons are
Shopify-owned chrome that cannot be restyled at all. Rewriting it was neither safe nor
necessary. `assets/crooks-cart.css` instead repoints **Horizon's own design tokens** at the
terminal's, so the whole cart restyles without one line of its Liquid changing. It loads from
`theme.liquid` only when `template.name == 'cart'`, which is why it can scope to `:root`.

**Specificity, not load order.** Horizon emits `:root, .color-scheme-1 { --color-background-rgb: … }`
in an inline `<style>` that lands *after* any stylesheet link, so an equal-specificity override
loses. `:root:root` and `:root [class*="color-scheme"]` are both (0,2,0) and win wherever the
inline block sits. Chasing load order would have been fragile — that block is emitted during
section rendering.

Measured on the deployed cart, 390 and 1280, dark and light:

| | before | after |
|---|---|---|
| Typefaces | Archivo Narrow **+** CRX Mono | CRX Mono only |
| Ground | `rgb(244,241,234)` bone | `rgb(11,10,14)` |
| Sub-44px tap targets | 4 | **0** |
| Shadows | 1 | 0 |
| `aria-required-children` | 1 critical | **0** |
| Horizontal overflow | none | none |

Checkout still completes: the button is a real `<button name="checkout">`, enabled, 124×54, and
9th of 18 in the tab order.

### The axe violation

`snippets/cart-products.liquid` set `role="table"` on a `<table>` and `role="caption"` on its
`<caption>`. The ARIA `table` role permits only `row`/`rowgroup` children, so an explicit
caption child is invalid under it — while the native HTML pairing is entirely correct. Both
attributes duplicated what the elements already expose, so removing them restores native
semantics and clears the violation with no markup change. `sections/quick-order-list.liquid:45`
has the same pattern but is not on the cart; left alone.

### Found here, not in the audit: the cart thumbnail

A cart line rendered its product shot at **552×552**. This is pre-existing — the pre-audit
fallback theme measures **563×563** — and the audit missed it because every cart screenshot it
took was of an *empty* cart. There is no merchant-facing width setting for that block, so the
cap lives in CSS: 96px mobile, 120px above 750px.

### Harness error worth recording

The first cart audit ran against a page with Horizon's `base.css` and `styles.css` **stripped**,
because the localiser only kept stylesheets with `crooks` in the filename. Every layout and
tap-target number from that run was meaningless. Re-run with all six stylesheets present the
token results happened to hold — but that was luck, not method. A harness must serve the page
the browser would actually get.

## Header logo in dark mode

The uploaded mark (`IMG_3682.png`, 241×161) is a **pure black silhouette on transparency** —
every opaque pixel samples as `rgb(0,0,0)`. On the `#0B0A0E` ground it was invisible.

Fixed with `filter: invert(1) brightness(0.88)` in dark mode only. The invert lifts the black
pixels while the alpha channel is preserved, and the brightness pulls pure white back to roughly
`--crk-text`'s value so the mark does not out-shout the wordmark beside it. Light mode is left
alone.

Gated on a section setting (`logo_invert_dark`, on by default) rather than hardcoded, because
inverting a *colour* logo would wreck it — if the mark is ever replaced with one, the switch is
in the theme editor, not in CSS. Driven by a `data-crk-logo-invert` attribute on the header, so
no Liquid goes anywhere near a style tag.

A recolour-by-mask would hit `--crk-text` exactly rather than approximately, but the logo URL is
a merchant setting and CSS `mask-image` would need that URL inlined — which is the thing the
house rules forbid. Invert is the honest trade.

## Incident — pushing an editor-owned JSON wiped merchant settings

**What happened.** Changing the announcement-bar copy, I edited `sections/header-group.json`
in the repo and pushed it. Section-group and template JSON files are written by the **theme
editor**, so the authoritative copy lives on the theme, not in git. The repo copy was stale, and
pushing it overwrote four settings George had set in the editor:

| Setting | Was on the theme | After my push |
|---|---|---|
| `logo` | `shopify://shop_images/IMG_3682.png` | *gone* — header fell back to the wordmark |
| `show_theme_toggle` | `true` | *gone* |
| `label_to_light` / `label_to_dark` | `LIGHT MODE` / `DARK MODE` | *gone* |
| status message `m3` | `[count] PRODUCTS CURRENTLY ONLINE` | reverted to `[count] EXHIBITS CURRENTLY LOGGED` |
| status message `m2` | *deleted in the editor* | **re-added** (`PROPERTY STORE — UNIT 7, LONDON`) |

The last two are worse than the first three: they silently reinstated copy George had explicitly
asked to be removed.

**Fix.** Pulled `header-group.json` from the pre-audit fallback theme (#203044159831), which
still held the correct editor state, re-applied *only* the announcement copy change on top, and
pushed that. The repo copy now matches the theme.

**Rule going forward.** Before pushing any `sections/*-group.json` or `templates/*.json`, pull
that file from the target theme first and edit the pulled version. `.liquid`, `.css` and `.js`
assets are code and safe to push from the repo; the JSON is merchant data and is not.

`footer-group.json` was checked the same way and was clean — the `TRACK ORDER` addition was the
only difference.

**Unverified.** `templates/index.json` was pushed earlier in the same session, before the
fallback themes existed, so there is no pre-push control to diff against. The homepage renders
with all of George's requested copy intact, but if he made homepage edits in the theme editor
between the repo's last sync and that push, they cannot be recovered from here.

## "Statement of provenance" → "Item description"

Provenance means an object's documented ownership and origin history — an art-and-antiques
term. The accordion it labelled renders `product.description`: fabric, cut, fit. The label
promised origin history and delivered a product description.

Three reasons it had to go, beyond the plain mismatch:

- **It collided with CHAIN OF CUSTODY.** In both evidence and art usage the two phrases mean
  nearly the same thing. Two headings on one page, meaning different things, sharing a meaning.
- **The audience won't have the word.** Traffic is Instagram and TikTok, young, mobile.
- **It was BACKLOG #13 again on a different accordion.** Good content behind a label that does
  not say what is inside. Persona 1 went hesitant at step 7 for exactly that reason on the
  custody panel and only converted at step 8 after opening it.

Now `Item description`, and it opens by default — `SPECIFICATION` and `MEASUREMENTS` were both
open while the description, the thing most shoppers want first, was the one collapsed.

**Method note, following the header-group incident.** `provenance_open` looked persisted in the
repo's `templates/product.json`, which would have meant the schema default could not take
effect. Pulling that file from the theme first showed the opposite: the theme stores *fewer*
keys than the repo, so those accordions run on schema defaults and changing the default was
sufficient — no template push, no merchant data touched. The repo copy has been synced to the
theme's so the stale keys cannot cause a future clobber.

`templates/index.json` was diffed the same way and is clean: the only difference is an empty
`"settings": {}` object Shopify normalises. The earlier worry that the index push might have
lost editor changes is retracted — it did not.

## Colourway swatches on catalogue cards

Four products carry a colour option; nothing else does. The PDP already let you pick colour
(the generic variant picker), but the register gave no sign a tee came in two colourways, so
the information only existed after a shopper had already opened the product.

**Colour source, in order:**
1. the merchant's configured Shopify swatch (`value.swatch.color`)
2. else the option value used directly as a CSS colour keyword — `BLACK`, `WHITE`, `NAVY`,
   `OLIVE` all resolve
3. else an empty square with its rule, plus the visually-hidden name

No hardcoded colour map, nothing invented. Only **CRXST★RZ** has swatches configured today
(`#000000` / `#FFFFFF`); the other three tees fall through to step 2 — and both paths render
identical `rgb(0,0,0)` / `rgb(255,255,255)`, verified in the browser. Setting swatches in the
admin for the other three would make the source authoritative rather than inferred.

**Which option counts as "colour" is a setting**, not a hardcoded name, because this catalogue
already spells it two ways: three tees use `Colour`, CRXST★RZ uses `Color`. Default matches
`Colour,Color,Colourway,Colorway`. The socks are the proof the matching is not over-eager —
their option is `Quantity`, and they correctly render no swatches.

A colourway with no buyable variant is dimmed, computed in a single pass over the variants. A
swatch for a colourway that is entirely gone would be a lie on a card nobody has opened yet.
Swatches only render when the option has more than one value; "available in one colour" is not
information.

**"Pills" became squares.** The system enforces `border-radius: 0` globally, twice, once with
`!important`. Rounded pills would have been the only rounded thing on the site.

Reflow re-checked after the change: 195/195 and 320/320, unchanged.

### Upstream inconsistency (admin, for George)

| Product | Option 1 | Option 2 |
|---|---|---|
| 3 CLIVES TEE / BROADCAST TEE / MONEY CLIVE TEE | Size | Colour |
| CRXST★RZ T-SHIRT | **Color** | **Size** |

CRXST★RZ uses the American spelling and the reverse order, so on three tee pages the size row
renders first and on that one the colour row does. The theme handles both spellings; the
ordering inconsistency is visible to shoppers and is an admin fix.

## Catalogue source switched from `frontpage` to the ALL collection

`frontpage` (title "PRODUCTS") holds **23** products, of which only 14 are published — the other
nine are the archived items from BACKLOG #2, invisible to Liquid but sitting in the collection.
The new `ALL` collection holds exactly the 14. Same output today; a cleaner source.

**Three settings changed, not one.** The collection drives three separate things and they must
agree:

| Section | What it derives |
|---|---|
| `crooks-exhibit-log` | the register itself, and each card's `NO. nn` |
| `crooks-hero-intake` | the `n PRODUCTS CURRENTLY ONLINE` count |
| `crooks-exhibit-record` | the PDP's `PRODUCT n / 14` and the back link |

Leaving the PDP on `frontpage` while the register used `ALL` would let a card read `NO. 07`
while its own product page read `PRODUCT 03 / 14`. Verified after the change: card `NO. 01` and
`PRODUCT 01 / 14` are the same product.

**Side effect worth knowing:** the register order now follows the ALL collection's sort order,
not `frontpage`'s. Reordering that collection in the admin is now how the register is ordered —
which is the useful version of this, but it did change today's order.

**Handle caveat.** The collection's handle is `all`, which collides with Shopify's reserved
`collections.all` global (all published products in the store). Tested: `/collections/all`
renders the collection's own title, so the custom collection owns the handle here. But the two
are indistinguishable today because both contain the same 14 products. If the built-in ever
takes precedence, curation would silently stop mattering — a product added to the store but not
to ALL would still appear. A distinct handle (`catalogue`) would remove the ambiguity entirely.

Pulled both templates from the theme before editing, per the rule from the header-group incident.

## Buying from the product page: two actions, neither of which leaves the page unasked

Before this, `ADD TO BAG` was a plain `{% form 'product' %}` POST with no JS anywhere, so every
add did a full page load and dumped the shopper on `/cart`. For a catalogue with £6 socks and
£60 jeans that is the wrong default — it ends the browse.

**ADD TO BAG** now posts to `/cart/add.js`, stays put, updates both header cart counts and
confirms with a readout in the same voice as the dispatch line — `> Added — 2 in bag`, with a
link to the bag. No overlay, no drawer, nothing to dismiss; the audit found overlays interrupted
every one of the eight personas. Errors are surfaced from Shopify's own `description` field
rather than a generic message, so "sold out" reads as sold out.

Progressive enhancement throughout: the form's `action="/cart/add"` is untouched, so with JS off
it posts normally and lands on the cart. The no-JS path that KEEP.md flags as worth protecting
still sells.

**CHECKOUT NOW** is Shopify's dynamic checkout (`payment_button`) — George's call, made with the
trade stated: one tap for anyone with Shop Pay saved, at the cost of the only non-CROOKSLDN
pixels in the buy panel. Its chrome is Shopify-owned and cannot be restyled, so it is framed
rather than faked, and the frame only draws when there is a wallet inside — Shopify renders the
container regardless of whether any payment method is enabled, which is the same empty-box fault
the cart had.

**The sticky bar carries both.** It sits outside the product form, and Shopify only renders a
`payment_button` inside one, so its CHECKOUT NOW is a theme button that adds and then goes to
checkout: same destination, different mechanism from the wallet row above it. Worth knowing that
the two paths are not identical.

I warned that two controls plus title and price would squeeze the bar below 44px. Measured, it
does not:

| Viewport | ADD | CHECKOUT NOW | Page overflow |
|---|---|---|---|
| 390 | 108×44 | 121×44 | none |
| 360 | 108×44 | 121×44 | none |
| 320 | 108×44 | 121×44 | none |

### Testing note

The AJAX path cannot reach the network from this container, so it was tested by stubbing
`window.fetch` — that exercises this code, not Shopify's. Three consecutive adds increment the
bag 1 → 2 → 3 and the readout follows. Verified separately with curl that `/cart/add.js` works
against the real store, and that Shopify is emitting `shopify-payment-button__button` in the
served HTML.

A first run reported "the second add does nothing". That was the harness: it reused click
coordinates captured before the confirmation line shifted the layout. Re-probing the element
before each click showed all three adds working. Same failure as the sold-out test — coordinates
go stale the moment the DOM moves.
