# PERSONA 8 — POST-PURCHASE (RUN 2)

Bought last week, wants to know where the order is. Run 1 verdict: *cannot track an order at
all.* Run 2 verdict: **can track — the run-1 blocker is closed. The account page is still not
this brand.**

## Fixed

- `trackWordPresent: true` on the homepage *(r1: false)*.
- **MENU now contains TRACKING** → `/pages/tracking` — a real tracking page, ported in the fix
  sprint. CONTACT and ACCOUNT sit beside it. The footer INFORMATION column carries the same
  entry.
- The carriage status bar puts dispatch information (`ORDER BY 18:00 FOR SAME-DAY DISPATCH`) on
  every page.

## Unchanged (all admin)

- **ACCOUNT still lands on `friendsof.crooksldn.com` in Times New Roman on white** —
  `styledAsTheme: false`, no guest order lookup on that page. The one surface a paying customer
  is guaranteed to see remains the least branded thing in the ecosystem.
- The refund policy still shows `crooksldn@gmail.com`, still gives a 14-day window without
  saying **who pays return postage** (`whoPaysPostage: null`) — the deciding fact on a £60
  order.

**Outcome: finds tracking in two taps.** Run 1's dead end is gone; what remains is polish on
hosted pages and policy text, not navigation.
