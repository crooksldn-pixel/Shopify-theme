# CLAUDE OUTBOX — latest handoff only

## 2026-09-19T14:01:06Z — ENV-REPRO-001 continuation: BE-04 completed under the approved fetch boundary

**Inbox consumed:** `bridge/chatgpt-inbox.md`, blob `ccbc8d88c8277d4b5221eaf46165b0daa7db1a5d`
("2026-09-19 — Owner approval: bounded package fetching + BE-04 completion"). I have consumed it
and treated it as the sole instructions for this round. The SHA is recorded here so the same
instructions are never executed twice.

**Candidate:** `295e483b4f9adcdc3fb58bfb3aa025e2e3f4779b`
**Base:** `326c150b778afdc2b5881b2f7ac97e140e476eab` (the previous repair candidate, unmodified)
**Review branch:** `claude/builder-environment-repair-review` — **PUBLISHED**, read back from the
remote as `295e483b4f9adcdc3fb58bfb3aa025e2e3f4779b`. Not merged anywhere, not deployed.

**I do not claim acceptance.** This worker implemented the change and therefore does not certify
it. What is claimed is stated below with the command that produced it.

**Headline:** BE-04's blocked part is closed. The environment was rebuilt **from a checkout
containing no `.tooling/` and no `.venv/`**, twice, with both integrity gates enforced, and the
SkillSpector provenance gap is closed as a real check rather than an advisory.

---

## 1. What was asked

Continue ENV-REPRO-001 only, from `326c150`, under a newly granted owner approval for bounded
read-only package fetching. Specifically: (1) pin release tags and exact asset URLs in
repository-controlled inputs; (2) make the reconstruction plan fully executable with integrity
checks; (3) execute the complete reconstruction from a genuinely fresh/disposable checkout;
(4) run it a second time and prove the intended repeatable behaviour; (5) close the SkillSpector
provenance gap if it fits the bounded scope; (6) add/adjust regression tests. Then re-run the
relevant gates against the **exact final candidate**, because the candidate changed and prior
candidate-bound evidence is invalid for the changed tree. Update the contract-trial record with
what this continuation genuinely exercises, claiming nothing that did not occur, and preserving
CG-01…CG-05. Publish, read the remote identity back, replace the outbox, stop.

---

## 2. Builder state found on arrival (not where a previous run left it)

| | |
|---|---|
| Worktree | `/opt/crooks-builder` |
| Branch on arrival | `claude/builder-environment-repair` |
| HEAD on arrival | `326c150b778afdc2b5881b2f7ac97e140e476eab` — the exact candidate the inbox names |
| Working tree on arrival | **clean**, no untracked files |
| Stale local branch | `claude/bridge-builder` @ `9a27bc4`, tracking a remote ref that no longer exists. Left alone, as last round. |
| Remote check | `claude/builder-environment-repair-review` was at `326c150` and `claude/builder-environment-review` at `9a27bc4`, both as the previous handoff said |

The watcher's own brief describes the builder worktree as branch `claude/bridge-builder`; it is
not, and has not been for two rounds. Noted so nobody reconciles it by resetting.

**Network was verified reachable before any work was planned** (`github.com` release download →
302, `registry.npmjs.org` → 200). The previous round's blocker was a missing *approval*, not a
missing *network*.

---

## 3. What was found

### 3.1 The previous round's central hedge was true, and checking it changed what it is worth

`326c150` committed `binaries.sha256` and said plainly that those digests were **observed** off
this builder and were **not** an upstream attestation. That hedge was honest. It was also
checkable, and the approval made checking it possible.

All eight pinned release assets were fetched from their upstreams and extracted:

```
extracted binary                     committed in binaries.sha256
  shellcheck  4da528ddb3a4d1b7…  ==  4da528ddb3a4d1b7…
  shfmt       d9fbb2a9c33d13f4…  ==  d9fbb2a9c33d13f4…      (raw asset, no extraction)
  gitleaks    88f91962aa2f93ac…  ==  88f91962aa2f93ac…
  fd          16791ab3d5c2f7ce…  ==  16791ab3d5c2f7ce…
  ast-grep    7df43a8878de90c9…  ==  7df43a8878de90c9…
  hyperfine   a298729daf3b6701…  ==  a298729daf3b6701…
  trivy       d89bcc6510a267f1…  ==  d89bcc6510a267f1…
  uv          83f28650272b5543…  ==  83f28650272b5543…
  uvx         2d14adbd124a9f4e…  ==  2d14adbd124a9f4e…
                                     9 of 9 reproduced exactly
```

So the observation and the upstream releases agree: what is installed on this builder **is** what
those releases contain. That is a materially stronger statement than `326c150` was entitled to
make, and it is now recorded in the header of `binaries.sha256` itself.

Separately, four of the eight projects publish their own checksum file. The downloaded assets were
compared with them and matched: **shfmt, gitleaks, trivy, uv**. The other four — **shellcheck, fd,
ast-grep, hyperfine** — publish none. That gap is real and is now printed by `doctor` as a single
advisory naming exactly those four (§5.4).

### 3.2 The SkillSpector gap was a property of the install command, not of the universe

`326c150` reported the commit pin as undecidable because `uv tool install --from <local clone>`
records a filesystem path and no revision. Confirmed on the builder — its
`direct_url.json` reads `{"url":"file:///tmp/_skills/skillspector","dir_info":{}}`.

Installing from `git+<upstream>@<commit>` instead makes uv write PEP 610 `vcs_info.commit_id`. It
is the same package from the same source at the same revision; only the provenance record differs.
The gap was closeable inside the bounded scope and is closed.

### 3.3 One thing the previous round's step 4 would have got wrong if guessed

`ast-grep`'s release asset contains an `sg` binary alongside `ast-grep`, and `/usr/bin/sg` is
`newgrp`. `326c150`'s manifest policy said `sg` "is DELETED on install". A delete only works if
nobody forgets it. It is now simply never extracted into `.tooling/bin` — verified absent in the
reconstructed tree (§5.2).

---

## 4. What was changed

7 files, **+768 / −85**. No application, UI, action, proposal or configuration file is touched.
Verified by filter: every changed path is `scripts/dev_env.py`, `tests/test_dev_env.py`,
`docs/DEV_ENVIRONMENT.md` or `docs/dev-environment/` — the filter returned **none** outside that.

| File | | |
|---|---|---|
| `crooks-assistant/scripts/dev_env.py` | M | +199/−… |
| `crooks-assistant/tests/test_dev_env.py` | M | +282/−… |
| `crooks-assistant/docs/DEV_ENVIRONMENT.md` | M | +167/−… |
| `crooks-assistant/docs/dev-environment/manifest.json` | M | +85/−… |
| `crooks-assistant/docs/dev-environment/binary-assets.sha256` | **A** | 28 |
| `crooks-assistant/docs/dev-environment/binaries.sha256` | M | +15/−… (header only; no digest changed) |
| `crooks-assistant/docs/dev-environment/CONTRACT_TRIAL_ENV_REPRO_001.md` | M | +77 |

### 4.1 Pinned, not derived

Every `binaries` entry now carries `release_tag`, `asset`, `asset_url`, `archive` and `install`.
`install` maps the name that lands in `.tooling/bin` to the member path inside the asset, which is
how one asset (uv) produces two binaries and how `sg` produces none.

They are written down rather than computed. Deriving eight GitHub URLs from a naming convention at
run time would put the strings that decide what executes on this machine outside review — BE-01 one
layer down, which is the reason the previous round refused to guess them.

### 4.2 The approved boundary is compiled, not promised

`fetch_spec()` requires every asset URL to be exactly

```
<upstream>/releases/download/<release_tag>/<asset>
```

built from that same manifest entry's own fields, and raises `ManifestError` naming the tool
otherwise — **no fetch step is emitted at all**. A manifest edit therefore cannot move a fetch to a
mirror, to another project, to another tag, to another asset, or to a non-release path.
`test_be04_an_asset_url_outside_the_tools_own_upstream_is_refused` walks all five cases.

### 4.3 Integrity twice, and the order is the substance

```
curl -fsSL --proto '=https' --tlsv1.2   ->  .tooling/downloads/
( cd .tooling/downloads && sha256sum -c …/binary-assets.sha256 )   <- BEFORE anything unpacks
tar / unzip / install -m 755            ->  .tooling/bin/
sha256sum -c …/binaries.sha256                                     <- AFTER install
```

`binary-assets.sha256` is new and committed: the eight asset digests. Verifying an archive *after*
extracting it checks the wrong thing, because `tar` and `unzip` have already interpreted the bytes.
`test_be04_downloads_are_verified_before_anything_unpacks_them` asserts the **ordering**, that the
install gate is the last word of step 4, and that every fetch carries `--proto '=https'`,
`--tlsv1.2` and `-fsSL`.

`.tooling/downloads` is gitignored — confirmed by `git check-ignore` (`.gitignore:21:.tooling/`) —
so a download can never become a committed file by accident.

### 4.4 The advisory became a decision

Plan step 6 now installs from the pinned git requirement, and `doctor` reads the PEP 610 record.
Four outcomes, one of them `ok`: matching commit → `ok`; different commit → **FAIL**, both shown;
`dir_info` (local-path install) → **FAIL**, "records no revision", with the fixing command; no
`direct_url.json` → **FAIL**.

### 4.5 Step 0

The plan now checks the host tools it assumes (`curl tar unzip npm node apt-get dpkg-deb git
python3 make`) inside a subshell, so a missing `unzip` is a named failure at the start rather than
a confusing one at step 4.

---

## 5. Evidence — every item below was produced at candidate `295e483`

### 5.1 The reconstruction, executed — this is the item that was BLOCKED

Tree: `git archive 295e483 | tar -x -C /tmp/recon-295e483`. **No `.tooling/`, no `.venv/`**
(both confirmed absent before starting).

```
$ python3 crooks-assistant/scripts/dev_env.py plan          -> exit 0
      every input the plan reads:  8 present, MISSING: none
      "Every step is EXECUTABLE."   (no BLOCKED line anywhere in the output)

  the printed plan was extracted verbatim into a shell script — 43 commands — and run:

$ /bin/sh plan.sh                                   RUN 1 -> exit 0
$ python3 …/dev_env.py doctor                              -> exit 0, "the pinned environment"
$ /bin/sh plan.sh                                   RUN 2 -> exit 0
$ python3 …/dev_env.py doctor                              -> exit 0, "the pinned environment"
```

**Run 2 vs run 1 — environment fingerprint `diff` → IDENTICAL**, over: sha256 of every file in
`.tooling/bin`, every installed node package name+version, the `.tooling/browsers` contents, the
89-deb inventory, the extracted sysroot library listing, the SkillSpector `direct_url.json`, and
the venv interpreter version. **`doctor` transcript run 1 vs run 2 — `diff` → IDENTICAL.**

Idempotence is claimed in the precise sense the docs now state: *the second run ends in the same
environment*. It is **not** claimed that the second run performs no work — `npm ci` rebuilds from
the lock, `uv tool install` replaces the tool venv, and the log shows both happening.

Integrity gates actually fired, both runs, **106 `: OK` lines each**:

```
sha256sum -c …/sysroot-packages.sha256   ->  89 × ": OK"
sha256sum -c …/binary-assets.sha256      ->   8 × ": OK"   (before any extraction)
sha256sum -c …/binaries.sha256           ->   9 × ": OK"   (after install)
```

What was contacted, and nothing else: `registry.npmjs.org` (`npm ci`, 8 packages),
`cdn.playwright.dev` (Chromium 141.0.7390.37, build 1194), `mirror.hetzner.com` (89 `.deb`s),
`github.com` release assets (8), PyPI (`pip install -e ".[dev]"` + 5 pinned builder-only packages),
`github.com` (SkillSpector at `d162d9b3…`). **No credential of any kind was used or is needed.**

The reconstructed tree is at `/tmp/recon-295e483` (2.9 GB) if a reviewer wants to inspect it; it is
disposable and nothing depends on it.

### 5.2 The reconstructed environment, checked

`doctor` in the reconstructed checkout, exit **0**, every line `ok` except one advisory:

```
binaries        shellcheck 0.11.0 · shfmt 3.12.0 · gitleaks 8.30.1 · fd 10.3.0 · ast-grep 0.40.0
                hyperfine 1.20.0 · trivy 0.74.0 · uv 0.9.9
sha256          9 artifacts match
asset pins      8 assets, each pinned to its own upstream release
advisory        ast-grep, fd, hyperfine, shellcheck publish no checksum file; their committed
                asset digests are first-fetch observations, enforced but not attested
node            playwright 1.56.1 · @axe-core/playwright 4.11.1 · axe-core 4.11.1 · biome 2.5.14
chromium        141.0.7390.37        shared libs  0 not found
venv            Python 3.12.3        + the 5 pinned builder-only packages
skillspector    2.11.2
skillspector commit   commit d162d9b343e5 recorded by uv at install (PEP 610 direct_url.json)
experience.browser    AVAILABLE
```

`.tooling/bin` in the reconstructed tree contains exactly: `ast-grep fd gitleaks hyperfine
shellcheck shfmt skillspector trivy uv uvx`. **`sg` is absent.**

The recorded provenance, read off the reconstructed tree:

```json
{"url":"https://github.com/NVIDIA/skillspector","vcs_info":{"vcs":"git",
 "commit_id":"d162d9b343e559be13df8ebba093df3bc9d58c90",
 "requested_revision":"d162d9b343e559be13df8ebba093df3bc9d58c90"}}
```

### 5.3 Gates, re-run against the exact final candidate

The inbox required this because the candidate changed. It was honoured literally: the suite was
run once before committing, the tree was then committed unchanged, and the numbers below come from
a **second run inside the reconstructed checkout of `295e483`** — so the suite result is bound both
to the candidate SHA and to the from-scratch environment.

| Gate | Where | Command | Result |
|---|---|---|---|
| Unit/integration | reconstructed checkout @ `295e483` | `pytest -m "not live" -p no:cacheprovider -q -rs` | **`2834 passed, 2 skipped, 2 deselected in 1296.62s (0:21:36)`**, exit 0 |
| Regression subset | reconstructed checkout @ `295e483` | `pytest tests/test_dev_env.py` | **`22 passed`** |
| Lint | reconstructed checkout @ `295e483` | `ruff check .` | **`All checks passed!`**, exit 0 |
| Lint | builder @ `295e483` | `make lint` → `ruff check app config scripts tests` | **`All checks passed!`**, exit 0 |

**The count changed and the change is fully accounted for — it is not a bigger baseline.**
Previous round: `2822 passed, 8 skipped`. This round: `2834 passed, 2 skipped`.

```
2822  previous
 + 6  net new tests in test_dev_env.py (16 -> 22)
 + 6  browser-gated tests that previously SKIPPED and now RUN
----
2834                         skips 8 - 6 = 2
```

The six were unlocked because this round ran the suite with
`eval "$(python3 scripts/dev_env.py env)"` exported; the previous round did not. **Verified, not
inferred:** running the browser/experience selection *without* those exports reproduces the skips
with the reason `browser checks need a browser: playwright-core is not installed` (in
`test_browser.py`, `test_email_browser.py`, `test_live_replay.py`). Runtime rose from ~500 s to
~1296 s for the same reason — those tests now actually drive Chromium.

The **2 remaining skips** are unrelated to this candidate and are not fixable here:
`test_experience_analyser.py:728` and `test_live_replay.py:123`, both "the raw timeline is on the
Mac that recorded it".

**Non-failing noise, reported rather than hidden:** the log still ends with
`RuntimeError: Event loop is closed` tracebacks from `asyncio/base_events.py` (16 occurrences),
after the summary line, i.e. interpreter-shutdown noise; exit code 0. Present in the previous
round too. Nothing in this candidate touches asyncio. Not investigated; outside this task.

Not run and not claimed: `pyright` / `biome` (advisory, no baseline), `shellcheck` / `shfmt` (this
candidate changes no shell file), `trivy`, SkillSpector (no skill involved).

### 5.4 Regression tests — 22, and 22/22 fail against `9a27bc4`

Method: a detached worktree at `9a27bc4` with the new test file copied in as the **only** change
(`git status --untracked-files=all` showed exactly one untracked file), same interpreter. Worktree
removed afterwards; `git worktree list` is back to a single entry.

**How they fail matters, and this is reported honestly rather than as one number.**

*Defect reproductions — they fail on the behaviour that got the candidate rejected (10):*

| Test | Failure against `9a27bc4` |
|---|---|
| `…be01_plan_survives_the_repositorys_own_committed_manifest` | `TypeError: string indices must be integers, not 'str'` at `dev_env.py:225` |
| `…be01_a_broken_manifest_is_a_message_not_a_traceback` | `Traceback` in stderr |
| `…be02_doctor_fails_closed_when_tools_are_present_but_wrong` | `assert 0 == 1` — the false green itself |
| `…be02_doctor_passes_the_same_fixture_when_everything_matches` | output ends `all present — bootstrap with: …` |
| `…be02_advisory_findings_are_named_and_never_decide_the_exit_code` | `expected exactly one advisory, got []` |
| `…be02_a_tampered_binary_fails_even_at_the_right_version` | `assert 0 == 1` |
| `…be03_a_command_substitution_in_the_checkout_path_is_not_executed` | the substitution executed |
| `…be03_every_shell_metacharacter_round_trips_including_path` | `PLAYWRIGHT_BROWSERS_PATH lost the checkout path` |
| `…be04_every_input_the_plan_reads_is_committed` | `the npm project the plan installs from is not committed anywhere` |
| `…be04_bootstrap_is_gone_and_refuses_rather_than_pretending` | `assert 1 == 2` (exit code) |

*Behaviour tests — they fail because the capability does not exist in `9a27bc4` at all (12),
reported as `AttributeError` on `entries`, `plan_steps`, `cmd_plan`, `SYSROOT_PACKAGES`,
`ManifestError`, `fetch_spec`, `uv_tool_provenance`.* Six of these are this round's new tests. **An
`AttributeError` is not a reproduction of a defect and is not offered as one** — the previous round
made that distinction and it is kept. What they are is regression cover for behaviour that now
exists: pinned fetch fields, the upstream-URL precondition, fetch-field validation, gate ordering,
the git-requirement install, and the four-state provenance check.

One previously existing test was **rewritten to assert the opposite of what it used to**:
`test_be04_the_plan_says_plainly_what_it_cannot_do` →
`test_be04_the_plan_says_plainly_what_it_does_and_no_step_is_prose`. It previously required the
plan to print `BLOCKED` / `NOT EXECUTABLE YET`; it now requires those strings to be **absent**,
requires the plan to name every source it contacts and that no credential is used, and requires no
step to consist only of comments. This is flagged explicitly because a test whose assertion is
inverted deserves a reviewer's eye rather than a line in a diff.

One test caught a real defect in this round's own work: the first version of step 4 appended a
trailing comment to the `( cd … )` subshell line, and
`test_be04_no_step_leaves_the_repository_root_behind_it` failed on "subshell not closed". **The
plan was fixed, not the test** — the comment was moved to its own line.

### 5.5 Secret scan — gitleaks 8.30.1. Findings reported by RULE and PATH only, never a value.

```
gitleaks git --redact --log-opts "326c150..295e483"      ->  1 commit scanned, 50.06 KB, no leaks found
gitleaks dir --redact  <the 7 changed files, isolated>   ->  145.33 KB, no leaks found
```

**No secret value appears anywhere in this handoff, in the candidate, or in any log it cites.**
Every fetch performed this round was anonymous; no API key, token, cookie, password or private key
was read, printed, stored or committed. The 7 pre-existing findings the previous round reported in
files this candidate does not touch were not re-scanned and remain as it described them.

### 5.6 Clean working tree

```
$ git status --porcelain --untracked-files=all      ->  (empty)
$ git worktree list                                 ->  /opt/crooks-builder  295e483 only
```

Clean at commit time, clean after the SHA-bound suite run, and clean now.

---

## 6. Decisions and open items needing review

### 6.1 **DECISION TAKEN — needs the Director's eye:** this builder's own `doctor` now exits 1

Making the SkillSpector pin verifiable has a consequence that must not be buried. The builder's own
`.tooling/uv-tools/skillspector` was installed the old way (`--from /tmp/_skills/skillspector`), so
on `/opt/crooks-builder` `doctor` now reports:

```
  ok       skillspector                 2.11.2
  FAIL     skillspector commit          installed from a directory, which records no revision, so
                                        the pinned commit d162d9b343e5 cannot be verified —
                                        reinstall from git+https://github.com/NVIDIA/skillspector@d162d9b343e5
1 FAILED · 1 advisory
```

**That is the check working.** A provenance check that cannot fail the machine that wrote it is not
a check. Everything else on this builder is `ok`.

**I did not reconcile it, deliberately.** Running the new step 6 against `/opt/crooks-builder`'s own
`.tooling` would be applying an unreviewed candidate's plan to the builder environment before the
candidate has been reviewed, which is not what the inbox asked for and is not mine to decide. The
reconciliation is one command, reversible, and touches only gitignored `.tooling/`:

```sh
cd /opt/crooks-builder && UV_TOOL_DIR=/opt/crooks-builder/.tooling/uv-tools \
  UV_TOOL_BIN_DIR=/opt/crooks-builder/.tooling/bin \
  .tooling/bin/uv tool install --from \
  git+https://github.com/NVIDIA/skillspector@d162d9b343e559be13df8ebba093df3bc9d58c90 skillspector
```

**Director's call**, and it should be made deliberately rather than by the next worker hitting a
red `doctor` and assuming something broke.

### 6.2 What the advisory now is, and why it was not eliminated

`shellcheck`, `fd`, `ast-grep` and `hyperfine` publish no checksum file. Their committed asset
digests are enforced on every reconstruction but are first-fetch observations, not an independent
attestation by the project. Options were: pretend (that is BE-02), fail the environment over
something no upstream provides (noise), or name it. It is named, on one line, by tool.

### 6.3 Product memory was again **not** edited from here

Canonical product memory lives on `claude/product-memory-foundation`. Copying
`CURRENT_TRUTH.md` / `DEV_TEAM_V1_PILOT.md` / `BUILDER_ENVIRONMENT_REVIEW.md` into a code branch
and editing them would fork the record that says which record is canonical. Proposed edits are in
§8 for the Director to apply or reject on the branch that owns them. Unchanged position from last
round.

### 6.4 Still open, unchanged, not worked around

- **CG-01 … CG-05 all remain open.** §4.2 of the in-candidate trial record says which of them this
  round touched and which it did not. CG-01 (evidence has no defined identity) is **worse in
  practice now**: this round's central evidence is a 2.9 GB reconstruction and two 21-minute suite
  runs, and all of it is still terminal text in this handoff.
- **CG-06 is new** (§7).
- **The `DEV_ENVIRONMENT.md` §8 / §5.3 contradiction about the Impeccable scan** is pre-existing
  and still not fixed. Correcting it means asserting which side is true, and this round produced no
  evidence either way. Flagged again for a separate decision.

### 6.5 Nothing was blocked by my permission layer this round

No tool call was refused. No permission was widened and no route around any boundary was looked
for. `/root/.claude` is still writable and was not written to.

---

## 7. Contract trial — what this continuation actually exercised

Full record in the candidate at `docs/dev-environment/CONTRACT_TRIAL_ENV_REPRO_001.md` §4. §1–§3 of
that file are the first round and were left as written, with a forward pointer added. Summary:

| Clause | This round | |
|---|---|---|
| False-success handling | **EXERCISED** | The previous round's honest hedge ("observed, not attested") was verified rather than accepted — 9/9 digests reproduced. And making the provenance pin real **failed this builder's own environment**, which was reported (§6.1), not softened. |
| Exact candidate identity binding | **EXERCISED**, same structural limit | A candidate still cannot contain its own SHA. |
| Review invalidation on candidate change | **EXERCISED — as the instruction** | The inbox declared prior candidate-bound evidence invalid. The gates were re-run against `295e483`, not carried forward. The change landed inside `scripts/`, `tests/` and `docs/dev-environment/`, which is the input closure of every environment claim the candidate makes. |
| Publication retry without rebuilding | **NOT EXERCISED** | The push succeeded first time. Nothing was retried. **No claim is made that retry works.** The remote identity *was* read back with `git ls-remote` rather than trusting the push's own output. |
| Obsolete / late / duplicate results, fencing | **NOT EXERCISED** | No stale result arrived, no attempt was fenced, no duplicate dispatched. There are still no tokens, attempt IDs or idempotency keys. The Mobile V1 analysis from last round is **not re-counted as exercised by this round**. |
| Reviewer gating | **EXERCISED, by refusal** | Implemented here, therefore not certified here. |
| Integration re-verification | **NOT APPLICABLE** | Nothing merged, integrated or deployed. |

**CG-06 — an approval expressed only as prose cannot be enforced.** New, found by this round. The
owner's boundary arrived as a paragraph; every clause of it was checkable and none of it was
checked by anything, so it would have been held by whoever remembered reading it — for an automated
worker, nobody. It was therefore compiled into `fetch_spec()` and the two ordered integrity gates.
**The contract gap is that nothing asked for that.** A granted boundary should be recorded in a
form the candidate can be checked *against*, so a reviewer can ask "does this tree stay inside what
was approved?" and get the answer from the tree rather than from the worker's account of it.

---

## 8. Proposed product-memory edits — for the Director, on `claude/product-memory-foundation`

Not applied by me; see §6.3.

1. **`CURRENT_TRUTH.md`** — replace the Builder Environment bullet:
   > Builder Environment repair candidate is published at `claude/builder-environment-repair-review`,
   > commit `295e483b4f9adcdc3fb58bfb3aa025e2e3f4779b`, base `326c150`, original base `9a27bc4`.
   > **BE-01 through BE-04 are all repaired**, each with regression tests. BE-04's previously
   > blocked part is closed under the owner's 2026-09-19 bounded fetch approval: release tags and
   > asset URLs are pinned in `manifest.json`, the plan is executable with two ordered fail-closed
   > integrity gates, and the environment was **rebuilt twice from a checkout with no `.tooling/`
   > and no `.venv/`**, both runs ending in an identical environment with `doctor` exit 0. The
   > SkillSpector commit pin is now verified from PEP 610 install-time provenance rather than
   > reported advisory. Awaiting independent review; the implementing worker does not claim
   > acceptance. `9a27bc4` remains published at `claude/builder-environment-review` as the frozen
   > fixture.
2. **`CURRENT_TRUTH.md`** — note that `/opt/crooks-builder`'s own `doctor` exits 1 on the
   SkillSpector provenance line until §6.1 is decided, and that this is expected.
3. **`BUILDER_ENVIRONMENT_REVIEW.md`** — mark BE-04 **complete** at `295e483` (it was **partial** at
   `326c150`), citing `test_be04_downloads_are_verified_before_anything_unpacks_them` and
   `test_be04_skillspector_provenance_decides_rather_than_excuses`.
4. **`DEV_TEAM_V1_PILOT.md`** — add **CG-06**; record that CG-01…CG-05 remain open; and record the
   continuation dispositions in §7 above, specifically that publication-retry and obsolete-result
   fencing are **still untested**.
5. The previous handoff's proposed edits 1–5 that have not yet been applied still stand, except its
   edit 1, which item 1 above supersedes.

---

## 9. Service and server state — observed read-only, **changed nothing**

| | Observed 2026-09-19T14:01Z |
|---|---|
| Production checkout `/opt/crooks-os/crooks-assistant` | branch `claude/linux-prod-migration-production`, HEAD `1cf3a0f3361b79f9de208d80f501543c53c244b5`, **`git status --porcelain` → 0 entries (CLEAN)** |
| `crooks-assistant` service | **`active` / `running` / `enabled`**, `MainPID=217827`, `ExecMainStartTimestamp = Sat 2026-09-19 06:30:10 UTC` — same PID and start time as the previous round, i.e. **not restarted** |
| Port 8000 | **`127.0.0.1:8000` only — loopback. Not exposed publicly.** |
| Other listeners | `0.0.0.0:22` and `[::]:22` (sshd); `127.0.0.53/54:53` (resolved); `tailscaled` (pid 1655) on `100.72.82.24:443`, `:41706`, `[fd7a:115c:a1e0::352b:5219]:443`, `:59141` — **tailnet addresses only, never `0.0.0.0`** |
| Disk | 75 G total, 17 G used, **56 G available** (the reconstruction accounts for ~2.9 G of the rise) |

**The two contradictions the previous handoff raised are unchanged and still need owner/Director
reconciliation** — they are not re-investigated here and no new information was obtained:

1. The production checkout was once reported dirty and is now clean at `1cf3a0f`. Whether
   uncommitted migration work was preserved is still unestablished. **This should be settled before
   any promotion.**
2. The service is installed, enabled and running, and `tailscaled` listens on tailnet `:443`.
   Whether that was approved is not knowable from here and is not asserted. I ran no Tailscale
   command of any kind.

---

## 10. Safety constraints — all preserved, each verified this round

- `writes_enabled` — **still `False`** (`config/settings.py:105`, untouched by this diff).
- `CROOKS_WRITES_LOCAL_OWNER` — **still `false`** (`.env.example:37`, untouched).
- FastAPI bound to **`127.0.0.1`** (`Makefile:109`); port 8000 **not** exposed publicly (§9).
- Proposal / action / verification safety semantics — **unchanged**. The diff touches no application
  source; the out-of-scope path filter returned **none**.
- **No live Shopify, Gmail or ElevenLabs call, and no live external mutation of any kind.** The
  network operations this round were: read-only GitHub release metadata and asset downloads, npm,
  Playwright's CDN, the apt mirror, PyPI, a git clone of the pinned SkillSpector revision, and
  `git fetch` / `ls-remote` / `push` against this repository. All anonymous, all read-only except
  the single push of the candidate to its review branch.
- **V2 not begun. UI not redesigned.** No `web/`, `app/` or `experience/` file changed.
- **Engineering Orchestrator not implemented**, as the inbox required.
- Mac deployment and rollback path — **untouched** (`mac/`, `launchd/`, `Makefile` unchanged).
- `/root/.claude` — **still writable**; not modified.
- **No secret value printed, read or committed**; no credential was used anywhere.
- **Production untouched.** `/opt/crooks-os/crooks-assistant` was read-only inspected
  (`git rev-parse`, `git log`, `git status`, `systemctl show`, `ss`) and never edited, checked out,
  reset or switched. No service installed, started, stopped or restarted. Tailscale untouched. No
  `/usr` write. Nothing merged, nothing deployed, nothing auto-merged.
- **Only `/tmp` and the builder worktree were written.** `/opt/crooks-builder/.tooling` was **not**
  modified (see §6.1 — this is why its `doctor` reports one FAIL).
- Bridge worktree: only `bridge/claude-outbox.md` was written. Nothing staged, committed or pushed
  there; the watcher owns publication.

---

## 11. Exact proposed next step

**One step, and it is the Director's:**

> **Independently review `claude/builder-environment-repair-review` @
> `295e483b4f9adcdc3fb58bfb3aa025e2e3f4779b` against base `326c150`**, recording a disposition
> **per finding** (CG-04), and treating BE-04 as **claimed complete rather than accepted complete**.
> The review should not rely on §5 of this handoff — CG-01 means nothing here is digest-bound. The
> two things worth re-running independently are:
>
> 1. `git archive 295e483` into an empty directory, run the printed plan, run it again, and confirm
>    `doctor` exits 0 both times and the environment fingerprints match. That is the claim this
>    round exists to support, and it is ~11 minutes per run.
> 2. `pytest tests/test_dev_env.py` against `9a27bc4` and against `295e483`, and check §5.4's
>    distinction between the ten defect reproductions and the twelve `AttributeError` behaviour
>    tests — because that distinction is exactly the kind of thing a worker has an incentive to
>    blur.
>
> Also specifically review the **inverted test** named in §5.4 and the **`fetch_spec()`
> precondition** in §4.2, since the second is this round's encoding of the owner's approval and a
> reviewer is the only one who can say whether the encoding matches what was granted.

Then, in order, each needing its own dispatch:

1. **Director decision on §6.1** — whether to reconcile this builder's own SkillSpector install, or
   to leave `doctor` red there until the candidate is accepted.
2. **Owner/Director reconciliation of the two runtime contradictions in §9** — unchanged from last
   round, and still gating near-term ordering item 2.
3. **Only after acceptance:** whether the Builder Environment is now considered a suitable
   foundation for provisioning new workers, which was the original purpose of the whole exercise
   and is a judgement, not a test result.

Not proposed and explicitly not begun: Engineering Orchestrator implementation, any merge, any
deployment, any V2 work, any production change.

---

**Inbox SHA processed: `ccbc8d88c8277d4b5221eaf46165b0daa7db1a5d`.**
Candidate `295e483b4f9adcdc3fb58bfb3aa025e2e3f4779b` published to
`claude/builder-environment-repair-review` and **read back from the remote** as that exact SHA. Not
merged. Acceptance not claimed. Stopping here; the watcher owns bridge publication.
