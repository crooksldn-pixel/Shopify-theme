# 12 — The searcher, "I don't do menus — I search"
**Device:** mobile (390x844) · **Goal:** find the returns policy using search only — test "returns", "delivery", "size", "refund" · **Mood:** impatient, allergic to burger menus

### Step 1 — Landed on the homepage, cleared the furniture
**Did:** Opened the site. Cookie banner covering the bottom half; tapped Decline. Went straight for the magnifier in the header.
**Got:** My tap on the search icon didn't work — a full-screen popup ("CROOKSLDN: THE GETAWAY — Crack the cuffs. 10% off your first order — code sent by text. Attempts unlimited.") had slid in at that exact moment and swallowed the tap. Tapped NOT NOW and it went away cleanly. (Screens r12-01, r12-02, r12-03.)
**Expected:** To be typing within five seconds of arriving.
**Felt:** "Every site does this now. But it literally ate my tap on the search button — that's the worst possible timing. At least NOT NOW actually means not now."
**Next:** Tap the magnifier again.

### Step 2 — The search page itself
**Did:** Tapped SEARCH in the header (goes to /search).
**Got:** A proper search page, cursor already blinking in the box, placeholder "Item, category or question" — and underneath, before I've typed a thing: DIRECT LINKS — START A RETURN → Returns Centre, TRACK YOUR ORDER → Tracking, QUESTIONS → FAQ, then category shortcuts. (Screen r12-04.)
**Expected:** An empty box and nothing else.
**Felt:** "Hold on — the thing I came for is already on the screen. 'Question' is in the placeholder, so someone has anticipated people like me."
**Next:** Type the queries anyway — that's what I'm here to test.

### Step 3 — Query 1: "returns"
**Did:** Typed "returns". Watched the typeahead, then pressed enter, then tapped the suggestion.
**Got:** Typeahead: a PAGES panel with one row — "START A RETURN — RETURNS CENTRE" (r12-05). Results page: zero products, and instead of a dumb "no results" it said "NO PRODUCTS MATCH THAT. IF YOU WERE AFTER AN ANSWER RATHER THAN A PIECE, THE LINKS ABOVE HAVE IT" — with the returns link re-ordered to the top of the direct links (r12-06). Tapped the suggestion: it opened a NEW TAB onto an external Aftership "Returns Center" — order number + email, verify by postal code or phone, and a "View return policy" link. A reCAPTCHA badge sits bottom-right; I did not touch the form (r12-13).
**Expected:** Product noise or a dead end; got a route in one tap.
**Felt:** "1 tap from query to the returns centre. Two small gripes: it jumped me to a different-looking external site in a new tab with no warning — for a second I thought I'd been hijacked, the whole vibe changes from prison-terminal to generic white app — and it's the DO-a-return machine, not the policy. I wanted the terms first. Also the suggestion row and the static direct link stack up as near-identical twins on this page, which made me look twice."
**Next:** Try "delivery".

### Step 4 — Query 2: "delivery"
**Did:** Typed "delivery"; read the typeahead; submitted; tapped the policy suggestion.
**Got:** Typeahead: PAGES → "SHIPPING POLICY", plus two products (Black Convict Joggers, Charcoal Cellblock Shorts) whose blurbs evidently mention delivery (r12-07). Results page: same shape — policy link on top, 2 products below (r12-08). One tap on SHIPPING POLICY → a genuinely complete answer: free UK over £30, standard £3, Tracked 24 £4.99, free Tracked 24 over £80, order by 18:00 Mon–Sat for same-day dispatch, UK 1–2 working days, international 7–14, customs caveat, lost/damaged procedure (r12-14).
**Expected:** A vague "shipping calculated at checkout" page.
**Felt:** "1 tap, full answer, real numbers. This is what search should do."
**Next:** "size".

### Step 5 — Query 3: "size"
**Did:** Typed "size"; submitted; tapped the "SIZE GUIDE — SIZING" suggestion.
**Got:** Typeahead: PAGES → "SIZE GUIDE", plus six products (r12-09). Results page: SIZE GUIDE link on top, 10 products under it with availability lines like "2 OF 5 SIZES LEFT" (r12-10). The SIZE GUIDE link goes to /pages/faq — and dumps me at the TOP of the FAQ, in the DELIVERY section, not at sizing (r12-15). Scrolled to SIZING, tapped "HOW DO I KNOW WHAT SIZE TO BUY?" — answer: measured pieces carry a measurements table on the product page ("tap SIZE GUIDE next to the size buttons"), garment measurements, cm/inch switch (r12-17, r12-18).
**Expected:** A size chart.
**Felt:** "2 taps plus a scroll, and the thing labelled SIZE GUIDE is actually an FAQ that tells me the real size guide lives on each product page. Not a dead end — I got my answer — but the label over-promises and the link can't even be bothered to scroll me to the sizing section."
**Next:** Last one: "refund".

### Step 6 — Query 4: "refund"
**Did:** Typed "refund"; submitted; tapped "REFUND POLICY".
**Got:** Typeahead: two page rows — START A RETURN and REFUND POLICY (r12-11). Results page: zero products, the same honest empty-state line, REFUND POLICY link on top (r12-12). One tap → /policies/refund-policy: 14 days from delivery, unworn with tags, return postage on me, free UK size swap with outbound postage covered, faulty items covered both ways, refunds in 5–7 days, return address in Bourne End, final-sale exclusions (r12-16).
**Expected:** Another portal bounce.
**Felt:** "There it is — the actual policy I wanted when I typed 'returns' four minutes ago. 1 tap. Funny that 'refund' finds the policy but 'returns' only finds the portal — those two typeaheads should be twins."
**Next:** Done — I have everything I came for.

## Outcome
**Bought / didn't:** Didn't buy — wasn't shopping; I came for answers and got all four.
**Total time:** ~7 minutes, most of it reading the (good) policy pages, not hunting.
**Worst moment:** The Getaway popup materialising exactly as I tapped the search icon and eating the tap; runner-up, "returns" quietly throwing me into an external Aftership tab that looks nothing like the site, with the policy itself one query further away.
**Best moment:** The empty-state on the results page — "IF YOU WERE AFTER AN ANSWER RATHER THAN A PIECE, THE LINKS ABOVE HAVE IT" — written for exactly me; and the /search page pre-loading returns/tracking/FAQ links before I typed a character.
**Would they come back?** Yes — as a shop this passed my personal test: I never had to open a menu.
**One thing that would have changed the outcome:** Nothing changed my outcome — all four queries landed. To make it flawless: have "returns" also suggest the refund/returns POLICY (not just the portal), and make SIZE GUIDE anchor to the FAQ's sizing section instead of the top of the page.

### Tap counts (from typed query to answer on screen)
- "returns" → 1 tap (typeahead) → external Aftership Returns Centre, new tab. Policy wording itself: not offered for this query — reached via "refund" or the portal's "View return policy" link (+1 tap).
- "delivery" → 1 tap → /policies/shipping-policy. Complete answer.
- "size" → 2 taps + a scroll (typeahead → FAQ top → sizing accordion). Answer reached; link mislabelled and unanchored.
- "refund" → 1 tap → /policies/refund-policy. Complete answer — this is the returns policy.
- Zero dead ends in four queries; typeahead surfaced a non-product "PAGES" row for every single query.
