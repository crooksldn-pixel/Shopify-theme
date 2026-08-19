# 18 — Priya, 31, vestibular disorder — animation makes her ill
**Device:** mobile 390x844, OS-level "reduce motion" ON (prefers-reduced-motion: reduce), normal 4G · **Goal:** a friend recommended the football drop; she wants to browse slowly and buy one in-stock piece without triggering a vertigo episode · **Mood:** careful, deliberate — she opens unfamiliar sites the way other people open jars they suspect are fizzy

*(Session note: audit egress geo-detects as US; session pinned with `?country=GB` as a real UK visitor. Read-only run: cart used, required terms checkbox ticked on /cart, nothing else submitted, stopped at the checkout landing page. Because two earlier testers disagreed about whether this site honours reduced motion, this session measured it instrumentally: the hero was sampled every 500ms for 16s with DOM state + screenshots at +0s/+4s/+8s, every stylesheet was scanned for `prefers-reduced-motion` rules, and a control session with the setting OFF was run for comparison. The numbers below are those measurements.)*

### Step 1 — The hero carousel: measured, and it does NOT respect my setting
**Did:** Landed on the homepage with reduce-motion on and just… watched the hero, hands off, sampling it every half-second. Screenshotted it at +0s, +4s and +8s.
**Got:** It moves. Autoplay is enabled and running (delay 4000ms, 600ms sliding transition, confirmed via the slider's own config). Slide 1 "World Cup Drop Live!" slid to slide 2 "All Nation Items Available Now!" at t≈3.0s, slid back at t≈7.5s, forward again at t≈12.0s, back at t≈16.5s — a two-slide ping-pong, forever. The +0s/+4s/+8s screenshots are three different frames. Worse: every swap replays text entrance animations — the sub-heading, headline and Shop Now button each run a `heroContentAnimation` keyframe (0.85s/0.9s/1.15s), so the words themselves glide in again on every pass, on top of an 8-second animated progress ring in the corner. And there is no pause button anywhere: the prev/next arrows are hidden on mobile and the two pagination dashes at the bottom are 4px tall. I cannot stop it; I can only scroll it off screen.
**Expected:** With my OS setting on, a still hero — or at minimum a pause control (that's the WCAG 2.2.2 ask for anything auto-moving longer than 5 seconds).
**Felt:** "I asked, in the one standard way a person can ask, for things not to move. The first thing this shop does is wave two full-screen photos back and forth at me with re-animating text, and it took away the stop button."
**Next:** continued, scrolling the hero away quickly (u18-01, u18-02, u18-03)

### Step 2 — The newsletter popup slides up at me
**Did:** Kept still on the homepage. At ~8.5 seconds the "Sign up for our newsletter" sheet arrived.
**Got:** It animates in: a bottom sheet that slides up ~287px to its resting place on a 0.3s transform transition while the page behind fades dark (0.3s opacity). Under reduced motion it should simply appear; instead it glides. Fair play on the contents though — email field, Subscribe, and a clear underlined NO THANKS all on screen; one tap dismissed it for the rest of the session. I looked at the form and left it alone (audit rule: never submit).
**Expected:** An instant appearance, or no popup at all.
**Felt:** "A small motion, but it's motion aimed at me, eight seconds in, while the carousel is still swinging above it. My head does the maths even when I don't want it to."
**Next:** continued (u18-04)

### Step 3 — Scrolling the homepage: hidden text that fades in, and a strip that never stops moving
**Did:** Scrolled down slowly, section by section, sampling styles as I went.
**Got:** Two more ignored-setting moments. First: the mid-page banner's heading ("Clothing designs to make everyone feel truely unique" — typo theirs) and its View More button are held at opacity 0 until they enter the viewport, then fade in over ~0.9s (measured 0.01 → 1.0 across ~900ms). The content does all arrive — nothing is permanently withheld — but every section greets you with a little materialisation. Second, and genuinely the worst thing on the site for me: the social-media photo strip is a perpetual marquee — autoplay delay 0, linear crawl (~50px/s, measured continuously drifting across ten straight samples), no pause, no end. It moves for as long as it's on screen. I also tried the floating back-to-top bubble: it animated a ~2,500px scroll back to the top over ~750ms — a full-screen swoop, exactly the gesture that sets me off. For completeness I scanned all 50 stylesheets: exactly ONE `prefers-reduced-motion` rule exists on the whole site (Shopify's stock `.motion-reduce` utility in base.css) and zero elements use it. My setting is read by nothing. A control run with the setting off behaved identically — same autoplay, same delays, same marquee.
**Expected:** Content visible without ceremony; a marquee that respects reduce-motion (or at least stops); an instant back-to-top.
**Felt:** "It isn't that they tried and missed. There is no code path in which my preference does anything. The switch is connected to nothing."
**Next:** continued to the shop grid (u18-05, u18-06)

### Step 4 — The collection page is, unexpectedly, an oasis
**Did:** Opened /collections/all ("Latest Drop", 20 of 44 showing) and scrolled the whole grid slowly, sampling for animations and card fades.
**Got:** Stillness. Zero running animations, no cards fading or sliding in on scroll — opacity 1 across the board, products just there: photos, prices, SOLD OUT badges on the many dead items, quick-add "+" on the living. This is the calmest shopping screen on the site and honestly a relief. (Same catalogue reality other testers hit: most of the wall is sold out.)
**Expected:** After the homepage, more theatrics — got none.
**Felt:** "This is all I wanted the homepage to be. A shelf. Things on it. Nothing performing."
**Next:** continued — picked the Italy Polo, £23, in stock (u18-07, u18-08)

### Step 5 — Italy Polo product page: motion only when I ask for it
**Did:** Opened /products/italy-polo. Checked the gallery configuration and then paged the gallery once, sampling the movement.
**Got:** The gallery does not autoplay (confirmed: autoplay disabled). Advancing to the next photo runs a 300ms eased slide — animated, so strictly it too ignores my setting, but it's brief, singular, and only happens when I trigger it; that I can live with. Six photos, price £23.00 TAXES INCLUDED, "Please Allow 2-5 Working Days For Item To Be Shipped", size chips reading "XS - In Hand", "S - In Hand"… with S/M/L struck through dead and XS/XL alive. XS pre-selected. No size guide anywhere, but the polo decision was easy.
**Expected:** A gallery that jumps cut-to-cut under reduce; a 300ms user-initiated slide is the closest this site gets to good behaviour.
**Felt:** "Here the site only moves when my finger tells it to. That's the whole contract I'm asking for."
**Next:** continued — Add To Cart, XS (u18-09, u18-10, u18-11)

### Step 6 — Add to cart: the drawer takes a run-up
**Did:** Tapped Add To Cart and sampled the cart drawer as it arrived.
**Got:** The drawer's panel slides in from fully off-screen right — translateX 360px → 0 on a 0.45s transform transition (measured gliding through 355 → 330 → 250 → 82 → 31 → 0 over ~430ms) — under reduced motion. A whole panel sweeping across most of the screen is precisely the kind of lateral motion my setting exists to prevent. Contents were good, though: "Your cart 1", ITALY POLO £23.00, "XS - In Hand", a visible quantity stepper and bin icon, Subtotal £23.00 GBP, "Taxes included.", a terms checkbox, View Cart and Checkout. Clear add-to-cart feedback — just delivered by catapult.
**Expected:** The drawer to appear, not to travel.
**Felt:** "Good drawer, wrong entrance."
**Next:** continued to /cart (u18-12)

### Step 7 — Cart, terms tick, and a checkout that finally sits still
**Did:** Opened /cart, reviewed the one line item, ticked the required "Agree to terms of sale" checkbox (16px — tiny), tapped Checkout.
**Got:** Cart maths clean: £23.00, "Taxes included.", no shipping estimate anywhere before the till — same gap every other tester found. Then the checkout landing loaded ("Checkout - Unfounded", bird logo, Order summary £23.00, Shop Pay / G Pay, Contact, Delivery pre-set to United Kingdom) and I sampled it for motion: zero running animations. Shopify's checkout is the stillest page on the site. STOPPED HERE per audit rules — nothing entered.
**Expected:** Exactly this. The irony is thick: the page the brand built is a fairground; the page Shopify built is a library.
**Felt:** "I could buy from here. I just had to survive their homepage to reach it."
**Next:** stopped at the checkout landing with intent (u18-13, u18-13b, u18-14)

## Outcome
**Bought / didn't:** Reached the checkout landing with the Italy Polo (XS, £23.00) and genuine intent — nothing on the purchase path actually blocked her. (Audit stop line; nothing entered.)
**Total time:** ~12 minutes — slow by design; a vestibular shopper paces herself, and the homepage forced two deliberate rests.
**Worst moment:** The homepage triptych: a hero that ping-pongs every ~4.5s with re-animating text and no pause control, a social strip that literally never stops crawling, and a popup that slides up into all of it — three simultaneous motion sources, none of which honour the setting. Measured fact underneath the feeling: one `prefers-reduced-motion` rule exists in 50 stylesheets and zero elements use it; behaviour with the setting on and off is byte-for-byte identical.
**Best moment:** Discovering the collection grid and checkout are completely still — zero running animations on either — and that the PDP gallery only moves 300ms at a time, when asked. Nothing was ever LOST to her either: all animated content (hero text, fading banners) does eventually render fully, so reduce-motion users miss no information — they just pay a motion tax to receive it.
**Would they come back?** A qualified yes — but never through the front door. Priya would bookmark /collections/all and deep-link past the homepage forever. If a link ever drops her on the homepage, she'll close the tab first and decide later.
**One thing that would have changed the outcome:** Wire the setting up: one `@media (prefers-reduced-motion: reduce)` block that stops the hero autoplay and the social-media marquee (and lets everything else simply appear). The theme already checks nothing — a dozen lines would take the homepage from "actively hostile to my condition" to "as calm as their own checkout".
