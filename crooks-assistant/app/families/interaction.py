"""The sentences that are aimed at the interaction, not at the shop (§24, and the unrouted list).

`turn_82ff85cbbc7f` of the live session is one word:

    "Stop"

It routed to no family, so a language model was asked what to do about it, and it answered —
which is the one thing "Stop" cannot mean. An interruption that produces a paragraph is not an
interruption. And nine of the evening's twenty-one unrouted request shapes are like it: "hi",
"crooks os", "are you working right now?" — three words or fewer, aimed at the assistant
itself, each one costing a round trip to a model to be told something the Mac already knew.

So three families, all deterministic, none of them reading anything:

* **`interaction_stop`** — stop. Stops the voice that is speaking, drops any control that was
  waiting for words, and stops the background half's display on request. It does not undo, it
  does not withdraw a change, and it does not answer at length: the whole point is that the
  turn ends.
* **`greeting`** — "hi", "hello", "crooks", "crooks os". One line, and it claims NOTHING: the
  live session's answers to this shape were capability blurbs, and a greeting is not a request
  for a manifest.
* **`assistant_status`** — "are you working right now?", "are you okay?". True by construction:
  the Mac is answering, so it is running. It says what it is doing from state it already
  holds and invents nothing.

The two conversational families are `kind=STATUS` (app/fastpath/intent.py), so neither can take
a turn away from actual work: "are you okay now? pull up today's emails" answers the emails and
acknowledges the health question in a clause, which is §14's rule.

Read-only. No recipe here names a tool at all, so `assert_read_only` holds trivially, and
nothing here can stage a change.
"""

from __future__ import annotations

import logging
from typing import Any

from app.commands import Command, Outcome
from app.commands import Ctx as CommandCtx
from app.commands import register as register_command
from app.fastpath.intent import STATUS, Family, extend, signal
from app.fastpath.models import Ctx, FastAnswer
from app.fastpath.recipes import CACHE_NONE, Recipe, register
from app.reads.scheduler import ReadPlan, ReadResult

log = logging.getLogger("crooks.families.interaction")

# ------------------------------------------------------------------------------ the words

# "Stop", and the ways it is said. Every one of them is an interruption and nothing else: none
# of these can name a record, so none of them can be a request about the shop.
STOP_WORDS = frozenset({"stop", "quiet", "shush", "hush", "enough", "cancel"})
# What may stand beside it without changing what it means. "Stop talking", "stop it", "stop
# that", "be quiet", "shut up", "stop please".
STOP_COMPANIONS = frozenset({
    "it", "that", "this", "there", "now", "please", "talking", "speaking", "reading", "you",
    "yourself", "up", "be", "just", "ok", "okay", "right", "and", "the", "a", "listening",
    "doing", "shut", "hold", "on", "off", "no", "nope",
})
# "Cancel" is in STOP_WORDS and is also a mutation verb, which is deliberate and bounded: a
# BARE "cancel" is an interruption, and "cancel order 1938" is a change the fast lane must not
# touch. The order-number and entity blocks below are what keep them apart, and the family
# does not declare `serves_mutation_words`, so a mutation sentence cannot reach it at all.

GREETINGS = frozenset({
    "hi", "hello", "hey", "yo", "morning", "afternoon", "evening", "alright", "hiya",
    "crooks", "os", "assistant", "there", "you", "again", "mate",
})
# A greeting must have at least one of these in it. Without this, "there you are" and "os"
# alone would be read as hellos.
GREETING_HEADS = frozenset({"hi", "hello", "hey", "yo", "hiya", "alright", "crooks", "morning"})

# "Are you working right now?" "Are you okay?" "Are you there?" "Are you up?"
STATUS_SUBJECT = frozenset({"you", "your", "yourself", "it", "everything", "this"})
STATUS_WORDS = frozenset({
    "working", "work", "works", "okay", "ok", "alright", "fine", "there", "up", "running",
    "alive", "awake", "listening", "ready", "broken", "down", "dead", "back", "on",
})
STATUS_FRAMES = frozenset({"are", "is", "you", "everything", "still", "now", "right", "yet", "do"})


def _only(words: tuple[str, ...], allowed: frozenset[str]) -> bool:
    """Whether the sentence is made of nothing but these words. The bound that makes these
    families safe: a sentence with one word outside the set is somebody else's."""
    return bool(words) and all(w in allowed for w in words)


def _says_stop(sig: Any) -> bool:
    words = tuple(sig.words)
    if not words or not (set(words) & STOP_WORDS):
        return False
    return _only(words, STOP_WORDS | STOP_COMPANIONS)


def _says_hello(sig: Any) -> bool:
    words = tuple(sig.words)
    if not (set(words) & GREETING_HEADS):
        return False
    return _only(words, GREETINGS)


def _asks_how_it_is(sig: Any) -> bool:
    words = set(sig.words)
    if not (words & STATUS_WORDS) or not (words & STATUS_SUBJECT):
        return False
    return _only(tuple(sig.words), STATUS_WORDS | STATUS_SUBJECT | STATUS_FRAMES)


_SAYS_STOP = signal("says_stop", _says_stop)
_SAYS_HELLO = signal("says_hello", _says_hello)
_ASKS_HOW_IT_IS = signal("asks_how_it_is", _asks_how_it_is)


# ------------------------------------------------------------------------------- stopping


def _stop(runtime: Any, session: Any, branch: Any) -> dict[str, Any]:
    """Everything an interruption stops, and nothing it does not.

    Three things, which are §24's three, and each is state the Mac already owns:

    * the VOICE. Any answer still being synthesised is dropped, so the tablet is not handed
      audio for a sentence the owner has already stopped listening to.
    * the WAITING CONTROL. A tapped Reply or Add a note is armed for the next sentence; "stop"
      is not that sentence, and leaving it armed means the next thing said is swallowed.
    * the BACKGROUND DISPLAY. A half working in the background pulses at him. Asked to stop,
      it stops asking for his attention; it is NOT cancelled, because he did not say cancel.

    Nothing is undone and nothing is withdrawn. A staged change is the action engine's, and an
    interruption is not an authorisation to throw one away.
    """
    stopped: dict[str, Any] = {}
    voice = getattr(runtime, "voice", None)
    if voice is not None and hasattr(voice, "cancel_prefetches"):
        try:
            stopped["voice"] = int(voice.cancel_prefetches())
        except Exception as exc:  # noqa: BLE001 — a voice that cannot be stopped is not a crash
            log.warning("the voice could not be stopped: %s", exc)
    if branch is not None and getattr(branch, "voice_context", None):
        branch.release_voice()
        stopped["listening"] = True
    quietened = 0
    for half in (getattr(session, "branches", {}) or {}).values():
        if half is branch or str(getattr(half, "status", "")) != "BACKGROUND":
            continue
        if getattr(half, "task", None):
            # Still working, and no longer asking to be looked at. `idle()` is the branch's own
            # word for "nothing to report" (app/session/branch.py).
            half.idle()
            quietened += 1
    if quietened:
        stopped["background"] = quietened
    return stopped


def _stop_plan(ctx: Ctx) -> ReadPlan | None:
    """Nothing is read. The stopping happens here rather than in the render, because it must
    happen whether or not there is anything to say afterwards."""
    ctx.moved = {"stopped": _stop(ctx.runtime, ctx.session, ctx.branch)}
    return None


def _stop_render(ctx: Ctx, result: ReadResult) -> FastAnswer:    # noqa: ARG001 — nothing was read
    """The shortest true sentence, and no card.

    The live session's "Stop" was answered by a model, at length. What the owner wants back is
    an acknowledgement he can talk over — so: what stopped, in as many words as that takes,
    and nothing about what the assistant could do instead.
    """
    stopped = dict((ctx.moved or {}).get("stopped") or {})
    said = []
    if stopped.get("listening"):
        said.append("not listening for that any more")
    if stopped.get("background"):
        said.append("the other half will keep quiet")
    words = "Stopped." if not said else "Stopped — " + ", ".join(said) + "."
    return FastAnswer(answer=words, trace={"source": "interaction", **stopped})


register(Recipe(
    recipe_id="interaction_stop", intent_family="interaction_stop", read_primitives=(),
    ui="assistant", cache_policy=CACHE_NONE, min_confidence=0.72, target_ms=20,
    plan=_stop_plan, render=_stop_render,
))


def _stop_command(ctx: CommandCtx) -> Outcome:
    """The same interruption, tapped. One implementation, reached two ways — the rule
    app/commands.py exists for."""
    stopped = _stop(ctx.runtime, ctx.session, ctx.branch)
    return Outcome(answer="Stopped.", changed={"stopped": stopped, "listening_for": None})


register_command(Command("interaction.stop", "Stop the voice and stop listening", _stop_command))


# ---------------------------------------------------------------------------- hello, and how


def _nothing(ctx: Ctx) -> ReadPlan | None:      # noqa: ARG001 — nothing is read
    return None


def _greeting_render(ctx: Ctx, result: ReadResult) -> FastAnswer:   # noqa: ARG001
    """One line, and no claim.

    Not a capability blurb. The unrouted "hi" and "crooks os" of the live session went to a
    model, and a model asked to greet somebody with a tool manifest in its prompt greets them
    with the manifest. This says the Mac is here and stops.
    """
    return FastAnswer(answer="I'm here. Ask me something.", trace={"source": "interaction"})


def _status_render(ctx: Ctx, result: ReadResult) -> FastAnswer:     # noqa: ARG001
    """How the assistant is, from state it holds.

    True by construction on the first clause — it is answering, so it is running — and
    everything after that is read, never guessed: whether this half is in the middle of
    something, and whether the other half is.
    """
    from app.capabilities import screen as screen_mod

    here = screen_mod.state(ctx.session, ctx.branch)
    parts = ["Yes — running and listening."]
    state = ctx.branch.state() if hasattr(ctx.branch, "state") else ""
    if state in ("WORKING", "WAITING"):
        what = str((getattr(ctx.branch, "task", None) or {}).get("what") or "").strip()
        parts.append(f"This half is still {state.lower()}" + (f" on {what}." if what else "."))
    elif here.cards:
        parts.append(f"{len(here.cards)} card{'s' if len(here.cards) != 1 else ''} on the deck.")
    else:
        parts.append("Nothing has been drawn on the deck yet.")
    return FastAnswer(answer=" ".join(parts), trace={"source": "interaction", "state": state or None})


register(Recipe(
    recipe_id="greeting", intent_family="greeting", read_primitives=(),
    ui="assistant", cache_policy=CACHE_NONE, min_confidence=0.72, target_ms=20,
    plan=_nothing, render=_greeting_render,
))
register(Recipe(
    recipe_id="assistant_status", intent_family="assistant_status", read_primitives=(),
    ui="assistant", cache_policy=CACHE_NONE, min_confidence=0.72, target_ms=20,
    plan=_nothing, render=_status_render,
))


# --------------------------------------------------------------------------- registration

extend([
    # "Stop." Highest base in the router, because an interruption that has to compete is not
    # an interruption — and its signal is already the tightest in the file: the sentence must
    # be made of nothing but the words of stopping. Blocked by an order number and by a named
    # person, so "cancel order 1938" and "stop David's order" cannot reach it.
    Family("interaction_stop", needs=(_SAYS_STOP,),
           blocks=("order_number", "names_a_person", "period", "metric", "ranking", "email",
                   "order", "customer", "stock", "running_out", "delayed", "address", "status",
                   "bought", "waiting", "unfulfilled", "international", "has_address",
                   "has_compose", "rewrite"),
           base=0.97, floor=0.72, max_words=5, kind=STATUS),
    # "Hi." "Crooks OS." A hello, and nothing else in it.
    Family("greeting", needs=(_SAYS_HELLO,), blocks=("mutation", "order_number"),
           base=0.9, floor=0.72, max_words=4, kind=STATUS),
    # "Are you working right now?" Below the capability families' floor is not the point —
    # this is a different question, and `capability_summary` needs a word of ABILITY that none
    # of these sentences has.
    Family("assistant_status", needs=(_ASKS_HOW_IT_IS,), boosts=("question",),
           blocks=("mutation", "order_number", "period", "metric", "ranking", "email",
                   "order", "customer", "stock", "running_out", "delayed", "bought"),
           base=0.86, floor=0.72, max_words=6, kind=STATUS),
])
