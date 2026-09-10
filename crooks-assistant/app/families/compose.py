"""Writing an email to anybody, and the draft→send correction (brief §7, §8).

Two bench failures, one family.

    "Write an email to a model asking if they're free for a shoot next Sunday. Their email
     is 1232candlestickhorse@gmail.com. Don't send it yet."

was refused, because every recipient this build could reach was a Shopify customer. The
address the owner says out loud is the one recipient the shop cannot supply, and refusing it
is refusing the job — a shoot is booked with models, not with people who have bought a hoodie.

    "No, don't save a draft. You want it sent."

spent twenty-five seconds in Claude and failed. It is a correction, not a new instruction:
the draft is on the Mac already, with its recipient, its subject and its words decided, and
turning it into a send is arithmetic on state the Mac holds.

WHAT IS NEW HERE, AND WHAT IS NOT. The composer is a *context on the branch*
(`Branch.compose`), not a change. Opening it reads nothing and stages nothing; typing into it
posts `compose.field` — a compose id, a field NAME from a closed set, and the typed value —
and the Mac validates that into its own copy; only a gesture on Save draft or Send stages, and
staging calls the one registered write tool through the one action engine with the execution
arguments built from the Mac's copy. So the hybrid precision input of §7 changes nothing about
the write boundary: the tablet still never supplies an argument of a mutation, it supplies a
value the Mac decides what to do with. That distinction is the whole design, and the tests
hold it.

An arbitrary address is admitted by `gmail_draft_new`/`gmail_send_new` only alongside the
`compose_id` of a composer this conversation was handed, which the gate checks against
`session.issued_ids` like any other id — so an address can only be staged from a composer
whose card the owner has already read. The address itself could never carry that check: an
address is not a well-formed id (`gate._ID_SHAPE` has no "@").

THE FAST LANE AND THE MUTATION GUARD. `intent.resolve` refuses to score a sentence carrying a
mutation verb, and both bench sentences carry one ("write", "send"). Rather than lift the
guard, the three read-only families here declare `serves_mutation_words=True` and
`app/fastpath/intent.py` narrows the candidate set to the families that have declared it — so
"cancel it" still leaves the lane unscored, and what these families may DO is unchanged:
`recipes.assert_read_only` still holds and the read scheduler still refuses a plan with a
write in it. Nothing on the fast lane here can stage. `draft.send_instead` therefore stages
from the TOUCH path only (`POST /command`, where a gesture arrives); spoken, "send it instead"
draws the same email as a composer in send mode, one gesture from going.
"""

from __future__ import annotations

import logging
import os
import re
import time
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from app.capabilities.families import CapabilityFamily
from app.capabilities.families import register as register_capability
from app.commands import Command, Outcome
from app.commands import Ctx as CommandCtx
from app.commands import register as register_command
from app.fastpath.intent import Family, extend
from app.fastpath.models import Ctx, FastAnswer
from app.fastpath.recipes import CACHE_NONE, Recipe, register
from app.surfaces import Surface
from app.tools.gate import Tier
from app.tools.gmail_writes import (
    EMAIL_ADDRESS,
    MAX_ADDRESS_CHARS,
    MAX_BODY_CHARS,
    MAX_SUBJECT_CHARS,
)
from app.tools.registry import ToolError, tool

log = logging.getLogger("crooks.families.compose")

# The shop's clock. Every relative date the owner speaks is his own working week, and the
# fixture world is stamped in this zone too (experience/fixtures/data.py) — a date resolved in
# UTC is the wrong day for the hour either side of midnight, which is a bug that passes all
# day and fails at eleven at night.
SHOP_TZ = ZoneInfo("Europe/London")

# How long a composer stands. Long enough to dictate, read it back, correct an address and
# think about it; short enough that a composer left open this morning cannot be what "send
# it" means this afternoon.
COMPOSE_TTL_S = 1800.0
# How far back "send it instead" will look for the draft it converts. A draft proposed
# seconds ago is what "it" means; one from ten minutes ago is not, and guessing would send an
# email the owner had moved on from.
CONVERT_WINDOW_S = 300.0
MAX_ABOUT_CHARS = 200
PLACEHOLDER_SUBJECT = "the assistant is writing this"

# What may be typed into the composer, and nothing else. A field name outside this set is
# refused: the tablet must not be able to name a key of the Mac's own context.
FIELDS = ("to", "to_name", "subject", "body")


def _now() -> float:
    return time.time()


# --------------------------------------------------------------------------- the address


# Lead-in words a dictated address arrives wrapped in: "their email is 1232 candlestick horse
# at gmail dot com". "at" is deliberately absent — it is the @.
_LEAD_IN = frozenset({
    "their", "her", "his", "its", "it's", "the", "email", "e-mail", "mail", "address",
    "is", "to", "and", "on", "an", "a", "send", "write", "compose", "it", "this",
})
_DICTATED = re.compile(r"\s+(?:at|@)\s+|\s+dot\s+|\s+underscore\s+|\s+dash\s+|\s+hyphen\s+", re.I)


def looks_dictated(value: str) -> bool:
    """Whether this reads as an address a microphone heard rather than one a finger typed."""
    return bool(_DICTATED.search(f" {str(value or '').strip()} "))


def normalise_address(said: str) -> str:
    """A spoken address as characters: "1232 candlestick horse at gmail dot com" →
    "1232candlestickhorse@gmail.com".

    Word by word rather than by substitution, because the pieces of a local part arrive as
    separate words and every space inside an address is a space the speaker did not mean. The
    lead-in ("their email is") is dropped from the FRONT only: a word that is filler in front
    of the address is part of the address anywhere inside it.
    """
    words = [w for w in re.split(r"\s+", str(said or "").strip().lower()) if w]
    while words and words[0] in _LEAD_IN:
        words.pop(0)
    swap = {"at": "@", "@": "@", "dot": ".", "underscore": "_", "dash": "-", "hyphen": "-"}
    return "".join(swap.get(word, word) for word in words)[:MAX_ADDRESS_CHARS]


def check_address(said: str) -> tuple[str, str, str]:
    """(value, status, hint) for an address as it was given.

    Three statuses, and they mean three different things to the owner:

        ok          it is an address, typed or written cleanly, and it may be staged
        uncertain   it was DICTATED. It is normalised and shown, and the owner is asked to
                    look at it — because a microphone that hears "candlestick" as "candle
                    stick" produces a perfectly valid address belonging to somebody else,
                    and no check on this side of the wire can tell the difference.
        invalid     it is not an address at all

    A dictated address is never `ok`, even when it validates. That is the point:
    `compose.stage` refuses anything but `ok`, so the correction is a tap on the field rather
    than an email to a stranger.
    """
    raw = " ".join(str(said or "").split())
    if not raw:
        return "", "invalid", "no address yet"
    if looks_dictated(raw):
        value = normalise_address(raw)
        if not EMAIL_ADDRESS.match(value):
            return value, "invalid", "I could not make an address out of that — type it in"
        return value, "uncertain", "heard, not typed — check it before this goes anywhere"
    value = raw.lower()[:MAX_ADDRESS_CHARS]
    if not EMAIL_ADDRESS.match(value):
        return value, "invalid", "that is not an email address"
    return value, "ok", ""


# --------------------------------------------------------------------------- the date

_WEEKDAYS = {
    "monday": 0, "mondays": 0, "tuesday": 1, "tuesdays": 1, "wednesday": 2, "wednesdays": 2,
    "thursday": 3, "thursdays": 3, "friday": 4, "fridays": 4, "saturday": 5, "saturdays": 5,
    "sunday": 6, "sundays": 6,
}
_WHEN = re.compile(
    r"\b(?:(?:on|next|this|coming)\s+)?(" + "|".join(sorted(_WEEKDAYS, key=len, reverse=True)) + r")\b"
    r"|\b(today|tomorrow|tonight)\b"
    r"|\b(next|this)\s+(week|weekend|month)\b",
    re.I,
)


def resolve_when(text: str, *, now: datetime | None = None) -> dict[str, str]:
    """The first relative date in the words, as a date and as the owner said it.

    One rule, written down here rather than guessed at each call site: **a named weekday is
    the soonest one strictly after today.** "Next Sunday" and "on Sunday" resolve the same,
    because on a workbench they mean the same thing and pretending to tell them apart would
    be a guess printed as a fact. Today's own weekday therefore means a week away, which is
    what "next Sunday" said on a Sunday means.

    Empty when the words name no date, and the composer then says nothing about a date. That
    is the failure that matters: an email proposing a day the owner never said.
    """
    moment = now or datetime.now(SHOP_TZ)
    today = moment.date()
    found = _WHEN.search(str(text or ""))
    if not found:
        return {}
    phrase = " ".join(found.group(0).split()).lower()
    weekday, plain, relative, unit = found.group(1), found.group(2), found.group(3), found.group(4)
    if weekday:
        ahead = (_WEEKDAYS[weekday.lower()] - today.weekday()) % 7
        when = today + timedelta(days=ahead or 7)
    elif plain:
        when = today + timedelta(days=1) if plain.lower() == "tomorrow" else today
    elif unit.lower() == "weekend":
        ahead = (5 - today.weekday()) % 7                      # the coming Saturday
        when = today + timedelta(days=ahead or 7)
    elif unit.lower() == "month":
        when = today + timedelta(days=30)
    else:
        when = today + timedelta(days=7 if relative.lower() == "next" else 0)
    return {"date": when.isoformat(), "phrase": phrase}


# --------------------------------------------------------------------------- what it is about

# Where the brief of the email starts, when the owner gave one. "Write an email to X ASKING IF
# they're free for a shoot next Sunday" — the clause after the marker is the instruction, and
# the words in front of it are the addressing.
_ABOUT_MARKERS = ("asking", "and ask", "to ask", "about", "saying", "and say", "to say", "telling", "tell them", "letting them know")
# And where it stops. "Their email is …" is addressing and "don't send it yet" is an
# instruction to the assistant; neither is a line of the email, and neither may end up in the
# subject the model is asked to write.
_ABOUT_ENDS = re.compile(
    r"\b(?:don'?t|do not|dont)\s+(?:send|email|mail)\b|\bnot\s+yet\b|\bjust\s+a\s+draft\b"
    r"|\b(?:their|his|her|the)\s+(?:e-?mail|address)\s+is\b",
    re.I,
)


def about_from(text: str, *, address: str = "") -> str:
    """What the email is about, in the owner's own words — never the assistant's summary of
    them. A summary is a guess, and the owner is about to read this on the card."""
    said = " ".join(str(text or "").split())
    if address:
        # Case-insensitively: the span the router matched came off the lowered text, and the
        # sentence it came from is capitalised ("Their email is …"). A case-sensitive replace
        # left the whole address sitting in the subject the model was asked to write.
        said = " ".join(re.sub(re.escape(address), " ", said, flags=re.I).split())
    lowered = said.lower()
    start = min((lowered.find(m) for m in _ABOUT_MARKERS if lowered.find(m) >= 0), default=-1)
    clause = said[start:] if start >= 0 else said
    stop = _ABOUT_ENDS.search(clause)
    if stop:
        clause = clause[: stop.start()]
    return " ".join(clause.split()).strip(" ,.;:")[:MAX_ABOUT_CHARS]


# --------------------------------------------------------------------------- the context


def new_compose_id() -> str:
    return f"cmp_{os.urandom(5).hex()}"


def open_compose(
    branch: Any,
    *,
    kind: str = "new",
    to: str = "",
    to_name: str = "",
    subject: str = "",
    body: str = "",
    thread_id: str = "",
    about: str = "",
    origin_text: str = "",
    resolved_when: dict[str, str] | None = None,
) -> str:
    """Start a composer on this half and return its id. Reads nothing; stages nothing.

    The context this creates is the ONLY place the recipient, subject and body live until a
    gesture asks for them. That is what makes a typed value on the tablet safe: it is an
    input to this dictionary, not an argument to a mutation.
    """
    value, status, hint = check_address(to)
    compose: dict[str, Any] = {
        "compose_id": new_compose_id(),
        "kind": "reply" if kind == "reply" else "new",
        "to": value, "to_status": status, "to_hint": hint,
        "to_name": " ".join(str(to_name or "").split())[:80],
        "subject": " ".join(str(subject or "").split())[:MAX_SUBJECT_CHARS],
        "subject_status": "ok" if str(subject or "").strip() else "uncertain",
        "body": str(body or "").replace("\r\n", "\n")[:MAX_BODY_CHARS],
        "body_status": "ok" if str(body or "").strip() else "uncertain",
        "thread_id": str(thread_id or "")[:120],
        "about": " ".join(str(about or "").split())[:MAX_ABOUT_CHARS],
        "original": " ".join(str(origin_text or "").split())[:MAX_ABOUT_CHARS],
        "resolved_when": dict(resolved_when or {}),
        "converts": "",
        "at": _now(),
    }
    branch.compose = compose
    return str(compose["compose_id"])


def held(branch: Any, compose_id: str = "") -> dict[str, Any] | None:
    """This half's composer, when it is the one named and it has not gone stale.

    Both checks matter. The id, because a composer belongs to the half it was started on and
    a tap posted from a screen that has moved on must not reach the other half's. The clock,
    because the execution arguments are built from this dictionary, and an address that has
    been sitting on the Mac since this morning is not what the owner is looking at.
    """
    compose = getattr(branch, "compose", None)
    if not isinstance(compose, dict) or not compose.get("compose_id"):
        return None
    if compose_id and str(compose_id) != str(compose["compose_id"]):
        return None
    if _now() - float(compose.get("at") or 0) > COMPOSE_TTL_S:
        branch.compose = None
        return None
    return compose


def _continue_prompt(compose: dict[str, Any]) -> str:
    """The follow-up the model is asked for once the composer is on screen: the owner's own
    instruction, the date the Mac resolved, and the one call that fills the fields.

    Server-authored, every word of it, and it names a tool that writes only into the Mac's
    own context. It rides on the card's data rather than being spoken because the fast lane
    has no second wave to carry it — `app/routes/turn.py` returns as soon as a recipe answers
    — so the tablet relays it once and never renders it.
    """
    when = compose.get("resolved_when") or {}
    lines = [f'The owner said: "{compose.get("original") or compose.get("about") or ""}"']
    if compose.get("to"):
        lines.append(f"A composer is open and addressed to {compose['to']}. Nothing is saved or sent.")
    if when.get("date"):
        lines.append(f'"{when.get("phrase")}" is {when["date"]} (Europe/London) — use the date, not the phrase.')
    lines.append(
        f'Write the email in the owner\'s voice, plainly, and call gmail_compose_fill('
        f'compose_id="{compose.get("compose_id")}", subject=…, body=…). Do not stage a draft '
        "or a send: the owner's gesture on the card does that."
    )
    return "\n".join(lines)


ACTIONS: tuple[dict[str, Any], ...] = (
    {"id": "save_draft", "label": "Save draft", "mode": "stage"},
    {"id": "send", "label": "Send", "mode": "stage", "risk": "red"},
    {"id": "discard", "label": "Discard"},
)


def compose_surface(compose: dict[str, Any]) -> Surface:
    """The composer as a card. Every value copied key by key and bounded, which is
    `app/presentation.py`'s rule kept here because this card is built outside it."""
    return Surface(
        surface_type="email_compose",
        ui_type="email_compose",
        title="Reply" if compose["kind"] == "reply" else "New email",
        data={
            "compose_id": str(compose["compose_id"]),
            "kind": str(compose["kind"]),
            "to": {"value": str(compose.get("to") or ""),
                   "status": str(compose.get("to_status") or "invalid"),
                   "hint": str(compose.get("to_hint") or "")[:120]},
            "to_name": str(compose.get("to_name") or "")[:80],
            "subject": {"value": str(compose.get("subject") or "")[:MAX_SUBJECT_CHARS],
                        "status": str(compose.get("subject_status") or "uncertain"),
                        "placeholder": PLACEHOLDER_SUBJECT},
            "body": {"value": str(compose.get("body") or "")[:MAX_BODY_CHARS],
                     "status": str(compose.get("body_status") or "uncertain"),
                     "placeholder": PLACEHOLDER_SUBJECT},
            "thread_id": str(compose.get("thread_id") or "")[:120],
            "about": str(compose.get("about") or "")[:MAX_ABOUT_CHARS],
            "resolved_when": (dict(compose.get("resolved_when") or {}) or None),
            "original": str(compose.get("original") or "")[:MAX_ABOUT_CHARS],
            "actions": [dict(a) for a in ACTIONS],
            # For the model, by way of the tablet. Never drawn.
            "continue_prompt": _continue_prompt(compose),
        },
        spoken_summary="Nothing is saved or sent until you tap.",
    )


def _spoken(compose: dict[str, Any]) -> str:
    who = compose.get("to") or "nobody yet"
    line = f"Writing to {who}" if compose["kind"] == "new" else f"Replying to {who}"
    when = (compose.get("resolved_when") or {}).get("date") or ""
    if when:
        line += f", about {when}"
    if compose.get("to_status") == "uncertain":
        return f"{line}. I heard that address rather than read it — check it. Nothing is saved or sent."
    return f"{line}. Nothing is saved or sent until you tap."


# --------------------------------------------------------------------------- the read tools


def _session_and_branch() -> tuple[Any, Any]:
    from app.tools.context import CURRENT_SESSION, acting_branch

    session = CURRENT_SESSION.get()
    if session is None:
        raise ToolError("There is no conversation to compose in.")
    return session, session.branch(acting_branch(session))


@tool(
    name="gmail_compose_open",
    description=(
        "Put an email to an address the owner gave (a model, a supplier, a venue — not a Shopify "
        "customer) on their screen as editable fields, and return its compose_id. Stages nothing "
        "and sends nothing. For a customer's own address use gmail_draft_new or gmail_send_new."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "to": {"type": "string", "maxLength": MAX_ADDRESS_CHARS, "description": "The address, as the owner gave it."},
            "subject": {"type": "string", "maxLength": MAX_SUBJECT_CHARS, "description": "One plain line."},
            "body": {"type": "string", "maxLength": MAX_BODY_CHARS, "description": "The email, plainly."},
            "to_name": {"type": "string", "maxLength": 80, "description": "Their name, if said."},
            "about": {"type": "string", "maxLength": MAX_ABOUT_CHARS, "description": "What it is about, in the owner's words."},
            "thread_id": {"type": "string", "description": "Only for a reply in a thread already read."},
        },
        "required": ["to", "subject", "body"],
    },
    tier=Tier.GREEN,
    issued_id_args=("thread_id",),
)
async def gmail_compose_open(to: str, subject: str, body: str, to_name: str = "", about: str = "", thread_id: str = "") -> dict[str, Any]:
    """The composer, opened by the model. A read tool because it reads and changes nothing
    outside the Mac: the branch gets a context, the session is issued its id, the card goes
    up. That id is what lets `gmail_draft_new`/`gmail_send_new` accept an address at all
    (`app/tools/gmail_writes.py::_recipient`), and the gate holds it to this conversation."""
    session, branch = _session_and_branch()
    compose_id = open_compose(
        branch, kind="reply" if thread_id else "new", to=to, to_name=to_name, subject=subject,
        body=body, thread_id=thread_id, about=about or subject, origin_text=about or subject,
        resolved_when=resolve_when(f"{about} {subject} {body}"),
    )
    compose = held(branch, compose_id) or {}
    if compose.get("to_status") == "invalid":
        branch.compose = None
        raise ToolError(f"{str(to)[:80]!r} is not an address I can send to, so no composer was opened.")
    # The id becomes an id this conversation has been handed, which is the whole permission
    # story for the address behind it. The address is remembered as personal data so the turn
    # log scrubs it.
    session.issue(compose_id)
    session.remember_pii(*[v for v in (compose.get("to"), compose.get("to_name")) if v])
    return {
        "compose_id": compose_id, "kind": compose.get("kind"), "to": compose.get("to"),
        "to_status": compose.get("to_status"), "to_hint": compose.get("to_hint"),
        "subject": compose.get("subject"), "body": compose.get("body"),
        "resolved_when": dict(compose.get("resolved_when") or {}),
        "_surfaces": [compose_surface(compose).as_ui()],
        "staged": False,
        "note": "The composer is on the owner's screen. Nothing is saved or sent; the owner's gesture on Save draft or Send does that.",
    }


@tool(
    name="gmail_compose_fill",
    description=(
        "Write the subject and body into an open composer. Nothing is saved or sent; this only "
        "changes what the owner is reading."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "compose_id": {"type": "string", "description": "From gmail_compose_open."},
            "subject": {"type": "string", "maxLength": MAX_SUBJECT_CHARS, "description": "One plain line."},
            "body": {"type": "string", "maxLength": MAX_BODY_CHARS, "description": "The email, plainly."},
        },
        "required": ["compose_id", "subject", "body"],
    },
    tier=Tier.GREEN,
    issued_id_args=("compose_id",),
)
async def gmail_compose_fill(compose_id: str, subject: str, body: str) -> dict[str, Any]:
    """The words, into the Mac's own copy. The recipient is not touched: the model may write
    the email and may not change who it goes to."""
    _session, branch = _session_and_branch()
    compose = held(branch, compose_id)
    if compose is None:
        raise ToolError("That composer is closed. Open one with gmail_compose_open.")
    line = " ".join(str(subject or "").split())[:MAX_SUBJECT_CHARS]
    text = str(body or "").replace("\r\n", "\n")[:MAX_BODY_CHARS]
    if not line or not text.strip():
        raise ToolError("A composer needs both a subject and a body.")
    compose.update({"subject": line, "subject_status": "ok", "body": text, "body_status": "ok", "at": _now()})
    return {
        "compose_id": str(compose["compose_id"]), "subject": line, "body": text,
        "_surfaces": [compose_surface(compose).as_ui()], "staged": False,
        "note": "On screen. Save draft or Send is the owner's gesture, not yours.",
    }


# --------------------------------------------------------------------------- the recipes


def _no_plan(_ctx: Ctx) -> None:
    """Every recipe here reads nothing. The composer is state the Mac already holds and the
    date is arithmetic — there is no source to ask, which is why these answer in a
    millisecond and why they can never write."""
    return None


def _open_render(ctx: Ctx, _result: Any) -> FastAnswer:
    """"Write an email to <address> …" — the composer, immediately.

    Deferring rather than guessing is this lane's rule and it does real work here: the family
    matches on `has_address`, and a sentence of the same shape with no address the Mac can
    make sense of ("email them all") lands in the defer below and goes to Claude, exactly as
    it did before this family existed.
    """
    said = ctx.text or ""
    span = str(getattr(ctx.intent.signals, "address_words", "") or "")
    if not span:
        return FastAnswer(answer="", defer="no address in the words")
    if check_address(span)[1] == "invalid":
        return FastAnswer(answer="", defer="the address in the words did not resolve")
    when = resolve_when(said)
    compose_id = open_compose(
        ctx.branch, kind="new", to=span, subject="", body="",
        about=about_from(said, address=span), origin_text=said, resolved_when=when,
    )
    compose = held(ctx.branch, compose_id) or {}
    ctx.session.issue(compose_id)
    ctx.session.remember_pii(str(compose.get("to") or ""))
    # `partial` because the words of the email are not written yet. The card is honest about
    # that — the body's status is `uncertain` — and `continue_prompt` asks the model for them.
    return FastAnswer(
        answer=_spoken(compose), surfaces=[compose_surface(compose)], drawn=[], partial=True,
        trace={"compose_id": compose_id, "to_status": compose.get("to_status"),
               "when": (when or {}).get("date"), "dictated": looks_dictated(span)},
    )


def _rewrite_render(ctx: Ctx, _result: Any) -> FastAnswer:
    """"Make it shorter" / "change the subject to …" — the composer again, with the owner's
    instruction handed to the model. The Mac does not paraphrase an email; it holds the one
    copy of it and asks for better words."""
    compose = held(ctx.branch)
    if compose is None:
        return FastAnswer(answer="", defer="no composer is open on this half")
    said = " ".join((ctx.text or "").split())
    surface = compose_surface(compose)
    surface.data["continue_prompt"] = "\n".join([
        f"The composer {compose['compose_id']} is open" + (f" to {compose['to']}" if compose.get("to") else "") + ".",
        f"Its subject is: {compose.get('subject') or '(not written yet)'}",
        f"Its body is:\n{compose.get('body') or '(not written yet)'}",
        f'The owner just said: "{said}"',
        f'Apply that and call gmail_compose_fill(compose_id="{compose["compose_id"]}", subject=…, body=…). '
        "Do not stage anything.",
    ])
    return FastAnswer(
        answer="Reading it back to change it. Nothing is saved or sent.",
        surfaces=[surface], drawn=[], partial=True,
        trace={"compose_id": compose["compose_id"], "chars": len(str(compose.get("body") or ""))},
    )


def _convert_render(ctx: Ctx, _result: Any) -> FastAnswer:
    """"Send it instead" — the draft, loaded into the composer as a send, one gesture away.

    §8 asks for the send to be staged here. It is not, and that is deliberate: the fast lane
    cannot stage (`recipes.assert_read_only`, `reads/scheduler.assert_reads_only`), and the
    answer to that is not a hole in the guard but a card. The words the draft was going to
    carry are printed, the recipient is the draft's own — read out of the proposal's stored
    execution, which is what the Mac itself decided and would have sent — and Send is the red
    gesture on it. That tap posts `compose.stage`, which is the touch path, where an
    authorisation arrives and where the draft it replaces is withdrawn.
    """
    found = _latest_draft(ctx.session, ctx.branch)
    if found is None:
        return FastAnswer(answer="", defer="no draft on this half to convert")
    execution = dict(found.execution)
    thread_id = str(execution.get("thread_id") or "")
    to = str(execution.get("to") or "")
    compose_id = open_compose(
        ctx.branch, kind="reply" if thread_id else "new",
        to=to, to_name=str(execution.get("to_name") or ""),
        subject=str(execution.get("subject") or ""), body=str(execution.get("body") or ""),
        thread_id=thread_id, about="the draft you asked for, as a send",
        origin_text=" ".join((ctx.text or "").split()),
    )
    compose = held(ctx.branch, compose_id) or {}
    # This recipient came from the Mac's own prepared draft, which read it from the thread or
    # from Shopify. It is not a dictation and must not be marked as one, or the composer
    # would refuse to stage an address it had itself verified a moment ago.
    compose["to_status"], compose["to_hint"] = ("ok" if to else "invalid"), ""
    compose["converts"] = found.proposal_id
    ctx.session.issue(compose_id)
    return FastAnswer(
        answer=f"Not a draft then. The same email to {to or 'them'}, ready to send — tap Send.",
        surfaces=[compose_surface(compose)], drawn=[],
        trace={"compose_id": compose_id, "converts": found.proposal_id, "reply": bool(thread_id)},
    )


def _latest_draft(session: Any, branch: Any) -> Any:
    """The most recent email DRAFT this half prepared, recently enough to be what "it" means.
    Pending, verified, or revoked.

    REVOKED is in the list because of the voice path, not by accident: `POST /turn` advances
    the epoch and withdraws this half's pending cards BEFORE the fast lane runs
    (app/routes/turn.py), so by the time "send it instead" is routed, the draft card the owner
    is looking at has already been marked REVOKED by the very sentence trying to convert it.
    VERIFIED is in the list because the draft may really be sitting in Gmail by now.
    """
    from app.actions.models import ActionStatus

    # Order matters: a draft still waiting for a tap is what "it" means, and one already
    # withdrawn is only a fallback. Without the ranking, converting a draft twice would find
    # the withdrawn one first and prepare a second send of the same email.
    usable = (ActionStatus.PENDING, ActionStatus.VERIFIED, ActionStatus.REVOKED)
    return _latest(session, branch, lambda op: op.startswith("gmail_draft_"), usable)


def _latest_send(session: Any, branch: Any) -> Any:
    """A send this half has already prepared and not yet applied. Its card is on the screen,
    so a second "send it instead" is a repetition rather than a new instruction."""
    from app.actions.models import ActionStatus

    return _latest(session, branch, lambda op: op.startswith("gmail_send_"), (ActionStatus.PENDING,))


def _latest(session: Any, branch: Any, matches, usable) -> Any:
    branch_id = str(getattr(branch, "branch_id", "") or "")
    cutoff = _now() - CONVERT_WINDOW_S
    best = None
    best_rank = ()
    for proposal in getattr(session, "proposals", None) or ():
        if not matches(str(getattr(proposal, "operation", "") or "")):
            continue
        if getattr(proposal, "undo_of", None) or str(getattr(proposal, "branch_id", "") or "") not in ("", branch_id):
            continue
        status = getattr(proposal, "status", None)
        if status not in usable or float(getattr(proposal, "created_at", 0)) < cutoff:
            continue
        rank = (-usable.index(status), float(proposal.created_at))
        if best is None or rank >= best_rank:
            best, best_rank = proposal, rank
    return best


# --------------------------------------------------------------------------- the commands


def _no_composer() -> Outcome:
    return Outcome.refused("no_composer", "There is no email open on this half to do that to.")


def _compose_field(ctx: CommandCtx) -> Outcome:
    """A precision field on the composer, typed.

    THIS is the hybrid input of §7, and the reason it is not a way round the write boundary:
    the tablet posts a compose id, a field NAME from a closed set, and the characters the
    owner typed. It does not post an execution argument, and nothing it posts is sent
    anywhere — the Mac validates the value into its own copy of the composer and answers with
    the card again. When the gesture comes, the arguments are built from the Mac's copy.
    """
    compose = held(ctx.branch, ctx.arg("compose_id"))
    if compose is None:
        return _no_composer()
    name = ctx.arg("field")
    if name not in FIELDS:
        # Fail closed. The tablet must not be able to name a key of the Mac's own context —
        # "at", "converts" and "thread_id" are all in that dictionary and none of them is
        # something a keystroke may set.
        log.warning("compose.field refused: %r is not a field of the composer", name)
        return Outcome.refused("unknown_field", f"There is no field called {name!r} on the composer.")
    raw = str(ctx.args.get("value") or "")
    if name == "to":
        value, status, hint = check_address(raw)
        compose.update({"to": value, "to_status": status, "to_hint": hint})
    elif name == "to_name":
        compose["to_name"] = " ".join(raw.split())[:80]
    elif name == "subject":
        line = " ".join(raw.split())[:MAX_SUBJECT_CHARS]
        compose.update({"subject": line, "subject_status": "ok" if line else "uncertain"})
    else:
        text = raw.replace("\r\n", "\n")[:MAX_BODY_CHARS]
        compose.update({"body": text, "body_status": "ok" if text.strip() else "uncertain"})
    compose["at"] = _now()
    ctx.session.remember_pii(*[v for v in (compose.get("to"), compose.get("to_name")) if v])
    return Outcome(answer="", surfaces=[compose_surface(compose)],
                   changed={"compose_id": str(compose["compose_id"]), "field": name,
                            "status": str(compose.get(f"{name}_status") or "ok")})


# Which write tool each gesture on the composer reaches. Server-owned: the tablet posts
# "draft" or "send" and the Mac decides what that is a call to.
_STAGE_TOOL = {
    ("new", "draft"): "gmail_draft_new",
    ("new", "send"): "gmail_send_new",
    ("reply", "draft"): "gmail_draft_reply",
    ("reply", "send"): "gmail_send_reply",
}


def _stage_args(compose: dict[str, Any], mode: str) -> tuple[str, dict[str, Any]]:
    """(tool, arguments) for this composer, built entirely from the Mac's copy of it."""
    kind = "reply" if compose.get("thread_id") else "new"
    tool_name = _STAGE_TOOL[(kind, mode)]
    if kind == "reply":
        # A reply's recipient and subject are re-read from the thread by the tool itself, as
        # they always have been. Passing them would be the model's-recipient bug in a new hat.
        return tool_name, {"thread_id": str(compose["thread_id"]), "body": str(compose["body"])}
    return tool_name, {
        "compose_id": str(compose["compose_id"]), "to": str(compose["to"]),
        "to_name": str(compose.get("to_name") or ""), "subject": str(compose["subject"]),
        "body": str(compose["body"]),
    }


def _ready_to_stage(compose: dict[str, Any]) -> str:
    """Why this composer cannot be prepared yet, in the owner's words. Empty when it can."""
    if compose["kind"] == "new" and compose.get("to_status") != "ok":
        if compose.get("to_status") == "uncertain":
            return "That address is what I heard, not what you typed. Tap it, check it, and then I'll prepare this."
        return "There is no address I can send to yet."
    if not str(compose.get("subject") or "").strip():
        return "It has no subject yet."
    if not str(compose.get("body") or "").strip():
        return "It has no words in it yet."
    return ""


def _compose_stage(ctx: CommandCtx) -> Outcome:
    """Save draft or Send, tapped. Prepares the change; applies nothing.

    The staging itself happens in `POST /command` (`changed["stage"]`), for the same reason
    `open.area` names a recipe rather than reading: a command is synchronous by design
    (app/commands.py) and preparing a change is a fresh read. What crosses that line is a
    registered write tool's NAME and the arguments the MAC built here — never anything the
    tablet posted, and never a value that has not been through `check_address`.
    """
    compose = held(ctx.branch, ctx.arg("compose_id"))
    if compose is None:
        return _no_composer()
    mode = ctx.arg("mode") or "draft"
    if mode not in ("draft", "send"):
        return Outcome.refused("unknown_mode", "A composer is saved as a draft or sent; there is no third thing.")
    why = _ready_to_stage(compose)
    if why:
        return Outcome.refused("not_ready", why)
    tool_name, args = _stage_args(compose, mode)
    # A composer loaded from a draft (`draft_send_instead`) carries the draft's proposal id.
    # Sending replaces that card; saving another draft does not.
    revoke = [str(compose["converts"])] if compose.get("converts") and mode == "send" else []
    return Outcome(answer="", changed={
        "compose_id": str(compose["compose_id"]),
        "stage": {"tool": tool_name, "args": args, "revoke": revoke,
                  "what": "send the email" if mode == "send" else "save the draft"},
    })


def _compose_discard(ctx: CommandCtx) -> Outcome:
    compose = held(ctx.branch, ctx.arg("compose_id"))
    if compose is None:
        return _no_composer()
    ctx.branch.compose = None
    return Outcome(answer="Gone. Nothing was saved.",
                   changed={"compose": None, "discarded": str(compose["compose_id"])})


def _draft_send_instead(ctx: CommandCtx) -> Outcome:
    """"Send it instead", as a gesture: this half's draft, staged as a send, and the draft's
    own card withdrawn once the send is prepared.

    Everything comes from the Mac. The recipient, subject and body are read out of the draft
    proposal's stored `execution` — the arguments the Mac itself decided and would have sent
    — so the send carries exactly the email the owner read on the draft card. Which identity
    argument the send needs is decided from the proposal's `entity_ref`, which is what the
    Mac recorded the change as being about; the model's own arguments are not consulted.
    The withdrawal is ordered AFTER the staging (`POST /command` does it in that order),
    because a draft card taken away by a send that then failed to prepare leaves the owner
    with nothing at all.
    """
    already = _latest_send(ctx.session, ctx.branch)
    if already is not None:
        # The conversion has happened and its card is on the screen. Preparing a second send
        # of one email is how an email goes twice, and the words are the honest answer.
        return Outcome.refused("already_ready", "That one is already ready to send — hold the card.")
    found = _latest_draft(ctx.session, ctx.branch)
    if found is None:
        return Outcome.refused(
            "no_draft",
            "There is no draft of mine on this half to send. Say what the email should say and I'll write it.",
        )
    execution = dict(found.execution)
    thread_id = str(execution.get("thread_id") or "")
    body = str(execution.get("body") or "")
    if not body.strip():
        return Outcome.refused("no_draft_body", "That draft has no words in it that I can send.")
    if thread_id:
        tool_name = "gmail_send_reply"
        args: dict[str, Any] = {"thread_id": thread_id, "body": body}
    else:
        tool_name = "gmail_send_new"
        ref = str(getattr(found, "entity_ref", "") or "")
        args = {"subject": str(execution.get("subject") or ""), "body": body}
        if ref.startswith("cmp_"):
            args.update({"compose_id": ref, "to": str(execution.get("to") or ""),
                         "to_name": str(execution.get("to_name") or "")})
        elif ref.startswith("gid://shopify/Customer/"):
            args["customer_id"] = ref
        elif ref:
            args["order_id"] = ref
        else:
            return Outcome.refused("no_draft_recipient", "I cannot tell who that draft was to, so I have not prepared a send.")
    return Outcome(answer="", changed={
        "converts": found.proposal_id,
        "stage": {"tool": tool_name, "args": args, "revoke": [found.proposal_id], "what": "send it instead"},
    })


def _draft_discard(ctx: CommandCtx) -> Outcome:
    """"Forget the draft." Withdraws the card, which is synchronous and needs no read. A
    draft already saved in Gmail is removed by its own undo, which is the engine's business
    and not this command's."""
    found = _latest_draft(ctx.session, ctx.branch)
    if found is None:
        return Outcome.refused("no_draft", "There is no draft of mine on this half to forget.")
    withdrawn = ctx.runtime.actions.revoke_ids([found.proposal_id], "the owner said no draft")
    return Outcome(answer="Forgotten. Nothing was saved.",
                   changed={"discarded": found.proposal_id, "revoked": withdrawn})


# --------------------------------------------------------------------------- registration

register(Recipe(
    recipe_id="email_compose_any", intent_family="email_compose_any", read_primitives=(),
    ui="email_compose", cache_policy=CACHE_NONE, min_confidence=0.7, target_ms=50,
    plan=_no_plan, render=_open_render,
))
register(Recipe(
    recipe_id="compose_rewrite", intent_family="compose_rewrite", read_primitives=(),
    ui="email_compose", cache_policy=CACHE_NONE, min_confidence=0.7, target_ms=50,
    plan=_no_plan, render=_rewrite_render,
))
register(Recipe(
    recipe_id="draft_send_instead", intent_family="draft_send_instead", read_primitives=(),
    ui="email_compose", cache_policy=CACHE_NONE, min_confidence=0.7, target_ms=50,
    plan=_no_plan, render=_convert_render,
))

# All three declare `serves_mutation_words`, which is what lets a sentence with "write" or
# "send" in it be scored at all (app/fastpath/intent.py). None of them can write.
extend([
    # "Write an email to <address> asking …". Long by nature — a dictated email is one
    # instruction with as many clauses as the owner speaks — so the word bound is generous and
    # `many_clauses` waives the two-clauses penalty. What keeps it honest is `has_address`:
    # with no address in the words this family cannot match at all, so "email them all" still
    # goes to Claude, which can work out who "them" are.
    Family("email_compose_any", needs=("has_address", "email"), boosts=("customer",),
           blocks=("order_number", "send_instead"), base=0.86, floor=0.7, max_words=60,
           serves_mutation_words=True, many_clauses=True),
    # "Send it instead" / "no, don't save a draft, send it".
    Family("draft_send_instead", needs=("send_instead",), boosts=("deixis",),
           blocks=("has_address", "order_number", "metric", "ranking", "stock"),
           base=0.88, floor=0.7, max_words=14, serves_mutation_words=True),
    # "Make it shorter" / "change the subject to …", while a composer is open on this half.
    # Blocked by every signal that names another subject, so "cancel order 1938" said over an
    # open composer is refused as it always was rather than quietly rewriting an email.
    Family("compose_rewrite", needs=("has_compose", "rewrite"), boosts=("email",),
           blocks=("has_address", "send_instead", "order_number", "order", "customer", "metric",
                   "ranking", "stock", "running_out", "period", "status", "address", "delayed",
                   "bought", "possessive_name", "waiting"),
           base=0.8, floor=0.7, max_words=40, serves_mutation_words=True, many_clauses=True),
])

register_command(Command("compose.field", "Type into the email being written", _compose_field, voice=False))
register_command(Command("compose.stage", "Save the email as a draft, or send it", _compose_stage, voice=False))
register_command(Command("compose.discard", "Throw away the email being written", _compose_discard, voice=False))
# Voice AND touch: "send it instead" is a sentence, and Send on a draft card is a button.
register_command(Command("draft.send_instead", "Send the draft instead of saving it", _draft_send_instead))
register_command(Command("draft.discard", "Forget the draft that is waiting", _draft_discard))

register_capability(CapabilityFamily(
    key="email_compose",
    label="Writing an email to any address",
    area="email",
    what="write, draft or send an email to an address you give me, not only to a customer",
    operations=("gmail_draft_new", "gmail_send_new"),
    tools=("gmail_compose_open", "gmail_compose_fill"),
    scopes=("https://www.googleapis.com/auth/gmail.compose",),
    state="READY",
    detail="the composer opens instantly; the draft and the send are gestures on its card",
))
