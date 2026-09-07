# Day 1 acceptance test

Eighteen spoken commands, run **from the tablet, in the office, at your normal working
distance**. `scripts/acceptance.py` walks you through them one at a time and records the score.

## Pass criteria

Day 1 passes only when all five hold:

| Measure | Threshold |
|---|---|
| Transcript accuracy after normalisation | ≥ 16 / 18 |
| Correct tool selected | ≥ 17 / 18 |
| Answer accuracy | ≥ 16 / 18 |
| Confidently-wrong answers | **exactly 0** — any one fails the whole run |
| End-to-end latency | median ≤ 4 s, p90 ≤ 6 s |

A confidently-wrong answer is one delivered without hedging that turns out to be false. It fails
the run regardless of the other counts, because it is the failure that destroys trust in the
product. Score it honestly.

## The commands

Replace the bracketed placeholders with real CROOKS values before you run this.

### Orders and sales (5)
1. How many orders have we had today?
2. What did we take yesterday?
3. Find order [REAL ORDER NUMBER].
4. What was in that order?
5. Which orders haven't shipped yet?

### Inventory (2)
6. How many [REAL PRODUCT] in medium do we have?
7. Are we out of stock on anything?

### Customers (2)
8. Look up [REAL CUSTOMER NAME].
9. How many orders has that customer placed?

### Email (3)
10. What emails have I had today?
11. Any customer emails this morning?
12. Read the one about [SUBJECT OF A REAL RECENT EMAIL].

### Cross-system (2)
13. The customer who emailed about order [REAL ORDER NUMBER] — check their order and tell me what's happened.
14. Has the customer from order [REAL ORDER NUMBER] emailed us?

### Conversational follow-ups (2)
15. *(after 3)* When was it shipped?
16. *(after 1)* And how much did that come to?

### Ambiguous (1)
17. What happened with [A FIRST NAME MATCHING TWO CUSTOMERS]'s order?
    → **must ask which one.** Picking one fails.

### Impossible (1)
18. How many orders will we get tomorrow?
    → **must say it cannot know.** Any number fails.
