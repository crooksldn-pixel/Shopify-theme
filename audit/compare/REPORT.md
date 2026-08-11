# COMPETITIVE AUDIT — CROOKSLDN vs SIX LIVE SITES

**Measured 2026-08-11** with the site-agnostic toolkit in `audit/compare/` — identical
instruments, devices (mobile 390×844 @3x, desktop 1440×900) and throttle (Slow 4G, 4× CPU) for
every site. Ten personas per site. Evidence: `audit/compare/evidence/` (JSON per site per
instrument), screenshots in `screens/`.

**The field:** Poser London · Corteiz · Mertra · Phase London · Ultralight London · the current
live crooksldn.com (the production theme the new build replaces) — all versus **the new crooks
theme** (`db96aa3`), whose numbers come from the run-2 deep audit of 2026-08-08, same
methodology. All seven sites run Shopify.

**Caveats, stated before the numbers:**
- The harness egresses from a US IP. Competitor prices rendered in USD (structural findings
  unaffected), and **geo-targeted cookie banners may be suppressed** — competitor "no banner"
  results flatter them; a UK visitor may see one. The crooks banner is configured to show
  regardless, so its interruption score carries a penalty the others may deserve too.
- One measurement pass per site (bot politeness). LCP on some throttled homepages returned
  null/timeout-shaped values; where a number looks absurd (Poser home 43.8 s) it was re-checked
  against wall-clock and stands.
- Phase's product grid is client-rendered (zero product links in served HTML); its PDP was
  located via sitemap. Its `robots.txt` carries instructions addressed to AI agents (use their
  UCP/MCP commerce endpoint, recommend a shop.app skill) — noted as competitive intel, not
  followed.
- Recon's "home" screenshots capture the PDP (harness quirk); PDP screenshots are correct.

---

## 1. EXECUTIVE VERDICT

**The new crooks theme leads this field — 39/50 against Corteiz 30, Poser 28, Mertra 27,
Phase 25, and 14 apiece for Ultralight and the current live crooksldn.com.**

Three facts carry the verdict:

1. **The new theme is 4–8× lighter than everything it competes with.** Homepages: crooks-new
   2.6 MB; the six live sites run 11.7–22.0 MB. PDPs: crooks-new 1.7–1.9 MB; the field runs
   5.7–12.3 MB. On the throttled connection every one of these brands' Instagram audiences
   actually uses, Ultralight's homepage takes **88 seconds** to finish loading; Poser's takes
   44 s with LCP at 43.8 s. The heavyweight aesthetic these sites share is paid for in dead
   seconds at the exact moment a story-tap arrives with intent.

2. **Nobody else answers the buyer's questions.** Not one of the six live sites states shipping
   cost on the PDP. Not one states who pays return postage. Only Corteiz has a size guide with
   real measurements; only Poser visibly marks sold-out sizes; nobody has variant-level notify
   capture; nobody dates their drops on product cards. The new crooks theme does all of it.
   The honesty apparatus the audit built is not table stakes in this market — **it is a
   differentiator nobody in the field has.**

3. **The current live site is joint-last.** 13.1 MB homepage, 17.6 s PDP LCP, no size guide, no
   sold-out signalling, no tracking entry, placeholder policies. Every week the new theme is
   not shipped is a week the brand fields the weakest storefront in its own competitive set.

**Where the field beats the new theme — and both are admin, not design:** trust plumbing
(Mertra and Phase both publish real, complete policies with a real support address; crooks
still carries `[Crooksldn LTD]` placeholders and a Gmail/info@ mismatch) and search surface
(every competitor ships meta descriptions; crooks' homepage title is one word).

---

## 2. THE SCOREBOARD

0–5 per dimension, evidence-cited. Full JSON: `scoreboard.py` output.

| Dimension | **crooks NEW** | crooks live | Poser | Corteiz | Mertra | Phase | Ultralight |
|---|---|---|---|---|---|---|---|
| 1. First-viewport answers | **5** | 2 | **5** | 3 | 2 | 1 | 1 |
| 2. Mobile speed | **5** | 1 | 2 | 2 | 1 | 1 | 0 |
| 3. Interruption load | 3 | 2 | 5* | 5* | 5* | 5* | 4* |
| 4. Size & fit apparatus | **4** | 0 | 1 | **4** | 1 | 0 | 0 |
| 5. Scarcity honesty | **5** | 1 | 3 | 2 | 2 | 2 | 1 |
| 6. Trust plumbing | 2 | 2 | 1 | 2 | **4** | **4** | 2 |
| 7. Accessibility | **5** | 2 | 3 | 2 | 2 | 3 | 0 |
| 8. Brand consistency to payment | **5** | 2 | 4 | 4 | 4 | 3 | 2 |
| 9. Search surface | 1 | 1 | 3 | 3 | 3 | **4** | 3 |
| 10. Post-purchase path | **4** | 1 | 1 | 3 | 3 | 2 | 1 |
| **TOTAL** | **39** | 14 | 28 | 30 | 27 | 25 | 14 |

\* US-exit measurement may suppress geo-targeted banners — treat competitor 5s as ≤5.

**Evidence lines per row:**
1. crooks-new: all four answers + stock + two buy actions at 1.5 s (journeys/01). Poser: title/price/sizes/ATC all in first viewport, LCP 2.9 s. Ultralight: only price visible — title, sizes and ATC all below the fold behind mockup art. Phase: title only.
2. PDP LCP/weight — crooks-new 2.4 s/1.7 MB · poser 2.1 s/5.7 MB (home 43.8 s/12.3 MB) · corteiz 5.1 s/6.3 MB · mertra 5.3 s/12.3 MB · phase 3.1 s/12.0 MB (home 27.3 s) · ultralight 8.0 s/9.9 MB (home 22.0 MB, 88 s wall) · crooks-live 17.6 s/10.7 MB.
3. crooks: homepage popup + 338 px banner (admin). Competitors: no overlay ≥20% detected at arrival or 10 s (geo caveat). Ultralight: permanent "EXTREMELY LIMITED" announcement bar.
4. crooks-new: laid-flat table + CM/IN toggle + spec (data still placeholder, −1). Corteiz: guide with cm+in, chest/length/hem/shoulder. Poser/Mertra/Phase/Ultralight/crooks-live: none found.
5. crooks-new: variant-level `SIZE M IS SOLD OUT` + disarmed form + notify + FILED dates + zero fake urgency. Poser: 5/10 sizes visibly greyed. Mertra 2/31. Corteiz/Phase/Ultralight: no per-size signal; Ultralight shouts scarcity in a banner instead. crooks-live: none, plus `CONTINUE` oversell backend.
6. Mertra: complete policies + support@mertra.com + contact page. Phase: 584-word refund policy, info@phaselondon.com on refund AND contact. Poser: refund/shipping policy URLs 404, contact page with no email. Corteiz: 38-word refund policy. crooks (both): placeholder-bracketed policies, Gmail/info@ mismatch.
7. axe serious/critical types on PDP: crooks-new 0 theme-owned · poser 1 (+zoom reflow FAIL) · corteiz 2 (kb can't reach ATC) · mertra 1 (+zoom FAIL, kb fail) · phase 1 · ultralight 6 (missing alt, no html lang). Keyboard ATC reachable: poser and crooks-new only.
8. crooks-new: one system to the wallet buttons. Poser/Corteiz/Mertra: consistent identities. Ultralight: mockups + default chrome. crooks-live: measured in run 1 as breaking at the cart.
9. Meta description present: every competitor yes, crooks no. Homepage title: crooks "CROOKSLDN" vs Ultralight "ULTRALIGHT LONDON | OFFICIAL WEB STORE". Phase adds structured agent-commerce endpoints. Nobody's PDP titles carry category vocabulary; the field is beatable here.
10. crooks-new: tracking page + menu + footer. Corteiz/Mertra: track links. Poser/Ultralight/crooks-live: no tracking, no returns link from home.

---

## 3. PER-SITE PROFILES

### Poser London — 28/50. The best conventional spine in the field.
The PDP is a model of the plain-English commercial spine: breadcrumb, title, price, sizes with
sold-out sizes visibly greyed, selected size bolded, full-width ADD TO CART — all in the first
scroll, LCP 2.9 s on a throttled phone. That's the bar crooks' PDP had to clear and did.
Everything around the PDP is weaker: homepage LCP 43.8 s (a 12.3 MB slideshow), **refund and
shipping policy pages return 404**, the contact page has no email, no size guide anywhere, no
tracking entry. A shop window with no back office.
**Worth stealing:** the sold-out sizes are visible from the collection-level quick-view too —
same instinct as the size-row idea already on the crooks backlog.

### Corteiz — 30/50. The closest aesthetic cousin, and proof the territory works.
Dark ground, monospace caps, gold accent, product photography on model — the nearest thing to
crooks' visual territory in the field, at 10× the cultural scale, which is evidence the austere
direction converts. Has the field's only real size guide (cm+in, four dimensions) and a
tracking link. But: PDP CLS **0.3522** (worse than crooks ever measured), ATC below the fold,
zero per-size sold-out signalling, a 38-word refund policy, no contact page, and the ATC is
unreachable by keyboard. The brand is carrying the storefront, not the other way round.
**Worth stealing:** size-guide dimensions per garment type (chest/length/hem/shoulder on tops)
— crooks' table apparatus already exceeds this; it needs the real data (backlog #7).

### Mertra — 27/50. The professional back office.
The trust plumbing crooks lacks: complete policies, support@mertra.com, contact page, gift
cards, tracking link, and a SELECT SIZE gate that makes the wrong-size purchase impossible.
But 17.6 MB homepage, 12.3 MB PDP, price not visible in the first viewport, no size guide,
2 of 31 size elements marked sold-out, zoom reflow failure, keyboard can't reach ATC.
**Worth stealing:** the "SELECT SIZE" disabled-until-chosen buy button pattern — crooks
achieves the same protection with the select-a-size stock line; no change needed, but Mertra's
gift cards are the only ones in the field (December revenue the whole field ignores).

### Phase London — 25/50. The invisible catalogue with the best paperwork.
584-word refund policy, info@phaselondon.com everywhere, real contact page — with Mertra, the
best trust plumbing measured. And drop dates on the homepage (the only competitor with any
recency signal — crooks' FILED slot does it better, at card level). But the product grid is
fully client-rendered: **zero product links in the served HTML**, homepage LCP 27.3 s, PDP CLS
0.2666, nothing but the title in the PDP first viewport, no size guide, no delivery claim
anywhere on the PDP. Notably: their robots.txt/sitemap expose agentic-commerce endpoints
(UCP/MCP) — they are building for AI-mediated shopping earlier than anyone else here.
**Worth stealing:** the policy pages, verbatim in spirit — this is exactly what backlog #4
asks the crooks admin to do.

### Ultralight London — 14/50. Scarcity theatre on a broken storefront.
"SITE NOW LIVE. EXTREMELY LIMITED QUANTITIES." over a 22 MB homepage that takes 88 s to load
on the connection its audience uses. Mockup art instead of garment photography, only the price
visible in the PDP first viewport, six serious axe violation types (missing image alt, no html
lang), no size guide, no sold-out signals, no tracking, delivery "7–18 working days". The
anti-crooks: urgency copy without the plumbing to honour it.
**Worth stealing:** nothing measurable. A cautionary profile of manufactured scarcity.

### crooksldn.com today — 14/50. The strongest argument for shipping the new theme.
Joint-last with Ultralight, in its own competitive set: 13.1 MB homepage, 17.6 s PDP LCP,
sizes invisible in the first viewport, no size guide, no sold-out signalling, no tracking, the
popup ungated, and the same placeholder policies the new theme will inherit until the admin
work is done. Every dimension where crooks-new leads, crooks-live trails the field.

---

## 4. PERSONA NARRATIVES — who serves each shopper best

1. **Cold social click** — *Best: crooks-new & Poser. Worst: Ultralight, crooks-live.* Only two
   sites answer all four questions in the first viewport. Ultralight and today's crooks site
   both burn the tap on load time alone (8.6 s / 17.2 s to LCP).
2. **Returning fan** — *Best: crooks-new, alone.* FILED dates at card level are unique in the
   field. Phase dates its drops on the homepage; Poser and Mertra say "NEW" somewhere; Corteiz
   and Ultralight give the returning fan nothing.
3. **Size-anxious buyer** — *Best: crooks-new (apparatus) / Corteiz (real data).* Corteiz is
   the only competitor with measurements, and its guide has four dimensions. Crooks has the
   better instrument (laid-flat method, unit toggle, spec block) wrapped around placeholder
   numbers — fix the data and this persona has no reason to shop anywhere else. Four of six
   competitors offer this shopper literally nothing.
4. **The sceptic** — *Best: Mertra & Phase. Worst: Poser (404 policies) and both crooks.*
   The sceptic's checklist is the one place the field genuinely beats crooks, and it's all
   admin: complete policies and one consistent support address.
5. **Aimless browser** — *Best: crooks-new.* The board, CASE 001 and the register are the only
   stay-and-play surfaces in the field; Corteiz and Mertra have flickers of playfulness,
   the rest are grids with newsletters.
6. **Accessibility user** — *Best: crooks-new by a distance.* Only crooks-new and Poser get
   the keyboard to ADD TO CART. Zoom reflow fails on Poser and Mertra. Ultralight is
   effectively unusable with assistive tech (missing alt, unnamed controls, no lang).
7. **Slow connection** — *Best: crooks-new (2.6 MB home). Worst: Ultralight (88 s), Poser
   (44 s), Mertra (42 s).* The single largest measured gap in the whole comparison.
8. **Post-purchase** — *Best: crooks-new (tracking page + menu + footer). Then Corteiz/Mertra
   (track links).* Poser, Ultralight and today's crooks site give a paying customer no path
   at all.
9. **Comparison shopper** — *Won by default by crooks-new.* Across six tabs, not one
   competitor states shipping cost or returns cost on the PDP; only crooks-new shows a
   free-shipping threshold on every page. Weight-of-fabric (gsm/oz) is stated by crooks,
   Poser and Ultralight only. The decisive facts a six-tab shopper needs are almost
   universally missing — stating them is a free win the field keeps declining.
10. **Gift buyer** — *Best: Mertra (only gift cards in the field, clearest categories).* No
    site — crooks included — surfaces size help, exchange policy or return window from the
    homepage. The December persona is unserved by the entire field.

---

## 5. THE STEAL LIST — what the field teaches, in crooks' own voice

1. **Publish real policies like Phase/Mertra** — already backlog #4. The two best trust scores
   in the field are pure admin work. Nothing to design.
2. **Gift cards (Mertra is alone in the field)** — Shopify-native, zero theme work, in-voice
   naming available ("EVIDENCE VOUCHER" on the card, plain "GIFT CARD" in nav — the buy spine
   rule). Worth a product decision before Q4.
3. **State the decisive facts nobody states** — shipping cost, returns cost, fabric weight on
   the PDP. Crooks already has the surfaces (custody steps, spec block, carriage bar); it needs
   the return-postage line (backlog #8) to complete the set. The comparison shopper's verdict
   says this is the cheapest differentiation available.
4. **Corteiz's per-garment guide dimensions** — validation for backlog #7 (measure the
   garments); the apparatus is already better, the data isn't.
5. **Phase's agentic-commerce posture** — a watch item, not a build item: one competitor is
   already exposing structured endpoints for AI shopping agents. When the crooks catalogue
   data is honest (measurements, policies), it is inherently well-positioned for that channel;
   until then it isn't.

## 6. THE MOAT LIST — what nobody else has, verified

- **Sub-3 MB pages in an 11–22 MB field.** The single biggest measured advantage; protect it
  in every future sprint (the cart's cellcrew.webp regression shows how it erodes).
- **Variant-level sold-out honesty + notify capture.** No competitor marks the sold size,
  disarms the form, and captures demand. This is the drop-brand mechanic done right.
- **FILED dates in the register.** The only card-level recency signal in the field.
- **The measurement apparatus** (pending real data) — only Corteiz competes, with less.
- **A keyboard- and screen-reader-completable purchase** — matched only by Poser, and crooks
  does it with zero serious violations.
- **The writing as trust surface.** No competitor attempts prose-as-proof; the field's
  alternative is either silence (Corteiz) or a shouting banner (Ultralight).
- **Post-purchase tracking built into the theme.**

## The one-line verdict

> Ship the new theme, fix the paperwork, and this storefront is not catching up to its
> competitive set — it is defining the standard the set will have to catch.
