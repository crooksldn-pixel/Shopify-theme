# 18 — Maya, evening browse with prefers-reduced-motion on (vestibular disorder — animation makes her ill)
**Device:** iPhone-class mobile, 390x844, reduced motion ON · **Goal:** see if this loud-looking streetwear site is even usable for her — homepage, the popup everyone mentions, menu, one product, add to bag · **Mood:** braced. New sites usually mean parallax, sliders, and ten minutes of nausea.

### Step 1 — Opened the homepage
**Did:** Loaded the site, hands half over eyes, ready to close the tab.
**Got:** Nothing moved. At all. A big cookie sheet sat over the lower third, the status bar said "FREE UK SHIPPING OVER £30 // ORDER BY 18:00 FOR SAME-DAY DISPATCH" and just... sat there, no scrolling ticker. A terminal-style line "> 13 PRODUCTS AVAILABLE TO PURCHASE" was already fully printed — no typing effect. Two screenshots 1.5s apart were pixel-identical; zero running animations in the page.
**Expected:** A hype brand homepage = auto-playing everything.
**Felt:** "Wait. It's... still. It's actually still. I can look at it."
**Next:** Deal with the cookie sheet.

### Step 2 — Declined cookies, and the popup appeared
**Did:** Tapped Decline on the cookie banner (Manage preferences / Accept / Decline — all three present, no dark pattern).
**Got:** A full-screen dark overlay was already waiting behind it: "CROOKSLDN: THE GETAWAY — Crack the cuffs. 10% off your first order — code sent by text. Attempts unlimited. RUN IT / NOT NOW. One code per player." It appeared instantly — no zoom, no slide, no fade. Nothing inside it moved.
**Expected:** Popups usually bounce in and shimmer.
**Felt:** "Ambushed the second I arrive, which is rude — but at least it's a *motionless* ambush. And 'code sent by text' makes me wary."
**Next:** Curiosity wins. She's heard these game popups are seizure fuel — she taps RUN IT to see how bad it gets, ready to close it instantly.

### Step 3 — RUN IT: the lock-up opens
**Did:** Tapped RUN IT.
**Got:** A black sheet with "OPENING THE LOCK-UP…" for a few seconds (a beat too long, she wondered if it broke), then a second intro inside a frame: "CRACK THE CUFFS. 10% off your first order if you do. Three tumblers. Tap each one at the right moment. RUN IT / NOT NOW. One code per player. Attempts unlimited. Code expires in 20 minutes." Different title than the first screen, and its own RUN IT again.
**Expected:** One intro, not two; one name, not two ("THE GETAWAY" outside, "CRACK THE CUFFS." inside).
**Felt:** "Two doors to get into one game. And which is it called? Still — nothing has moved yet. I'm oddly okay."
**Next:** Tap the inner RUN IT. This is the moment she expects to regret.

### Step 4 — The tumblers (the part she feared)
**Did:** Tapped RUN IT and watched the actual game, ready to slam the X.
**Got:** Three bordered boxes, each with one large digit and "TAP" under it, header "TAP TO STOP", and — the line that made her exhale — "Tap each tumbler to lock it. No timer — take your time." No timer bar anywhere. The digits do still change on their own: a clean swap to the next number about every 0.7 seconds (measured ticks at ~613/1310/2007/2716/3392ms), all three in step, like a station clock — not a spinning reel, no blur, no easing, zero CSS animations running.
**Expected:** Slot-machine reels whirring — instant nausea.
**Felt:** "They actually thought about me. There's no countdown breathing down my neck and the numbers step instead of spin. The steady tick-tick-tick in three places is still more flicker than I'd like — I can't pause it — but it doesn't make me ill. Livable."
**Next:** With no timer, she may as well play — it costs nothing and she wants to see what they ask for at the end.

### Step 5 — Locked all three, won, and was NOT forced into SMS
**Did:** Tapped the three tumblers, one at a time, at her own pace (locked 1, 4, 6 — apparently any digits do; "the right moment" is theatre).
**Got:** "1/3… 2/3… CUFFS OPEN — You cracked the cuffs. Cutting your code." then a result card: "EVIDENCE Nº GTWY-KU4G — 10% off. One use. Expires in 19:59" with a big COPY CODE button. The phone number is *optional*, below a divider: "Want it kept on file? Phone number goes in the evidence log — one message per drop, nothing else." with an 07XXXXXXXXX field, FILE IT, and a plain "No need — I've got it" opt-out. She did not enter any number. Only remaining movement: the "Expires in 19:59" countdown ticking once a second. No confetti, no shake, no flash on winning.
**Expected:** After "code sent by text" on the intro, she assumed the code would be held hostage behind her phone number.
**Felt:** "The code is just... there, with a copy button. The text thing is a genuine opt-in. That's the most respectful discount popup I've met. The 20-minute expiry is a bit of pressure I didn't need, and one more ticking number on screen — but fine."
**Next:** Close it and see the actual shop.

### Step 6 — Menu drawer and the CASE 001 board
**Did:** Closed the popup (it vanished instantly, no exit animation) and opened MENU.
**Got:** Drawer with SHOP / TRACKING / QUESTIONS / TERMS / CONTACT, and below, the "CASE 001: THE GETAWAY" pixel-art heist board — a thief, an officer, a coin on an alley grid — completely frozen, one static frame. Full-page screenshots 1.2s apart were identical; zero animations. The DOM even carries a written description ("Animated map: a thief moves through an alley grid collecting coins while a patrolling officer…") in place of the show. Button under it: "PLAY CROOKS: THE GETAWAY" — a third variant of the game's name.
**Expected:** The board to be the thing that finally forces her to look away.
**Felt:** "It's a poster instead of a cartoon, and they even wrote down what it would have done. This is what respecting the setting looks like."
**Next:** One product, then bag.

### Step 7 — Product page and add to bag
**Did:** Went to the grey joggers (GREY CONVICT SWEATS, £60), picked XS (only XS and S orderable — M/L/XL struck through), tapped ADD TO BAG.
**Got:** Perfectly still page (screenshots identical over 1.2s). After adding: no drawer flew in — just an inline line "> Added — 1 in bag  View bag" under the button and BAG [0] became BAG [1]. "Order before 18:00 and it ships today" reads as static text. It was past 18:00 and it still said "Ordered now — leaves today", which she side-eyed, but that's not a motion problem.
**Expected:** A cart panel sliding across the screen — the classic trigger.
**Felt:** "Even the cart doesn't lunge at me. Quiet inline confirmation. I could shop here for real."
**Next:** Stop here — she has what she came to learn.

### Step 8 — Auditor control check (harness, out of persona)
**Did:** Re-ran the same game in an identical session with reduced motion OFF to verify what the setting removes.
**Got:** Control game copy is "Tap each tumbler before the bar drains" with a live draining bar (running 100ms width transitions) and digits swapping every ~50–75ms (a blur, ~15/sec) vs one swap per ~700ms under reduced motion. Control drawer board animates (frames differ over 1s); reduced board is frozen. Homepage boot line and status bar are static in BOTH modes — nothing is lost to the setting; the game is fully completable (easier, if anything) with it on. The iframe (crackthecuffs.base44.app — old name in the domain) correctly inherits prefers-reduced-motion.
**Expected:** Per the earlier check, decorations gone but tumblers unchanged.
**Felt:** n/a — evidence step.
**Next:** Write up.

## Outcome
**Bought / didn't:** Didn't buy — added XS joggers to bag as a test and stopped there (tour, not a purchase mission). She left with discount code GTWY-KU4G copied and her phone number kept to herself.
**Total time:** ~11 minutes
**Worst moment:** Realising the three tumbler digits tick away on their own forever with no way to pause them — plus a second ticking countdown on the win screen. Discrete swaps, not motion sickness fuel, but it's the one place the site still moves without being asked, and 3-in-sync flicker draws the eye constantly.
**Best moment:** "No timer — take your time." — the game explicitly rebuilt itself around her setting (timer bar deleted, tick slowed ~10x, heist board frozen with a written description), and then handed her the code on screen without demanding her phone number.
**Would they come back?** Yes — genuinely. This is one of the very few hype-brand sites she can look at without consequences; she'd shop here over competitors for that alone.
**One thing that would have changed the outcome:** Nothing blocked her — but to make it flawless: let the tumblers hold still until tapped (or add a pause), and match the copy to the reduced game ("at the right moment" / "TAP TO STOP" describe a timing challenge that no longer exists).
