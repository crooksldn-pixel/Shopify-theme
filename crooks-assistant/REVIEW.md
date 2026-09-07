# Review ledger

Eight independent reviewers, one lens each, produced these findings against commit c4d9e64 and
the working tree that followed it. Every finding was triaged by hand against the current tree.
An automated three-refuter verification pass ran alongside; it had returned 11 standing and 39 refuted verdicts out of 50 when this ledger was written, and is not the
basis of the dispositions below — the code is.

**63 findings**: 55 fixed · 2 partly · 4 accepted · 2 open

Status meanings: **fixed** — changed in the named commit, with a test where one was practical;
**partly** — the real part is fixed, the rest is explained; **accepted** — true, and left as a
deliberate trade-off that is written down; **open** — true and not yet done.

| Sev | Lens | Where | Finding | Status | Disposition |
|---|---|---|---|---|---|
| high | agent-sdk | `app/providers/max_agent_sdk.py:177` | ResultMessage.is_error / subtype / errors are ignored: usage-limit, auth and max_turns failures are reported as successful READY turns | **fixed** | result_kind() reads is_error/subtype/api_error_status (f72198f) |
| high | agent-sdk | `app/providers/max_agent_sdk.py:163` | Per-turn state lives on the singleton provider: concurrent turns gate tool calls against the wrong session's issued ids and share one SDK stream | **fixed** | asyncio.Lock serialises turns (f72198f) |
| high | gate-security | `app/providers/max_agent_sdk.py:163` | Provider-wide _current/_calls/_states let overlapping turns cross-contaminate the issued-id ledger and mis-route tool calls | **fixed** | asyncio.Lock serialises turns (f72198f) |
| high | gmail-api | `app/clients/gmail.py:57` | Gmail refresh token and OAuth client_secret are stored in a plaintext file despite the no-secrets-in-files rule | **fixed** | credential can live in the Keychain (gmail_token); token.json 600 remains the plan's fallback (cebccbe) |
| high | ops-reliability | `app/tools/gmail_tools.py:153` | Gmail tools block the event loop and defeat the tool timeout | **fixed** | duplicate of the gmail-api finding (cebccbe) |
| high | ops-reliability | `app/providers/max_agent_sdk.py:203` | A Claude turn has no timeout and holds the global turn lock forever | **fixed** | duplicate (cebccbe) |
| high | ops-reliability | `app/speech/transcribe.py:135` | Stdlib log output is unredacted and unrotated under launchd | **fixed** | duplicate (cebccbe) |
| high | ops-reliability | `app/logging/turnlog.py:57` | Turn-log redaction misses names and street lines, and mangles ids, errnos and season/size codes | **partly** | customer_name/displayName/from keys and GIDs handled (cebccbe); free-text street lines are not detectable by regex — the tools never return full addresses |
| high | plan-conformance | `app/runtime.py:74` | POST /reload-kb reports success but the assistant keeps answering from the old knowledge base | **fixed** | provider.set_system_prompt drops open clients (cebccbe) |
| high | plan-conformance | `app/speech/transcribe.py:135` | Raw spoken transcripts are written verbatim to the unredacted, unrotated stdout log | **fixed** | as above — RedactingFilter (cebccbe) |
| high | speech | `app/clients/whisper.py:62` | Client forces vad=true on every request; a server started without a Silero model then fails every transcription with 500 | **fixed** | falls back to no per-request VAD on a 500 mentioning vad (cebccbe) |
| high | speech | `app/speech/transcribe.py:135` | Full transcripts (customer names, spoken emails/phone numbers) are logged via stdlib logging, bypassing turnlog.redact() | **fixed** | RedactingFilter on all handlers, rotating file log (cebccbe) |
| medium | agent-sdk | `app/tools/dispatch.py:137` | RED calls denied by the PreToolUse hook never appear in tool_calls or the turn log; ResultMessage.permission_denials is discarded | **fixed** | hook events append a failed ToolCall (cebccbe) |
| medium | agent-sdk | `app/providers/max_agent_sdk.py:37` | Billing guard only checks two env vars; the CLI recognises five other credential sources and the init message's apiKeySource/apiProvider are never verified | **fixed** | as above (cebccbe) |
| medium | agent-sdk | `app/providers/max_agent_sdk.py:143` | SDK clients (one `claude` subprocess each) never expire; SessionManager sweeps sessions but not their clients, and id-less requests mint a new subprocess per request | **fixed** | idle-client sweep tied to session timeout (cebccbe) |
| medium | agent-sdk | `app/providers/max_agent_sdk.py:172` | No timeout around the SDK response loop: a stalled CLI pins the request, the session and the shared _current forever | **fixed** | 120 s turn timeout; client dropped on expiry (cebccbe) |
| medium | browser | `web/app.js:152` | speechSynthesis chain survives cancel(): onerror re-arms the next chunk, so stopSpeaking() never actually stops speaking | **fixed** | generation counter (cebccbe) |
| medium | browser | `web/app.js:202` | Release before getUserMedia resolves is lost: mic starts recording after the finger has already lifted | **fixed** | pendingStart guard (cebccbe) |
| medium | browser | `web/app.js:272` | submit() reports any HTTP error as 'lost contact / Backend unreachable' and never checks response.ok | **open** | not addressed in this session |
| medium | browser | `web/app.js:360` | Microphone test's onstop has no error handling; a failed /audio-test leaves the page stuck in LISTENING | **fixed** | try/catch plus WAV playback (cebccbe) |
| medium | gate-security | `app/tools/gate.py:104` | Gate ignores ToolSpec.tier and ToolSpec.issued_id_args; registry tiers are decorative and /tools can misreport them | **fixed** | gate consults registry tier and issued-id args (cebccbe) |
| medium | gate-security | `app/providers/max_agent_sdk.py:37` | Billing guard checks two env names while the SDK subprocess inherits the entire parent environment | **fixed** | guard covers key-helper and Bedrock/Vertex/Foundry; CLI asked for its auth source (cebccbe) |
| medium | gate-security | `app/providers/max_agent_sdk.py:177` | ResultMessage.is_error, subtype and api_error_status are ignored, so failed turns are reported as READY | **fixed** | result_kind() reads is_error/subtype/api_error_status (f72198f) |
| medium | gate-security | `app/tools/dispatch.py:75` | Error-path log lines write model-supplied argument values and Google HttpError URLs (containing the Gmail query) to the process log | **fixed** | RedactingFilter on every log line; Gmail error text drops URLs (cebccbe) |
| medium | gmail-api | `app/tools/gmail_tools.py:153` | Async Gmail tools run blocking googleapiclient I/O on the event loop, so the 8-second timeout cannot fire and the whole backend freezes on a Gmail stall | **fixed** | asyncio.to_thread; cross-references gathered concurrently (cebccbe) |
| medium | gmail-api | `app/tools/gmail_tools.py:167` | gmail_search is a sequential N+1 (1 list + N gets + N Shopify lookups) and will exceed the 8-second tool budget at moderate limits | **fixed** | gets in one thread, Shopify lookups concurrent; result count is the lever (cebccbe) |
| medium | gmail-api | `app/clients/gmail.py:68` | invalid_grant raised inside execute() after start-up is reported as a generic failure and the broken service is never reset | **fixed** | auth failures reset the client and name the fix (cebccbe) |
| medium | gmail-api | `scripts/gmail_auth.py:41` | Re-authorisation does not force prompt=consent and verify() does not check for a refresh_token, so a re-auth can silently produce a one-hour credential | **fixed** | prompt=consent, access_type=offline; refuses a credential without a refresh token (cebccbe) |
| medium | gmail-api | `app/tools/gmail_tools.py:163` | Gmail HttpError text embeds the request URI including the search query, leaking user-typed email addresses into stdout logs and turns.jsonl | **fixed** | _describe() strips URLs and redacts (cebccbe) |
| medium | ops-reliability | `app/runtime.py:65` | Live customer names are written to kb/.catalogue-cache.txt, which is not gitignored | **fixed** | (cebccbe) |
| medium | ops-reliability | `app/main.py:36` | A failed provider start is never retried; the process stays up answering "still starting up" | **fixed** | each /turn retries start() (cebccbe) |
| medium | plan-conformance | `app/main.py:209` | M4 startup assertion is swallowed: a set ANTHROPIC_API_KEY logs an error and the server boots anyway | **fixed** | assert_no_payg_credentials() runs before boot (cebccbe) |
| medium | plan-conformance | `app/tools/shopify_tools.py:518` | Shop-local day bounds discard the end bound, so 'yesterday' cannot be answered and days=2 silently means today+yesterday | **fixed** | days_ago window with both bounds (cebccbe) |
| medium | plan-conformance | `app/routes/turn.py:127` | chat.py REPL does not show tool arguments; /turn strips them from the response | **fixed** | redacted args in tool_calls (cebccbe) |
| medium | plan-conformance | `scripts/acceptance.py:40` | Acceptance harness sends '*(after 3)*' prefixes to the model, runs follow-ups in the wrong order, and auto-passes transcript accuracy | **fixed** | markers stripped; follow-ups run after their referent (cebccbe) |
| medium | plan-conformance | `app/routes/turn.py:109` | Normaliser ambiguities and low-confidence matches are computed then discarded before the agent sees them | **fixed** | ambiguities appended to the model's input (cebccbe) |
| medium | shopify-api | `app/tools/shopify_tools.py:412` | shopify_inventory query exceeds Shopify's 1,000-point single-query cap for any limit >= 10 | **fixed** | MAX_PRODUCTS = 10 (cebccbe) |
| medium | shopify-api | `app/tools/shopify_tools.py:426` | Inventory search 'title:*Yard Jeans*' is parsed by Shopify as 'title:*Yard' AND 'Jeans*', not a title phrase; leading wildcard is undocumented | **fixed** | bare-word search, verified live (cebccbe) |
| medium | shopify-api | `app/tools/dispatch.py:82` | ShopifyError/ShopifyAuthError are not ToolError, so every Shopify failure reaches Claude as 'failed unexpectedly' with the message stripped and a traceback logged | **open** | still surfaces as 'failed unexpectedly' with the message logged; message should be passed through. Low effort, not yet done |
| medium | shopify-api | `tests/test_shopify_tools.py:64` | Two tests in tests/test_shopify_tools.py fail against the working tree's name:1928 change | **fixed** | tests updated to the verified name:1928 syntax (f72198f) |
| medium | shopify-api | `app/runtime.py:67` | Catalogue job persists 50 customer names to an un-ignored file and requests customer emails it never uses; order queries also fetch unused customer emails | **fixed** | customer names no longer cached; cache gitignored (cebccbe) |
| medium | speech | `app/speech/transcribe.py:65` | After the first hourly catalogue refresh the Whisper prompt contains customer names and aliases only — every product name is cut by the 60-term cap | **fixed** | prompt budgeted by characters, live-then-seed order (cebccbe) |
| medium | speech | `app/speech/normalise.py:45` | words_to_digits rewrites conversational "oh"/"one"/"ten two" into digits, damaging correct transcripts | **fixed** | lone number words are left alone (cebccbe) |
| medium | speech | `app/speech/normalise.py:289` | extract_order_numbers reports numbers nobody said and phone-number fragments that then reach turns.jsonl | **fixed** | 3–5 digits, not preceded/followed by digits (cebccbe) |
| medium | speech | `app/clients/whisper.py:74` | Only ConnectError/TimeoutException are caught; a whisper-server crash mid-request turns into an unhandled 500 with no spoken answer | **fixed** | any httpx.HTTPError is a named failure (cebccbe) |
| low | agent-sdk | `app/providers/max_agent_sdk.py:74` | start() hard-requires a `claude` on PATH even though the SDK ships a bundled CLI, so a pip-only install refuses to boot with a misleading message | **accepted** | the plan requires the native CLI; the message names the fix |
| low | agent-sdk | `app/providers/max_agent_sdk.py:153` | No test exercises the provider's SDK integration, so none of the above is caught by the 123-test suite | **fixed** | tests/test_provider.py constructs real ClaudeAgentOptions; live M4/M5 run recorded in bench/results |
| low | browser | `web/app.js:213` | MediaRecorder.onstop closes over mutable globals `chunks` and `mediaRecorder`; a fast re-press discards the previous recording | **accepted** | the button is disabled while busy; a re-press cannot overlap a submit |
| low | browser | `web/app.js:284` | ERROR state is replaced by SPEAKING → READY in the same tick, so error turns never display as errors when speech is on | **fixed** | errors persist after being spoken (cebccbe) |
| low | browser | `app/routes/turn.py:84` | Developer-facing error strings (internal URL, shell command, raw PyAV exception) are shown on the tablet and spoken aloud | **fixed** | WhisperUnavailable.spoken; decode errors reworded (cebccbe) |
| low | browser | `web/app.js:122` | Sentence chunker splits on every '.', so a GBP amount can be cut at the decimal point across two utterances | **fixed** | decimal points excluded (cebccbe) |
| low | gate-security | `app/tools/dispatch.py:22` | Issued-id ledger is a flat untyped set and over-issues every 'id', customer_id and variant_id it sees | **accepted** | ids are only ever those a tool returned; broad issuance is the intended ledger semantics |
| low | gate-security | `app/routes/turn.py:38` | Session ids are caller-chosen and unauthenticated, so the ledger's trust boundary is a guessable client string | **accepted** | single user on a tailnet; documented in README. Revisit if exposure widens |
| low | gmail-api | `app/tools/gmail_tools.py:258` | gmail_read_thread returns the oldest 12 messages of a long thread, dropping the customer's latest reply | **fixed** | newest 12 (cebccbe) |
| low | gmail-api | `app/runtime.py:163` | Sender-controlled From address is interpolated unquoted into a Shopify search where '*' is a wildcard, so a crafted header can mark a stranger as a known customer | **fixed** | email quoted, search syntax stripped (cebccbe) |
| low | ops-reliability | `pyproject.toml:32` | pyproject packages list omits every sub-package: a non-editable install is broken | **fixed** | packages.find (cebccbe) |
| low | ops-reliability | `scripts/doctor.py:127` | doctor mislabels an unavailable keychain as missing secrets and can print two contradictory reports | **fixed** | (cebccbe) |
| low | plan-conformance | `scripts/bench_whisper.py:63` | M2 WAV playback and M3 per-stage bench timings are not delivered | **partly** | playback added (cebccbe); bench reports median wall time per file, not per stage — the server does not expose stage timings |
| low | shopify-api | `app/clients/shopify.py:170` | _partial_errors is set but never read, so protected-customer-data redaction silently surfaces as 'no customer' | **fixed** | surfaced as `partial` in results (cebccbe) |
| low | shopify-api | `app/clients/shopify.py:153` | HTTP-429 branch is dead: Shopify throttling and cost errors arrive as HTTP 200, and sales_summary's 10-page burst can drain the bucket and lose the whole figure | **fixed** | THROTTLED / MAX_COST_EXCEEDED detected in the 200 body (cebccbe) |
| low | shopify-api | `app/tools/shopify_tools.py:571` | sales_summary 'basis' says 'before refunds' but currentTotalPriceSet is the after-returns/refunds figure | **fixed** | wording corrected (cebccbe) |
| low | speech | `app/speech/decode.py:48` | A clipped recording is discarded and the user is told it was "too short" | **fixed** | distinct spoken reason for clipping (cebccbe) |
| low | speech | `scripts/bench_whisper.py:53` | Benchmark measures a different Whisper prompt than production uses | **fixed** | bench uses prompt_terms() (cebccbe) |

## Findings the reviewers were wrong about, briefly

- *A top-level `secrets/` package is missing* — it shadows the stdlib and breaks FastAPI; `app/secrets/` is deliberate.
- *Double Metaphone is not used* — jellyfish removed it in 1.0.
- *`name:#NNNN` should be used for order search* — bare `name:1928` matches both `CROOKS-1928` and legacy `#1036`, verified on the live store.

## Still open, in priority order

- **medium** `web/app.js:272` — submit() reports any HTTP error as 'lost contact / Backend unreachable' and never checks response.ok. not addressed in this session.
- **medium** `app/tools/dispatch.py:82` — ShopifyError/ShopifyAuthError are not ToolError, so every Shopify failure reaches Claude as 'failed unexpectedly' with the message stripped and a traceback logged. still surfaces as 'failed unexpectedly' with the message logged; message should be passed through. Low effort, not yet done.
