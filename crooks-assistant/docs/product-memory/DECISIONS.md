# CROOKS OS — Decision Log

**Purpose:** preserve important product/architecture decisions and the reasoning behind them so future agents do not silently reverse them.

---

## DEC-001 — CROOKS is an operating layer, not a chatbot
**Date:** 2026-09-19  
**Status:** ACTIVE

CROOKS should be designed around persistent business state, capabilities, automation, anticipation, and verified actions.

Chat is one interface, not the product definition.

**Reason:** a generic conversational wrapper is not sufficiently differentiated or operationally valuable.

---

## DEC-002 — Maximum capability, minimum visible UI
**Date:** 2026-09-19  
**Status:** ACTIVE

Hide complexity whenever possible.

Prefer one useful card/action over large dashboards or multiple controls.

**Reason:** subscriber usability is a core differentiator.

---

## DEC-003 — Human attention is the scarce resource
**Date:** 2026-09-19  
**Status:** ACTIVE

CROOKS should suppress routine normality and surface exceptions.

**Reason:** the product should reduce owner attention cost, not simply centralise more information.

---

## DEC-004 — Durable business state lives outside the model
**Date:** 2026-09-19  
**Status:** ACTIVE

Critical state, events, decisions, expectations, and actions must not depend on conversational memory.

**Reason:** model context is transient and unreliable as a system of record.

---

## DEC-005 — Models propose; deterministic server capabilities execute
**Date:** 2026-09-19  
**Status:** ACTIVE / SAFETY-CRITICAL

Consequential actions use the proposal/action/verification model.

Preserve:
- immutable server-side action identity/arguments,
- explicit authorisation where required,
- precondition reread,
- deterministic execution,
- authoritative verification.

**Reason:** model narration is not proof of execution.

---

## DEC-006 — Voice “yes” is not sufficient for sensitive authorisation
**Date:** 2026-09-19  
**Status:** ACTIVE / SAFETY-CRITICAL

Sensitive writes require the appropriate bound approval mechanism.

---

## DEC-007 — Unknown writes fail closed
**Date:** 2026-09-19  
**Status:** ACTIVE / SAFETY-CRITICAL

Do not allow models to improvise arbitrary write operations outside known capability families.

---

## DEC-008 — Autonomy is narrow and earned
**Date:** 2026-09-19  
**Status:** ACTIVE

No blanket “full autonomy.”

Autonomy should be granted per action class based on repeated approval history, risk, reversibility, and verification.

---

## DEC-009 — Event-driven architecture is preferred where available
**Date:** 2026-09-19  
**Status:** ACTIVE

Use real events/webhooks when practical; use schedules for deadlines/reconciliation and systems without useful events.

---

## DEC-010 — Models are replaceable
**Date:** 2026-09-19  
**Status:** ACTIVE

The long-term architecture requires a Model Gateway.

Claude may be primary, but model/provider identity must not become the durable business architecture.

---

## DEC-011 — Self-improvement uses isolated candidate development
**Date:** 2026-09-19  
**Status:** ACTIVE

Production does not freely rewrite itself.

Required direction:
observe → diagnose → reproduce → isolated branch/worktree → tests → replay → independent review → candidate → controlled deployment → monitoring/rollback.

---

## DEC-012 — Every autonomous worker gets its own worktree
**Date:** 2026-09-19  
**Status:** ACTIVE

Parallel agents must not share one mutable working tree.

**Reason:** the Linux migration exposed a real duplicate-Claude collision where two agents edited the same checkout.

---

## DEC-013 — Implementers do not solely review themselves
**Date:** 2026-09-19  
**Status:** ACTIVE

Every specialist layer should eventually have an independent reviewer/critic.

Reviewer objective is adversarial verification, not agreement.

---

## DEC-014 — GPT should eventually act as independent director/reviewer above Claude workers
**Date:** 2026-09-19  
**Status:** DIRECTION APPROVED

The GPT layer should inspect actual diffs/tests/evidence and challenge Claude manager/worker assumptions.

The owner remains above both for genuine product decisions.

---

## DEC-015 — Owner should not be a message courier
**Date:** 2026-09-19  
**Status:** ACTIVE

Bridge/watcher/orchestrator work should progressively remove the need for the owner to manually copy messages between ChatGPT and Claude.

---

## DEC-016 — GitHub is canonical product memory
**Date:** 2026-09-19  
**Status:** ACTIVE

Important product ideas, decisions, and roadmaps must be versioned and durable.

AI memory is not the system of record.

---

## DEC-017 — Brainstorming does not equal implementation approval
**Date:** 2026-09-19  
**Status:** ACTIVE

Ideas are captured first.

Only explicit owner approval promotes them into committed roadmap/feature work.

---

## DEC-018 — Current product quality comes before major V2 expansion
**Date:** 2026-09-19  
**Status:** ACTIVE

Before building the full World/automation/self-improvement system, finish:
- always-on deployment,
- UI,
- response quality,
- reliability,
- device experience,
- error cleanup.

**Reason:** self-improvement should operate on a solid baseline rather than compensate for an unfinished product.

---

## DEC-019 — Server becomes canonical always-on runtime
**Date:** 2026-09-19  
**Status:** ACTIVE

CROOKS runtime should not depend on the Mac being awake.

Mac becomes optional control/development/rollback device.

---

## DEC-020 — Private-first networking
**Date:** 2026-09-19  
**Status:** ACTIVE

FastAPI should bind loopback by default and be accessed through private Tailscale HTTPS.

Avoid unnecessary public endpoints.

---

## DEC-021 — Temporary root execution is acceptable for initial Linux migration
**Date:** 2026-09-19  
**Status:** TEMPORARY

Root is temporarily approved because Claude Max auth currently lives under `/root/.claude`.

Later hardening should migrate CROOKS to a dedicated service account.

---

## DEC-022 — Whisper is intentionally disabled on the Linux production server initially
**Date:** 2026-09-19  
**Status:** ACTIVE FOR CURRENT DEPLOYMENT

ElevenLabs Scribe remains primary STT.

Do not reproduce the Mac M4 whisper.cpp/Core ML setup on the Hetzner CPU VM initially.

Health must distinguish intentional disablement from failure.

---

## DEC-023 — Disabled optional subsystem must not falsely degrade top-level health
**Date:** 2026-09-19  
**Status:** ACTIVE

If local Whisper is explicitly disabled:
- mark it disabled/not in use,
- do not run Mac/Core ML checks,
- do not degrade top-level health solely because it is absent.

Speech health must still fail if no usable STT remains.

---

## DEC-024 — Static and mutable secrets require different Linux storage
**Date:** 2026-09-19  
**Status:** ACTIVE

Do not use systemd `LoadCredential` as a universal secret backend.

Static secrets may use encrypted systemd credentials.

Mutable credentials require secure writable persistence.

---

## DEC-025 — Gmail token should live outside the Git checkout on Linux
**Date:** 2026-09-19  
**Status:** ACTIVE

Preferred Linux production location:
`/etc/crooks-os/secrets/gmail_token`

Requirements:
- root-only,
- 0600,
- writable for OAuth refresh,
- outside Git.

Existing `token.json` may remain fallback/compatibility.

---

## DEC-026 — media_signing_key is a recognised persistent secret on both platforms
**Date:** 2026-09-19  
**Status:** ACTIVE

Accept:
- new Mac Keychain entry,
- one initial cache invalidation.

**Reason:** the previous unrecognised key silently regenerated each boot and invalidated media URLs.

---

## DEC-027 — Writes remain disabled during migration/verification
**Date:** 2026-09-19  
**Status:** ACTIVE UNTIL EXPLICIT CHANGE

`CROOKS_WRITES_ENABLED=false` and `CROOKS_WRITES_LOCAL_OWNER=false` remain the migration baseline.

Enabling writes is a separate explicit decision.

---

## DEC-028 — GitHub bridge uses a separate branch
**Date:** 2026-09-19  
**Status:** ACTIVE

`crooks-ai-bridge` carries communication only.

It must not be merged into production code.

---

## DEC-029 — Bridge watcher should trigger on inbox blob SHA, not branch HEAD
**Date:** 2026-09-19  
**Status:** ACTIVE

Claude updating its outbox must not retrigger itself.

---

## DEC-030 — Bridge watcher must fail closed around shared/dirty worktrees
**Date:** 2026-09-19  
**Status:** ACTIVE

Before launching a headless Claude worker:
- acquire lock,
- confirm expected worktree state,
- ensure no unrelated Claude process is editing the same target,
- prefer dedicated builder worktree.

---

## DEC-031 — Subscriber product must hide internal engineering complexity
**Date:** 2026-09-19  
**Status:** ACTIVE

Subscribers should not need to understand:
- prompts,
- agents,
- MCPs,
- systemd,
- model routing,
- OAuth internals,
- Tailscale.

---

## DEC-032 — Commercial differentiation is operating leverage, not model cleverness
**Date:** 2026-09-19  
**Status:** ACTIVE

The key metric is:

> How much owner attention can CROOKS remove without reducing control or trust?

---

## DEC-033 — Ecommerce domain knowledge should be opinionated
**Date:** 2026-09-19  
**Status:** ACTIVE

Future subscriber CROOKS should natively understand:
- orders,
- fulfilment,
- returns,
- chargebacks,
- stock,
- suppliers,
- production,
- campaigns,
- support,
- payments/cash.

This is part of differentiation from generic chat.

---

## DEC-034 — Self-improvement may learn from behaviour, not just explicit preference text
**Date:** 2026-09-19  
**Status:** ACTIVE DIRECTION

Use signals such as:
- corrections,
- repeated questions,
- interruptions,
- abandoned screens,
- action usage,
- latency.

Do not infer major product decisions from weak signals without review.

---

## DEC-035 — High-risk self-modification areas stay approval-gated
**Date:** 2026-09-19  
**Status:** ACTIVE

Do not auto-deploy changes touching:
- authentication,
- secrets,
- permissions,
- refunds,
- Shopify write semantics,
- action authorisation,
- safety invariants,
- destructive migrations.

---

## DEC-036 — Product memory should be cleaned periodically, not allowed to become a transcript dump
**Date:** 2026-09-19  
**Status:** ACTIVE

Maintain:
- concise rationale,
- status,
- supersession history,
- deduplication.

---

# How to add a decision

Use:

```
## DEC-XXX — Title
Date:
Status:

Decision:

Reason:

Consequences:
```

Never silently rewrite old rationale. If a decision changes, add a new decision that explicitly supersedes the old one.
