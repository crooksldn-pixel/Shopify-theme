#!/usr/bin/env python3
"""Launch whisper.cpp's whisper-server with the flags this project depends on.

The two flags that matter are --vad (silence becomes nothing, not "Thank you.") and the Core ML
encoder, which whisper-server picks up automatically when the .mlmodelc sits beside the .bin.
Without it everything still works, twice as slowly, with no error — which is why this script
checks for the file and says so.
"""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import get_settings  # noqa: E402

BUILD_COMMAND = """
git clone https://github.com/ggml-org/whisper.cpp ~/tools/whisper.cpp
cd ~/tools/whisper.cpp
cmake -B build -DWHISPER_COREML=1 && cmake --build build -j --config Release
sh ./models/download-ggml-model.sh small.en
sh ./models/download-ggml-model.sh medium.en

# The upstream Core ML script is broken. Fetch the encoders by hand and unzip them into models/:
#   https://huggingface.co/ggerganov/whisper.cpp/tree/main   (ggml-small.en-encoder.mlmodelc.zip)

# Silero VAD:
sh ./models/download-vad-model.sh silero-v5.1.2
"""


@dataclass
class Resolved:
    """What starting whisper-server would run, or why it cannot."""

    cmd: list[str] | None
    problem: str = ""
    notes: list[str] = field(default_factory=list)


def resolve(settings=None) -> Resolved:
    settings = settings or get_settings()
    root = settings.whisper_bin_dir
    model = root / "models" / f"ggml-{settings.whisper_model}.bin"
    coreml = root / "models" / f"ggml-{settings.whisper_model}-encoder.mlmodelc"
    vad = next((root / "models").glob("ggml-silero*.bin"), None) if root.exists() else None
    binary = next(
        (p for p in [root / "build" / "bin" / "whisper-server", root / "build" / "whisper-server"]
         if p.exists()),
        None,
    )

    notes: list[str] = []
    if binary is None or not model.exists():
        return Resolved(None, f"whisper.cpp is not built at {root}.\n\nBuild it with:\n{BUILD_COMMAND}")

    if not coreml.exists():
        notes.append(
            f"{coreml.name} is not present, so the encoder runs on Metal rather than the\n"
            "Neural Engine. That is correct and fine if whisper.cpp was built with\n"
            "-DWHISPER_COREML=OFF (the large-v3-turbo build on this Mac). If it was built WITH\n"
            "Core ML, the missing file makes it about twice as slow with no error — unzip the\n"
            "encoder from Hugging Face into models/ in that case."
        )
    if vad is None:
        return Resolved(None, (
            "No Silero VAD model found in models/. Without it the server rejects every request\n"
            "that asks for VAD, and silence that slips past the level gate transcribes as\n"
            "'Thank you.' Refusing to start. Fix:\n\n"
            f"  cd {root} && sh ./models/download-vad-model.sh silero-v5.1.2"
        ), notes)

    host, port = settings.whisper_url.rsplit(":", 1)
    cmd = [
        str(binary),
        "--model", str(model),
        "--host", host.rsplit("/", 1)[-1],
        "--port", port,
        "--language", "en",
        "--threads", str(os.cpu_count() or 8),
        "--no-timestamps",
        # Suppress non-speech tokens at the decoder. Flags verified against `whisper-server --help`.
        "--suppress-nst",
    ]
    if vad is not None:
        cmd += [
            "--vad", "--vad-model", str(vad),
            # Keep the soft onset of the first word rather than trimming it at the speech
            # boundary. The tablet fix (a warm microphone stream) removes the other cause.
            "--vad-speech-pad-ms", str(settings.whisper_vad_pad_ms),
        ]

    return Resolved(cmd, "", notes)


def main() -> int:
    resolved = resolve()
    for note in resolved.notes:
        print(f"Note: {note}\n")
    if resolved.cmd is None:
        print(resolved.problem)
        return 1
    print(" ".join(resolved.cmd) + "\n")
    return subprocess.call(resolved.cmd)


if __name__ == "__main__":
    raise SystemExit(main())
