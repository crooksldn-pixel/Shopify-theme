# CROOKS OS — Phase 3 engineering pass

**Not deployed.** Nothing in this pass has been applied to the running build. The branch is
pushed for the owner to test physically on the Samsung first; the deployment steps are at the
end of this report and none of them has been run.

- **Starting SHA** `644be75` (the Phase 2 report's final commit)
- **Final SHA** _see the last line of this report_
- **Branch** `claude/crooks-assistant-build-lgxlau`
- **Coding environment** Linux, no Keychain, no Shopify or Gmail credentials, no Claude
  subscription for the assistant's own provider. Everything below was proved against the
  golden fixture world, the offline suite, and a real Chromium at the tablet's own viewport.
  What could not be proved here is listed under *Blocked by credentials*, with what to run on
  the Mac instead.

---

## 1. What the live test found, and what happened to each finding

The Phase 2 live tablet test (`ts-20260910-125946`, 601 × 889, DPR 1.33) is the input to this
pass. Each row says whether the failure is now impossible **by a test that can fail**, or still
possible.

| The live failure | Now | Held by |
| --- | --- | --- |
| Two fingers on the orb produced a blank speech turn, six times | **Impossible** | `scripts/browser/tablet.js` — a CDP two-finger spread forks the branch and asserts **zero** `/turn` posts and no hearing error |
| Split depended on a secret gesture | **Impossible** | The same gate asserts a visible `Split` control that reaches the same backend command |
| Tapping the other half changed who was listening, not what was on screen | **Impossible** | `tests/test_split_workspaces.py` plus a browser check that switching halves changes the visible cards |
| A half finished a ten-second turn with nothing on the tablet | **Impossible** | `branch.ready(...)` when the focus is elsewhere, asserted in `tests/test_split_workspaces.py` |
| The dock was decorative unless already in an interaction | **Impossible** | `experience/scenario_packs/landings.py` — four landings, each tapped from an idle tablet, no model; the tablet gate asserts the tap lands by command, not by sentence |
| `commerce_query` failed three times running with "sort by :" | _see §13_ | — |
| An email thread showed no linked order | **Impossible** | `tests/test_graph.py` and `experience/scenario_packs/graph.py` |
| "Add a black hoodie to this order" refused | _see §10_ | — |
| Discount code, store credit, abandoned checkouts refused | _see §12_ | — |
| An email to an address that is not a customer refused | _see §11_ | — |
| "No, don't save a draft, you want it sent" took 25 s and failed | _see §11_ | — |
| The armed state was clipped in a dock pill 788 px below the finger | **Impossible** | The armed pill is drawn on the control; the tablet gate asserts it is unclipped, inside the card, with a 44 px Cancel |
| A failed customer read was drawn as "no customer" | **Impossible** | `tests/web/ui.test.js` and `tests/test_context.py` — a failed region says so and the tab is marked |
| Compound surfaces over 3,300 CSS px | **Reduced, measured** | §22 below: the three compound landings now fit one screen at 601 × 889 |

---

## 2. Architecture changes

### 2.1 One Claude conversation per half of the orb (§3F)

The provider kept **one client per session** and **one process-wide turn lock**, with the
turn's state — the session it was for, its tool calls, its steps, the conversation position it
answered — in fields on the provider itself. Two halves thinking at once would have shared all
of it.

- `app/providers/max_agent_sdk.py`: a `_Conversation` per `conversation_key(session_id,
  branch_id)`, each holding its own client, its own `asyncio.Lock` and its own turn state. A
  client's MCP tool server and PreToolUse hook look through a `_Holder` to find whose turn they
  are serving, so a tool call can never be filed against the wrong half.
- Turns on **one** half still serialise. Turns on **different** halves run together, up to
  `MAX_CONCURRENT_TURNS` (two — one per half).
- `interrupt(session_id, branch_id=...)` stops one half's turn and leaves the other thinking.

Two things had to become per-half for this to be *safe* rather than merely parallel:

1. **Which half a proposal belongs to.** `session.acting_branch` is one field for both halves
   and holds whichever spoke last. The branch now travels on the task the tool call runs in
   (`app/tools/context.py:CURRENT_BRANCH`, read through `acting_branch(session)`), so with two
   calls in flight the engine cannot stamp the left half's proposal with the right half's id.
2. **"The owner has moved on."** This was judged by the session's epoch, which moves for
   *either* half's instruction — so every slower answer would have been called abandoned,
   unspoken, its proposals withdrawn, because the owner asked the other half something
   meanwhile. Each half now counts its own instructions (`Branch.instruction_seq`) and carries
   its own cancel flag; `/cancel` takes a `branch_id`.

**The mutation boundary is untouched.** Staging and commit are the action engine's, on its own
terms; a background half still cannot commit; a proposal is still bound to session, epoch,
turn and branch. Nothing about concurrency lets two writes overlap: the engine serialises
commits as it always did.

On the tablet, `busy` was one flag for the page. It is now a map of in-flight turns by half,
and `busy` means "the half on screen is thinking" — switching halves switches what it means.
An answer that lands for a half the owner has left is not drawn over the conversation he is
having now; its chip says READY and the Mac holds its screen for `branch.show`.

### 2.2 The dock's landings (§4)

Each icon asked a sentence through the whole turn pipeline, so "show me today's orders" on a
quiet afternoon drew an empty list. A landing is now a place with a fixed shape, in
`app/families/landings.py`:

| Icon | What it draws |
| --- | --- |
| Orders | what has to go out, oldest first and a set to walk, plus what came in today |
| Inbox | who is waiting on a reply, then what else people have written |
| Sales | the week against the week before, today so far, and what is selling |
| Products | the month's best sellers and what is closest to running out |

Four FAST recipes — deterministic reads through the read scheduler, no model — reached two ways
that resolve to the same recipe: the tap posts the semantic command `open.area` (which area,
nothing else; the Mac decides the rest), and "open orders" / "open the inbox" / "open sales" /
"show me stock" spoken resolve to the same recipes. A sentence that names a period still gets
the period's list. A tap the Mac cannot draw falls back to the sentence, so the icon always
does something.

Two supporting changes in `app/routes/command.py`: a command may name a FAST recipe for the
route to run (`changed["recipe"]`), and every posted form field reaches the command, bounded
(24 fields, 8,000 chars) — which is also what makes precision input work without a route change
per field. A fresh tablet may tap the dock before it has said anything: `open.area` creates the
conversation, as a sentence would.

### 2.3 Capability families as a seam (§29)

`app/families/` is a package where each capability is one module: its tools, commands, recipes,
intent families and capability state register on import. Adding a capability is adding a file,
so parallel work never edits the same table.

`runtime.withheld_by_family()` now hides from the model every tool of a family that is not
READY — all of them for NOT_SUPPORTED_BY_STORE, DISCONNECTED or NOT_IMPLEMENTED, the write
tools for MISSING_SCOPE or READ_ONLY. The live test spent fifteen seconds of Claude attempting
operations the store could only refuse; a tool that is not offered is not tried. The same table
reaches the model as one context line and the tablet as the settings sheet's "What I can do",
where an unavailable family says which kind of unavailable it is and names the scope to grant.

---

## 3. Density: measured, then reorganised (§22)

Measured with a real Chromium at 601 × 889, DPR 1.33, against the fixture world, before and
after. `screens` is the deck's scroll height over the viewport.

| Surface | Before | After |
| --- | --- | --- |
| Orders landing | 1,112 px · 1.25 screens · two lists and **two** "these" cards | **671 px · 0.75** |
| Inbox landing | 952 px · 1.07 screens · two email lists stacked | **671 px · 0.75** |
| Products landing | 1,498 px · 1.69 screens · two full rankings | **736 px · 0.83** |
| Order card | 796 px · 0.90 | unchanged (physically judged good) |
| Capability card | 1,132 px · 1.27 | unchanged |
| Stock ranking | 1,013 px · 1.14 | unchanged (one card, legitimately long) |

`compact()` in `app/presentation.py` applies two rules to the **whole screen**, after a recipe's
own cards have been put in front of the tool cards — which is why it is not part of `_merge`:
`_merge` runs inside `present()` and can only see the tool cards, so the Inbox landing's two
lists never met until afterwards.

1. **One cursor per turn.** Two cards each saying "these" are two claims to the same word.
2. **One headline per kind.** The second card of one analytic kind is marked `secondary`, and
   the tablet folds it behind its own title (`web/ui.js:folded`: a real button with
   `aria-expanded`, the card inside complete and untouched). Nothing is removed. An order card
   is never folded — two orders in one turn are two records, both wanted open — and two
   *different* kinds are both headlines, so Sales keeps its numbers beside its ranking.

---

## 4. Latency: three numbers where there was one (§25)

`turn_performance` now carries `facts_ms` (when the Mac held the authoritative data the cards
are drawn from — the last read to land), `workspace_ms` (when the cards existed) and
`prose_wait_ms` (the rest: what the owner waited *after* the facts were in hand). The third is
the number to attack, and the old single `turn_total_ms` could not see it: a turn that read an
order in 400 ms and then spent eight seconds writing a sentence about it looked the same as one
that spent eight seconds reading. `enrichment_pending` names the regions a card left loading,
so final enrichment pairs with the `/context/order` request that finishes it.

Bench (`make bench-lanes`, 200 orders, 40 ms per source request; baseline quoted from the real
session of 9 September 2026):

| Asked | Then, on the tablet | Now, the Mac's own work |
| --- | --- | --- |
| Which customers are waiting on a reply | 29.0 s (28.1 s of it Claude) | 87 ms, FAST |
| Next | 30.4 s (29.4 s of it Claude) | 0 ms, FAST |
| Tap Orders | not asked in that session | 2 ms, FAST |
| Tap Sales | not asked in that session | 4 ms, FAST |
| Tap Products | not asked in that session | 3 ms, FAST |

17 of 17 bench rows answer with **no model call**. The landing figures are warm: their reads go
through the order cache, which the Mac warms at start-up, so this is what the second tap of the
day costs. The first tap pays the cache warm.

### 2.4 The capability manifest, made user-useful (§29)

Fifteen families are registered for what already worked — reading orders, customers, products
and email, the analytics, and the ten write operations (cancel, refund, fulfil, tracking,
address, notes, tags, stock, drafts, sends, archive). A manifest that lists only the new
things is not a manifest, and `/health families` returned nothing before this.

Their states are **derived, not declared**: `families.states()` reads the per-operation table
`runtime.capabilities()` already builds, so a family says READ_ONLY when changes are switched
off and MISSING_SCOPE when Shopify has not granted the scope, without `app/families/core.py`
knowing anything about either. Two tests hold the seam: every registered write operation and
every model-facing read tool must be named by some family, so a capability cannot be added
without appearing in the manifest.

What the model is told changed with it. The line used to list every family; with fifteen
registered that is **420 characters of prompt on every turn** to say that reading orders
works. It now carries only what the Mac **cannot** do:

| | Lines | Characters per turn |
| --- | --- | --- |
| Every family (the old shape) | 15 | 420 |
| Only the unavailable ones, all ready | 0 | **0** |
| Only the unavailable ones, one blocked | 1 | 117 |

The ready families are the tools the model is offered — `withheld_by_family` takes the rest
away — so the tool list already says what is available. The owner's surfaces still ask for
the whole list (`words(table, only_unavailable=False)`), and the settings sheet shows it.

### 2.5 A family brings its own word to the router (§17)

The brief's section 17 names the requests that should avoid the model. Run against the router,
three of its own examples resolved to no family at all — not because the fast lane could not
answer them, but because the router had no word for *shipping*, *latest* or *half*, and its
signal vocabulary was a fixed dataclass every family would have had to edit at once.

`app.fastpath.intent.signal(name, predicate)` is now a seam: a family registers its own word
and `score` looks it up like any other. A core signal can never be shadowed. Three families
use it (`app/families/navigation_extras.py`): the tab move goes through the same
`surface.tab` command the tap reaches, the latest order names which order it turned out to
be, and the switch moves the focus and draws what that half was looking at.

The routing table now, with an order open and a set being walked:

| Said | Lane | Family |
| --- | --- | --- |
| order 1938 | FAST | order_lookup |
| show me today's orders | FAST | order_list_period |
| read me the full address | FAST | order_address_lookup |
| where is order 1938 | FAST | order_status_lookup |
| show me the shipping / the items / the customer | **FAST** | order_tab_show |
| show me the latest order · the most recent order | **FAST** | order_latest |
| switch to the other half · the other half | **FAST** | branch_switch |
| next · go back | FAST | working_set_next · navigation_back |
| open orders · open the inbox · open sales · show me stock | FAST | the four landings |
| what can you do? | FAST | capability_summary |
| what else has this customer ordered? | FAST | customer_history_lookup |
| what sold best this month · which orders are late | FAST | best_sellers_period · delayed_orders |

Two collisions were found by the tests and fixed, both of which had made a previously fast
sentence slow: "address" as a shipping-tab word stole the sentence that reads the address
out, and "last" as a latest word stole the cursor's "the last one". One the router was right
about: with an order open, a bare "show me the email" is genuinely ambiguous between this
order's Email tab and the inbox (0.96 against 0.90, inside the margin), so the inbox keeps
the bare word and the tab is reached by a sentence that says which order.

---

## 5. Blocked by credentials or configuration

This machine has no Keychain, no Shopify token, no Gmail credential and no Claude
subscription for the assistant's own provider, and by the brief's own rule no automated run
may make a real Shopify or Gmail write. So four things could not be proved here, and each has
an exact command to run on the Mac instead.

| What | Why it could not run here | Run this on the Mac |
| --- | --- | --- |
| Live read-only scenarios against the real store | No token; the harness refuses to read a real shop unless the read-only guard is armed, which needs the credential | `make experience-live` |
| Whether Shopify has granted the new scopes | `access_scopes()` needs the token; the probes are written and tested against a fake | `crooks-status`, then the settings sheet's "What I can do" |
| Any real mutation | Forbidden by the brief, and the fixture Shopify raises on every mutation so a test can only ever exercise prepare, observe, present and verify | The owner's own gesture on the tablet, once he has read the card |
| The model's own behaviour on the new prompts | No subscription here; the fixture harness stubs the provider | Ask the questions on the tablet and read `make watch` |

Nothing in this pass depends on a credential to be *correct* — every write's prepare,
precondition, verification and refusal path is exercised against the fixture, and the fixture
refuses every mutation, which is what makes those tests able to fail.

## 6. Deployment steps — for later, not now

**None of this has been run.** The running build is untouched. When the owner has tested the
branch physically and accepts it:

1. **On the Mac, in the project:** `git fetch origin` then
   `git log --oneline HEAD..origin/claude/crooks-assistant-build-lgxlau` to read what is
   coming.
2. **Check before applying:** `make update CHECK=1` (or `python3 scripts/control.py update
   --check --json`). It reports the current and candidate SHA, whether it is a fast-forward,
   whether the tree is dirty and whether dependencies changed. A dirty tree or a diverged
   branch **stops** the update; it never discards local work.
3. **Apply:** `make update`. That fast-forwards, installs dependencies if they changed,
   restarts through the existing launchd agents, and verifies `/health`.
4. **Verify on the Mac:** `crooks-status` — or the Control app's status view — and check that
   the build id moved, every check is green, and the capability families read as expected.
5. **Verify on the tablet:** open CROOKS OS, confirm the dock lands, and read the settings
   sheet's "What I can do".
6. **If it does not come up:** `make restart` once. If it is still unhealthy, the last known
   good SHA is in `logs/last_known_good.json`; `git checkout <that sha> && make restart`
   returns to it. Nothing in this pass moves a branch destructively.

Scopes: any family whose state reads MISSING_SCOPE needs its scope granted in the Shopify
admin before it will work. The families table names the scope; §6 above lists the new ones.

---

## 7. Does any of this weaken the mutation security model?

**No, and two of the changes strengthen it.** Taken one at a time against the twenty-four
invariants:

- **Concurrency (§3F).** Two halves think at once; nothing about writes changed. A proposal is
  still staged by the Mac from arguments the Mac built, still bound to session, epoch, turn and
  branch, still committed at most once by the action engine, still verified by an authoritative
  re-read. A background half still cannot commit. What changed is that the branch a proposal
  belongs to now travels on the task the tool call runs in rather than in one field the two
  halves shared — **without** that, two halves staging at once would have mis-stamped each
  other's proposals, which is a security bug this pass removes rather than adds.
- **The dock's landings (§4).** Four recipes that read. `assert_read_only` holds for them, and
  the command that opens one carries an area name from a fixed table of four.
- **Every posted field reaching a command (§7).** Bounded at 24 fields and 8,000 characters,
  and a command is a read or a move by construction. This is the precision-input path and it
  keeps the rule exactly: the tablet posts identity and typed text to a Mac command that
  validates it into a Mac-held context; staging then builds execution from that context. The
  tablet still cannot post an execution argument.
- **Withholding tools by family state (§29).** Strictly subtractive: it can only take a tool
  away from the model, never offer one. A test holds that no family which already worked
  withholds anything.
- **The compaction (§22) and the fold.** Presentation only; the folded card is the whole card
  and the actions on it are the same server-decided actions.
- **The signal seam (§17).** Routing only, and a core signal cannot be shadowed. A recipe
  reached this way is read-only like every other.

One thing to watch, recorded as a weakness rather than dismissed: the per-half turn state made
`_Conversation` the holder of what used to be provider fields, and the PreToolUse hook now
finds its session through that holder. If a future change gave a client to two conversations,
the hook would gate against the wrong session. `_Holder` is deliberately one slot, filled when
a conversation adopts a client and emptied when it lets it go, and `test_a_hook_event_with_no_turn_behind_it_touches_nothing`
holds the empty case — but this is the place to be careful.

---

_This report is being written as the pass completes. Sections still to come: the remaining
capability families (order editing, discount codes, store credit, abandoned checkouts,
arbitrary email compose, precision input, the query engine, anticipation, the learned layer,
the Control app, the analyser and recorder), the capability matrix before and after, scope
requirements, test counts, screenshots, the slowest scenarios, unresolved weaknesses, and the
deployment steps._
