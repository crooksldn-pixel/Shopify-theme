"""POST /turn — the whole product, in one endpoint.

Accepts text (development, and the typed interface that keeps allowance testing cheap) or audio
(the tablet). Both converge on the same agent path, which is what made M11 nearly trivial.
"""

from __future__ import annotations

import asyncio
import base64
import logging
import re
import time
import uuid
from typing import Any

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import JSONResponse

from app.actions.grammar import AFFIRMATION_BLOCKED, affirmation_for, words_for
from app.actions.grammar import FIXED_LINES as GRAMMAR_FIXED_LINES
from app.logging.turnlog import redact
from app.observability import timeline
from app.presentation import present
from app.providers.base import ToolCall
from app.routes.actions import session_matches, writes_context
from app.speech.decode import DecodeError, decode
from app.speech.speakable import to_speakable

log = logging.getLogger("crooks.turn")

router = APIRouter()

MAX_UPLOAD_BYTES = 10_000_000
MAX_TEXT_CHARS = 2_000


def _tool_state(tool_names: list[str]) -> str:
    """The UI state is driven by the tool actually running, never guessed from the question."""
    for name in reversed(tool_names):
        if name.startswith("shopify_"):
            return "CHECKING SHOPIFY"
        if name.startswith("gmail_"):
            return "CHECKING EMAIL"
    return "THINKING"


@router.post("/turn")
async def turn(
    request: Request,
    text: str | None = Form(default=None),
    session_id: str = Form(default=""),
    audio: UploadFile | None = File(default=None),
) -> dict:
    runtime = request.app.state.runtime
    started = time.perf_counter()
    timings: dict[str, float] = {}
    transcript_info: dict | None = None
    expected_turns: int | None = None
    # "I will ask /speak for this answer." Lets the backend start the voice a round trip early.
    speak = False
    # Which half of a divided orb asked. Empty is the focused one, which is the usual case.
    branch_id = ""

    # JSON bodies are what curl and scripts/chat.py send; multipart is what the tablet sends.
    if text is None and audio is None:
        try:
            body = await request.json()
        except Exception:  # noqa: BLE001
            body = {}
        text = body.get("text")
        session_id = body.get("session_id") or session_id
        # A count, whatever shape the client sent it in; "0" must not read as "one turn".
        try:
            expected_turns = int(body.get("turns") or 0) or None
        except (TypeError, ValueError):
            expected_turns = None
        speak = _truthy(body.get("speak"))
        branch_id = str(body.get("branch_id") or "")[:32]
    else:
        form = await request.form()
        form_turns = form.get("turns")
        expected_turns = int(form_turns) if form_turns not in (None, "") else None
        speak = _truthy(form.get("speak"))
        branch_id = str(form.get("branch_id") or "")[:32]

    # The tablet says how many turns it thinks this conversation has had. If the backend has
    # no such session but the tablet believes one exists, the backend restarted (or the
    # session idled out) and the honest answer is "I've lost the thread", not a fresh start
    # that silently forgets what "that order" meant.
    lost_thread = False
    if session_id and expected_turns and not runtime.sessions.exists(session_id):
        lost_thread = True
    session_id = session_id or uuid.uuid4().hex[:12]
    if lost_thread:
        runtime.sessions.drop(session_id)
        await runtime.provider.reset_session(session_id)
    # The session exists from the first moment of the turn: the tablet must not see the last
    # question while this one is heard, and a hold that abandons this question may land at
    # any point from here on — during transcription as much as during Claude's thinking.
    live = runtime.sessions.get_or_create(session_id)
    if not session_matches(live, request):
        # A conversation is its first caller's. Another login on the tailnet that learns the
        # id gets nothing of it: not the thread, not the cards, not the tap.
        log.warning("turn refused: session belongs to another login")
        return JSONResponse(status_code=403, content={"code": "wrong_session", "detail": "That conversation belongs to another login."})
    live.heard = ""
    live.abandoned = False
    # This turn's place in the conversation. A hold that abandons the question, or a later
    # question, moves the session past it; the answer then goes unspoken.
    epoch = live.epoch
    # The turn's id: every tool call, proposal and tablet event it causes is written against
    # it on the test-session timeline (a no-op while no session is on).
    live.turn_id = timeline.new_id("turn")
    if timeline.current().active is not None:
        timeline.emit(
            "turn_started", session_id=session_id, turn_id=live.turn_id, input="audio" if audio is not None else "text",
            turns_before=live.turns, epoch=epoch, lost_thread=lost_thread, focus=(live.context[0] if live.context else None),
            waiting=[p.proposal_id for p in live.proposals if p.status.value == "PENDING" and not p.batch_id] + [b.batch_id for b in live.batches.values() if b.status.value == "PENDING"],
        )

    if audio is not None:
        blob = await audio.read()
        if len(blob) > MAX_UPLOAD_BYTES:
            return await _answer(
                runtime, session_id, "That recording was too long for me to handle.",
                request=request, error_kind="audio_too_large", timings=timings, started=started, speak=speak, epoch=epoch,
            )
        # The Mac says what it is doing while it does it: the tablet reads this rather than
        # guessing from a timer how long the recogniser takes.
        live.set_state("TRANSCRIBING")
        result = await runtime.transcriber.from_blob(blob, filename_hint=audio.filename or "")
        transcript_info = result.as_dict()
        timings.update(result.timings_ms)
        if timeline.current().active is not None:
            stats = transcript_info.get("stats") or {}
            timeline.emit(
                "stt", session_id=session_id, turn_id=live.turn_id, ok=result.ok, engine=result.engine or None, fallback=result.fallback,
                engine_detail=result.engine_detail or None, reason=result.reason or None, raw_text=result.raw_text or None, text=result.text or None,
                audio_s=stats.get("duration_s"), audio_bytes=len(blob), timings=transcript_info.get("timings_ms"),
                matches=transcript_info.get("matches"), order_numbers=transcript_info.get("order_numbers"),
            )
        if not result.ok:
            live.set_state("READY")
            return await _answer(
                runtime, session_id, result.reason, request=request, error_kind="speech",
                timings=timings, started=started, transcript=transcript_info, speak=speak, epoch=epoch,
            )
        text = result.text
        # The normaliser refused to guess between near-identical names; tell the model, so it
        # can search the partial name and ask — rather than silently losing the information.
        if result.normalised and result.normalised.ambiguities:
            notes = "; ".join(
                f"'{a.heard}' could be {' or '.join(a.candidates)}" for a in result.normalised.ambiguities
            )
            text = f"{text}\n[The speech recogniser was unsure: {notes}. Ask if it matters.]"

    if not text or not text.strip():
        live.set_state("READY")
        return await _answer(
            runtime, session_id, "I did not catch that.", request=request, error_kind="empty",
            timings=timings, started=started, transcript=transcript_info, speak=speak, epoch=epoch,
        )
    text = text.strip()[:MAX_TEXT_CHARS]

    # A new instruction, now that there is one. Whatever the assistant proposed under the last
    # one is withdrawn: a proposal is bound to the conversation position it was made in, and
    # this is a new one. A fumbled hold or a recording that said nothing is not an instruction
    # and withdraws nothing; the card the owner was about to tap survives it.
    # A bare "yes" while a card is waiting is not a new instruction and applies nothing; it
    # is answered here, in a fixed sentence, without the model and without withdrawing the
    # card — the owner is told again what applies it. Anything else said is an instruction.
    # Which half of the orb is being spoken to, before anything is withdrawn: a question
    # asked over here is not a new instruction to a card waiting over there.
    branch = live.branch(branch_id)
    # Everything downstream that is handed only the session — the action engine when it
    # stages, working sets when they are created — asks the session which half is speaking.
    live.acting_branch = branch.branch_id
    waiting = _waiting_proposal(runtime, live, branch.branch_id)
    if waiting is not None and is_affirmation(text):
        live.heard = text
        live.set_state("READY")
        # The card is re-presented as it stands: its clock started when it was delivered and
        # a spoken yes does not wind it back. The tablet keeps the card it already shows.
        calls = [ToolCall(name=waiting.tool_name, args={}, ok=True, result={}, proposal_id=waiting.proposal_id)]
        return await _answer(
            runtime, session_id, _affirmation_answer(live, waiting), request=request, timings=timings, started=started,
            transcript=transcript_info, question=text, speak=speak, calls=calls, epoch=epoch, revoked=[],
        )

    # A control was tapped that expects words, and these are the words. The sentence is about
    # the record that was bound when it was tapped, so the owner does not have to name it
    # again — "make it shorter and more apologetic" rather than "rewrite Millie's draft to be
    # shorter and more apologetic". The binding belongs to THIS half of the orb and expires;
    # a sentence spoken to the other half never picks it up (app/session/branch.py).
    # What the owner SAID, kept apart from what the model is told. The continuation note below
    # is an instruction to the model — "[this applies to order #1938]" — and while it was
    # spliced into `text` itself, everything downstream read the annotated string as the
    # transcript: `live.heard`, which /state returns and the tablet prints under the orb, and
    # `question`, which the payload carries and the turn log records. The owner tapped Note,
    # said "make it shorter", and saw his own words come back with a machine instruction
    # stapled to them.
    spoken = text
    continuation = branch.voice_target()
    if continuation:
        branch.release_voice()      # one sentence, one binding, taken or abandoned
        if not _is_a_command(text, branch):
            text = _with_continuation(text, continuation)

    revoked = runtime.actions.revoke_pending(live, "new instruction", branch_id=branch.branch_id) + runtime.batches.revoke_pending(live, "new instruction")
    epoch = runtime.actions.advance_epoch(live, "new instruction", branch_id=branch.branch_id)
    runtime.batches.advance_epoch(live)

    # The hourly catalogue refresh is a Shopify round trip; it runs beside this turn, not
    # in front of it. This question is answered with the catalogue as it stands.
    runtime.refresh_catalogue_soon()

    # ---------------------------------------------------------------- the fast lane
    # Most of what is said to a tablet on a workbench is not a new problem. If the Mac knows
    # the procedure for this one — an order, a customer, a period, "next", "what can you do"
    # — it runs it and answers, with no model on the critical path. A recipe that is not sure
    # defers, and the turn carries on to Claude exactly as it did before.
    live.heard = spoken.strip()
    lane, lane_why, intent, recipe = _route(text, branch)
    if timeline.current().active is not None:
        timeline.emit(
            "lane", session_id=session_id, turn_id=live.turn_id, lane=lane, why=lane_why,
            branch_id=branch.branch_id, recipe_id=(recipe.recipe_id if recipe else None), **intent.public(),
        )
    # What this half is doing, in the owner's words, while it does it. A half he has put
    # aside says this on its own chip rather than taking his attention (brief section 17).
    branch.working(_working_words(lane, intent))
    if lane == "FAST" and recipe is not None:
        # The rail is worked out beside the read, not after it. A fast turn used to answer with
        # `writes` still None — that variable is set further down, on the path the fast lane
        # returns before reaching — so present() built the card with no actions on it and an
        # order looked up quickly offered nothing to do with the order.
        #
        # Beside, though, and not in front. This was an `asyncio.gather` of the two, with a
        # comment claiming the preflight is cached and so costs nothing — which was wrong on
        # both halves. Before that change a read turn never called `writes_context` at all
        # (`_answer` asks for it only when something was proposed), and the scope caches behind
        # it last ten minutes, so every expiry, every restart and every cold tablet paid
        # `WRITE_STATUS_TIMEOUT_S` on the fastest turn in the system: measured, "what can you
        # do now?" went from 24 ms to 1508 ms with a slow scope check. So the preflight starts
        # here and is only waited for by an answer that has a card to hang a rail on. A recipe
        # that draws from its own state — capability, navigation, the end of a list — reads
        # nothing and offers nothing, and now pays nothing.
        preflight = (
            asyncio.create_task(writes_context(request)) if request is not None else None
        )
        fast = await _fast(runtime, live, branch, intent, recipe, text)
        fast_writes = None
        if preflight is not None:
            if fast is not None and fast.calls:
                fast_writes = await preflight
            else:
                preflight.cancel()
        if fast is not None:
            return await _answer(
                runtime, session_id, fast.answer, request=request, timings=timings, started=started,
                transcript=transcript_info, question=spoken.strip(), speak=speak,
                # What is worth looking at, which is not always everything that was read. The
                # reads themselves still reach the log and the timeline, on the line below.
                calls=fast.calls if fast.drawn is None else fast.drawn,
                epoch=epoch, revoked=revoked, tool_calls=_fast_tool_calls(fast.calls),
                lane=lane, recipe_id=recipe.recipe_id, branch=branch, partial=fast.partial,
                surfaces=fast.surfaces, writes=fast_writes,
            )
        lane, lane_why = "NORMAL", "the fast path deferred"

    await _ensure_provider_started(runtime)

    # What was heard, on the session now, so the tablet can show it while Claude thinks
    # rather than only once the answer lands — a mis-heard question is visible at once.
    live.heard = spoken.strip()

    # What the Mac already knows about applying a change from this request, before the model
    # is asked: a change proposed while changes are off must never be announced as something
    # to tap. Asked once per turn (the scope answer is cached), and reused for the card.
    # An order number in the question is looked up before the model is asked: the Mac
    # already knows it is an order number, the lookup is the model's first step anyway, and
    # having the record — and its id issued — saves a model round trip and the stumble of a
    # note proposed for an order that has not been looked up yet. It runs beside the scope
    # preflight, which does not depend on it.
    prefetched: list[ToolCall] = []
    prompt_text = f"{_now_line(runtime)}\n{text.strip()}"
    writes, lookup = await asyncio.gather(
        writes_context(request) if request is not None else _none(),
        _prefetch_order(runtime, live, text, prefetched, timings),
    )
    live.writes_blocked = "" if writes is None or writes["allowed"] else _blocked_words(writes)
    if lookup:
        prompt_text = f"{prompt_text}\n\n{lookup}"
    from app.analytics import sets as working_sets

    set_line = working_sets.prompt_line(live, branch=branch)
    if set_line:
        prompt_text = f"{prompt_text}\n\n{set_line}"
    for extra in _context_lines(live, text, runtime=runtime):
        prompt_text = f"{prompt_text}\n\n{extra}"
    where = _branch_line(branch)
    if where:
        prompt_text = f"{prompt_text}\n\n{where}"
    if timeline.current().active is not None:
        timeline.emit(
            "prefetch", session_id=session_id, turn_id=live.turn_id, order_numbers=spoken_order_numbers(text), hit=bool(lookup),
            ms=(round(timings["prefetch"], 1) if "prefetch" in timings else None), hydrating=live.hydrating is not None, writes_code=(None if writes is None or writes["allowed"] else writes.get("code")),
        )

    # What the model is about to be given, in numbers (brief section 11). Counts only: no
    # part of the prompt is written anywhere, here or on the timeline. Kept apart from
    # `timings`, which is milliseconds and is published as such.
    measures = {"model_input_chars": len(prompt_text), "tool_schema_bytes": _tool_schema_bytes(runtime)}
    t0 = time.perf_counter()
    result = await runtime.provider.turn(session_id, prompt_text)
    timings["agent"] = (time.perf_counter() - t0) * 1000
    for step, ms in getattr(result, "steps", None) or []:
        timings[f"step:{step}"] = ms
    if timeline.current().active is not None:
        timeline.emit(
            "model", session_id=session_id, turn_id=live.turn_id, ms=round(timings["agent"], 1), steps=list(getattr(result, "steps", None) or []),
            error_kind=result.error_kind, stopped_early=result.stopped_early, answer=result.text or None,
            tool_calls=[{"tool": c.name, "ok": c.ok, "tool_call_id": getattr(c, "tool_call_id", "") or None, "proposal_id": c.proposal_id} for c in result.tool_calls or []],
        )
    if prefetched:
        result.tool_calls = _hydrated(live, prefetched + list(result.tool_calls or []))

    answer = result.text or "I could not work out an answer to that."
    if len(answer) > runtime.settings.max_answer_chars:
        # A forty-second spoken monologue is a bad product; truncate at a sentence boundary.
        cut = answer[: runtime.settings.max_answer_chars]
        answer = cut[: cut.rfind(".") + 1] or cut
    if lost_thread and result.error_kind is None:
        # The backend restarted (or the conversation idled out) since the tablet last spoke.
        # It heard the question, so it answers it — from the start, and says so — rather than
        # asking the owner to repeat himself. Only "that order" questions lose anything, and
        # for those Claude asks which one.
        answer = f"{LOST_THREAD_PREFIX}{answer}"

    return await _answer(
        runtime,
        session_id,
        answer,
        request=request,
        error_kind=result.error_kind,
        timings=timings,
        started=started,
        transcript=transcript_info,
        question=spoken.strip(),
        tool_calls=[
            {
                "name": c.name, "ok": c.ok, "error": c.error, "ms": c.duration_ms,
                # Arguments are what make a wrong answer diagnosable in chat.py — redacted,
                # because the model may have put an email address in them. A proposed write's
                # content stays out of the log altogether; the ledger keeps its length.
                "args": _loggable_args(c),
                "proposal_id": c.proposal_id,
                "tool_call_id": getattr(c, "tool_call_id", "") or None,
            }
            for c in result.tool_calls
        ] + [],
        calls=result.tool_calls,
        speak=speak,
        lost_thread=lost_thread,
        epoch=epoch,
        revoked=revoked,
        writes=writes,
        branch=branch,
        measures=measures,
    )


LOST_THREAD_PREFIX = "I lost our earlier thread, so from the start: "


def _written(text: str, names: set[str]) -> str:
    """What the timeline keeps of something spoken. The spoken answer is the owner's and may
    carry a customer's name, an email address or a street; the file it would land in is read
    later, by a person, and may be handed to somebody else. The turn log has always redacted
    by shape and by the exact names this turn's tools returned — this is that, applied to the
    other place an answer is written."""
    from app.logging.turnlog import redact_text

    return redact_text(str(text or ""), names) if text else ""


def _performance(timings: dict, *, lane: str, recipe_id: str, branch, calls, partial: bool, session, measures: dict) -> dict:
    """The turn's own measurements. No content, no arguments, no personal data: counts,
    milliseconds and names of tools."""
    from app.memory import current as memory
    from app.memory.coalesce import current as coalescer
    from app.memory.prefetch import current as prefetcher

    sources: dict[str, float] = {}
    for call in calls or []:
        source = "shopify" if call.name.startswith(("shopify_", "commerce_", "inventory_")) else ("gmail" if call.name.startswith(("gmail_", "email_")) else "mac")
        sources[source] = round(sources.get(source, 0.0) + float(getattr(call, "duration_ms", 0.0) or 0.0), 1)
    model_ms = timings.get("agent")
    model_phases = sum(1 for key in timings if key.startswith("step:model"))
    return {
        "lane": lane,
        "recipe_id": recipe_id or None,
        "fast_path_hit": lane == "FAST",
        "branch_id": getattr(branch, "branch_id", None),
        "parent_branch_id": (getattr(branch, "parent_id", "") or None),
        "backgrounded": getattr(branch, "status", "") == "BACKGROUND",
        "cancelled": bool(getattr(session, "abandoned", False)),
        "partial": bool(partial),
        "tool_calls": len(calls or []),
        "source_ms": sources,
        "stt_ms": round(float(timings.get("transcribe") or timings.get("stt") or 0.0), 1) or None,
        "model_ms": round(float(model_ms), 1) if model_ms is not None else None,
        "model_calls": 0 if lane == "FAST" else 1,
        "model_phases": model_phases or None,
        "model_input_chars": measures.get("model_input_chars"),
        "tool_schema_bytes": measures.get("tool_schema_bytes"),
        "prefetch_ms": round(float(timings["prefetch"]), 1) if "prefetch" in timings else None,
        "turn_total_ms": round(float(timings.get("total") or 0.0), 1),
        "cache": memory().counts(),
        "coalesced": coalescer().counts(),
        "prefetch": prefetcher().counts(),
    }


def _call_summary(call) -> str:
    """A read, in a clause the next turn can be told without re-reading it."""
    body = call.result if isinstance(getattr(call, "result", None), dict) else {}
    for key in ("order_number", "name", "subject", "label", "set_label"):
        if body.get(key):
            return f"{call.name}: {body[key]}"
    for key in ("rows", "orders", "customers", "threads"):
        if isinstance(body.get(key), list):
            return f"{call.name}: {len(body[key])} rows"
    return call.name


def _call_ref(call) -> str:
    body = call.result if isinstance(getattr(call, "result", None), dict) else {}
    for key in ("order_id", "customer_id", "thread_id", "set_id"):
        if body.get(key):
            return str(body[key])
    return ""


_SCHEMA_BYTES: dict[bool, int] = {}


def _tool_schema_bytes(runtime) -> int:
    """The size of the tool block the model is offered, in bytes. Measured once per writes
    setting: the registry does not change while the process runs."""
    import json

    writes = bool(getattr(runtime.settings, "writes_enabled", False))
    if writes not in _SCHEMA_BYTES:
        from app.providers.max_agent_sdk import withheld_tools
        from app.tools import registry

        specs = registry.all_specs()
        withheld = withheld_tools(specs, writes_enabled=writes)
        _SCHEMA_BYTES[writes] = sum(
            len(json.dumps({"name": s.name, "description": s.description, "input_schema": s.input_schema}))
            for s in specs if s.name not in withheld
        )
    return _SCHEMA_BYTES[writes]


def _route(text: str, branch):
    """(lane, why, intent, recipe) for this request. Structure only: no source is touched."""
    from app.fastpath import choose_lane, recipe_for, resolve

    intent = resolve(text, branch=branch)
    recipe = recipe_for(intent.family) if intent.family else None
    lane, why = choose_lane(intent, recipe=recipe, text=text)
    return lane, why, intent, recipe


async def _fast(runtime, session, branch, intent, recipe, text: str):
    """Run a recipe. Returns its answer, or None when it deferred and Claude should answer."""
    from app.fastpath import run as run_recipe
    from app.fastpath.models import Ctx
    from app.memory import current as memory

    session.turns += 1
    session.set_state("THINKING", recipe.recipe_id)
    answer = await run_recipe(recipe, Ctx(runtime=runtime, session=session, branch=branch, intent=intent, text=text, memory=memory()))
    session.set_state("READY")
    if answer.deferred:
        # The turn is about to be answered properly; it was never a second turn.
        session.turns -= 1
        return None
    return answer


# What a lane is doing, said once, in words. Deliberately vague about the work and exact
# about the source: the owner does not need to know which tool, and must never be told what
# the model is thinking.
_WORKING = {
    "order_lookup": "reading the order", "order_status_lookup": "reading the order",
    "order_address_lookup": "reading the order", "customer_purchase_lookup": "reading the customer",
    "best_sellers_period": "adding up the sales", "sales_breakdown_period": "adding up the sales",
    "delayed_orders": "listing what is late", "stock_cover_analysis": "checking stock",
    "needs_reply": "checking the inbox", "inbox_state": "checking the inbox",
    "working_set_next": "reading the next one", "working_set_previous": "reading the last one",
}


def _working_words(lane: str, intent) -> str:
    if lane == "DEEP":
        return "working through it"
    return _WORKING.get(getattr(intent, "family", ""), "working it out")


# Families that are instructions to the assistant rather than words about a record. A
# continuation must not swallow one: tapping Note and then saying "go back" abandons the note,
# it does not write "go back" into it. Deciding this from the family rather than from a list of
# phrases means it holds for however those things are said.
# Sentences that are instructions to the assistant, whatever control was tapped a moment ago.
# Two kinds. These are the ones that command it directly: "go back", "next", "what can you do".
_NEVER_A_CONTINUATION = frozenset({
    "navigation_back", "navigation_home", "working_set_next", "working_set_previous",
    "capability_summary", "capability_delta", "order_reopen",
})
# And these are the ones that NAME THEIR OWN SUBJECT, which the glue would then overrule. Tap
# Add a note on #1938, then ask "how many orders today", and the model was handed
#
#     how many orders today
#     [This continues order.add_note on the order the owner is looking at (#1938) … Apply it
#      to that record and to nothing else.]
#
# — a sales question turned into an instruction about one order's note, and the turn dropped
# off the fast lane on the way. "Show me order 1782" was glued to #1938 the same way.
#
# Dictated note and rewrite text is not in either set, because it does not resolve to a
# confident family: "he wants it by Friday" names no order, no period and no list, so it is
# still taken as the words the tapped control was waiting for. That is the whole distinction —
# a sentence the router can already act on is not dictation.
_CARRIES_ITS_OWN_SUBJECT = frozenset({
    "order_lookup", "order_list_period", "order_status_lookup", "order_address_lookup",
    "customer_history_lookup", "customer_purchase_lookup", "sales_breakdown_period",
    "best_sellers_period", "stock_cover_analysis", "delayed_orders", "inbox_state",
    "needs_reply",
})


def _is_a_command(text: str, branch: Any) -> bool:
    """Whether this sentence is an instruction in its own right.

    Resolved from the words the owner actually said, before any continuation note is added —
    the note is for the model, and routing must not see it.
    """
    from app.fastpath import resolve

    try:
        family = resolve(text, branch=branch).family
    except Exception:  # noqa: BLE001 — a router that cannot decide is not a reason to fail a turn
        return False
    return family in _NEVER_A_CONTINUATION or family in _CARRIES_ITS_OWN_SUBJECT


def _with_continuation(text: str, continuation: dict) -> str:
    """The sentence, with what it applies to said plainly beside it.

    A bracketed note rather than a new mechanism: the recogniser's ambiguity note already uses
    this shape, the model already reads it, and it survives being logged. The reference is the
    record's id and its label — never its contents.
    """
    family = str(continuation.get("family") or "")
    kind = str(continuation.get("kind") or "record").replace("_", " ")
    label = str(continuation.get("label") or "").strip()
    ref = str(continuation.get("ref") or "")
    named = f" ({label})" if label else ""
    return (
        f"{text}\n[This continues {family} on the {kind} the owner is looking at{named}"
        f"{f', id {ref}' if ref else ''}. Apply it to that record and to nothing else.]"
    )


def _fast_tool_calls(calls) -> list[dict]:
    """The fast lane's reads, in the shape the turn log and the tablet already read."""
    return [
        {"name": c.name, "ok": c.ok, "error": c.error, "ms": c.duration_ms, "args": _loggable_args(c),
         "proposal_id": c.proposal_id, "tool_call_id": getattr(c, "tool_call_id", "") or None}
        for c in calls or []
    ]


def _branch_line(branch) -> str:
    """Where the conversation is, in one line, so the model does not spend a tool call
    rediscovering it. Position only — never a permission, and never a whole read."""
    if branch is None:
        return ""
    bits: list[str] = []
    entity = getattr(branch, "entity", None)
    if entity:
        bits.append(f"looking at the {entity['kind']} {entity['label']}")
    workflow = getattr(branch, "workflow", None)
    if workflow is not None and workflow.total:
        bits.append(f"working through {workflow.total} {workflow.kind}, at {workflow.position}")
    recent = getattr(branch, "recent_results", None) or []
    if recent:
        bits.append("just read: " + "; ".join(str(r.get("summary") or "")[:60] for r in recent[:2]))
    return f"[Where we are: {'; '.join(bits)}.]" if bits else ""

# What a spoken yes gets while a card is waiting: the waiting card's own gesture, in a fixed
# sentence — synthesised once and kept, and never a promise: the gesture is the only thing
# that applies anything. The sentences live with the grammar (app/actions/grammar.py).
AFFIRMATION_ANSWER = words_for("tap_commit")["affirmation"]
AFFIRMATION_BLOCKED_ANSWER = AFFIRMATION_BLOCKED
FIXED_LINES = GRAMMAR_FIXED_LINES

def _context_lines(session, text: str, runtime=None) -> list[str]:
    """What the Mac knows that the model would otherwise guess at, one line each: the last
    gesture's counted outcome (once), the last query's shape (for a follow-up), and which
    composable capability the question's words name (so it is reached for, not declined)."""
    from app.observability import claims

    lines: list[str] = []
    outcome = str(getattr(session, "last_outcome", "") or "").strip()
    if outcome:
        lines.append(f'[The last change, as the Mac proved it: "{outcome[:200]}". If asked whether it worked, say this; do not propose it again.]')
        session.last_outcome = ""
    session.hinted = False
    last = getattr(session, "last_query", None)
    if isinstance(last, dict) and last:
        lines.append(f"[Last read-layer query: {_short_query(last)}. A follow-up (\"just this week\", \"by size\", \"only joggers\") is this query with that one thing changed.]")
    # A change the Mac knowingly cannot make: said plainly, with what it can do instead.
    # Without this the September session's "add two items to David Randall's order" was
    # answered as though it had been done (app/observability/contract.py).
    from app.observability import contract as contract_mod

    limitation = contract_mod.limitation_line(text)
    if limitation:
        lines.append(limitation)
    # Drafting and sending are different requests, and the words tell them apart. Said here
    # rather than left to be inferred, because the wrong one is either an email nobody meant
    # to send or a draft nobody asked for.
    wants = _draft_or_send(text)
    if wants:
        lines.append(wants)
    matched = claims.match_capabilities(text)
    if matched:
        known = claims.registered()
        usable = [c for c in matched if all(t in known for t in c.tools)]
        if usable:
            lines.append("[This asks for " + "; ".join(f"{c.what} ({', '.join(c.tools)})" for c in usable[:3]) + " — the Mac composes it; call the tool rather than saying it cannot be done.]")
            session.hinted = True
    lines.extend(_family_lines(runtime))
    return lines


def _family_lines(runtime) -> list[str]:
    """The capability families that are NOT ready, with the reason, so the model stops trying
    them and says why — and the ready ones by name, so it reaches for them. Read from the
    table the last capability check left on the runtime; nothing is probed on the turn."""
    from app.capabilities import families as families_mod

    table = getattr(runtime, "family_states_table", None) if runtime is not None else None
    if not table:
        table = {f.key: {"label": f.label, "state": f.state, "detail": f.detail} for f in families_mod.all_families()}
    if not table:
        return []
    return ["[Capability families on this Mac:\n" + "\n".join(families_mod.words(table)) + "]"]


# "Draft", "prepare", "write me" ask for something to read first. "Send", "email them",
# "let them know" ask for something to go. Both still need the owner's gesture; what differs
# is which change is staged, and staging the wrong one is not a small mistake.
_WANTS_DRAFT = re.compile(r"\b(?:draft|drafts?|prepare|prepared|write me|write out|put together|compose|mock up|rough out|have a go at)\b", re.I)
# "Reply to" is deliberately absent: it names what the email is, not whether it goes. A bare
# "reply to Millie" is left unhinted and the model decides, which is honest — the owner's
# gesture is what sends either way.
_WANTS_SEND = re.compile(r"\b(?:send|sends|email them|email him|email her|email the|let (?:them|him|her) know|tell (?:them|him|her)|get back to|chase|fire (?:it|them) off)\b", re.I)


def _draft_or_send(text: str) -> str:
    draft, send = bool(_WANTS_DRAFT.search(text)), bool(_WANTS_SEND.search(text))
    if draft and not send:
        return "[This asks for a DRAFT: stage gmail_draft_reply or gmail_draft_new, not a send. Nothing leaves the Mac.]"
    if send and not draft:
        return "[This asks for the email to GO: stage gmail_send_reply or gmail_send_new. It still waits for the owner's gesture; a spoken yes never sends it.]"
    if send and draft:
        return "[This says both draft and send. Stage the DRAFT and say that sending it is a second gesture.]"
    return ""


def _short_query(query: dict) -> str:
    import json

    keep = {k: query[k] for k in ("tool", "entity", "period", "filters", "group_by", "metrics", "sort", "limit", "compare") if k in query and query[k] not in (None, [], {}, False)}
    return json.dumps(keep, ensure_ascii=False, default=str)[:300]


def _blocked_words(writes: dict) -> str:
    """Why a tap would be refused, in a clause the model can put in a sentence."""
    return str(writes.get("detail") or "changes cannot be applied from there.").rstrip(".") + "."


def _affirmation_answer(session, waiting=None) -> str:
    """What a spoken yes gets: the waiting card's own gesture, in its fixed sentence."""
    kind = getattr(waiting, "interaction", "tap_commit") if waiting is not None else "tap_commit"
    return affirmation_for(kind, blocked=bool(session.writes_blocked))


# A bare affirmation: a few words that mean "apply it", nothing else. "Yes, and cancel the
# order" is not one; neither is "fine" or "correct", which may answer a question the model
# asked, and must reach it.
_AFFIRMATIONS = frozenset({
    "yes", "yeah", "yep", "yup", "ok", "okay", "go", "go ahead", "go on", "do it", "do that",
    "confirm", "confirmed", "yes please", "please do", "apply it", "add it", "go ahead please",
    "yes do it", "yes go ahead", "ok go ahead", "okay go ahead",
})


def is_affirmation(text: str) -> bool:
    words = re.sub(r"[^a-z' ]+", " ", text.lower()).split()
    if not words or len(words) > 4:
        return False
    return " ".join(words) in _AFFIRMATIONS


def _waiting_proposal(runtime, session, branch_id: str = ""):
    """The one proposal a spoken yes could refer to: pending, unexpired, this epoch, staged
    in THIS half of the orb, and a change the owner asked for — never the undo the Mac
    offered after a success, or "okay" said to "Note added" would be answered as if a card
    were waiting to be tapped; and never the other half's, which he is not looking at."""
    now = time.time()
    for proposal in reversed(session.proposals):
        if (
            proposal.status.value == "PENDING" and proposal.epoch == session.epoch
            and not proposal.expired(now) and proposal.undo_of is None and not proposal.batch_id
            and (not branch_id or str(getattr(proposal, "branch_id", "") or "") in ("", branch_id))
        ):
            return proposal
    # A batch's members are not cards of their own; the batch is the card.
    return runtime.batches.waiting(session)


def _now_line(runtime) -> str:
    """The clock, in the shop's own time zone, at the top of every question. "Yesterday" and
    "this morning" then mean what the owner means, whatever day the model believes it is."""
    from datetime import datetime
    from zoneinfo import ZoneInfo

    try:
        tz = ZoneInfo(runtime.settings.shop_timezone)
    except Exception:  # noqa: BLE001
        tz = None
    now = datetime.now(tz)
    # Day without a leading zero, spelled out here rather than with a strftime flag that
    # differs between the Mac's libc and Linux's.
    return f"[Now: {now.strftime('%A')} {now.day} {now.strftime('%B %Y, %H:%M')} {runtime.settings.shop_timezone}]"


# The lookup ahead of the model gets less time than a tool call the model makes: past this,
# the model does its own looking up and nothing was lost but the head start.
PREFETCH_TIMEOUT_S = 2.5

# An order number the owner SAID: the cue, then the number, and nothing between them but
# "number", "no." or "#". Four digits, because that is what CROOKS issues; not a year unless
# written as a number ("order number 2025", "#2025"); and never "orders over 500 pounds",
# "orders from 2025" or "orders in the last 100 days", which name no order.
_SPOKEN_ORDER = re.compile(
    r"\b(?:order|invoice)\b\s*(?P<explicit>(?:number|no\.?|#)\s*#?\s*)?(?P<digits>\d{4})\b"
    # Not a figure with a unit after it, and not the head of something the recogniser left
    # half-converted ("1930-eight"): a number that runs into a word is not an order number.
    r"(?!\s*(?:pounds?|quid|days?|items?|units?|percent|%|per\b))"
    r"(?![\u2010-\u2015-]?[A-Za-z])",
    re.I,
)


def spoken_order_numbers(text: str) -> list[str]:
    """The order numbers the owner named, if any. CROOKS issues four digits; "order 2025" is
    read as the year unless it was said as a number ("order number 2025", "order #2025")."""
    found: list[str] = []
    for match in _SPOKEN_ORDER.finditer(text):
        digits = match.group("digits")
        looks_like_a_year = 2000 <= int(digits) <= 2099
        if looks_like_a_year and not match.group("explicit"):
            continue
        if digits not in found:
            found.append(digits)
    return found


async def _prefetch_order(runtime, session, text: str, calls: list, timings: dict) -> str:
    """Look one spoken order number up through the same gate the model uses. Returns the
    text to hand the model, or nothing when there was no single order number, or the lookup
    failed (the model then does it itself, as before)."""
    from app.tools.dispatch import dispatch

    numbers = spoken_order_numbers(text)
    if len(numbers) != 1:
        return ""
    number = numbers[0]
    session.set_state("CHECKING SHOPIFY", "shopify_find_order")
    t0 = time.perf_counter()
    try:
        rendered = await dispatch(
            "shopify_find_order", {"query": number}, session=session,
            timeout_s=min(PREFETCH_TIMEOUT_S, runtime.settings.tool_timeout_s), calls=calls,
        )
    finally:
        timings["prefetch"] = (time.perf_counter() - t0) * 1000
    if not calls or not calls[-1].ok:
        calls.clear()
        return ""
    # One order: its full picture is read now, beside the model rather than in front of it.
    # If the model asks for the detail it is answered at once; if it does not, the card still
    # shows the whole order when the read has landed by the time the answer does.
    found = calls[-1].result.get("orders") if isinstance(calls[-1].result, dict) else None
    hydrating = ""
    if isinstance(found, list) and len(found) == 1 and isinstance(found[0], dict) and found[0].get("order_id"):
        session.hydrating = _hydrate_soon(str(found[0]["order_id"]))
        hydrating = (
            " The full order (items, money, address, tracking, the customer's history and their "
            "recent email) is being read beside you: call shopify_order_detail if the answer needs "
            "any of it — it answers at once."
        )
    return (
        f"[The Mac already ran shopify_find_order(query=\"{number}\") for this question. Its result:\n"
        f"{rendered}\nUse it as if you had called the tool; do not call shopify_find_order for "
        f"{number} again.{hydrating}]"
    )


def _hydrate_soon(order_id: str) -> asyncio.Task | None:
    """Start the order's full read in the background. Never awaited by the turn itself."""
    from app.tools.shopify_tools import hydrator

    try:
        return asyncio.get_running_loop().create_task(hydrator().order(order_id))
    except Exception as exc:  # noqa: BLE001 — Shopify not bound; the model looks it up itself
        log.debug("no background hydration: %s", exc)
        return None


def _hydrated(session, calls: list) -> list:
    """The order the Mac read beside the model, as a tool call the card is built from — when
    it landed in time and the model did not read it itself. The ids in it are issued as any
    tool result's are. Nothing is waited for: a read still in flight is collected by the
    tablet from /context/order once the card is up."""
    task = getattr(session, "hydrating", None)
    if task is None:
        return calls
    session.hydrating = None
    if not task.done() or task.cancelled() or task.exception() is not None:
        if task.done() and task.exception() is not None:
            log.debug("background hydration failed: %s", task.exception())
        return calls
    result = task.result()
    if not isinstance(result, dict) or any(c.name == "shopify_order_detail" and c.ok for c in calls):
        return calls
    from app.tools.dispatch import harvest_ids

    harvest_ids(result, session)
    return list(calls) + [ToolCall(name="shopify_order_detail", args={"order_id": result.get("order_id", "")}, ok=True, result=result)]


def _ui_entities(ui: list) -> list[dict]:
    """Which records the cards showed, by kind and id — never their contents."""
    out: list[dict] = []
    for item in ui or []:
        data = item.get("data") if isinstance(item, dict) else None
        if not isinstance(data, dict):
            continue
        kind = str(item.get("type") or "")
        named = item.get("entity") if isinstance(item.get("entity"), dict) else None
        ref = (named or {}).get("ref") or data.get("order_id") or data.get("customer_id") or data.get("thread_id") or data.get("proposal_id") or ""
        if not ref and kind in ("product", "inventory") and isinstance(data.get("products"), list) and data["products"] and isinstance(data["products"][0], dict):
            ref = data["products"][0].get("product_id") or ""
        if ref:
            out.append({"type": kind, "ref": str(ref)[:80]})
    return out


def _loggable_args(call) -> dict:
    """What the turn log keeps of a tool call's arguments. A write tool's content — the note
    the owner dictated — is logged by length only, whether or not it became a proposal: a
    refused or unpreparable note is still the owner's words about a customer."""
    args = call.args or {}
    if call.proposal_id or _is_write_tool(call.name):
        return {k: (str(v)[:80] if k.endswith("_id") else f"<{len(str(v))} chars>") for k, v in args.items()}
    return redact({k: str(v)[:80] for k, v in args.items()})


def _is_write_tool(name: str) -> bool:
    from app.tools import registry

    try:
        spec = registry.get(name)
        return spec.write is not None or spec.batch is not None
    except KeyError:
        return False


async def _none():
    return None


def _truthy(value) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


async def _ensure_provider_started(runtime) -> None:
    """If the provider failed at boot (token not yet stored, say), retry now rather than
    answering "still starting up" until someone restarts the process."""
    provider = runtime.provider
    if getattr(provider, "_started", True):
        return
    try:
        await provider.start()
    except Exception as exc:  # noqa: BLE001
        log.warning("provider start retry failed: %s", exc)


async def _answer(
    runtime,
    session_id: str,
    answer: str,
    *,
    request: Request | None = None,
    error_kind: str | None = None,
    timings: dict,
    started: float,
    transcript: dict | None = None,
    question: str = "",
    tool_calls: list | None = None,
    lost_thread: bool = False,
    calls: list | None = None,
    speak: bool = False,
    epoch: int | None = None,
    revoked: list[str] | None = None,
    writes: dict | None = None,
    lane: str = "NORMAL",
    recipe_id: str = "",
    branch: Any = None,
    partial: bool = False,
    measures: dict | None = None,
    surfaces: list | None = None,
) -> dict:
    tool_calls = tool_calls or []
    turns = 0
    names: set[str] = set()
    session = None
    try:
        session = runtime.sessions.get(session_id)
        turns = session.turns
        names = set(session.pii_seen)
    except KeyError:
        pass
    # Abandoned: the owner cancelled, or asked something else while this was being answered.
    # The session's position has moved past this turn's; nobody is waiting for its voice.
    abandoned = bool(session is not None and (session.abandoned or (epoch is not None and session.epoch != epoch)))
    proposed = [c.proposal_id for c in (calls or []) if getattr(c, "proposal_id", None)]
    if abandoned and proposed:
        # Claude was still running when the owner moved on, and staged a change into the
        # conversation's new position. Nobody asked for it there: withdrawn, unsent.
        runtime.actions.revoke_ids(proposed, "the owner moved on")
        runtime.batches.revoke_ids(proposed, "the owner moved on")
        proposed = []
    # A change was proposed this turn. Say, now and in the same breath, whether a tap on THIS
    # tablet could apply it — a card that cannot be applied must never look as if it can.
    if proposed and writes is None and request is not None:
        writes = await writes_context(request)
    if proposed and writes is not None and not writes["allowed"] and writes["spoken"]:
        answer = f"{answer.rstrip()} {writes['spoken']}"
    # `writes` on the wire is about a proposal: it tells the tablet whether a tap on the card
    # this turn produced could apply it, and on a turn that proposed nothing there is nothing
    # for it to describe. But the same table is also where the order card's rail comes from —
    # which changes make sense for THIS order and which the store has granted — and a read
    # turn is exactly when the rail matters. Nulling the one variable did both, so every
    # order looked up came back with an empty `actions` list and nothing to do with it. The
    # rail keeps the table; the payload keeps its old contract.
    rail = writes
    if not proposed:
        writes = None
    # The card leaves for the tablet now; its wait for the tap starts now.
    for proposal_id in proposed:
        if proposal_id.startswith("batch_"):
            runtime.batches.deliver(proposal_id)
        else:
            runtime.actions.deliver(proposal_id)
    if speak and answer and not abandoned:
        # Start the voice now: by the time the tablet has this JSON and asks /speak, the MP3
        # is already generating. The same request it would make anyway, just earlier. An
        # error line is a fixed sentence: synthesised once, kept, free and instant after that.
        # A question the owner abandoned (/cancel) gets no voice: nobody will ask for it.
        runtime.voice.prefetch(
            to_speakable(answer, max_chars=runtime.voice.max_chars), pin=bool(error_kind) or answer in FIXED_LINES
        )
    # The turn is over: whatever it was doing (hearing, checking Shopify, thinking), the
    # session says so now, so a /state poll that outlives the turn cannot report otherwise.
    if session is not None and session.state not in ("READY", "ERROR"):
        session.set_state("ERROR" if error_kind else "READY")
    timings["total"] = (time.perf_counter() - started) * 1000
    # What the screen shows beside the answer: cards chosen from the tool results, never from
    # the prose. See app/presentation.py for the vocabulary and the bounds.
    ui = present(calls, session=session, error_kind=error_kind, writes=rail)
    # A card a recipe built for itself, for an answer no tool produced. It goes in front of
    # the context stack and behind nothing: it IS the answer to the question that was asked.
    if surfaces:
        ui = [s.as_ui() if hasattr(s, "as_ui") else s for s in surfaces] + ui
    turn_id = getattr(session, "turn_id", "") if session is not None else ""
    if branch is None and session is not None:
        branch = session.branch()
    if branch is not None:
        # The answer is here. A half the owner is looking at simply goes quiet; one he has
        # put aside — or simply tapped away from while it was working — says "ready" on its
        # chip and pulses once, and does not take his attention. The live test found a half
        # that finished a ten-second turn with zero change on the tablet and an answer that
        # could never be read: it was not BACKGROUND, only not looked at, so it went idle.
        elsewhere = bool(session is not None and getattr(session, "focused_branch", "") and session.focused_branch != branch.branch_id)
        if error_kind:
            branch.failed("that did not work")
        elif branch.status == "BACKGROUND" or elsewhere:
            branch.ready("there is an answer")
        else:
            branch.idle()
        # What this half now shows, kept on the Mac so tapping it later draws it (branch.show).
        branch.shown(ui, answer, question)
    for call in calls or []:
        if branch is not None and getattr(call, "ok", False):
            branch.remember_result(call.name, summary=_call_summary(call), ref=_call_ref(call), ms=float(getattr(call, "duration_ms", 0.0) or 0.0))
    # How this turn actually went, in numbers. Every field is measured; none of it is content.
    # This is what the report's speed section and the bench read (brief section 32).
    performance = _performance(timings, lane=lane, recipe_id=recipe_id, branch=branch, calls=calls, partial=partial, session=session, measures=measures or {})
    if timeline.current().active is not None:
        # An answer that declines, held against what the Mac composes: a refusal of a best
        # seller, a breakdown, a comparison or a bulk change the tools could have made is a
        # FALSE UNSUPPORTED claim, and the report counts it. Words only; no reasoning text.
        from app.observability import claims

        signal = claims.claim(question or (transcript or {}).get("text") or "", answer, tool_calls, claims.registered(), hinted=bool(getattr(session, "hinted", False)))
        if signal is not None:
            timeline.emit("unsupported_claim", session_id=session_id, turn_id=turn_id or None, **signal)
        timeline.emit(
            "turn_performance", session_id=session_id, turn_id=turn_id or None, **performance,
        )
        timeline.emit(
            "turn_finished", session_id=session_id, turn_id=turn_id or None, ms=round(timings["total"], 1),
            timings={k: round(v, 1) for k, v in timings.items()}, question=_written(question or (transcript or {}).get("text") or "", names) or None,
            # Redacted by the same rule the turn log uses, and for the same reason: the
            # answer may carry a street address the owner asked to be read out. He may hear
            # it; the timeline and the report built from it get "[address]".
            answer=_written(answer, names), error_kind=error_kind, lost_thread=lost_thread, abandoned=abandoned,
            ui=[item["type"] for item in ui], ui_entities=_ui_entities(ui), proposed=proposed or None, revoked=list(revoked or []) or None,
            # What the owner was actually shown, as a fact separate from which components drew
            # it: the surfaces this turn produced, whether anything was shown at all, and what
            # it offered to do next. A turn that answered in words and drew nothing is the
            # failure this pass exists for, and `surfaces: []` is what it looks like here.
            surfaces=[item.get("surface") or item["type"] for item in ui if item["type"] != "context_stack"] or None,
            showed_nothing=not any(item["type"] != "context_stack" for item in ui),
            actions=sorted({
                str(a.get("operation") or a.get("id") or "")
                for item in ui if isinstance(item.get("data"), dict)
                for a in (item["data"].get("actions") or []) if isinstance(a, dict)
            }) or None,
            writes_code=(None if writes is None or writes.get("allowed") else writes.get("code")),
            speak_requested=speak, tts_prefetched=bool(speak and answer and not abandoned),
            tool_calls=[{"tool": c.get("name"), "ok": c.get("ok"), "ms": c.get("ms"), "tool_call_id": c.get("tool_call_id") or None, "proposal_id": c.get("proposal_id")} for c in tool_calls] or None,
        )
    payload = {
        "session_id": session_id,
        "turn_id": turn_id,
        "test_session_id": timeline.current().active_id,
        "turns": turns,
        "answer": answer,
        "question": question or (transcript or {}).get("text", ""),
        "error_kind": error_kind,
        "lost_thread": lost_thread,
        "state": "ERROR" if error_kind else "READY",
        "last_state": _tool_state([c["name"] for c in tool_calls]),
        # The page files this answer was made for. A tablet running an older page learns it
        # here, at the end of the turn, rather than at the next health poll.
        "build": runtime.build,
        "writes": writes,
        # Cards this instruction withdrew. The tablet settles exactly these, no others.
        "revoked": list(revoked or []),
        "tool_calls": tool_calls,
        "transcript": transcript,
        "timings_ms": {k: round(v, 1) for k, v in timings.items()},
        "ui": ui,
        # Which lane answered, and where the conversation now is. The tablet renders its
        # navigation from this rather than from what it can see on screen.
        "lane": lane,
        "recipe_id": recipe_id or None,
        "branch": branch.public() if branch is not None else None,
        # Both halves, when there are two, so the tablet draws what the Mac holds rather
        # than what it remembers doing.
        "branches": (
            {"focused": session.focused_branch,
             "branches": [b.public() for b in session.branches.values() if b.status in ("ACTIVE", "BACKGROUND")]}
            if session is not None and session.branches else None
        ),
        "partial": bool(partial),
        "performance": performance,
    }
    # The cards repeat what the tools returned, which the log already has in redacted form;
    # the log keeps only which kinds were shown.
    runtime.turnlog.write({**payload, "ui": [item["type"] for item in ui]}, names=names)
    return payload


@router.get("/state/{session_id}")
async def state(request: Request, session_id: str) -> dict:
    """What the assistant is doing right now. The tablet polls this during a turn so the
    screen says CHECKING SHOPIFY because shopify_list_orders is actually running, not because
    the question had the word "orders" in it."""
    runtime = request.app.state.runtime
    try:
        session = runtime.sessions.peek(session_id)
    except KeyError:
        return {"session_id": session_id, "known": False, "state": "READY", "detail": ""}
    if not session_matches(session, request):
        return JSONResponse(status_code=403, content={"code": "wrong_session", "detail": "That conversation belongs to another login."})
    return {
        "session_id": session_id,
        "known": True,
        "state": session.state,
        "detail": session.state_detail,
        "turns": session.turns,
        "epoch": session.epoch,
        "heard": session.heard,
    }


@router.post("/cancel")
async def cancel(request: Request, session_id: str = Form(default="")) -> dict:
    """The owner has moved on: he is holding the orb again while the last question is still
    being thought about. Interrupt Claude, and stop synthesising any answer nobody will hear.
    Nothing applied is undone; whatever the abandoned turn had proposed is withdrawn, unsent."""
    runtime = request.app.state.runtime
    interrupted = False
    revoked: list[str] = []
    if session_id:
        # Marked whether or not the turn has reached Claude yet — a hold during transcription
        # counts — and even before the session's first turn has created it. Anything the
        # abandoned turn proposed is withdrawn with it.
        live = runtime.sessions.get_or_create(session_id)
        if not session_matches(live, request):
            return JSONResponse(status_code=403, content={"code": "wrong_session", "detail": "That conversation belongs to another login."})
        live.abandoned = True
        # Named, so the tablet settles exactly the cards this withdrew rather than guessing.
        revoked = runtime.actions.revoke_pending(live, "turn abandoned", undos=True) + runtime.batches.revoke_pending(live, "turn abandoned", undos=True)
        runtime.actions.advance_epoch(live, "turn abandoned")
        interrupted = await runtime.provider.interrupt(session_id)
    stopped = runtime.voice.cancel_prefetches()
    return {"cancelled": True, "interrupted": interrupted, "prefetches_stopped": stopped, "revoked": revoked}


@router.post("/audio-test")
async def audio_test(request: Request, audio: UploadFile = File(...)) -> dict:
    """M2's endpoint. Kept afterwards because "is the microphone alright today" stays useful."""
    runtime = request.app.state.runtime
    blob = await audio.read()
    stamp = time.strftime("%Y%m%d-%H%M%S")
    suffix = (audio.filename or "").rsplit(".", 1)
    # Kept on disk only when captures are asked for, like every other recording.
    save_to = (
        runtime.settings.bench_audio_dir / f"{stamp}.{suffix[-1] if len(suffix) > 1 else 'webm'}"
        if runtime.settings.save_captures else None
    )
    try:
        decoded = await asyncio.to_thread(decode, blob, save_to=save_to)
    except DecodeError as exc:
        return {"ok": False, "error": str(exc), "bytes_in": len(blob),
                "mime_type": audio.content_type}
    return {
        "ok": True,
        "mime_type": audio.content_type,
        "saved_to": str(decoded.saved_to) if decoded.saved_to else None,
        # The decoded WAV, so the page can play back exactly what the backend heard (M2).
        "wav_base64": base64.b64encode(decoded.as_wav()).decode("ascii"),
        **decoded.stats.as_dict(),
    }


@router.post("/reset")
async def reset(request: Request, session_id: str = Form(default="")) -> dict:
    runtime = request.app.state.runtime
    if session_id:
        try:
            existing = runtime.sessions.peek(session_id)
        except KeyError:
            existing = None
        if existing is not None and not session_matches(existing, request):
            return JSONResponse(status_code=403, content={"code": "wrong_session", "detail": "That conversation belongs to another login."})
        runtime.actions.forget_session(session_id)
        runtime.sessions.drop(session_id)
        await runtime.provider.reset_session(session_id)
    return {"reset": True}
