"""The report: an hour with the tablet, read back from the timeline.

`reconstruct` turns the JSONL into turns, tool calls and proposals joined by their ids;
`render` writes the twelve sections as Markdown. Everything in it is counted or matched —
nothing is scored by a model. The rules that classify a failure are the ones written here,
and the report names them, so a reader can disagree with a line and see why it was drawn."""

from __future__ import annotations

import difflib
import re
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.observability import claims
from app.observability.timeline import read_events

# The classes a failed or partial turn is filed under, in the order they are tested.
CLASSES = (
    "STT_ERROR", "TIMEOUT", "PERMISSION_ERROR", "MISSING_CAPABILITY", "FALSE_UNSUPPORTED", "TOOL_ERROR", "VERIFICATION_ERROR",
    "TOOL_SELECTION_ERROR", "UI_RENDER_ERROR", "UI_NAVIGATION_PROBLEM", "CONTEXT_INCOMPLETE", "INTENT_ERROR", "UNKNOWN",
)
SEVERITY = {
    "VERIFICATION_ERROR": 5, "TOOL_ERROR": 4, "TIMEOUT": 4, "PERMISSION_ERROR": 4, "UI_RENDER_ERROR": 4, "FALSE_UNSUPPORTED": 4,
    "STT_ERROR": 3, "MISSING_CAPABILITY": 3, "UNKNOWN": 3,
    "TOOL_SELECTION_ERROR": 2, "CONTEXT_INCOMPLETE": 2, "INTENT_ERROR": 2, "UI_NAVIGATION_PROBLEM": 2,
}
COMPONENT = {
    "STT_ERROR": "speech (Scribe / whisper.cpp, app/speech)", "TIMEOUT": "the turn's budget (provider or tool timeouts)",
    "PERMISSION_ERROR": "the write boundary (CROOKS_WRITES_ENABLED, allow-list, scopes, Tailscale identity)",
    "MISSING_CAPABILITY": "the tool registry (app/tools)", "TOOL_ERROR": "the Shopify / Gmail clients (app/clients, app/tools)",
    "FALSE_UNSUPPORTED": "the model's use of the read layer and the batch tools (system prompt, commerce_capabilities)",
    "VERIFICATION_ERROR": "the action engine's proof (app/actions/engine.py)", "TOOL_SELECTION_ERROR": "the model's tool use (system prompt, tool descriptions)",
    "UI_RENDER_ERROR": "the tablet renderer (web/ui.js, app/presentation.py)", "UI_NAVIGATION_PROBLEM": "the tablet's screens (web/app.js)",
    "CONTEXT_INCOMPLETE": "context hydration (app/context/order.py, /context route)", "INTENT_ERROR": "the model's reading of the request (system prompt, normaliser)",
    "UNKNOWN": "unclassified — read the turn's events",
}
PERMISSION_CODES = frozenset({
    "writes_disabled", "allow_list_missing", "scope_missing", "gmail_scope_missing", "not_authorised", "not_authorised_local", "identity_unverified", "wrong_session",
})
# What a turn is about, from its tools first and its words second. Higher entries win.
CLUSTERS = (
    ("actions", (), ()),
    ("analytics", ("commerce_", "inventory_query", "email_query"), ("best seller", "sold most", "by size", "by colour", "compare", "average order", "days of cover", "run out", "older than", "who have emailed")),
    ("email", ("gmail_",), ("email", "inbox", "reply", "draft")),
    ("sales", ("shopify_sales_summary",), ("sales", "revenue", "takings", "how much did we")),
    ("inventory", ("shopify_inventory",), ("stock", "inventory", "how many left")),
    ("products", ("shopify_product_info",), ("inseam", "made of", "fabric", "measurements")),
    ("customers", ("shopify_find_customer", "shopify_customer_history"), ("customer", "bought before", "spent")),
    ("orders", ("shopify_find_order", "shopify_order_detail", "shopify_list_orders"), ("order", "shipped", "tracking", "delivery")),
)
# The rail's chips, by the change each puts into the owner's mouth.
RAIL_BY_OPERATION = {
    "order_note_append": "note", "order_cancel": "cancel", "refund_create": "refund", "order_shipping_address_set": "address",
    "fulfillment_create": "fulfil", "gmail_draft_new": "email",
}
# Words the assistant uses when it declines: a deterministic signal, not a judgement. Held
# with the map of what the Mac composes (app/observability/claims.py).
CANNOT_RE = claims.CANNOT_RE
CLARIFY_RE = re.compile(r"\b(which (?:one|order|customer|product)|do you mean|could you (?:say|tell me)|can you (?:say|tell me)|which do you)\b", re.I)
OFFER_GESTURE_RE = re.compile(r"\b(tap|hold|swipe|drag)\b.{0,40}\b(card|to apply|to send)\b|\bthe card\b", re.I)
# The change a request names, for "the assistant said it cannot, but a tool exists".
CAPABILITY_WORDS = {
    "refund": "shopify_refund_create", "cancel": "shopify_order_cancel", "address": "shopify_order_shipping_address_set",
    "note": "shopify_order_note_append", "tag": "shopify_order_tags_add", "ship": "shopify_order_fulfil", "fulfil": "shopify_order_fulfil",
    "tracking": "shopify_fulfillment_tracking_set", "stock": "shopify_inventory_adjust", "email": "gmail_draft_new", "reply": "gmail_draft_reply",
    "archive": "gmail_thread_archive",
}
ABANDON_S = 3.0        # a screen left this soon after it was rendered was not what was wanted
SLOW_MS = {"stt": 3000.0, "claude": 8000.0, "total": 12000.0, "tts_first_byte": 2000.0, "context": 4000.0}


# ----------------------------------------------------------------------- the model


@dataclass
class ToolRecord:
    tool_call_id: str
    tool: str
    turn_id: str
    requested_at: float = 0.0
    finished_at: float = 0.0
    args: dict[str, Any] = field(default_factory=dict)
    tier: str = ""
    disposition: str = ""
    outcome: str = ""            # ok | staged | refused | not_yet | error | exception | unprepared | (empty: never finished)
    ok: bool | None = None
    error: str = ""
    ms: float | None = None
    result: dict[str, Any] | None = None
    proposal_id: str = ""
    missing_capability: str = ""

    @property
    def service(self) -> str:
        if self.tool.startswith("shopify_"):
            return "shopify"
        if self.tool.startswith("gmail_"):
            return "gmail"
        return "other"


@dataclass
class ProposalRecord:
    proposal_id: str
    turn_id: str = ""
    session_id: str = ""
    operation: str = ""
    tool: str = ""
    risk: str = ""
    interaction: str = ""
    reversible: bool | None = None
    entity_kind: str = ""
    entity_label: str = ""
    undo_of: str = ""
    events: list[dict[str, Any]] = field(default_factory=list)   # the ledger's, in order
    refusals: list[dict[str, Any]] = field(default_factory=list)  # arm/commit refused before the engine
    commits: list[dict[str, Any]] = field(default_factory=list)   # action_commit (the route's outcome)
    tablet: list[dict[str, Any]] = field(default_factory=list)    # gestures, arms, commits, renders naming it

    def _first(self, event: str) -> dict[str, Any] | None:
        return next((e for e in self.events if e.get("event") == event), None)

    @property
    def staged_at(self) -> float | None:
        e = self._first("PROPOSED")
        return e.get("ts") if e else None

    @property
    def delivered(self) -> bool:
        return self._first("DELIVERED") is not None

    @property
    def armed(self) -> bool:
        return self._first("ARMED") is not None

    @property
    def committed(self) -> bool:
        return self._first("EXECUTING") is not None

    @property
    def final(self) -> dict[str, Any] | None:
        terminal = [e for e in self.events if e.get("status") in ("VERIFIED", "UNVERIFIED", "FAILED", "STALE", "EXPIRED", "REVOKED")]
        return terminal[-1] if terminal else None

    @property
    def status(self) -> str:
        final = self.final
        if final is not None:
            return str(final.get("status") or "")
        if self.committed:
            return "EXECUTING"
        return "PENDING"

    @property
    def code(self) -> str:
        final = self.final
        return str(final.get("code") or "") if final else ""

    @property
    def verified(self) -> bool | None:
        final = self.final
        return final.get("verified") if final else None

    @property
    def reason(self) -> str:
        final = self.final
        return str(final.get("reason") or final.get("detail") or "") if final else ""

    @property
    def latency_ms(self) -> float | None:
        if self.commits:
            ms = self.commits[-1].get("ms")
            if isinstance(ms, (int, float)):
                return float(ms)
        e = self._first("EXECUTED")
        return float(e["ms"]) if e and isinstance(e.get("ms"), (int, float)) else None


@dataclass
class Turn:
    turn_id: str
    session_id: str = ""
    seq: int = 0
    started_at: float = 0.0
    finished_at: float = 0.0
    input: str = ""
    focus: dict[str, Any] | None = None
    waiting: list[str] = field(default_factory=list)
    stt: dict[str, Any] | None = None
    prefetch: dict[str, Any] | None = None
    model: dict[str, Any] | None = None
    finished: dict[str, Any] | None = None
    tools: list[ToolRecord] = field(default_factory=list)
    proposals: list[ProposalRecord] = field(default_factory=list)
    hydrations: list[dict[str, Any]] = field(default_factory=list)
    context_requests: list[dict[str, Any]] = field(default_factory=list)
    tts: list[dict[str, Any]] = field(default_factory=list)
    tablet: list[dict[str, Any]] = field(default_factory=list)
    # The read layer's own bookkeeping: working sets made, cross-source reads, rejected
    # queries, and the turn-time claim signal (app/observability/claims.py).
    sets: list[dict[str, Any]] = field(default_factory=list)
    rejected: list[dict[str, Any]] = field(default_factory=list)
    claims: list[dict[str, Any]] = field(default_factory=list)
    batches: list[dict[str, Any]] = field(default_factory=list)
    submitted: dict[str, Any] | None = None   # the tablet's turn_submitted, paired by order
    classes: list[str] = field(default_factory=list)
    signals: list[str] = field(default_factory=list)
    outcome: str = "successful"
    cluster: str = "other"

    # ---- what was said
    @property
    def raw_text(self) -> str:
        if self.stt and self.stt.get("raw_text"):
            return str(self.stt["raw_text"])
        return self.question

    @property
    def question(self) -> str:
        if self.finished and self.finished.get("question"):
            return str(self.finished["question"])
        if self.stt and self.stt.get("text"):
            return str(self.stt["text"])
        return ""

    @property
    def answer(self) -> str:
        if self.finished and self.finished.get("answer"):
            return str(self.finished["answer"])
        if self.model and self.model.get("answer"):
            return str(self.model["answer"])
        return ""

    @property
    def error_kind(self) -> str:
        return str((self.finished or {}).get("error_kind") or (self.model or {}).get("error_kind") or "")

    @property
    def ui(self) -> list[str]:
        return [str(x) for x in ((self.finished or {}).get("ui") or [])]

    @property
    def ui_entities(self) -> list[dict[str, Any]]:
        return [x for x in ((self.finished or {}).get("ui_entities") or []) if isinstance(x, dict)]

    def tablet_events(self, kind: str) -> list[dict[str, Any]]:
        return [e for e in self.tablet if e.get("kind") == f"tablet_{kind}"]

    @property
    def render(self) -> dict[str, Any] | None:
        renders = self.tablet_events("render")
        return renders[0] if renders else None

    # ---- where the time went
    def latency(self, part: str) -> float | None:
        timings = (self.finished or {}).get("timings") or {}
        if part == "audio":
            return float(self.stt["audio_s"]) * 1000 if self.stt and isinstance(self.stt.get("audio_s"), (int, float)) else None
        if part == "stt":
            t = (self.stt or {}).get("timings") or {}
            for key in ("transcribe", "stt", "scribe", "whisper"):
                if isinstance(t.get(key), (int, float)):
                    return float(t[key])
            return float(timings["transcribe"]) if isinstance(timings.get("transcribe"), (int, float)) else None
        if part == "claude":
            return float(self.model["ms"]) if self.model and isinstance(self.model.get("ms"), (int, float)) else None
        if part in ("shopify", "gmail"):
            values = [t.ms for t in self.tools if t.service == part and isinstance(t.ms, (int, float))]
            return float(sum(values)) if values else None
        if part == "context":
            values = [h.get("ms") for h in self.hydrations if isinstance(h.get("ms"), (int, float))]
            return float(max(values)) if values else None
        if part == "tts_first_byte":
            values = [t.get("ms_first_byte") for t in self.tts if isinstance(t.get("ms_first_byte"), (int, float))]
            if values:
                return float(values[0])
            speaks = [e.get("ms") for e in self.tablet_events("speak") if isinstance(e.get("ms"), (int, float))]
            return float(speaks[0]) if speaks else None
        if part == "total":
            return float(self.finished["ms"]) if self.finished and isinstance(self.finished.get("ms"), (int, float)) else None
        if part == "round_trip":
            responses = [e.get("ms") for e in self.tablet_events("turn_response") if isinstance(e.get("ms"), (int, float))]
            return float(responses[0]) if responses else None
        return None


@dataclass
class Reconstruction:
    session: dict[str, Any]
    events: list[dict[str, Any]]
    turns: list[Turn]
    proposals: dict[str, ProposalRecord]
    orphans: list[dict[str, Any]]           # tablet and Mac events outside any turn
    unknown_kinds: Counter = field(default_factory=Counter)

    def turn(self, turn_id: str) -> Turn | None:
        return next((t for t in self.turns if t.turn_id == turn_id), None)


# ------------------------------------------------------------------ reconstruction


def reconstruct(events: list[dict[str, Any]]) -> Reconstruction:
    """Turns, tool calls and proposals from the timeline, joined by their ids. Deterministic:
    the same file gives the same structure."""
    events = sorted(events, key=lambda e: (float(e.get("ts") or 0.0), int(e.get("seq") or 0)))
    session: dict[str, Any] = {"test_session_id": "", "name": "", "started_at": None, "stopped_at": None, "duration_s": None}
    turns: dict[str, Turn] = {}
    order: list[str] = []
    proposals: dict[str, ProposalRecord] = {}
    tools: dict[str, ToolRecord] = {}
    orphans: list[dict[str, Any]] = []
    unknown: Counter = Counter()
    pending_submits: dict[str, list[dict[str, Any]]] = defaultdict(list)

    def turn_for(event: dict[str, Any]) -> Turn | None:
        turn_id = str(event.get("turn_id") or "")
        if not turn_id:
            return None
        if turn_id not in turns:
            turns[turn_id] = Turn(turn_id=turn_id, session_id=str(event.get("session_id") or ""), seq=int(event.get("seq") or 0), started_at=float(event.get("ts") or 0.0))
            order.append(turn_id)
        return turns[turn_id]

    def proposal_for(event: dict[str, Any]) -> ProposalRecord:
        pid = str(event.get("proposal_id") or "")
        if pid not in proposals:
            proposals[pid] = ProposalRecord(proposal_id=pid)
        p = proposals[pid]
        for key in ("turn_id", "session_id", "operation", "tool", "risk", "interaction", "entity_kind", "entity_label", "undo_of"):
            if event.get(key) and not getattr(p, key):
                setattr(p, key, event[key])
        if event.get("reversible") is not None and p.reversible is None:
            p.reversible = bool(event["reversible"])
        return p

    for event in events:
        kind = str(event.get("kind") or "")
        session["test_session_id"] = session["test_session_id"] or str(event.get("test_session_id") or "")
        if kind == "session_started":
            session["name"] = str(event.get("name") or "")
            session["started_at"] = event.get("started_at") or event.get("ts")
        elif kind == "session_stopped":
            session["stopped_at"] = event.get("ts")
            session["duration_s"] = event.get("duration_s")
        elif kind == "turn_started":
            turn = turn_for(event)
            if turn is not None:
                turn.session_id = str(event.get("session_id") or turn.session_id)
                turn.input = str(event.get("input") or "")
                turn.focus = event.get("focus") if isinstance(event.get("focus"), dict) else None
                turn.waiting = [str(x) for x in event.get("waiting") or []]
                turn.started_at = float(event.get("ts") or 0.0)
                turn.seq = int(event.get("seq") or 0)
                queued = pending_submits.get(turn.session_id) or []
                if queued:
                    turn.submitted = queued.pop(0)
        elif kind == "stt":
            turn = turn_for(event)
            if turn is not None:
                turn.stt = event
        elif kind == "prefetch":
            turn = turn_for(event)
            if turn is not None:
                turn.prefetch = event
        elif kind == "model":
            turn = turn_for(event)
            if turn is not None:
                turn.model = event
        elif kind == "turn_finished":
            turn = turn_for(event)
            if turn is not None:
                turn.finished = event
                turn.finished_at = float(event.get("ts") or 0.0)
        elif kind == "tool_requested":
            tc = str(event.get("tool_call_id") or "")
            record = ToolRecord(tool_call_id=tc, tool=str(event.get("tool") or ""), turn_id=str(event.get("turn_id") or ""), requested_at=float(event.get("ts") or 0.0),
                                args=event.get("args") if isinstance(event.get("args"), dict) else {}, tier=str(event.get("tier") or ""), disposition=str(event.get("disposition") or ""))
            tools[tc] = record
            turn = turn_for(event)
            if turn is not None:
                turn.tools.append(record)
            else:
                orphans.append(event)
        elif kind == "tool_finished":
            tc = str(event.get("tool_call_id") or "")
            record = tools.get(tc)
            if record is None:
                record = ToolRecord(tool_call_id=tc, tool=str(event.get("tool") or ""), turn_id=str(event.get("turn_id") or ""))
                tools[tc] = record
                turn = turn_for(event)
                if turn is not None:
                    turn.tools.append(record)
            record.finished_at = float(event.get("ts") or 0.0)
            record.outcome = str(event.get("outcome") or "")
            record.ok = event.get("ok")
            record.error = str(event.get("error") or "")
            record.ms = float(event["ms"]) if isinstance(event.get("ms"), (int, float)) else None
            record.result = event.get("result") if isinstance(event.get("result"), dict) else None
            record.proposal_id = str(event.get("proposal_id") or "")
            record.missing_capability = str(event.get("missing_capability") or "")
        elif kind.startswith("action_") and event.get("proposal_id"):
            p = proposal_for(event)
            if kind in ("action_arm_refused", "action_commit_refused"):
                p.refusals.append(event)
            elif kind == "action_commit":
                p.commits.append(event)
            else:
                p.events.append(event)
            turn = turn_for(event)
            if turn is not None and p not in turn.proposals:
                turn.proposals.append(p)
        elif kind in ("working_set", "cross_source"):
            turn = turn_for(event) or _turn_in_flight(turns, order, event)
            if turn is not None:
                turn.sets.append(event)
            else:
                orphans.append(event)
        elif kind == "query_rejected":
            turn = turn_for(event) or _turn_in_flight(turns, order, event)
            if turn is not None:
                turn.rejected.append(event)
            else:
                orphans.append(event)
        elif kind == "unsupported_claim":
            turn = turn_for(event)
            if turn is not None:
                turn.claims.append(event)
            else:
                orphans.append(event)
        elif kind.startswith("batch_") and event.get("batch_id"):
            turn = turn_for(event) or _turn_in_flight(turns, order, event)
            if turn is not None:
                turn.batches.append(event)
            else:
                orphans.append(event)
        elif kind == "context_hydration":
            turn = _turn_in_flight(turns, order, event)
            if turn is not None:
                turn.hydrations.append(event)
            else:
                orphans.append(event)
        elif kind == "context_request":
            turn = turn_for(event) or _turn_in_flight(turns, order, event)
            if turn is not None:
                turn.context_requests.append(event)
            else:
                orphans.append(event)
        elif kind == "tts":
            turn = turn_for(event)
            if turn is not None:
                turn.tts.append(event)
            else:
                orphans.append(event)
        elif kind.startswith("tablet_"):
            if kind == "tablet_turn_submitted":
                pending_submits[str(event.get("session_id") or "")].append(event)
                continue
            turn = turn_for(event)
            if turn is not None:
                turn.tablet.append(event)
                pid = str(event.get("proposal_id") or "")
                if pid:
                    proposal_for({"proposal_id": pid}).tablet.append(event)
                if kind == "tablet_render":
                    # A render names the proposals whose cards it drew, inside the cards.
                    for c in event.get("cards") or []:
                        if isinstance(c, dict) and c.get("proposal_id"):
                            proposal_for({"proposal_id": str(c["proposal_id"])}).tablet.append(event)
            else:
                orphans.append(event)
        else:
            unknown[kind] += 1
            orphans.append(event)

    # A proposal's events name its turn; a turn it was not filed under yet gets it now.
    for p in proposals.values():
        if p.turn_id and p.turn_id in turns and p not in turns[p.turn_id].proposals:
            turns[p.turn_id].proposals.append(p)
    result = [turns[t] for t in order]
    for turn in result:
        turn.tools.sort(key=lambda t: t.requested_at or t.finished_at)
        _classify(turn)
        turn.cluster = _cluster(turn)
    _mark_repeats(result)
    return Reconstruction(session=session, events=events, turns=result, proposals=proposals, orphans=orphans, unknown_kinds=unknown)


def _turn_in_flight(turns: dict[str, Turn], order: list[str], event: dict[str, Any]) -> Turn | None:
    """The turn a Mac-side event without a turn id belongs to: the one in flight at that
    moment, else the last one finished within a few seconds (a hydration that landed after
    the answer left)."""
    ts = float(event.get("ts") or 0.0)
    for turn_id in reversed(order):
        turn = turns[turn_id]
        if turn.started_at <= ts and (not turn.finished_at or ts <= turn.finished_at + 30.0):
            return turn
    return None


# -------------------------------------------------------------------- classification


def _classify(turn: Turn) -> None:
    classes: list[str] = []
    signals: list[str] = []
    stt = turn.stt or {}
    error_kind = turn.error_kind
    tools = turn.tools
    ok_tools = [t for t in tools if t.outcome in ("ok", "staged")]
    failed_tools = [t for t in tools if t.outcome in ("error", "exception", "unprepared")]
    refused = [t for t in tools if t.outcome == "refused"]
    not_yet = [t for t in tools if t.outcome == "not_yet"]
    missing = [t for t in tools if t.missing_capability]
    tablet_failed = turn.tablet_events("turn_failed")

    if stt and stt.get("ok") is False or error_kind in ("speech", "empty", "audio_too_large"):
        classes.append("STT_ERROR")
        signals.append(f"speech: {stt.get('reason') or error_kind}")
    if error_kind == "timeout" or any(e.get("aborted") for e in tablet_failed) or any(re.search(r"time[d ]?out|timeout", t.error, re.I) for t in failed_tools):
        classes.append("TIMEOUT")
        signals.append("a timeout: " + (error_kind or next((t.tool for t in failed_tools if re.search(r"time[d ]?out|timeout", t.error, re.I)), "the tablet gave up")))
    permission_refusals = [r for p in turn.proposals for r in p.refusals if str(r.get("code") or "") in PERMISSION_CODES]
    if permission_refusals or ((turn.finished or {}).get("writes_code") in PERMISSION_CODES and turn.proposals):
        classes.append("PERMISSION_ERROR")
        signals.append("a tap refused by the write boundary: " + ", ".join(sorted({str(r.get('code')) for r in permission_refusals}) or [str((turn.finished or {}).get("writes_code"))]))
    false_claim = _false_claim(turn)
    if false_claim:
        classes.append("FALSE_UNSUPPORTED")
        signals.append("declined, though the Mac composes this: " + ", ".join(false_claim["capabilities"]) + " via " + ", ".join(false_claim["composable_via"]))
    elif missing or (not ok_tools and CANNOT_RE.search(turn.answer)):
        classes.append("MISSING_CAPABILITY")
        signals.append("asked for: " + (", ".join(sorted({t.missing_capability for t in missing})) or "something the assistant said it cannot do"))
    if failed_tools:
        classes.append("TOOL_ERROR")
        signals.append("; ".join(f"{t.tool}: {t.error[:80]}" for t in failed_tools[:3]))
    unverified = [p for p in turn.proposals if p.status == "UNVERIFIED" or (p.committed and p.status == "FAILED" and p.code == "unverified")]
    if unverified:
        classes.append("VERIFICATION_ERROR")
        signals.append("not proven: " + ", ".join(p.proposal_id for p in unverified))
    duplicates = _duplicate_calls(tools)
    rules = [t for t in refused if not t.missing_capability]
    if len(not_yet) >= 2 or rules or duplicates:
        classes.append("TOOL_SELECTION_ERROR")
        if len(not_yet) >= 2:
            signals.append(f"{len(not_yet)} calls with an id the conversation had not been shown")
        if rules:
            signals.append("refused by a rule: " + ", ".join(f"{t.tool} ({t.error[:60]})" for t in rules[:2]))
        if duplicates:
            signals.append("the same call twice: " + ", ".join(duplicates))
    render = turn.render or {}
    exceptions = turn.tablet_events("exception")
    if exceptions or render.get("skipped") or render.get("errors") or turn.tablet_events("image_failed"):
        classes.append("UI_RENDER_ERROR")
        if exceptions:
            signals.append("tablet exception: " + str(exceptions[0].get("message") or "")[:100])
        if render.get("skipped"):
            signals.append("cards the tablet could not draw: " + ", ".join(str(x) for x in render["skipped"]))
        if render.get("errors"):
            signals.append("error cards: " + ", ".join(str(x) for x in render["errors"]))
        if turn.tablet_events("image_failed"):
            signals.append(f"{len(turn.tablet_events('image_failed'))} image(s) failed to load")
    if _abandoned(turn) or _dead_touches(turn):
        classes.append("UI_NAVIGATION_PROBLEM")
        if _abandoned(turn):
            signals.append(f"the screen was left within {ABANDON_S:.0f} s of rendering")
        signals.extend(_dead_touches(turn))
    if _context_incomplete(turn):
        classes.append("CONTEXT_INCOMPLETE")
        signals.append(_context_incomplete(turn))
    if CLARIFY_RE.search(turn.answer) and not ok_tools and (stt.get("order_numbers") or turn.focus):
        classes.append("INTENT_ERROR")
        signals.append("asked which, though the request named one (" + (", ".join(str(n) for n in stt.get("order_numbers") or []) or "the entity in focus") + ")")
    if (error_kind or tablet_failed) and not classes:
        classes.append("UNKNOWN")
        signals.append(f"error_kind={error_kind or 'tablet turn_failed'}")
    turn.classes = classes
    turn.signals = signals
    cards = [u for u in turn.ui if u not in ("error", "context_stack", "assistant")]
    if not classes:
        turn.outcome = "successful"
    elif ok_tools or any(p.status == "VERIFIED" for p in turn.proposals) or (cards and not error_kind):
        turn.outcome = "partial"
    else:
        turn.outcome = "failed"
    if classes in (["MISSING_CAPABILITY"], ["FALSE_UNSUPPORTED"]) and not ok_tools:
        turn.outcome = "failed"


def _false_claim(turn: Turn) -> dict[str, Any] | None:
    """The turn's claim signal, from the timeline when the Mac wrote one, else from the same
    rule applied now to the words (an older timeline, a session without the signal)."""
    for c in turn.claims:
        if c.get("false_unsupported"):
            return {"capabilities": [str(x) for x in c.get("capabilities") or []], "composable_via": [str(x) for x in c.get("composable_via") or []]}
    if turn.claims:
        return None
    signal = claims.claim(turn.question, turn.answer, [{"tool": t.tool, "ok": t.outcome in ("ok", "staged")} for t in turn.tools], _registered_for_claims())
    return signal if signal and signal.get("false_unsupported") else None


_REGISTERED_CACHE: list[str] | None = None


def _registered_for_claims() -> frozenset[str]:
    """The tools the claim rule judges against when a turn carries no signal of its own (an
    older timeline): this process's registry, read once."""
    global _REGISTERED_CACHE
    if _REGISTERED_CACHE is None:
        _REGISTERED_CACHE = registered_tools()
    return frozenset(_REGISTERED_CACHE)


def _duplicate_calls(tools: list[ToolRecord]) -> list[str]:
    seen: Counter = Counter((t.tool, tuple(sorted((k, str(v)) for k, v in t.args.items()))) for t in tools if t.outcome in ("ok", "staged", "error", "exception"))
    return [name for (name, _args), n in seen.items() if n > 1]


def _abandoned(turn: Turn) -> bool:
    render = turn.render
    if not render or not isinstance(render.get("t"), (int, float)):
        return False
    for nav in turn.tablet_events("navigate"):
        if nav.get("nav") in ("back", "home") and isinstance(nav.get("t"), (int, float)) and 0 <= (nav["t"] - render["t"]) / 1000 <= ABANDON_S:
            return True
    return False


def _dead_touches(turn: Turn) -> list[str]:
    out = []
    for tap in turn.tablet_events("rail_tap"):
        if tap.get("state") == "disabled":
            out.append(f"a tap on the disabled '{tap.get('action')}' chip")
    for nav in turn.tablet_events("navigate"):
        if nav.get("nav") == "dead_chip":
            out.append("a tap on a context chip the tablet no longer held")
    for g in turn.tablet_events("gesture"):
        if g.get("gesture") == "down" and g.get("state") in ("unavailable", "expired", "revoked", "stale"):
            out.append(f"a touch on a card already {g.get('state')}")
    for c in turn.tablet_events("action_commit"):
        if c.get("outcome") in ("unknown", "blocked_busy"):
            out.append(f"a tap the tablet could not settle ({c.get('outcome')})")
    return out


def _context_incomplete(turn: Turn) -> str:
    failed = turn.tablet_events("context_failed")
    if failed:
        return f"the tablet could not collect the rest of the order ({len(failed)} failed request(s))"
    if any(int(r.get("status") or 0) >= 500 for r in turn.context_requests):
        return "the order's history could not be read (/context answered 503)"
    unavailable = sorted({str(u) for h in turn.hydrations for u in (h.get("unavailable") or [])})
    if unavailable:
        return "unavailable for the order: " + ", ".join(unavailable)
    return ""


def _cluster(turn: Turn) -> str:
    names = {t.tool for t in turn.tools}
    words = f"{turn.question} {turn.answer}".lower()
    if turn.proposals or any(t.outcome == "staged" for t in turn.tools):
        return "actions"
    for name, prefixes, _keywords in CLUSTERS[1:]:
        if any(any(n.startswith(p) for p in prefixes) for n in names):
            return name
    for name, _prefixes, keywords in CLUSTERS[1:]:
        if any(k in words for k in keywords):
            return name
    return "other"


def _mark_repeats(turns: list[Turn]) -> None:
    """A signal, not a class: the answer repeats most of the previous answer in the session."""
    last: dict[str, str] = {}
    for turn in turns:
        previous = last.get(turn.session_id, "")
        if previous and turn.answer and _overlap(previous, turn.answer) >= 0.6:
            turn.signals.append("repeats the previous answer")
        if turn.answer:
            last[turn.session_id] = turn.answer


def _overlap(a: str, b: str) -> float:
    sa = {s.strip().lower() for s in re.split(r"[.!?]\s+", a) if len(s.strip()) > 12}
    sb = {s.strip().lower() for s in re.split(r"[.!?]\s+", b) if len(s.strip()) > 12}
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / max(1, min(len(sa), len(sb)))


# ------------------------------------------------------------------------ rendering


def _fmt_ms(value: float | None) -> str:
    return "—" if value is None else f"{value:,.0f} ms"


def _stats(values: list[float]) -> tuple[str, str, str]:
    if not values:
        return "—", "—", "—"
    ordered = sorted(values)
    p95 = ordered[min(len(ordered) - 1, max(0, int(round(0.95 * (len(ordered) - 1)))))]
    return _fmt_ms(statistics.fmean(values)), _fmt_ms(statistics.median(values)), _fmt_ms(p95)


def _clock(ts: float | None) -> str:
    if not ts:
        return "—"
    import time

    return time.strftime("%H:%M:%S", time.localtime(float(ts)))


def _cell(text: Any, limit: int = 90) -> str:
    s = " ".join(str(text if text is not None else "").split())
    s = s.replace("|", "\\|")
    return s if len(s) <= limit else s[: limit - 1] + "…"


def _table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    if not rows:
        return ["_none_", ""]
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join(" --- " for _ in headers) + "|"]
    out.extend("| " + " | ".join(_cell(c) for c in row) + " |" for row in rows)
    out.append("")
    return out


def _closest_capability(name: str, registered: list[str]) -> str:
    for word, tool in CAPABILITY_WORDS.items():
        if word in name and tool in registered:
            return f"{tool} (by the word '{word}')"
    close = difflib.get_close_matches(name, registered, n=1, cutoff=0.5)
    return close[0] if close else "none close by name"


def registered_tools() -> list[str]:
    try:
        from app.tools import (  # noqa: F401
            analytics_tools,
            batch_tools,
            gmail_tools,
            gmail_writes,
            shopify_tools,
            shopify_writes,
        )
        from app.tools.registry import all_specs

        return sorted(s.name for s in all_specs() if not s.name.startswith("mock_"))
    except Exception:  # noqa: BLE001 — the report still reads without the registry
        return []


def intelligence(rec: Reconstruction, registered: list[str]) -> dict[str, Any]:
    """Section 13's evidence, by rule, each row citing its turn: false unsupported claims,
    composable requests that failed, the multi-tool workflows and follow-up shapes the
    session repeated, and the query dimensions, actions, bulk actions and card types asked
    for that do not exist yet."""
    turns = rec.turns
    known = frozenset(registered)
    false_rows: list[dict[str, Any]] = []
    failed_rows: list[dict[str, Any]] = []
    for t in turns:
        signal = _false_claim(t)
        if signal:
            caps = [c for c in claims.CAPABILITIES if c.key in signal["capabilities"]]
            hinted = any(c.get("hinted") for c in t.claims)
            false_rows.append({"turn_id": t.turn_id, "question": t.question or t.raw_text, "answer": t.answer, "what": "; ".join(c.what for c in caps) or ", ".join(signal["capabilities"]), "tools": signal["composable_via"], "attempted": (", ".join(x.tool for x in t.tools) or "nothing") + (" (the prompt named the capability)" if hinted else "")})
        matched = [c for c in claims.match_capabilities(t.question) if all(x in known for x in c.tools)]
        if matched:
            wanted = {x for c in matched for x in c.tools}
            tried = [x for x in t.tools if x.tool in wanted]
            broken = [x for x in tried if x.outcome not in ("ok", "staged")]
            if tried and broken and not any(x.outcome in ("ok", "staged") for x in tried):
                failed_rows.append({"turn_id": t.turn_id, "question": t.question, "what": "; ".join(c.what for c in matched), "detail": "; ".join(f"{x.tool}: {x.outcome} {x.error[:80]}".strip() for x in broken[:3])})
    workflows: Counter = Counter()
    workflow_turns: dict[tuple[str, ...], list[str]] = defaultdict(list)
    for t in turns:
        names = tuple(x.tool for x in t.tools if x.outcome in ("ok", "staged"))
        if len(names) >= 2:
            workflows[names] += 1
            workflow_turns[names].append(t.turn_id)
    dimensions: Counter = Counter()
    dimension_turns: dict[str, list[str]] = defaultdict(list)
    for t in turns:
        for r in t.rejected:
            for name in r.get("unknown") or []:
                dimensions[str(name)] += 1
                dimension_turns[str(name)].append(t.turn_id)
    actions: Counter = Counter()
    action_turns: dict[str, list[str]] = defaultdict(list)
    for t in turns:
        for x in t.tools:
            if x.missing_capability:
                actions[x.missing_capability] += 1
                action_turns[x.missing_capability].append(t.turn_id)
    bulk: dict[str, dict[str, Any]] = {}
    for t in turns:
        req = claims.bulk_request(t.question)
        if req is None:
            continue
        served = any(x.tool.startswith("batch_") and x.outcome == "staged" for x in t.tools) or any(b.get("event") == "PROPOSED" for b in t.batches)
        entry = bulk.setdefault(req["operation"], {"n": 0, "turns": [], "supported": bool(req["supported"]), "served": 0})
        entry["n"] += 1
        entry["turns"].append(t.turn_id)
        entry["served"] += 1 if served else 0
    follow_ups: Counter = Counter()
    follow_up_turns: dict[str, list[str]] = defaultdict(list)
    previous: dict[str, Turn] = {}
    for t in turns:
        shape = claims.follow_up_shape(t.question)
        if shape and previous.get(t.session_id) is not None:
            follow_ups[shape] += 1
            follow_up_turns[shape].append(t.turn_id)
        previous[t.session_id] = t
    ui_types: Counter = Counter()
    ui_turns: dict[str, list[str]] = defaultdict(list)
    for t in turns:
        for r in t.tablet_events("render"):
            for kind in r.get("skipped") or []:
                ui_types[str(kind)] += 1
                ui_turns[str(kind)].append(t.turn_id)
        entity_results = [x for x in t.tools if x.outcome == "ok" and x.result and any(k in x.result for k in ("rows", "orders", "customers", "threads", "products"))]
        if entity_results and not [u for u in t.ui if u not in ("assistant", "error", "context_stack")]:
            ui_types["(records without a card)"] += 1
            ui_turns["(records without a card)"].append(t.turn_id)
    sets_made = [e for t in turns for e in t.sets if e.get("kind") == "working_set"]
    cross = [e for t in turns for e in t.sets if e.get("kind") == "cross_source"]
    batches = {str(e.get("batch_id")): e for t in turns for e in t.batches if e.get("event") == "DONE"}
    return {
        "false_unsupported": false_rows,
        "composable_failed": failed_rows,
        "workflows": [(names, n, workflow_turns[names][:5]) for names, n in workflows.most_common(10)],
        "dimensions": [(name, n, dimension_turns[name][:5]) for name, n in dimensions.most_common(10)],
        "new_actions": [(name, n, action_turns[name][:5]) for name, n in actions.most_common(10)],
        "bulk": [(op, e["n"], e["turns"][:5], e["supported"] and e["served"] > 0) for op, e in sorted(bulk.items(), key=lambda kv: -kv[1]["n"])],
        "follow_ups": [(shape, n, follow_up_turns[shape][:6]) for shape, n in follow_ups.most_common()],
        "ui_types": [(kind, n, ui_turns[kind][:5]) for kind, n in ui_types.most_common(10)],
        "sets": {"made": len(sets_made), "derived": sum(1 for e in sets_made if e.get("parent")), "by_step": dict(Counter(str(e.get("step")) for e in sets_made)), "cross_source": len(cross)},
        "batches": {"done": len(batches), "counts": {k: sum(int((e.get("counts") or {}).get(k) or 0) for e in batches.values()) for k in ("requested", "eligible", "excluded", "verified", "failed", "stale", "unverified", "not_attempted")}},
    }


def render(rec: Reconstruction, *, tools_registered: list[str] | None = None) -> str:
    registered = tools_registered if tools_registered is not None else registered_tools()
    turns = rec.turns
    session = rec.session
    lines: list[str] = []
    add = lines.append

    add(f"# CROOKS OS test session — {session.get('test_session_id') or 'unknown'}")
    add("")
    add(f"Name: **{session.get('name') or '—'}**. Written from the timeline alone; every number below is a count or a measurement, and the rules that file a turn under a failure class are the ones named in section 5.")
    add("")

    # 1 ------------------------------------------------------------------------------
    add("## 1. Session summary")
    add("")
    duration = session.get("duration_s")
    if duration is None and turns:
        duration = (turns[-1].finished_at or turns[-1].started_at) - turns[0].started_at
    counts = Counter(t.outcome for t in turns)
    add(f"- Started {_clock(session.get('started_at'))}, stopped {_clock(session.get('stopped_at'))}; duration {(_fmt_s(duration))}.")
    add(f"- Interactions: **{len(turns)}** turns across {len({t.session_id for t in turns})} conversation(s); {sum(len(t.tools) for t in turns)} tool calls; {len(rec.proposals)} proposals.")
    add(f"- Successful **{counts.get('successful', 0)}** · partial **{counts.get('partial', 0)}** · failed **{counts.get('failed', 0)}**.")
    add(f"- By input: {dict(Counter(t.input or 'unknown' for t in turns))}. Events: {len(rec.events)} ({sum(1 for e in rec.events if e.get('source') == 'tablet')} from the tablet).")
    if rec.unknown_kinds:
        add(f"- Event kinds this report does not read: {dict(rec.unknown_kinds)}.")
    add("")
    add("Outcome rule: a turn with no failure class is successful; one with a class but an answered request (a tool that returned, a card, a verified change) is partial; otherwise failed. A request for something the assistant does not have is failed, and listed in section 6.")
    add("")

    # 2 ------------------------------------------------------------------------------
    add("## 2. Performance")
    add("")
    rows = []
    parts = [("audio", "Audio length"), ("stt", "Speech to text"), ("claude", "Claude"), ("shopify", "Shopify (per turn, summed)"), ("gmail", "Gmail (per turn, summed)"), ("context", "Context hydration"), ("tts_first_byte", "TTS to first byte"), ("total", "Total turn (Mac)"), ("round_trip", "Total turn (tablet round trip)")]
    for key, label in parts:
        values = [v for v in (t.latency(key) for t in turns) if v is not None]
        avg, med, p95 = _stats(values)
        rows.append([label, len(values), avg, med, p95])
    lines.extend(_table(["Stage", "Samples", "Average", "Median", "P95"], rows))
    slowest = sorted((t for t in turns if t.latency("total") is not None), key=lambda t: -(t.latency("total") or 0))[:10]
    add("The ten slowest turns:")
    add("")
    lines.extend(_table(["Turn", "Total", "STT", "Claude", "Shopify", "Gmail", "TTS first byte", "Request"], [
        [t.turn_id, _fmt_ms(t.latency("total")), _fmt_ms(t.latency("stt")), _fmt_ms(t.latency("claude")), _fmt_ms(t.latency("shopify")), _fmt_ms(t.latency("gmail")), _fmt_ms(t.latency("tts_first_byte")), t.question] for t in slowest
    ]))

    # 3 ------------------------------------------------------------------------------
    add("## 3. Requests")
    add("")
    by_cluster: dict[str, list[Turn]] = defaultdict(list)
    for t in turns:
        by_cluster[t.cluster].append(t)
    for name in [c[0] for c in CLUSTERS] + ["other"]:
        group = by_cluster.get(name) or []
        if not group:
            continue
        add(f"### {name} — {len(group)}")
        add("")
        lines.extend(_table(["Turn", "Outcome", "Request", "Tools"], [[t.turn_id, t.outcome, t.question or t.raw_text, ", ".join(f"{x.tool}:{x.outcome or '?'}" for x in t.tools) or "—"] for t in group]))

    # 4 ------------------------------------------------------------------------------
    add("## 4. Tool usage")
    add("")
    per_tool: dict[str, list[ToolRecord]] = defaultdict(list)
    for t in turns:
        for x in t.tools:
            per_tool[x.tool].append(x)
    rows = []
    for name in sorted(per_tool):
        calls = per_tool[name]
        ok = sum(1 for c in calls if c.outcome in ("ok", "staged"))
        ms = [c.ms for c in calls if isinstance(c.ms, (int, float))]
        failures = [f"{c.turn_id}: {c.outcome} {c.error[:50]}".strip() for c in calls if c.outcome not in ("ok", "staged")]
        rows.append([name, len(calls), f"{100 * ok / len(calls):.0f}%", _fmt_ms(statistics.fmean(ms)) if ms else "—", "; ".join(failures) or "—"])
    lines.extend(_table(["Tool", "Calls", "Success", "Avg latency", "Failures"], rows))

    # 5 ------------------------------------------------------------------------------
    add("## 5. Failures")
    add("")
    add("Classes, in the order tested: " + ", ".join(CLASSES) + ". A turn may carry more than one. STT_ERROR: the recogniser returned no usable text. TIMEOUT: the turn, a tool or the tablet gave up. PERMISSION_ERROR: a tap refused by the write boundary. MISSING_CAPABILITY: a tool asked for that is not registered, or an answer that says it cannot with no tool having succeeded. TOOL_ERROR: a tool raised or returned an error. VERIFICATION_ERROR: a change sent but not proven. TOOL_SELECTION_ERROR: repeated calls with unissued ids, a rule refusal, or the same call twice. UI_RENDER_ERROR: a tablet exception, a card it could not draw, a failed image. UI_NAVIGATION_PROBLEM: the screen left within three seconds, or a touch on something dead. CONTEXT_INCOMPLETE: part of the order never arrived. INTENT_ERROR: a clarifying question though the request named its entity. UNKNOWN: an error nothing above explains.")
    add("")
    failed = [t for t in turns if t.outcome != "successful"]
    rows = []
    for t in failed:
        rows.append([t.turn_id, t.raw_text, t.question if t.question != t.raw_text else "(same)", t.answer, ", ".join(f"{x.tool}:{x.outcome or '?'}" for x in t.tools) or "—", "; ".join(t.signals), ", ".join(c.get("type", "") for c in ((t.render or {}).get("cards") or [])) or ", ".join(t.ui) or "—", ", ".join(t.classes)])
    lines.extend(_table(["Turn", "Owner said", "Normalised", "Assistant answered", "Tools attempted", "Technical reason", "UI displayed", "Class"], rows))
    add("By class: " + (", ".join(f"{k} × {v}" for k, v in Counter(c for t in failed for c in t.classes).most_common()) or "none") + ".")
    add("")

    # 6 ------------------------------------------------------------------------------
    add("## 6. Unsupported requests")
    add("")
    asked: dict[str, list[Turn]] = defaultdict(list)
    cannot: list[Turn] = []
    for t in turns:
        names = {x.missing_capability for x in t.tools if x.missing_capability}
        for name in names:
            asked[name].append(t)
        if not names and "MISSING_CAPABILITY" in t.classes:
            cannot.append(t)
    if asked:
        rows = [[name, f"requested {len(group)} time(s)", ", ".join(x.turn_id for x in group[:4]), _closest_capability(name, registered)] for name, group in sorted(asked.items(), key=lambda kv: -len(kv[1]))]
        lines.extend(_table(["Capability asked for", "Frequency", "Turns", "Closest existing capability"], rows))
        for name, group in sorted(asked.items(), key=lambda kv: -len(kv[1])):
            for t in group[:3]:
                add(f"- `{name}` — {t.turn_id}: owner said “{_cell(t.raw_text, 120)}”; assistant answered “{_cell(t.answer, 160)}”.")
        add("")
    if cannot:
        add("Answers that declined without naming a tool:")
        add("")
        lines.extend(_table(["Turn", "Owner said", "Assistant answered", "Closest existing capability"], [[t.turn_id, t.raw_text, t.answer, _closest_capability(t.question.lower(), registered)] for t in cannot]))
    if not asked and not cannot:
        add("_none_")
        add("")

    # 7 ------------------------------------------------------------------------------
    add("## 7. UI usage")
    add("")
    renders = [e for t in turns for e in t.tablet_events("render")] + [e for e in rec.orphans if e.get("kind") == "tablet_render"]
    screens = Counter(str(r.get("screen") or "") for r in renders)
    card_types = Counter(str(c.get("type") or "") for r in renders for c in (r.get("cards") or []) if isinstance(c, dict))
    sections = Counter(s for r in renders for c in (r.get("cards") or []) if isinstance(c, dict) for s in (c.get("sections") or []))
    tabs_rendered = Counter(s for r in renders for c in (r.get("cards") or []) if isinstance(c, dict) for s in (c.get("tabs") or []))
    tab_taps = Counter(str(e.get("label") or "") for t in turns for e in t.tablet_events("tab"))
    exposed: Counter = Counter()
    disabled: Counter = Counter()
    for r in renders:
        for c in r.get("cards") or []:
            for a in (c.get("actions") or []) if isinstance(c, dict) else []:
                if isinstance(a, dict):
                    (exposed if a.get("enabled") else disabled)[str(a.get("id") or "")] += 1
    used: Counter = Counter()
    for t in turns:
        for e in t.tablet_events("rail_tap"):
            used[str(e.get("action") or "")] += 1
        for e in t.tablet_events("action_primed"):
            used[str(e.get("action") or "")] += 1
    nav = Counter(str(e.get("nav") or "") for t in turns for e in t.tablet_events("navigate"))
    nav.update(str(e.get("nav") or "") for e in rec.orphans if e.get("kind") == "tablet_navigate")
    add(f"- Screens rendered: {dict(screens) or '—'}; cards: {dict(card_types) or '—'}.")
    add(f"- Sections shown on cards: {dict(sections) or '—'}; tab controls: {dict(tabs_rendered) or 'none rendered'}; tabs tapped: {dict(tab_taps) or 'none'}.")
    add(f"- Rail actions exposed (enabled): {dict(exposed) or '—'}; shown disabled: {dict(disabled) or '—'}; actually used: {dict(used) or 'none'}.")
    unused = sorted(set(exposed) - set(used))
    if unused:
        add(f"- **Exposed but never used:** {', '.join(unused)}.")
    staged_ops = Counter(p.operation for p in rec.proposals.values() if not p.undo_of)
    not_shown = [op for op in staged_ops if RAIL_BY_OPERATION.get(op) and RAIL_BY_OPERATION[op] not in exposed]
    if not_shown:
        add(f"- **Asked for by voice but never offered on the rail:** {', '.join(f'{op} ×{staged_ops[op]}' for op in not_shown)}.")
    add(f"- Navigation: {dict(nav) or 'none recorded'}.")
    abandoned = [t.turn_id for t in turns if _abandoned(t)]
    if abandoned:
        add(f"- **Screens left within {ABANDON_S:.0f} s:** {', '.join(abandoned)}.")
    images = [e for t in turns for e in t.tablet_events("image_failed")] + [e for e in rec.orphans if e.get("kind") == "tablet_image_failed"]
    if images:
        add(f"- **Failed image loads:** {len(images)} — {dict(Counter(str(e.get('src') or '') for e in images))}.")
    clipped = [(t.turn_id, c.get("type"), c.get("clipped_x")) for t in turns for r in t.tablet_events("render") for c in (r.get("cards") or []) if isinstance(c, dict) and c.get("clipped_x")]
    if clipped:
        add(f"- **Clipping / horizontal overflow:** {clipped}.")
    long_scroll = [(t.turn_id, (r.get("document") or {}).get("cards_height"), (r.get("document") or {}).get("cards_visible")) for t in turns for r in t.tablet_events("render") if (r.get("overflow") or {}).get("long_scroll")]
    if long_scroll:
        add(f"- **Long scroll surfaces** (cards taller than the view; turn, height, visible): {long_scroll}.")
    scrolls = [e for t in turns for e in t.tablet_events("scroll")]
    if scrolls:
        add(f"- Scrolling: {len(scrolls)} scroll report(s); deepest {max(int(e.get('depth') or 0) for e in scrolls)} px.")
    viewports = {f"{(r.get('viewport') or {}).get('w')}×{(r.get('viewport') or {}).get('h')}@{(r.get('viewport') or {}).get('dpr')}" for r in renders}
    if viewports:
        add(f"- Viewports seen: {', '.join(sorted(viewports))}.")
    exceptions = [e for t in turns for e in t.tablet_events("exception")] + [e for e in rec.orphans if e.get("kind") == "tablet_exception"]
    if exceptions:
        add(f"- **Frontend exceptions:** {len(exceptions)} — " + "; ".join(_cell(e.get("message"), 100) for e in exceptions[:5]) + ".")
    connectivity = [e for t in turns for e in t.tablet_events("connectivity")] + [e for e in rec.orphans if e.get("kind") == "tablet_connectivity"]
    if connectivity:
        add(f"- Connectivity: {dict(Counter(str(e.get('state')) for e in connectivity))}.")
    add("")

    # 8 ------------------------------------------------------------------------------
    add("## 8. Action engine")
    add("")
    rows = []
    for p in sorted(rec.proposals.values(), key=lambda p: p.staged_at or 0):
        rows.append([
            p.proposal_id, p.turn_id or "—", p.operation + (" (undo)" if p.undo_of else ""), p.risk, p.interaction, "yes" if p.staged_at else "no",
            "yes" if p.committed else "no", {True: "yes", False: "no", None: "—"}[p.verified], p.status + (f" / {p.code}" if p.code else ""), _fmt_ms(p.latency_ms), p.reason or (p.refusals[-1].get("code") if p.refusals else "") or "—",
        ])
    lines.extend(_table(["Proposal", "Turn", "Operation", "Risk", "Gesture", "Staged", "Committed", "Verified", "Outcome", "Latency", "Failure reason"], rows))
    discrepancies = []
    for p in rec.proposals.values():
        attempted = [e for e in p.tablet if e.get("kind") == "tablet_action_commit"]
        shown_unavailable = [e for e in p.tablet if e.get("kind") == "tablet_render" and any(isinstance(c, dict) and c.get("proposal_id") == p.proposal_id and (c.get("surface") or {}).get("state") == "unavailable" for c in e.get("cards") or [])]
        if p.refusals and attempted:
            discrepancies.append(f"{p.proposal_id}: the tablet tried ({len(attempted)}×) and the Mac refused ({', '.join(str(r.get('code')) for r in p.refusals)})")
        if attempted and not p.committed and not p.refusals:
            discrepancies.append(f"{p.proposal_id}: the tablet reported a commit the Mac never claimed")
        if p.committed and not attempted and p.tablet:
            discrepancies.append(f"{p.proposal_id}: committed on the Mac with no tablet commit event")
        if shown_unavailable:
            discrepancies.append(f"{p.proposal_id}: shown as unavailable on the tablet")
        if p.status == "EXPIRED" and p.armed:
            discrepancies.append(f"{p.proposal_id}: armed by a hold, then expired")
    revoked = [p for p in rec.proposals.values() if p.status == "REVOKED"]
    if revoked:
        add("Withdrawn: " + "; ".join(f"{p.proposal_id} ({p.reason or 'no reason recorded'})" for p in revoked) + ".")
        add("")
    add("Displayed / available / attempted discrepancies: " + ("; ".join(discrepancies) if discrepancies else "none") + ".")
    add("")

    # 9 ------------------------------------------------------------------------------
    add("## 9. Context quality")
    add("")
    already = []
    for t in turns:
        if t.prefetch and t.prefetch.get("hit") and any(x.tool == "shopify_order_detail" and x.outcome == "ok" for x in t.tools) and t.prefetch.get("hydrating"):
            already.append(t.turn_id)
        for x in t.tools:
            if x.tool == "shopify_find_order" and t.prefetch and t.prefetch.get("hit") and x.requested_at > float(t.prefetch.get("ts") or 0):
                already.append(f"{t.turn_id} (find_order after the Mac had run it)")
    history_missing = [t.turn_id for t in turns if any("history" in (h.get("unavailable") or []) for h in t.hydrations)]
    email_missing = [t.turn_id for t in turns if any("email" in (h.get("unavailable") or []) for h in t.hydrations)]
    incomplete = [t.turn_id for t in turns if any(h.get("pending") for h in t.hydrations if h.get("hydration") == "order") and not t.tablet_events("context_landed")]
    duplicates = [(t.turn_id, _duplicate_calls(t.tools)) for t in turns if _duplicate_calls(t.tools)]
    add(f"- Claude asked for what the Mac had already read: {', '.join(already) or 'never'}.")
    add(f"- Customer history missing from an order's context: {', '.join(history_missing) or 'never'}.")
    add(f"- Email correlation missing: {', '.join(email_missing) or 'never'}.")
    add(f"- Order context still incomplete when the answer left, and not collected later: {', '.join(incomplete) or 'never'}.")
    add(f"- Duplicate tool calls: {duplicates or 'none'}.")
    hydrations = [h for t in turns for h in t.hydrations]
    if hydrations:
        reused = sum(1 for h in hydrations if h.get("reused_core"))
        add(f"- Hydrations: {len(hydrations)} ({reused} reused a recent read); by kind {dict(Counter(str(h.get('hydration')) for h in hydrations))}.")
    add("")

    # 10 -----------------------------------------------------------------------------
    add("## 10. Response quality")
    add("")
    add("Deterministic signals only: word matching against the registered tools and the previous answer, never a judgement of tone or correctness.")
    add("")
    rows = []
    for t in turns:
        answer = t.answer
        if not answer:
            continue
        if CANNOT_RE.search(answer):
            named = [tool for word, tool in CAPABILITY_WORDS.items() if word in t.question.lower() and tool in registered]
            if named:
                rows.append([t.turn_id, "says it cannot, though a registered tool can", ", ".join(sorted(set(named)))])
        if OFFER_GESTURE_RE.search(answer) and not t.proposals:
            rows.append([t.turn_id, "offers a card or a gesture, but no change was staged", _cell(answer, 100)])
        if "repeats the previous answer" in t.signals:
            rows.append([t.turn_id, "repeats most of the previous answer", _cell(answer, 100)])
        entity_results = [x for x in t.tools if x.outcome == "ok" and x.result and any(k in x.result for k in ("order_id", "customer_id", "thread_id", "orders", "customers", "threads", "products"))]
        if entity_results and not [u for u in t.ui if u not in ("assistant", "error", "context_stack")]:
            rows.append([t.turn_id, "a tool returned records but no structured card was shown", ", ".join(x.tool for x in entity_results)])
    lines.extend(_table(["Turn", "Signal", "Detail"], rows))

    # 11 -----------------------------------------------------------------------------
    add("## 11. Anticipation")
    add("")
    attention_turns = [t for t in turns if "attention" in t.ui or ((t.render or {}).get("attention"))]
    opens = [e for t in turns for e in t.tablet_events("navigate") if e.get("nav") == "attention_open"] + [e for e in rec.orphans if e.get("kind") == "tablet_navigate" and e.get("nav") == "attention_open"]
    add(f"- Attention surfaces shown: {len(attention_turns)} turn(s) ({', '.join(t.turn_id for t in attention_turns) or '—'}); items on the last: {((attention_turns[-1].render or {}).get('attention') if attention_turns else 0) or 0}.")
    add(f"- Opened by the owner: {len(opens)} time(s).")
    if opens:
        later = []
        for e in opens:
            t0 = float(e.get("t") or 0) / 1000
            after = [p for p in rec.proposals.values() if p.staged_at and p.staged_at >= t0 and p.staged_at - t0 <= 600 and not p.undo_of]
            later.append(f"{len(after)} change(s) proposed within ten minutes" if after else "no change followed within ten minutes")
        add("- Relevance to later actions: " + "; ".join(later) + ".")
    add("")

    # 12 -----------------------------------------------------------------------------
    add("## 12. Top improvement opportunities")
    add("")
    opportunities = _opportunities(rec, turns, registered)
    if not opportunities:
        add("_Nothing in this session's evidence calls for a change._")
    for i, o in enumerate(opportunities, 1):
        add(f"{i}. **{o['problem']}** — {o['frequency']}; severity {o['severity']}/5; e.g. {', '.join(o['examples']) or '—'}. Likely component: {o['component']}. Task: {o['task']}")
    add("")

    # 13 -----------------------------------------------------------------------------
    add("## 13. Intelligence")
    add("")
    add("What the session asked of the read layer, the working sets and the batch tools, and what it asked for that does not exist yet. Every row names its turns; the rules are word matches (app/observability/claims.py) and counts, never a judgement.")
    add("")
    intel = intelligence(rec, registered)
    add("### False unsupported claims")
    add("")
    add("The assistant said it could not, and the tools registered on this Mac compose exactly that.")
    add("")
    lines.extend(_table(["Turn", "Owner said", "Assistant answered", "Composable as", "Via", "Attempted"], [[r["turn_id"], r["question"], r["answer"], r["what"], ", ".join(r["tools"]), r["attempted"]] for r in intel["false_unsupported"]]))
    hinted = sum(1 for r in intel["false_unsupported"] if "the prompt named" in r["attempted"])
    if intel["false_unsupported"]:
        add(f"{len(intel['false_unsupported']) - hinted} declined unaided; {hinted} declined after the Mac named the capability on the prompt (a prompted decline is the model's, not the prompt's).")
        add("")
    add("### Composable but failed requests")
    add("")
    lines.extend(_table(["Turn", "Owner said", "Composable as", "What failed"], [[r["turn_id"], r["question"], r["what"], r["detail"]] for r in intel["composable_failed"]]))
    add("### Common multi-tool workflows")
    add("")
    lines.extend(_table(["Workflow", "Times", "Turns"], [[" → ".join(names), n, ", ".join(ids)] for names, n, ids in intel["workflows"]]))
    add("### Potential new query dimensions")
    add("")
    add("Asked of the query language and refused as unknown.")
    add("")
    lines.extend(_table(["Dimension", "Times", "Turns"], [[name, n, ", ".join(ids)] for name, n, ids in intel["dimensions"]]))
    add("### Potential new actions")
    add("")
    lines.extend(_table(["Capability asked for", "Times", "Turns"], [[name, n, ", ".join(ids)] for name, n, ids in intel["new_actions"]]))
    add("### Bulk workflows requested")
    add("")
    lines.extend(_table(["Change, in bulk", "Times", "Turns", "A batch exists and was staged"], [[op, n, ", ".join(ids), "yes" if served else "no"] for op, n, ids, served in intel["bulk"]]))
    add("### Repeated follow-up patterns")
    add("")
    lines.extend(_table(["Shape", "Times", "Turns"], [[shape, n, ", ".join(ids)] for shape, n, ids in intel["follow_ups"]]))
    add("### Potential UI components")
    add("")
    lines.extend(_table(["Card type", "Times", "Turns"], [[kind, n, ", ".join(ids)] for kind, n, ids in intel["ui_types"]]))
    sets_info = intel["sets"]
    add(f"Working sets: {sets_info['made']} made ({sets_info['derived']} derived), by step {sets_info['by_step'] or '—'}; cross-source reads: {sets_info['cross_source']}. Batches run: {intel['batches']['done']}; members counted {intel['batches']['counts']}.")
    add("")
    add("---")
    add(f"Timeline: `logs/test-sessions/{session.get('test_session_id')}.jsonl` · {len(rec.events)} events · {len(rec.orphans)} outside any turn.")
    return "\n".join(lines) + "\n"


def _fmt_s(seconds: float | None) -> str:
    if seconds is None:
        return "—"
    seconds = float(seconds)
    return f"{int(seconds // 60)} min {int(seconds % 60)} s" if seconds >= 60 else f"{seconds:.0f} s"


def _opportunities(rec: Reconstruction, turns: list[Turn], registered: list[str]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    by_class: dict[str, list[Turn]] = defaultdict(list)
    for t in turns:
        for c in t.classes:
            by_class[c].append(t)
    tasks = {
        "FALSE_UNSUPPORTED": "the assistant declined a question the read layer or a batch tool composes: add the example to commerce_capabilities or the prompt's guidance so the composition is reached for.",
        "STT_ERROR": "replay the failing recordings through `make bench`; check the keyterms and the VAD padding for the words that were lost.",
        "TIMEOUT": "raise or split the budget that expired, and make the slow step visible on the tablet while it runs.",
        "PERMISSION_ERROR": "grant the scope or login the refusal names (the card and /health say which) before the next session.",
        "MISSING_CAPABILITY": "decide whether to build the capability (see section 6) or to have the assistant say plainly what the nearest existing one is.",
        "TOOL_ERROR": "read the client error on the failing tool and add the retry or the clearer refusal it needs.",
        "VERIFICATION_ERROR": "look at the re-read the proof made and the state Shopify/Gmail holds; the change may need a longer settle or a different fingerprint.",
        "TOOL_SELECTION_ERROR": "tighten the tool description or the system prompt for the call the model kept making wrongly.",
        "UI_RENDER_ERROR": "reproduce the card in the renderer tests with the same data shape; fix the exception or the skipped item.",
        "UI_NAVIGATION_PROBLEM": "watch the screen the owner left at once; the card or the chip did not offer what they wanted.",
        "CONTEXT_INCOMPLETE": "extend the hydration budget for the part that never arrived, or make the tablet's collection retry longer.",
        "INTENT_ERROR": "hand the model the entity in focus more plainly (the prefetch line, the context stack) for follow-up questions.",
        "UNKNOWN": "read the turn's events; the error kind has no rule here yet.",
    }
    for cls, group in by_class.items():
        out.append({
            "problem": cls, "frequency": f"{len(group)} of {len(turns)} turns", "severity": SEVERITY[cls],
            "examples": [t.turn_id for t in group[:3]], "component": COMPONENT[cls], "task": tasks[cls], "weight": SEVERITY[cls] * len(group),
        })
    for key, bound in SLOW_MS.items():
        slow = [t for t in turns if (t.latency(key) or 0) > bound]
        if slow:
            out.append({"problem": f"Slow {key.replace('_', ' ')} (over {bound:,.0f} ms)", "frequency": f"{len(slow)} of {len(turns)} turns", "severity": 2,
                        "examples": [t.turn_id for t in sorted(slow, key=lambda t: -(t.latency(key) or 0))[:3]], "component": {"stt": "speech", "claude": "the model / prompt size", "total": "the whole turn", "tts_first_byte": "ElevenLabs / prefetch", "context": "context hydration"}[key],
                        "task": "look at the slowest examples' step timings and cut the step that dominates.", "weight": 2 * len(slow)})
    images = [e for t in turns for e in t.tablet_events("image_failed")]
    if images:
        out.append({"problem": "Images failed to load", "frequency": f"{len(images)} failure(s)", "severity": 2, "examples": sorted({t.turn_id for t in turns if t.tablet_events('image_failed')})[:3],
                    "component": "the media proxy (app/media.py) and the thumbnail paths", "task": "fetch the failing paths on the Mac and see what the proxy answers.", "weight": 2 * len(images)})
    exposed: Counter = Counter()
    used: Counter = Counter()
    for t in turns:
        for r in t.tablet_events("render"):
            for c in r.get("cards") or []:
                for a in (c.get("actions") or []) if isinstance(c, dict) else []:
                    if isinstance(a, dict) and a.get("enabled"):
                        exposed[str(a.get("id"))] += 1
        for e in t.tablet_events("rail_tap") + t.tablet_events("action_primed"):
            used[str(e.get("action") or "")] += 1
    unused = sorted(set(exposed) - set(used))
    if unused and len(turns) >= 5:
        out.append({"problem": "Rail actions exposed but never used", "frequency": f"{len(unused)} chip(s) ({', '.join(unused)}) across {len(turns)} turns", "severity": 1, "examples": [],
                    "component": "the rail (app/actions/available.py, web/ui.js)", "task": "ask whether these chips earn their place, or whether their wording did not read as the thing the owner wanted.", "weight": len(unused)})
    for name, n in Counter(x.missing_capability for t in turns for x in t.tools if x.missing_capability).items():
        out.append({"problem": f"Requested capability not built: {name}", "frequency": f"requested {n} time(s)", "severity": 3, "examples": [t.turn_id for t in turns if any(x.missing_capability == name for x in t.tools)][:3],
                    "component": "the tool registry (app/tools)", "task": f"build `{name}` on the action engine, or teach the assistant the nearest existing capability ({_closest_capability(name, registered)}).", "weight": 3 * n})
    intel = intelligence(rec, registered)
    for name, n, ids in intel["dimensions"]:
        out.append({"problem": f"Query dimension asked for and unknown: {name}", "frequency": f"{n} time(s)", "severity": 3, "examples": ids[:3],
                    "component": "the query language (app/analytics/query.py)", "task": f"decide whether `{name}` is a filter, a group or a metric, and add it with a bound; or teach the prompt the nearest existing one.", "weight": 3 * n})
    for op, n, ids, served in intel["bulk"]:
        if not served:
            out.append({"problem": f"Bulk change asked for with no batch: {op}", "frequency": f"{n} time(s)", "severity": 3, "examples": ids[:3],
                        "component": "the batch engine (app/actions/batch.py, app/tools/batch_tools.py)", "task": f"register a batch over the single `{op}` write once that change has proved itself; money and irreversible changes take a hold and a drag at any size.", "weight": 3 * n})
    for shape, n, ids in intel["follow_ups"]:
        if n >= 3:
            out.append({"problem": f"Follow-up shape repeated: {shape}", "frequency": f"{n} time(s)", "severity": 1, "examples": ids[:3],
                        "component": "the prompt's follow-up guidance (app/kb/loader.py)", "task": "check each follow-up re-ran the previous query with one thing changed; spell the case out in the prompt if any started over.", "weight": n})
    out.sort(key=lambda o: (-o["weight"], o["problem"]))
    return out[:12]


# ---------------------------------------------------------------------- entry points


def build_report(path: Path, *, tools_registered: list[str] | None = None) -> tuple[Reconstruction, str]:
    events = read_events(Path(path))
    rec = reconstruct(events)
    if not rec.session.get("test_session_id"):
        rec.session["test_session_id"] = Path(path).stem
    return rec, render(rec, tools_registered=tools_registered)


def write_report(path: Path, out_dir: Path, *, tools_registered: list[str] | None = None) -> Path:
    rec, markdown = build_report(Path(path), tools_registered=tools_registered)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / f"{rec.session.get('test_session_id') or Path(path).stem}.md"
    target.write_text(markdown, encoding="utf-8")
    try:
        target.chmod(0o600)
    except OSError:
        pass
    return target
