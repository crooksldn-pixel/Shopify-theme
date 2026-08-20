# CROOKSLDN: The Getaway — Base44 revision prompt (popup edition)

Written 2026-08-19 from the behavioural audit evidence + owner decisions:
reward fixed at 10%; mobile-first; popup game only; SMS-only optional capture
after the code is shown; unique per-win Shopify codes minted server-side.
Paste the block below into the duplicated Base44 app's chat.

---

This app is being renamed and reworked. It is now CROOKSLDN: The Getaway (popup edition) —
the mini-game that appears in a popup on crooksldn.com, an evidence-terminal-themed London
streetwear store. The tumbler game itself is proven and fun — KEEP its core feel (three
tumblers, tap to stop each one). Everything wrapped around the game changes. Twenty scripted
shopper tests found the current flow takes a phone number, SMS consent and an email and then
pays out nothing; this rework inverts that: PAY THE WIN INSTANTLY, make capture optional.

== CONTEXT AND HARD RULES ==
Mobile-first: design at 360–390px wide inside a bottom-sheet popup; everything must also fit
a 390px-TALL landscape viewport (the current build clips the tumblers below the fold there —
never again: game area compresses, nothing scrolls out of reach) and a desktop overlay.
Design law of the parent site, non-negotiable: border-radius 0 on everything; 1px borders;
no box-shadows; no gradients; near-black ground #0B0A0E; off-white ink #EDEBF2; accent
purple range — deep #6E4E93 for fills/washes, mid #A77AC7 for interactive/focus, bright
#C9A6E8 for hover. Fonts (Google Fonts): VT323 for display/fiction lines, Space Mono for
everything else including all numbers and codes (tabular feel, generous tracking on labels).
Type contrast: display moments (the code reveal) at 64–96px VT323 against 14px Space Mono
labels — reach contrast by going bigger, never by shrinking labels below 14px.
The fiction lives in chrome only. Anything transactional — the 10% figure, the code string,
the expiry, the consent line — is plain English, always.
DO NOT USE: rounded corners of any radius; shadcn Card look; pill buttons; gradient fills;
confetti or particle win effects; backdrop-blur; Inter or any default sans; emoji; fade-in-up
entrances; auto-playing loops. Buttons are flat rectangles, 1px border, 48px min height,
full-width on mobile. Texture: keep the existing pixel-tile/scanline surface treatment from
the current build as a thin pass (≤4% opacity over dark ground, never over the code string).

== THE FOUR SCREENS ==

1) THE OFFER (replaces the current cold open)
Stakes stated before anyone plays — this is the whole fix. Layout: sparse, one idea.
  VT323 display: "CRACK THE CUFFS."
  Space Mono: "10% off your first order if you do. Three tumblers. Tap each one at the
  right moment."
  Small print, plain: "One code per player. Attempts unlimited. Code expires with the
  current drop."
  Buttons: [RUN IT] (primary) and [NOT NOW] (ghost — closes the popup via
  postMessage "getaway:close" to the parent page).
On desktop the instruction line reads "Click each one" — detect coarse/fine pointer, never
show "Tap" to a mouse. No countdown, no "only today", no fake pressure anywhere on this
screen.

2) THE GAME (keep, with fixes)
Keep the three tap-to-stop tumblers exactly as they play now. Changes:
  - Unlimited attempts. Remove every trace of "one attempt per customer".
  - Remove the blinking idle beacon.
  - prefers-reduced-motion: THIS IS REQUIRED. Under PRM the tumblers advance in discrete
    steps with no spin/strobe, there is no draining timer bar, and the round is untimed —
    the accessibility override beats the mechanic. Currently the app ignores PRM entirely;
    a vestibular-disorder tester had to close it in self-defence.
  - All controls are real <button>s with visible focus (2px #A77AC7 outline, 2px offset,
    never removed); result announced via an aria-live="polite" region.

3) THE WIN — the signature moment
The code appears IMMEDIATELY on winning. No form stands between the win and the code. Ever.
Ceremony (the one theatrical move — everything else stays quiet): the cuffs spring open and
an evidence tag stamps down carrying the code — tag rendered as a bordered rectangle,
radius 0, stamped with a slight rotation between -3° and +3° derived from the code string's
hash so each win lands differently. Under PRM the tag simply appears, no stamp travel.
  On the tag, plain English, Space Mono:
    "EVIDENCE Nº [CODE]"
    "10% off. One use. Expires with the current drop."
  [COPY CODE] button — on tap the label becomes "COPIED" for 2s (state change on the
  button itself, no toast).
BELOW the code, clearly optional, never blocking:
    "Want it kept on file? Phone number goes in the evidence log — one message per drop,
    nothing else. Same promise as the register."
    UK phone field (07… format) + [FILE IT] + a plain "No need — I've got it" dismiss link.
    Affirmative SMS-consent line adjacent to the button in plain English. No email field.
    No birthday field. These are deleted from the app entirely.
Filing the number must never be required to see, copy, or use the code.

4) THE MISS
  VT323: "CUFFS HOLD."
  Space Mono: "Run it again — attempts are unlimited."
  [RUN IT AGAIN] primary. One quiet line beneath: "Or skip the game — join the register on
  the site for first word of every drop." (link closes popup and anchors to the homepage
  register section).
No consolation-prize fakery, no "so close!" — a miss is a miss, the retry is free.

== THE CODE ITSELF (backend — the part that was broken) ==
Mint a UNIQUE one-time Shopify discount code per win via a Base44 backend function calling
the Shopify Admin GraphQL API (discountCodeBasicCreate; the store's Admin token lives in a
Base44 secret, never in client code):
  - Format GTWY-XXXX (4 random unambiguous chars — no 0/O/1/I).
  - 10% off the order, once per customer, single-use, no combining with order discounts.
  - End date read from one app setting: DROP_END_DATE (owner-editable) — this is what
    "expires with the current drop" means; the popup prints the real date next to it in
    small print: "(this drop closes DD.MM)".
  - One code per player enforced honestly: persist a won flag + the code locally and
    return the SAME code on revisit rather than minting again; say so on screen:
    "You've already got one on file: GTWY-XXXX."
Failure state (must be designed — the old app failed silently here, which is the single
worst thing it did): if minting fails, say so plainly — "The printer's jammed. Your win is
saved — reopen this and we'll cut the code again." — persist the win locally, retry on next
open, never show a fake or hardcoded code, never fail silently.
Log per event: plays, wins, codes minted (code string = redemption tracking in Shopify).

== STATES CHECKLIST (all must exist) ==
Loading (the old build sat as an empty black box for 4–8s: show the offer screen's text
instantly from first paint — words before any asset); win-with-code; win-code-pending
(minting: button reads "CUTTING THE CODE…", disabled, max 5s before failure state);
mint-failure (above); already-won revisit; SMS field error (bad number — "That number
doesn't look right. 07… format."); SMS filed confirmation ("On file. One message per
drop."); PRM variants of offer/game/win; landscape-390px-height layout for every screen;
desktop pointer copy variant.

== COPY BANS ==
Never: "unlock", "exclusive", "hurry", "don't miss out", "last chance", any countdown to
claim, any fake scarcity ("3 people playing"). The parent brand's entire trust position is
that it never fakes urgency — this popup is part of that brand.

---

## Owner checklist outside the prompt
1. Shopify Admin API token with write_discounts scope → Base44 secret.
2. Set DROP_END_DATE per drop (drives real expiry + on-screen date).
3. Minted codes are non-combining → retires the O1 stacking question for game codes.
4. Embed-side fixes (focus trap, Escape, cookie-banner collision, trigger timing) live in
   the theme's popup snippet, not this app — separate small theme task.
