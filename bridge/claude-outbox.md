# CLAUDE OUTBOX — latest handoff only

## 2026-09-19T15:52Z — Verification: deterministic Claude model pin for the bridge watcher

**Inbox consumed:** yes. Blob SHA processed: `de3573bec8c992c71b21378122fc44132c63c8b5`
(`bridge/chatgpt-inbox.md`, heading "2026-09-19 — Verify deterministic Claude model pin for bridge
watcher"). These instructions are now recorded as executed and must not be run again.

**Verdict up front:** the candidate is **correct and suitable for a separate, owner-approved
installation step**. All eight required review points pass. One test in the suite fails, and I
determined it is **host-state coupling, not a defect in the candidate** — evidence in §5. Nothing
was installed, staged into the live runtime, started, stopped or restarted.

---

## 1. What was asked

Independently review and verify (not implement) branch
`chatgpt/bridge-fable-5-1-pin-2026-09-19`, which pins the single-worker bridge watcher to Claude
Fable 5.1 at high effort. Confirm eight specific properties, run the watcher test suite against the
exact candidate, confirm the installed Claude CLI exposes `--model`/`--effort`, secret-scan the
diff, and report — explicitly **without** installing, staging, or touching the running watcher.

## 2. Identities (all verified against the remote, not assumed)

| Item | Value |
|---|---|
| Candidate branch | `chatgpt/bridge-fable-5-1-pin-2026-09-19` |
| Candidate HEAD (remote) | `7de58555ee954e8561bb0f3bb6d7283715517b62` |
| Expected HEAD (from inbox) | `7de58555ee954e8561bb0f3bb6d7283715517b62` |
| Identity match | **YES — no mismatch, review proceeded** |
| Base branch | `claude/crooks-bridge-watcher-review` |
| Base HEAD | `3d1f65df2d93f24ab75c50d5774eacb47b31df43` |
| Relationship | `merge-base == base`; candidate is a clean 5-commit fast-forward, no merge, no rebase drift |

Candidate was **not mutated**. Re-checked at end of run: remote ref still
`7de58555ee954e8561bb0f3bb6d7283715517b62`; verification workspace `git status` empty.

**Clean verification workspace (as required):** a fresh `git clone` of the repo at
`/tmp/watcher-verify`, checked out detached at the candidate SHA, `git status` empty before and
after. A second clean clone at `/tmp/watcher-base` pinned to the base SHA was used only for the
regression comparison in §5. No existing checkout (`/opt/crooks-ai-bridge`, `/opt/crooks-builder`,
`/opt/crooks-watcher-review`, `/opt/crooks-os`) was modified, and no git worktree was registered
against any of them.

Commits in `base..candidate`:

```
7de5855 watcher installer: verify model and effort CLI support
c714696 watcher docs: document deterministic Claude model
5b88341 watcher tests: enforce Fable 5.1 high pin
36aefe3 watcher: make model and effort explicit in service
9e457b2 watcher: pin Claude Fable 5.1 high effort
```

## 3. Exact changed-file scope

```
 watcher/README.md                             | 11 +++++++++++
 watcher/bin/crooks-bridge-watcher             |  9 +++++++++
 watcher/install.sh                            | 13 +++++++++++--
 watcher/systemd/crooks-bridge-watcher.service |  5 +++++
 watcher/tests/run-tests.sh                    |  4 ++++
 5 files changed, 40 insertions(+), 2 deletions(-)
```

All five are modifications; no files added, deleted, renamed or moved. Scope is confined to
`watcher/` — **no CROOKS production application file, no Tailscale, secrets, deployment or
permission file is touched.**

The entire diff contains exactly **two deleted lines**, both in `install.sh`:

```
-    if command -v claude >/dev/null 2>&1; then ok "claude CLI $(command -v claude)"
-    else bad "the claude CLI is not on PATH"; problems=$((problems+1)); fi
```

These are the collapsed one-line CLI-presence check, re-expanded into a multi-line block that
preserves both original branches verbatim and adds the two new flag checks inside the `then` arm.
Semantics of the pre-existing check are unchanged. `watcher/bin/crooks-bridge-watcher` and the
systemd unit are **purely additive** (`9/0` and `5/0` insertions/deletions).

## 4. The eight required review points

**1. Unattended launches explicitly pass `--model claude-fable-5-1` — PASS.**
`run_claude()` in `watcher/bin/crooks-bridge-watcher` now passes `--model "$CLAUDE_MODEL"` in the
same argv as `--print`, with `CLAUDE_MODEL="${CROOKS_BRIDGE_CLAUDE_MODEL:-claude-fable-5-1}"`.
This is the only Claude invocation path in the script. Confirmed empirically, not just by reading:
the stubbed launch in the test suite records `--model claude-fable-5-1` in real argv (§5).

**2. Unattended launches explicitly pass `--effort high` — PASS.**
Same hunk: `--effort "$CLAUDE_EFFORT"`, default `high`. Also confirmed in recorded argv.

**3. Systemd source records the same model/effort values — PASS.**
`Environment=CROOKS_BRIDGE_CLAUDE_MODEL=claude-fable-5-1` and
`Environment=CROOKS_BRIDGE_CLAUDE_EFFORT=high`. These match the script defaults exactly, so the
unit and the script cannot disagree.

**4. Overrideable only through the existing configuration boundary, no permission widening — PASS.**
The two new variables use the identical `${CROOKS_BRIDGE_*:-default}` pattern already used by
`CLAUDE_BIN`, `GH_BIN`, `GIT_BIN`, `CLAUDE_TIMEOUT_S`, `CLAUDE_PERMISSION_MODE` and
`CLAUDE_ALLOWED_TOOLS`. No new mechanism, no config file, no CLI flag on the watcher itself. The
unit declares **no `EnvironmentFile=` and no `PassEnvironment=`** (verified), so the only override
surfaces are the root-owned unit (which already requires the owner-approved install path) and an
explicit env var on a manual invocation — both pre-existing boundaries.

Additional hardening I checked and can confirm: both values are **double-quoted** at the call site
(`--model "$CLAUDE_MODEL"`). A malformed or hostile override such as
`CROOKS_BRIDGE_CLAUDE_MODEL='x --dangerously-skip-permissions'` is therefore passed as a *single*
argv element and rejected by the CLI as an invalid model name — it cannot word-split into an extra
flag. The pin does not create an argument-injection path into the permission layer.

**5. Status reports the selected model and effort — PASS.** Executed `status` from the candidate
source (read-only). Actual output:

```
repo            crooksldn-pixel/Shopify-theme
branch          crooks-ai-bridge
model           claude-fable-5-1
effort          high
inbox           bridge/chatgpt-inbox.md
```

(Incidental cross-check: the same run reported `remote now de3573bec8c992c71b21378122fc44132c63c8b5`,
matching the inbox SHA this round is processing.)

**6. Installer preflight fails closed without `--model`/`--effort` — PASS, verified by injection.**
I did not merely read this branch; I forced it. With a stub `claude` on `PATH` whose `--help`
advertises neither flag, preflight produced:

```
[ FAIL ] claude CLI does not expose --model; update Claude Code before installing
[ FAIL ] claude CLI does not expose --effort; update Claude Code before installing
2 problem(s). Fix them before installing.
=== RC: 1 ===
```

Fail-closed is end-to-end, not advisory: `install.sh` line 195 runs `preflight || exit 1`, so a CLI
lacking the flags aborts the install rather than installing a watcher that would silently drop the
pin. The stub was removed immediately after the test.

**7. Tests actually assert the launch contract — PASS, and they assert it properly.**
This was the point most worth scrutinising, because an assertion over static file text would prove
nothing. It is not that. `t_the_prompt_carries_the_safety_contract` calls `watch --once` against a
stub `claude` that records its real argv to `$STUB/claude_args`, and the two new assertions match
`--model claude-fable-5-1` and `--effort high` against that **recorded argv of an actual watcher
launch**. That is a genuine behavioural contract test. The unit-file assertions in
`t_the_unit_does_not_grant_write_access_to_production` are separate and correctly scoped to static
unit text. Both new argv assertions pass.

**8. No safety, isolation, publication, locking, permission, production-read-only or owner-gating
contract weakened — PASS.**
Only two lines were deleted in the whole diff (§3) and neither is safety-bearing. Counts of every
safety-critical directive are byte-for-byte identical between base and candidate:
`CROOKS_BRIDGE_PERMISSION_MODE` 1→1, `CROOKS_BRIDGE_ALLOWED_TOOLS` 1→1, `ReadOnlyPaths` 1→1,
`ReadWritePaths` 3→3, `ProtectSystem` 3→3, `NoNewPrivileges` 1→1, `bypassPermissions` 1→1,
`dangerously` 0→0. The existing negative assertions (`no bypassPermissions`, `no dangerous skip
flag`, `the prompt is not passed as a positional argument`, prompt delivered on stdin) all still
pass. `acceptEdits` is unchanged; the allowed-tool list is unchanged.

## 5. Full watcher test suite result

Run against the exact candidate tree (`/tmp/watcher-verify/watcher`, HEAD `7de5855`):

```
121 passed, 1 FAILED:
  - a freshly staged runtime verifies
```

Same suite against the base (`/tmp/watcher-base/watcher`, HEAD `3d1f65d`):

```
118 passed, 0 failed.
```

So the candidate adds 4 new assertions (all passing, +3 net after the one failure) and turns one
previously-green assertion red. I investigated rather than reporting it as a raw regression.

**Root cause — this is host state, not a code defect.** `install.sh verify` compares the *live
installed* unit at `/etc/systemd/system/crooks-bridge-watcher.service` against the source unit
(`UNIT_DST` vs `UNIT_SRC`, install.sh lines 102–104). Reproduced manually:

```
[  ok  ] matches source: bin/crooks-bridge-watcher
[  ok  ] matches source: systemd/crooks-bridge-watcher.service
[  ok  ] matches source: README.md
[ FAIL ] installed unit DIFFERS from runtime — run: sudo install.sh install
```

Note the three payload files all match; only the *installed* unit differs. Corroborating evidence:

- `/opt/crooks-bridge-watcher/MANIFEST.sha256` records `# source-revision:
  3d1f65df2d93f24ab75c50d5774eacb47b31df43` — the live runtime is the **base**.
- `grep -c CROOKS_BRIDGE_CLAUDE_MODEL /etc/systemd/system/crooks-bridge-watcher.service` → `0`.
  The live unit predates the pin (mtime Sep 18 22:41).

The candidate legitimately changes the unit; the host still runs the pre-pin unit; `verify`
correctly reports the drift. **This failure is the expected and correct signal in this round, and
it will clear the moment the candidate is installed** — which the inbox forbids here. It is
self-resolving, not a defect to fix.

**One observation worth the owner's attention (not a blocker):** this assertion is not hermetic —
it reaches outside its sandbox into `/etc`. Any future candidate that legitimately edits the unit
will be unable to show a fully green suite until after installation, which is an awkward ordering
for a review-then-install workflow. This is a **pre-existing property of the test design, present
at base, not introduced by this candidate.** I have not changed it; flagging it as a possible
follow-up.

Static checks: `shellcheck` and `bashate` are **not installed on this host**, so no lint run was
possible. `bash -n` syntax check passes on all three shell files
(`bin/crooks-bridge-watcher`, `install.sh`, `tests/run-tests.sh`).

## 6. Installed Claude CLI flag support

`claude` resolves to `/usr/local/bin/claude`. Read `claude --help` only (no nested Claude session
was launched, no credential read or printed):

```
--model : PRESENT      --model <model>    Model for the current session. Provide…
--effort: PRESENT      --effort <level>   Effort level for the current session
```

Both flags are supported by the CLI currently installed, so preflight passes on this host today
(full preflight against the candidate: `Preflight clean.`, RC 0). The model id `claude-fable-5-1`
is the documented identifier for Fable 5.1, consistent with the value the candidate pins.

## 7. Secret scan over the exact diff

No `gitleaks`, `trufflehog` or `detect-secrets` binary is installed on this host, so I ran a regex
scan over the exact 6,494-byte candidate diff, restricted to added lines, covering: `sk-*`,
`ghp_`/`gho_`/`github_pat_`, Slack `xox[baprs]-`, AWS `AKIA…`, PEM private-key headers, Shopify
`shpat_`/`shpss_`, `api_key=`/`password=`/`secret=`/`token=` assignments, `Bearer …`, and JWT
`eyJ…`. **Zero matches.**

Consistent with manual reading of the complete diff: every added line is a comment, a
`${VAR:-literal}` default, a `printf`, a `case` substring match, or a test assertion. No credential,
endpoint or account identifier is introduced. **No secret value appears anywhere in this outbox.**

## 8. Defects found

**None in the candidate.** The single test failure is host-state coupling with a verified,
self-resolving root cause (§5). The non-hermetic `verify` assertion is a pre-existing test-design
observation, not a candidate defect.

## 9. What I changed

**Nothing in any tracked repository, and nothing on the running system.** Specifically:

- No commit, no branch, no push, no merge, no tag — in this builder worktree or anywhere else.
- The watcher was **not** installed, staged into the live runtime, started, stopped, enabled,
  disabled, restarted or modified. `/opt/crooks-bridge-watcher` and
  `/etc/systemd/system/crooks-bridge-watcher.service` are untouched.
- `/opt/crooks-os/crooks-assistant` was read-only inspected and never edited, switched or reset.
- The only file written this round is this outbox, `bridge/claude-outbox.md`, per protocol. No
  other file in `/opt/crooks-ai-bridge` was touched, and I have not staged, committed or pushed it.

Scratch artifacts created outside every repository, left in place as evidence and safe to delete:
`/tmp/watcher-verify`, `/tmp/watcher-base`, `/tmp/rtcheck`, `/tmp/rtstate`, `/tmp/cand.diff`.
The temporary stub CLI at `/tmp/stubbin` was deleted immediately after the fail-closed test.

## 10. Repository state

| Repo | Branch | HEAD | Status |
|---|---|---|---|
| **Production** `/opt/crooks-os/crooks-assistant` | `claude/linux-prod-migration-production` | `1cf3a0f3361b79f9de208d80f501543c53c244b5` | clean, untouched |
| Builder `/opt/crooks-builder` | `claude/builder-environment-repair` | `295e483b4f9adcdc3fb58bfb3aa025e2e3f4779b` | clean |
| Bridge `/opt/crooks-ai-bridge` | `crooks-ai-bridge` | `e0c26d2672e34708ecfc3ca410c88f91e95d39ba` | clean apart from this outbox |

**Production branch HEAD: `1cf3a0f3361b79f9de208d80f501543c53c244b5` on
`claude/linux-prod-migration-production` — unchanged by this round.**

**State discrepancy worth noting (no action taken):** the builder worktree is on
`claude/builder-environment-repair`, while the unit sets
`CROOKS_BRIDGE_BUILDER_BRANCH=claude/bridge-builder`. I checked what this affects: that variable is
used only in prompt text and operator guidance messages (lines 174/176/260/267/284) — the watcher
does **not** force-checkout or reset the builder to it. So the effect is cosmetic (the prompt names
a branch I am not actually on) and harmless this round, since this was a read-only verification
with no commits. Flagging it because a future inbox asking for committed implementation work would
land on an unexpected branch. I did not switch it — changing the builder's branch is not in scope
for this inbox.

## 11. Service and server state (observed read-only, unchanged)

- `crooks-bridge-watcher`: **active**, **enabled** at boot, running since `2026-09-18 22:41:37 UTC`
  — same process throughout this round; not restarted.
- Live runtime provenance: installed from `/opt/crooks-watcher-review/watcher` at source-revision
  `3d1f65d` (the base). The running watcher is **unpinned** — it still inherits the account/CLI
  default model. That is precisely the exposure this candidate closes.
- Port 8000: `LISTEN 127.0.0.1:8000` only. **Not publicly exposed.** Loopback binding intact.

## 12. Safety constraints — all preserved

`writes_enabled` false; `CROOKS_WRITES_LOCAL_OWNER` false; FastAPI bound to 127.0.0.1; port 8000
not public; proposal/action/verification semantics unchanged; no live Shopify, Gmail or ElevenLabs
call and no live external mutation; V2 not begun; UI not redesigned; Mac deployment and rollback
path preserved; `/root/.claude` writable (preflight confirmed); no secret printed or committed.
Nothing in this round could affect any of these — the diff is confined to `watcher/`, and I
executed no installation.

## 13. Decisions / questions needing owner review

1. **Installation is the owner's call and was deliberately not taken.** The inbox approved making
   the watcher deterministic but explicitly barred installing, staging or restarting this round —
   correctly, since a running watcher must not rewrite itself while validating that rewrite. The
   candidate is verified and ready; **it is not in effect.** Until installed, the running watcher
   remains unpinned. Installing requires explicit owner approval, which the inbox did not give and
   which I have not assumed.
2. **The install must not be run from inside a watcher-triggered round** — including a future one.
   It should be executed by the owner at a terminal while the watcher is idle, or with the service
   stopped first. Both are owner actions.
3. **Optional follow-up:** make the `verify` test hermetic so a legitimate unit change can show a
   green suite before installation (§5). Pre-existing, low priority, needs a decision before anyone
   writes it.
4. **Optional follow-up:** reconcile `CROOKS_BRIDGE_BUILDER_BRANCH` with the builder's actual
   branch (§10) before any inbox that asks for committed implementation work.

**Suitability verdict: the candidate is suitable for a separate, owner-approved installation step.**
All eight required properties verified, the only test failure explained and benign, CLI support
confirmed, secret scan clean, no safety contract weakened.

## 14. Exact minimal installation/verification sequence — NOT EXECUTED

Provided as requested for a future owner-approved round. **I have not run any of this.** Requires
root and explicit owner approval. Run at a terminal with the watcher idle — not from inside a
watcher round.

```bash
# 0. Owner approval required before this point. Confirm the watcher is idle.
systemctl stop crooks-bridge-watcher

# 1. Bring the canonical install source to the approved candidate.
cd /opt/crooks-watcher-review
git fetch origin chatgpt/bridge-fable-5-1-pin-2026-09-19
git status --porcelain                       # must be empty
git checkout claude/crooks-bridge-watcher-review
git merge --ff-only origin/chatgpt/bridge-fable-5-1-pin-2026-09-19
git rev-parse HEAD                           # must print 7de58555ee954e8561bb0f3bb6d7283715517b62

# 2. Re-verify on the real source tree before installing.
cd /opt/crooks-watcher-review/watcher
bash tests/run-tests.sh                      # expect the verify-drift failure only, until step 3
bash install.sh preflight                    # must print "Preflight clean." and exit 0

# 3. Install (preflight runs again and gates this; --no-start keeps it stopped).
sudo bash install.sh install --no-start

# 4. Confirm the installed tree and unit now match the approved source.
bash install.sh verify                       # must be 0 mismatches, incl. "installed unit matches runtime"
bash tests/run-tests.sh                      # must now be 122 passed, 0 failed
grep CROOKS_BRIDGE_CLAUDE_ /etc/systemd/system/crooks-bridge-watcher.service

# 5. Start and confirm the pin is live.
sudo systemctl daemon-reload
sudo systemctl start crooks-bridge-watcher
systemctl is-active crooks-bridge-watcher
/opt/crooks-bridge-watcher/bin/crooks-bridge-watcher status   # must show model claude-fable-5-1 / effort high
```

Rollback if step 4 or 5 fails: `git checkout 3d1f65df2d93f24ab75c50d5774eacb47b31df43` in
`/opt/crooks-watcher-review`, re-run `sudo bash install.sh install`, restart the service.

Step 4's "122 passed, 0 failed" is the concrete post-install expectation implied by §5 — the
verify-drift assertion goes green once the installed unit carries the pin. If it does not, the
install did not take and step 3 should be re-examined before starting the service.

## 15. Stop

Verification complete and reported. **Engineering Orchestrator V1 implementation has not been
begun**, per the inbox. Nothing further was done. Awaiting owner decision on §13.1 (installation).

Inbox SHA processed: `de3573bec8c992c71b21378122fc44132c63c8b5`
