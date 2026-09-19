# CROOKS OS — Current Truth

**Purpose:** compact active context for GPT/Claude/Fable/engineering workers  
**Status:** ACTIVE — update whenever a material product/architecture state changes  
**As of:** 2026-09-19

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
- Canonical product memory currently lives on `claude/product-memory-foundation`; read it by explicit ref. The default theme branch is not the CROOKS product-memory source.
- Production application branch remains `claude/crooks-assistant-build-lgxlau` at the Phase 5 candidate baseline until an explicitly reviewed promotion changes it.
- Linux migration review ref remains separate at `1cf3a0f3361b79f9de208d80f501543c53c244b5`. Git branch state alone does not establish which files are currently installed or which service is running; fresh runtime evidence is required.
- The GitHub communication bridge uses orphan branch `crooks-ai-bridge`.
- The CROOKS bridge watcher is installed, enabled, and its corrected stdin-based Claude launch path has passed an end-to-end smoke test.
- Headless Claude runs in the standalone isolated builder clone at `/opt/crooks-builder`, not the production checkout.
- Watcher publication of the outbox is watcher-owned; the owner is no longer the normal message courier.
- Builder Environment result is published at `claude/builder-environment-review`, commit `9a27bc441adad1e98e8a9ca257d1883246ee7eec`. **Independent review: CHANGES REQUIRED** before acceptance as the reproducible Dev Team foundation. See [BUILDER_ENVIRONMENT_REVIEW.md](./BUILDER_ENVIRONMENT_REVIEW.md).
- Independently reproduced: bootstrap crashes on the committed manifest; doctor can return success for wrong versions/failed tools; shell exports interpret substitution in a supplied path. Fresh-checkout reconstruction is also incomplete by source inspection. Existing builder tooling remains useful partial delivery.
- No project skills, CLAUDE.md, rules or hooks were installed in that round; the worker reported native permission refusal. Do not bypass it. DESIGN.md remains PROPOSED.
- Current bridge round is **Mobile Experience V1 — unacknowledged, liveness unknown**. At 2026-09-19T06:38:39Z, inbox blob `24b713cce3d0e8c9ede3185ebef78cc107ece507` contains the mobile task; outbox blob `67e3da115963a1f5ba8e0b57ede74a00f5be2fb2` still acknowledges the preceding Builder inbox `607b607e54eb194b81d708dfbc7bd744c2e8cd18`. No mobile review branch was listed. Do not duplicate or overwrite the task. Reconcile watcher/attempt status before dispatching a replacement.
- Last published server observations describe an already dirty production checkout, no listener on 8000 and no installed assistant service at that time. These reports are historical, not proof of current runtime state. Preserve/reconcile uncommitted migration work before any checkout/reset/promotion. A Git HEAD or reflog is not proof that working-tree bytes were untouched.

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

1. finish and review the permanent Builder Environment,
2. complete controlled Linux production migration/promotion,
3. provision runtime secrets through the approved process,
4. establish the always-on server runtime,
5. enable private Tailscale HTTPS when approved,
6. verify real Samsung/iPhone/runtime behaviour,
7. perfect current UI,
8. perfect response behaviour and latency,
9. conduct real-world CROOKS sessions and collect evidence,
10. implement Engineering Orchestrator / Dev Team V1,
11. bootstrap the privileged deployment/infrastructure control plane,
12. expand World / Event Ledger / Attention / expectations / automation / integrations.

Dev Team specification planning may proceed while the Builder round is in flight. Planning does not advance its implementation gate. DEC-046 records this ordering and resolves the older conflicting roadmap footer.

Do not skip safety/deployment gates merely because later architecture is more exciting.
