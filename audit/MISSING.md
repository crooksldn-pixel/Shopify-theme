# MISSING.md — everything a shopper expected and couldn't find

Distinct from broken (see `features/FEATURES.md` for those): a missing thing
needs a decision to build, buy, or deliberately decline — not a repair.
Grouped by who missed it. Persona numbers in brackets.

## Things that cost identified sales in this audit

| What | Who missed it | The cost, in their words |
|---|---|---|
| **A gift card** | 09 | Searched "gift card" → 0 results. "You literally sell to teenagers. Who do you think pays for teenagers?" Left £19–25 of intended spend behind. A real Shopify product — no fabrication, no design-law breach. |
| **Measurements on every sized garment** | 09, 11 | Coverage is a per-product lottery: jeans/baggies/one tee have the site's proven closer; the £50 crewneck, £85 set, CRXST★RZ tee and socks have nothing. Cost 09 the crewneck sale outright; 11 said it "would have made this a two-item order." Data gap — the component exists. |
| **A second photo / front view / named colour for the grey jeans** | 10 | One dark back-shot, wash unreadable on the dark theme, no colour word anywhere in the text. Bought blue instead: "the grey's real shade is a gamble the site never resolves." Grey colour-confidence 5–6/10 vs blue 9/10. |
| **Any statement of whether drops restock** | 06 | The notify form says "when this size is back" but no surface says whether *back* ever happens. FAQ has 15 questions, none about restocks — for a drops brand, the most on-brand question there is. |
| **A neutral "pick a size" state** | 01, 04, 06, 08, 09, 16, 17 | XS is silently preselected everywhere; the sticky bar reads "£60.00 · XS" untouched. Not a missing feature so much as a missing *absence* — the wrong-size-order risk is carried by gift buyers, zoom users and screen-reader users. |

## Gift buying (persona 09's list, in full)

- Gift card (above).
- Gift note / message field — cart has no note field at all; checkout has no gift options.
- Gift receipt / price-hiding.
- A standalone size-guide page shareable without the product link ("what size are you?" without spoiling the present).
- Body-size guidance anywhere — tables are flat garment measurements only; no "model is 6'1" and wears L".
- Socks state no size (variants are pack quantities) — even the safe gift is unlabelled.
- Counterweight, for the record: the evidence-bag packaging is de facto gift wrap and the free UK size-swap policy is genuinely gift-friendly — neither is *told* to gift buyers.

## Product confidence

- **Gallery zoom, in any form** (M-1; 10, 19). Two photos per product, tap does nothing, £60 garments judged on fabric detail.
- **On-model photos** — the `model_image` metafield is empty for all 14 products, so the ON MODEL toggle shows one placeholder man on every card (10's worst moment; 11: hide the toggle until photos exist).
- **Colour/wash named in product text** (10).
- **Restock/drop-model explanation** (06, above).

## Money clarity

- **Sub-£20 shipping prices anywhere before checkout** (M-6; 07) — the £3.00/£4.99 figures exist only in the shipping policy until an address is entered; the free thresholds are loudly advertised everywhere.
- **A "full policy" link inside the custody accordion** (M-7) — the summary is good; the trip to the footer is unnecessary.
- **The £10 set saving restated in cart/checkout** (04, 05) — the £95 anchor vanishes after the PDP; checkout's "TOTAL SAVINGS" line understates what the shopper actually saved.

## Wayfinding and chrome

- **ACCOUNT in the header** (M-5) — it lives below the board at the bottom of the drawer.
- **The header wordmark** (M-4) — inner pages carry only the handcuffs logo; SPEC says a wordmark should render.
- **A RETURNS link in the footer** (20) — REFUNDS is the decoy that cost her a 7-tap trail; the returns centre is linked only from FAQ answers and Terms clauses.
- **Guest order lookup on /pages/tracking** (20; RUN3 A6) — the FAQ promises it, the returns centre proves the mechanism exists (order number + email), the tracking page doesn't have it.
- **Cart size/variant editing** (08) — rows offer qty and bin only; a size swap means re-add plus manual removal, and the cart silently holds both sizes meanwhile.
- **Undo after remove** (cart agent) — remove is labelled and works; there is no way back.

## Feedback

- **A visible add-to-bag confirmation at the point of tap** (04, 07, 08, 13, 14, 17, 19) — the aria-live line exists (and is exactly right for screen readers — protect it); sighted shoppers adding via the sticky bar see nothing, and desktop sees nothing at all. Three double-adds and one abandoned checkout trace to this.
- **Any state on CHECKOUT NOW when the selected size is sold out** (01, 06) — it stays lit and silently no-ops.

## Trust furniture the brand may *deliberately* decline (flag, don't assume)

- **A legal identity** — no company name or number anywhere; Terms are excellent but unsigned (02).
- **An explanation of "Oairo UK Office"** on the returns address (02).
- **A non-gmail support address** (01, 02) — `info@crooksldn.com` is already the theme's footer default per RUN3 B2; the gmail is what's actually published.
- **Desktop hover states** and a desktop sticky buy bar (19) — the custom UI acknowledges the mouse only in the drawer.
- **Checkout and login branding** (02, 13, 17, 19, 20) — both are config surfaces, not theme code; the white stock skin and `friendsof.crooksldn.com` are the two biggest off-brand jolts on the money path.

## Homepage

- **The lookbook's content** (M-3) — the section renders 0px.
- **The hero's second button** — configured for two, carries one.
- **A working signup mechanism** — the informant intake renders no fields (B-1, filed as broken, listed here because a shopper simply experiences "no way to sign up").
