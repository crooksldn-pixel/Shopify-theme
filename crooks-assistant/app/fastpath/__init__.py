"""The fast lane.

Most of what the owner says to a tablet on a workbench is not a new problem. "Next." "Order
1938." "What about last week?" "What can you do now?" Each of those has one right procedure,
the Mac knows it, and asking a language model to rediscover it costs thirty seconds.

Three modules:

    intent.py   what was asked, as structure: family, entities, confidence
    recipes.py  the procedure for a family: which reads, in what order, into which card
    runner.py   run one, from the branch state the conversation already holds

The fast lane is READ ONLY and NAVIGATION ONLY. A recipe cannot stage, arm or commit a
change: `recipes.assert_read_only()` is checked at import and again before every run. Any
request carrying a mutation verb leaves the fast lane before its intent is even scored.

When confidence is short, or a required entity does not resolve, the turn goes to Claude as
it always did. Being fast is never a reason to answer the wrong question.
"""

from app.fastpath.intent import Intent, resolve
from app.fastpath.lanes import DEEP, FAST, NORMAL, choose_lane
from app.fastpath.recipes import RECIPES, Recipe, recipe_for
from app.fastpath.runner import FastAnswer, run

__all__ = ["DEEP", "FAST", "NORMAL", "FastAnswer", "Intent", "RECIPES", "Recipe", "choose_lane", "recipe_for", "resolve", "run"]
