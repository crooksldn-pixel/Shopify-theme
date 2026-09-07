"""decode → transcribe → filter hallucinations → normalise CROOKS terminology.

The pipeline's contract is that it never returns text it does not believe. Silence, a decode
failure and a blocklisted artefact all come back as "no speech", because an assistant that
answers a question nobody asked is worse than one that says it did not hear.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path

from app.clients.whisper import Transcript, WhisperClient, WhisperUnavailable
from app.speech.decode import AudioStats, DecodeError, decode
from app.speech.normalise import Normalised, Normaliser

log = logging.getLogger("crooks.transcribe")

# Whisper accepts an initial prompt to bias decoding. It is truncated from the FRONT at 224
# tokens, so the most important terms go LAST. It must be a bare comma-separated list — prose
# here bleeds into the transcript, which looks like a hallucination and is not one.
PROMPT_MAX_TERMS = 60


@dataclass(slots=True)
class SpeechResult:
    ok: bool
    text: str = ""
    raw_text: str = ""
    reason: str = ""  # populated when ok is False
    stats: AudioStats | None = None
    normalised: Normalised | None = None
    timings_ms: dict[str, float] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "ok": self.ok,
            "text": self.text,
            "raw_text": self.raw_text,
            "reason": self.reason,
            "stats": self.stats.as_dict() if self.stats else None,
            "matches": [
                {"heard": m.heard, "became": m.replaced_with, "score": m.score, "via": m.via}
                for m in (self.normalised.matches if self.normalised else [])
            ],
            "order_numbers": self.normalised.order_numbers if self.normalised else [],
            "timings_ms": {k: round(v, 1) for k, v in self.timings_ms.items()},
        }


def build_prompt(terms: list[str]) -> str:
    """A bare comma-separated term list, most important LAST because truncation eats the front."""
    if not terms:
        return ""
    return ", ".join(terms[-PROMPT_MAX_TERMS:])


class Transcriber:
    def __init__(
        self,
        client: WhisperClient,
        normaliser: Normaliser,
        *,
        save_dir: Path | None = None,
    ) -> None:
        self._client = client
        self._normaliser = normaliser
        self._save_dir = save_dir

    async def from_blob(self, blob: bytes, *, filename_hint: str = "") -> SpeechResult:
        timings: dict[str, float] = {}

        save_to = None
        if self._save_dir is not None:
            stamp = time.strftime("%Y%m%d-%H%M%S")
            suffix = Path(filename_hint).suffix or ".webm"
            save_to = self._save_dir / f"{stamp}{suffix}"

        t0 = time.perf_counter()
        try:
            audio = decode(blob, save_to=save_to)
        except DecodeError as exc:
            return SpeechResult(ok=False, reason=str(exc), timings_ms={"decode": _ms(t0)})
        timings["decode"] = _ms(t0)

        if not audio.stats.usable:
            return SpeechResult(
                ok=False,
                reason=(
                    "I could not hear that clearly."
                    if audio.stats.rms_dbfs <= -50
                    else "That recording was too short."
                ),
                stats=audio.stats,
                timings_ms=timings,
            )

        t1 = time.perf_counter()
        try:
            transcript: Transcript = await self._client.transcribe(
                audio.as_wav(), prompt=build_prompt(self._normaliser.catalogue.terms)
            )
        except WhisperUnavailable as exc:
            return SpeechResult(ok=False, reason=str(exc), stats=audio.stats, timings_ms=timings)
        timings["transcribe"] = _ms(t1)

        if transcript.is_hallucination:
            log.info("filtered hallucination: %r", transcript.text)
            return SpeechResult(
                ok=False,
                raw_text=transcript.text,
                reason="I did not catch any speech there.",
                stats=audio.stats,
                timings_ms=timings,
            )

        t2 = time.perf_counter()
        normalised = self._normaliser.normalise(transcript.text)
        timings["normalise"] = _ms(t2)
        if normalised.changed:
            log.info("normalised %r -> %r", normalised.raw, normalised.text)

        return SpeechResult(
            ok=True,
            text=normalised.text,
            raw_text=transcript.text,
            stats=audio.stats,
            normalised=normalised,
            timings_ms=timings,
        )


def _ms(since: float) -> float:
    return (time.perf_counter() - since) * 1000
