# CHATGPT INBOX

## 2026-09-19 — build the permanent CROOKS Builder development environment

The watcher smoke test passed. This is now a real DEVELOPMENT-ENVIRONMENT task.

You are running headlessly in the standalone builder clone at /opt/crooks-builder.
Do not touch /opt/crooks-os except for read-only inspection where explicitly useful.
Do not merge or deploy production.
Do not install/start crooks-assistant.service.
Do not change Tailscale.
Do not provision/read/print secrets.
Do not enable CROOKS writes.
Do not call live Shopify/Gmail/ElevenLabs.
Do not redesign the CROOKS UI in this round.

OBJECTIVE

Create a reproducible, audited CROOKS Builder environment that makes future Claude engineering materially better at:

- frontend/UI/UX quality
- seeing and testing the actual rendered interface
- debugging
- code discovery/refactoring
- Python/JS/CSS/shell quality
- security
- performance measurement
- long-running autonomous work

Do not blindly bulk-install skill registries.
Do not add tools simply because they are popular.
Prefer a small number of strong, complementary tools with documented purpose and provenance.

IMPORTANT REPOSITORY / BRANCH RULES

- Remain in /opt/crooks-builder.
- The local working branch should remain claude/bridge-builder throughout this watcher run.
- Do not switch the production repo.
- Commit implementation/config/documentation changes on claude/bridge-builder.
- After the work is complete and clean, publish the resulting commit as the remote review branch:
    claude/builder-environment-review
  using an explicit branch push such as HEAD:refs/heads/claude/builder-environment-review.
- Do NOT merge it.
- If Claude's permission layer refuses that application-branch push, do not bypass it. Report the exact commit SHA and the blocked push in the outbox.

PRODUCT MEMORY

The product-memory documents may not exist in this builder checkout yet.

Fetch metadata/read-only as needed and read the canonical product-memory files directly from:
  origin/claude/product-memory-foundation

At minimum read, without switching the builder branch:
- crooks-assistant/docs/product-memory/PRODUCT_BRAIN.md
- ROADMAP.md
- DECISIONS.md
- SELF_IMPROVEMENT.md

Use git show / read-only Git plumbing if necessary.
Do not merge the product-memory branch in this round merely to read it.

Also read:
- crooks-assistant/PHASE_1_UX_BASELINE.md
- relevant Phase 2/3 engineering reports
- crooks-assistant/docs/ENGINEERING_LOOP.md
- current web/ frontend architecture
- current test/browser/audit scripts
- pyproject.toml / Makefile / existing developer tooling

PHASE 1 — INVENTORY FIRST

Before installing anything, inventory what is ALREADY present on this server and builder:

- /root/.claude skills/plugins/config
- project .claude directories
- exact existing skill names
- claude version/auth health, without displaying credential values
- Node/npm
- Python/.venv
- current Chromium/Playwright/browser tooling
- rg/fd/ast-grep
- shellcheck/shfmt
- uv
- gitleaks
- trivy
- biome
- pyright
- pytest plugins
- Shopify CLI/theme-check
- existing CROOKS browser/collision/audit harnesses
- any other useful development tools already present

Capture the BEFORE inventory durably.
Do not invent names for skills that are not actually installed.

PHASE 2 — THIRD-PARTY SKILL SECURITY GATE

Evaluate NVIDIA SkillSpector as the security gate for third-party Agent Skills.

Install it only in an isolated/user-space tool environment if the current upstream install is compatible and can be pinned/reproduced.

Before installing ANY third-party Agent Skill:
- inspect its actual repository/source
- pin an exact commit/version
- run SkillSpector static scanning where compatible
- inspect scripts/hooks/install behaviour
- record network/tool requirements
- record auto-trigger vs explicit-use behaviour
- identify overlap/conflict with existing CROOKS instructions

Do not introduce an API key simply to make SkillSpector work.
Static/local scanning is the required baseline.

If a skill produces a material security finding:
- do not install around it
- document the finding
- leave it uninstalled
- continue with unrelated safe work if possible

PHASE 3 — CORE DESIGN / UI SKILLS

Evaluate and, if compatible and clean under the security gate, install PROJECT-SCOPED, reproducibly pinned versions of:

1. Anthropic:
   - frontend-design
   - webapp-testing

2. Vercel:
   - web-design-guidelines

3. pbakaus/impeccable

4. ibelick/ui-skills:
   - create-design-md

5. Leonxlnx/taste-skill:
   - redesign-existing-projects
   - image-to-code
   - design-taste-frontend

CROOKS-SPECIFIC PRECEDENCE

design-taste-frontend is NOT the default authority for CROOKS operational/product screens.
It is for explicit creative/high-variance design work.

For existing CROOKS product UI:
- redesign-existing-projects and Impeccable are more directly relevant
- image-to-code only activates when a visual/reference image is supplied or explicitly requested
- Vercel web-design-guidelines is primarily an audit/review layer, not the visual authority

Do NOT bulk-install:
- awesome-design-agent-skills
- giant design registries
- full gstack
- UI UX Pro Max
- random skill packs

They may be documented as later/reference candidates.

PHASE 4 — CREATE ONE CROOKS DESIGN AUTHORITY

Use the create-design-md methodology, plus actual CROOKS source, UX baseline and Phase reports, to create a PROPOSED:

  crooks-assistant/DESIGN.md

This must document the existing CROOKS product language and interaction constraints.
Do not invent a replacement aesthetic.

Cover:
- visual hierarchy
- typography
- spacing/density
- colour / near-black / glass system
- controls
- touch targets
- selected/armed states
- cards and nested surfaces
- navigation
- responsive/device behaviour
- motion
- accessibility
- loading/error/empty states
- Samsung performance constraints
- speech-vs-screen principle
- maximum-capability / minimum-visible-UI principle

Authority order for future UI work:

1. owner request
2. PRODUCT_BRAIN / DECISIONS / UX invariants
3. DESIGN.md
4. existing functional/safety behaviour
5. specialist design skills

A third-party design skill must never silently override CROOKS product intent.

If Impeccable expects its own PRODUCT.md, do not create a competing source of truth.
Either configure it to use the existing product-memory system or create only a minimal pointer if absolutely necessary.

PHASE 5 — BROWSER / VISUAL TOOLING

Audit first. Preserve existing CROOKS browser/collision/experience tooling.

Evaluate/install a PINNED Microsoft Playwright CLI + Claude skills setup where compatible.

Also provide/evaluate:
- @axe-core/playwright
- screenshot capture
- visual comparison capability
- Playwright accessibility/ARIA snapshots
- traces
- console/browser-log capture

Do not replace CROOKS's existing browser, collision, experience or physical-test harnesses.
Playwright AUGMENTS them.

Define a future visual verification matrix including at minimum:
- existing 601x889 test viewport
- 800x1280 Samsung/tablet viewport
- a representative iPhone/mobile viewport
- desktop/control viewport where relevant

Future UI workflow should be capable of:

before screenshot
→ implement
→ after screenshot
→ interaction test
→ CROOKS collision/browser tests
→ accessibility audit
→ visual comparison
→ bounded specialist critique

PROVE in this round, without live business APIs, that the browser tooling can:
- open a local CROOKS/fixture page
- capture a screenshot
- inspect/log browser state
- close the browser process cleanly

SYSTEM PACKAGE RULE

The watcher sandbox intentionally cannot modify /usr or production system areas.

Prefer:
- project-local installs
- /root/.local
- /root/.cache
- isolated virtual environments
- pinned npm/pip/uv tooling

Do NOT weaken the watcher sandbox to install packages.

If Chromium or another tool requires an OS package that cannot be installed inside the sandbox:
- do not bypass
- record the exact missing package(s)
- provide the exact future owner-approved command
- continue all work that does not require it

PHASE 6 — GENERAL ENGINEERING TOOLS

Audit first, then install appropriate current stable PINNED versions in user/project scope where useful and compatible:

- ripgrep
- fd
- ast-grep
- shellcheck
- shfmt
- gitleaks
- uv
- biome
- pyright
- trivy
- hyperfine

Rules:
- do not bulk-reformat existing CROOKS JS/CSS with Biome
- Biome begins advisory/check-only
- Pyright begins advisory/check-only
- a warning-heavy new tool is NOT a required gate until a baseline is established
- do not duplicate an already adequate installed tool without reason
- no network listener/service
- do not modify production system configuration

PHASE 7 — PYTHON TEST QUALITY

In the BUILDER only, evaluate:

- pytest-xdist
- pytest-timeout
- pytest-cov
- Hypothesis

The current offline suite is roughly 2,900 tests and historically around 8 minutes.

Benchmark pytest-xdist only if the current builder checkout contains the relevant test setup and dependencies.

Adopt parallel execution only if repeated runs show:
- deterministic results
- no shared-state/race failures
- unchanged semantics

Do NOT hide flaky tests with retries.

Hypothesis should be recommended/applied only where property testing genuinely helps, especially:
- parsers
- serialization
- proposal/action state machines
- future Event Ledger logic

Do not rewrite existing tests merely to claim Hypothesis usage.

PHASE 8 — CLAUDE PROJECT CONFIGURATION

Propose/create a clean project-scoped Claude environment with:

- concise CLAUDE.md
- .claude/rules/ for topic/path-specific rules
- project skills
- future specialist-agent slots
- deterministic hooks where useful

Do NOT put thousands of lines in CLAUDE.md.

Permanent instructions should mostly point to:
- PRODUCT_BRAIN
- DECISIONS
- DESIGN.md
- engineering/test commands
- safety invariants
- builder-vs-production boundaries

Evaluate hooks such as:
- Python changed → targeted Ruff feedback
- shell changed → ShellCheck
- JS/CSS changed → Biome check
- before commit/publication → Gitleaks
- UI candidate completion → relevant browser/collision checks

Do not run the full suite after every file edit.
Do not create hooks that mutate source unexpectedly.

PHASE 9 — REPRODUCIBILITY / ANTI-FORGETTING

Create:

  crooks-assistant/docs/DEV_ENVIRONMENT.md

For every installed/adopted tool/skill record:
- name
- purpose
- upstream repository
- exact version/commit
- install scope/path
- auto-trigger vs explicit use
- hooks/scripts introduced
- network requirements
- security scan result/date
- update policy

Also create an idempotent builder environment check/bootstrap approach so this environment can be recreated on a fresh server without relying on chat memory.

Prefer:
- a manifest
- a read-only doctor/check command
- a bootstrap script that is explicit and idempotent

Do NOT auto-update third-party skills.

Future update policy:
upstream update → security scan → diff → test → review → update manifest.

PHASE 10 — LATER CANDIDATES, RESEARCH/RECORD ONLY

Research and document whether these are worth adding later, but DO NOT install them now unless required by an earlier explicit phase:

- Emil Kowalski motion/design skills
- UI UX Pro Max
- selected gstack concepts such as investigate, QA, review, design-review
- Lighthouse CI
- Shopify CLI + Theme Check for the Shopify-theme side
- Semgrep / additional SAST
- load testing
- Python profiling
- disposable container sandboxing for future autonomous workers
- code-intelligence / LSP tooling
- GitHub App
- Privileged Action Broker

Do not install full gstack.
Do not install any third-party deploy/ship automation.
CROOKS already has its own deployment gates and planned GPT↔Claude hierarchy.

FINAL VERIFICATION

At the end, verify as much as the sandbox permits:

- every installed tool's version/help check
- SkillSpector works, if adopted
- Gitleaks works without exposing values
- ShellCheck works
- Biome check works without rewriting source
- Playwright/browser smoke test
- screenshot created
- browser process closes cleanly
- accessibility tooling can execute
- pytest-xdist benchmark if appropriate
- disk-space impact
- no secrets introduced
- no production files changed
- builder working tree clean after commit
- no service / Tailscale / CROOKS production state changed

Before committing:
- inspect the full diff
- run secret scanning over the candidate
- ensure generated caches/browser binaries/tool environments are NOT accidentally committed
- ensure only reproducible manifests/config/docs/scripts/project skills are committed

COMMIT / REVIEW BRANCH

Commit the candidate on local claude/bridge-builder with a clear message.

Then try to publish that exact commit to:
  origin/claude/builder-environment-review

Do not merge it.
Do not push production.
Do not push --all.
Do not push tags.

If application-branch publication is blocked by Claude permissions, leave the local commit intact and report the exact SHA. Do not widen permissions.

OUTBOX REPORT

Replace bridge/claude-outbox.md with a detailed handoff containing:

1. exact inventory BEFORE
2. exact inventory AFTER
3. skills evaluated
4. skills installed
5. skills rejected/deferred and why
6. security scan results
7. exact versions/commits/upstreams
8. DESIGN.md summary
9. browser/visual tooling proof
10. test/benchmark results
11. new CLAUDE.md/rules/hooks structure
12. DEV_ENVIRONMENT/bootstrap/check structure
13. disk impact
14. exact builder commit SHA
15. whether claude/builder-environment-review was successfully pushed
16. exact git status
17. production unchanged proof
18. anything that still needs owner approval
19. recommended next step

Then STOP.

Do not run git add/commit/push for the bridge outbox itself; the watcher owns outbox publication.
