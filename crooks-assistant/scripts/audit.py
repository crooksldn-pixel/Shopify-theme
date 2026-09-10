#!/usr/bin/env python3
"""The Phase 2 tablet audit: drive the page like a person, and write down the numbers.

    python scripts/audit.py                 measure the current build, screenshots to .cache
    python scripts/audit.py --label before  name the run, so before/after can be compared
    python scripts/audit.py --compare       print the last two runs side by side

The regression gate is `scripts/experience.py`; this is the measuring tape. It reuses the same
fixture backend, so what it measures is the same world the golden scenarios assert on.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

OUT = ROOT / "reports" / "audit"
SCRIPT = ROOT / "scripts" / "browser" / "audit.js"
BOLD, DIM, RED, AMBER, GREEN, RESET = "\033[1m", "\033[2m", "\033[31m", "\033[33m", "\033[32m", "\033[0m"


def _tone(value: float, good: float, bad: float) -> str:
    if value <= good:
        return GREEN
    return AMBER if value < bad else RED


async def run(label: str) -> int:
    from experience.browser import CHROMIUM, _free_port, _stop, available, serve_fixture_world

    ok, why = available()
    if not ok:
        print(f"{AMBER}The audit needs a browser: {why}{RESET}")
        return 2

    shots = OUT / label
    shots.mkdir(parents=True, exist_ok=True)
    for stale in shots.glob("*.png"):
        stale.unlink()

    port = _free_port()
    server, task, _store = await serve_fixture_world(port)
    try:
        result = await asyncio.to_thread(
            subprocess.run,
            ["node", str(SCRIPT), f"http://127.0.0.1:{port}", str(shots), label],
            cwd=ROOT, capture_output=True, text=True, timeout=600,
            env={**os.environ, "CROOKS_CHROMIUM": CHROMIUM},
        )
    finally:
        await _stop(server, task)

    payload: dict = {}
    for line in reversed((result.stdout or "").strip().splitlines()):
        try:
            payload = json.loads(line)
            break
        except ValueError:
            continue
    if not payload:
        print(f"{RED}the audit produced no result{RESET}\n{(result.stdout + result.stderr)[-800:]}")
        return 1

    (OUT / f"{label}.json").write_text(json.dumps(payload, indent=1))
    _print(payload, label)
    return 0 if payload.get("ok") else 1


def _print(payload: dict, label: str) -> None:
    print(f"{BOLD}CROOKS OS · tablet audit{RESET}  {DIM}{label} · 800x1280{RESET}")
    if payload.get("errors"):
        for e in payload["errors"]:
            print(f"  {RED}script error{RESET} {e[:110]}")
    print()
    print(f"  {DIM}{'surface':<15}{'chrome':>8}{'scroll':>9}{'screens':>9}{'small':>7}{'below':>7}{'spoken':>8}{RESET}")
    for s in payload.get("surfaces") or []:
        chrome = s.get("contentStartsAt")
        screens = s.get("screensToScroll") or 0
        small, below = s.get("tooSmall") or 0, s.get("belowFold") or 0
        print(
            f"  {s['name']:<15}"
            f"{_tone(chrome or 0, 120, 200)}{(chrome if chrome is not None else '—')!s:>8}{RESET}"
            f"{s.get('scrollHeight', 0):>9}"
            f"{_tone(screens, 1.0, 2.0)}{screens:>9}{RESET}"
            f"{_tone(small, 0, 1)}{small:>7}{RESET}"
            f"{_tone(below, 0, 3)}{below:>7}{RESET}"
            f"{_tone(s.get('spokenChars', 0), 140, 220)}{s.get('spokenChars', 0):>8}{RESET}"
        )
    print()
    for s in payload.get("surfaces") or []:
        notes = []
        if s.get("overflowX"):
            notes.append(f"{RED}spills sideways{RESET}")
        if s.get("repeated"):
            notes.append(f"{AMBER}repeated{RESET} {DIM}{', '.join(s['repeated'][:4])}{RESET}")
        if notes:
            print(f"  {s['name']:<15} {' · '.join(notes)}")
    print(f"\n{DIM}chrome = pixels before the first card · scroll = deck height · screens = scroll/viewport{RESET}")
    print(f"{DIM}small = tap targets under 44px · below = tappables below the fold · spoken = characters said{RESET}")
    print(f"{DIM}screenshots: {OUT / label}{RESET}")


def compare() -> int:
    runs = sorted(OUT.glob("*.json"), key=lambda p: p.stat().st_mtime)
    if len(runs) < 2:
        print("Need two runs to compare. Try `python scripts/audit.py --label before` first.")
        return 2
    old, new = json.loads(runs[-2].read_text()), json.loads(runs[-1].read_text())
    by_name = {s["name"]: s for s in old.get("surfaces") or []}
    print(f"{BOLD}{runs[-2].stem} → {runs[-1].stem}{RESET}\n")
    print(f"  {DIM}{'surface':<15}{'chrome':>14}{'scroll':>16}{'small':>12}{'spoken':>14}{RESET}")
    for s in new.get("surfaces") or []:
        was = by_name.get(s["name"])
        if not was:
            continue

        def move(key: str, before=was, now=s) -> str:
            a, b = before.get(key) or 0, now.get(key) or 0
            if a == b:
                return f"{DIM}{b:>6} ={RESET}    "
            arrow = "↓" if b < a else "↑"
            tone = GREEN if b < a else RED     # every column here is lower-is-better
            return f"{tone}{a:>5}{arrow}{b:<5}{RESET}"

        print(f"  {s['name']:<15}{move('contentStartsAt'):>14}{move('scrollHeight'):>16}"
              f"{move('tooSmall'):>12}{move('spokenChars'):>14}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Measure the tablet interface.")
    parser.add_argument("--label", default="after", help="name this run (before / after / ...)")
    parser.add_argument("--compare", action="store_true", help="diff the last two runs")
    args = parser.parse_args()
    if args.compare:
        return compare()
    try:
        return asyncio.run(run(args.label))
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
