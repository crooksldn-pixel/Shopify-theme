# Knowledge base

Every `.md` file in this directory is loaded into the system prompt at startup, in filename
order, and reloaded by `POST /reload-kb` without a restart. Total budget is 40,000 characters.

`terminology.md` is different: it also feeds the speech normaliser, so it is a term list, not
prose.

What belongs here (the M10 content dependency):

- `returns-policy.md` — the actual policy, in the words you would say to a customer
- `shipping-policy.md` — carriers, timings, costs, what happens when something is late
- `sizing.md` — the size chart and garment measurements
- `cs-rules.md` — how customer service decisions get made, and where the discretion is

Write them as answers, not as internal notes. The assistant reads these aloud.
