# 14 — Trevor, 56, night-shift security guard whose son keeps going on about this brand
**Device:** old Android, 360x800, congested 4G (~1.6Mbps down, 150ms lag, CPU throttled x4) · **Goal:** have a proper look at the site his son rates — the lad's been living in their football gear all summer · **Mood:** on the sofa about 10pm, expects the internet to be rubbish because it always is at this hour

*(Session note: audit egress geo-detects as US, so the session was pinned with `?country=GB` as a real UK visitor would see it. All timings are genuine cold loads — cache, cookies and storage wiped — on emulated slow 4G with the CPU throttle kept on. Screenshots at the stated seconds are true-time compositor frames on a fresh navigation. Strict read-only: nothing typed into any form; stopped at the checkout landing.)*

### Step 1 — Opened the site and watched it arrive
**Did:** Tapped the link his son sent months ago and sat there watching, tea in hand.
**Got:** At **1 second**: a white page, a faint grey band at the top with a burger, magnifier, person and bag icon, and a big solid black rectangle where something was clearly meant to go. Not a word of text. At **3 seconds**: the black rectangle became a proper photo — two lads in blue Italy polos outside a block of flats — and the header settled. Still not one word on the whole screen: no headline, no button, and blank white below the photo. At **5 seconds**: same photo, a little "01 02" appeared under it. Still silent. At **10 seconds**: the picture had changed by itself to a different slide that finally had words on it — "All Nation Items Available Now!" with a Shop Now button — and collection photos had filled in below. The page finished loading at about 10.4 seconds. (u14-00-home-1s, u14-01-home-3s, u14-02-home-5s, u14-03-home-10s)
**Expected:** A minute of white and a spinner, like most shops at this hour.
**Felt:** "Nice photo. What's it selling?" Ten seconds of a picture book with no words. The photo being up early felt fast; the words being that far behind it felt odd — backwards, even. He never saw the first slide's headline at all: the slideshow moved itself on before its own text turned up.
**Next:** continued

### Step 2 — Did anything jump around?
**Did:** Kept still and watched for the usual shuffling-about as things loaded.
**Got:** Above the fold, honestly, very little: text never popped in and shoved other text down, and no white boxes flashed where photos should be. Under the bonnet the page did move — on the very first cold load the whole page shrank by about 430 pixels and shifted up ~30px around the 5–6 second mark as the hero carousel woke up (the second slide had been stacked underneath as a black band until then), and the hero itself grew 40px taller — but nearly all of it happened below what Trevor could see. The movement he *did* see was the slideshow auto-advancing and the headline text fading in seconds late.
**Expected:** Pictures arriving and punting the text he was reading down the page — that's what shopping sites do to him.
**Felt:** "It's not jumpy, it's just… quiet." The page holds its shape; it's the words that are on a delay.
**Next:** continued

### Step 3 — The newsletter popup landed mid-read
**Did:** Started reading properly once the words showed up.
**Got:** At **15 seconds** into the visit a "Sign up for our newsletter — Stay informed about new collections and discounts" sheet slid up over the bottom half of the screen and dimmed the rest. Email box, Subscribe, and a small underlined "NO THANKS" sitting at the very bottom edge of his 360x800 screen — when the same popup later fired over the product page, that NO THANKS line was half clipped by the bottom of the display. Tapped NO THANKS; it went and stayed gone. (Nothing entered — audit rule.) (u14-04-home-popup, u14-19-pdp-popup)
**Expected:** Some interruption eventually; every site has one.
**Felt:** "I've been able to read your page for seven seconds and you're already after my email." At his connection speed the site spent longer showing him a wordless photo than it waited before asking for his address. And the escape hatch being the smallest thing on the sheet, right at the screen's edge — that's the bit designed for younger thumbs than his.
**Next:** continued, unbothered but clocking it

### Step 4 — Scrolled down the homepage
**Did:** Scrolled down steadily: collections row, "Latest arrivals", the brand blurb.
**Got:** Photos were there every time he stopped — hoodie tiles, then a "SALE Nation Polo Sets" carousel with ITALY POLO £23.00 right at the front ("Available in 5 size", a black "+" on the card), then a black panel reading "Clothing designs to make everyone feel truely unique". By ~14 seconds into the visit 24 of 30 images were in; he never caught a blank tile mid-scroll except in the first ten seconds. (u14-06-home-carousel, u14-07-home-latest)
**Expected:** Grey squares trailing ten seconds behind his thumb.
**Felt:** "It keeps up once it's awake." The Italy polo was the same shirt as the hero photo — that'll do; his son's got the France one. ("Truely," though. His son would say it doesn't matter. It's a shop window; it matters.)
**Next:** continued — tapped the ITALY POLO card

### Step 5 — The product page, twice over
**Did:** Tapped ITALY POLO £23.00. (Separately, the audit re-ran this page as a stone-cold direct load — the "son texts you the link" case — with the same 3s/5s watch.)
**Got:** **Warm, from the homepage:** product photo up at 3 seconds, page complete at ~5 — quickest page of the night. **Cold, direct:** at 3 seconds the page was pure white with nothing but the black header and the bird logo — not a pixel of product; at 5 seconds the polo photo and thumbnails were in; the page finished at ~8.5 seconds, and the price didn't exist on screen until he scrolled to the buy box at ~9.5. Buy box when reached: Italy Polo, £23.00, "TAXES INCLUDED.", "Please Allow 2-5 Working Days For Item To Be Shipped", SIZE row of five chips labelled "XS - IN HAND" … "XL - IN HAND" with S, M and L struck through — only XS (pre-selected) and XL alive — "Only 9 left in stock. Order soon.", Add To Cart, purple "Buy with shop", FAST GLOBAL SHIPPING badge. Three photos in the gallery: the shirt, a colourway grid with a size chart, a lifestyle shot. (u14-09-pdp-3s, u14-10-pdp-5s, u14-16-pdp-cold-3s, u14-17-pdp-cold-5s, u14-18-pdp-buybox, u14-11-pdp-settled)
**Expected:** Product pages are usually the slow ones on his phone.
**Felt:** "Card said five sizes; three of them are crossed out. And what's 'IN HAND' when it's at home?" (He guessed right — it means they've actually got it, not a pre-order — but nobody tells him.) The cold white screen at 3 seconds is the one moment of the night he'd have started doubting the link. He waited; it came.
**Next:** continued — tapped "XL - IN HAND" (the stock line flipped from "Only 9 left" to "Only 2 left in stock. Order soon.") (u14-20-size-xl)

### Step 6 — Add to cart: how long until he believed it
**Did:** Tapped ADD TO CART and — from habit — hovered his thumb, ready to tap again when nothing happened.
**Got:** For the first ~0.8 seconds, nothing — page identical, button unchanged. Then a white drawer slid in from the right, and by **1.5 seconds** it was fully there: photo of the polo, ITALY POLO £23.00, "XL - In Hand", quantity stepper, Subtotal £23.00 GBP, "Taxes included." One motion, everything on it, no ambiguity. (u14-21-atb-300ms, u14-21-atb-800ms, u14-21-atb-1500ms, u14-22-cart-drawer)
**Expected:** His usual: button does nothing, no drawer, tap it again, end up with two.
**Felt:** "Right, that's in. No arguments." A second and a half on his connection, with the shirt's picture and size staring back at him — that's the difference between confidence and the double-tap lottery. Thumb stood down.
**Next:** continued

### Step 7 — The till: one toll-booth, then a quick door — and the postage question
**Did:** In the drawer: a required checkbox, "Agree to terms of sale as per the merchants terms of service." Ticked it (no choice), tapped Checkout.
**Got:** The checkout URL answered in about 2 seconds and the page was up in ~3 — on slow 4G, easily the fastest "big" step of the night. Proper Shopify checkout: bird logo, Order summary £23.00, Shop Pay and Google Pay buttons, Contact with Sign in, Delivery already set to United Kingdom. And the delivery cost? "Shipping method — Enter your shipping address to view available shipping methods." Nowhere in the whole visit — homepage, product page, cart drawer, checkout door — was a postage price ever shown; the only shipping words were "FAST GLOBAL SHIPPING" and "2-5 working days", neither of which is a number. **STOPPED HERE** — audit line, nothing entered. (u14-14-cart-drawer, u14-23-checkout-landing, u14-15-checkout-landing)
**Expected:** The checkout to be the step that dies at this hour. It wasn't — it responded first tap, no spinner-limbo, no total that didn't match his bag (his £23 was £23, one shirt, the shirt he picked).
**Felt:** "That was the easy bit — first time that's ever been the easy bit." Mild grumble at signing terms just to look at the till, and at a shop that'll tell him the shipping's *fast* but not what it costs.
**Next:** stopped at the checkout landing with intent

### The verdict he'd give his son — wait or leave?
**Wait.** At every choke point he stayed: 3 seconds of wordless white at the start (he's waited longer for a headline), the 15-second popup (one tap, gone), the cold white product page at 3 seconds (the only genuine wobble — on a site he didn't have a personal reason to trust, that's where he'd have backed out). Nothing ever died, double-added, or ignored a tap — which is precisely where the other lot lost him. He would buy: he reached the till with the £23 polo, first tap, right total, right size. At 10pm on the phone he'd likely leave the address form for the morning — not because anything broke, but because the shop wouldn't tell him the postage before asking where he lives, and he's been stung by that before.

## Outcome
**Bought / didn't:** Bought, to the audit line — reached the checkout landing page with the £23 Italy Polo (XL - In Hand) in the cart and genuine intent; the summary matched his bag exactly. (Nothing entered past the door.)
**Total time:** ~8 minutes at his reading pace (machine path was ~73 seconds; Trevor isn't).
**Worst moment:** The newsletter popup at 15 seconds — over the buy box he was reading when it fired on the product page, its NO THANKS escape half-clipped off the bottom edge of his screen — narrowly ahead of the cold product page spending 3 seconds as pure white with just a logo, and prices that only exist after a scroll.
**Best moment:** Add to cart. On genuinely bad internet: tap, 1.5 seconds, full drawer with photo, size and total — zero doubt, no double-tap. (And a checkout door that opened in ~3 seconds, which on his phone is witchcraft.)
**Would they come back?** Yes. Browsing kept pace with him, nothing jumped, nothing silently failed, and the one thing he wanted to buy was buyable. He'll finish on the laptop — and if the shipping fee at the address step reads like a joke against a £23 shirt, that's where it ends.
**One thing that would have changed the outcome:** Words with the pictures. The photos beat the text to his screen by 5–7 seconds because the headlines and buttons wait for the site's JavaScript to wake up and animate in — on his connection the shop stands mute for ten seconds, and the newsletter popup still makes its 15-second appointment regardless. Paint the text with the page (and put a postage number anywhere before the address form) and Trevor pays for the polo tonight, on the phone.
