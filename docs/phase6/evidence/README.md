# Raw evidence

Kept because §33 asks for it: *"preserve raw evidence"*. These are the unedited outputs, not
summaries of them. Where a number appears in a Phase 6 document, it came from a file here.

| file | what it is |
|---|---|
| `baseline_premerge.txt` | the full Phase 5 suite on the integration branch at 5d4ee5c — BEFORE any workstream was merged. The control measurement, so that any drift afterwards is attributable to the merge rather than argued about. `2814 passed, 2 skipped in 1017.91s`, exit 0. |

## On the traceback at the end of `baseline_premerge.txt`

`Exception ignored in: BaseSubprocessTransport.__del__ … RuntimeError: Event loop is closed`,
repeated. It is a garbage-collection-time teardown of the Chromium subprocess transport after
asyncio's loop has already closed, and it is printed **after** the summary line — so every test
had already reported before it appeared, and the process exited 0.

It is recorded rather than deleted because a traceback in an evidence file that nobody explains
is a traceback somebody will worry about later. It is cosmetic and it is not introduced by
Phase 6: the tree measured here is Phase 5's code plus documentation.
