"""Bulk changes on the action engine: one card, one gesture, many proposals.

A batch is not a new way to mutate. It is a set of ordinary proposals — each prepared by the
same write tool from a fresh read of its own entity, each committed by the same engine with
the same precondition, the same at-most-once claim and the same proving re-read — held
together under one id so the owner authorises them with one gesture. What the batch adds:

  - The membership is the Mac's. It is snapshotted from a working set when the batch is
    staged and never changes; the tablet names the batch id and nothing else.
  - Eligibility is decided per member, on the Mac, from a fresh read: a member the change
    does not apply to (an order that already has the tag, a thread not in the inbox) is
    EXCLUDED with its reason, before anything is shown.
  - The gesture follows the size as well as the change: a handful takes the change's own
    gesture; more than a few takes a hold; a large batch takes a hold and a drag.
  - The result is counted, never claimed: VERIFIED is the number of members whose proving
    re-read matched, and every other member is named with what happened to it.
"""

from __future__ import annotations

import asyncio
import copy
import logging
import re
import secrets
import time
from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType
from typing import Any

from app.actions import engine as engine_module
from app.actions.engine import ARM_SLACK_MS, WAIT_FOR_OUTCOME_S, ActionEngine
from app.actions.grammar import ARMED_FOR_S, dwell_ms, gesture_for
from app.actions.ledger import ActionLedger, NullLedger
from app.actions.models import ActionStatus, Prepared, args_fingerprint
from app.tools.registry import BatchPlan, ToolError, ToolSpec

log = logging.getLogger("crooks.actions")

# How long a batch card waits for the gesture: more than a single card, because there is
# more to read on it. Its children live exactly as long.
BATCH_TTL_S = 120.0
# The most members one batch may hold. A working set can be ten times this; a batch over a
# larger set is refused with "narrow it first", never silently cut.
MAX_BATCH = 50
# Preparing the children: each is a fresh read of its entity on the Mac. A few at a time,
# under one budget; members not read within it are excluded, never guessed at.
PREPARE_CONCURRENCY = 4
PREPARE_BUDGET_S = 20.0
# Committing them: each is a precondition read, the change and a proving read. A few at a
# time so Shopify is not hammered; members not reached within the budget are NOT ATTEMPTED
# and withdrawn, and the count says so.
COMMIT_CONCURRENCY = 3
COMMIT_BUDGET_S = 90.0
# Size and the gesture. Up to TAP_MAX eligible members the batch takes the change's own
# gesture; more takes a hold; DRAG_MIN or more takes a hold and a drag onto the target.
TAP_MAX = 5
DRAG_MIN = 25
SETTLED_RETENTION_S = 900.0

# Codes the tablet turns into calm states. Closed, like the engine's.
CODES = frozenset({
    "proposed", "done", "expired", "revoked", "already_executed", "in_progress", "unknown",
    "wrong_session", "not_armed", "batch_member",
})

# What a child's outcome is counted as. Anything the engine can answer lands in one bucket.
_BUCKET = {
    "verified": "verified", "unverified": "unverified", "stale": "stale",
    "failed": "failed", "service_unavailable": "failed", "refused": "failed",
    "already_executed": "verified", "in_progress": "unverified",
    "expired": "not_attempted", "revoked": "not_attempted", "not_attempted": "not_attempted", "unknown": "not_attempted",
}
COUNT_KEYS = ("requested", "eligible", "excluded", "verified", "unverified", "stale", "failed", "not_attempted")


class BatchStatus(StrEnum):
    PENDING = "PENDING"
    EXECUTING = "EXECUTING"
    DONE = "DONE"          # every eligible child has a terminal outcome; the counts are final
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


TERMINAL = frozenset({BatchStatus.DONE, BatchStatus.EXPIRED, BatchStatus.REVOKED})


@dataclass(slots=True)
class BatchChild:
    """One member's place in the batch: its proposal when eligible, its reason when not,
    and — once the batch has run — what became of it."""

    ref: str
    label: str
    proposal_id: str = ""
    excluded: str = ""
    code: str = ""
    status: str = ""

    @property
    def eligible(self) -> bool:
        return bool(self.proposal_id)

    def public(self) -> dict[str, Any]:
        out: dict[str, Any] = {"label": self.label[:60]}
        if self.excluded:
            out["excluded"] = self.excluded[:120]
        if self.code:
            out["outcome"] = self.code
        return out


@dataclass(slots=True)
class BatchProposal:
    batch_id: str
    session_id: str
    epoch: int
    tool_name: str                 # the batch tool the model called
    child_tool: str                # the write tool each child was prepared by
    operation: str                 # the batch's own name, for the card and the ledger
    child_operation: str           # the write's name, for the scope preflight
    risk: str
    interaction: str
    reversible: bool
    set_id: str
    set_label: str
    set_kind: str
    members: tuple[str, ...]       # the membership as it was when staged; never changes
    model_args: MappingProxyType
    children: list[BatchChild]
    summary: dict[str, Any]
    fingerprint: str
    created_at: float
    expires_at: float
    turn_id: str = ""
    status: BatchStatus = BatchStatus.PENDING
    code: str = ""
    reason: str = ""
    caller: str = ""
    delivered_at: float | None = None
    executed_at: float | None = None
    finished_at: float | None = None
    counts: dict[str, int] = field(default_factory=dict)
    armed_at: float | None = None
    arm_nonce: str = ""
    undo_of: str | None = None
    undo_id: str | None = None
    done: asyncio.Event = field(default_factory=asyncio.Event)

    # The batch stands where a proposal stands in the turn's bookkeeping (the tool call
    # names it, the answer delivers it, a new instruction withdraws it): same field name.
    @property
    def proposal_id(self) -> str:
        return self.batch_id

    @property
    def terminal(self) -> bool:
        return self.status in TERMINAL

    @property
    def requested(self) -> int:
        return len(self.children)

    @property
    def eligible(self) -> list[BatchChild]:
        return [c for c in self.children if c.eligible]

    @property
    def excluded(self) -> list[BatchChild]:
        return [c for c in self.children if not c.eligible]

    @property
    def all_verified(self) -> bool:
        return self.status is BatchStatus.DONE and bool(self.eligible) and self.counts.get("verified") == len(self.eligible)

    def expired(self, now: float | None = None) -> bool:
        return (now if now is not None else time.time()) > self.expires_at

    def ttl_s(self, now: float | None = None) -> int:
        return max(0, int(round(self.expires_at - (now if now is not None else time.time()))))

    def public(self, now: float | None = None) -> dict[str, Any]:
        """What the tablet may see: counts, the set's name, the gesture. No member ids, no
        arguments, no fingerprints."""
        return {
            "batch_id": self.batch_id,
            "status": self.status.value.lower(),
            "code": self.code,
            "operation": self.operation,
            "risk": self.risk.lower(),
            "entity_kind": "set",
            "set_id": self.set_id,
            "set_label": self.set_label,
            "set_kind": self.set_kind,
            "requested": self.requested,
            "eligible": len(self.eligible),
            "excluded": len(self.excluded),
            "interaction": self.interaction,
            "reversible": self.reversible,
            "expires_at": _iso(self.expires_at),
            "ttl_s": self.ttl_s(now),
            "counts": dict(self.counts),
            "all_verified": self.all_verified,
            "undo_of": self.undo_of,
            "undo_id": self.undo_id,
        }


@dataclass(slots=True)
class BatchResult:
    batch: BatchProposal | None
    code: str
    spoken: str
    detail: str = ""

    @property
    def status(self) -> str:
        return self.batch.status.value.lower() if self.batch else "unknown"


def new_batch_id() -> str:
    return f"batch_{secrets.token_hex(6)}"


def batch_gesture(risk: str, op_class: str, count: int) -> str:
    """The gesture for a batch: the change's own table, and the size on top of it. A large
    batch is a hold and a drag whatever the change; unknown inputs fall to the strictest."""
    if count >= DRAG_MIN:
        return "hold_drag_target"
    return gesture_for(risk, op_class)


def batch_risk(child_risks: list[str], tool_tier: str, count: int) -> str:
    """RED when any child is, when the tool is, or when there are more than a few."""
    if str(tool_tier).upper() == "RED" or any(str(r).upper() == "RED" for r in child_risks) or count > TAP_MAX:
        return "RED"
    return "AMBER"


def spoken_for(verb: str, noun: str, counts: dict[str, int]) -> str:
    """The line after a batch has run: numbers the engine counted, in a fixed shape."""
    verified = int(counts.get("verified") or 0)
    requested = int(counts.get("requested") or 0)
    parts = [f"{verb} {verified} of the {requested} {noun}."]
    for key, words in (
        ("stale", "changed meanwhile and were left alone"), ("failed", "could not be applied"),
        ("unverified", "could not be confirmed"), ("excluded", "were excluded"), ("not_attempted", "were not attempted"),
    ):
        n = int(counts.get(key) or 0)
        if n:
            parts.append(f"{n} {words}." if n > 1 else f"1 {words.replace('were', 'was')}.")
    return " ".join(parts)


class BatchEngine:
    def __init__(self, engine: ActionEngine | None = None, *, ledger: ActionLedger | None = None, ttl_s: float = BATCH_TTL_S, clock=None) -> None:
        self.engine = engine or engine_module.current()
        self.ledger = ledger or getattr(self.engine, "ledger", None) or NullLedger()
        self.ttl_s = ttl_s
        self.clock = clock or self.engine.clock
        self._index: dict[str, Any] = {}     # batch id → session

    # ------------------------------------------------------------- staging

    async def stage(self, session: Any, spec: ToolSpec, model_args: dict[str, Any], plan: BatchPlan, working_set: Any) -> tuple[BatchProposal, bool]:
        """Prepare one proposal per member of the set, from a fresh read each, and hold them
        under one batch. Nothing is sent. Raises ToolError when nothing is eligible."""
        from app.tools import registry
        from app.tools.dispatch import _readable_errors

        assert spec.batch is not None
        now = self.clock()
        self.prune(now)
        fingerprint = args_fingerprint(spec.name, model_args)
        for existing in _held(session).values():
            if (
                existing.status is BatchStatus.PENDING and existing.batch_id in self._index
                and existing.epoch == session.epoch and existing.fingerprint == fingerprint and not existing.expired(now)
            ):
                return existing, False
        child_spec = registry.get(plan.child_tool)
        if child_spec.write is None or not child_spec.write.complete:
            raise ToolError(f"{plan.child_tool} is not a write tool; a batch cannot be built on it.")
        members = tuple(dict.fromkeys(str(m) for m in working_set.members if m))
        if not members:
            raise ToolError("The set is empty.")
        if len(members) > spec.batch.max_members:
            raise ToolError(f"The set has {len(members)} {working_set.kind}; a batch takes at most {spec.batch.max_members}. Narrow it first.")
        labels = getattr(working_set, "labels", None) or {}
        batch_id = new_batch_id()
        children = [BatchChild(ref=ref, label=str(labels.get(ref) or _tail(ref))) for ref in members]
        readable = _readable_errors()
        semaphore = asyncio.Semaphore(PREPARE_CONCURRENCY)
        loop = asyncio.get_running_loop()
        deadline = loop.time() + PREPARE_BUDGET_S
        preview: dict[str, Any] = {}
        timeout_s = float(child_spec.timeout_s or 6.0)

        async def prepare(child: BatchChild) -> None:
            nonlocal preview
            async with semaphore:
                if loop.time() > deadline:
                    child.excluded = "not read in time"
                    return
                try:
                    child_args = plan.child_args(child.ref)
                    if asyncio.iscoroutine(child_args) or isinstance(child_args, asyncio.Future):
                        child_args = await child_args
                    prepared = await registry.invoke(plan.child_tool, dict(child_args), timeout_s=min(timeout_s, max(1.0, deadline - loop.time())))
                except readable as exc:
                    child.excluded = _reason(exc)
                    return
                except TimeoutError:
                    child.excluded = "not read in time"
                    return
                except Exception as exc:  # noqa: BLE001 — one member's failure excludes that member
                    log.warning("batch %s: could not prepare %s: %s", batch_id, child.ref, _short(exc))
                    child.excluded = "could not be read"
                    return
                if not isinstance(prepared, Prepared):
                    child.excluded = "could not be prepared"
                    return
                pii = prepared.summary.get("pii")
                if isinstance(pii, (list, tuple)):
                    session.remember_pii(*(p for p in pii if isinstance(p, str)))
                proposal, created = self.engine.stage(session, child_spec, dict(child_args), prepared, batch_id=batch_id)
                if not created and proposal.batch_id != batch_id:
                    # The same change is already waiting on its own card: that card decides.
                    child.excluded = "already waiting on its own card"
                    return
                child.proposal_id = proposal.proposal_id
                # The set's own name for the member where it has one (a subject line, an
                # order number); the write's label ("thread") only where it has none.
                if not labels.get(child.ref):
                    child.label = str(prepared.entity_label or child.label)[:60]
                if not preview and spec.batch.preview is not None:
                    try:
                        preview = dict(spec.batch.preview(prepared) or {})
                    except Exception as exc:  # noqa: BLE001 — a card without a preview is still a card
                        log.warning("batch %s: preview failed: %s", batch_id, _short(exc))

        await asyncio.gather(*(prepare(child) for child in children))
        eligible = [c for c in children if c.eligible]
        if not eligible:
            reasons = _reasons(children)
            raise ToolError(f"Nothing to do for any of the {len(children)} {working_set.kind}: {reasons}")
        child_proposals = [session.proposal(c.proposal_id) for c in eligible]
        risk = batch_risk([p.risk for p in child_proposals if p is not None], spec.tier.value, len(eligible))
        interaction = batch_gesture(risk, child_spec.write.kind, len(eligible))
        summary = {k: v for k, v in dict(plan.summary or {}).items() if isinstance(v, (str, int, float, bool, list, dict))}
        if preview:
            summary["preview"] = preview
        batch = BatchProposal(
            batch_id=batch_id, session_id=str(session.session_id), epoch=int(session.epoch), tool_name=spec.name, child_tool=plan.child_tool,
            operation=spec.batch.operation, child_operation=child_spec.write.operation, risk=risk, interaction=interaction,
            reversible=bool(child_spec.write.reversible), set_id=str(working_set.set_id), set_label=str(working_set.label)[:80], set_kind=str(working_set.kind),
            members=members, model_args=MappingProxyType(copy.deepcopy(model_args)), children=children, summary=summary, fingerprint=fingerprint,
            created_at=now, expires_at=now + self.ttl_s, turn_id=str(getattr(session, "turn_id", "") or ""),
        )
        for child in eligible:
            proposal = session.proposal(child.proposal_id)
            if proposal is not None:
                proposal.expires_at = batch.expires_at
        _held(session)[batch.batch_id] = batch
        self._index[batch.batch_id] = session
        self.ledger.record_batch("PROPOSED", batch, reason=_reasons(children) or None)
        return batch, True

    def stage_undo(self, session: Any, batch: BatchProposal) -> BatchProposal | None:
        """The undo of a batch: the undo proposals the engine staged for each verified child,
        held under one batch of their own, authorised with the batch's own gesture."""
        if not batch.reversible or batch.undo_of is not None:
            return None
        children: list[BatchChild] = []
        for child in batch.eligible:
            proposal = session.proposal(child.proposal_id)
            if proposal is None or proposal.status is not ActionStatus.VERIFIED or not proposal.undo_id:
                continue
            undo = session.proposal(proposal.undo_id)
            if undo is None or undo.status is not ActionStatus.PENDING:
                continue
            children.append(BatchChild(ref=child.ref, label=child.label, proposal_id=undo.proposal_id))
        if not children:
            return None
        now = self.clock()
        undo_batch = BatchProposal(
            batch_id=new_batch_id(), session_id=batch.session_id, epoch=batch.epoch, tool_name=batch.tool_name, child_tool=batch.child_tool,
            operation=f"{batch.operation}_undo", child_operation=batch.child_operation, risk=batch.risk,
            interaction=batch_gesture(batch.risk, "reversible" if batch.reversible else "irreversible", len(children)), reversible=False,
            set_id=batch.set_id, set_label=batch.set_label, set_kind=batch.set_kind, members=tuple(c.ref for c in children),
            model_args=MappingProxyType({}), children=children, summary={"undo": True}, fingerprint=args_fingerprint(f"undo:{batch.tool_name}", {"of": batch.batch_id}),
            created_at=now, expires_at=now + self.ttl_s, turn_id=batch.turn_id, undo_of=batch.batch_id,
        )
        for child in children:
            proposal = session.proposal(child.proposal_id)
            if proposal is not None:
                proposal.batch_id = undo_batch.batch_id
                proposal.expires_at = undo_batch.expires_at
        _held(session)[undo_batch.batch_id] = undo_batch
        self._index[undo_batch.batch_id] = session
        batch.undo_id = undo_batch.batch_id
        self.ledger.record_batch("PROPOSED", undo_batch)
        return undo_batch

    # -------------------------------------------------------- invalidation

    def advance_epoch(self, session: Any) -> None:
        """A new instruction moved the session on (the engine did the moving). Pending undo
        batches follow it, as pending undo proposals do; everything else was revoked."""
        for batch in _held(session).values():
            if batch.status is BatchStatus.PENDING and batch.undo_of is not None:
                batch.epoch = session.epoch

    def revoke_pending(self, session: Any, reason: str, *, undos: bool = False) -> list[str]:
        revoked: list[str] = []
        for batch in _held(session).values():
            if batch.status is BatchStatus.PENDING and (undos or batch.undo_of is None):
                self._finish(batch, BatchStatus.REVOKED, "revoked", reason=reason)
                revoked.append(batch.batch_id)
        return revoked

    def revoke_ids(self, batch_ids: list[str], reason: str) -> int:
        count = 0
        for bid in batch_ids:
            batch = self.find(bid)
            if batch is not None and batch.status is BatchStatus.PENDING:
                self._finish(batch, BatchStatus.REVOKED, "revoked", reason=reason)
                count += 1
        return count

    def deliver(self, batch_id: str) -> BatchProposal | None:
        batch = self.find(batch_id)
        if batch is None or batch.status is not BatchStatus.PENDING or batch.delivered_at is not None:
            return batch
        now = self.clock()
        batch.delivered_at = now
        batch.expires_at = max(batch.expires_at, now + self.ttl_s)
        session = self._index.get(batch_id)
        if session is not None:
            for child in batch.eligible:
                proposal = session.proposal(child.proposal_id)
                if proposal is not None and proposal.status is ActionStatus.PENDING:
                    proposal.expires_at = batch.expires_at
        self.ledger.record_batch("DELIVERED", batch)
        return batch

    def forget_session(self, session_id: str) -> None:
        for bid, session in list(self._index.items()):
            if session.session_id == session_id:
                batch = _held(session).get(bid)
                if batch is not None and batch.status is BatchStatus.PENDING:
                    self._finish(batch, BatchStatus.REVOKED, "revoked", reason="session ended")
                del self._index[bid]

    def prune(self, now: float | None = None) -> int:
        now = self.clock() if now is None else now
        dropped = 0
        for bid, session in list(self._index.items()):
            batch = _held(session).get(bid)
            if batch is None:
                del self._index[bid]
                dropped += 1
            elif batch.terminal and batch.finished_at is not None and now - batch.finished_at > SETTLED_RETENTION_S:
                del self._index[bid]
                _held(session).pop(bid, None)
                dropped += 1
        return dropped

    # ---------------------------------------------------------------- look up

    def find(self, batch_id: str) -> BatchProposal | None:
        session = self._index.get(batch_id)
        if session is None:
            return None
        batch = _held(session).get(batch_id)
        if batch is not None and batch.status is BatchStatus.PENDING and batch.expired(self.clock()):
            self._finish(batch, BatchStatus.EXPIRED, "expired")
        return batch

    def state(self, batch_id: str, session_id: str) -> BatchProposal | None:
        batch = self.find(batch_id)
        if batch is None or batch.session_id != session_id:
            return None
        return batch

    def waiting(self, session: Any) -> BatchProposal | None:
        """The batch a spoken yes could refer to: pending, unexpired, this epoch, not an undo."""
        now = self.clock()
        for batch in reversed(list(_held(session).values())):
            if batch.status is BatchStatus.PENDING and batch.epoch == session.epoch and not batch.expired(now) and batch.undo_of is None:
                return batch
        return None

    # ------------------------------------------------------------------- arming

    def arm(self, batch_id: str, session_id: str) -> tuple[BatchProposal | None, str]:
        batch = self.find(batch_id)
        if batch is None:
            return None, "unknown"
        if batch.session_id != session_id:
            return None, "wrong_session"
        if batch.status is not BatchStatus.PENDING:
            return batch, batch.code or batch.status.value.lower()
        batch.armed_at = self.clock()
        batch.arm_nonce = secrets.token_urlsafe(12)
        self.ledger.record_batch("ARMED", batch)
        return batch, ""

    # ----------------------------------------------------------------- commit

    async def commit(self, batch_id: str, session_id: str, *, caller: str, spec_lookup, nonce: str = "") -> BatchResult:
        """The owner's gesture on the batch card. Claim the batch once, then commit every
        eligible child through the engine — each with its own precondition, its own send,
        its own proof — a few at a time, under a budget, and count what came back."""
        batch = self.find(batch_id)
        if batch is None:
            return BatchResult(None, "unknown", "")
        if batch.session_id != session_id:
            return BatchResult(None, "wrong_session", "")
        if batch.status is BatchStatus.PENDING and not self._armed(batch, nonce):
            return BatchResult(batch, "not_armed", "")
        if batch.status is BatchStatus.EXECUTING:
            try:
                await asyncio.wait_for(batch.done.wait(), timeout=WAIT_FOR_OUTCOME_S)
            except TimeoutError:
                return BatchResult(batch, "in_progress", "")
            return self._terminal(batch, spec_lookup)
        if batch.terminal:
            return self._terminal(batch, spec_lookup)
        session = self._index.get(batch_id)
        if session is None or batch.epoch != session.epoch:
            self._finish(batch, BatchStatus.REVOKED, "revoked", reason="the owner moved on")
            return self._terminal(batch, spec_lookup)

        # --- the claim. Nothing may await between the checks above and this line. ---
        batch.status = BatchStatus.EXECUTING
        batch.caller = caller
        batch.executed_at = self.clock()
        self.ledger.record_batch("EXECUTING", batch)
        started = time.perf_counter()
        semaphore = asyncio.Semaphore(COMMIT_CONCURRENCY)
        loop = asyncio.get_running_loop()
        deadline = loop.time() + COMMIT_BUDGET_S

        async def run(child: BatchChild) -> None:
            async with semaphore:
                if loop.time() > deadline:
                    child.code = "not_attempted"
                    return
                try:
                    result = await self.engine.commit(child.proposal_id, session_id, caller=caller, spec_lookup=spec_lookup, via_batch=batch.batch_id)
                except asyncio.CancelledError:
                    child.code = child.code or "unverified"
                    raise
                except Exception as exc:  # noqa: BLE001 — the engine settles its own outcomes; this is a belt
                    log.warning("batch %s: child %s raised: %s", batch.batch_id, child.proposal_id, _short(exc))
                    child.code = "unverified"
                    return
                child.code = result.code
                child.status = result.status

        try:
            await asyncio.gather(*(run(child) for child in batch.eligible))
        except asyncio.CancelledError:
            for child in batch.eligible:
                if not child.code:
                    child.code = "not_attempted"
            self._settle(batch, session, spec_lookup, started)
            raise
        return self._settle(batch, session, spec_lookup, started)

    def _settle(self, batch: BatchProposal, session: Any, spec_lookup, started: float) -> BatchResult:
        # Children never reached are withdrawn: they cannot be committed later on their own.
        leftovers = [c.proposal_id for c in batch.eligible if _BUCKET.get(c.code, "not_attempted") == "not_attempted"]
        if leftovers:
            self.engine.revoke_ids(leftovers, "batch budget spent")
        counts = {key: 0 for key in COUNT_KEYS}
        counts["requested"] = batch.requested
        counts["eligible"] = len(batch.eligible)
        counts["excluded"] = len(batch.excluded)
        for child in batch.eligible:
            counts[_BUCKET.get(child.code, "not_attempted")] += 1
        batch.counts = counts
        self._finish(batch, BatchStatus.DONE, "done", ms=round((time.perf_counter() - started) * 1000, 1))
        if batch.undo_of is None:
            self.stage_undo(session, batch)
        spec = spec_lookup(batch.tool_name)
        verb, noun = ("Undid", batch.set_kind) if batch.undo_of else _words(spec, batch)
        return BatchResult(batch, "done", spoken_for(verb, noun, counts))

    # ---------------------------------------------------------------- helpers

    def _armed(self, batch: BatchProposal, nonce: str) -> bool:
        required_ms = dwell_ms(batch.interaction)
        if required_ms <= 0:
            return True
        if not nonce or not batch.arm_nonce or batch.armed_at is None:
            return False
        if not secrets.compare_digest(str(nonce), batch.arm_nonce):
            return False
        held_ms = (self.clock() - batch.armed_at) * 1000
        return required_ms <= held_ms <= (ARMED_FOR_S * 1000 + required_ms + ARM_SLACK_MS)

    def _terminal(self, batch: BatchProposal, spec_lookup) -> BatchResult:
        if batch.status is BatchStatus.DONE:
            return BatchResult(batch, "already_executed", "")
        if batch.status is BatchStatus.EXPIRED:
            return BatchResult(batch, "expired", "That batch expired. Ask again.")
        if batch.status is BatchStatus.REVOKED:
            return BatchResult(batch, "revoked", "")
        return BatchResult(batch, batch.code or "unknown", "")

    def _finish(self, batch: BatchProposal, status: BatchStatus, code: str, *, reason: str = "", ms: float | None = None) -> None:
        if batch.terminal:
            log.warning("ignored %s → %s for settled batch %s", batch.status.value, status.value, batch.batch_id)
            return
        batch.status = status
        batch.code = code
        batch.reason = reason
        batch.finished_at = self.clock()
        if status in (BatchStatus.REVOKED, BatchStatus.EXPIRED):
            # The children go with it, whatever the engine's own clock says.
            session = self._index.get(batch.batch_id)
            if session is not None:
                self.engine.revoke_ids([c.proposal_id for c in batch.eligible], reason or code)
        self.ledger.record_batch(status.value, batch, reason=reason or None, ms=ms)
        batch.done.set()


def _words(spec, batch: BatchProposal) -> tuple[str, str]:
    if spec is not None and spec.batch is not None:
        return str(spec.batch.verb or "Applied to"), str(spec.batch.noun or batch.set_kind)
    return "Applied to", batch.set_kind


def _held(session: Any) -> dict[str, BatchProposal]:
    batches = getattr(session, "batches", None)
    if not isinstance(batches, dict):
        batches = {}
        try:
            session.batches = batches
        except AttributeError:
            pass
    return batches


def _reasons(children: list[BatchChild]) -> str:
    """The exclusions, grouped: "already has those tags: 2, not in the inbox: 1"."""
    counts: dict[str, int] = {}
    for child in children:
        if child.excluded:
            counts[child.excluded] = counts.get(child.excluded, 0) + 1
    return ", ".join(f"{reason}: {n}" for reason, n in sorted(counts.items(), key=lambda kv: -kv[1]))


_ENTITY_PREFIX = re.compile(r"^(?:the order|that thread|that draft|the thread|order \S+|that|the|there is no)\s+", re.I)


def _reason(exc: BaseException) -> str:
    """A tool's own refusal, as the exclusion's reason: its first sentence, without the
    entity's name in front ("The order already has those tags." → "already has those tags"),
    bounded."""
    text = " ".join(str(exc).split()).split(". ")[0].rstrip(".")
    text = _ENTITY_PREFIX.sub("", text, count=1)
    text = re.sub(r"^is\s+", "", text)
    return (text[:1].lower() + text[1:])[:120] if text else "not applicable"


def _tail(ref: str) -> str:
    return str(ref).rsplit("/", 1)[-1][:40]


def _short(exc: BaseException, limit: int = 120) -> str:
    return f"{type(exc).__name__}: {str(exc)[:limit]}"


def _iso(ts: float) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(ts)) + "Z"


# ------------------------------------------------------------ the process's batches

_batches: BatchEngine | None = None


def install(batches: BatchEngine) -> BatchEngine:
    global _batches
    _batches = batches
    return batches


def current() -> BatchEngine:
    global _batches
    if _batches is None or _batches.engine is not engine_module.current():
        _batches = BatchEngine(engine_module.current())
    return _batches


__all__ = ["MAX_BATCH", "BatchChild", "BatchEngine", "BatchProposal", "BatchResult", "BatchStatus", "CODES", "batch_gesture", "batch_risk", "current", "install", "spoken_for"]
