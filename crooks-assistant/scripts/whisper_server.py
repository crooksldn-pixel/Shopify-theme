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


def main() -> int:
    settings = get_settings()
    root = settings.whisper_bin_dir
    model = root / "models" / f"ggml-{settings.whisper_model}.bin"
    coreml = root / "models" / f"ggml-{settings.whisper_model}-encoder.mlmodelc"
    vad = next((root / "models").glob("ggml-silero*.bin"), None) if root.exists() else None
    binary = next(
        (p for p in [root / "build" / "bin" / "whisper-server", root / "build" / "whisper-server"]
         if p.exists()),
        None,
    )

    if binary is None or not model.exists():
        print(f"whisper.cpp is not built at {root}.\n\nBuild it with:\n{BUILD_COMMAND}")
        return 1

    if not coreml.exists():
        print(
            f"WARNING: {coreml.name} is missing. Inference will run on GPU only — roughly twice\n"
            "as slow, with no error message. Download the encoder zip from Hugging Face and\n"
            "unzip it into models/ before trusting any benchmark number.\n"
        )
    if vad is None:
        print("WARNING: no Silero VAD model found. Without VAD, silence transcribes as 'Thank you.'\n")

    host, port = settings.whisper_url.rsplit(":", 1)
    cmd = [
        str(binary),
        "--model", str(model),
        "--host", host.rsplit("/", 1)[-1],
        "--port", port,
        "--language", "en",
        "--threads", str(os.cpu_count() or 8),
        "--no-timestamps",
        "--print-progress", "false",
    ]
    if vad is not None:
        cmd += ["--vad", "--vad-model", str(vad)]

    print(" ".join(cmd) + "\n")
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
