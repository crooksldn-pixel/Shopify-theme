"""POST /turn — the whole product, in one endpoint.

Accepts text (development, and the typed interface that keeps allowance testing cheap) or audio
(the tablet). Both converge on the same agent path, which is what made M11 nearly trivial.
"""

from __future__ import annotations

import asyncio
import base64
import logging
import time
import uuid

from fastapi import APIRouter, File, Form, Request, UploadFile

from app.logging.turnlog import redact
from app.presentation import present
from app.routes.actions import writes_context
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

    # JSON bodies are what curl and scripts/chat.py send; multipart is what the tablet sends.
    if text is None and audio is None:
        try:
            body = await request.json()
        except Exception:  # noqa: BLE001
            body = {}
        text = body.get("text")
        session_id = body.get("session_id") or session_id
        expected_turns = body.get("turns")
        speak = _truthy(body.get("speak"))
    else:
        form = await request.form()
        form_turns = form.get("turns")
        expected_turns = int(form_turns) if form_turns not in (None, "") else None
        speak = _truthy(form.get("speak"))

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
    live.heard = ""
    live.abandoned = False
    # This turn's place in the conversation. A hold that abandons the question, or a later
    # question, moves the session past it; the answer then goes unspoken.
    epoch = live.epoch

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
    revoked = runtime.actions.revoke_pending(live, "new instruction")
    epoch = runtime.actions.advance_epoch(live, "new instruction")

    # The hourly catalogue refresh is a Shopify round trip; it runs beside this turn, not
    # in front of it. This question is answered with the catalogue as it stands.
    runtime.refresh_catalogue_soon()
    await _ensure_provider_started(runtime)

    # What was heard, on the session now, so the tablet can show it while Claude thinks
    # rather than only once the answer lands — a mis-heard question is visible at once.
    live.heard = text.strip()

    t0 = time.perf_counter()
    result = await runtime.provider.turn(session_id, text.strip())
    timings["agent"] = (time.perf_counter() - t0) * 1000
    for step, ms in getattr(result, "steps", None) or []:
        timings[f"step:{step}"] = ms

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
        question=text.strip(),
        tool_calls=[
            {
                "name": c.name, "ok": c.ok, "error": c.error, "ms": c.duration_ms,
                # Arguments are what make a wrong answer diagnosable in chat.py — redacted,
                # because the model may have put an email address in them. A proposed write's
                # content stays out of the log altogether; the ledger keeps its length.
                "args": _loggable_args(c),
                "proposal_id": c.proposal_id,
            }
            for c in result.tool_calls
        ],
        calls=result.tool_calls,
        speak=speak,
        lost_thread=lost_thread,
        epoch=epoch,
        revoked=revoked,
    )


LOST_THREAD_PREFIX = "I lost our earlier thread, so from the start: "


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
        return registry.get(name).write is not None
    except KeyError:
        return False


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
        proposed = []
    # A change was proposed this turn. Say, now and in the same breath, whether a tap on THIS
    # tablet could apply it — a card that cannot be applied must never look as if it can.
    writes = None
    if proposed and request is not None:
        writes = await writes_context(request)
        if not writes["allowed"] and writes["spoken"]:
            answer = f"{answer.rstrip()} {writes['spoken']}"
    # The card leaves for the tablet now; its wait for the tap starts now.
    for proposal_id in proposed:
        runtime.actions.deliver(proposal_id)
    if speak and answer and not abandoned:
        # Start the voice now: by the time the tablet has this JSON and asks /speak, the MP3
        # is already generating. The same request it would make anyway, just earlier. An
        # error line is a fixed sentence: synthesised once, kept, free and instant after that.
        # A question the owner abandoned (/cancel) gets no voice: nobody will ask for it.
        runtime.voice.prefetch(
            to_speakable(answer, max_chars=runtime.voice.max_chars), pin=bool(error_kind)
        )
    timings["total"] = (time.perf_counter() - started) * 1000
    # What the screen shows beside the answer: cards chosen from the tool results, never from
    # the prose. See app/presentation.py for the vocabulary and the bounds.
    ui = present(calls, session=session, error_kind=error_kind, writes=writes)
    payload = {
        "session_id": session_id,
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
    if session_id:
        # Marked whether or not the turn has reached Claude yet — a hold during transcription
        # counts — and even before the session's first turn has created it. Anything the
        # abandoned turn proposed is withdrawn with it.
        live = runtime.sessions.get_or_create(session_id)
        live.abandoned = True
        runtime.actions.advance_epoch(live, "turn abandoned")
        interrupted = await runtime.provider.interrupt(session_id)
    stopped = runtime.voice.cancel_prefetches()
    return {"cancelled": True, "interrupted": interrupted, "prefetches_stopped": stopped}


@router.post("/audio-test")
async def audio_test(request: Request, audio: UploadFile = File(...)) -> dict:
    """M2's endpoint. Kept afterwards because "is the microphone alright today" stays useful."""
    runtime = request.app.state.runtime
    blob = await audio.read()
    stamp = time.strftime("%Y%m%d-%H%M%S")
    suffix = (audio.filename or "").rsplit(".", 1)
    save_to = runtime.settings.bench_audio_dir / f"{stamp}.{suffix[-1] if len(suffix) > 1 else 'webm'}"
    try:
        decoded = await asyncio.to_thread(decode, blob, save_to=save_to)
    except DecodeError as exc:
        return {"ok": False, "error": str(exc), "bytes_in": len(blob),
                "mime_type": audio.content_type}
    return {
        "ok": True,
        "mime_type": audio.content_type,
        "saved_to": str(decoded.saved_to),
        # The decoded WAV, so the page can play back exactly what the backend heard (M2).
        "wav_base64": base64.b64encode(decoded.as_wav()).decode("ascii"),
        **decoded.stats.as_dict(),
    }


@router.post("/reset")
async def reset(request: Request, session_id: str = Form(default="")) -> dict:
    runtime = request.app.state.runtime
    if session_id:
        runtime.actions.forget_session(session_id)
        runtime.sessions.drop(session_id)
        await runtime.provider.reset_session(session_id)
    return {"reset": True}
