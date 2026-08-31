# RUN-SHEET — CROOKSLDN abandoned-checkout flow (3 emails)

Council-ruled plan (working papers + full verdict: `audit/` council files and
`scratchpad` transcript; verdict summarised in the session log). Files:

1. `crooks-abandoned-1-property-log.html` — ~5 min, no discount.
   Subject: "You left something in your bag at CROOKSLDN"
2. `crooks-abandoned-2-evidence-tampering.html` — ~1 h, unique 15% + fulfilment socks.
   Subject: "15% off the items you left — CROOKSLDN"
3. `crooks-abandoned-3-final-disposition.html` — ~24 h, unique one-time 20% (owner's
   call, council guardrails baked in; the 15%-closure council default is a 3-string
   swap documented in the file header).
   Subject: "Last call: 20% off your bag for 24 hours — CROOKSLDN"

NOTE (owner request, 2026-08-31): copy rewritten in plain English — the
terminal look stays, but no in-world jargon a customer must translate.
Honesty lines survive in plain form ("stock isn't reserved", the sub-£30
postage disclosure, "codes don't stack — use whichever is bigger", real
expiries, one browse-anyway text link).

## The rail (pick one, honestly)
- **Klaviyo (recommended)**: Flow trigger "Checkout Started" → wait 5 min →
  email 1 → wait 55 min → email 2 → wait 23 h → email 3. Flow filter:
  "Placed Order zero times since starting this flow" (cancel-on-order).
  Email 3 additional filter: has NOT received this flow before (first
  abandonment only — caps the 20% training effect).
- **Native Shopify**: one email only, fires 10–60 min after abandonment. If
  staying native, use email 1's HTML in Settings → Notifications → Checkout
  abandonment and skip 2/3 — do NOT pretend it's a 5-minute send.

## Discounts to create (before any send)
- **EVID15** (Klaviyo unique-coupon family): 15% off order · one use per code ·
  expires 48 h after issue · combinability OFF (can't stack with GTWY codes).
- **DISP20**: 20% off order · one use · expires 24 h after issue ·
  combinability OFF · **excludes the Sets collection** (already £10 under —
  and the email copy discloses the exclusion).

## The socks flag (email 2's CONTRABAND block)
Shopify Flow: order created → discount code starts with "EVID15" AND order
total ≥ £30 → add order tag `CONTRABAND-SOCKS` (shows on admin order + print
templates). **If this flag is not built, delete the SOCKS-START→SOCKS-END
block from email 2 before sending** — a forgotten pair costs more trust than
no socks.

## Pre-launch checklist (from the council verdict — all 8 before go-live)
1. Disable Shopify's native abandoned-checkout email (or you send duplicates).
2. Untick the pre-ticked marketing checkbox at checkout (PECR; audit flag).
3. Test a code end-to-end: issue, redeem, and CONFIRM it dies at expiry.
4. Verify combinability OFF vs GTWY codes both directions.
5. Build + test the CONTRABAND-SOCKS tag → packing-slip flag (or cut the block).
6. Dark-mode test sends: Gmail iOS/Android, Outlook, Apple Mail (the near-black
   build carries literal bgcolors to resist inversion — verify anyway).
7. Confirm the cancel-on-order flow filter (a buyer must never get email 2/3).
8. Confirm the unsubscribe merge tag for your ESP ({% unsubscribe_url %} is a
   placeholder — check the exact tag in your Klaviyo account before send 1).

## Copy laws these emails obey (don't edit them out)
- Every stated expiry is real; no countdown theatre.
- "Logged, not reserved" — stock is never claimed to be held.
- The shipping-threshold trap is disclosed ("below £30 net, postage runs
  £3–£4.99") — a discount that quietly springs postage is a card trick.
- GTWY line ("codes don't stack, use the larger number") stays in 2 and 3.
- "Browse anyway" is one dry line + text link, never a second button.
