# CHATGPT INBOX

## 2026-09-19 — watcher smoke test

This is a NO-CHANGE smoke test for the newly installed CROOKS AI bridge watcher.

Do not modify application code.
Do not modify the builder branch.
Do not install or start any service.
Do not provision secrets.
Do not activate Tailscale Serve.
Do not make live Shopify/Gmail/ElevenLabs calls.
Do not enable writes.
Do not push any application branch.

Verify only:
1. You were launched automatically by the watcher, without the owner manually telling you to check the inbox.
2. Your current working directory is the standalone builder clone at /opt/crooks-builder.
3. The builder is on branch claude/bridge-builder and is clean at the start of the run.
4. The production repository under /opt/crooks-os remains untouched.
5. The bridge worktree is /opt/crooks-ai-bridge.
6. Claude authentication is healthy, but do not print tokens or secrets.

Then replace bridge/claude-outbox.md with a concise smoke-test handoff containing:
- timestamp
- inbox SHA processed
- watcher-launched: yes/no
- builder cwd
- builder branch/HEAD
- builder clean: yes/no
- production unchanged: yes/no
- Claude auth healthy: yes/no
- any error encountered
- final line exactly: SMOKE TEST PASSED
  only if every check above passed

Then STOP.

Do not run git add, commit or push for the outbox; the watcher owns publication.
