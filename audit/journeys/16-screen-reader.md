# 16 — Priya, screen reader user (NVDA on desktop), buys her second pair of CROOKS bottoms
**Device:** Desktop 1440x900, normal broadband · **Goal:** Heard about the V2 Baggies from a mate; wants to pick a size and buy them tonight, unassisted · **Mood:** Practised, patient, but braced — streetwear sites are usually a wall of unlabelled buttons

*Method note: this run could not use a live screen reader. Every "I hear" below is what the accessibility tree would hand NVDA — accessible names, roles, states and live-region announcements read via ARIA snapshots and DOM inspection. Where I'm inferring how a reader would voice something, I say so.*

### Step 1 — Landed on the homepage and took a first listen
**Did:** Opened the site and let the page settle, listening for title, landmarks and the first focusable things.
**Got:** Page title "CROOKSLDN". A "Skip to content" link to #MainContent as the very first stop. Proper landmarks: banner, "Main menu" navigation, main, footer. Heading structure starts with H1 "CROOKSLDN" then H2s (CATALOGUE, EVERY ORDER SHIPS LIKE THIS...). A cookie banner announced as an alertdialog with an H2 "COOKIE CONSENT" and three plainly named buttons: Manage preferences, Accept, Decline. The logo link is named "CROOKSLDN" via image alt. Even the LIGHT MODE switch is a real toggle with aria-pressed.
**Expected:** A div soup with icon buttons called "button". This is a fashion label after all.
**Felt:** Honestly relieved. Skip link, labelled nav, a cookie dialog that says what it is — someone built this properly. I hear "COOKIE CONSENT" and I know exactly what's being asked of me.
**Next:** continued

### Step 2 — The page went quiet on me (the popup)
**Did:** Was still deciding on the cookie banner when I noticed the page had changed under me.
**Got:** A "Crack the Cuffs" overlay had opened — it is marked role=dialog, aria-modal=true, aria-label "Crack the Cuffs", which is the right ARIA. But focus never moved into it: my cursor was still sitting in the page body. Nothing announced it. And inside the dialog there is only an unnamed iframe and a "Close" button. (Inferred: with aria-modal=true honoured, everything OUTSIDE the dialog drops out of my browse mode — so from my side, the whole site just vanished and was replaced by "frame" and "Close, button", with no explanation of what a Crack the Cuffs is.) Escape closed it.
**Expected:** If a dialog opens, I expect to be put in it and told what it is.
**Felt:** This is the classic silent-modal trap. A sighted person sees a game popup; I get a site that suddenly reads as empty except an unlabelled frame. If I hadn't guessed Escape, I'd have been stuck wandering a dialog I never knew opened. Whatever the game says visually, none of it reaches me.
**Next:** hesitated, pressed Escape, carried on

### Step 3 — Accepted cookies and tried the menu
**Did:** Activated Accept, then found "MENU, button, collapsed" in the header and pressed Enter.
**Got:** A drawer opened as a real dialog: role=dialog, aria-modal=true, named "Main menu". Focus moved straight onto its CLOSE button, the page behind was hidden from me (aria-hidden on main), and inside is a labelled "Main menu" navigation with a proper nested list — SHOP with ALL/NEW/TEES/DENIM/SWEATS, then TRACKING, QUESTIONS, TERMS, Contact, ACCOUNT, "BAG [0]". Escape closed it and put me back on the MENU button, which now reads collapsed again.
**Expected:** A drawer that half-works — usually focus stays behind it.
**Felt:** Textbook. I hear "Main menu, dialog", I'm inside it, Escape puts me back where I was. "BAG left bracket zero right bracket" is a bit of cosplay in my ear, but I know it's the bag and I know it's empty. (One nitpick: the link to their game reads out an entire paragraph about a thief in an alley grid — a mouthful.)
**Next:** continued to CATALOGUE

### Step 4 — Browsed the catalogue by product
**Did:** Went to the catalogue and arrowed through the product list.
**Got:** A list of listitems, one link per product, each announcing everything in one go: "NO. 11 SWEATS V2 BAGGIES £60.00 AVAILABLE". Tees add their colourways. Image alts are real descriptions ("blue wash heavyweight denim jeans with baggy fit and white handcuff embroidery on back pockets").
**Expected:** Card soup — image link, then title link, then price floating loose.
**Felt:** One link per product with name, price and availability in it — that's how you do it. Some cards read the title twice (the photo's alt text, then the title again), which is wordy but never confusing. I found my baggies in seconds.
**Next:** continued into V2 BAGGIES

### Step 5 — Landed on the product and read the buy area
**Did:** Opened V2 BAGGIES, jumped by heading to the H1, then read forward into the form.
**Got:** "V2 BAGGIES, heading level 1", price "£60.00", then a group named "Size" containing five toggle buttons: "Size XS, pressed", "Size S", then "Size M", "Size L", "Size XL" — those last three in a dimmed/unavailable state (aria-disabled, so I still land on them and hear them rather than them being skipped). After the grid: "IN STOCK", a "Size guide" button, "Order before 18:00 and it ships today", and "Add to bag, button".
**Expected:** Sizes as bare buttons called "XS" at best, sold-out ones simply missing.
**Felt:** Each size tells me its name and whether it's selected, and the dead ones are still there and audibly dimmed — so I know M, L and XL exist and aren't options tonight. I hear "Size XS, toggle button, pressed" before I've chosen anything though — the site picked XS for me, which I only notice because I listen for it.
**Next:** continued

### Step 6 — Picked my size
**Did:** Moved to "Size S" and pressed Enter.
**Got:** "Size S" flipped to pressed, "Size XS" to not pressed, and the stock line — a polite live region — re-announced "IN STOCK".
**Expected:** State to change silently, if at all.
**Felt:** I hear the pressed state move to S and a quiet "IN STOCK" confirmation without leaving the size grid. That's all I ever ask for.
**Next:** continued

### Step 7 — Poked a sold-out size to see what I'd be told
**Did:** Went back to "Size M, dimmed" and activated it anyway (readers let you fire these).
**Got:** A polite announcement: "SIZE M IS SOLD OUT". The add button becomes "SOLD OUT", and a new field appears below, properly labelled "TELL ME WHEN THIS SIZE IS BACK" with an email input. Selected S again afterwards and everything recovered.
**Expected:** A dead click and silence.
**Felt:** Genuinely impressed — I'm TOLD the size is sold out, in words, and offered a labelled restock field. My only doubt: plenty of screen reader users never press a "dimmed" button because dimmed usually means "does nothing", so some people will never discover the notify option exists. (I didn't submit the form — I know these things end in a captcha and I wasn't risking my evening on one.)
**Next:** continued

### Step 8 — Checked the accordions and the size guide
**Did:** Read the H2 accordions — SPECIFICATION, ITEM DESCRIPTION, MEASUREMENTS, CHAIN OF CUSTODY — opened SPECIFICATION with Enter, closed it, then tried the "Size guide" button.
**Got:** Accordions are buttons with aria-expanded that toggles true/false and the content appears right after (fabric, cut, origin, care — all real text). The size guide is different: pressing it produced no announcement and no expanded state on the button. A region named "Measurements table" with a real table (SIZE / WAIST / INSEAM / RISE / HEM, all in cm, with proper column headers) had appeared elsewhere on the page — I only found it by going exploring after nothing seemed to happen.
**Expected:** Accordions to be clickable divs; they weren't.
**Felt:** The accordions are exactly right — "SPECIFICATION, button, collapsed... expanded". The size guide made me think the button was broken: I pressed it, heard nothing, and only later stumbled on a measurements table that must have been it. A 40cm waist on the S, for the record — the table itself reads beautifully once you find it.
**Next:** hesitated at the silence, then continued

### Step 9 — Added to bag
**Did:** With S selected, moved to "Add to bag" and pressed Enter.
**Got:** A polite live region spoke: "Added — 1 in bag View bag". Focus stayed on the Add to bag button. The header bag link now reads "BAG [1]". The "View bag" link that was announced is a real link sitting right there — I followed it.
**Expected:** The silent add — the one where you press the button, hear nothing, and have to trek to the cart to learn whether anything happened.
**Felt:** This is the moment that usually kills these sites for me, and it just... worked. I hear that it was added, how many are in the bag, and I'm handed a link to go there. No focus stolen, no mystery drawer.
**Next:** continued to the bag

### Step 10 — The bag, and through to checkout
**Did:** Read the cart page top to bottom, nudged quantity up to see what I'd be told, put it back, then activated "Check out".
**Got:** Heading level 1 announces "Cart 1" (the item count is glued into the heading). Before it, a progressbar named "Progress toward free carriage" and a live message "£10.00 to free Tracked 24". The cart itself is a real table with column headers; my row reads the product, "Size: S", price, then "Decrease quantity" (correctly disabled at 1), a "Quantity" spinbutton, "Increase quantity", and "Remove V2 BAGGIES - S" — named down to the size. Pressing Increase announced "Estimated total £120.00 GBP" (the total is a status region) and then "Free Tracked 24 — unlocked". Decrease put it back. The discount box only gets its name from its placeholder, "Discount code" (inferred: its visual label is empty — placeholder-as-name works today but it's thin). Two unnamed frames sit after the Check out button (express-pay widgets, I'd guess). "Check out, button" took me to a page titled "Checkout - CROOKSLDN". That's where I stopped — card details are for when I'm actually keeping them.
**Expected:** A cart of unlabelled plus/minus icons and a remove link called "×".
**Felt:** "Remove V2 BAGGIES dash S" — the remove button tells me WHICH item, which matters enormously when there are three things in a bag. And the total re-announcing itself when quantity changes means I never have to go hunt for it. "Cart one" as a heading is odd in the ear — one what? — but I knew. The free-shipping voice even told me when I'd unlocked it. I reached checkout without asking anyone for eyes.
**Next:** continued to checkout intent — done

## Outcome
**Bought / didn't:** Bought — size S V2 Baggies, reached the Shopify checkout door unassisted (stopped at payment by audit rules, but there was nothing between me and it).
**Total time:** ~28 minutes — a sighted user would do this in 8; a good chunk of my extra time was the silent popup and the silent size guide, the rest is just how I browse.
**Worst moment:** The Crack the Cuffs popup opening without moving focus or announcing itself — "the whole site just went quiet and turned into an unlabelled frame and a Close button. If I didn't know Escape, I'd still be in there."
**Best moment:** "Added — 1 in bag. View bag." spoken the instant I pressed Add to bag — followed closely by a sold-out size that actually SAYS "SIZE M IS SOLD OUT" out loud.
**Would they come back?** Yes — unreservedly, and she'd tell the access-tech group chat. This is one of the few streetwear stores where the size grid, the stock state and the cart all speak. She'll dread the popup every visit though.
**One thing that would have changed the outcome:** Nothing blocked the purchase — but move focus into the Crack the Cuffs dialog when it opens (and give its iframe a name); as it stands the site's flashiest feature is a hole a screen reader user can silently fall into.
