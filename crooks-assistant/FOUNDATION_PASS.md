# CROOKS OS — the foundation pass

The change set is `a743c6c..HEAD`: ten commits, 75 files, ~8,000 lines added. Everything
below was measured or run; nothing is claimed that was not.

---

## 1. What changed, in one paragraph

CROOKS OS used to treat every sentence as a new problem for a language model. It now knows
where the conversation is, keeps what it has read, and has its own written-down procedure for
the questions a shop owner actually asks a tablet on a workbench. Those questions are answered
by the Mac, in milliseconds, with no model on the critical path. Claude is still the
intelligence — it answers everything the Mac is not certain about, and it alone proposes a
change — but it is no longer standing between the owner and "Next".

---

## 2. The architecture

**Lanes.** Every request is resolved to an intent (family, entities, confidence) from
structure rather than a phrase table, and routed to one of three lanes:

* **FAST** — the Mac's own procedure. Sixteen recipes, read-only and navigation-only.
* **NORMAL** — Claude, with a compact line saying where the conversation is.
* **DEEP** — work that outlives one answer: a sweep, two clauses, both sources at once.

A mutation verb leaves the lane before scoring. A family that is not clear of its runner-up by
a margin goes to Claude. A recipe that cannot honestly plan declines and the turn goes to
Claude. Being fast is never a reason to answer the wrong question.

**The pieces.**

| Module | What it is |
|---|---|
| `app/fastpath/intent.py` | the request as structure: signals, families, confidence, margin |
| `app/fastpath/lanes.py` | which lane, and why, in one clause |
| `app/fastpath/recipes.py` | the recipe contract, and the read-only assertion |
| `app/fastpath/library.py` | the sixteen recipes |
| `app/fastpath/runner.py` | resolve, plan, read, render, remember — or defer |
| `app/reads/scheduler.py` | a dependency graph: independent reads together, no write can be in one |
| `app/memory/store.py` | six tiers, each entry carrying source, age, query, watermark |
| `app/memory/coalesce.py` | the same read asked twice is made once |
| `app/memory/prefetch.py` | bounded, cancelable, read-only speculation |
| `app/capabilities/manifest.py` | what this build can do, generated from the registries |
| `app/capabilities/delta.py` | what it can do that the last build could not |
| `app/session/branch.py` | where the conversation is: entity, set, cursor, back stack, tab, scroll |
| `app/routes/branches.py` | fork, focus, background, merge, cancel, mark, back, forward |
| `app/actions/rows.py` | the buttons a row may carry, and how a tap becomes a staged change |
| `app/observability/contract.py` | what a request was FOR, and the limitations stated rather than invented |

---

## 3. Files changed

Ten commits, each self-contained and green. `git log --oneline a743c6c..HEAD`:

```
48489b4 A half put aside says what it is doing
3bda05b While it reads, it says what it is reading
a3f710a The brief's acceptance scenarios, as tests over the real endpoint
41bd70d A card is settled by the Mac, or not at all
0bcf895 Measured, not claimed: the lane bench and what the session proposes about itself
d04361a The screen: one screenful at a time, buttons where the owner asked for them
304f0c2 Action state the Mac owns, and the orb divided
e726b7c Three words on the PATH, and the count that said zero
ace5813 The nine things the September session got wrong
1fcbe44 Execution lanes: the Mac's own procedures, with no model on the critical path
```

---

## 4. The recipes

Sixteen, each with declared reads, declared parallel waves, a preferred card, a cache policy,
a confidence floor and a latency target the bench fails on.

`capability_summary`, `capability_delta`, `navigation_back`, `navigation_home`,
`working_set_next`, `working_set_previous`, `order_lookup`, `order_status_lookup`,
`order_address_lookup`, `customer_purchase_lookup`, `best_sellers_period`,
`sales_breakdown_period`, `delayed_orders`, `stock_cover_analysis`, `inbox_state`,
`needs_reply`.

---

## 5. The orb, divided

Two halves at most. They share the read caches, the source clients and the issued-id ledger —
they are one conversation and one login. They share nothing that is a position or an approval.

* A change carries the branch that staged it.
* A merge brings back a structured summary of what the other half found, moves no proposal,
  and approves nothing.
* A half put aside cannot commit; a half with a change waiting refuses to be put aside.
* Cancelling one half withdraws its changes and drops its speculative reads, and touches
  nothing of the other.

The orb divides into two lobes of itself rather than spawning a widget. Two fingers apart
fork, pinched together merge, a tap on a half focuses it — and a row of chips does all of it
too, because one way is not enough on a workbench.

---

## 6. The capability gaps, closed

| | What happened on 9 September | What happens now |
|---|---|---|
| A | "None of my order tools return the actual street address line" | `shopify_order_address`, unredacted, and a fast path that answers it in 41 ms |
| B | `gmail_read_thread:refused` — a thread id nobody had issued | `gmail_find_in_email` searches every thread it finds and says "checked 4 of 6" |
| C | Answered in one thread, still counted as answered | cross-thread reply state per customer, no thread merging anywhere |
| D | "I can't add buttons to the card" | server-owned row actions; remove means archive, and there is no delete to reach for |
| E | "Why can't I just send them all at once?" | `batch_email_send`, RED, frozen messages, no undo |
| F | draft and send confused | told apart from the words before Claude reads them |
| G | a saved draft reported UNVERIFIED | proven by the id Gmail handed back as well as the header |
| H | an order edit reported done that never happened | a stated limitation, and FALSE_SUCCESS in the report |
| I | 75.5 seconds and no tools for "what more can you do now?" | a comparison of two manifests, in under a millisecond |

---

## 7. Action state

`GET /actions/states` answers where every card on the screen stands, in one request. The
tablet reconciles after every gesture and on every wake and believes the answer. It no longer
infers an outcome from the fact that a finger moved. A Mac that has lost the conversation says
so, and its silence settles nothing.

---

## 8. Observability

Every turn now records: the lane, the recipe, whether the fast path hit, the branch and its
parent, cache hits and misses, coalesced requests, prefetch hits, the read plan's waves and
critical path against its serial time, source latencies, the model's latency and call count,
the model's input size in characters, the tool block's size in bytes, the turn's total, and
whether it was backgrounded or cancelled. Counts, milliseconds and tool names — no content.

New failure classes, each graded against what the request was FOR: `FALSE_SUCCESS`,
`UNFULFILLED_ACTION`, `ACTION_MISMATCH`, `UI_INTENT_UNFULFILLED`, `DATA_FIELD_UNAVAILABLE`,
`INTENT_DIVERGENCE`, `PARTIAL_COVERAGE`.

`make test-session-status` counts from the file, so a supervisor restart no longer reports
zero against a session holding a thousand.

---

## 9. The three words

```
crooks-status    build, voice, Claude, Shopify, Gmail, orders, what it can do, the address
crooks-update    fetch, fast-forward only, deps if they changed, restart, verify
crooks-watch     the live semantic trace, one line per thing
```

`crooks-update` runs no git verb that could lose work — a test reads the verbs off the source
and fails if one appears. A dirty tree or a diverged branch stops it, and it says why. It
never touches `.env`, `logs/` or `reports/`, and nothing inside CROOKS OS calls it.

---

## 10. Tests

1,342 pytest (was 1,163), 78 node, ruff clean, 38 Chromium acceptance checks — ACCEPTED.

New files: `tests/test_fastpath.py` (58), `tests/test_memory.py` (13), `tests/test_reads.py`
(13), `tests/test_capabilities.py` (11), `tests/test_gaps.py` (45), `tests/test_branches.py`
(25), `tests/test_operations.py` (23).

Two adversarial review passes were run on the new code after it was written, each told that
four real findings beat twenty speculative ones. Between them they found twenty-one defects
that had been executed against the real payload shapes — including two that would have shipped
a confidently wrong answer, and one that would have let a change be applied from a half of the
conversation the owner had put aside. All twenty-one are fixed and tested;
`REVIEW_PASS_D.md` records each one, and the three suggestions that were rejected with the
reason each was wrong.

---

## 11. The measured before and after

`make bench-lanes` — 200 orders, 40 ms a source request. Baseline quoted from the 9 September
session; the after column measured now, and it is the Mac's own work, which is what the
baseline's non-Claude time also measures.

| Asked | 9 Sept, on the tablet | Now | Model calls |
|---|---|---|---|
| What more can you do now? | 76.6 s (75.5 s Claude, 0 tools) | 0 ms | 1 → 0 |
| Read me the full address | 36.8 s (35.2 s Claude, 1 tool) | 41 ms | 1 → 0 |
| Next | 30.4 s (29.4 s Claude, 0 tools) | 1 ms | 1 → 0 |
| Which customers are waiting on a reply | 29.0 s (28.1 s Claude, 0 tools) | 740 ms | 1 → 0 |
| Order 1938 (cold / again) | not asked that session | 84 ms / 41 ms | 1 → 0 |
| What sold best this month | not asked that session | 124 ms | 1 → 0 |
| Which orders are late | not asked that session | 943 ms | 1 → 0 |

All fourteen rows answer in the fast lane, none over its own target, none calls the model.
"Which orders are late" costs 943 ms rather than 246 ms because the review found it reading a
thirty-day window where the read layer's own catalogue uses ninety — so the order that had
been waiting forty-five days was exactly the one it could not see. Correctness first.

Model input on the turns that still reach Claude, measured by `make accept`: prompt 14,614
characters, 12 read tools, 6,028 characters of schema. The tool block grew by about 1.7 KB
this pass for three named capabilities and was paid back by half in tighter descriptions.

---

## 12. What is still true, and what is not done

**Two halves do not think at once.** A background half reads, reports and holds its place, but
the provider serialises model turns behind one lock, and two concurrent Claude sessions
sharing the provider's per-turn state would misattribute tool calls between branches. That is
exactly the trade the brief forbids. Making the client pool per-branch is a real change to
`app/providers/max_agent_sdk.py` and is the next piece of work, not this one's.

**Shopify order editing is not built.** Adding a line to a paid order changes what the customer
owes. It is a stated limitation with the nearest real thing beside it, and the report catches
the failure shape if it is ever answered as done.

**The fast lane declines more than it could.** "What is the address on 1938" (without the word
"order"), "any new email?", and several near neighbours fall to Claude by a few hundredths of
confidence. That is the correct direction to be wrong in, and `make test-session-proposals`
will name them from a real session if they repeat.

**The coalescer and the prefetcher are built and not yet called.** Both are bounded, tested
and read-only, and no turn asks them for anything yet. Until one does, "cancelling a half drops
its speculative reads" is true of a thing that is not running. They are wired the moment a
recipe wants them; wiring them speculatively now would be a moving part in production earning
nothing.

**The numbers here are from a fake store.** Shopify's and Gmail's real latency is what it is;
what the bench measures is that the Mac no longer adds thirty seconds of its own.

---

## 13. Deploying it

On the Mac, in a Terminal:

```bash
cd ~/crooks-assistant/crooks-assistant
git fetch origin claude/crooks-assistant-build-lgxlau
git checkout claude/crooks-assistant-build-lgxlau
git pull --ff-only
make venv          # only if the dependencies changed; it is quick if they did not
make test          # 1,328 tests, entirely offline, about 16 seconds
make commands      # once: crooks-status, crooks-update, crooks-watch onto the PATH
make restart       # or make up, if you run it in a window
crooks-status
```

From then on, every update is one word:

```bash
crooks-update
```

To watch an hour with the tablet:

```bash
make test-session-start NAME="the first hour"
crooks-watch                      # in a second Terminal
make test-session-stop
make test-session-report
make test-session-proposals
```
