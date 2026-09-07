#!/usr/bin/env python3
"""M14: walk through the 18 acceptance commands, score them, and apply the pass criteria.

Deliberately manual. It cannot tell you whether an answer was accurate — only you know what the
Shopify admin says — so it asks, one question at a time, and does the arithmetic honestly.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
import time
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import get_settings  # noqa: E402

BOLD, DIM, RED, GREEN, YELLOW, RESET = "\033[1m", "\033[2m", "\033[31m", "\033[32m", "\033[33m", "\033[0m"

THRESHOLDS = {
    "transcript": 16, "tool": 17, "answer": 16, "median_s": 4.0, "p90_s": 6.0, "confident_wrong": 0,
}


def load_commands(path: Path) -> list[dict]:
    """Parse the numbered commands out of tests/acceptance.md, so there is one source of truth."""
    commands = []
    section = ""
    for line in path.read_text(encoding="utf-8").splitlines():
        heading = re.match(r"^### (.+?) \(\d+\)|^### (.+)$", line.strip())
        if heading:
            section = (heading.group(1) or heading.group(2)).strip()
            continue
        item = re.match(r"^(\d+)\.\s+(.+)$", line.strip())
        if item:
            commands.append(
                {"n": int(item.group(1)), "section": section, "text": item.group(2).strip()}
            )
    return commands


def ask_yn(prompt: str) -> bool:
    while True:
        answer = input(f"    {prompt} [y/n] ").strip().lower()
        if answer in {"y", "yes"}:
            return True
        if answer in {"n", "no"}:
            return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--spoken", action="store_true",
                        help="you speak each command on the tablet; this script only scores it")
    args = parser.parse_args()

    settings = get_settings()
    commands = load_commands(Path(__file__).resolve().parent.parent / "tests" / "acceptance.md")
    if not commands:
        print("Could not parse tests/acceptance.md.")
        return 1

    placeholders = [c for c in commands if "[" in c["text"]]
    if placeholders:
        print(f"{YELLOW}{len(placeholders)} command(s) still contain placeholders:{RESET}")
        for c in placeholders:
            print(f"  {c['n']}. {c['text']}")
        print("\nEdit tests/acceptance.md and put real CROOKS values in before scoring.\n")
        if not ask_yn("Run anyway?"):
            return 1

    client = httpx.Client(base_url=args.url, timeout=180)
    session_id = f"acc-{time.strftime('%H%M%S')}"
    records = []

    print(f"\n{BOLD}Day 1 acceptance — {len(commands)} commands{RESET}")
    print(f"{DIM}Speak each one from the tablet, at your normal working distance. Score honestly:")
    print(f"a wrong answer delivered with confidence fails the whole run.{RESET}\n")

    for command in commands:
        print(f"\n{'─' * 74}\n{BOLD}{command['n']}. {command['text']}{RESET}   {DIM}({command['section']}){RESET}")

        if args.spoken:
            input(f"    {DIM}Say it on the tablet, then press Enter.{RESET}")
            transcript = input("    What did the tablet show as the transcript? ").strip()
            answer = input("    What did it answer? ").strip()
            elapsed = float(input("    Roughly how many seconds end to end? ") or 0)
            tools = input("    Which tool(s) did it use, if shown? ").strip()
        else:
            started = time.perf_counter()
            data = client.post("/turn", json={"text": command["text"], "session_id": session_id}).json()
            elapsed = time.perf_counter() - started
            transcript = data.get("question", command["text"])
            answer = data.get("answer", "")
            tools = ", ".join(c["name"] for c in data.get("tool_calls", [])) or "none"
            print(f"    {DIM}tools: {tools}  ·  {elapsed:.1f}s{RESET}")
            print(f"    {BOLD}→{RESET} {answer}")

        transcript_ok = True if not args.spoken else ask_yn("Transcript correct?")
        tool_ok = ask_yn("Right tool(s) for the question?")
        answer_ok = ask_yn("Answer accurate?")
        confident_wrong = False if answer_ok else ask_yn("Was it stated confidently (not hedged)?")

        records.append({
            "n": command["n"], "section": command["section"], "command": command["text"],
            "transcript": transcript, "answer": answer, "tools": tools,
            "seconds": round(elapsed, 2), "transcript_ok": transcript_ok,
            "tool_ok": tool_ok, "answer_ok": answer_ok, "confident_wrong": confident_wrong,
        })

    return report(records, settings)


def report(records: list[dict], settings) -> int:
    total = len(records)
    transcript_ok = sum(r["transcript_ok"] for r in records)
    tool_ok = sum(r["tool_ok"] for r in records)
    answer_ok = sum(r["answer_ok"] for r in records)
    confident_wrong = [r for r in records if r["confident_wrong"]]
    times = sorted(r["seconds"] for r in records)
    median = statistics.median(times) if times else 0
    p90 = times[max(0, int(len(times) * 0.9) - 1)] if times else 0

    checks = [
        ("transcript accuracy", f"{transcript_ok}/{total}", transcript_ok >= THRESHOLDS["transcript"], f"≥{THRESHOLDS['transcript']}"),
        ("tool selection", f"{tool_ok}/{total}", tool_ok >= THRESHOLDS["tool"], f"≥{THRESHOLDS['tool']}"),
        ("answer accuracy", f"{answer_ok}/{total}", answer_ok >= THRESHOLDS["answer"], f"≥{THRESHOLDS['answer']}"),
        ("confidently wrong", str(len(confident_wrong)), not confident_wrong, "0"),
        ("median latency", f"{median:.1f}s", median <= THRESHOLDS["median_s"], f"≤{THRESHOLDS['median_s']}s"),
        ("p90 latency", f"{p90:.1f}s", p90 <= THRESHOLDS["p90_s"], f"≤{THRESHOLDS['p90_s']}s"),
    ]

    print(f"\n\n{'═' * 74}\n{BOLD}DAY 1 ACCEPTANCE{RESET}\n{'═' * 74}")
    for name, value, passed, threshold in checks:
        mark = f"{GREEN}PASS{RESET}" if passed else f"{RED}FAIL{RESET}"
        print(f"  {mark}  {name:<22}{value:>10}   (need {threshold})")

    if confident_wrong:
        print(f"\n{RED}Confidently wrong answers — these fail the run on their own:{RESET}")
        for record in confident_wrong:
            print(f"  {record['n']}. {record['command']}\n     → {record['answer'][:90]}")

    passed = all(check[2] for check in checks)
    print(f"\n{'═' * 74}")
    print(f"{GREEN}{BOLD}DAY 1 PASSES{RESET} — tag the commit v1.0-day1." if passed
          else f"{RED}{BOLD}DAY 1 DOES NOT PASS YET{RESET}")
    if not passed:
        fails = [c[0] for c in checks if not c[2]]
        print("\nWhere to look:")
        if "transcript accuracy" in fails:
            print("  · transcription — revisit the M3 model decision with this evidence, and add")
            print("    the misheard terms to kb/terminology.md before reaching for a bigger model.")
        if "tool selection" in fails:
            print("  · tool descriptions, not the model. Rewrite them to say when to use each.")
        if any("latency" in f for f in fails):
            print("  · check the Claude subprocess is held open, not recreated per turn.")
        if "confidently wrong" in fails:
            print("  · find the tool that returned something misleading instead of an error.")

    settings.bench_results_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    payload = {
        "date": stamp, "passed": passed,
        "summary": {name: {"value": value, "passed": ok} for name, value, ok, _ in checks},
        "records": records,
    }
    out = settings.bench_results_dir / f"acceptance-{stamp}.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    md = settings.bench_results_dir / f"acceptance-{stamp}.md"
    lines = [f"# Day 1 acceptance — {stamp}", "", f"**{'PASS' if passed else 'FAIL'}**", "",
             "| Measure | Result | Threshold | |", "|---|---|---|---|"]
    lines += [f"| {n} | {v} | {t} | {'PASS' if ok else 'FAIL'} |" for n, v, ok, t in checks]
    lines += ["", "## Per command", "", "| # | Command | Transcript | Tool | Answer | s |", "|---|---|---|---|---|---|"]
    lines += [
        f"| {r['n']} | {r['command'][:52]} | {'ok' if r['transcript_ok'] else 'MISS'} | "
        f"{'ok' if r['tool_ok'] else 'MISS'} | {'ok' if r['answer_ok'] else 'MISS'} | {r['seconds']} |"
        for r in records
    ]
    md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"\nWritten to {out}\n            {md}\n")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
