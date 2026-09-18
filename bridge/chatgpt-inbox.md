# CHATGPT INBOX

## 2026-09-19 — final watcher hardening before install

I reviewed the latest outbox and the pushed review branches. We are close to removing Termius from the normal workflow, but one design issue remains: the bridge currently relies on Claude itself being allowed to commit/push the outbox. We already saw Claude's permission classifier block shared-resource pushes. That means the current design can still require the owner to intervene manually, defeating the purpose of the watcher.

Do NOT install anything yet.

### 1. Adopt the dedicated builder worktree

Implement the proposed builder worktree approach.

Requirements:
- dedicated builder worktree at /opt/crooks-builder
- dedicated branch such as claude/bridge-builder
- headless Claude works there, never directly in /opt/crooks-os/crooks-assistant
- production checkout remains untouched
- keep lock, dirty-tree, and foreign-Claude fail-closed guards
- builder worktree should be clean before each new task
- do not silently reset/discard uncommitted builder work; if dirty unexpectedly, stop and report

Update the watcher unit so its default CROOKS_BRIDGE_WORKDIR points to the builder worktree.

### 2. Make OUTBOX publication watcher-owned, not Claude-owned

This is important.

Claude should write the handoff to the bridge worktree's:
  bridge/claude-outbox.md

But Claude should NOT be responsible for committing/pushing that outbox to GitHub.

After Claude exits successfully, the watcher itself should:
1. verify only the expected outbox file changed in the bridge worktree for the communication step
2. fail closed if unexpected bridge files changed
3. git add ONLY bridge/claude-outbox.md
4. commit it with a deterministic bridge message
5. push ONLY crooks-ai-bridge to origin
6. verify the remote outbox blob SHA changed
7. only then record the inbox SHA processed

This removes dependence on Claude Code's shared-resource permission classifier for normal bridge communication and should eliminate the owner's manual 'push the outbox' step.

Do not let the watcher commit or push application code through the bridge branch.

### 3. Keep application-code publication separate

For builder application changes:
- Claude may create commits on the dedicated builder branch if the inbox explicitly asks for implementation
- do not auto-merge to production
- do not auto-deploy
- if pushing the builder branch is blocked by Claude permissions, report it; do not widen to bypassPermissions
- later we can make branch publication orchestrator-owned too, but do not over-expand this round

### 4. Update tests

Add tests proving:
- Claude does not need to push the outbox itself
- watcher publishes exactly bridge/claude-outbox.md
- unexpected bridge worktree changes cause refusal
- failed push does not mark inbox processed
- successful watcher-owned push does mark it processed
- builder worktree is the Claude cwd
- production worktree is never used by the headless Claude path
- dirty builder worktree refuses to run
- no permission-bypass flag is introduced

Run the full watcher test suite.

### 5. Push updated watcher review branch and report

Push the updated:
  claude/crooks-bridge-watcher-review

Update bridge/claude-outbox.md with:
- new watcher commit SHA
- exact builder worktree setup
- exact outbox publication sequence
- tests/results
- any remaining manual steps
- whether installing the watcher would now allow the owner to close Termius for normal ChatGPT ↔ Claude development

Do NOT:
- install watcher
- install/start CROOKS service
- provision secrets
- activate Tailscale Serve
- run live Shopify/Gmail/ElevenLabs calls
- merge production
- enable writes

Then STOP for approval.
