"""POST /speak — the answer, in Derek's voice.

Deliberately a second request rather than part of /turn. The answer text has to be on the
tablet's screen the moment the agent finishes; making /turn wait for an MP3 would delay the
thing that matters for the sake of the thing that does not.

Nothing about ElevenLabs reaches the tablet: it sends text and receives audio/mpeg. The
credential stays on the Mac. Every failure is a 503 with a short, safe reason, which the tablet
reads as "use the Android voice" — never as "say nothing".
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse

from app.clients.elevenlabs_tts import VoiceUnavailable
from app.speech.speakable import to_speakable

log = logging.getLogger("crooks.speak")

router = APIRouter()

MAX_TEXT_CHARS = 4_000

# What the tablet is told. The kind is a shape, never an account detail or an API message —
# those are in the log on the Mac, where they belong.
REASONS = {
    "off": "the ElevenLabs voice is switched off",
    "no_key": "the ElevenLabs key is not set up on the Mac",
    "cooldown": "the ElevenLabs voice is unavailable at the moment",
    "rejected": "the ElevenLabs key was rejected",
    "forbidden": "the ElevenLabs key is not allowed to speak",
    "credit": "the ElevenLabs account has no credit left",
    "no_voice": "the ElevenLabs voice was not found",
    "timeout": "ElevenLabs did not answer in time",
    "network": "ElevenLabs could not be reached",
    "server_error": "ElevenLabs had a server error",
    "rate": "the ElevenLabs voice has been asked for too often this minute",
    "cancelled": "that answer was abandoned",
    "prefetch": "the ElevenLabs voice could not be prepared",
}


@router.post("/speak")
async def speak(request: Request) -> Response:
    """Text in, MP3 out. 204 when there is nothing worth saying, 503 when Derek cannot."""
    runtime = request.app.state.runtime
    voice = runtime.voice
    try:
        body = await request.json()
    except Exception:  # noqa: BLE001
        body = {}
    raw = str(body.get("text") or "")[:MAX_TEXT_CHARS]

    spoken = to_speakable(raw, max_chars=voice.max_chars)
    if not spoken:
        # An answer made only of punctuation, or an empty one. Silence is the right output and
        # a paid request is not; 204 tells the tablet so without looking like a failure.
        return Response(status_code=204)

    headers = {
        # Diagnostics the tablet can show without a second request, and nothing secret.
        "X-Crooks-Voice": voice.voice_name,
        "X-Crooks-Model": voice.model,
        "Cache-Control": "no-store",
    }
    try:
        # /turn started synthesising this answer the moment it knew it (VoiceClient.prefetch).
        # What has arrived goes out now and the rest follows as ElevenLabs produces it — the
        # tablet starts playing the opening while the ending is still being generated.
        ready = await voice.take_ready(spoken)
        if ready is not None:
            return StreamingResponse(
                ready, media_type="audio/mpeg", headers={**headers, "X-Crooks-Prefetched": "1"}
            )
        stream = await voice.open_stream(spoken)
    except VoiceUnavailable as exc:
        # The text is not logged; its length is what makes a latency or truncation report
        # readable, and an answer read out in the office does not need repeating to disk.
        log.info("tts declined (%s) for %d chars — tablet falls back", exc.kind, len(spoken))
        return JSONResponse(
            status_code=503,
            content={
                "ok": False,
                "kind": exc.kind,
                "reason": REASONS.get(exc.kind, "the ElevenLabs voice is unavailable"),
            },
        )

    return StreamingResponse(stream.chunks(), media_type="audio/mpeg", headers=headers)
