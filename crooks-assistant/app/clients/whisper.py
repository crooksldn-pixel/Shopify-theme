"""HTTP client for whisper.cpp's `whisper-server`.

The server runs as a separate long-lived process (launchd, M13) so the model stays resident.
Loading a model per request costs seconds and would make the whole product feel broken.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

import httpx

log = logging.getLogger("crooks.whisper")

# Whisper's decoder emits these on silence — artefacts of its training data, not speech. They
# are the single most common way a voice assistant answers a question nobody asked.
HALLUCINATION_BLOCKLIST = frozenset(
    {
        "thank you.", "thank you", "thanks for watching!", "thanks for watching.",
        "you", "you.", "bye.", "bye", ".", "...", "[blank_audio]", "[music]",
        "subtitles by the amara.org community", "subs by www.zberg.net",
        "please subscribe to my channel.", "transcription by castingwords",
        "amara.org", "♪", "[silence]", "(silence)", "so.", "so",
    }
)


class WhisperUnavailable(RuntimeError):
    """whisper-server is not reachable. A named failure, not a generic 500."""


@dataclass(slots=True)
class Transcript:
    text: str
    ms: float
    model: str = ""

    @property
    def is_hallucination(self) -> bool:
        stripped = self.text.strip().lower()
        return not stripped or stripped in HALLUCINATION_BLOCKLIST


class WhisperClient:
    def __init__(self, base_url: str, *, model: str = "", timeout_s: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._timeout = timeout_s

    async def transcribe(self, wav: bytes, *, prompt: str = "") -> Transcript:
        """POST a 16 kHz mono WAV to /inference and return the transcript."""
        files = {"file": ("audio.wav", wav, "audio/wav")}
        data = {
            "temperature": "0.0",
            "temperature_inc": "0.2",
            "response_format": "json",
            # VAD is what stops silence becoming "Thank you." The server is started with --vad
            # too; asking per request as well means a mis-started server still filters.
            # Field name verified against examples/server/server.cpp: it is `vad`.
            "vad": "true",
            "no_timestamps": "true",
            # Suppress non-speech tokens ("[MUSIC]", "♪") at the decoder, not just in our blocklist.
            "suppress_nst": "true",
        }
        if prompt:
            data["prompt"] = prompt

        started = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(f"{self.base_url}/inference", files=files, data=data)
        except httpx.ConnectError as exc:
            raise WhisperUnavailable(
                f"whisper-server is not running at {self.base_url}. Start it with "
                "`make whisper-server`."
            ) from exc
        except httpx.TimeoutException as exc:
            raise WhisperUnavailable("whisper-server did not respond in time.") from exc

        if response.status_code != 200:
            raise WhisperUnavailable(
                f"whisper-server returned {response.status_code}: {response.text[:200]}"
            )

        payload = response.json()
        text = (payload.get("text") or "").strip()
        ms = (time.perf_counter() - started) * 1000
        return Transcript(text=text, ms=ms, model=self.model)

    async def health(self) -> tuple[bool, str]:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(f"{self.base_url}/")
            return response.status_code < 500, f"whisper-server at {self.base_url}"
        except Exception as exc:  # noqa: BLE001
            return False, f"whisper-server unreachable at {self.base_url}: {exc}"
