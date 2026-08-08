# KEEP.md — what is working and must not be touched

**Read this before acting on `BACKLOG.md`.** Audits that only list faults get acted on badly: the distinctive things get sanded off because nobody wrote down that they were load-bearing. Everything below is named specifically, with the evidence for why it stays.

The single most important finding of this audit is the one easiest to lose: **across eight persona journeys, not one abandonment was caused by the way this site looks.** Three personas left. All three left over inventory, overlays, missing data or unfilled template text. The austere design is not the liability — in two cases it is measurably an asset.

---

## 1. The canvas board — the best-engineered thing on the site

`assets/crooks-board.js`, `sections/crooks-board-test.liquid`

| Condition | Frame rate |
|---|---|
| In viewport, idle | **60.0 fps** |
| Full-page scroll, 4× CPU throttle | **57.5 fps** |
| Scrolled off-screen | **0 fps** |
| Tab hidden | **0 fps** |
| `prefers-reduced-motion: reduce` | **0 fps** |

Three independent pause guards (`crooks-board.js:166, 190, 199, 211-218`) — `matchMedia`, `document.hidden` + `visibilitychange`, and an `IntersectionObserver` — all verified working, each calling `cancelAnimationFrame`.

It also contributes **CLS 0** on the homepage across a full 10-second load on a throttled older Android (persona 7). It paints *after* the text, reserves its own space, and nothing reflows around it.

**The obvious "performance win" of removing or shrinking it would gain nothing and cost the one thing persona 5 stays for.** If page weight must come down, it comes from the 8 mis-named image masters and the 1.17 MB of JavaScript — not from here.

---

## 2. The product page's first viewport

`sections/crooks-exhibit-record.liquid`

Persona 1 — the cold Instagram click, the highest-volume and highest-bounce-risk visitor — stated four tests. The first viewport passes all four with no scrolling: **what is this** (title + `PRODUCT 09 / 14` + category), **what does it cost** (`£25.00`), **does it come in my size** (size row at 746 px, found in ~2 seconds against a 15-second threshold), **is it available** (`IN STOCK`), plus a persistent `.crk-stickybar` carrying product, price, selected size and `ADD TO BAG` in the bottom 9% of the screen.

The Outsider's verdict on why this works: *"the fiction is decoration hung around a completely conventional spine."* `£60.00`, `SIZE XS S M L XL`, `IN STOCK`, `ADD TO BAG` are all plain English. **Never let `ADD TO BAG` become in-fiction.** That rule is the reason the whole aesthetic survives contact with a stranger.

---

## 3. The measurement table and CM/IN toggle

Persona 3 is the hardest sale in the catalogue — a between-sizes buyer, £60, burned before by baggy fits — and it is the strongest journey on the site.

- `GARMENT LAID FLAT. ALL MEASUREMENTS IN CENTIMETRES.` — states the method, so the shopper knows to double the waist.
- A working unit toggle: 38 cm → 15 in, verified accurate.
- `SIZE GUIDE` scrolls 1,230 px and lands the `MEASUREMENTS` heading at exactly y = 0. One tap, no modal, no PDF, no "contact us for sizing".
- `SPECIFICATION` gives fabric weight (`14oz denim`), cut, origin and care.

**The numbers themselves are placeholder and must be replaced (BACKLOG #11) — but the apparatus around them is better than most brands ten times this size provide. Replace the data. Do not touch the component.**

---

## 4. The accessibility work — better *because* of the constraints

| Measure | Result |
|---|---|
| Interactive controls with no accessible name | **0 of 35** |
| `<h1>` on a PDP | exactly one, the product title |
| Landmarks | `header`, `nav`, `main`, `footer` all present |
| Size buttons | `aria-label="Size XS"` + `aria-pressed` |
| Gallery | `role="group"`, `aria-label="Evidence photographs"` |
| Focus ring | 2 px `rgb(167,122,199)` at **5.88 : 1** on the near-black ground, consistent across every `crk-*` control |
| Contrast | 25 of 26 rendered pairs pass |
| Keyboard purchase task | completable end to end, no traps |

`crooks.css:64` carries the comment `/* raised from #C4433F: 3.91:1 -> 4.50:1 on panel (WCAG AA) */` — someone did a deliberate contrast pass and documented it.

The near-black ground, absence of gradients and single saturated accent are *why* the focus ring is this visible. A "friendlier" palette would degrade this.

---

## 5. The no-JavaScript fallback

With JS disabled: 18 product links and 40 images on the homepage, prices rendered, sizes rendered, and a working `/cart/add` form on the PDP. The board degrades to its container with the caption text intact.

Uncommon, quietly excellent, and easy to break by accident during any of the BACKLOG work.

---

## 6. The writing

This is the brand's substitute for the trust furniture it refused, and it is doing the job.

- **WITNESS STATEMENT** — explains the entire commercial model in four sentences without sounding like marketing, signed `FILED BY THE PROPRIETOR. NO FURTHER COMMENT OFFERED.` Persona 5: *"the best writing on the site… this is the bit that makes me think there's a person behind it."*
- **CHAIN OF CUSTODY** — `01 LOGGED / 02 DISPATCHED / 03 IN TRANSIT / 04 RELEASED`, naming courier, dispatch window, delivery window and return window. Persona 1 converted on it. **The label needs the word "shipping" appended (BACKLOG #13); the copy inside must not be touched.**
- **REGISTER AS INFORMANT** — *"One message per drop, nothing else… We do not sell the register."* Persona 5: *"does more for my trust than any padlock icon would."*
- **`> 14 PRODUCTS AVAILABLE TO PURCHASE`** — an inventory readout, not a marketing line.

---

## 7. The catalogue register

`sections/crooks-exhibit-log.liquid` — `NO. 01 / SWEATS / CHARCOAL CELLBLOCK CREWNECK / £50.00 / AVAILABLE`.

Persona 5: *"the numbering makes me want to see all fourteen… it feels like flipping through an evidence log rather than scrolling a shop, and that's the difference between leaving and staying."*

The register format is the asset. The fix in BACKLOG #14 is to make the `AVAILABLE` slot carry information (a filing date) instead of a constant — **an addition to the format, not a replacement of it.** Do not turn this into a conventional product grid.

---

## 8. The refusal to fake data

`sections/crooks-case-file.liquid:25-28`:

> *"There is no Liquid-side source for live scores, so the only honest options are ruled empty rows or nothing at all. Placeholder scores are never rendered."*

One advisor read the hidden leaderboard as an oversight and proposed switching it on as a cheap win. It is not an oversight — it is the same principle that rejected fake stock counters, applied consistently, and written down. **Respect it.** If the leaderboard is ever wired up (BACKLOG #25) it must carry real scores from Base44 or stay hidden.

---

## 9. The enforcement of the design rules

`crooks.css:101` — `.crk-root, .crk-root *, ::before, ::after { border-radius: 0 }`
`crooks.css:428` — `.crk-record * { border-radius: 0 !important; box-shadow: none !important }`

The system is enforced in code, not left to discipline. The only place it is violated is `snippets/crack-the-cuffs.liquid` (BACKLOG #5) — which is also the only element that interrupts every persona. **Removing that popup's radii and shadow brings the site back into compliance with its own rules; it does not compromise them.**

---

## 10. The sold-out and notify components that already exist

`sections/crooks-exhibit-record.liquid:281-301` already contains a complete, in-voice sold-out state: `RELEASED — NO LONGER IN CUSTODY`, an email capture form with subject `Restock request`, product handle and URL, plus success and error states.

It is not missing. It is gated at `:142` on `{% if product.available %}` — product-level — while variant availability is already computed 91 lines later at `:233`.

**BACKLOG #3 is therefore not "build a notify feature". It is "surface a feature you already built at the right granularity."** Do not design anything new here; `--crk-red` is already reserved for exactly this state and is currently unused.

---

## The one-line summary for anyone acting on the backlog

> Fix the inventory, the overlays and the unfilled template text. Replace the placeholder measurements with real ones. Leave the terminal alone.

---

# ROUND 2 ADDENDUM — 2026-08-08 re-audit

Everything above held: the board's guards, the buy spine, the measurement apparatus, the
accessibility profile, the no-JS fallback (re-verified: 18 links / 40 images), the writing, the
register, the fake-data refusal, the radius enforcement (now with zero violations — the popup
was brought into compliance). Three additions are now load-bearing and join the protect list:

1. **The FILED status slot** (`FILED 03.08` style) — it flipped the returning fan from "would
   leave" to "stays" without breaking the register format. Do not replace it with "NEW", do not
   let it become a badge.
2. **The variant-level sold-out + notify pattern** — `SIZE M IS SOLD OUT` in the live region,
   disarmed form, in-voice capture. This is the honest version of the scarcity fiction and is
   now proven to work end-to-end. `aria-disabled` + still-selectable is deliberate; do not swap
   it for the `disabled` property (removes it from the tab order).
3. **The two-action sticky bar** (`ADD TO BAG` / `CHECKOUT NOW`) — both plain English. The rule
   from round 1 stands: these buttons are never in-fiction.

Two cautions from the round-2 council:

- **The carriage status bar is NOT on this list.** It corrected a false free-shipping claim
  (good) but accreted above the register (first card 1.22 → 1.48 viewports). New furniture must
  earn its viewport the way the board did.
- **Any change near `.crk-meta` or the display-font stack must re-run the no-JS and 200% zoom
  checks** — the two things the last sprint proved are easiest to break silently.
