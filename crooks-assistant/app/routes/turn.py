"""POST /turn — the whole product, in one endpoint.

Accepts text (development, and the typed interface that keeps allowance testing cheap) or audio
(the tablet). Both converge on the same agent path, which is what made M11 nearly trivial.
"""

from __future__ import annotations

import base64
import logging
import time
import uuid

from fastapi import APIRouter, File, Form, Request, UploadFile

from app.logging.turnlog import redact
from app.speech.decode import DecodeError, decode

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

    # JSON bodies are what curl and scripts/chat.py send; multipart is what the tablet sends.
    if text is None and audio is None:
        try:
            body = await request.json()
        except Exception:  # noqa: BLE001
            body = {}
        text = body.get("text")
        session_id = body.get("session_id") or session_id
        expected_turns = body.get("turns")
    else:
        form_turns = (await request.form()).get("turns")
        expected_turns = int(form_turns) if form_turns not in (None, "") else None

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

    if audio is not None:
        blob = await audio.read()
        if len(blob) > MAX_UPLOAD_BYTES:
            return _answer(
                runtime, session_id, "That recording was too long for me to handle.",
                error_kind="audio_too_large", timings=timings, started=started,
            )
        result = await runtime.transcriber.from_blob(blob, filename_hint=audio.filename or "")
        transcript_info = result.as_dict()
        timings.update(result.timings_ms)
        if not result.ok:
            return _answer(
                runtime, session_id, result.reason, error_kind="speech",
                timings=timings, started=started, transcript=transcript_info,
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
        return _answer(
            runtime, session_id, "I did not catch that.", error_kind="empty",
            timings=timings, started=started, transcript=transcript_info,
        )
    text = text.strip()[:MAX_TEXT_CHARS]

    if lost_thread:
        return _answer(
            runtime, session_id,
            "I've lost the thread of our conversation — either I restarted or it has been a "
            "while. Ask me again from the start.",
            error_kind="lost_thread", timings=timings, started=started,
            transcript=transcript_info, question=text, lost_thread=True,
        )

    await runtime.maybe_refresh_catalogue()
    await _ensure_provider_started(runtime)

    t0 = time.perf_counter()
    result = await runtime.provider.turn(session_id, text.strip())
    timings["agent"] = (time.perf_counter() - t0) * 1000

    answer = result.text or "I could not work out an answer to that."
    if len(answer) > runtime.settings.max_answer_chars:
        # A forty-second spoken monologue is a bad product; truncate at a sentence boundary.
        cut = answer[: runtime.settings.max_answer_chars]
        answer = cut[: cut.rfind(".") + 1] or cut

    return _answer(
        runtime,
        session_id,
        answer,
        error_kind=result.error_kind,
        timings=timings,
        started=started,
        transcript=transcript_info,
        question=text.strip(),
        tool_calls=[
            {
                "name": c.name, "ok": c.ok, "error": c.error, "ms": c.duration_ms,
                # Arguments are what make a wrong answer diagnosable in chat.py — redacted,
                # because the model may have put an email address in them.
                "args": redact({k: str(v)[:80] for k, v in (c.args or {}).items()}),
            }
            for c in result.tool_calls
        ],
    )


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


def _answer(
    runtime,
    session_id: str,
    answer: str,
    *,
    error_kind: str | None = None,
    timings: dict,
    started: float,
    transcript: dict | None = None,
    question: str = "",
    tool_calls: list | None = None,
    lost_thread: bool = False,
) -> dict:
    tool_calls = tool_calls or []
    timings["total"] = (time.perf_counter() - started) * 1000
    turns = 0
    try:
        turns = runtime.sessions.get(session_id).turns
    except KeyError:
        pass
    payload = {
        "session_id": session_id,
        "turns": turns,
        "answer": answer,
        "question": question or (transcript or {}).get("text", ""),
        "error_kind": error_kind,
        "lost_thread": lost_thread,
        "state": "ERROR" if error_kind else "READY",
        "last_state": _tool_state([c["name"] for c in tool_calls]),
        "tool_calls": tool_calls,
        "transcript": transcript,
        "timings_ms": {k: round(v, 1) for k, v in timings.items()},
    }
    runtime.turnlog.write(payload)
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
    }


@router.post("/audio-test")
async def audio_test(request: Request, audio: UploadFile = File(...)) -> dict:
    """M2's endpoint. Kept afterwards because "is the microphone alright today" stays useful."""
    runtime = request.app.state.runtime
    blob = await audio.read()
    stamp = time.strftime("%Y%m%d-%H%M%S")
    suffix = (audio.filename or "").rsplit(".", 1)
    save_to = runtime.settings.bench_audio_dir / f"{stamp}.{suffix[-1] if len(suffix) > 1 else 'webm'}"
    try:
        decoded = decode(blob, save_to=save_to)
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
        runtime.sessions.drop(session_id)
        await runtime.provider.reset_session(session_id)
    return {"reset": True}
