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

**3. Browser concurrency is capped at 2–3 sessions.** This box has 4 cores. This
audit reports felt slowness, so machine contention would contaminate the very
observations it exists to collect. Sessions run few-at-a-time; persona 14 (slow
connection) runs alone.

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

## Hard limits observed

No order placed · no card details · no real personal data (test values only) ·
no discount, product or store setting modified · read-only on the store.

## Screenshot naming

`audit/screens/<area-or-persona>-<step>.png`. Feature-phase shots are prefixed
by area (`pdp-`, `set-`, `cart-`…); journey shots by persona number (`01-`…).
