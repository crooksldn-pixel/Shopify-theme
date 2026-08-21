# CROOKSLDN — Shopify theme

Working context for this repo. Auto-loaded at the start of every session, so
new chats start knowing the store, the design system, and what's already built.

## Store & themes

- Store: `5wn03t-nm.myshopify.com` (brand: **CROOKSLDN**)
- Base theme: Shopify **Horizon** (Online Store 2.0), imported at `224acdc`
- Theme IDs:
  | Theme | ID | Status |
  |---|---|---|
  | `CROOKSLDN — Staging` | `202053779799` | unpublished — **`npm run push` target** |
  | `CROOKSLDN — Dev` | `202044309847` | **live** (published at Sprint 1) |
  | `Horizon` (original) | `196747034967` | unpublished — rollback point |

**Never publish to live without George's explicit say-so.** All work goes to
Staging and is reviewed at
`https://5wn03t-nm.myshopify.com?preview_theme_id=202053779799`.

## Commands

`npm run dev` (temp dev theme + live reload) · `npm run check` (Theme Check) ·
`npm run pull` (pull down theme-editor changes) · `npm run push` (→ Staging).

Run `npm run check` before committing. If the theme editor may have been used
since the last session, `npm run pull` first so local doesn't clobber it.

## Visual identity

Locked in Sprint 3 (`f8c4acd`). Set via colour schemes in
`config/settings_data.json` — change the schemes, not per-section overrides.

- **Bone** `#F4F1EA` — light base (`scheme-1`), ink text, hairline borders
- **Ink** `#0A0A0A` — dark sections, hero, footer (`scheme-5`)
- **Caution yellow** `#FFD400` — accent (`scheme-2`); CTAs flash yellow on hover
- Badges: SALE/NEW → `scheme-2` (yellow), SOLD OUT → `scheme-5` (ink)
- Headings: **Archivo Narrow**, uppercased (H1–H3)
- **Square corners everywhere** — cards, inputs, popovers, badges
- Mono: self-hosted **Space Mono** (OFL) as `assets/crx-mono.woff2` /
  `-bold`, applied by `assets/crx-mono.css` to prices, unit price, SKU,
  inventory, delivery message and badges — the "docket / evidence" look.
  Loaded from `layout/theme.liquid` after the theme fonts.

Aesthetic shorthand: workwear/evidence-locker. Sharp, mono, high-contrast.

## Custom code (everything else is stock Horizon)

| File | What it does |
|---|---|
| `sections/category-bar.liquid` | Sticky chip row on collection pages (Shop All / Tees / Denim / Sweats / Accessories). Server-rendered, current chip filled ink/bone, others outlined. 44px targets, horizontal scroll, no layout shift. Handles + labels are section settings. |
| `snippets/crack-the-cuffs.liquid` | First-visit popup embedding the Base44 game `crack-cuff-codes.base44.app` in an overlay iframe. Wired into `layout/theme.liquid` before `</body>`, skipped in the theme editor. |
| `blocks/delivery-message.liquid` | PDP block reading product tags — `made-to-order` tag swaps the in-stock message for the made-to-order one, with an optional status dot. |
| `assets/crx-mono.css` + fonts | Self-hosted mono face (above). |
| `image-backups/originals-white-bg/` | Pre-cutout white-background product PNGs, kept so any image can be restored after the background-removal pass. |

`sections/crooksminigame.liquid` came in with the original Horizon import — it
predates this repo, it is not something built here.

### Crack the Cuffs popup — details worth not rediscovering

- First visit only, via `localStorage` flag `crooksldn_ctc_seen`, set as soon
  as it shows so it never re-nags. `?ctc=1` forces it for QA.
- Fires ~3s after load; deferred; the iframe is only created when shown.
- Full-screen on mobile, centred on desktop, ink overlay. Closes on the
  overlay X, backdrop tap, Esc, and the app's `crooks-popup-close` message.
- **Discount generation and hand-off are owned by Base44**, not the theme.
  "Shop the Drop" uses Shopify's native `/discount/{code}` route with
  `target=_top`.

## Conventions

- Prefer theme settings and colour schemes over hardcoded CSS.
- Custom sections/blocks expose settings via their `{% schema %}` so content
  can be edited in the theme editor rather than in code.
- Placeholder copy and imagery get swapped in the theme editor, not committed.
- Server-render where possible; avoid layout shift.
- Commit messages are the project log — one commit per sprint/task, with a
  body explaining what changed and why. Keep that up; it is how context
  survives between chats.

## Where the history lives

Work was done in numbered sprints. `git log` bodies are detailed — read them
before assuming something isn't built. Shipped so far:

1. **Sprint 1** — nav / collections (`0381a06`)
2. **Sprint 2** — PDP image zoom, related products, tag-based delivery
   message (`77ac705`, `2c0c262`)
3. **Sprint 3** — visual identity lock, homepage rebuild, mono face
   (`f8c4acd`, `d63a865`, `7b3c410`)
4. **Sprint 7** — Crack the Cuffs popup (`bab2a94`)
5. **Task 2** — collection category chip bar (`c7988fa`)

Known open thread: the homepage **lookbook teaser links out until Sprint 4** —
Sprints 4–6 were not committed, so check with George on what they cover before
picking up numbering.
