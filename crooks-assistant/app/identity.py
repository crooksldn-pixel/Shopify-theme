"""Who is on the other end of a proxied request, confirmed with Tailscale itself.

`tailscale serve` stamps Tailscale-User-Login and X-Forwarded-For on what it proxies. A
header is a claim, though, and the app listens on loopback, where any process on the Mac
can write one. Before a change is applied, the forwarded address is put to `tailscale
whois`, which answers from the tailnet's own state who holds that address; the login on
the header must be that person. Answers are cached briefly. No CLI, no answer, or a
different person: the change is refused — a claim is never trusted for want of a check."""

from __future__ import annotations

import ipaddress
import json
import logging
import shutil
import subprocess
import threading
import time
from pathlib import Path

log = logging.getLogger("crooks.identity")

TAILNET_V4 = ipaddress.ip_network("100.64.0.0/10")
TAILNET_V6 = ipaddress.ip_network("fd7a:115c:a1e0::/48")
CACHE_S = 600.0        # a confirmed pairing is good for this long
NEGATIVE_S = 30.0      # a refusal is remembered this long, so a busy tablet is not a whois storm
TIMEOUT_S = 2.5
MAC_APP_CLI = "/Applications/Tailscale.app/Contents/MacOS/Tailscale"

_cache: dict[tuple[str, str], tuple[bool, str, float]] = {}
_lock = threading.Lock()
_runner = None   # tests hand in a fake `tailscale whois`


def bind_runner(runner) -> None:
    global _runner
    _runner = runner
    with _lock:
        _cache.clear()


def cli_path(configured: str = "") -> str | None:
    """The Tailscale CLI: configured, on PATH, or inside the Mac app bundle."""
    if configured and Path(configured).exists():
        return configured
    found = shutil.which("tailscale")
    if found:
        return found
    return MAC_APP_CLI if Path(MAC_APP_CLI).exists() else None


def forwarded_address(header: str) -> str:
    """The client address `tailscale serve` put first in X-Forwarded-For."""
    return str(header or "").split(",")[0].strip().strip("[]")


def on_tailnet(address: str) -> bool:
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        return False
    return ip in TAILNET_V4 or ip in TAILNET_V6


def _run_whois(cli: str, address: str) -> str:
    completed = subprocess.run([cli, "whois", "--json", address], capture_output=True, text=True, timeout=TIMEOUT_S, check=False)
    if completed.returncode != 0:
        raise RuntimeError((completed.stderr or completed.stdout or "").strip()[:160] or f"exit {completed.returncode}")
    return completed.stdout


def whois_login(address: str, *, cli: str) -> str | None:
    """The login Tailscale says holds this address, lower-cased; None when it cannot say."""
    runner = _runner or _run_whois
    try:
        out = runner(cli, address)
        data = json.loads(out) if isinstance(out, str) else out
    except Exception as exc:  # noqa: BLE001 — every failure is "cannot say"
        log.warning("tailscale whois %s failed: %s", address, str(exc)[:160])
        return None
    profile = (data or {}).get("UserProfile") or {}
    login = str(profile.get("LoginName") or "").strip().lower()
    return login or None


def verify(address: str, login: str, *, cli: str | None, now: float | None = None) -> tuple[bool, str]:
    """Whether Tailscale confirms that `login` holds `address`. (ok, why)."""
    login = str(login or "").strip().lower()
    address = forwarded_address(address)
    if not login or not address:
        return False, "no login or address to check"
    if not on_tailnet(address):
        return False, f"{address} is not a tailnet address"
    if not cli:
        return False, "the tailscale CLI was not found (set CROOKS_TAILSCALE_CLI)"
    now = time.time() if now is None else now
    key = (address, login)
    with _lock:
        cached = _cache.get(key)
        if cached is not None and now - cached[2] < (CACHE_S if cached[0] else NEGATIVE_S):
            return cached[0], cached[1]
    holder = whois_login(address, cli=cli)
    if holder is None:
        ok, why = False, "tailscale did not say who holds that address"
    elif holder != login:
        ok, why = False, "the address belongs to a different login"
    else:
        ok, why = True, "confirmed by tailscale whois"
    with _lock:
        _cache[key] = (ok, why, now)
    return ok, why
