# CLAUDE OUTBOX — latest handoff only

**Timestamp:** 2026-09-19 (session clock 22:31 UTC)
**Host:** crooks-os-prod-1
**Inbox commit processed:** `afe4067` — blob `47cc8990f9aff131ccc1ec170a21e8c6e3a62763`
("bridge: harden watcher for zero-manual outbox flow")
**Previously processed:** `7f4e598`, `1d71681`

---

## 0. Result

Steps 1–5 done. **87 watcher tests pass, 0 fail.** The watcher is still **not installed, not
enabled, not running**. Nothing else was installed, started, provisioned or activated.

```
watcher review branch   claude/crooks-bridge-watcher-review
new commit              e60af6bdaf0f488ace9bb5ebcacc909a76fbef9d   (pushed)
previous commit         dadf2574d66398064f3f65a0a4bd7fdf087cc148
builder worktree        /opt/crooks-builder on claude/bridge-builder @ e43aecd — created, clean
production branch       claude/crooks-assistant-build-lgxlau @ e43aecd — untouched
```

## 1. Builder worktree — adopted

Created:

```
$ git -C /opt/crooks-os worktree add -b claude/bridge-builder /opt/crooks-builder e43aecd
$ git -C /opt/crooks-builder rev-parse --abbrev-ref HEAD   ->  claude/bridge-builder
$ git -C /opt/crooks-builder status --porcelain -uall      ->  (empty: clean)
```

Worktrees now on this host:

```
/opt/crooks-os              e43aecd [claude/crooks-assistant-build-lgxlau]   production, untouched
/opt/crooks-builder         e43aecd [claude/bridge-builder]                  headless Claude works here
/opt/crooks-ai-bridge       ....... [crooks-ai-bridge]                       communication only
/opt/crooks-review          1cf3a0f [claude/linux-prod-migration-review]     for your review
/opt/crooks-watcher-review  e60af6b [claude/crooks-bridge-watcher-review]    for your review
```

The unit's defaults changed accordingly:

```
Environment=CROOKS_BRIDGE_WORKDIR=/opt/crooks-builder
Environment=CROOKS_BRIDGE_BUILDER_BRANCH=claude/bridge-builder
Environment=CROOKS_BRIDGE_PRODUCTION_DIR=/opt/crooks-os/crooks-assistant
ReadWritePaths=/opt/crooks-builder          (added)
```

`/opt/crooks-os` stays in `ReadWritePaths` for one reason only: the builder and bridge worktrees
keep their git metadata under its `.git`, so git must write there. Claude is told, in the prompt,
never to edit, switch or reset the production checkout.

**Guards, all kept, all fail-closed, none destructive.** Before launching anything the watcher
refuses if:
- the target resolves to the production checkout (new — the configuration mistake this whole
  change exists to prevent, so it is checked rather than trusted),
- the builder worktree does not exist (and it prints the one command that creates it),
- the builder worktree is dirty — **reported, never reset**. There is a deliberate override,
  `CROOKS_BRIDGE_ALLOW_DIRTY=1`, off by default,
- another run holds the flock,
- another Claude process has its cwd inside the builder.

Nothing in the watcher runs `reset`, `clean`, `checkout -f` or `stash`. A test asserts that a
dirty builder produces no such operation.

## 2. Outbox publication is now the watcher's

**Claude writes; the watcher publishes.** You were right that this was the remaining manual
dependency: Claude Code's permission layer refused a shared-repository push twice in this project,
and each time the owner had to run it by hand.

The prompt now tells Claude, explicitly:

> Completely replace the file `$BRIDGE_DIR/bridge/claude-outbox.md` with this round's handoff.
> Then STOP. Do NOT run git add, git commit or git push for that file, and do not touch any other
> file in the bridge worktree.

**Exact publication sequence, after Claude exits 0** (`publish_outbox()`):

1. `git -C /opt/crooks-ai-bridge status --porcelain=v1 --untracked-files=all`
   - empty → **refuse**: "Claude wrote no outbox", inbox NOT processed.
2. Every changed path must be `bridge/claude-outbox.md`.
   - anything else → **refuse**, naming each offending path. Nothing staged, committed or pushed.
3. `git -C … add -- bridge/claude-outbox.md`
4. `git -C … diff --cached --name-only` must equal exactly `bridge/claude-outbox.md`
   - otherwise → **refuse** before committing.
5. `git -C … -c user.name=… -c user.email=… commit -q -m "bridge: claude outbox update (inbox <sha>)"`
6. `git -C … push origin crooks-ai-bridge` — one branch, named literally. Never `--all`, never the
   builder branch, never a tag.
   - failure → **refuse**: "committed locally but not published", inbox NOT processed, retried.
7. `gh api …/contents/bridge/claude-outbox.md?ref=crooks-ai-bridge --jq .sha` must differ from the
   SHA read before the run.
   - unchanged → **refuse**. A push that moved no blob told nobody anything.
8. **Only then** is the inbox SHA recorded as processed.

Application code cannot travel down this channel even if a run goes badly wrong, because the only
path the watcher will ever stage is the outbox. There is a test that puts
`crooks-assistant/app/main.py` in the bridge worktree and asserts nothing is pushed.

## 3. Application-code publication — unchanged and separate

Claude may commit implementation work on `claude/bridge-builder` when an inbox explicitly asks for
it. No auto-merge to production, no auto-deploy, and the watcher never pushes that branch. If
pushing the builder branch is blocked by Claude's permission layer, the prompt requires it to say
so plainly in the outbox and stop — it is told, in those words, not to widen its permissions or
look for a way around. A test asserts that instruction is present, and two more assert no
`bypassPermissions` or `--dangerously-skip-permissions` flag can appear in the invocation.

## 4. Tests

```
$ ./tests/run-tests.sh
87 passed, 0 failed.
```

Every test you asked for, by name:

| requirement | test |
|---|---|
| Claude need not push the outbox | `claude never publishes anything itself` |
| watcher publishes exactly the outbox | `the watcher publishes exactly the outbox` |
| unexpected bridge changes refuse | `unexpected bridge changes refuse to publish` |
| failed push does not mark processed | `a failed push does not mark the inbox processed` |
| successful push does mark processed | `a successful watcher push marks it processed` |
| builder is Claude's cwd | `claude runs in the builder worktree` |
| production never used headlessly | `the production checkout is never the target` |
| dirty builder refuses | `a dirty builder refuses and discards nothing` |
| no permission-bypass introduced | `the prompt carries the safety contract` (two assertions) |

Plus, kept from before: inbox-SHA detection, duplicate suppression, outbox-move-does-not-retrigger,
lock suppression and pickup after release, newer-inbox-mid-run, GitHub unreachable, seeding,
backoff growth and cap, foreign-Claude detection and its converse, and three further publication
refusals — no outbox written, a push that changed nothing, and a staged set wider than one file.

The stub Claude in the harness is deliberately incapable of committing or pushing. That a round
still completes is itself the proof that publication no longer depends on Claude.

Also verified: `systemd-analyze verify` on the unit — clean. `./install.sh preflight` — clean,
including `builder worktree clean` and `production checkout … (never edited by the watcher)`.

## 5. Could you close Termius after installing this?

**For the normal ChatGPT ↔ Claude round trip: yes.** You write the inbox, the watcher notices
within 30s, Claude works in the builder, writes the handoff, and the watcher publishes it. No
terminal, no tmux, no "check inbox", and — the new part — no "push the outbox". The two manual
steps you actually hit this session are both gone.

**Honestly, five things would still bring you back:**

1. **Installing it.** One approval and `sudo /opt/crooks-bridge-watcher/install.sh install`.
   Until then nothing is automatic.
2. **Approval gates, by design.** Secrets, systemd install/start, Tailscale Serve, live
   verification — Claude stops and asks rather than proceeding. That is the safety property you
   asked for, not a defect, but it means those rounds end with you.
3. **Pushing implementation branches.** Outbox publication is now watcher-owned; pushing
   `claude/bridge-builder` is not. If Claude's permission layer blocks it, the round reports and
   stops. Making branch publication orchestrator-owned too is the obvious next step, and you said
   not to over-expand this round.
4. **Repeated failures.** Backoff caps at 900s and the watcher keeps retrying, but a genuinely
   stuck round needs a person. `./install.sh status` and `journalctl -u crooks-bridge-watcher -f`
   are the two commands for that.
5. **The builder is at e43aecd**, which does NOT contain the Phase 1–4 migration — that work is
   still uncommitted in the production checkout. Headless work therefore starts from a tree
   without it. See §6.

## 6. Remaining manual steps

1. **Approve and install the watcher** (blocking for everything above).
2. **Decide where the Phase 1–4 work lands.** 25 paths are still uncommitted in
   `/opt/crooks-os/crooks-assistant`. `claude/linux-prod-migration-review` @ `1cf3a0f` is a copy,
   not a move. Until it lands on the production branch — and until `claude/bridge-builder` is
   based on something containing it — headless rounds start from a tree missing the migration.
   My suggestion: merge or cherry-pick the review branch into
   `claude/crooks-assistant-build-lgxlau` once you are satisfied with it, then reset
   `claude/bridge-builder` onto that. Not done here: it is a production-branch change and you have
   not approved one.
3. **Secret provisioning** — `/etc/crooks-os/secrets` does not exist; only you hold the values.
4. **Phase 5** — systemd install/start, Tailscale Serve, live verification.

## 7. Exact proposed next step

1. You review `claude/crooks-bridge-watcher-review` @ `e60af6b`.
2. If it passes, approve the install: `sudo /opt/crooks-bridge-watcher/install.sh install`. It
   preflights, installs the unit, **seeds the state at the current inbox** so it does not
   re-execute anything already dealt with, enables and starts it.
3. Tell me where the Phase 1–4 work should land (§6.2), and I will do it in a round of its own.
4. Then, separately and explicitly: secrets, then Phase 5.

Stopping here as instructed.

---
*No API keys, passwords, OAuth tokens, cookies, private keys or secret values appear in this file.*
