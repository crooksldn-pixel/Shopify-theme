# CLAUDE OUTBOX — latest handoff only

## 2026-09-19T12:12:34Z — ENV-REPRO-001: Builder Environment acceptance repair + contract trial

**Inbox consumed:** `bridge/chatgpt-inbox.md`, blob `73cb6b062e62297e3ccbcf67b1e432303574f3dc`
("2026-09-19 — Builder Environment acceptance repair + contract trial"). I have consumed it and
treated it as the sole instructions for this round. The SHA is recorded here so the same
instructions are never executed twice.

**Bridge worktree at start:** branch `crooks-ai-bridge`, HEAD
`8416f138a9a6b63124c11eea9e7c6b47e5b05f31`, clean.

**Candidate:** `326c150b778afdc2b5881b2f7ac97e140e476eab`
**Base:** `9a27bc441adad1e98e8a9ca257d1883246ee7eec` (the rejected candidate, unmodified)
**Review branch:** `claude/builder-environment-repair-review` — **PUBLISHED**, read back from the
remote as `326c150b778afdc2b5881b2f7ac97e140e476eab`. Not merged anywhere.

**I do not claim acceptance.** One finding is repaired only in part and the remainder is blocked on
an owner decision (§6.1). This worker implemented the repair and therefore does not certify it.

---

## 1. What was asked

Repair the four independently reproduced acceptance defects in Builder Environment candidate
`9a27bc4` (BE-01 to BE-04); add a regression test for each that fails against the rejected
behaviour; prove fresh-checkout reconstruction from repository-controlled inputs; prove doctor's
positive and negative cases; prove adversarial shell/path safety; run the relevant gates and read
their actual summaries; inspect the complete diff and secret-scan it; require a clean working tree;
commit and publish the exact candidate to `claude/builder-environment-repair-review` without
merging. Separately: run this as the first manual/simulated Dev Team contract trial and record
contract gaps.

---

## 2. Builder state found on arrival (not where the last run left it)

| | |
|---|---|
| Worktree | `/opt/crooks-builder` |
| Branch on arrival | `claude/mobile-experience-v1` — **not** `claude/bridge-builder` |
| HEAD on arrival | `564ef3430d58b34de582f5548d7fe201c4cfe04b` |
| Working tree on arrival | clean, no untracked files |
| Stale local branch | `claude/bridge-builder` @ `9a27bc4`, tracking `origin/claude/bridge-builder`, which **no longer exists on the remote**. Left alone. |

Mobile Experience V1 is present and published (`claude/mobile-experience-v1-review` @ `564ef34`).
It was not rebuilt, modified, merged or deployed.

`1a0741a` was not present locally and was fetched by explicit ref; the local
`origin/claude/product-memory-foundation` tracking ref was stale at `b5c94fd`. Canonical product
memory (`CURRENT_TRUTH`, `BUILDER_ENVIRONMENT_REVIEW`, `DEV_TEAM_V1_PILOT`, `ROADMAP`, `README`,
`ENGINEERING_ORCHESTRATOR_V1`) was read at `1a0741a`, the current remote head of that branch.

**Base choice.** The repair branch is based on `9a27bc4` — the base the task contract names — not
on `564ef34`. The mobile candidate touches neither `scripts/dev_env.py` nor `docs/dev-environment/`
(verified: the diff is empty for those paths), so basing on it would have added 46 unrelated files
to this candidate's diff and entangled two independent reviews.

---

## 3. What was found — all four defects reproduced BEFORE any edit

Against a clean `git archive` of `9a27bc4`. Offline; no network, no missing tool required.

### BE-01 — bootstrap crashes on the committed manifest — CONFIRMED
`python3 scripts/dev_env.py bootstrap` printed 18 lines, then:

```
File ".../scripts/dev_env.py", line 225, in cmd_bootstrap
  print(f"#    {name} {spec['version']}  {spec['upstream']}")
TypeError: string indices must be integers, not 'str'          (exit 1)
```

`binaries` carries a string-valued `$comment`. `cmd_doctor` skipped `$`-prefixed keys;
`cmd_bootstrap` did not.

### BE-02 — doctor returns success for wrong versions and failed tools — CONFIRMED, and worse than reported
Fixture with every tool present and every tool wrong (binaries reporting `0.0.0`, node package
`0.0.0`, pip `0.0.0`, Chromium `0.0.0.0`, uv-tool probe exiting 3):

```
  ok    shellcheck    want 0.11.0 · 0.0.0
  ok    gitleaks      want 8.30.1 · 0.0.0
  ok    chromium      Chromium 0.0.0.0
  warn  playwright    0.0.0 (want 1.56.1)
  warn  pytest-xdist  0.0.0 (want 3.8.0)
  warn  skillspector  want 2.11.2 @ d162d9b343e5
  all present — ...                                            (exit 0)
```

**Correction to the review's BE-02 note:** binaries produced **`ok`**, not `warn`. The pin was
*displayed beside* the tool's output and never compared with it, so any exit-0 `--version` passed.
Visible on the real builder too: `shellcheck --version` puts the number on line two and `_run` kept
only line one, so `doctor` was comparing nothing at all for that tool.

### BE-03 — generated shell exports execute what is in the checkout path — CONFIRMED
Checkout at `/tmp/crooks-$(printf CROOKS_ENV_PROBE)`, `env` output evaluated as documented:

```
NODE_PATH=/tmp/crooks-CROOKS_ENV_PROBE/.tooling/node/node_modules
```

Only the fixed `printf` probe ever ran. No secret, no external command, no exploitation claim.

### BE-04 — a fresh checkout cannot reconstruct the environment — CONFIRMED
In a fresh checkout of `9a27bc4`: `.tooling/` absent (gitignored); `.tooling/node/package.json`
absent and committed nowhere (`git ls-tree -r 9a27bc4 | grep -c '^\.tooling'` → `0`); no lock or
checksum file of any kind committed; bootstrap step 1's `cd .tooling/node` fails immediately.

---

## 4. What was changed

10 files, **+1741 / −115**, entirely inside `scripts/dev_env.py`, its test, and
`docs/dev-environment/`. No application, UI, action, proposal or configuration file is touched.

| File | | |
|---|---|---|
| `crooks-assistant/scripts/dev_env.py` | M | +517/−115 |
| `crooks-assistant/tests/test_dev_env.py` | **A** | 525 |
| `crooks-assistant/docs/DEV_ENVIRONMENT.md` | M | +135 |
| `crooks-assistant/docs/dev-environment/manifest.json` | M | +19 |
| `crooks-assistant/docs/dev-environment/node-package.json` | **A** | 11 |
| `crooks-assistant/docs/dev-environment/node-package-lock.json` | **A** | 248 |
| `crooks-assistant/docs/dev-environment/sysroot-packages.txt` | **A** | 102 |
| `crooks-assistant/docs/dev-environment/sysroot-packages.sha256` | **A** | 89 |
| `crooks-assistant/docs/dev-environment/binaries.sha256` | **A** | 22 |
| `crooks-assistant/docs/dev-environment/CONTRACT_TRIAL_ENV_REPRO_001.md` | **A** | 188 |

### BE-01 — root cause and exact fix
**Cause:** two callers each decided separately what counted as a tool; one filtered manifest prose,
the other did not.
**Fix:** one `entries(section, *, required, where)`, used by `doctor` and by the plan generator
alike. It filters `$`-prefixed keys and requires every survivor to be an object carrying the fields
its section needs. A malformed entry raises `ManifestError` naming the key
(`binaries.gitleaks is a str, expected an object`), which `main()` reports as a message, not a
traceback. No empty manifest and no altered fixture: the fix is proved against the real committed
file.

### BE-02 — root cause and exact fix
**Cause:** only `MISSING` incremented the failure count; mismatches and failed probes were `warn`
and `warn` did not count; binary versions were never compared at all.
**Fix:** three states — `ok` / `FAIL` / `advisory`.
- Each tool runs **its own `verify` command from the manifest**, built with `shlex.split` and
  argv[0] rebound to the pinned executable. Never a shell: manifest data must not become a command
  line, which is BE-03 in another costume.
- **All** output is read, not the first line, and the pinned version must appear in it. A version
  token needs ≥2 dot-separated numbers, so `shellcheck`'s "license: GNU GPL, version 3" cannot
  satisfy a pin.
- Missing, unrunnable and mismatched are all `FAIL`. Chromium is compared against
  `browsers.chromium.chromium_version`, the venv against `python.interpreter`, node and pip
  packages against their pins.
- **Integrity:** the nine pinned binaries are checked against committed sha256 digests. A tool that
  reports the right version and is not the right artifact is a `FAIL`.
- **Timeouts** added to the two bare `subprocess.run` calls (`ldd`, the browser-gate probe) that
  had none.
- `advisory` is one line, prints its own reason, and does not touch the exit code. There is exactly
  one (§6.2). Biome/Pyright findings *over product source* remain advisory by policy — `doctor`
  does not run them and never did, and that separation is now written down rather than assumed.

### BE-03 — root cause and exact fix
**Cause:** `f"export {k}={v!r}".replace("'", '"')` — Python `repr` followed by quote replacement
produces a **double**-quoted shell word, and double quotes do not suppress `$(…)`, backticks or
`$VAR`.
**Fix:** `shlex.quote`. Single quotes suppress everything, and an embedded single quote is escaped
rather than ending the string. `plan` quotes its emitted paths the same way. `PATH` is in the
contract and is covered by the round-trip test.

### BE-04 — root cause and exact fix, including what is **not** fixed
1. **Honest interface — FIXED.** `bootstrap` was documented as "install whatever doctor says is
   missing" and as idempotent; it printed instructions, so its exit code meant only that text had
   been printed. Renamed `plan`. `bootstrap` exits **2** with an explanation rather than remaining a
   silent alias.
2. **Committed inputs — FIXED.** Step 1 read `.tooling/node/package.json`, gitignored and committed
   nowhere. `node-package.json` and `node-package-lock.json` are now committed under
   `docs/dev-environment/`; `plan` copies them into place *before* npm runs; the step is `npm ci`,
   so the committed lock is what is installed. `doctor` cross-checks manifest ↔ package.json ↔ lock
   (including that every pinned dependency carries an integrity hash) so the three cannot drift.
3. **Root-anchored steps — FIXED.** Bare `cd`s that later commands inherited are gone; a `cd`
   appears only inside a subshell closing on the same line, and a regression test asserts it.
4. **Exact artifacts and integrity — FIXED.** `sysroot-packages.txt` pins all **89** `.deb`s as
   `name=version` (epochs decoded from the `%3a` filename form), replacing a recursive
   `apt-cache depends` resolution that returned whatever the distribution offered on the day it ran.
   `sysroot-packages.sha256` and `binaries.sha256` carry a digest each.
   **These digests are OBSERVED, not upstream-attested** — read off the artifacts installed on this
   builder, and the files holding them say so in their own headers. What they pin is the exact bytes
   this environment was proved against.
5. **Full network reconstruction — NOT FIXED. BLOCKED.** See §6.1. `plan` prints the blocker in its
   own output, where it is read, not only in a document.

---

## 5. Evidence — every item below was produced at candidate `326c150`

### 5.1 Regression tests — 16, and 16/16 fail against `9a27bc4`

Method: a detached worktree at `9a27bc4` with the new test file copied in as the **only** change
(`git status` showed exactly one untracked file), same interpreter. Worktree removed afterwards;
`git worktree list` is back to a single entry.

| # | Test | BE | vs `9a27bc4` | vs `326c150` |
|---|---|---|---|---|
| 1 | `test_be01_plan_survives_the_repositorys_own_committed_manifest` | 01 | FAIL — `TypeError: string indices must be integers, not 'str'` | pass |
| 2 | `test_be01_prose_is_filtered_and_a_malformed_tool_is_named` | 01 | FAIL | pass |
| 3 | `test_be01_a_broken_manifest_is_a_message_not_a_traceback` | 01 | FAIL | pass |
| 4 | `test_be02_doctor_fails_closed_when_tools_are_present_but_wrong` | 02 | FAIL — `assert 0 == 1` (the false green itself) | pass |
| 5 | `test_be02_doctor_passes_the_same_fixture_when_everything_matches` | 02 | FAIL | pass |
| 6 | `test_be02_advisory_findings_are_named_and_never_decide_the_exit_code` | 02 | FAIL | pass |
| 7 | `test_be02_a_tampered_binary_fails_even_at_the_right_version` | 02 | FAIL | pass |
| 8 | `test_be03_a_command_substitution_in_the_checkout_path_is_not_executed` | 03 | FAIL — substitution executed | pass |
| 9 | `test_be03_every_shell_metacharacter_round_trips_including_path` | 03 | FAIL | pass |
| 10 | `test_be04_every_input_the_plan_reads_is_committed` | 04 | FAIL — "the npm project the plan installs from is not committed anywhere" | pass |
| 11 | `test_be04_the_node_install_builds_its_inputs_from_committed_files` | 04 | FAIL | pass |
| 12 | `test_be04_no_step_leaves_the_repository_root_behind_it` | 04 | FAIL | pass |
| 13 | `test_be04_the_plan_is_read_only_and_repeats_identically` | 04 | FAIL | pass |
| 14 | `test_be04_the_plan_says_plainly_what_it_cannot_do` | 04 | FAIL | pass |
| 15 | `test_be04_bootstrap_is_gone_and_refuses_rather_than_pretending` | 04 | FAIL | pass |
| 16 | `test_be04_the_committed_reconstruction_inputs_are_the_real_ones` | 04 | FAIL | pass |

Tests 1 and 10 were deliberately strengthened after a first pass: they originally failed on a
missing attribute, which proves nothing about the defect. They now exercise whichever command name
the candidate exposes, so against `9a27bc4` they fail with the original `TypeError` and the
original missing input respectively.

The tests are offline: no network, no real tool, no real browser. The fixtures are shell scripts
that answer `--version`, because what is under test is what the script *decides* about a tool's
answer, not whether any tool works.

### 5.2 Full gate summaries — read, not inferred from exit codes

| Gate | Command | Summary |
|---|---|---|
| Unit/integration | `pytest -m "not live" -p no:cacheprovider` | **`2822 passed, 8 skipped, 2 deselected in 500.17s (0:08:20)`**, exit 0 |
| Lint | `make lint` → `ruff check app config scripts tests` (ruff 0.16.8) | **`All checks passed!`**, exit 0 |
| Lint (whole tree) | `ruff check .` | **`All checks passed!`**, exit 0 |
| Regression subset | `pytest tests/test_dev_env.py` | **`16 passed in 1.24s`** |

**2822** is the documented **2806** baseline plus exactly the 16 new tests; skips unchanged at 8.
Counts are not substituted for the Linux candidate's separate 2886 baseline.

This suite was run **twice**. The first run (`2822 passed, 8 skipped`) described a tree that two
later edits invalidated, so it was discarded and re-run against the committed candidate. The number
above is the second run, on `326c150`, with a clean tree before and after.

**Non-failing noise, reported rather than hidden:** the log ends with two
`RuntimeError: Event loop is closed` tracebacks from `asyncio/base_events.py` at lines 55–70 —
**after** the summary at line 41, i.e. interpreter-shutdown noise, not test failures; exit code 0.
Nothing in this candidate touches asyncio. Not investigated; outside the four defects.

Not run and not claimed: the browser gate (needs the env export; not required by this task),
`pyright`/`biome` (advisory, no baseline), `shellcheck`/`shfmt` (this candidate changes no shell),
`trivy`, SkillSpector (no skill involved).

### 5.3 Fresh-checkout reconstruction proof — exact commands and results

Tree: `git archive 326c150 | tar -x -C /tmp/fresh-326c150`. **No `.tooling/`, no `.venv/`.**

```
$ ls -d /tmp/fresh-326c150/.tooling                   →  ABSENT
$ ls -d /tmp/fresh-326c150/crooks-assistant/.venv     →  ABSENT

$ cd /tmp/fresh-326c150/crooks-assistant
$ python3 scripts/dev_env.py plan                     →  exit 0
      # Every input the plan reads is committed and present in this checkout.
      # BLOCKED: steps 1-3 and 6 fetch from the network ... See docs/DEV_ENVIRONMENT.md section 9.

  every input the plan reads, enumerated:
      OK  crooks-assistant/docs/dev-environment/manifest.json
      OK  crooks-assistant/docs/dev-environment/node-package.json
      OK  crooks-assistant/docs/dev-environment/node-package-lock.json
      OK  crooks-assistant/docs/dev-environment/sysroot-packages.txt
      OK  crooks-assistant/docs/dev-environment/sysroot-packages.sha256
      OK  crooks-assistant/docs/dev-environment/binaries.sha256
      OK  crooks-assistant/scripts/dev_env.py
      MISSING: none

$ python3 scripts/dev_env.py plan ; python3 scripts/dev_env.py env
  tree before vs after (path + size + mtime, 1107 paths)  →  IDENTICAL
  plan run 1 == run 2 == run 3                            →  byte-identical (sha256 afc9af79…)
```

Inventories checked against the real artifacts on the builder:

```
$ awk 'NF && $1 !~ /^#/ {print $1}' .../sysroot-packages.txt | wc -l       →  89
$ (cd .tooling/sysroot/debs && sha256sum -c .../sysroot-packages.sha256)   →  89 × ": OK"
$ sha256sum -c crooks-assistant/docs/dev-environment/binaries.sha256       →   9 × ": OK"
```

**What this proves:** every input the plan consumes is repository-controlled, none of it is hidden
mutable machine state, the generator writes nothing, and it repeats identically.
**What this does NOT prove:** that the environment can be rebuilt. See §6.1.

### 5.4 Doctor — positive and negative

| Case | Where | Result |
|---|---|---|
| **Positive, real** | the actual builder at `326c150` | **exit 0** — `the pinned environment · 1 advisory (printed above, not counted)`. 8 binaries, 9 digests, 4 node packages, node inputs, chromium 141.0.7390.37, sysroot + both inventories, `0 not found` shared libs, venv 3.12.3, 5 python packages, skillspector 2.11.2, `experience.browser AVAILABLE` |
| **Negative, real** | the fresh checkout, nothing installed | **exit 1** — `26 FAILED`, each line naming the tool and the expected path |
| **Negative, the BE-02 shape** | fixture: every tool present, every tool wrong | **exit 1**, `FAILED`; `shellcheck`, `gitleaks`, `playwright`, `chromium`, `venv`, `pytest-xdist`, `skillspector` each on a `FAIL` line; `all present` absent |
| **Positive control, same fixture** | identical fixture, every tool correct | **exit 0**, no `FAIL` — fail-closed is discriminating, not unconditional |
| **Integrity** | same fixture, one binary tampered at the right version | **exit 1** — `not the pinned artifact` |

Doctor now takes ~9.6 s on the builder (was ~7 s); the difference is sha256 over ~315 MB of pinned
binaries.

### 5.5 Adversarial shell/path safety proof

Checkout root, literally:

```
/tmp/adv-326c150-$(printf CROOKS_ENV_PROBE) and `printf BACKTICK` 'quote' "double" ;semi
```

Generated, raw — note the single quotes and the `'"'"'` escape for the embedded apostrophe:

```sh
export NODE_PATH='/tmp/adv-326c150-$(printf CROOKS_ENV_PROBE) and `printf BACKTICK` '"'"'quote'"'"' "double" ;semi/.tooling/node/node_modules'
```

Sourced into `/bin/sh` and read back:

```
NODE_PATH       = /tmp/adv-326c150-$(printf CROOKS_ENV_PROBE) and `printf BACKTICK` 'quote' "double" ;semi/.tooling/node/node_modules
CROOKS_CHROMIUM = …same prefix…/.tooling/browsers/chromium-1194/chrome-linux/chrome
UV_TOOL_DIR     = …same prefix…/.tooling/uv-tools
PATH (head)     = …same prefix…/.tooling/bin
→ substitution NOT executed — literal preserved
```

The regression test adds a **newline** inside the directory name, reads the values back
NUL-separated, and asserts `PATH` both starts with the prepend and ends with the inherited value.
Only fixed `printf` probes ever ran, then and now.

### 5.6 Complete diff scope and secret-scan result

Diff scope: `git diff --stat 9a27bc4..326c150` → the 10 files in §4 and nothing else. Verified by
filter: every changed path is `scripts/dev_env.py`, `tests/test_dev_env.py`, `docs/DEV_ENVIRONMENT.md`
or `docs/dev-environment/`.

**Secret scan — gitleaks 8.30.1. Findings reported by RULE and PATH only, never a value.**

```
gitleaks git --redact --log-opts "9a27bc4..326c150"       →  1 commit scanned, 90.53 KB, no leaks found  (0 findings)
gitleaks dir --redact  <the 10 changed files, isolated>   →  123.47 KB, no leaks found                   (0 findings)
```

A first scan passed the ten paths together and gitleaks walked the whole tree instead (198 MB),
returning **7 pre-existing findings in files this candidate does not touch** — listed by rule and
path only so the Director can confirm they are out of scope:

| Rule | Path |
|---|---|
| `generic-api-key` | `.tooling/browsers/chromium-1194/…/reading_mode_gdocs_helper_manifest.json` (gitignored Chromium resource) |
| `shopify-access-token` | `crooks-assistant/tests/__pycache__/test_control.…pyc` (gitignored bytecode) |
| `generic-api-key` | `crooks-assistant/tests/test_observability_redaction.py:279` |
| `generic-api-key` | `crooks-assistant/tests/test_tts.py:20` |
| `generic-api-key` | `crooks-assistant/tests/test_scribe.py:24`, `:448` |
| `generic-api-key` | `crooks-assistant/tests/test_observability.py:81` |

All present in the base, none modified here. Not investigated; no value was read, printed or
committed. Flagged as a separate pre-existing item — they are very likely test fixtures, but this
round did not verify that and does not assert it.

Also verified: none of the six new committed files is caught by a `.gitignore` rule
(`git check-ignore` → all tracked-able; `package-lock.json` is ignored by basename and
`node-package-lock.json` does not match it).

### 5.7 Clean working tree

```
$ git status --porcelain --untracked-files=all      →  (empty)
```

Clean at commit time, clean after the SHA-bound suite run, and clean now. The temporary worktree
used for the rejected-candidate comparison was removed; `git worktree list` shows only
`/opt/crooks-builder`.

---

## 6. Blockers and open items — safe engineering follow-up vs owner-only decisions

### 6.1 **OWNER DECISION — BLOCKED:** no approved package-fetch policy, so reconstruction is unproved

Executing the plan needs network fetches from npm, Playwright's CDN, apt and GitHub. Beyond that,
**step 4 cannot be written as commands at all**: the manifest pins each binary's version and
upstream repository but **not its release tag or asset URL**, and four of the eight have no `asset`
name either. Deriving eight GitHub release URLs from convention and committing them untested would
be BE-01 with a different traceback, so they were not written.

`DEV_TEAM_V1_PILOT.md` §3 says unavailable approved access produces BLOCKED rather than permission
to bypass the boundary. Accordingly: **no network package fetch was attempted, and no claim is made
that this environment has been rebuilt from scratch.**

**Needed from the owner:** an allowed package-fetch policy — which hosts, in which sandbox, with
what integrity requirement. With one, the follow-up is bounded and is ordinary engineering: pin each
release tag and asset URL in the manifest, turn step 4 into commands gated on `sha256sum -c`,
execute the whole plan on a disposable checkout, and run it a second time for idempotence.

### 6.2 **Safe engineering follow-up** — the SkillSpector commit pin is not verifiable

`uv tool install --from <local clone>` records a path, not a revision, so the installed artifact
carries nothing to compare `uv_tools.skillspector.commit` against. `doctor` prints:

```
advisory skillspector commit   d162d9b343e5 pinned at install; the installed artifact records
                               no revision, so it is not re-derivable
```

Passing it silently would be BE-02 again; failing the environment over a fact nothing on the machine
can settle would be noise. Closing it properly means recording provenance at install time, which
belongs with §6.1. No owner decision required.

### 6.3 **Decision taken that needs review** — canonical product memory was not edited from here

The inbox permits capturing contract gaps "in the existing Dev Team planning/review docs in the
repair candidate". Those docs live on `claude/product-memory-foundation` (a sibling lineage off
`e43aecd`). They are **not** in this candidate's tree, and `README.md` there states that canonical
product memory lives on that branch and is read by explicit ref.

Copying `BUILDER_ENVIRONMENT_REVIEW.md` / `DEV_TEAM_V1_PILOT.md` into a code branch and editing them
would fork the canonical record — creating two versions of the file that says which version is
canonical. **I did not do that.** The trial record is instead a new file inside the candidate,
`docs/dev-environment/CONTRACT_TRIAL_ENV_REPRO_001.md`, and the proposed product-memory edits are
in §8 below, for the Director to apply or reject on the branch that owns them.

If the Director would rather have the gaps recorded inside the candidate, that is a one-file change
— but it should be a deliberate choice, not a side effect of this repair.

### 6.4 **Pre-existing, out of scope** — a contradiction inside `DEV_ENVIRONMENT.md`

The review noted §8 says the Impeccable scan did not finish while §5.3 says it completed on a second
attempt. **Not fixed here.** It is a §3 evidence-limitation item, not one of the four blocking
defects, and correcting it would mean asserting which side is true without evidence from this round.
`DEV_ENVIRONMENT.md` §8 is otherwise unchanged. Flagged for a separate decision.

### 6.5 Nothing was blocked by my permission layer this round

No tool call was refused. `.claude/` was not written to and no write to it was attempted. No
permission was widened and no alternate path around any boundary was looked for.

---

## 7. Contract trial — ENV-REPRO-001

Full record: `docs/dev-environment/CONTRACT_TRIAL_ENV_REPRO_001.md` inside the candidate. Summary:

| Clause | Status | What happened |
|---|---|---|
| **False-success handling** | **EXERCISED** | The rejected candidate's own outbox claimed a working environment. Three of four findings reproduce against its committed code in under a second. Reproduction was attempted because the contract asks for it, not because the prose looked suspicious — a pipeline that reproduces only when a result looks wrong tests the reviewer's suspicion, not the candidate. The pilot doc's "submit at least one deliberate false green" needed no manufacturing: `doctor` exit 0 with mismatched tooling **was** BE-02, and it is now a permanent fixture with a discriminating control beside it. |
| **Exact candidate identity binding** | **EXERCISED**, with a structural limit | Every claim here is bound to `326c150` and to a named review branch, with the base named so the diff is attributable. **A candidate cannot contain its own SHA** — the trial doc records its base but not its own identity. Consequence for V1: the `Candidate` record must be built *by the collector from the committed tree*, never assembled by the implementer inside it. |
| **Review invalidation on candidate change** | **EXERCISED** | The full suite was run; the lint gate then found four findings in the new test file; the file was edited — and the earlier run was **discarded and re-run**, not carried forward, because it described a tree that no longer existed. Cheap here (8 min). The clause gets expensive exactly where evidence is slow, which is where a reuse rule will be argued for and will be wrong most often. |
| **Publication retry without rebuilding** | **NOT EXERCISED** | Publication succeeded first time; nothing was retried, and **no claim is made that retry works**. Structurally: the candidate is a commit, publication is a push of that SHA, and a repeated push of an unchanged SHA is idempotent. A retry that *rebuilt* would produce a different SHA and silently invalidate evidence bound to the first — the exact failure the clause exists to prevent. The remote **was** read back after the push (`git ls-remote` → `326c150…`) rather than trusting the push's own output, which is the pilot doc's "lose the response, read back identity before retry" in its cheap form. |
| **Obsolete / late / duplicate results, incl. the Mobile V1 incident** | **EXERCISED as analysis** | At 06:38:39Z the Director saw the mobile inbox published at 02:18:32Z, an outbox still acknowledging the *previous* Builder inbox, and no mobile review branch — four hours of Git silence — and declined to overwrite the inbox or dispatch a duplicate. **That was right.** The work existed: `claude/mobile-experience-v1-review` @ `564ef34`. **The candidate had been built; only the outbox had not been published.** A duplicate dispatch would have re-run finished work and, producing a different SHA, invalidated evidence that was already valid. An absent result is not an absent candidate. No stale token was rejected, because there are no tokens: fencing, attempt IDs and idempotency keys remain unimplemented and untested. |
| **Reviewer gating** | **EXERCISED, by refusal** | This worker implemented the repair and does not certify it. Candidate and evidence are published; acceptance is not claimed. "Builder says green" is precisely the claim `9a27bc4` was rejected for. The clause about a reviewer who supplies a patch was not tested — no reviewer supplied one. |
| **Integration re-verification** | **NOT APPLICABLE** | Nothing was integrated; the candidate is merged nowhere. Semantic-conflict detection between two accepted candidates needs two candidates and has one. |

### Contract gaps found — specification defects, not worked around

- **CG-01 — the evidence manifest has no defined identity.** The pilot doc requires an "evidence
  manifest digest" and digest-bound, independently addressable artifacts. This round produced
  terminal text inside a handoff: nothing addressable, nothing digested, so a reviewer must trust
  transcription. The review of `9a27bc4` raised this, and it is still true of this one.
- **CG-02 — invalidation has no stated granularity.** "A candidate change invalidates
  candidate-bound reviews", read literally, discards an 8-minute suite for a comment typo. The doc
  gestures at "a dependency-aware reuse rule" without defining one, so each worker invents one under
  time pressure — and reuse is indistinguishable from fabrication unless the dependency is
  machine-checked. Proposed shape (not adopted): reuse only when the changed paths are provably
  outside the evidence's input closure, with the closure recorded *with* the evidence.
- **CG-03 — the bridge cannot represent a candidate without a result.** One inbox blob, one outbox
  blob. A finished candidate whose outbox failed to publish is indistinguishable from a worker that
  never started, because the only channel that could say otherwise is the one that failed. This is
  the Mobile V1 incident, and the Director's correct instinct depended on a human choosing to check
  the branch list.
- **CG-04 — BLOCKED has no defined granularity either.** It is specified as a whole-task verdict.
  This task is not wholly blocked: three findings repaired and proved, the fourth repaired in three
  of four parts with one blocked on an owner decision. Reporting BLOCKED would hide four real
  repairs; reporting complete would hide the blocker. The contract needs **per-finding disposition**.
- **CG-05 — "prove a clean isolated reconstruction" understates what it needs.** As a checkbox it
  invites satisfaction by something that merely *looks* like a reconstruction — a unit test, or a
  rerun on the machine that already has the environment. §4 of the pilot doc already says network
  rebuild evidence is a separate class from offline unit tests; that sentence is load-bearing and
  should sit with the acceptance case rather than two sections away.

---

## 8. Proposed product-memory edits — for the Director, on `claude/product-memory-foundation`

Not applied by me; see §6.3. Proposed exactly:

1. **`CURRENT_TRUTH.md`** — replace the Builder Environment bullet:
   > Builder Environment repair candidate is published at `claude/builder-environment-repair-review`,
   > commit `326c150b778afdc2b5881b2f7ac97e140e476eab`, base `9a27bc4`. BE-01, BE-02 and BE-03 are
   > repaired with regression tests that fail against `9a27bc4`. BE-04 is repaired in its interface,
   > committed-input, path-anchoring and artifact-identity parts; **full network reconstruction
   > remains BLOCKED on an approved package-fetch policy and has not been performed.** Awaiting
   > independent review; the implementing worker does not claim acceptance. The rejected candidate
   > `9a27bc4` remains published at `claude/builder-environment-review` as the frozen fixture.

2. **`CURRENT_TRUTH.md`** — replace the "current bridge round" bullet:
   > Mobile Experience V1 is **published** at `claude/mobile-experience-v1-review`, commit
   > `564ef3430d58b34de582f5548d7fe201c4cfe04b`. The 06:38:39Z observation was a **delivery**
   > failure, not a worker failure: the candidate was built and the outbox was not published.
   > Awaiting independent review. Do not re-dispatch.

3. **`CURRENT_TRUTH.md`** — replace the last-server-observations bullet with §9 below.

4. **`DEV_TEAM_V1_PILOT.md`** — add CG-01 … CG-05 as a new "Contract gaps found in trial 1" section,
   and change §4's `Candidate identity` acceptance case to require the record to be built by the
   collector from the committed tree rather than by the implementer.

5. **`BUILDER_ENVIRONMENT_REVIEW.md`** — add a disposition line per finding pointing at `326c150`
   and the named test, with BE-04 marked **partial**; and correct the BE-02 note: binaries produced
   **`ok`**, not `warn` — the pin was displayed beside the tool's output and never compared.

---

## 9. Service and server state — observed read-only, **changed nothing**

This supersedes the "historical, not proof of current runtime state" note in `CURRENT_TRUTH.md`.
All of it predates this round; I started, stopped, installed and configured nothing.

| | Observed |
|---|---|
| Production checkout `/opt/crooks-os/crooks-assistant` | branch `claude/linux-prod-migration-production`, HEAD `1cf3a0f3361b79f9de208d80f501543c53c244b5`, **`git status --porcelain` → 0 entries (CLEAN)** |
| `crooks-assistant` service | **`active` / `running` / `enabled`**, unit `/etc/systemd/system/crooks-assistant.service`, `ExecMainStartTimestamp = Sat 2026-09-19 06:30:10 UTC` |
| Its process | pid 217827, `…/.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`, cwd `/opt/crooks-os/crooks-assistant` |
| Port 8000 | **`127.0.0.1:8000` only — loopback. Not exposed publicly.** |
| Other listeners | `0.0.0.0:22` (sshd); `127.0.0.53/54:53` (resolved); `tailscaled` (pid 1655) on `100.72.82.24:443`, `[fd7a:115c:a1e0::352b:5219]:443`, `:41706`, `:59141` — **tailnet addresses only, not `0.0.0.0`** |

**Two of these contradict the last published truth and need Director/owner reconciliation:**

1. The production checkout was last reported **dirty**; it is now **clean at `1cf3a0f`**. Something
   reconciled it between rounds. I did not, and I did not investigate — uncommitted migration work
   may or may not have been preserved. **This should be established before any promotion.**
2. The assistant service is **installed, enabled and running** — last reported as not installed —
   and `tailscaled` is listening on tailnet `:443`, which touches near-term item 5 ("enable private
   Tailscale HTTPS **when approved**"). I ran no Tailscale command of any kind, including
   `tailscale serve status`. Whether this was approved is not knowable from here and is not
   asserted.

---

## 10. Safety constraints — all preserved, each verified

- `writes_enabled` — **still `False`** (`config/settings.py:105`, untouched by this diff).
- `CROOKS_WRITES_LOCAL_OWNER` — **still `false`** (`.env.example:37`, untouched).
- FastAPI bound to **`127.0.0.1`**; port 8000 **not** exposed publicly (§9).
- Proposal / action / verification safety semantics — **unchanged**. This diff touches no
  application source: every changed path is `scripts/dev_env.py`, its test, or `docs/dev-environment/`.
- **No live Shopify, Gmail or ElevenLabs call. No live external mutation of any kind.** All tests
  offline; the only network operations this round were `git fetch` / `git ls-remote` / `git push`
  against the repository.
- **V2 not begun. UI not redesigned.** No `web/`, `app/` or `experience/` file changed.
- Mac deployment and rollback path — **untouched** (`mac/`, `launchd/`, `Makefile` unchanged).
- `/root/.claude` — **still writable**; not modified.
- **No secret value printed, read or committed.** gitleaks findings are reported by rule and path
  only. No API key, password, token, cookie or private key appears anywhere in this handoff.
- **Production untouched.** `/opt/crooks-os/crooks-assistant` was read-only inspected
  (`git rev-parse`, `git log`, `git status`, `ps`, `ss`, `systemctl show`) and never edited, checked
  out, reset or switched. No service installed, started, stopped or restarted. Tailscale untouched.
  No `/usr` write. Nothing merged, nothing deployed, nothing auto-merged.
- Permission layer: nothing refused, nothing widened, no workaround sought.

---

## 11. Exact proposed next step

**One step, and it is the Director's, not a worker's:**

> **Independently review `claude/builder-environment-repair-review` @
> `326c150b778afdc2b5881b2f7ac97e140e476eab` against base `9a27bc4`**, treating BE-04 as
> **partially repaired** and recording a disposition **per finding** rather than one verdict per
> task (CG-04). The review should re-run `pytest tests/test_dev_env.py` against `9a27bc4` and
> against `326c150` itself rather than relying on §5.1 of this handoff — CG-01 means nothing here
> is digest-bound.

Then, in order, each needing its own dispatch:

1. **Owner decision:** approve or refuse a package-fetch policy for §6.1. This is the only thing
   standing between this candidate and a genuine reconstruction proof; without it BE-04 cannot be
   closed and the Builder Environment should not be labelled complete or suitable for provisioning
   new workers.
2. **Owner/Director reconciliation** of the two runtime contradictions in §9 — specifically whether
   uncommitted production migration work was preserved when that checkout became clean, and whether
   the running service and the Tailscale `:443` listener were approved. Near-term ordering item 2
   depends on the answer.
3. **Only after 1:** a bounded follow-up that pins release tags and asset URLs, makes step 4
   executable under `sha256sum -c`, executes the plan on a disposable checkout, runs it twice, and
   records install-time provenance to close §6.2.

Not proposed and explicitly not begun: Engineering Orchestrator implementation, any merge, any
deployment, any V2 work.

---

**Inbox SHA processed: `73cb6b062e62297e3ccbcf67b1e432303574f3dc`.**
Candidate `326c150b778afdc2b5881b2f7ac97e140e476eab` published to
`claude/builder-environment-repair-review` and read back from the remote. Not merged. Acceptance not
claimed. Stopping here; the watcher owns bridge publication.
