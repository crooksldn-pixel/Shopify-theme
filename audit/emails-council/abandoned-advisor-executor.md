# The Executor

Monday morning: install Klaviyo free tier. It's the only rail that delivers a real 5-minute first touch ("Checkout Started" trigger, 5-min wait, cancel-on-order filter). Shopify Email/Flow fires when Shopify decides the checkout is abandoned — tell the owner plainly: on native rails email 1 lands 10–60 minutes out, and either accept that or use the ESP. Don't promise "5 minutes" on Flow; you can't keep it.

Discounts — create both in Shopify admin before writing a line of copy:

- **EVIDENCE-15**: 15% off order, expires 48h from send (Klaviyo can't do per-recipient Shopify expiry on shared codes — use Klaviyo's unique-code generator so expiry is real, per the no-fake-urgency law).
- **EVIDENCE-20**: 20% off, unique codes, 48h expiry.

Free socks: pick option (b). One code, socks tossed in at fulfilment — the store already ships CONTRABAND 03 keyrings this way, so ops can do it today. Two combinable codes (option a) dies at checkout; the audit already shows code-entry drops sales. Copy: "contraband slipped in the bag — no code needed."

The 3 HTML files must contain: 600px table layout, inline CSS, Courier New stack, `{{ event.extra.checkout_url }}` (Klaviyo) as the sole recovery link on a bulletproof button, line-item loop with product image/title/price, preheader text, unsubscribe footer, alt text on every image. No JS, no webfonts, one GIF max.

Escalation ladder: kill the public pattern. Unique codes, and cap email 3 at 15% + free Tracked 24 instead of 20% — otherwise you outbid The Getaway and train abandonment.

Live in one week: Klaviyo install Monday, codes Tuesday, HTML paste + test sends Wednesday–Thursday, live Friday.
