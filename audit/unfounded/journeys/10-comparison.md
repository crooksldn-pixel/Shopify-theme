# 10 — Ryan, the comparison shopper deciding between two polos (and eyeing a hoodie for later)
**Device:** iPhone-class mobile 390x844, normal network · **Goal:** decide between the Italy Polo (£23) and Portugal Polo (£25), and scout the Bird hoodie grey vs black for a later buy — he compares everything before spending anything · **Mood:** methodical, unhurried, wears XL, hates re-finding things

*(Session note: pinned to `?country=GB` throughout — the audit egress IP geo-renders USD otherwise. All prices below are the GBP view a UK shopper gets.)*

### Step 1 — Opened the menu looking for a "Polos" category
**Did:** Landed on the homepage, dismissed the newsletter popup ("NO THANKS"), opened the hamburger menu.
**Got:** Six entries: Home, Shop all, Contact, England Set, Nations Shorts, All products. No Polos, no Tops, no per-garment categories at all. (Harness aside: even guessing `/collections/polos` returns a 404 "Oops!" page, and the store's own collections index lists just six unlabelled image tiles.)
**Expected:** A product-type menu — Polos, Tees, Hoodies — like every other clothes shop.
**Felt:** "So the menu is 'everything' or two random collections. Fine, Shop all it is."
**Next:** continued (u10-01, u10-02, u10-03, u10-07)

### Step 2 — Shop all: 44 products, my two polos aren't even on the same page
**Did:** Opened Shop all, scanned page 1, then opened the Filters drawer, then tried sorting by price.
**Got:** "44 products" over 3 paginated pages, in no useful order — page 1 has the Brazil, England and France polos but neither Italy nor Portugal. The filter drawer offers exactly two things: Availability (IN STOCK / OUT OF STOCK) and a Price range. No size filter, no colour, no product type, and no compare tool anywhere. Sorting price low-to-high finally put Italy Polo in row 1 (£23, next to the £18 Argentina shorts) and Portugal Polo in row 2 (£25) — one flick apart, but that's a workaround, not a feature. Silver lining: the IN STOCK filter exists, and in a store where most things are sold out that's the single most useful control on the site.
**Expected:** Tap "Polos", see all six polos in one grid.
**Felt:** "I'm doing the shop's merchandising for it. Price sort as a way to find two shirts — okay."
**Next:** continued (u10-08, u10-13, u10-14, u10-15, u10-16)

### Step 3 — Search "polo": the comparison view the site never built
**Did:** Gave up browsing and searched "polo".
**Got:** 6 results, and the first row is exactly my A/B: ITALY POLO £23 and PORTUGAL POLO £25 side by side, same-style flat-lay photos, prices underneath, quick-add "+" buttons, size chips on each card. This one screen is the entire side-by-side comparison the store offers — and it's genuinely decent: colours, prices and names in one glance. Both cards claim "Available in 5 size" (sic).
**Expected:** Some way to see both shirts together — got it, by accident of search.
**Felt:** "There we go. Blue/navy/yellow versus red/green. Why is one £2 more? The cards don't say. And '5 sizes' — we'll see."
**Next:** continued (u10-11, u10-12)

### Step 4 — Italy Polo PDP: good photos, zero words, no zoom
**Did:** Tapped the Italy card (tap 1). Read everything, tried to zoom the photo.
**Got:** £23, TAXES INCLUDED, "Please Allow 2-5 Working Days For Item To Be Shipped" — and that is the whole description. No fabric, no weight, no fit note. 3 photos: crisp flat-lay front, a group shot of all polo colourways with a size-chart table (pit-to-pit/length/sleeve in inches, XS–XL), and a proper lifestyle shot of two models outside a London estate. Tapping the main image does nothing — no lightbox, no pinch-zoom modal, nothing. Size chips: XS/S/M/L/XL all suffixed "- IN HAND", but S, M and L are struck through — only XS and XL are real. "Only 9 left in stock. Order soon." Below the fold, "You may also like" includes the Portugal Polo — the one cross-link that makes this comparison cheaper.
**Expected:** A sentence about the fabric, and tap-to-zoom to judge the pique/jersey texture.
**Felt:** "Photos are honestly good — the on-body shot tells me the fit is boxy. But I can't zoom, and you won't tell me what it's made of. £23 for… cotton? Poly? Mystery."
**Next:** continued (u10-17, u10-18, u10-19)

### Step 5 — The round-trip loop: back, Portugal, back, Italy again — 5 taps
**Did:** Back to search (tap 2) → Portugal Polo (tap 3) → back (tap 4) → Italy again for a second look (tap 5).
**Got:** The back gesture behaved: search results reloaded with my scroll position intact and both cards still there (the query survives in the URL though the search box displays empty). Each PDP, however, always opens fresh at the top — no memory of where I'd scrolled. So one full A/B compare plus one "wait, what was the collar like?" re-check = 5 taps, and every further doubt costs 2 more. (Cheaper path a shopper might not find: Portugal sits in Italy's "You may also like", one tap PDP-to-PDP.) Portugal PDP: £25, identical one-line "description", identical size-chart image (same measurements — so the £2 is NOT for a different cut), only 2 photos (flat-lay + group/size chart — no lifestyle shot), plain XS–XL chips with S/M/L/XL all struck through — XS is the only live size — and "Only 3 left in stock." Nothing anywhere explains why Portugal costs £2 more than Italy; if anything Italy gives you more (an extra photo, more sizes, more stock).
**Expected:** Some state to survive — it mostly did on the search page — and some reason for the price gap.
**Felt:** "Comparison verdict basically writes itself: Portugal is £2 more, shows me less, and doesn't exist in my size. Same measurements chart on both, so it's the same shirt in different colours at different prices. Why?"
**Next:** continued (u10-20, u10-21, u10-22, u10-23, u10-24)

### Step 6 — The hoodie detour: grey vs black, perfectly side by side, all dead
**Did:** For the later purchase, opened the Hoodies collection and both Bird hoodie PDPs.
**Got:** The collection (banner "Joggers & Hoodies", breadcrumb oddly reads "SALE Black + Grey Items") is actually the best comparison layout on the site: BIRD HOODIE - BLACK and BIRD HOODIE - GREY side by side in row 1, both £35, both wearing SOLD OUT badges before you tap — joggers pair and shorts pair stacked the same way beneath. But colourways are separate products with no swatch and no link between them: the grey PDP's "You may also like" suggests four unrelated football items, never the black hoodie. Both hoodies: 0 of 10 variants buyable (all "IN HAND" and all "PRE ORDER" slots gone), no notify-me. And the price puzzle repeats worse: Bird shorts are £30 in black but £27 in grey — same product, same one-line shipping "description", £3 apart, zero explanation (joggers both £27, hoodies both £35, so it's not a colour surcharge policy — it just looks like a typo you're asked to pay).
**Expected:** A colour swatch on one hoodie PDP; consistent colourway pricing, or a reason.
**Felt:** "The collection grid does grey-vs-black better than the product pages do — shame everything in it is sold out. And charging £3 more for black shorts than grey ones, no reason given, makes the £25 Portugal polo feel less like pricing and more like dice."
**Next:** went back to the polos (u10-25, u10-26, u10-27)

### Step 7 — Decision: Italy Polo, XL — and the stock counter changed its story
**Did:** Back on the Italy PDP, tapped "XL - IN HAND", then Add To Cart.
**Got:** Picking XL flipped "Only 9 left in stock" to "Only 2 left in stock" — the counter is per-size, which quietly means the "9" I'd been shown all along was just the XS pile. Add To Cart worked cleanly: cart drawer slid in with the polo, XL - In Hand, £23.00, qty stepper, subtotal £23.00 "Taxes included.", and the bag badge ticked to 1. (The newsletter sheet was lurking under the drawer again, still asking.)
**Expected:** Clear feedback — got it; the drawer is one of the site's better moments.
**Felt:** "2 left in XL — now the 'order soon' line actually lands. Italy wins: £2 cheaper, extra photo, on-body shot, and it comes in my size. Portugal never stood a chance at XS-only."
**Next:** continued (u10-28, u10-29)

### Step 8 — Cart to the checkout door — after the silent terms trap
**Did:** Opened the cart page, checked the maths, tapped Checkout. Twice.
**Got:** Cart correct: 1 × Italy Polo XL, £23.00, subtotal £23.00, "Taxes included.", an Order note box — and no shipping estimate anywhere. First Checkout tap did nothing: no navigation, no error banner — there's an unticked "Agree to terms of sale as per the merchants terms of service." checkbox whose only complaint is a small native browser tooltip ("Please check this box if you want to proceed") that's easy to never see. Ticked the box, tapped again: landed on the branded Shopify checkout — bird logo, "Checkout - Unfounded", Order summary £23.00, Shop Pay and Google Pay express buttons, standard Contact/Delivery/Payment form. Shipping method: "Enter your shipping address to view available shipping methods" — so the delivery cost on a £23 shirt is still unknown at the door. STOPPED here per audit rules; nothing entered, nothing submitted.
**Expected:** Checkout button that either works or says why it won't; a shipping cost before the door.
**Felt:** "The dead button had me tapping like an idiot for a second. Door itself looks legit — proper Shopify, my £23 is right. Still don't know postage. That's tomorrow's surprise."
**Next:** continued to the door, then stopped (u10-30, u10-33, u10-34, u10-35)

## Outcome
**Bought / didn't:** Bought (audit-bought) — Italy Polo, XL - In Hand, £23.00: reached the branded Shopify checkout landing page with intent and stopped there. Italy beat Portugal on every axis a comparison shopper can actually check: £2 cheaper, 3 photos vs 2 (including the only on-body shot), 2 live sizes vs XS-only, 9-ish left vs 3. The Bird hoodie grey-vs-black decision was postponed indefinitely — both 0/10 sold out with no notify-me to hold his place.
**Total time:** ~12 minutes, a third of it re-finding things the site never groups.
**Worst moment:** Realising nothing on either PDP explains anything: identical one-line "descriptions", the same size chart, no fabric info, no zoom, no reviews — so the £23-vs-£25 (and black-£30-vs-grey-£27 shorts) gaps read as arbitrary, and the comparison had to be settled on photo count and stock instead of substance. Runner-up: the silently dead Checkout button before the terms box.
**Best moment:** The search results page — "polo" put both candidates literally side by side with prices, one screen doing the job the whole information architecture doesn't; and the back gesture reliably returned to that exact spot, keeping each extra comparison round-trip to a predictable 2 taps.
**Would they come back?** For the polo, yes — he got what he wanted cheap and the door worked. As a comparison shopper, warily: a store with no category pages, no size filter, no product facts and mood-based colourway pricing makes every future comparison this manual. The hoodie money goes elsewhere unless a restock email exists — which it doesn't, because there's no notify-me.
**One thing that would have changed the outcome:** It ended in a purchase, so: a line of actual product information (fabric/weight) plus a reason for the price differences would have upgraded a photo-guess into a confident buy — he's ~60% sure of the colour and cut he'll receive, and 0% sure of the fabric.
