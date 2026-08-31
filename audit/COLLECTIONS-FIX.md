# COLLECTIONS-FIX.md — why products weren't showing, and what was done (2026-08-31)

## Diagnosis
The main menu's SHOP submenu items carried resourceIds pointing at DELETED
collections: NEW, TEES, DENIM and SWEATS no longer existed (their handles
were still soft-reserved, which is why recreating them yielded -1 handles).
ALL also pointed at a deleted custom collection but survived because
/collections/all falls back to Shopify's automatic catalogue. On top of
that, 11 of 25 active products had a BLANK product type — invisible to the
register's category chips (built from product.type) and to any TYPE-rule
smart collection — and the manual collections were incomplete: PRODUCTS
missing 7 actives, Sets holding 1 of 4 sets, TRACKSUITS 3 of 6 pieces.

## Fixes applied (Admin API, all verified by read-back)
1. **Types set on 11 products**: grey/black Convict hoodies + black Convict
   sweats → Sweats · Crooks Express tee + CRX Garms → T-Shirt · OG Jeans →
   Denim · Hyrdocuff windbreaker → Outerwear · all four SET products → Sets.
   Register chips now cover every card (SETS and OUTERWEAR chips appear
   automatically; chip order setting keeps DENIM, SWEATS, T-SHIRT,
   ACCESSORIES first).
2. **Four smart collections created + published** (Online Store + Shop):
   TEES (type=T-Shirt, 4 live), DENIM (type=Denim, 5), SWEATS (type=Sweats,
   8), NEW (tag=new, 9 live). Handles are tees-1/denim-1/sweats-1/new-1 —
   the bare handles are still reserved by the deleted collections.
3. **Main menu repointed**: NEW/TEES/DENIM/SWEATS items → the new
   collections; ALL converted to the native CATALOG type (/collections/all)
   instead of a dead collection reference.
4. **Manual collections completed**: Sets → all 4 sets; TRACKSUITS → all 6
   Convict pieces (3 colours × hoodie/sweats); PRODUCTS (frontpage) → +7
   (both pinks, black hoodie, all four sets), now 29 (incl. 4 archived,
   hidden on the storefront automatically).

## Owner notes
- Admin counts include archived products (TEES shows 6 in admin, 4 on the
  storefront — Broadcast/3 Clives are archived and hidden).
- The "new" tag drives NEW and still sits on May-era Yard denim; untag
  anything that shouldn't count as new.
- No SETS link in the menu — the four sets are reachable via ALL, the SETS
  register chip, and PDP set toggles; add a menu item if wanted.
- If the bare handles (tees, denim, sweats, new) free up, the -1 handles
  can be renamed in admin; the menu uses IDs, so nothing breaks either way.
