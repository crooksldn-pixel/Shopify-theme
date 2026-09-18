# CHATGPT INBOX

## 2026-09-19 — post-reinstall watcher smoke test

This is a NO-CHANGE smoke test of the corrected watcher.

Do not modify application code.
Do not modify the builder branch.
Do not install/start any other service.
Do not provision secrets.
Do not activate Tailscale Serve.
Do not make live Shopify/Gmail/ElevenLabs calls.
Do not enable writes.
Do not push any application branch.

Verify only:
1. You were launched automatically by the watcher.
2. Your current working directory is /opt/crooks-builder.
3. The builder is on claude/bridge-builder and was clean at start.
4. Production under /opt/crooks-os remains untouched.
5. Claude authentication is healthy without printing any secret.
6. The watcher instructions arrived successfully over stdin.

Then completely replace bridge/claude-outbox.md with a concise handoff containing:
- timestamp
- inbox SHA processed
- watcher-launched: yes/no
- stdin prompt received: yes/no
- builder cwd
- builder branch/HEAD
- builder clean at start: yes/no
- production unchanged: yes/no
- Claude auth healthy: yes/no
- any error encountered
- final line exactly: SMOKE TEST PASSED
  only if every check above passed

Then STOP.

Do not run git add, commit or push for the outbox; the watcher owns publication.
