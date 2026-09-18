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
- Linux migration work exists separately and has not been silently promoted to production.
- The GitHub communication bridge uses orphan branch `crooks-ai-bridge`.
- The CROOKS bridge watcher is installed, enabled, and its corrected stdin-based Claude launch path has passed an end-to-end smoke test.
- Headless Claude runs in the standalone isolated builder clone at `/opt/crooks-builder`, not the production checkout.
- Watcher publication of the outbox is watcher-owned; the owner is no longer the normal message courier.
- Permanent Builder Environment round: **awaiting result; preserve as in flight**. At the 2026-09-18T23:20:53Z Git inspection, inbox blob `607b607e54eb194b81d708dfbc7bd744c2e8cd18` still requests that work. Outbox blob `21e5f54610abc813e65b7d0e5674440761187604` acknowledges the earlier smoke-test inbox `dceefbb9f2e47b38ed8183b262a9e98e15d2cdc1`; no `claude/builder-environment-review` branch was listed. Process liveness and local progress are unverified. Do not restart/resubmit based on absence of a published result.
- Last server observation, in the smoke-test outbox at 2026-09-18 22:42 UTC: `/opt/crooks-os` was already dirty (15 tracked modifications, 9 untracked paths), and port 8000 had no listener. These are historical observations, not a fresh runtime inspection. Preserve/reconcile that work against the Linux review candidate before any checkout/reset/promotion. A clean branch HEAD is not proof of a clean deployed tree.

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
