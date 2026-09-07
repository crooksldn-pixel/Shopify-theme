"""The transcription pipeline with a fake whisper, plus the prompt rules and capture pruning."""

from __future__ import annotations

import time

import pytest

from app.clients.whisper import Transcript, WhisperClient, WhisperUnavailable
from app.speech.normalise import from_terms
from app.speech.transcribe import Transcriber, build_prompt, prune_captures

av = pytest.importorskip("av")
from tests.test_decode import tone_pcm, webm_opus  # noqa: E402


class FakeWhisper(WhisperClient):
    def __init__(self, text: str = "", fail: bool = False) -> None:
        super().__init__("http://fake")
        self.text, self.fail, self.prompts = text, fail, []

    async def transcribe(self, wav: bytes, *, prompt: str = "") -> Transcript:
        self.prompts.append(prompt)
        if self.fail:
            raise WhisperUnavailable("whisper-server is not running")
        return Transcript(text=self.text, ms=12.0)


def norm():
    return from_terms(["Blue Wash Yard Jeans"], {"cross stars tee": "CRXST★RZ T-Shirt"})


async def test_speech_path_normalises_and_reports_timings():
    t = Transcriber(FakeWhisper("find the blue wash yard genes"), norm())
    result = await t.from_blob(webm_opus(tone_pcm(1.0)))
    assert result.ok
    assert "Blue Wash Yard Jeans" in result.text
    assert result.raw_text == "find the blue wash yard genes"
    assert {"decode", "transcribe", "normalise"} <= result.timings_ms.keys()


async def test_silence_never_reaches_whisper():
    fake = FakeWhisper("Thank you.")
    result = await Transcriber(fake, norm()).from_blob(webm_opus(b"\x00\x00" * 48000))
    assert not result.ok
    assert fake.prompts == [], "whisper was called for a recording with no signal"
    assert "could not hear" in result.reason


@pytest.mark.parametrize("text", ["Thank you.", "", "you", "[BLANK_AUDIO]", "Subtitles by the Amara.org community"])
async def test_hallucinations_become_no_speech(text):
    result = await Transcriber(FakeWhisper(text), norm()).from_blob(webm_opus(tone_pcm(1.0)))
    assert not result.ok
    assert "did not catch" in result.reason


async def test_whisper_down_is_spoken_not_crashed():
    result = await Transcriber(FakeWhisper(fail=True), norm()).from_blob(webm_opus(tone_pcm(1.0)))
    assert not result.ok
    assert "speech recognition" in result.reason
    assert "whisper" not in result.reason.lower(), "developer detail must not be spoken aloud"


async def test_undecodable_upload_is_reported():
    result = await Transcriber(FakeWhisper("x"), norm()).from_blob(b"not audio at all")
    assert not result.ok
    assert "Could not open" in result.reason


async def test_prompt_is_display_case_and_ends_with_period():
    fake = FakeWhisper("hello")
    await Transcriber(fake, norm()).from_blob(webm_opus(tone_pcm(1.0)))
    prompt = fake.prompts[0]
    assert prompt.endswith(".")
    assert "Blue Wash Yard Jeans" in prompt
    assert "Cross Stars Tee" in prompt, "spoken aliases must be in the prompt — they are what is said"
    assert "★" not in prompt


def test_build_prompt_puts_last_terms_last_and_caps_length():
    terms = [f"term number {i}" for i in range(300)]
    prompt = build_prompt(terms)
    assert prompt.endswith("term number 299.")
    assert "term number 0," not in prompt  # truncated from the front
    assert len(prompt) <= 905


def test_build_prompt_strips_symbols_and_dedupes():
    assert build_prompt(["CRXST★RZ T-SHIRT", "CRXST★RZ T-SHIRT"]) == "CRXST RZ T SHIRT."


def test_build_prompt_empty():
    assert build_prompt([]) == ""


async def test_captures_are_saved_and_pruned(tmp_path):
    t = Transcriber(FakeWhisper("hi"), norm(), save_dir=tmp_path, max_saved=3)
    for i in range(5):
        await t.from_blob(webm_opus(tone_pcm(0.5)), filename_hint=f"t{i}.webm")
        time.sleep(0.01)
        # same-second timestamps collide; give each a distinct name by touching mtime order
    files = sorted(p for p in tmp_path.iterdir() if not p.name.startswith("."))
    assert len(files) <= 3


def test_prune_keeps_newest(tmp_path):
    for i in range(6):
        p = tmp_path / f"{i}.webm"
        p.write_bytes(b"x")
        ts = 1_700_000_000 + i
        import os

        os.utime(p, (ts, ts))
    (tmp_path / ".gitkeep").write_text("")
    removed = prune_captures(tmp_path, keep=2)
    assert removed == 4
    remaining = sorted(p.name for p in tmp_path.iterdir())
    assert remaining == [".gitkeep", "4.webm", "5.webm"]


def test_prune_handles_missing_dir(tmp_path):
    assert prune_captures(tmp_path / "nope", keep=5) == 0
    assert prune_captures(None, keep=5) == 0
