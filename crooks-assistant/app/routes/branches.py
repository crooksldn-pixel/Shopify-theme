"""The orb, divided.

  POST /branches/fork              {session_id, from}      two-finger pull apart
  POST /branches/{id}/focus        {session_id}            tap the one you want
  POST /branches/{id}/background   {session_id}            drag it aside
  POST /branches/{id}/merge        {session_id}            pinch together
  POST /branches/{id}/cancel       {session_id}            flick it away
  POST /branches/{id}/mark         {session_id, tab, scroll}
  POST /branches/{id}/back         {session_id}
  POST /branches/{id}/forward      {session_id}
  GET  /branches                   ?session_id=            what there is

Two branches at most. What they share is what is safe to share — the read caches, the source
clients, the issued-id ledger, because they are one conversation and one login. What they
never share is a position, a proposal or an approval:

* A branch's pending changes are its own. A merge brings back a structured summary of what
  the other half FOUND; every proposal stays where it was staged, exact, and unapproved.
* A branch working in the background cannot commit anything. The commit route refuses it,
  and this route refuses to background a branch with a change waiting rather than leaving
  a card that a gesture could no longer apply.
* Cancelling one branch cancels its work and nothing else: the other half is untouched.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Form, Request
from fastapi.responses import JSONResponse

from app.observability import timeline
from app.routes.actions import session_matches
from app.session.branch import MAX_BRANCHES, Branch, new_branch_id

log = logging.getLogger("crooks.branches")

router = APIRouter(prefix="/branches", tags=["branches"])


def _refuse(status: int, code: str, detail: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"code": code, "detail": detail})


def _session(request: Request, session_id: str):
    runtime = request.app.state.runtime
    session_id = (session_id or "").strip()
    if not session_id:
        return None, _refuse(400, "wrong_session", "The session is missing.")
    try:
        session = runtime.sessions.get(session_id)
    except KeyError:
        return None, _refuse(409, "no_session", "That conversation has gone; ask again.")
    if not session_matches(session, request):
        return None, _refuse(403, "wrong_session", "That conversation belongs to another login.")
    return session, None


def _live(session) -> list[Branch]:
    return [b for b in session.branches.values() if b.status in ("ACTIVE", "BACKGROUND")]


# Halves that are over are kept only long enough for a card still on the tablet to be settled
# against them, then dropped. Without this a fork/close loop would grow the session for as
# long as it lasted.
KEEP_CLOSED = 2


def _prune(session) -> None:
    closed = [b for b in session.branches.values() if b.status in ("MERGED", "CANCELLED")]
    for branch in sorted(closed, key=lambda b: b.created_at)[: max(0, len(closed) - KEEP_CLOSED)]:
        session.branches.pop(branch.branch_id, None)


def _shape(session) -> dict[str, Any]:
    return {
        "session_id": session.session_id,
        "focused": session.focused_branch,
        "branches": [b.public() for b in _live(session)],
        "can_fork": len(_live(session)) < MAX_BRANCHES,
    }


def _waiting(session, branch_id: str) -> list[str]:
    """Every change staged in this branch that is still waiting for a gesture — INCLUDING the
    undo the Mac offered after a change was proven here, which is a change like any other and
    must not be left committable in a half that is closing."""
    return [
        p.proposal_id for p in session.proposals
        if str(getattr(p, "branch_id", "") or "") == branch_id and p.status.value == "PENDING"
    ]


@router.get("", response_model=None)
async def listing(request: Request, session_id: str = "") -> JSONResponse | dict:
    session, refusal = _session(request, session_id)
    if refusal is not None:
        return refusal
    session.branch()      # the first branch exists from the first question
    return _shape(session)


@router.post("/fork", response_model=None)
async def fork(request: Request, session_id: str = Form(default=""), label: str = Form(default="")) -> JSONResponse | dict:
    """The orb divides. The new half starts where the old one is — same entity, same working
    set, same place in the workflow — and then goes its own way. Nothing is copied that could
    be applied: proposals stay with the branch that staged them."""
    session, refusal = _session(request, session_id)
    if refusal is not None:
        return refusal
    parent = session.branch()
    if len(_live(session)) >= MAX_BRANCHES:
        return _refuse(409, "too_many_branches", f"The orb divides once. Merge or close one of the {MAX_BRANCHES} first.")
    child = Branch(
        branch_id=new_branch_id(), session_id=session.session_id, parent_id=parent.branch_id,
        label=str(label or "").strip()[:40] or "second",
        entity=dict(parent.entity) if parent.entity else None,
        set_id=parent.set_id, tab=parent.tab,
    )
    if parent.workflow is not None:
        # The same set at the same place; advancing one cursor does not move the other.
        from dataclasses import replace

        child.workflow = replace(parent.workflow, workflow_id=f"{parent.workflow.workflow_id}b", visited=list(parent.workflow.visited))
    if parent.entity:
        child.visit(parent.entity["kind"], parent.entity["ref"], parent.entity["label"], tab=parent.tab)
    session.branches[child.branch_id] = child
    timeline.emit("branch_forked", session_id=session.session_id, branch_id=child.branch_id, parent_branch_id=parent.branch_id)
    log.info("branch %s forked from %s", child.branch_id, parent.branch_id)
    return {**_shape(session), "branch_id": child.branch_id}


@router.post("/{branch_id}/focus", response_model=None)
async def focus(request: Request, branch_id: str, session_id: str = Form(default="")) -> JSONResponse | dict:
    session, refusal = _session(request, session_id)
    if refusal is not None:
        return refusal
    if branch_id not in session.branches:
        return _refuse(404, "unknown_branch", "There is no such branch in this conversation.")
    branch = session.branches[branch_id]
    if branch.status == "BACKGROUND":
        branch.status = "ACTIVE"
    session.focus_branch(branch_id)
    timeline.emit("branch_focused", session_id=session.session_id, branch_id=branch_id)
    return _shape(session)


@router.post("/{branch_id}/background", response_model=None)
async def background(request: Request, branch_id: str, session_id: str = Form(default="")) -> JSONResponse | dict:
    """Put a branch to one side. It carries on reading; it can never commit while it is there,
    so a change waiting for a gesture stops it rather than being left unappliable."""
    session, refusal = _session(request, session_id)
    if refusal is not None:
        return refusal
    if branch_id not in session.branches:
        return _refuse(404, "unknown_branch", "There is no such branch in this conversation.")
    waiting = _waiting(session, branch_id)
    if waiting:
        return _refuse(409, "change_waiting", "That half has a change waiting for you. Apply it or let it go first.")
    branch = session.branches[branch_id]
    branch.status = "BACKGROUND"
    if session.focused_branch == branch_id:
        other = next((b.branch_id for b in _live(session) if b.branch_id != branch_id and b.status == "ACTIVE"), "")
        if other:
            session.focused_branch = other
        else:
            branch.status = "ACTIVE"
            return _refuse(409, "last_branch", "That is the only half there is; there is nothing to put it behind.")
    timeline.emit("branch_backgrounded", session_id=session.session_id, branch_id=branch_id)
    return _shape(session)


@router.post("/{branch_id}/merge", response_model=None)
async def merge(request: Request, branch_id: str, session_id: str = Form(default="")) -> JSONResponse | dict:
    """Pinch together. What comes back is a STRUCTURED SUMMARY of what that half found — the
    entities it looked at, the reads it made, the set it holds — never a transcript stitched
    onto another. Its pending changes are not brought over and are not approved: a change
    belongs to the branch it was asked for in, and a merge is not a gesture."""
    session, refusal = _session(request, session_id)
    if refusal is not None:
        return refusal
    if branch_id not in session.branches:
        return _refuse(404, "unknown_branch", "There is no such branch in this conversation.")
    branch = session.branches[branch_id]
    if branch.branch_id == session.focused_branch and len(_live(session)) > 1:
        return _refuse(409, "merge_into_itself", "Tap the half you want to keep first, then pinch.")
    waiting = _waiting(session, branch_id)
    summary = {
        "branch_id": branch.branch_id,
        "label": branch.label,
        "entity": branch.entity,
        "set_id": branch.set_id or None,
        "workflow": branch.workflow.public() if branch.workflow else None,
        "looked_at": list(branch.recent_entities[:6]),
        "read": [{"tool": r["tool"], "summary": r["summary"], "cached": r["cached"]} for r in branch.recent_results[:6]],
        "resolved": [{"said": said, "kind": v["kind"], "label": v["label"]} for said, v in list(branch.resolutions.items())[:6]],
        "actions": list(branch.recent_actions[:4]),
        # Named, not moved: the owner is told what is still waiting over there and where.
        "still_waiting": waiting,
    }
    branch.status = "MERGED"
    _prune(session)
    keeper = session.branch()
    for entity in reversed(branch.recent_entities[:6]):
        keeper.remember_entity(entity["kind"], entity["ref"], entity["label"])
    for said, value in branch.resolutions.items():
        keeper.resolutions.setdefault(said, value)
    timeline.emit("branch_merged", session_id=session.session_id, branch_id=branch_id, into=keeper.branch_id,
                  looked_at=len(summary["looked_at"]), read=len(summary["read"]), still_waiting=len(waiting) or None)
    return {**_shape(session), "merged": summary}


@router.post("/{branch_id}/cancel", response_model=None)
async def cancel(request: Request, branch_id: str, session_id: str = Form(default="")) -> JSONResponse | dict:
    """Flick it away. Its speculative reads are dropped and its pending changes withdrawn —
    and nothing of the other half is touched. That is the whole point of the scoping."""
    runtime = request.app.state.runtime
    session, refusal = _session(request, session_id)
    if refusal is not None:
        return refusal
    if branch_id not in session.branches:
        return _refuse(404, "unknown_branch", "There is no such branch in this conversation.")
    if len(_live(session)) <= 1:
        return _refuse(409, "last_branch", "That is the only half there is.")
    branch = session.branches[branch_id]
    branch.status = "CANCELLED"
    branch.task = None
    from app.memory.prefetch import current as prefetcher

    dropped = prefetcher().cancel_branch(branch_id)
    # The ids first, so the answer can name exactly which cards the tablet must settle.
    revoked = _waiting(session, branch_id)
    runtime.actions.revoke_ids(revoked, "that half was closed")
    if session.focused_branch == branch_id:
        session.focused_branch = next((b.branch_id for b in _live(session)), "")
        if not session.focused_branch:
            session.branch()
    _prune(session)
    timeline.emit("branch_cancelled", session_id=session.session_id, branch_id=branch_id, prefetches=dropped, revoked=len(revoked) or None)
    return {**_shape(session), "revoked": revoked, "prefetches_stopped": dropped}


@router.post("/{branch_id}/mark", response_model=None)
async def mark(request: Request, branch_id: str, session_id: str = Form(default=""), tab: str = Form(default=""), scroll: str = Form(default="")) -> JSONResponse | dict:
    """The screen moved: a tab was chosen, or it was scrolled. Kept against the branch's
    current stop so that going back and coming forward again puts it where it was."""
    session, refusal = _session(request, session_id)
    if refusal is not None:
        return refusal
    if branch_id not in session.branches:
        return _refuse(404, "unknown_branch", "There is no such branch in this conversation.")
    try:
        depth = int(scroll) if scroll not in (None, "") else None
    except (TypeError, ValueError):
        depth = None
    session.branches[branch_id].mark(tab=tab or None, scroll=depth)
    return {"branch": session.branches[branch_id].public()}


@router.post("/{branch_id}/back", response_model=None)
async def back(request: Request, branch_id: str, session_id: str = Form(default="")) -> JSONResponse | dict:
    return await _step(request, branch_id, session_id, forward=False)


@router.post("/{branch_id}/forward", response_model=None)
async def forward(request: Request, branch_id: str, session_id: str = Form(default="")) -> JSONResponse | dict:
    return await _step(request, branch_id, session_id, forward=True)


async def _step(request: Request, branch_id: str, session_id: str, *, forward: bool) -> JSONResponse | dict:
    session, refusal = _session(request, session_id)
    if refusal is not None:
        return refusal
    if branch_id not in session.branches:
        return _refuse(404, "unknown_branch", "There is no such branch in this conversation.")
    branch = session.branches[branch_id]
    entry = branch.forward() if forward else branch.back()
    timeline.emit("branch_navigated", session_id=session.session_id, branch_id=branch_id,
                  nav="forward" if forward else "back", landed=bool(entry), depth=max(0, branch.nav_index))
    return {"branch": branch.public(), "landed": entry.public() if entry is not None else None}
