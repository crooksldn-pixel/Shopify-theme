"""GET /context/order/{order_id} — the rest of an order card, once the card is up.

The turn answers with the order and whatever of its history and inbox arrived within the
budget; the tablet collects the remainder here. Session-bound and id-bound: only an order
this session has already been shown can be asked about, so the route cannot be used to read
a stranger's order. No model is in the loop; the shape is the card's own.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.presentation import present_extension
from app.tools.registry import ToolError

log = logging.getLogger("crooks.context")

router = APIRouter(prefix="/context")

# How long the route waits for an enrichment still in flight before answering with what it
# has. The tablet asks again for anything still pending.
EXTENSION_WAIT_S = 4.0


@router.get("/order/{order_id:path}", response_model=None)
async def order_extension(request: Request, order_id: str, session_id: str = "") -> JSONResponse | dict:
    runtime = request.app.state.runtime
    try:
        session = runtime.sessions.peek(session_id.strip())
    except KeyError:
        return JSONResponse(status_code=404, content={"code": "unknown", "detail": "No such session."})
    if order_id not in session.issued_ids:
        # Not an order this conversation was shown: the same rule the detail tool keeps.
        return JSONResponse(status_code=404, content={"code": "unknown", "detail": "No such order for this session."})
    from app.tools.dispatch import harvest_ids
    from app.tools.shopify_tools import hydrator

    try:
        ext = await hydrator().extension(order_id, wait_s=EXTENSION_WAIT_S)
    except ToolError as exc:
        return JSONResponse(status_code=404, content={"code": "unknown", "detail": str(exc)[:160]})
    except Exception as exc:  # noqa: BLE001 — Shopify or Gmail failing is "not yet", not a crash
        log.warning("context extension for %s failed: %s", order_id, type(exc).__name__)
        return JSONResponse(status_code=503, content={"code": "service_unavailable", "detail": "The order's history could not be read."})
    # The ids in it (recent orders, threads) are issued to the session like any tool result's.
    harvest_ids(ext, session)
    return present_extension(ext)
