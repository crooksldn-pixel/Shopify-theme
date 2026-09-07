#!/usr/bin/env python3
"""M3's benchmark: small.en vs medium.en, on YOUR tablet audio, with YOUR vocabulary.

The point of this script is to make the model choice a measurement rather than a preference.
It applies the decision rule from the build plan to the numbers it collects and prints the
answer, so the decision is recorded rather than remembered.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.clients.whisper import WhisperClient  # noqa: E402
from app.speech.decode import DecodeError, decode, read_wav  # noqa: E402
from app.speech.normalise import from_file  # noqa: E402
from app.speech.transcribe import build_prompt  # noqa: E402
from config.settings import get_settings  # noqa: E402

# The plan's rule, in one place so it cannot drift: medium only wins if it fixes at least two
# CROOKS-term errors AND stays inside the latency budget.
MEDIUM_MIN_FIXES = 2
MEDIUM_MAX_MS = 700


def load_expected(path: Path) -> dict[str, str]:
    expected = {}
    if not path.exists():
        return expected
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "|" not in line:
            continue
        stem, text = line.split("|", 1)
        expected[stem.strip()] = text.strip()
    return expected


def similar(a: str, b: str) -> bool:
    strip = lambda s: "".join(c for c in s.lower() if c.isalnum() or c.isspace()).split()  # noqa: E731
    return strip(a) == strip(b)


async def bench_model(model: str, files: list[Path], normaliser, iterations: int, url: str):
    client = WhisperClient(url, model=model)
    prompt = build_prompt(normaliser.catalogue.prompt_terms())  # exactly what production sends
    rows = []
    for path in files:
        try:
            audio = read_wav(path) if path.suffix == ".wav" else decode(path.read_bytes())
        except DecodeError as exc:
            print(f"  ! {path.name}: {exc}")
            continue
        wav = audio.as_wav()
        times, raw = [], ""
        for _ in range(iterations):
            started = time.perf_counter()
            transcript = await client.transcribe(wav, prompt=prompt)
            times.append((time.perf_counter() - started) * 1000)
            raw = transcript.text
        normalised = normaliser.normalise(raw)
        rows.append(
            {
                "file": path.name,
                "stem": path.stem,
                "audio_s": round(audio.stats.duration_s, 2),
                "rms_dbfs": round(audio.stats.rms_dbfs, 1),
                "median_ms": round(statistics.median(times), 1),
                "raw": raw.strip(),
                "normalised": normalised.text.strip(),
                "matches": [f"{m.heard}→{m.replaced_with}" for m in normalised.matches],
            }
        )
    return rows


def score(rows: list[dict], expected: dict[str, str]) -> tuple[int, int]:
    raw_ok = norm_ok = 0
    for row in rows:
        want = expected.get(row["stem"])
        if want is None:
            continue
        raw_ok += similar(row["raw"], want)
        norm_ok += similar(row["normalised"], want)
    return raw_ok, norm_ok


def report(model: str, rows: list[dict], expected: dict[str, str]) -> None:
    print(f"\n{'─' * 78}\n{model}\n{'─' * 78}")
    print(f"{'file':<18}{'audio':>7}{'median':>9}  transcript")
    for row in rows:
        want = expected.get(row["stem"])
        mark = "" if want is None else ("  ok" if similar(row["normalised"], want) else "  MISS")
        print(f"{row['file'][:17]:<18}{row['audio_s']:>6.1f}s{row['median_ms']:>8.0f}ms  {row['normalised'][:44]}{mark}")
        if row["raw"].strip() != row["normalised"].strip():
            print(f"{'':<18}{'':>16}  raw: {row['raw'][:44]}")
        if row["matches"]:
            print(f"{'':<18}{'':>16}  fixed: {', '.join(row['matches'])[:60]}")
    if rows:
        print(f"\nmedian across corpus: {statistics.median(r['median_ms'] for r in rows):.0f} ms")
    if expected:
        raw_ok, norm_ok = score(rows, expected)
        scored = sum(1 for r in rows if r["stem"] in expected)
        print(f"correct: {raw_ok}/{scored} raw, {norm_ok}/{scored} after normalisation")


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="+", default=["small.en", "medium.en"])
    parser.add_argument("--iterations", type=int, default=5)
    parser.add_argument("--url", default="")
    args = parser.parse_args()

    settings = get_settings()
    url = args.url or settings.whisper_url
    files = sorted(
        p for p in settings.bench_audio_dir.iterdir()
        if p.suffix.lower() in {".webm", ".wav", ".ogg", ".m4a", ".mp4"}
    ) if settings.bench_audio_dir.exists() else []

    if not files:
        print(
            f"No audio in {settings.bench_audio_dir}.\n\n"
            "M3 depends on M2: the benchmark must run on clips recorded through the TABLET at\n"
            "your working distance. Benchmarking on the MacBook's mic array measures the wrong\n"
            "microphone. Record the five phrases in bench/phrases.txt from the tablet first."
        )
        return 1

    expected = load_expected(Path(settings.bench_audio_dir).parent / "phrases.txt")
    normaliser = from_file(settings.kb_dir / "terminology.md")
    print(f"corpus: {len(files)} file(s) · terminology: {len(normaliser.catalogue)} term(s) "
          f"· {args.iterations} iteration(s) each")

    results = {}
    for model in args.models:
        print(f"\nSwitch whisper-server to {model} now, then press Enter (Ctrl-C to skip).")
        try:
            input()
        except (EOFError, KeyboardInterrupt):
            print(f"skipping {model}")
            continue
        rows = await bench_model(model, files, normaliser, args.iterations, url)
        results[model] = rows
        report(model, rows, expected)

    decision = decide(results, expected)
    print(f"\n{'═' * 78}\nDECISION: {decision['model']}\n{decision['why']}\n{'═' * 78}")

    settings.bench_results_dir.mkdir(parents=True, exist_ok=True)
    out = settings.bench_results_dir / f"whisper-{time.strftime('%Y%m%d-%H%M%S')}.json"
    out.write_text(json.dumps({"results": results, "decision": decision}, indent=2), encoding="utf-8")
    print(f"\nWritten to {out}. Record the decision and these numbers in the README.")
    return 0


def decide(results: dict, expected: dict) -> dict:
    """Apply the plan's rule to the measured numbers, rather than eyeballing them."""
    small, medium = results.get("small.en"), results.get("medium.en")
    if not small:
        return {"model": "unknown", "why": "small.en was not benchmarked."}

    _, small_ok = score(small, expected)
    scored = sum(1 for r in small if r["stem"] in expected)
    small_ms = statistics.median(r["median_ms"] for r in small)

    if scored and small_ok == scored:
        return {
            "model": "small.en",
            "why": f"small.en got all {scored} phrases right after normalisation "
                   f"({small_ms:.0f} ms median). No argument for a bigger model.",
        }
    if not medium:
        return {"model": "small.en", "why": "medium.en was not benchmarked; keep small.en."}

    _, medium_ok = score(medium, expected)
    medium_ms = statistics.median(r["median_ms"] for r in medium)
    fixes = medium_ok - small_ok

    if fixes >= MEDIUM_MIN_FIXES and medium_ms <= MEDIUM_MAX_MS:
        return {
            "model": "medium.en",
            "why": f"medium.en fixed {fixes} more phrase(s) than small.en and runs in "
                   f"{medium_ms:.0f} ms, inside the {MEDIUM_MAX_MS} ms budget.",
        }
    return {
        "model": "small.en",
        "why": f"medium.en fixed {fixes} phrase(s) at {medium_ms:.0f} ms — the rule needs "
               f"{MEDIUM_MIN_FIXES}+ fixes within {MEDIUM_MAX_MS} ms. Remaining errors are the "
               "normaliser's job: add the terms to kb/terminology.md rather than buying 300 ms.",
    }


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
