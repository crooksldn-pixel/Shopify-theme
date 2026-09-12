# The 11 September session, re-scored

`ts-20260911-201129-phase-4-live-tablet-test.jsonl` · 1,365 events · 44 turns · 40 tool calls ·
zero proposals. The same file, read twice: once by the analyser as it stood before this
workstream, once by the analyser as it stands after it. Nothing about the evening changed; only
what the machine can say about it.

No customer name, email address or order total appears in this document. Customer ids are
truncated to their last four digits where one is needed to prove two records are different.

---

## The headline

| | Before | After |
|---|---|---|
| **First improvement candidate** | "A value had to be exact and a voice could not make it so", severity 2, weight **124** | **CONTROL_TAP_MISROUTED_TO_VOICE**, severity 6, weight 30 |
| **Second** | STT_ERROR, severity 3, weight 27 | OWNER_FEEDBACK_IGNORED, severity 6, weight 24 |
| **Third** | UNFULFILLED_ACTION, severity 5, weight 15, component *"the write tools"* | WRONG_ENTITY_ANSWERED, severity 6, weight 6 |
| **Where speech ranks** | **2nd** | 8th |
| **"Precision input needed" table** | **62 rows** | 1 row |
| **Turns the owner would call successful** | 24 of 44 | 10 of 44 |

Three of the before-column entries are the three false diagnoses §21 was written about. Had
this pass followed them it would have tuned speech recognition, de-duplicated a renderer that
was not duplicating, and hunted a write tool that is not missing.

---

## By class

Counts are TURNS the class was filed against, which is what the ranking uses.

| Class | Before | After | Why it moved |
|---|---:|---:|---|
| `CONTROL_TAP_MISROUTED_TO_VOICE` | — | **5** | New. 47 taps in five bursts, the largest 26 in ten seconds with zero commands posted anywhere in it. One finding per burst. |
| `REAL_SHORT_VOICE_RECORDING` | — | 13 | New. What was left of "the recording was too short" once the taps and the gestures came out of it. |
| `GESTURE_COLLISION` | 2 | **9** | Every one of the 18 `multitouch` events lands 2–3 ms AFTER a release: the second finger ended the hold. Plus D-13's long empty holds, which sit inside tap bursts. |
| `STT_ERROR` | **9** | 4 | Five of the nine were recordings a finger had already ruined. The recogniser is not sent the bill for them. |
| `PRECISION_INPUT_REQUIRED` | (62 rows) | **1** | 61 of the 62 rows were short recordings. One real row remains: a transcript the normaliser had to correct. |
| `DUPLICATE_RENDER` | 3 | **2** | `turn_be1b384ca420` was seven DIFFERENT customers and is no longer this class. `turn_1e7f630eae7e` was two telemetry frames 11 ms apart — one paint, not a redraw. The redraw storm on `turn_f0628fcf7be5` (131–982 ms between frames) stays. |
| `SUMMARY_ANSWERED_WITH_PROFILES` | — | **1** | New, and it is what `turn_be1b384ca420` actually was: a one-line question answered with seven 265 px profile pages. |
| `UNFULFILLED_ACTION` | **3** | 1 | Two were owner feedback recorded successfully. The one left is a turn that errored with nothing staged, which is the class doing its job. |
| `OWNER_FEEDBACK` | — | **8** | New, and not a defect. All eight of the evening's `owner_feedback` records, which the old classifier punished. |
| `OWNER_FEEDBACK_IGNORED` | 0 | **4** | D-12. Four defects he stated plainly without the word "log" — "Logical error here. You just pulled up two […] screens for no reason", "why is there bullshit on the screen right now?" — that nothing recorded. |
| `UI_INTENT_UNFULFILLED` | 0 | **4** | D-5. Three attempts at a customer page in twenty seconds, escalating to "bring up a UI", plus "Pull up […]'s orders" with nothing but the context stack drawn. |
| `EMPTY_NOTIFICATION` | — | **11** | New. Eleven of the sixteen notifications carried no words at all. |
| `WRONG_ENTITY_ANSWERED` | — | **1** | D-14. He named one customer and it spoke another customer's order history at him as fact. |
| `COLLISION` | 3 | 1 | A second finger that ENDED a recording is now the sharper class; one that landed without ending anything is still this. |
| `FAKE_CONTROL` | 1 | 1 | Unchanged. |
| `NAV_SEMANTIC_MISMATCH` | 1 | 1 | Unchanged. |
| `PROGRESSIVE_RENDER_MISSING` | 1 | 1 | Unchanged. |
| `TOOL_SELECTION_ERROR` | 1 | 1 | Unchanged. |

---

## The session as a whole

| | Before | After |
|---|---|---|
| Findings the owner could see | 15 | 73 |
| Turns: successful / partial / failed *(backend rule)* | 29 / 1 / 14 | 27 / 2 / 15 |
| Turns as the OWNER lived them: SUCCESSFUL / PARTIAL / FAILED | **24** / 6 / 14 | **10** / 12 / 22 |
| Owner feedback recorded | 8 | 8 |
| Owner feedback the owner gave and nothing recorded | **0** | **4** |
| Report length | 48,682 chars | 59,922 chars |
| Rules that could not read the timeline | none | none |

The row that matters is the third. Twenty-four of forty-four turns were scored as things the
owner would call successes, in an evening whose second sitting contains not one business
question and ends with him asking whether the thing is working. Ten is the honest number, and
the difference is not severity inflation: it is 47 taps that did nothing, four defects he
reported that nothing wrote down, four requests for a screen that produced no screen, and one
answer about the wrong person.

The report grew by 23%, and the growth is in the two places that were empty: section 14's
reading of what each finger did, and section 16's evidence. The table that dominated it before
lost 61 of its 62 rows, and no class may now take more than four rows of the evidence table.

---

## What the re-score does NOT claim

- **Speech is still not exonerated by this document, and still not the priority.** Four turns
  remain STT_ERROR after the taps and gestures come out. §22 is right to wait: until touch
  ownership is fixed every speech measurement in this session is contaminated.
- **`CONTROL_TAP_MISROUTED_TO_VOICE` is inferred on four of its five findings.** The 11
  September file records `target: "dock"` for 131 of its 132 holds, so the class is read from
  duration, burst shape, the absence of any multitouch and the absence of any command — not
  from the pointer's owner, which did not exist yet. One burst is corroborated by the owner's
  own words. Workstream A's touch-ownership state machine retires the inference; until then the
  risk and its bounds are stated in `app/observability/touch.py`.
- **`SUMMARY_ANSWERED_WITH_PROFILES` is a finding, not a fix.** Workstream D owns the summary
  surfaces.
