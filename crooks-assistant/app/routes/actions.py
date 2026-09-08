"""POST /actions/{proposal_id}/commit — the owner tapped.

The only route from the tablet to a mutation, and it carries no arguments: a proposal id and
the session it belongs to. Everything else — what to send, to which order, checked against
what — was decided on the Mac when the proposal was staged. Claude is not in this loop.

Refusals are controlled codes the tablet turns into calm states. Nothing here leaks a GraphQL
document, a token, a variable, or a stack trace.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Form, Request
from fastapi.responses import JSONResponse

from app.presentation import present_action, present_proposal_state
from app.speech.speakable import to_speakable

log = logging.getLogger("crooks.actions")

router = APIRouter(prefix="/actions")


def _refuse(status: int, code: str, detail: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"code": code, "detail": detail})


def _authorise(request: Request) -> tuple[str, JSONResponse | None]:
    """Who is tapping, and whether they may. The write boundary, independent of the general
    middleware: writes need the allow-list to exist, the caller to be on it, and a request made
    on the Mac itself to be deliberately permitted."""
    runtime = request.app.state.runtime
    settings = runtime.settings
    if not settings.writes_enabled:
        return "", _refuse(403, "writes_disabled", "Writes are switched off on the Mac (CROOKS_WRITES_ENABLED).")
    allowed = runtime.allowed_logins
    if not allowed:
        return "", _refuse(403, "allow_list_missing", "No allowed Tailscale logins are configured (CROOKS_ALLOWED_LOGINS).")
    login = request.headers.get("tailscale-user-login", "").strip()
    proxied = bool(request.headers.get("x-forwarded-for"))
    if proxied or login:
        if login.lower() in allowed:
            return login.lower(), None
        return "", _refuse(403, "not_authorised", "This login may not apply changes.")
    # No login and not proxied: a request made on the Mac itself.
    if settings.writes_local_owner:
        return "local", None
    return "", _refuse(403, "not_authorised", "Requests made on the Mac itself may not apply changes (CROOKS_WRITES_LOCAL_OWNER).")


@router.post("/{proposal_id}/commit", response_model=None)
async def commit(request: Request, proposal_id: str, session_id: str = Form(default="")) -> JSONResponse | dict:
    runtime = request.app.state.runtime
    caller, refusal = _authorise(request)
    if refusal is not None:
        return refusal
    status = await runtime.write_status()
    if not status.ready:
        return _refuse(403, status.code, status.detail)
    if not session_id.strip():
        return _refuse(400, "wrong_session", "The session is missing.")

    from app.tools import registry

    def spec_lookup(name: str):
        try:
            return registry.get(name)
        except KeyError:
            return None

    result = await runtime.actions.commit(proposal_id, session_id.strip(), caller=caller, spec_lookup=spec_lookup)
    if result.proposal is None:
        return _refuse(404 if result.code == "unknown" else 403, result.code, "No such proposal for this session.")

    proposal = result.proposal
    log.info("action %s %s → %s (%s)", proposal.proposal_id, proposal.operation, proposal.status.value, result.code)
    if result.spoken:
        # A fixed line, synthesised once and kept: the tablet asks /speak for it next.
        runtime.voice.prefetch(to_speakable(result.spoken, max_chars=runtime.voice.max_chars), pin=True)
    try:
        session = runtime.sessions.peek(session_id.strip())
    except KeyError:
        session = None
    undo = None
    if proposal.undo_id and session is not None:
        undo_proposal = session.proposal(proposal.undo_id)
        if undo_proposal is not None:
            undo = undo_proposal.public()
    return {
        **proposal.public(),
        "code": result.code,
        "spoken": result.spoken,
        "ui": present_action(result, session=session),
        "undo": undo,
    }


@router.get("/{proposal_id}", response_model=None)
async def state(request: Request, proposal_id: str, session_id: str = "") -> JSONResponse | dict:
    """Where a proposal stands, for a tablet that lost the connection mid-tap: it asks what
    happened rather than sending the tap again. Public fields only."""
    runtime = request.app.state.runtime
    proposal = runtime.actions.state(proposal_id, session_id.strip())
    if proposal is None:
        return _refuse(404, "unknown", "No such proposal for this session.")
    try:
        session = runtime.sessions.peek(session_id.strip())
    except KeyError:
        session = None
    return {**proposal.public(), "ui": present_proposal_state(proposal, session=session)}
