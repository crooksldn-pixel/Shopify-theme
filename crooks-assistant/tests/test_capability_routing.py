"""§5: "can you" is not a capability question, and a named person outranks the record in focus.

Two rules, one file, because they are the same mistake twice: the router decided what a
sentence was about from a frame at the front of it instead of from what followed.

    §5   "can you" + anything  →  capability_summary.  D-5's first turn asked to expand a
         customer's page and got a 1,014-pixel list of what the product can do.
    D-14 a pronoun and a held record  →  the held record wins, even when the words NAMED
         somebody else. One turn spoke customer B's order history in answer to a question
         about customer A, as a statement of fact, out loud.

D-14's note is worth keeping in view while reading the assertions: the report scored that turn
`backend=READ_OK / visible=DRAWN / experience=SUCCESSFUL`. Both tools returned 200 and a card
was drawn. So every assertion here is about the ENTITY in the answer, never about a tool's
return code.
"""

from __future__ import annotations

import pytest

from app.capabilities import ask
from app.families import load_all
from app.fastpath.intent import CAPABILITY, kind_of, resolve
from app.fastpath.recipes import RECIPES
from app.session.branch import Branch
from app.session.models import Session

load_all()
import app.fastpath.library  # noqa: E402, F401 — registers the core recipes


@pytest.fixture()
def branch():
    return Branch(branch_id="br_test", session_id="s1")


@pytest.fixture()
def session():
    return Session(session_id="s1")


# ----------------------------------------------------------------- §5's six required cases

# Exactly the six the brief lists, with what each one IS. The sixth is the only capability
# question among them.
SIX = [
    ("Can you show today's orders?", ask.TASK),
    ("Can you open David Harding?", ask.NAVIGATION),
    ("Can you find his emails?", ask.TASK),
    ("Can you pull up his order history?", ask.TASK),
    ("Can you refund this?", ask.ACTION),
    ("Can you access refunds?", ask.CAPABILITY),
]


@pytest.mark.parametrize(("said", "kind"), SIX)
def test_the_six_cases_are_read_as_what_they_are(said, kind, branch):
    assert ask.classify_text(said, branch=branch) == kind, said


@pytest.mark.parametrize(("said", "kind"), SIX)
def test_only_the_capability_question_reaches_a_capability_family(said, kind, branch):
    """The assertion §5 asks for. Five of the six must not route to capability_summary; the
    sixth must."""
    family = resolve(said, branch=branch).family
    if kind == ask.CAPABILITY:
        assert family == "capability_summary", f"{said!r} → {family or '(the model)'}"
    else:
        assert kind_of(family) != CAPABILITY, f"{said!r} → {family!r}"
        assert family != "capability_summary", f"{said!r} → {family!r}"


def test_the_words_can_you_never_decide_anything_by_themselves(branch):
    """The rule as one statement: the same opener, eight different operations, and not one of
    them a question about the assistant."""
    for tail in ("show today's orders", "open David Harding", "find his emails",
                 "pull up his order history", "refund this", "expand his customer page",
                 "bring up the inbox", "take me to sales"):
        said = f"Can you {tail}?"
        assert ask.classify_text(said, branch=branch) != ask.CAPABILITY, said
        assert kind_of(resolve(said, branch=branch).family) != CAPABILITY, said


# ------------------------------------------------------- and the neighbours, not undermatched

GENUINE = [
    "what can you do",
    "what can you do?",
    "what else are you able to do",
    "what are your capabilities",
    "Can you access refunds?",
    "Can you access customer records?",
    "are you able to handle refunds?",
    "what are you capable of",
]


@pytest.mark.parametrize("said", GENUINE)
def test_a_genuine_capability_question_still_routes_to_the_capability_summary(said, branch):
    """Do not fix overmatching by creating undermatching. Every one of these names nothing to
    do, which is the whole definition, and every one must still be answered from the
    manifest."""
    assert ask.classify_text(said, branch=branch) == ask.CAPABILITY, said
    assert resolve(said, branch=branch).family == "capability_summary", said


def test_the_delta_question_is_still_the_delta(branch):
    assert resolve("what more can you do now?", branch=branch).family == "capability_delta"
    assert resolve("what else can you do since the last build?", branch=branch).family == "capability_delta"


def test_the_capability_manifest_itself_is_untouched():
    """§2: never regress the capability manifest. The discrimination changed which SENTENCES
    reach it, and nothing about what it says."""
    from app.capabilities.families import all_families
    from app.capabilities.manifest import build, spoken_summary

    manifest = build(build_id="test", writes_enabled=True)
    assert manifest["fingerprint"] and manifest["reads"]
    assert len(spoken_summary(manifest)) > 40
    assert len(all_families()) >= 15, "the capability family table shrank"


def test_show_me_what_you_can_do_is_both_and_still_reaches_the_manifest(branch):
    """A demand for a surface whose OBJECT is the assistant. The object decides, not the verb,
    so this one stays a capability question."""
    assert ask.classify_text("show me what you can do", branch=branch) == ask.CAPABILITY


# --------------------------------------------------------------------- D-14, the false fact


def _customer_b_order(branch) -> None:
    """The state the failing turn was in: an order belonging to customer B in focus.

    `gid://…7655` in the timeline. Its customer is not the person the next sentence names.
    """
    branch.visit("order", "gid://shopify/Order/7655", "#1965")


def test_a_named_person_outranks_the_record_in_focus(branch):
    """The routing half of D-14.

    With an order in focus, "what has <name> ordered in his lifetime" reached
    `customer_history_lookup`, whose plan reads the HELD ORDER and then that order's customer.
    The sentence names somebody; the family that answers from focus must not be able to take
    it.
    """
    _customer_b_order(branch)
    said = "what has David Randall ordered in his lifetime"
    assert ask.names_a_person(resolve(said, branch=branch).signals), "the name was not seen"
    family = resolve(said, branch=branch).family
    assert family != "customer_history_lookup", (
        "the family that answers from the record in focus took a sentence that named somebody else"
    )


def test_the_name_the_words_said_reaches_the_recipe_as_something_to_search_for(branch):
    """A name this conversation has never resolved is still the person the turn is about."""
    _customer_b_order(branch)
    intent = resolve("what has David Randall ordered in his lifetime", branch=branch)
    assert intent.slots.get("name") == "David Randall", intent.slots


def test_the_failing_shape_cannot_recur(branch, session):
    """The plan-level refusal, so the defect cannot come back through a routing change.

    `order_detail` on a held order must not drive a customer-history answer for a turn that
    named someone. Asserted against the plan itself rather than against the router, because
    the router is the part that could change.
    """
    from app.fastpath.models import Ctx

    _customer_b_order(branch)
    said = "what has David Randall ordered in his lifetime"
    ctx = Ctx(runtime=None, session=session, branch=branch,
              intent=resolve(said, branch=branch), text=said)
    assert RECIPES["customer_history_lookup"].plan(ctx) is None, (
        "the held order still drives the history read"
    )


def test_the_named_recipe_resolves_the_name_before_it_reads_anything(branch, session):
    """And the recipe that DOES take it searches for the name first."""
    from app.fastpath.models import Ctx

    _customer_b_order(branch)
    said = "what has David Randall ordered in his lifetime"
    intent = resolve(said, branch=branch)
    recipe = RECIPES.get(intent.family) or RECIPES["customer_purchase_lookup"]
    ctx = Ctx(runtime=None, session=session, branch=branch, intent=intent, text=said)
    plan = recipe.plan(ctx)
    assert plan is not None and plan.reads, f"{recipe.recipe_id} had no plan"
    assert plan.reads[0].tool == "shopify_find_customer", [r.tool for r in plan.reads]


def test_a_pronoun_with_nothing_named_still_answers_from_the_record_in_focus(branch):
    """The case `customer_history_lookup` is FOR, kept working. "What else has this customer
    ordered" names nobody, so the record in focus is the right answer."""
    _customer_b_order(branch)
    assert resolve("what else has this customer ordered", branch=branch).family == "customer_history_lookup"


def test_a_group_of_people_is_not_a_person(branch):
    """"Which customers have spent over two hundred pounds" names nobody. Reading a name out
    of it sent a ranking question down a single-customer lookup and asked the shop for a
    customer called Hundred Pounds."""
    said = "which customers have spent over two hundred pounds"
    assert not ask.names_a_person(resolve(said, branch=branch).signals)
    assert resolve(said, branch=branch).family != "customer_purchase_lookup"


@pytest.mark.parametrize("said", [
    "show me the items",
    "show me the contents",
    "show me the latest order",
    "show me the customer",
    "can you access refunds",
    "what else has this customer ordered",
    "which orders are late",
])
def test_an_ordinary_word_is_never_mistaken_for_a_name(said):
    """The name rule is conservative on purpose: a determiner in front of a word means a
    common noun. Every sentence here lost a working fast path when it was not."""
    assert ask.person_named(said) == "", f"{said!r} → {ask.person_named(said)!r}"


# ----------------------------------------------------------------- D-14, end to end, aloud


@pytest.fixture()
async def stage():
    from experience.harness import harness

    async with harness() as h:
        yield h


async def test_the_answer_names_the_customer_the_words_named(stage):
    """The whole turn, through /turn, with a different customer's order in focus.

    The assertion is on the NAME IN THE ANSWER. Both tools returned 200 on the failing turn
    and a card was drawn; the only thing wrong with it was that it was about the wrong person.
    """
    # Mia's order in focus first, so the branch holds a record belonging to somebody else.
    opened = await stage.say("order 1930")
    assert opened.status == 200, opened.answer
    capture = await stage.say("what has David Randall ordered in his lifetime")
    assert "Randall" in capture.answer, (
        f"asked about David Randall and answered {capture.answer!r}"
    )
    assert "Mia" not in capture.answer, f"answered about the record in focus: {capture.answer!r}"


async def test_the_customer_card_is_the_person_who_was_named(stage):
    """And the card agrees with the sentence. A card for one customer under an answer about
    another is the same defect drawn instead of spoken."""
    await stage.say("order 1930")
    capture = await stage.say("show me David Randall's orders")
    card = capture.data("customer")
    assert card, f"no customer card: {capture.surface_types}"
    assert "Randall" in str(card.get("name") or ""), card.get("name")
