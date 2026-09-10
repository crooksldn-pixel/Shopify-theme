"""Tapping a control that expects words, and then saying them.

The behaviour: tapping [Rewrite] on a draft binds that draft, the tablet shows what it is
listening for, and the next thing said applies to it without the owner naming it again.

The properties that matter are the ones about NOT applying: a binding belongs to one half of
the orb, lasts one sentence, and expires. Each of those is a way the right words could be
applied to the wrong record, which is worse than not being applied at all.
"""

from __future__ import annotations

import pytest

from experience.harness import harness


@pytest.fixture()
async def stage():
    async with harness() as h:
        yield h


async def test_tapping_a_spoken_control_binds_what_is_open(stage):
    await stage.say("show me order 1938", session_id="tv")
    tapped = await stage.touch("voice.bind", family="order.add_note", session_id="tv")
    assert tapped.raw.get("ok") is True, tapped.raw
    listening = (tapped.raw.get("changed") or {}).get("listening_for") or {}
    assert listening.get("family") == "order.add_note"
    branch = stage.branch("tv")
    target = branch.voice_target()
    assert target and target["kind"] == "order"
    assert target["ref"] == "gid://shopify/Order/1938"


async def test_the_tablet_is_told_what_it_is_listening_for(stage):
    await stage.say("show me order 1938", session_id="tv2")
    await stage.touch("voice.bind", family="order.add_note", session_id="tv2")
    branch = stage.branch("tv2").public()
    assert (branch.get("listening_for") or {}).get("family") == "order.add_note"


async def test_the_next_sentence_carries_the_binding_and_only_the_next(stage):
    await stage.say("show me order 1938", session_id="tv3")
    await stage.touch("voice.bind", family="order.add_note", session_id="tv3")
    await stage.say("he rang about the sizing", session_id="tv3")
    asked = stage.provider.calls[-1] if stage.provider.calls else ""
    assert "order.add_note" in asked, f"the binding did not reach the turn: {asked!r}"
    assert "gid://shopify/Order/1938" in asked, "the record was not named to the model"
    assert stage.branch("tv3").voice_target() is None, "the binding outlived its sentence"


async def test_a_binding_does_not_leak_across_the_split(stage):
    """The point of holding it on the branch. A continuation armed on one half must never
    catch a sentence spoken to the other."""
    session = "tv4"
    await stage.say("show me order 1938", session_id=session)
    fork = await stage.client.post(
        "/branches/fork", data={"session_id": session, "label": "right"},
        headers={"Tailscale-User-Login": "owner@example.com", "X-Forwarded-For": "100.64.0.9"},
    )
    body = fork.json()
    right_id = str((body.get("branch") or {}).get("branch_id") or body.get("branch_id") or "")
    assert right_id, body
    await stage.touch("voice.bind", family="order.add_note", session_id=session)
    before = len(stage.provider.calls)
    await stage.say("what about this one", session_id=session, branch_id=right_id)
    spoken_to_the_other_half = stage.provider.calls[before:]
    assert not any("order.add_note" in c for c in spoken_to_the_other_half), (
        "a continuation armed on one half was applied to the other"
    )
    assert stage.branch(session).voice_target() is not None, "the armed half lost its binding"


async def test_a_binding_expires(stage):
    await stage.say("show me order 1938", session_id="tv5")
    branch = stage.branch("tv5")
    branch.bind_voice("order.add_note", kind="order", ref="gid://shopify/Order/1938",
                      clock=lambda: 1000.0)
    assert branch.voice_target(clock=lambda: 1000.0 + 5) is not None
    assert branch.voice_target(clock=lambda: 1000.0 + branch.VOICE_CONTEXT_TTL_S + 1) is None
    assert branch.voice_context is None, "an expired binding is dropped, not kept"


async def test_binding_a_control_with_nothing_open_is_refused(stage):
    # A conversation, but nothing on screen to apply words to: asking what the assistant can
    # do opens no record.
    await stage.say("what can you do now?", session_id="tv6")
    tapped = await stage.touch("voice.bind", family="email.rewrite", session_id="tv6")
    assert tapped.raw.get("ok") is False
    assert tapped.raw.get("code") == "no_target", tapped.raw


async def test_an_unknown_control_is_refused(stage):
    await stage.say("show me order 1938", session_id="tv7")
    tapped = await stage.touch("voice.bind", family="order.detonate", session_id="tv7")
    assert tapped.raw.get("ok") is False
    assert tapped.raw.get("code") == "unknown_control", tapped.raw


async def test_cancelling_stops_the_listening(stage):
    await stage.say("show me order 1938", session_id="tv8")
    await stage.touch("voice.bind", family="order.add_note", session_id="tv8")
    await stage.touch("voice.cancel", session_id="tv8")
    assert stage.branch("tv8").voice_target() is None


async def test_the_owner_is_shown_his_own_words_not_the_note_added_for_the_model(stage):
    """The continuation note is an instruction to the model, not a transcript.

    `_with_continuation` rebound `text` itself, so everything downstream read the annotated
    string as what the owner had said: `live.heard`, which /state returns and the tablet prints
    under the orb, and `question`, which the payload carries and the turn log records. Tapping
    Note and saying "make it shorter" showed those words back with a machine instruction
    stapled on. The model still needs the note — that is the whole point of binding a control —
    so the two are simply kept apart.
    """
    said = "make it shorter and more apologetic"
    await stage.say("show me order 1938", session_id="tv9")
    await stage.touch("voice.bind", family="order.add_note", session_id="tv9")

    before = len(stage.provider.calls)
    answered = await stage.say(said, session_id="tv9")

    assert answered.raw.get("question") == said, answered.raw.get("question")
    assert "[" not in str(answered.raw.get("question") or ""), "a bracketed note reached the owner"

    # And the model was told what the words apply to, which is why the binding exists.
    asked = " ".join(str(getattr(c, "prompt", c)) for c in stage.provider.calls[before:])
    assert "order.add_note" in asked or "1938" in asked, "the model lost the continuation"


def test_every_fast_path_family_is_classified_against_the_continuation_glue():
    """A new family that nobody classified is a sentence the glue can swallow.

    `_is_a_command` decides from the family the router resolved, which is the right way round
    — it holds for however the thing is said. But the two sets it reads were hand-written for
    the families that existed when the glue was, and a family added since is silently absent
    from both: tap Note on #1938, say "open the inbox", and the model was handed the words as
    note text with an instruction to apply them to that order and nothing else.

    So the rule, as a test: every family the router can resolve is either an instruction to
    the assistant or names its own subject. Dictation is what does NOT resolve to a confident
    family (see the comment above the sets), so there is no third case to leave a hole for.
    """
    from app.families import load_all
    from app.fastpath import intent
    from app.routes import turn

    load_all()
    registered = {f.name for f in intent.all_families()}
    assert len(registered) > 20, "the family table did not load — the check would pass vacuously"
    classified = turn._NEVER_A_CONTINUATION | turn._CARRIES_ITS_OWN_SUBJECT
    missing = sorted(registered - classified)
    assert not missing, (
        "these families are in neither set, so a tapped control would take their sentences "
        f"as dictation: {missing}"
    )
