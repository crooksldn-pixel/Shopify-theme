#!/usr/bin/env python3
"""Terminal REPL against /turn.

The typed interface exists so that repeat testing does not go through voice — and, just as
importantly, so that M5–M10 testing does not burn Max allowance through the tablet loop when a
curl would do. It prints the tool calls, their arguments and per-stage timings, which is what
makes a wrong answer diagnosable.
"""

from __future__ import annotations

import argparse
import uuid

import httpx

BOLD, DIM, YELLOW, RED, GREEN, RESET = "\033[1m", "\033[2m", "\033[33m", "\033[31m", "\033[32m", "\033[0m"

BANNER = """CROOKS Assistant — typed interface
  /new     start a fresh conversation      /health   backend status
  /tools   what the assistant can do       /reload   reload the knowledge base
  /quit    exit
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--session", default="")
    args = parser.parse_args()

    session_id = args.session or f"cli-{uuid.uuid4().hex[:8]}"
    client = httpx.Client(base_url=args.url, timeout=120)
    print(BANNER)

    try:
        health = client.get("/health").json()
        bad = [k for k, c in health["checks"].items() if not c["ok"]]
        print(f"{GREEN if not bad else YELLOW}backend {health['status']}{RESET}"
              + (f" — down: {', '.join(bad)}" if bad else ""))
    except httpx.HTTPError as exc:
        print(f"{RED}Cannot reach {args.url}: {exc}{RESET}\nStart it with: make dev")
        return 1

    while True:
        try:
            text = input(f"\n{BOLD}you ›{RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not text:
            continue

        if text in {"/quit", "/exit"}:
            return 0
        if text == "/new":
            client.post("/reset", data={"session_id": session_id})
            session_id = f"cli-{uuid.uuid4().hex[:8]}"
            print(f"{DIM}new session {session_id}{RESET}")
            continue
        if text == "/health":
            for name, check in client.get("/health").json()["checks"].items():
                mark = f"{GREEN}ok  {RESET}" if check["ok"] else f"{RED}FAIL{RESET}"
                print(f"  {mark} {name:<15} {check['detail']}")
            continue
        if text == "/tools":
            for spec in client.get("/tools").json()["tools"]:
                colour = {"GREEN": GREEN, "AMBER": YELLOW, "RED": RED}[spec["tier"]]
                print(f"  {colour}{spec['tier']:<6}{RESET}{spec['name']}")
            continue
        if text == "/reload":
            print(f"  {client.post('/reload-kb').json()}")
            continue

        try:
            data = client.post("/turn", json={"text": text, "session_id": session_id}).json()
        except httpx.HTTPError as exc:
            print(f"{RED}request failed: {exc}{RESET}")
            continue

        session_id = data.get("session_id", session_id)
        for call in data.get("tool_calls", []):
            if call["ok"]:
                print(f"{DIM}  → {call['name']}  {call.get('ms') or '?'}ms{RESET}")
            else:
                print(f"{RED}  → {call['name']} failed: {call['error']}{RESET}")
        if not data.get("tool_calls"):
            print(f"{DIM}  → no tools used (answered from the knowledge base){RESET}")

        colour = RED if data.get("error_kind") else ""
        print(f"\n{colour}{BOLD}crooks ›{RESET}{colour} {data['answer']}{RESET}")
        timings = data.get("timings_ms") or {}
        if timings:
            print(f"{DIM}  {'  ·  '.join(f'{k} {v}ms' for k, v in timings.items())}{RESET}")


if __name__ == "__main__":
    raise SystemExit(main())
