# CONTRADICTIONS.md — everywhere the site tells a shopper two different things

For a brand with no reviews, self-consistency is the trust mechanism (Q4).
Each entry quotes both sides and names who hit it. Sorted by damage.
"Known" = already logged pre-audit; everything else is new.

## Money and delivery

| # | Side A | Side B | Who hit it | Status |
|---|---|---|---|---|
| C1 | Jeans descriptions (cb1 + cb2): **"9-16 days delivery uk / 16-21 days international"** | Custody accordion, FAQ, Terms, shipping policy, ticker: **same-day dispatch before 18:00, UK 1–2 working days** — on the same screen, one accordion apart | Personas 2 ("the AliExpress line"), 3, 10; Phase 1 | Known family — confirmed shopper-facing at the decision moment |
| C2 | V2 BAGGIES description: **"3-5 day delivery uk"** | Same site-wide promise as C1 | Phase 1 (product-record, content) | **New** — a second, different wrong number in the same family |
| C3 | Checkout, Tracked 48 (£3.00): **"Estimated delivery Fri 28 Aug"** (10 days; once "Mon 24–Wed 26") | The service's own name (**48** hours), custody's "UK 1–2 working days", and Tracked 24 beside it honestly saying "Thu 20–Fri 21" | Personas 7 ("what is the 48 doing for ten days, walking?"), 14 | **New** — checkout shipping-profile config, not theme code |
| C4 | Cart with `10CROOKS`: **£76.50** | Checkout sixty seconds later: **£85.00**, code field empty, re-entry rejected | Persona 5; Phase 1 B-5 | **New** — reproduced on preview twice; MUST be retested on the live domain before treating as real |
| C5 | Set copy: save £10 off the **£85** set | `10CROOKS` takes the set to **£76.50** below the stated price | Phase 1 | Known (O1) — confirmed live in cart |
| C6 | Status ticker at 21:40: **"order before 18:00 for same-day dispatch"** (static) | PDP dispatch line, correctly: **"Ordered now — leaves tomorrow"** | Persona 7 | **New** — mild; the computed line is right, the static ticker doesn't know the time |
| C7 | Ticker (hardcoded): **"FREE UK SHIPPING OVER £20"** in £ | Every price on the page in **USD** for non-UK visitors (Markets conversion) | Phase 1 (multiple areas) | **New** — framing clash for overseas traffic |

## Returns

| # | Side A | Side B | Who hit it | Status |
|---|---|---|---|---|
| C8 | `/pages/terms`: **14 days from delivery to notify + 14 more to post back** (~28-day effective window) | `/policies/refund-policy`: **"14 days from delivery to return"** | Phase 1 (content) | **New** — a day-20 shopper doesn't know which governs |
| C9 | Site policies: **14 days**, faulty items per Terms | AfterShip returns portal (the destination FAQ/Terms route to): **"30 days from purchase"**, faulty window **7 days** | Persona 12 — postponed her order over it | **New** — external portal config, directly contradicts the site that links it |
| C10 | FAQ + Terms clauses 03/04: returns go through the **AfterShip portal** ("Start your return here") | `/policies/refund-policy`: **"email crooksldn@gmail.com or DM @crooksldn"** — never mentions the portal | Persona 20 (7-tap decoy trail via footer REFUNDS) | **New** |
| C11 | FAQ answer link text: **"Start your return here"** | Its href: `/pages/terms#returns` — the terms page, **not** the portal the words promise | Persona 9 | **New** |
| C12 | Terms: transit-damage claims within **48 hours** | Shipping policy: damage claims within **14 days** | Phase 1 (content) | **New** |

## Promises vs behaviour

| # | Side A | Side B | Who hit it | Status |
|---|---|---|---|---|
| C13 | FAQ: **"You can also look your order up on the tracking page — no account needed."** | `/pages/tracking` signed out: SIGN IN wall, no lookup form of any kind | Persona 20 (worst moment); Phase 1 | Known (RUN3 A6) — **still unfixed**, verbatim broken promise one tap after it's made |
| C14 | Crack the Cuffs: win the game, surrender phone + SMS consent + email → **"REVEAL MY CODE"** | The button produces nothing — no code, no error, no spinner (reproduced across sessions) | Persona 17 (audit's worst moment) | **New** — third-party app; the site takes two contact channels and gives nothing back |
| C15 | Notify form: **"TELL ME WHEN THIS SIZE IS BACK"** | The commercial model: short runs that don't restock — nothing anywhere on the site says whether a restock ever happens (FAQ has no restock question) | Persona 6 | **New** — the form promises a future the brand may not intend |
| C16 | Contact-information policy: **"Prefer a form? Drop your details below."** | No form exists or can exist on a policy page; `/pages/contact` isn't linked from it | Phase 1 (content) | **New** |
| C17 | Catalogue card: **"AVAILABLE"** on V2 BAGGIES | PDP: 3 of 5 sizes sold out | Personas 1, 6 ("reads as a broken promise once the PDP reveals the truth") | Deliberate per SPEC §9.5 (status slot is product-level). Recorded per the §8 rule: persona 6's step is the journey evidence of a real cost; the council weighs it — the design itself is protected |
| C18 | Fit copy on cb2 jeans: SPECIFICATION **"OG straight, mid rise"** | ITEM DESCRIPTION: **"baggy, stacked fit"** | Persona 3 | **New** — a size-anxious buyer reading closest hits it |
| C19 | Two-garment set added to bag | Header badge: **BAG [1]** — "did only one thing add?" | Personas 4, 5, 19 | **New** — framing, not arithmetic; cart line itself is correct |

## Consistency notes that stop short of contradiction

- Search results header says **"0 RESULTS"** while the PAGES & ANSWERS block
  directly beneath it contains the answer ("terms", "refund") — the big zero
  reads as failure above the real answer (persona 12; register agent).
- Popup birthday field wants **mm/dd/yyyy** on a UK store (persona 17).
- V2 BAGGIES is categorised **SWEATS**; shoppers seeking "baggies" tap DENIM
  and dead-end in a jeans/jorts-only collection (persona 18).
- The returns address names **"Oairo UK Office"** with no explanation of who
  Oairo is (persona 2) — not a contradiction, but an unexplained third name at
  a trust-sensitive moment.
- `crooksldn@gmail.com` as the support address for a brand that owns
  crooksldn.com (personas 1, 2) — consistent everywhere now (the `.com.com`
  typo is gone), but the free-mail domain itself dents the "real shop" read.

**The pattern:** every theme-owned surface (custody, FAQ, Terms, ticker,
dispatch line, carriage bar, policies skin) agrees with every other — Phase 1
verified the four theme surfaces match to the penny and the day. The
contradictions live in store-side *content* (product descriptions), *config*
(checkout shipping estimates, AfterShip portal policy), and *third-party
machinery* (popup, captcha). The theme keeps its promises; the surfaces
around it break them.
