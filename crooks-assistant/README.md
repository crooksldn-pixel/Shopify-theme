# CROOKS Assistant

A voice assistant for CROOKS LDN. You hold a button on a tablet, ask a question out loud, and it
answers out loud — reading from the Shopify store and the email inbox, and never writing to
either.

Everything runs on your own Mac. No cloud services, no database, no monthly cost. Claude is
reached through the Agent SDK on the Claude Max subscription; speech-to-text is whisper.cpp
locally; speech-to-speech is the tablet's own voice.

Built to the fifteen-milestone plan in *CROOKS Assistant Build Plan* (Rev 3, 7 Sept 2026).

---

## Status

The portable code is written and tested. The machine-specific work — the parts that need your
Mac, your tablet, and your console access — is not, and cannot be done from anywhere else.

| Milestone | State |
|---|---|
| M0 Environment | Repo, packaging, `make doctor`. **Run `make doctor` on the Mac.** |
| M1 Transport | FastAPI + `/health` + the tablet page. **Tailscale setup is yours.** |
| M2 Microphone | Capture UI, `/audio-test`, decode + level stats. **Needs the tablet.** |
| M3 Speech | Whisper client, VAD/hallucination filter, normaliser, benchmark harness. **Needs whisper.cpp built and tablet audio.** |
| M4 Claude provider | Implemented, with the billing guard. **Needs `claude setup-token`.** |
| M5 Tools + gate | Implemented and **proven by tests that run here**. |
| M6 Shopify auth | Client with token cache and the `shpat_` fallback. **Needs your credentials.** |
| M7 Shopify tools | Six tools, queries validated against the live Admin schema. |
| M8 Gmail auth | Auth script and refresh handling. **Needs the Google Cloud console work.** |
| M9 Gmail tools | Two tools, no write path anywhere. |
| M10 Typed agent | System prompt, KB loader, `scripts/chat.py`, redacted logging. **Needs your KB content.** |
| M11 Voice in | `/turn` takes audio or text; state machine wired. |
| M12 Voice out | Chunking, unlock, voice picker — all three Android guardrails. |
| M13 Reliability | Named failures, per-subsystem `/health`, launchd plists, log rotation. |
| M14 Acceptance | 18-command script and the scoring harness. **Run it from the tablet.** |

What has actually been verified, on Linux, with no credentials:

```
123 passed, 2 skipped        # 2 skipped = the live Shopify/Gmail tests
ruff: All checks passed
8/8 GraphQL queries validated against the live Shopify Admin schema
```

Nothing here has run against the real store, the real inbox, or the real tablet. Work the
milestones in order on the Mac; each one's success test is in the build plan.

---

## Setup on the Mac

```bash
git clone <this repo> ~/crooks-assistant && cd ~/crooks-assistant
make doctor          # tells you exactly what is missing
make venv
make dev             # http://127.0.0.1:8000
```

Then, in order:

1. **Tailscale** (M1) — install on Mac and tablet, same account. Admin console → DNS → enable
   MagicDNS, then HTTPS. Rename the Mac to something unrevealing: the hostname lands in public
   Certificate Transparency logs. Start uvicorn, then `tailscale serve 8000`. Open the
   `https://<machine>.<tailnet>.ts.net/` address on the tablet and add it to the home screen.
   *It must be that address, not the LAN IP* — the microphone and speech APIs both require a
   trusted secure context, and the LAN IP is not one.

2. **whisper.cpp** (M3) — `python scripts/whisper_server.py` prints the exact build commands if
   it is not built yet. Two things to check: the Core ML `.mlmodelc` must sit beside the `.bin`
   (without it everything works about twice as slowly and says nothing), and a Silero VAD model
   must be present (without it, silence transcribes as "Thank you.").

3. **Claude token** (M4) — `claude /login`, then `claude setup-token`, then
   `python scripts/set_secrets.py claude_oauth_token` and paste at the local prompt.
   **The token expires after one year — diary a reminder for month eleven.**

4. **Shopify** (M6) — check the store is listed under Stores in the Dev Dashboard organisation
   *first*; if it is not, client credentials fail permanently with `shop_not_permitted` and the
   `shpat_` fallback is the way out. Scopes are in `SHOPIFY_SCOPES.md`. Then
   `python scripts/set_secrets.py shopify_client_id` and `… shopify_client_secret`, and
   `python scripts/shopify_check.py`.

5. **Gmail** (M8) — Google Cloud project → enable the Gmail API → Branding → Audience: External
   → Data Access: `gmail.readonly` only → **Publish app** → Clients → Desktop app → save the
   JSON as `credentials.json`. Then `python scripts/gmail_auth.py`.
   **Skip "Publish app" and your token dies every seven days.**

6. **Content** — `kb/terminology.md` (~40 product names as you say them) and the knowledge base
   files described in `kb/README.md`.

7. **Voice** (M12) — settings → audition the voices → pick one. If none show "offline", install
   the en-GB voice data: Settings → General management → Text-to-speech → Install voice data.

8. **Run at boot** (M13) — edit `USERNAME` in `launchd/*.plist`, copy to `~/Library/LaunchAgents`,
   `launchctl load` both.

---

## Working on it

```bash
make dev          # backend
make chat         # terminal REPL — use this, not voice, for repeat testing
make test         # 123 tests; the live API ones skip without credentials
make lint
make bench        # M3 model comparison, on tablet audio
make acceptance   # M14, 18 commands
```

**Test through `make chat`, not through the tablet.** The build and the assistant draw from the
same Max allowance, and a long day of voice testing can exhaust the weekly window. Tool logic is
testable directly in Python without spending anything.

---

## How it is put together

```
tablet (Chrome)  ──HTTPS via tailscale serve──▶  FastAPI on 127.0.0.1:8000
                                                  │
                    ┌─────────────────────────────┼────────────────────┐
                    ▼                             ▼                    ▼
             whisper.cpp                  Claude Agent SDK        knowledge base
          (local, port 8910)            (Max subscription)         (system prompt)
                                                  │
                                        in-process MCP server
                                                  │
                                          ┌───────┴───────┐
                                          ▼               ▼
                                    Shopify Admin      Gmail API
                                     (read-only)      (readonly)
```

`app/tools/gate.py` is the security architecture. Every tool call passes through it, including
auto-approved ones — that is why the gating lives in a `PreToolUse` hook rather than in
`can_use_tool`, which auto-approved tools never reach. Three rules make it fail closed:

- an unregistered tool is RED, so adding a tool without adding a rule grants nothing;
- any tool whose *name* reads as a mutation is RED before the rule table is consulted;
- detail tools accept only ids issued by a search earlier in the same session.

`tests/test_gate.py` proves a RED tool's handler never executes, via a module-level counter. If
that test ever fails, stop and fix it before anything else.

### Layout

```
app/
  main.py            FastAPI app; loopback only
  runtime.py         composition root — everything is wired here
  routes/            health · turn · admin
  providers/         base.py (ABC) · max_agent_sdk.py · anthropic_api.py (stub, deliberately)
  tools/             registry · gate · dispatch · shopify_tools · gmail_tools · mock
  clients/           shopify · gmail · whisper
  speech/            decode · transcribe · normalise
  session/           manager · models (issued-id ledger)
  kb/                loader + the system prompt
  secrets/           keyring wrapper
  logging/           redacted JSONL with rotation
config/settings.py   non-secret configuration
web/                 the tablet client
scripts/             doctor · set_secrets · gmail_auth · shopify_check · whisper_server
                     bench_whisper · chat · acceptance
tests/               gate · normalise · turnlog · shopify_tools · gmail_tools · bench_decision
launchd/             run-at-boot plists
```

whisper.cpp itself lives outside the repo at `~/tools/whisper.cpp` — it is a large third-party
build tree and does not belong in this history.

---

## Two deviations from the build plan

Both were forced by things that only show up when the code is actually run.

**1. `secrets/` is `app/secrets/`.** A top-level package named `secrets` shadows the standard
library's `secrets` module, and FastAPI imports `token_hex` from it during startup. The result
is an `ImportError` before a single line of our code runs — verified, not theorised. Nesting it
under `app/` keeps the same shape and cannot shadow anything.

**2. Metaphone, not Double Metaphone.** `jellyfish` removed Double Metaphone in 1.0. Metaphone is
the closest maintained equivalent and is what the normaliser's thresholds were tuned against.

---

## Rules this codebase is built on

- **Read-only.** No send, no draft, no label, no edit, no refund, no inventory write. The gate
  refuses mutation verbs by name; the Gmail scope cannot write; the Shopify scope list has no
  `write_` entry. A write path would have to defeat all three.
- **Never report success that was not verified.** A tool error is reported as an error. This is
  the one failure mode that is not negotiable, because it is the one that destroys trust.
- **Ask rather than guess.** Two customers called John produce a question, not a choice.
- **No pay-as-you-go billing, ever.** The process refuses to start if `ANTHROPIC_API_KEY` or
  `ANTHROPIC_AUTH_TOKEN` is set. Do not remove that check.
- **Secrets live in the Keychain.** Typed at a local prompt, never in a file, never in an
  argument, never echoed, never logged.
- **Logs carry no personal data.** Addresses, phone numbers, emails, postcodes, card numbers and
  message bodies are redacted before anything is written. `tests/test_turnlog.py` opens a real
  log file and checks.

---

## Out of scope for Day 1

Wake word, Android APK, VPS hosting, scheduled triage, shipping-label integration, and every
write action. Phase 2 starts from a tagged `v1.0-day1`.
