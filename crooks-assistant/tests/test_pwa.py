"""The installed app: manifest, icons, service worker and the system layer.

Static checks of what the tablet is served. The worker's behaviour is exercised for real under
Node (tests/web/sw.test.js, via test_web_js.py); here is everything that can be read: that the
manifest says what Chrome needs to install "CROOKS OS", that the icons exist at the sizes it
claims, that the worker's shell list is the shell and nothing else, and that the page never
reloads itself while the owner is recording, waiting or listening.
"""

from __future__ import annotations

import json
import re
import struct
from pathlib import Path

import pytest

WEB = Path(__file__).resolve().parent.parent / "web"
MANIFEST = json.loads((WEB / "manifest.webmanifest").read_text(encoding="utf-8"))
INDEX = (WEB / "index.html").read_text(encoding="utf-8")
STYLE = (WEB / "style.css").read_text(encoding="utf-8")
APP_JS = (WEB / "app.js").read_text(encoding="utf-8")
SW_JS = (WEB / "sw.js").read_text(encoding="utf-8")

BACKEND_PATHS = ("/turn", "/speak", "/tts", "/health", "/state", "/cancel", "/reset", "/audio-test", "/voices", "/tools", "/reload-kb", "/ping")


def function_body(source: str, signature: str) -> str:
    body = source[source.index(signature):]
    return body[: body.index("\n}")]


def png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", f"{path.name} is not a PNG"
    width, height = struct.unpack(">II", data[16:24])
    return width, height


def css_token(name: str) -> str:
    match = re.search(rf"{re.escape(name)}:\s*(#[0-9a-fA-F]{{6}})", STYLE)
    assert match, f"{name} is not defined in style.css"
    return match.group(1).lower()


# --------------------------------------------------------------------------- the manifest


def test_the_manifest_names_the_installed_app():
    assert MANIFEST["name"] == "CROOKS OS"
    assert MANIFEST["short_name"] == "CROOKS"
    assert MANIFEST["display"] == "standalone"
    assert MANIFEST["orientation"] == "portrait-primary"
    assert MANIFEST["start_url"] == "/" and MANIFEST["scope"] == "/" and MANIFEST["id"] == "/"
    assert MANIFEST["prefer_related_applications"] is False


def test_the_manifest_matches_the_interface_ground():
    ground = css_token("--bg-0")
    assert MANIFEST["theme_color"].lower() == ground
    assert MANIFEST["background_color"].lower() == ground
    assert re.search(r'<meta name="theme-color" content="(#[0-9a-fA-F]{6})"', INDEX).group(1).lower() == ground


@pytest.mark.parametrize("purpose", ["any", "maskable"])
@pytest.mark.parametrize("size", [192, 512])
def test_every_icon_exists_at_the_size_it_claims(purpose, size):
    icons = [i for i in MANIFEST["icons"] if i["purpose"] == purpose and i["sizes"] == f"{size}x{size}"]
    assert len(icons) == 1, f"one {purpose} icon at {size}"
    (icon,) = icons
    assert icon["type"] == "image/png" and icon["src"].startswith("/static/")
    assert png_size(WEB / icon["src"].removeprefix("/static/")) == (size, size)


# --------------------------------------------------------------------------- the page


def test_the_page_carries_what_chrome_needs_and_nothing_stale():
    assert '<link rel="manifest" href="/manifest.webmanifest">' in INDEX
    assert "<title>CROOKS OS</title>" in INDEX
    assert '<meta name="application-name" content="CROOKS OS">' in INDEX
    assert '<meta name="mobile-web-app-capable" content="yes">' in INDEX
    assert 'rel="icon" type="image/png" sizes="192x192"' in INDEX
    assert "viewport-fit=cover" in INDEX
    assert "apple-mobile-web-app-capable" not in INDEX   # iOS-only and superseded by the manifest


def test_the_system_layer_is_in_the_page_and_boots_first():
    assert '<div id="system" class="system" data-phase="boot"' in INDEX
    assert 'id="system-title"' in INDEX and 'id="system-sub"' in INDEX
    # Fully covering, above the interface, and gone (not merely transparent) once online.
    assert re.search(r"\.system\{[^}]*position:fixed;inset:0;z-index:30", STYLE)
    assert re.search(r'\.system\[data-phase="online"\]\{[^}]*visibility:hidden;pointer-events:none', STYLE)


# --------------------------------------------------------------------------- the worker


def shell_list() -> list[str]:
    block = SW_JS[SW_JS.index("const SHELL = [") : SW_JS.index("];", SW_JS.index("const SHELL = ["))]
    return re.findall(r"'([^']+)'", block)


def test_the_worker_keeps_the_shell_and_nothing_else():
    shell = shell_list()
    assert "/" in shell and "/static/app.js" in shell and "/manifest.webmanifest" in shell
    for path in shell:
        assert path == "/" or path == "/manifest.webmanifest" or path.startswith("/static/"), path
        assert not path.endswith("fixtures.js"), "the developer fixtures are not the shell"
    for backend in BACKEND_PATHS:
        assert not any(p == backend or p.startswith(backend + "/") for p in shell), f"{backend} must never be cached"
    # Every shell file exists on disk, so the install step cannot fail on a typo.
    for path in shell:
        if path == "/":
            continue
        assert (WEB / path.removeprefix("/static/").removeprefix("/")).exists(), path


def test_the_worker_touches_only_same_origin_gets_for_the_shell():
    fetch_handler = SW_JS[SW_JS.index("self.addEventListener('fetch'") :]
    fetch_handler = fetch_handler[: fetch_handler.index("\n});") + 4]
    assert "if (request.method !== 'GET') return;" in fetch_handler
    assert "if (url.origin !== self.location.origin) return;" in fetch_handler
    assert "if (SHELL.indexOf(path) === -1) return;" in fetch_handler
    # Nothing is queued, synced or replayed: no background sync, no push, no storage but the cache.
    for forbidden in ("'sync'", "periodicsync", "'push'", "indexedDB", "localStorage", "BackgroundSync"):
        assert forbidden not in SW_JS, forbidden


def test_the_worker_takes_over_only_when_told():
    install = SW_JS[SW_JS.index("self.addEventListener('install'") : SW_JS.index("self.addEventListener('activate'")]
    assert "skipWaiting" not in install
    message = SW_JS[SW_JS.index("self.addEventListener('message'") :]
    assert "if (event.data && event.data.type === 'SKIP_WAITING') self.skipWaiting();" in message
    assert "const BUILD = '__BUILD__';" in SW_JS, "the Mac writes the build id in when it serves the file"


def test_the_fallback_page_carries_no_data():
    html = SW_JS[SW_JS.index("const OFFLINE_HTML") : SW_JS.index("self.addEventListener('install'")]
    assert "CROOKS OS" in html and "System offline" in html
    assert not re.search(r"order|customer|@|shopify|gmail", html, re.IGNORECASE)


# --------------------------------------------------------------------------- the system layer


def test_the_page_asks_the_mac_whether_it_is_there_and_never_hangs_on_it():
    body = function_body(APP_JS, "async function checkReachable()")
    assert "fetch('/ping', { cache: 'no-store', signal: controller.signal })" in body
    assert "wentOnline()" in body and "wentOffline()" in body
    assert "const PING_TIMEOUT_MS = 4000;" in APP_JS


def test_offline_is_shown_only_over_a_quiet_screen_and_retries_quietly():
    body = function_body(APP_JS, "function wentOffline()")
    assert "if (idle()) {" in body
    assert "'System offline', 'Waiting for CROOKS Assistant…'" in body
    assert "reconnectTimer = setTimeout(checkReachable, reconnectDelay);" in body
    idle = function_body(APP_JS, "function idle()")
    assert "!busy && !recording && !speakingVia" in idle
    assert "const RECONNECT_MAX_MS = 15000;" in APP_JS


def test_recovery_needs_no_hand():
    body = function_body(APP_JS, "function wentOnline()")
    assert "setSystem('online');" in body
    assert "pollHealth(true);" in body and "acquireWakeLock();" in body and "warmMic();" in body
    assert "window.addEventListener('online'" in APP_JS
    assert "el.system.addEventListener('click'" in APP_JS


def test_a_failed_turn_hands_over_to_the_system_layer_once_it_is_finished():
    assert "if (!controller.signal.aborted) setTimeout(checkReachable, 0);" in APP_JS


# --------------------------------------------------------------------------- updates


def test_a_new_build_is_taken_only_when_nothing_is_in_progress():
    assert "navigator.serviceWorker.register('/sw.js')" in APP_JS
    body = function_body(APP_JS, "function applyUpdateWhenIdle()")
    assert "if (!updateWaiting || !idle()) return;" in body
    assert "worker.postMessage({ type: 'SKIP_WAITING' });" in body
    # The reload after a takeover is the one we asked for, never the first install's.
    assert "if (!updateApplied || reloadingForUpdate) return;" in APP_JS
    # A first install (no controller yet) is not an update and does not reload anything.
    assert "if (worker.state === 'installed' && navigator.serviceWorker.controller)" in APP_JS


def test_a_new_build_on_the_mac_goes_through_the_worker_when_there_is_one():
    body = function_body(APP_JS, "function maybeReloadForNewBuild(build)")
    assert "if (busy || recording || speakingVia || el.settings.open) return;" in body
    assert "swRegistration.update()" in body
    assert "const UPDATE_GRACE_MS = 20000;" in APP_JS


# --------------------------------------------------------------------------- the thin client


@pytest.mark.parametrize("name", sorted(p.name for p in WEB.iterdir() if p.is_file()))
def test_nothing_served_to_the_tablet_holds_a_secret_or_the_mac_s_address(name):
    text = (WEB / name).read_bytes().decode("utf-8", errors="ignore")
    lowered = text.lower()
    for forbidden in ("client_secret", "refresh_token", "authorization:", "bearer ", "192.168.", "10.0.", "100.64.", ".local:8000", "127.0.0.1:8000"):
        assert forbidden not in lowered, f"{name} contains {forbidden}"
    assert not re.search(r"\b(?:sk|xi|shpat|shpca|shpss)_[A-Za-z0-9]{16,}", text), f"{name} contains a key"
