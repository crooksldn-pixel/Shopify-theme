# Council Verdict — CROOKSLDN abandoned-checkout flow

## Where the Council Agrees
All five advisors converge on: (1) a real 5-minute first touch exists only on an ESP — Klaviyo's "Checkout Started" trigger; native Shopify fires 10–60 minutes out and the owner must be told so plainly. (2) Free socks via option (b) — added at fulfilment, "contraband in the bag," on the CONTRABAND 03 keyring precedent — with the Contrarian's condition that it needs a literal packing-slip flag or it will be forgotten on a drop day. (3) The "browse anyway" invitation is one dry in-voice line, never a second button — the Outsider confirms it reads as confidence, not neediness. (4) Any stated expiry must be real. (5) Fix the pre-ticked marketing checkbox before the first send (PECR). Four of five condemn the public 15→20% ladder as a machine that trains abandonment and outbids The Getaway.

## Where the Council Clashes
The Expansionist stands alone defending 20% and reframing trained abandoners as "an engaged segment" — every reviewer named this the pack's biggest blind spot, and the fake-clock audit incident backs them. Subject lines split the room: the Expansionist wants "CASE FILE OPENED" police-log theatre; the Outsider correctly notes that from an unknown sender this reads as phishing — fiction needs the context of the site, and the inbox has none. Email 3's content splits three ways: First Principles says same 15% with a real closing time; the Executor says 15% plus a shipping upgrade; the Contrarian says 15% or no code at all. The Outsider alone questions whether three emails in 24 hours is one too many.

## Blind Spots the Council Caught
- **GTWY stacking**: nobody defined what happens when an abandoner already holds a GTWY-XXXX 10% code. Undefined, email 2 is a code collision at checkout — the audit's "silently dropped discount" wound reopened.
- **Free-shipping threshold trap**: 15% off a £30–35 cart drops it under the £30 line and springs £3–£4.99 postage at checkout. The discount backfires into exactly the card trick the design law forbids.
- **Native email duplication**: Shopify's own abandoned-checkout notification must be disabled or customers get two competing sequences.
- **No stock reservation**: "ITEMS HELD IN EVIDENCE" is a fabricated claim — Shopify reserves nothing, and items can sell out mid-flow. Copy must say *logged, not reserved*.
- **Dark mode**: Gmail/Outlook inversion can wreck the near-black/purple terminal look; nobody designed for it.
- **Missing subject lines**: the brief demanded subjects + preheaders for all three; no advisor delivered a complete set.

## The Recommendation
Build on **Klaviyo** (Checkout Started → 5 min → cancel-on-order). All discounts are **Klaviyo unique one-time codes** auto-applied via the checkout URL (no typing — the audit shows code entry drops sales), **not combinable** with GTWY codes (set combinability off both ways). All emails: 600px tables, inline CSS, Courier New stack, dark-first with literal `bgcolor="#0C0B10"` on every cell, text #E8E5EF, accents #9B6FC4, `<meta name="color-scheme" content="dark light">`, alt text everywhere, bulletproof CTA, preheader, unsubscribe. Sender name: **CROOKSLDN**.

**Email 1 — "PROPERTY LOG" (5 min, no discount).**
Subject: `You left items at CROOKSLDN — logged, not reserved.` Preheader: `Order before 18:00 London for same-day dispatch. Free UK size swaps. 14-day returns.` Hero: the abandoned line items rendered as evidence cards — image, title, exact price, numbered EXHIBIT 01/02. Body: deadpan procedural log of what was started and not completed; exact facts only (free UK Tracked 48 over £30, dispatch cutoff). Availability caveat in-voice: "Stock is not reserved. Exhibits may be released to other claimants." CTA: **RECLAIM PROPERTY**. Browse line (footer, text link): *"No obligation to claim. THE REGISTER remains open for inspection."*

**Email 2 — "EVIDENCE TAMPERING AUTHORIZED" (1 hour, 15% + socks).**
Subject: `15% off the items you left — CROOKSLDN.` Preheader: `Code applies itself at the link. Expires in 48 hours — genuinely. Socks in the bag on claims of £30+.` Hero: same exhibit cards with a static "15% STRUCK FROM THE RECORD" stamp graphic. Code: unique `EVID15-XXXX`, 15% off order, 48h real expiry, auto-applied. Socks: option (b) — fulfilment-added, **conditional on the packing-slip flag existing** (Klaviyo/Flow auto-tags the order `CONTRABAND-SOCKS`; tag prints on the slip). If the flag isn't built, cut socks — "if possible" means no. Copy: "Contraband: one pair of socks slipped in the bag on claims of £30 or more. Not logged at checkout. No code needed." Shipping trap, disclosed deadpan: "For the file: free UK shipping is calculated after the discount. Below £30 net, postage runs £3–£4.99." GTWY line: "Holding a GTWY code? Codes don't stack. Use the larger number." CTA: **RECLAIM — 15% APPLIED**. Browse line: *"Not buying? The file is still public. Inspect THE REGISTER."*

**Email 3 — "FINAL DISPOSITION" (24 hours).**
My ruling: **not 20%**. The majority is right — a public 20% top step reprices the store and makes The Getaway the sucker's discount. Default build: restate the recipient's same `EVID15-XXXX` code with its actual closing timestamp merged in. Subject: `CROOKSLDN — your 15% code closes {{ expiry_time }}.` Preheader: `After that the file is sealed and full price stands. No obligation.` Hero: brand graphic — case-file stamp "DISPOSITION PENDING," no fake countdown. Body: closure of the case, not a bigger bribe; exact expiry, availability caveat repeated. CTA: **FINAL CLAIM — 15% APPLIED**. Browse line: *"Case closed either way. THE REGISTER stays open for inspection."*
The owner's word is final: if they keep 20%, run it safely — unique one-time `DISP20-XXXX` codes, **first-abandonment-only** segment (never received this flow before), excludes the £85 sets (already save £10), 24h real expiry, non-combinable, never shown to GTWY holders in copy as an upgrade path. That caps the training effect to one taste per customer.

**Timing promise**: tell the owner "5 minutes, for real, on Klaviyo; 10–60 minutes if we stay native — pick one, and the copy will match whichever is true."

**Pre-launch checklist**: (1) disable Shopify's native abandoned-checkout email; (2) untick the pre-ticked marketing checkbox; (3) verify code expiry actually fires on a test code; (4) set combinability off vs GTWY; (5) build the CONTRABAND-SOCKS order-tag → packing-slip flag; (6) dark-mode test sends (Gmail iOS/Android, Outlook, Apple Mail); (7) cancel-on-order filter confirmed; (8) unsubscribe link live.

## The One Thing to Do First
Install Klaviyo and, the same hour, disable the native abandoned-checkout email and untick the pre-ticked marketing box — no copy gets written until the rails are legal and non-duplicating.
