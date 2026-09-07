# Knowledge base

Every `.md` file in this directory is loaded into the system prompt at startup, in filename
order, and reloaded by `POST /reload-kb` without a restart. Total budget is 40,000 characters.

`terminology.md` is different: it also feeds the speech normaliser, so it is a term list, not
prose.

What is here (the M10 content dependency), and where it came from:

- `returns-policy.md` — from the Refund Policy published on crooksldn.com
- `shipping-policy.md` — from the published Shipping policy
- `sizing.md` — from the `crooks.measurements` / fabric / cut / care metafields on each product
- `cs-rules.md` — from the published Contact page, plus a **discretion section for the owner**
- `terminology.md` — the live catalogue with spoken aliases; also feeds the speech normaliser

All were read from the store on 7 Sept 2026. They are snapshots: if a policy page or a
product's measurements change, change the file (or delete it and let the live tools answer).
This README is not loaded into the prompt. Write everything else as answers, not as internal
notes — the assistant reads these aloud.
