# RUN3-FINDINGS.md — everything audit 3 surfaced, in one place, build-chat ready

Audit 3 ran 2026-08-17 against staging theme `202053779799` at commit `d0363ee`
(13 commits past run 2). Full evidence lives beside this file (`evidence/METRICS.md`,
`evidence/newtabs.json`, `journeys/`, `DELTA-3WAY.md`, `COUNCIL.md`). This file is the
actionable distillation: every line reference below was re-verified against `d0363ee`
on 2026-08-17.

---

## READ THIS FIRST

**1. Branch situation.** This file lives on the audit branch
(`claude/crooksldn-site-audit-eijmkd`). The theme code lives on
`claude/crooksldn-theme-init-bnen7a` @ `d0363ee`. If your working tree is the theme branch,
read this file with:
```
git fetch origin claude/crooksldn-site-audit-eijmkd
git show origin/claude/crooksldn-site-audit-eijmkd:audit/RUN3-FINDINGS.md
```
If your session sits on the audit branch instead, the theme files are readable via
`git show origin/claude/crooksldn-theme-init-bnen7a:<path>` — do not create theme files from
scratch on the wrong branch.

**2. The council's standing rule (round 3, adopted):** implement item A1 below, and then make
**no further theme commits** until the store owner flips the three `CONTINUE → DENY`
checkboxes (section B1). The backend is days from overselling again; more theme polish before
that flip is misallocated effort.

**3. What run 3 verified WORKING — do not touch, do not "improve":**
- Search (field, typeahead, page results, no-JS) — first-measurement clean.
- TERMS and QUESTIONS pages — content, structure and no-JS rendering all pass.
- Variant-level sold-out + notify (`SIZE M IS SOLD OUT`, disarmed form, capture) — re-verified.
- FILED dates, custody label, tracking page, popup gating, cart brand pass.
- axe sets, 200% zoom, keyboard path — identical to run 2 through 13 new commits.
- The board's pause guards, the no-JS fallback, the plain-English buy spine.
`audit/KEEP.md` is the authority; the bilingual-naming rule (fiction labels subtitled in plain
English) is now on it.

---

## SECTION A — THEME FIXES (this is what your chat can fix)

### A1 · Reserve the header and give BOTH fonts metric-matched fallbacks — the only BLOCKS-class theme defect

**Finding:** CLS **0.325–0.391 on every mobile page** (cold-journey stacking 0.59), all from one
shift at t≈1.9 s: the header control row (CATALOGUE · SEARCH · BAG · LIGHT MODE · MENU) wraps
to a second line when CRX Mono finishes loading, `MAIN` drops 48 px, and on V2 BAGGIES the
size row lands at y=844 — the exact fold — degrading the protected first-viewport answer on
the #2 lifetime seller. Ablation-proven: block `crx-mono.woff2` → CLS 0; VT323 uninvolved.
This is the second consecutive audit topped by the same defect class (run 2: VT323 meta row);
the round-2 prescription (`size-adjust`) was never implemented — it appears zero times in the
theme CSS.

**Where:**
- `assets/crx-mono.css:7` and `:14` — both faces declare `font-display: swap` with no
  size-adjusted local fallback.
- `assets/crooks.css:47–48` — the two font stacks (`--crk-font-mono`, `--crk-font-display`).
- `assets/crooks.css:397` — `.crk-header__bar` is `min-height: 56px` flex (free to grow).
- `assets/crooks.css:432–435` — the ≤429px media block sets `flex-wrap: wrap` on
  `.crk-header__bar` and `.crk-header__actions`.

**Fix, two layers (do both):**
1. **Token layer (kills the defect class):** add `@font-face` fallback declarations with
   `size-adjust` (plus `ascent-override`/`descent-override` as needed) matching CRX Mono's
   metrics against its actual fallback (`IBM Plex Mono`/ui-monospace), and the same for VT323
   against ui-monospace; insert the fallback family names into the stacks at `crooks.css:47–48`.
   Measure the adjustment empirically (render a sample string in both faces, ratio of widths),
   don't guess.
2. **Geometry layer (belt and braces):** reserve the header's height so late font arrival
   cannot move `MAIN` — fix the bar's wrapped height at ≤429px, or prevent the wrap by
   letting the actions row shrink/truncate instead of wrapping. Careful: `flex-wrap` was added
   for the 200% zoom fix (run 2) — whatever you do must keep zoom passing.

**Verify (all four, on throttled mobile 390×844):** CLS < 0.05 on home, both PDPs and cart;
V2 BAGGIES size row back inside the first viewport after banner dismissal; 200% zoom still
195==195 with no horizontal scroll; no-JS render intact. The audit harness scripts
(`audit/p1-perf.mjs`, `p1-clstest.mjs` on the audit branch) are the reference instruments.

### A2 · Isolate and fix the INP regression (~600 → ~1,050 ms on PDPs)

**Finding:** INP roughly doubled everywhere in run 3 (1,032–1,208 ms). Structural suspect,
verified in source: `sections/crooks-header.liquid:3–5` now loads `crooks-board.js` on every
page (gated only on the menu-game setting, which is on) to power the menu drawer's canvas at
`:150` — in run 2 the board script was homepage-only. The search typeahead's link index is the
secondary suspect.

**Fix:** measure first (long-task attribution), then defer — load `crooks-board.js` only when
the drawer actually opens (dynamic import or injected script on first menu open), and check
the typeahead index build is off the interaction path. **The board itself and its pause guards
are protected (KEEP §1)** — this is about when its code loads, not what it does.

**Verify:** INP back under ~700 ms on PDPs on the throttled profile; menu game still plays;
board guards still show 0 fps off-screen/hidden.

### A3 · Add FAQPage structured data to the QUESTIONS page

**Finding:** `sections/crooks-faq.liquid` renders 14 Q&As but emits no JSON-LD
(`newtabs.json → faqSchema: false`; the only `{% schema %}` at `:64` is the section schema).
A free Google rich-result is unclaimed.

**Fix:** emit one `<script type="application/ld+json">` FAQPage block built from the same
section blocks that render the visible Q&As — generated from the real content so it can never
drift (same principle as the register's self-numbering). Escape properly; no hardcoded copy.

**Verify:** valid FAQPage per Google's rich-results test shape; JSON parses; questions match
the rendered page one-to-one.

### A4 · Tidy the homepage seam: manifest AND CASE 001 both render

**Finding:** commit `a17d4b3` says the packaging manifest *replaces* the CASE 001 box, but the
deployed homepage renders both (`newtabs.json → homepage: packagingManifest true,
case001OnHome true`).

**Fix:** make the replacement real in `templates/index.json` — remove the CASE 001 section
(the game's home is now the menu entry, which run 3 verified live). **Caution:** template JSON
is editor-owned; follow the push-order rules recorded in the theme's NOTES commits
(`43521ee`, `2ba26de`) so customizer state isn't clobbered.

**Verify:** homepage shows the manifest, no CASE 001 box, board and register untouched,
menu game entry still present.

### A5 · Optional decision, not a defect: the homepage popup

Round 3's council flipped its presumption: now that the game has an honest opt-in menu entry
(`PLAY CASE:001 NOW`), the uninvited homepage popup is redundant. No persona currently abandons
over it, so retiring it is an owner decision informed by discount-code redemption data — not a
fix to make unprompted. If instructed: `layout/theme.liquid` render of `crack-the-cuffs`,
homepage-gated since run 2.

---

## SECTION B — ADMIN ITEMS (no code can fix these; listed so this file is complete)

| # | Item | Urgency | Where |
|---|---|---|---|
| B1 | **CONTINUE → DENY on 3 CLIVES / MONEY CLIVE / BROADCAST.** Third audit. Variants at 8–9 units under live trade (22 orders/9 days) — a countdown, not a chronic item. Decide CRX GARMS (985 archived under CONTINUE) in the same visit. | **NOW** | Products → variant → untick "Continue selling when out of stock" |
| B2 | **Email find-and-replace.** Legal pages sign `crooksldn@gmail.com`; the shipping policy says **`crooksldn@gmail.com.com`** — undeliverable, on a legal page. Standardise on `info@crooksldn.com` (the theme's own footer default). | **NOW** | Settings → Policies, page content |
| B3 | **Re-upload three masters as `.png`:** `cellcrew.webp` (976 KB, rides the CART), `v2baggies.webp`, `crooksldn-white-red-motiontec-socks.webp`. Third audit. Same fix that took the tee PDP 13.9 s → 2.4 s. | High | Products → media |
| B4 | **The archive: ~£28,270 across 1,452 units, frozen through three pulls.** Hand-count first (counts provably lie: CRXST★RZ 970→98), then the closed-case register per council round 2 — not a plain unarchive. | High, days | Products → Archived |
| B5 | Cookie banner position — still 40% of viewport, first four tab stops, covering the size row on first visit. Third audit. | High | Settings → Customer privacy |
| B6 | Measurement tables — same placeholder arithmetic in all three audits. The apparatus is excellent; the numbers are invented. | High | Measure garments, metafields |
| B7 | Jeans descriptions still carry `9-16 days delivery uk` against custody's `UK 1–2 working days`. | Medium | Product descriptions |
| B8 | Terms page lacks a governing-law line (England & Wales) — copy decision, get it checked. | Low | Settings/pages |
| B9 | Hosted account page: Times New Roman, no order lookup — untouched across all three audits. | Low | Settings → Customer accounts |

## SECTION C — FOR THE RECORD

- The competitive score (39/50, field: 14–30) was measured pre-header-regression at `db96aa3`;
  re-score after A1 lands, not before.
- All trading data still comes from the live site — scored **14/50**, worst in the competitive
  set. Once A1 + B1–B3 land, shipping the theme is the highest-value act available; three
  audits of measured advantage become receipts only in production.
- Instrument notes for the next audit: `p2-fix`/`p2-fix2` need re-targeting at the collapsed
  panels; the corrected sold-out check needs scroll-into-view before tapping (fold geometry);
  badge capture is FILED-aware as of run 3.
