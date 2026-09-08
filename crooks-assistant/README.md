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
| M3 Speech | Pipeline **passed against a real whisper-server** here. Normaliser tuned on the real catalogue. **Benchmark needs the Mac and tablet audio.** |
| M4 Claude provider | **Passed against real Claude.** Billing guard, CLI-login fallback. **Needs `claude setup-token` before launchd.** |
| M5 Tools + gate | **Passed against real Claude** — hook denied a RED call live. Proven by tests on every run. |
| M6 Shopify auth | Client with token cache and the `shpat_` fallback. **Needs your credentials.** |
| M7 Shopify tools | Seven tools; queries validated against the schema and search syntax verified on the live store. **Needs your credentials to run.** |
| M8 Gmail auth | Auth script and refresh handling. **Needs the Google Cloud console work.** |
| M9 Gmail tools | Two tools, no write path anywhere. |
| M10 Typed agent | System prompt, KB loader, `scripts/chat.py`, redacted logging. **KB written from the store's own policies and metafields**; one discretion section is yours. |
| M11 Voice in | `/turn` takes audio or text; the tablet polls `/state` so the screen shows the tool actually running. |
| M12 Voice out | Chunking, unlock, voice picker — all three Android guardrails. |
| M13 Reliability | Named failures incl. usage-limit reset time and "lost the thread"; per-subsystem `/health` with Core ML check; launchd plists; log rotation; capture cap. |
| M14 Acceptance | 18-command script; placeholders fill themselves from the live store. **Run it from the tablet.** |

What has actually been verified — here, on Linux, and against the real store:

```
268 tests pass, 2 skipped (live Shopify/Gmail), all offline     make test
ruff clean                                                       make lint
8/8 GraphQL queries validated against the Shopify Admin schema
```

**Against the live CROOKSLDN store** (read-only, through the developer connector — never
through the assistant): shop domain, timezone, order-name format, order search syntax, product
search syntax, customer search behaviour, variant title shapes and the real 23-product catalogue.
Each of these corrected something the plan assumed. See *What the live data changed* below.

**Against whisper.cpp, built and run here** (CPU only, no Core ML): a PyAV-encoded
`audio/webm;codecs=opus` blob — what the tablet's MediaRecorder sends — decodes to 16 kHz mono,
transcribes correctly through `app/clients/whisper.py`, and silence stops at the level gate
before whisper is called. Two server-API mistakes were found and fixed. The Linux timing
(~6 s for 11 s of speech, no acceleration) is not representative of the M4 Max and is not
quoted anywhere as if it were.

**Against real Claude on subscription auth** (`bench/results/m4-m5-*.txt`): the plan's M4 and
M5 success tests pass. With a deliberately bland tool description Claude *attempts* the RED
tool, the `PreToolUse` hook logs `tier=RED`, the SDK denies it, the handler's counter stays at
zero, a proposal id is staged, and Claude reports the refusal honestly. No API key was present.

Not verified, because it cannot be from here: the tablet microphone (M2), Core ML timings (M3),
your Keychain, Tailscale, launchd, and the live Shopify/Gmail tools with your credentials.

---

## Setup on the Mac

Every step is the same shape: open Terminal, `cd ~/crooks-assistant`, type one line. You never
run a Python file directly; `make` does it. `make help` prints this list.

| Step | You type | Then |
|---|---|---|
| Check the Mac | `make doctor` | Install whatever it names, the way it says |
| Install | `make venv` then `make test` | Expect 279 passed |
| Run it | `make dev` | In a second Terminal tab: `tailscale serve 8000` |
| Speech | `make whisper-server` | It prints the build steps the first time |
| Tokens and keys | `make secrets` | Asks for the Claude token, Client ID, Client secret, one at a time, hidden |
| Prove Shopify | `make shopify` | Shop name, `Europe/London`, one recent order, cache reused |
| Gmail | `make gmail` | A browser opens once. Then `make gmail-verify` |
| Everything at once | `make check` | Doctor, Shopify, Gmail in one go |
| Ask questions | `make chat` | Typed, so it does not use the tablet or much allowance |
| Day 1 test | `make acceptance SPOKEN=1` | From the tablet, at your working distance |

The console work (Tailscale, Shopify Dev Dashboard, Google Cloud) is the only part that is
not a `make` line, and it is described step by step below.

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
   must be present — the launcher refuses to start without one, because a server without it
   rejects every request that asks for voice detection and the tablet would say "connected"
   while every question failed.

3. **Claude token** (M4) — run `claude` and sign in with `/login` if you have not, then `claude setup-token`, then
   `make secrets` and paste it at the hidden prompt.
   **The token expires after one year — diary a reminder for month eleven.**

4. **Shopify** (M6) — check the store is listed under Stores in the Dev Dashboard organisation
   *first*; if it is not, client credentials fail permanently with `shop_not_permitted` and the
   `shpat_` fallback is the way out. Scopes are in `SHOPIFY_SCOPES.md`. Then `make secrets`
   for the Client ID and secret, and `make shopify` to prove it. You do not need to find the
   Stores list first: `make shopify` either works or names `shop_not_permitted`, which is the
   same answer in ten seconds.

5. **Gmail** (M8) — Google Cloud project → enable the Gmail API → Branding → Audience: External
   → Data Access: `gmail.readonly` only → **Publish app** → Clients → Desktop app → save the
   JSON as `credentials.json` in this folder. Then `make gmail`.
   **Skip "Publish app" and your token dies every seven days.**

6. **Content** — `kb/terminology.md` already holds the live catalogue with spoken aliases for
   the stylised names; correct the aliases to how you actually say them (five minutes). The
   policy and sizing files are written from the store's own published content; the one thing
   only you can write is the discretion section of `kb/cs-rules.md`.

7. **Voice** (M12) — settings → audition the voices → pick one. If none show "offline", install
   the en-GB voice data: Settings → General management → Text-to-speech → Install voice data.

8. **Run at boot** (M13) — edit `USERNAME` in `launchd/*.plist`, copy to `~/Library/LaunchAgents`,
   `launchctl load` both.

---

## Working on it

```bash
make dev          # backend
make chat         # terminal REPL — use this, not voice, for repeat testing
make test         # 268 tests, all offline; the two live API ones skip without credentials
make lint
make bench        # M3 model comparison, on tablet audio
make acceptance   # M14, 18 commands
```

**The acceptance script has not been run against real Claude.** It could have been — the store
was readable and the CLI was logged in — but eighteen live turns come out of your Max allowance
and nobody had authorised that spend. It is a five-minute decision that is yours: once M6 is
done, `python scripts/acceptance.py` in typed mode fills the placeholders from the store, costs
about eighteen turns, and turns "the gate holds" into an answer-accuracy score with the
questions it fumbled listed.

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

## The review

Eight independent reviewers each took one lens — gate security, Agent SDK correctness, Shopify
API, Gmail API, Chrome-on-Android, speech, plan conformance, unattended operation — and produced
63 findings. Every finding was triaged against the current tree; the ones that stood were fixed
in commit `cebccbe`. The most serious: transcripts were reaching the stdout log unredacted,
`POST /reload-kb` changed nothing the model saw, the billing guard ran inside a caught start-up,
Gmail calls blocked the event loop so the tool timeout could never fire, and a stalled Claude
turn would have held the turn lock forever. The full list is in that commit's message.

Findings that were refuted stayed refuted: "token.json is a secret in a file" was the plan's own
choice (the Gmail credential can now live in the Keychain instead); caller-chosen session ids are
accepted on a single-user tailnet.

---

## What the live data changed

The build plan was written from the spec. Running the code against the real store, a real
whisper-server and real Claude changed these things — each one would have cost time on the Mac.

| Plan assumed | Reality | What changed |
|---|---|---|
| Shop domain `crooksldn.myshopify.com` | `5wn03t-nm.myshopify.com` | Settings default |
| Orders named `#4832`, searched as `name:#4832` | Orders are `CROOKS-1928` (older ones `#1036`); bare `name:1928` matches both | Search uses the bare number; "crooks 1928", "CROOKS-1928", "#1928" all resolve |
| Variant title is the size | Multi-option variants are `Black / XS` | Size filter matches one segment |
| Stock is ≥ 0 | `inventoryQuantity` can be `-1` | Reported as "oversold by 1", never as minus one |
| Product options are Size | Sets have options like `Grey Convict Hoodie (Size)`; socks have `Quantity: 1pc` | Live catalogue takes only Colour values, so `XS`/`1pc`/`V2` never become terms |
| A name search finds the customer | "Noah" returns three other Noahs before the buyer | `find_order` flags ambiguity with the candidates; `find_customer` flags truncation |
| Product names are pronounceable | `CRXST★RZ T-SHIRT`, `MOTIONTEC™️` | Terminology file supports `spoken form => Canonical` aliases; the seed ships with the real catalogue |
| whisper-server takes `vad_filter` | The field is `vad` | Client fixed; VAD was silently off per request |
| A bare term list is the right Whisper prompt | It strips capitals and punctuation from transcripts | Prompt is display-case and ends with a period — measured before and after |
| The Keychain is always reachable | Not from launchd, not on Linux | Provider falls back to the CLI's own login, with a loud warning that launchd needs `setup-token` |

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
