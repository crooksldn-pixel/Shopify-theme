# CLAUDE OUTBOX — latest handoff only

## 2026-09-19T16:25Z — Reconciliation: Linux migration/runtime prerequisite state (read-only)

**Inbox consumed:** yes. Blob SHA processed: `2b7bd0d67973f8e3b09315c73c650240dc9195c4`
(`bridge/chatgpt-inbox.md`, heading "2026-09-19 — Reconcile Linux migration/runtime prerequisite
state"). These instructions are now recorded as executed and must not be run again.

**Verdict up front.** The Linux migration candidate `1cf3a0f` **is already installed and running as
production** on `crooks-os-prod-1`: the production checkout is byte-identical to the candidate,
`crooks-assistant.service` is enabled and active on `127.0.0.1:8000`, and Tailscale Serve exposes it
as tailnet-only HTTPS. All of this was done **by the owner, in a root SSH terminal session, between
06:18Z and 06:31Z on 2026-09-19**, via the documented `make install` path. **No bridge inbox
authorised it and canonical Git still says the opposite** (production branch "remains
`claude/crooks-assistant-build-lgxlau`", "not silently moved", private HTTPS "when approved"). The
promotion is therefore *observed and owner-performed but not canonically ratified*. The
write-safety baseline is proven off. One runtime gap is real: **no Gmail token is provisioned**, so
`/health` reports `degraded`. One owner-only decision is needed (§9). Nothing was changed this round.

---

## 1. What was asked

A bounded, read-only reconciliation of the Linux production/runtime state against canonical product
memory (`claude/product-memory-foundation`), the migration candidate `1cf3a0f`, and the latest
outbox, producing eight observations, a satisfied/not-satisfied verdict on DEC-046's Linux/runtime
prerequisites, any provenance contradiction, the smallest safe next step, and any owner-only
decision. No Orchestrator implementation, no promotion, no service/Tailscale/secret/permission
change, no Builder modification.

## 2. Evidence sources and commands used (all read-only)

- Git: `git branch/rev-parse/status/diff --stat/reflog/stash list/for-each-ref/ls-remote/worktree list/log/show/cat-file` on `/opt/crooks-os` (production, git root), `/opt/crooks-review`, `/opt/crooks-watcher-review`, `/opt/crooks-builder`, `/opt/crooks-ai-bridge`. One shallow `git clone --depth 1` of `claude/product-memory-foundation` into `/tmp/pmf-scratch` (remote head `fe3ffa5f`, newer than the builder's stale remote-tracking ref `b5c94fd`), read, then deleted. No fetch into any existing repo.
- systemd: `systemctl list-unit-files/is-enabled/is-active/show` (selected properties), unit file read with every `Environment=` value redacted, `journalctl -u crooks-assistant`, `-u tailscaled`, `-u crooks-bridge-watcher`, `_COMM=sshd`, `--list-boots`.
- Process: `/proc/217827/{cmdline,exe,cwd,status,environ (names only),fd}`, `ps`.
- Network: `ss -ltnp`, `nft list ruleset`, `ufw status`.
- Tailscale (no mutation): `tailscale status`, `serve status`, `funnel status`, `ip`, `version`, `debug prefs` (exposure keys only); cert file metadata and `openssl x509 -noout -subject -issuer -dates` on the public certificate.
- Application: `GET http://127.0.0.1:8000/health` and `GET https://crooks-os-prod-1.taildfb357.ts.net/health` from the host itself (reads).
- Files: `stat`/`ls`/`find` metadata on `/etc/crooks-os/**` (names, sizes, modes, mtimes only), `/etc/systemd/system/crooks-*`, the checkout, `.venv`, `logs/`.
- Config: `.env` key **names** listed; values printed only for `CROOKS_WRITES_ENABLED`, `CROOKS_WRITES_LOCAL_OWNER`, `CROOKS_HOST`, `CROOKS_PORT`, `CROOKS_WHISPER_ENABLED`, `CROOKS_SHOPIFY_AUTH_MODE`, `CROOKS_CLAUDE_MODEL`, and three record/capture flags. `CROOKS_ALLOWED_LOGINS` reported by length only.
- `/root/.bash_history` read with secret-bearing arguments masked; it has no timestamps (ordering only).
- Bridge history: every prior inbox and outbox version grepped for install/Tailscale/promotion/approval language.

No secret value was read into this handoff. The service's decrypted credential directory is in its private mount namespace and is not visible from outside it (confirmed: `ls /run/credentials/crooks-assistant.service` → no such directory from the host).

## 3. The eight required observations

### 3.1 Production checkout identity and bytes

| Item | Observed |
|---|---|
| Git root | `/opt/crooks-os` (the application lives in `crooks-assistant/` under it) |
| Branch | `claude/linux-prod-migration-production` (local only; **not on origin**) |
| HEAD | `1cf3a0f3361b79f9de208d80f501543c53c244b5` |
| Upstream | `origin/claude/linux-prod-migration-review` (set by `git switch -c … origin/…-review`) |
| `git status --porcelain` | empty; only ignored files present (`.env`, `.venv`, caches, `__pycache__`) |
| `git diff --stat 1cf3a0f` (working tree vs candidate) | **empty — tracked bytes identical** |
| `git diff --stat 1cf3a0f HEAD` | empty |
| Files modified after service start (excl. venv/caches/logs) | only `kb/.catalogue-cache.txt` (a runtime cache the unit lists as writable) |
| Registered worktrees | `/opt/crooks-os` @1cf3a0f prod; `/opt/crooks-review` @1cf3a0f review (clean); `/opt/crooks-watcher-review` @5ada7b4 |
| `origin/claude/linux-prod-migration-review` via `ls-remote` | `1cf3a0f` — matches |

Candidate commit: author/committer "CROOKS OS Bridge", 2026-09-18 21:38:09Z, parent `e43aecd` (the Phase 5 baseline), 25 files, +2411/−91; message ends "Nothing here has been installed or started."

### 3.2 `crooks-assistant.service` identity and configuration

| Property | Value |
|---|---|
| FragmentPath | `/etc/systemd/system/crooks-assistant.service` (mtime 2026-09-19 06:30:09Z, root:root 644) |
| DropIns | none |
| UnitFileState / preset | enabled / enabled; wants-symlink created 06:30:10Z |
| ActiveState / SubState | active / running; `NRestarts=0` |
| ActiveEnterTimestamp | 2026-09-19 06:30:10 UTC |
| WorkingDirectory | `/opt/crooks-os/crooks-assistant` |
| ExecStart | `/opt/crooks-os/crooks-assistant/.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000` |
| User | root (unit has no `User=`; documented as temporary) |
| Environment= | 4 lines present; values redacted (template names them `HOME`, `PATH`, `CROOKS_CLAUDE_CLI_PATH`, plus one more) |
| LoadCredentialEncrypted | `shopify_client_id`, `shopify_client_secret`, `elevenlabs_api_key` from `/etc/crooks-os/credentials/*.cred` |
| Hardening | `ProtectSystem=strict`, `NoNewPrivileges`, `PrivateTmp`, kernel protections, `ProtectHome=no`, `ReadWritePaths=` checkout, `/root`, `-/etc/crooks-os/secrets` |
| Restart | always, 10s; `StartLimitIntervalSec=300`/`Burst=5` in `[Unit]` |
| After | `network-online.target tailscaled.service` |

**The installed unit is the candidate's template `deploy/systemd/crooks-assistant.service` with its `{{ROOT}}/{{PYTHON}}/{{HOST}}/{{PORT}}/{{CREDENTIALS}}/{{HOME}}/{{SECRET_DIR}}` placeholders filled.** A redacted diff shows no other difference.

### 3.3 Running process, venv, command, port

- MainPID 217827, started 2026-09-19 06:30:10Z, uid 0, `cmdline` exactly the ExecStart above, `cwd` = the checkout, `exe` → `/usr/bin/python3.12` (the `.venv` interpreter symlink; venv created 2026-09-18 15:31Z, Python 3.12.3).
- The venv's editable install maps `app` and `config` to `/opt/crooks-os/crooks-assistant/{app,config}` — the process imports the production checkout, not a copy.
- Open fd 13 → `/opt/crooks-os/crooks-assistant/logs/assistant.log`. Process env contains `CREDENTIALS_DIRECTORY`, `CROOKS_CLAUDE_CLI_PATH`, `HOME`, `PATH` (names only inspected).
- Child process: one `claude` CLI (Agent SDK, `auth=cli`, model `sonnet`) started 06:32:06Z.
- `/health` reports `build ad6c7abf1333`, `uptime_s 35480` (consistent with 06:30Z start), Shopify/Scribe/TTS/Claude ok.
- **Listeners:** `127.0.0.1:8000` (python 217827) — loopback only. Others: sshd 22 (all interfaces), systemd-resolved 53 (loopback), tailscaled 443 + two ephemeral ports on `100.72.82.24` / `fd7a:115c:a1e0::352b:5219` only. Nothing on `0.0.0.0:8000`.
- Firewall: ufw inactive; nftables has only Tailscale's own `ts-input`/`ts-forward` chains, INPUT policy accept. Port 8000 is unreachable from outside because it is bound to loopback, not because of a filter.

### 3.4 Provenance: how production became clean at `1cf3a0f` and how the service was installed

Reconstructed from reflog, journal, file mtimes and the (untimestamped) root shell history, cross-dated by the timestamped sources. All times UTC.

| When | Evidence | Event |
|---|---|---|
| 2026-09-18 15:24:38 | reflog | `/opt/crooks-os` cloned from `crooksldn-pixel/Shopify-theme` at `e43aecd`, branch `claude/crooks-assistant-build-lgxlau` |
| 09-18 21:35–21:38 | branch reflog, review worktree reflog, outbox `05492e7` | review branch created from `e43aecd`; `1cf3a0f` committed in `/opt/crooks-review`; pushed. Outbox recorded "NOT installed, inactive; no serve config" |
| 09-18 22:31 / 22:41 | journal | bridge watcher installed/reinstalled (session 49). Not the assistant. |
| 09-18 22:42 and 23:5x | outboxes `1683ac6`, `97c086a` | production still dirty (migration files in working tree), `crooks-assistant.service` not-found/inactive |
| 09-19 06:18:42 | sshd journal | root public-key SSH login → session 120 |
| 06:23:05 | reflog "reset: moving to HEAD"; `git stash list` | `git stash push -u -m "pre-linux-promotion verified exact match"` on the old branch. History shows a per-file `cmp` loop against the review branch immediately before it. |
| 06:23:52 | reflog, branch reflog | `git switch -c claude/linux-prod-migration-production origin/claude/linux-prod-migration-review` → HEAD `1cf3a0f` |
| 06:27–06:29 | mtimes under `/etc/crooks-os/` | `make secrets` (`provision_secrets.py`): `shopify_client_id.cred`, `shopify_client_secret.cred` (06:27), `elevenlabs_api_key.cred` (06:29), `secrets/media_signing_key` (06:29, 64 bytes) |
| 06:30:09–06:30:10 | unit mtime; two `daemon-reload` from session 120; wants-symlink mtime; journal "Started" | `make install` (`install_systemd.py`): unit rendered, daemon-reload, enable, restart |
| 06:30:10 | tailscaled journal `localapi POST /serve-config`, "creating a new proxy handler for http://127.0.0.1:8000" | `ensure_serve()` ran `tailscale serve --bg 8000` as part of the same `make install` |
| 06:30:44 → 06:31:20 | tailscaled journal | first ACME order invalid, retry succeeded: "got cert" |
| 06:31:20 onward | assistant journal | first requests from the iPhone (`100.67.4.67`): `GET /`, `/branches`, `/turn`, `/speak`, transcription |
| 06:32:06 | ps | Claude CLI child spawned |

Shell history order (lines 39–51): `make status` → `git fetch … review && git diff --stat` → three per-file cmp loops → `git stash push -u` → `git switch` (the first switch to the review branch necessarily failed because `/opt/crooks-review` already holds it, hence the `-c` production branch on the next line) → `git status && rev-parse HEAD` → `make doctor` → `make secrets` → `make install`. This matches the documented Install sequence in `docs/DEPLOY_LINUX.md` exactly.

**Bridge involvement: none.** No inbox exists between `0c7474b` (09-18 22:46Z) and `165c366` (09-19 02:18Z) and the next is `8416f13` (11:40Z); every inbox before and after says "do not install/start services, change Tailscale, provision secrets". The install was owner-operated at the terminal.

**Stash check:** `stash@{0}` (on `claude/crooks-assistant-build-lgxlau`, parent `e43aecd`) plus its untracked commit `stash@{0}^3` are blob-for-blob identical to `1cf3a0f` for all 25 files. The owner's "verified exact match" label is accurate. The stash is a leftover, reproducible from the candidate.

Nothing above is invented; where a step has only shell-history evidence its timing is inferred from the adjacent timestamped events and is stated as such.

### 3.5 Tailscale / private HTTPS state, and canonical approval

- `tailscaled` 1.102.4 enabled/active. Node `crooks-os-prod-1` = `100.72.82.24` / `fd7a:115c:a1e0::352b:5219`. Tailnet peers: `crooks-assistant` (macOS, offline, last seen 9 min ago), `galaxy-tab-a-8` (android, offline, last seen 5 days ago), `iphone183` (iOS, online). All under the same user.
- `tailscale serve status`: `https://crooks-os-prod-1.taildfb357.ts.net (tailnet only) → / proxy http://127.0.0.1:8000`. **Funnel not enabled** (funnel status shows the same tailnet-only entry; ACME log says "Funnel is not enabled").
- Prefs: `ShieldsUp=false`, `RunSSH=false`, `AdvertiseRoutes=null`, no exit node.
- Certificate: `CN=crooks-os-prod-1.taildfb357.ts.net`, Let's Encrypt, valid 2026-09-19 05:32Z → 2026-12-18 05:32Z; key file 0600 root.
- Live check from the host: `GET https://crooks-os-prod-1.taildfb357.ts.net/health` → HTTP 200, TLS verified (`ssl_verify_result=0`), remote `100.72.82.24`.
- **Canonical Git approval: none found.** `DECISIONS.md:211` approves the *direction* ("FastAPI should bind loopback by default and be accessed through private Tailscale HTTPS"); DEC-046, `ROADMAP.md` N1 and `CURRENT_TRUTH.md` step 5 all say "enable private Tailscale HTTPS **when approved**"; every bridge inbox to date says "do not activate Tailscale Serve"; DEC-047 explicitly does not approve deployment or promotion. The route was activated as a side effect of the owner's `make install`, which `DEPLOY_LINUX.md` documents as "unit, enable, start, Tailscale route, /health".

### 3.6 Write-safety baseline (no secret values used)

| Layer | Evidence | State |
|---|---|---|
| `.env` (0600, mtime 2026-09-18 20:52Z, before promotion) | `CROOKS_WRITES_ENABLED=false`, `CROOKS_WRITES_LOCAL_OWNER=false` | off |
| Code defaults | `config/settings.py`: `writes_enabled: bool = False`, `writes_local_owner: bool = False` | off |
| Running process | `/health` → `writes: {state: disabled, detail: "disabled — CROOKS_WRITES_ENABLED=false"}`; all 18 write capabilities `disabled` | off |
| Runtime behaviour | journal 08:08:55Z and 16:03:51Z: "change proposed but a tap would be refused: writes_disabled … writes=disabled"; 16:03:51Z five "refused: product … was not issued to this conversation" | enforced |
| Capability manifest `logs/capabilities.json` | `"writes_enabled": false, "writes": [], "batches": []` | off |

**Proven satisfied.** FastAPI bound to `127.0.0.1` by `.env` (`CROOKS_HOST=127.0.0.1`, `CROOKS_PORT=8000`), by the unit's ExecStart, and by `ss`.

### 3.7 Observed runtime vs candidate/review evidence — remaining gaps

Canonical review proof for `1cf3a0f` (MIGRATION_HANDOFF §3, outbox `05492e7`): 2886 passed / 8 skipped / 2 deselected, Ruff clean, `systemd-analyze verify` clean — produced in `/opt/crooks-review` on 09-18. Observed runtime matches that candidate byte-for-byte and the installed unit matches its template. Gaps that remain before "promotion complete" can honestly be claimed:

1. **Not ratified in canonical Git** (§4 contradiction). This is the blocking gap.
2. **Gmail token absent.** `/etc/crooks-os/secrets/` holds only `media_signing_key`; `/health` `gmail.ok=false` "No Gmail token stored", overall `status: degraded`. Gmail reads and every email family are non-functional on Linux. Provisioning needs the owner's browser OAuth (`scripts/gmail_auth.py`).
3. **`CROOKS_ALLOWED_LOGINS` is empty** (length 1 = blank). Startup warning: "any tailnet login may ask (reads only; changes need the allow-list)". Today the tailnet is a single user, so exposure is nil, but the allow-list is unset.
4. **Test suite not re-run on the production host/venv** against `1cf3a0f`. The review proof exists; a rerun writes caches into the tree and was out of scope for a read-only round.
5. **Real-device verification partial.** iPhone has used the service since 06:31Z (turns, speech, TTS all logged OK). Samsung tablet last seen on the tailnet 5 days ago — unverified. Mac (`crooks-assistant`) offline; its rollback path is documented as untouched but cannot be inspected from here.
6. **Branch bookkeeping.** `claude/linux-prod-migration-production` exists only locally and tracks the *review* branch; a future `crooks-update` (fast-forward from upstream) would pull from the review branch. `stash@{0}` leftover on the old branch.
7. **Claude provider health text is Mac-worded** ("needs a logged-in Mac") while Linux uses `/root/.claude`'s CLI login; cosmetic, but the health line misdescribes the dependency.
8. Root service user — canonically **approved as temporary** (`DECISIONS.md:221`, `DEPLOY_LINUX.md`); hardening item remains open by design.

### 3.8 Classification

**Already satisfied and proven**
- Production checkout clean and byte-identical to candidate `1cf3a0f` (tracked bytes and stash both verified).
- Service runs the checkout's venv with the candidate's unit; loopback-only bind; NRestarts=0; ~10h uptime.
- Port 8000 not public; no Funnel; tailnet-only HTTPS with a valid LE certificate; TLS-verified 200.
- Writes disabled at every layer (config, code default, runtime, behaviour, manifest).
- Static secrets provisioned as host-bound encrypted credentials (Shopify id/secret, ElevenLabs); media signing key generated once.
- Builder Environment gate (DEC-046 step 1) — accepted per CURRENT_TRUTH.
- Bridge watcher pinned and healthy (`pending YES` for this inbox, `failures 0`, lock held by this run).

**Observed but not authorised/reconciled in canonical Git**
- The promotion of `/opt/crooks-os` to `1cf3a0f` (06:23Z).
- Installation, enabling and start of `crooks-assistant.service` (06:30Z).
- Activation of Tailscale Serve (06:30Z).
- Secret provisioning via `make secrets` (06:27–06:29Z).
All four were owner-performed at the terminal; none is recorded in DECISIONS/CURRENT_TRUTH, and CURRENT_TRUTH/MIGRATION_HANDOFF currently assert the opposite state.

**Unknown**
- Samsung tablet behaviour on the Linux origin. Mac deployment/rollback state (offline, not inspectable). Whether the owner intends the Linux server to be *the* production or a parallel instance while the Mac remains authoritative.

**Safe engineering follow-up (needs an inbox, not owner terminal time)**
- Push `claude/linux-prod-migration-production` and set its upstream correctly, or decide the review branch *is* the production ref. Drop `stash@{0}` (verified reproducible). Fix the Mac-worded Claude health string. Re-run the offline suite in `/opt/crooks-review` at `1cf3a0f` on this host and record it. Update CURRENT_TRUTH/MIGRATION_HANDOFF once §9 is decided.

**Owner-only decision** — see §9.

## 4. Provenance contradictions and unexplained state changes

1. **Canonical memory vs runtime.** `CURRENT_TRUTH.md` ("Production application branch remains `claude/crooks-assistant-build-lgxlau` … until an explicitly reviewed promotion changes it") and `MIGRATION_HANDOFF.md` §3 ("Production has not been silently moved to the Linux migration candidate"; "This remains a review candidate until deliberately promoted") are contradicted by the runtime since 06:23Z. CURRENT_TRUTH's final control-plane bullet already flags the conflict and asks for exactly this reconciliation. The move was *deliberate and owner-performed* (verified-match loop, then switch, secrets, install), so it is not an unexplained change; it is an unrecorded one.
2. **Watcher/builder branch mismatch** persists: unit says `claude/bridge-builder`, `/opt/crooks-builder` is on `claude/builder-environment-repair` @ `295e483`. Irrelevant to this read-only round; unchanged.
3. **Builder's remote-tracking ref for product memory is stale** (`b5c94fd` vs origin `fe3ffa5f`). I read the origin head via a scratch clone rather than fetching into the builder.
4. No other unexplained change: only one boot since 09-18 14:54Z, only one `crooks-assistant` start ever, `.env` untouched since before promotion, no crooks timers.

## 5. What I changed

**Nothing except this file.** No commit, checkout, switch, reset, stash, fetch, push, merge or tag in any repository. No service action of any kind. No Tailscale command other than status reads. No file under `/etc`, `/opt/crooks-os`, `/opt/crooks-review`, `/opt/crooks-builder`, `/opt/crooks-bridge-watcher` written. Scratch clone `/tmp/pmf-scratch` created and deleted. Two HTTP GETs to `/health` (loopback and tailnet origin) are visible in the service journal as reads from `127.0.0.1` / `100.72.82.24`.

## 6. Repository state (end of round)

| Repo | Branch | HEAD | Status |
|---|---|---|---|
| **Production** `/opt/crooks-os` | `claude/linux-prod-migration-production` | `1cf3a0f3361b79f9de208d80f501543c53c244b5` | clean, untouched |
| Review `/opt/crooks-review` | `claude/linux-prod-migration-review` | `1cf3a0f` | clean |
| Builder `/opt/crooks-builder` | `claude/builder-environment-repair` | `295e483b4f9adcdc3fb58bfb3aa025e2e3f4779b` | clean, untouched |
| Bridge `/opt/crooks-ai-bridge` | `crooks-ai-bridge` | `9db656cc1ebb3ba24a543e05178f02a7275a67ac` | clean apart from this outbox |
| Product memory (origin) | `claude/product-memory-foundation` | `fe3ffa5f788adf8d34ef9bdb2fccc92388f342e4` | read only, via scratch clone |

**Production branch HEAD: `1cf3a0f3361b79f9de208d80f501543c53c244b5` — unchanged by this round.**
Files changed this round: `bridge/claude-outbox.md` only.

## 7. Test results

None run (read-only round; running the suite writes caches into a checkout). Recorded proof for `1cf3a0f` remains 2886 passed / 8 skipped / 2 deselected, Ruff clean, `systemd-analyze verify` clean (MIGRATION_HANDOFF §3; outbox `05492e7`).

## 8. Service and server state (observed, unchanged)

| Service | State | Enabled | Active since (UTC) |
|---|---|---|---|
| `crooks-assistant.service` | active/running, PID 217827, 0 restarts | yes | 2026-09-19 06:30:10 |
| `crooks-bridge-watcher.service` | active/running, model `claude-fable-5-1`, effort `high` | yes | 2026-09-19 16:11:15 |
| `tailscaled.service` | active/running, serve → 127.0.0.1:8000 (tailnet only) | yes | since boot |

Host: up 1 day 1h29m, load 0.18, root fs 18% used (59G free), single boot since 09-18 14:54Z. `/health`: `degraded` solely because of the missing Gmail token; Claude, Shopify, Scribe, TTS, KB, terminology, writes(disabled) all ok; whisper disabled by design.

## 9. Decisions or questions needing owner review

**The single owner-only decision:** *Ratify, or reverse, the owner-performed 2026-09-19 06:23–06:31Z promotion of `/opt/crooks-os` to `1cf3a0f` with `crooks-assistant.service` installed/enabled and Tailscale Serve (tailnet-only HTTPS, no Funnel) active.*

- **Ratify** → the Director records it in canonical Git (a new DEC superseding the "not moved" statements; CURRENT_TRUTH §control-plane and MIGRATION_HANDOFF §3 updated; DEC-046 steps 2, 4, 5 marked satisfied, step 3 partial pending Gmail). Only then can DEC-046's runtime prerequisites be called satisfied.
- **Reverse** → `make uninstall` + `tailscale serve reset` + switch the checkout back, per `DEPLOY_LINUX.md` "Rolling back to the Mac"; owner terminal or an explicitly approved inbox, not this worker.

I have taken neither. Secondary owner items, not blocking: provision the Gmail token (browser OAuth); decide whether `CROOKS_ALLOWED_LOGINS` should be set now; confirm the Samsung tablet against the new origin.

## 10. Exact proposed next step

The Director takes the §9 decision to the owner and, on **ratify**, updates canonical Git first. The next bridge round after that should be a bounded, non-production engineering task: push/re-parent the production branch (or declare the review branch the production ref), drop the verified stash, rerun and record the suite at `1cf3a0f` in `/opt/crooks-review`, and fix the Mac-worded health string — followed by the owner's Gmail OAuth and a real-device (Samsung + iPhone) verification round. Engineering Orchestrator V1 remains not started, per DEC-046/047.

## 11. Safety constraints — all preserved

`writes_enabled` false; `CROOKS_WRITES_LOCAL_OWNER` false; FastAPI bound to 127.0.0.1; port 8000 not public; proposal/action/verification semantics untouched; no live Shopify, Gmail or ElevenLabs call and no external mutation by this round (the two `/health` reads hit the cached result); V2 not begun; UI not redesigned; Mac deployment and rollback path untouched; `/root/.claude` writable; no secret value printed or committed. The claude.ai MCP connectors exposed to this session were not invoked. No permission-layer block was encountered.

## 12. Stop

Round complete. Nothing further was done.

Inbox SHA processed: `2b7bd0d67973f8e3b09315c73c650240dc9195c4`
