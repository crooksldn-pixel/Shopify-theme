# PERSONA 6 — The accessibility user

**Who:** Keyboard-only, then screen reader, then 200% browser zoom, then reduced-motion.
**Conditions:** 390 × 844 throttled **and** 1440 × 900 desktop.
**Route:** homepage → menu → a product → select a size → reach add-to-cart, using each method.
**Recorded:** every point where the task becomes **impossible**, not merely awkward.

---

### Step 1 — Homepage, before any key is pressed
**Screenshot:** screens/p6-step1.png
**On screen:** Announcement bar, header, canvas board, cookie banner across the bottom 40%.
**Goal right now:** get to a product using the keyboard.
**Felt experience:** Standard opening. Let's see where the first Tab takes me.
**Blocked by:** nothing yet.
**Would they continue?** yes.
**Seconds elapsed:** 7.7

### Step 2 — Tabbing to the first product
**Screenshot:** screens/p6-step2.png
**Measured — 19 Tab presses to reach the first product link.** In order:
1. `Privacy Policy` (cookie banner)
2. `Manage preferences` (cookie banner) — **no focus indicator at all**
3. `Accept` (cookie banner)
4. `Decline` (cookie banner)
5. `Skip to content`
6. logo · 7. `SEARCH` · 8. `BAG [0]` · 9. `LIGHT MODE` · 10. `MENU` · 11. `CATALOGUE`
12–18. seven filter chips · 19. first product card

**Goal right now:** reach a product.
**Felt experience:** Four stops on a cookie notice before I even get the skip link, and one of them gives me no focus ring at all — I genuinely can't tell where I am. After that it's fine, and the purple ring is strong and easy to follow. But nineteen presses to reach the first product is a lot when I'm doing it one key at a time.
**Blocked by:** nothing is impossible. The cookie banner is the friction.
**Would they continue?** yes.
**Seconds elapsed:** 12.5

### Step 3 — Tabbing to the sizes on a PDP
**Screenshot:** screens/p6-step3.png
**Measured:** 9 Tab presses from the top of `/products/cb2-wash-jeans` to the first `.crk-size` button.
**Felt experience:** Quick. The gallery region announces itself as a group and the sizes come straight after.
**Blocked by:** nothing.
**Would they continue?** yes.
**Seconds elapsed:** 18.8

### Step 4 — Selecting a size and reaching ADD TO BAG
**Screenshot:** screens/p6-step4.png
**Measured:** Enter on a focused size button selects it (sticky bar updates to `BLUE WASH OG JEANS £60.00 · XS`). 6 further Tabs reach ADD TO BAG. **Task completes.**
**Felt experience:** It works. Enter selects, the bar at the bottom confirms what I picked, and I can get to the buy button. No mouse needed at any point.
**Blocked by:** nothing.
**Would they continue?** **yes — the core purchase task is completable by keyboard alone.**
**Seconds elapsed:** 20.0 · 1 tap

### Step 5 — Screen-reader surface
**Screenshot:** screens/p6-step5.png
**Measured on the PDP:**

| Check | Result |
|---|---|
| Interactive controls | 35 |
| **Controls with no accessible name** | **0** |
| `<h1>` | exactly one — `BLUE WASH OG JEANS` |
| Landmarks | `header`, `nav`, `main`, `footer` all present |
| Size buttons | `aria-label="Size XS"`, `aria-pressed="true"/"false"` |
| Sold-out sizes | `aria-disabled="true"` |
| Gallery | `role="group"` `aria-label="Evidence photographs"` |
| Images missing `alt` | 1 |
| Heading order | **`H2: Cookie consent` precedes the `H1`** |

**Felt experience:** This is careful work. Every button has a name, the sizes announce as "Size XS, pressed", the gallery is a labelled group, and there's exactly one H1 which is the product name. That's better than most stores I use. The one jarring thing is that the first heading my reader hits is the cookie notice, before the product.
**Blocked by:** nothing impossible.
**Would they continue?** yes.
**Seconds elapsed:** 20.2

### Step 6 — 200% browser zoom
**Screenshot:** screens/p6-zoom200.png · screens/p6d-zoom200.png
**Measured:**

| Viewport | `scrollWidth` / `clientWidth` | Horizontal scroll |
|---|---|---|
| **Mobile 390 px @200%** | **308 / 195** | **YES — fails WCAG 2.1 AA §1.4.10 Reflow** |
| Desktop 1440 px @200% | 720 / 720 | no — passes |

Overflowing elements at mobile 200%: `p.crk-status__msg (+164px)` · `div.crk-header__actions (+113px)` · `button.crk-header__link (+113px)` · `table.crk-table (+111px)` · `caption (+111px)`.

**Goal right now:** read the page at a size I can actually see.
**Felt experience:** Now I'm scrolling sideways to read one line of text, then scrolling back to read the next. The header runs off the edge and so does the measurement table — which is the exact thing I most need to read carefully. This is the point where the site stops working for me.
**Blocked by:** **the header action row and the measurement table both overflow.** The measurement table overflowing is the worst of it — it's the content that requires the most careful reading.
**Would they continue?** **would leave on mobile.** Desktop is fine.
**Seconds elapsed:** 32.1

### Step 7 — prefers-reduced-motion: reduce
**Screenshot:** screens/p6-reducedmotion.png
**Measured:** canvas board **0 fps** — fully stopped. One CSS animation still runs anywhere on the site: `div.resource-card` `fadeIn 0.15s` × 1 (non-looping, 150 ms).
**Goal right now:** browse without motion triggering symptoms.
**Felt experience:** The board just stops. Not slowed, not faded — stopped, and the page still looks complete. Somebody actually thought about this.
**Blocked by:** nothing.
**Would they continue?** **yes.**
**Seconds elapsed:** 47.4

---

## Desktop run

Identical results except for zoom: 19 tabs to first product, 9 to sizes, 6 more to ADD TO BAG, 0 unnamed controls, board 0 fps under reduced-motion, **and 200% zoom passes cleanly (720/720, no overflow)**.

---

## Verdict

**Would complete the purchase by keyboard or screen reader. Would fail at 200% zoom on mobile.**

Against this persona's own standard — "every point where the task becomes impossible, not merely awkward" — there is **exactly one impossible point: 200% zoom on a phone.** Everything else is friction.

**What is genuinely good here, and unusual:**
- Zero unnamed controls out of 35.
- `aria-label="Size XS"` + `aria-pressed` on the size buttons.
- A single, correct `<h1>`; full landmark set.
- A 2 px purple focus ring at **5.88 : 1** against the near-black ground, applied consistently to every `crk-*` control.
- The canvas board stops completely under reduced-motion, and also pauses off-screen and on tab blur.
- **The shop works with JavaScript disabled** — prices, sizes, images and a working `/cart/add` form are all server-rendered.

**Three real defects, in order:**
1. **200% zoom on mobile causes horizontal scrolling** — WCAG 2.1 AA failure. The measurement table and header action row are the offenders.
2. **The cookie banner takes the first four tab stops on every page**, ahead of the skip link, and its `Manage preferences` button has no focus indicator at all. (Shopify-owned, configured in admin.)
3. **`H2: Cookie consent` precedes the page `H1`**, which is the source of the `heading-order` axe violation.

Note that the austere design is *helping* this persona, not hurting: high-contrast near-black ground, no gradients to wash out focus rings, a single saturated accent that makes the focus indicator unusually visible, and stepped motion that stops cleanly. The accessibility problems are in the inherited Horizon layer and the Shopify consent banner, not in the terminal.
