# CROOKS Assistant

A voice assistant for CROOKS LDN. You hold a button on a tablet, ask a question out loud, and it
answers out loud — reading from the Shopify store and the email inbox, and never writing to
either.

Everything runs on your own Mac bar one thing. No database, no monthly cost beyond the ones you
already have. Claude is reached through the Agent SDK on the Claude Max subscription;
speech-to-text is ElevenLabs Scribe v2, with whisper.cpp on this Mac as the automatic fallback
whenever ElevenLabs cannot answer; the answer is spoken back by Derek, an ElevenLabs voice
generated on this Mac, with the tablet's own Android voice as that fallback.

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
| Install | `make venv` then `make test` | Expect 344 passed |
| Run it | `make dev` | In a second Terminal tab: `tailscale serve 8000` |
| Speech | `make whisper-server` | It prints the build steps the first time |
| Tokens and keys | `make secrets` | Asks for the Claude token, Client ID, Client secret and ElevenLabs key, one at a time, hidden |
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

2. **whisper.cpp** (M3) — the fallback recogniser, and still required: it is what answers when
   ElevenLabs cannot. `make whisper-server` prints the exact build commands if it is not built
   yet. On the M4 Max the working configuration is `large-v3-turbo` on a build made with
   `-DWHISPER_COREML=OFF` (Metal only): the Core ML path crashed on models without a matching
   encoder, and Metal alone is fast enough. Put `CROOKS_WHISPER_MODEL=large-v3-turbo` in `.env`
   so plain `make whisper-server` starts the right model. A Silero VAD model must be present;
   the launcher refuses to start without one, because a server without it rejects every
   request that asks for voice detection while the tablet still says "connected".

3. **ElevenLabs** — `make secrets` and paste the API key at the hidden prompt (a key scoped to
   speech-to-text is enough; `/health` says "quota unreadable (restricted key)" for one of
   those, which is not a fault). Nothing else is needed: Scribe becomes the recogniser and
   whisper.cpp becomes the fallback. Without a key the assistant listens entirely locally, as
   it did before — set `CROOKS_STT_PRIMARY=whisper` to choose that on purpose.

4. **Claude token** (M4) — run `claude` and sign in with `/login` if you have not, then `claude setup-token`, then
   `make secrets` and paste it at the hidden prompt.
   **The token expires after one year — diary a reminder for month eleven.**

5. **Shopify** (M6) — check the store is listed under Stores in the Dev Dashboard organisation
   *first*; if it is not, client credentials fail permanently with `shop_not_permitted` and the
   `shpat_` fallback is the way out. Scopes are in `SHOPIFY_SCOPES.md`. Then `make secrets`
   for the Client ID and secret, and `make shopify` to prove it. You do not need to find the
   Stores list first: `make shopify` either works or names `shop_not_permitted`, which is the
   same answer in ten seconds.

6. **Gmail** (M8) — Google Cloud project → enable the Gmail API → Branding → Audience: External
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

## Running it day to day

Three things stay running, each in its own Terminal tab, in this order:

```bash
cd ~/crooks-assistant/crooks-assistant && make dev              # backend
cd ~/crooks-assistant/crooks-assistant && make whisper-server   # speech (model from .env)
tailscale serve 8000                                            # HTTPS for the tablet
```

Then open the ts.net address on the tablet. Hold the button, speak, release. The microphone
stays open while the page is showing, so the first word is not lost to start-up; it is
released when the page is hidden and reopened when it returns.

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
        ElevenLabs Scribe v2             Claude Agent SDK        knowledge base
       ↳ whisper.cpp fallback            (Max subscription)         (system prompt)
          (local, port 8910)
        ElevenLabs TTS (Derek)
       ↳ Android voice fallback
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

### Hearing you

Two recognisers, one job. Every recording is decoded and level-checked here first — silence and
distortion never reach a paid API — then sent to **ElevenLabs Scribe v2**, biased with keyterms
drawn from the same live Shopify catalogue that biases Whisper's prompt. Product words only:
customer names correct transcripts on this Mac and are held back from anything that leaves it.

Every way Scribe can fail — no key, a rejected key, no credit, a timeout, no network, a reply
that is not a transcript — falls through to **whisper.cpp** on port 8910 and the speaker is
never told. What comes back from either engine goes through the same hallucination blocklist,
the same CROOKS normaliser, the same order-number and ambiguity handling as before. A rejected
key or an exhausted account also opens a five-minute cooldown, so a broken account costs one
round trip rather than one per sentence.

Before any of that, the recording has to be worth transcribing: at least 0.3 s long, above the
noise floor, and not distorted. Distortion is measured as the *proportion* of samples sitting on
the rail, never the single highest one — a plosive or a knock on the desk reaches full scale in a
recording that is perfectly intelligible, and gating on the peak refused a third of everything
the tablet ever recorded. `clipped_ratio` and `clipped_ms` are in the stats and on the
`/audio-test` page, so a rejection can be argued with rather than guessed at.

Correction is deliberately conservative, because a wrong correction turns a transcript the
recogniser got right into a wrong answer. Ordinary English is never corrected towards a
catalogue term — the live catalogue contributes the store's colour options as one-word terms,
and "what" is one character-pair away from "White", "back" from "Black", "and" from "Sand". A
short one-word term needs near-exact evidence; an equal phonetic code corroborates a match but
can never invent one; and a match may not swallow an ordinary word at its edge. Anything below
that bar keeps the words as spoken.

Which engine actually answered is in the turn log and in the console (`recognised via scribe_v2
in 1413ms`), and `/health` carries a `speech` block naming the primary, the effective recogniser
and how many Scribe attempts have succeeded. Scribe being down is `degraded`, never dead: the
Mac still hears you. `CROOKS_STT_PRIMARY=whisper` turns Scribe off entirely.

### Answering you

The answer text is on the tablet's screen the moment the agent finishes. Only then does the
tablet post it to `/speak`, which is a separate request for exactly that reason: making `/turn`
wait for an MP3 would delay the thing that matters for the sake of the thing that does not.

`/speak` sends the text to **ElevenLabs** — voice *Derek*, model `eleven_flash_v2_5`, format
`mp3_44100_128` — and forwards the MP3 to the tablet as it arrives, so the audio is not copied
into memory on the Mac before it starts moving. The tablet plays it through one `<audio>`
element that lives for the life of the page. The ElevenLabs key never leaves this Mac: the
tablet sends text and receives audio, and `tests/test_web.py` reads every file in `web/` to
prove no credential, key header or ElevenLabs URL is served to the browser.

Before the text is sent it passes through `app/speech/speakable.py`, which is deliberately
small. The system prompt already asks Claude for spoken-shaped answers; this is the safety net
for the two things a synthesiser reliably gets wrong here — `£430.50` becomes "four hundred and
thirty pounds fifty", `order #1930` becomes "order nineteen thirty" — plus the removal of
markdown, links and HTML. It never rewrites what the answer says.

Every way ElevenLabs can fail is a 503 with a short reason, and the tablet reads that as "use
your own voice", not as "say nothing": a bad key, no credit, a timeout, an empty body, or a
player that will not play all end in Android's speechSynthesis with the reason in the console.
A rejected key or an exhausted account opens the same five-minute cooldown Scribe uses. A
broken voice never breaks a turn — Shopify, Gmail and Claude do not depend on it.

Holding the talk button stops Derek before the microphone opens, so the assistant can never be
recorded answering itself, and a new answer cancels the previous one's request and playback.
`/health` carries a `voice` block and a `tts` check naming the voice, the model and the last
request's latency and size; it is a key and configuration check only, because a health page
that synthesises a sentence every fifteen seconds is a bill rather than a check.

### Layout

```
app/
  main.py            FastAPI app; loopback only
  runtime.py         composition root — everything is wired here
  routes/            health · turn · speak · admin
  providers/         base.py (ABC) · max_agent_sdk.py · anthropic_api.py (stub, deliberately)
  tools/             registry · gate · dispatch · shopify_tools · gmail_tools · mock
  clients/           shopify · gmail · whisper · elevenlabs (Scribe) · elevenlabs_tts (Derek)
  speech/            decode · transcribe · normalise · speakable (text for a mouth)
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
