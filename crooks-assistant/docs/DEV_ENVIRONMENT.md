# CROOKS Builder — development environment

**Scope:** the builder worktree (`/opt/crooks-builder`, branch `claude/bridge-builder`) only.
**Not** the production checkout at `/opt/crooks-os/crooks-assistant`, and **not** the
`crooks-assistant` service. Nothing described here runs in production, listens on a socket, or
needs a secret.

The machine-readable source of truth is **`docs/dev-environment/manifest.json`**. This file is the
prose around it: why each thing is here, what it may and may not do, and what is still missing.

```
python3 scripts/dev_env.py doctor      # what is installed, what is missing   (read-only)
python3 scripts/dev_env.py env         # the exports a browser run needs      (read-only)
python3 scripts/dev_env.py bootstrap   # the exact, idempotent install steps
eval "$(python3 crooks-assistant/scripts/dev_env.py env)"
```

`doctor` exits non-zero when anything is missing, so it can be used as a precondition.

---

## 1. Why this exists

Two problems, both observed in this round:

1. **The CROOKS browser harness was inert on this server.** `experience/browser.py` and the
   eleven scripts in `scripts/browser/` have always required Playwright and a Chromium at
   `chromium-1194`. Neither was installed here, and the builder had no `.venv` at all, so every
   browser check reported itself *skipped* — honestly, but it proved nothing.
2. **The environment lived in a chat.** Nothing recorded which versions were used or why, so it
   could not be rebuilt on a fresh server.

Everything below is pinned, and nothing self-updates.

---

## 2. Layout

| Path | Contents | Committed? |
|---|---|---|
| `.tooling/bin` | single static binaries | no — gitignored |
| `.tooling/node` | pinned npm project (Playwright, axe, Biome) | no |
| `.tooling/browsers` | Playwright's Chromium 1194 | no |
| `.tooling/sysroot` | Chromium's shared libraries, extracted locally | no |
| `.tooling/uv-tools` | isolated env for SkillSpector | no |
| `.tooling/scans` | SkillSpector reports | no |
| `crooks-assistant/.venv` | project venv + builder test tooling | no |
| `crooks-assistant/docs/dev-environment/manifest.json` | the pins | **yes** |
| `crooks-assistant/scripts/dev_env.py` | doctor / env / bootstrap | **yes** |

`.tooling/` (~1.8 GB) and `.venv/` (~630 MB) are gitignored. Only manifests, scripts and docs are
committed.

---

## 3. The browser stack, and the one non-obvious thing

### 3.1 Playwright 1.56.1 was chosen to match existing CROOKS source

`experience/browser.py` already reads:

```python
CHROMIUM = os.environ.get("CROOKS_CHROMIUM", "/opt/pw-browsers/chromium-1194/chrome-linux/chrome")
```

Playwright **1.56.1** is the release that ships Chromium build **1194**. The pin was selected to
match the build number CROOKS already expects, not by taking the newest release. Changing this pin
changes the build number and silently breaks the default path.

### 3.2 `NODE_PATH` is required, and its absence looks like "not installed"

`scripts/browser/*.js` do `require('playwright')`. Node resolves that from the **script's own
directory**, not the working directory. With the tooling in `.tooling/node/node_modules`, the
scripts cannot see it unless `NODE_PATH` is set. Without it, `experience.browser.available()`
reports `playwright-core is not installed` even though it is.

`dev_env.py env` sets it. This is the single most likely thing to go wrong.

### 3.3 Chromium's shared libraries, and the read-only `/usr`

Chromium needs 12 shared libraries that are not present on this host:

```
libnspr4 libnss3 libnssutil3 libsmime3 libatk-1.0 libatk-bridge-2.0 libatspi
libcairo libcups libpango-1.0 libasound libXdamage
```

`apt-get install` cannot supply them: **`/usr` is read-only in the watcher sandbox, deliberately,
and must stay that way.** Rather than weaken the sandbox, the `.deb` payloads are downloaded and
extracted into `.tooling/sysroot/root`, and Chromium is run with `LD_LIBRARY_PATH` pointing there.

- 89 packages extracted; nothing outside `/opt/crooks-builder` is written.
- `libc6`, `libgcc-s1`, `libstdc++6` and `gcc-14-base` are **deliberately excluded** so the system
  C runtime is never shadowed.

If the owner would rather install these properly, the exact command is in
`manifest.json → sysroot.owner_approved_alternative`. **It has not been run** — it needs owner
approval and a writable `/usr`.

### 3.4 What was proven in this round

Against a local fixture page, with no live business API:

| Capability | Result |
|---|---|
| Chromium starts | Chromium **141.0.7390.37** |
| Renders and executes JS | yes |
| Screenshot at 601×889 DPR 1.33 | 34 KB PNG written |
| Console capture | `[console.log] probe: page script ran` |
| ARIA snapshot | heading / paragraph / button captured |
| axe-core audit | executed — 13 passes, 2 moderate violations on the fixture |
| Browser closes cleanly | no lingering processes |
| `experience.browser.available()` | **AVAILABLE** |

### 3.5 The visual verification matrix

Defined in `DESIGN.md` §13, and the workflow it supports:

```
before screenshot → implement → after screenshot → interaction test
→ CROOKS collision/browser gate → accessibility audit → visual comparison
→ bounded specialist critique
```

**Playwright augments the existing CROOKS harnesses; it does not replace them.** The collision,
touch, experience and physical-test harnesses stay exactly as they are. axe-core cannot see two
boxes that are each the right size and in the same place — which is the defect class
`collision.js` exists for.

---

## 4. Installed tools

Full pins in `manifest.json`. Summary, with the policy attached to each:

| Tool | Version | Policy |
|---|---|---|
| shellcheck | 0.11.0 | advisory |
| shfmt | 3.12.0 | **check only** (`-d`), never `-w` on existing shell |
| gitleaks | 8.30.1 | pre-publication gate; reports rule + path, **never a value** |
| fd | 10.3.0 | — |
| ast-grep | 0.40.0 | the `sg` alias upstream ships is **deleted** — `/usr/bin/sg` is `newgrp` |
| hyperfine | 1.20.0 | — |
| trivy | 0.74.0 | downloads a vulnerability DB on first use |
| uv | 0.9.9 | — |
| playwright | 1.56.1 | pinned to Chromium 1194, see §3.1 |
| @axe-core/playwright | 4.11.1 | supplements, never replaces, CROOKS harnesses |
| @biomejs/biome | 2.5.14 | **advisory, check-only.** Not a gate. See §4.1 |
| pyright | 1.1.407 | **advisory, check-only.** Not a gate |
| pytest-xdist / -timeout / -cov | 3.8.0 / 2.4.0 / 7.0.0 | see §6 |
| hypothesis | 6.145.1 | only where property testing genuinely helps |
| skillspector | 2.11.2 @ `d162d9b` | `--no-llm` mandatory; see §5 |

Already present and **not** duplicated: `ripgrep 14.1.1` (bundled with Claude Code), `node
v22.23.2`, `npm 10.9.8`, `python 3.12.3`, `jq`, `git`, `ruff 0.16.8` (via the project's own
`[dev]` extra).

### 4.1 Why Biome is advisory

First run over `web/`: **20 errors, 272 warnings, 18 infos across 14 files** — and
`No fixes applied`, with `web/` verifiably unmodified afterwards.

A warning-heavy new tool is not a gate until a baseline exists. **Do not bulk-reformat CROOKS
JS/CSS.** `web/style.css` and `web/ui.js` carry extensive load-bearing commentary and a
hand-maintained token ladder; a reformat would destroy review history for no product gain.

Worth a future, *deliberate* look (not this round, which does not touch the UI):

- `lint/a11y/useAriaPropsSupportedByRole` — 3 errors
- `lint/a11y/useSemanticElements` — 2 errors
- `lint/suspicious/noDuplicateProperties` — 1 error

---

## 5. The third-party skill security gate

**No third-party Agent Skill is installed without passing this gate first.**

```bash
skillspector scan <path> --no-llm --format json --output .tooling/scans/<name>.json
```

`--no-llm` is mandatory here. It keeps file contents local, requires no API key, and none is
provisioned. The SC4 supply-chain check still queries `api.osv.dev` with dependency
**coordinates only** — never file contents — and falls back to a bundled list offline.

The gate is: inspect the real repository → pin an exact commit → scan → read the flagged lines
yourself → record triggers, network needs and overlap with CROOKS instructions.

**A scanner verdict is evidence, not a decision.** Both outcomes happened in this round: a HIGH
that was a false positive, and MEDIUMs that were real.

### 5.1 Results

| Skill | Upstream | Pinned commit | Scan | Verdict |
|---|---|---|---|---|
| `frontend-design` | `anthropics/skills` | `34040c9` | 1 HIGH | **CLEARED** — false positive |
| `webapp-testing` | `anthropics/skills` | `34040c9` | 2 HIGH, 3 MED | **REJECTED** |
| `web-interface-guidelines` | `vercel-labs/web-interface-guidelines` | `e3d624b` | 3 MED | **CLEARED, content only** |
| `create-design-md` | `ibelick/ui-skills` | `d07392a` | 4 MED | **NOT INSTALLED** — methodology used instead |
| `redesign-skill` | `Leonxlnx/taste-skill` | `e79ca9e` | **0 issues** | **CLEARED** |
| `image-to-code-skill` | `Leonxlnx/taste-skill` | `e79ca9e` | **0 issues** | **CLEARED** |
| `taste-skill` | `Leonxlnx/taste-skill` | `e79ca9e` | 2 HIGH, 4 MED | **REJECTED** |
| `impeccable` | `pbakaus/impeccable` | `f2c7051` | 39 HIGH, 34 MED | **REJECTED for now** — §5.3 |

**None of them is actually installed.** See §8 — writing to `.claude/` is blocked here.

### 5.2 The reasoning, per skill

**`frontend-design` — cleared.** The single HIGH is category *Anti-Refusal* at `SKILL.md:69`,
columns 163–178. Those columns are the literal string `" don't apologize"`, inside the sentence
*"Errors don't apologize, and they are never vague about what happened."* That is UI copy guidance
about error tone, matched by a jailbreak pattern. The skill has **no executable scripts**
(`has_executable_scripts: false`). Confirmed false positive.

**`webapp-testing` — rejected.** Two HIGH *Tool Misuse* plus a MEDIUM *Dangerous Code Execution*,
all at `scripts/with_server.py:69`: `subprocess.Popen(server['cmd'], shell=True)` on a
caller-supplied command string. That is a real pattern, not a false positive. It is also
**redundant**: CROOKS already has an eleven-script Playwright harness that is strictly more
capable, and Phase 6's rule is not to duplicate an adequate installed tool. Per the standing rule
— do not install around a material finding — it is left uninstalled and recorded here.

**`web-interface-guidelines` — cleared, content only; never run `install.sh`.** Two things are
wrong with the installer and both matter:

1. It `curl`s from `refs/heads/main` **unpinned** at install time. What you get is whatever `main`
   says that day — the rug-pull vector, and it defeats pinning entirely.
2. It writes to `$HOME/.claude/commands/` — **global user scope**, not project scope — and probes
   for and writes into six other agent tools besides.

The *content* (`command.md`, `AGENTS.md`) is MIT-licensed static markdown with no executable
content. The correct adoption is to vendor the pinned files from commit `e3d624b` and never
execute the installer.

> Naming: the inbox asked for Vercel **`web-design-guidelines`**. No such repository exists under
> `vercel/` or `vercel-labs/`; the search hits are unrelated low-star lookalikes. The real artifact
> is **`vercel-labs/web-interface-guidelines`** (MIT). The lookalikes were **not** used.

**`create-design-md` — not installed; methodology applied directly.** Its four MEDIUM findings are
`npx @google/design.md` invocations (lint / export / diff). `npx` on an unpinned package fetches
and executes whatever version is current — a genuine rug-pull vector in a skill that would
otherwise run routinely. The methodology itself is sound and was followed by hand to write
`DESIGN.md`, so nothing ever invokes the unpinned package. Its `@google/design.md` frontmatter
schema was **not** adopted, because it cannot be validated offline and CROOKS needs its own
section set.

**`redesign-skill` and `image-to-code-skill` — cleared, 0 issues, no executable scripts.** These
are the inbox's "redesign-existing-projects" and "image-to-code". Per CROOKS precedence,
`redesign-skill` is the relevant one for existing product UI, and `image-to-code-skill` activates
only when a reference image is supplied or explicitly requested.

**`taste-skill` — rejected.** This is the inbox's "design-taste-frontend". Two HIGH and four
MEDIUM, and unlike the `frontend-design` HIGH these are substantive:

- Two HIGH at `SKILL.md:272–329` instruct the agent to emit **remote image URLs**
  (`picsum.photos`, Unsplash, Pexels) into generated markup. CROOKS loads **no** external
  resources — not even a web font (`DESIGN.md` §4) — precisely because the tablet is often on poor
  connectivity. A skill whose default output injects third-party URLs is contrary to the product.
- MEDIUM *Excessive Agency* at `SKILL.md:51`: *"Do not ask the user to edit this file — overrides
  happen conversationally."* A skill instructing the agent **not** to consult the owner conflicts
  directly with the authority order in `DESIGN.md` §0 (owner request is rank 1) and with
  `DEC-017`.

The inbox's own precedence rule already said this skill is not the authority for CROOKS
operational screens. The scan agrees, for independent reasons.

### 5.3 `impeccable` — not installed in this round

The scan completed on a second attempt (the first exceeded a 420 s budget). Result: **73 issues —
39 HIGH, 34 MEDIUM**.

| Category | Count |
|---|---|
| Prompt Injection | 35 |
| Excessive Agency | 15 |
| Server-Side Request Forgery | 12 |
| MCP Rug Pull | 4 |
| Anti-Refusal | 3 |
| Memory Poisoning | 2 |
| Data Exfiltration | 2 |

**The count overstates the risk, and saying so matters.** Sampling the HIGH findings shows the
same class of match as the `frontend-design` false positive — e.g. a HIGH *Prompt Injection* at
`SKILL.src.md:21` whose finding text is *"Load the request's playbook: its Commands-table
reference…"*, which is ordinary instructional prose. A large instructional skill will always
accumulate these.

**What is not a false positive is the executable surface.** `impeccable` ships
`has_executable_scripts: true` and, among others:

- `scripts/live-browser.js` — **547 KB** of bundled JavaScript, carrying all 12 SSRF findings
- `scripts/impeccable` — an executable entry point
- `scripts/modern-screenshot.umd.js`, `scripts/live-browser-*.js`

Half a megabyte of bundled JS cannot be meaningfully reviewed in this round, and the standing rule
is not to install around a material finding. **Not installed.** This is a "needs a dedicated
review", not a permanent verdict — it is the most directly relevant of the candidates for existing
CROOKS product UI, so it is worth the review.

Two further things need a decision regardless of the scan:

- It ships **`PRODUCT.md`** at its repository root. CROOKS must not gain a second product source
  of truth — `PRODUCT_BRAIN.md` and `DECISIONS.md` are canonical (`DEC-016`). If adopted, point it
  at product memory, or add only a minimal pointer.
- It ships **four sub-agents** (`impeccable-finish-reviewer`, `impeccable-manual-edit-applier`,
  `impeccable-documenter`, `impeccable-asset-producer`). `impeccable-manual-edit-applier` **edits
  source**, which needs an explicit decision before it exists in this repo.

---

## 6. Python test quality

The offline suite collects **2814 tests** (`-m "not live"`, 2 deselected). Host: 4 CPUs, 7 GB RAM.

- **pytest-timeout, pytest-cov** — installed, explicit use.
- **pytest-xdist** — installed, **recommended, not yet enabled by default.**

  Measured on this host (4 CPUs, 7 GB, quiet machine, `-p no:cacheprovider`, `-m "not live"`):

  | Run | Wall | Result |
  |---|---|---|
  | serial | 490.3 s | — |
  | serial | 495.7 s | — |
  | serial | 514.4 s | **2806 passed, 8 skipped, 2 deselected** |
  | `-n 4` | 220.4 s | **2806 passed, 8 skipped** |
  | `-n 4` | 224.4 s | **2806 passed, 8 skipped** |

  **2.2× faster — 8.2 min down to 3.7 min — with the identical outcome.** Both parallel runs match
  each other *and* match serial, so there is no evidence of shared-state or ordering dependence at
  `-n 4`. All three adoption criteria (deterministic, no race failures, unchanged semantics) are
  met on this host.

  It is left **off by default** anyway. `make test` is unchanged; use `-n 4` explicitly. Two
  reasons: the evidence is two runs on one host, which is enough to recommend and not enough to
  make it the default for everyone; and the serial ordering is what every previous result in this
  repo was measured under. Flip the default in a separate, deliberate change.
- **Hypothesis** — installed, applied nowhere yet. It belongs on parsers, serialization, the
  proposal/action state machine, and future Event Ledger logic. **Do not rewrite existing tests
  merely to claim Hypothesis usage.**
- **No retry plugin, ever.** A flaky test is never hidden behind a rerun.

---

## 7. Update policy

**Nothing here auto-updates.** To move any pin:

```
upstream update → security scan → diff → test → review → update manifest.json
```

For a third-party skill, "security scan" means the full §5 gate again, including reading the
flagged lines rather than accepting the verdict.

---

## 8. Not done, and why

- **Project-scoped Claude configuration (`CLAUDE.md`, `.claude/rules/`, project skills, hooks) was
  NOT created, and no skill was installed.** Writes to `/opt/crooks-builder/.claude/` are refused
  by the agent's permission layer. The refusal was not worked around. The proposed layout is
  specified in `docs/dev-environment/CLAUDE_PROJECT_LAYOUT.md` so it can be applied in one
  reviewed step.
- **`.gitignore` still ignores `.claude/`.** Adopting the layout requires changing that line to
  `.claude/*` plus explicit negations — git cannot re-include a file inside an excluded
  *directory*, so negations under `.claude/` are dead until the trailing slash goes. Left
  unchanged because the configuration was not installed.
- **The `impeccable` scan did not finish** (§5.3).
- **No system package was installed**; `/usr` is untouched and still read-only.
- **No service was installed, started or changed. Tailscale untouched. Writes still disabled.
  No live Shopify, Gmail or ElevenLabs call was made** — the browser gate runs against the
  fixture world on loopback.
