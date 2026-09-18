# CLAUDE OUTBOX — latest handoff only

**Timestamp:** 2026-09-18 21:26 UTC
**Host:** crooks-os-prod-1 (Hetzner, Ubuntu 24.04 x86_64)
**Production repo:** /opt/crooks-os  (app lives in ./crooks-assistant)
**Production branch:** claude/crooks-assistant-build-lgxlau — HEAD unchanged, nothing committed
**Inbox commit processed:** `1d71681` — blob `e5a8da28ada1db792f3f5f745a831fdedbd1343b`
("bridge: ChatGPT instructions after session cleanup"). Consumed and now carried out in full.

---

## 1. Result

**Inbox steps 1–8 are complete. The offline suite is GREEN.**

```
$ .venv/bin/pytest -q -m "not live"
2870 passed, 8 skipped, 2 deselected in 493.45s (0:08:13)
exit code 0 — zero FAILED, zero ERROR
```

The previous round of this inbox stopped at step 2 with 3 failures. All three are resolved and
explained below. No live calls, no external mutations, nothing installed, nothing started.

## 2. Step 1 — the duplicate session

Confirmed resolved. PID 51046 is gone (`ps -p 51046` returns no row). The only `claude` process
on the host is this one. The tmux session `crooks-claude` still exists as a shell but holds no
agent. The tree's last third-party write was 20:55:08 and nothing has moved it since, so it was
quiescent before any of this work began.

The stopped session had got further than the last outbox knew. Before it was killed it had also
written `scripts/doctor.py`, `scripts/control.py`, `Makefile`, `scripts/set_secrets.py`,
`tests/test_whisper_disabled.py`, `tests/test_linux_ops.py` and `/opt/crooks-os/crooks-assistant/.env`.
None of it was truncated — every file compiles and ruff passes.

## 3. Step 2 — the three failures, root causes, and what was done

The 20:57 run reported `3 failed, 2866 passed`. None was a defect in the shipped behaviour; all
three were the test suite still describing the world as it was before the approved Phase 4
portability work. Two were stale assertions, one was a genuine specification disagreement.

### 3.1 `test_control.py::test_the_restart_button_is_the_line_make_restart_runs`
**Root cause.** It asserted the Makefile literally contains `scripts/install_launchd.py --restart`.
The Makefile now dispatches by `uname` to `$(INSTALLER)`. The assertion also hard-coded
`install_launchd.py` as the button's command, so on the Linux server it would have failed a
second time for the same reason. It also directly contradicted the new
`test_the_makefile_no_longer_hardcodes_the_mac_installer_in_a_target`.
**Fix.** The test now asserts the *pairing* rather than either platform's name: the Makefile's
`restart` target runs `$(INSTALLER) --restart`, both `INSTALLER :=` branches are present, and the
button's command matches `launch_common.installer_script()` for whichever host it runs on. It
still asserts the thing it was written to protect — that restart restarts what is installed and
does not reinstall it (`kickstart` on the Mac, `systemctl` on the server).

### 3.2 `test_routes.py::test_health_names_each_subsystem`
**Root cause.** It asserted every health check's key set is exactly `{ok, detail}`. The approved
truthful-health work adds `disabled` to the whisper check and `redundancy` to the speech check.
**Fix.** `{ok, detail}` is still required of every check — that is the contract the tablet reads —
and the set is now bounded by `{ok, detail, disabled, redundancy}`, so a check that invents its
own shape still fails. The assertion also names the offending check now instead of failing bare.

### 3.3 `test_linux_ops.py::test_the_doctor_reads_the_whisper_setting_without_pydantic[-True]`
**Root cause — a real disagreement, not a stale assertion.** The test asserted that an explicitly
empty `CROOKS_WHISPER_ENABLED=` means *disabled*. `scripts/doctor.py` treats an empty value as
"not configured" and lets the default stand, i.e. *enabled*.

**DECISION (mine — flagged for review below).** The implementation is right; the test was changed.
Reasons, in order of weight:
1. `CROOKS_WHISPER_ENABLED=` is what a half-edited `.env` line looks like, not a decision. Reading
   a blank as "switch the recogniser off" turns a typo into a silent capability loss on the Mac —
   the one platform that actually depends on whisper.
2. Disabling is deliberate and is spelled deliberately: `false`, `0`, `no`, `off`. A blank says
   none of those.
3. `config/settings.py` defaults `whisper_enabled` to `True`. Had the doctor answered "disabled"
   for a blank, the doctor and the application would disagree about the same line, and the doctor
   would be describing a host that does not exist. That is precisely the drift it exists to catch.

The reasoning is written into both `tests/test_linux_ops.py` and `scripts/doctor.py`, not just
into this document. **If ChatGPT or the owner disagrees, this is a one-line change in each place** —
say so and it will be reversed.

## 4. Step 3 — the systemd defect, fixed and verified

`deploy/systemd/crooks-assistant.service` had `StartLimitIntervalSec=300` and `StartLimitBurst=5`
in `[Service]`. Since systemd v229 they belong in `[Unit]`. Verified before the fix:

```
$ systemd-analyze verify <rendered unit>
Unknown key name 'StartLimitIntervalSec' in section 'Service', ignoring.
```

The consequence was not cosmetic: the key was dropped, the 10-second default window applied, and
with `RestartSec=10` the burst counter could never fill — so a service failing every start would
have restarted forever while the unit file appeared to forbid exactly that.

Both keys are now in `[Unit]`. Verified after the fix:

```
$ systemd-analyze verify <rendered unit>
(no output — clean)
```

## 5. Step 4 — the stale docstring

`app/media.py::_load_key` still said the key lives "in the Keychain" and that "Without a Keychain
(tests, Linux)" it is per-process. After the F1 fix both platforms persist it — Keychain on the
Mac, the root-only secret directory on the server. The docstring now says that, and still
documents the genuine per-process fallback (no store at all: the test suite, or a process outside
the login session).

## 6. Steps 5 and 6 — remaining Phase 4 work and tests

Step 5 was already complete when this round began; it was audited rather than rewritten:
- `scripts/doctor.py` — Linux branch: systemd, `systemd-creds`, unit state, secret-directory mode
  and owner, `.env`, Tailscale serve, and a writability check on the Claude Max credential so a
  read-only HOME cannot become a silent auth failure days later. Its one judgment call — dropping
  `cmake` and `ffmpeg` from the required tools on a whisper-disabled host — was verified correct:
  nothing in the codebase shells out to `ffmpeg` (PyAV does the decoding) and `cmake` appears only
  in whisper build instructions.
- `scripts/control.py` — the restart button uses `lc.installer_script()`; the rollback stage names
  `lc.service_labels()`.
- `Makefile` — `uname`-based dispatch for install/uninstall/status/restart/logs/secrets, plus a new
  `make health`.
- `scripts/set_secrets.py` — refuses on Linux and redirects to `provision_secrets.py`. Without this
  it would have quietly worked and done the wrong thing: a static secret meant to be an encrypted,
  host-bound systemd credential would have landed as a plain 0600 file, unencrypted at rest, with
  no error and nothing to notice until a disk image walked.

Step 6 — one gap found and closed. Nothing asserted *where* the start-limit keys live, so §4 could
silently regress. Added `test_the_start_limit_is_in_the_section_systemd_reads_it_from`, which
partitions the rendered unit on the `[Service]` header and fails if either key is live in the wrong
section. It caught a subtlety on its first run: the explanatory comment contains the literal string
`[Service]`, so a naive split cut the file in the wrong place and hid the settings from the
assertion. It partitions on the section header proper now.

## 7. Files changed

**Modified by me this round (5):**
```
crooks-assistant/tests/test_control.py            restart-button test, platform-aware
crooks-assistant/tests/test_routes.py             health check key set
crooks-assistant/tests/test_linux_ops.py          empty-value decision + new start-limit test
crooks-assistant/scripts/doctor.py                comment recording the empty-value rule
crooks-assistant/app/media.py                     docstring corrected (step 4)
crooks-assistant/deploy/systemd/crooks-assistant.service   start-limit keys -> [Unit] (step 3)
```

**Full working-tree state (this round plus the earlier sessions' approved Phase 1–4 work).**
`git status --short`:
```
 M crooks-assistant/Makefile
 M crooks-assistant/app/media.py
 M crooks-assistant/app/routes/health.py
 M crooks-assistant/app/runtime.py
 M crooks-assistant/app/secrets/keychain.py
 M crooks-assistant/app/speech/transcribe.py
 M crooks-assistant/config/settings.py
 M crooks-assistant/scripts/control.py
 M crooks-assistant/scripts/doctor.py
 M crooks-assistant/scripts/launch_common.py
 M crooks-assistant/scripts/set_secrets.py
 M crooks-assistant/scripts/update.py
 M crooks-assistant/tests/conftest.py
 M crooks-assistant/tests/test_control.py
 M crooks-assistant/tests/test_linux_ops.py
 M crooks-assistant/tests/test_routes.py
?? crooks-assistant/app/secrets/linux_store.py
?? crooks-assistant/deploy/
?? crooks-assistant/docs/DEPLOY_LINUX.md
?? crooks-assistant/scripts/healthcheck.py
?? crooks-assistant/scripts/install_systemd.py
?? crooks-assistant/scripts/provision_secrets.py
?? crooks-assistant/tests/test_linux_ops.py
?? crooks-assistant/tests/test_linux_store.py
?? crooks-assistant/tests/test_whisper_disabled.py
```

New files and their sizes:
```
199  app/secrets/linux_store.py         two-tier Linux secret store
211  scripts/provision_secrets.py       tier-aware provisioning
201  scripts/install_systemd.py         make install/status/restart/uninstall on Linux
111  scripts/healthcheck.py             production health: one line, one exit code
 79  deploy/systemd/crooks-assistant.service
 76  deploy/env.production.example
179  docs/DEPLOY_LINUX.md
280  tests/test_linux_ops.py            platform dispatch, unit rendering, healthcheck
253  tests/test_whisper_disabled.py     disabled-whisper health semantics
205  tests/test_linux_store.py          the secret store
```

`git diff --stat` on tracked files: **16 files, +547 / −92**. Untracked files add ~1,794 lines more.

## 8. Production git state

```
HEAD:      e43aecdb39b87b622f64b6ab434e428d216ef157   (unchanged all session)
short:     e43aecd  "§38: the final gate, measured on the tree being delivered"
branch:    claude/crooks-assistant-build-lgxlau
upstream:  origin/claude/crooks-assistant-build-lgxlau   ahead 0, behind 0
```

Nothing has been committed to or pushed to the production branch. The bridge branch has never
been merged into it and shares no history with it (`git merge-base` returns nothing).

## 9. Tests

| run | tree | result |
|---|---|---|
| 20:39 | before this round's fixes | 2826 passed, 8 skipped, 2 deselected, 0 failed |
| 20:57 | after the stopped session's Phase 4 work | **3 failed**, 2866 passed, 8 skipped |
| 21:16 | after §3–§6 | **2870 passed**, 8 skipped, 2 deselected, **0 failed**, exit 0 |

`ruff check app config scripts tests` — All checks passed. (One import-ordering nit my own edit
introduced was fixed; it is semantically identical, so the in-flight run was unaffected.)

`systemd-analyze verify` on the rendered unit — clean.

No live tests. No Shopify, Gmail or ElevenLabs calls. No external mutations.

## 10. Server state (21:26 UTC)

```
crooks-assistant.service ......... NOT installed, inactive
listening on :8000 / :8910 ....... nothing
/etc/crooks-os/secrets ........... does not exist
encrypted credential blobs ....... none provisioned
.env ............................. PRESENT (new since the last outbox)
tailscale serve .................. no serve config
tailscale funnel ................. off
tailnet HTTPS certs .............. available for crooks-os-prod-1.taildfb357.ts.net
```

**`.env` has appeared** at `/opt/crooks-os/crooks-assistant/.env`, written 20:52:56 by the session
that was later stopped. Mode 0600, root-owned, and its key set is identical to
`deploy/env.production.example`. The safety-relevant values are correct:
`CROOKS_WRITES_ENABLED=false`, `CROOKS_WRITES_LOCAL_OWNER=false`, `CROOKS_HOST=127.0.0.1`,
`CROOKS_PORT=8000`, `CROOKS_WHISPER_ENABLED=false`, `CROOKS_STT_PRIMARY=scribe`. It is not in git
and contains no secrets by design. This clears one of the three manual items from the last outbox.

## 11. Also built this round, NOT installed: the bridge watcher

The owner asked for a watcher so that "check inbox" never has to be typed again. It is written and
tested at `/opt/crooks-bridge-watcher/` (921 lines: worker, systemd unit, install/uninstall/status,
38 tests, README). It is **not installed, not enabled and not running** — no unit file, no state
directory, no process — pending owner approval.

- Triggers on the inbox **blob SHA**, never the branch HEAD, so Claude's own outbox push cannot
  retrigger it. Verified live: `gh api …/contents/bridge/chatgpt-inbox.md?ref=crooks-ai-bridge`
  returns `e5a8da28ada1db792f3f5f745a831fdedbd1343b`, byte-identical to git's blob SHA.
- Records an inbox as processed only after Claude exits 0 **and** the outbox blob on the remote has
  moved, so a run that dies quietly can never swallow an instruction.
- `flock` on tmpfs; the SHA handed to Claude is captured before the run, so a newer inbox arriving
  mid-run is never marked processed by a run that never read it.
- Backoff 60s → 120s → 240s, capped at 900s.
- No endpoint, no webhook, no port, no firewall change. Outbound polling on the existing `gh` login.
- Launches Claude with `--permission-mode acceptEdits` and an explicit tool list — **not**
  `bypassPermissions`; two tests assert no bypass flag is ever passed.

## 12. Decisions and questions for review

1. **The empty-value rule (§3.3)** — I decided that `CROOKS_WHISPER_ENABLED=` means *not
   configured*, therefore enabled. Reversible in one line in each of two places if you disagree.
2. **The watcher's permission scope** — `acceptEdits` plus an explicit tool list may prove too
   narrow for some Bash steps in a fully headless run. The remedy is widening
   `CROOKS_BRIDGE_ALLOWED_TOOLS` in the unit. I have deliberately not pre-authorised a bypass.
3. **Installing the watcher** — needs owner approval (`sudo ./install.sh install`).

## 13. Still requires owner action

1. **Provision secrets** — `/etc/crooks-os/secrets` does not exist and no encrypted blobs are
   stored, so the rendered unit still carries the "no credentials provisioned" placeholder instead
   of `LoadCredentialEncrypted=` lines. Only the owner holds these values.
2. **Approve Phase 5** — installing and starting `crooks-assistant.service`, activating the
   Tailscale route, and any live verification.
3. **Approve the bridge watcher install**, if it is wanted.

(`.env` is done — see §10.)

## 14. Exact proposed next step

Nothing further should happen without the owner. When approval is given, in this order:

1. Owner rules on §12.1 (the empty-value decision). If reversed, it is one line in
   `scripts/doctor.py` and one parametrised case in `tests/test_linux_ops.py`, then re-run the suite.
2. Owner decides §12.3 (watcher). If approved: `cd /opt/crooks-bridge-watcher && sudo ./install.sh install`,
   which preflights, installs the unit, seeds the state at the current inbox so it does not
   re-execute old instructions, enables and starts it. Verify with `./install.sh status` and
   `journalctl -u crooks-bridge-watcher -f`.
3. Owner provisions secrets: `python scripts/provision_secrets.py --all` on the server, typed at the
   prompt, never passed as arguments.
4. **Only then** Phase 5, and only with explicit approval: `make install` (installs the unit, enables
   it, sets the Tailscale route via `tailscale serve --bg 8000`, reads /health back), then
   `make status`, `make health`, `make doctor`.
5. Report back through this outbox.

Nothing in steps 2–4 has been done or rehearsed against live services.

Non-negotiables held throughout this round: `writes_enabled` false, `CROOKS_WRITES_LOCAL_OWNER`
false, FastAPI bound to 127.0.0.1, port 8000 not exposed, proposal/action/verification safety
semantics untouched, no live Shopify/Gmail/ElevenLabs calls, V2 not begun, UI not redesigned, Mac
deployment and rollback path preserved, `/root/.claude` writable, no secrets committed, no secret
values printed. The CROOKS working tree was never switched off
`claude/crooks-assistant-build-lgxlau`, and the bridge branch was never merged into it.

---
*No API keys, passwords, OAuth tokens, cookies, private keys or secret values appear in this file.
Secret names and configuration KEY names are referenced; no secret value was read or printed to
produce it.*
