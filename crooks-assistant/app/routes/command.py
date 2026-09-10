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
from app.routes.actions import session_matches, writes_context

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
    family: str = Form(default=""),
) -> JSONResponse | dict:
    runtime = request.app.state.runtime
    session_id = (session_id or "").strip()
    if not session_id:
        return _refuse(400, "wrong_session", "The session is missing.")
    name = (command or "").strip()
    try:
        session = runtime.sessions.get(session_id)
    except KeyError:
        # A tap on a fresh tablet — the dock from the idle screen — is as legitimate a first
        # request as a sentence is, and /turn creates the conversation for a sentence. A
        # command about a record the tablet claims to have, though, has nothing to be about
        # when the conversation is gone: those still say so.
        if name not in FRESH_START:
            return _refuse(409, "no_session", "That conversation has gone; ask again.")
        session = runtime.sessions.get_or_create(session_id)
    if not session_matches(session, request):
        # A conversation is its first caller's, on this route as on every other.
        return _refuse(403, "wrong_session", "That conversation belongs to another login.")

    spec = commands.get(name)
    if spec is None:
        return _refuse(400, "unknown_command", f"There is no command called {name!r}.")
    if not spec.touch:
        return _refuse(400, "not_tappable", f"{name!r} is not something the tablet can post.")

    branch = session.branch(branch_id) if branch_id else session.branch()
    # A tap is addressed to a half too, and anything it causes downstream — a read that opens
    # a working set, a proposal — must be filed against that half rather than the focused one.
    session.acting_branch = branch.branch_id
    started = time.perf_counter()
    outcome = commands.run(name, commands.Ctx(runtime, session, branch, await _arguments(request, {
        "kind": (kind or "").strip()[:40],
        "ref": (ref or "").strip()[:MAX_REF_CHARS],
        "label": (label or "").strip()[:120],
        "tab": (tab or "").strip()[:40],
        "surface": (surface or "").strip()[:40],
        "family": (family or "").strip()[:40],
    })))
    recipe_id = outcome.changed.get("recipe") if outcome.ok and isinstance(outcome.changed, dict) else None
    if recipe_id:
        # A command that names a place rather than a record — a dock landing. Commands are
        # synchronous and read nothing themselves; the recipe reads, through the same
        # scheduler and the same read tools a sentence would use, and no model.
        outcome = await _run_recipe(runtime, session, branch, str(recipe_id), outcome)
    wanted = outcome.changed.get("stage") if outcome.ok and isinstance(outcome.changed, dict) else None
    if isinstance(wanted, dict):
        # A command that PREPARES a change: Save draft or Send on the composer
        # (app/families/compose.py). Same reason as the recipe above — a command is
        # synchronous and preparing a change is a fresh read — and the same shape: the
        # command named a registered write tool and the arguments THE MAC built from its own
        # context, and this stages them. The gesture is still to come.
        outcome = await _stage_change(request, runtime, session, branch, wanted, outcome)
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

    calls = list(outcome.calls)
    needs = outcome.changed.get("needs_read") if isinstance(outcome.changed, dict) else None
    if isinstance(needs, dict) and not calls:
        # The cursor landed on a record the Mac does not hold. Memory makes Back and Next
        # instant when it can; when it cannot, the record is read here rather than the tap
        # doing nothing. A button that moves a cursor and draws nothing is the worst of both.
        calls = await _read_member(runtime, session, needs)
        outcome.changed["read"] = bool(calls)
    ui = present(calls, session=session, writes=await _writes(request))
    if outcome.surfaces:
        ui = [s.as_ui() if hasattr(s, "as_ui") else s for s in outcome.surfaces] + ui
    if any(item.get("type") != "context_stack" for item in ui):
        # What this half now shows, kept on the Mac: a tap that drew cards is as much this
        # half's workspace as a sentence that did, and `branch.show` redraws it after a
        # switch or a reload (app/session/branch.py).
        branch.shown(ui, outcome.answer, "")
    return {
        "ok": True,
        "command": name,
        "answer": outcome.answer,
        "ui": ui,
        "changed": outcome.changed,
        "branch": branch.public(),
        "session_id": session.session_id,
        "ms": round(elapsed, 1),
        # `ms` above is how long the COMMAND took to resolve, measured before the read a
        # cursor move can cause and before the card is built — which is the number the
        # timeline wants. `served_ms` is the whole request, which is what the owner waited
        # and what a benchmark should print. They are the same for a replay and differ by
        # a Shopify round trip when memory had dropped the record.
        "served_ms": round((time.perf_counter() - started) * 1000, 1),
        # Named so the timeline and the report can tell a tap from a sentence without guessing.
        "lane": "TOUCH",
        "model_calls": 0,
    }


# Commands a tablet may post before the conversation exists on the Mac.
FRESH_START = frozenset({"open.area"})

# Bounds on what a tap may carry. A command's arguments are identities and small values —
# an id, a field name, an address typed into a precision field, a quantity — never an
# execution argument (those the Mac builds); the bound keeps a runaway client from posting
# a document.
MAX_ARGS = 24
MAX_ARG_CHARS = 8000
RESERVED = frozenset({"session_id", "command", "branch_id"})


async def _arguments(request: Request, named: dict[str, str]) -> dict[str, str]:
    """Every field the tablet posted, the named ones already bounded, the rest bounded here.
    A family's command takes its own arguments (`area`, `compose_id`, `quantity` …) without
    this route having to know each one; the command decides what they mean."""
    try:
        form = await request.form()
    except Exception:  # noqa: BLE001 — not a form body: only the named fields
        return dict(named)
    args = dict(named)
    for key, value in list(form.multi_items())[:MAX_ARGS + len(RESERVED) + len(named)]:
        if key in RESERVED or key in args or not isinstance(value, str):
            continue
        if len(args) >= MAX_ARGS + len(named):
            break
        args[str(key)[:40]] = value[:MAX_ARG_CHARS]
    return args


async def _run_recipe(runtime, session, branch, recipe_id: str, outcome):
    """A FAST recipe, run for a tap. The same runner the fast lane uses (app/fastpath), the
    same read-only assertion, the same timeline event; the intent is the recipe's own family
    at full confidence, because a tap on Orders is not ambiguous."""
    from app import commands as command_mod
    from app.fastpath import RECIPES
    from app.fastpath import run as run_recipe
    from app.fastpath.intent import Intent, signals_for
    from app.fastpath.models import Ctx as RecipeCtx
    from app.memory import current as memory

    recipe = RECIPES.get(recipe_id)
    if recipe is None:
        return command_mod.Outcome.refused("unknown_recipe", f"There is no recipe called {recipe_id!r}.")
    intent = Intent(family=recipe.intent_family, confidence=1.0, signals=signals_for("", branch=branch), reason="a tap")
    branch.working("opening " + str(outcome.changed.get("area") or recipe.ui))
    try:
        answer = await run_recipe(recipe, RecipeCtx(runtime=runtime, session=session, branch=branch, intent=intent, text="", memory=memory()))
    finally:
        branch.idle()
    if answer.deferred:
        return command_mod.Outcome.refused("landing_unavailable", f"That could not be drawn just now ({answer.defer}).")
    calls = list(answer.calls if answer.drawn is None else answer.drawn)
    changed = {**outcome.changed, "lane": "FAST", "recipe_id": recipe_id, "partial": bool(answer.partial),
               "reads": list((answer.trace or {}).get("reads") or []), "ms": (answer.trace or {}).get("ms")}
    return command_mod.Outcome(answer=answer.answer, calls=calls, surfaces=list(answer.surfaces), changed=changed)


async def _stage_change(request: Request, runtime, session, branch, wanted: dict, outcome):
    """Stage what a command prepared, exactly as `POST /actions/row` stages what a row button
    prepared (app/routes/actions.py).

    Every check that route makes is made here, in the same order and by the same functions,
    because a tap that prepares a change on this route is the same event as a tap that
    prepares one on that route:

      * `caller_check` — this login may apply changes at all. /command does not run it for a
        read, and staging is not a read: without this, a tablet the Mac refuses at the commit
        could still fill the screen with cards it will never be allowed to apply. Its own
        words are used, so the refusal says which of the three reasons it was.
      * `_write_status_soon` — the store has granted what this change needs.
      * `dispatch` — the gate, then the write tool's own prepare step, which re-reads and
        builds the execution arguments itself. Nothing the tablet posted reaches Gmail.
      * `deliver` — the TTL starts when the card leaves for the tablet, not when it was made.

    `revoke` is applied AFTER a successful stage and never before: it is the card this one
    replaces (a draft turned into a send), and withdrawing it first would leave the owner
    with nothing to tap if the send could not be prepared.
    """
    from app import commands as command_mod
    from app.routes.actions import _write_status_soon, caller_check
    from app.tools.dispatch import dispatch

    tool_name = str(wanted.get("tool") or "")
    args = wanted.get("args")
    if not tool_name or not isinstance(args, dict):
        return command_mod.Outcome.refused("not_prepared", "That change could not be prepared.")
    _caller, code, detail, _spoken = caller_check(request)
    if code:
        log.warning("a command that prepares a change was refused: %s — %s (path=%s)", code, detail, request.url.path)
        return command_mod.Outcome.refused(code, detail)
    status = await _write_status_soon(runtime, tool_name)
    if not status.ready:
        return command_mod.Outcome.refused(status.code, status.detail)
    calls: list = []
    await dispatch(tool_name, dict(args), session=session, timeout_s=runtime.settings.tool_timeout_s, calls=calls)
    proposal_id = next((c.proposal_id for c in calls if getattr(c, "proposal_id", None)), "")
    if not proposal_id:
        detail = next((str(c.error) for c in calls if not c.ok and c.error), "That change could not be prepared.")
        timeline.emit("command_stage", session_id=session.session_id, branch_id=branch.branch_id,
                      tool=tool_name, ok=False, detail=detail[:200])
        return command_mod.Outcome.refused("not_prepared", detail[:200])
    runtime.actions.deliver(proposal_id)
    withdrawn = runtime.actions.revoke_ids([str(x) for x in (wanted.get("revoke") or [])], "replaced by " + tool_name)
    timeline.emit("command_stage", session_id=session.session_id, branch_id=branch.branch_id,
                  tool=tool_name, ok=True, proposal_id=proposal_id, revoked=withdrawn or None)
    return command_mod.Outcome(
        answer="", calls=calls,
        changed={**outcome.changed, "stage": None, "staged": True, "proposal_id": proposal_id,
                 "revoked": withdrawn, "what": str(wanted.get("what") or "")[:80]},
    )


async def _read_member(runtime, session, needs: dict) -> list:
    """Read one record, through the same scheduler and the same tools a recipe would use.

    Not a shortcut around the gate: `run_plan` refuses a plan naming anything but a read, and
    the tools are the registered ones. A tap can therefore cause a read and can never cause
    anything else.
    """
    from app.commands import MEMBER_READ
    from app.reads.scheduler import Read, ReadPlan, run_plan

    tool, argument, _kind = MEMBER_READ.get(str(needs.get("set_kind") or ""), ("", "", ""))
    ref = str(needs.get("ref") or "")
    if not tool or not ref:
        return []
    plan = ReadPlan([Read("member", tool, {argument: ref},
                          source="gmail" if tool.startswith("gmail_") else "shopify")],
                    label="command:member")
    try:
        result = await run_plan(plan, session=session, timeout_s=6.0,
                                turn_id=getattr(session, "turn_id", ""))
    except Exception as exc:  # noqa: BLE001 — a tap that cannot read says so; it never fails the app
        log.info("a command could not read %s: %s", tool, exc)
        return []
    _remember(needs, ref, result)
    return list(result.calls)


def _remember(needs: dict, ref: str, result) -> None:
    """Put what the tap just read where a replay will look for it.

    `run_plan` reads; only the fast lane's `_keep` was writing to the tiers. So a record
    reached by tapping Next was gone a second later: Back onto it missed `replay()` and read
    Shopify again, and `open.entity` refused a record the owner had been looking at moments
    before with "I no longer have that one to hand". `commands.replay`'s premise — the read
    happened when the record was opened, so going back to it is not a new question — held only
    for records opened by voice.
    """
    from app.commands import MEMBER_READ
    from app.memory import ENTITY
    from app.memory import current as memory

    _, _, kind = MEMBER_READ.get(str(needs.get("set_kind") or ""), ("", "", ""))
    body = result.values.get("member") if hasattr(result, "values") else None
    if not kind or not isinstance(body, dict):
        return
    try:
        memory().put(ENTITY, f"{kind}:{ref}", body, source="gmail" if kind == "email_thread" else "shopify",
                     query="command:member", provenance={"command": "member", "ref": ref})
    except Exception as exc:  # noqa: BLE001 — a cold cache is a slower Back, not a fault
        log.debug("could not keep what a tap read: %s", exc)


async def _writes(request: Request) -> dict:
    """What the action rail on a replayed card may offer THIS caller.

    `writes_context` is the same function /turn uses, and using it is the whole point: a card
    redrawn by a tap must offer exactly what the same card offered when it was read, no more.

    This used to build its own dict — `{"enabled": ..., "capabilities": await
    runtime.capabilities()}` — which was wrong twice. Every consumer in app/presentation.py
    reads `writes["allowed"]`, which was absent, so the rail fell back to None. And
    `runtime.capabilities()` is the MAC's table, not this caller's: `writes_context` runs
    `caller_check` first and returns no capabilities at all when the caller may not apply
    changes — no allow-list, a request from the Mac itself with CROOKS_WRITES_LOCAL_OWNER
    false, or an identity Tailscale cannot verify. /command ran none of that, so a tapped card
    carried live chips that /turn deliberately suppresses on the same order, with no code or
    reason on it to say why a tap would fail.
    """
    try:
        return await writes_context(request)
    except Exception as exc:  # noqa: BLE001 — a rail is not worth failing a navigation for
        log.info("could not read the capability table for a command: %s", exc)
        return {}
