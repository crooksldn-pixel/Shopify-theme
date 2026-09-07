"""decode → transcribe → filter hallucinations → normalise CROOKS terminology.

The pipeline's contract is that it never returns text it does not believe. Silence, a decode
failure and a blocklisted artefact all come back as "no speech", because an assistant that
answers a question nobody asked is worse than one that says it did not hear.
"""

from __future__ import annotations

import logging
import re
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
# Whisper keeps roughly the last 224 tokens of the prompt; ~900 characters of short product
# names lands under that. Counting characters rather than terms keeps a long live catalogue from
# pushing the hand-written aliases out.
PROMPT_MAX_CHARS = 900


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
    """A comma-separated term list ending in a full stop, most important LAST because
    truncation eats the front.

    Whisper imitates the prompt's style. A bare lower-case list produced transcripts with no
    capitals and no punctuation; the same list in display case ending with a period restored
    both. Symbols are dropped because '★' teaches the model nothing about how a word sounds."""
    cleaned = [re.sub(r"[^A-Za-z0-9' ]+", " ", t).strip() for t in terms]
    cleaned = [" ".join(t.split()) for t in cleaned if t and t.strip()]
    cleaned = list(dict.fromkeys(cleaned))
    if not cleaned:
        return ""
    kept: list[str] = []
    length = 0
    for term in reversed(cleaned):  # last terms are the most important; keep from the end
        if length + len(term) + 2 > PROMPT_MAX_CHARS:
            break
        kept.append(term)
        length += len(term) + 2
    return ", ".join(reversed(kept)) + "."


class Transcriber:
    def __init__(
        self,
        client: WhisperClient,
        normaliser: Normaliser,
        *,
        save_dir: Path | None = None,
        max_saved: int = 200,
    ) -> None:
        self._client = client
        self._normaliser = normaliser
        self._save_dir = save_dir
        self._max_saved = max_saved

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
        if save_to is not None:
            prune_captures(self._save_dir, self._max_saved)

        if not audio.stats.usable:
            if audio.stats.duration_s < 0.3:
                reason = "That was too short — hold the button while you speak."
            elif audio.stats.peak >= 0.999:
                reason = "That came through distorted — a bit further from the microphone."
            else:
                reason = "I could not hear that clearly — a bit closer to the microphone."
            return SpeechResult(ok=False, reason=reason, stats=audio.stats, timings_ms=timings)

        t1 = time.perf_counter()
        try:
            transcript: Transcript = await self._client.transcribe(
                audio.as_wav(), prompt=build_prompt(self._normaliser.catalogue.prompt_terms())
            )
        except WhisperUnavailable as exc:
            # Spoken line for the tablet; the developer detail goes to the log, not the speaker.
            log.error("whisper unavailable: %s", exc)
            return SpeechResult(ok=False, reason=exc.spoken, stats=audio.stats, timings_ms=timings)
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


def prune_captures(directory: Path | None, keep: int) -> int:
    """Keep the newest `keep` recordings. These are recordings of an office; the benchmark
    corpus needs a few dozen, not a year of them. Returns how many were removed."""
    if directory is None or keep <= 0 or not directory.exists():
        return 0
    files = sorted(
        (p for p in directory.iterdir() if p.is_file() and not p.name.startswith(".")),
        key=lambda p: p.stat().st_mtime,
    )
    removed = 0
    for path in files[: max(0, len(files) - keep)]:
        try:
            path.unlink()
            removed += 1
        except OSError:
            pass
    return removed


def _ms(since: float) -> float:
    return (time.perf_counter() - since) * 1000
