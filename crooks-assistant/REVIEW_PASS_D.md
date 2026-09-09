# Council pass D — the foundation pass

Reviewed after implementation, against the change set `a743c6c..HEAD`. Every finding below
was reproduced before it was acted on, and every finding that could not be reproduced is
recorded as rejected with the reason. Nothing was changed on a suspicion.

## Confirmed and fixed

1. **`capability_delta` raised `AttributeError` at the moment it was asked.**
   `app/capabilities/__init__.py` re-exports `delta` and `build` as FUNCTIONS, so
   `from app.capabilities import delta as delta_mod` bound the function, and
   `delta_mod.spoken_delta(...)` was an attribute error. The recipe caught it, deferred, and
   the turn silently fell back to the model — which is precisely the seventy-five-second
   turn the pass exists to remove. Found by writing `scripts/bench_lanes.py`; the unit tests
   did not catch it because they import the submodule directly, which is the shape that
   works. Fixed by importing the functions by name, with the reason in a comment so the
   shape is not restored by someone tidying imports.

2. **A listing never opened a workflow, so "Next" had nothing to walk.**
   `_needs_reply_args` and `_open_workflow` looked for a working set under `set_id` at the
   top level of a read-layer result; the read layer publishes it under `set` (the whole
   public shape). The bench showed `needs_reply` deferring with "the inbox correlation did
   not come back". Fixed with `_set_id_of`, which looks for both, and used everywhere a
   listing's set is read.

3. **A module-level path bound as a function default, twice.**
   `scripts/update.py`'s `git(*args, cwd: Path = ROOT)` and `scripts/watch.py`'s
   `follow(..., out=sys.stdout)` both froze a global at import. The first made the update
   command untestable against any checkout but its own; the second made the watch's output
   uncapturable. Both now read the global at call time. The tests that found them are in
   `tests/test_operations.py`.

4. **A proposals file could carry a customer's name.**
   `_shape_of` reduced a question by dropping a list of stop words, so "has Millie Rogers at
   12 Elm Road had a reply" became "millie rogers elm road had reply" — written to disk and
   read by a person. Replaced with a CLOSED vocabulary taken from the router's own word sets:
   a word the router does not know cannot appear. A deny-list is only as good as its last
   omission.

5. **A card could be settled on the strength of a Mac that had lost the conversation.**
   The tablet's reconciliation settled every id `/actions/states` reported unknown. A Mac
   that has restarted, or a conversation that idled out, knows nothing about ANY proposal,
   and its silence is not evidence that a card is dead. The route now says
   `session_known`, and the tablet settles unknowns only when it is true. Two acceptance
   checks hold both directions.

## Routing findings, confirmed and fixed while building

6. **"How much stock of the yard jeans" answered with a restock ranking.** One product's
   stock is not the catalogue's cover ranking. `stock` and `running_out` are now separate
   signals and the recipe requires the second.

7. **"Who are our top customers" answered with a product ranking.** `best_sellers_period`
   now blocks on the customer signal: a ranking of customers is a different query and makes
   a working set.

8. **"What sold best by colour last month" ignored the dimension.** The recipe now honours a
   named grouping from a closed map of the read layer's own `GROUPS`, and declines to plan
   at all when the "by" names something the map does not have.

9. **"Who needs replying to" was read as an instruction to reply.** A gerund after a question
   opener is a description, not an order given. `mutating()` now splits strong verbs from
   soft ones, and `app/observability/contract.py` uses the SAME function — a request graded
   against a contract the router never gave it is a report that lies.

## Second round: two reviewers set on the new code, told to break it

Two adversarial passes, each given the files and the rules and told that four real findings
beat twenty speculative ones. Both produced findings that had been executed against the real
payload shapes, not guessed at. Every one below was reproduced here before it was fixed.

### The two that would have shipped a wrong answer

10. **A direction word beside a thing was read as a direction.** `_PREV` held "last" and
    "before"; `_NEXT` held "another" and "following"; neither looked at what else the request
    named. So "what's the last order" and "next week's sales" were routed to the working-set
    walker — and `_adopt_latest_set` takes the newest set of ANY kind, so a question about an
    order was answered with a customer, at "0 of 3", with the owner's place in the set moved
    under him. `customer_purchase_lookup` could barely ever win, because "before" — the word
    that marks "has she bought before" — also set the direction.
    A direction is now a direction only when the request names nothing else and is five words
    or fewer. "Before" belongs to the direction, not to both readings; "has she bought before"
    already carries "bought".

11. **Two renderers read keys that do not exist.** `shape_customer_history` returns `orders`
    (a count) and `spent` (money as a string); the recipes read `orders_count` and
    `total_spent`. Every customer walked with "Next" — the whole needs-reply queue — was
    announced as "0 orders, in total", and `customer_purchase_lookup` raised `TypeError` on
    `len(12)` and deferred after paying for two Shopify reads. A confident sentence that was
    simply false is the worst thing this system can produce, and it was producing one per
    customer.

### Also confirmed and fixed

12. A question in one half of the orb revoked the other half's pending card, and a spoken
    "yes" was answered with the other half's card. `revoke_pending` and `_waiting_proposal`
    walked every proposal in the session. Both are branch-scoped now, and `advance_epoch`
    carries the other half's proposals forward rather than leaving them behind at a position
    that is not theirs.
13. An undo carried no branch, so it escaped every branch guard: it could be armed and
    committed from a half that had been put aside or closed. It inherits its forward change's
    branch now, `_waiting` counts it, and `/actions/{id}/arm` performs the same branch refusal
    the commit route does — which its own docstring had promised.
14. The comparison the owner asked for was requested, paid for in query cost, and thrown
    away: the render looked for `revenue_pct`, and the engine's shape is
    `{metric: {from, to, delta, pct}}`.
15. `_best_sellers_plan` defaulted to thirty days over `period_from`'s deliberate refusal, so
    "what sold best this week compared to last week" was answered with a month.
16. Counts were the row limit spoken as the truth: "25 orders are unfulfilled" against 61.
    `row_count` and `truncated` are read now.
17. A cache still filling produced "Nothing sold in last_week" with no hedge. The read's own
    `complete` and `note` are part of the answer now — and the period is spoken as a period,
    not as a slug with underscores in it.
18. The delayed-orders window was thirty days where the read layer's own catalogue uses
    ninety, so the order that had been waiting forty-five days was exactly the one that could
    not be seen. It costs 943 ms instead of 246 ms and is worth every one of them.
19. A customer's name reached the timeline on every turn, through `Signals.as_dict()`. The
    record says a name was recognised; it does not say which.
20. An address the owner asked to be read out reached the timeline in the answer. The turn
    log has always redacted by shape and by the exact names a turn's tools returned; the
    timeline does it now too, and the report built from it inherits it.
21. `session.branches` grew for ever; `Prefetcher.start` counted finished tasks against its
    in-flight limit, stopping prefetch for twelve seconds after three quick reads;
    `rows.resolve` did not check that an action belongs to the kind of row it was offered on;
    `assert_read_only` skipped a tool name the registry does not carry instead of failing
    closed; `session.last_query` was clobbered with None by every fast analytics answer,
    destroying the follow-up hint the tool had just written; the cursor started at 0 down one
    path and −1 down the other, so "Next" meant the first member or the second depending on
    which had opened the set; and "what did you do?" was answered with a capability blurb.

Sixteen tests, named for what happened, hold all of it.

## Rejected

* *"The fast lane should answer 'what is the address on 1938' too."* It scores 0.70 against
  a floor of 0.72 and would defer anyway on the entity check, because `1938` without the
  word "order" is not a spoken order number. Correct as it stands: the number is ambiguous
  and the model can ask.
* *"`_thread_fingerprint` accepting a draft by Gmail's id weakens the proof."* It does not.
  The id is one Gmail handed back to THIS commit, and before the change there is no such id,
  so the precondition still counts nothing. It removes a false UNVERIFIED, not a real one.
* *"The prefetcher and the coalescer are unwired, so the branch cancel's 'speculative reads
  are dropped' is vacuous."* Correct as an observation and recorded as a limitation rather
  than a fix: both are built, bounded and tested, and neither is called from a turn yet. They
  are wired the moment a recipe wants them; wiring them speculatively now, with nothing asking,
  would be adding a moving part to production for a benchmark.
* *"Two concurrent read plans give eight simultaneous Shopify calls, not four."* True, and it
  cannot happen today: the provider serialises turns behind one lock, so two plans are never
  in flight. It becomes real the moment two halves think at once, which is the next piece of
  work and is recorded as such in FOUNDATION_PASS.md.
* *"The order card's tabs hide information."* Every section is still on the card, behind its
  own tab, and the telemetry snapshot now names the tabs — so a report can tell "the owner
  never found the Email tab" from "there was no Email tab". The alternative was measured on
  9 September: 7,524 pixels against 655, and 131 scrolls.
