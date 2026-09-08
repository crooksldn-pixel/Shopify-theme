#!/usr/bin/env python3
"""make install — have the Mac start the assistant itself, at login, with no Terminal open.

Writes two launchd agents from the templates in launchd/ — the backend and whisper-server —
with this checkout's paths filled in, loads them into your login session, makes Tailscale
serve port 8000 over HTTPS in the background (which persists), and reads /health back.

    make install     install (or reinstall) and start now
    make status      is it running, what does /health say, what is the address
    make restart     restart both services (after `git pull`, say)
    make uninstall   stop and remove the agents

These are LaunchAgents, not daemons: they run inside your login session, so the claude CLI's
own login and the Keychain both work exactly as they do in a Terminal. The Mac has to be logged
in (the lid can be shut; sleep is what you want to prevent — System Settings → Energy).
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import launch_common as lc  # noqa: E402

AGENT_DIR = Path.home() / "Library" / "LaunchAgents"


def launchctl(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["launchctl", *args], capture_output=True, text=True, timeout=30)


def rendered_plists(values: dict[str, str] | None = None) -> dict[str, str]:
    values = values or lc.plist_values()
    out = {}
    for label, filename in lc.AGENTS.items():
        template = (lc.LAUNCHD_DIR / filename).read_text(encoding="utf-8")
        out[label] = lc.render(template, values)
    return out


def preflight() -> list[str]:
    problems = []
    if not lc.VENV_PYTHON.exists():
        problems.append(f"no virtualenv at {lc.VENV_PYTHON} — run: make venv")
    if not lc.find_claude():
        problems.append("the claude CLI was not found — install it and open a new Terminal")
    if not lc.find_tailscale():
        problems.append("Tailscale was not found — the tablet needs its HTTPS address")
    return problems


def install(port: int) -> int:
    problems = preflight()
    for problem in problems:
        print(f"  FAIL   {problem}")
    if problems:
        return 1
    AGENT_DIR.mkdir(parents=True, exist_ok=True)
    lc.LOG_DIR.mkdir(parents=True, exist_ok=True)
    domain = f"gui/{lc.uid()}"
    for label, body in rendered_plists().items():
        target = AGENT_DIR / f"{label}.plist"
        # Stop the previous copy first: launchd will not reload a changed plist in place.
        launchctl("bootout", f"{domain}/{label}")
        target.write_text(body, encoding="utf-8")
        out = launchctl("bootstrap", domain, str(target))
        if out.returncode != 0:
            # Older macOS: fall back to the legacy verb.
            out = launchctl("load", "-w", str(target))
        if out.returncode != 0:
            print(f"  FAIL   {label}: {(out.stderr or out.stdout).strip()}")
            return 1
        launchctl("kickstart", "-k", f"{domain}/{label}")
        print(f"  ok     {label} → {target}")
    host, note = lc.ensure_serve(port)
    print(f"  https  https://{host}/  ({note})" if host else f"  https  not available: {note}")
    print("  wait   backend starting…")
    health = lc.wait_for_health(f"http://127.0.0.1:{port}/health", timeout_s=60)
    print(f"  health {lc.summarise_health(health)}")
    if health is None:
        print(f"         look in {lc.LOG_DIR}/assistant.err.log")
        return 1
    print("\n  Done. Both services now start when you log in. Open the address above on the tablet.")
    return 0


def uninstall() -> int:
    domain = f"gui/{lc.uid()}"
    for label in lc.AGENTS:
        launchctl("bootout", f"{domain}/{label}")
        target = AGENT_DIR / f"{label}.plist"
        if target.exists():
            target.unlink()
        print(f"  ok     {label} removed")
    print("  Tailscale still serves port 8000; `tailscale serve reset` clears that if you want.")
    return 0


def restart(port: int) -> int:
    domain = f"gui/{lc.uid()}"
    for label in lc.AGENTS:
        out = launchctl("kickstart", "-k", f"{domain}/{label}")
        print(f"  {'ok    ' if out.returncode == 0 else 'FAIL  '} {label} {(out.stderr or '').strip()}")
    time.sleep(2)
    health = lc.wait_for_health(f"http://127.0.0.1:{port}/health", timeout_s=60)
    print(f"  health {lc.summarise_health(health)}")
    return 0 if health else 1


def status(port: int) -> int:
    domain = f"gui/{lc.uid()}"
    running = 0
    for label in lc.AGENTS:
        out = launchctl("print", f"{domain}/{label}")
        if out.returncode != 0:
            print(f"  --     {label}: not installed (make install)")
            continue
        pid = next((line.split("=", 1)[1].strip() for line in out.stdout.splitlines() if "pid =" in line), "")
        state = next((line.split("=", 1)[1].strip() for line in out.stdout.splitlines() if "state =" in line), "")
        print(f"  {'ok    ' if pid else 'DOWN  '} {label}: {state or 'unknown'}{' pid ' + pid if pid else ''}")
        running += 1 if pid else 0
    host, note = lc.serve_status(port)
    print(f"  https  https://{host}/" if host else f"  https  {note}")
    health = lc.fetch_health(f"http://127.0.0.1:{port}/health")
    print(f"  health {lc.summarise_health(health)}")
    return 0 if running == len(lc.AGENTS) and health else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--uninstall", action="store_true")
    group.add_argument("--status", action="store_true")
    group.add_argument("--restart", action="store_true")
    group.add_argument("--print", action="store_true", help="show the rendered plists and exit")
    args = parser.parse_args(argv)

    if args.print:
        for label, body in rendered_plists().items():
            print(f"# {label}\n{body}\n")
        return 0
    if not lc.is_macos():
        print("launchd is macOS only. On other systems use: make up")
        return 1
    from config.settings import get_settings

    port = get_settings().port
    if args.uninstall:
        return uninstall()
    if args.status:
        return status(port)
    if args.restart:
        return restart(port)
    return install(port)


if __name__ == "__main__":
    raise SystemExit(main())
