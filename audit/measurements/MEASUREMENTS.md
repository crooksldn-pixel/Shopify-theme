# MEASUREMENTS.md — real size data loaded from the factory charts

2026-08-19. Seven `crooks.measurements` metafields written via Admin API
(`metafieldsSet`, zero errors, values read back verified). All values follow
the component's stated convention — **GARMENT LAID FLAT, in cm** —
circumferences halved, inches ×2.54, rounded to 0.5cm. The PDP's cm/in toggle
parses these directly (verified against `crooks-record.js` conversion code).

## What each product now shows

| Product | Rows | Source chart |
|---|---|---|
| GREY + BLUE WASH OG JEANS | waist 38–48.5 · inseam 73.5–81.5 · hem 23–28 | "SIZE CHART" (waist 30–38in nominal, inseam 29–32in, leg 9–11in) — **replaces the fake +2cm placeholder** |
| BLUE + GREY WASH JORTS | waist 38–48 · hip 51–61 · thigh 35–40 · hem 29.5–34.5 · length 54.5–62.5 | ZY124 factory tech pack (cm circumferences, halved) |
| CHARCOAL CELLBLOCK SHORTS | length 49.5–59.5 · hem 29–39.5 | A/B/C diagram chart (inches) |
| CHARCOAL CELLBLOCK CREWNECK | chest 54.5–65 · length 65.5–73 · shoulder 47–57 · sleeve 62–67.5 | crewneck factory tech pack (inches; chest halved from circumference) — **fills the gap that cost the £50 gift-buyer sale** |
| CRXST★RZ T-SHIRT | chest 50–59.5 · length 67.5–76 · shoulder 49.5–59.5 | CRX chart (explicit inches; chest halved) — **first data ever on this product** |
| MONEY CLIVE TEE + archived BROADCAST / 3 CLIVES tees | same CRX table | owner confirmed one chart covers all tees — **replaces the tee placeholder (chest 51–63) on all three** |

## Honesty decisions (what was deliberately left out)

- **Jeans waist** is derived from nominal denim sizes (30–38in) on the
  standard assumption nominal = waistband circumference. If the garments run
  vanity-sized, correct the row — the owner can verify with one tape measure.
- **Cellblock shorts waist omitted**: elastic drawstring — the chart's
  28–36in is a to-fit body range, which cannot be printed under a
  "garment laid flat" caption without lying. If wanted, it belongs in copy or
  a size-name change, not this table.
- **Crewneck cuff omitted**: the tech pack's 7.5–9.5in is ambiguous between
  circumference and flat width; unverifiable claims don't ship.
- **Grey jorts inherit the blue jorts' tech pack** (ZY124 photos show blue;
  same style/cut per metafields). If the grey is a different pattern, say so
  and it gets its own table.
- **V2 BAGGIES now carries the jeans chart** (waist/inseam/hem) — owner
  confirmed the baggies match those laid-flat measurements. The last invented
  placeholder in the store is gone. Note: jeans and baggies now intentionally
  share numbers by owner decision (previously they shared them by
  placeholder accident — the audit's original flag).
  The pink hoodie chart (with the height guide) awaits a product name, and
  the Arc'teryx body chart was **refused** for the windbreaker: another
  brand's body-fit table is not this garment's measurements.

## Verification note

Store-side values verified by API read-back. Visual check on the staging PDP
(accordion render + cm/in toggle) needs a fresh share-preview link — the old
one has expired. The live theme does not render these metafields, so nothing
appears on crooksldn.com until the redesign publishes.

---

# REVISION 2 — true to size (2026-08-19, owner request)

The laid-flat convention above is SUPERSEDED. Owner verdict: "15.9in as a
waist measurement is hard to understand" — shoppers compare against garments
they own, so charts now follow industry standard.

## The new convention
- **Girths are full circumference**: waist, hip, thigh, chest, leg opening.
  A shopper who wears a 32 jean reads "32". Flat tech-pack values were
  doubled; circumference sources kept as-is.
- **Lengths unchanged**: inseam, length, shoulder, sleeve.
- **Inch-first legibility**: every stored cm value is chosen so the IN toggle
  displays a clean industry number (stored cm = inches × 2.54 to 0.1mm; the
  theme's JS round-trips exactly). Verified for every cell.
- **Caption updated on the staging theme** (both product templates,
  `themeFilesUpsert`, settings `measure_caption_cm`/`measure_caption_in`):
  "True to size — waist, chest and leg measurements are taken around the
  garment. All measurements in centimetres/inches." The old "Garment laid
  flat" caption would have lied about the new numbers.

## What each product now shows (inches view)
- **Jeans + V2 Baggies**: waist 30/32/34/36/38 · inseam 29/30/30.5/31.5/32 ·
  leg opening 18–22 (flat 9–11in doubled).
- **Jorts**: waist 30–38 · hip 40–48 · thigh 27.5–31.5 · leg opening 23–27 ·
  length 21.5–24.6 (ZY124 cm circumferences, rounded ≤0.5cm to land on clean
  inches; length kept at true cm).
- **Cellblock shorts**: fits waist 28–36 (the tech pack's to-fit range — now
  publishable under the circumference convention) · length 19.5–23.5 · leg
  opening 23–31 (flat doubled).
- **Crewneck**: chest 43/45/47/49/51 (tech-pack circumference, as printed) ·
  length 25.7–28.7 · shoulder 18.5–22.5 · sleeve 24.5–26.5.
- **All four tees**: chest 39.5–47 (the CRX chart's own circumference
  column, verbatim) · length 26.5–30 · shoulder 19.5–23.5.

## Notes
- The crewneck and tee charts were ALREADY circumference-based as supplied —
  this revision publishes them as printed instead of halving them.
- Rounding: nudges of ≤0.5cm (garment tolerance) were applied to land jorts
  girths on whole inches; jeans waist follows nominal denim sizing as before.
- Template upsert diff: ONLY the two caption settings were added; every other
  template value byte-identical (custody blocks, settings, order untouched).
- Spotted while editing, not changed: product.json's custody step 4 says
  crooksldn@gmail.com while product.crooks.json says info@crooksldn.com —
  the RUN3 B2 email question, now visible inside the theme too.

## Email ruling (owner, 2026-08-19)
**crooksldn@gmail.com is the canonical address** — overrides RUN3 B2's
"standardise on info@crooksldn.com" recommendation. Theme sweep: footer, FAQ
and Terms already used the gmail; the single `info@crooksldn.com` (alternate
product template's custody step 4) has been corrected to the gmail via
themeFilesUpsert. The theme is now email-consistent. Remaining owner note
from the audit: the *legal policy pages* (store admin, not theme) also sign
with the gmail — nothing to change there now, only the old "Capitalised
variant on contact-information" cosmetic if desired.

## Hoodie chart (owner-supplied, 2026-08-31)

Chart supplied for the Convict hoodies (image via PRESTON): Length /
Width / Inner Arm Length in inches, laid flat, plus a Recommended Height
column. Written to `crooks.measurements` on all three active hoodies —
**PINK CONVICT HOODIE** (10993383801175, incl. its V1/V2 variants),
**BLACK CONVICT HOODIE** (10837208105303), **GREY CONVICT HOODIE**
(10636762841431). None had a measurements metafield before; the size-guide
button and MEASUREMENTS accordion now unlock on all three.

Published under the true-to-size convention (inches shown after toggle):
- **chest** 46 / 48 / 50 / 51 / 52 — flat width 23–26 doubled to full
  circumference (baggy fit, consistent with the description).
- **length** 23 / 24 / 25 / 25.5 / 26 — as printed.
- **inner arm** 18.5 / 19.5 / 20.5 / 21.5 / 22.5 — as printed (underarm
  seam; keyed "inner arm", not "sleeve", to stay honest about the method).
- **fits height** ~5'4" and under · ~5'5"–5'7" · ~5'8"–5'10" ·
  ~5'11"–6'1" · ~6'2" and up — the chart's body-fit mapping, the exact
  thing personas 03/09 asked for ("describes the garment, not the wearer").

Mechanics note: the cm/in toggle converts any cell whose value parses as a
number (`parseFloat`), so a bare `5'5"–5'7"` would render as "2in" in inch
mode. Height values are therefore prefixed with `~` (verified against the
staging theme's live crooks-record.js: non-numeric values pass through both
unit modes verbatim). Heights stay in feet/inches under both modes — UK
convention for body height regardless of unit.

cm stored (×2.54, 1dp) so the inch toggle round-trips exactly: chest
116.8/121.9/127/129.5/132.1 · length 58.4/61/63.5/64.8/66 · inner arm
47/49.5/52.1/54.6/57.2. Mutation returned all three values byte-identical;
userErrors empty.
