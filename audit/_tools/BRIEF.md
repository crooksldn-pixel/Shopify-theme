# Standing brief — every agent on this audit reads this first

You are auditing the CROOKSLDN Shopify staging theme **as a shopper**, not as a tester.
Working dir: `/home/user/Shopify-theme`. Read `audit/_tools/README.md` for the browser harness.

## Work efficiently

Several agents run at once and **only 3 browsers may touch the store at a time** — a disk
lock enforces it, because heavier traffic trips the store's bot protection and every page
then hangs. So:

- **Write ONE script that performs many checks in a single browser run.** Print plenty of
  `visibleText`, take your screenshots as you go, and put the most valuable checks first so
  a slow run still yields evidence. Do not launch a fresh browser per check.
- `session()` can sit for one to three minutes waiting for a slot. **That is the queue, not
  a hang.** Give your `node` runs a Bash timeout of 600000 ms and do not kill and retry.
- Always `await s.close()` in a `finally` — it releases the slot for everyone else.
- Never open a second `session()` while one is open; you would deadlock against yourself.
- If a check fails twice, record what happened and move on. A recorded "I could not get
  this to work as a shopper" is a legitimate finding, not a failure.

## The three rules that govern everything

**1. Behavioural, not technical.** Never report Lighthouse, CLS, LCP, console warnings,
bundle size, or DOM/z-index/viewport/render/breakpoint jargon. *"LCP is 3.1s"* is not a
finding. *"I stared at an empty screen long enough to wonder if the site was broken"* is.
The test for every observation: **would a shopper have noticed, and did it change what they
did next?**

**2. Trust `SPEC.md`.** It is a complete map of the build. Read §0, §3 and §9. Do not
re-derive what it states.

**3. Deliberate is not defective.** `SPEC.md §9` lists eleven behaviours that look like
faults and are decisions. Do **not** flag: sold-out sizes staying selectable, accordions
defaulting closed, the hidden CASE 001 leaderboard, the empty-search stand-down, the
unloaded cart-drawer CSS, the board's pause guards, the absence of fake urgency, the
plain-English buy controls. If you think one is genuinely wrong you may say so — but only
by describing a specific shopper journey where it cost something real.

## Already known — do not raise as new discoveries

Confirm shopper *impact* where relevant, tag it with the ref, and move on.

| Ref | Thing |
|---|---|
| D1 | Status bar `interval_ms` is seconds in schema, milliseconds in JS. Setting inert; every install runs at 8s. |
| O1 | `10CROOKS` (10% off, all combine flags true) stacks on the £85 set, taking it to £76.50. |
| O2 | Wishlist and "Only X in stock" are injected by app `bestpush-101`, not by the theme. |
| O3 | The catalogue's `Outline` toggle is pending an aesthetic decision. |
| O4 | The CASE 001 link points at the old build; the drawer's board art came from a newer copy. |
| — | Placeholder measurement numbers on several products. |
| — | Three product image masters are `.webp` served under the wrong extension. |
| — | No cookie banner. |
| — | V2 BAGGIES description says "9-16 days delivery uk"; chain of custody says UK 1–2 working days. |
| — | Three collections have no description: `frontpage`, `tracksuits`, `all`. |

## The design law — fixes must live inside it

A deliberately austere fictional police evidence terminal: radius 0, 1px borders, no
shadows, no gradients, monospace on near-black. Deliberately rejected: trust badges, reviews
widgets, countdown timers, fake stock counters, "17 people viewing", live chat, exit-intent
popups, stock photography, models, rounded cards. The proposition is that it does **not**
look like a Shopify store.

Never recommend making it look like a normal shop. Any fix you propose must be implementable
without a border-radius above 0, a gradient, a shadow, a third typeface, a new accent
colour, fabricated content, or a build step.

## Hard limits

No order placed. No card details. No real personal data — use `buyer+test@example.com` and
obvious test values. Do not modify any store setting, product or discount. Checkout may be
walked **to the payment step and abandoned**, never submitted.

## Evidence

Screenshot anything you assert: `shot(page, '<areakey>-<step>')`. A finding with no
screenshot is not a finding. **Quote the exact on-screen wording** of any message a shopper
is shown — never paraphrase it.

## Output

Write `audit/features/raw-<AREAKEY>.md`, one entry per feature:

```
### <feature name>
**Should:** ...
**Did:** ...
**Verdict:** works | partly | broken | absent
**Shopper cost:** ... (omit if none)
**Evidence:** audit/screens/<file>.png — plus the exact strings you saw.
```

Finish the file with four short lists: `## Surprises` (things the owner probably does not
know), `## Missing` (expected as a shopper, could not find), `## Contradictions` (the site
tells a shopper two different things — quote both sides), `## Works and must be protected`.

Then reply with a compact summary: the headline, the broken items, and those four lists.
Be concrete. A sentence that could be pasted into a review of any random Shopify store is
worthless here.
