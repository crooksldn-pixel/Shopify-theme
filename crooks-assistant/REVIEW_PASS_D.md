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

## Rejected

* *"The fast lane should answer 'what is the address on 1938' too."* It scores 0.70 against
  a floor of 0.72 and would defer anyway on the entity check, because `1938` without the
  word "order" is not a spoken order number. Correct as it stands: the number is ambiguous
  and the model can ask.
* *"`_thread_fingerprint` accepting a draft by Gmail's id weakens the proof."* It does not.
  The id is one Gmail handed back to THIS commit, and before the change there is no such id,
  so the precondition still counts nothing. It removes a false UNVERIFIED, not a real one.
* *"The order card's tabs hide information."* Every section is still on the card, behind its
  own tab, and the telemetry snapshot now names the tabs — so a report can tell "the owner
  never found the Email tab" from "there was no Email tab". The alternative was measured on
  9 September: 7,524 pixels against 655, and 131 scrolls.
