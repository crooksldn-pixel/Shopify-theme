# SUMMARY.md — twenty journeys, distilled

Twenty scripted personas, 2026-08-18 evening, staging theme `202053779799`,
GB market pinned, staging verified per session. Full logs in this directory;
screenshots in `../screens/` prefixed by persona number.

## The scoreboard

| # | Persona | Outcome | Min | Why |
|---|---|---|---|---|
| 01 | Cold Instagram click | didn't | 3 | L/M/XL sold out; restock signup killed by hCaptcha |
| 02 | The sceptic | **bought** (PayPal-only) | 25 | policies + rails outweighed zero reviews |
| 03 | Size-anxious denim | **bought** (L) | 21 | the measurement table closed it |
| 04 | Set buyer | **bought** (set £85) | 7 | struck-through £95→£85 converted the upsell |
| 05 | Set sceptic | **bought** (set, code) | 11 | came to catch a fake bundle, verified a real one |
| 06 | Sold-out hunter | didn't | 8 | M gone; captcha ate the notify signup; followed IG instead |
| 07 | £6 impulse | **bought** (£9 total) | 6 | fastest journey on the site — 8 taps |
| 08 | Basket builder | **bought** (£85 after 7 edits) | 16 | cart maths held through every edit |
| 09 | Gift buyer | **bought** £31 of intended £50+ | 24 | crewneck abandoned: no size info, no gift card |
| 10 | Comparison shopper | **bought** (blue) | 13 | photo asymmetry decided it, not preference |
| 11 | The tinkerer | **bought** (jeans M) | 35 | cm/in table closed the sale; O3 verdict filed |
| 12 | The searcher | didn't (not shopping) | 13 | got answers, then 14-vs-30-day contradiction postponed her order |
| 13 | Mobile landscape | **bought** (after double-add fiasco) | 16 | layout survived; cart overlap didn't |
| 14 | Slow connection | didn't | 12 | checkout showed £12 for £6 socks (CHECKOUT NOW re-add bug) |
| 15 | Keyboard-only | **bought** | 12 | nothing impossible anywhere on the path |
| 16 | Screen reader | **bought** | 28 | every buying-critical state announced |
| 17 | 200% zoom | **bought** | 19 | theme never broke at 200% |
| 18 | Reduced motion | **bought** | 14 | "calmest streetwear site she's used" |
| 19 | Desktop shopper | **bought** (set) | 30 | set flow sold it; desktop feels second-class |
| 20 | Post-purchase | n/a (service visit) | 13 | tracking dead-ends guests; returns centre works |

**15 of 20 reached checkout.** Not one abandonment was caused by how the site
looks — the terminal aesthetic converted sceptics and survived every
accessibility profile. The five non-purchases: sold-out stock ×2 (compounded
by the captcha eating the restock lead both times), one self-contradiction
(returns windows), one cart bug (double-add), one non-shopping mission.

---

## The five worst moments

1. **"REVEAL MY CODE" does nothing** *(17, reproduced across sessions)*. Win
   the Crack the Cuffs game → forced to hand over phone + SMS consent (step 1)
   → email (step 2, reads optional, isn't) → the reveal button silently never
   produces a code, an error, or a spinner. The shop takes two pieces of
   contact data and gives nothing back. This is the single worst thing on the
   site: it converts the brand's honesty story into its opposite, invisibly.
2. **CHECKOUT NOW charged the £6 shopper £12** *(14; kin in 13, 17)*. The
   sticky bar's CHECKOUT NOW posts another `/cart/add` for the current product
   before redirecting, so ADD TO BAG followed by CHECKOUT NOW = quantity 2.
   Trevor backed out at the till: "Twelve quid? For socks?" A first tap that
   did nothing for 30s nearly ended it earlier. Silent add feedback caused
   sibling double-adds in 13 (landscape) and 17 (zoom).
3. **The bag said £76.50, the till said £85.00** *(05; Phase 1 B-5)*. A
   discount applied in the cart's own field does not survive the hop to
   checkout; the code chip vanishes and the field is empty. "A trusting
   shopper would have paid the difference without ever knowing." (Preview→live
   domain handoff is the suspect — one live retest decides it.)
4. **The captcha ate two warm £60 leads** *(01, 06)*. Sold-out size → honest
   red state → notify form → submit → full-screen hCaptcha puzzle → dismiss →
   form sits as if never submitted, email still in the box, no confirmation
   either way. Both personas left not knowing if they'd signed up; one
   followed Instagram *because they didn't believe the notify email exists*.
5. **"9-16 days delivery uk" one accordion above "UK 1–2 working days"**
   *(02, 03, 10)*. Three personas independently hit it at the exact decision
   moment; the sceptic named it "the AliExpress line". It nearly killed sale
   02 and forced PayPal-only caution. The same family: baggies say
   "3-5 day delivery uk", and the jeans' SPECIFICATION says "OG straight"
   while the description says "baggy, stacked" (03).

---

## Appeared in three or more journeys

**Negative:**

- **The Crack the Cuffs popup is the most-complained-about object on the site
  (12 of 20 journeys).** It renders on top of the cookie banner (02, 18, 20);
  paints 4–8s late as an empty dimmed box (13, 19); is unplayable in
  landscape (13); never takes keyboard/SR focus — a silent `aria-modal` trap
  whose × sits after the iframe in tab order (15, 16); ignores
  `prefers-reduced-motion` while "one attempt per customer" burns the shot of
  anyone who closes it in self-defence (18); deters players who already hold
  a code (04, 05); demands phone + SMS consent before naming the discount
  (11, 19); uses mm/dd/yyyy on a UK store (17); and its prize mechanism is
  broken outright (17). The game itself is fun (11: "genuinely fun") — the
  delivery mechanism is what's rotten.
- **Silent add-to-bag** (7 journeys: 04, 07, 08, 13, 14, 17, 19). The quiet
  `> Added — 1 in bag` line is below the fold when adding from the sticky
  bar, the header (and its BAG count) has scrolled away, and desktop gets
  nothing at all. Direct cause of double-adds in 13, 14, 17 and a removed
  impulse add-on in 19. Related: the two-garment set shows as BAG [1]
  (04, 05, 19); the badge goes stale during cart-page edits (08, 17).
- **XS silently preselected on every apparel PDP** (7 journeys: 01, 04, 06,
  08, 09, 16, 17). No neutral "pick a size" state exists; the sticky bar
  reads "£60.00 · XS" before the shopper touches anything. Wrong-size-order
  risk for gift buyers, zoom users and screen-reader users alike; the set's
  silent size-mirroring (04) is the same family.
- **Sold-out blindness until the PDP** (01, 06 + Phase 1): every card says
  AVAILABLE; three of five baggies sizes are gone. Once discovered, the
  blanket label "conveys zero information and reads as a broken promise" (06).
  And nothing anywhere says whether drops ever restock (06) — the notify form
  promises "when it's back" on a site whose model is runs that don't return.
- **Filter resets on browser back** (10, 19 + Phase 1) — punishes exactly the
  comparison behaviour the register invites.
- **ON MODEL toggle misleads** (10, 11, 19 + Phase 1): all 14 cards swap to
  the same placeholder man; the jeans card stops showing jeans. 10's worst
  moment; 11's verdict: hide it until real photos exist.
- **Measurements are a per-product lottery** (03, 09, 11 + Phase 1): jeans
  yes, £50 crewneck no, £85 set no; two same-price tees differ; and
  jeans + baggies serve byte-identical tables that a two-product shopper can
  catch. Where it exists it sells (03, 11 both credit it as the closer).
- **Returns-route contradictions** (09, 12, 20 + Phase 1): the AfterShip
  portal says **30 days from purchase** against the site's 14-from-delivery
  (12 — postponed her order over it); the refund policy says "email or DM"
  and never mentions the portal the FAQ/Terms route through (20 — a 7-tap
  decoy trail); the FAQ's "Start your return here" links to the terms page,
  not the portal it promises (09).
- **Off-brand third-party surfaces jolt** (02, 13, 17, 19, 20): stock white
  checkout ("brand costume-change"), the `friendsof.crooksldn.com` login
  (20: "momentary phishing suspicion"), AfterShip's white theme + second
  cookie banner, cream contact/404 pages (02).
- **Cookie banner is every session's first tap** (nearly all): 40–60% of the
  viewport, covers the sticky buy bar on PDPs until answered (14), stacks
  under the popup on first visit (02, 18, 20). Behaves correctly once
  answered; Decline works first time (05).

**Positive (three or more):**

- **The measurement apparatus closes sales** (03, 11, 16, 19): method stated,
  cm/in honest both directions, SIZE GUIDE lands the heading at y=0 with the
  selected size pre-highlighted. 03: "the single reason the purchase happened."
- **The set mechanic converts and survives scepticism** (04, 05, 19): honest
  £95 anchor verifiable on-page (MORE FROM THIS DROP shows the shorts at
  £45), partner size pre-mirroring, one clean £85 cart line naming both
  garments. Two personas came for £50 and left committing £85.
- **The buy spine in plain English + honest states** (01, 02, 16, 18): red
  SIZE SOLD OUT, real "3 LEFT" from inventory, no fake urgency anywhere —
  sceptics repeatedly cite the *absence* of tricks as the reason they stayed.
- **Accessibility is a clean sweep** (15, 16, 17, 18 all bought): keyboard
  end-to-end with a consistent 2px ring, textbook drawer dialog, aria-live
  add confirmation, aria-pressed sizes, zero horizontal scroll at 200%, and
  a reduced-motion experience with literally zero running animations. The
  only accessibility failures on the site are third-party: the popup and the
  payment iframes.
- **Slow-connection resilience** (01, 14 + Phase 1): readable at ~3s on slow
  4G, zero layout shift at 3/5/10s, dark ground hides image lag. 14: "wait,
  not leave."
- **Search as a route to answers** (07, 12): auto-focused field, typeahead
  with photos, 1-tap policy routing via direct links — the impulse buyer's
  fastest funnel and the searcher's rescue. Caveats: "returns" is the one
  natural word that dead-ends on-site (0 results + off-site portal), and the
  big "0 RESULTS" overshadows the small direct-link answer (12).
- **The packaging section is the homepage's sleeper asset** (09 best moment,
  homepage agent's best block): the evidence-bag presentation is de facto
  gift packaging and the most memorable thing on the page now that the board
  lives in the drawer.

---

## Smaller but real (one or two journeys, worth keeping)

- CHECKOUT NOW stays visually live beside SOLD OUT and no-ops silently (01, 06).
- Landscape cart: thumbnail overlays title, unit price and the minus button —
  taps navigate to the PDP instead of decrementing (13).
- V2 BAGGIES is categorised SWEATS; a shopper tapping DENIM for baggies
  dead-ends (18).
- Sock packs create a free-shipping dead zone: no sock-only basket can reach
  £20 without the 6-pack (07).
- Tracked 48's checkout estimate said 28 Aug (10 days) beside Tracked 24's
  20–21 Aug — "what is the 48 doing for ten days, walking?" (07, 14-adjacent).
- No gift card, no gift note, no body-size guidance, socks don't state a size
  — the gift buyer had no safe purchase (09).
- Desktop: no hover states in the custom UI, hero uses half the width, no
  sticky buy bar, empty grid cells render as bare purple slabs (19).
- Cart "You may also like" recommends items already in the cart (08, 19).
- Grey jeans have one back-shot photo and no colour named in text; the wash
  is unreadable on the dark theme without LIGHT MODE (10).
- "14 ITEMS" header never updates when filters narrow the register (19,
  homepage agent).
- Light-mode search: the submit button is near-invisible (Phase 1; corroborated
  by the light-mode passes in 10, 11).
