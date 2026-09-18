# CLAUDE OUTBOX — latest handoff only

**Timestamp:** 2026-09-19 (session clock 21:58 UTC)
**Host:** crooks-os-prod-1 (Hetzner, Ubuntu 24.04 x86_64)
**Production repo:** /opt/crooks-os  (app in ./crooks-assistant)
**Production branch:** claude/crooks-assistant-build-lgxlau
**Inbox commit processed:** `7f4e598` — blob `102dc1f273d33a0cce80979ff27651b396bef4a4`
("bridge: request code review branches before live install")
**Previous inbox processed:** `1d71681` (blob `e5a8da2`)

---

## 0. HEADLINE — one thing needs you before review can happen

Both review branches are **committed locally but NOT pushed**. Two `git push` attempts were
**refused by this session's permission layer** as shared-resource modifications:

```
Permission for this action was denied by the Claude Code auto mode classifier.
Reason: [Modify Shared Resources]
```

This is an environment restriction on this session, not a git, auth or network failure — `gh` is
authenticated and the earlier outbox pushes to `crooks-ai-bridge` succeeded. I did not attempt to
work around it.

**The branches therefore do not exist on GitHub yet and cannot be reviewed there.** Everything
else in steps 1–5 is complete. The owner needs either to approve the pushes or to run them:

```
git -C /opt/crooks-review          push -u origin claude/linux-prod-migration-review
git -C /opt/crooks-watcher-review  push -u origin claude/crooks-bridge-watcher-review
```

Both commits are made, verified and byte-identical to the tested tree; only the push is missing.

## 1. The report inconsistency — my error, not a worktree problem

You were right: that porcelain state was impossible. `tests/test_linux_ops.py` is **untracked and
only untracked**. I hand-assembled the status block in the last outbox and added an ` M` line for
it because I had edited it that round, while it was in fact still untracked. A reporting mistake
in the outbox. No path issue, no worktree issue, nothing discarded.

Exact output, run from the repo root (/opt/crooks-os):

```
$ git status --porcelain=v1 --untracked-files=all
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
 M crooks-assistant/tests/test_routes.py
?? crooks-assistant/app/secrets/linux_store.py
?? crooks-assistant/deploy/env.production.example
?? crooks-assistant/deploy/systemd/crooks-assistant.service
?? crooks-assistant/docs/DEPLOY_LINUX.md
?? crooks-assistant/scripts/healthcheck.py
?? crooks-assistant/scripts/install_systemd.py
?? crooks-assistant/scripts/provision_secrets.py
?? crooks-assistant/tests/test_linux_ops.py
?? crooks-assistant/tests/test_linux_store.py
?? crooks-assistant/tests/test_whisper_disabled.py

$ git diff --name-status
M	crooks-assistant/Makefile
M	crooks-assistant/app/media.py
M	crooks-assistant/app/routes/health.py
M	crooks-assistant/app/runtime.py
M	crooks-assistant/app/secrets/keychain.py
M	crooks-assistant/app/speech/transcribe.py
M	crooks-assistant/config/settings.py
M	crooks-assistant/scripts/control.py
M	crooks-assistant/scripts/doctor.py
M	crooks-assistant/scripts/launch_common.py
M	crooks-assistant/scripts/set_secrets.py
M	crooks-assistant/scripts/update.py
M	crooks-assistant/tests/conftest.py
M	crooks-assistant/tests/test_control.py
M	crooks-assistant/tests/test_routes.py

$ git ls-files --others --exclude-standard
crooks-assistant/app/secrets/linux_store.py
crooks-assistant/deploy/env.production.example
crooks-assistant/deploy/systemd/crooks-assistant.service
crooks-assistant/docs/DEPLOY_LINUX.md
crooks-assistant/scripts/healthcheck.py
crooks-assistant/scripts/install_systemd.py
crooks-assistant/scripts/provision_secrets.py
crooks-assistant/tests/test_linux_ops.py
crooks-assistant/tests/test_linux_store.py
crooks-assistant/tests/test_whisper_disabled.py
```

15 modified + 10 untracked = 25 distinct paths, each appearing exactly once. Note `.env` appears
in none of them: it is gitignored (`crooks-assistant/.gitignore:4`), which is also why it is
excluded from the review branch without special handling.

## 2. The empty-value rule, measured against the real parser

**You were right to refuse the opinion. The measurement overturned my previous decision.**

Probed through the application's own path, `config.settings.Settings`, with `_env_file=None` so
the host's `.env` could not answer for it:

```
CROOKS_WHISPER_ENABLED unset      -> whisper_enabled = True
CROOKS_WHISPER_ENABLED=''         -> RAISES ValidationError (bool_parsing)
CROOKS_WHISPER_ENABLED='  '       -> RAISES ValidationError (bool_parsing)
CROOKS_WHISPER_ENABLED='false'    -> False
CROOKS_WHISPER_ENABLED='true'     -> True
```

So a blank is **neither** enabled nor disabled: pydantic rejects it and the backend refuses to
start. My earlier ruling ("blank means enabled") and the original test ("blank means disabled")
were **both wrong**, and each would have had the doctor report a host that cannot exist.

Full vocabulary, measured rather than assumed:

```
accepted true : true True TRUE 1 yes Yes on t y
accepted false: false False FALSE 0 no off f n
REJECTED      : '' '  ' 'maybe' '2' 'flase' ' true ' 'true '
```

Two further facts that matter, and that an approximation would have got wrong:
- **The environment is not stripped.** `' true '` via `os.environ` is invalid.
- **The `.env` file path IS stripped and unquoted**, because python-dotenv normalises before
  pydantic sees it: a line `CROOKS_WHISPER_ENABLED= false ` yields `False`, and `"false"` yields
  `False`. An empty `.env` value is still invalid.

**Implementation now aligned to exactly that.** `scripts/doctor.py` gained a tri-state
`whisper_setting() -> "enabled" | "disabled" | "invalid"`, mirroring both paths separately
(`env_file_value()` strips and unquotes; the environment is read raw). `whisper_disabled()` is
derived and returns True only for a real "disabled", so an unparseable value cannot quietly
suppress the whisper checks as well. The doctor reports an invalid setting as a **blocking
failure** — "the backend would refuse to start" — ahead of the whisper rows, because it outranks
them.

**The test no longer encodes anyone's opinion.** It computes the expected answer from the real
`Settings` parser and requires the doctor to agree, across all 23 values above. If pydantic's
vocabulary ever changes, that test fails rather than the doctor drifting silently.

## 3. Review branch — the Phase 1–4 migration

```
branch:  claude/linux-prod-migration-review
commit:  1cf3a0f3361b79f9de208d80f501543c53c244b5
base:    e43aecdb39b87b622f64b6ab434e428d216ef157   (current production HEAD)
pushed:  NO — blocked, see §0
worktree: /opt/crooks-review   (the production checkout was never switched)
```

**Exact staged file list** (`git diff --cached --name-status`, 25 paths, +2411 / −91):

```
M	crooks-assistant/Makefile
M	crooks-assistant/app/media.py
M	crooks-assistant/app/routes/health.py
M	crooks-assistant/app/runtime.py
M	crooks-assistant/app/secrets/keychain.py
A	crooks-assistant/app/secrets/linux_store.py
M	crooks-assistant/app/speech/transcribe.py
M	crooks-assistant/config/settings.py
A	crooks-assistant/deploy/env.production.example
A	crooks-assistant/deploy/systemd/crooks-assistant.service
A	crooks-assistant/docs/DEPLOY_LINUX.md
M	crooks-assistant/scripts/control.py
M	crooks-assistant/scripts/doctor.py
A	crooks-assistant/scripts/healthcheck.py
A	crooks-assistant/scripts/install_systemd.py
M	crooks-assistant/scripts/launch_common.py
A	crooks-assistant/scripts/provision_secrets.py
M	crooks-assistant/scripts/set_secrets.py
M	crooks-assistant/scripts/update.py
M	crooks-assistant/tests/conftest.py
M	crooks-assistant/tests/test_control.py
A	crooks-assistant/tests/test_linux_ops.py
A	crooks-assistant/tests/test_linux_store.py
M	crooks-assistant/tests/test_routes.py
A	crooks-assistant/tests/test_whisper_disabled.py
```

**Excluded, as required:** `.env` (gitignored; verified absent from the review tree), every secret
value, all bridge files, and all watcher files.

**Secret scan before staging.** Checked for `gh[pousr]_`, `shpat_`/`shpss_`/`shpca_`, `sk-`,
`AIza`, `xox[baprs]-`, JWT-shaped `eyJ…`, and `BEGIN … PRIVATE KEY` across all 25 paths, plus a
file-level check for `.env`, `token.json`, `credentials.json`, `*.cred`, `*.pem`, `id_rsa*`.

One hit, and it is **not** a leak: `tests/test_control.py` contains
`ghp_b7b7b7b7b7b7b7b7b7b7b7b7` — a synthetic repeating-pattern token that is **already committed
at e43aecd** (line 1031 there) and is the fixture for the test asserting that tokens are redacted
out of health details and git output. `git diff` on that file shows zero `ghp_` lines, i.e. my
changes neither added nor altered it. Flagging it because any scanner you run will flag it too.

**Test result for this exact content:**

```
$ .venv/bin/pytest -q -m "not live"
2886 passed, 8 skipped, 2 deselected in 506.50s (0:08:26)
exit code 0 — zero FAILED, zero ERROR
```

Verified afterwards that all 25 committed files are **byte-identical** (`cmp`) to the working tree
that produced that result, so the number describes the branch and not an earlier state.
`ruff check app config scripts tests` — All checks passed.
`systemd-analyze verify` on the rendered unit — clean.

**Production branch pointer:**

```
$ git rev-parse claude/crooks-assistant-build-lgxlau
e43aecdb39b87b622f64b6ab434e428d216ef157
```

**CONFIRMED unchanged**, identical to the SHA you named. Nothing was merged, nothing rebased, the
production worktree was never switched, and the review branch was built in a separate worktree
specifically so it could not be.

## 4. Review branch — the bridge watcher

```
branch:  claude/crooks-bridge-watcher-review   (orphan — shares no history with production)
commit:  dadf2574d66398064f3f65a0a4bd7fdf087cc148
pushed:  NO — blocked, see §0
worktree: /opt/crooks-watcher-review
files:   watcher/bin/crooks-bridge-watcher, watcher/install.sh, watcher/README.md,
         watcher/systemd/crooks-bridge-watcher.service, watcher/tests/run-tests.sh
```

Orphan on purpose: watcher code is on neither `crooks-ai-bridge` nor the production branch, and
cannot be fast-forwarded into either.

**Exact Claude CLI invocation.** The worker runs, with `WORK_DIR` as the process's cwd:

```
cd /opt/crooks-os/crooks-assistant && \
timeout --signal=TERM --kill-after=60 7200 \
  claude --print \
         --permission-mode acceptEdits \
         --allowed-tools Read,Edit,Write,Glob,Grep,Bash \
         "<prompt, carrying the inbox blob SHA being processed>"
```

Nothing else is passed. No `--dangerously-skip-permissions`, no `bypassPermissions`; two tests
assert that no permission-bypassing flag can appear in the invocation.

**Permission / tool configuration** (unit `Environment=`, overridable without editing code):

```
CROOKS_BRIDGE_PERMISSION_MODE=acceptEdits
CROOKS_BRIDGE_ALLOWED_TOOLS=Read,Edit,Write,Glob,Grep,Bash
CROOKS_BRIDGE_CLAUDE_TIMEOUT_S=7200
```

**Lock and state paths:**

```
/run/crooks-bridge/watcher.lock     flock, exclusive, non-blocking; systemd RuntimeDirectory,
                                    mode 0700, tmpfs — a reboot cannot strand a stale lock
/var/lib/crooks-bridge/last-inbox-sha   the last inbox PROVEN processed
/var/lib/crooks-bridge/failures         consecutive failures, drives the backoff
/var/lib/crooks-bridge/last-run         ok|failed, timestamp, which SHA
/var/lib/crooks-bridge/.next-delay      how long the loop sleeps next
                                    systemd StateDirectory, mode 0700
```

**Retry policy.** Poll every 30s. An inbox is recorded as processed only when Claude exits 0
**and** the outbox blob on the remote has changed — exit 0 without a report is treated as a
failure, because nobody has been told anything. On failure: 60s, 120s, 240s, 480s, capped at 900s,
reset to 30s polling on success. The SHA handed to Claude is captured before the run and is the
one recorded, so a newer inbox arriving mid-run is never marked processed by a run that never saw
it.

**Tests:** `48 passed, 0 failed` — no network, no real Claude, no real state directories. Covering
inbox-SHA detection, duplicate suppression, outbox-push-does-not-retrigger, lock suppression and
pickup after release, newer-inbox-mid-run, failed run not recorded, retry-then-record, backoff
growth and cap, exit-0-without-report, GitHub unreachable, seeding, the three fail-closed guards,
and the prompt's safety contract.

**Not installed, not enabled, not running.** No unit file in /etc/systemd/system, no
/var/lib/crooks-bridge, no process.

## 5. The safety requirement — implemented, and your premise is correct

The watcher now **fails closed** before launching anything. Three refusals, each naming the remedy:

1. **Another run holds the lock** — non-blocking `flock`; the cycle logs and returns, recording
   nothing, so the inbox is retried rather than lost.
2. **The target working tree has uncommitted changes** — `git status --porcelain=v1 -uall` is
   non-empty. Refuses. There is a deliberate override, `CROOKS_BRIDGE_ALLOW_DIRTY=1`, **off by
   default**, for when a person has looked at the changes and decided the run is safe.
3. **Another Claude process has its cwd inside the target tree** — found by resolving
   `/proc/<pid>/cwd` for each Claude process and comparing against the resolved target. Both sides
   are resolved, or a symlinked path compares unequal to itself and the guard waves through the
   process it exists to catch. Tested against a real process with a real cwd, including the
   converse: an unrelated Claude elsewhere on the box does **not** block a run, or the watcher
   would refuse to work on any machine where anyone uses Claude for anything.

**And you are right that this is not sufficient.** The watcher as it stands does target
`/opt/crooks-os/crooks-assistant` directly, so per your instruction it is **not installed**.

### Proposed minimal builder worktree

The smallest change that removes the shared-tree problem entirely, rather than guarding it:

```
git -C /opt/crooks-os worktree add -b claude/bridge-builder /opt/crooks-builder <production HEAD>
```

then one line in the unit:

```
Environment=CROOKS_BRIDGE_WORKDIR=/opt/crooks-builder
```

What this buys:
- The live production checkout is **never** mutated by headless work. A person editing
  `/opt/crooks-os` and the watcher can run at the same time without either noticing the other.
- The dirty-tree guard becomes meaningful instead of near-permanently tripped: the builder tree is
  the watcher's own, so uncommitted leftovers there are a genuine anomaly worth refusing on. As
  things stand today the production tree has 25 uncommitted paths, so the watcher would refuse
  every run until the migration is committed — correct, but not useful.
- Headless work lands on `claude/bridge-builder` and is pushed as a branch for review. It reaches
  production only when a person merges it, which is the same gate this review process already has.
- The blast radius of a bad headless run is one disposable worktree, recoverable with
  `git worktree remove --force`.

What it costs, stated plainly:
- Work done headless is not visible in the production checkout until merged. That is the point,
  but it does mean two places to look.
- One more worktree to keep roughly in step with production.

**Recommendation:** adopt the builder worktree, keep all three fail-closed guards (they still
matter — the lock and the foreign-Claude check are not made redundant by it), and only then
install. I have not created the builder worktree or changed the unit's default, because that
changes what you would be approving and you asked to review the current implementation first.

## 6. State

```
production branch ............ claude/crooks-assistant-build-lgxlau @ e43aecd (unchanged, 0/0 vs origin)
review branch ................ claude/linux-prod-migration-review @ 1cf3a0f (local only)
watcher review branch ........ claude/crooks-bridge-watcher-review @ dadf257 (local only, orphan)
crooks-assistant.service ..... NOT installed, inactive
listening on :8000 / :8910 ... nothing
/etc/crooks-os/secrets ....... does not exist, no credentials provisioned
.env ......................... present, 0600, root — safety flags correct
tailscale serve .............. no serve config;  funnel off
bridge watcher ............... NOT installed, not enabled, not running
```

Nothing was installed, started, provisioned or activated. No live Shopify, Gmail or ElevenLabs
calls. No writes enabled. No V2, no UI work. No merge into the production branch.

## 7. Exact proposed next step

1. **Owner unblocks the two pushes** (§0) — either approving them in this session or running the
   two commands. Until then neither branch is reviewable on GitHub, and that is the only thing
   standing between you and the diff you asked for.
2. You review `claude/linux-prod-migration-review` (1cf3a0f) and
   `claude/crooks-bridge-watcher-review` (dadf257).
3. You rule on the builder worktree (§5). If adopted, I create it, point the unit at it, re-run
   the watcher suite, and push the updated watcher branch — still without installing.
4. Only then, and only with explicit approval: watcher install, secret provisioning, and Phase 5
   (systemd install/start, Tailscale Serve, live verification).

Stopping here as instructed.

---
*No API keys, passwords, OAuth tokens, cookies, private keys or secret values appear in this file.
Secret and configuration KEY names are referenced; the one credential-shaped string discussed in
§3 is a pre-existing synthetic test fixture, named so that your scanner's hit on it is explained
rather than mysterious.*
