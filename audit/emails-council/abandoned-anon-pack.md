# Anonymized council responses — abandoned-checkout flow

## Response A

I left a checkout at a clothes shop I found twenty minutes ago. Then I get three emails in 24 hours. That's not a brand universe, that's a needy stranger. Email 1 at 5 minutes feels like a shop assistant following me into the car park. By email 3 I know exactly one thing about you: you email a lot.

The subject lines worry me most. "CASE FILE" or "EVIDENCE" from a sender I don't recognise reads as either phishing or an actual problem — my heart does a small jump before I realise it's about trousers. Your on-site fiction works because I walked into it; in my inbox I have no context, just an unknown sender shouting police words. Put something a normal person parses in half a second — the product I left, the shop name — and let the terminal voice live inside the email, not in the scary part.

The "browse even if you're not buying" line: I'd never do it, but weirdly it doesn't annoy me — it reads as confidence, "no pressure, the shop's open." Keep it as one dry line, not a plea. It's the only bit that feels human.

The discount ladder teaches me maths, fast. No discount, then 15%, then 20% — lesson learned: never buy from you at full price again, just abandon the cart and wait a day. And if I already grabbed the 10% game code, email 3 tells me the game was a mug's move. Once I suspect the prices are theatre, the whole "honest evidence" act collapses — that's the one thing you can't afford. One email, one honest nudge, maybe one modest sweetener. Three escalating bribes reads as desperation in a costume.

## Response B

Monday morning: install Klaviyo free tier. It's the only rail that delivers a real 5-minute first touch ("Checkout Started" trigger, 5-min wait, cancel-on-order filter). Shopify Email/Flow fires when Shopify decides the checkout is abandoned — tell the owner plainly: on native rails email 1 lands 10–60 minutes out, and either accept that or use the ESP. Don't promise "5 minutes" on Flow; you can't keep it.

Discounts — create both in Shopify admin before writing a line of copy:

- **EVIDENCE-15**: 15% off order, expires 48h from send (Klaviyo can't do per-recipient Shopify expiry on shared codes — use Klaviyo's unique-code generator so expiry is real, per the no-fake-urgency law).
- **EVIDENCE-20**: 20% off, unique codes, 48h expiry.

Free socks: pick option (b). One code, socks tossed in at fulfilment — the store already ships CONTRABAND 03 keyrings this way, so ops can do it today. Two combinable codes (option a) dies at checkout; the audit already shows code-entry drops sales. Copy: "contraband slipped in the bag — no code needed."

The 3 HTML files must contain: 600px table layout, inline CSS, Courier New stack, `{{ event.extra.checkout_url }}` (Klaviyo) as the sole recovery link on a bulletproof button, line-item loop with product image/title/price, preheader text, unsubscribe footer, alt text on every image. No JS, no webfonts, one GIF max.

Escalation ladder: kill the public pattern. Unique codes, and cap email 3 at 15% + free Tracked 24 instead of 20% — otherwise you outbid The Getaway and train abandonment.

Live in one week: Klaviyo install Monday, codes Tuesday, HTML paste + test sends Wednesday–Thursday, live Friday.

## Response C

Strip the ask down: the owner said "3 emails, 15% then 20%." But the actual problem is "recover carts without damaging the two assets that make this store work: trust, and the scarcity-of-discounts economy." Measured against that, the briefed ladder fails its own design law. A public 15→20% escalation IS a card trick — it teaches every regular that full price is for suckers who check out promptly, and it outbids The Getaway, the store's own loyalty mechanic. You cannot run a no-fake-urgency brand on a real incentive to fake abandonment.

Rebuild from the ground up. Money is the commodity; the fiction is the moat. So escalate NARRATIVE, not percentage:

- **Email 1 (the hold notice)**: no discount, correct. Concept: "ITEMS HELD IN EVIDENCE." Line-item images, exact facts (18:00 dispatch, free swaps). CTA: "RECLAIM PROPERTY." The browse-anyway line is honest in-voice: "No obligation to claim. The Register remains open for inspection."
- **Email 2**: 15% single code, socks via option (b) — fulfilment-added contraband, exactly the keyring precedent. Zero extra checkout typing; the audit says codes already drop.
- **Email 3**: NOT 20%. Same 15%, now with a real, stated expiry ("this file closes at [time]" — and it must actually close). Final beat is closure of the case, not a bigger bribe. Tell the owner plainly: 20% costs margin and trains abandonment; if they insist, make it one-time-per-customer via ESP, never a pattern.

Five-minute timing: promise it only on an ESP; on native Shopify say "first touch lands 10–60 minutes, and that's fine — the fiction doesn't need speed." One warning: fix the pre-ticked marketing box before sending anything; the flow's legality shouldn't rest on a dark pattern the audit already flagged.

## Response D

The fatal flaw is the ladder itself. A public 5min/1hr/24hr escalation to 20% is a machine that teaches your best customers to abandon on purpose — and this audience *reads mechanics for sport*. They found the fake popup clock; they will find this in a week, and it permanently reprices the store at -20%. Worse: it outbids The Getaway, so your own on-site game becomes the sucker's discount. Ruling: kill the 20% email as a discount escalation. Email 3 should be 15% max — same as email 2, later deadline — or no code at all, just a last-call restatement. If the owner insists on 20%, cap the flow to first-time checkout-startees only (Klaviyo can segment this; native Shopify cannot — another reason "3 emails, 5 minutes" is an ESP purchase, not a setting. Do not promise the owner 5 minutes on native; promise 10–60 and say why).

Free socks: option (a) two codes is dead on arrival — your own audit says code entry drops codes. Option (b) is a manual fulfilment promise that WILL be forgotten on a busy drop day, and one missing "contraband" pair torches the trust brand harder than no socks ever could. Only do (b) if there's a literal packing-slip flag; otherwise cut socks entirely. "If possible" means no.

"Browse even if not buying" in a discount email is a conversion leak — three CTAs per email is zero CTAs. One line, footer only, in-voice ("the register remains open for inspection"), never a second button.

Also: fix the pre-ticked marketing box before sending anything under PECR — the flow's legal footing is soft opt-in, and that checkbox is the audit finding that turns into a complaint.

Timing honesty extends to expiry: if email 2's code says 24 hours, it must actually die. Build the expiry first, copy second.

## Response E

Everyone will treat this as damage control. Wrong frame. These are the only three emails the brand is guaranteed to send its hottest prospects — treat them as CROOKSLDN's serialized fiction, episodes 1–3 of a case file. Email 1: "CASE FILE OPENED — items logged, not released." Hero = the actual abandoned line items rendered as evidence photos with case numbers. Email 2: "EVIDENCE TAMPERING AUTHORIZED — 15% struck from the record." Email 3: "FINAL DISPOSITION — 20%, then the file is sealed." Subject lines that read like police-log entries get forwarded and screenshotted; this flow can become organic marketing, not just recovery.

The "browse anyway" line is the buried treasure. Don't apologize for it — weaponize it: "Not buying? Review the evidence anyway. THE REGISTER is public record." Link the register, The Getaway, and REGISTER AS INFORMANT in every email. A non-buyer who plays the game and joins SMS is a bigger long-term win than one recovered cart. Measure browse-clicks, not just revenue.

Free socks: option (b), all the way — "CONTRABAND slipped into the bag, unlogged" is the single most on-brand sentence this flow can contain, and it manufactures unboxing-video moments. That's a mechanic worth extending later to loyalty tiers and drops.

Escalation ladder upside everyone's missing: if regulars learn to abandon carts, you've accidentally built an engaged list segment that opens everything you send. Cap exposure (one ladder per customer per 60 days) and you keep the upside — a trained audience for future drop announcements — without the margin bleed.

Promise the owner honestly: ESP-based, 5 minutes real. But sell the bigger prize — this is the pilot for a whole email world: drop alerts, case-file restocks, informant-only briefings. Build it as chapter one.
