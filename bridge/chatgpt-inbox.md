# CHATGPT INBOX

## 2026-09-19 — Audit ECC candidates for CROOKS engineering harness reuse

This is a **read-only research/security audit**, not an installation task and not Engineering Orchestrator implementation. The Linux reconciliation round is complete. Do not act on its owner-only ratify/reverse decision.

### Objective

Evaluate selected public components from `affaan-m/ECC` against the accepted CROOKS Builder/Orchestrator contracts so the Director can decide what is worth selectively adopting instead of rebuilding.

Pin the audit to ECC commit:

`07756cee15788a54506031462794ad645719b028`

Canonical CROOKS research proposal to read:
`claude/product-memory-foundation:crooks-assistant/docs/product-memory/ENGINEERING_STACK_REUSE_PLAN.md`

Also read current:
- CURRENT_TRUTH.md
- ENGINEERING_ORCHESTRATOR_V1.md
- DEV_TEAM_V1_PILOT.md
- accepted Builder DEV_ENVIRONMENT.md / CLAUDE project-layout proposal
- latest bridge outbox

### Candidate ECC surfaces

Audit these first:
- skills/agent-architecture-audit
- skills/agent-harness-construction
- skills/agent-eval
- skills/ai-regression-testing
- skills/automation-audit-ops
- skills/benchmark-methodology
- skills/security-review
- skills/tdd-workflow
- skills/verification-loop
- skills/unified-memory
- hooks architecture, especially destructive-Git/path GateGuard concepts

You may clone/fetch the exact public ECC commit into a disposable `/tmp` directory and run the already-present SkillSpector in no-LLM/static mode where available. Manually inspect findings and source. Delete disposable scratch state before stopping.

### Required report

For each candidate classify:
- ADOPT STATIC CONTENT
- ADAPT / REIMPLEMENT CROOKS-SPECIFIC
- DEFER
- REJECT

Give:
1. executable/network/install surface;
2. overlap with existing CROOKS Builder and canonical contracts;
3. conflicts or authority widening;
4. concrete value;
5. exact safe integration form;
6. provenance/commit and security-scan evidence.

Specifically determine whether any full ECC plugin/runtime/hook installation is justified. Default assumption is **no** unless evidence proves otherwise.

Also inspect whether current headless Claude engineering sessions can inherit user/business MCP connectors or other unnecessary tool surface. Report observed exposure and a safe isolation design, but do not change settings.

### Boundaries

- Do not install ECC or npm packages.
- Do not modify `/opt/crooks-builder`, production, watcher runtime, Claude user settings, MCP settings, systemd, Tailscale, secrets, or permissions.
- Do not create persistent external accounts/services.
- Do not spend money.
- Do not enable CROOKS writes or invoke business connectors.
- Do not commit/push any implementation branch.
- Do not begin Orchestrator implementation.
- Scratch clone/read/scan only.
- Replace only `bridge/claude-outbox.md`; watcher owns publication.

### Handoff

Return a ranked shortlist with explicit reasons, scan evidence, conflicts, and the smallest safe next integration experiment. STOP.
