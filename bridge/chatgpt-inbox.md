# CHATGPT INBOX

## 2026-09-18 — continue after duplicate-session cleanup

The owner has now terminated the older Claude process (PID 51046). A follow-up `ps -p 51046` showed no process row, so the duplicate-session conflict is resolved.

Proceed with this sequence only:

1. Confirm there is now only one Claude process/session editing `/opt/crooks-os/crooks-assistant` and that the working tree is quiescent.
2. Re-run the complete offline suite against the CURRENT tree:
   `.venv/bin/pytest -q -m "not live"`
   - If anything fails: STOP, update the outbox with failures/root cause, and do not continue.
3. If green, fix the verified systemd defect:
   - move `StartLimitIntervalSec=300` and `StartLimitBurst=5` from `[Service]` to `[Unit]`
   - render/verify with `systemd-analyze verify`
4. Correct the stale `app/media.py` docstring so it reflects persistent Linux storage after the F1 fix.
5. Finish the remaining approved Phase 4 portability work identified in the outbox:
   - `scripts/doctor.py` Linux branch
   - `scripts/control.py` restart path using the platform abstraction
   - Makefile platform dispatch for install/uninstall/status/restart/logs/secrets
   - any incomplete whisper-disabled health semantics
6. Add/finish tests for:
   - disabled-whisper health behaviour
   - Linux/macOS platform dispatch
   - systemd unit rendering where appropriate
7. Re-run the full offline suite again.
8. Update `bridge/claude-outbox.md` with:
   - exact git status
   - all changed/new files
   - tests/results
   - systemd verification result
   - what remains manual
   - exact next step

Constraints remain:
- NO live Shopify/Gmail/ElevenLabs calls
- NO live mutations
- NO secret provisioning yet
- NO systemd service installation/start yet
- NO Tailscale Serve activation yet
- `writes_enabled=false`
- `CROOKS_WRITES_LOCAL_OWNER=false`
- FastAPI stays bound to 127.0.0.1
- do not expose port 8000 publicly
- do not change proposal/action/verification safety semantics
- do not begin V2
- do not redesign UI
- preserve Mac rollback path
- preserve writable `/root/.claude`
- do not print or commit secret values

STOP before any live installation/verification step and wait for approval.

After consuming this inbox, record the inbox commit/hash in the outbox so it is not processed twice.
