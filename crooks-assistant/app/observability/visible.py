"""The other outcome: what the owner could see (§17).

The report of the live hour said **11 of 14 turns successful**. During that hour the owner
said out loud that the split was broken, that the applying button was broken, and that Back,
Back-to-assistant and Next had regressed. A report can be internally consistent and still be
wrong about the only thing that matters.

The gap has one cause. **The analyser scored the backend and the owner lives in the UI.** A
send that Gmail confirmed is VERIFIED whatever the glass says, and the glass said "Applying…"
for the rest of the session. So every turn now carries two outcomes and their disagreement is
itself the defect:

    gmail_send_reply:  backend = VERIFIED   visible = APPLYING_STUCK   experience = FAILED

This module is the second reading. It processes what the tablet already writes down and the
old classifier never looked at — the reconciles, the branch moves, the renders and their
surface states, the navigation commands, the refusals, the scroll depths, the multitouches,
the prediction and anticipation records, and the owner's own feedback — and files fifteen
classes that describe the SCREEN rather than the server.

Every rule is a count or a match over ids, and each one names the evidence it read. Nothing
here is scored by a model, nothing here executes anything, and nothing here can authorise a
write: it is a function from a timeline to a list of findings.

The rules, and the evidence each needs:

    ACTION_UI_STUCK            the Mac settled a surface and the tablet submitted it again at
                               the next reconcile. `tablet_reconcile.kept` is the tablet's own
                               count of surfaces it was told were finished; two consecutive
                               reconciles that keep something mean the settle did not stick.
    SPLIT_NO_REDRAW            a half was forked and a focus change drew nothing.
    SPLIT_DUPLICATE_SURFACE    two halves whose cards are the same cards.
    WRONG_BRANCH_SURFACE       a control acted on a half that was not the focused one.
    DUPLICATE_RENDER           the same cards drawn twice inside seconds.
    PROGRESSIVE_RENDER_MISSING nothing at all on screen until everything was ready.
    NAV_SEMANTIC_MISMATCH      accepted navigation that took the owner nowhere: a burst of
                               Home and Back inside half a minute, every one ok, or a Home
                               that replayed the last record instead of reaching a landing.
    DEAD_CONTROL               a control accepted and nothing redrawn.
    FAKE_CONTROL               a control offered with nothing behind it: refused not_held,
                               landing_unavailable, dead_chip, or tapped while disabled.
    STALE_PENDING_ACTION       a change left PENDING for the rest of the session, and the
                               "changes still waiting" that counts one.
    FOREGROUND_STARVED         the owner's own read refused because the turn had already read
                               too much.
    SELF_UI_KNOWLEDGE_ERROR    a question the UI manifest answers, disclaimed instead.
    OWNER_FEEDBACK_IGNORED     feedback said out loud with no `owner_feedback` event for it.
    COLLISION                  two fingers on one control, or two controls in one place.
    FOCUS_LOST                 a render took away the owner's place: the keyboard's focus, a
                               field's contents, or the scroll position.
"""

from __future__ import annotations

import logging
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

log = logging.getLogger("crooks.observe")

# The classes this module files, in the order they are tested. Ordered so that the cause comes
# before the consequence: a surface stuck after a verified change explains the reconciles that
# follow it, and a half that redrew nothing explains the taps that hunted for it.
CLASSES: tuple[str, ...] = (
    "ACTION_UI_STUCK", "SPLIT_NO_REDRAW", "SPLIT_DUPLICATE_SURFACE", "WRONG_BRANCH_SURFACE",
    "STALE_PENDING_ACTION", "FOREGROUND_STARVED", "PROGRESSIVE_RENDER_MISSING",
    "DUPLICATE_RENDER", "NAV_SEMANTIC_MISMATCH", "FAKE_CONTROL", "DEAD_CONTROL",
    "SELF_UI_KNOWLEDGE_ERROR", "OWNER_FEEDBACK_IGNORED", "COLLISION", "FOCUS_LOST",
)
SEVERITY: dict[str, int] = {
    "ACTION_UI_STUCK": 6, "OWNER_FEEDBACK_IGNORED": 6, "SELF_UI_KNOWLEDGE_ERROR": 5,
    "SPLIT_NO_REDRAW": 5, "SPLIT_DUPLICATE_SURFACE": 5, "WRONG_BRANCH_SURFACE": 5,
    "FOREGROUND_STARVED": 5, "NAV_SEMANTIC_MISMATCH": 4, "STALE_PENDING_ACTION": 4,
    "FAKE_CONTROL": 4, "DEAD_CONTROL": 4, "PROGRESSIVE_RENDER_MISSING": 3,
    "FOCUS_LOST": 3, "DUPLICATE_RENDER": 2, "COLLISION": 2,
}
COMPONENT: dict[str, str] = {
    "ACTION_UI_STUCK": "the action surface (web/app.js::settleProposals, web/ui.js): the server's terminal status must settle a card from ANY non-terminal state, `committing` included",
    "SPLIT_NO_REDRAW": "the halves (web/app.js, app/routes/branches.py): focus must redraw the half it moves to",
    "SPLIT_DUPLICATE_SURFACE": "the fork (app/session/branch.py): a forked half needs its own navigation state, or it draws its parent's screen",
    "WRONG_BRANCH_SURFACE": "the halves: a control carried a branch that was not the focused one",
    "STALE_PENDING_ACTION": "the proposal store (app/actions): an undo offer is a property of a finished change, not a queued one",
    "FOREGROUND_STARVED": "the read budget (app/reads/scheduler.py): speculation and the owner's own request share one budget",
    "PROGRESSIVE_RENDER_MISSING": "the workspace (app/presentation.py, app/routes/turn.py): a shell, then facts patched in place",
    "DUPLICATE_RENDER": "the renderer (web/app.js): the same cards drawn again instead of left alone",
    "NAV_SEMANTIC_MISMATCH": "navigation (app/commands.py, web/app.js): Home is a landing and Back is a workspace, and ok=true is not the same as arriving",
    "FAKE_CONTROL": "the surface vocabulary (app/presentation.py, web/ui.js): a control offered with nothing behind it",
    "DEAD_CONTROL": "the command layer (app/commands.py, app/routes/command.py): a tap accepted that changed nothing on screen",
    "SELF_UI_KNOWLEDGE_ERROR": "the UI semantics manifest (app/observability/ui_semantics.py) and the read family that reaches it",
    "OWNER_FEEDBACK_IGNORED": "owner feedback (app/observability/feedback.py, app/families/owner_feedback.py)",
    "COLLISION": "the tablet's touch targets (web/style.css, web/app.js): two fingers on one control, or two controls in one place",
    "FOCUS_LOST": "the renderer's patching (web/app.js): a background render must not take the keyboard or the scroll position",
}
TASKS: dict[str, str] = {
    "ACTION_UI_STUCK": "the worst class on the screen: the change was made and the card never said so. One state machine with terminal states, the server authoritative, and a watchdog that asserts no surface stays EXECUTING after its proposal is terminal.",
    "SPLIT_NO_REDRAW": "give each half its own navigation state and redraw on focus; a fork that draws its parent's screen is not a split.",
    "SPLIT_DUPLICATE_SURFACE": "the two halves drew the same cards. Per-half header, per-half entity and cursor, and a forked half that says plainly when it holds nothing.",
    "WRONG_BRANCH_SURFACE": "read the focused half from one place; a control that names a backgrounded half is either refused or redirected, never served quietly.",
    "STALE_PENDING_ACTION": "separate `pending` from `undoable`, give undo its own TTL, and take it out of every \"still waiting\" count.",
    "FOREGROUND_STARVED": "separate the budgets with strict priority — foreground read first, speculation last — and make speculation yield at once.",
    "PROGRESSIVE_RENDER_MISSING": "draw the shell, then patch the facts in as each read lands; instrument time_to_shell and time_to_first_fact and hold them.",
    "DUPLICATE_RENDER": "patch the surface that changed rather than redrawing the same cards; each redraw costs the owner his scroll position.",
    "NAV_SEMANTIC_MISMATCH": "Home reaches the branch's landing, Back restores the exact prior workspace, Next moves the set's cursor with a visible \"3 of 10\". Assert the restored workspace, never the HTTP code.",
    "FAKE_CONTROL": "either the control holds what it offers, or it is not drawn; a refusal under a finger is a control that should not have been there.",
    "DEAD_CONTROL": "a tap that changes nothing must say so; find what the owner expected and either do it or disable the control with a reason.",
    "SELF_UI_KNOWLEDGE_ERROR": "the manifest answers this. Check the question reaches the read family rather than the model.",
    "OWNER_FEEDBACK_IGNORED": "the owner narrated a defect and nothing recorded it. A test session must take it as an `owner_feedback` event and the report must print it verbatim.",
    "COLLISION": "separate the targets, or make the second touch a no-op rather than a different gesture.",
    "FOCUS_LOST": "patch in place; keep the field's focus, its contents and the scroll position across a background render.",
}

# What the SCREEN did, as one word per class. The vocabulary of the `visible` column.
VISIBLE_WORD: dict[str, str] = {
    "ACTION_UI_STUCK": "APPLYING_STUCK", "SPLIT_NO_REDRAW": "NOT_REDRAWN",
    "SPLIT_DUPLICATE_SURFACE": "TWO_OF_THE_SAME", "WRONG_BRANCH_SURFACE": "WRONG_HALF",
    "STALE_PENDING_ACTION": "STILL_WAITING", "FOREGROUND_STARVED": "STARVED",
    "PROGRESSIVE_RENDER_MISSING": "LATE", "DUPLICATE_RENDER": "REDRAWN",
    "NAV_SEMANTIC_MISMATCH": "WENT_NOWHERE", "FAKE_CONTROL": "NOTHING_BEHIND_IT",
    "DEAD_CONTROL": "NO_RESPONSE", "SELF_UI_KNOWLEDGE_ERROR": "DISCLAIMED",
    "OWNER_FEEDBACK_IGNORED": "DISCARDED", "COLLISION": "COLLIDED", "FOCUS_LOST": "PLACE_LOST",
}

# ------------------------------------------------------------------------ the thresholds

# Two reconciles that keep something are a settle that did not stick; one is a correction.
STUCK_RECONCILES = 2
# How long after a focus change a redraw still counts as that focus change's.
REDRAW_S = 5.0
# The same cards, again, inside this many seconds of the last time they were drawn.
DUPLICATE_S = 5.0
# Nothing on screen for this long, with no shell before it, is not progressive rendering.
PROGRESSIVE_MS = 3_000.0
# A burst of navigation this size inside this window is hunting, not moving.
NAV_WINDOW_S = 30.0
NAV_BURST = 4
# A control accepted and nothing redrawn within this is a control that did nothing.
DEAD_S = 3.0
# A place lost this soon after something redrew is that redraw's doing.
FOCUS_S = 5.0

# The refusal codes that mean the control had nothing behind it. Every one is a code the Mac
# itself writes (app/commands.py, app/families/landings.py).
NOTHING_BEHIND = frozenset({
    "not_held", "landing_unavailable", "no_entity", "no_set", "unknown_command", "unknown_kind",
    "unknown_area", "unknown_tab", "no_tabs", "no_ref", "unknown_control", "no_target",
    "unknown_branch", "branch_closed", "empty_set", "dead_chip",
})
# A read refused because the turn had already read too much (app/reads/scheduler.py). The
# owner's own request, refused by work nobody asked for.
STARVED_RE = re.compile(
    r"reading for too long|answer from what has been read|read budget|budget (?:spent|exhausted)"
    r"|too many reads|read cap", re.I)
# The navigation commands, and the ones that are a move through a set rather than a trail.
NAV_COMMANDS = frozenset({"navigation.home", "navigation.back", "navigation.forward"})
SET_COMMANDS = frozenset({"workflow.next", "workflow.previous"})
# The states a card can be in while it says "Applying…" (web/ui.js). A render carrying one of
# these for a proposal the Mac has already settled is the stuck surface itself, photographed.
APPLYING_STATES = frozenset({"committing", "executing", "verifying"})
TERMINAL_STATUS = frozenset({"VERIFIED", "UNVERIFIED", "FAILED", "STALE", "EXPIRED", "REVOKED"})

# The answers that disclaim the product's own interface, or its own ability to write something
# down. Held here because they are the sentences the live session actually produced.
DISCLAIMS_RE = re.compile(
    r"i (?:do not|don'?t) know what that (?:button|control|thing|is)"
    r"|not something i control"
    r"|check with whoever"
    r"|whoever (?:built|builds|made|makes|handles|handles the)"
    r"|that'?s just the tablet'?s (?:own )?screen"
    r"|i(?:'ve| have) no (?:tool|way)\b"
    r"|i still have no tool"
    r"|nothing here reaches whoever"
    r"|you'?d need to raise it with", re.I)


# ---------------------------------------------------------------------------- findings


@dataclass(frozen=True)
class Finding:
    """One thing the owner could see going wrong, and what was read to say so."""

    name: str
    turn_id: str
    signal: str
    subject: str = ""          # the proposal's operation or the control's name, where there is one

    def as_dict(self) -> dict[str, Any]:
        return {"class": self.name, "turn_id": self.turn_id, "signal": self.signal,
                "subject": self.subject or None}


@dataclass
class Row:
    """A turn's two outcomes, and the verdict they produce together."""

    turn_id: str
    subject: str
    backend: str
    visible: str
    experience: str
    why: str = ""

    def line(self) -> str:
        """The line §17 asks for, padded so a column of them reads as a column."""
        return (f"{self.subject}:  backend = {self.backend}   visible = {self.visible}   "
                f"experience = {self.experience}")


@dataclass
class Reading:
    """Everything this module found, for the report and for the tests."""

    findings: list[Finding] = field(default_factory=list)
    rows: list[Row] = field(default_factory=list)
    feedback: list[dict[str, Any]] = field(default_factory=list)
    ignored_feedback: list[dict[str, Any]] = field(default_factory=list)
    # A rule that could not read this timeline, by name. Kept rather than swallowed: a
    # detection that silently stops detecting is how the live hour came to be scored 11 of 14,
    # so the report prints these and a test asserts the list is empty.
    errors: list[str] = field(default_factory=list)

    @property
    def counts(self) -> Counter:
        return Counter(f.name for f in self.findings)

    def by_turn(self, turn_id: str) -> list[Finding]:
        return [f for f in self.findings if f.turn_id == turn_id]

    def of(self, name: str) -> list[Finding]:
        return [f for f in self.findings if f.name == name]


# ------------------------------------------------------------------------- small readers


def _events(rec: Any, kind: str) -> list[dict[str, Any]]:
    return [e for e in rec.events if str(e.get("kind") or "") == kind]


def _renders(rec: Any) -> list[dict[str, Any]]:
    return _events(rec, "tablet_render")


def _signature(render: dict[str, Any]) -> tuple:
    """What was on screen, as a comparable shape: the card types, their refs and the tab that
    was open. Never their contents."""
    return tuple(
        (str(c.get("type") or ""), str(c.get("ref") or ""), str(c.get("tab_active") or ""))
        for c in (render.get("cards") or []) if isinstance(c, dict)
    )


def _turn_at(rec: Any, ts: float) -> str:
    """The turn running at that moment, else the one most recently started. A tap between two
    questions belongs to the one before it, which is the turn the owner was looking at."""
    best = ""
    for turn in rec.turns:
        if turn.started_at <= ts:
            best = turn.turn_id
    return best


def _terminal_by(rec: Any, ts: float) -> list[Any]:
    """The proposals the Mac had already settled by that moment."""
    out = []
    for proposal in rec.proposals.values():
        final = proposal.final
        if final is not None and float(final.get("ts") or 0.0) <= ts:
            out.append(proposal)
    return out


# ------------------------------------------------------------------------------- rules


def _action_ui_stuck(rec: Any) -> list[Finding]:
    """A surface the Mac settled and the tablet kept.

    `tablet_reconcile` carries the tablet's own three numbers: `count`, how many live
    proposals it submitted; `kept`, how many of them the Mac said were finished and it
    therefore called settle on; `cancelled`, how many the Mac had never heard of. A card that
    is settled leaves the live list, so it cannot be submitted again. Two reconciles in a row
    that KEEP something mean the settle did nothing — and the live session has six in a row
    reading `count=2 kept=2`, one per turn, for six turns.
    """
    events = sorted(_events(rec, "tablet_reconcile"), key=lambda e: float(e.get("ts") or 0.0))
    out: list[Finding] = []
    run: list[dict[str, Any]] = []

    def close(run: list[dict[str, Any]]) -> None:
        if len(run) < STUCK_RECONCILES:
            return
        pairs = Counter((int(e.get("count") or 0), int(e.get("kept") or 0)) for e in run)
        (count, kept), repeats = pairs.most_common(1)[0]
        for event in run[1:]:
            ts = float(event.get("ts") or 0.0)
            settled = _terminal_by(rec, ts)
            if not settled:
                continue
            operations = sorted({p.operation for p in settled if p.operation and not p.undo_of})
            out.append(Finding(
                "ACTION_UI_STUCK",
                str(event.get("turn_id") or _turn_at(rec, ts)),
                f"the Mac had settled {len(settled)} change(s) and the tablet submitted "
                f"{event.get('count')} again, keeping {event.get('kept')}: "
                f"{len(run)} consecutive reconciles, {repeats} of them count={count} kept={kept}"
                + (f"; settled: {', '.join(operations)}" if operations else ""),
                subject=operations[0] if operations else "",
            ))

    for event in events:
        if int(event.get("kept") or 0) >= 1:
            run.append(event)
            continue
        close(run)
        run = []
    close(run)

    # The same fault, photographed: a card drawn still saying "Applying…" for a proposal the
    # Mac had already settled. Stronger evidence than the reconciles when the tablet reports
    # its surface states, and silent when it does not.
    for render in _renders(rec):
        ts = float(render.get("ts") or 0.0)
        settled = {p.proposal_id for p in _terminal_by(rec, ts)}
        for card in render.get("cards") or []:
            if not isinstance(card, dict):
                continue
            state = str((card.get("surface") or {}).get("state") or "")
            pid = str(card.get("proposal_id") or "")
            if state in APPLYING_STATES and pid in settled:
                proposal = rec.proposals.get(pid)
                out.append(Finding(
                    "ACTION_UI_STUCK", str(render.get("turn_id") or _turn_at(rec, ts)),
                    f"the card for {pid} was drawn in state {state!r} after the Mac settled it "
                    f"as {proposal.status if proposal else 'terminal'}",
                    subject=(proposal.operation if proposal else ""),
                ))
    return out


def _split_findings(rec: Any) -> list[Finding]:
    """What the two halves cost the owner: a focus that drew nothing, and two halves showing
    the same cards."""
    out: list[Finding] = []
    forks = [e for e in rec.events if str(e.get("kind") or "") == "branch_forked"]
    if not forks:
        return out
    first_fork = min(float(e.get("ts") or 0.0) for e in forks)
    renders = sorted(((float(r.get("ts") or 0.0), r) for r in _renders(rec) if r.get("cards")),
                     key=lambda pair: pair[0])
    focuses = sorted((e for e in rec.events if str(e.get("kind") or "") == "branch_focused"),
                     key=lambda e: float(e.get("ts") or 0.0))
    for event in focuses:
        ts = float(event.get("ts") or 0.0)
        if ts < first_fork:
            continue
        after = [r for at, r in renders if ts <= at <= ts + REDRAW_S]
        if not after:
            out.append(Finding(
                "SPLIT_NO_REDRAW", _turn_at(rec, ts),
                f"the half {event.get('branch_id') or '?'} was focused and nothing was drawn "
                f"within {REDRAW_S:.0f} s of it",
                subject=str(event.get("branch_id") or ""),
            ))
            continue
        # What the half drew, held against what the previous half drew. Two halves whose cards
        # are the same cards is the owner's "it just shows two of the same thing".
        signature = _signature(after[0])
        previous = [(at, r) for at, r in renders if at < ts]
        if previous and _signature(previous[-1][1]) == signature and signature:
            out.append(Finding(
                "SPLIT_DUPLICATE_SURFACE", _turn_at(rec, ts),
                f"the half {event.get('branch_id') or '?'} drew the same cards as the half "
                f"before it: {', '.join(sorted({t for t, _r, _tab in signature}))}",
                subject=str(event.get("branch_id") or ""),
            ))
    return out


def _wrong_branch(rec: Any) -> list[Finding]:
    """A control that acted on a half which was not the one the owner was talking to."""
    out: list[Finding] = []
    focused = ""
    for event in sorted(rec.events, key=lambda e: (float(e.get("ts") or 0.0), int(e.get("seq") or 0))):
        kind = str(event.get("kind") or "")
        branch = str(event.get("branch_id") or "")
        if kind == "branch_focused":
            # Only a FOCUS moves who the owner is talking to. A fork does not: "Divided. Tap a
            # half to talk to it" is what the tablet says, and treating the fork as a focus
            # reported every command on the parent half as being on the wrong one.
            focused = branch
            continue
        if kind in ("branch_merged", "branch_cancelled"):
            # The surviving half is not named by the event, so the tracking stops rather than
            # reporting every command afterwards as being on the wrong half.
            focused = ""
            continue
        if kind not in ("command", "command_stage", "row_action") or not focused or not branch:
            continue
        if branch != focused and event.get("ok") is not False:
            ts = float(event.get("ts") or 0.0)
            out.append(Finding(
                "WRONG_BRANCH_SURFACE", str(event.get("turn_id") or _turn_at(rec, ts)),
                f"{event.get('command') or event.get('action') or kind} was served on {branch} "
                f"while {focused} was the focused half",
                subject=str(event.get("command") or event.get("action") or ""),
            ))
    return out


def _duplicate_renders(rec: Any) -> list[Finding]:
    """The same cards, drawn again within seconds. Every redraw costs the owner his place."""
    out: list[Finding] = []
    seen: dict[tuple, tuple[float, int]] = {}
    for render in sorted(_renders(rec), key=lambda r: float(r.get("ts") or 0.0)):
        signature = _signature(render)
        if not signature:
            continue
        ts = float(render.get("ts") or 0.0)
        last = seen.get(signature)
        if last is not None and ts - last[0] <= DUPLICATE_S:
            n = last[1] + 1
            seen[signature] = (ts, n)
            out.append(Finding(
                "DUPLICATE_RENDER", str(render.get("turn_id") or _turn_at(rec, ts)),
                f"the same {', '.join(t for t, _r, _tab in signature)} card(s) drawn again "
                f"{ts - last[0]:.1f} s later (#{n} of this shape)",
            ))
        else:
            seen[signature] = (ts, 1)
    return out


def _progressive(rec: Any) -> list[Finding]:
    """Nothing on screen until everything was ready.

    `workspace_ms` is the Mac's own measurement of when the cards existed
    (app/routes/turn.py::_performance); with no shell drawn before it, that number is how long
    the owner looked at the previous screen.
    """
    out: list[Finding] = []
    for turn in rec.turns:
        drew = sorted(((float(r.get("ts") or 0.0), r) for r in turn.tablet_events("render")),
                      key=lambda pair: pair[0])
        with_cards = [at for at, r in drew if r.get("cards")]
        if not with_cards:
            continue
        shells = [at for at, r in drew if not r.get("cards") and at < with_cards[0]]
        workspace = (turn.performance or {}).get("workspace_ms")
        waited = float(workspace) if isinstance(workspace, (int, float)) else (with_cards[0] - turn.started_at) * 1000
        if waited >= PROGRESSIVE_MS and not shells and len(with_cards) == 1:
            out.append(Finding(
                "PROGRESSIVE_RENDER_MISSING", turn.turn_id,
                f"the first and only cards arrived after {waited:,.0f} ms with nothing drawn "
                f"before them",
            ))
    return out


def _navigation(rec: Any) -> list[Finding]:
    """Navigation that was accepted and took the owner nowhere.

    Two rules. A BURST — four or more accepted Home / Back / Forward inside half a minute — is
    somebody hunting for a landing he never reaches; the live hour has eight Homes and four
    Backs in twenty-two seconds, every one `ok=true`, and the old report called that "100 %
    accepted". And a HOME that replays the record already in hand instead of reaching the
    branch's landing, which is what made the hunt necessary.
    """
    out: list[Finding] = []
    commands = sorted((e for e in rec.controls if str(e.get("kind") or "") == "command"
                       and str(e.get("command") or "") in NAV_COMMANDS and e.get("ok") is not False),
                      key=lambda e: float(e.get("ts") or 0.0))
    used: set[int] = set()
    for i, first in enumerate(commands):
        if i in used:
            continue
        start = float(first.get("ts") or 0.0)
        window = [(j, e) for j, e in enumerate(commands[i:], start=i)
                  if float(e.get("ts") or 0.0) - start <= NAV_WINDOW_S]
        if len(window) < NAV_BURST:
            continue
        used.update(j for j, _e in window)
        counts = Counter(str(e.get("command") or "") for _j, e in window)
        span = float(window[-1][1].get("ts") or 0.0) - start
        out.append(Finding(
            "NAV_SEMANTIC_MISMATCH", _turn_at(rec, start),
            ", ".join(f"{n} × {name.split('.')[-1]}" for name, n in counts.most_common())
            + f" accepted in {span:.0f} s, every one ok=true — accepted is not arrived",
            subject="navigation",
        ))
    for event in rec.controls:
        if str(event.get("command") or "") != "navigation.home" or event.get("ok") is False:
            continue
        if event.get("replayed") and event.get("entity"):
            ts = float(event.get("ts") or 0.0)
            out.append(Finding(
                "NAV_SEMANTIC_MISMATCH", str(event.get("turn_id") or _turn_at(rec, ts)),
                f"Home replayed the {event.get('entity')} already in hand instead of reaching "
                f"the half's landing",
                subject="navigation.home",
            ))
    return out


def _controls(rec: Any) -> list[Finding]:
    """Controls with nothing behind them, and controls that did nothing."""
    out: list[Finding] = []
    renders = sorted(float(r.get("ts") or 0.0) for r in _renders(rec) if r.get("cards"))
    for event in rec.controls:
        kind = str(event.get("kind") or "")
        if kind not in ("command", "command_stage", "row_action"):
            continue
        ts = float(event.get("ts") or 0.0)
        name = str(event.get("command") or event.get("action") or kind)
        turn_id = str(event.get("turn_id") or _turn_at(rec, ts))
        code = str(event.get("code") or "")
        if event.get("ok") is False and code in NOTHING_BEHIND:
            out.append(Finding(
                "FAKE_CONTROL", turn_id,
                f"{name} was on screen and the Mac refused it {code}: the control was offered "
                f"with nothing behind it",
                subject=name,
            ))
            continue
        if event.get("ok") is False:
            continue
        if str(event.get("command") or "") in NAV_COMMANDS | SET_COMMANDS and not any(
                ts <= at <= ts + DEAD_S for at in renders):
            out.append(Finding(
                "DEAD_CONTROL", turn_id,
                f"{name} was accepted and nothing was drawn within {DEAD_S:.0f} s of it",
                subject=name,
            ))
    for turn in rec.turns:
        for tap in turn.tablet_events("rail_tap"):
            if str(tap.get("state") or "") == "disabled":
                out.append(Finding(
                    "FAKE_CONTROL", turn.turn_id,
                    f"the {tap.get('action')} chip was tapped while it was disabled",
                    subject=str(tap.get("action") or ""),
                ))
        for nav in turn.tablet_events("navigate"):
            if str(nav.get("nav") or "") == "dead_chip":
                out.append(Finding(
                    "FAKE_CONTROL", turn.turn_id,
                    "a context chip was tapped that the tablet no longer held",
                    subject="context chip",
                ))
    return out


def _stale_pending(rec: Any) -> list[Finding]:
    """A change left PENDING for the rest of the session, and the count that reported one.

    The two "changes still waiting" the live session warned about at merge were the two UNDO
    offers for changes that had already succeeded. Availability of an undo is not unfinished
    work.
    """
    out: list[Finding] = []
    stopped = rec.session.get("stopped_at")
    end = float(stopped) if isinstance(stopped, (int, float)) else max(
        [float(e.get("ts") or 0.0) for e in rec.events] or [0.0])
    for proposal in sorted(rec.proposals.values(), key=lambda p: p.staged_at or 0.0):
        if proposal.status != "PENDING" or proposal.staged_at is None:
            continue
        out.append(Finding(
            "STALE_PENDING_ACTION", proposal.turn_id or _turn_at(rec, proposal.staged_at),
            f"{proposal.proposal_id} ({proposal.operation or 'a change'}"
            + (" — an undo offer" if proposal.undo_of else "")
            + f") stayed PENDING for {end - proposal.staged_at:.0f} s, to the end of the session",
            subject=proposal.operation or proposal.proposal_id,
        ))
    for turn in rec.turns:
        for toast in turn.tablet_events("toast"):
            words = str(toast.get("message") or "")
            if not re.search(r"\bstill waiting\b|\bchanges waiting\b", words, re.I):
                continue
            undone = [p for p in rec.proposals.values() if p.status == "PENDING" and p.undo_of]
            if undone:
                out.append(Finding(
                    "STALE_PENDING_ACTION", turn.turn_id,
                    f"the tablet said changes were still waiting; {len(undone)} of the pending "
                    f"proposal(s) are undo offers for changes already made",
                    subject="undo",
                ))
    return out


def _starved(rec: Any) -> list[Finding]:
    """The owner's own read, refused because the turn had already read too much."""
    out: list[Finding] = []
    for turn in rec.turns:
        refusals = [t for t in turn.tools if t.outcome == "refused" and STARVED_RE.search(t.error or "")]
        if refusals:
            names = Counter(t.tool for t in refusals)
            out.append(Finding(
                "FOREGROUND_STARVED", turn.turn_id,
                f"{len(refusals)} read(s) the owner asked for were refused for having read too "
                f"long: " + ", ".join(f"{name} × {n}" for name, n in names.most_common()),
                subject=next(iter(names)),
            ))
        for event in turn.commands:
            if event.get("ok") is False and str(event.get("code") or "") == "landing_unavailable":
                out.append(Finding(
                    "FOREGROUND_STARVED", turn.turn_id,
                    f"a dock landing was refused {event.get('code')} while the turn was reading",
                    subject=str(event.get("command") or "open.area"),
                ))
    return out


def _self_knowledge(rec: Any) -> list[Finding]:
    """A question the manifest answers, disclaimed instead.

    The manifest is asked whether it has an entry for the question. If it has, and the answer
    disclaimed the interface or referred the owner to whoever built it, the product did not
    know itself. A sentence that is feedback rather than a question is not this: that is
    OWNER_FEEDBACK_IGNORED, and the two are kept apart here as they are in the router.
    """
    from app.observability import feedback as feedback_mod
    from app.observability import ui_semantics

    out: list[Finding] = []
    for turn in rec.turns:
        question, answer = turn.question or turn.raw_text, turn.answer
        if not question or not answer:
            continue
        if feedback_mod.recognise(question) is not None:
            continue
        known = ui_semantics.lookup(question)
        if known is None or not DISCLAIMS_RE.search(answer):
            continue
        out.append(Finding(
            "SELF_UI_KNOWLEDGE_ERROR", turn.turn_id,
            f"asked about {known.entry.control} and disclaimed it; the manifest has the answer"
            + (f" (the {known.entry.command} command)" if known.entry.command else ""),
            subject=known.entry.key,
        ))
    return out


def _feedback(rec: Any) -> tuple[list[Finding], list[dict[str, Any]], list[dict[str, Any]]]:
    """What the owner said about the product, and whether anything wrote it down."""
    from app.observability import feedback as feedback_mod

    recorded = _events(rec, "owner_feedback")
    by_turn = {str(e.get("turn_id") or ""): e for e in recorded}
    out: list[Finding] = []
    ignored: list[dict[str, Any]] = []
    for turn in rec.turns:
        said = turn.question or turn.raw_text
        recognition = feedback_mod.recognise(said)
        if recognition is None:
            continue
        if turn.turn_id in by_turn:
            continue
        ignored.append({"turn_id": turn.turn_id, "shape": recognition.kind, "text": recognition.text,
                        "answer": turn.answer, "at": turn.started_at,
                        "screen": [str(c.get("type") or "") for r in turn.tablet_events("render")
                                   for c in (r.get("cards") or []) if isinstance(c, dict)][:6]})
        out.append(Finding(
            "OWNER_FEEDBACK_IGNORED", turn.turn_id,
            f"the owner asked for this to be recorded ({recognition.kind}) and no owner_feedback "
            f"event exists for the turn; the answer was: " + (turn.answer[:120] or "nothing"),
            subject="owner_feedback",
        ))
    return out, recorded, ignored


def _collisions(rec: Any) -> list[Finding]:
    """Two fingers on one control, or two controls in one place.

    The tablet reports the first itself (`tablet_hold` with `phase: "multitouch"` and the
    finger count) and would report the second as `tablet_collision`. A collision that ended a
    recording is GESTURE_COLLISION's — the narrower class, already filed by the classifier —
    so a turn that carries that one is left alone here.
    """
    out: list[Finding] = []
    gesture_turns = {t.turn_id for t in rec.turns if "GESTURE_COLLISION" in t.classes}
    for event in rec.events:
        kind = str(event.get("kind") or "")
        ts = float(event.get("ts") or 0.0)
        turn_id = str(event.get("turn_id") or _turn_at(rec, ts))
        if kind == "tablet_hold" and str(event.get("phase") or "") == "multitouch":
            if turn_id in gesture_turns:
                continue
            fingers = event.get("fingers") if isinstance(event.get("fingers"), int) else 2
            out.append(Finding(
                "COLLISION", turn_id,
                f"{fingers} fingers landed on the {event.get('target') or 'orb'} at once",
                subject=str(event.get("target") or ""),
            ))
        elif kind == "tablet_collision":
            out.append(Finding(
                "COLLISION", turn_id,
                f"{event.get('a') or 'a control'} and {event.get('b') or 'another'} overlap by "
                f"{event.get('overlap') or '?'} px",
                subject=str(event.get("a") or ""),
            ))
    return out


def _focus_lost(rec: Any) -> list[Finding]:
    """The owner's place, taken away by something that redrew.

    Two shapes. The tablet says so — `tablet_focus` with a lost state, or a composer field
    whose contents went from something to nothing across a render. Or the scroll position did:
    a deep scroll, then a redraw, then the top of the same document, with no navigation
    between to explain it.
    """
    out: list[Finding] = []
    ordered = sorted(rec.events, key=lambda e: (float(e.get("ts") or 0.0), int(e.get("seq") or 0)))
    typed = 0
    for i, event in enumerate(ordered):
        kind = str(event.get("kind") or "")
        ts = float(event.get("ts") or 0.0)
        turn_id = str(event.get("turn_id") or _turn_at(rec, ts))
        if kind == "tablet_focus" and str(event.get("state") or "") in ("lost", "blur"):
            out.append(Finding(
                "FOCUS_LOST", turn_id,
                f"the keyboard left {event.get('name') or 'a field'}"
                + (f" when {event.get('cause')}" if event.get("cause") else ""),
                subject=str(event.get("name") or ""),
            ))
        elif kind == "tablet_compose_field":
            chars = int(event.get("chars") or 0)
            if typed > 0 and chars == 0:
                out.append(Finding(
                    "FOCUS_LOST", turn_id,
                    f"the composer's {event.get('name') or 'field'} held {typed} character(s) "
                    f"and then held none",
                    subject=str(event.get("name") or ""),
                ))
            typed = chars
        elif kind == "tablet_scroll" and int(event.get("depth") or 0) == 0:
            deep = None
            for earlier in reversed(ordered[:i]):
                earlier_kind = str(earlier.get("kind") or "")
                if float(event.get("ts") or 0.0) - float(earlier.get("ts") or 0.0) > FOCUS_S:
                    break
                if earlier_kind in ("command", "tablet_navigate", "tablet_tab"):
                    deep = None
                    break
                if earlier_kind == "tablet_scroll" and int(earlier.get("depth") or 0) > 0:
                    deep = earlier
                    break
            if deep is None:
                continue
            if int(deep.get("height") or 0) != int(event.get("height") or 0):
                continue      # a different document: the place could not be kept
            between = [e for e in ordered[:i]
                       if str(e.get("kind") or "") in ("tablet_render", "branch_focused")
                       and float(deep.get("ts") or 0.0) <= float(e.get("ts") or 0.0) <= ts]
            if not between:
                continue
            out.append(Finding(
                "FOCUS_LOST", turn_id,
                f"the scroll was {deep.get('depth')} px down the same {event.get('height')} px "
                f"document and returned to the top after {len(between)} redraw(s), with no "
                f"navigation between",
                subject="scroll",
            ))
    return out


def _feedback_findings(rec: Any) -> list[Finding]:
    return _feedback(rec)[0]


RULES = (_action_ui_stuck, _split_findings, _wrong_branch, _duplicate_renders, _progressive,
         _navigation, _controls, _stale_pending, _starved, _self_knowledge, _collisions,
         _focus_lost)


# --------------------------------------------------------------------- the two outcomes


def backend_outcome(turn: Any) -> str:
    """What the SERVER did. The old report's only column."""
    proposals = [p for p in turn.proposals if p.proposal_id and not p.undo_of]
    if any(p.status == "VERIFIED" for p in proposals):
        return "VERIFIED"
    if any(p.status == "UNVERIFIED" for p in proposals):
        return "UNVERIFIED"
    if any(p.status in ("FAILED", "STALE", "EXPIRED", "REVOKED") for p in proposals):
        return next(p.status for p in proposals if p.status in ("FAILED", "STALE", "EXPIRED", "REVOKED"))
    if any(p.committed for p in proposals):
        return "EXECUTING"
    if proposals:
        return "STAGED"
    if any(t.outcome in ("error", "exception", "unprepared") for t in turn.tools):
        return "TOOL_ERROR"
    if any(t.outcome == "refused" for t in turn.tools):
        return "REFUSED"
    if any(t.outcome in ("ok", "staged") for t in turn.tools):
        return "READ_OK"
    if turn.error_kind:
        return "ERROR"
    if turn.answer:
        return "ANSWERED"
    return "NOTHING"


def visible_outcome(turn: Any, found: list[Finding]) -> str:
    """What the OWNER could see. The column the report did not have.

    The worst of what went wrong, not the first: a turn whose feedback was discarded AND whose
    cards were late is a turn whose feedback was discarded.
    """
    names = {f.name for f in found}
    for name in sorted(names, key=lambda n: (-SEVERITY[n], CLASSES.index(n))):
        return VISIBLE_WORD[name]
    cards = [c for r in turn.tablet_events("render") for c in (r.get("cards") or []) if isinstance(c, dict)]
    if turn.error_kind:
        return "NOTHING"
    if cards:
        return "DRAWN"
    if turn.answer:
        return "SPOKEN"
    return "NOTHING"


# What a class does to the verdict. At this severity or above the owner could not do or see
# the thing at all — a change that never said it was made, feedback thrown away, a half that
# drew nothing, his own read refused — and the turn is a failure whatever the backend managed.
# Below it the turn happened and cost him something: a redraw, a dead tap, a late card.
FAILS_THE_TURN = 5
# Backend states that are a failure on their own, whatever the screen did.
BACKEND_FAILED = frozenset({"UNVERIFIED", "FAILED", "STALE", "EXPIRED", "REVOKED", "TOOL_ERROR", "ERROR"})


def experience_outcome(turn: Any, found: list[Finding]) -> str:
    """The verdict the owner would give.

    A turn is NOT successful because the backend verified. It is successful when the backend
    did its part AND nothing the owner could see went wrong.
    """
    worst = max((SEVERITY[f.name] for f in found), default=0)
    if worst >= FAILS_THE_TURN or backend_outcome(turn) in BACKEND_FAILED:
        return "FAILED"
    if worst:
        return "PARTIAL"
    if turn.outcome == "successful":
        return "SUCCESSFUL"
    return "FAILED" if turn.outcome == "failed" else "PARTIAL"


def _subjects(turn: Any, found: list[Finding]) -> list[str]:
    """What each row of a turn is ABOUT: the changes it staged, else what it did."""
    operations = [p.operation for p in turn.proposals if p.operation and not p.undo_of]
    if operations:
        return sorted(set(operations))
    worst = sorted(found, key=lambda f: (-SEVERITY[f.name], CLASSES.index(f.name)))
    subject = next((f.subject for f in worst if f.subject), "")
    if subject:
        return [subject]
    tools = [t.tool for t in turn.tools if t.outcome in ("ok", "staged")]
    if tools:
        return [tools[0]]
    return [str((turn.lane or {}).get("family") or turn.cluster or "the turn")]


def read(rec: Any) -> Reading:
    """Everything this module finds in one timeline, and the two outcomes per turn."""
    findings: list[Finding] = []
    errors: list[str] = []
    for rule in RULES + (_feedback_findings,):
        try:
            findings.extend(rule(rec))
        except Exception as exc:  # noqa: BLE001 — one rule that cannot read a timeline is not a crash
            errors.append(f"{rule.__name__}: {type(exc).__name__}")
            log.warning("the experience rule %s could not read this timeline: %s", rule.__name__, exc)
    # Exact repeats are one finding: eleven Homes that each replayed the record in hand are one
    # defect said eleven times, and a report that lists it eleven times buries the other ten.
    seen: set[tuple[str, str, str]] = set()
    unique: list[Finding] = []
    for finding in findings:
        key = (finding.name, finding.turn_id, finding.signal)
        if key in seen:
            continue
        seen.add(key)
        unique.append(finding)
    findings = sorted(unique, key=lambda f: (CLASSES.index(f.name), f.turn_id))
    _extra, recorded, ignored = _feedback(rec)
    reading = Reading(findings=findings, feedback=recorded, ignored_feedback=ignored, errors=errors)
    for turn in rec.turns:
        mine = reading.by_turn(turn.turn_id)
        backend = backend_outcome(turn)
        visible = visible_outcome(turn, mine)
        experience = experience_outcome(turn, mine)
        why = "; ".join(dict.fromkeys(f.signal for f in mine))
        for subject in _subjects(turn, mine):
            reading.rows.append(Row(turn_id=turn.turn_id, subject=subject, backend=backend,
                                    visible=visible, experience=experience, why=why))
    return reading


def apply(rec: Any) -> Reading:
    """Read the timeline and put what it says on the turns themselves.

    The classes join `turn.classes` so section 5, section 12 and the improvement candidates
    see them like any other; `turn.backend`, `turn.visible` and `turn.experience` are the two
    outcomes and the verdict.
    """
    reading = read(rec)
    for turn in rec.turns:
        mine = reading.by_turn(turn.turn_id)
        for finding in mine:
            if finding.name not in turn.classes:
                turn.classes.append(finding.name)
                turn.signals.append(finding.signal)
            elif finding.signal not in turn.signals:
                turn.signals.append(finding.signal)
        turn.backend = backend_outcome(turn)
        turn.visible = visible_outcome(turn, mine)
        turn.experience = experience_outcome(turn, mine)
    return reading
