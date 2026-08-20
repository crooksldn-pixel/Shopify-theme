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

## Outline toggle (temporary, for evaluation)

A single chip in the catalogue toggles the alpha-trace outline on product shots. The attribute
lands on `:root` and the choice is held in `sessionStorage`, so the product page follows the same
setting and it survives navigation. Resolved in the existing inline head script alongside the
theme, so there is no flash of outlined images before it applies.

**Dark mode only.** `:root[data-crk-theme="light"] .crk-product-image` already sets
`filter: none`, so the button does nothing in light mode. Worth knowing before judging.

Deliberately built to be disposable: its own section setting (`show_outline_toggle`) so it can
be removed in one click, its own `data-crk-outline-btn` attribute so `initLog`'s category filter
can never pick it up — the view toggle and the category chips shared a class once and it hid
every product — and an `outline_default` select so the winner can be made permanent from the
theme editor without touching code.

Verified: on → off → on, with the computed `filter` genuinely changing, `aria-pressed` following,
and the choice persisting.

### Three harness failures in one sitting, same root cause

1. `scrollIntoView` and `getBoundingClientRect` in the same evaluate — the rect is the
   pre-scroll one, so the click lands somewhere else entirely.
2. The stray click hit a product card link and navigated the page away, after which the button
   "did not exist".
3. Earlier, the same stale-coordinate bug made a working second add-to-bag look broken.

`locator.click()` re-measures after scrolling and waits for stability, which is why it worked
first time. **Use it instead of `mouse.click` on computed coordinates** unless the point is
specifically to test hit-testing — and when a harness says a feature is broken, suspect the
harness before the feature.

## Order tracking — ported from crooksldn-tracking-page

Closes BACKLOG #10 properly, replacing the `/account` stopgap.

**The prototype had no data source.** `src/lib/tracking/lookupOrder.js` is a mock over six
hardcoded orders (`1001`–`1006`, fixed postcodes) and says so in its own header: *"DEVELOPMENT
MOCK DATA — REMOVE / REPLACE BEFORE PRODUCTION… NEVER place a private Shopify Admin API token in
browser code."* Ported as-is it would have returned NOT FOUND for every real order.

Two departures from the prototype, both forced by what data actually exists:

**1. Signed-in customer's real orders, not order-number + postcode lookup.** Guest lookup needs
an Admin API token behind an App Proxy — infrastructure, not a theme file. `customer.orders`
gives real orders, real carriers, real tracking numbers and URLs, today, with nothing invented.

**2. The five stages collapse to two knowable ones plus a hand-off.** Shopify does not model
MANUFACTURING or INBOUND FREIGHT at all. Liquid's `fulfillment` drop carries `created_at`,
`tracking_company`, `tracking_number` and `tracking_url` — **and no shipment status**, so a theme
cannot know an order was delivered either. The timeline therefore reports:

| Cell | Source |
|---|---|
| 01 LOGGED | `order.created_at` — always true |
| 02 IN TRANSIT | a fulfillment exists / `fulfillment_status == 'fulfilled'` |
| 03 DELIVERY | never claimed — labelled "tracked by courier" and links to `tracking_url` |

The custody log is built only from timestamps Shopify holds: order placed, and dispatch if a
fulfillment exists. No invented events, which is why an unfulfilled order shows exactly one line.

The prototype hardcodes `#0B0A0E / #0E0C13 / #3A2F4A / #A77AC7 / #DDD7C9` — exactly the terminal
tokens — so the port maps onto `--crk-*` and follows light/dark for free.

**Signed-out state names the emailed order-status link**, because that is the only route that
works without an account and a shopper who cannot sign in otherwise hits a dead end.

No-JS: every record renders stacked; the JS only chooses which one is on screen.

**This store uses new customer accounts** (no `templates/customers/`, account lives on
`friendsof.crooksldn.com`), so this is a page template — `templates/page.tracking.json` — not an
account template.

**Not yet verified in a browser:** rendering needs a page in the admin using the `tracking`
suffix, and creating one touches the live storefront. Left for George to authorise.

## Cart line items on mobile

Reported as "items clash with the text". Measured, it was not a text collision but a
**four-column table forced onto a phone**:

| Width | media | details | quantity | price |
|---|---|---|---|---|
| 390 | 96 | **63** | 136 | 53 |
| 320 | **28** | **61** | 136 | 53 |

The quantity stepper is a fixed ~136px — 48% of the usable width at 320px — so the thumbnail
collapsed to 28px and the product title was left 61px to wrap into.

Below 600px the row is now a two-column grid: an 88px thumbnail on the left, with details,
quantity and price stacked beside it. Details went **63 → 256px** at 390 and **61 → 186px** at
320. No overflow at 390, 360 or 320.

**Why changing `display` on table elements was safe here.** It normally strips the implicit
table semantics. Horizon's markup already carries explicit `role="row"` and `role="cell"`, but
the table itself had no role — I had removed `role="table"` earlier to clear the
`aria-required-children` violation caused by pairing it with a `<caption>`. So the caption (a
screen-reader-only total) moved *out* of the table into a visually-hidden `<p>`, which let
`role="table"` come back. Full ARIA structure, and the grid layout cannot break it.

Two more found while measuring:
- The variant line (`XS`) is a `<dd>` carrying the UA default `margin-left: 40px`. `crooks.css`
  resets that inside `.crk-root`; the cart is Horizon's markup and never enters that scope.
- The remove control was inheriting the primary purple fill and reading louder than *Check out*.
  Ghosted, target kept at 44px.

Sub-44px tap targets on the cart page: **0** (Horizon's card-gallery arrows in the
recommendations rendered at 20×26 — pre-existing, not part of this fix, raised anyway).

**Harness note:** the overlap detector flagged `Product image ⨯ IMG` throughout. False positive —
those are `<th>`s inside a `position: absolute; clip: rect(0,0,0,0)` `<thead>`, so
`getBoundingClientRect` reports a real box for something that is clipped to nothing. A detector
that ignores `clip` will invent collisions.

## Tracking added to the main menu

`SHOP / TRACKING / Contact`. Navigation is store data shared with the live theme, so the item is
live now — and on the live theme `/pages/tracking` still renders a bare titled page until the
theme is published. Also noted: the menu's SHOP entry still points at `frontpage`, not the ALL
collection the catalogue now uses.

## A wrong diagnosis, recorded so it isn't repeated

`config/settings_data.json` sets `"cart_type": "drawer"`, and `snippets/header-actions.liquid`
renders `<cart-drawer-component>`. From that I concluded the reported mobile clash was the cart
drawer going unstyled, because `crooks-cart.css` is gated to `template.name == 'cart'`. I built
a drawer stylesheet and deployed it.

**It renders zero times.** The Crooks header replaced Horizon's and never renders
`header-actions`; its bag link points at `routes.cart_url`. Checked on the homepage, the cart
and a product page: `cart-drawer-component` appears 0 times on all three. The setting is inert.

The global include was reverted so it is not a request per page for dead rules.
`assets/crooks-cart-drawer.css` is kept, unreferenced, because the setting would become live
again if Horizon's header were restored.

**The lesson:** a theme *setting* and a *snippet that exists* are not evidence that anything
renders. Grep the served HTML, not the repo. Two greps would have saved the whole detour.

## The reported mobile cart clash was the LIVE theme, not a bug

Reproduced by building an identical cart in one session and rendering it twice under iPhone 13
emulation — once with `?preview_theme_id=202053779799`, once without:

| | details column | title | outcome |
|---|---|---|---|
| Live theme | **68px** | wraps to two lines | collides with the quantity stepper |
| Staging | **256px** | single line | clean |

Live carries neither `crooks-cart.css` nor any `crk-` markup. The preview cookie is per-browser,
so opening the preview on desktop does not carry to a phone. Every customer on the live
storefront currently sees the left-hand cart; publishing is the fix.

**Two measurement errors of my own, found on the way:**

1. `.cart-items__table-row` is on the `<thead>` header row as well as the body rows.
   `querySelector('.cart-items__table-row')` returns the clipped, 1px-wide hidden header — so
   cells, title and image all measured as null and an earlier screenshot clipped around the
   wrong element by luck. Row measurements must be scoped `tbody > .cart-items__table-row`.
   The mobile grid is now scoped the same way, so the hidden header row is not laid out as one.
2. Diagnosing from the repo instead of the served HTML produced the cart-drawer detour above.

**The standing lesson:** when the person holding the phone says it is broken and the harness says
it is fine, establish *which build they are looking at* before measuring anything again. Two
rounds of re-measuring were spent before checking the most likely explanation.

## Collection pages now render the register

`/collections/all` — and every other collection page — was still Horizon's stock
`main-collection` + `category-bar`, in stark contrast to the rest of the site. They now render
`crooks-exhibit-log`, the same section as the homepage catalogue.

**The section had to learn where it is.** It read `collections[section.settings.collection]`,
a fixed handle — so on a collection template every category page would have shown the same
products. It now prefers the collection being viewed:

    assign crk_col = collections[section.settings.collection]
    if collection and collection.handle != blank
      assign crk_col = collection
    endif

`collection` is only defined on collection templates, so the homepage is untouched and needs no
new setting. The heading falls back to `collection.title` when the section's own heading is
blank, so the homepage keeps "Catalogue" while each collection page carries its own name.

Verified on the deployed build:

| Page | Cards | Heading | Filter chips |
|---|---|---|---|
| /collections/all | 14 | ALL | ALL · T-SHIRT · DENIM · SWEATS · ACCESSORIES |
| /collections/denim | 4 | Denim | *(none — see below)* |
| /collections/tees | 4 | Tees | none |
| /collections/accessories | 3 | Accessories | none |
| /collections/new | 9 | New | ALL · T-SHIRT · DENIM · SWEATS |

**The filter rail now needs more than one category, not more than zero.** On
`/collections/denim` every product is Denim, so it rendered "ALL | DENIM" — two controls that
do nothing.

**The outline toggle is off on collection pages.** It is a temporary evaluation control and it
was taking a third full row of chrome above the first product on a phone. It stays on the
homepage, which is where the comparison is being made.

Horizon's template is preserved verbatim as `templates/collection.horizon.json`, the same
treatment `product.horizon.json` got.

No horizontal overflow at 390 or 320.

**Not addressed:** the section renders `crk_col.products` with no `paginate`. At 14 products
that is fine; past ~50 a collection page would silently truncate. Worth revisiting before the
catalogue grows.

## Carriage status bar (cart) — grounded in the real rate card

Built from the delivery profile and 42 real orders, not from a guess.

**The shipping rules that already existed and were nowhere on the site:**

| UK method | Price | Free at |
|---|---|---|
| Tracked 48 | £3.00 | **£20** |
| Tracked 24 | £4.99 | **£70** |

EU is a flat £12.99 and International £18.99, both with **no free tier** — which is why the bar
is UK-only. Showing a threshold to an overseas shopper would be chasing something that does not
apply to them (~7% of orders).

**Why the £70 tier is the one worth promoting.** From the last 42 paid orders (8 test/£0
excluded), 39 of them UK:

| | |
|---|---|
| UK AOV | £54.51 |
| Single-item orders | 86% |
| UK under £20 | 5% |
| UK £20–£69 | 87% |
| **UK £45–£69** | **77%** |

A bar aimed at £20 would be invisible to 95% of customers. 77% sit £1–£25 short of free
Tracked 24, and 28 of 39 are exactly £50 or £60 — one jeans or one crewneck. With 86% of orders
being a single item, "add a second thing" is the lever, and £6 socks are the obvious add.
George confirmed Tracked 24 costs **80p** more than Tracked 48, so ~£10 of extra product for 80p
of absorbed postage. Clearly worth promoting.

**The honesty fix that had to come first.** The announcement bar said `FREE UK SHIPPING *` (with
an asterisk that pointed at no footnote) and CHAIN OF CUSTODY step 02 said "Free UK shipping on
every order". Both false below £20 — two orders in the sample paid exactly that £3. Corrected to
state the threshold. You cannot run a progress bar toward a benefit you claim is unconditional.

**A correction to an earlier claim of mine.** During the dispatch-cutoff work I reported custody
step 01 updated to the 18:00 wording. It never took effect: the block bodies are **persisted in
`templates/product.json`**, so changing the schema default did nothing and the PDP still read
"Dispatch within 24 hours". Fixed properly this time by editing the stored blocks. Schema
defaults only govern *new* instances — a lesson that applies to every block-based section.

**Design.** A readout, not a widget: `> £10.00 to free Tracked 24`, a segmented meter (hard-edged
repeating stops, since gradients are banned), a marker at the tier-1 position, and tier labels
that tick when met. No countdown, no urgency, no red.

**Correctness details:**
- Basis is `cart.total_price`, i.e. **after discounts** — the same basis Shopify's `TOTAL_PRICE`
  condition uses. The pre-discount subtotal would promise carriage that checkout withdraws.
- Fill is measured against the **top** tier so the bar keeps moving after tier 1 clears.
- Fill floors and holds at 99% until a tier is genuinely met. Rounding showed a full bar next to
  "£0.01 to go".
- Hidden entirely when the cart is empty, and outside the configured country.
- Thresholds are settings, with a note in the schema to keep them in step with the rate card.

**Same Liquid trap, second time.** `label | replace: '[amount]', crk_remaining | money` applies
`money` to the *result of the replace*, so the message rendered as bare `£10.00` with the label
gone — exactly the fault the FILED date hit. The amount must be formatted into its own variable
first. I had already recorded this and still wrote it.

Verified across boundaries on the client path: £5 · £19.99 · £20 · £60 · £69.99 · £70 · £120 all
produce the right message, fill, aria-valuenow and tier ticks. The £120 and empty-cart states
were confirmed server-side; the £60 server-render is pending a Shopify `/cart/add.js` rate limit
(429) from repeated test adds.

**Harness note:** fetching `crooks-cart-progress.js` from the CDN without its `?v=` returned a
stale build and the boundary test "failed" against code that no longer existed. Test the source
of truth, or carry the version.

## Quick-add was a black box — a regression from replacing the product template

Horizon's quick-add fetches the product page and extracts specific nodes:
`[data-product-grid-content]`, `.product-details`, `product-form-component`,
`variant-picker`, `product-price` (`assets/product-card.js:102, 208-211`).

`sections/crooks-exhibit-record.liquid` emits **none of them** — grep returns 0 for all five.
So the fetch succeeded, the extraction found nothing, and the dialog opened empty at
390×844: a full-screen near-black box. The colours were fine; there was simply no content.

This was caused by swapping `templates/product.json` to the custom record and never checking
what else depended on Horizon's product markup. `quick_add` (default **true**) and
`mobile_quick_add` are now set to `false` explicitly in `config/settings_data.json` — they were
absent from `current`, so they were running on schema defaults. Cards now link to the product
page, which works and is on-brand.

Rebuilding quick-add in the register's own voice is possible later; a broken control is worse
than none in the meantime.

## Search page branded

`templates/search.json` now renders the register (Horizon's preserved as
`search.horizon.json`). The section takes `search.results` when
`template.name == 'search'`, skips non-product results — search can return articles and pages,
which have none of the fields a card needs — and counts products rather than "results".

Verified: `tee` → 5 cards "Search: tee"; `jeans` → 4; a nonsense query → 0 with the empty state
shown; no query → "Search" with the empty state. No overflow at 390.

## Carriage bar moved out of the cart

Behind the cart page it was invisible to anyone browsing or checking out through the wallet
buttons — which, given Shop Pay express, is exactly the customer most likely to skip the cart.
It now renders on **home, collection, product, search and cart**, and hides itself entirely when
the cart is empty, so it only ever appears as genuine progress.

Confirmed: with an empty cart the bar is absent from all four surfaces; with £60 in the bag it
reads `£10.00 to free Tracked 24` on every one — including the £6 socks product page, which is
the moment it is actually worth something.

**Server-side render confirmed** at £60 (`fill=85%`), closing the gap left when Shopify
rate-limited the earlier test.

**Note on probing:** repeated `/cart/add.js` calls triggered 429s and then Shopify's
"Verifying your connection" bot challenge, which silently returned a challenge page instead of
the cart. One conclusion was drawn from that page before I noticed. Check for the challenge
string before trusting any fetched HTML.

## Catalogue: a header control, not a menu item

First attempt added CATALOGUE to the main nav menu. Wrong: the nav is merchant data shared with
the live theme, and it put a second full product listing beside SHOP. Reverted — the menu is
back to SHOP / TRACKING / Contact with the original item IDs intact, so nothing was lost.

It is now a link in `.crk-header__actions`, first, to the left of SEARCH, behind three settings
(`show_catalogue`, `catalogue_label`, `catalogue_url`).

**Two things this broke, both caught by measuring:**

1. **Shopify rejects a `shopify://` default on a `url` setting** — "default must be a string or
   datasource access path". The push reported errors and the link silently did not render. The
   default is removed and the value is stored on the header group instead.

2. **The extra control ate the logo.** `.crk-header__logo` carried `min-width: 0` so the
   wordmark absorbs whatever space is left. With five controls in the actions row that left it
   **4px wide at 390 and 0px at 360** — the mark vanished on every common phone, the same mark
   that had to be fixed for dark mode earlier the same day. The actions row now wraps below
   430px instead of squeezing, and the logo has a 44px floor.

| Width | logo | bar | overflow |
|---|---|---|---|
| 430 | 44×29 | 60px, one row | none |
| 390 | 48×32 | 110px, two rows | none |
| 360 | 48×32 | 158px | none |
| 320 | 48×32 | 158px | none |
| 195 | 48×32 | 206px | none |

Zero sub-44px targets at every width.

**Lesson:** adding one control to a flex row that contains a `min-width: 0` element does not
overflow — it silently consumes that element. Overflow tests pass while something disappears.
Measure the thing that absorbs the slack, not just `scrollWidth`.

## Destructive error: menuUpdate wiped SHOP's sub-menu

`menuUpdate` replaces the **entire item tree**, including children. Every menu query I ran
fetched only `items { id title url type resourceId }` — never the nested `items` — so when
adding TRACKING, and again when adding and reverting CATALOGUE, the child items under SHOP were
sent back as absent and deleted.

`sections/crooks-header.liquid` renders `link.links` as `.crk-drawer__sub`, so those children
were the collection list in the pull-out menu. Losing them emptied it down to three top-level
entries, which is what George noticed.

**Not recoverable.** Navigation is store data, not a theme file, so none of the fallback themes
contain it and Shopify exposes no menu history through the API. The sub-menu below has been
**reconstructed**, not restored, and the order and labels are a guess that needs confirming:

    SHOP → ALL · NEW · TEES · DENIM · SWEATS · TRACKSUITS · ACCESSORIES

**Rule:** any `menuUpdate` must first read the full tree — `items { id title type url resourceId
items { ... items { ... } } }` — and send it back intact. Shopify's menus nest three levels.
This belongs with the `*-group.json` rule: read the whole of a merchant-owned structure before
writing any part of it.

## Terms + Questions pages, and the one source of truth for trading facts

Modelled on Mertra's `/pages/terms` (their site is password-gated between drops; read from the
Wayback copy): one plain-English page covering shipping rates, order processing, refunds and a
bot clause, with the legal documents demoted to a single link at the bottom.

**Shopify has no `policy` template.** The template list is 404, article, blog, cart, collection,
index, list-collections, page, password, product, search, metaobject, plus a few `.liquid`
specials. `/policies/*` renders Shopify's own `.shopify-policy__container` inside `theme.liquid`
and cannot take sections. That is *why* the page exists rather than a styling preference — the
legal pages can only ever be skinned with CSS, and they were rendering on Horizon's cream
`rgb(244 241 234)` between the terminal header and footer.

The skin needs `--crk-*` to resolve inside markup we do not own, so the token block's selector
now also matches `main:has(> .shopify-policy__container)` — the container's parent, so the
tokens inherit down. Two selectors changed, nothing duplicated.

### Canonical trading facts

These are stated in the PDP custody blocks, the four legal policies, `/pages/terms` and
`/pages/faq`. They have already drifted twice. Change them **together** or not at all.

| Fact | Value |
|---|---|
| Free UK shipping | over £20 |
| Free Tracked 24 | over £70 |
| UK delivery, once dispatched | 1–2 working days |
| International delivery | 7–14 working days |
| Return window | 14 days from delivery to notify, 14 more to post back |
| Return condition | unworn, unwashed, tags attached |
| Return postage | paid by the customer unless faulty or wrongly sent |
| Return address | Oairo UK Office, Bourne End Business Park, Bourne End, Bucks, SL8 5AS |
| Refund speed | 5–7 days to the original payment method |
| Transit damage | report within 48 hours |
| Lost parcel | report within 14 days; courier investigation up to 10 working days |
| Contact | crooksldn@gmail.com (the store's own address) / @crooksldn |

`info@crooksldn.com` was on the footer and the PDP custody step and is **not** the store's
contact address — `shop.email` and `shop.contactEmail` are both `crooksldn@gmail.com`. Returns
requests sent to `info@` may have gone nowhere. Both corrected.

### Dispatch: measured, not assumed

Fulfilment timestamps for the last 50 shipped orders:

| | |
|---|---|
| Fulfilments by weekday | Mon 3 · Tue 0 · Wed 10 · Thu 11 · Fri 13 · **Sat 13** · Sun 0 |
| Orders placed before 18:00 that shipped the same calendar day | **17 of 35 (49%)** |
| Median order → fulfilment | 23.7 h (p25 3.3 h, p75 52.7 h) |
| Within 24 h / 48 h | 26 of 50 / 35 of 50 |

Two conclusions. **Saturday is a real dispatch day** — the shipping policy's "orders are not
shipped on weekends" is the document that is wrong, not the PDP. And **the same-day claim holds
about half the time**: fulfilments come in batches every few days (ten orders spanning 8–12
August were all fulfilled within six minutes of each other on the 12th), so a customer ordering
at 17:00 on a Sunday, Monday or Tuesday is unlikely to see their parcel move that day.

New copy therefore says "dispatched the same day where possible, Monday to Saturday" and "allow
up to two working days after a drop", which is true. The PDP custody step still makes the
unqualified claim and has been left alone — that is a business decision, not a bug.

### Left open deliberately

- **Faults window.** The refund policy says 14 days; the Consumer Rights Act gives 30 for the
  short-term right to reject. The new pages state no deadline at all rather than publish a term
  narrower than the law or contradict the policy.
- **Restocks.** No answer exists, so there is no restock question on the FAQ.
- **Terms of service** is still Shopify boilerplate: `[LINK TO REFUND POLICY]` twice,
  `[LINK TO PRIVACY POLICY]`, `[Crooksldn LTD]`, `[Crooksldn@gmail.com]`, `[TW200JW]`, and it
  names the operator "Crooks Store".
- **Kiwi Sizing.** `templates/product.horizon.json` carries an app block for
  `kiwi-size-chart-recommender`. The crooks product template does not, so if that app is still
  subscribed it is being paid for and rendering nowhere.

### Section groups reject settings their schema has not yet seen

`sections/footer-group.json` and `sections/crooks-footer-log.liquid` were pushed together, the
group carrying the new `label_6` / `url_6`. Shopify **silently stripped both keys** — the group
was validated against the schema the theme had at the start of the push. Pulling the file back
proved it. Push the section first, then the group.

### Main menu now carries QUESTIONS and TERMS

    SHOP → ALL · NEW · TEES · DENIM · SWEATS · TRACKSUITS · ACCESSORIES
    TRACKING · QUESTIONS · TERMS · Contact

Added by reading the full nested tree first and sending every existing item back with its own
`id` — the seven children under SHOP survived, verified in the rendered drawer. New items were
sent without an `id` and with `type: PAGE` + `resourceId` only; Shopify derives the url. Menus
are store data, so this is not in any commit.

### Owner override of KEEP.md §6: `04 RELEASED` → `04 Delivered`

`audit/KEEP.md` §6 protects the chain-of-custody copy — *"the label needs the
word 'shipping' appended (BACKLOG #13); the copy inside must not be touched."*
The step label was changed anyway, on George's explicit instruction after the
conflict was put to him: *"change the released to delivered i even believe that
it would look better."*

Rationale accepted: `RELEASED` is the one step in the timeline a customer has to
decode, and it sits at the point where they are checking whether the parcel has
arrived. The other three steps and every line of body copy are untouched.

Changed in three places, because the label lives in all of them:
`templates/product.json` (what renders), the section preset in
`sections/crooks-exhibit-record.liquid` (so a fresh instance matches), and
`templates/product.crooks.json` (the unused legacy template).

The section preset also still carried `info@crooksldn.com` — the address proven
dead and corrected on the live template earlier. Fixed at the same time, so
adding a fresh Exhibit Record can no longer reintroduce it.

This is a deliberate decision, not drift. The next audit should not re-flag it.

---

## 2026-08-20 — Change-of-mind returns: postage is the customer's

George: *"any change of mind returns postage is handled by the customer, not by
us. so that is size change, returns, refund, exchanges etc. anything that is due
to our error is covered by us."*

One fork was put to him before editing, because the two readings are materially
different money. He answered: *"they pay to return to us, free to go back out to
them."*

So the settled position is:

| Reason | Return leg | Replacement going out |
|---|---|---|
| Change of mind, wrong size, swap | **customer** | **us** (no fee for the swap either) |
| Faulty, damaged, or we sent the wrong thing | **us** | **us** |

Substantively this is what the store already did — the live Refund policy has
said *"return postage is covered by the customer"* since before the redesign.
What changed is the **framing**: `UK size swaps are free` was the headline
claim, and a shopper reads that as free returns. Every surface now leads with
the customer's obligation and states the exception.

Edited:

- `templates/page.terms.json` — clauses Returns (c3), Size swaps (c4), Faults
  (c5), Refunds (c6); `revised` 13.08.2026 → 20.08.2026
- `templates/page.faq.json` — q8 exchanges, q9 returns, q10 refunds, q11 faults
- `templates/product.json` + the section preset in
  `sections/crooks-exhibit-record.liquid` — custody step 04
- `templates/product.crooks.json` — the unused legacy template carried the same
  returns line

Two stale things were swept while in the same sentences, both the class of bug
the 2026-08-18 entry describes (a preset default outliving the corrected
persisted value): `info@crooksldn.com` in the legacy custody step and in the
`crooks-footer-log` preset. The address is now gone from the theme entirely.
What renders in the footer was already correct.

### The live Refund policy was NOT changed

George approved updating it directly. The attempt failed — this connection
lacks the `write_legal_policies` scope:

    Access denied for shopPolicyUpdate field.
    Required access: `write_legal_policies` access scope.

Re-read afterwards to confirm the mutation wrote nothing. It did not; the live
body is byte-identical to before. The corrected text was handed over for
pasting into Settings → Policies instead.

### Two things flagged, not changed

1. **`templates/product.crooks.json` is a landmine.** Unused today (no product
   carries the `crooks` suffix), but it still claims *"Free UK shipping on every
   order"* — false, it is over £20 — and *"Dispatch within 24 hours"*, which
   contradicts the 18:00 cutoff. If anyone ever assigns that suffix those go
   out. Out of scope for this change; should be either corrected or deleted.
2. **UK Consumer Contracts Regulations 2013.** For a change-of-mind cancellation
   the trader must refund the *original outbound* delivery charge at the basic
   rate; only the return leg can be pushed to the customer. Both the Terms page
   and the FAQ say *"Original shipping charges are not refunded unless the item
   was faulty or wrongly sent."* That sentence predates this change and was left
   alone, but it is the one line here that a trading-standards complaint would
   land on. George's call, and worth an actual solicitor's eye rather than mine.

### 2026-08-20 (later) — `templates/product.crooks.json` corrected

George: *"fix"*, on the landmine flagged in the entry above.

The file was older than the flagged lines suggested. Everything in it predated
the jargon cleanup and the shipping-copy pass:

| | was | now |
|---|---|---|
| custody 01 | "Dispatch within 24 hours" | the real 18:00 cutoff, Mon–Sat |
| custody 02 | **"Free UK shipping on every order"** — false | over £20, Tracked 24 over £70 |
| custody labels | `LOGGED` / `DISPATCHED` / `IN TRANSIT` / `DELIVERED` | sentence case, matching the live template |
| `collection` | `frontpage` (23 products) | `all` (14) — this is the denominator in `PRODUCT 09 / 14` |
| `back_label` | `← RETURN TO LOG` | `← Catalogue` |
| `exhibit_word` | `EXHIBIT` | `PRODUCT` |
| `photo_label` / `gallery_label` | shouty | sentence case |
| `show_wash` | set — **the setting no longer exists in the schema** | removed |
| `case_word`, `show_texture`, `related_heading` | absent | present |
| carriage bar | absent | added, so the template is a usable twin |

Verified by diffing the parsed JSON against `product.json`: order, main settings,
all four custody blocks and the carriage section now compare equal, and neither
template carries a setting id the schema does not declare.

**The deeper problem is not fixed.** This file is a redundant duplicate —
`product.json` already renders `crooks-exhibit-record` for every product, and no
product carries the `crooks` suffix. Its only failure mode is drift, and
correcting a duplicate is precisely what guarantees the next drift: every copy
change now has to be made in two places or this file goes stale again, exactly
as it did here. Deleting it removes the class of bug. Left in place because the
instruction was "fix", and deletion is the owner's call under §0.

---

## 2026-08-20 — Nothing is chosen on the shopper's behalf

George: *"can you stop size being autoselected when first clicking a product,
and also if item is in a bundle, stop it from autoselecting the same size"*

Two separate guesses, same principle: a pre-pressed button is indistinguishable
from a choice the shopper made, so the wrong size gets bought and nobody can
tell whose mistake it was. That got more expensive the same day — change-of-mind
return postage is now the customer's.

### 1. The PDP no longer picks a size

`sections/crooks-exhibit-record.liquid` opened with
`product.selected_or_first_available_variant`, which picks the first in-stock
variant. Now:

    assign crk_var = product.selected_variant
    if product.variants.size == 1
      assign crk_var = product.variants.first
    endif

`selected_variant` is Shopify's deep-link accessor — nil unless `?variant=` is
in the URL ([confirmed against the Support product variants doc]). So shared
links, the `<noscript>` size links and the Back button all still land
pre-selected; only a cold landing is blank. A product with exactly one variant
is not a choice, so it stays selected.

**No JS change was needed for this.** `crooks-record.js` reads the selection
back out of the buttons' `data-selected` on init and already had a complete
`!complete` state — `Select a size`, disabled button, wallet hidden, notify
panel suppressed. Rendering every button unselected is the whole fix.

Five knock-on renders had to follow, because each was written assuming a
variant always existed:

| | was | now |
|---|---|---|
| price | `crk_var.price` → blank | falls back to `product.price`, formatted into a variable first |
| stock line `data-out` | `true` when nil → styled sold-out | `true` only for a chosen size that is gone |
| delivery line | hidden when nil | hidden only for a chosen size that is gone |
| wallet row | always rendered | hidden until a size is chosen |
| notify panel | `{% if crk_var.available %} hidden` → nil is falsy, so **the restock form showed on every cold landing** | shown only for a chosen size that is gone |

### 2. The set toggle no longer matches the first size

`assets/crooks-set.js` carried `if (!touched && mainSize) partnerSize = mainSize;`
in the render hook and again in the checkbox handler. Both gone, along with the
`touched` flag they existed to guard.

Removing the guess created a state that did not exist before — ticked, main size
chosen, partner size not — and it needed two things:

- a third panel state. Previously `paint()` was binary: sellable, or the
  sold-out line. With no partner size the sold-out branch rendered
  *"sold out in  — pick another size"* against an empty size. Now the panel
  prompts in black rather than reporting a fault in red.
- **the button must not stay on ADD TO BAG.** `current()` returns null, the hook
  used to `return` and leave the record's own state, and the record's state for
  a chosen main size is a live ADD TO BAG for the single item. Ticking the box
  and pressing it would have bought one thing to someone who asked for two.
  The button now states what is missing and is disabled.

New setting `set_pick_text` (default `Pick a [partner] size`), passed to JS as
`data-crk-set-pick` with `[partner]` already substituted in Liquid.

### Verified, not assumed

A fixture mirroring the new markup (5 sizes, L sold out, S low, a 25-variant
bundle with XL gone) driven in headless Chromium against the real
`crooks-record.js` and `crooks-set.js`: **41 assertions, 41 passing.** Covers the
cold landing, picking a size, picking a sold-out size, ticking the set, picking a
partner size, changing the main size afterwards, a sold-out partner size, and
unticking.

The run caught a bug I had just written: removing `var touched` left the
assignment `touched = true` in the click handler, and under `'use strict'` that
throws a ReferenceError, so **every partner-size click died silently.** Nine
assertions failed on it. It would not have shown up in any static check —
`node --check` passes, the file parses, the listener is attached, and the throw
only happens on click. That is the second time this session a test has paid for
itself; it is the argument for building the fixture rather than reasoning it
through.

### Left alone

Ticked + partner size chosen + that pair unavailable still leaves ADD TO BAG
live for the single item. Same class of silent-intent bug as the one fixed
above, but it predates this change and is not what was asked. Worth fixing next.

---

## 2026-08-20 — "pushed" meant git, not Shopify

George: *"nothing has actually changed?"* He was right, and the fault was mine.

Four commits went to the branch today and I reported each as "pushed". The theme
had not been touched since 18 August. Git and Shopify are two different
destinations and I conflated them in every status line I wrote.

Proof, read off the theme before deploying:

| file | local | on theme | deployed |
|---|---|---|---|
| `assets/crooks-set.js` | 6,204 | 5,551 | 18 Aug |
| `assets/crooks-record.js` | 22,170 | 22,031 | 18 Aug |
| `templates/page.terms.json` | 5,450 | 5,262 | 13 Aug |

### The near-miss that mattered more

Checking `updatedAt` on every file before overwriting caught drift going the
other way. Two template files had been edited in the **theme editor** since the
last commit, and the repo knew nothing about it:

- `templates/product.json` — 19 Aug 22:46
- `templates/product.crooks.json` — 20 Aug 11:32

Both had gained real sizing copy:

    "measure_caption_cm": "True to size — waist, chest and leg measurements
                           are taken around the garment. All measurements in
                           centimetres."

A straight `shopify theme push` of the local tree would have **deleted it**.
Merged both by hand instead — deployed content plus this session's custody edit —
and verified after upload that the captions and the postage line are both
present.

This is structural, not bad luck. `templates/*.json` and `config/settings_data.json`
are written by the theme editor, so the repo is not their source of truth; the
theme is. Any push of a JSON template must read the deployed copy first.
`--nodelete` was used throughout, and only named files were pushed — never the
whole tree.

### Deployment, written down because it was not

- The container had lost both the CLI (`node_modules` empty after a restart) and
  its credentials. `npm install` restores `@shopify/cli` 4.7.0; auth came back
  with it.
- `package.json` already carries the right command:
  `npm run push` → `--store=5wn03t-nm.myshopify.com --theme=202053779799`.
- Pushed in two stages, code before templates, per the push-order rule.
- Verified by MD5, not by the CLI's success banner: all seven code and page
  files match the local checksums byte for byte; the two product templates were
  read back in full because Shopify reformats JSON.

The live theme is `#202044309847`, and it is named **"CROOKSLDN — Dev"**. The
staging theme is `#202053779799`, named "CROOKSLDN — Staging". A tired person
reading those two names will pick the wrong one. Renaming the live theme to
something that says *live* is a five-second job worth doing.

---

## 2026-08-20 — Audit A1: the buy path

Three findings from the twenty-journey audit, all on the same code path.

**Already dead before starting.** Three findings the 20 Aug deploy had killed
and which should not be re-fixed: XS silently preselected on every apparel PDP
(7 journeys), the set's silent size-mirroring (04), and the FAQ's "Start your
return here" pointing at the terms page rather than the portal (09).

### CHECKOUT NOW charged the £6 shopper £12 (worst moment #2)

`sNow.addEventListener('click', addToBag('checkout'))` — an unconditional add.
ADD TO BAG then CHECKOUT NOW put the item in twice. Persona 14 reached the till
at £12 for £6 socks and left.

CHECKOUT NOW is an express lane, not a second ADD TO BAG. It now reads `/cart.js`
first and only adds what the cart is missing. Server truth rather than page
state, so it also holds for an item added on an earlier visit. On a cart read
failure it falls through to the old behaviour, because `/cart/add.js` is almost
certainly unreachable too and failing loudly beats dropping someone into an
empty checkout.

### Silent add-to-bag (7 journeys, direct cause of three double-adds)

Two separate gaps:

- **No acknowledgement of the tap.** Persona 14's first tap did nothing visible
  for 30 seconds on slow 4G and nearly ended the session there. The tapped
  control now changes to `Adding…` and disables synchronously, before any
  network work starts. New setting `label_adding`.
- **The confirmation was below the fold.** `say()` writes under the main button;
  when the tap came from the sticky bar that is off-screen, and the header's BAG
  count has scrolled away. The sticky bar's own meta line now flashes the
  confirmation. Not aria-live — the line under the button already announces, and
  two live regions would say it twice.

### CHECKOUT NOW looked live beside SOLD OUT (01, 06)

It was correctly `disabled`; it just did not look it. `.crk-btn--now` paints
`background: none`, so the shared `:disabled` rule was swapping a background
that is not there and only the text dimmed. Added `opacity: 0.5`.

### Two bugs the tests caught

Both mine, both introduced by this change, neither findable statically:

1. `settle()` re-renders after the request settles, and `render()` rewrites the
   sticky meta line — so the confirmation was being wiped a microtask after it
   was set. The flash is now queued and applied after `settle()`.
2. Navigating to checkout still ran `settle()` on the page being left, and
   `render()` calls `replaceState` — which was building the URL as
   `u.pathname + u.search`, **dropping the fragment**. The test caught the hash
   disappearing. Fixed by not re-rendering once committed to leaving, and by
   preserving `u.hash`. That second one is a latent bug well beyond this change:
   any in-page anchor died on the next size change.

### Verified

16 new assertions on a fixture with a stubbed cart, counting real `/cart/add.js`
calls: pending label, single add, confirmation placement, stale-confirmation
clearing, no second add when the item is already held, exactly one add when it
is not, and all three controls dead on a sold-out size. Plus the existing 41
no-autoselect assertions re-run green. Deployed to 202053779799 and verified by
checksum.

---

## 2026-08-20 — Audit A2/A3: the Crack the Cuffs popup

### A3 — "REVEAL MY CODE does nothing" is not what is happening

The audit calls this worst moment #1 and says *"the shop takes two pieces of
contact data and gives nothing back."* Inspected the Base44 app directly
(`Crack the Cuffs`, appId `6a2967eacd8fe987405353d2`). The finding is wrong in
its diagnosis, and wrong in a way that matters.

**The backend works.** `base44/functions/issueDiscount/entry.ts` mints codes and
has been doing so all along. Most recent real lead:
`baily.coggin@yahoo.com` / `ESCP-WK72VV` / 15% at **13:19 UTC on 18 August** —
the day of the audit — with `code_failed: false`. Every `code_failed: true`
record in the table is a `cracktest*@crooksldn.com` or `test*@` address from
20 July or earlier, i.e. development.

**No path in the client is silent.** It handles success, `already_played`,
`code_failed` and a catch. `LOADING` renders a spinner reading "Forging your
code…". `RewardDisplay`'s `code_failed` branch renders a "Check Your Email"
fallback. There is no branch that shows nothing.

**And nothing was captured.** A `Lead` is written even when code generation
fails — that is the whole point of the `code_failed` column. There is **no Lead
from the audit's evening session**; the last one is 13:19 that afternoon. So the
function never completed during the audit, and the two pieces of contact data
the audit says were taken were not taken either. Less bad ethically than the
audit states. Equally bad commercially.

The failure is therefore upstream of the backend, in the call itself. Prime
suspect: `base44.functions.invoke` failing inside a **cross-site iframe** —
third-party cookie and storage partitioning would break an authenticated SDK
call embedded in crooksldn.com while leaving it working when the app is opened
first-party at crack-cuff-codes.base44.app. That fits every observation,
including why real customers still got codes.

Not reproducible from here: Chromium in this container has no external network
(curl does, via the proxy). Settling it needs one live play with the network tab
open, or permission to invoke the function directly — which mints a real
discount code and creates a real customer, so it is not mine to do unasked.

### A2 — what the overlay actually gets wrong

Twelve of twenty journeys complained about this popup. The game is not the
problem (11: *"genuinely fun"*). Four defects, all in
`snippets/crack-the-cuffs.liquid`, all fixed:

1. **It lied about being a dialog.** `role="dialog" aria-modal="true"` with no
   focus move, no trap, no restore, and the close X *after* the iframe in DOM
   order — so a keyboard or screen-reader user tabbed straight into a
   cross-origin iframe with no announced way out (15, 16). Close button is now
   first in the DOM, focus moves to it, Tab cycles between it and the frame,
   Escape closes, focus returns to whatever had it, and everything else in
   `<body>` is `aria-hidden` while the dialog is up.
2. **The one attempt was spent on opening.** `markSeen()` fired at open, so
   anyone who shut it reflexively lost their only go for good (18). Now spent
   only after `SEEN_AFTER_MS` (8s) on screen, or when the app itself says the
   visitor is done.
3. **An empty dimmed box for 4–8 seconds** (13, 19) — the overlay was attached
   before the iframe had loaded. Now waits for the frame's `load`, with a 6s
   timeout so a slow app still gets shown.
4. **It stacked on the cookie banner** (02, 18, 20). Now waits for a consent
   banner to be answered, polling up to 30s before giving up and showing anyway.

Also gave landscape its own layout — 460px frame, scrollable overlay, smaller
close target — because at ~300px of height the controls sat below the fold with
nothing to scroll (13).

Verified with 16 assertions in headless Chromium against the real snippet (the
script is extracted from the `.liquid` at test time so the test cannot drift
from what ships): banner gating, deferred show with the frame confirmed loaded,
DOM order, focus move, Tab and Shift+Tab cycling, background `aria-hidden`,
Escape, focus restore, scroll-lock release, and the attempt surviving a fast
close.

Two false starts worth recording: a `sed`-style patch left an unclosed `try`, so
the test file was a syntax error and silently never ran — the popup still opened,
which made it look like a product bug rather than a test bug. And a fixed
`await wait(3000)` raced the iframe load, because Chromium's virtual time
advances past timers while real network fetches still take wall-clock time.
Polling for the overlay fixed it. Both cost a cycle each; neither was in the
product.

---

## 2026-08-20 — Audit A4: cards that said AVAILABLE with three sizes gone

Personas 01 and 06 both hit V2 BAGGIES, found three of five sizes gone only on
the PDP, and left. Persona 06 on the card label: *"conveys zero information and
reads as a broken promise."*

`product.available` is true while a single variant remains, so the card had no
way to say "yes, but probably not in your size". Added a fourth status state,
below SOLD OUT and LOW STOCK, above AVAILABLE. New setting `sizes_left_label`,
default `[n] OF [m] SIZES LEFT`.

Two things it deliberately does not do:

- **Counts size VALUES, not variants.** A tee is size x colour, so M/BLACK
  selling out does not mean M has gone. Counting variants would have reported
  nine of ten on a product where every size is still buyable.
- **Only for an option actually named like a size.** The socks' option is
  "Quantity" and the duffle's has one value; both keep AVAILABLE rather than
  being told they have options left.

This is an addition to the register format, not a replacement — KEEP.md §7 and
the round-2 addendum both protect that slot, and the same mistake (a state
replacing availability rather than joining it) was already made once with the
FILED date.

### Verified against the deployed page, not a fixture

Computed the truth from the Admin API first — exactly one product in `all`
should change — then fetched the staging collection page and read the rendered
labels back:

    CHARCOAL CELLBLOCK CREWNECK   AVAILABLE
    ...
    V2 BAGGIES                    2 OF 5 SIZES LEFT
    BLACK/BLUE MOTIONTEC SOCKS    AVAILABLE
    LARGE DUFFLE BAG              AVAILABLE

CRXST★RZ T-SHIRT is the useful case: its Size is option 2, not 1, and it still
reads correctly.

Fetching a preview theme needs `-L` with a cookie jar; `?preview_theme_id=` 302s
and sets a cookie, so a plain curl returns 0 bytes.

**Noticed while verifying:** the storefront now renders **12** products, not 14.
3 CLIVES TEE and BROADCAST TEE were archived at some point today.

---

## 2026-08-20 — Audit A7: the register forgets, and miscounts

Two findings, one initialiser.

### The count ignored the filter

*"'14 ITEMS' header never updates when filters narrow the register"* (19 +
homepage agent). The number itself was never wrong — it counts the products
actually rendered, and reads 12 today because two tees were archived this
morning. It simply took no notice of filtering, so DENIM showed two cards under
a header claiming twelve.

The number is now its own element with `data-crk-count`, and `apply()` already
had the figure — it was computing `shown` to decide whether to reveal the empty
state and then throwing it away. The label stays in Liquid so it does not have
to exist twice.

### The filter reset on Back

*"punishes exactly the comparison behaviour the register invites"* (10, 19 +
Phase 1). Filter to DENIM, open a piece, press Back, and everything is showing
again.

The category now lives in the URL as `?cat=`. `replaceState`, not `pushState`:
the filter is a view of one page rather than a place, so it should not cost a
Back press every time it changes — and the URL the shopper leaves from already
carries the filter, which is the whole point. The fragment is preserved, because
dropping it is precisely how in-page anchors died in `crooks-record.js` earlier
today.

`cat` rather than `filter` deliberately: Shopify's own faceted filtering uses
`filter.*` parameters, and a bare `filter` sitting next to them is asking for a
collision later.

An unknown `?cat=` value is ignored rather than hiding everything — a stale or
hand-edited link shows the full register instead of an apparently empty shop.

### Verified

22 assertions across three separate page loads — clean, `?cat=DENIM`, and
`?cat=BOGUS` — covering the count following the filter, the URL being written
and cleared, ALL clearing the param rather than storing "ALL", the hash
surviving, restore-on-load, and an unknown category degrading safely. Then
confirmed on the deployed page: header reads `12 ITEMS` against 12 rendered
cards, with filters ALL / T-SHIRT / DENIM / SWEATS / ACCESSORIES.
