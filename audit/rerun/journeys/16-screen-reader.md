# 16 — Priya, screen reader user (NVDA on desktop), back for round two
**Device:** Desktop 1440x900, normal broadband · **Goal:** Bought the V2 Baggies in S last time; tonight she wants to hear whether the site still speaks to her — and whether that silent popup ever got fixed · **Mood:** Fond but wary; she told the access-tech group chat about this shop AND about its popup trap

*Method note: as in run 1, no live screen reader was available. Every "I hear" below is what the accessibility tree would hand NVDA — roles, accessible names, states and live-region text read via ARIA snapshots, DOM inspection and mutation-watching of aria-live regions. Where I'm inferring how a reader voices something, I say so.*

### Step 1 — Landed and took the first listen
**Did:** Opened the homepage and let it settle: title, landmarks, headings, first focus stops.
**Got:** Title "CROOKSLDN". "Skip to content" → #MainContent as the first link. Landmarks: banner, main, footer. Headings: H1 "CROOKSLDN", then H2s — WORLD OF CROOKS, CATALOGUE, EVERY ORDER SHIPS LIKE THIS, REGISTER AS INFORMANT. Cookie banner is still a proper alertdialog labelled by its "Cookie consent" heading, with Manage preferences / Accept / Decline as plainly named buttons. One stray polite announcement drifted past on arrival: "Frame 4, PRODUCT: REDACTED" — from a dedicated sr-only live region attached to the photo strip (the frames read "- FRAME 01 / 05 - LOCATION REDACTED" etc.). It spoke once and never again in a 20-second listen; with my reduced-motion setting the strip doesn't rotate, so it doesn't chatter. (Inferred: a one-off caption announcement as the strip initialises.)
**Expected:** The solid arrival I remembered.
**Felt:** Same good bones. "Frame 4, PRODUCT: REDACTED" in my ear apropos of nothing is very this-brand — cryptic, but it said it once and left me alone.
**Next:** declined cookies, braced for the popup

### Step 2 — The popup came back — and this time it introduced itself
**Did:** Activated Decline; less than a second later the overlay opened.
**Got:** role=dialog, aria-modal=true, accessible name "CROOKSLDN: The Getaway" — and focus MOVED INTO IT, landing on the Close button. Everything behind (main, footer) gets aria-hidden. Inside is real, readable content: H2 "CROOKSLDN: THE GETAWAY", a paragraph — "Crack the cuffs. 10% off your first order — code sent by text. Attempts unlimited." — then buttons "RUN IT" and "NOT NOW", and "One code per player." Escape closes it, and both Escape and NOT NOW restore the page (aria-hidden comes off). One rough edge: after closing, focus is dropped on the page body — nowhere in particular — so I have to find my place again.
**Expected:** Run 1's nightmare: an unannounced modal with an unnamed frame, the whole site silently swapped out from under me.
**Felt:** Night and day. Last time I called this a hole a screen reader user falls into; this time I hear "CROOKSLDN: The Getaway, dialog", I'm standing on its Close button, and the offer is written in front of me in actual text. I know what it is, what it wants, and how to leave. The focus-drop on close is a wobble, not a trap.
**Next:** last time the game was closed to me — this time it named itself, so I went in

### Step 3 — Played the game blind, and won
**Did:** Pressed RUN IT. The dialog's content became an iframe — titled "Crack the Cuffs" (the old name; the dialog around it says "The Getaway" — two names for one thing, mildly disorienting). Inside the frame: a second pitch screen — H1 "CRACK THE CUFFS.", "Three tumblers. Click each one at the right moment.", its own named Run It / Not Now / "Close popup" buttons — so I hear the sales pitch twice. Pressed the inner Run It.
**Got:** A game I can actually play. Three real buttons named "Tumbler 1, spinning, tap to stop" (2, 3 likewise), text "0/3 LOCKED" and — bless them — "Click each tumbler to lock it. No timer — take your time." Focus did fall to the frame body when the screen changed, so I had to walk forward to find the tumblers. Each press renames the button ("Tumbler 1, locked on 4") and disables it. The "1/3 LOCKED" progress line is plain text, not announced — I only knew by re-reading. On the third lock a polite live region spoke: "You cracked the cuffs. Cutting your code." Then the result screen: "EVIDENCE Nº GTWY-RHE3 — 10% off. One use. Expires in 19:56", a named COPY CODE button — the code is right there on screen, no text message needed. The phone number is optional and honestly framed: "Want it kept on file? Phone number goes in the evidence log — one message per drop, nothing else", with a labelled input (type=tel, name "UK phone number", placeholder 07XXXXXXXXX), a FILE IT submit and a "No need — I've got it" decline. Per audit rules I looked and did not enter a number. Two blemishes: the intro card upstairs promised "code sent by text" — not true any more, the code is shown on screen; and for the first beat the expiry line rendered "CODE EXPIRED" before the countdown started — read the screen too eagerly and you'd think you'd lost before you began.
**Expected:** A canvas of silence with a Close button.
**Felt:** I did not expect to WIN A DISCOUNT CODE UNASSISTED in a streetwear popup game. Labelled tumblers, no timer, a spoken win, a code in plain text with a copy button — someone thought about players like me. My notes for their inbox: announce the LOCKED count, keep focus on something when screens change, and make the outer card stop promising SMS it no longer sends.
**Next:** closed the popup with the code in my back pocket, went shopping

### Step 4 — The menu drawer
**Did:** Found "MENU, button" in the header, pressed Enter, Tab-walked it, then Escape.
**Got:** role=dialog, aria-modal=true, named "Main menu"; focus lands on its CLOSE button; main is aria-hidden behind it. Inside, a "Main menu" navigation with a proper list: SHOP (with a "Show SHOP links" disclosure), TRACKING, QUESTIONS, TERMS, Contact, then ACCOUNT and "BAG [0]". Focus stayed inside across 25 Tabs; Escape closed it and put me back on the MENU button.
**Expected:** The textbook drawer from run 1.
**Felt:** Still textbook. Still the same nitpick: the game link reads out an entire paragraph about a thief in an alley grid before I can move on — a mouthful every single visit.
**Next:** to the catalogue

### Step 5 — Catalogue by ear
**Did:** Opened ALL and arrowed down the product list, hunting for my baggies.
**Got:** H1 "ALL", a real list of 13 items, one link per product announcing everything at once — "NO. 01 SWEATS CHARCOAL CELLBLOCK CREWNECK £50.00 AVAILABLE". The view toggles (FLAT pressed / ON MODEL) and the register filters (ALL / T-SHIRT / DENIM / SWEATS / ACCESSORIES) are honest aria-pressed toggle buttons. My baggies took a second to find: the card now says "NO. 09 SWEATS GREY CONVICT SWEATS £60.00 2 OF 5 SIZES LEFT" — but its photo's alt text still says "V2 BAGGIES", which is the only reason I was sure it was the same trousers. "2 OF 5 SIZES LEFT" spoken inside the card link is genuinely useful — I knew stock was thin before I clicked.
**Expected:** To find "V2 BAGGIES" where I left them.
**Felt:** They renamed my trousers. The old name surviving in the image alt is a bug that accidentally did me a favour — I'd rather they said "formerly V2 Baggies" out loud. The card itself is exemplary: name, price, and how many sizes are left, in one breath.
**Next:** into GREY CONVICT SWEATS

### Step 6 — The size grid speaks, and nothing is chosen for me
**Did:** H1 "GREY CONVICT SWEATS", price £60.00, then the size row: a group named "Size" of toggle buttons — "Size XS", "Size S", then "Size M", "Size L", "Size XL" all aria-disabled (dimmed but still landed on, so I know they exist and are gone). The stock line — a polite live region — says "Select Size", and the buy button itself reads "Select Size, button, disabled".
**Got:** Nothing pre-selected — run 1 had quietly picked XS for me; now the site waits. I pressed "Size S": pressed-state flipped to S and the live region spoke "IN STOCK". Then I deliberately fired "Size M, dimmed": a polite "SIZE M IS SOLD OUT", and a properly labelled field appeared — "Tell me when this size is back", email input, NOTIFY ME button. Selected S again; all recovered.
**Expected:** The good grid from run 1, XS pre-picked.
**Felt:** Better than last time. No silent default to catch me out, the grid tells me name + state, sold-out sizes say so in words, and the restock offer is labelled. My standing caveat: readers who never press "dimmed" buttons will never hear the notify option exists.
**Next:** measurements — I'm between reorder confidence and curiosity

### Step 7 — The size guide button is still mute, but the table now lands in my lap
**Did:** Pressed "Size guide, button".
**Got:** From the button itself: nothing. No aria-expanded, no announcement, focus doesn't move. But this time the page expanded the MEASUREMENTS accordion (its own H2 button elsewhere flips to expanded) and scrolled the table right to the top of the view. The table is the best-spoken thing on the site: a region named "Measurements table" holding a real table with a CAPTION — "True to size. These are the garment's own full measurements." — which I hear the moment I enter the table, before any numbers. Column headers size / waist / inseam / leg opening are TH scope=col; each size is a TH scope=row; and every cell carries its unit: in table mode I hear "S, row... waist, 81.3 centimetres" (inferred voicing; the header associations and per-cell "81.3cm" text are verified). The CM / IN switch is a pair of aria-pressed toggles; flipping to IN is silent but the state is audible and the cells re-read "32in", "30in". Numbers step sensibly XS→XL.
**Expected:** Run 1's silent button and a table I had to stumble on.
**Felt:** Half-fixed. The button still plays dead — press, silence, nothing — and a reader who doesn't go exploring afterwards will again conclude it's broken. But the payoff moved to arm's reach, and the table itself is how every size chart should read: "True to size" and "the garment's own measurements" spoken up front answers the two questions I actually had, and units in every cell means no guessing what 81.3 is. Give that button aria-expanded and this becomes perfect.
**Next:** skimmed the accordions

### Step 8 — Accordions
**Did:** Walked CHAIN OF CUSTODY — SHIPPING & RETURNS, SPECIFICATION, ITEM DESCRIPTION, MEASUREMENTS.
**Got:** All are buttons with aria-expanded and aria-controls under H2s; SPECIFICATION toggled to expanded with real content behind it. The visual +/− glyph is part of each name ("Specification plus" — inferred voicing).
**Expected:** Fine, and they were.
**Felt:** The "plus" suffix is a tiny cough in the ear; the states are what matter and they're right.
**Next:** buy it

### Step 9 — Add to bag
**Did:** With S selected the buy button reads "Add to bag, button"; pressed Enter.
**Got:** A polite live region spoke "Added — 1 in bag View bag". Focus stayed put; no drawer hijacked me; the header now reads "BAG [1]"; a real "View bag" link sits where announced. Followed it.
**Expected:** The run-1 magic moment.
**Felt:** Still my favourite pattern on any shop: told it worked, told the count, handed the way there.
**Next:** the bag

### Step 10 — The bag, and to the checkout door
**Did:** Read the cart page top to bottom, nudged quantity up and back, then Check out.
**Got:** H1 "Cart 1" (count still glued to the heading — "cart one" remains odd in the ear). A progressbar named "Progress toward free carriage" with a live "£20.00 to free Tracked 24". A true table — headers Product image / Product information / Quantity / Product total. My row: image link announcing "V2 BAGGIES" (old name again), title link "GREY CONVICT SWEATS", "Size: S" as a proper term/definition pair, "Decrease quantity" correctly disabled at 1, a "Quantity" spinbutton, "Increase quantity", and "Remove GREY CONVICT SWEATS - S" — named down to the size. Increase spoke "Estimated total £120.00 GBP" then "Free Tracked 24 — unlocked"; decrease spoke "£60.00" and "£20.00 to free Tracked 24". The discount field — where that game code would go — now has a real label, "Apply a discount code", with a visible "Apply" button (run 1 it leaned on a placeholder). PayPal's express iframe is titled; one other frame next to it has no title (small blot). "Check out, button" → page titled "Checkout - CROOKSLDN". Stopped there, per the rules — and per my rules, since the code stays unspent tonight.
**Expected:** The strong cart from run 1.
**Felt:** Stronger. The remove button that names its item, totals that speak when they change, a labelled discount field — and my ear catching "V2 BAGGIES" then "GREY CONVICT SWEATS" for the same trousers in the same row. Pick a name, tell the alt text.
**Next:** done — checkout door reached, unassisted, again

## Outcome
**Bought / didn't:** Bought — GREY CONVICT SWEATS (née V2 Baggies) in S, reached the Shopify checkout door unassisted; stopped at payment by audit rule.
**Total time:** ~25 minutes — and unlike run 1, almost none of it was lost to silence; the extra time was the game (which I chose, and won).
**Worst moment:** The "Size guide" button still playing dead — press, silence, no state change on the button itself; I only trust it because I went looking afterwards. Honourable mentions: focus dumped on the body whenever the popup closes, and the result screen flashing "CODE EXPIRED" before the countdown wakes up.
**Best moment:** "You cracked the cuffs. Cutting your code." — a popup that trapped me silently in run 1 turned into a game I could play and win by ear, with the code in plain text and the phone number optional. Closely followed by the measurements caption: "True to size. These are the garment's own full measurements."
**Would they come back?** Yes — enthusiastically. Run 1 she came back despite the popup; run 2 she'd come back partly BECAUSE of it. The group chat is getting a correction post.
**One thing that would have changed the outcome:** Nothing blocked her — but put aria-expanded (or any announcement) on the Size guide button so the best-spoken table on the site stops hiding behind the only silent control left in the buy flow.
