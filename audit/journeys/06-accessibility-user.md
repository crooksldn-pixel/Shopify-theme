# PERSONA 6 — ACCESSIBILITY USER (RUN 2)

Keyboard + screen-reader semantics on mobile and desktop, 200% zoom, reduced motion. Run 1
verdict: *would buy; fails at 200% zoom on mobile.* Run 2 verdict: **would buy — the WCAG
failure is fixed.**

## Fixed and verified this run

- **200% zoom reflow (WCAG 2.1 AA §1.4.10): passes.** scrollWidth 195 == clientWidth 195, no
  horizontal scroll *(run 1: 308 vs 195, a hard failure)*. The 320 px homepage overflow is gone
  with it — the one remaining 10 px protrusion is the filter rail's deliberate scroll cue.
- **The only contrast failure is gone.** `--crk-micro` now carries the `--crk-dim` values in
  both modes; every rendered pair passes *(run 1: 2.53–2.57:1 on the 9 px micro-copy)*.
- **The cart's critical axe violation (`aria-required-children`) is gone**, along with
  `aria-allowed-role`. Remaining on the cart: wallet-iframe `frame-title` (Shopify-owned) and
  the banner's `heading-order`/`region` (admin).
- **Sold-out sizes now announce themselves.** `aria-disabled` + selection allowed + live-region
  `SIZE M IS SOLD OUT` + notify form — the correct pattern (stays in tab order, state readable).

## Unchanged

The cookie banner still takes the first four tab stops on every page, its `Manage preferences`
button still has no visible focus, and its H2 still precedes the page H1 (the remaining
`heading-order` violation). All one admin setting. The `#PBarNextFrame` focus trap is the
preview bar, not the storefront. Reduced-motion behaviour re-verified: board 0 fps, popup
transition suppressed.

**Outcome: completes the purchase with no failing WCAG criterion in the theme's own surfaces.**
What remains belongs to the banner and the wallet chrome.
