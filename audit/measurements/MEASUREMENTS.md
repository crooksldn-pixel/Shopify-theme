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
- **Not touched**: V2 BAGGIES still carries its invented placeholder — no real
  chart supplied yet.
  The pink hoodie chart (with the height guide) awaits a product name, and
  the Arc'teryx body chart was **refused** for the windbreaker: another
  brand's body-fit table is not this garment's measurements.

## Verification note

Store-side values verified by API read-back. Visual check on the staging PDP
(accordion render + cm/in toggle) needs a fresh share-preview link — the old
one has expired. The live theme does not render these metafields, so nothing
appears on crooksldn.com until the redesign publishes.
