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
