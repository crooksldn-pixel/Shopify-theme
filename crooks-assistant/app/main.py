"""FastAPI application.

Bound to loopback and served to the tablet by `tailscale serve`, which supplies the trusted
HTTPS origin that getUserMedia and speechSynthesis both require. Binding 0.0.0.0 and using the
LAN IP looks like it works and then fails on the browser API that actually matters.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app import runtime as runtime_module
from app.logging.turnlog import RedactingFilter
from app.providers.max_agent_sdk import BillingGuardError, assert_no_payg_credentials
from app.routes import admin, health, speak, turn
from config.settings import get_settings

log = logging.getLogger("crooks")


def configure_logging(log_dir: Path) -> None:
    """Every log line — stdout and file — passes through the redaction filter, and the file
    rotates. Under launchd stdout goes to a file that would otherwise grow forever."""
    from logging.handlers import RotatingFileHandler

    fmt = logging.Formatter("%(asctime)s %(levelname)-7s %(name)-22s %(message)s", "%H:%M:%S")
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    if getattr(root, "_crooks_configured", False):
        return
    stream = logging.StreamHandler()
    stream.setFormatter(fmt)
    stream.addFilter(RedactingFilter())
    root.addHandler(stream)
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        rotating = RotatingFileHandler(log_dir / "assistant.log", maxBytes=5_000_000, backupCount=5)
        rotating.setFormatter(fmt)
        rotating.addFilter(RedactingFilter())
        root.addHandler(rotating)
    except OSError as exc:
        log.warning("file logging disabled: %s", exc)
    root._crooks_configured = True  # type: ignore[attr-defined]

WEB_DIR = Path(__file__).resolve().parent.parent / "web"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # The billing guard is the one startup failure that must stop the process outright. A
    # missing token can be fixed while the backend keeps serving /health; a present API key
    # cannot be allowed to serve a single turn.
    assert_no_payg_credentials()
    settings = get_settings()
    configure_logging(settings.log_dir)
    app.state.runtime = runtime_module.build(settings)
    app.state.health_cache = None   # /health answers from a recent result; none yet
    app.state.health_lock = None
    app.state.allowed_logins = tuple(
        login.strip().lower() for login in settings.allowed_logins.split(",") if login.strip()
    )
    try:
        await app.state.runtime.provider.start()
    except BillingGuardError:
        raise
    except Exception as exc:  # noqa: BLE001
        # A missing Claude token must not stop the backend booting: /health then names the
        # problem, and each /turn retries start() so fixing it needs no restart.
        log.error("Claude provider did not start: %s", exc)
    log.info("CROOKS Assistant ready (bind address is whatever uvicorn was started with)")
    yield
    await app.state.runtime.aclose()


app = FastAPI(title="CROOKS Assistant", version="0.1.0", lifespan=lifespan)


@app.middleware("http")
async def guard_and_freshness(request: Request, call_next):
    """Two small things every request passes through.

    Who may ask: by default anyone who can reach the port — the tailnet is the owner's own
    private network and the backend binds to loopback behind it. When CROOKS_ALLOWED_LOGINS
    names Tailscale logins, `tailscale serve` tags every proxied request with the caller's
    login and only those callers are answered; a request that reaches the port without the
    header (curl on the Mac itself) is still allowed, because it is on the Mac.

    What the tablet keeps: the page and its scripts are served with no-cache, so a page open
    for a week picks up a new build on its next load rather than in a fortnight.
    """
    allowed = getattr(request.app.state, "allowed_logins", ())
    if allowed:
        login = request.headers.get("tailscale-user-login", "")
        # `tailscale serve` adds X-Forwarded-For to everything it proxies and a login only for
        # tailnet users: a proxied request with no login is Funnel or a tagged node, and is
        # refused. A request with neither header was made on the Mac itself.
        proxied = bool(request.headers.get("x-forwarded-for"))
        if (login and login.lower() not in allowed) or (proxied and not login):
            return JSONResponse(status_code=403, content={"error": "not allowed", "who": login or "unknown"})
    response = await call_next(request)
    path = request.url.path
    if path == "/" or path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-cache"
    return response


app.include_router(health.router)
app.include_router(turn.router)
app.include_router(speak.router)
app.include_router(admin.router)

if WEB_DIR.exists():
    app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")

    @app.get("/")
    async def index() -> FileResponse:
        return FileResponse(WEB_DIR / "index.html")
