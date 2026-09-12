"""§24: "Stop" is an interruption, and an interruption that answers is not one.

`turn_82ff85cbbc7f` of the live session is one word — "Stop" — and it routed to no family, so
a language model was asked what to do about it and answered. The rules this file holds:

* stop stops the voice, drops a control that was waiting for words, and quietens a background
  half that was asking for attention
* stop does NOT create a generic model turn
* stop does NOT undo anything and does NOT withdraw a staged change — he said stop, not cancel
* an expected interruption is not logged as a provider error

And the conversational shapes beside it, which were nine of the evening's twenty-one unrouted
requests: "hi", "crooks os", "are you working right now?". Cheap, deterministic, and honest —
no capability claims.
"""

from __future__ import annotations

import pytest

from app.families import load_all
from app.fastpath import choose_lane, recipe_for
from app.fastpath.intent import KIND_RANK, STATUS, WORK, kind_of, resolve
from app.fastpath.models import Ctx
from app.fastpath.recipes import RECIPES, assert_read_only
from app.reads.scheduler import ReadResult
from app.session.branch import Branch
from app.session.models import Session

load_all()
import app.fastpath.library  # noqa: E402, F401 — registers the core recipes


class FakeVoice:
    """A voice that can be stopped, and counts being stopped."""

    def __init__(self) -> None:
        self.cancelled = 0

    def cancel_prefetches(self) -> int:
        self.cancelled += 1
        return 2


class FakeRuntime:
    def __init__(self) -> None:
        self.voice = FakeVoice()


@pytest.fixture()
def branch():
    return Branch(branch_id="br_test", session_id="s1")


@pytest.fixture()
def session(branch):
    live = Session(session_id="s1")
    live.branches = {branch.branch_id: branch}
    live.focused_branch = branch.branch_id
    return live


def _run(text: str, session, branch, runtime=None):
    recipe = RECIPES["interaction_stop"]
    ctx = Ctx(runtime=runtime or FakeRuntime(), session=session, branch=branch,
              intent=resolve(text, branch=branch), text=text)
    assert recipe.plan(ctx) is None, "an interruption reads nothing"
    return recipe.render(ctx, ReadResult()), ctx


# ------------------------------------------------------------------------- it is not a prompt


@pytest.mark.parametrize("said", ["stop", "Stop", "Stop.", "stop it", "stop talking",
                                  "be quiet", "quiet", "enough", "stop please"])
def test_stop_routes_to_the_interruption_and_never_to_the_model(said, branch):
    intent = resolve(said, branch=branch)
    assert intent.family == "interaction_stop", f"{said!r} → {intent.family or '(the model)'}"
    recipe = recipe_for(intent.family)
    assert recipe is not None
    assert choose_lane(intent, recipe=recipe, text=said)[0] == "FAST", (
        "an interruption that has to wait for a model is not an interruption"
    )


def test_the_answer_is_an_acknowledgement_and_not_a_paragraph(session, branch):
    """The live session's "Stop" was answered at length by a model. What comes back now is
    something he can talk over."""
    answer, _ = _run("stop", session, branch)
    assert not answer.deferred, answer.defer
    assert 0 < len(answer.answer) <= 80, answer.answer
    assert not answer.surfaces, "an interruption draws nothing"
    assert "can" not in answer.answer.lower(), f"no capability blurb: {answer.answer!r}"


def test_it_stops_the_voice(session, branch):
    runtime = FakeRuntime()
    answer, _ = _run("stop", session, branch, runtime=runtime)
    assert runtime.voice.cancelled == 1, "the voice being synthesised was not stopped"
    assert answer.trace.get("voice") == 2


def test_it_drops_a_control_that_was_waiting_for_words(session, branch):
    """Tap Add a note, then say "stop". The binding must go, or the next thing said is
    swallowed as note text."""
    branch.bind_voice("order.add_note", kind="order", ref="gid://shopify/Order/1", label="#1938",
                      prompt="Add a note", phrase="Listening for the note")
    assert branch.voice_target() is not None
    answer, _ = _run("stop", session, branch)
    assert branch.voice_target() is None, "still listening for the note"
    assert answer.trace.get("listening") is True
    assert "listening" in answer.answer.lower()


def test_it_quietens_a_background_half_without_cancelling_it(session, branch):
    """§24's third: stop the background display on request. The half keeps its work — he said
    stop, not cancel — and stops asking to be looked at."""
    other = Branch(branch_id="br_other", session_id="s1", label="right", status="BACKGROUND")
    other.ready("the inbox")
    session.branches[other.branch_id] = other
    answer, _ = _run("stop", session, branch)
    assert other.task is None, "the background half is still asking for attention"
    assert other.status == "BACKGROUND", "the half was cancelled, and he did not say cancel"
    assert answer.trace.get("background") == 1


def test_it_withdraws_nothing(session, branch):
    """An interruption is not an authorisation. Anything staged is the action engine's, and
    stop must not throw it away."""
    session.proposals.append(object())
    before = len(session.proposals)
    _run("stop", session, branch)
    assert len(session.proposals) == before, "a staged change was withdrawn by an interruption"
    assert session.epoch == 0, "the epoch moved, which withdraws every pending card"


def test_the_interruption_reads_nothing_and_can_write_nothing():
    recipe = RECIPES["interaction_stop"]
    assert recipe.read_primitives == ()
    assert_read_only({"interaction_stop": recipe})


def test_a_change_with_a_record_in_it_is_not_an_interruption(branch):
    """"Cancel" is in the words of stopping and is also a mutation verb. A BARE cancel is an
    interruption; "cancel order 1938" is a change, and the fast lane must not touch it."""
    for said in ("cancel order 1938", "cancel the order", "stop order 1938 going out",
                 "cancel David Randall's order"):
        assert resolve(said, branch=branch).family != "interaction_stop", said


def test_the_same_interruption_is_reachable_by_a_tap(session, branch):
    """One implementation, two ends — app/commands.py's rule. A tap and the word must not be
    two features that can disagree."""
    from app import commands

    branch.bind_voice("order.add_note", kind="order", ref="gid://shopify/Order/1", label="#1938",
                      prompt="Add a note", phrase="Listening")
    runtime = FakeRuntime()
    outcome = commands.run("interaction.stop", commands.Ctx(runtime, session, branch, {}))
    assert outcome.ok and outcome.changed.get("listening_for") is None
    assert branch.voice_target() is None
    assert runtime.voice.cancelled == 1


# ------------------------------------------------------- an interruption is not a failure


async def test_a_cancelled_prefetch_is_an_interruption_not_a_provider_error():
    """§24's last line, measured on the route that files it.

    A prefetch dropped because the owner moved on was reported to the timeline as
    `ok=False, failure="cancelled"` — his own Stop, in the ElevenLabs failure column. It is
    now `ok=True, interrupted=True`, and the tablet gets 204: there is nothing to say.
    """
    from app.clients.elevenlabs_tts import VoiceUnavailable
    from app.observability import timeline
    from experience.harness import harness

    async with harness() as stage:
        events: list[dict] = []

        def record(kind, **fields):
            events.append({"kind": kind, **fields})

        original = timeline.emit
        timeline.emit = record  # type: ignore[assignment]

        class Interrupted:
            voice_name, model, max_chars, cooling_down = "v", "m", 400, False

            async def take_ready(self, text):
                raise VoiceUnavailable("cancelled", kind="cancelled")

            async def open_stream(self, text):      # pragma: no cover — never reached
                raise AssertionError("a cancelled answer must not be synthesised again")

        stage.runtime.voice = Interrupted()
        try:
            response = await stage.client.post("/speak", json={"text": "Two orders today."})
        finally:
            timeline.emit = original  # type: ignore[assignment]

    assert response.status_code == 204, response.text
    tts = [e for e in events if e["kind"] == "tts"]
    assert tts, "nothing was filed at all"
    assert tts[-1]["ok"] is True and tts[-1].get("interrupted") is True, tts[-1]
    assert "failure" not in tts[-1], f"an expected interruption filed as a failure: {tts[-1]}"


# ------------------------------------------------------------------- the conversational ones


@pytest.mark.parametrize(("said", "family"), [
    ("hi", "greeting"),
    ("hello", "greeting"),
    ("hey", "greeting"),
    ("crooks os", "greeting"),
    ("crooks", "greeting"),
    ("are you working right now?", "assistant_status"),
    ("are you okay?", "assistant_status"),
    ("are you there?", "assistant_status"),
])
def test_the_cheap_ones_are_deterministic(said, family, branch):
    """Nine of the twenty-one unrouted shapes were these. Every one cost a round trip to a
    model to be told something the Mac already knew."""
    intent = resolve(said, branch=branch)
    assert intent.family == family, f"{said!r} → {intent.family or '(the model)'}"
    assert choose_lane(intent, recipe=recipe_for(family), text=said)[0] == "FAST"


def test_a_greeting_claims_nothing(session, branch):
    """"Keep them honest: do not invent capability claims." A hello is not a request for a
    manifest, and the live session answered this shape with capability blurbs."""
    recipe = RECIPES["greeting"]
    ctx = Ctx(runtime=None, session=session, branch=branch, intent=resolve("hi", branch=branch), text="hi")
    answer = recipe.render(ctx, ReadResult())
    assert not answer.deferred
    assert len(answer.answer) <= 60, answer.answer
    for claim in ("orders", "email", "inbox", "refund", "shopify", "gmail", "i can"):
        assert claim not in answer.answer.lower(), f"a capability claim in a hello: {answer.answer!r}"


def test_the_status_answer_is_read_and_not_guessed(session, branch):
    """True by construction on the first clause — it is answering, so it is running — and
    everything after that is state the Mac holds."""
    recipe = RECIPES["assistant_status"]
    said = "are you working right now?"
    ctx = Ctx(runtime=None, session=session, branch=branch, intent=resolve(said, branch=branch), text=said)
    answer = recipe.render(ctx, ReadResult())
    assert not answer.deferred
    assert "running" in answer.answer.lower()
    assert "deck" in answer.answer.lower(), answer.answer
    branch.shown([{"type": "customer", "data": {}}], "x", "y")
    answer = recipe.render(ctx, ReadResult())
    assert "1 card" in answer.answer, answer.answer


def test_none_of_the_three_can_take_a_turn_away_from_work():
    """§14's order: explicit requested work outranks contextual status. All three are STATUS,
    so a sentence that asks for work and says hello answers the work."""
    for family in ("interaction_stop", "greeting", "assistant_status"):
        assert kind_of(family) == STATUS, family
        assert KIND_RANK[kind_of(family)] > KIND_RANK[WORK]


def test_the_conversational_families_read_nothing():
    for family in ("greeting", "assistant_status"):
        assert RECIPES[family].read_primitives == ()
        assert_read_only({family: RECIPES[family]})
