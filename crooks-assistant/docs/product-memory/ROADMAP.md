# CROOKS OS — Roadmap

**Last consolidated:** 2026-09-19  
**Purpose:** keep sequencing explicit so ambitious ideas do not derail the current product.

This roadmap is intentionally staged. “Later” ideas should not be used as an excuse to leave the current product unfinished.

---

# NOW — make the current CROOKS product genuinely reliable

## N1. Complete the always-on Linux deployment
**Status:** BUILDING

- finish review of Linux migration code
- provision secrets safely
- install `crooks-assistant.service`
- enable private Tailscale HTTPS
- verify reboot recovery
- verify Claude Max auth under systemd
- verify Shopify read path
- verify Gmail
- verify ElevenLabs Scribe
- verify Derek TTS
- keep writes disabled until the read/runtime layer is proven
- keep Mac deployment as rollback
- later move service from temporary root execution to a dedicated `crooks` user

## N2. Install the Claude inbox watcher
**Status:** SHIPPED

- standalone bridge and builder clones
- poll inbox blob SHA, not branch HEAD
- single-run lock
- failed instructions remain pending
- bounded backoff/retry
- Claude Max auth preserved
- production checkout read-only to watcher
- watcher owns outbox publication
- stdin prompt delivery regression-tested
- corrected watcher passed end-to-end automatic smoke test
- no public webhook endpoint required
- normal GPT → Claude → outbox loop no longer requires the owner to relay messages

## N3. Perfect the current UI
**Status:** PLANNED

Primary focus after deployment.

- fix truncation/spacing/layout issues
- remove engineering-looking UI
- make mobile responsive
- Samsung refinement
- iPhone refinement
- better loading states
- better error states
- better media/image presentation
- cleaner action cards
- one contextual action where possible
- reduce unnecessary information density
- improve CROOKS Control from engineering utility to polished resizable app

## N4. Perfect response behaviour
**Status:** PLANNED

- concise by default
- better entity/customer/order focus
- fewer unnecessary clarifying questions
- better multi-turn context
- reduce repeated answers
- reduce hallucinated references
- lower model/tool latency
- improve voice turn-taking and interruptions
- improve “what actually matters” presentation

## N5. Real-world test sessions
**Status:** PLANNED

Use CROOKS normally and intentionally stress:

- Shopify queries
- Gmail
- customer/order lookup
- product questions
- voice
- images
- action proposals
- multi-turn context
- device switching

Capture:

- failures
- friction
- corrections
- latency
- abandoned interactions
- screenshots
- tool/action traces

## N6. Product-memory foundation
**Status:** BUILDING / ACTIVE

- PRODUCT_BRAIN
- ROADMAP
- IDEAS
- FEATURES
- DECISIONS
- SELF_IMPROVEMENT
- CURRENT_TRUTH
- EVOLUTION_POLICY
- DIRECTOR_PROTOCOL

All future meaningful ideas and architecture decisions should become durable entries.

Active context must remain curated: Git stores history; current truth and active decisions drive new releases.

## N7. Permanent Builder Environment
**Status:** BUILDING

Build the reproducible engineering environment currently running through the automated bridge:

- security-gated project skills,
- current DESIGN.md derived from CROOKS evidence,
- browser/Playwright/accessibility tooling,
- code-discovery/security/performance tools,
- concise CLAUDE.md/rules/hooks,
- DEV_ENVIRONMENT manifest,
- idempotent bootstrap/check,
- no production deployment as part of this task.

---

# NEXT — make CROOKS proactive and operationally useful

## X1. Formal issue/improvement pipeline
**Status:** PLANNED

Convert telemetry into structured categories:

- bug
- UI friction
- UX friction
- bad response
- latency
- failed tool call
- wrong entity
- visual issue
- repeated owner correction
- automation opportunity

This becomes the engineering backlog.

## X2. CROOKS World / persistent business state
**Status:** APPROVED DIRECTION

Core entities:

- Person
- Customer
- Order
- Product
- Production
- Supplier
- Payment
- Shipment
- Issue
- Decision
- Task
- Event

Build durable relationships and provenance.

## X3. Event Ledger
**Status:** APPROVED DIRECTION

- append important events
- preserve source/provenance
- support debugging, audit, replay, anticipation, automation
- avoid relying on model memory for durable state

## X4. Expectations and deadlines
**Status:** APPROVED DIRECTION

Convert normal statements into structured expectations.

Example:
“Jessica said the sample takes four weeks.”

Becomes:

- supplier: Jessica
- related product/production item
- expected milestone
- due date
- source event
- escalation rule

## X5. Attention / “What needs me?”
**Status:** APPROVED DIRECTION

Core owner experience:

- surface exceptions
- suppress routine normality
- prioritise by urgency/materiality
- “What needs my attention?” should be first-class

## X6. Notifications
**Status:** PLANNED

Examples:

- supplier overdue
- refund approval required
- order stuck
- stock risk
- important support issue

Notifications should be selective, not noisy.

## X7. Automation/Objectives engine
**Status:** APPROVED DIRECTION

Support:

- scheduled
- event-driven
- conditional
- deadline-based
- stateful
- goal-based
- human-in-the-loop
- narrow autonomous actions

Natural-language authoring should be possible without exposing workflow-builder complexity.

## X8. Earned autonomy
**Status:** APPROVED DIRECTION

Track repeated approval patterns.

Example:
“You approved this exact class of action 31/31 times. Allow CROOKS to handle these automatically?”

Autonomy remains action-class-specific.

---

# NEXT — integrations that make CROOKS an operating layer

## I1. WhatsApp
**Status:** CAPTURED / HIGH VALUE

- ingest supplier/customer messages
- link messages to business entities
- use messages as event triggers
- draft replies
- approved sending
- supplier follow-up automation
- optional CROOKS control channel later

## I2. Royal Mail Click & Drop
**Status:** CAPTURED / HIGH VALUE

- create labels
- attach tracking
- monitor dispatch state
- detect label-created/not-dispatched mismatch
- track shipment progression
- surface stuck parcels
- verified fulfilment actions

## I3. Resend
**Status:** CAPTURED

Use as a clean transactional outbound-email layer for:

- operational notifications
- supplier/customer messages
- system reports
- controlled templates

Gmail remains useful for inbox/conversation ingestion.

## I4. Stripe
**Status:** PLANNED

- payment state
- refunds/charge context
- event triggers
- financial verification

## I5. Drive / Notes / business documents
**Status:** CAPTURED

- durable supplier/product docs
- decision context
- production notes
- linked document references

## I6. Base44/internal apps
**Status:** CAPTURED

Treat internal apps as capabilities/data sources inside CROOKS rather than isolated tools.

## I7. Broader fulfilment/supplier integrations
**Status:** CAPTURED

Use a capability graph so integrations do not become one-off hardcoded logic.

---

# LATER — make CROOKS model-independent and anticipatory

## L1. Model Gateway
**Status:** APPROVED DIRECTION

- Claude primary where appropriate
- fallback provider/model
- specialist model routing
- deterministic routes for non-AI work
- usage-limit resilience
- model vendor invisible to product/user

## L2. Anticipation engine
**Status:** APPROVED DIRECTION

Move from request-response to continuous business awareness.

Detect:

- overdue supplier milestones
- stuck fulfilment
- likely stock-outs
- unresolved customer problems
- important communications
- sales anomalies
- missing expected events

## L3. Objectives
**Status:** APPROVED DIRECTION

Persistent goals rather than isolated tasks.

Examples:

- keep support backlog controlled
- maintain production progress
- prevent avoidable stock-outs
- prevent overdue fulfilment exceptions
- surface high-risk refunds

## L4. Scene compiler
**Status:** APPROVED DIRECTION

Render the smallest useful interface based on current context/objective:

- text
- card
- timeline
- one action
- warning
- nothing

## L5. Multi-user/staff permissions
**Status:** CAPTURED

Potential roles:

- owner
- fulfilment
- customer service
- product development
- supplier-facing
- finance

All share the same World with scoped capabilities.

---

# LATER — controlled self-improvement

## S1. Nightly Observer
**Status:** APPROVED DIRECTION

Analyse:

- error logs
- turn/verbal logs
- image logs
- UI telemetry
- action ledger
- corrections
- latency
- abandoned interactions
- physical test sessions

Output evidence-backed issues, not speculative “improvements.”

## S2. Reproduction and replay
**Status:** APPROVED DIRECTION

Before changing code:

- reproduce issue
- freeze relevant evidence
- create regression fixture
- prove candidate improves the original failure

## S3. Builder environment
**Status:** APPROVED DIRECTION

- isolated worktree/branch
- never edit live production directly
- sanitised test/replay data
- full suite before promotion

## S4. Independent review
**Status:** APPROVED DIRECTION

Developer agent cannot be its own sole reviewer.

Reviewers should challenge:

- diagnosis
- necessity
- regression risk
- test quality
- changed expectations
- security implications

## S5. Morning improvement report
**Status:** CAPTURED

Example:

- interactions analysed
- issues detected
- issues reproduced
- fixes prepared
- fixes rejected
- candidates ready
- production changes made

Initially zero production auto-deploy.

## S6. Limited autonomous deployment
**Status:** SOMEDAY

Possible only for narrow, low-risk, objectively verified classes.

High-risk areas remain approval-gated:

- auth
- secrets
- refunds
- permissions
- Shopify write semantics
- action authorisation
- migrations

---

# LATER — autonomous engineering organisation

## D1. Claude Dev Manager
**Status:** CAPTURED

Takes broad engineering objectives and decomposes them into specialist tasks.

## D2. Specialist workers
**Status:** CAPTURED

Potential agents:

- UI Engineer
- UX Researcher
- Debugger
- Feature Engineer
- QA/Test Engineer
- Performance Engineer
- Security/Actions Reviewer
- Integration Engineer

## D3. Specialist critics
**Status:** CAPTURED

Each worker has an independent “voice of reason” reviewer.

Reviewer objective is to find why a change should **not** ship, not to agree by default.

## D4. Parallel isolated worktrees
**Status:** APPROVED DIRECTION

Each worker gets:

- own task
- own branch
- own worktree
- narrow tools/context

Never repeat the shared-working-tree collision experienced during Linux migration.

## D5. GPT Director
**Status:** CAPTURED

GPT sits above Claude manager/team as an independent architecture/review layer.

Reads:

- actual diffs
- tests
- replay results
- worker reports
- product memory

Can approve, reject, or send work back.

## D6. Owner escalation
**Status:** APPROVED DIRECTION

Agents should escalate decisions that are fundamentally product/taste/strategy questions.

The owner should not be used as a command courier.

## D7. Engineering Orchestrator V1
**Status:** APPROVED DIRECTION

Build the layer above the single-worker watcher:

- task queue,
- quality-first model/effort selection,
- isolated worker workspace per task,
- safe parallel execution,
- dependency tracking,
- result/evidence collection,
- independent review routing,
- integration gate,
- bounded retries and escalation.

Do not obtain concurrency by allowing several writers into the same checkout.

## D8. Fable Experience Director
**Status:** APPROVED DIRECTION

Make Fable a first-class specialist for substantial UX/interaction work:

- pre-implementation experience direction,
- device/workflow evaluation,
- post-implementation independent experience review.

Fable complements DESIGN.md, browser evidence and technical review.

## D9. Quality-first model routing
**Status:** APPROVED DIRECTION

Routing should use:
- Opus for high-complexity/high-risk reasoning,
- Sonnet for bounded implementation,
- cheaper/faster models only for mechanical work,
- automatic escalation on ambiguity/failure/risk.

Cost and speed must not reduce code/product quality.

## D10. Privileged Action Broker + Deployment/Infrastructure Controller
**Status:** APPROVED DIRECTION

Bootstrap a controlled privileged plane so approved backend/infrastructure changes no longer require routine owner shell commands.

Requirements:
- allowlisted structured privileged actions,
- exact artifact/version identity,
- owner approval gates where needed,
- versioned installs,
- health checks,
- automatic rollback,
- separation of duties for self-updating infrastructure,
- SSH/Termius retained as break-glass recovery.

## D11. Active Context / release evolution automation
**Status:** APPROVED DIRECTION

Automate the memory procedures in DIRECTOR_PROTOCOL:

- bootstrap current truth,
- generate Active Context Packs,
- classify active vs historical/superseded constraints,
- supersede/retire obsolete architecture explicitly,
- audit memory drift,
- keep future releases free to simplify/delete obsolete systems while preserving current outcomes and lessons.

---

# SOMEDAY — CROOKS manages its own engineering

## Y1. Natural-language engineering requests
**Status:** CAPTURED

Example:
“That customer screen was bad — fix whatever caused it.”

CROOKS packages:

- screenshot
- verbal turn
- focused entity
- logs
- tool calls
- UI state
- source context

Then invokes Builder/Reviewer automatically.

## Y2. CROOKS-managed Claude Code
**Status:** CAPTURED

User no longer “uses Claude Code.”

Claude Code becomes an internal engineering worker.

Termius becomes emergency/admin access only.

## Y3. Automatic GPT ↔ Claude loop
**Status:** CAPTURED

- Claude completes
- GPT reviews
- GPT writes next instruction
- watcher launches Claude again
- repeat until gate or escalation

Hard stop conditions and max rounds required.

---

# SOMEDAY — subscriber product

## P1. CROOKS SaaS
**Status:** APPROVED DIRECTION

Configurable operating layer for ecommerce/small businesses.

## P2. Simple onboarding
**Status:** APPROVED DIRECTION

Target:

1. create account
2. connect Shopify
3. connect email
4. connect payments/fulfilment
5. CROOKS builds business model
6. use normally

No agent/MCP/prompt setup required.

## P3. Subscriber differentiation
**Status:** APPROVED DIRECTION

Sell:

- one intelligent business control centre
- persistent context
- proactive exceptions
- verified actions
- automation
- easy UI

Not:

- “another chatbot”
- “Claude with Shopify attached”

## P4. Multi-device commercial clients
**Status:** CAPTURED

- phone
- tablet
- desktop/control
- notifications
- role-based staff interfaces

---

# Sequencing rule

Do not jump to Later/Someday because the concept is exciting.

The current sequence remains:

1. stable always-on deployment
2. excellent UI/responses/reliability
3. real-world evidence
4. persistent World + attention + automation
5. broader integrations
6. self-improvement
7. multi-agent dev organisation + privileged infrastructure control
8. subscriber product expansion

At every stage, apply EVOLUTION_POLICY: inherit value and evidence, not obsolete implementation form.

The system should earn complexity only after the layer below it is reliable.
