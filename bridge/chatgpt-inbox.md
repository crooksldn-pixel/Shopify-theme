# CHATGPT INBOX

## 2026-09-19 — Builder Environment acceptance repair + contract trial

CROOKS Mobile Experience V1 is complete and published for review at `claude/mobile-experience-v1-review` commit `564ef3430d58b34de582f5548d7fe201c4cfe04b`. Do not rebuild, modify, merge, or deploy it. Treat it as the single-worker control sample for the later Dev Team mobile benchmark.

This is a bounded BUILDER ENVIRONMENT REPAIR and MANUAL/SIMULATED DEV TEAM CONTRACT TRIAL. Work only in isolated builder/review state. Do not touch production except read-only inspection if genuinely necessary. Do not deploy, install/start/stop production services, change Tailscale, provision/read/print secrets, enable CROOKS writes, widen permissions, perform destructive actions, or call live Shopify/Gmail/ElevenLabs.

SOURCE OF TRUTH

Read current canonical product memory and Dev Team planning/review material first, including CURRENT_TRUTH, DECISIONS, ROADMAP, MIGRATION_HANDOFF, the latest Dev Team planning/review state including commit `1a0741a` and any newer superseding Git truth, plus the existing Builder candidate/review evidence. Git current truth supersedes old chat assumptions.

OBJECTIVE

Repair the independently reproduced acceptance defects in the permanent Builder Environment candidate. The candidate must not be accepted until all four defects are fixed and independently reproducible regression evidence is present:

1. Bootstrap crashes on the committed manifest.
2. Doctor can return success despite incorrect versions or failed tools.
3. Generated shell exports can interpret commands embedded in a checkout path.
4. Fresh-checkout reconstruction is incomplete.

REPAIR REQUIREMENTS

- Work from the appropriate existing Builder candidate in `/opt/crooks-builder` on an isolated repair branch; do not alter production.
- Diagnose each defect from actual code/reproduction before editing.
- Implement the smallest coherent fixes; do not broaden scope or silently change product/safety doctrine.
- Add a regression test for EACH of the four defects. Tests must fail against the rejected behaviour and pass against the repair.
- Prove explicit fresh-checkout reconstruction from repository-controlled inputs/instructions, not hidden mutable machine state. Record exact commands and results.
- Doctor must fail closed/non-zero when required tool/version checks are wrong or fail; prove both success and negative cases.
- Generated environment/shell output must safely represent arbitrary valid checkout paths and must not execute/interpolate command substitutions embedded in paths; include an adversarial regression case.
- Bootstrap must consume the committed manifest successfully from a fresh checkout; include the exact manifest/candidate identity used.
- Run relevant unit/static/tooling gates and inspect their actual summaries, not merely shell exit codes.
- Inspect the complete diff and run a secret scan before publication.
- Require a clean working tree at completion.
- Commit the exact finished candidate and publish that exact commit to dedicated remote review branch `claude/builder-environment-repair-review`. Do not merge it.
- Outbox must bind every evidence claim to the exact candidate SHA and review branch. If publication fails after the candidate is already built/tested, retry publication without rebuilding or mutating the candidate.

MANUAL/SIMULATED DEV TEAM CONTRACT TRIAL

Use this rejected-then-repaired Builder candidate as the first contract trial. Explicitly exercise/document, where applicable without inventing destructive scenarios:

- false-success handling: prior prose claiming success must not override independently reproduced failure;
- exact candidate identity binding;
- review invalidation if candidate code changes after review evidence was produced;
- publication retry without rebuilding/mutating an already verified candidate;
- obsolete/late/duplicate result handling, including the Mobile V1 duplicate-dispatch incident where a completed outbox was not published;
- reviewer gating: no acceptance merely because Builder says green;
- integration re-verification after a corrective change where applicable.

Capture any contract gaps in the existing Dev Team planning/review docs in the repair candidate only when they are a direct record of this verified trial. Do not silently work around contract defects. Do not begin Engineering Orchestrator implementation in this round.

DELIVERABLES

Replace `bridge/claude-outbox.md` with a detailed handoff containing:

- exact repaired candidate SHA and publication status for `claude/builder-environment-repair-review`;
- root cause and exact fix for each of the four defects;
- regression test names/results for each defect;
- fresh-checkout reconstruction proof and commands;
- doctor positive + negative proof;
- adversarial shell/path safety proof;
- relevant full gate summaries;
- complete diff scope and secret-scan result;
- clean-working-tree proof;
- contract-trial results for each item above and any remaining contract gaps;
- confirmation production was untouched and no secrets/live writes/permission widening occurred;
- unresolved blockers, clearly distinguishing safe engineering follow-up from owner-only decisions.

Do not claim acceptance yourself. Publish the candidate/evidence for independent review, write the outbox, and STOP. The watcher owns bridge publication.