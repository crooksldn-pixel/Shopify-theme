# THE GETAWAY — Appearance & UX refinement plan (2026-08-19)

Owner-reported issues: ~5s glitchy heavy load; "expired" flashes for a split
second after a win before reverting; the expiry line is gibberish; copy-code
interaction poor. Owner decision: gate the code — 10% visible, code sealed
until an SMS number is given; code delivered by text; copy shows ~0.5s state
then the popup closes itself.

Honesty rules carried from the audit (what made the OLD gate toxic, kept out
of the new one): value visible before any input; one channel, stated on the
offer screen ("code sent by text") so the gate is never a post-win ambush;
delivery can never fail silently — SMS failure still reveals the code on
screen. Marketing opt-in is a separate unticked checkbox (PECR).

## Stage 0 — Reproduce & baseline (no code)
Throttled mobile (Slow 4G, 4x CPU): record T-text, T-playable, total KB,
3 heaviest requests, console errors; screen-record the expired-flash and the
gibberish expiry line.
AC: numbers + recordings exist for later pass/fail.

## Stage 1 — Split shell from game (theme side)
1. Offer screen becomes native theme HTML in the popup snippet — instant:
   title, offer copy incl. "code sent by text", RUN IT / NOT NOW. No iframe
   on first paint.
2. RUN IT mounts the iframe (app opens at ?screen=game). Holding line
   "OPENING THE LOCK-UP…" (text, no spinner).
3. preconnect to app origin on shell render; prefetch app HTML on RUN IT
   hover/touchstart.
4. Trigger rules: never before cookie consent answered; never over open
   drawer/cart; not on /cart or /checkout; NOT NOW = 14-day suppress
   (localStorage); a win suppresses forever.
5. postMessage contract: getaway:close, getaway:height; theme shell owns
   Escape and focus-return.
AC: text at 0ms after trigger; no iframe request until RUN IT; NOT NOW
suppresses 14 days; never over banner/drawer/cart; Escape closes with focus
returned, no scroll jump.

## Stage 2 — App load & glitch diet
1. Text-first paint in iframe; font-display swap + metric-safe mono fallback.
2. Reserved dimensions for tumblers/buttons (no CLS); asset diet — total
   ≤~300KB, no single asset >100KB.
3. Mount once; view swaps not remounts.
4. Verify PRM: discrete steps, no timer bar, untimed.
AC: RUN IT → playable ≤2s throttled; zero visible layout shift; no console
errors on mount/win/replay; PRM verified with OS setting.

## Stage 3 — Expiry correctness
1. Three-state expiry: unknown → valid → expired. Nothing renders in
   unknown; "expired" unreachable until DROP_END_DATE loaded+parsed.
2. Parse once, Europe/London; format dd.mm per site convention:
   "This drop closes 31.08 — the code expires with it." Never ISO/epoch/
   Invalid Date/locale-guessed output.
3. Missing/unparseable DROP_END_DATE: omit line, log; never a wrong date.
4. Real expired state: "This drop has closed. New case opens soon — the
   register hears first." No minting.
AC: 10 consecutive throttled wins — "expired" never appears for any frame
unless truly expired; line reads exactly as specced; yesterday-date → clean
expired state, no mint; malformed date → line absent, no crash.

## Stage 4 — The gate: sealed evidence → SMS unlock → delivered
Design: redaction, not blur — tag shows "EVIDENCE Nº — 10% OFF" clear, code
area is a censor bar "CODE: ██████ — SEALED". Code not in DOM until unlock.
Prerequisite decision: SMS sender — Omnisend API or Twilio (token in Base44
secret).
1. Win screen v2: sealed tag; "Unseal it — number goes in, code comes back
   by text."; UK 07… field; separate UNTICKED marketing opt-in ("One message
   per drop, nothing else — same promise as the register."); [UNSEAL].
2. Backend on UNSEAL: validate, rate-limit, mint GTWY-XXXX if not already
   minted for player, send SMS ("CROOKSLDN — evidence released: GTWY-XXXX.
   10% off, one use, expires 31.08."), return code. Button "UNSEALING…"
   max 5s.
3. Success: bar peels (instant under PRM), code revealed, "Sent to
   07•••• ••4.", button → [COPY CODE].
4. Copy: clipboard write → "COPYING…" ~0.5s → "COPIED — IT'S IN YOUR TEXTS"
   → auto-close ~1s later. Safe because SMS sent at unseal, not at copy.
5. FAIL-SAFE (non-negotiable): SMS send fails but mint ok → reveal code on
   screen + "The text didn't go through — code's above, screenshot it."
   Mint fails → seal stays + "The printer's jammed. Your win is saved —
   reopen and we'll cut it again."; persist win; retry next open. No path
   takes a number and returns nothing.
6. Already-won revisit: pre-unsealed tag + existing code + [COPY CODE].
7. Store number + consent + timestamp + opt-in; only opted-in numbers join
   the marketing list.
AC: pre-unseal, 10% legible and code absent from DOM; happy path on a real
phone — SMS ≤30s with working code, copy state 0.5s, auto-close, clipboard
has code; code = 10% once, non-stacking, single-use; broken sender test →
code still shown on screen; same number twice → same code; malformed number
→ inline error; unticked opt-in → code text only, nothing else ever.

## Stage 5 — Re-audit battery
Portrait 390x844, landscape 844x390 (nothing clipped), reduced motion,
keyboard-only full flow (Escape at every screen), slow-4G cold load; all
four original complaints unreproducible (3 runs each) vs Stage 0 recordings.
AC: all pass; landscape controls on-screen at 390px height on all screens;
keyboard completes flow with visible focus.

## Sequencing
Stage 1 first (kills the 5s box, speeds all later testing) → 2 → 3 → 4
(blocks on SMS-sender decision) → 5. Each stage shippable alone.
