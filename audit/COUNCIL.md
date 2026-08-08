# COUNCIL.md — CROOKSLDN storefront — ROUND 2 (RE-AUDIT)

**Question put to the council:** unchanged from round 1 — where is this aesthetic costing sales,
and where is it earning its keep? What must change, what must not, and what is the highest-value
single change?

**Method:** same five-advisor roster as round 1 (Outsider, Contrarian, Executor, Expansionist,
First Principles Thinker), answering independently against the regenerated evidence pack
(`METRICS.md`, eight journey files, `DELTA.md`) and theme source at
`origin/claude/crooksldn-theme-init-bnen7a@db96aa3`. Responses anonymised A–E and peer-reviewed
on five fixed angles (accuracy, brand, feasibility, protection, commercial). One deliberate
deviation from round 1: **advisors received the commercial data from the start** — round 1's
council answered blind and was corrected by the chairman afterwards; repeating that blindness
would have been theatre. The chairman verified the review pass's checkable claims against source
before synthesising. Raw responses: `audit/council/responses-round2.md`.

**Guardrail applied:** unchanged and unbreached — no advisor challenged radius, palette,
typeface count, or the urgency-mechanics refusal. For the first time, the guardrail needed no
defending.

**Run-1 verdict, one line:** *"Audit the inventory, not the interface."* Round 2 confirms the
interface work is now done and verified; the inventory instruction was half-followed.

---

## WHERE THE COUNCIL AGREES — unanimous this round

**1. The aesthetic is exonerated with money attached.** 1 of 8 personas leaves (was 3), and the
leaver — the sceptic — bounces on admin plumbing: placeholders, contact page, banner position.
The register's `FILED` dates flipped the highest-LTV persona to "stays" *inside* the fiction;
the honest sold-out state (`SIZE M IS SOLD OUT`, disarmed form, in-voice notify) is scarcity
executed truthfully; the cold Instagram click converts in ~3 taps at 3.0 s. Nobody, on any
angle, attributed a lost sale to the look.

**2. Flip `inventoryPolicy` CONTINUE → DENY on the three tees.** On all five advisors' lists;
highest-value single change for three of them (Outsider, Executor, Expansionist), and the
chairman adopts it — see THE ONE THING below. The restock to 10/variant without the policy
change is a countdown: overselling re-arms at zero, primed for exactly the July-shaped spike
(186 orders) the store hopes for. While there: CRX GARMS sits archived at a phantom 985 units
*still under CONTINUE*, and V2 BAGGIES/M at −1.

**3. The meta row must be reserved — and the fix is systemic, not local.** The 0.2315 PDP CLS
is `PRODUCT NN / 14` in display type inside `flex-wrap: wrap` (`crooks.css:500`, verified). The
Contrarian's reframe was adopted unanimously in review: this is not a fix-sprint footprint but a
**standing tax of the VT323 constraint** — a bitmap face with wildly mismatched fallback metrics
makes every VT323 surface a layout hazard until reserved. The feasibility reviewer killed the
cheap fix (`white-space: nowrap` on the span is a no-op against flex wrap; chairman-verified)
and identified the right one: a **`size-adjust`ed fallback in the `--crk-font-display` stack**
(`crooks.css:47`), which retires the tax for every present and future VT323 surface at once.
Priced honestly: hours including the no-JS and zoom regression checks, not minutes.

**4. Three image masters and one banner setting.** Re-upload `cellcrew.webp` (976 KB, now on
the money page), `v2baggies.webp`, the white/red socks master; move the cookie banner off
bottom-overlay. Both admin, both minutes, both proven this run (the same re-upload took the tee
PDP from 13.9 s to 2.4 s; the banner is now proven to have manufactured round 1's worst
finding).

---

## THE CLASH — what to do about £28,270 of archived stock

The only genuine disagreement of the round, and it produced the best thinking.

**The First Principles Thinker (E):** re-file the proven sellers into the register. "The theme
has out-built its catalogue... The aesthetic isn't the constraint; it's the shelf. Stock it."
Zero theme work — the register renumbers itself, filing dates self-label.

**The Contrarian (B):** the pledge is the wall around the money. *"When a run is gone it does
not come back"* is already falsified backend-side (restock-under-CONTINUE), and a visible
re-file falsifies it in public. Amend the sentence — one honest edit — then re-file.

**The Expansionist (D):** neither. Closed cases with real sales history are *provenance*, not
clearance — a separate CASE CLOSED register (the collection-page register from commit `1892419`
makes this nearly free), preceded by a hand-count because the repull proves counts lie
(CRXST★RZ 970→98).

**The review pass settled it.** Brand: E's plain unarchive dilutes `PRODUCT NN / 14` — the one
element proving a finite catalogue — and publicly falsifies an unamended pledge; D's is "the
only archive route that survives brand review." Protection: B's edit is the round's only
KEEP §6 violation — the WITNESS STATEMENT is named must-not-change, and "make the backend true
first; the prose may need no edit at all." Feasibility: E's "zero theme work" hides real costs —
archived products carry no `crooks.*` metafields (half-empty records), and unarchiving CRX GARMS
at a phantom 985 under CONTINUE "is the oversell reborn at 20× scale." Commercial: D ranked
first — three pools covered, honest prices, and the round's one newly discovered asset.

**Chairman's ruling:** sequence, don't choose.
1. DENY flip first (minutes) — the integrity precondition for everything else.
2. Hand-count the archive (the repull's own evidence says trust no count).
3. Trial the archive as a **separate closed-case register** in the fiction's own voice — not a
   plain unarchive into the live catalogue. The `/14` stays honest, the pledge stays untouched,
   and the runs that were never gone (467 units that never sold out — they were hidden, not
   sold) become provenance.
4. The WITNESS STATEMENT is edited only if the trial proves it must be — a last resort, per
   KEEP §6, not a headline.

---

## WHAT THE REVIEW PASS CAUGHT — kept for the record

- **A (Outsider)** miscited the cart regression's vector (the brand pass didn't carry
  `cellcrew.webp` in; the crewneck's image did — DELTA R2), and its popup-timing figures are
  run-1 carryover no run-2 instrument re-measured. Its ask (exit-intent/second-visit) exceeds
  the evidence — journeys/05 records homepage firing as correct — but feasibility notes the
  timer and once-per-browser gate are theme-owned (`crack-the-cuffs.liquid`), so if analytics
  ever justify it, it is a snippet edit, not a Base44 project.
- **B (Contrarian)** invented a quotation ("relist the stock" appears nowhere in COMMERCIAL.md)
  and misattributed a journey LCP; both minor, its mechanism work was the round's sharpest.
- **C (Executor)** was near-flawless on citations; its one theme fix named the wrong CSS lever
  (nowrap), corrected above.
- **D (Expansionist)** overpriced the image savings (~1.1 MB, not 1.4), underpriced its notify
  claim — **Shopify Flow has no contact-form trigger**, so routing the restock captures is a
  real integration (consent copy, list tooling, no-JS re-verify), not a "no theme change" rule.
- **E (First Principles)** survived accuracy review with zero factual errors — and still drew
  the round's sharpest feasibility objection, which is the correct division of labour.

**The round's newly discovered asset (D):** the variant-level notify capture — built in the fix
sprint, verified working — posts through `form 'contact'`, so restock intent arrives as
unstructured inbox email with no consent flag and no per-variant list. At drop cadence this is
the owned-audience machine running with its output unplugged. Scoped as a project item in the
refreshed backlog.

**Blind spots, round 2:** four of five advisors proposed theme work without checking the no-JS
fallback KEEP §5 calls the easiest thing to break (the Executor alone re-verified it: 18 links /
40 images intact). And two advisors flagged what nobody else priced: the carriage bar accreted
*above* the register — first product card 1.22 → 1.48 viewports. The board earned its viewport;
new furniture hasn't. **Stop stacking.**

---

## THE RECOMMENDATION

**Round 1 said the storefront wasn't the biggest problem. Round 2 says the storefront is
finished — and the back office is now the only thing contradicting the brand.**

The theme did its part: eleven backlog items closed and verified, the design system's one
self-violation removed, zero WCAG failures in theme-owned surfaces, and the fiction upgraded
from decoration to function (custody-as-tracking, filing dates, honest sold-out capture). The
two theme defects left are small, priced, and named (meta-row reservation; carriage-bar
stacking).

What remains is the store telling the truth about itself: a policy checkbox that lets it sell
what it doesn't have, a five-figure archive it pretends not to have, legal pages with template
brackets where a company should be, and a consent banner standing between every first visit and
the size row. None of it is design. All of it is under an hour each, except the archive — which
is days, and worth more than everything else combined.

**What must not change** — restated from round 1, with round-2 additions: the canvas board and
its pause guards · the register format and numbering, **now including the FILED status slot** ·
the measurement apparatus · the WITNESS STATEMENT and informant-register prose · the focus-ring
system · the refusal to render fake data · zero-radius/no-shadow enforcement · the no-JS
fallback · the plain-English buy spine, **now two actions in the sticky bar** · the untouched
`RELEASE REQUEST` span · **the variant-level sold-out + notify pattern.**

---

## THE ONE THING TO DO FIRST

**Untick one checkbox, three times.**

`inventoryPolicy: CONTINUE → DENY` on MONEY CLIVE TEE, 3 CLIVES TEE, BROADCAST TEE. Minutes, in
admin, zero design cost. It is the only item every advisor listed, and the Expansionist's
framing is the verdict: the entire system — the filing dates, the notify capture, the sworn
statement — is a scarcity fiction that is commercially valuable only while it is true. DENY is
what makes a sell-out fire the notify form instead of a phantom sale; the notify form is what
feeds the register; the register is what the next drop is sold to. The storefront now says
"this is a real shop" everywhere a shopper can see. One checkbox in the back office still says
otherwise.

Then count the archive, and open the closed cases properly.
