# Review ledger

Eight independent reviewers, one lens each, produced these findings against commit c4d9e64 and
the working tree that followed it. Every finding was triaged by hand against the current tree.
An automated three-refuter verification pass ran alongside; it had returned 11 standing and 39 refuted verdicts out of 50 when this ledger was written, and is not the
basis of the dispositions below — the code is.

**71 findings**: 65 fixed · 2 partly · 4 accepted · 0 open

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
| high | speech | `app/clients/whisper.py:62` | Client forces vad=true on every request; a server started without a Silero model then fails every transcription with 500 | **fixed** | first fix (cebccbe) keyed on a body that never says "vad" and never fired — the review's synthesis reproduced that; now any 500 while VAD is on gets one retry without it, the launcher refuses to start without a VAD model, and /health transcribes half a second of silence so "ok" means inference works (this commit) |
| high | speech | `app/speech/transcribe.py:135` | Full transcripts (customer names, spoken emails/phone numbers) are logged via stdlib logging, bypassing turnlog.redact() | **fixed** | RedactingFilter on all handlers, rotating file log (cebccbe) |
| medium | agent-sdk | `app/tools/dispatch.py:137` | RED calls denied by the PreToolUse hook never appear in tool_calls or the turn log; ResultMessage.permission_denials is discarded | **fixed** | hook events append a failed ToolCall (cebccbe) |
| medium | agent-sdk | `app/providers/max_agent_sdk.py:37` | Billing guard only checks two env vars; the CLI recognises five other credential sources and the init message's apiKeySource/apiProvider are never verified | **fixed** | as above (cebccbe) |
| medium | agent-sdk | `app/providers/max_agent_sdk.py:143` | SDK clients (one `claude` subprocess each) never expire; SessionManager sweeps sessions but not their clients, and id-less requests mint a new subprocess per request | **fixed** | idle-client sweep tied to session timeout (cebccbe) |
| medium | agent-sdk | `app/providers/max_agent_sdk.py:172` | No timeout around the SDK response loop: a stalled CLI pins the request, the session and the shared _current forever | **fixed** | 120 s turn timeout; client dropped on expiry (cebccbe) |
| medium | browser | `web/app.js:152` | speechSynthesis chain survives cancel(): onerror re-arms the next chunk, so stopSpeaking() never actually stops speaking | **fixed** | generation counter (cebccbe) |
| medium | browser | `web/app.js:202` | Release before getUserMedia resolves is lost: mic starts recording after the finger has already lifted | **fixed** | pendingStart guard (cebccbe) |
| medium | browser | `web/app.js:272` | submit() reports any HTTP error as 'lost contact / Backend unreachable' and never checks response.ok | **fixed** | response.ok is checked and the status shown (cebccbe) |
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
| medium | shopify-api | `app/tools/dispatch.py:82` | ShopifyError/ShopifyAuthError are not ToolError, so every Shopify failure reaches Claude as 'failed unexpectedly' with the message stripped and a traceback logged | **fixed** | client errors (Shopify, Gmail, whisper) reach the model with their spoken message intact (e3fda21+) |
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

| high | council (outsider) | `app/kb/loader.py:38` | Editing instructions and open questions in kb/*.md reached the model's system prompt | **fixed** | loader strips HTML comments; discretion section tells the model to defer; regression test over the shipped kb (cd0d567) |
| medium | council (executor) | `README.md` | `claude /login` written as a shell command; policy files described as still unwritten; test count stale | **fixed** | corrected from the tree and from pytest output (cd0d567, this commit) |
| medium | council (contrarian) | `app/clients/shopify.py:136` | Read-only rested on the scope list alone; no mutation refusal in the client; RED tools in allowed_tools | **fixed** | client refuses mutation documents; RED tools in disallowed_tools; both tested (e3fda21) |

| high | synthesis | `app/logging/turnlog.py:69` | Customer names inside the spoken answer and transcript reached turns.jsonl; errnos, filenames and size codes were mangled by the shape regexes | **fixed** | names tool results exposed are remembered per session and scrubbed from free text; identifiers protected; postcode regex excludes size codes; tests reproduce each case (this commit) |
| medium | synthesis | `app/providers/max_agent_sdk.py:233` | Post-connect auth-source check read `apiKeySource` at the top level; the CLI nests it under `account`, so the check was inert | **fixed** | reads the nested account block (this commit) |
| medium | synthesis | `app/clients/gmail.py:59` | Keychain failure fell back to writing the credential to a file silently | **fixed** | the fallback logs a warning naming the exception and the file (this commit) |
| medium | synthesis | `README.md`, `app/secrets/keychain.py` | Keychain reachability under launchd stated three contradictory ways | **fixed** | a LaunchAgent runs in the login session and reaches the Keychain; SSH, system daemons and pre-login do not — stated the same way everywhere (this commit) |
| low | synthesis | `app/tools/gate.py:125` | The issued-id ledger is untyped: a Customer gid passed the gate as an order_id | **fixed** | each detail tool checks its argument is the right kind of id (this commit) |

## Findings the reviewers were wrong about, briefly

- *A top-level `secrets/` package is missing* — it shadows the stdlib and breaks FastAPI; `app/secrets/` is deliberate.
- *Double Metaphone is not used* — jellyfish removed it in 1.0.
- *`name:#NNNN` should be used for order search* — bare `name:1928` matches both `CROOKS-1928` and legacy `#1036`, verified on the live store.

## The refuter pass

Three independent refuters (one for low severity) were asked to disprove each finding. 11 verdicts stood; 50 were refuted. The standing verdicts, in the refuters' own words, with the disposition each maps to:

- Confirmed in source. app/clients/gmail.py:57-58 and scripts/gmail_auth.py:43-44 write creds.to_json() to REPO_ROOT/token.json (gmail.py:18-20); credentials.json is also kept there (gmail.py:19). The installed Credentials.to_json() serialises token, refresh_tok… *(severity: keep)* — covered by the matching **fixed** row above.
- Confirmed against the source and the installed library. app/clients/gmail.py:20 sets TOKEN_PATH = REPO_ROOT / "token.json"; gmail.py:57 and scripts/gmail_auth.py:43 both call TOKEN_PATH.write_text(creds.to_json(), ...), and gmail.py:45 reads it back with Crede… *(severity: keep)* — covered by the matching **fixed** row above.
- The factual core of the claim checks out and I could not refute it. app/clients/gmail.py:57 and scripts/gmail_auth.py:43 both call `TOKEN_PATH.write_text(creds.to_json(), ...)` with TOKEN_PATH = REPO_ROOT/token.json (gmail.py:18-20). I read google.oauth2.crede… *(severity: lower)* — covered by the matching **fixed** row above.
- Confirmed against /home/user/Shopify-theme/crooks-assistant/web/app.js. stopSpeaking() (line 118) is a bare speechSynthesis.cancel() with no generation/ownership tracking; speak() (lines 145-154) chains chunks with `utterance.onend = next; utterance.onerror = … *(severity: keep)* — covered by the matching **fixed** row above.
- Confirmed from /home/user/Shopify-theme/crooks-assistant/web/app.js. The chain only ever has one utterance queued at a time: `next()` (lines 145-154) creates chunk N and enqueues chunk N+1 solely from that chunk's `onend`/`onerror`, and both handlers are the s… *(severity: keep)* — covered by the matching **fixed** row above.
- Confirmed in web/app.js. stopSpeaking() (117-119) is a bare speechSynthesis.cancel(); the chain closure `next` (145-154) is re-armed on both onend and onerror (151-152) with no generation/abort guard, so the spec-mandated error event ('interrupted') on the can… *(severity: keep)* — covered by the matching **fixed** row above.
- Confirmed against the actual sources. app/clients/whisper.py:62 sends `"vad": "true"` unconditionally on every /inference call, and the comment at lines 59-60 claims this makes "a mis-started server still filter". scripts/whisper_server.py:58-59 only prints a … *(severity: lower)* — covered by the matching **fixed** row above.
- The claim stands; I confirmed it in source and empirically, not just by reading. Source check (whisper.cpp checkout at scratchpad/tools/whisper.cpp, commit 52a939a): examples/server/server.cpp:594-596 copies the `vad` form field into params.vad; :968-969 sets … *(severity: lower)* — covered by the matching **fixed** row above.
- Confirmed in source. app/runtime.py:77-79 reload_kb() only reassigns self.kb; the provider is constructed once at runtime.py:111-112 with build_system_prompt(kb). In app/providers/max_agent_sdk.py the prompt is stored at line 76 and read only in _options() at … *(severity: keep)* — covered by the matching **fixed** row above.
- Reproduced end to end, not just traced. A whisper-server was built in the scratchpad (/tmp/claude-0/-home-user-Shopify-theme/d1718050-649b-5a97-8172-d7d22b2cb490/scratchpad/tools/whisper.cpp, commit 52a939a, build/bin/whisper-server present). Started it with e… *(severity: lower)* — covered by the matching **fixed** row above.
- Confirmed against the source. app/runtime.py:77-79 `reload_kb()` only does `self.kb = load(self.settings.kb_dir)`; the provider is constructed once at runtime.py:111-117 with `system_prompt=build_system_prompt(kb)` and is never touched again. In app/providers/… *(severity: keep)* — covered by the matching **fixed** row above.

A refuted verdict does not by itself close a finding here; several refuted findings were fixed anyway because the fix was cheap and the failure real on the Mac even if not on Linux.

## Still open

Nothing. The four accepted items are trade-offs, written down above, not omissions. Session-id authentication is one of them: on a single-user tailnet the trust is in Tailscale; if the backend is ever exposed more widely, add a shared token before anything else.

## Council pass C — the read layer, working sets, batches, observability intelligence

Five advisors (executor, outsider, first-principles, contrarian, expansionist), five peer
reviewers, one chairman; every finding read against the code before anything changed. Held
by `tests/test_council_fixes.py`.

Confirmed and fixed:
- The order cache's page (forty orders with a dozen line items) would have cost ~3,600
  points against Shopify's 1,000-point cap per query and been refused on the live store:
  eight orders of ten items a page now, halved when Shopify says a page is too expensive,
  paced on the bucket Shopify reports, one order per id re-read (`app/analytics/cache.py`).
- A batch member could expire on the card's clock while the batch was still applying it,
  and a word spoken mid-run withdrew every member not yet reached: the claim now freezes the
  members' clocks and the engine leaves a running batch's members alone
  (`app/actions/engine.py`, `app/actions/batch.py`).
- The undo batch was staged at a stale position after a mid-run turn, and its members were
  ordinary proposals for a moment: born as batch members now, staged at the current position.
- Fifty courtesy order reads per batch and no pacing: skipped for a batch; the run waits for
  the bucket by Shopify's own refill figures.
- The tablet gave up on a batch at thirty seconds and the state route lost the count and the
  undo: two minutes, polling while it runs, and the state carries both.
- After a batch the cache dropped up to thirty of fifty orders for five minutes and called
  itself complete: stale rows are kept, re-read in full across syncs, and the view says so;
  a walk or a delta that stops at its page bound is reported partial.
- "This week" was compared with the whole of last week; order-level refunds and unfulfilled
  value were folded into every product bucket: compared to the same point now, money is
  the line's own, a shared refund is derived, the basis is named.
- FALSE_UNSUPPORTED fired when the tool had run and found nothing; the model was never told a
  batch's outcome; "these" drifted to a derived set after the inbox read; drafts were counted
  per customer for a per-order plan; three denominators on one change; sets issued every
  member's id; the inbox read kicked a year's backfill and dropped unheld members silently.
  All changed as the tests say.

Findings the reviewers showed to be wrong, not acted on: the DST week (same-zone
subtraction is wall-clock); `_PERIOD_DESC` lacking `last_90_days` (only the prompt lacked it);
"the report forces failed" (only with no tool having run); "the page retries blind" (it
sleeps Shopify's own wait).

Clashes, settled: a set holds every match, except when the model asked for a number, when
it is exactly those rows (the owner said "the five oldest"). The pre-turn capability hint
ships, and a decline after it is counted apart from an unaided one.

Still open (proposals, not changes): chips on the working-set card ("Tag all of these"),
catalogue examples generated from the claims map, a morning brief from the cache, a ledger
replay after a Mac restart mid-batch, per-turn bounds for the inbox read and batch staging,
refunds by the date they were made, and bulk versions of refund, cancel, fulfilment and stock
once the first three batches have proved themselves on the tablet.

First thing to run on the Mac: one order page against the live store and read
`extensions.cost.requestedQueryCost`; the page size is right when that number is under a
thousand with room to spare.
