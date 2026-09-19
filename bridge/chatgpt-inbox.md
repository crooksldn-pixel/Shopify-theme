# CHATGPT INBOX

## 2026-09-19 — CROOKS Mobile Experience V1

The permanent Builder Environment candidate completed successfully and is published for review at `claude/builder-environment-review` commit `9a27bc441adad1e98e8a9ca257d1883246ee7eec`.

This is a bounded PRODUCT-UI DEVELOPMENT task. Work only in the standalone builder clone at `/opt/crooks-builder`. Do not touch `/opt/crooks-os` except read-only inspection if genuinely necessary. Do not merge or deploy production. Do not install/start services, change Tailscale, provision/read/print secrets, enable CROOKS writes, or call live Shopify/Gmail/ElevenLabs.

OBJECTIVE

Build a high-quality CROOKS Mobile Experience V1 candidate focused on representative iPhone/mobile layouts while preserving the current CROOKS product doctrine, safety/action semantics, and existing Samsung/tablet behaviour. This is not a blank-sheet redesign and must not create a separate mobile product. It should make the existing CROOKS/Jarvis experience feel intentional, fast, touch-native and coherent on a phone.

SOURCE OF TRUTH / PRECEDENCE

Before changing UI, read the canonical product-memory material from the appropriate existing refs without merging merely to read it, including at minimum PRODUCT_BRAIN.md, ROADMAP.md, DECISIONS.md, SELF_IMPROVEMENT.md, PHASE_1_UX_BASELINE.md, relevant Phase reports, ENGINEERING_LOOP.md, and the proposed `crooks-assistant/DESIGN.md` from `claude/builder-environment-review`.

Authority order remains: owner request → PRODUCT_BRAIN/DECISIONS/UX invariants → DESIGN.md → existing functional/safety behaviour → specialist design guidance. Do not let a third-party design convention silently override CROOKS intent.

BUILDER / BRANCH RULES

- Remain in `/opt/crooks-builder`.
- Start from the appropriate current builder/application state and incorporate the Builder Environment candidate only as needed to use its audited tooling; do not merge or alter production.
- Work on an isolated local branch suitable for this task, e.g. `claude/mobile-experience-v1`.
- Commit the finished candidate there.
- Publish the exact finished commit to remote review branch `claude/mobile-experience-v1-review`.
- Do NOT merge it.
- If permission refuses an application-branch push, do not bypass it; report the exact commit SHA and blocked operation in the outbox.

KNOWN BROWSER-GATE FINDING

The revived browser gate has one deterministic existing finding: a 95 ms press on the Split control does not land. Treat this as evidence, not permission for a broad behavioural rewrite. During this mobile task, attribute the failure precisely. If the fix is clearly a UI hit-target/layering/pointer-events defect and can be corrected without changing action semantics, speech semantics, authorization, or backend behaviour, include the smallest safe fix and prove it with a regression test. If attribution points to broader behavioural/safety semantics, leave it unchanged and report it. Do not weaken or skip the browser gate merely to make the candidate green.

MOBILE EXPERIENCE SCOPE

Audit the actual rendered interface first. Capture BEFORE evidence before editing. Then improve the existing interface for representative phone use, including where applicable:

- responsive layout and information hierarchy at representative iPhone/mobile widths;
- navigation and screen hierarchy;
- thumb-friendly placement and touch targets;
- voice input/control placement without increasing accidental speech activation risk;
- order/customer/product cards and operational information density;
- proposal/action approval cards while preserving all existing approval/arming/expiry semantics;
- loading, error and empty states only where supported by real product state — do not fake completion;
- text truncation, overflow and long-content behaviour;
- image/media presentation;
- on-screen keyboard behaviour and viewport resizing;
- iOS safe-area/notch/home-indicator handling;
- modal/sheet behaviour;
- typography and density;
- motion/transitions only where useful and with `prefers-reduced-motion` preserved;
- accessibility and readable focus/selected/armed/disabled-with-reason states;
- performance appropriate to the existing no-external-resource/Samsung constraints.

The goal is maximum capability with minimum visible UI, not simply shrinking the desktop/tablet surface or adding decorative complexity.

NON-REGRESSION REQUIREMENTS

Preserve existing tablet/Samsung behaviour. At minimum test the established 601×889 viewport, 800×1280 Samsung/tablet viewport, representative iPhone/mobile viewport(s) such as 390×844, and a desktop/control viewport where relevant. Do not degrade speech-vs-screen behaviour, layer safety, disabled-with-reason actions, proposal/action safety, write gating, or any other existing safety invariant.

EVIDENCE-DRIVEN WORKFLOW

Use the Builder Environment tooling that is actually available. Do not widen Claude permissions or require the deferred project-scoped `.claude/` installation to proceed. That deferred configuration is not a blocker for this bounded task.

Required workflow:

1. Inspect current source and rendered UI.
2. Capture BEFORE screenshots at the required viewport matrix.
3. Record the concrete mobile defects/opportunities observed.
4. Implement the smallest coherent responsive/mobile improvement set.
5. Capture AFTER screenshots at the same viewports.
6. Run interaction tests, including touch-target and navigation behaviour.
7. Run existing CROOKS browser/collision/experience regressions.
8. Run accessibility checks with the available axe/Playwright tooling and inspect meaningful ARIA/focus state where applicable.
9. Test safe-area behaviour, keyboard/viewport behaviour, overflow/truncation, loading/error/empty states that are actually reachable, and reduced-motion behaviour.
10. Re-run the Split-control reproduction and document whether it is fixed, unchanged, or intentionally deferred with attribution.
11. Run relevant Python/unit tests and any targeted static checks required by changed file types.
12. Inspect the full diff and secret-scan the candidate before commit/publication.

Do not bulk-reformat unrelated source. Do not change backend/action semantics merely for visual convenience. Do not invent live business data or call live APIs.

DELIVERABLES

The review candidate must include or otherwise durably reference:

- exact candidate commit SHA;
- `claude/mobile-experience-v1-review` publication status;
- concise rationale for each intentional UX change;
- BEFORE and AFTER screenshot evidence at representative iPhone plus Samsung/tablet and control viewports;
- interaction-test results;
- accessibility results;
- browser/collision/experience regression results;
- relevant unit/static test results;
- safe-area/keyboard/touch-target/navigation/loading/error/empty-state findings;
- Split-control finding and regression evidence;
- confirmation that production was untouched and no live APIs/writes/secrets were used;
- unresolved issues or items requiring owner judgement.

QUALITY BAR

Do not claim success from screenshots alone. The candidate must be visually coherent AND interaction-tested. Do not hide failures. If a test exposes a pre-existing issue, distinguish it from regressions introduced by this candidate. Prefer a smaller polished candidate over a broad speculative redesign.

OUTBOX

When complete, replace `bridge/claude-outbox.md` with a detailed handoff containing the evidence above and recommended next step, then STOP. Do not commit/push the bridge outbox itself; the watcher owns publication.
