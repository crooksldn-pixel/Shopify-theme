"""Audio decode, round-tripped through PyAV the way Chrome's MediaRecorder produces it."""

from __future__ import annotations

import io
import math
import struct
import wave

import pytest

av = pytest.importorskip("av")

from app.speech.decode import (  # noqa: E402
    CLIPPED_RATIO_LIMIT,
    DecodeError,
    _stats,
    decode,
    read_wav,
)


def tone_pcm(seconds: float = 1.0, rate: int = 48000, hz: float = 440.0, amplitude: float = 0.5) -> bytes:
    count = int(rate * seconds)
    return struct.pack(
        f"<{count}h", *(int(amplitude * 32767 * math.sin(2 * math.pi * hz * i / rate)) for i in range(count))
    )


def speech_pcm(seconds: float = 1.5, rate: int = 48000, drive: float = 1.0) -> bytes:
    """A tone under a syllable-rate envelope, hard-limited: speech's shape, not a sine's.

    `drive` 1.0 just touches full scale on the loudest syllables — the recording the tablet
    used to refuse. Above that it is progressively over-driven."""
    count = int(rate * seconds)
    out = []
    for i in range(count):
        envelope = abs(math.sin(2 * math.pi * 3.0 * i / rate)) ** 2
        value = drive * envelope * math.sin(2 * math.pi * 180.0 * i / rate)
        out.append(int(max(-1.0, min(1.0, value)) * 32767))
    return struct.pack(f"<{count}h", *out)


def pcm_16k(seconds: float = 1.0, hz: float = 180.0, amplitude: float = 0.3) -> list[int]:
    """Speech-level 16 kHz mono samples, as they are after decoding."""
    count = int(16000 * seconds)
    return [int(amplitude * 32767 * math.sin(2 * math.pi * hz * i / 16000)) for i in range(count)]


def as_pcm(samples: list[int]) -> bytes:
    return struct.pack(f"<{len(samples)}h", *samples)


def webm_opus(pcm: bytes, rate: int = 48000) -> bytes:
    """audio/webm;codecs=opus at 32 kbps — what the tablet uploads."""
    buf = io.BytesIO()
    out = av.open(buf, "w", format="webm")
    stream = out.add_stream("libopus", rate=rate)
    stream.bit_rate = 32000
    stream.layout = "mono"
    frame = av.AudioFrame(format="s16", layout="mono", samples=len(pcm) // 2)
    frame.planes[0].update(pcm)
    frame.sample_rate = rate
    frame.pts = 0
    for packet in stream.encode(frame):
        out.mux(packet)
    for packet in stream.encode(None):
        out.mux(packet)
    out.close()
    return buf.getvalue()


def test_webm_opus_decodes_to_16k_mono():
    decoded = decode(webm_opus(tone_pcm(1.0)))
    assert decoded.stats.sample_rate == 16000
    assert decoded.stats.channels == 1
    assert 0.9 <= decoded.stats.duration_s <= 1.15  # opus adds a little priming
    assert decoded.stats.container.startswith("matroska")
    assert decoded.stats.codec == "opus"


def test_level_stats_are_sane():
    decoded = decode(webm_opus(tone_pcm(1.0, amplitude=0.5)))
    assert -8 < decoded.stats.peak_dbfs < -3  # 0.5 FS ≈ -6 dBFS
    assert decoded.stats.rms_dbfs < decoded.stats.peak_dbfs
    assert decoded.stats.usable


# --- clipping ---------------------------------------------------------------

def test_one_full_scale_spike_does_not_condemn_the_recording():
    """The bug: a knock on the desk hit full scale and the whole utterance was refused with
    "that came through distorted", while the saved recording was perfectly intelligible."""
    samples = pcm_16k(2.0)
    for i in range(8000, 8004):  # four samples — a quarter of a millisecond
        samples[i] = 32767
    stats = _stats(as_pcm(samples), bytes_in=len(samples) * 2)
    assert stats.peak >= 0.999, "the spike really does reach full scale"
    assert stats.clipped_samples == 4
    assert stats.clipped_ratio < 0.001
    assert stats.usable, "one spike is a moment, not distortion"


def test_a_hot_recording_that_touches_full_scale_still_transcribes():
    """Measured over 98 real tablet captures: a third of them touched full scale and the worst
    spent 0.27% of its samples there. Every one was intelligible."""
    decoded = decode(webm_opus(speech_pcm(drive=1.0)))
    assert decoded.stats.peak >= 0.999, "the loudest syllables reach the rail"
    assert 0 < decoded.stats.clipped_ratio < CLIPPED_RATIO_LIMIT
    assert decoded.stats.usable


def test_a_heavily_clipped_recording_is_still_rejected():
    """The protection this replaces, not the protection this removes."""
    decoded = decode(webm_opus(speech_pcm(drive=2.0)))
    assert decoded.stats.clipped_ratio >= CLIPPED_RATIO_LIMIT
    assert decoded.stats.rms_dbfs > -50, "loud, not quiet — it fails on distortion alone"
    assert decoded.stats.duration_s >= 0.3
    assert not decoded.stats.usable


def test_a_square_wave_is_the_extreme_case():
    samples = [32767 if (i // 40) % 2 == 0 else -32767 for i in range(16000)]
    stats = _stats(as_pcm(samples), bytes_in=32000)
    assert stats.clipped_ratio > 0.9
    assert not stats.usable


def test_clipping_is_reported_in_the_stats():
    samples = pcm_16k(1.0)
    samples[100] = -32767
    stats = _stats(as_pcm(samples), bytes_in=32000)
    payload = stats.as_dict()
    assert payload["clipped_samples"] == 1
    assert payload["clipped_ratio"] == round(1 / 16000, 5)
    assert payload["clipped_ms"] == round(1000 / 16000, 1)
    assert payload["usable"] is True


def test_a_clean_recording_reports_no_clipping():
    stats = _stats(as_pcm(pcm_16k(1.0, amplitude=0.5)), bytes_in=32000)
    assert stats.clipped_samples == 0
    assert stats.clipped_ratio == 0.0
    assert stats.usable


def test_silence_is_not_usable():
    decoded = decode(webm_opus(b"\x00\x00" * 48000))
    assert decoded.stats.rms_dbfs <= -50
    assert not decoded.stats.usable


def test_too_short_is_not_usable():
    decoded = decode(webm_opus(tone_pcm(0.1)))
    assert not decoded.stats.usable


def test_as_wav_is_valid_16k_mono():
    decoded = decode(webm_opus(tone_pcm(0.5)))
    with wave.open(io.BytesIO(decoded.as_wav()), "rb") as w:
        assert (w.getnchannels(), w.getframerate(), w.getsampwidth()) == (1, 16000, 2)


def test_garbage_raises_decode_error():
    with pytest.raises(DecodeError):
        decode(b"\x00" * 200)


def test_empty_raises_decode_error():
    with pytest.raises(DecodeError):
        decode(b"")


def test_save_to_writes_the_original_bytes(tmp_path):
    blob = webm_opus(tone_pcm(0.5))
    target = tmp_path / "captures" / "x.webm"
    decoded = decode(blob, save_to=target)
    assert target.read_bytes() == blob
    assert decoded.saved_to == target


def test_read_wav_rejects_wrong_rate(tmp_path):
    path = tmp_path / "bad.wav"
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(44100)
        w.writeframes(b"\x00\x00" * 1000)
    with pytest.raises(DecodeError):
        read_wav(path)
