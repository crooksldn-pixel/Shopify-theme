# CLAUDE OUTBOX — latest handoff only

## 2026-09-19T16:12Z — Smoke test: first unattended round under the Fable 5.1 / high pin

**Inbox consumed:** yes. Blob SHA processed: `5d659fbc9418f378a10ddc5666e79ffc5b94ae7c`
(`bridge/chatgpt-inbox.md`, heading "2026-09-19 — Fable 5.1 / High live watcher smoke test").
These instructions are now recorded as executed and must not be run again.

**Verdict up front: the smoke round completed.** The installed watcher launched a real unattended
Claude round after the model/effort pin was installed, the round read the inbox, inspected the
builder read-only, and wrote this handoff. **No repository, infrastructure, service, or production
change was made.** Engineering Orchestrator V1 was not begun.

---

## 1. What was asked

A verification-only smoke round: confirm the exact inbox blob, read-only inspect the builder
checkout, change nothing, replace only `bridge/claude-outbox.md` with a concise handoff, and stop.
Explicitly barred: any change to application code, builder code, watcher code, product memory,
infrastructure, services, Tailscale, secrets, permissions, or deployment state.

## 2. What I found

**Inbox identity.** `git hash-object bridge/chatgpt-inbox.md` in `/opt/crooks-ai-bridge` returned
`5d659fbc9418f378a10ddc5666e79ffc5b94ae7c`, matching the SHA the watcher passed in its launch
prompt. The instructions I executed are the instructions the watcher believed it was dispatching.

**Builder checkout `/opt/crooks-builder` (observed, unchanged).**

| Item | Value |
|---|---|
| Branch | `claude/builder-environment-repair` |
| HEAD | `295e483b4f9adcdc3fb58bfb3aa025e2e3f4779b` |
| Subject | "The BLOCKED half of BE-04, unblocked and then actually run" |
| `git status --porcelain --untracked-files=all` | empty (0 lines) at start and at end of round |
| Registered worktrees | only `/opt/crooks-builder` itself |

**Pre-existing discrepancy, carried forward from the previous handoff, still not acted on:** the
watcher prompt and the installed unit both name the builder branch as `claude/bridge-builder`
(`CROOKS_BRIDGE_BUILDER_BRANCH=claude/bridge-builder`), but the checkout is on
`claude/builder-environment-repair`. `claude/bridge-builder` exists locally and on `origin`; the
checkout is simply not on it. The inbox said "do not change the builder checkout", so I did not
switch it. Harmless for a read-only round; it would matter for any future inbox that asks for
committed implementation work.

**Watcher state, which is what this round exists to prove (all read-only).**

- `/etc/systemd/system/crooks-bridge-watcher.service` now contains
  `CROOKS_BRIDGE_CLAUDE_MODEL=claude-fable-5-1` and `CROOKS_BRIDGE_CLAUDE_EFFORT=high`. In the
  previous handoff (15:52Z) those lines were absent from the installed unit. The pin has since been
  installed.
- `/opt/crooks-bridge-watcher/MANIFEST.sha256` records `source-revision:
  5ada7b47f13547f107be1f53beeb79021cc48c24`. The previous handoff recorded `3d1f65d` (the unpinned
  base). The live runtime was reinstalled from a newer source between rounds. Note this is not the
  candidate SHA `7de5855` verified last round; it is a later revision. I did not investigate what
  `5ada7b4` adds beyond the pin, as that is outside this inbox.
- `crooks-bridge-watcher.service`: active, enabled, `ActiveEnterTimestamp` 2026-09-19 16:11:15 UTC.
  This round's timestamp is 16:12:47 UTC, so the watcher had been running for about 90 seconds
  when it launched this session. This session is the pinned watcher's first real dispatch.
- The model identity reported to this session is `claude-fable-5-1`, consistent with the pin.

## 3. What I changed

**Nothing except this file.**

- No commit, branch, checkout, reset, merge, tag, or push in any repository.
- `/opt/crooks-builder` was inspected with `git branch`, `git rev-parse`, `git status`,
  `git worktree list` and `git branch -a` only. Status was empty before and after.
- `/opt/crooks-os/crooks-assistant` was inspected with `git branch`, `git rev-parse` and
  `git status` only. Never edited, switched, or reset.
- No service was started, stopped, restarted, enabled, disabled, or reloaded. No file under `/etc`,
  `/opt/crooks-bridge-watcher`, or `/opt/crooks-watcher-review` was written.
- Only `bridge/claude-outbox.md` in `/opt/crooks-ai-bridge` was written. It is not staged,
  committed, or pushed; the watcher publishes it. No other file in the bridge worktree was touched.
- No scratch files were created anywhere this round.

## 4. Repository state

| Repo | Branch | HEAD | Status |
|---|---|---|---|
| **Production** `/opt/crooks-os/crooks-assistant` | `claude/linux-prod-migration-production` | `1cf3a0f3361b79f9de208d80f501543c53c244b5` | clean, untouched |
| Builder `/opt/crooks-builder` | `claude/builder-environment-repair` | `295e483b4f9adcdc3fb58bfb3aa025e2e3f4779b` | clean, untouched |
| Bridge `/opt/crooks-ai-bridge` | `crooks-ai-bridge` | `a6dab064286a0ad9beb105b1f4f27d0377f8f04b` | clean apart from this outbox |

**Production branch HEAD: `1cf3a0f3361b79f9de208d80f501543c53c244b5` on
`claude/linux-prod-migration-production` — unchanged since the previous handoff and unchanged by
this round.**

Files changed this round: `bridge/claude-outbox.md` only.

## 5. Test results

None run. The inbox asked for a verification-only smoke round with no code change, so there was
nothing to test and running the watcher or application suites was not requested.

## 6. Service and server state (observed read-only, unchanged)

| Service | State | Enabled | Active since (UTC) |
|---|---|---|---|
| `crooks-bridge-watcher.service` | active, running | enabled | 2026-09-19 16:11:15 |
| `crooks-assistant.service` (FastAPI backend) | active, running | enabled | 2026-09-19 06:30:10 |

- Port 8000: `LISTEN 127.0.0.1:8000` only, owned by the `python` process of the assistant. Not
  bound on any public or Tailscale address. Other listeners are SSH on 22 and Tailscale-serve on
  the `100.72.82.24` / `fd7a:...` addresses on 443, unchanged.
- Host: up 1 day 1h18m, load average 0.12, root filesystem 18% used (59G free).

## 7. Errors

None. Every command succeeded. No permission-layer block was encountered; nothing the inbox asked
for required a permission I lack.

## 8. Safety constraints — all preserved

`writes_enabled` false; `CROOKS_WRITES_LOCAL_OWNER` false; FastAPI bound to 127.0.0.1; port 8000
not public; proposal/action/verification semantics unchanged; no live Shopify, Gmail or ElevenLabs
call and no live external mutation; V2 not begun; UI not redesigned; Mac deployment and rollback
path preserved; `/root/.claude` writable (this session's memory directory is on it); no secret
printed or committed. This round executed no code path that could affect any of these.

Several claude.ai MCP connectors (Shopify, Gmail, Google Drive, Omnisend, Resend, and others) were
exposed to this session by the harness. None was invoked. Some require authorization and one
(similarweb) failed to connect; neither matters for this round and I took no action on them.

## 9. Decisions or questions needing owner review

1. **Smoke test passed; no decision required for that.** The pinned watcher dispatched and
   completed a real round.
2. **Builder branch mismatch remains open** (§2). Before the first inbox that asks for committed
   implementation work, the owner should decide whether to check out `claude/bridge-builder` in
   `/opt/crooks-builder` or change `CROOKS_BRIDGE_BUILDER_BRANCH` to match. I recommend the former,
   so the unit stays the single source of truth, but it is an owner action and I have not taken it.
3. **Installed source-revision `5ada7b4` differs from the reviewed candidate `7de5855`** (§2). If
   the owner intended the installed runtime to be exactly the reviewed candidate, that is worth a
   glance. If `5ada7b4` is a later approved revision that includes the pin, nothing is needed.

## 10. Exact proposed next step

The smoke round is complete and the watcher is proven live under the pin. The next step is the
owner's: resolve §9.2 (a one-line `git checkout claude/bridge-builder` in `/opt/crooks-builder`
while the watcher is idle, or an equivalent unit edit), then send the first real inbox. Per the
inbox, I have not begun Engineering Orchestrator V1 and will not until an inbox asks for it.

## 11. Stop

Round complete. Nothing further was done.

Inbox SHA processed: `5d659fbc9418f378a10ddc5666e79ffc5b94ae7c`
