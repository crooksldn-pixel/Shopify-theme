# CHATGPT INBOX

## 2026-09-19 — Reconcile Linux migration/runtime prerequisite state

Owner direction now recorded in canonical product memory: Engineering Orchestrator V1 implementation is authorised under the existing specification and safety boundaries, but DEC-046 prerequisite ordering remains binding. This round is **not** Orchestrator implementation and is **not** a production promotion.

The previous Fable 5.1/high smoke round is complete. Do not repeat it.

### Objective

Perform a bounded, read-only reconciliation of the current Linux production/runtime state so the Director can determine exactly what remains before the controlled Linux migration/promotion prerequisite can be considered satisfied.

Canonical references to read first:
- `claude/product-memory-foundation` current CURRENT_TRUTH, DECISIONS (including DEC-046 and DEC-047), ROADMAP, MIGRATION_HANDOFF;
- Linux migration review candidate `1cf3a0f3361b79f9de208d80f501543c53c244b5`;
- latest bridge outbox.

### Required observations — read only

Establish with concrete evidence:
1. exact production checkout branch, HEAD, working-tree status and whether its tracked bytes match the Linux migration candidate;
2. current `crooks-assistant.service` unit identity/configuration relevant to source path, bind address, startup command and enabled/active state — do not print environment values or secrets;
3. whether the running process actually executes the expected checkout/venv/command and whether port 8000 remains loopback-only;
4. available provenance showing when/how the production checkout became clean at `1cf3a0f` and when/how the service was installed/started (Git reflog/log, safe file metadata, systemd journal/unit metadata, existing manifests or documented install evidence). Do not invent provenance if it cannot be established;
5. current Tailscale/private-HTTPS state as observable without changing it, and whether canonical Git contains explicit approval for that state;
6. verify the migration write-safety baseline remains disabled using configuration/code/state that does not expose secret values;
7. compare observed runtime state with the controlled Linux migration candidate/review evidence and identify any remaining verification gap before promotion can be considered complete;
8. distinguish clearly between: already satisfied and proven, observed-but-not-authorised/reconciled, unknown, safe engineering follow-up, and owner-only decision.

### Boundaries

- READ ONLY on production and infrastructure.
- Do not edit/switch/reset the production checkout.
- Do not install, stop, start, restart, enable or disable any service.
- Do not run Tailscale mutation commands.
- Do not read, print, copy or provision secret values.
- Do not enable CROOKS writes.
- Do not deploy/promote/rollback anything.
- Do not change permissions or infrastructure.
- Do not begin Engineering Orchestrator implementation.
- Do not modify the Builder checkout in this round.
- Replace only `bridge/claude-outbox.md` and stop; watcher owns publication.

### Handoff

Report:
- exact evidence and commands/observations used;
- what DEC-046 Linux/runtime prerequisites are actually proven satisfied vs not;
- any provenance contradiction or unexplained state change;
- exact smallest safe next step;
- if an owner-only decision is now required, state the single decision precisely rather than taking it.

STOP after the handoff.
