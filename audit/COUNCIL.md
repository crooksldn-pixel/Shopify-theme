# COUNCIL — five advisors, five peer reviews, one verdict

Five advisors received the same evidence pack independently: the feature census,
twenty shopper journeys, the four answered questions and the context file. Their
memos were anonymised as A–E and each advisor reviewed all five without knowing
who wrote what. This is the synthesis, weighted by peer standing.

**Peer standing.** The Executor (C) was named strongest by three reviewers, the
Contrarian (E) by two. Both remaining reviewers who preferred E called C the
better *plan* and E the better *judgement*. The Outsider (B) drew three
blind-spot votes and the Expansionist (A) two.

**One correction to that scoring before it is used.** B was marked down for
"never answering the question — no verdict, no highest-value change." That is
true and it is my fault, not B's: the Outsider was deliberately given a
different brief (read three journeys cold, report what the shop looks like from
outside) and was never asked for a verdict. Its standing should be read as
*out of scope*, not *weak*. Its actual content survived every check.

---

## Where the council agrees

**1. The aesthetic is not the problem, and four advisors say so unprompted.**
Not one of the eight abandonments was caused by how the site looks. E puts the
mechanism best: *"austerity is the mobile strategy here, not a style that
survives it."* Journey 14 read the entire catalogue — names, prices, stock — at
three seconds on one bar of signal, before a single photograph existed. B, cold
and with no context, returned the verdict **"a real shop being deliberately
odd"**, and named exactly why: *"the design stops at the wallet."*

**2. The measurements are the costliest fault on the site.** Four of five put
them at or near the top; three reviewers independently marked the two memos that
omitted them (A and B) as the weakest for that reason. Five journeys caught the
fabricated table; two abandoned on it outright.

**3. Four protections, named repeatedly and independently:** the plain-English
money spine, the quiet add-to-bag line with no cart drawer, price-and-stock
inside every register link, and `Decline` sized like `Accept`. Every advisor
listed at least three of the four unprompted.

**4. Ship this week.** A, C and D say it outright.

---

## Where the council clashes

**The single highest-value change — three different answers, and they are not
reconcilable.**

- **D: publish the theme.** *"The audit has become the work."*
- **E and C: real measurements.** The only fault that makes a shopper order
  the wrong size *by obeying the site*, and it needs a tape measure rather than
  a developer, so it never blocks a deployment.
- **A: wire `ON MODEL` to the model photographs that already exist.**

**Two reviewers killed A's version on the evidence:** the second photographs
reach only 4 of 12 cards and just one shows a human, while seven of twelve
products have exactly one image. A's "no new asset, no build step" claim is
false for most of the catalogue. A's *idea* is right and its scope was
overstated.

**Is "ship vs fix" even a real choice?** E alone refused the frame — *"ship-vs-fix
is a false choice, and that framing killed three rounds"* — arguing both top
fixes live outside theme code. E is half right, and the half it got wrong
matters; see the corrections below.

**Is the no-reviews position "conditionally fine" or already broken?** The
audit's own answer (Q4) said conditionally fine, with the countdown as the
breach. **E overturned it**, and two reviewers called this the sharpest single
insight in the set: `SPEC.md §0` says the fiction stops where it would cost a
sale and sizes are *never* in-fiction — so an invented 34-inch waist is
fabricated content **inside the protected zone**. *"`Code expires in 20 minutes`
is chrome; an invented 34in waist is the shop lying with a number."* On that
reading the condition is already broken, and no photograph fixes it.

**I side with E here, and it revises Q4.** The countdown remains a real breach
and should still go — but it is the second one, not the first.

---

## Blind spots the council caught

**1. Every single advisor missed journey 20.** Four of five reviewers caught it.
A customer who has already paid £60 can neither track his order nor start a
return, having been told twice in writing that he could. This is fatal to D's
own thesis: if the asset is the audience that comes back for the next drop, then
the site's only interaction with a *paying* customer is a refusal. For a
no-restock drop label, post-purchase **is** the retention engine, and nobody
costed it.

**2. Nobody named the consent banner.** Three reviewers caught it. Seven
journeys, lands on the price and the buy bar of every phone arrival, takes the
tap meant for `PLAY CASE:001 NOW`, and clips `Decline` off the screen at 200%.
It is an admin setting, not code, and it is the first object every Instagram
visitor meets.

**3. Journey 14's buy button is A1.** One reviewer made the connection nobody
else did: the enabled `ADD TO BAG` that flips to a disabled `SELECT A SIZE` in
the same position is the layout-shift defect run 3 called the only
BLOCKS-class theme fault, and run 2 had already prescribed the fix for. **One of
this run's eight abandonments is a fix written down twice and never made.**

**4. The consensus was partly dictated, not earned.** One reviewer checked the
brief and found that `AUDIT-CONTEXT.md §5` had literally invited the answer:
*"If the answer is 'ship it, fix two things first', say so plainly."* Three
advisors returned that sentence. **That framing was mine, and the reviewer is
right to flag it.** What rescues the conclusion is that it was reached
independently by the round-3 council months earlier, and E — the one advisor who
refused the frame — still ended at "publish the same day."

**5. Publishing is not the audit's to command.** `SPEC.md §0`: *"No `shopify
theme publish`. Publishing is the owner's command."* Four advisors made
publishing their headline action without noting that. It is a recommendation to
the owner, not a task on a list.

**6. The 39/50 score is stale.** `RUN3-FINDINGS.md` records it as measured
before the header regression, with an explicit instruction to re-score after A1
lands. D quoted it as current.

---

## Three claims the chairman checked and corrected

The council's specifics were verified against the deployed theme rather than
taken on trust. Three did not survive.

**1. The overlay is theme code, not an app toggle.** E wrote *"the countdown is
an app embed — a dashboard toggle… neither change is a theme commit."* It is
`snippets/crack-the-cuffs.liquid`, rendered from `layout/theme.liquid`,
homepage-gated. Removing it *is* a theme commit — a five-minute one. Three
reviewers caught this; E's closing argument rests on it, and the argument
survives without it, because the measurement strings genuinely are store data.

**2. The overlay does *not* breach the design law — and the way that error
happened is a warning.** C wrote that the file carries `border-radius: 8px`,
`999px` and a `box-shadow`, *"the only design-law breach on the site."* Two
reviewers independently confirmed it. **All three read the wrong file.** This
repository's working tree sits on a month-old branch that contains a *different*
157-line `crack-the-cuffs.liquid` with four radius and shadow declarations; the
deployed 293-line version has **none**. Round 2 brought that popup into
compliance and it has stayed there. The rounded corners shoppers saw are inside
the cross-origin game iframe, which the theme cannot style. Anyone acting on
this audit must read theme code with `git show` against the theme branch — a fix
applied to the working tree would edit a file that is not deployed.

**3. The no-JavaScript fallback works.** One census pass reported that a shopper
without JavaScript cannot select a size, dead-ending on `Cart Error: Cannot find
variant`. That pass blocked script *files* while leaving JavaScript enabled —
which means `<noscript>` never renders, so it tested a condition no shopper is
ever in. Fetching the page as a no-JS browser receives it: **three `<noscript>`
blocks, five variant links labelled `XS S M L XL`**, and following the M link
returns HTML with the variant id already server-rendered into the buy form.
`SPEC.md §9.11` and `KEEP.md §5` hold. **Do not "fix" this.**

---

## The recommendation

**Publish this week — but flip the three `CONTINUE → DENY` checkboxes first, and
start the tape measure in parallel.**

The ship case is real and it is not new: three audits have now measured this
build as substantially better than a live site scoring 14/50, and that advantage
has earned nothing because it is not in production. D's line stands — *"a fourth
fault list makes the gap wider on paper and narrower in reality."*

But D also names the one thing that gets **worse** the moment you publish, and
it is the only genuine gate in the set: variants set to keep selling at 8–9
units under live trade. A better theme sells more of them. Ship into that and
you are funding refunds. It is a checkbox, not a project.

**The measurements do not block the ship and must not be allowed to.** They need
a tape measure and thirteen garments, not a developer. E's interim move is the
best single idea the council produced and it costs nothing: **until a garment is
measured, delete its table and print what the FAQ already promises** — *we will
measure any garment for you, reply in 1–2 working days.* That converts the
audit's worst fault into the exact quality five journeys rated highest in this
shop: volunteering bad news before being asked.

**What must not change** is now evidenced rather than asserted, and is listed in
`KEEP-ADDITIONS.md`. The short version: the plain-English money spine, the quiet
add-to-bag line, the absence of a cart drawer, price-and-stock inside every
register link, `Decline` at full size, the drawer's focus trap, the £45 that is
£45 in three places, and the absence of reviews.

**On the aesthetic, the verdict is settled and should stop being re-litigated.**
Twenty strangers, eight abandonments, none of them caused by how the site looks;
six of the eight would come back. The coldest visitor in the panel gave the
condition under which that holds — *"only because the money words are plain"* —
and that condition is currently being met everywhere except the size table.

---

## The one thing to do first

**Flip the three `CONTINUE → DENY` checkboxes in Shopify admin.**

It takes minutes, needs no developer, and it is the only item on any list that
gets more expensive the moment the better theme goes live. Three audits have
said publishing is the highest-value act available; this is the one thing
standing between that decision and a stack of oversell refunds.

Then publish, and put a tape measure on thirteen garments while the site is
already earning.
