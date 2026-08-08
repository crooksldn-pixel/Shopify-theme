# PERSONA 2 — RETURNING FAN HUNTING THE NEW DROP (RUN 2)

Mobile, cold cache. Run 1 verdict: *would leave* — no recency signal anywhere, and tapping a
sold-out size silently kept the old size. Run 2 verdict: **stays — both blockers are closed.**

## The recency signal exists now

Four cards in the register carry filing dates in the status slot — `FILED 03.08` (CRXST★RZ),
`FILED 13.07` (V2 BAGGIES), `FILED 19.07` (both socks) — exactly the products published inside
the 30-day window. The other ten still read `AVAILABLE`. The register can finally answer "what
changed since I was last here" without breaking the evidence-log format *(run 1: `newInGrid: 0`,
`anyDates: false`, all fourteen stamped `AVAILABLE`)*.

*Instrument note:* the journey script's badge capture whitelists `AVAILABLE|SOLD OUT|NEW|LOW`
and cannot see `FILED …` — its `anyDates: false` this run is the instrument's blindness, not the
page's. Verified by direct page fetch. Fix the regex before run 3.

## The sold-out tap is honest now

On V2 BAGGIES (M, L, XL sold out), a real tap on L — after dismissing the cookie banner —
produces `SIZE L IS SOLD OUT` in the live-region stock line, a disabled `SOLD OUT` buy button,
a cleared variant id (the form physically cannot submit), and a notify capture:
`TELL ME WHEN THIS SIZE IS BACK — NOTIFY ME`. Verified end-to-end in `checks-corrected.json`.

**Correction to run 1:** the "silently sells the wrong one" evidence was contaminated — the tap
harness never actually removed the cookie banner (wrong selector), so its taps landed on the
banner, in both runs. The real run-1 defects were the product-level gate and the missing notify
path; both are now fixed. See METRICS §10.

**Outcome: finds the drop by date, gets told the truth about sizes, leaves an email if theirs
is gone.** The highest-LTV persona is no longer the one the site serves worst.
