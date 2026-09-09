# The engineering loop: from an hour on the tablet to a change the owner approves

CROOKS OS improves from evidence, never from itself. The production assistant on the Mac
answers the owner and changes nothing about its own code. What it does leave behind is a
timeline of everything it did during a test session, and that timeline is where every
improvement starts.

## The loop

```
  1. observe      make test-session-start / stop      logs/test-sessions/<id>.jsonl
  2. read back    make test-session-report            reports/<id>.md   (13 sections, counted, never scored)
  3. candidates   make test-session-proposals         reports/<id>-proposals.md  (IMPROVEMENT CANDIDATES, each with its turn ids)
  4. propose      the owner picks candidates to pursue and hands them to an engineering agent
  5. build        the engineering agent works on a DEVELOPMENT branch, never on the branch the Mac runs
  6. prove        pytest, the Node renderer tests, ruff, `make accept` (Chromium), and a mocked test session
  7. review       a security review of the diff: the gate, the write boundary, the ledger, the prompt, PII
  8. summarise    a plain summary: what changed, which turn ids it answers, what was not done, what to watch
  9. approve      the owner reads the summary and merges; the Mac is updated by the owner, deliberately
```

Steps 1–3 are deterministic scripts a person runs on the Mac (`make` targets); nothing
starts them by itself. Steps 4–9 involve a person at every gate that matters: choosing what
to build, and deciding what runs.

## What a candidate is

An IMPROVEMENT CANDIDATE is a proposal, not a change. It is written from the report by the
same deterministic rules that write the report, and every one cites the turns it comes from:

- the problem, in one line, and the class it was filed under
- the evidence: turn ids, what the owner said, what the assistant answered, what was tried
- the component it most likely lives in (a file or a module)
- the change proposed, in words a developer can start from
- the tests that would prove it, named before the code is written
- the risk, and which invariant it must not touch

Candidates come from: false unsupported claims (the assistant said it could not, and the
read layer or a batch tool could have); composable requests that failed; requested query
dimensions the language does not have yet; capabilities asked for that are not built; bulk
workflows asked for that have no batch; multi-tool workflows repeated often enough to
deserve one call; follow-up shapes repeated often enough to deserve a shortcut; UI types the
tablet could not draw; and the failure classes, slowness and dead chips the report already
counts.

## What is never automatic

- **The production branch is never modified while servicing the owner.** The assistant
  the owner talks to has no tool that edits, commits, deploys or restarts anything: no such
  tool is registered, the gate denies any tool that is not registered, and any name that
  reads as a mutation is denied unless it carries a reviewed write definition. Nothing in
  the timeline, the report or the proposals file can execute.
- **No candidate is applied by the thing that generated it.** The proposals file is read by
  a person. An engineering agent, when one is used, is given a candidate by the owner and
  works on a development branch under the same rules as any contributor: tests, review,
  summary, approval.
- **A candidate never widens the write boundary.** A new action is a new reviewed mutation on
  the action engine, with a fresh read, a precondition, an at-most-once claim, a proving
  re-read and a ledger line — and it ships behind the same switches (CROOKS_WRITES_ENABLED,
  the allow-list, the store's scopes). A new bulk action is a batch over such a mutation.
  A new read is a query the language validates and bounds. None of that is decided by a
  report.
- **Nothing private travels.** The timeline and the report hold what the owner said about
  customers, and are created 0600 and never committed. A candidate quotes a turn by id and
  by the owner's words as the report already bounded them; it carries no customer detail
  beyond what the owner said aloud.

## Where the pieces are

| Step | Code |
| --- | --- |
| the timeline | `app/observability/timeline.py`, `app/observability/hooks.py`, `web/telemetry.js` |
| the report | `app/observability/report.py` (`make test-session-report`) |
| the claims rule | `app/observability/claims.py` — what the Mac composes, by the words of a question |
| the candidates | `app/observability/proposals.py` (`make test-session-proposals`) |
| the invariants a change must keep | `app/tools/gate.py`, `app/actions/engine.py`, `app/actions/batch.py`, `app/presentation.py` |
| the proofs a change must pass | `make accept`, `tests/`, `tests/web/` |
