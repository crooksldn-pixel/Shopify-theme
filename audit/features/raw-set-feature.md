# RAW — complete-the-set, end to end (staging theme 202053779799)

Audited 2026-08-18 ~21:00–22:00 London, mobile 390x844 DPR3 via the preview
harness. Staging verified on every session (.crk-root + crooks.css).

Currency note that colours everything below: the audit egress IP is non-UK, so
Shopify Markets served the first session in **USD** — the collapsed line read
"Save $15" and the crewneck "$70.00", all correctly converted, nothing broken.
All checks below were re-run pinned to GB (`?country=GB`, which sticks for the
session) so quotes are the £ experience a UK shopper gets.

Slow-4G first load of the crewneck PDP: content readable ~2.3s, the set line
painted by ~2.5s, settled ~5.5s. Felt brisk for throttled mobile; no late
jumping in the buy panel. The set line sits just below the first fold (top
~922px on an 844px viewport) — one small scroll reveals it, it is not buried.

A Shopify cookie-consent dialog ("COOKIE CONSENT — We and our partners,
including Shopify…" with Accept / Decline / Manage preferences) covers the
bottom ~40% of the mobile viewport on every page until answered, including the
region where the set toggle lives. Not a theme element and not this area's
defect — but note SPEC's open item says "No cookie banner" and there now is
one, so that item looks stale.

---

### 1. Collapsed set line on /products/charcoal-cellblock-crewneck
- **Should:** A quiet, comprehensible one-line offer: what you get, what you save.
- **Did:** Below the dispatch line, above ADD TO BAG: an unticked checkbox, a
  34px thumbnail of the shorts, and exactly: **"Cop the full fit — add the
  matching Cellblock Shorts. Save £10."** To someone who has never seen a
  bundle control it reads plainly: tick box + named garment + named saving. The
  one thing it withholds is the set price itself (£85 only appears after
  ticking) — a cautious shopper must tick to learn the number, but the tick
  costs nothing and undoes cleanly, so this is curiosity, not commitment. (In
  the USD session the same line said "Save $15" — converted, not broken.)
- **Verdict:** works
- **Screens:** f-set-feature-01-collapsed-line, f-set-feature-02-collapsed-gbp

### 2. Tick it — panel, prices, button relabel
- **Should:** Partner size row with live stock appears; was/now prices read correctly; button relabels to the set price.
- **Did:** Panel opens instantly: eyebrow **"CELLBLOCK SHORTS SIZE"**, size row
  XS–XL, and the partner size arrives **pre-selected to match my main size**
  (main XS → partner XS; later main M → partner M) — a genuinely good touch.
  Prices: struck-through **"£95"**, then **"£85 for the set"**, plus **"FREE UK
  TRACKED 24 INCLUDED"**. Both the main buy button and the sticky-bar copy
  relabel to **"ADD THE FULL FIT — £85"** — note: not "£85.00"; trailing zeros
  are dropped everywhere in the set UI (£95/£85), a deliberate-looking style
  choice, and the £85.00 form appears in the cart. The hidden form's variant id
  swapped from the crewneck variant to a real bundle variant. The main price
  under the title stays "£50.00" while the button says £85 — the was/now pair
  beside the toggle explains it, so it never read as a contradiction.
- **Verdict:** works
- **Screens:** f-set-feature-03-ticked-open

### 3. Partner sizes — low/out of stock marking
- **Should:** Sold-out partner sizes marked; stock reflected live.
- **Did:** Clicked all five partner sizes: each swapped to a distinct bundle
  variant id (five different ids logged), button stayed "ADD THE FULL FIT —
  £85", no size carried aria-disabled and the stock line stayed empty — correct,
  because **all 25 bundle variants are in stock right now, so the OOS path could
  not be exercised live**. What the UI holds in reserve (read from the page, not
  invented): a partner size with no buyable pairing gets greyed via
  aria-disabled, and picking an unavailable pair shows **"Cellblock Shorts sold
  out in [size] — pick another size"** in the stock slot and blanks the prices.
  There is no low-stock count ("only 2 left") in the panel — consistent with the
  site's no-fake-urgency rule; silence means in stock.
- **Verdict:** works
- **Shopper impact:** the in-stock state is communicated by absence — nothing
  says "in stock" in the panel. Nobody will miss it, but worth knowing that a
  shopper gets no positive confirmation until the cart.
- **Screens:** f-set-feature-04-partner-size-picked

### 4. Untick — exact restore
- **Should:** Everything returns to the single-item state.
- **Did:** Button back to **"ADD TO BAG"** (both instances), panel hidden,
  variant id restored to the exact crewneck variant it had before, main price
  still £50.00, main size selection untouched. Also checked the interplay the
  other way: with the set ON, changing main size XS→L moved the partner to L
  too (until you've touched the partner row, it mirrors; once touched, your
  partner choice is respected) and kept the £85 label — no stale state anywhere.
- **Verdict:** works
- **Screens:** f-set-feature-05-unticked-restored

### 5. Add main M + partner L — the cart line
- **Should:** ONE line item at £85.00, recognisable, both sizes visible.
- **Did:** One line exactly: title **"CELLBLOCK SET"**, beneath it **"CHARCOAL
  CELLBLOCK CREWNECK - M"** and **"CHARCOAL CELLBLOCK SHORTS - L"**, price
  **£85.00**, total **£85.00**. Both garments and both sizes named — a shopper
  would recognise precisely what they bought. Bonus: after tapping ADD, the page
  stays put but announces **"Added — 1 in bag  View bag"** and the header bumps
  to BAG [1] — clear, no interrupting drawer.
- **Verdict:** works
- **Screens:** f-set-feature-06-mainM-partnerL, f-set-feature-07-cart-bundle, f-set-feature-09-after-add-feedback

### 6. Set-cart section — saving confirmed with the bundle in the cart
- **Should:** SPEC §3.13: "the bundle in the cart → the saving confirmed in words."
- **Did:** With ONLY the Cellblock Set in the cart (the normal outcome of the
  PDP flow), **nothing renders**. No "SET SAVING APPLIED", no set-cart section
  at all — verified twice in separate sessions, server-rendered page, section
  absent from the DOM. The confirmation DOES exist and CAN render — but it only
  appeared when the bundle sat in the cart **alongside a loose component**
  (see item 7 Path B): exactly the situation where "SET SAVING APPLIED — £10"
  is misleading, because that cart is £130 with a duplicate pair of shorts.
  Behaviourally: the bundle-in-cart detection appears to need some *other* cart
  line's product to point at the bundle, and with the bundle alone there is no
  such line. The mirror state (half a set → offer) renders fine, so this is
  specific to the confirmation state.
- **Verdict:** broken
- **Shopper impact:** the shopper who took the £85 offer gets no echo of their
  £10 saving where it should land — mildly deflating but not costly; the £85.00
  price is still correct. The real sting is the inversion: the confirmation
  fires only above the one cart where it isn't true.
- **Screens:** f-set-feature-08-cart-top-setcart (no line, bundle-only cart),
  f-set-feature-15-pathB-set-plus-dupe-shorts (line present, wrong cart)

### 7. Half a set in the cart — the offer line and where it leads
- **Should:** Cart offers the other half; its mechanism delivers the saving.
- **Did:** Emptied the cart (Remove control works), added only the shorts (M).
  Cart shows, above the "Cart" heading in purple: **"Complete the set — add the
  Cellblock Crewneck, save £10."** — the whole line is a link to
  /products/charcoal-cellblock-crewneck, and it lands correctly on the crewneck
  PDP with the set toggle right there. So far, good. But I then played the
  naive shopper both ways:
  - **Path A — plain ADD TO BAG** (what the line's wording invites): cart is
    now crewneck £50 + shorts £45 = **£95.00 total, no saving**, and the
    set-cart section goes silent — nothing tells you that you are paying £10
    over the advertised set price for identical contents.
  - **Path B — tick the toggle and ADD THE FULL FIT**: cart is now CELLBLOCK
    SET £85 **plus the original shorts £45 = £130.00 with two pairs of
    shorts**, crowned by "SET SAVING APPLIED — £10".
  The only route that honours the promise is: come back to the cart, remove
  your original shorts yourself, then tick the toggle on the PDP — and nothing
  anywhere says so. The offer line's claim ("add the crewneck, save £10") is
  not deliverable by the action it names.
- **Verdict:** partly
- **Shopper impact:** a shopper who trusts the line most likely pays £95 for
  what £85 buys, silently; a shopper who half-understands it ends up at £130
  with duplicate shorts and a congratulatory savings banner. Either way the
  cart made a promise the mechanism can't keep without manual cart surgery.
- **Screens:** f-set-feature-12-cart-half-set-offer, f-set-feature-13-offer-link-landing,
  f-set-feature-14-pathA-95-no-saving, f-set-feature-15-pathB-set-plus-dupe-shorts

### 8. Shorts-side PDP — symmetric offer
- **Should:** The shorts PDP offers the crewneck the same way.
- **Did:** Perfect mirror: **"Cop the full fit — add the matching Cellblock
  Crewneck. Save £10."**, crewneck thumbnail, panel opens to **"CELLBLOCK
  CREWNECK SIZE"** XS–XL, same **£95** struck / **£85 for the set** / **"ADD
  THE FULL FIT — £85"** / "FREE UK TRACKED 24 INCLUDED". Shorts price £45.00
  untouched.
- **Verdict:** works
- **Screens:** f-set-feature-10-shorts-pdp-toggle, f-set-feature-11-shorts-ticked

### 9. Refresh mid-flow — does the tick survive?
- **Should:** Either answer acceptable; record it.
- **Did:** Ticked (button "ADD THE FULL FIT — £85"), reloaded: checkbox back to
  unticked, panel hidden, button **"ADD TO BAG"**. The tick does NOT survive
  reload. That is the safe answer — no invisible state that could sneak an £85
  add onto someone who forgot they'd ticked it — at the cost of re-ticking after
  an accidental refresh (two taps to recover).
- **Verdict:** works

### 10. Overall shopper verdict — trustworthy or dark pattern?
- **Should:** A bundle control a stranger would trust.
- **Did:** **On the PDP, trustworthy — unusually so.** It is opt-in, collapsed
  by default, states the partner and the saving in plain English, pre-mirrors
  your size, shows was/now honestly (£95 → £85), relabels the button so you
  cannot mistake what you're paying, restores perfectly on untick, forgets
  itself on reload, and lands in the cart as one honest line naming both
  garments and both sizes. No urgency, no popup, no pre-tick. The weak seam is
  entirely cart-side: the clean £85 cart never confirms the saving (item 6),
  and the half-set offer line promises a saving that its own click cannot
  deliver (item 7). Neither is malicious — the failure mode is a broken promise,
  not a trap laid on purpose — but item 7 in particular will cost real shoppers
  real money (£10 silently, or £45 in duplicate shorts) and is the one part of
  the feature a shopper could come away calling dishonest.
- **Verdict:** works (PDP control) / partly (as an end-to-end promise)

---

## Not exercised / notes

- **OOS partner path:** all 25 bundle variants in stock; mechanism (aria-disabled
  size + "Cellblock Shorts sold out in [size] — pick another size") observed in
  the page's own data, not live.
- **O1 (10CROOKS stacking):** not crossed in these flows — no discount field on
  the cart page itself; a code-holder would only hit the stack at checkout,
  which this audit did not enter.
- **Passing observation for the cart-area agent:** immediately after removing
  the bundle line on /cart, the header still read BAG [1] against an empty cart
  (single observation, ~2s after the tap; may be timing).
- **Stale spec note:** a Shopify cookie-consent dialog now exists and occupies
  the lower ~40% of the mobile viewport until answered — it overlaps the set
  toggle's screen position on first load of the PDP.
