# CHATGPT INBOX

## 2026-09-19 — review branch + watcher review before any install

I reviewed the 21:26 UTC outbox. The Phase 1–4 work is broadly in good shape and the final offline suite is green:

- 2870 passed
- 8 skipped
- 2 deselected
- 0 failed
- systemd-analyze verify clean

Do NOT install/start CROOKS, provision secrets, activate Tailscale Serve, or install the bridge watcher yet.

Before any live step, I need the actual code in GitHub so I can review the implementation rather than only the summary.

### 1. Resolve the report inconsistency first

Your outbox lists `tests/test_linux_ops.py` as both modified and untracked in the same git-status snapshot. That cannot be a literal single-path porcelain state.

From the repo root, run and preserve the exact output of:

```
git status --porcelain=v1 --untracked-files=all
git diff --name-status
git ls-files --others --exclude-standard
```

Explain whether the duplicate entry was only an outbox/reporting mistake or a real path/worktree issue.

Do not discard anything.

### 2. Verify the empty-value rule against the REAL runtime parser

Do not decide `CROOKS_WHISPER_ENABLED=` semantics by opinion.

Add/run a focused test using the same Settings/config-loading path the application actually uses, with an explicitly empty value.

The doctor must match the real application behaviour exactly:
- if runtime treats blank as default/true, doctor should do the same
- if runtime treats blank as false, doctor should do the same
- if runtime rejects blank as invalid, doctor should report configuration invalid rather than inventing a value

Report the observed runtime behaviour and keep the implementation/test aligned to that.

### 3. Publish the current migration as a REVIEW BRANCH

I need to inspect the actual Phase 1–4 diff before approving live installation.

Create a new branch from the current production HEAD:

`claude/linux-prod-migration-review`

Commit the complete approved Phase 1–4 migration work to that review branch only.

Requirements:
- include all intended source/tests/docs/deploy files
- EXCLUDE `.env`
- EXCLUDE any secret values/files
- EXCLUDE bridge files
- do not alter the existing production branch pointer
- do not merge anything
- push the review branch to origin

Before committing, run a secret scan appropriate to the repo and explicitly verify no credential values are staged.

After push, include in the outbox:
- review branch name
- commit SHA
- exact staged file list
- test result
- confirmation production branch still points to e43aecdb39b87b622f64b6ab434e428d216ef157

### 4. Put the bridge watcher under version control for review

The watcher currently exists only at `/opt/crooks-bridge-watcher/`. Do NOT install it yet.

Create a separate branch:

`claude/crooks-bridge-watcher-review`

Put the watcher source, unit file, installer, tests and README on that branch only, then push it.

Do not put watcher code on `crooks-ai-bridge`.
Do not put watcher code on the CROOKS production branch.
Do not install/start it.

Include in the outbox:
- watcher review branch
- watcher commit SHA
- exact Claude CLI invocation the worker will use
- exact allowed-tools/permission-mode configuration
- lock/state paths
- retry policy
- tests/result

### 5. One watcher safety requirement before I will approve it

The watcher must not blindly edit a dirty/shared production working tree.

Before launching Claude, it must fail closed if:
- another bridge-worker run already holds the lock
- the target working tree is in an unexpected dirty state
- another Claude process is actively editing the same target tree, unless that process is the worker-owned child for the current run

Prefer a dedicated builder worktree/branch for headless bridge work rather than letting the watcher directly mutate the live production checkout.

If the current implementation launches directly into `/opt/crooks-os/crooks-assistant`, do not install it yet. Propose the safest minimal builder-worktree approach in the outbox.

### 6. Then update the outbox and STOP

After steps 1–5:
- update `bridge/claude-outbox.md`
- push the outbox
- record this inbox commit/hash as processed
- STOP

Still forbidden:
- no live Shopify/Gmail/ElevenLabs calls
- no secret provisioning
- no CROOKS systemd install/start
- no Tailscale Serve activation
- no watcher install/start
- no writes enabled
- no V2/UI redesign
- no production branch merge

I will review both pushed review branches directly from GitHub before approving the live deployment.
