"""POST /command — a tap, in the same words a sentence would have used.

The tablet posts which command it was and which record it was on. It does not post what the
command should do, and it cannot: the body is a name from a fixed registry plus a reference,
and the Mac decides the rest. That is the same rule the write boundary keeps — the tablet
carries identity, never arguments — applied to the read side, where it costs nothing and
removes a class of bug that starts with the client and the server disagreeing about what a
button means.

The response is the shape `/turn` returns: an answer, a `ui` list, the branch state. So the
tablet renders a tap and a spoken instruction with the same code, and so does everything
downstream of it — the timeline, the report, the experience harness.

Nothing here can change the shop or the inbox. Every command in the registry is a read or a
move; a change is a proposal and goes to `/actions`, which has the staging, the gesture, the
freshness reread and the verification that a change needs and a tap on a tab does not.
"""

from __future__ import annotations

import logging
import time

from fastapi import APIRouter, Form, Request
from fastapi.responses import JSONResponse

from app import commands
from app.observability import timeline
from app.presentation import present
from app.routes.actions import session_matches

router = APIRouter(tags=["command"])
log = logging.getLogger("crooks.command")

MAX_REF_CHARS = 200


def _refuse(status: int, code: str, detail: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"code": code, "detail": detail})


@router.get("/commands", response_model=None)
async def listing() -> dict:
    """What the tablet may post, and which end of the system may reach each one.

    Derived from the registry, so the tablet cannot offer a control the Mac does not implement
    and the feature matrix cannot claim a command that does not exist.
    """
    return {"commands": commands.public()}


@router.post("/command", response_model=None)
async def command(
    request: Request,
    session_id: str = Form(default=""),
    command: str = Form(default=""),      # noqa: A002 — the field name the tablet posts
    branch_id: str = Form(default=""),
    kind: str = Form(default=""),
    ref: str = Form(default=""),
    label: str = Form(default=""),
    tab: str = Form(default=""),
    surface: str = Form(default=""),
) -> JSONResponse | dict:
    runtime = request.app.state.runtime
    session_id = (session_id or "").strip()
    if not session_id:
        return _refuse(400, "wrong_session", "The session is missing.")
    try:
        session = runtime.sessions.get(session_id)
    except KeyError:
        return _refuse(409, "no_session", "That conversation has gone; ask again.")
    if not session_matches(session, request):
        # A conversation is its first caller's, on this route as on every other.
        return _refuse(403, "wrong_session", "That conversation belongs to another login.")

    name = (command or "").strip()
    spec = commands.get(name)
    if spec is None:
        return _refuse(400, "unknown_command", f"There is no command called {name!r}.")
    if not spec.touch:
        return _refuse(400, "not_tappable", f"{name!r} is not something the tablet can post.")

    branch = session.branch(branch_id) if branch_id else session.branch()
    started = time.perf_counter()
    outcome = commands.run(name, commands.Ctx(runtime, session, branch, {
        "kind": (kind or "").strip()[:40],
        "ref": (ref or "").strip()[:MAX_REF_CHARS],
        "label": (label or "").strip()[:120],
        "tab": (tab or "").strip()[:40],
        "surface": (surface or "").strip()[:40],
    }))
    elapsed = (time.perf_counter() - started) * 1000

    timeline.emit(
        "command", session_id=session.session_id, branch_id=branch.branch_id, command=name,
        ok=outcome.ok, code=outcome.code or None, ms=round(elapsed, 1),
        # The reference, never the record: a timeline is a record of what happened, not of
        # whose address was on the screen.
        entity=(outcome.changed.get("entity") or {}).get("kind") if isinstance(outcome.changed.get("entity"), dict) else None,
        replayed=bool(outcome.changed.get("replayed")),
    )
    if not outcome.ok:
        # A refusal is not an error: the owner tapped something that no longer applies. It
        # comes back 200 with the reason so the tablet can say so without a failure state.
        return {
            "ok": False, "code": outcome.code, "detail": outcome.detail, "answer": outcome.answer,
            "ui": [], "command": name, "branch": branch.public(), "session_id": session.session_id,
            "ms": round(elapsed, 1), "lane": "TOUCH",
        }

    ui = present(outcome.calls, session=session, writes=await _writes(runtime))
    if outcome.surfaces:
        ui = [s.as_ui() if hasattr(s, "as_ui") else s for s in outcome.surfaces] + ui
    return {
        "ok": True,
        "command": name,
        "answer": outcome.answer,
        "ui": ui,
        "changed": outcome.changed,
        "branch": branch.public(),
        "session_id": session.session_id,
        "ms": round(elapsed, 1),
        # Named so the timeline and the report can tell a tap from a sentence without guessing.
        "lane": "TOUCH",
        "model_calls": 0,
    }


async def _writes(runtime) -> dict:
    """What the action rail on a replayed card may offer.

    The same table `/health` builds, so a card redrawn by a tap offers exactly the actions it
    offered when it was first read — and offers none at all when changes are switched off.
    """
    try:
        return {"enabled": bool(runtime.settings.writes_enabled),
                "capabilities": await runtime.capabilities()}
    except Exception as exc:  # noqa: BLE001 — a rail is not worth failing a navigation for
        log.info("could not read the capability table for a command: %s", exc)
        return {}
