# Workstream D → C: the request shapes that need deterministic routing

Workstream C owns `app/fastpath/intent.py` — the signal vocabulary and the scoring. This
workstream owns the SUMMARY/LIST/ROW surfaces those shapes have to land on
(`app/summaries.py`, `app/analytics/summarise.py`, `app/families/summaries.py`). The families
below are registered from this workstream's own file through the published
`app.fastpath.intent.extend` / `signal` seams, so no shared table was edited. They are listed
here because C is the one who can tell whether they collide with anything else, and because
two of them are cases where the scorer currently gets the wrong answer rather than no answer.

Everything here is measured against `docs/phase5/LIVE_SESSION_FORENSICS.md`.

## The three families, and what each is for

| family | needs | lands on | why it exists |
|---|---|---|---|
| `returning_customers` | `returning` + `period` | `summary_list`, task `returning_customers` | D-4: *"Has anyone bought today that has bought before, a returning customer?"* scored **nothing** — `family=''`, `NORMAL`, 12,116 ms in the model, seven `shopify_customer_history` reads, seven full profile cards. |
| `returning_customers_before` | `bought` + `before` | the same | the same question without the word "returning": *"who bought today that has bought before"*. |
| `orders_attention` | `attention` | `summary_list`, task `orders_attention` | *"which orders need attention"* scored nothing; and **"which orders need my attention today" scored `order_list_period` at 0.81** — a plain listing of every order of the day, which is the right card for a different question. |
| `order_list_summary` | `arrived` + `period` | `summary_list`, task `order_list` | *"what came in yesterday"* scored nothing. It names no noun for an order, so `order_list_period` (which needs `order`) cannot take it. |

## The four signals this workstream registered

Through `signal(name, predicate)`, in `app/families/summaries.py`. Word sets, so C can see
exactly what they claim:

```
returning   returning repeat repeats returned regular regulars loyal
before      before previously prior already past
attention   attention chase chasing chased problem problems wrong stuck urgent outstanding
arrived     (came|come|arrived|arrive|landed) AND (in|through|over)
```

Two deliberate exclusions, both of which C should keep if the vocabulary is ever moved:

* **`again` is NOT in `returning`.** "Show it again" is `order_reopen` (D-8's own turn), and a
  word that means two families means neither.
* **`arrived` requires the preposition.** "in" alone is in half the sentences in the session;
  "came in" / "come through" is an arrival.

## What C may want to look at

1. **`order_list_period` does not block `attention`.** `orders_attention` has a higher base
   (0.74 vs 0.74 with fewer boosts) and wins "which orders need my attention today" on this
   tree — but it wins on scoring rather than on a block, which is weaker than it should be.
   The clean fix is `blocks=("attention",)` on `order_list_period` in
   `app/fastpath/intent.py`, which is C's line, not this workstream's.
   `tests/test_summaries.py::test_the_attention_question_draws_attention_rows_not_a_days_listing`
   is the test that would hold it.

2. **Four more shapes in the session still score nothing** and are not covered here because
   they are not summary questions: *"what needs attention"* and *"anything need attention"*
   (no `order` and no period — they reach `orders_attention` on this tree, which is right),
   and the three D-5 shapes (*"can you expand his customer page"*, *"expand his customer
   page"*, *"no, bring up a UI for the customer's page"*), which belong to whoever owns the
   entity workspace.

3. **§36, the half this workstream can measure.** The three families above reach the glass
   with `model_calls: 0` and one read. The session's own numbers for the same question were
   12,895 ms with 12,116 ms of it in the model. There is nothing left in these three turns for
   the model to be asked.

## What a summary surface promises the routing layer

So that C can rely on it rather than reading this workstream's code:

* **One card.** A summary recipe returns `FastAnswer(surfaces=[one], drawn=[])` — no tool
  cards behind it, no working-set card beside it.
* **One read.** `read_primitives == ("commerce_summary",)`, and
  `tests/test_n_plus_one.py::BOUND` pins one tool call and **zero** per-entity reads.
* **A resolvable tap, or no tap.** Every row that offers one has been checked against the
  same rule `open.entity` applies (`app/summaries.py::destination_for`), before it is drawn
  (§18). A row whose destination does not resolve is drawn as a line.
* **No id anywhere readable.** `assert_human` refuses a `gid://` in any display field at build
  time; the `ref` that carries one is never drawn as text.
