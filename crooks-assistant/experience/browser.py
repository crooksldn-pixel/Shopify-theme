"""The page in a real browser, against a real backend serving the golden world.

Everything else in this package drives the application through ASGI, which is the right way to
assert on what the backend produced. It cannot tell you whether a finger can hit the thing, or
whether the card fits an eight-inch screen, or whether the page threw on the way to drawing it.
Those need a browser and a socket.

So this starts uvicorn on loopback with the fixture clients bound, hands the address to
`scripts/browser/experience.js`, and collects what it reports. The backend is the real one and
the fixture world is the same one the scenarios use, so a card in a screenshot is a card the
scenarios asserted on.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import os
import shutil
import socket
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "browser" / "experience.js"
# The physical tablet's own viewport, 601 x 889 at DPR 1.33: the checks the Phase 2 live test
# found on the device and the 800 x 1280 gate could not see. Run after the gate, folded into
# the same result, so one green means both sizes.
TABLET_SCRIPT = ROOT / "scripts" / "browser" / "tablet.js"
# Where Playwright's Chromium lives in this environment. Overridable, because on the Mac it
# will be wherever `npx playwright install` put it.
CHROMIUM = os.environ.get("CROOKS_CHROMIUM", "/opt/pw-browsers/chromium-1194/chrome-linux/chrome")

log = logging.getLogger("crooks.experience.browser")


class BrowserUnavailable(RuntimeError):
    """Node, playwright-core or a Chromium is missing. The suite says so and carries on: a
    browser check that cannot run is reported as skipped, never as passed."""


def available() -> tuple[bool, str]:
    if shutil.which("node") is None:
        return False, "node is not installed"
    if not SCRIPT.exists():
        return False, f"{SCRIPT.name} is missing"
    probe = subprocess.run(["node", "-e", "require.resolve('playwright-core')"],
                           cwd=ROOT, capture_output=True, text=True)
    if probe.returncode != 0:
        return False, "playwright-core is not installed (npm i playwright-core)"
    if not Path(CHROMIUM).exists():
        return False, f"no Chromium at {CHROMIUM}"
    return True, ""


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


async def serve_fixture_world(port: int):
    """A real uvicorn on loopback, with the golden world bound to it.

    The lifespan builds the runtime with whatever clients the settings describe, so the swap
    happens after start-up — the same order the harness uses, and for the same reason.
    """
    import uvicorn

    from app.main import app
    from app.runtime import _make_customer_lookup
    from app.session.manager import SessionManager
    from app.tools import gmail_tools, gmail_writes, shopify_tools
    from experience.fixtures import FixtureShopify, fixture_gmail
    from experience.harness import RecordingProvider, _warm

    original_lifespan = app.router.lifespan_context

    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning", lifespan="on")
    server = uvicorn.Server(config)
    task = asyncio.create_task(server.serve())
    for _ in range(200):
        await asyncio.sleep(0.05)
        if server.started:
            break
    if not server.started:
        task.cancel()
        raise BrowserUnavailable("the fixture backend did not start")

    runtime = app.state.runtime
    runtime.provider = RecordingProvider()
    store, gmail = FixtureShopify(), fixture_gmail()
    runtime.shopify = store
    runtime.gmail = gmail
    shopify_tools.bind(store)
    # Both Gmail modules, and the real customer cross-reference — the same three the harness
    # binds, and for the same reasons: `runtime.customer_lookup` does not exist, and the write
    # module holds its own client which would otherwise still be the real one.
    gmail_tools.bind(gmail, customer_lookup=_make_customer_lookup(store))
    gmail_writes.bind(gmail, customer=_make_customer_lookup(store),
                      policy=lambda: runtime.settings)
    runtime.sessions = SessionManager()
    runtime.settings = runtime.settings.model_copy(update={
        "writes_enabled": True, "allowed_logins": "owner@example.com",
        "writes_local_owner": False, "tailscale_verify": False,
    })
    app.state.allowed_logins = runtime.allowed_logins
    await _warm(runtime)
    _ = original_lifespan
    return server, task, store


async def capture_screens(_harness: Any, *, out: Path, only: str = "") -> list[Path]:
    """Drive the page and take the pictures. Returns the files written.

    The harness passed in is NOT used to serve: a browser needs a socket, so a second backend
    is started on loopback against the same fixture world. They do not share a session, which
    is deliberate — the browser run is its own conversation.
    """
    ok, why = available()
    if not ok:
        log.warning("browser checks skipped: %s", why)
        return []
    out.mkdir(parents=True, exist_ok=True)
    for stale in out.glob("*.png"):
        stale.unlink()

    port = _free_port()
    server, task, _store = await serve_fixture_world(port)
    try:
        result = await asyncio.to_thread(
            subprocess.run,
            ["node", str(SCRIPT), f"http://127.0.0.1:{port}", str(out)],
            cwd=ROOT, capture_output=True, text=True, timeout=300,
            env={**os.environ, "CROOKS_CHROMIUM": CHROMIUM},
        )
    finally:
        await _stop(server, task)

    payload: dict[str, Any] = {}
    for line in reversed((result.stdout or "").strip().splitlines()):
        try:
            payload = json.loads(line)
            break
        except ValueError:
            continue
    if not payload:
        log.warning("the browser run produced no result: %s", (result.stdout + result.stderr)[-400:])
        return []

    for entry in payload.get("checks") or []:
        mark = "ok  " if entry.get("ok") else "FAIL"
        print(f"    {mark} {entry.get('name')}"
              + (f"  — {entry.get('detail')}" if not entry.get("ok") and entry.get("detail") else ""),
              file=sys.stderr)
    if not payload.get("ok"):
        log.warning("browser checks failed")
    _ = only
    return sorted(out.glob("*.png"))


async def run_checks() -> dict[str, Any]:
    """The browser checks on their own, for a test to assert on."""
    ok, why = available()
    if not ok:
        return {"skipped": True, "why": why, "checks": []}
    port = _free_port()
    server, task, _store = await serve_fixture_world(port)
    try:
        results = []
        for script in (SCRIPT, TABLET_SCRIPT):
            if not script.exists():
                continue
            results.append(await asyncio.to_thread(
                subprocess.run,
                ["node", str(script), f"http://127.0.0.1:{port}", ""],
                cwd=ROOT, capture_output=True, text=True, timeout=300,
                env={**os.environ, "CROOKS_CHROMIUM": CHROMIUM},
            ))
    finally:
        await _stop(server, task)
    merged: dict[str, Any] = {"skipped": False, "ok": True, "checks": [], "shots": []}
    for result in results:
        payload = None
        for line in reversed((result.stdout or "").strip().splitlines()):
            try:
                payload = json.loads(line)
                break
            except ValueError:
                continue
        if payload is None:
            payload = {"ok": False, "checks": [{"name": "browser run", "ok": False, "detail": (result.stdout + result.stderr)[-400:]}]}
        merged["ok"] = bool(merged["ok"] and payload.get("ok"))
        merged["checks"].extend(payload.get("checks") or [])
        merged["shots"].extend(payload.get("shots") or [])
    return merged


async def _stop(server: Any, task: asyncio.Task) -> None:
    """Shut the fixture backend down without leaving a traceback in the suite's output.

    uvicorn's socket closes a beat after the serve task returns, and anything still finishing
    then raises "Event loop is closed" into stderr — noise that reads like a failure in a run
    that passed. A moment for the loop to drain removes it.
    """
    server.should_exit = True
    try:
        await asyncio.wait_for(asyncio.shield(task), timeout=10)
    except (TimeoutError, asyncio.CancelledError):
        task.cancel()
        with contextlib.suppress(BaseException):
            await task
    # A beat for uvicorn's transports to finish closing before the loop goes.
    await asyncio.sleep(0.25)
