# RAW — header, menu drawer, CASE 001 board, status bar

Staging verified on every session (`.crk-root` + `crooks.css` present; harness threw no verification errors).
Device baseline: mobile 390x844 DPR3. Slow-4G first-load pass done on the homepage.
Environment note that colours several observations: the audit proxy exits **outside GB**, so Shopify Markets
presents prices in **USD ($35.00 tee)** and the GB-gated carriage bar never renders. Theme behaviour, not
a theme fault — a UK shopper sees £ and the carriage bar.

Slow-4G first load feel: DOM ready ~1.2s, header text readable ~1.6s, images settled by ~5.6s. The page is
legible and tappable almost immediately; images fill in after. Nothing jumped around while loading. Feels fast
for a heavy-looking site.

### Header — logo (handcuffs mark)
- **Should:** Taps back to the homepage; identifiable as the brand.
- **Did:** From the V2 BAGGIES PDP, tapping the handcuffs icon landed on `/` (h1 CROOKSLDN). No visible text label; the image carries `alt="CROOKSLDN"`. Sits alone on its own row on mobile (row 1), links row below it.
- **Verdict:** works
- **Screens:** f-header-drawer-01-home-slow4g

### Header — wordmark
- **Should:** SPEC §3.1 says the header renders a wordmark alongside the logo.
- **Did:** No CROOKSLDN text anywhere in the header at 390px or 1440px (`headerText: "CATALOGUE SEARCH BAG [0] LIGHT MODE MENU"`). The hero owns the wordmark on the homepage; on inner pages the only brand mark is the handcuffs icon and the tab title.
- **Verdict:** absent
- **Shopper impact:** Minor — a shopper deep-linked to a PDP sees no brand name on the page chrome, just handcuffs. Recognisable enough once you know the brand; anonymous if you don't.

### Header — CATALOGUE
- **Should:** Reads as "all products"; lands on the full register.
- **Did:** → `/collections/all`, h1 "ALL", 14 items. Label made sense before tapping — on-theme synonym for "shop all" that doesn't need decoding.
- **Verdict:** works

### Header — SEARCH
- **Should:** Lands on a usable search page.
- **Did:** → `/search`. Before typing anything the page already offers DIRECT LINKS (START A RETURN / TRACK YOUR ORDER / QUESTIONS). Label obvious.
- **Verdict:** works
- **Screens:** f-header-drawer-02-search-landing

### Header — ACCOUNT
- **Should:** Checklist expects an ACCOUNT entry in the header.
- **Did:** Not in the header at any width (mobile 390 or desktop 1440). It exists only as the last row of the menu drawer, **below the CASE 001 board** — the deepest scroll point of the drawer. Tapping it there goes to the hosted sign-in at `friendsof.crooksldn.com` ("Sign in - CROOKSLDN"), which works.
- **Verdict:** partly
- **Shopper impact:** A shopper looking for "log in / my orders" scans the header, finds nothing, and has to open MENU and scroll past the entire nav *and the game board* to find ACCOUNT. Most will get there via the empty-cart page's "Log in" link or the TRACKING page instead. Costs a hunt; loses nobody permanently.
- **Screens:** f-header-drawer-19-account-landing

### Header — BAG [n]
- **Should:** Shows live cart count; taps to the cart.
- **Did:** `BAG [0]` → `/cart` ("Your cart is empty" + Log in prompt + a You-may-also-like row, so the dead end still sells). Count updates are covered in the cart-count item below. Bracketed count reads on-theme and is instantly understood.
- **Verdict:** works
- **Screens:** f-header-drawer-03-bag-landing-empty

### Header — MENU
- **Should:** Opens the navigation drawer.
- **Did:** Opens a `role="dialog" aria-modal="true"` drawer; the header button relabels itself MENU→CLOSE with `aria-expanded`. On mobile the drawer takes the full screen; on desktop it is a 420px right-hand panel over a dimmed scrim.
- **Verdict:** works
- **Screens:** f-header-drawer-05-drawer-open-top, f-header-drawer-17-desktop-drawer

### Header — LIGHT MODE / DARK MODE toggle (not on the checklist, present in header)
- **Should:** (common expectation) switches theme; label understandable.
- **Did:** Site loads dark; button reads "LIGHT MODE" (i.e. what you'll switch to), one tap flips the whole page instantly (body went rgb(11,10,14) → rgb(250,250,251)) and the label becomes "DARK MODE". Sticks across navigation. The relabel changes the button width ~10px so MENU shifts slightly — only when the shopper themself taps it, invisible otherwise.
- **Verdict:** works
- **Screens:** f-header-drawer-04-light-mode

### Drawer — every link, destinations
- **Should:** Each link lands where its label promises.
- **Did:** All followed by tap, all correct, all on the preview host except the last two by design:
  SHOP → `/collections/frontpage` (h1 "PRODUCTS", 14 items) · ALL → `/collections/all` ("ALL", 14) · NEW → `/collections/new` · TEES → `/collections/tees` · DENIM → `/collections/denim` · SWEATS → `/collections/sweats` · TRACKSUITS → `/collections/tracksuits` · ACCESSORIES → `/collections/accessories` · TRACKING → `/pages/tracking` · QUESTIONS → `/pages/faq` (h1 "COMMONLY ASKED QUESTIONS") · TERMS → `/pages/terms` · CONTACT → `/pages/contact` · ACCOUNT → hosted sign-in (friendsof.crooksldn.com) · BAG [n] → `/cart`. Curiosity, not a fault: SHOP and ALL are different URLs that both show the same 14 products under different headings ("PRODUCTS" vs "ALL") — no shopper harm observed.
- **Verdict:** works

### Drawer close — its close control
- **Should:** CLOSE at the drawer's top-right closes it.
- **Did:** Closed instantly; keyboard focus returned to the MENU button; stayed on the same page.
- **Verdict:** works

### Drawer close — tapping the scrim
- **Should:** Tapping outside the panel closes it.
- **Did:** Desktop: the 420px panel sits over a visible scrim; clicking the scrim closed the drawer. Mobile: the drawer is full-screen — there is no scrim to tap (an edge tap hits the panel and does nothing). Nothing broken, but the mobile shopper's only pointer exits are CLOSE or a link.
- **Verdict:** partly

### Drawer close — Escape
- **Should:** Escape closes the dialog.
- **Did:** Closed on both mobile and desktop; focus back on MENU.
- **Verdict:** works

### Drawer close — browser back
- **Should:** (Android habit) back closes the overlay and keeps you on the page.
- **Did:** History was home → /collections/tees, drawer opened on tees; `goBack()` landed on `/` — the drawer is not a history entry, so back **navigated away from the page the shopper was on** (though not off the site). An Android gesture-back user who opens the menu "to have a look" gets teleported back a page and has to re-find where they were.
- **Verdict:** partly
- **Shopper impact:** Mild disorientation for gesture-back users; on a shallow site the cost is one extra tap.
- **Screens:** f-header-drawer-10-after-back

### CASE 001 board — does the canvas animate?
- **Should:** Animated attract board at the bottom of the drawer.
- **Did:** Canvas 339x287 in the mobile drawer, pixels changing on every sample (three snapshots over 1.4s all differed) — thief, patrolling officer, £ coins moving through the brick/jail-bar grid. Confirmed the script is fetched only on first drawer open (0 requests before, 1 after), so pages that never open the menu never pay for it.
- **Verdict:** works
- **Screens:** f-header-drawer-06-drawer-bottom-case001

### PLAY CASE:001 NOW
- **Should:** Launches the game without losing the shop.
- **Did:** Opens a **new tab** (`target="_blank"`) at `https://crooks-case-break.base44.app` — title "CASE 001: THE GETAWAY — CROOKS", a fully on-brand terminal title screen (START CASE / LEADERBOARD / SOUND: ON), then a briefing and a playable tile game with touch pad, swipe controls and a SMOKE BOMB button. The original tab keeps the shop with the drawer still open, so getting back is just closing the tab.
- **Verdict:** works
- **Shopper impact:** The jump off-site is safe — you cannot lose your place in the shop.
- **Screens:** f-header-drawer-07-case001-game, f-header-drawer-09-game-in-play, f-header-drawer-11-game-board

### O4 check — board art vs game destination, as a shopper
- **Should:** Known item O4: drawer art is from the newer build, the link serves the old one — would a shopper notice?
- **Did:** Same tileset, same palette, same characters family — visually they read as the same game. The one tell: the drawer caption says the thief is "**collecting coins**" and the drawer board shows gold £ coins, while the game itself is about "**Recover 3 evidence packages**" (white bundles, no coins). A shopper who read the caption, then played, might register a flicker of "thought this was about coins"; nobody would call it broken.
- **Verdict:** works
- **Shopper impact:** Effectively unnoticeable; already logged as O4, no new cost observed.

### Homepage without the board — does anything carry that weight? Would a first-timer ever find it?
- **Should:** Judgment call per the brief (show_board false is deliberate).
- **Did:** Homepage is now hero → 14-card register → PROPERTY BAG packaging → REGISTER AS INFORMANT → footer. All of it is commerce; nothing playful carries the board's weight. The only homepage trace of the game is one plain footer line, "GAME / Play CROOKSLDN: The Getaway" (which, unlike the drawer button, opens in the **same tab**). Discovery odds in the drawer are better than feared: on first open the animated board's top edge is already peeking in at the bottom of the screen on mobile, and on desktop the canvas top is at 667px of a 900px viewport — moving pixels in view are a decent scroll lure. But a visitor who never taps MENU will never meet the board at all.
- **Verdict:** partly
- **Shopper impact:** The board went from a homepage set-piece to an easter egg for menu-openers. The homepage lost its one purely-fun beat; whether that matters is the owner's call, not a defect.
- **Screens:** f-header-drawer-12-home-full, f-header-drawer-05-drawer-open-top

### Cart count — BAG [n] updates and header reflow
- **Should:** Count updates on add; header row must not reflow (SPEC reserves 5ch).
- **Did:** On the CRXST★RZ tee PDP, ADD TO BAG stayed on the page and showed "> Added — 1 in bag · View bag"; header read BAG [1]. Two more adds → BAG [3]. Measured the BAG cell across [0]→[1]→[3]: x=144.8, w=61.3 every time — **zero reflow**, and every other header element held its position. One honest caveat: the header is not sticky, so at the moment of adding (buy button deep in the page) the count change happens off-screen; the inline "1 in bag" line covers that moment well.
- **Verdict:** works
- **Screens:** f-header-drawer-13-bag-1, f-header-drawer-14-bag-3

### Status bar — rotation and timing
- **Should:** Rotates its messages; SPEC D1 predicts 8s regardless of the configured 5.
- **Did:** Two messages alternate: "FREE UK SHIPPING OVER £20 — ORDER BY 18:00 FOR SAME-DAY DISPATCH" and "14 PRODUCTS CURRENTLY ONLINE". Changes logged at t=6.5s, 14.5s, 22.5s — a clean 8.0s cadence (D1's shopper experience confirmed; 8s reads fine, nobody would call it slow). One message at a time, wraps to two lines at 390px without pushing the header around. Not sticky — scrolls away with the page.
- **Verdict:** works
- **Shopper impact:** At 21:00 the bar still says "order by 18:00 for same-day dispatch" — as a standing offer that's accurate, and the PDP's own line ("Ordered now — leaves tomorrow") does the live math, so no one is misled.

### Status bar — [count]
- **Should:** Substitutes a real number.
- **Did:** "14 PRODUCTS CURRENTLY ONLINE" — matches the 14 active products and the hero's own "> 14 PRODUCTS AVAILABLE TO PURCHASE".
- **Verdict:** works

### Status bar — hover pause (desktop)
- **Should:** Rotation stops on hover.
- **Did:** Rotation confirmed running, then hovered: same message held for 12+ seconds.
- **Verdict:** works
- **Screens:** f-header-drawer-15-desktop-statusbar

### Status bar — reduced motion
- **Should:** No rotation under prefers-reduced-motion.
- **Did:** With reducedMotion emulated, the first message sat unchanged for 18s.
- **Verdict:** works

### Desktop quick pass (1440x900)
- **Should:** Same behaviours, laid out for desktop.
- **Did:** Single-row header: logo left; CATALOGUE / SEARCH / BAG [0] / LIGHT MODE / MENU right — still no ACCOUNT, still no wordmark. Status bar one quiet line on top. Drawer becomes a 420px right panel over a dimmed scrim; scrim-click and Escape both close; board canvas already visible on open (top at 667/900); ACCOUNT/BAG footer below it. Everything that worked on mobile worked here.
- **Verdict:** works
- **Screens:** f-header-drawer-16-desktop-header, f-header-drawer-17-desktop-drawer

## Surprises (incl. not-in-SPEC)

- **A cookie consent banner exists.** SPEC's open-items list says "No cookie banner", but Shopify's native COOKIE CONSENT dialog (Accept/Decline, styled close enough to the theme to pass) appears on first visit and covers a large slab of the lower mobile viewport until answered. The SPEC line appears stale — someone enabled it store-side. First-visit friction is real but ordinary.
- **Non-GB visitors see $ prices under £-denominated promises.** Geo presentment (audit proxy exits outside GB) shows $35.00 etc. while the status bar and set copy talk in £ — and the GB-gated carriage bar rightly stands down. Correct behaviour for a UK-market store; other audit agents should not read the $ prices or the missing carriage bar as defects.
- **Footer game link opens same-tab** while the drawer's PLAY button opens a new tab — the footer route can walk a shopper off the site with no way back but browser-back. (Footer is another area's surface; noting for cross-reference.)
- **Preview-bar artifact (not a site feature, per brief):** the Shopify preview overlay (`#PBarNextFrameWrapper`) intercepts taps at the very bottom of the viewport — exactly where the drawer's ACCOUNT/BAG footer row sits. Removed during testing; real shoppers unaffected.

## Protect (clearly working and load-bearing)

- Drawer dialog discipline: MENU relabels to CLOSE with aria-expanded, Escape closes, focus returns to the trigger, CLOSE always in reach.
- Lazy board injection: zero board requests until the first drawer open, then a smoothly animating canvas — the fiction costs nothing until asked for.
- The fixed-width BAG count cell: 0→1→3 with not a single pixel of header reflow.
- Status bar's three quiet manners: 8s rotation, pause on hover, full stop under reduced motion.
- PLAY CASE:001 NOW opening a new tab so the shop (and the open drawer) is still there when the shopper comes back.
