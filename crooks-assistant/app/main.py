"""FastAPI application.

Bound to loopback and served to the tablet by `tailscale serve`, which supplies the trusted
HTTPS origin that getUserMedia and speechSynthesis both require. Binding 0.0.0.0 and using the
LAN IP looks like it works and then fails on the browser API that actually matters.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import runtime as runtime_module
from app.routes import admin, health, turn
from config.settings import get_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-7s %(name)-22s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("crooks")

WEB_DIR = Path(__file__).resolve().parent.parent / "web"


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.runtime = runtime_module.build(settings)
    try:
        await app.state.runtime.provider.start()
    except Exception as exc:  # noqa: BLE001
        # A missing Claude token must not stop the backend booting: /health then names the
        # problem, which is far more useful than a container that will not start.
        log.error("Claude provider did not start: %s", exc)
    log.info("CROOKS Assistant listening on http://%s:%s", settings.host, settings.port)
    yield
    await app.state.runtime.provider.stop()


app = FastAPI(title="CROOKS Assistant", version="0.1.0", lifespan=lifespan)
app.include_router(health.router)
app.include_router(turn.router)
app.include_router(admin.router)

if WEB_DIR.exists():
    app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")

    @app.get("/")
    async def index() -> FileResponse:
        return FileResponse(WEB_DIR / "index.html")
