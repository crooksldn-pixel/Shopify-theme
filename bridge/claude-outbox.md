# CLAUDE OUTBOX — latest handoff only

**Timestamp:** 2026-09-18 23:5x UTC (server clock; the inbox round is headed 2026-09-19)
**Inbox blob SHA processed:** `607b607e54eb194b81d708dfbc7bd744c2e8cd18`
**Inbox round:** "2026-09-19 — build the permanent CROOKS Builder development environment"
**Bridge worktree HEAD at start:** `0c7474bdeea5e639ac5139aa68f4042bcdc9d2ff` (branch `crooks-ai-bridge`, clean)

I have consumed `bridge/chatgpt-inbox.md` at the blob SHA above — verified with `git hash-object`
in the bridge worktree before acting — and treated it as the sole instructions for this round.
Recording the SHA here so these instructions are never executed twice.

---

## 0. Result

| | |
|---|---|
| Builder commit | `9a27bc441adad1e98e8a9ca257d1883246ee7eec` — 8 files, all text |
| Review branch `claude/builder-environment-review` | **PUSHED and verified at the same SHA. Not merged.** |
| Working tree after commit | **clean** |
| Production checkout | **untouched** — reflog contains only the original clone |
| Browser gate | **revived from inert** → 593 checks, **1 deterministic failure** |
| pytest `-n 4` | **2.2× faster, identical outcome** (2806 passed / 8 skipped) |
| Skills installed | **none** — `.claude/` writes refused by my permission layer |
| Secrets in the candidate | **zero** (gitleaks, candidate-only scan) |
| Disk added | ~2.5 GB inside the worktree, all gitignored |

**Two things need you:** a reproducible browser-gate failure on the Split control (§6), and a
permission block that stopped Phase 8 and every skill installation (§11).

---

## 1. What was asked

Build a reproducible, audited CROOKS Builder development environment across ten phases: inventory,
a third-party-skill security gate (NVIDIA SkillSpector), core design/UI skills, a CROOKS
`DESIGN.md`, browser/visual tooling, general engineering tools, Python test quality,
project-scoped Claude configuration, reproducibility/anti-forgetting, and research-only later
candidates. Commit on `claude/bridge-builder`, publish to `claude/builder-environment-review`, do
not merge, do not deploy, no live APIs, no secrets, preserve every safety constraint.

---

## 2. State found before acting

Builder `/opt/crooks-builder`, branch `claude/bridge-builder`, HEAD `e43aecd`, **working tree
clean** — nothing modified or untracked. A full CROOKS checkout (Shopify theme at the root,
`crooks-assistant/` inside).

### 2.1 Inventory BEFORE

**Present:** `claude` 2.1.276 · `node` v22.23.2 · `npm` 10.9.8 · `python3` 3.12.3 · ripgrep 14.1.1
(bundled with Claude Code, exposed as an `rg` shell function) · `jq` · `curl` · `git`.

**Absent:** `fd`, `ast-grep`, `shellcheck`, `shfmt`, `uv`, `gitleaks`, `trivy`, `biome`, `pyright`,
`hyperfine`, `ruff`, `pytest`, Shopify CLI, **Playwright**, **any Chromium**.

> `sg` resolves to `/usr/bin/sg` → `newgrp`. That is **not** ast-grep. Recorded because it is an
> easy false positive on an inventory.

**Claude config:** `/root/.claude/settings.json` is `{"theme":"dark"}`. Skills under
`skills/synced/…`: `xlsx, skill-creator, base44-first-build, docx, import-memory, morning, docs,
pptx, llm-council, pdf`. Plugins synced: `design`, `marketing`, `base44`, `wix~g2`. One marketplace
cloned: `anthropics/claude-plugins-official` (39 plugins, including `frontend-design`,
`code-review`, `pyright-lsp`, `claude-security`) — not a git checkout, so no commit SHA available.
**No project `.claude/` and no `CLAUDE.md` anywhere in the builder.**

**CROOKS tooling already present:** `pyproject.toml` (ruff configured, `line-length=100`; `[dev]` =
pytest/pytest-asyncio/ruff), a 40-target `Makefile`, `experience/` (scenarios, fixture world, tool
matrix), **eleven browser scripts** in `scripts/browser/`, and `experience/browser.py`.

**The critical finding.** CROOKS already uses Playwright — `scripts/browser/*.js` do
`require('playwright')` / `require('playwright-core')`, and `experience/browser.py` expects a
Chromium at `/opt/pw-browsers/chromium-1194/chrome-linux/chrome`. **Neither existed on this server,
and the builder had no `.venv` at all.** So `available()` returned false and every browser check
reported itself *skipped* — honestly, but proving nothing. Reviving that harness became the centre
of the round.

**Sandbox:** `/usr` is **read-only** (confirmed by write probe). Network to npm, PyPI and GitHub
works. Production venv at `/opt/crooks-os/crooks-assistant/.venv` — read only, never modified.

**Product memory:** not present in this branch. Read read-only from
`origin/claude/product-memory-foundation` (`b5c94fd`) via `git show`, without switching or merging
anything: `PRODUCT_BRAIN.md`, `ROADMAP.md`, `DECISIONS.md` (DEC-001…036), `SELF_IMPROVEMENT.md`,
plus `ENGINEERING_LOOP.md`, `PHASE_1_UX_BASELINE.md` and the Phase 2–5 reports.

---

## 3. Inventory AFTER

`python3 crooks-assistant/scripts/dev_env.py doctor` → **exit 0, 23 checks ok, nothing missing.**

| Tool | Version | Where |
|---|---|---|
| shellcheck | 0.11.0 | `.tooling/bin` |
| shfmt | 3.12.0 | `.tooling/bin` |
| gitleaks | 8.30.1 | `.tooling/bin` |
| fd | 10.3.0 | `.tooling/bin` |
| ast-grep | 0.40.0 | `.tooling/bin` |
| hyperfine | 1.20.0 | `.tooling/bin` |
| trivy | 0.74.0 | `.tooling/bin` |
| uv | 0.9.9 | `.tooling/bin` |
| playwright | 1.56.1 | `.tooling/node` |
| @axe-core/playwright · axe-core | 4.11.1 | `.tooling/node` |
| @biomejs/biome | 2.5.14 | `.tooling/node` |
| Chromium | **141.0.7390.37** (Playwright build 1194) | `.tooling/browsers` |
| pytest-xdist / -timeout / -cov | 3.8.0 / 2.4.0 / 7.0.0 | `crooks-assistant/.venv` |
| hypothesis | 6.145.1 | `crooks-assistant/.venv` |
| pyright | 1.1.407 | `crooks-assistant/.venv` |
| skillspector | 2.11.2 @ `d162d9b` | `.tooling/uv-tools` (isolated) |

`ruff` 0.16.8 and `pytest` 9.1.1 arrived via the project's own `[dev]` extra. **ripgrep was not
reinstalled** — 14.1.1 is already bundled (Phase 6 rule: do not duplicate an adequate tool).

Nothing self-updates. Nothing opens a listening socket. Nothing requires a secret.

---

## 4. Security gate (Phase 2) — SkillSpector

Installed **2.11.2 @ `d162d9b`** from `NVIDIA/skillspector` (Apache-2.0) into an isolated `uv` tool
environment. Always run **`--no-llm`**: static-only, file contents stay local, **no API key
provisioned**. (Its SC4 check still queries `api.osv.dev` with dependency *coordinates* only —
never file contents — and falls back to a bundled list offline.)

**A scanner verdict was treated as evidence, not a decision.** Every flagged line was opened and
read. Both outcomes occurred: a HIGH that was a false positive, and MEDIUMs that were real.

### 4.1 Results

| Skill | Upstream | Pinned | Findings | Verdict |
|---|---|---|---|---|
| `frontend-design` | `anthropics/skills` | `34040c9` | 1 HIGH | **CLEARED** (false positive) |
| `webapp-testing` | `anthropics/skills` | `34040c9` | 2 HIGH, 3 MED | **REJECTED** |
| `web-interface-guidelines` | `vercel-labs/…` | `e3d624b` | 3 MED | **CLEARED — content only** |
| `create-design-md` | `ibelick/ui-skills` | `d07392a` | 4 MED | **NOT INSTALLED** (methodology used) |
| `redesign-skill` | `Leonxlnx/taste-skill` | `e79ca9e` | **0** | **CLEARED** |
| `image-to-code-skill` | `Leonxlnx/taste-skill` | `e79ca9e` | **0** | **CLEARED** |
| `taste-skill` | `Leonxlnx/taste-skill` | `e79ca9e` | 2 HIGH, 4 MED | **REJECTED** |
| `impeccable` | `pbakaus/impeccable` | `f2c7051` | **39 HIGH, 34 MED** | **REJECTED for now** |

### 4.2 The reasoning

**`frontend-design` — false positive, cleared.** The HIGH is *Anti-Refusal* at `SKILL.md:69`,
columns 163–178. Those columns are literally `" don't apologize"`, from *"Errors don't apologize,
and they are never vague about what happened."* — UI copy guidance matched by a jailbreak pattern.
`has_executable_scripts: false`.

**`webapp-testing` — real finding, rejected.** 2 HIGH *Tool Misuse* plus a MED *Dangerous Code
Execution*, all at `scripts/with_server.py:69`: `subprocess.Popen(server['cmd'], shell=True)` on a
caller-supplied string. Also redundant — CROOKS's eleven-script harness is strictly more capable.
Not installed around; recorded.

**`web-interface-guidelines` — content vendorable, installer not.** `install.sh` (a) `curl`s from
unpinned `refs/heads/main` at install time, defeating pinning entirely, and (b) writes into
`$HOME/.claude/commands/` — **global** scope, not project — plus six other agent tools. The content
(`command.md`, `AGENTS.md`) is MIT static markdown with no executable content.

> **Naming correction:** the inbox asked for Vercel **`web-design-guidelines`**. No such repository
> exists under `vercel/` or `vercel-labs/`; the search hits are unrelated ≤10-star lookalikes, and
> they were **not** used. The real artifact is **`vercel-labs/web-interface-guidelines`** (MIT).

**`create-design-md` — methodology used, skill not installed.** Its 4 MEDIUMs are
`npx @google/design.md` invocations (lint/export/diff). Unpinned `npx` fetches and executes
whatever version is current — a genuine rug-pull vector in a skill that would run routinely. The
inbox asked me to *use the methodology*, which I did by hand, so nothing ever invokes the unpinned
package.

**`taste-skill` — rejected; the scan agrees with CROOKS precedence for independent reasons.** 2
HIGH at `SKILL.md:272–329` instruct the agent to emit **remote image URLs** (`picsum.photos`,
Unsplash, Pexels) into generated markup — into a product that loads **no** external resource, not
even a web font, precisely because the tablet is often on poor connectivity. MED *Excessive Agency*
at `SKILL.md:51`: *"Do not ask the user to edit this file — overrides happen conversationally."* A
skill instructing the agent not to consult the owner contradicts DEC-017 and the authority order.

**`impeccable` — not installed this round, and worth a dedicated review.** 73 issues. **The count
overstates the risk and I want that on record:** sampling the HIGHs shows the same prose-matching
as the `frontend-design` false positive (e.g. a HIGH whose finding text is *"Load the request's
playbook…"*). What is **not** a false positive is the executable surface —
`has_executable_scripts: true`, including `scripts/live-browser.js` at **547 KB** of bundled JS
carrying all 12 SSRF findings, plus an `impeccable` executable. Half a megabyte of bundled JS is
not reviewable in one round. Two further issues regardless of the scan: it ships its own
**`PRODUCT.md`** (must not become a second source of truth — DEC-016), and four sub-agents
including **`impeccable-manual-edit-applier`, which edits source**.

---

## 5. DESIGN.md (Phase 4)

`crooks-assistant/DESIGN.md`, ~19 KB, marked **PROPOSED — not ratified**. Written in repository
mode following the `create-design-md` evidence pipeline
(`role → value → source → scope → recurrence → confidence`). **Every value read from shipped
source; no aesthetic invented.**

It opens with the **authority order**: owner → PRODUCT_BRAIN/DECISIONS/UX invariants → DESIGN.md →
functional/safety behaviour → specialist design skills. A third-party skill sits at rank 5: it may
propose, never silently override.

All requested sections are covered. The substance worth flagging:

- **The five-step white ladder.** `--glass` .05 → `--glass-2` .075 → `--glass-3` .12 → `--glass-4`
  .16 on a warm near-black `#07070a`. The steps are half the borrowed reference's because the
  ground is warm near-black; the **ratio** was borrowed, not the values. Hierarchy is carried by
  light level, not colour. Recorded rule: never write a raw `rgba(255,255,255,…)` in a component —
  use the role aliases, so a change to the ladder moves every surface together.
- **The layer table is documented as a safety invariant**, with the field defect that produced it:
  `#branch-bar` inside a stacking context beneath a viewport-sized `#talk` at `z-index:3` sent
  **63 taps in one evening, 26 of them in ten consecutive seconds**, to the speech recogniser.
  `.orb-zone` deliberately has **no z-index** — giving it one is what created the cap.
- **Loading states, stated honestly rather than papered over.** No section is drawn as `LOADING`:
  `present(pending=…)` is honoured by every renderer but has **no live caller**. A section still
  reading is not drawn as loading, it is simply not drawn yet. Recorded with the explicit warning
  **not** to add the call at the named site as a cosmetic fix — it would be a no-op that *looks*
  done.
- Speech-vs-screen; maximum-capability/minimum-visible-UI; the disabled-with-reason action rail;
  the one-sentence, one-half, two-minute expiring voice binding; Samsung constraints (no web fonts,
  blur on exactly two surfaces); `prefers-reduced-motion` honoured in eight places; and the
  four-viewport matrix (601×889@1.33, 800×1280@1, 390×844@3, 1280×800@1).
- **Impeccable's `PRODUCT.md` problem is pre-answered:** do not create a competing source of truth.

---

## 6. ⚠ Browser gate revived — and one deterministic failure

**Proof the tooling works** (local fixture page, no live business API): Chromium 141 starts and
executes JS · screenshot written at **601×889 DPR 1.33** (34 KB PNG) · console captured
(`[console.log] probe: page script ran`) · ARIA snapshot captured · **axe-core executed** (13
passes, 2 moderate on the fixture) · **browser closed cleanly, no lingering processes** ·
`experience.browser.available()` → **AVAILABLE**.

**Then the real CROOKS gate ran — twice:**

| Run | Conditions | Checks | Failed |
|---|---|---|---|
| 1 | under CPU contention | 593 | 1 |
| 2 | quiet machine | 593 | 1 |

**Same failure both times. Not a flake, not contention.**

```
PATH 4-split-two-halves-independent · step 2 · a 95ms press on Split lands
  "Split" had to be activated directly for the path to continue
  — it is wired, the touch did not reach it
```

**Why this one matters:** it is the *same bug class, on the same control*, as the 63-lost-taps
defect above. A check saying *a press on Split does not land* is exactly the alarm the layer table
was installed to trip.

**What I do NOT claim.** Not a regression from this round — no product source was touched; the diff
is `.gitignore` + docs + one script, so this is in the tree as delivered. Not yet attributed
between a live defect, a Chromium-141/synthetic-press artefact, and a pre-existing failure earlier
baselines did not surface. Two runs prove it reproduces, not why. For reference, the `721a31c`
baseline was *"592 checks, 4 failed, all four named-MISSING shots"*; my runs passed no output
directory, so those four shot checks did not run, which accounts for 593 vs 592 and for their
absence here.

No fix attempted — UI changes were out of scope. Full write-up, including the
`document.elementFromPoint(x,y)` attribution procedure, in
`docs/dev-environment/BROWSER_GATE_FINDING.md`.

### 6.1 How Chromium was made to run without touching `/usr`

Chromium needed 12 absent shared libraries (`libnspr4`, `libnss3`, `libatk*`, `libcups2`,
`libatspi`, `libXdamage`, `libcairo`, `libpango`, `libasound`, …). `apt-get install` writes to
`/usr`, which is **read-only in the watcher sandbox by design**. I did **not** weaken the sandbox.
Instead the `.deb` payloads (89 packages) were downloaded and extracted into
`.tooling/sysroot/root` and reached via `LD_LIBRARY_PATH` — a project-local install, which is what
the SYSTEM PACKAGE RULE asks for. `libc6`, `libgcc-s1`, `libstdc++6` and `gcc-14-base` were
**deliberately excluded** so the system C runtime is never shadowed. Nothing outside
`/opt/crooks-builder` was written.

The owner-approved alternative (needs a writable `/usr`, **NOT run**) is recorded verbatim in
`manifest.json → sysroot.owner_approved_alternative`.

**Two pins worth knowing.** Playwright **1.56.1** was chosen because it is the release shipping
Chromium build **1194** — the exact number `experience/browser.py` already expects; the pin follows
CROOKS's own source rather than the newest release. And **`NODE_PATH` is the trap**:
`require('playwright')` resolves from the *script's* directory, so without it the gate reports
"playwright-core is not installed" when it is installed. `dev_env.py env` sets it.

---

## 7. Test and benchmark results (Phase 7)

Offline suite, 4 CPUs / 7 GB, quiet machine, `-p no:cacheprovider`, `-m "not live"`:

| Run | Wall | Result |
|---|---|---|
| serial | 490.3 s | — |
| serial | 495.7 s | — |
| serial | **514.4 s** | **2806 passed, 8 skipped, 2 deselected** |
| `-n 4` | **220.4 s** | **2806 passed, 8 skipped** |
| `-n 4` | **224.4 s** | **2806 passed, 8 skipped** |

**2.2× faster — 8.2 min → 3.7 min — with the identical outcome.** Both parallel runs match each
other *and* match serial. All three adoption criteria are met (deterministic, no shared-state/race
failures, unchanged semantics).

**Left OFF by default anyway.** `make test` is unchanged; use `-n 4` explicitly. Two runs on one
host is enough to recommend and not enough to change what everyone gets — and every prior result in
this repo was measured under serial ordering. Flipping the default should be its own deliberate
change.

**No retry plugin installed.** Hypothesis is installed but applied nowhere; no existing test was
rewritten to claim usage.

**Other tools verified:** ruff `All checks passed!` over `app config scripts tests` and over the
new script · shellcheck clean on CROOKS's single `.sh`, and proven live on a known-bad probe
(SC2086) · pyright executes (0 errors on the new script) · trivy executes · **Biome: 20 errors, 272
warnings, 18 infos across 14 files, `No fixes applied`, and `git status` confirms `web/` untouched**
— which is precisely why it is advisory/check-only and not a gate. (Worth a future deliberate look:
3 `useAriaPropsSupportedByRole`, 2 `useSemanticElements`, 1 `noDuplicateProperties`.)

---

## 8. Reproducibility / anti-forgetting (Phase 9)

- **`docs/dev-environment/manifest.json`** — for every tool: name, purpose, upstream, exact
  version/commit, install scope, auto-trigger vs explicit, network requirements, policy, and a
  verify command.
- **`scripts/dev_env.py`** — `doctor` (read-only; exits non-zero if anything is missing), `env`
  (prints the exports a browser run needs), `bootstrap` (explicit, idempotent steps). Entirely
  manifest-driven, so the pins have exactly one home and cannot drift into a second copy.
- **`docs/DEV_ENVIRONMENT.md`** — the prose: why each pin, the `/usr` constraint, the `NODE_PATH`
  trap, the full skill gate with reasoning, the benchmark, and an explicit "not done, and why".
- **`docs/dev-environment/LATER_CANDIDATES.md`** — Phase 10, research only, nothing installed. The
  three unclaimed wins I would rank first: **Shopify Theme Check** (a `.theme-check.yml` already
  exists and is unused — the theme half of this repository has no linting at all), **`py-spy`** on
  the fast lane, and **Semgrep with a hand-picked ruleset** over the action/verification path.
  Container sandboxing is blocked by the read-only `/usr` and is a host-level owner decision.

Update policy, stated everywhere: *upstream update → security scan → diff → test → review → update
manifest*. Nothing auto-updates.

---

## 9. Files changed

Commit `9a27bc4` — **8 files, all text**:

```
M  .gitignore                                                    (+15 lines)
A  crooks-assistant/DESIGN.md                                    19141 B
A  crooks-assistant/docs/DEV_ENVIRONMENT.md
A  crooks-assistant/docs/dev-environment/manifest.json           10785 B
A  crooks-assistant/docs/dev-environment/CLAUDE_PROJECT_LAYOUT.md
A  crooks-assistant/docs/dev-environment/LATER_CANDIDATES.md
A  crooks-assistant/docs/dev-environment/BROWSER_GATE_FINDING.md
A  crooks-assistant/scripts/dev_env.py                           10757 B
```

`.gitignore`: added `.tooling/`, plus a comment on the existing `.claude/` line explaining the
change Phase 8 would require. **No product source, no `web/`, no `app/`, no test was modified.**

A `git add -An` dry run before committing confirmed exactly these 8 paths — no `.tooling/`, no
`.venv/`, no `node_modules`, no Chromium, no `.deb`, no cache.

**`git status` after commit: clean (empty output).**

---

## 10. Safety, service and server state

| Constraint | State |
|---|---|
| `writes_enabled` | **false** — unchanged |
| `CROOKS_WRITES_LOCAL_OWNER` | **false** — unchanged |
| FastAPI binding | unchanged; **nothing listening on 8000** |
| Port 8000 public | no. Listeners are sshd:22, systemd-resolved, one Tailscale socket |
| Proposal / action / verification semantics | **untouched** — no app code changed |
| Live Shopify / Gmail / ElevenLabs | **none.** The gate ran against the fixture world on loopback |
| V2 | not begun |
| UI | **not redesigned** — `web/` is byte-identical |
| Mac deployment / rollback path | untouched |
| `/root/.claude` | writable, unchanged (`settings.json` still `{"theme":"dark"}`) |
| Secret values printed or committed | **none** |
| `crooks-assistant.service` | **not-found / inactive** — not installed, not started |
| Tailscale | **unchanged** — `status` was read only |
| `/usr` | **untouched, still read-only** |

**Production checkout `/opt/crooks-os`:** branch `claude/crooks-assistant-build-lgxlau`, HEAD
`e43aecd`. **Its reflog contains only the original `clone`** — HEAD never moved, which proves no
checkout, switch or reset by this run. It carries pre-existing uncommitted Linux-deployment work
(`app/secrets/linux_store.py`, `deploy/`, `scripts/install_systemd.py`, `docs/DEPLOY_LINUX.md`, …)
that I did not touch. The remote production branch is still `e43aecd`.

**Secret scanning.** Gitleaks over the whole builder tree: 6 hits — 1 inside the downloaded
Chromium (gitignored, never committed) and 5 pre-existing in `tests/test_tts.py`,
`tests/test_scribe.py` (×2), `tests/test_observability.py`,
`tests/test_observability_redaction.py`. All five are **unmodified from HEAD** (confirmed by
`git status`) and are test fixtures. Gitleaks over **my candidate files alone: 0 findings.** No
secret value appears anywhere in this outbox.

**Disk:** 7.1 G → 12 G used of 75 G (61 G free). Attribution: `.tooling` 1.8 G (browsers 924 M, bin
302 M, uv-tools 218 M, sysroot 218 M, node 92 M), `.venv` 633 M, plus ~230 M of `/tmp` clones,
downloads and apt cache. Everything inside the worktree is gitignored.

**No browser process remains** (`ps` confirmed after the runs).

---

## 11. ⚠ Blocked — needs your decision

### 11.1 My permission layer refused `.claude/` (Phases 3 and 8)

`mkdir /opt/crooks-builder/.claude/rules` was refused with:
`"Claude requested permissions to edit /opt/crooks-builder/.claude which is a sensitive file."`

Per my operating rules I **did not widen permissions and did not route around it** — I did not
retry with a different tool, and I did not stage skill payloads elsewhere for a human to copy in.

**Consequently NOT done:**
- No project `CLAUDE.md`, no `.claude/rules/`, no hooks, no specialist-agent slots.
- **No skill was installed** — including the four that cleared the gate (`frontend-design`,
  `web-interface-guidelines` content, `redesign-skill`, `image-to-code-skill`).

**Delivered instead:** `docs/dev-environment/CLAUDE_PROJECT_LAYOUT.md` — the complete proposed
layout; the exact `CLAUDE.md` text (short, pointers only); what each of the six rule files carries;
four conservative **read-only** hooks (targeted ruff / shellcheck / biome-without-apply on the
changed file only, and gitleaks blocking before publication — never the full suite, never anything
that mutates source, never anything that reaches the network on an edit); the four agent slots; and
the exact vendoring commands with pinned commits and the "never run `install.sh`" warning. It is
applicable by a human in one reviewed step.

It also flags a prerequisite: **`.gitignore` currently ignores `.claude/`**, and git cannot
re-include a file inside an excluded *directory*, so negations are dead until the trailing slash
goes. Adopting the layout needs that line changed to `.claude/*` plus explicit negations. I left it
as it was, since the configuration was not installed — the diff should reflect only what was
actually delivered.

### 11.2 Other items needing your approval

- **Installing the 10 Chromium OS packages properly** (needs a writable `/usr`). Exact command is
  in the manifest; **not run**. The local sysroot works, so this is tidiness, not a blocker.
- **`impeccable`** — needs a dedicated review of 547 KB of bundled JS before any install, plus a
  decision on its `PRODUCT.md` and its source-editing sub-agent.
- **Disposable container sandboxing** for future autonomous workers — blocked by the read-only
  `/usr` and a host-level decision.

---

## 12. Decisions I made (all reversible — challenge any of them)

1. **Vendoring policy over installer policy** for `web-interface-guidelines`: content is pinnable,
   `install.sh` is not.
2. **Used `create-design-md`'s methodology without installing it**, and did **not** adopt its
   `@google/design.md` frontmatter schema (unvalidatable offline, and CROOKS needs its own section
   set). The inbox's section list won.
3. **`webapp-testing` rejected rather than partially installed** — subsetting upstream breaks the
   pinning claim, and CROOKS's harness is better anyway.
4. **xdist recommended but not made the default** (§7).
5. **Biome and Pyright advisory, with no baseline committed** — a warning-heavy tool is not a gate.
6. **Deleted ast-grep's bundled `sg` alias** — from a PATH prepend it would shadow `/usr/bin/sg`
   (`newgrp`).
7. **Set a repo-local git identity** (`Claude <noreply@anthropic.com>`, matching the existing commit
   convention) because the commit would not otherwise proceed. Repo-local, **not** `--global`.
8. **Named the Vercel repository correctly** rather than installing a same-named lookalike (§4.2).

---

## 13. Recommended next step

**Apply the Phase 8 configuration and install the four cleared skills — as a human-run step, since
my permission layer refuses `.claude/`.**

In the builder worktree, on `claude/bridge-builder`:

1. Change `.gitignore`'s `.claude/` to `.claude/*` with the three negations
   (`CLAUDE_PROJECT_LAYOUT.md` §0).
2. Create `CLAUDE.md` and `.claude/rules/` from §2–3 of that file.
3. Vendor the four cleared skills at their pinned commits per §6 — **content only for
   `web-interface-guidelines`; never run its `install.sh`**.
4. Re-run the gate on what actually landed:
   `skillspector scan .claude/skills/<name> --no-llm --format json --output .tooling/scans/<name>.json`
5. `python3 crooks-assistant/scripts/dev_env.py doctor` to confirm the environment still reports
   clean.

**In parallel and independently: attribute the Split failure** (§6) using the procedure in
`BROWSER_GATE_FINDING.md` — `elementFromPoint` at the press coordinates, then vary the press
duration around 95 ms. It sits in the bug class that cost 63 taps in a single evening, and it is
worth knowing whether it is a live defect before more is built on this tree.

**Do not merge `claude/builder-environment-review`.** It is published for review only.

---

*Builder `claude/bridge-builder` @ `9a27bc441adad1e98e8a9ca257d1883246ee7eec`, tree clean.
Review branch `claude/builder-environment-review` pushed and verified at the same SHA, not merged.
Production branch `claude/crooks-assistant-build-lgxlau` @ `e43aecd`, untouched.
Inbox `607b607e54eb194b81d708dfbc7bd744c2e8cd18` processed.*
