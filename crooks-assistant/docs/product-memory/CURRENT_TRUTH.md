# CROOKS OS — Current Truth

**Purpose:** compact active context for GPT/Claude/Fable/engineering workers  
**Status:** ACTIVE — update whenever a material product/architecture state changes  
**As of:** 2026-09-19T10:33Z — reconciled against direct runtime observation; see Engineering control plane for method.

This file is intentionally not a historical transcript. It answers: **what is true and important now?**

For historical rationale, use Git and DECISIONS.md. For release evolution rules, use EVOLUTION_POLICY.md.

## Product

CROOKS OS is the intelligent operating layer for the business: persistent state, controlled capabilities, verified actions, proactive exception handling, and minimal owner attention.

Core product principles remain:

- maximum capability, minimum visible UI,
- human attention is scarce,
- persistent business state outside conversational memory,
- models propose; deterministic capabilities execute consequential actions,
- autonomy is narrow and earned,
- models/providers are replaceable,
- self-improvement is isolated, evidence-driven and reversible.

## Engineering control plane

- Canonical repository: `crooksldn-pixel/Shopify-theme`.
- Canonical product memory currently lives on `chatgpt/ops-memory-2026-09-19`, which contains all of `claude/product-memory-foundation` plus the operator runbook; read it by explicit ref. The default theme branch is not the CROOKS product-memory source.
- **The Linux migration candidate is what actually runs.** `/opt/crooks-os/crooks-assistant` is checked out on `claude/linux-prod-migration-production` at `1cf3a0f3361b79f9de208d80f501543c53c244b5`, working tree **clean**, and `crooks-assistant.service` serves it. `claude/crooks-assistant-build-lgxlau` at `e43aecdb39b87b622f64b6ab434e428d216ef157` remains the Phase 5 Git baseline and the Mac rollback reference, but it is no longer the running code. Earlier memory asserting production had "not been silently moved to the Linux migration candidate" described Git branch bookkeeping, not the runtime, and is superseded by direct observation.
- Runtime verified 2026-09-19T10:25Z by read-only inspection on the server (`systemctl show`, `ss -ltnp`, `curl /health`, `git --no-optional-locks status`): service **active (running)** since 06:30:10Z, `NRestarts=0`, uvicorn bound to `127.0.0.1:8000`; `tailscale serve` proxies `https://crooks-os-prod-1.taildfb357.ts.net` to `127.0.0.1:8000`, **tailnet only, no funnel**. Writes remain **disabled** (`CROOKS_WRITES_ENABLED=false`) and every write capability reports disabled. DEC-027 intact.
- Health is **`degraded`, and Gmail is the only failing check**: "No Gmail token stored." `/etc/crooks-os/secrets/` exists at 0700 and holds `media_signing_key` (DEC-026), but has no `gmail_token` (DEC-025) and there is no fallback `token.json`. Shopify read path, Scribe v2 (4/4), ElevenLabs Derek (7/7, 463ms), knowledge base and terminology all report OK. Whisper is correctly reported disabled-by-design without degrading top-level health (DEC-022/023).
- **UNKNOWN / VERIFY — was private Tailscale HTTPS approved?** Near-term step 5 gates it on owner approval. It is live. No approving entry exists in DECISIONS.md. Confirm with the owner and record a decision, or treat it as a gate crossed without a record.
- The GitHub communication bridge uses orphan branch `crooks-ai-bridge`.
- The CROOKS bridge watcher is installed, enabled, and its corrected stdin-based Claude launch path has passed an end-to-end smoke test.
- Headless Claude runs in the standalone isolated builder clone at `/opt/crooks-builder`, not the production checkout.
- Watcher publication of the outbox is watcher-owned; the owner is no longer the normal message courier.
- Builder Environment result is published at `claude/builder-environment-review`, commit `9a27bc441adad1e98e8a9ca257d1883246ee7eec`. **Independent review: CHANGES REQUIRED** before acceptance as the reproducible Dev Team foundation. See [BUILDER_ENVIRONMENT_REVIEW.md](./BUILDER_ENVIRONMENT_REVIEW.md).
- Independently reproduced: bootstrap crashes on the committed manifest; doctor can return success for wrong versions/failed tools; shell exports interpret substitution in a supplied path. Fresh-checkout reconstruction is also incomplete by source inspection. Existing builder tooling remains useful partial delivery.
- No project skills, CLAUDE.md, rules or hooks were installed in that round; the worker reported native permission refusal. Do not bypass it. DESIGN.md remains PROPOSED.
- Current bridge round is **Mobile Experience V1 — COMPLETE and published**. The watcher recorded inbox `24b713cce3d0e8c9ede3185ebef78cc107ece507` as processed at 2026-09-19T10:09:58Z; the outbox blob is now `0af10d40ac4148f69e1fc454fbafbcd28f020a78` at bridge HEAD `2f1408b`. Candidate `564ef3430d58b34de582f5548d7fe201c4cfe04b` is published on `claude/mobile-experience-v1-review`. Not merged, not deployed. The watcher is idle: `pending no`, `lock free`, `last run ok`, 0 failures. **No engineering worker is running**; the live `claude` processes on the box are children of the backend and are product assistant sessions. This supersedes the "unacknowledged, liveness unknown" state recorded at 06:38:39Z.
- Mobile candidate gates are reported as pytest **0 failed** (2821 passed / 8 skipped / 2 deselected) and browser sweep **714 checks, 0 failed**, each measured by two different workers. Confirmed here by Git inspection only: the `564ef34` diff is 46 files, 9 text plus 37 screenshots, and **no file under `crooks-assistant/app/` is touched**, so no route, action, proposal, authorisation or speech semantics changed. The outbox says 40 screenshots; the actual count is 37. The gate numbers themselves were not re-run in this checkout.
- **The mobile candidate is stacked on the unaccepted Builder Environment commit.** The parent of `564ef34` is `9a27bc4`, which is CHANGES REQUIRED. Merging mobile as-is would carry BE-01 through BE-04 with it. Either land the Builder repair first, or rebase the mobile candidate onto an accepted base, before any promotion is considered.
- Two owner decisions block mobile merge consideration: the keyboard trade (dock areas standing down while the phone keyboard is open) and retaining `user-scalable=no` (WCAG 1.4.4, kept deliberately because pinch and spread are the product's own gestures). The axe-core accessibility figures are still relayed from their original author and have never been independently re-measured.
- **Watcher duplicate-dispatch defect, confirmed in the service logs.** The round before last finished its work but exited before publishing its outbox; the watcher then re-dispatched the same inbox SHA at 09:47:29Z. That run detected the duplicate and verified rather than rebuilding, but unattended this would redo completed work. Proposed guard: skip dispatch when the working-tree outbox already records the incoming inbox SHA. Not implemented.
- Superseded: the earlier bullet describing a dirty production checkout, no listener on 8000 and no installed assistant service. Those observations were accurate when published and are now false; the runtime facts above replace them, and there is no longer uncommitted migration work to preserve. The durable lesson survives: a Git HEAD or reflog is not proof that working-tree bytes were untouched, and any "production untouched" claim should state its actual observation method and its limits.
- The `clickpath.js` settle-budget flake is open and deliberately unfixed. The Split press failure has now not reproduced across three independent sweeps and is attributed to `hop()`'s fixed 4.3s settle budget under CPU contention rather than a UI hit-target, layering or `pointer-events` defect. While it remains, any full-sweep result from a loaded machine is ambiguous.

## Dev-team direction

The approved direction is a quality-first engineering organisation:

- GPT Director above the engineering loop for independent decomposition/review.
- Claude Opus for architecture, security, difficult diagnosis, major refactors, integration decisions and high-scrutiny review.
- Claude Sonnet for bounded implementation where quality remains protected by evidence and review.
- Fable as a first-class Experience Director for substantial UX/interaction work, including pre-implementation direction and post-implementation experience review.
- Specialist QA, performance, security and integration workers.
- Independent reviewers rather than implementers certifying themselves.
- Parallel work only in isolated worker workspaces/branches.
- An Integrator combines successful candidates and proves the integrated result.

Cost and speed are subordinate to quality. Cheaper/faster models may handle genuinely mechanical work, but substantive product/code quality is not traded away to save usage.

[ENGINEERING_ORCHESTRATOR_V1.md](./ENGINEERING_ORCHESTRATOR_V1.md) now holds the proposed detailed specification. Planning is active; implementation has not started or been authorised by that document. Proposed mechanisms such as task-store choice, leases, retry limits and initial concurrency are not approved product decisions. Fable/GPT invocation and credential isolation require verification before automated operation.

[DEV_TEAM_V1_PILOT.md](./DEV_TEAM_V1_PILOT.md) defines proposed durable record/review/recovery contracts and a first acceptance trial based on the reproduced Builder defects. Foundation repair through the existing bridge and later Orchestrator acceptance are separate activities. The current mobile task must not be duplicated or retrospectively described as a full Dev Team run.

## Infrastructure autonomy direction

Routine infrastructure maintenance should eventually require owner **approval**, not owner **terminal operation**.

Target components:

- Engineering Orchestrator,
- worker/workspace manager,
- model router,
- Privileged Action Broker,
- Deployment/Infrastructure Controller,
- versioned infrastructure releases,
- deterministic health checks,
- automatic rollback.

No component should have unrestricted authority to rewrite itself and declare itself healthy.

Termius/SSH should become break-glass recovery, not a normal workflow.

## Release doctrine

History accelerates the next version but does not constrain it.

Preserve valuable outcomes, contracts, safety invariants and lessons.

Allow obsolete implementation, UI, compatibility layers, abstractions, tests and even whole components to be superseded, retired or deleted when a better system makes them unnecessary.

A component becoming null is valid.

DESIGN.md describes the current direction; older visual directions are evidence/history, not permanent constraints.

Every substantial release should operate from a curated Active Context Pack rather than carrying all historical context forward.

## Current near-term order

1. finish and review the permanent Builder Environment — **open**; CHANGES REQUIRED, repair task ENV-REPRO-001 specified but not dispatched,
2. complete controlled Linux production migration/promotion — **runtime achieved**; the service runs migration candidate `1cf3a0f`, but the promotion has never been recorded as a reviewed decision,
3. provision runtime secrets through the approved process — **partial**; `media_signing_key` provisioned, `gmail_token` outstanding and the sole cause of degraded health,
4. establish the always-on server runtime — **done**; `crooks-assistant.service` active and enabled at boot, though reboot recovery has not actually been exercised,
5. enable private Tailscale HTTPS when approved — **live**; approval not recorded, see UNKNOWN / VERIFY above,
6. verify real Samsung/iPhone/runtime behaviour,
7. perfect current UI,
8. perfect response behaviour and latency,
9. conduct real-world CROOKS sessions and collect evidence,
10. implement Engineering Orchestrator / Dev Team V1,
11. bootstrap the privileged deployment/infrastructure control plane,
12. expand World / Event Ledger / Attention / expectations / automation / integrations.

Dev Team specification planning may proceed while the Builder round is in flight. Planning does not advance its implementation gate. DEC-046 records this ordering and resolves the older conflicting roadmap footer.

Do not skip safety/deployment gates merely because later architecture is more exciting.
