# CLAUDE OUTBOX — latest handoff only

**Timestamp:** 2026-09-19 ~10:05 UTC
**Inbox blob SHA processed:** `24b713cce3d0e8c9ede3185ebef78cc107ece507`
**Inbox round:** "2026-09-19 — CROOKS Mobile Experience V1"
**Bridge worktree at start:** branch `crooks-ai-bridge`, HEAD `165c366c3132ef2dc3b42f3cc1ffaa5296b4af07`
**Builder worktree at start:** `/opt/crooks-builder`, branch `claude/mobile-experience-v1`,
HEAD `564ef3430d58b34de582f5548d7fe201c4cfe04b`, **working tree clean**

I have consumed `bridge/chatgpt-inbox.md` at the blob SHA above — verified with `git hash-object`
in the bridge worktree — and treated it as the sole instructions for this round. Recording the SHA
here so these instructions are never executed twice.

---

## 0. READ THIS FIRST — this was a DUPLICATE DISPATCH, not a fresh round

**The work this inbox asks for was already completed and published by the previous run, and the
previous run's handoff was written but never published.** Two facts established that before I
changed anything:

1. The outbox already present in the bridge worktree recorded **this exact inbox SHA**
   (`24b713c…`) as processed, and was sitting **uncommitted** (` M bridge/claude-outbox.md`) —
   i.e. the prior round finished its work and wrote its handoff, but the watcher never published
   it.
2. `git ls-remote` confirms `refs/heads/claude/mobile-experience-v1-review` is already at
   `564ef3430d58b34de582f5548d7fe201c4cfe04b` — the candidate is published.

**Therefore I did not re-execute the build.** Re-running a completed, published candidate would
have risked a second divergent commit on the review branch for no gain. Instead I spent this round
**independently verifying the prior run's claims** and **carrying its handoff forward** so its
content is not lost when this file is replaced.

**Everything in §3–§8 below is the prior round's substantive handoff, preserved. §1–§2 are mine.**

---

## 1. Result

**Candidate commit SHA:** `564ef3430d58b34de582f5548d7fe201c4cfe04b` (`564ef34`)
**Review branch:** `claude/mobile-experience-v1-review` — **PUBLISHED and verified this round** by
`git ls-remote`: remote ref == local HEAD == `564ef34`.
**Not merged. Not deployed.** Production untouched.

**Nothing in the repository was changed by me this round.** The builder worktree is clean at
`564ef34`, identical to how the prior run left it. The only file I wrote is this outbox.

**Both primary gates re-run and green under my own measurement:** `pytest` **0 failed**
(2821 passed, 8 skipped, 2 deselected) and the full browser sweep **714 checks, 0 failed** — the
latter an exact reproduction of the prior round's number. Detail and the reconciliation of the
pytest counts are in §2.2.

## 2. What I independently verified this round

I did not take the prior run's numbers on trust. Verified directly:

| Check | Method | Result |
|---|---|---|
| Review branch published | `git ls-remote --heads origin` | `claude/mobile-experience-v1-review` == `564ef34` ✔ |
| Builder tree clean | `git status --porcelain` | empty ✔ |
| **Production untouched** | read-only inspect of `/opt/crooks-os/crooks-assistant` | branch `claude/linux-prod-migration-production` @ `1cf3a0f`, clean ✔ — never switched, edited or reset |
| `writes_enabled` still false | `config/settings.py:105` | `writes_enabled: bool = False` ✔ |
| FastAPI loopback binding | `config/settings.py:32` | `host: str = "127.0.0.1"` ✔ (port 8000 not exposed) |
| `CROOKS_WRITES_LOCAL_OWNER` | grep across `app/` | unchanged; **no `app/` file is in the diff** ✔ |
| Candidate diff scope | `git show --name-only 564ef34` | 9 text files + 40 screenshots — see below ✔ |
| Secret scan of full diff | regex sweep (`api_key\|secret\|password\|bearer\|private key\|shpat_\|shpss_\|ghp_\|sk-…\|AKIA…`) | **clean** — single hit is the word "secret" in prose ✔ |

**Candidate file list, confirmed by me** (this is the non-regression claim as a fact, not a
promise): `DESIGN.md`, `docs/MOBILE_EXPERIENCE_V1.md`, `experience/browser.py`,
`scripts/browser/mobile.js`, `tests/test_browser.py`, `tests/test_compose.py`,
`tests/test_mobile.py`, `tests/test_touch.py`, `web/style.css` — plus 40 PNGs under
`docs/screens/mobile-v1/`.

**No `app/` route, no backend, no product JS, no HTML, no config, no dependency change.** The only
non-CSS/test/doc file is `experience/browser.py`, and I read its full diff: it is **purely
additive** — it defines `MOBILE_SCRIPT` and adds it to two existing tuples so `mobile.js` joins the
default sweep and the screenshot pass. No action, proposal, speech, arming, expiry or authorization
semantics are touched anywhere in the candidate.

### 2.1 A correction to my own first reading — the browser gate is NOT broken

My first attempt at the sweep returned `skipped: playwright-core is not installed`. **That was my
own missing environment, not a defect in the candidate and not a regression.** The Builder
Environment supplies the toolchain outside the worktree (`.tooling/node/node_modules`,
`.tooling/browsers/chromium-1194`, `.tooling/sysroot`), and `scripts/dev_env.py env` exports the
four variables that make it resolvable (`NODE_PATH`, `PLAYWRIGHT_BROWSERS_PATH`, `CROOKS_CHROMIUM`,
`LD_LIBRARY_PATH`). With that environment applied, `experience.browser.available()` returns
**`(True, '')`** and the sweep runs.

This is exactly the trap `docs/DEV_ENVIRONMENT.md` §3.2 warns about ("its absence looks like *not
installed*"). **Recording it because it will catch the next reviewer too:** any gate run must be
preceded by `eval "$(.venv/bin/python scripts/dev_env.py env)"`, or the gate will report itself
skipped while appearing green-ish. I installed nothing and widened no permission to resolve it.

### 2.2 Gate re-runs — **completed and measured by me this round**

I re-ran both primary gates from scratch on this tree. **Both are green.**

| Gate | My measurement this round | Prior round's claim |
|---|---|---|
| `pytest -q -m "not live"` (full offline suite) | **2821 passed, 8 skipped, 2 deselected, 0 failed** (512.92s) | 2827 passed, 4 skipped, 0 failed |
| Full browser sweep (`run_checks()`, correct env) | **714 checks, 0 failed**, `skipped: False` | 714 checks, 0 failed |

**The browser sweep reproduces the prior claim exactly: 714 checks, 0 failures.**

**The pytest counts differ, and the difference is fully explained — it is not a discrepancy.**
The totals reconcile exactly: mine 2821 + 8 + 2 = **2831 collected**; the prior round's 2827 + 4 =
**2831 collected**. The delta is:

- **2 deselected** — I used the `make test` target `-m "not live"`, which deselects the two
  live-marked tests. The prior round ran the suite without that marker filter.
- **4 additional skips** — my pytest run did **not** have the Builder Environment applied, so the
  browser-gated tests skip. I confirmed the exact mechanism: `tests/test_browser.py:77` skips with
  *"browser checks need a browser: playwright-core is not installed"*. Six test files are gated
  this way (`test_browser`, `test_clickpath`, `test_collision_gate`, `test_density`,
  `test_email_browser`, `test_live_replay`).

**No test failed in either run. Zero `FAILED` lines in my log.** I checked the summary line
directly rather than trusting the exit code — the prior round recorded that an exit code once
masked a real failure through a shell pipe, and my own run likewise exited 0 while printing an
unrelated `RuntimeError: Event loop is closed` from asyncio teardown at exit. **That teardown noise
is post-summary and not a test failure**, but it is worth a reviewer's eye as latent log noise.

**Independent confirmations from my sweep, beyond the headline number:**

- **The Split-control finding did not reproduce — a third independent sweep.** All eleven
  `PATH 4-split-two-halves-independent` checks pass, **including `step 2 · Split → 2 halves`**,
  which is the exact check the original finding recorded as deterministically failing. This
  materially strengthens the load-dependent attribution in §6.
- **The new phone gate genuinely measures phones.** 122 check lines at `390x844@3` and
  `375x667@2`, of which 26 are safe-area / keyboard / touch-target checks — e.g. *"every control a
  finger finds is at least 44px"*, *"the voice layer touches no navigation control"*, *"the page is
  not wider than the phone"*, and *"a 95ms press on orders lands, as a landing and not as a
  sentence"*. **Zero interactive collisions at both phone viewports**, alongside the pre-existing
  zero at 601×889 and 800×1280.

The sweep's `tool=… tier=AMBER/GREEN` log lines are the **local fixture harness on loopback**, not
live API calls. The run also logged *"no elevenlabs_api_key in the Keychain"* and *"whisper-server
is not running"* — **positive evidence that no live speech or external API call was possible or
made**.

---

*Everything from here down is the previous round's handoff, preserved verbatim in substance so it
is not lost. Its "I" is that run, and its gate numbers are its own measurements.*

## 3. What was asked

Build a CROOKS Mobile Experience V1 candidate for representative iPhone/mobile widths, preserving
product doctrine, safety/action semantics and existing Samsung/tablet behaviour. Evidence-driven
workflow (BEFORE capture → implement → AFTER capture → interaction/a11y/regression/unit tests →
diff and secret scan → commit → publish to a review branch, no merge). Attribute the known
Split-control browser-gate finding precisely rather than rewriting behaviour around it.

## 4. The candidate, and the failure found on re-measure

The prior round inherited a substantially complete but **entirely uncommitted** candidate from an
earlier run (HEAD was `9a27bc4`, the Builder Environment candidate). It re-ran the gates rather
than trusting them, and its first full `pytest` returned **1 failed, 2826 passed**:

```
FAILED tests/test_compose.py::test_the_hold_surface_is_not_over_the_composer
```

**The candidate broke it.** The test asserted the voice band's height as the literal string
`height:var(--dock)`. The safe-area-token change makes it `height:calc(var(--dock) + var(--safe-b))`,
so the assertion went stale. The parallel assertion in `tests/test_touch.py` **had** been updated
for the same change; this one had not — an inconsistently-carried edit, not a second opinion about
the layout.

**Flagged for review: the earlier run's own document reported the suite as passing. It did not.**
Had the candidate been published unverified, a red suite would have reached review described as
green.

The underlying safety invariant was verified **before** the test was touched. The test exists to
prove the hold surface is a band along the bottom and never over the composer — that typing cannot
sit under the voice surface. `.app` reserves `calc(var(--dock) + var(--safe-b))` for that band. The
band used to be `--dock` tall with the inset taken *out* of it, so on a notched phone it was 34px
**shorter** than its own reservation. The two are now one number: the composer still stops above
the band on every device, and the strip of dead ground between them is gone. Where there is no
inset — tablet, desktop, every viewport in `DESIGN.md` §13 but the phone — `--safe-b` is `0px` and
the arithmetic is byte-for-byte the old behaviour. **The invariant is preserved and is now tighter.**

The assertion was updated to match, and **a second one added**: that the band's height and `.app`'s
reservation are the same expression. A brittle string equality that could drift silently is
replaced by the pairing that actually carries the safety property. A sweep for the same class of
miss across every changed value (`83827c`, `min-width:240px`, `padding:9px 0`, `88vh`, `26vh`,
`min-height:32px`, `height:var(--dock)`, bare `env(safe-area-inset`, `hold-w:200px`) found **no
other stale assertion**.

### What changed in the UI, and why

- **The dock asked for 476px of a 390px screen.** Orders sat at x=-29 and Products ended at x=419:
  two of the four ways into the shop could not be reached with a thumb. The band cannot get wider,
  so on a phone the **arrangement** changes rather than the sizes — the same 112px becomes two rows,
  four areas above and the hold across the whole of the bottom. The NAVIGATION/VOICE separation §8
  requires is then vertical, bought with geometry exactly as before.
- **`.talk-label` kept `min-width:240px`** in a slot the phone query narrowed to 200px, so the voice
  layer was painted 10px over the Inbox and Sales icons — layer 5 over layer 3, D-1's own rule and
  D-1's own shape. A width is now **bought from its slot and never asserted over it**, which removes
  the mechanism rather than the symptom.
- **The four safe-area insets became tokens** — both to fix the band/reservation mismatch above, and
  because `env()` cannot be set from a test, which is why nothing here had ever checked a notch or a
  home indicator. A custom property can, and the new gate does.
- Not phone-specific, found at every viewport: `.rows.tight .row` used a padding shorthand that
  reset the 26px reserved for the chevron, so "1h ago" read "1h ag›" on every tight list; `--ink-3`
  measured 4.26:1 on a raised tile where AA wants 4.5; `.rail-more` was a 32px target in a product
  whose floor is 44.

## 5. Gate and evidence results

| Gate | Result (prior round) | Re-confirmed by me? |
|---|---|---|
| Python suite (`pytest`, full) | 2827 passed, 4 skipped, 0 failed (22m30s) | **Yes** — 2821/8/2 deselected, 0 failed; totals reconcile to 2831 (§2.2) |
| Full browser sweep (`run_checks`) | 714 checks, 0 failed, `ok=True` | **Yes — exact match**, 714 checks / 0 failed |
| Split reproduction | 38 checks, 0 failed | **Yes** — all 11 PATH-4 checks pass in my full sweep, incl. step 2 |
| Interactive collisions @ 601×889, 800×1280, 390×844, 375×667 | 0 | **Yes** — 0 at all four in my sweep |
| Secret scan | clean | **Yes** — independently re-scanned (§2) |
| axe-core accessibility figures | 44 → 40, contrast 15 → 0 | **No** — relayed only, see below |

The sweep grew from 593 to 714 checks — `mobile.js` joining `run_checks`' default tuple. Its check
names are **guarded** in `tests/test_browser.py`, so a run that quietly stops measuring a viewport
is a **failure** rather than a smaller green number. That guard is the most valuable structural part
of this candidate.

**BEFORE → AFTER, the product's own collision engine** (8 surfaces):

| Viewport | Collisions | Off-viewport |
|---|---|---|
| 390 × 844 @3 | **32 → 0** | 75 → 9 |
| 375 × 667 @2 | **32 → 0** | 83 → 9 |
| 601 × 889 @1.33 | 0 → 0 | 6 → 6 |
| 800 × 1280 @1 | 0 → 0 | 0 → 0 |
| 1280 × 800 @1 | 0 → 0 | 0 → 0 |

The tablet and desktop columns are unchanged — the non-regression claim stated as a number.
BEFORE/AFTER screenshots at all four device viewports are committed under `docs/screens/mobile-v1/`.

**Accessibility:** axe-core 4.11.1, 4 viewports × 3 surfaces: 44 → 40 violation entries,
`color-contrast` **15 nodes → 0**. The four remaining violation classes are identical at all four
viewports, so none is phone-specific and none is a regression; each is carried in
`docs/MOBILE_EXPERIENCE_V1.md` §6 with a proposed fix. **This evidence is two rounds removed from
direct measurement** — the prior round relayed it rather than reproducing it, and so do I.

## 6. The Split-control finding — attributed, and explicitly NOT fixed

`BROWSER_GATE_FINDING.md` recorded one deterministic failure: a 95 ms press on Split not landing in
`PATH 4-split-two-halves-independent · step 2`.

**On this tree it did not reproduce at all** — not in isolation (38/38) and not in the full sweep
(714/714), where it had previously been deterministic. All nine steps of the path passed.

Combined with the attribution work (the chip is the top element at the press coordinates; the touch
machine classifies the press as `{control:true, voice:false, approval:false, scroll:false}`; the
rect is stable across 500 ms; press durations of 95–400 ms all land in isolation):

> A hit-target, layering or `pointer-events` defect is a property of **the tree**, and the tree did
> not change between the run that failed and the run that passed. A settle budget under CPU
> contention is a property of **the machine**, and that did change.

Attribution: `hop()`'s 4.3 s settle budget in `scripts/browser/clickpath.js`. **Not** a UI
hit-target/layering/pointer-events defect, and **not** D-1 returning.

**No fix is included, and the green must not be read as a repair.** The flake is still in the
harness and will return on a loaded machine. Widening a harness timeout changes what the gate
measures and belongs in its own reviewed step. **The browser gate was not weakened, skipped or made
more permissive.**

## 7. Safety — every constraint verified intact

- `writes_enabled` remains `False` — **re-verified by me this round**, and not in the diff.
- `CROOKS_WRITES_LOCAL_OWNER` unchanged; FastAPI loopback binding unchanged — **both re-verified**.
  Port 8000 not exposed.
- Proposal / action / verification / arming / expiry / authorization / speech-vs-screen semantics:
  **not one line touched** — re-verified against the committed file list.
- **No live Shopify, Gmail or ElevenLabs call, and no external mutation of any kind.** All evidence
  is the fixture backend on loopback.
- V2 not begun. UI not redesigned. Mac deployment and rollback path untouched. `/root/.claude`
  untouched and still writable. **No secret value read, printed or committed** — re-scanned by me.
- **Production untouched:** `/opt/crooks-os/crooks-assistant` on
  `claude/linux-prod-migration-production` @ `1cf3a0f`, clean — **re-verified read-only this round**.
  Nothing merged, nothing deployed, nothing auto-merged.
- Builder worktree clean at `564ef34`; the only remote ref ever written was
  `claude/mobile-experience-v1-review`. **I wrote no ref and made no commit this round.**

## 8. Decisions and questions needing owner review

1. **The keyboard trade on a phone** (candidate doc §7) — *the item genuinely needing owner
   judgement.* While the keyboard is open on a phone **and only then**, the four dock areas, the
   Split invitation and the trail's entity chips stand down. Assistant / Back / Previous / Next and
   the full-width 48px hold stay. Everything returns when the keyboard closes; nothing is disabled
   or made unreachable. Forced by arithmetic: 375×313 with the keyboard up is 244px of fixed
   furniture on a 313px screen, and without the trade the deck measured **20px**. The precedent is
   the product's own — the halves' band already does this in the same query, for the same reason.
   **But it is a decision about what the owner can reach while composing, and it should be his.**
2. **`user-scalable=no` stays** (§6.1). axe flags it (WCAG 1.4.4) at every viewport. It is disabled
   deliberately: two-finger spread *divides the orb* and pinch *merges the halves*, so browser zoom
   would compete with the product's own gesture on the same surface, over a write-capable
   workspace. Reported rather than silently resolved, per the authority order. **Owner decision.**
3. **The prior round fixed a failing test rather than stopping** (§4). Judged in scope — the inbox
   asks for the smallest safe fix with proof and for failures not to be hidden — but it is a test
   assertion authored by an agent and warrants a reviewer's eye.
4. Three pre-existing, non-phone-specific accessibility items are deferred with proposed fixes in
   §6.2–6.4 (`<li role="button">`, the card tab strip's missing overflow fade, no `<h1>`). Each
   would change shared DOM or render paths and belongs in its own pass with its own gate run.

**No blockers were hit this round.** Nothing required owner approval to reach this point. **Nothing
was blocked by my permission layer, no permission was widened, and no workaround was sought.**

## 9. Exact proposed next step

1. **First, decide whether the duplicate dispatch needs fixing at the watcher level.** This round
   fired on an inbox SHA that had already been processed, because the prior round's outbox was
   written but never published. If the watcher re-dispatches whenever an outbox publish does not
   land, an unattended round could redo completed work. **Suggested guard: have the watcher skip
   dispatch when the working-tree outbox already records the incoming inbox SHA.** This is the one
   new finding of this round.
2. **Then review `claude/mobile-experience-v1-review` @ `564ef34`.** Suggested order:
   `crooks-assistant/docs/MOBILE_EXPERIENCE_V1.md` → the `web/style.css` diff (every rule carries
   the measurement that justifies it) → §4 above for the changed test.
   **Both primary gates are independently green as of this round (§2.2)** — the candidate does not
   need re-gating before review. If you do re-run, apply
   `eval "$(.venv/bin/python scripts/dev_env.py env)"` first (§2.1), or the browser-gated tests
   will silently skip rather than run.
   **The one piece of deliverable evidence still unverified by anyone but its original author is
   the axe-core accessibility result** (§5). If a reviewer wants it confirmed, that is the gap.
3. **Two owner decisions are needed before merge can be considered:** the keyboard trade (§8.1) and
   `user-scalable=no` (§8.2).
4. **Best next work item, as its own round:** fix the `clickpath.js` settle-budget flake (§6). It is
   demonstrably load-dependent rather than deterministic, and while it remains, every full-sweep
   result on a loaded machine is ambiguous — which is adjacent to how a red suite nearly reached
   review as green. Suggested shape: make `hop()`'s settle wait on an observable post-fork state
   change rather than a fixed 4.3 s budget, so the gate measures the product rather than the
   machine. That changes what the gate measures and must be reviewed on its own terms.

---

*Inbox SHA processed: `24b713cce3d0e8c9ede3185ebef78cc107ece507` — already processed by the prior
run; this round verified rather than re-executed. Candidate `564ef34` published to
`claude/mobile-experience-v1-review`; not merged, not deployed. Production untouched; writes stay
disabled; no live API was called; no secret was read, printed or committed. No commit, no push and
no ref write was made by this round.*
