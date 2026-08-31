# Framed question — CROOKSLDN 3-part abandoned-checkout email flow

The owner of CROOKSLDN (London streetwear; police-evidence-terminal storefront)
wants a 3-part abandoned-checkout email sequence, then 3 production HTML files:

- **Email 1, ~5 minutes after abandonment**: plain reminder, NO discount.
- **Email 2, ~1 hour**: 15% off + free socks "if possible".
- **Email 3, ~24 hours**: 20% off.

Owner asks: they must "look cool", speak the CROOKSLDN world, and each should
also invite the reader to "browse the website even if you're not interested in
purchasing". The council decides imagery, copy angles, subject lines, CTAs,
discount mechanics, and flags anything unwise — BEFORE the HTML is built.

## The world (voice + design law — binding)
Police-evidence/terminal fiction: catalogue = THE REGISTER (cards numbered
"NO. 04 DENIM"), shipping accordion = CHAIN OF CUSTODY, packaging = evidence
bag ("sealed, tagged and numbered"), SMS list = REGISTER AS INFORMANT, popup
game = The Getaway (pays a real 10% code). Deadpan procedural voice; exact
numbers are the brand's substitute for social proof. DESIGN LAW from the spec:
no fake urgency, no fabricated claims, no rounded corners, fiction stops where
it would cost a sale. Palette: near-black #0C0B10, purple #9B6FC4, off-white
#E8E5EF; terminal monospace type. 40+ audited shopper journeys confirm: this
audience rewards honesty and walks on any whiff of a card trick (a silently
dropped discount nearly lost two sales; a fake "20 minutes" popup clock was
called out as a bluff by two personas).

## Store facts usable in copy (verified)
Free UK Tracked 48 over £30; free Tracked 24 over £80; sub-£30 postage
£3–£4.99. Order before 18:00 London = same-day dispatch. Free UK size swaps;
14-day returns. Prices £6 (socks) to £85 (sets, save £10). IG @crooksldn.
The Getaway popup already hands out 10% codes (GTWY-XXXX) on-site.

## Platform facts (constrain the mechanics — do not wish these away)
1. Shopify's NATIVE abandoned-checkout notification is ONE email. A 3-part
   sequence requires Shopify Email automations (Flow) or an ESP
   (Klaviyo/Omnisend). A literal 5-minute first touch is only reliable on an
   ESP ("checkout started" + 5-min wait + cancel-on-order); native Shopify
   declares abandonment on its own schedule (first email realistically
   10–60 min). The plan must say what to promise the owner honestly.
2. One Shopify discount code = one discount type. A 15% order code CANNOT also
   grant a free product. Free socks options:
   (a) TWO codes (15% basic + BxGy "1pc socks 100% off", combinable) — extra
       typing friction, and the audit shows checkout code-entry already
       drops codes;
   (b) ONE 15% code + socks added at fulfilment when the code was used
       (manual promise, in-world "contraband slipped in the bag"; the store
       already ships a keyring this way: "CONTRABAND 03 ships with selected
       sweat bottoms only");
   (c) drop socks from email 2 (15% only), or make socks the whole email-2
       hook (BxGy only) and keep % for email 3.
3. Email HTML reality: tables + inline CSS, 600px, no webfonts in most
   clients (Courier New monospace fallback IS the terminal look), no JS,
   bulletproof buttons, dark-mode quirks, alt text, preheader, unsubscribe.
   Imagery = static: abandoned line-item images via Liquid, or brand
   graphics. No animation beyond maybe one GIF.
4. Escalation risk: a public 15%→20% ladder trains regulars to abandon carts
   on purpose. The Getaway already pays 10% to anyone who plays — a 24h 20%
   abandon code outbids the store's own game. Codes must genuinely expire if
   the email says so (no-fake-urgency law).
5. UK PECR: cart-recovery to checkout-startees rides on soft opt-in; include
   unsubscribe. (Separately: the audit flagged the checkout's pre-ticked
   marketing box — worth one line to the owner.)

## What the council must return
Per email: concept, subject line + preheader, hero/imagery approach, body
copy angle (with the "browse anyway" line solved in-voice), CTA label, and
discount mechanics (incl. the free-socks call and expiry honesty). Plus:
the escalation-ladder ruling, what to promise about the 5-minute timing, and
anything the owner should be warned about. What's at stake: the store's
first-ever email automation, its trust-first brand, and real margin.
