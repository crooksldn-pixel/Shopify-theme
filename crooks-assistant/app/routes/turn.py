"""POST /turn — the whole product, in one endpoint.

Accepts text (development, and the typed interface that keeps allowance testing cheap) or audio
(the tablet). Both converge on the same agent path, which is what made M11 nearly trivial.
"""

from __future__ import annotations

import logging
import time
import uuid

from fastapi import APIRouter, File, Form, Request, UploadFile

from app.speech.decode import DecodeError, decode

log = logging.getLogger("crooks.turn")

router = APIRouter()

MAX_UPLOAD_BYTES = 10_000_000


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
    session_id = session_id or uuid.uuid4().hex[:12]
    started = time.perf_counter()
    timings: dict[str, float] = {}
    transcript_info: dict | None = None

    # JSON bodies are what curl and scripts/chat.py send; multipart is what the tablet sends.
    if text is None and audio is None:
        try:
            body = await request.json()
        except Exception:  # noqa: BLE001
            body = {}
        text = body.get("text")
        session_id = body.get("session_id") or session_id

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

    if not text or not text.strip():
        return _answer(
            runtime, session_id, "I did not catch that.", error_kind="empty",
            timings=timings, started=started, transcript=transcript_info,
        )

    await runtime.maybe_refresh_catalogue()

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
            {"name": c.name, "ok": c.ok, "error": c.error, "ms": c.duration_ms}
            for c in result.tool_calls
        ],
    )


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
) -> dict:
    tool_calls = tool_calls or []
    timings["total"] = (time.perf_counter() - started) * 1000
    payload = {
        "session_id": session_id,
        "answer": answer,
        "question": question or (transcript or {}).get("text", ""),
        "error_kind": error_kind,
        "state": "ERROR" if error_kind else "READY",
        "last_state": _tool_state([c["name"] for c in tool_calls]),
        "tool_calls": tool_calls,
        "transcript": transcript,
        "timings_ms": {k: round(v, 1) for k, v in timings.items()},
    }
    runtime.turnlog.write(payload)
    return payload


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
        **decoded.stats.as_dict(),
    }


@router.post("/reset")
async def reset(request: Request, session_id: str = Form(default="")) -> dict:
    runtime = request.app.state.runtime
    if session_id:
        runtime.sessions.drop(session_id)
        await runtime.provider.reset_session(session_id)
    return {"reset": True}
