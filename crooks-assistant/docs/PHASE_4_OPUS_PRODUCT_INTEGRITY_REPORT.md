# PHASE 4 — PRODUCT INTEGRITY

A pass prompted by one hour on a physical Samsung Tab A, not by a feature list. The starting
question was not "what else can it do" but "what did the owner actually see, and was it true".

- **STARTING SHA** `53ff16a` (Phase 3 final)
- **FINAL SHA** `0b67803`
- **BRANCH** `claude/crooks-assistant-build-lgxlau`, pushed
- **COMMITS** 83
- **FILES CHANGED** 107 (+20,497 / −844)
- **DEPLOYED** No. Production is untouched.

---

## 1 · THE REFRAMING

The generated analyser scored the live session 11 successful, 2 partial, 1 failed. Judged by
what the owner could see, it was close to the opposite. The rebuilt analyser now reports both
outcomes for every turn, and re-scored the same file:

| | SUCCESSFUL | PARTIAL | FAILED |
|---|---|---|---|
| System outcome (what the old report said) | 11 | 2 | 1 |
| Owner-visible outcome (what the new one says) | **1** | **3** | **10** |

Nine of those ten failed on the glass while the Mac was correct. That gap — HTTP 200 with a
stuck spinner, a focus change that redrew nothing, a landing that existed and was reported
missing — is what this pass was for.

The full reconstruction is `docs/phase4/LIVE_SESSION_FORENSICS.md`, written before any code
changed, with fifteen defects D-1…D-15 each carrying evidence, root cause, visible
consequence, system consequence, fix and regression test. It contains no customer names and no
email addresses; the raw JSONL it was written from stays in gitignored `logs/test-sessions/`.

---

## 2 · ROOT CAUSES

Eight defects had a single, provable mechanism. Each was established in the code before any
work was briefed, not hypothesised from the symptom.

**D-1 — the stuck "Applying…" — had two independent causes, and both are fixed.**

1. `settleProposals` in `web/app.js` settled a card only when its state was `arming` or
   `armed`. A committed card's state is `committing`, set by `ui.js`'s `commit()` on the same
   tap. So the one card that had actually been applied was the one card the reconciler refused
   to settle. The tablet's own telemetry recorded this once per turn, in a field called
   `kept` — six `tablet_reconcile reason=turn count=2 kept=2` events nobody read.
2. `web/app.js` declared `function replaceCard` **twice** at the top level — one taking DOM
   nodes already drawn, one taking a ui list to draw. JavaScript hoists the later declaration
   over the earlier, so `settleAction`'s `replaceCard(node, rendered.nodes)`, written against
   the first, silently reached the second, handed DOM nodes to `CrooksUI.render`, got nothing,
   and returned null. The proof of a verified change was never drawn at all.

   Two of the eight workstreams found this independently, from opposite ends. Neither an ASGI
   test nor a source-reading test could see it: the test that covered `replaceCard` asserted
   on the body of the declaration the browser never ran.

**D-2** — `waiting_ids` counted undo offers as changes still pending, so a merge announced
"2 changes still waiting" over a branch whose only outstanding items were offers to undo work
already done.

**D-3** — `branch.show` replayed the parent's presented cards into a fresh fork. Verified on
the base tree: `branch.show` on a new half returned `['order','attention']`, byte-identical to
its parent. The owner tapped between the two halves six times in nine seconds looking for a
difference that did not exist.

**D-4** — two causes again. The analytics read plan was keyed on `session.turn_id`, and a tap
starts no turn, so a tap inherited the last spoken turn's budget AND its "this query already
ran" answers; and speculative reads spent the same single budget the owner's own reads drew
on. `open.area` at 00:25:48 came back `landing_unavailable` for a landing that existed.

**D-6** — asked "what does the split button do?", the system answered about Shopify. It had no
representation of its own interface to answer from.

**D-8** — `period_from()` returned `None` for a corrected temporal word and its caller's
fallback was literally `or "today"`, so "today's — uh — yesterday's orders" was answered for
the word the owner had just taken back.

**D-10** — `navigation.home` was a trail move over a stack that held a record, so Home
replayed an entity instead of landing on a place; `navigation.back` restored a render rather
than a workspace. Eight Home presses and four Back presses in twenty-two seconds, all
returning `ok=true`.

**D-12** — the deck was drawn and scrolled **through** the fixed 112 px dock band, so any
control that came to rest there was untouchable: `#talk` took the tap as speech. It hit 9 of
15 stress fixtures at 601 × 889 and was invisible to every existing check, because the
telemetry's `clipped=0` was answering a narrower question than the one the owner was asking
while looking at overlapping text.

---

## 3 · LIVE DEFECTS FIXED

| ID | Defect | Fix | Proof |
|----|--------|-----|-------|
| D-1 | Verified change left "Applying…" for ever | Explicit finite UI state machine (`web/action-state.js`) with a watchdog; SETTLED maps only `verified` to done; both `replaceCard` declarations renamed | `tests/web/action-state.test.js` (15), `tests/test_action_state.py` (10), `scripts/browser/action_state.js` (12), `scripts/browser/accept.js` check "success is shown only from the verified answer" |
| D-2 | Undo offer counted as a change still waiting | `waiting_ids`/`undoable_ids` split in `app/actions/engine.py`; `POST /actions/{id}/dismiss` | `tests/test_actions.py`, `action_state.js` merge check |
| D-3 | Split showed two identical screens | `fork_from`: a half inherits what its parent HOLDS and nothing of what it SHOWS; per-branch state and headline; five branch states | `tests/test_split.py` (19), `scripts/browser/split.js` (23 × 2 viewports) |
| D-4 | The owner's read refused because an earlier turn read too much | Five read lanes in priority order, each keyed on a unit of work; foreground yields nothing to background | `tests/test_read_budget.py` (17) |
| D-5 | Nothing appeared until everything was ready | Progressive workspaces: shell at 0.0 ms, first fact at 2.5 ms, complete at 210 ms | `tests/test_progressive.py` (31), `tests/test_progressive_turn.py` (6), `tests/web/progressive.test.js` (13) |
| D-6 | The assistant disclaimed its own interface | `app/observability/ui_semantics.py` + `app/families/self_knowledge.py` | analyser suite |
| D-7 | Owner-reported defects had nowhere to go | `app/observability/feedback.py` + `app/families/owner_feedback.py`; report §15 carries them verbatim | analyser suite |
| D-8 | "today's — uh — yesterday's" answered for today | `app/fastpath/correction.py`; nine correction shapes, nine comparisons that must not flip | `tests/test_self_correction.py` (25) |
| D-9 | Precision had no keyboard | Typable fields with a visible "Tap to type"; a new address workspace; drafts survive a redraw with the caret | `tests/test_address_typing.py` (36), `tests/web/email.test.js` (24) |
| D-10 | Navigation answered ok=true while the owner was lost | Home is a branch-local landing; Back restores a workspace; Next carries position and total as numbers; the list got its own step-back chip | `tests/test_navigation.py` (20), 4 golden scenarios, 11 browser checks |
| D-11 | Eight rail actions rendered, none used | At most two primary chips by context; the rest behind one control; every disabled chip says why | `tests/test_email_workspace.py` (34) |
| D-12 | Cards far taller than the screen, controls under the dock | Deck ends where the dock begins; thread 1,488→640 px, order list 933→665 px, worst order 633 px | `tests/test_density.py` (39 checks), `scripts/browser/collision.js` (26 checks, 21 fixtures, 7 rules, both viewports) |
| D-13 | Duplicate reads inside one turn | Read dedupe: 66 requests avoided of 139 across all 55 scenarios | `tests/test_read_dedupe.py` (15) |
| D-14 | A status aside hijacked the request | `asked` signal (question OR listing); clause splitting on sentences only | `tests/test_multi_intent.py` (6) |
| D-15 | A card type the tablet could not draw | A read that found nothing draws a card saying so; an unknown type is dropped loudly | `tests/test_progressive.py` |

Two further defects were found by this pass rather than by the owner, both of the same class —
a name that silently meant something else — and both in the path D-1 lives in:

- the duplicate `replaceCard` above;
- `web/ui.js`'s `h()` dropped a null *attribute* but stringified a null *dataset value*, so
  `{ ref: staged ? text(ref) : null }` wrote `data-ref="null"`. The moment "open" chips
  existed it wrote `data-command="null"`, and **every rail chip on every card** posted the
  command `"null"` and took a 400.

And one that had been costing time silently for two phases: `scripts/bench_lanes.py` freezes
the clock the analytic tools read, using a shim written for pytest's `monkeypatch` but without
its undo. Run in-process by a test, it left that clock behind, so every later harness read of
"today's orders" came back empty three files down the suite. Two separate workstreams hit it
and worked around it. It is fixed at the source, with a test that fails on the old bench.

---

## 4 · LIVE DEFECTS NOT FIXED

| What | Why | Where it goes |
|------|-----|---------------|
| A verified Gmail archive cannot be driven to VERIFIED in the fixture world | `experience/fixtures/gmail.py` refuses every mailbox write by design. The browser run drives the real path to its terminal answer with only the commit response stubbed, in the exact shape `app/presentation.py` produces | Needs a live Gmail token to prove end to end; the Samsung acceptance script step 7 covers it by hand |
| After a verified archive the Mac does not re-read the needs-reply queue | The tablet removes the row from every copy it holds; the Mac-side invalidation of that read is not exercised by the fixture world | Next pass, with a live token |
| A record opened by a Claude turn is not pushed onto the branch trail | Pre-existing. The fix is one hook, but it would start setting `branch.entity` from model turns — a wide blast radius that belongs with the context-stack work, not with navigation | Next pass |
| Two concurrent `commerce_query` calls still make two requests | They publish a working set; serving the second from the first would skip the set a listing needs to be navigable. Their duplicates are caught at the plan layer instead | Accepted, documented in `app/reads/dedupe.py` |
| Tracking numbers and SKUs have no typing path | `FIELD_KINDS` has `tracking` and `variant` and no family uses them; fulfilment belongs to the commerce families | Next pass |
| Scroll restoration is best-effort | The tablet reports depth on a 1.5 s debounce, so open-then-back inside that window restores a slightly stale depth | Accepted |
| `app/observability/report.py` does not yet surface the four glass timings or `renders{}` | They are published on `turn_performance` for it to read; the file was one agent's territory this pass | Next pass |

---

## 5 · ACTION STATE RESULTS

The UI state machine is explicit and finite: READY → STAGED → ARMING → ARMED → EXECUTING →
VERIFYING → VERIFIED, with FAILED, EXPIRED and UNDONE as the other terminals. VERIFIED, FAILED,
EXPIRED and UNDONE are terminal and nothing leaves them.

- A watchdog moves any card that has been in a non-terminal state past its deadline, so no
  surface can sit mid-flight whatever the network does.
- `executed` no longer maps to done in the UI. **Only `verified` does.** Success means
  verified and nothing less, on the glass as on the Mac.
- A commit whose answer never returns recovers by asking the Mac, which is the only party
  that knows.
- 12 Chromium checks drive the machine through every transition including the one the owner
  watched get stuck.

`crooks-watch`, replayed over the real hour, prints
`UI action prop_037e20c6ea04 stuck EXECUTING after server VERIFIED` at 00:21:55 — four turns
before the owner first asked what was wrong.

## 6 · SPLIT RESULTS

Branch-local: `branch_id`, navigation stack, entity, set and cursor, tab, scroll, expanded
rows, visible workspace, area, headline, task, in-flight count, state, composer, voice
context, recent actions, resolutions, recent entities. Proposals stay bound to the branch that
staged them.

Five states, each a fact: ACTIVE, WORKING, WAITING, READY, FAILED. WORKING counts turns
actually in flight, so a turn that dies no longer leaves a half working for ever. No
percentages anywhere — nothing a half says about itself is a number out of a number.

A background half may READ and may STAGE. It can never APPLY: `tests/test_split.py::
test_a_half_put_aside_may_read_and_stage_and_can_never_apply` drives the real boundary on a
real app and asserts the mutation store is **empty** after both `arm` and `commit` are refused
409 `branch_not_focused`, then brings the half back and applies the same card, proving it was
the aside that was refused and not the change.

## 7 · NAVIGATION RESULTS

| Control | What it means now |
|---------|-------------------|
| Home | This half's landing AREA, branch-local, identical on the eighth press as on the first. Never a held entity. |
| Back | The previous WORKSPACE: entity, tab, scroll depth, expanded rows, set with cursor and total, dock area, and the record it was reached from. A stop whose cards no cache can rebuild is read again. |
| Next / Previous | Arithmetic over the current set and cursor, refusing with `no_set` when no list is open. `position` and `total` travel as numbers, so the chip draws "3 of 10" without parsing prose. |

Eleven operations are deterministic and reach the Mac with **zero model calls**:
`navigation.back`, `navigation.forward`, `navigation.home`, `workflow.next`,
`workflow.previous`, `surface.tab`, `surface.expand`, `surface.scroll`, `open.entity`,
`branch.show`, `POST /branches/{id}/focus`.

## 8 · COLLISION RESULTS

Real DOM geometry, `getBoundingClientRect` on every rectangle, 21 stress fixtures, 7 rules,
both viewports — because the old telemetry reported `clipped=0` while the owner was looking at
overlapping controls.

| | 601 × 889 | 800 × 1280 |
|---|---|---|
| Fixtures driven | 21 | 21 |
| Rules | 7 | 7 |
| Overlaps now | **0** | **0** |
| Targets under 44 px now | **0** | **0** |

The before-figure is the one the collision workstream measured while building this: **9 of 15
fixtures** hit at 601 × 889, every one of them a control sitting in the dock band where `#talk`
takes the tap as speech. It is quoted rather than re-measured, because the measurement needs
`web/collide.js`, which did not exist on the old tree — which is the point: nothing could see
this before the instrument existed.

The telemetry now records real `collisions.{total, by_rule, worst, small_targets, measured}`,
with `null` for "not measured" and never a silent zero, and the gate asserts that the number
the page reports equals the number it has just measured itself.

## 9 · DENSITY (D-12)

Visible deck at 601 × 889: **559 px** (was reported as 671 before the deck stopped scrolling
under the dock). Ceiling is a screen and a quarter: **699 px**.

| Surface | Before | After |
|---------|--------|-------|
| Worst email thread | 1,488 px | **640 px** |
| Worst order list | 933 px | **665 px** |
| Worst order | 757 px | **633 px** |

The worst order needed two folds, and the second was found by measuring rather than guessing:
169 px of the card was one 308-character note read in full. A clamp with a "More" button was
tried first and saved nothing — the 44 px the control needs for a thumb is exactly what the
clamp gives back — so a note longer than four lines goes behind one control, and an item tail
past five rows does the same. That failed attempt is in the comment, so the next person does
not repeat it.

## 10 · PERFORMANCE BEFORE / AFTER

| Measure | Before | After |
|---------|--------|-------|
| Time to shell (first card on the glass) | — (nothing until the turn finished; `turn_c8eb4cffe077` waited 7,975 ms) | **0.0 ms** |
| Time to first fact | 7,975 ms observed | **2.5 ms** |
| Time to first useful workspace | = time to final prose | **2.5 ms** |
| Time to complete workspace | — | **210.3 ms** (with a deliberately slow 500 ms customer read) |
| Duplicate reads across 55 scenarios | 0 avoided | **66 avoided of 139 served (47%)** |
| Provider calls saved | 0 | **66** |
| Renders drawn vs suppressed, one live turn | 7 drawn | **4 drawn, 3 suppressed** |
| 24 identical thread renders | 24 drawn | **1 drawn, 23 suppressed** |

The milliseconds saved by dedupe are small against the fixture shop, which answers instantly.
Against the real store — where the live session measured **17,302 ms** of reading — each
avoided request is 150–400 ms.

## 11 · TOOL MATRIX

`docs/phase4/TOOL_MATRIX.md`: 48 tools and 40 intent families, audited from the registries
themselves rather than from a list someone maintained by hand, and asserted against the
checked-in document by `tests/test_tool_matrix.py` (which spawns a fresh interpreter, because
several existing tests register a tool and never remove it).

The DIRECTLY TESTED and GOLDEN SCENARIO columns are citations, not execution traces: a test
that exercises a tool without naming it is reported as not naming it. That is stated in the
document.

## 12 · CLICK-PATH MATRIX

Every path below is driven end to end — a real tap, a real command, a real answer, asserted on
the screen rather than on the HTTP code.

| Path | Where it is driven |
|------|--------------------|
| Orders → an order → Customer tab → a prior order → Back → Back | `tests/test_navigation.py`, `nav_click_path` scenario, `experience.js` |
| Home from a deep record, three times running | `nav_home_landing` scenario |
| Next through ten orders reporting 1..3 of 10 | `nav_next_position` scenario |
| Back on one half leaves the other untouched | `nav_branch_isolation` scenario |
| Split → second half → back → retrieve a finished aside | `split.js`, both viewports |
| Thread → Reply → type the body → stage → gesture → verified → back on the thread | `email.js`, 49 checks |
| Order → Email chip → composer; Order → Address chip → address workspace | `email.js` |
| Stage → arm → commit → verify → undo → dismiss | `action_state.js` |
| A blocked proposal; an expiring card; a recovered commit | `action_state.js`, `accept.js` |
| Dock landing after a read-heavy turn | `tests/test_read_budget.py` |

## 13 · SCREENSHOT INDEX

`docs/screens/phase4/` — 31 pictures with an index in `docs/screens/phase4/README.md`, all
taken by the gates themselves so every one is a screen a check has just asserted on. Both
viewports throughout. A re-run writes 96; the 31 kept are the ones worth carrying in git.

## 14 · TEST COUNTS

| Suite | Phase 3 end | Phase 4 end |
|-------|-------------|-------------|
| Python | 2,040 passed, 2 skipped | **2,399 passed, 2 skipped** |
| Node (`tests/web/*.test.js`) | 131 | **203** |
| Chromium checks in the gate | 61 | **227** |
| Browser scripts in the default gate | 2 | **7** |

The two permanent skips are unchanged and are environment, not code:
`tests/test_gmail_tools.py:175` (no Gmail token here) and `tests/test_shopify_tools.py:190`
(no Shopify Keychain entry here).

**Test-quality note.** Three tests were changed rather than added, and each is justified in
place: the `replaceCard` assertion (it read the body of a declaration the browser never ran),
the command-delegate assertion (it asserted the guard flag that caused the bug), and one
operations test. No test was weakened to accept broken behaviour.

## 15 · KNOWN LIMITATIONS

- Everything above is proved against the golden fixture world and Chromium on this machine.
  No Shopify or Gmail write was performed anywhere in this pass.
- `make accept`'s 23 Chromium checks had never run in the suite's gate before this pass. They
  are in it now. They were the only check anywhere that had seen the duplicate `replaceCard`.
- The progressive channel is the existing 400 ms `/state` poll, so the shell reaches the glass
  within a poll even though the Mac's own `time_to_shell` is 0.0 ms. A push channel would
  close that gap.
- `TOOL_MATRIX.md` is checked in and asserted, so it goes stale whenever a family is added;
  `make tool-matrix` regenerates it.

## 16 · SCOPES STILL NEEDED

None newly. The pass needed no scope it did not already have, and asked for none.

For the record, what remains ungranted from earlier phases is unchanged: nothing in this build
requires a scope the owner has not already approved, and the two skipped tests need a token
and a Keychain entry on the Mac rather than a new permission.

**No Anthropic PAYG API key was introduced.** Voice, TTS, Shopify and Gmail configuration is
untouched: Derek (`Q0Et7LOU7VpeoeCRQAVS`), `eleven_flash_v2_5`, `5wn03t-nm.myshopify.com`,
`team@crooksldn.com`.

## 17 · INVARIANTS

All twenty action-engine invariants hold. `app/actions/engine.py` was not modified in this
pass; the work around it was the UI's representation of what the engine says, which is where
the defects were. Specifically:

- the model still proposes and never authorises, and a spoken yes still authorises nothing;
- a gesture still posts a proposal id and a session id and never a mutation argument;
- a precondition is still re-read before a write and verification is still a deterministic
  authoritative re-read;
- **success still means VERIFIED**, and the UI now agrees — that change is in this pass;
- the service worker still never caches, replays or syncs a write;
- background work may read and may stage; it may never commit. There is a test that drives
  that boundary against a real mutation store and asserts the store is empty.

## 18 · PHYSICAL SAMSUNG TEST SCRIPT

`docs/phase4/PHYSICAL_SAMSUNG_ACCEPTANCE.md` — eleven steps, 17–27 minutes, each tied to the live
defect it re-tests. Two of the steps test the system by testing the owner rather than the
screen: step 6 asks him to find the typing path **without being told where it is** ("Find it
without being told. That is the test."), and step 9 asks him to say a defect out loud and then
check that the report carries his words verbatim.

---

## 19 · COMPLETION GATES

| Gate | Result |
|------|--------|
| Full Python suite green | ✅ 2,399 passed, 2 skipped |
| JS / web suites green | ✅ 203 node tests, `node --check` clean on every script |
| Lint green | ✅ ruff, all checks passed |
| Browser checks green | ✅ 227 checks, 0 failed |
| Golden experience scenarios green | ✅ 59 scenarios |
| 601 × 889 collision suite green | ✅ |
| 800 × 1280 collision suite green | ✅ |
| Action terminal-state suite green | ✅ |
| Branch isolation suite green | ✅ |
| Navigation semantics suite green | ✅ |
| Owner-feedback test green | ✅ |
| Tool matrix report complete | ✅ `docs/phase4/TOOL_MATRIX.md` |
| No known P0 | ✅ |
| No fake enabled controls | ✅ every control works, is visibly disabled with a reason, or no longer looks like a control |
| Working tree clean | ✅ |
| Branch pushed | ✅ |
| Suite re-run from clean HEAD | ✅ |

**DEPLOYED: NO.** Production is untouched, as instructed.
