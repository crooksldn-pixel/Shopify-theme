# CROOKS AI bridge watcher

Runs Claude Code automatically when ChatGPT writes to the bridge inbox, so nobody has to type
"check inbox" again.

    ChatGPT / owner  ──push──>  bridge/chatgpt-inbox.md  (branch: crooks-ai-bridge)
                                        │
                        watcher notices the BLOB SHA changed (polls every 30s)
                                        │
                     flock ── one Claude at a time, fail-closed guards
                                        │
             claude --print, run in the BUILDER worktree /opt/crooks-builder
                        (the live checkout is never touched)
                                        │
                     Claude WRITES bridge/claude-outbox.md and stops
                                        │
            the WATCHER stages that one file, commits, pushes crooks-ai-bridge,
                       and verifies the remote blob actually changed
                                        │
                  only now is the inbox SHA recorded as processed

## Why the blob SHA and not the branch HEAD

Claude pushes the outbox at the end of every run, which moves HEAD. A watcher that triggered on
HEAD would trigger itself, forever. It watches the inbox file's blob SHA, so only someone
writing to the inbox starts any work. There is a test for exactly this
(`the outbox moving does not retrigger`).

## Why the watcher publishes, and not Claude

Claude Code's permission layer can refuse a push to a shared repository — it did, twice, during
this project, and each time a person had to run the push by hand. That is the exact manual step
the watcher exists to remove, so publication is the watcher's job, not Claude's.

It is also narrower. Claude writes one file and stops. The watcher stages exactly
`bridge/claude-outbox.md`, refuses if anything else in the bridge worktree changed, commits,
pushes only `crooks-ai-bridge`, and then asks GitHub whether the blob really moved. Application
code cannot travel down the communication channel even if a run goes wrong, and a push that
silently changed nothing is treated as a failure rather than a success.

## The builder worktree

Headless Claude works in `/opt/crooks-builder` on `claude/bridge-builder`, never in
`/opt/crooks-os/crooks-assistant`. A headless agent and a person cannot share a working tree:
whoever writes second wins and neither knows. The watcher refuses to start if its target resolves
to the production checkout, if the builder is missing, or if the builder is dirty — and it never
resets or discards what it finds there.

## What counts as "processed"

Claude exiting 0 is not enough. The outbox blob on the remote must also have changed — otherwise
the run finished without telling anyone anything, and the instruction has not been answered. A
run that fails either test is left unprocessed and retried with backoff (60s, 120s, 240s …
capped at 15 minutes), so a broken run never silently swallows an instruction and never spins.

## Files

    bin/crooks-bridge-watcher                 the worker (loop | --once | status | seed)
    systemd/crooks-bridge-watcher.service     the unit
    install.sh                                install | uninstall | status | preflight
    tests/run-tests.sh                        38 assertions, no network, no real Claude

## Use

    sudo ./install.sh preflight     check prerequisites, change nothing
    sudo ./install.sh install       install, seed, enable, start
    ./install.sh status             what it has processed, what is pending, is it running
    journalctl -u crooks-bridge-watcher -f
    sudo ./install.sh uninstall     stop, disable, remove   (--purge also deletes state)

Install seeds the state with the inbox as it stands, so the watcher starts listening from now
rather than re-executing instructions that have already been dealt with.

## State

    /var/lib/crooks-bridge/last-inbox-sha   the last inbox proven processed  (systemd StateDirectory, 0700)
    /var/lib/crooks-bridge/failures         consecutive failures, drives the backoff
    /var/lib/crooks-bridge/last-run         ok|failed, when, which SHA
    /run/crooks-bridge/watcher.lock         the exclusive run lock (tmpfs — a reboot cannot strand it)

## Security

No HTTP endpoint, no webhook, no listening socket, no firewall change: it polls outbound over
the GitHub API using the `gh` CLI's existing login. No token is read, printed or stored by any
of this. It runs as root only because Claude Code's Max login lives in `/root/.claude` and is
rewritten in place on token refresh, so HOME stays writable.

Claude is launched with `--permission-mode acceptEdits` and an explicit tool list — **not**
`bypassPermissions`, and no `--dangerously-skip-permissions`. Two tests assert that. The prompt
requires it to preserve every CROOKS safety constraint, to stop and report rather than proceed
when something needs the owner's approval, to never fabricate approval, and to never put a
secret value in the outbox.

Separate from `crooks-assistant.service` in every respect. Installing, stopping or removing this
watcher does not touch the assistant.
