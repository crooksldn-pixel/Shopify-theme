# AUDIT-CONTEXT — what an advisor needs that the build spec doesn't frame

`SPEC.md` is the build map: seventeen sections, every setting, every deliberate
decision, every known defect. **Read it; don't restate it.** `SPEC.md §9` lists
eleven behaviours that look like faults and are decisions. `audit/_ref/KEEP.md`
names what is load-bearing and must not be improved away.

This file adds only the things those two don't say.

---

## 1. The commercial reality

Thirteen active products plus an £85 two-piece set. Prices run **£6 to £60**.
Short runs that don't restock — when a size goes, it's gone, and the store
refuses to pretend otherwise.

**No reviews. No press. No retail. No physical presence.** Nowhere for a
stranger to check that this is real except the site itself.

Traffic is almost entirely **Instagram and TikTok** — which means mobile,
one-handed, often mid-scroll, often late at night, and frequently landing
**straight on a product page** rather than the homepage. The single
highest-volume visitor in this audit is persona 01: arrives cold on a product
from a story, has never heard of the brand, and decides inside ninety seconds.

So: **every sale is a stranger deciding to trust an odd-looking website with up
to £60, on a phone, in about a minute.** Every recommendation should be weighed
against that sentence.

---

## 2. The design law

Quoted from `SPEC.md §0`, because advisors keep trying to negotiate with it:

> *The fiction stops where it would cost a sale.* Flavour lives in chrome —
> never in sizes, stock, price, add-to-cart, shipping or returns. `ADD TO BAG`,
> `£60.00`, `SIZE M`, `IN STOCK` are always plain English.
>
> Radius `0`, borders `1px`, no shadows, no gradients. Enforced in CSS
> (`crooks.css:101` and `:428`), not left to discipline.

The storefront is a fictional police evidence terminal: monospace on near-black,
products numbered like exhibits, shipping written as a chain of custody. The
proposition is that **it does not look like a Shopify store.**

Every recommendation must be implementable without: a border-radius above 0, a
gradient, a shadow, a third typeface, a new accent colour, fabricated content,
or a build step.

---

## 3. Deliberately rejected — decisions, not oversights

Trust badges · reviews widgets · countdown timers · fake stock counters · "17
people are viewing" · live chat · exit-intent popups · stock photography ·
models · rounded cards.

An advisor who recommends any of these has not understood the brief. The correct
move when one seems necessary is to ask **what job it would do** and find
something inside the design law that does that job.

**This matters more than it looks, and the evidence says so.** Persona 02 — the
sceptic, the hardest trust case in the panel — concluded that having no reviews
is *actually fine*, and gave the reason:

> *"A five-star widget would be the least believable object on this page… The
> absence reads as they haven't faked anything, not as nobody has bought this —
> but only because nothing else is faked either. Add one fake-urgency line and
> the missing reviews instantly become a cover-up."*

That is a conditional, and **the condition is currently being breached**: the
first-visit overlay carries `Code expires in 20 minutes.` and a closing date.
The one mechanic that invalidates the no-reviews position is the first thing a
stranger meets. Advisors should treat that as a live finding, not a preference.

---

## 4. The tension this audit exists to resolve

**The design is doing real brand work and may be doing real conversion damage.
Both can be true.** That is the question — not "is the terminal good".

The evidence points somewhere more specific than either side of that argument,
and advisors should engage with it rather than re-litigating the aesthetic:

> **The machinery works. The information around it doesn't.**

Filters write themselves into the address bar so a shared link survives. Sizes
deep-link. The cart arithmetic never disagreed with itself once across a
three-item basket, a swap, a removal and checkout. The accessibility profile
verifies exactly as claimed — zero of 46 controls without an accessible name.
The bundle sells correctly as one £85 line naming both garments and both sizes.

And then the store makes a specific money promise and charges something else; or
answers the same question two different ways on two pages; or takes an email
address and says nothing back.

**Not one abandonment in this audit was caused by the way the site looks.** That
was also the headline finding of the previous audit round, and it held again.
The abandonments were caused by a false out-of-stock, measurements that can't be
trusted, a missing photograph, a missing gift card, and a form that never
answers.

---

## 5. The thing nobody has said out loud

**This is the fourth audit of this site.** `audit/_ref/RUN3-FINDINGS.md` closes
with a rule the round-3 council actually adopted:

> *"implement A1, and then make no further theme commits until the store owner
> flips the three CONTINUE → DENY checkboxes… more theme polish before that flip
> is misallocated effort."*

and, in its closing section:

> *"All trading data still comes from the live site — scored **14/50**, worst in
> the competitive set. Once A1 + B1–B3 land, shipping the theme is the
> highest-value act available; **three audits of measured advantage become
> receipts only in production.**"*

Theme `202053779799` was verified `role: unpublished` on the morning of this
audit. So three audits have measured this build as substantially better than
what is live, the live site scores 14/50, and it still has not shipped.

Several items on the known list have now survived three or four audits unfixed —
the cookie banner's position, the placeholder measurements, the mis-named image
masters. **Three audits produced findings that did not get implemented.** A
fourth comprehensive fault list is the least likely thing to break that pattern.

Advisors are therefore asked to answer one question the previous rounds were not
asked: **given three audits of measured advantage sitting unpublished, is any of
this worth more than shipping it this week?** If the answer is "ship it, fix two
things first", say so plainly — that is more useful than a long backlog, even
though it makes the audit look smaller.

---

## 6. Two cautions about the evidence

**Timings are felt, not measured.** No page-speed metric was collected; the
brief ruled it out and the numbers already live in `SPEC.md`. Where a journey
says something took too long, it means a shopper would have noticed and it
changed what they did next.

**Two forms could not be settled.** The restock-notify capture and the homepage
drop register both sit behind a bot check that renders blank in automated
sessions. A scripted browser failing a bot check proves nothing about a person
on a handset, so the forms are filed **untested, not broken**. What is
confirmable, and is the actual finding: when the check does not complete the
shopper gets **no message of any kind**, and the drop register gives no
confirmation on success either — so there is no way to tell "signed up" from
"silently failed". Persona 06 pressed `NOTIFY ME` four times and got two
different kinds of nothing.

---

## 7. The evidence pack

| File | What it is |
|---|---|
| `audit/features/FEATURES.md` | The feature census. What's broken, what's missing, ten groups of contradictions, what's load-bearing, the full feature table, and what's untested. |
| `audit/features/raw-*.md` | Twelve raw area notes, with the quoted on-screen strings. |
| `audit/journeys/*.md` | Twenty scripted shopper journeys with felt-experience notes at every step. |
| `audit/journeys/SUMMARY.md` | The five worst moments and everything appearing in three or more journeys. |
| `audit/QUESTIONS.md` | The four open design questions, answered from evidence. |
| `audit/screens/` | Every claim's screenshot, named by area or persona and step. |
| `audit/RUN-NOTES.md` | How the run was conducted and the judgement calls made. Machinery, not findings. |
| `SPEC.md` | The build map. `§9` is the protect list. |
| `audit/_ref/KEEP.md` | What previous rounds established must not be touched. |
