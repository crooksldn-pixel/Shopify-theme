# KEEP-ADDITIONS.md — working and load-bearing, not yet on the protect list

Additions to `KEEP.md` (branch `claude/crooksldn-site-audit-eijmkd`) from this
audit. Named specifically, with the evidence for why each is load-bearing —
audits that only list faults get acted on badly. The council's unanimous
do-not-touch list (buy spine, measurement apparatus + SIZE GUIDE anchor, set
toggle purchase flow, honest sold-out state, evidence bag) reaffirms existing
KEEP entries; below is what's NEW.

## Mechanics proven this audit

1. **The carriage bar's empty-cart stand-down** (`crooks-cart-progress`).
   Renders nothing until the bag has an item; first catalogue card sits at
   0.90 viewports pre-add. This single behaviour resolved the round-2
   council's real-estate objection (1.22→1.48 viewports). If anyone "fixes"
   the bar to always show, the old complaint returns. (Phase 1; Q2.)
2. **`?variant=` URL rewriting on size selection** (`crooks-record.js`).
   Survives history, reload, and sharing; the cart's title links deep-link to
   the exact variant, which quietly de-risks the remove-and-re-add size dance
   (08). Deliberately does NOT rewrite for sold-out sizes so shared links
   reopen on an available size — keep that asymmetry.
3. **The pre-paint theme resolver** — zero wrong-theme flash even at slow 4G,
   scroll position preserved on mid-scroll toggle. (Toggles agent; 11.)
4. **Lazy CASE 001 board injection** — zero requests before first drawer
   open, one after. The drawer stays cheap for the majority who never open
   it. (Header agent.)
5. **The fixed-width `BAG [n]` cell** — count 0→1→3 with zero header reflow,
   measured constant geometry. (Header agent.)
6. **Partner-size pre-mirroring with touched-override** in the set toggle —
   it removes a step for the common same-size buyer. NOTE the paired risk
   (04: silent mirror shipped wrong-size shorts) — the fix is a visible cue,
   not removal of the mirroring.
7. **Liquid-prerendered prices in data attributes** (set + record). The
   reason a USD-market session converted cleanly instead of breaking. Any
   refactor that lets JS assemble a currency string reintroduces the bug
   class this design eliminated. (Set agent.)
8. **The sticky bar's appear/disappear contract** — shows only while the
   real buy button is off-screen, carries live price + selected size; 17
   (200% zoom) named it the thing that meant she "never loses the buy
   button". Protect the contract while fixing its two bugs (double-add,
   lit-when-sold-out).
9. **The add-to-bag aria-live announcement with the in-region View bag link**
   (16: "Added — 1 in bag" with an actionable link, focus untouched). The
   coming visible-feedback fix must be layered ON this pattern, not replace
   it — it is currently the best-announced cart add 16 has met in streetwear.
10. **The empty-search stand-down + curated direct links** — the only route
    from search to Terms/FAQ/policies, confirmed end-to-end (12: two answers
    were literally one tap). Also the pre-typing links (TRACK YOUR ORDER /
    QUESTIONS / START A RETURN).

## Experience qualities proven this audit

11. **The reduced-motion completeness** — zero `@keyframes` in `crooks.css`,
    boot line pre-typed, drawer hard-cut, board drawing one static frame.
    Persona 18: "the calmest streetwear site she's used", and she *bought*.
    This is a competitive property; any new animation must be
    reduce-guarded or it breaks a proven state.
12. **The slow-4G first-paint order** — readable text UI at ~3s, zero layout
    shift at 3/5/10s, dark ground hiding image lag (14: "wait, not leave";
    01 usable in ~5s on bus 4G). The metric-matched font fallbacks landed;
    treat the font stack as sealed (KEEP round-2 already warns on this —
    re-affirmed with journey evidence).
13. **The drawer's keyboard contract** — 16-stop cycle that never escapes,
    Escape returns focus to MENU (15: "exemplary"). Already KEEP-adjacent;
    now journey-proven.
14. **The packaging ("PROPERTY BAG") section as the homepage's signature** —
    09's best moment and the de facto gift wrap; the homepage agent's
    best-landing block. With the board gone, this is the memorable thing on
    the page. Do not trade it for a lookbook revival without noticing what
    it's carrying.
15. **The dispatch line's honesty pairing** — computed "leaves tomorrow"
    correct at 22:00 against the 18:00 cutoff AND hiding itself when a
    sold-out size is selected (07 called the pairing "honest"). The no-JS
    fallback text is stale (backlog) — fix the fallback, keep the behaviour.
16. **The 404's path back** — real 404 status, Continue shopping, four live
    recommendations (content agent: "a dead link costs one tap"). The cream
    skin is backlog; the content is protect.
17. **Whole-card single link on the register** — image, title, price one
    focus stop announcing name/price/availability (15, 16); no dead zones
    (register agent).
18. **Misspelling-tolerant search ranking + auto-focused search field** —
    "bagies" still ranks V2 BAGGIES first; /search auto-focuses its input
    (07's fastest-funnel ingredient).

## A sharpened rule, for the record

The council's agreed formulation is worth writing into KEEP: **the brand's
substitute for social proof is exact numbers and self-consistency.** That
elevates copy reconciliation from admin tidying to conversion work, and it is
the standing test for any new surface: if two site surfaces can state the
same fact, they must be generated from one source or checked against each
other before ship.
