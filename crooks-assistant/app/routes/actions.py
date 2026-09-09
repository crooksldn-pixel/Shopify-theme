"""POST /actions/{proposal_id}/commit — the owner tapped.

The only route from the tablet to a mutation, and it carries no arguments: a proposal id and
the session it belongs to. Everything else — what to send, to which order, checked against
what — was decided on the Mac when the proposal was staged. Claude is not in this loop.

Refusals are controlled codes the tablet turns into calm states. Nothing here leaks a GraphQL
document, a token, a variable, or a stack trace.
"""

from __future__ import annotations

import asyncio
import logging
import time

from fastapi import APIRouter, Form, Request
from fastapi.responses import JSONResponse

from app.presentation import present_action, present_proposal_state
from app.speech.speakable import to_speakable

log = logging.getLogger("crooks.actions")

router = APIRouter(prefix="/actions")


# What the tablet says, out loud, when a change cannot be applied from where it is. Fixed
# lines: nothing from the request and nothing from Shopify reaches the voice.
SPOKEN_REFUSALS = {
    "writes_disabled": "Changes are switched off on the Mac, so I can't apply that.",
    "allow_list_missing": "Nobody is allowed to apply changes yet: the allowed logins aren't set on the Mac.",
    "not_authorised": "This tablet isn't allowed to apply changes.",
    "not_authorised_local": "Requests from the Mac itself aren't allowed to apply changes.",
    "scope_missing": "Shopify hasn't given the app permission to write orders yet.",
}


def _refuse(status: int, code: str, detail: str, spoken_key: str | None = None) -> JSONResponse:
    content = {"code": code, "detail": detail, "spoken": SPOKEN_REFUSALS.get(spoken_key or code, "")}
    return JSONResponse(status_code=status, content=content)


def caller_check(request: Request) -> tuple[str, str, str, str]:
    """Who is asking, and whether they may apply a change: (caller, code, detail, spoken_key).
    The code is empty when they may. The write boundary, independent of the general
    middleware: writes need the allow-list to exist, the caller to be on it, and a request made
    on the Mac itself to be deliberately permitted. Used by the commit route to refuse, and by
    /turn to tell the tablet — before anyone taps — whether a tap could work from here."""
    runtime = request.app.state.runtime
    settings = runtime.settings
    if not settings.writes_enabled:
        return "", "writes_disabled", "Writes are switched off on the Mac (CROOKS_WRITES_ENABLED).", "writes_disabled"
    allowed = runtime.allowed_logins
    if not allowed:
        return "", "allow_list_missing", "No allowed Tailscale logins are configured (CROOKS_ALLOWED_LOGINS).", "allow_list_missing"
    login = request.headers.get("tailscale-user-login", "").strip()
    # Only `tailscale serve` stamps an identity, and it stamps X-Forwarded-For on everything
    # it proxies. A login header without it is a claim made by something on the Mac itself,
    # and is worth nothing: that request is judged as what it is, a local one.
    proxied = bool(request.headers.get("x-forwarded-for"))
    if proxied:
        if login and login.lower() in allowed:
            return login.lower(), "", "", ""
        return "", "not_authorised", "This login may not apply changes.", "not_authorised"
    # Not proxied: a request made on the Mac itself, whatever headers it carries.
    if settings.writes_local_owner:
        return "local", "", "", ""
    return "", "not_authorised_local", "Requests made on the Mac itself may not apply changes (CROOKS_WRITES_LOCAL_OWNER).", "not_authorised_local"


def caller_identity(request: Request) -> str:
    """Who is asking, for binding a conversation to them: the proxied login, or "local" for
    a request made on the Mac itself. The middleware has already refused a proxied request
    with no login, so this is never empty."""
    login = request.headers.get("tailscale-user-login", "").strip().lower()
    proxied = bool(request.headers.get("x-forwarded-for"))
    return login if proxied and login else "local"


def session_matches(session, request: Request) -> bool:
    """Whether this request may use this session. A session binds to the tailnet login that
    first used it; every later proxied request must carry the same one. A request made on
    the Mac itself is the owner at the keyboard — it may look at any conversation (and is
    still held to CROOKS_WRITES_LOCAL_OWNER before it can apply anything) and binds none."""
    identity = caller_identity(request)
    if identity == "local":
        return True
    if not session.login:
        session.login = identity
        return True
    return session.login == identity


def _authorise(request: Request) -> tuple[str, JSONResponse | None]:
    caller, code, detail, spoken_key = caller_check(request)
    if code:
        # Findable in one grep: the next "it said not allowed" is answered from this line.
        log.warning(
            "commit refused: %s — %s (login=%s proxied=%s path=%s)",
            code, detail, request.headers.get("tailscale-user-login", "") or "-",
            bool(request.headers.get("x-forwarded-for")), request.url.path,
        )
        return "", _refuse(403, code, detail, spoken_key)
    return caller, None


# The tablet is told whether a tap could work while the owner waits for the answer's voice.
# A Shopify scope check that is slow must not become the answer's latency: past this, the
# card is shown as it would be if the scopes were fine, and the tap itself decides.
WRITE_STATUS_TIMEOUT_S = 1.5


# When the preflight has just timed out, this is how long before it is tried again. Without
# it a Shopify that hangs costs the bound on the answer AND again on the tap.
PREFLIGHT_QUIET_S = 30.0
_preflight_timed_out_at = 0.0
_SLOW = "ready, unverified — the Shopify scope check was slow"


async def _write_status_soon(runtime, operation: str | None = None):
    """The preflight, bounded. It runs before the answer's voice and before a tap; neither may
    wait on a slow Shopify. Past the bound the change is treated as applicable — Shopify has
    the last word on the mutation itself, and refuses it there if the scope is really missing."""
    global _preflight_timed_out_at
    from app.runtime import WriteStatus

    if time.time() - _preflight_timed_out_at < PREFLIGHT_QUIET_S:
        return WriteStatus("unknown", _SLOW)
    try:
        return await asyncio.wait_for(runtime.write_status(operation), timeout=WRITE_STATUS_TIMEOUT_S)
    except TimeoutError:
        _preflight_timed_out_at = time.time()
        log.warning("the write preflight took longer than %.1fs; treated as ready", WRITE_STATUS_TIMEOUT_S)
        return WriteStatus("unknown", _SLOW)


def _unknown_capabilities(runtime) -> dict:
    return {op: {"state": "unknown", "detail": _SLOW, "scope": scope} for op, scope in runtime._write_scopes().items()}


async def _preflight_soon(runtime, operation: str | None = None):
    """The status and the per-change table together, under ONE bound: the two read the same
    cached scope answer, and a Shopify that hangs costs the turn the bound once, not twice.
    Past it every built change is "unknown": offered, with Shopify deciding the tap."""
    global _preflight_timed_out_at
    from app.runtime import WriteStatus

    if time.time() - _preflight_timed_out_at < PREFLIGHT_QUIET_S:
        return WriteStatus("unknown", _SLOW), _unknown_capabilities(runtime)
    try:
        status, capabilities = await asyncio.wait_for(
            asyncio.gather(runtime.write_status(operation), runtime.capabilities()), timeout=WRITE_STATUS_TIMEOUT_S,
        )
    except TimeoutError:
        _preflight_timed_out_at = time.time()
        log.warning("the write preflight took longer than %.1fs; treated as ready", WRITE_STATUS_TIMEOUT_S)
        return WriteStatus("unknown", _SLOW), _unknown_capabilities(runtime)
    return status, capabilities


async def writes_context(request: Request, operation: str | None = None) -> dict:
    """What the tablet needs to know about applying changes from this request's identity:
    whether writes are ready on the Mac, whether this caller may tap, and which changes the
    Mac could make right now (for the order card's rail). Sent with every turn that proposes
    something, so the card can say up front when a tap would be refused."""
    runtime = request.app.state.runtime
    caller, code, detail, spoken_key = caller_check(request)
    status, capabilities = await _preflight_soon(runtime, operation)
    if not code and not status.ready:
        code, detail, spoken_key = status.code, status.detail, status.code
    if code:
        # The turn-time refusal, in the log as plainly as a refused tap: the owner hears one
        # sentence, and this line says which and why. The card names the local case as the
        # Mac's own doing, never as the tablet's login.
        log.warning(
            "change proposed but a tap would be refused: %s — %s (login=%s proxied=%s writes=%s)",
            spoken_key or code, detail, request.headers.get("tailscale-user-login", "") or "-",
            bool(request.headers.get("x-forwarded-for")), status.state,
        )
    return {
        "state": status.state,
        "allowed": not code,
        "code": (spoken_key or code) if code else "",
        "detail": detail,
        "spoken": SPOKEN_REFUSALS.get(spoken_key, "") if code else "",
        "caller": caller or None,
        # The rail's source: which changes this Mac could make now, by operation. Empty when
        # the caller may not tap at all, so no chip is offered to a login that cannot use it.
        "capabilities": capabilities if not code or code == status.code else {},
    }


@router.post("/{proposal_id}/commit", response_model=None)
async def commit(request: Request, proposal_id: str, session_id: str = Form(default="")) -> JSONResponse | dict:
    runtime = request.app.state.runtime
    caller, refusal = _authorise(request)
    if refusal is not None:
        return refusal
    if not session_id.strip():
        return _refuse(400, "wrong_session", "The session is missing.")
    try:
        owner_session = runtime.sessions.peek(session_id.strip())
    except KeyError:
        owner_session = None
    if owner_session is not None and not session_matches(owner_session, request):
        log.warning("commit refused: wrong_session — another login's conversation (caller=%s)", caller)
        return _refuse(403, "wrong_session", "That conversation belongs to another login.")
    # The preflight is for THIS change's scope: a fulfilment scope the store has not granted
    # does not stop a note. The proposal is looked at, not claimed; the engine claims it.
    pending = runtime.actions.state(proposal_id, session_id.strip())
    status = await _write_status_soon(runtime, pending.operation if pending is not None else None)
    if not status.ready:
        log.warning("commit refused: %s — %s (caller=%s)", status.code, status.detail, caller)
        return _refuse(403, status.code, status.detail, status.code)

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
        # Pinned only when fixed: a success line names the order and is not worth a slot.
        runtime.voice.prefetch(to_speakable(result.spoken, max_chars=runtime.voice.max_chars), pin=result.code != "verified")
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
        "ui": present_action(result, session=session, writes=await writes_context(request, proposal.operation)),
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
    if session is not None and not session_matches(session, request):
        return _refuse(403, "wrong_session", "That conversation belongs to another login.")
    # The same preflight the commit route runs: a card recovered after a lost connection is
    # only shown as tappable when a tap from this request could actually work.
    writes = await writes_context(request, proposal.operation)
    return {**proposal.public(), "ui": present_proposal_state(proposal, session=session, writes=writes)}
