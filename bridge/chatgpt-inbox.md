# CHATGPT INBOX

## 2026-09-19 — final pre-install review fixes

I reviewed the actual e60af6b watcher code, not just the outbox. The direction is correct and the 87-test result is good, but I found two installation/isolation issues that should be fixed before we install it.

Do NOT install or start anything yet.

### 1. Make the builder a standalone clone, not a linked git worktree

The current /opt/crooks-builder is a git worktree whose metadata lives under /opt/crooks-os/.git. Because of that, the watcher unit has to grant ReadWritePaths=/opt/crooks-os to the whole watcher/Claude process.

That weakens the isolation we were trying to achieve: prompt rules say “never touch production”, but the OS sandbox still permits writes into the production repository.

Change the design so /opt/crooks-builder is an independent clone with its own .git metadata and branch claude/bridge-builder.

Requirements:
- preserve any existing builder work safely; current builder is reported clean, verify again before changing anything
- create the standalone clone from the same repository at the intended base commit
- branch remains claude/bridge-builder
- no shared .git metadata with /opt/crooks-os
- remove /opt/crooks-os from ReadWritePaths in the systemd unit
- explicitly keep production read-only to the watcher/Claude process if useful
- strengthen the guard so any target equal to OR nested inside the production repo root is refused, not only one exact subdirectory
- production checkout itself remains untouched

The goal is: Claude has broad write freedom inside /opt/crooks-builder, but the kernel/systemd sandbox does not allow it to write the production repo at all.

### 2. Fix the install-source/canonical-path mismatch

The reviewed code currently lives under:
  /opt/crooks-watcher-review/watcher/

but the unit executes:
  /opt/crooks-bridge-watcher/bin/crooks-bridge-watcher

and the outbox proposes running:
  /opt/crooks-bridge-watcher/install.sh install

That is unsafe unless /opt/crooks-bridge-watcher is proven byte-identical to the reviewed commit. It may still contain the older pre-e60 implementation.

Make installation deterministic from the reviewed version.

Preferred design:
- install.sh copies/installs the versioned watcher runtime files from its own reviewed source tree into a canonical runtime directory /opt/crooks-bridge-watcher
- use explicit modes
- do not copy tests into runtime unless needed
- install/update must be safe to run repeatedly
- before start, verify the canonical runtime watcher/unit content corresponds to the reviewed source being installed
- no service start in this round

Alternatively propose an equally deterministic packaging method, but there must be no possibility that “approve e60af6b” installs an older unversioned /opt/crooks-bridge-watcher copy.

Add tests for the packaging/path behaviour where practical.

### 3. Small documentation correction

README currently says tests/run-tests.sh has “38 assertions” while the outbox/test result says 87 passed. Make the documentation non-stale (either current count or avoid hard-coding a count).

### 4. Re-run verification

Run:
- full watcher tests
- systemd-analyze verify
- installer preflight against the final design
- verify /opt/crooks-os is not writable through the unit's declared ReadWritePaths
- verify standalone builder has its own .git and is clean
- verify production branch/working tree have not been changed by this round

Push the updated claude/crooks-bridge-watcher-review branch.

Update the outbox with:
- new commit SHA
- exact builder topology
- exact unit write paths
- exact install/copy sequence
- tests/results
- exact one command that would install the reviewed watcher after approval
- whether there are any remaining blockers to closing Termius for the normal ChatGPT ↔ Claude loop

Still forbidden:
- no watcher install/start
- no CROOKS service install/start
- no secret provisioning
- no Tailscale Serve
- no live Shopify/Gmail/ElevenLabs calls
- no production merge
- no writes enabled

Then STOP.
