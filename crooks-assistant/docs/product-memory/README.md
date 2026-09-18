# CROOKS OS Product Memory

This directory is the canonical durable product memory for CROOKS OS.

The rule is simple:

> If an idea, product principle, architecture decision, roadmap item, or self-improvement concept matters to CROOKS OS, it must not live only in an AI conversation.

ChatGPT, Claude, future model workers, and human contributors should treat these documents as the durable source of truth for product intent.

## Files

- [PRODUCT_BRAIN.md](./PRODUCT_BRAIN.md) — enduring vision, product principles, architecture philosophy, and non-negotiables.
- [ROADMAP.md](./ROADMAP.md) — ordered Now / Next / Later / Someday implementation roadmap.
- [IDEAS.md](./IDEAS.md) — captured ideas that are not yet necessarily approved for implementation.
- [FEATURES.md](./FEATURES.md) — feature register with state and ownership.
- [DECISIONS.md](./DECISIONS.md) — important decisions and the reasoning behind them.
- [SELF_IMPROVEMENT.md](./SELF_IMPROVEMENT.md) — controlled self-improvement, multi-agent development hierarchy, reviewers, replay, and deployment gates.

## Status model

Use these states consistently:

- **CAPTURED** — worth preserving; not yet committed.
- **APPROVED** — owner has explicitly agreed with the direction.
- **PLANNED** — accepted into the roadmap with an intended phase.
- **BUILDING** — actively being implemented.
- **TESTING** — implementation exists and is under validation.
- **SHIPPED** — in the production system and verified.
- **DEFERRED** — intentionally not being worked on now.
- **REJECTED** — considered and intentionally not proceeding.

## Capture rule

When the owner raises a potentially meaningful CROOKS idea:

1. Capture it in `IDEAS.md` with an ID, date, context, and status.
2. Do **not** silently convert brainstorming into implementation.
3. If the owner explicitly approves it, promote it to `FEATURES.md` and/or `ROADMAP.md`.
4. If implementation changes product behaviour or architecture, record the decision in `DECISIONS.md`.
5. If an old idea is superseded, keep the history and mark it superseded rather than deleting context.

## Agent startup rule

Before making meaningful CROOKS changes, an engineering agent should read:

1. `PRODUCT_BRAIN.md`
2. relevant entries in `DECISIONS.md`
3. the assigned feature/issue
4. `SELF_IMPROVEMENT.md` when the task touches agent autonomy, deployment, testing, or self-modification

An agent must not reverse a recorded product or safety decision silently. It must escalate the disagreement.

## Maintenance

This product memory should be reviewed periodically to:

- merge duplicates,
- mark shipped/deferred/rejected items,
- update sequencing,
- preserve rationale,
- remove stale implementation detail while retaining decisions.

The goal is durable product intent, not an ever-growing transcript dump.
