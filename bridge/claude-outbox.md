# CLAUDE OUTBOX — latest handoff only

**Timestamp:** 2026-09-19 (session clock 22:20 UTC)
**Inbox commit processed:** `573f993` — blob `a093d720ab70bfb698d53e8c2ac4838bada0b3a4`
("bridge: final pre-install isolation and packaging fixes")
**Previously processed:** `afe4067`, `7f4e598`, `1d71681`

---

## 0. Result

```
watcher review branch   claude/crooks-bridge-watcher-review
new commit              0100f1d83e4a293e74b46bd38f90ded8c54a5fc4   (pushed)
previous commit         e60af6bdaf0f488ace9bb5ebcacc909a76fbef9d
tests                   116 passed, 0 failed
```

Both findings were correct and are fixed. **Nothing is installed, enabled or running.** The
production branch is untouched at `e43aecd`, its working tree still holds the same 25 uncommitted
paths, and no secret, service or route was touched.

**One consequence of finding 1 that was not in the brief, and had to be fixed with it:** the
BRIDGE worktree was also a linked worktree of `/opt/crooks-os`. Removing `/opt/crooks-os` from
`ReadWritePaths` without converting it too would have broken outbox publication — the exact thing
the previous round made watcher-owned. It is now a standalone clone as well. Details in §2.

## 1. Builder is a standalone clone

Before changing anything, re-verified: builder clean (0 paths), 0 unpushed commits; bridge clean,
0 unpushed commits. Nothing was discarded.

```
$ git -C /opt/crooks-os worktree remove /opt/crooks-builder
$ git clone --no-hardlinks --single-branch --branch claude/bridge-builder \
      /opt/crooks-os /opt/crooks-builder
$ git -C /opt/crooks-builder remote set-url origin https://github.com/crooksldn-pixel/Shopify-theme.git
$ git -C /opt/crooks-os branch -D claude/bridge-builder      # single owner of the branch
```

`--no-hardlinks` is deliberate. A plain local clone hardlinks `.git/objects`, which means the
builder's object files are the *same inodes* as production's — and systemd's `ReadWritePaths`
works on paths, not inodes, so a write through the builder path would have reached production's
objects. Git never rewrites objects in place, so it would not have happened in practice, but the
requirement was that the sandbox not permit it. Verified:

```
$ find /opt/crooks-builder/.git/objects -type f -links +1 | wc -l
0
```

## 2. Builder topology (exact)

```
/opt/crooks-os              claude/crooks-assistant-build-lgxlau @ e43aecd
                            the production repository. NOT writable by the watcher.
                            Still has the 25 uncommitted migration paths.

/opt/crooks-builder         STANDALONE CLONE, own .git, claude/bridge-builder @ e43aecd, clean
                            origin -> github.com/crooksldn-pixel/Shopify-theme
                            git-common-dir: /opt/crooks-builder/.git
                            headless Claude works here, and only here

/opt/crooks-ai-bridge       STANDALONE CLONE, own .git, crooks-ai-bridge, 196K
                            (single-branch clone of an orphan branch holding two files)
                            the watcher publishes the outbox from here

/opt/crooks-review          linked worktree, claude/linux-prod-migration-review @ 1cf3a0f
/opt/crooks-watcher-review  linked worktree, claude/crooks-bridge-watcher-review @ 0100f1d
                            review checkouts only; the watcher never touches them
```

The last two remain linked worktrees deliberately: they exist for you to read, the watcher has no
access to them, and converting them would cost a gigabyte each for no benefit.

`git worktree list` on production now shows only itself and the two review checkouts — neither the
builder nor the bridge is attached to it any more.

## 3. Unit write paths (exact)

```
ProtectSystem=strict
ReadWritePaths=/opt/crooks-builder
ReadWritePaths=/opt/crooks-ai-bridge
ReadWritePaths=/root
ReadOnlyPaths=/opt/crooks-os
```

`/opt/crooks-os` is absent from `ReadWritePaths` and named in `ReadOnlyPaths`. With
`ProtectSystem=strict` it would already be read-only by omission; it is stated explicitly so the
property can be pointed at in the unit rather than inferred from an absence. `/root` stays
writable for one reason: the Claude Max login at `/root/.claude` is rewritten in place on token
refresh.

**Guard, strengthened beyond what was asked.** The watcher refuses to start if:
- the target resolves to the production repo ROOT **or any path nested inside it** — not one exact
  subdirectory, since `/opt/crooks-os/anything` is the same mistake wearing a different path;
- the target's `git-common-dir` resolves inside production. That is what a linked worktree looks
  like from outside, and it is checked because the difference between a clone and a linked
  worktree is invisible from the path alone — and the sandbox now depends on it;
- the builder is missing (it prints the exact clone command), or dirty (reported, never reset);
- another run holds the flock, or another Claude has its cwd inside the builder.

## 4. Install / copy sequence (exact)

The reviewed tree is the source of truth. `install.sh` installs *itself* into the canonical
runtime directory:

1. `preflight` — source files, claude CLI, gh auth, flock, systemd, both clones, builder clean,
   Max login writable. Prints the **source revision** it is about to install.
2. `stage` — for each payload entry, `install -D -m <mode> <source> <runtime>`:
   ```
   bin/crooks-bridge-watcher                 0755
   systemd/crooks-bridge-watcher.service     0644
   README.md                                 0644
   ```
   Tests are **not** shipped into runtime: they exist to be run against the source before you
   trust it, and putting them in the path executed as root only widens what is on disk.
3. Write `MANIFEST.sha256` — a sha256 per installed file, plus `installed-from`,
   `source-revision` and `installed-at`. Rewritten from what is actually on disk, not from what
   was intended.
4. `verify` — source vs runtime byte-for-byte, modes, and installed unit vs runtime. **Install
   aborts if this fails.**
5. `install -m 0644 <runtime unit> /etc/systemd/system/` — the unit comes from the verified
   runtime copy, never straight from source.
6. `systemctl daemon-reload`; seed the state at the current inbox so the first act is not to
   re-execute old instructions; `systemctl enable`; start (unless `--no-start`).

**The ambiguity you found is gone at the root: `/opt/crooks-bridge-watcher` no longer exists.** It
was an unversioned working copy, and you were right that "approve 0100f1d" could have installed
whatever was sitting there. I deleted it. The runtime directory is now created only by
`install.sh`, only from a reviewed tree, and only with a manifest naming the commit. Proven:

```
$ /opt/crooks-watcher-review/watcher/install.sh stage      (into a scratch dir)
# installed-from:   /opt/crooks-watcher-review/watcher
# source-revision:  0100f1d83e4a293e74b46bd38f90ded8c54a5fc4
$ git -C /opt/crooks-watcher-review rev-parse HEAD
0100f1d83e4a293e74b46bd38f90ded8c54a5fc4
$ /opt/crooks-watcher-review/watcher/install.sh verify      (before install)
[ FAIL ] no manifest at /opt/crooks-bridge-watcher/MANIFEST.sha256 — runtime was not installed
```

`install.sh verify` answers "is what is running what I reviewed?" at any time.

## 5. Tests and verification

```
$ /opt/crooks-watcher-review/watcher/tests/run-tests.sh
116 passed, 0 failed.
```

New this round: a nested path inside the production repo is refused; a linked worktree of
production is refused (and a standalone clone is accepted, so the guard cannot pass by refusing
everything); staging installs exactly the payload with modes 0755/0644; the staged runtime is
byte-identical to source; staging twice is safe and idempotent; `verify` detects a tampered
runtime and names the file; the manifest records provenance; and the unit grants no write access
to production.

Everything else you asked for in step 4:

```
systemd-analyze verify                     clean
installer preflight (final design)         clean, 13/13 ok
/opt/crooks-os in ReadWritePaths           NO
builder .git                               own directory; common-dir /opt/crooks-builder/.git
builder clean                              0 changed paths
builder hardlinks shared with production   0
bridge .git                                own directory
production branch                          claude/crooks-assistant-build-lgxlau @ e43aecd
production working tree                    25 paths, unchanged by this round
```

## 6. Documentation

README no longer hard-codes a test count — it points at the suite, which prints its own. Added a
section explaining the source-of-truth/runtime split and why `verify` exists.

## 7. The one command to install the reviewed watcher, after approval

```
sudo /opt/crooks-watcher-review/watcher/install.sh install
```

That tree is `claude/crooks-bridge-watcher-review` @ `0100f1d` — the commit you are reviewing. It
preflights, copies into `/opt/crooks-bridge-watcher`, verifies byte-identity, installs the unit
from the verified copy, seeds, enables and starts. Add `--no-start` to stop short of starting.

To install a different reviewed commit, check it out and run that tree's `install.sh`; the
manifest will name whatever revision it came from.

## 8. Blockers to closing Termius for the normal loop

**After installing this, for the normal ChatGPT ↔ Claude round trip: none.** You write the inbox;
within 30s the watcher runs Claude in the builder clone; Claude writes the handoff; the watcher
publishes it and verifies the blob moved. No terminal, no tmux, no "check inbox", no "push the
outbox".

Remaining, and honestly:

1. **The install itself** — one command, one approval. Until then nothing is automatic.
2. **Approval gates, by design** — secrets, CROOKS install/start, Tailscale Serve, live
   verification. Claude stops and writes what it is waiting for. That is the property you asked
   for, but those rounds still end with you.
3. **Pushing implementation branches.** Outbox publication is watcher-owned; pushing
   `claude/bridge-builder` is still Claude-side and can be refused by its permission layer. It
   reports and stops rather than widening. Making branch publication watcher-owned is the same
   pattern applied once more, and you said not to over-expand this round.
4. **A stuck round.** Backoff caps at 900s and it keeps retrying; a genuinely stuck one needs a
   person. `install.sh status` and `journalctl -u crooks-bridge-watcher -f` are the two commands.
5. **The builder is at `e43aecd`, which does not contain the Phase 1–4 migration.** Those 25 paths
   are still uncommitted in production and the review branch is a copy, not a move. Headless
   rounds would start from a tree without the migration. This is the one that quietly limits
   everything else, and it needs your decision rather than mine.

## 9. Exact proposed next step

1. Review `claude/crooks-bridge-watcher-review` @ `0100f1d`.
2. If it passes: `sudo /opt/crooks-watcher-review/watcher/install.sh install`.
3. Tell me where the Phase 1–4 work should land (§8.5) — merge or cherry-pick
   `claude/linux-prod-migration-review` @ `1cf3a0f` into the production branch, then re-point
   `claude/bridge-builder` at it. I will do it in a round of its own; it is a production-branch
   change and you have not approved one.
4. Then, separately and explicitly: secrets, then Phase 5.

Stopping here as instructed.

---
*No API keys, passwords, OAuth tokens, cookies, private keys or secret values appear in this file.*
