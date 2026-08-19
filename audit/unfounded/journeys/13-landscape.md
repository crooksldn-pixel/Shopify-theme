# 13 — Jay, 26, phone permanently in landscape
**Device:** mobile landscape 844x390 (rotation lock left on after YouTube — the whole session sideways), normal 4G · **Goal:** heard about the World Cup drop, wants an in-stock polo without turning his phone · **Mood:** relaxed, one thumb on each side of the screen, zero patience for "please rotate your device" energy

*(Session note: the audit egress IP geo-detects as US; the session was pinned with `?country=GB` as a real UK visitor would see it. All figures are the 844x390 GBP view. Read-only run: cart used, nothing submitted, stopped at the checkout landing page.)*

### Step 1 — Landed on the homepage and the hero got guillotined
**Did:** Opened unfoundedstudios.com sideways. Black header (burger / bird logo / search, account, bag) across the top — 96px of my 390px of height, a full quarter of the screen, and it's sticky, so it never leaves. Below it the hero carousel: a 273px-tall strip of photo in which the headline "World Cup Drop Live!" is chopped in half mid-letter and the "Shop Now" pill under it is amputated — top sliver of the button visible, the rest swallowed by the section edge. When the carousel moved to slide 2, its message ("All Nation Items Available Now") didn't survive at all: pure photo, no visible text or button anywhere.
**Got:** A homepage whose only call-to-action is half-erased on slide 1 and completely invisible on slide 2. (Verified afterwards: tapping the sliver does still navigate to /collections/all — the button works, it just looks broken.)
**Expected:** The hero to shrink its artwork, not its words. Cut the photo, keep the button.
**Felt:** "The shop's first sentence to me is cut off mid-word. Sideways phones exist, lads."
**Next:** continued (u13-01, u13-03)

### Step 2 — The newsletter popup took the whole screen — but played fair
**Did:** ~10 seconds in, the "Sign up for our newsletter" modal appeared. At this height it's a full-screen takeover: the white card runs from the top edge to ~40px short of the bottom, 100% of the viewport is covered or dimmed.
**Got:** Credit where due: everything fit. Heading, subline, email field, Subscribe, and the underlined "NO THANKS" all on screen at once — NO THANKS sat 51px off the bottom edge but was fully tappable, one tap and it was gone for good. No clipped buttons, no trapped scroll, no popup I couldn't leave.
**Expected:** Honestly, worse — this is where short viewports usually kill you (a dismiss link pushed below the fold you can never reach).
**Felt:** "Full-screen ambush, but the exit was where my thumb expected it. Annoying, not hostile."
**Next:** continued (u13-02, u13-03)

### Step 3 — TAP: burger menu — four links, still had to scroll
**Did:** Tapped the burger. The menu drawer opened under the header, giving itself the remaining 295px of height with 76px-tall menu rows.
**Got:** Two and a half items per screenful. "Home", "Shop all", "Collections >" visible; "Contact" cut in half at the fold; the Account link and country selector another scroll below. A four-link menu that needs scrolling. Rows are huge, comfortable tap targets though — nothing mis-tappable.
**Expected:** A menu this small to fit, or at least compress its font sideways.
**Felt:** "I'm scrolling a menu with four things in it. Comical, not blocking."
**Next:** continued — tapped "Shop all" (u13-06)

### Step 4 — Shop all: the grid is the first thing that truly likes landscape
**Did:** "Shop all" opened /collections/all ("Latest Drop", breadcrumb Home / Products). Filters and an Alphabetically-A-Z sort sit comfortably on one row; "Showing 20 of 44 products". Scrolled the grid.
**Got:** Three columns of product cards — genuinely good use of the wide screen, better dense than portrait's stack. Clear photos, prices, SOLD OUT badges on the corpses, quick-add "+" on the living, "Available in 5 size" lines (grammar theirs — and, as other personas found, sometimes a lie). Two fights, though: every screenful of scrolling pays the 96px sticky-header tax, so cards keep sliding under a black bar that covers their titles; and a floating scroll-to-top bubble sits on the bottom-right card of every row. The Italy Polo wasn't in the 20 — pagination at the very bottom is tiny numerals "1 2 3 →" with ~24x28px tap targets, the smallest touch targets of the whole session. Hit "2" (carefully), found the ITALY POLO £23.00 on page 2 — its card title half-buried under the sticky header when scrolled to.
**Expected:** Pagination targets sized like the lovely huge menu rows, and a header that gets out of the way when I scroll down.
**Felt:** "The grid's the best landscape screen they've got — three across feels like a proper shop shelf. But the header shadows every row like a bouncer, and those page numbers need sniper aim."
**Next:** continued (u13-07, u13-08, u13-10, u13-11, u13-12)

### Step 5 — TAPS: Italy Polo PDP — landscape accidentally gets the best layout on the site
**Did:** Opened /products/italy-polo. At 844px wide the theme serves the desktop two-column layout: photo gallery (6 images) down the left, buy box on the right.
**Got:** Title, £23.00 TAXES INCLUDED, "Please Allow 2-5 Working Days For Item To Be Shipped", and the full SIZE row all in the first screenful — no scrolling to understand the product. Sizes read "XS - IN HAND", "S - IN HAND"… (the "- In Hand" suffix is baked into the variant names, which is odd but I could decode it); S, M, L struck through dead, XS pre-selected and actually in stock, XL alive. Tapped XL — chip outlined, URL updated. Add To Cart sat ~90px below the fold; one small flick and it was mine. The one landscape wart: the first product photo's aspect ratio means the opening screen of the gallery is mostly an empty grey band — the polo itself only appears a scroll into the 812px-tall image column.
**Expected:** To fight a stretched portrait phone layout. Instead got the desktop one, which fits a sideways phone shockingly well.
**Felt:** "Sideways is the best this shop has looked. Photo one side, decisions the other — why isn't the homepage this smart?"
**Next:** continued — Add To Cart (u13-13, u13-14, u13-15)

### Step 6 — Cart drawer: one perfect screenful… with the quantity controls walled off
**Did:** Tapped Add To Cart. The cart drawer slid in from the right — a 485px-wide panel over the page.
**Got:** At 390px tall, the drawer nails the important stuff in a single screenful, no scrolling: "Your cart 1", product thumbnail, ITALY POLO £23.00, "XL - In Hand", Subtotal £23.00 GBP, "Taxes included.", the terms checkbox, and View Cart + Checkout side by side. Two real problems though. One: the item row is clipped mid-card — the quantity stepper and Remove control exist but live below the cut, inside a 74px-tall internal scroll slit (content 180px) with no scrollbar, no fade, no hint it scrolls; at this height they are effectively invisible and undiscoverable — if I'd wanted two polos, or none, the drawer appears to have no way to do it. Two: same as everyone else found — subtotal says "Taxes included." and not a word about shipping cost, no threshold, nothing.
**Expected:** Quantity and remove visible on the item, or at least a visible scroll affordance; a delivery price before the till.
**Felt:** "Everything I need to pay is on screen; everything I'd need to change my mind is hidden in a letterbox I can't see into."
**Next:** continued — wanted to see the full cart page too (u13-16, u13-24)

### Step 7 — Cart page, the 16px checkbox, and the toll-booth
**Did:** Opened /cart. "Your cart¹", PRODUCT/TOTAL table, Italy Polo £23.00, quantity stepper present and usable here (this page is where the drawer's hidden controls actually live), Order note expander, Subtotal £23.00, "Taxes included." — again no shipping line. Scrolled to the bottom block; the sticky header ate the top half of the "Subtotal £23.00" row on the way (u13-19 shows it literally beheaded). Ticked "Agree to terms of sale as per the merchants terms of service." — the checkbox is a 16x16px square, by far the smallest thing I was asked to hit all session; I aimed with the label text instead. Cart badge on the bag icon had shown "1" since the add — nice.
**Got:** A required legal checkbox the size of this full stop, then a big friendly Checkout button (708px wide, hard to miss), plus Shop Pay and G Pay.
**Expected:** A checkbox at least 24px, and a shipping estimate anywhere at all.
**Felt:** "The button you want me to press is enormous; the one you legally require is microscopic."
**Next:** continued — tapped Checkout (u13-18, u13-19, u13-20)

### Step 8 — Checkout landing: clean, branded, and completely landscape-proof
**Did:** Checkout loaded: "Checkout - Unfounded", bird logo, collapsible "Order summary £23.00" bar, Express checkout (Shop Pay, G Pay), Contact with Sign in, Delivery pre-set to United Kingdom, standard address form below. No horizontal scroll, nothing clipped, nothing overlapped — Shopify's checkout simply handles 844x390.
**Got:** The shipping price still isn't revealed until a full address goes in — but the page itself is the most composed screen of the session. STOPPED HERE per audit rules, nothing entered.
**Expected:** Exactly this — checkout is the one page nobody's theme can break.
**Felt:** "Ironic: the storefront fought my orientation for twenty minutes and the till doesn't even blink."
**Next:** stopped at the checkout landing (audit line) with intent (u13-21, u13-22)

## Outcome
**Bought / didn't:** Reached the checkout landing with the Italy Polo (XL, £23.00) in the cart and real intent — the landscape layout never actually blocked the purchase path, it just roughed it up. (Audit stop line; nothing entered.)
**Total time:** ~7 minutes, roughly 11 taps + a lot of scrolling — a good minute of it lost to the page-2 hunt for the polo and squinting at tiny pagination numbers.
**Worst moment:** Opening the cart drawer and realising the quantity/remove controls are clipped inside an unmarked 74px scroll slit — invisible and undiscoverable at this height; runner-up, the homepage hero decapitating its own headline and "Shop Now" button (slide 2's message vanishes entirely).
**Best moment:** The product page. At 844px wide the theme serves its desktop two-column layout — gallery left, buy box right — and it fits a sideways phone beautifully: price, delivery note, sizes and (one flick later) Add To Cart, no fighting. The full-screen newsletter popup also deserves a nod for keeping its NO THANKS reachable, which is where short viewports usually turn into traps.
**Would they come back?** Yes, with an asterisk: the path works end-to-end sideways, the grid and PDP are genuinely good in landscape, and checkout is flawless. But Jay would come back braced — for the sticky header eating a quarter of every screen, the beheaded hero, and cart edits that require either finding a secret scroll or a detour to /cart.
**One thing that would have changed the outcome:** The outcome was a success, so: the change that would have upgraded the whole session is height-aware chrome — give the hero a min-height so its headline and CTA survive 390px, and let the 96px header collapse or unstick on scroll. Those two fixes would turn landscape from "tolerated" into the best way to browse this store.
