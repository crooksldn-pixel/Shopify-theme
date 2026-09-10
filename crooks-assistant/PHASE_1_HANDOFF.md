# Phase 1 handoff

For whoever does Phase 2. This says what was built, what it is for, how to run it, what is
rough, and — most importantly — which parts are load-bearing and should not be rewritten
because they look unfamiliar.

Phase 1 was an engineering pass: architecture, correctness, and objective tests. Phase 2 is the
experiential one. Nothing here was tuned by looking at screenshots; it was built so that
looking at screenshots is now worth doing.

---

## 1. What was wrong, and what fixed it

Real testing on the tablet reported: order lookup was fast, and then "mostly rendered as plain
text… contextual actions not properly surfaced… repeated lookup remained text-heavy". The
latency work had landed; the presentation had not.

Four separate causes, each confirmed by running the code rather than by reading it:

**The action rail was empty on every read.** `app/routes/turn.py::_answer` ended with
`elif not proposed: writes = None`. That is right for the wire — `writes` on the payload says
whether a tap could apply the card THIS turn produced, and a turn that proposed nothing has
nothing to describe. But the same table is where the order card's rail comes from, and a read
turn is exactly when the rail matters. One variable served both. It is now two: `rail` goes to
`present()`, `writes` goes on the wire.

**The fast lane never computed that table at all.** `writes` is assigned further down the
function, past the point the fast lane returns from. It is now worked out beside the read.

**"Show me 1938 again" had no intent family.** It fell through to Claude every time. Likewise
"show me today's orders" — because the tokeniser kept apostrophes, so `today's` was a token
that matched no period word. And "orders today" resolved to a *sales metric* and answered with
a revenue figure.

**`Recipe.ui` was decoration.** Every recipe declares one; nothing that renders reads it. A
recipe could only draw a card by returning `ToolCall`s, so the two capability recipes — which
read no tool, by design, because the manifest comes from the registry — drew nothing at all.

---

## 2. Architecture added

### `app/surfaces.py` — the typed surface contract
`Surface`, `Entity`, `Linked`, `Loading`, `Freshness`, `SURFACE_VERSION`. A card now carries
which contract version it is, which entity it is about, what it links to, which regions are
still loading, how fresh it is, and what to say about it.

The wire shape is unchanged: `{"type": ..., "data": {...}}` plus sibling keys. An older tablet
ignores the additions and still renders. **This does not replace `app/presentation.py`** — that
file's whitelist-copy discipline (every value copied key by key, every list bounded) is the
reason no model-invented value has ever reached the screen, and it is untouched.

`FastAnswer.surfaces` is the new channel: a recipe that reads no tool can now draw a card.

### `app/commands.py` — one semantic command layer
Back, Forward, Home, Next, Previous, open a linked record, select a tab, expand a row, arm a
spoken continuation. Voice and touch both resolve into these.

Before this, Back existed twice: spoken, it moved the cursor, rebuilt the record from memory
and said a sentence; tapped (`/branches/{id}/back`), it moved the cursor and returned bare
JSON. The same gesture drew a card in one direction and not the other. The cursor arithmetic
moved here too, out of `app/fastpath/runner.py::_advance` where it was keyed on a recipe id and
touch could not reach it.

### `app/routes/command.py` — `POST /command`
The tablet posts *which* command and *which* record. It cannot post what the command should do.
That is the write boundary's rule applied to the read side, and `tests/test_web.py` now fails
if a note, body, amount, reason, address, subject or tag is ever posted with a command. The
response is the same shape `/turn` returns, so the tablet renders a tap and a sentence with
the same code.

`GET /commands` lists what may be posted, derived from the registry.

**The tablet actually uses it.** `web/app.js::goBack` posted nothing before — it walked a local
array of rendered nodes, so the tapped position and the Mac's position diverged the moment
either was used. It now posts `navigation.back` and draws what the Mac says it landed on,
falling back to the local history only when the request fails (a Back button that does nothing
when the tailnet hiccups is worse than one occasionally out of step). There is a **Next chip**
beside Back, shown while a list is open and not at its end, posting `workflow.next`.

Back also no longer degrades to prose when the entity tier has dropped the record: the trail
move happens in the runner *before* the plan, exactly as the cursor move does, so the plan
knows what it landed on and reads it. `tests/test_experience.py` empties the tier and proves
a card still appears.

### `app/readonly.py` — the read-only latch
Makes a process incapable of changing anything. Checked at three chokepoints, which are a
complete set because every write funnels through one of them:

| Chokepoint | Covers |
|---|---|
| `ShopifyClient.mutate` | every reviewed Shopify mutation |
| `GmailClient` send/draft/modify (5 methods) | every Gmail change |
| `ActionEngine.commit` | one layer up, so a refusal is a card and a ledger line |

Off unless engaged; no release; every refusal logged. Only `experience/live.py` engages it.

### `app/capabilities/surface.py`
The manifest, grouped by the part of the shop it touches, with per-change state. Built from the
state that holds *when asked*, not at boot.

---

## 3. Presentation types

The renderer's vocabulary is unchanged except for one addition, `capability`. The two
vocabulary tests (`tests/test_web.py`, `tests/web/ui.test.js`) keep `app/presentation.py` and
`web/ui.js` in step and will fail if you add one to either and not the other. That is
deliberate — let them.

`surface_type` (what the interface is *for*) is distinct from `ui_type` (which component draws
it). They are usually the same word. An order list built from an analytic query and one built
from a plain listing render with the same component and are the same surface.

---

## 4. Fast paths

Added: `order_list_period`, `order_reopen`, `customer_history_lookup`.
Fixed: the apostrophe tokeniser, the metric/listing split, the email past tense, a
possessive-name guard, and the deixis requirement on customer history.

The routing rules that matter, and why:

- **"Orders" is not a metric word.** It is the one word "how many orders today" and "show me
  today's orders" share, so it cannot be what decides between them. What decides is whether a
  quantity was asked for or a look was.
- **A named person is not the open record.** `customer_history_lookup` needs a pronoun —
  "this customer", "she". "Has Daniel bought from us before" goes to the path that can find
  Daniel. The mocked-hour observability test caught this; it is a real trap.
- **A possessive proper noun blocks the inbox families.** "Show me Millie's emails" used to
  show the whole inbox. It now defers, because the fast lane cannot resolve a name it has
  never seen and a confident wrong answer is worse than a slower right one.

---

## 5. The experience layer

```
experience/
  fixtures/data.py      the golden world: 5 people, 7 orders, 3 garments, 6 threads
  fixtures/shopify.py   a ShopifyClient with graphql() replaced — the narrowest seam
  fixtures/gmail.py     a fake Google API service, so GmailClient's real logic runs
  harness.py            drives real turns through the real runtime; captures everything
  scenarios.py          the 15 golden scenarios and their assertions
  browser.py            starts uvicorn + runs the Chromium suite
  live.py               real credentials, read-only, latch engaged first
  report.py             report.md / report.json per run
  matrix.py             the feature matrix, derived
```

**The one rule.** A scenario injects a transcript at `POST /turn` with a `text` body. That is
not a shortcut around the application — it is the exact point the audio path arrives at once
Scribe or whisper has finished. Everything after it is shared. Do not add a helper that
bypasses it.

**Fixtures fake at the boundary, not the class.** `FixtureShopify` replaces `graphql()` only,
so the query strings, the retry policy, the shop/timezone handling and every line of result
shaping above it are the ones that ship. The Gmail double is a fake *googleapiclient service*,
so all of `GmailClient` — header parsing, label handling, `internalDate` arithmetic, the scope
report — runs for real.

**Both fixture clients refuse every mutation**, and an unknown GraphQL operation raises rather
than returning an empty connection, because a scenario that silently reads nothing proves
nothing.

---

## 6. The golden scenarios

`capabilities`, `order_lookup`, `repeat_order`, `today_orders`, `next_previous`, `back`,
`tabs`, `full_address`, `customer_history`, `needs_reply`, `house_number`, `linked_entities`,
`unsupported_edit`, `split_branches`, `enrichment`. 15/15 pass, 92 checks.

The assertion order is load-bearing: structural, then grounding, then mechanical. Only those
three are here, because only those three can be decided without an opinion. A semantic grader
may be added and can never overturn them.

`prose_only` is the check the whole pass exists for.
`tests/test_experience.py::test_an_order_lookup_that_is_fast_and_empty_is_a_failure`
deliberately asserts **nothing about latency** — the build that was reported was fast, and that
was the complaint.

---

## 7. How to run it

```sh
make experience                    # the golden scenarios, offline
make experience SCENARIO=back      # one of them
make experience-list               # what there is
make experience-ui                 # the same, plus Chromium and screenshots
make experience-live               # the REAL shop and inbox, read-only
make matrix                        # which operations are reachable and tested
make test                          # everything, including the scenarios
```

On the PATH after `make commands`: `crooks-test`, `crooks-test-ui`, `crooks-test-live`,
`crooks-test-scenario <name>`.

Reports land in `reports/experience/<run-id>/` — `report.md`, `report.json`,
`screenshots/`. Twenty runs are kept.

The browser suite needs `npm i playwright-core` and a Chromium; without them it **skips
loudly**. A browser check that cannot run has proved nothing.

---

## 8. Benchmarks

**Card** is the backend's own measure of its own work: routing, reading, shaping, presenting,
up to an answer with something to look at. **Round trip** adds the transport — ASGI here, Wi-Fi
on the workbench.

| | card | round trip |
|---|---|---|
| order lookup | 7 ms | 10 ms |
| the repeat | 3 ms | 6 ms |
| today's orders | 4 ms | 7 ms |
| capability surface | 5 ms | 22 ms |
| full address | 2 ms | 4 ms |
| customer history | 3 ms | 5 ms |
| needs reply | 6 ms | 9 ms |
| spoken next | 3 ms | 6 ms |
| Back / Next / tab (touch) | 1 ms | 2–4 ms |
| enrichment (second request) | — | 4 ms |

**Read these honestly**, in three ways.

They are against an in-memory fixture shop, so they measure the Mac and not the network.
Production adds Shopify and Gmail round trips.

Nothing here includes speech: no run calls `/speak`.

And the two columns are two numbers, which they were not until the adversarial review found
that `first_ui_ms` was being assigned the same variable as `total_ms` — one measurement printed
twice under a heading claiming they were different things. The card column now comes from
`timings_ms.total` on a turn and `served_ms` on a tap; the check in `scenarios.py` fails if
they ever collapse back into one.

Every one of those turns made **zero model calls**.

---

## 8a. The adversarial review, and what it found

Eight hunt lenses were run over this tree — prose-and-buttons, duplicate logic between voice
and touch, state leakage, wrong answers, read-only holes, stale-and-cached, test integrity —
and their findings were reproduced against running code before anything was changed. Twenty
reproduced. All twenty are fixed, each with a test that fails when its fix is reverted.

The ones worth knowing about, because they say what this codebase gets wrong when it goes
wrong:

**A shared cache is not a shared permission.** `commands.replay` handed back any record the
process held, keyed on kind and ref, with no check that the asking conversation had ever been
shown it — while `/context/order/{id}`, serving the same data, refuses exactly that. Refs are
guessable. It checks `session.issued_ids` now, the rule every tool call already goes through.

**A list, and a change, belong to one half of the orb.** Working sets carried no branch, so the
newest set on the conversation answered for both halves — including in the sentence that tells
the model what "these" and "all of them" mean, which reaches the write path. And
`ActionEngine.stage` stamped the FOCUSED branch while every reader assumes the ASKING one,
which inverted four documented properties at once, among them "a background branch never
commits a change".

**Tests that could not fail.** "Nothing was changed in the shop" read an attribute the fixture
store does not have, so it was `not []` — true, forever. The fake inbox could not parse the
correlation query the application actually builds, so "which customers need replying to?"
answered "Nobody is waiting" in a world with three people waiting, with the scenario green.
The prose regression test treated falling off the fast lane as an exemption rather than the
regression it is.

**Cards that said more than was behind them.** The capability card's chips and its whole
"Since the last build" section were filtered to nothing by a helper that drops non-objects, so
they never rendered at all; its per-change states read an attribute nothing ever set, so every
change was badged "unknown"; and its row budget was eaten by reads, so "the shop" showed nine
readings and one change while the subtitle said fourteen changes existed.

One change entered the tree from a review agent and reached a commit unmentioned — the
`possessive_name` blocks in `app/fastpath/intent.py`. It is described in `aea8f30`, which
records how it got there, why it is right, and adds the test it was missing.

---

## 9. Known rough edges

- **Voice `next` and touch `next` word themselves differently.** The spoken one reads the
  member fully ("1940 is Priya Raman's for £18.00, unfulfilled. 1 of 3."); the tapped one
  replays from memory ("#1938. 2 of 3."). Same cursor, same list, same surface — different
  sentence. Phase 2 should decide what a tap should say.
- **"Show me Millie's emails" defers.** Cold name resolution is not something the fast lane
  can do. Claude handles it and `present()` builds an `email_list` from the tool result. A
  fast path for it would need a name→customer resolver.
- **Email rewrite / send-vs-draft / batch send are not golden scenarios.** They need the model
  to propose, and the harness's provider does not. Their *safety* is covered
  (`unsupported_edit` proves no false success, the fixtures refuse every write), their
  behaviour is not.
- **`make experience-live` runs a narrowed set.** The other scenarios name a fixture record —
  order 1938, Mia Jones — so against the owner's own shop they would fail for a reason that
  says nothing about the code. `LIVE_SCENARIOS` in `experience/scenarios.py` is the subset,
  and their grounding assertions are dropped in live mode: what is checked there is the
  shapes. Without credentials it says so in one line and exits 2.
- **`/branches/{id}/back` and `/forward` still exist** alongside `POST /command`, and the
  tablet no longer calls them. They are no longer a second implementation — they move through
  `commands.move_nav`, the same arithmetic as the word and the button — but they are still a
  second door, and they do not draw. Closing them is a tidy-up for later.
- **A replayed card does not say it is replayed.** `app/surfaces.py` declares `Freshness` and
  says "a card that is showing a cached read must say so, because the owner is about to make a
  decision on it" — and `present()` never sets it, so a record read 170 seconds ago looks
  exactly like one read this instant. The risk is bounded: the action engine rereads
  authoritative state before any change, so a stale card cannot cause a wrong write. But the
  claim in that docstring is not yet true, and plumbing `Freshness` through `present()` is
  presentation work sized for Phase 2.
- **A read-only latched process still reports its changes as ready.** `readonly.active()` is
  checked at the two clients, in `ActionEngine.commit` and in `BatchEngine.commit`, but not in
  `runtime.write_status()` or `capabilities()`. So during a live read-only run /health says
  writes are ready and the order card carries its full rail — for a process in which no change
  can execute by construction. The refusal is real; it just arrives at the gesture rather than
  on the card.
- **The capability card's per-change states are cold until something asks.** `capabilities()`
  now keeps what it works out, but it is deliberately not warmed at boot: the lifespan runs
  before the clients can be swapped, so a boot-time scope read goes to whatever `build()` made
  — which is how the order cache used to hang the harness on the network, and it hung it again
  when tried. Until the first /health poll or the first write preflight, changes read
  "unknown", which is honest but not useful.
- **`pytest tests/test_browser.py` prints `RuntimeError: Event loop is closed` to stderr.**
  It is pytest-asyncio closing the loop while uvicorn's transports finish. The test passes;
  the traceback is noise.
- **The order card renders slightly dimmed in a screenshot taken too early.** Handled by
  waiting for animations to settle before capturing; if you add a shot, use the existing
  `shot()` helper rather than calling `page.screenshot` directly.
- **The feature matrix lists 13 operations with no scenario.** They are listed, not hidden.

---

## 10. What Phase 2 must NOT rewrite

- **`app/presentation.py`'s whitelist-copy discipline and its bounds block.** Every value is
  copied key by key with an explicit cap. This is why no model-invented value has reached the
  screen. Add a line to carry a new field; do not replace the mechanism with a serializer.
- **`app/actions/` in its entirety** — the grammar table, `AvailableAction`, `RowAction`, the
  staging, the gesture, the freshness reread, the verification. The 25 invariants live here.
- **`app/fastpath/intent.py`'s signal-based scoring.** New families plug in by appending to
  `FAMILIES`. The `MARGIN` ambiguity check is what stops confident wrong answers.
- **`app/fastpath/runner.py`'s defer semantics.** Deferring must stay cheap and silent.
- **`assert_read_only` / `assert_reads_only`.** The fast lane's structural inability to write.
- **The two vocabulary tests.** They will annoy you exactly once per new card type, which is
  the point.
- **`app/readonly.py`'s one-way latch.** A releasable latch is one a later line of code can
  release.

---

## 11. Safety

No deployment occurred. The action-engine invariants are intact and untouched; the only change
near them is a refusal *before* anything is claimed when the read-only latch is down.

`experience/live.py` engages the latch before building a single client, and the clients it
binds have no working mutation of their own — so the latch would have to fail AND the wrapper
would have to fail AND the engine would have to fail before anything could be sent.

`tests/test_readonly.py` holds all of it.

---

## 12. Where this ends

Branch: `claude/crooks-assistant-build-lgxlau`.

Final code commit: **`efd63fc`**. This document is the commit after it, so `git log -1`
on the branch shows one further commit whose only content is these docs — the SHA of the last
commit that changed behaviour is the one above.

Suite at handoff:

| | |
|---|---|
| pytest, offline | **1401 passed, 2 deselected** (1342 baseline + 59) |
| ruff | clean across `app config scripts tests experience` |
| Node | 80 pass, 0 fail; every page script parses |
| golden scenarios | 15/15, 97 checks |
| browser checks | 25/25 at 800x1280 and at 400px |
| screenshots | 4, in `reports/experience/<run>/screenshots/` |

Changes anywhere near `app/actions/` are three, all additive and all refusals or scoping:
a refusal in `ActionEngine.commit` when the read-only latch is down; the same refusal in
`BatchEngine.commit`, before the batch is claimed; and `stage()` reading `acting_branch`
instead of `focused_branch`, so a change belongs to the half that asked for it. The 25 action
invariants are untouched — the third of those is what makes two of them true that were not.

**No deployment occurred.**
