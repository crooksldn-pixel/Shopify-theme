# PERSONA 7 — THE SLOW CONNECTION (RUN 2)

360×800, older Android profile, 6× CPU, Slow 4G. Run 1 verdict: *would continue, unsettled at
the cart.* Run 2 verdict: **smoother everywhere except the cart — which is now heavier than
run 1, for a new reason.**

## Better

- The PDP path lost the popup (gated to homepage) and its Base44 bundle — PDP script weight
  1,082 KB *(r1: 1,171)*, PDP transfer 1,680–1,857 KB *(r1: 2,591 on the tee)*.
- The tee PDP paints product at ~2.4–3.0 s *(r1: 13.9 s)*.
- The homepage is 543 KB lighter (2,560 KB) after five master re-uploads.
- **The cart no longer changes identity.** Dark ground, house type, tracked-shipping options
  (`Tracked 24 / Tracked 48 free`), a free-shipping progress line — the run-1 "handoff to
  somewhere else" moment at the point of payment is gone. Wallet buttons remain third-party
  chrome (Shopify-owned, cannot be restyled).

## Worse

- **Cart transfer 4,215 KB *(r1: 4,024)*, LCP 9,444 ms *(r1: 7,948)*.** The regression is one
  file: `cellcrew.webp`, 976 KB served as PNG, now shipping on the cart via the crewneck's
  image. It is one of the three masters still uploaded under a `.webp` name. Re-upload closes
  ~400 KB of it (the rest of the delta is wallet iframes varying run to run).
- INP on the cart measured 1,096 ms this run (wallet iframes initialising); long tasks 30 / 4.3 s
  — Horizon platform, unchanged.

**Outcome: reaches checkout, and for the first time the cart looks like the same shop — but
this persona pays 13 s of load to open it, and one mis-named image is a quarter of the bill.**
