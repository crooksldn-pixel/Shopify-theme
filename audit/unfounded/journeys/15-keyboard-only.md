# 15 — Marcus, 34, keyboard-only shopper (RSI — no mouse, ever)
**Device:** desktop 1440x900, normal broadband, mouse unplugged — Tab / Shift-Tab / Enter / Space / Escape / arrows only · **Goal:** heard about the World Cup drop, wants an in-stock polo without a single click · **Mood:** methodical, patient, but with a hard rule learned from years of bad shops: the first time Enter fires something I didn't aim at, trust is gone

*(Session note: the audit egress IP geo-detects as US; sessions were pinned with `?country=GB` as a real UK visitor would see it. Read-only run: cart used, nothing submitted, stopped at the checkout landing page. Every interaction below is a literal keyboard event — no programmatic clicks.)*

### Step 1 — First Tab, and the site does the single most important thing right
**Did:** Landed on the homepage, pressed Tab.
**Got:** "Skip To Content" — a real, visible skip link, first stop, black-on-white with a proper focus ring, and Enter genuinely moves focus to `#MainContent`. Kept tabbing: HOME, SHOP ALL, COLLECTIONS, CONTACT, logo, country selector, Search, account, bag — every stop with a visible white outline on the black header. No focus ever silently disappeared in the header.
**Expected:** Honestly, half of the independent shops I visit have no skip link and invisible focus. This one has both, correctly.
**Felt:** "A skip link that exists AND works. Someone left the theme's accessibility on. Promising."
**Next:** continued (u15-01, u15-06)

### Step 2 — The newsletter popup: it doesn't trap me — it does something weirder. It ignores me
**Did:** ~10 seconds in, mid-tab through the header, the "Sign up for our newsletter" modal faded in over a dimmed page. I pressed Escape. Nothing. Pressed Tab. Focus went to the country selector, then Search — the page BEHIND the popup. Kept tabbing to see where its NO THANKS lives.
**Got:** The popup is a modal in looks only: no dialog role, no focus capture, Escape is dead, and its three controls (email, Subscribe, NO THANKS) sit at tab stops 80–82 of 87 on the page. Measured cleanly: **68 Tab presses** from the top of the page before focus entered the popup. Sixty-eight. And the whole way there, the viewport scrolls up and down following invisible focus underneath the frosted overlay — I tabbed through 4x4px carousel dots (the hero slides flipped as I hit them), quick-add buttons, an entire dimmed product grid I couldn't properly read. Worse: the stop BEFORE NO THANKS is Subscribe — one mis-timed Enter from an RSI hand and I'd have submitted an empty newsletter form. When I finally hit NO THANKS (clear focus ring, to its credit) and pressed Enter, the popup died for good — and dumped my focus back at BODY, top of page, start again.
**Expected:** Escape closes it. That's the whole contract of a modal. Or at minimum: focus jumps into the dialog when it opens, so dismissing costs one or two keys, not 68.
**Felt:** "It didn't trap me — that's the accessibility failure I rehearsed for. Instead it just... sat there, king of the viewport, while I tabbed around in the dark underneath it. A mouse user pays one click. I paid 68 keys or shopped through frosted glass."
**Next:** continued — grudgingly (u15-02, u15-03, u15-07, u15-08)

### Step 3 — Tried to outrun it. It followed me
**Did:** In a fresh pass I refused to pay the 68-key toll: tabbed to SHOP ALL (3 presses) and hit Enter with the popup still up — Enter on links behind the overlay works fine, which is at least an escape route.
**Got:** /collections/all loaded ("Latest Drop", 20 of 44 products)… and ~10 seconds later the same popup faded in AGAIN, centre screen, and I tabbed through the whole grid underneath its dim. It appears on every page, every visit, until you formally dismiss it — later it materialised a third time over the product page while I had the cart drawer open, photobombing my own checkout (u15-45 shows the popup, the cart drawer and a validation bubble all on screen at once).
**Expected:** A popup that respects "I navigated away" as an answer.
**Felt:** "It's not a door, it's a seagull. Shoo it or it follows you round the shop."
**Next:** continued (u15-12, u15-13, u15-14)

### Step 4 — The menu: dropdown for mice only, but there's a side door
**Did:** Tabbed to COLLECTIONS (the only nav item with a ⌄ caret) and tried to open its dropdown: Enter, then arrows.
**Got:** It's a plain link — no aria-expanded, no haspopup, and the submenu (England Set, Nations Shorts, All products…) opens on hover only: those links are invisible to the keyboard and never appear in the tab order. There is no keyboard way to open that dropdown, full stop. BUT Enter navigates to /collections — an index page of all the collections — so everything the dropdown holds is reachable one page deeper. The grid itself is honest keyboard work: sold-out cards cost one tab stop (title only), in-stock cards cost up to six (quick-add button, title, then focusable size chips that appear on focus). Pagination links exist and take focus. It's ~90 tab stops to reach pagination on page 1 — search is clearly the sane route to a specific product.
**Expected:** Enter or arrows to open the dropdown, like every OS menu since 1984.
**Felt:** "The dropdown is a members-only club for mice. The /collections page is the fire exit — unlocked, unmarked."
**Next:** continued — went for search instead (u15-10, u15-11, u15-14)

### Step 5 — Search: the best keyboard surface in the shop… until you press Escape
**Did:** 8 tabs to the Search control, Enter.
**Got:** A full-width search overlay opened and — properly — focus landed straight in the input. Typed "italy polo": a predictive panel appeared live with the Italy Polo collection and the ITALY POLO £23.00 product card. Enter submitted to a real results page ("SEARCH RESULTS FOR italy polo — 8 results"), and 17 tabs later I was on the ITALY POLO card link; Enter took me to the product page. That whole chain — open, type, submit, pick — is genuinely keyboard-first. The one landmine: in an earlier pass I pressed Escape in the search box to change my mind, and my focus was thrown to BODY — lost entirely. I typed my query into nothing, pressed Enter, and "clicked" whatever the browser considered current — the logo. Teleported to the homepage, mid-thought. (Also: the standalone /search page greets you with "Oh no! No results found." before you've typed anything, and does NOT focus its own input.)
**Expected:** Escape to close the overlay and hand focus back to the Search button — exactly what (spoiler) the cart drawer manages to do.
**Felt:** "Opening search felt like the shop finally shook my hand. Escape felt like it then walked off mid-sentence."
**Next:** continued (u15-19, u15-40, u15-41)

### Step 6 — Product page: arrows skip the dead sizes — but the size row is where my focus goes invisible
**Did:** On /products/italy-polo (6 photos, £23.00, "Please Allow 2-5 Working Days"): 13 tabs from the top to the size group, then ArrowRight.
**Got:** The sizes are real radio buttons under the chips — and the three sold-out sizes (S, M, L, struck through) are properly disabled, so ONE ArrowRight jumped me from XS straight to XL, ticked it, and updated the URL to the XL variant. Mechanically perfect. Visually? The focus outline is drawn on the hidden 1x1px radio input, i.e. nowhere: while my focus sat in the size row there was NO visible indicator at all (u15-42) — the only proof I was there came when the arrow key moved the black selected border to XL. Four more tabs (quantity −, qty field, +) to a big obvious Add To Cart with a strong double ring, Enter.
**Expected:** A focus ring on the chip itself. Everywhere else on this site has one — its one gap is on the control that picks what I pay for.
**Felt:** "The size picker is a great keyboard citizen wearing an invisibility cloak. I operated it on faith and arrow keys."
**Next:** continued (u15-42, u15-43, u15-25)

### Step 7 — The cart drawer is the accessibility high point of the whole shop
**Did:** Add To Cart. Drawer slid in. Tabbed everything, pressed everything, then deliberately Escape'd and reopened it.
**Got:** Textbook, all of it: focus moved INTO the drawer (onto Close), and Tab cycles inside it — a real focus trap, on the one component that should have one. Every control is reachable and works by key: item links; quantity − / field / + (Enter on + took it to 2, the drawer re-rendered and my focus SURVIVED, still on the + button — I put it back to 1); a remove link; the terms checkbox — 16x16px but focusable, ringed, and Space ticks it; View Cart; Checkout. Escape CLOSES the drawer and returns focus to Add To Cart — the exact behaviour the popup and search couldn't manage. Even the bag icon in the header intercepts Enter to open this drawer, and after Escape puts focus back on the bag. Two smudges: the Close button is the one drawer control with no visible focus ring, and — as every persona before me found — the subtotal says "Taxes included." and not one word about shipping cost.
**Expected:** After the popup, honestly, a mess. Got the best-behaved cart drawer I've used all year.
**Felt:** "Whoever built this drawer read the spec. Whoever built the popup never met them."
**Next:** continued (u15-26, u15-44, u15-49, u15-27, u15-28)

### Step 8 — The terms toll booth, then a checkout that behaves
**Did:** Cocky, I tabbed to Checkout and hit Enter WITHOUT ticking the terms box.
**Got:** The browser's native bubble — "Please check this box if you want to proceed." — and focus was moved onto the offending checkbox for me (u15-45: that bubble, the drawer, and the third coming of the newsletter popup, all in one screenshot). Space to tick, three tabs back to Checkout, Enter — and the real Shopify checkout landed: "Checkout - Unfounded", bird logo, Shop Pay / G Pay express row, Contact, Delivery pre-set to United Kingdom, order summary showing Italy Polo XL £23.00 — and shipping still "Enter shipping address", the price a mystery to the very end. First Tab on the checkout page: a "Skip to content" link with a visible ring. Keyboard-safe ground. STOPPED HERE per audit rules, nothing entered.
**Expected:** A silent dead button on the unticked checkout — got a focused, explained failure instead, which is more than most shops give.
**Felt:** "From Add To Cart to the till, this shop was flawless on keys. Shame about the front door."
**Next:** stopped at the checkout landing (audit line) with intent (u15-50, u15-51, u15-52, u15-53)

## Outcome
**Bought / didn't:** Bought (audit sense): reached the checkout landing with the Italy Polo (XL, £23.00) — every single step from homepage to checkout achieved with keyboard alone. Nothing on the path was IMPOSSIBLE: no traps, no unreachable buy button. The three genuine keyboard failures are all survivable: the popup (68 presses or shop under frosted glass), the hover-only COLLECTIONS dropdown (mouse-only, workaround via /collections), and the search Escape (focus obliterated to BODY).
**Total time:** ~13 minutes — roughly 4 of them paid to the newsletter popup across its three appearances, and ~120 of the ~180 total key presses spent on things a mouse user never sees.
**Worst moment:** Realising the popup's NO THANKS was 68 Tab presses away, with Subscribe directly before it in the tab order — dismissal priced as an endurance event, with a subscription landmine at the finish line. Runner-up: Escape in the search box throwing focus to BODY, so my typed query went into the void and Enter "clicked" the logo.
**Best moment:** The cart drawer — real focus trap, focus into the drawer on open, Escape closes AND restores focus to Add To Cart, quantity re-render that doesn't eat focus, Space-tickable terms box. Honourable mentions: a skip link that works, arrows auto-skipping sold-out sizes, and the native "Please check this box" bubble that moves focus to the checkbox it's complaining about.
**Would they come back?** Yes — cautiously. Marcus can shop here, and by keyboard-web standards this is top-quartile: visible focus almost everywhere, sane tab order, an exemplary drawer. But he'll arrive braced for the popup toll and he'll never trust Escape in the search box again — and each of those is one bad reflex away from an accidental subscribe or a lost basket.
**One thing that would have changed the outcome:** The outcome succeeded, so the upgrade: make the popup a real dialog — focus into it on open, Escape to dismiss, focus restored where it stole the viewport from. One component fixed turns this from "keyboard-possible" into "keyboard-good", because everything after the popup already mostly is.
