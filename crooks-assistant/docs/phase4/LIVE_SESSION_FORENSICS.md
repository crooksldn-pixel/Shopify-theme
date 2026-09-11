# Phase 4 — forensics of the live tablet session

Session `ts-20260911-001845-phase-3c-live-tablet-tes`, 00:18:45–00:28:44, 9 min 59 s, 14 turns,
700 events, 405 of them from the tablet. Reconstructed from the **raw JSONL**, which is
authoritative; the generated report is cited only where it agrees.

The raw timeline holds real customer names and three real email addresses. It stays in
`logs/`, which is gitignored. **Nothing in this document names a customer**: people appear as
"the customer on order X" and addresses do not appear at all. Ids, counts, milliseconds and
the owner's own words are what a forensic record needs.

## How to read this

The generated report called this session **11 successful, 2 partial, 1 failed**. Judged by what
the owner could see and do, it was closer to the opposite. That gap is the subject of this
document, and it is the single most important finding: **the analyser scores the backend, and
the owner lives in the UI.**

Every defect below has evidence from the timeline, a root cause read from the code, what the
owner saw, what it means for the system, the fix, and the test that must fail before the fix
and pass after.

---

## The session, as the owner lived it

| # | Turn | The owner said | What came back | Verdict |
| --- | --- | --- | --- | --- |
| 1 | `turn_26db2bafe507` | "I restarted you. Are you okay now? Can you pull up the today's emails" | "Since the last build — 8 new things I can look up…" | **D-14** the emails never came |
| 2 | `turn_7462fe7a4bc0` | "Draft a reply email to [customer] giving out the return address…" | Draft staged, verified | worked (13,976 ms) |
| 3 | `turn_49d445f24ee2` | "Okay, how do we send?" | Send staged, held, **VERIFIED** | backend worked |
| 4 | `turn_b9c757f271ff` | **"Why, why has the email actually sent but the applying button is still going?"** | "It's sent" | **D-1** |
| 5 | `turn_bce8185f7946` | **"Yes, but your applying button was just stuck hovering"** | "That's just the tablet's screen" | **D-1** again |
| 6 | `turn_c631d4a1c431` | (a product list read aloud) | "I didn't catch a question there" | **D-9** precision |
| 7 | `turn_6168f7b94fe9` | **"What does the split button do?"** | **"I don't know what that button is… best to check with whoever built the tablet screen."** | **D-6** |
| 8 | `turn_d3abd8737886` | "How do I type a separate hall for you?" | "that didn't come through clearly" | **D-9** |
| 9 | `turn_c8eb4cffe077` | "Look up today's orders and today's emails and see if anything correlates" | one 7,975 ms dump | **D-5** |
| 10 | `turn_7afa465dda1d` | **"please log that your split function is broken. It just shows two of the same thing, and the applying button is also broken"** | **"I've no tool for logging a product bug like that."** | **D-7** |
| 11 | `turn_69abe877ef14` | "can you pull up today's, uh, yesterday's orders, please?" | **"No orders today."** | **D-8** |
| 12 | `turn_6089e7517986` | "Pull up yesterday's orders, please" | "10 orders yesterday" — and 3 tool refusals | **D-4** |
| 13 | `turn_fbe11cfedd53` | (sales) | worked | worked |
| 14 | `turn_000ee896c082` | **"Log--a lot of your functions are broken… especially with the back button, back to assistant button and the next button"** | **"I still have no tool that logs product feedback"** | **D-7** again |

The owner reported four defects out loud, twice each. The system told him twice it had no way
to record them, and the report that came out of the session did not contain them.

---

## D-1 · P0 · A verified send left the button saying "Applying…" for ever

### Evidence

```
00:21:51  action_executing   prop_037e20c6ea04  gmail_send_reply
00:21:52  action_executed    prop_037e20c6ea04
00:21:53  action_verified    prop_037e20c6ea04        ← the Mac proved it
00:21:55  tablet_action_commit  status=verified code=verified ms=1756 detail=200
                                                      ← the TABLET was told, and knew
00:22:22  tablet_reconcile   reason=turn count=2 kept=2   (turn_b9c757f271ff)
00:22:32  tablet_reconcile   reason=turn count=2 kept=2
00:22:47  tablet_reconcile   reason=turn count=2 kept=2
00:22:59  tablet_reconcile   reason=turn count=2 kept=2
00:23:15  tablet_reconcile   reason=turn count=2 kept=2
00:23:38  tablet_reconcile   reason=turn count=2 kept=2
```

Six consecutive reconciles, every one finding the same two proposals already settled on the
Mac, every one changing nothing on screen. **The tablet's own telemetry recorded this bug once
per turn for six turns and no one read it** — the field is even named `kept`.

### Root cause

`web/app.js::settleProposals`:

```js
if (current === 'arming' || current === 'armed') node.settle(state, label);
```

and `web/ui.js`, where committing sets the visible state:

```js
const commit = () => { committed = true; setState('committing'); say('Applying…'); … }
```

A card that has been committed is in state **`committing`** — which is exactly the state that
says "Applying…". The guard settles `arming` and `armed` and nothing else, so **the one state
that can be stuck is the one state reconcile refuses to touch.** The guard was written to stop
a background correction stealing a card mid-gesture; it was applied one state too wide.

`liveProposalIds()` compounds it: it treats anything not `done`/`failed`/`settled` as live, so
the stuck card is re-submitted to every future reconcile — for ever, at one HTTP round trip per
turn.

### Visible consequence

The owner watched a spinner on a send that had already gone out, asked about it twice, and was
told "that's just the tablet's screen". He was right and the machine was wrong.

### System consequence

The UI is not a projection of action state; it is a second, divergent copy. Any commit whose
own response is lost — a dropped connection, a backgrounded tab, a re-render — is unrecoverable
by design, because the only path that could repair it is gated on a state it can never be in.

### Fix

A single finite state machine with explicit terminal states (READY, STAGED, ARMING, ARMED,
EXECUTING, VERIFYING, VERIFIED, FAILED, EXPIRED, UNDONE); the server's terminal status is
authoritative and settles from **any** non-terminal state; a watchdog asserts no surface stays
EXECUTING after its proposal reached a terminal state.

### Regression test

Drive a commit in Chromium, let it reach `committing`, answer the commit request with a
verified state, and assert the surface is no longer "Applying…" — plus a unit test that
`settleProposals` settles from `committing`, which fails on today's guard.

---

## D-2 · P0 · A pending Undo counts as "changes still waiting"

### Evidence

```
00:21:35  action_proposed  prop_2d39c24040cd  gmail_draft_reply_undo   → PENDING for ever
00:23:50  action_proposed  prop_0e24a4b8c57e  gmail_thread_archive_undo → PENDING for ever
00:24:53  tablet_toast     "Merged. 2 changes still waiting over there."
```

The two "changes still waiting" at merge are the two **undo** offers for changes that had
already completed successfully.

### Root cause

Undo proposals are staged as ordinary pending proposals and counted by everything that counts
pending proposals. Availability of an undo is being modelled as unfinished work.

### Visible consequence

A merge that should have read "Merged" warned the owner that two changes were outstanding.
Nothing was outstanding.

### System consequence / fix / test

Undo is a property of a completed action, not a queued one. Separate `pending` from
`undoable`, give undo its own TTL and dismissal, and exclude it from every "still waiting"
count. Test: archive a thread, merge, and assert the toast says nothing is waiting.

---

## D-3 · P0 · Split produced two identical screens

### Evidence

```
00:23:01  branch_forked   br_29a02563cf
00:23:57  branch_focused  br_29a02563cf
00:23:59  branch_focused  br_dfceb6b219
00:24:00  branch_focused  br_29a02563cf
00:24:02  branch_focused  br_dfceb6b219
00:24:04  branch_focused  br_29a02563cf      ← six focus changes in nine seconds
00:25:48  open.area    ok=False  code=landing_unavailable   br_29a02563cf
00:25:53  open.entity  ok=False  code=not_held              br_29a02563cf
```

The report's own branch table: *"focus changed with nothing redrawn"* — four times. The owner:
*"It just so shows two of the same thing"* and *"the split function doesn't work at all"*.

### Root cause

A fork clones context and the halves have no independent navigation state, so both halves draw
the same card; `open.area` on the forked half is refused `landing_unavailable` and `open.entity`
`not_held`, because the clone never received the entities its parent held.

### Visible consequence

The owner tapped between two identical screens six times to find the difference, then said the
feature does not work.

### Fix / test

Branch-local navigation stack, entity, set, cursor, workspace and status; an unmistakable
per-half header; a redraw on focus; and the forked half either inherits what it needs or says
plainly that it holds nothing. Test: fork, ask each half a different question, assert the
visible cards differ and that focus redraws.

---

## D-4 · P0 · The owner's own read was refused because an earlier turn had read too much

### Evidence

```
turn_6089e7517986  commerce_aggregate  REFUSED: this turn has been reading for too long;
                                       answer from what has been read.      ×3
```

Two turns earlier, `open.area` was refused `landing_unavailable` (00:25:48).

### Root cause

One read budget is shared by speculation, hydration and the owner's foreground request, and it
is scoped to a long-lived turn. A turn that has been reading — including reads nobody asked for
— can refuse the next thing the owner actually wants.

### Visible consequence

"Pull up yesterday's orders" answered from partial data, and a dock landing simply refused.

### System consequence

Anticipation, added to make the product feel faster, can make it refuse work. That inverts the
whole point.

### Fix / test

Separate budgets with strict priority — foreground read > navigation hydration > mutation
precondition > branch background > speculation — and speculation yields immediately. Test: run
speculation to its cap, then issue a foreground dock command, and assert it is served.

---

## D-5 · P0 · Nothing appeared until everything was ready

### Evidence

`turn_c8eb4cffe077` ("today's orders + today's emails + correlate"): 7,975 ms to first cards,
`shopify_list_orders` → `gmail_search` → `gmail_read_thread` → … all before anything was drawn.
Session-wide, the report measures **17,302 ms reading against 13,388 ms waiting**.

### Root cause

The workspace is presented once, after the whole read graph resolves.

### Fix / test

Progressive hydration: a shell, then facts patched in place as each read lands, with
`time_to_shell`, `time_to_first_fact`, `time_to_first_useful_workspace` and
`time_to_complete_workspace` instrumented. Test: assert a useful card exists well before the
final one, and that patching does not reset scroll or focus.

---

## D-6 · P0 · The assistant disclaimed its own interface

### Evidence

> "What does the split button do?"
> **"I don't know what that button is — not something I control, so best to check with whoever
> built the tablet screen."**

### Root cause

No manifest of first-party UI semantics. The model is told what tools it has and nothing about
the screen it is speaking through.

### Visible consequence

The product denied knowledge of its own primary control, and referred its owner to himself.

### Fix / test

A bounded UI semantics manifest — Split, Back, Home, Next, Aside, Merge, dock destinations,
approval gestures, composer modes, branch states — reachable by a read family. Not a licence to
generate UI; product self-knowledge. Test: the five questions in §15 of the brief get correct
answers.

---

## D-7 · P0 · The owner reported four defects and the system had nowhere to put them

### Evidence

Turn 10: "please log that your split function is broken… the applying button is also broken" →
"I've no tool for logging a product bug like that."
Turn 14: "Log--a lot of your functions are broken… especially with the back button, back to
assistant button and the next button" → "I still have no tool that logs product feedback."

The generated report's "Potential new actions" section: **_none_**.

### Root cause

No owner-feedback event, and the analyser's "what was asked for" detection reads tool calls,
so a request that never reaches a tool is invisible to it.

### Visible consequence

The owner did the most valuable thing a tester can do — narrate defects as they happen — and
the machine discarded all of it, twice, then produced a report that did not mention them.

### Fix / test

An `owner_feedback` timeline event during a test session, recognised from "log that…", "note
this bug…", "this is broken…"; local only, no mutation approval, no Shopify or Gmail; surfaced
verbatim in the report under OWNER-REPORTED DEFECTS. Test: say it during an active session and
assert the event and the report section.

---

## D-8 · P1 · "today's — uh — yesterday's orders" was answered for today

### Evidence

```
turn_69abe877ef14  "can you pull up today's, uh, yesterday's orders, please?"  → "No orders today."
turn_6089e7517986  "Pull up yesterday's orders, please"                        → "10 orders yesterday"
```

The report notes the repeat at 72% word overlap and does not call it a defect.

### Root cause

The period extractor takes the first temporal phrase; ordinary spoken self-correction
("today's, uh, yesterday's") is not modelled.

### Fix / test

A correction rule: a later explicit temporal phrase separated by a hesitation marker replaces
an earlier one. Tests for today→yesterday, this week→last week, 1956→1957, medium→large — and
for the cases where the later noun must NOT win.

---

## D-9 · P1 · Precision had no keyboard

### Evidence

Four `tablet_recording_too_short` events (142 ms, 41 ms, 55 ms, 92 ms); the normaliser had to
repair two transcripts; turn 6 was a product list read aloud and answered "I didn't catch a
question"; turn 8 asked how to type and was not understood.

### Root cause / fix / test

The composer has fields, but nothing tells the owner they exist and no other surface offers
one. Every exact value — address, SKU, code, quantity, email — needs a visible typing path.
Test: each precision field is reachable by touch and keeps focus and content through a
background enrichment.

---

## D-10 · P1 · Navigation answered ok=true while the owner was lost

### Evidence

```
00:20:20 … 00:20:42   navigation.home ×8, navigation.back ×4, all ok=True
```

Eight Homes and four Backs in twenty-two seconds. The report's command table shows 12 Home and
6 Back, **100 % accepted**. Turn 14: "especially with the back button, back to assistant button
and the next button".

### Root cause

Home replays the last held entity rather than a branch landing; Back pops a history of renders
rather than restoring a workspace (entity + set + tab + branch + position); Next is not
distinguished from Back over a working set. All three return `ok=true` for doing something,
which is not the same as doing the right thing.

### Visible consequence

The owner hammered Home eight times looking for a landing and never reached one.

### Fix / test

Home → the branch's landing workspace, never a replayed entity. Back → the exact prior
workspace. Next → the current set's cursor, with a visible "3 of 10". Branch stacks isolated.
Tests assert the restored workspace, not the HTTP code.

---

## D-11 · P2 · Eight rail actions rendered, none ever used

Rail actions exposed enabled: reply ×24, email_archive ×24, note ×5, refund ×3, email ×3,
fulfil ×2, address ×2, cancel ×2. **Used: none.** Either they do not read as the thing the owner
wanted, or they do not deserve the space. Both are UI defects; §22 of the brief says prioritise
by entity state and give every disabled action a concise reason.

## D-12 · P2 · Cards far taller than the screen

38 long-scroll surfaces, up to **1,999 px against a 680 px viewport**; deepest scroll 2,014 px.
At 601 × 889 the first viewport must answer what am I looking at, what matters, what can I do.

## D-13 · P2 · Duplicate reads inside one turn

`turn_26db2bafe507`: `commerce_query` and `gmail_search` twice each.
`turn_6089e7517986`: `gmail_search` and `shopify_order_detail` twice each.
24 `email_thread` renders across 14 turns, five identical `order` renders.

## D-14 · P1 · A status aside hijacked the actual request

Turn 1 asked two things: "are you okay?" and "pull up today's emails". The answer was the
capability delta and no emails. Explicit requested work must outrank contextual status.

## D-15 · P2 · A card type the tablet could not draw

`turn_69abe877ef14` produced records with no card ("(records without a card)"). Either the type
joins the vocabulary on both sides with a bounded shape, or the presentation layer stops
emitting it.

---

## What the analyser must learn from this

The report said 11 of 14 turns were successful. The owner said, out loud, during the session,
that the split was broken, the applying button was broken, and Back, Back-to-assistant and Next
had regressed. A report can be internally consistent and still be wrong about the only thing
that matters.

The analyser needs to report two outcomes per turn — **system outcome** and **owner-visible
outcome** — and treat their disagreement as the defect it is:

```
gmail_send_reply:  backend = VERIFIED   visible = APPLYING_STUCK   experience = FAILED
```
