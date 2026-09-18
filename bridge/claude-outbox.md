# CLAUDE OUTBOX — latest handoff only

**Timestamp:** 2026-09-18 20:49 UTC
**Host:** crooks-os-prod-1 (Hetzner, Ubuntu 24.04 x86_64)
**Production repo:** /opt/crooks-os  (app lives in ./crooks-assistant)
**Production branch:** claude/crooks-assistant-build-lgxlau — NOT touched by this bridge
**Bridge worktree:** /opt/crooks-ai-bridge on branch `crooks-ai-bridge` (orphan, no app code)
**Last ChatGPT inbox commit processed:** none — `bridge/chatgpt-inbox.md` created empty this round

---

## 1. What I was asked to do

Two things this round.

**(a)** Resume interrupted work. A prior session died mid-run after the owner approved two
decisions:
- **F1 = Option 1** — keep `media_signing_key` as a recognised secret on both macOS and Linux;
  accept one new Mac Keychain entry and one initial Mac thumbnail-cache invalidation; eliminate
  the regenerate-on-restart bug on both platforms; no unnecessary platform divergence.
- **F2 = Option A** — Linux Tier B persistent secret store for `gmail_token` at
  `/etc/crooks-os/secrets/gmail_token`: root-only, 0600, writable so OAuth refresh persists,
  outside the Git checkout; existing `token.json` may remain as a compatibility fallback but
  must NOT become the preferred Linux production storage.

The gate: run the complete offline suite first (`pytest -q -m "not live"`); **stop** if anything
fails; otherwise continue previously approved Phases 1–4; then stop before Phase 5 live
verification.

**(b)** Set up this permanent GitHub bridge (separate branch + separate worktree, no app code,
no secrets), write the current status into it, push, confirm, stop.

## 2. Headline for the reviewer

1. **Offline baseline is GREEN** — 2826 passed, 8 skipped, 2 deselected, 0 failures, 504s.
2. **A second Claude session is editing the same production working tree concurrently.** This
   is unresolved and is the most important thing on this page. See §6.
3. Phase 3 (Tailscale) is verified as complete as it can safely be without a live install.
4. One real, verified defect found in the new systemd unit template (§4.2).

## 3. What I found

### 3.1 State of the previously approved work (written by the earlier session, all uncommitted)
Phases 1 and 2 are substantially implemented and consistent with the F1/F2 approvals:
- `app/secrets/linux_store.py` (new) — two tiers. **Tier A** = systemd credentials via
  `$CREDENTIALS_DIRECTORY`, read-only, `LoadCredentialEncrypted=`, encrypted at rest and
  host-bound. **Tier B** = `/etc/crooks-os/secrets`, dir 0700 / files 0600, read-write, atomic
  writes (mkstemp + fchmod before content + rename). Reads check A then B; writes go to B; a
  write to a key Tier A provides raises `SecretShadowed` rather than writing somewhere the next
  read would ignore. `gmail_token` and `media_signing_key` are both classified MUTABLE → Tier B,
  exactly as approved under F1/F2.
- `app/secrets/keychain.py` — platform dispatch only (`sys.platform`), macOS Keychain path
  unchanged. `media_signing_key` added to `KNOWN_KEYS`, which is the actual F1 fix: it was read
  and written by `app/media.py` but never listed, so every lookup raised "unknown key", every
  store was swallowed by that module's bare `except`, and the key was silently regenerated on
  every boot on **both** platforms — invalidating the tablet's thumbnail cache each restart.
- `tests/conftest.py` — sets `CROOKS_SECRET_DIR` into test state *before any app import*, because
  `app/media.py` loads its signing key at import time; without this, merely collecting the suite
  on Linux would create and write `/etc/crooks-os/secrets`.
- `scripts/provision_secrets.py`, `scripts/install_systemd.py`, `scripts/healthcheck.py` (new),
  `deploy/systemd/crooks-assistant.service`, `deploy/env.production.example`,
  `docs/DEPLOY_LINUX.md`, `tests/test_linux_store.py` (new).
- `scripts/launch_common.py` / `scripts/update.py` — `is_linux()`, `service_labels()`,
  `restart_services()` (`systemctl restart` vs `launchctl kickstart`), `installer_script()`,
  `restart_hint()`. The update path is otherwise identical code on both platforms.

### 3.2 Verification I ran (all read-only, nothing installed, nothing mutated)
- `py_compile` and `ruff check` over every changed/new file — clean.
- `install_systemd.preflight()` → `[]` (no problems): venv present, `claude` at
  `/usr/local/bin/claude`, Tailscale present, unit template present.
- Rendered the systemd unit to a scratch file (not installed) and confirmed real paths fill in
  correctly and **no secret values appear in it**.
- Confirmed `node` (/usr/bin/node) and `claude` both resolve from the PATH the unit hands
  systemd — the classic cause of a systemd restart loop for this service.

### 3.3 Phase 3 (Tailscale HTTPS route) — as far as is safe without installing
- Tailnet HTTPS certs are available: `CertDomains: ['crooks-os-prod-1.taildfb357.ts.net']`.
- `tailscale serve status` → **No serve config**; `tailscale funnel status` → **No serve config**.
  Funnel is off and must stay off.
- Tailscale CLI is **1.102.4**, which supports the exact `tailscale serve --bg <port>` form that
  `launch_common.ensure_serve()` calls. `scripts/install_systemd.py` already invokes
  `ensure_serve(port)` at install and reports `serve_status(port)` under `--status`.
- Conclusion: the Phase 3 **code path is complete and compatible**. The only remaining action is
  running the install, which is Phase 5 and is NOT approved.

## 4. Errors / defects found

### 4.1 (none in the test suite)
Zero failures, zero errors. The run emits `RuntimeError: Event loop is closed` noise from asyncio
GC at interpreter exit, which buries the summary line in `tail` output but is not a failure —
exit code 0.

### 4.2 Real defect: systemd start-limit keys in the wrong section
`crooks-assistant/deploy/systemd/crooks-assistant.service` puts `StartLimitIntervalSec=300` and
`StartLimitBurst=5` in `[Service]`. `systemd-analyze verify` on the rendered unit (systemd 255):

```
Unknown key name 'StartLimitIntervalSec' in section 'Service', ignoring.
```

Since systemd v229 these belong in `[Unit]`. As written the intended "five restarts in five
minutes, then give up" **does not apply**; the 10s default window applies instead, and with
`RestartSec=10` the burst counter effectively never fills — so a crash loop would spin forever
rather than stopping in a state `make status` can report. That is precisely the failure the
template's own comment claims to prevent.
**Fix:** move both keys into the `[Unit]` section. NOT yet applied (see §6).

### 4.3 Stale docstring
`crooks-assistant/app/media.py:32-35` still says the key is kept "in the Keychain … Without a
Keychain (tests, Linux) a key for this process only". After the F1 fix, Linux persists it too.
Wording only, no behaviour.

## 5. What I changed

**In the CROOKS production tree: nothing. I have made zero edits to production code this session.**
Everything in §3 was written by the earlier session; my contribution so far is verification.

**On this bridge branch:** created `bridge/claude-outbox.md` and `bridge/chatgpt-inbox.md` on the
new orphan branch `crooks-ai-bridge`, in the separate worktree `/opt/crooks-ai-bridge`. The
production checkout was never switched, reset or stashed.

## 6. DECISION REQUIRED — concurrent session editing the same working tree

While setting this up I found a **second Claude process still alive and actively editing the
production working tree**:

- PID 51046, started 17:30:33, running under `tmux new -As crooks-claude`, cwd
  `/opt/crooks-os/crooks-assistant`. Its transcript was still being written at 20:48:56.
- PID 62455 is me (started 20:37:23) — the session the owner opened after the Termius crash.

Evidence it is writing, not idle: at 20:38 the tree had 4 modified files; by 20:49 it had 8.
`config/settings.py` (mtime 20:48:08) and `app/routes/health.py` (mtime 20:48:34) changed while I
was mid-audit, and `app/runtime.py` and `app/speech/transcribe.py` appeared minutes later. The
content is Phase 4 work — a `whisper_enabled: bool = True` setting and `/health` reporting whisper
as `disabled` rather than failed.

**Why this matters:** two agents editing one working tree with no locking can interleave writes,
overwrite each other's edits, and produce a commit neither of them fully authored. It also makes
every `git status` in this document a moving target.

**This is why I applied no fixes** — including the one-line §4.2 fix. Writing into that tree right
now risks clobbering the other session mid-edit.

**Question for the owner / reviewer:** which session should own the tree? Recommended: stop one of
them (the tmux session `crooks-claude`, PID 51046, is the older one), confirm the tree is quiescent,
re-run the offline suite, and let the surviving session finish Phases 1–4 and report. I have made no
change to either process.

## 7. Production git state (snapshot 20:49 UTC — moving, see §6)

```
HEAD:      e43aecdb39b87b622f64b6ab434e428d216ef157
short:     e43aecd  "§38: the final gate, measured on the tree being delivered"
branch:    claude/crooks-assistant-build-lgxlau
upstream:  origin/claude/crooks-assistant-build-lgxlau
ahead/behind upstream: 0 / 0
```

`git status --short`:

```
 M crooks-assistant/app/routes/health.py
 M crooks-assistant/app/runtime.py
 M crooks-assistant/app/secrets/keychain.py
 M crooks-assistant/app/speech/transcribe.py
 M crooks-assistant/config/settings.py
 M crooks-assistant/scripts/launch_common.py
 M crooks-assistant/scripts/update.py
 M crooks-assistant/tests/conftest.py
?? crooks-assistant/app/secrets/linux_store.py
?? crooks-assistant/deploy/
?? crooks-assistant/docs/DEPLOY_LINUX.md
?? crooks-assistant/scripts/healthcheck.py
?? crooks-assistant/scripts/install_systemd.py
?? crooks-assistant/scripts/provision_secrets.py
?? crooks-assistant/tests/test_linux_store.py
```

`git diff --stat` (tracked files only; the untracked ones above add ~1100 further lines):

```
 crooks-assistant/app/routes/health.py     |  75 ++++++++++++++----
 crooks-assistant/app/runtime.py           |   1 +
 crooks-assistant/app/secrets/keychain.py  | 125 ++++++++++++++++++++++++++----
 crooks-assistant/app/speech/transcribe.py |  11 +++
 crooks-assistant/config/settings.py       |  11 +++
 crooks-assistant/scripts/launch_common.py |  82 +++++++++++++++++++-
 crooks-assistant/scripts/update.py        |  22 +++---
 crooks-assistant/tests/conftest.py        |   7 +-
 8 files changed, 284 insertions(+), 50 deletions(-)
```

Nothing has been committed to the production branch. Nothing has been pushed to it.

## 8. Tests / results

```
$ .venv/bin/pytest -q -m "not live"
2826 passed, 8 skipped, 2 deselected in 504.22s (0:08:24)
exit code 0 — zero FAILED, zero ERROR lines
```

Run at 20:39–20:48 UTC against the working tree as it stood at 20:39. **Caveat:** because of §6,
the tree has changed since that run started, so this result does not cover
`app/routes/health.py`, `app/runtime.py`, `app/speech/transcribe.py` or `config/settings.py` as
they now stand. The suite must be re-run once the tree is quiescent.

No live tests were run. No Shopify, Gmail or ElevenLabs API calls were made. No external mutations.

## 9. Server / service state (20:49 UTC)

```
systemd unit crooks-assistant.service ... NOT installed
listening on :8000 / :443 / :8910 ..... nothing
/etc/crooks-os/secrets ................ does not exist
encrypted credential blobs ............ none provisioned
/opt/crooks-os/crooks-assistant/.env .. DOES NOT EXIST
tailscale serve ....................... no serve config
tailscale funnel ...................... off
tailnet identity ...................... crooks-os-prod-1 / 100.72.82.24
tailnet HTTPS certs ................... available for crooks-os-prod-1.taildfb357.ts.net
```

All correct for a pre-Phase-5 host. Nothing is exposed.

## 10. Requires owner action (cannot be done for you)

1. **Resolve the two-session conflict (§6)** — blocking.
2. **Create `.env`** — `deploy/env.production.example` must be copied to
   `/opt/crooks-os/crooks-assistant/.env`. Without it the service starts on defaults: no Shopify
   domain, and `CROOKS_WHISPER_ENABLED=false` never takes effect.
3. **Provide secret values** for `scripts/provision_secrets.py` (Shopify client id/secret,
   ElevenLabs key, Gmail token). Only the owner holds these. Until then the rendered unit carries
   a "no credentials provisioned" placeholder instead of `LoadCredentialEncrypted=` lines.

## 11. Exact proposed next step

Do these in order, and nothing else:

1. Owner decides §6. Assume the tmux session PID 51046 is stopped and this session continues.
2. Re-run `.venv/bin/pytest -q -m "not live"` against the then-current tree. If it fails, stop and
   report.
3. Apply the §4.2 fix: move `StartLimitIntervalSec=` and `StartLimitBurst=` into `[Unit]` in
   `deploy/systemd/crooks-assistant.service`; re-verify with `systemd-analyze verify` on the
   rendered unit.
4. Apply the §4.3 docstring correction in `app/media.py`.
5. Finish whatever of Phase 4 the other session left incomplete: `scripts/doctor.py` Linux branch
   (it currently warns "targets macOS" and checks brew/xcode/Core ML), `scripts/control.py`
   restart button (still hard-codes `install_launchd.py --restart` — should use
   `lc.installer_script()`), and Makefile platform dispatch for
   install/uninstall/status/restart/logs/secrets.
6. Add tests for the disabled-whisper health semantics and the platform dispatch.
7. Re-run the offline suite, then report: git status, every changed/new file, what was
   implemented, service/Tailscale/health state, and what still needs owner action.
8. **STOP before Phase 5.** No live verification without explicit approval.

Non-negotiables held throughout: `writes_enabled` false, `CROOKS_WRITES_LOCAL_OWNER` false,
FastAPI bound to 127.0.0.1, port 8000 not exposed, proposal/action/verification safety semantics
untouched, no live Shopify/Gmail/ElevenLabs calls, V2 not begun, UI not redesigned, Mac deployment
and rollback path preserved, `/root/.claude` left writable for Claude Max OAuth refresh, no secrets
committed, no secret values printed.

---
*No API keys, passwords, OAuth tokens, cookies, private keys or secret values appear in this file.
Secret names are referenced; secret values are not, and none were read or printed to produce it.*
