# 20 — Maya, back again: one parcel to find, one pair of jeans to send back
**Device:** iPhone-size mobile (390×844), normal wifi · **Goal:** find out where last week's order is, then start a return on the jeans that don't fit · **Mood:** braced — her last after-sales visit here ended with "which one of you is lying?", so she's expecting to go in circles again

> **Note for the audit:** no test login was supplied, so everything below is the SIGNED-OUT experience. What a signed-in customer sees was **not testable** and is not covered here. Nothing was submitted to any form, on-site or external, per audit limits.

### Step 1 — Opened the homepage: one interruption at a time now
**Did:** Went to the site, 9-something pm, phone in bed. Braced for the double-stack from last time — game popup ON TOP of cookie banner.
**Got:** Just the cookie consent sheet over the bottom half of the page. No popup on top of it. She read the homepage headline in peace and tapped Decline.
**Expected:** Two overlays fighting for the same thumb.
**Felt:** "One thing at a time. Thank you." Small, but it's the difference between a doorman and a scrum.
**Next:** continued — (screens: r20-01, r20-03)

### Step 2 — The Getaway popup arrived — after she'd answered the cookies
**Did:** About a second after Decline, a full-screen popup: "CROOKSLDN: THE GETAWAY — Crack the cuffs. 10% off your first order — code sent by text. Attempts unlimited." RUN IT / NOT NOW / ×, "One code per player."
**Got:** Still a takeover, still aimed at someone's FIRST order via SMS — and they already have her money, so it's not for her. Tapped NOT NOW. It went, and — the part she only appreciated later — it never came back all night: not on the tracking page, not on the FAQ, not even when she closed the tab and reopened the site. Neither did the cookie banner. *(Audit note: dismissal is remembered in localStorage — `crooksldn_ctc_snooze`, a timestamp — so within this browser one NOT NOW held for the whole visit; observe-only, nothing entered.)*
**Expected:** To be re-pestered on every page like most shops.
**Felt:** "You asked once, I said no, you heard me." As a repeat customer she'd still rather it recognised that a first-order offer is wasted on her — but sequenced after the cookies and silenced by one tap, it's a toll now, not a wall.
**Next:** continued — (screens: r20-04, r20-05, r20-15)

### Step 3 — Tracking hunt: MENU → TRACKING, 2 taps like last time
**Did:** Tapped MENU (tap 1). Same clean drawer: SHOP, then TRACKING on its own row, QUESTIONS, TERMS, CONTACT — plus a little playable game card at the bottom now. Tapped TRACKING (tap 2).
**Got:** /pages/tracking in **2 taps from the homepage**. Findability was never the problem here.
**Expected:** Exactly this — it was the page itself she was dreading.
**Felt:** "Right. Let's see if the door opens this time."
**Next:** continued — (screen: r20-06)

### Step 4 — The tracking page: there is a form now
**Did:** Read the page, ready to be told to sign in.
**Got:** "IDENTIFICATION REQUIRED" — but then: "Signed in, every order you have placed is here… **Not signed in? Look it up with your order number and the email you used.**" And an actual form: ORDER NUMBER, EMAIL ON THE ORDER, a big FIND MY ORDER button, small print "BOTH ARE ON YOUR CONFIRMATION EMAIL. OPENS THE TRACKING CENTRE IN A NEW TAB." Underneath: "Start a return instead" and "Sign in for full order history" as the *secondary* option.
**Expected:** Last visit's locked door — one SIGN IN button and a shrug.
**Felt:** "Oh. You fixed it." Order number and email — both sitting on the confirmation email she still has. This is the exact box she asked the void for last time. Two quibbles: the headline still barks IDENTIFICATION REQUIRED above a form that requires no identification, leftover scare copy; and she didn't get to see the other side of FIND MY ORDER — *(audit note: the form was not submitted per audit limits. Read-only inspection: it GETs to `https://5wn03tnm.aftership.com` in a new tab — the same root URL that serves the RETURNS CENTER. Whether Aftership shows a tracking view or dumps the shopper into the returns flow is unverified; the merchant should click this once with a real order.)*
**Next:** continued — (screen: r20-07)

### Step 5 — Checked the FAQ's old promise against the new page
**Did:** MENU → QUESTIONS, opened "HOW DO I TRACK MY ORDER?" — the answer that burned her last time.
**Got:** Same wording: "Tracking is emailed the moment your parcel is dispatched. You can also look your order up on the tracking page — no account needed." Tapped the link; landed on the tracking page; the lookup form is right there. **The promise is true now.** She also spotted a new question that wasn't there before: "TRACKING SAYS DELIVERED BUT I HAVE NOTHING." — check neighbours and the safe place, then message within 14 days and they open a courier investigation, Royal Mail take up to 10 working days.
**Expected:** Honestly, she expected the FAQ and the page to still disagree.
**Felt:** The trust that snapped last visit quietly reset. "Both pages tell the same story now." And the delivered-but-missing answer is the first time this shop has anticipated the *bad* version of her evening rather than the buying one.
**Next:** continued — (screens: r20-08, r20-09, r20-10)

### Step 6 — Switched goals: the jeans. Scrolled to the footer
**Did:** Scrolled the homepage to the footer, where last time REFUNDS sent her on a 7-tap wild goose chase.
**Got:** The footer now reads: QUESTIONS, TERMS, SHIPPING, REFUNDS, TRACK ORDER, **RETURNS**. A RETURNS link exists. Tapped it. **1 tap from the homepage footer.**
**Expected:** To have to go back through the FAQ's "CAN I RETURN SOMETHING?" answer like last time (still there, still good — 4-tap route via MENU, and the tracking page itself now offers "Start a return instead" at 3 taps).
**Felt:** "THERE it is. In the footer. Where it should have been all along."
**Next:** continued — (screen: r20-12)

### Step 7 — The returns centre, one tap later
**Did:** Let the RETURNS link carry her off-site.
**Got:** The Aftership Returns Center, loaded clean: CROOKSLDN handcuffs up top, white card — Order number, Email, "VERIFY BY POSTAL CODE OR PHONE NUMBER", FIND YOUR ORDER, "Back to shop", "View return policy". No giant cookie banner this visit — just a small reCAPTCHA badge in the corner. She has the order number and email; the form is completable tomorrow in daylight. Stopped at the form — nothing submitted (audit limit, and it's external).
**Expected:** The second cookie interrogation she got last time. Didn't happen tonight.
**Felt:** "One tap. Last time this took me seven and a wrong turn." The white Aftership styling still looks like a different country after the black terminal, but the handcuffs logo says she's in the right place.
**Next:** one last suspicious check — (screen: r20-13)

### Step 8 — Poked the old decoy: footer REFUNDS
**Did:** Back on the site, tapped REFUNDS in the footer — the link that fooled her last time — to see if it had learned anything.
**Got:** The same refund policy: 14 days, unworn with tags, free UK size swaps, fair and human. But the "How" is still "**email crooksldn@gmail.com or DM @crooksldn with your order number**" — postal address, no link, no mention that a returns portal exists. Zero links on the whole page.
**Expected:** After tonight's fixes, at least a "start your return here" line.
**Felt:** "So this page still doesn't know about the portal ten centimetres below it in the same footer." Less dangerous now — the correctly-labelled RETURNS sits right next to it — but anyone who taps REFUNDS first (it's the word half of Britain uses) still gets told to email a gmail address, and nothing on the page corrects them.
**Next:** done — jeans go back tomorrow — (screen: r20-14)

**Tap counts (after cookie Decline + one NOT NOW on the popup):**
- Homepage → tracking page: **2 taps** (MENU → TRACKING) — unchanged, and the page is now *usable* signed out: order-number + email lookup form. (Not submitted; destination of FIND MY ORDER unverified — see Step 4 audit note.)
- Homepage → returns centre form: **1 tap** (footer RETURNS) — was 4 clean / 7 actual in run 1. Also reachable as "Start a return instead" from the tracking page (3 taps) and from the FAQ answer (4 taps). The Aftership destination loaded and presented the order-number + email form; nothing submitted.
- Footer REFUNDS → policy page: still an email-only dead end that never names the portal.

## Outcome
**Bought / didn't:** n/a — post-purchase visit. Tracking: the signed-out lookup she begged for last time now exists; she left with the form found and both fields in hand (submission out of audit scope). Return: reached the returns centre in one tap with everything she needs.
**Total time:** ~7 minutes — roughly half of last visit, and none of it spent going in circles.
**Worst moment:** Realising the REFUNDS policy page still pretends the returns portal doesn't exist — the one survivor of last visit's runaround. Runner-up: "IDENTIFICATION REQUIRED" still shouting over a form that requires none.
**Best moment:** The tracking page asking for her order number and email — the exact two things she owns — with the FAQ's "no account needed" finally telling the truth. Close second: RETURNS sitting in the footer like it had always been there.
**Would they come back?** Yes — and for the first time that includes coming back with a *problem*, not just a basket. The money-in journey was always polished; the money-already-taken journey now mostly holds up. She'd say "looked after" tonight, with an asterisk on that refunds page.
**One thing that would have changed the outcome:** Nothing blocked her tonight — but the fix she'd insist on: make sure FIND MY ORDER actually lands on a tracking view (its destination is the same address as the Returns Center — she never got to see the other side), and let the REFUNDS page mention the portal so the last decoy is gone.
