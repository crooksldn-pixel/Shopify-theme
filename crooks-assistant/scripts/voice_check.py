#!/usr/bin/env python3
"""Prove Vikram works on this Mac, before the tablet is asked to prove it.

One short sentence, one real ElevenLabs request, one MP3 played through the Mac's speaker. It
costs a few characters of credit — deliberately, because "the key is present" is not the same
claim as "the voice speaks", and the difference is what this script buys.

The same text preparation the tablet gets runs first, so what you hear is what it will hear.
"""

from __future__ import annotations

import asyncio
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.clients.elevenlabs_tts import VoiceClient, VoiceUnavailable  # noqa: E402
from app.speech.speakable import to_speakable  # noqa: E402
from config.settings import get_settings  # noqa: E402

SENTENCE = "Twelve orders today, £430.50 in total. Order #1930 is the one still to pack."


async def main() -> int:
    settings = get_settings()
    client = VoiceClient(
        voice_id=settings.tts_voice_id,
        voice_name=settings.tts_voice_name,
        model=settings.tts_model,
        output_format=settings.tts_output_format,
        timeout_s=settings.tts_timeout_s,
        base_url=settings.elevenlabs_base_url,
        max_chars=settings.tts_max_chars,
        enabled=settings.tts_enabled,
    )
    print(f"voice       : {settings.tts_voice_name} ({settings.tts_voice_id})")
    actual = await client.verify_voice()
    if actual and actual.lower() != settings.tts_voice_name.lower():
        print(f"              !! ElevenLabs calls that id '{actual}'. Check CROOKS_TTS_VOICE_ID in .env.")
    elif actual:
        print(f"              ElevenLabs agrees: {actual}")
    print(f"model       : {settings.tts_model}")
    print(f"format      : {settings.tts_output_format}")

    written = " ".join(sys.argv[1:]) or SENTENCE
    spoken = to_speakable(written, max_chars=client.max_chars)
    print(f"\nwritten     : {written}")
    print(f"spoken      : {spoken}\n")
    if not spoken:
        print("Nothing to say — that text is all punctuation.")
        return 1

    started = time.perf_counter()
    try:
        audio = await client.synthesise(spoken)
    except VoiceUnavailable as exc:
        print(f"FAILED ({exc.kind})\n\n{exc}\n")
        print("The tablet would fall back to its own Android voice; answers still work.")
        return 1
    ms = (time.perf_counter() - started) * 1000

    out = get_settings().log_dir / "voice-check.mp3"
    out.write_bytes(audio)
    print(f"latency     : {ms:.0f}ms")
    print(f"audio       : {len(audio)} bytes  ->  {out}")
    if not audio.startswith((b"\xff\xfb", b"\xff\xf3", b"\xff\xf2", b"ID3")):
        print("\nWARNING: that does not look like an MP3.")
        return 1

    if sys.platform == "darwin":
        print("\nPlaying it on this Mac's speaker…")
        subprocess.run(["afplay", str(out)], check=False)
    print("\nVikram works on the Mac. Now ask the tablet.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
