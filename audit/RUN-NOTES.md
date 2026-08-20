# Run notes — plumbing and judgement calls

Everything here is machinery, not findings. Nothing in this file belongs in a
report. It exists so the run is reproducible and so you can see which calls I
made without asking.

## Preflight result

| Check | Result |
|---|---|
| `SPEC.md` present in working dir | **No** — recovered from `origin/claude/crooksldn-theme-init-bnen7a` (last touched 2026-08-20 12:35, commit *"Deploy to staging 202053779799"*). Read in full. |
| `audit/KEEP.md` | Recovered from `origin/claude/crooksldn-site-audit-eijmkd` → `audit/_ref/KEEP.md` |
| `audit/RUN3-FINDINGS.md` | Recovered, same branch → `audit/_ref/RUN3-FINDINGS.md` |
| Preview URL loads | Yes, 200 |
| `.crk-root` present | **Yes** |
| `window.Shopify.theme.id` | **202053779799** — "CROOKSLDN — Staging", role `unpublished` ✓ |
| Cookie survives in-context navigation | Yes — re-asserted on every `go()` |
| Playwright + Chromium | Playwright 1.62.1, Chromium 1194 at `/opt/pw-browsers/chromium-1194` |
| `audit/` tree | `journeys/ features/ screens/ _tools/ _ref/` |

## Judgement calls made without asking

**1. Chromium had to be capped at TLS 1.2.** Every HTTPS request from the
browser died with a connection reset while `curl` to the same URL returned 200.
The tunnel itself was fine — a raw `CONNECT` returned `200 Connection
Established` — so the failure was in the TLS handshake that follows. The
session's egress proxy cannot complete Chromium's TLS 1.3 ClientHello.
`--ssl-version-max=tls1.2` fixes it. This changes nothing a shopper would
perceive; it is in `audit/_tools/lib.mjs` so the run reproduces.

**2. The audit is pinned to the GB market, by cookie.** Left alone, this
container geolocates as US and Shopify serves the store in USD: the £50 crewneck
renders `$70.00`, the £60 jeans `$84.00`. Worse for this audit, `SPEC.md §3.7`
gates the carriage bar to `country_code == GB`, so a US session cannot see the
feature Q2 asks me to judge. Setting `localization=GB` + `cart_currency=GBP`
before first navigation returns the real UK storefront — £50.00 / £45.00 /
£60.00, matching `SPEC.md §5` exactly. Every context in this audit sets both.
*(The US view is separately interesting and is logged as an observation in
`FEATURES.md`, not as a persona.)*

**3. Browser concurrency is capped at 3, enforced by a lock on disk.** Two
reasons, one of which cost an hour before it was understood.

The first is fidelity: this box has 4 cores and this audit reports *felt*
slowness, so machine contention would fake the very observations it exists to
collect. Persona 14 (slow connection) runs alone.

The second is the store. Running twelve browsers at once tripped its bot
protection. Two symptoms arrived together: HTTP 429s, and — more confusing —
pages that simply hung forever. The hang was a Cloudflare challenge frame:
the storefront started serving a challenge, and this session's egress policy
blocks `challenges.cloudflare.com`, so the frame could never resolve and every
page sat waiting on it. `curl` to the same URL kept returning 200 the whole
time, which is what made it look like the agents were stuck rather than
throttled.

The harness now: caps browsers across all agent processes via a lock directory;
aborts requests to the challenge host so they fail fast instead of hanging;
retries 429/503/challenge pages with exponential backoff; and paces navigations
with a little jitter. Sessions queue rather than pile on.

The cap was run at 4–6 during the feature census, which judges behaviour rather
than speed, and dropped back to 3 for the persona journeys. Personas 01 (the
90-second cold click), 07 (fastest path, taps counted) and 14 (congested 4G) all
report felt duration, so they were held back and run in a quiet window rather
than against a machine carrying a dozen other browsers. Persona 14 runs alone.

**How to read any timing in this audit.** Durations are what a shopper would
have *felt* in that session, on the profile named in the journey header. They
are not benchmarks and no page-speed metric was collected — that was ruled out
by the brief and the numbers already live in `SPEC.md`.

**4. No test login was supplied.** The `Test login:` field arrived as the
literal placeholder `<PASTE-OR-LEAVE-BLANK>`. Persona 20 therefore documents the
**signed-out** tracking experience only, and the signed-in timeline and courier
record in `SPEC.md §3.12` go down as **UNTESTED**, not as working.

**5. `10CROOKS` is entered in the cart discount field only.** `§3` of the brief
sanctions this as read-only observation. It is never carried into checkout, and
no order is ever placed. Checkout is walked to the payment step and abandoned.

**6. The repo checkout is not the theme under audit.** The working branch
(`claude/theme-gauntlet-v2-buyers-1ebhak`) holds a different, month-old Horizon
line with no `crooks.css`. The audit is conducted entirely through the browser
against the deployed staging theme, as the brief requires. Deliverables land on
the designated branch regardless.

## One preview artefact that must not become a finding

Shopify's preview bar renders as `DIV#PBarNextFrameWrapper` — transparent,
`pointer-events: auto`, fixed across the bottom **68px** of the viewport. On a
390×844 phone that lands exactly on top of the theme's own sticky buy bar, so
the sticky `ADD TO BAG` and `CHECKOUT NOW` swallow taps and appear dead.

**They are not dead.** The wrapper exists only because this audit runs against a
`shopifypreview.com` URL; a shopper on the published store never has it. Any
note reporting an untappable sticky buy button is reporting the preview bar.

The harness now hides it along with the older preview-bar ids. Two earlier
observations were traced to it and should be read with this in mind: the
"blocked click" on a sold-out size, and the sticky bar "swallowing every tap"
in one corner. What is **not** explained by it, and stands: the sticky bar
failing to hide when the real buy button is on screen, and the price it displays
being wrong while the set toggle is on.

## The store was edited while the audit ran

Persona 01 caught a product being renamed mid-journey: `GREY WASH OG JEANS` in
the timed screenshots at 18:27, `GREY WASH YARD JEANS` by the time the
add-to-bag confirmation was captured minutes later. Same handle, same £60.

Nothing in this audit touched the store — it is read-only throughout — so this
is someone editing in admin during the run. Two consequences worth knowing:

- **Product names quoted in journeys are true as at the moment of the
  screenshot**, and a name may not match what is live now.
- **Stock levels moved during the run too**, which is why one agent reports the
  catalogue as 12 products and another as 13, and why "nothing is currently
  sold out" in the register was true for the catalogue pass and not for the
  sold-out journey, which found `V2 BAGGIES` at `2 OF 5 SIZES LEFT`.

Neither affects a finding. Both are recorded so a discrepancy between two
journeys is read as the store moving, not as an agent being careless.

## Hard limits observed

No order placed · no card details · no real personal data (test values only) ·
no discount, product or store setting modified · read-only on the store.

## Screenshot naming

`audit/screens/<area-or-persona>-<step>.png`. Feature-phase shots are prefixed
by area (`pdp-`, `set-`, `cart-`…); journey shots by persona number (`01-`…).
