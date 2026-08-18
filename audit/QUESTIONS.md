# QUESTIONS.md — the four live questions, answered from evidence

Sources: `features/FEATURES.md` + eight raw area reports, twenty journeys
(`journeys/`), `journeys/SUMMARY.md`. References like (11) are persona numbers.

---

## Q1 — The board's move to the drawer: net gain or loss?

**Does anyone find it?** Menu-openers do, reliably — the animated board peeks
into the first drawer view and the header-drawer agent found discovery "fair"
for that group. Nobody else ever meets it: no persona who skipped the MENU
encountered the board anywhere, and the only other route to the game is a
plain same-tab footer link that strands the shopper off-site.

**Does the homepage still have anything memorable?** Barely, and not by
design. The two sections that should carry weight after the board's departure
are both dead: the informant intake renders a headline over an empty box (its
Forms block never mounts) and the lookbook renders 0px. What actually landed
with shoppers was the **packaging section** — persona 9's best moment
("accidental built-in gift wrapping"), the homepage agent's best block. On
desktop the hero uses half the width (19). The homepage is currently a
competent register with one good section and two broken ones.

**The unplanned complication:** the board didn't just move — its attract-mode
job got taken over by the **Crack the Cuffs popup**, which does the same job
uninvited and is the most-complained-about object in the audit (12 of 20
journeys; see SUMMARY). The board was an honest, pausable, zero-CLS invitation;
the popup is a modal toll-booth. The brand traded its politest asset for its
rudest.

**Verdict: a small loss as executed, not because the drawer is the wrong home
but because nothing honest replaced the board's job on the homepage.** The
drawer placement itself works (lazy-injected, animates, PLAY opens a new tab).
What the evidence supports: fix the two dead homepage sections; make the
footer game link open in a new tab like the drawer's; and let the popup's
duties be re-examined under Q4/council — the homepage does not need the board
back, it needs its remaining sections to work.

---

## Q2 — The carriage bar's position: does it earn 0.26 viewports?

**The premise has expired.** The bar is now cart-gated: with an empty bag it
renders literally nothing, and the first catalogue card sits at **0.90
viewports** — better than the 1.22 the round-2 council started from. The
0.26-viewport complaint no longer reproduces. Once the bag has items it costs
160px and shows real arithmetic ("£14.00 to free Tracked 48" → "£4.00 to free
Tracked 24" → "Free Tracked 24 — unlocked"), exact at every stage (08).

**Does anyone spend more because of it?** No persona increased their basket
because of the bar. The £6 impulse buyer (07) is the designed case and it
failed him honestly: every sock-sized top-up still misses £20 and the cart's
suggestions start at £45 — "the bar never stood a chance." The £10-saving line
it feeds into the set panel ("FREE UK TRACKED 24 INCLUDED") did help sell the
£85 set (04, 19), which is the closest it comes to earning revenue.

**Where it actively hurts:** the PDP copy goes stale on AJAX adds — it read
"£45.00 to free Tracked 24" seconds after the add that crossed £70, twice
(08). Wrong exactly at the unlock moment it exists to celebrate. And the £20
tier is only ever a tick, never words (08).

**Verdict: position earned, implementation owes.** Keep the bar and its
empty-cart stand-down (protect-list material — it's what defused the original
objection). Fix the stale-on-PDP-add bug. Accept that its upsell power is
near-zero for small baskets and real only via the set panel; if the owner
wants the £6→£20 top-up to work, that's a catalogue problem (nothing sellable
between £6 and £15), not a bar problem.

---

## Q3 — The Outline toggle (O3): control or clutter?

Persona 11 (the tinkerer — the most sympathetic possible user) delivered the
cleanest verdict in the audit: **"keep the TREATMENT, retire the TOGGLE."**

The evidence against the control: in light mode the treatment is suppressed
but the button stays live — a press visibly toggles the chip, changes nothing
on screen, and silently flips the state that dark mode will show later (11:
"dead control"; the toggles agent found the same). The label communicates
nothing before pressing (10 read it as a photo-view option next to
FLAT / ON MODEL and was confused). It exists only on the homepage register
while its sessionStorage state silently governs collection and search
registers that offer no control to change it (register agent). No persona
ever wanted the off-state; the outline halos are part of the evidence-sticker
look and read as the default identity of the catalogue.

**Verdict: the outline treatment earns its place; the toggle does not.**
Default the treatment on in dark mode, drop the button (or gate it behind the
dormant board-test/dev context). This removes a dead control from light mode,
an inconsistency across registers, and one item of cognitive load beside the
view toggle that actually matters — at zero cost to the look. Implementable
inside the design law (it deletes UI rather than adding any).

---

## Q4 — Trust with no reviews at all: fatal, survivable, or consistent?

**Survivable — proven, not assumed.** The two personas built to fail on this
(02 the sceptic, 05 the set sceptic) both bought. 02 spent 25 minutes vetting
and concluded the specific, self-consistent policies plus protected payment
rails (PayPal/Shop Pay/Google Pay + Pay-in-3) outweighed the silence where
reviews should be. 05 came to catch a fake bundle and "instead verified a
real one — the numbers all check out from every angle, which almost never
happens." The cold click (01) found the brand credible in 90 throttled
seconds. Nobody asked "where are the reviews?" and left.

**What actually earns the trust (strongest first):**
1. **Specific, checkable numbers everywhere money is discussed** — £3.00 /
   £4.99 / free over £20 / £70, same-day before 18:00, UK 1–2 days, a real
   Buckinghamshire returns address, a computed dispatch line that was correct
   at 22:00 on a Tuesday. 02: "someone who has actually posted a parcel wrote
   this."
2. **The refusal to fake anything** — real "3 LEFT" counts, honest red
   sold-out states, no timers, no "17 people viewing". The sceptics cite the
   absence of tricks as the reason they stayed.
3. **The measurement apparatus** (where it exists) — it closed sales 03 and 11
   on its own.
4. Express payment rails as the risk-remover of last resort (02 would only
   ever pay via PayPal — the trust cost of no reviews is *rail choice*, not
   abandonment).

**What spends that trust budget (weakest first):**
1. **Self-contradiction** — the audit's most repeated worst moment:
   "9-16 days delivery uk" against "UK 1–2 working days" (02, 03, 10), the
   AfterShip portal's 30-days against the site's 14 (12 — postponed a
   purchase outright), three different return routes, straight-vs-baggy fit
   copy. For a brand whose whole trust strategy is "our numbers are exact",
   every contradiction is a direct hit on the load-bearing wall.
2. **The broken honesty mechanisms** — the captcha-eaten notify form (01, 06)
   and the popup's dead REVEAL MY CODE (17) take a shopper's contact details
   and give nothing back; that is the *opposite* of the brand's stated ethic,
   delivered by its own machinery.
3. **Off-brand third-party moments at maximum-stakes seconds** — stock white
   checkout, the `friendsof.crooksldn.com` login (20: "momentary phishing
   suspicion"), the gmail support address, the unexplained "Oairo UK Office"
   returns address, no legal identity anywhere (02).

**Verdict: the no-reviews position is consistent with the brand and
affordable — on the strict condition that the site never contradicts itself,
because self-consistency is what it spends instead of social proof.** The
fastest trust wins available are deletions and reconciliations (stale
description lines, the returns-window conflict), not additions.
