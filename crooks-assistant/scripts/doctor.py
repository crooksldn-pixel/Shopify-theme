#!/usr/bin/env python3
"""make doctor — check every prerequisite and print what is missing.

Runs on a bare Python with no dependencies installed, because its whole job is to tell you what
is not installed yet.
"""

from __future__ import annotations

import importlib.util
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OK, WARN, BAD = "  ok  ", " warn ", " FAIL "


def run(cmd: list[str]) -> str | None:
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return (out.stdout or out.stderr).strip().splitlines()[0] if out.returncode == 0 else None


def row(status: str, name: str, detail: str) -> None:
    print(f"[{status}] {name:<22} {detail}")


def main() -> int:
    print("\nCROOKS Assistant — environment check\n" + "─" * 74)
    failures = 0
    warnings = 0

    mac = platform.system() == "Darwin"
    row(OK if mac else WARN, "operating system", f"{platform.system()} {platform.release()}")
    if not mac:
        warnings += 1
        print(
            "       The assistant targets macOS on Apple Silicon: whisper.cpp with Core ML,\n"
            "       the Keychain and launchd are all macOS-specific. Everything else in this\n"
            "       repository is portable and its tests run anywhere."
        )

    if mac:
        row(OK, "macOS version", run(["sw_vers", "-productVersion"]) or "unknown")
        arch = platform.machine()
        row(OK if arch == "arm64" else BAD, "architecture", arch)
        if arch != "arm64":
            failures += 1
            print("       Not Apple Silicon — Core ML acceleration will not be available.")
        row(OK, "cpu", run(["sysctl", "-n", "machdep.cpu.brand_string"]) or "unknown")

        xcode = run(["xcode-select", "-p"])
        row(OK if xcode else BAD, "xcode clt", xcode or "MISSING — run: xcode-select --install")
        failures += 0 if xcode else 1

        brew = shutil.which("brew")
        if brew:
            intel = brew.startswith("/usr/local")
            row(WARN if intel else OK, "homebrew", f"{brew} ({run(['brew', '--version']) or ''})")
            if intel:
                warnings += 1
                print("       Homebrew is on the Intel path — this shell may be running under")
                print("       Rosetta and will build x86 binaries. Expect /opt/homebrew.")
        else:
            row(BAD, "homebrew", "MISSING — https://brew.sh")
            failures += 1

    version = sys.version_info
    ok_python = version >= (3, 11)
    row(OK if ok_python else BAD, "python", f"{platform.python_version()} at {sys.executable}")
    if not ok_python:
        failures += 1
        print("       Python 3.11+ is required (3.12 preferred). A system 3.9 on PATH shadows newer ones;")
        print("       create the venv with an explicit interpreter: python3.12 -m venv .venv")
    py312 = shutil.which("python3.12")
    row(OK if py312 else WARN, "python3.12", py312 or "not on PATH — brew install python@3.12 (make venv needs it)")
    warnings += 0 if py312 else 1

    for name, hint in [
        ("git", "brew install git"),
        ("cmake", "brew install cmake"),
        ("ffmpeg", "brew install ffmpeg"),
    ]:
        path = shutil.which(name)
        row(OK if path else BAD, name, run([name, "--version"]) or f"MISSING — {hint}")
        failures += 0 if path else 1

    claude = shutil.which("claude")
    row(OK if claude else BAD, "claude cli", f"{run(['claude', '--version']) or 'MISSING'}")
    if not claude:
        failures += 1
        print("       Install it, then open a NEW shell — PATH is only updated for new shells.")

    tailscale = shutil.which("tailscale") or (
        "/Applications/Tailscale.app/Contents/MacOS/Tailscale"
        if Path("/Applications/Tailscale.app/Contents/MacOS/Tailscale").exists() else None
    )
    row(OK if tailscale else WARN, "tailscale", tailscale or "not found — the tablet needs its HTTPS address (make up sets the route)")
    warnings += 0 if tailscale else 1

    node = shutil.which("node")
    row(OK if node else WARN, "node", run(["node", "--version"]) or "not found — only the renderer tests need it (they skip)")

    whisper_root = Path.home() / "tools" / "whisper.cpp"
    whisper_bin = next((p for p in [whisper_root / "build" / "bin" / "whisper-server", whisper_root / "build" / "whisper-server"] if p.exists()), None)
    vad = next((whisper_root / "models").glob("ggml-silero*.bin"), None) if (whisper_root / "models").exists() else None
    row(OK if whisper_bin else WARN, "whisper.cpp", str(whisper_bin) if whisper_bin else "not built — make whisper-server prints the steps; Scribe still hears without it")
    row(OK if vad else WARN, "whisper vad model", vad.name if vad else "absent — cd ~/tools/whisper.cpp && sh ./models/download-vad-model.sh silero-v5.1.2")
    warnings += (0 if whisper_bin else 1) + (0 if vad else 1)

    print("─" * 74)

    for module, extra in [
        ("fastapi", ""), ("uvicorn", ""), ("httpx", ""), ("pydantic_settings", ""),
        ("av", "PyAV — audio decode"), ("rapidfuzz", ""), ("jellyfish", ""),
        ("keyring", "macOS Keychain"), ("claude_agent_sdk", ""),
        ("googleapiclient", "Gmail"), ("google_auth_oauthlib", "Gmail"),
    ]:
        found = importlib.util.find_spec(module) is not None
        row(OK if found else BAD, module, extra or ("installed" if found else "MISSING"))
        failures += 0 if found else 1
    if failures:
        print("       Missing Python packages — run: make venv")

    print("─" * 74)

    for name in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN"):
        present = bool(os.environ.get(name))
        row(BAD if present else OK, name, "SET — must be unset" if present else "not set (correct)")
        failures += 1 if present else 0
    if any(os.environ.get(n) for n in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN")):
        print("       The assistant runs on the Max subscription. A key in the environment")
        print("       would silently bill you per token. Check your shell profile.")

    print("─" * 74)

    try:
        sys.path.insert(0, str(REPO))
        from app.secrets import keychain

        try:
            keychain.get("claude_oauth_token")
        except keychain.KeychainUnavailable as exc:
            raise RuntimeError(str(exc)) from exc
        except keychain.SecretMissing:
            pass
        for key in keychain.KNOWN_KEYS:
            have = keychain.present(key)
            optional = key in {"shopify_static_token", "gmail_token", "elevenlabs_api_key"}
            absent = {
                "elevenlabs_api_key": "not stored (local Whisper listens; the tablet speaks in its own voice)",
            }.get(key, "not stored (fallback only)")
            row(
                OK if have else (WARN if optional else BAD),
                key,
                "stored" if have else (absent if optional else "MISSING"),
            )
            if not have and not optional:
                warnings += 1
    except Exception as exc:  # noqa: BLE001
        row(WARN, "keychain", f"unavailable to this process — secrets could not be checked: {str(exc)[:70]}")
        warnings += 1
    print("       Store a secret with: make secrets")

    print("─" * 74)
    for path, why in [
        (REPO / "kb" / "terminology.md", "product names as you say them"),
        (REPO / "credentials.json", "the Google Desktop client JSON (see README, Gmail)"),
    ]:
        row(OK if path.exists() else WARN, path.name, str(path) if path.exists() else f"absent — {why}")
    try:
        sys.path.insert(0, str(REPO))
        from app.secrets import keychain as kc

        gmail_ok = kc.present("gmail_token") or (REPO / "token.json").exists()
        row(OK if gmail_ok else WARN, "gmail credential",
            "stored" if gmail_ok else "absent — run: make gmail (the credential goes to the Keychain)")
    except Exception:  # noqa: BLE001
        row(OK if (REPO / "token.json").exists() else WARN, "gmail credential",
            "token.json present" if (REPO / "token.json").exists() else "absent — run: make gmail")

    print("─" * 74)
    if failures:
        print(f"\n{failures} blocking problem(s), {warnings} warning(s). Fix the failures first.\n")
        return 1
    print(f"\nAll prerequisites present. {warnings} warning(s).\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
