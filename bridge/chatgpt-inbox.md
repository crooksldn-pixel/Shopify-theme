# CHATGPT INBOX

## 2026-09-19 — Verify deterministic Claude model pin for bridge watcher

Owner decision: **APPROVED — make the current single-worker bridge deterministic on Claude Fable 5.1 at High effort.**

This is a bounded watcher-infrastructure verification round. It is **not** Engineering Orchestrator V1 implementation and it is not a production-application change.

### Candidate to verify

Branch: `chatgpt/bridge-fable-5-1-pin-2026-09-19`  
Expected candidate HEAD: `7de58555ee954e8561bb0f3bb6d7283715517b62`  
Base: `claude/crooks-bridge-watcher-review`

Do not mutate the candidate while reviewing it. If the remote identity differs from the expected SHA, stop and report the mismatch.

### Required review

Independently inspect the exact diff and verify that:

1. unattended watcher launches explicitly pass `--model claude-fable-5-1`;
2. unattended watcher launches explicitly pass `--effort high`;
3. the systemd source records the same model/effort values;
4. model/effort remain overrideable only through the existing watcher configuration boundary, without widening permissions;
5. watcher status reports the selected model and effort;
6. installer preflight fails closed if the installed Claude Code CLI does not expose `--model` or `--effort`;
7. tests actually assert the model/effort launch contract;
8. no existing safety, isolation, publication, locking, permission, production-read-only or owner-gating contract is weakened.

Run the full watcher test suite against the exact candidate and report the actual pass/fail summary. Run shell/static checks that already exist for this watcher if available.

On the host, read `claude --help` only to verify the currently installed CLI supports `--model` and `--effort`. Do not read/print credentials and do not launch a nested Claude session merely to test the model.

Inspect the complete candidate diff and run an appropriate secret scan over the exact diff. Require a clean verification workspace.

### Important deployment boundary

**DO NOT install, stage into the live runtime, restart, stop, enable, disable, or modify the running watcher service in this round.** A running watcher must not rewrite/restart itself while it is processing the instruction that validates the rewrite.

Do not touch the CROOKS production application, Tailscale, secrets, business writes, permissions, or deployment state.

### Handoff

Replace `bridge/claude-outbox.md` with:
- exact candidate/base identities;
- exact changed-file scope;
- full watcher test summary;
- installed Claude CLI flag-support result;
- secret-scan result;
- any defect found;
- whether the candidate is suitable for a separate owner-approved installation step;
- the exact minimal installation/verification command sequence, but do not execute it.

Then STOP. Do not begin Engineering Orchestrator implementation.
