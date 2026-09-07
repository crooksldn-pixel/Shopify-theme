"""Audio decode, round-tripped through PyAV the way Chrome's MediaRecorder produces it."""

from __future__ import annotations

import io
import math
import struct
import wave

import pytest

av = pytest.importorskip("av")

from app.speech.decode import DecodeError, decode, read_wav  # noqa: E402


def tone_pcm(seconds: float = 1.0, rate: int = 48000, hz: float = 440.0, amplitude: float = 0.5) -> bytes:
    count = int(rate * seconds)
    return struct.pack(
        f"<{count}h", *(int(amplitude * 32767 * math.sin(2 * math.pi * hz * i / rate)) for i in range(count))
    )


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
