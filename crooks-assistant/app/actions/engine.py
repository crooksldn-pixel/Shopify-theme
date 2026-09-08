"""Staging, authorisation and execution of proposals: the loop every future action uses.

    tool call → gate → stage (this) → card → tap → commit (this) → verify (this) → ledger

Two invariants live here and nowhere else:

  - A proposal executes at most once. The claim from PENDING to EXECUTING is synchronous —
    no await between the checks and the write of the status — so two commits that arrive
    together cannot both pass it. A second commit that lands while the first is executing or
    being proven waits for the first's outcome and returns it; a settled proposal is never
    re-opened, whoever asks and whatever they saw.
  - An ambiguous mutation is settled by looking, not guessing. If the request to Shopify
    fails after it was sent, the entity is re-read once: the fingerprint says whether the
    change landed, did not, or cannot be told — and the card says exactly that.
  - Nothing is sent that was not stored at staging time. `commit` takes a proposal id and a
    session id; the arguments come from the proposal.
"""

from __future__ import annotations

import asyncio
import copy
import logging
import time
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from app.actions.ledger import ActionLedger, NullLedger
from app.actions.models import (
    PROPOSAL_TTL_S,
    ActionProposal,
    ActionStatus,
    Observed,
    Prepared,
    args_fingerprint,
    new_proposal_id,
)
from app.session.models import Session
from app.tools.registry import ToolSpec

log = logging.getLogger("crooks.actions")

# A commit that finds the proposal already executing waits this long for the outcome.
WAIT_FOR_OUTCOME_S = 25.0

# Codes the tablet turns into calm states. The set is closed; a new code is a new line here.
CODES = frozenset({
    "proposed", "verified", "unverified", "failed", "stale", "expired", "revoked",
    "already_executed", "in_progress", "unknown", "wrong_session", "service_unavailable",
})

# A settled proposal is kept in the index this long after it finished, so the tablet can
# still ask about it; then it goes, and its session's copy of the note text with it.
SETTLED_RETENTION_S = 900.0


@dataclass(slots=True)
class CommitResult:
    proposal: ActionProposal | None
    code: str
    spoken: str
    detail: str = ""

    @property
    def status(self) -> str:
        return self.proposal.status.value.lower() if self.proposal else "unknown"


class ActionEngine:
    def __init__(
        self,
        *,
        ledger: ActionLedger | None = None,
        ttl_s: float = PROPOSAL_TTL_S,
        clock=time.time,
    ) -> None:
        self.ledger = ledger or NullLedger()
        self.ttl_s = ttl_s
        self.clock = clock
        # proposal id → session, so a commit can find its proposal without a session lookup
        # that might resurrect an idle session. A session that has gone takes its proposals.
        self._index: dict[str, Session] = {}
        self.executions = 0   # every mutation this engine has sent

    # ------------------------------------------------------------- staging

    def stage(
        self, session: Session, spec: ToolSpec, model_args: dict[str, Any], prepared: Prepared,
    ) -> tuple[ActionProposal, bool]:
        """Record a prepared change against the session's current epoch. Returns the proposal
        and whether it is new: the same request twice in one epoch is one proposal."""
        assert spec.write is not None
        now = self.clock()
        self.prune(now)
        fingerprint = args_fingerprint(spec.name, model_args)
        for existing in session.proposals:
            if (
                existing.status is ActionStatus.PENDING
                and existing.proposal_id in self._index      # ours: never a proposal this engine cannot execute
                and existing.epoch == session.epoch
                and existing.fingerprint == fingerprint
                and not existing.expired(now)
            ):
                # The same proposal, not a second one: the ledger already has its line.
                return existing, False
        proposal = ActionProposal(
            proposal_id=new_proposal_id(),
            session_id=session.session_id,
            epoch=session.epoch,
            tool_name=spec.name,
            operation=spec.write.operation,
            risk=spec.tier.value,
            model_args=MappingProxyType(copy.deepcopy(model_args)),
            execution=MappingProxyType(copy.deepcopy(prepared.execution)),
            entity_kind=spec.write.entity_kind,
            entity_ref=prepared.entity_ref,
            entity_label=prepared.entity_label,
            interaction=spec.write.interaction,
            reversible=spec.write.reversible,
            before=dict(prepared.before),
            expected_after=dict(prepared.expected_after),
            summary=dict(prepared.summary),
            fingerprint=fingerprint,
            created_at=now,
            expires_at=now + self.ttl_s,
        )
        session.stage(proposal)
        self._index[proposal.proposal_id] = session
        self.ledger.record("PROPOSED", proposal, payload_len=_payload_len(prepared))
        return proposal, True

    def stage_undo(self, session: Session, spec: ToolSpec, done: ActionProposal) -> ActionProposal | None:
        """A server-generated proposal that puts the entity back exactly as it was. Bound to
        the same session and epoch, with its own expiry, executed by the same path."""
        write = spec.write
        if write is None or not write.reversible or write.undo is None:
            return None
        try:
            reverse = write.undo(dict(done.execution))
        except Exception as exc:  # noqa: BLE001
            log.warning("could not build the undo for %s: %s", done.proposal_id, exc)
            return None
        now = self.clock()
        undo = ActionProposal(
            proposal_id=new_proposal_id(),
            session_id=session.session_id,
            # The epoch the owner authorised the change in. If they moved on while it was
            # being applied, the undo is already behind them and a tap on it is refused.
            epoch=done.epoch,
            tool_name=spec.name,
            operation=f"{write.operation}_undo",
            risk=done.risk,
            model_args=MappingProxyType({}),
            execution=MappingProxyType(copy.deepcopy(reverse)),
            entity_kind=done.entity_kind,
            entity_ref=done.entity_ref,
            entity_label=done.entity_label,
            interaction="tap_commit",
            reversible=False,
            # It may only run while the entity still shows what this action wrote.
            before=dict(done.after or done.expected_after),
            expected_after=dict(done.before),
            summary={"undo": True},
            fingerprint=args_fingerprint(f"undo:{spec.name}", {"of": done.proposal_id}),
            created_at=now,
            expires_at=now + self.ttl_s,
            undo_of=done.proposal_id,
        )
        session.stage(undo)
        self._index[undo.proposal_id] = session
        done.undo_id = undo.proposal_id
        self.ledger.record("PROPOSED", undo)
        return undo

    # -------------------------------------------------------- invalidation

    def advance_epoch(self, session: Session, reason: str) -> int:
        """A new instruction from the owner. Everything still waiting belongs to the last one
        and is revoked; a proposal never outlives the conversation position it was made in."""
        session.epoch += 1
        self.revoke_pending(session, reason)
        return session.epoch

    def revoke_pending(self, session: Session, reason: str) -> list[str]:
        """Withdraw every proposal still waiting in this session. Returns their ids, so the
        turn that withdrew them can tell the tablet which cards are dead."""
        revoked: list[str] = []
        for proposal in session.proposals:
            if proposal.status is ActionStatus.PENDING:
                self._finish(proposal, ActionStatus.REVOKED, "revoked", reason=reason)
                revoked.append(proposal.proposal_id)
        return revoked

    def revoke_ids(self, proposal_ids: list[str], reason: str) -> int:
        """Withdraw these proposals, if still waiting, whatever epoch they were staged in."""
        count = 0
        for pid in proposal_ids:
            proposal = self.find(pid)
            if proposal is not None and proposal.status is ActionStatus.PENDING:
                self._finish(proposal, ActionStatus.REVOKED, "revoked", reason=reason)
                count += 1
        return count

    def deliver(self, proposal_id: str) -> ActionProposal | None:
        """The card is on its way to the tablet. The wait for the tap starts now, not when
        the model asked: the answer and the spoken line came between, and the owner had no
        card to tap during them. Still the server's clock; still one TTL."""
        proposal = self.find(proposal_id)
        if proposal is None or proposal.status is not ActionStatus.PENDING:
            return proposal
        now = self.clock()
        proposal.expires_at = max(proposal.expires_at, now + self.ttl_s)
        self.ledger.record("DELIVERED", proposal)
        return proposal

    def forget_session(self, session_id: str) -> None:
        """The session is gone (reset, restart, idled out): nothing of it may stay tappable
        or in memory. Called by the session manager whenever it drops one."""
        for pid, session in list(self._index.items()):
            if session.session_id == session_id:
                for proposal in session.proposals:
                    if proposal.status is ActionStatus.PENDING:
                        self._finish(proposal, ActionStatus.REVOKED, "revoked", reason="session ended")
                del self._index[pid]

    def prune(self, now: float | None = None) -> int:
        """Drop settled proposals the tablet has had long enough to ask about, and any whose
        session no longer holds them. The index is the only thing keeping an old session —
        and the note text inside its proposals — alive."""
        now = self.clock() if now is None else now
        dropped = 0
        for pid, session in list(self._index.items()):
            proposal = session.proposal(pid)
            if proposal is None:
                del self._index[pid]
                dropped += 1
                continue
            if proposal.terminal and proposal.finished_at is not None and now - proposal.finished_at > SETTLED_RETENTION_S:
                del self._index[pid]
                dropped += 1
        return dropped

    # ---------------------------------------------------------------- look up

    def find(self, proposal_id: str) -> ActionProposal | None:
        session = self._index.get(proposal_id)
        if session is None:
            return None
        proposal = session.proposal(proposal_id)
        if proposal is not None and proposal.status is ActionStatus.PENDING and proposal.expired(self.clock()):
            self._finish(proposal, ActionStatus.EXPIRED, "expired")
        return proposal

    def state(self, proposal_id: str, session_id: str) -> ActionProposal | None:
        proposal = self.find(proposal_id)
        if proposal is None or proposal.session_id != session_id:
            return None
        return proposal

    # ----------------------------------------------------------------- commit

    async def commit(self, proposal_id: str, session_id: str, *, caller: str, spec_lookup) -> CommitResult:
        """The owner tapped. Validate, claim atomically, check the entity has not moved, send
        the one reviewed mutation with the stored arguments, prove it, record it."""
        proposal = self.find(proposal_id)
        if proposal is None:
            return CommitResult(None, "unknown", "")
        if proposal.session_id != session_id:
            return CommitResult(None, "wrong_session", "")
        spec = spec_lookup(proposal.tool_name)
        write = spec.write if spec is not None else None

        if proposal.status in (ActionStatus.EXECUTING, ActionStatus.EXECUTED):
            # Someone else's tap, a retried request, an Android double-fire — arriving while
            # the first commit is sending the change or proving it: wait for the outcome the
            # first commit produces and hand back that, never a second mutation.
            try:
                await asyncio.wait_for(proposal.done.wait(), timeout=WAIT_FOR_OUTCOME_S)
            except TimeoutError:
                return CommitResult(proposal, "in_progress", "")
            return self._terminal(proposal, write)
        if proposal.terminal:
            return self._terminal(proposal, write)

        session = self._index.get(proposal_id)
        if session is None or proposal.epoch != session.epoch:
            self._finish(proposal, ActionStatus.REVOKED, "revoked", reason="the owner moved on")
            return self._terminal(proposal, write)
        if write is None or not write.complete:
            self._finish(proposal, ActionStatus.FAILED, "failed", reason="no write definition")
            return self._terminal(proposal, write)

        # --- the claim. Nothing may await between the checks above and this line. ---
        proposal.status = ActionStatus.EXECUTING
        proposal.caller = caller
        proposal.executed_at = None
        self.ledger.record("EXECUTING", proposal)

        started = time.perf_counter()
        sent = False   # True from the moment the mutation leaves; after that, nothing is assumed
        try:
            execution = dict(proposal.execution)
            # Precondition: the entity must still be what it was when the change was decided.
            observed = await write.observe(execution)
            if observed.fingerprint != proposal.before:
                self._finish(proposal, ActionStatus.STALE, "stale", reason="entity changed since staging")
                return CommitResult(proposal, "stale", write.spoken_stale)

            self.executions += 1
            sent = True
            await write.execute(execution)
            proposal.executed_at = self.clock()
            proposal.status = ActionStatus.EXECUTED
            self.ledger.record("EXECUTED", proposal, ms=round((time.perf_counter() - started) * 1000, 1))

            # Verification: a 200 is not proof; the re-read is.
            proven = await write.observe(execution)
            return self._prove(proposal, proven, session, spec, write)
        except Exception as exc:  # noqa: BLE001 — every failure is a recorded outcome
            if not sent:
                # Nothing left this process: the precondition read failed. Proven unchanged.
                log.warning("action %s could not check the entity: %s", proposal.proposal_id, exc)
                self._finish(proposal, ActionStatus.FAILED, "service_unavailable", reason=_short(exc))
                return CommitResult(proposal, "service_unavailable", write.spoken_failure, detail=_short(exc))
            # The mutation left, or its answer did not come back, or the proving read failed.
            # Shopify may or may not hold the change. Look once; say what was seen.
            log.warning("action %s is ambiguous after sending: %s", proposal.proposal_id, exc)
            return await self._settle_by_observation(proposal, execution, session, spec, write, exc)

    def _prove(self, proposal, proven, session, spec, write) -> CommitResult:
        proposal.after = dict(proven.fingerprint)
        proposal.entity = proven.entity
        if proven.fingerprint == proposal.expected_after:
            proposal.verified = True
            self._finish(proposal, ActionStatus.VERIFIED, "verified")
            spoken = (write.spoken_undo_success if proposal.undo_of else write.spoken_success)
            # The line names what it touched: "{label}" is the entity as a person says it.
            spoken = spoken.replace("{label}", str(proposal.entity_label).lstrip("#"))
            if proposal.undo_of is None:
                self.stage_undo(session, spec, proposal)
            return CommitResult(proposal, "verified", spoken)
        proposal.verified = False
        self._finish(proposal, ActionStatus.UNVERIFIED, "unverified", reason="re-read does not match")
        return CommitResult(proposal, "unverified", write.spoken_failure)

    async def _settle_by_observation(self, proposal, execution, session, spec, write, exc) -> CommitResult:
        """One re-read decides an ambiguous mutation. Landed: verified, as if the answer had
        come back. Untouched: failed, and 'nothing was changed' is now a fact. Neither, or
        the re-read fails too: unverified — the card says to check the order, never that
        nothing happened."""
        try:
            proven = await write.observe(execution)
        except Exception as again:  # noqa: BLE001
            proposal.verified = False
            self._finish(proposal, ActionStatus.UNVERIFIED, "unverified", reason=_short(again))
            return CommitResult(proposal, "unverified", write.spoken_failure, detail=_short(exc))
        if proven.fingerprint == proposal.before and proposal.status is ActionStatus.EXECUTING:
            self._finish(proposal, ActionStatus.FAILED, "service_unavailable", reason=_short(exc))
            return CommitResult(proposal, "service_unavailable", write.spoken_failure, detail=_short(exc))
        if proposal.status is ActionStatus.EXECUTING:
            proposal.executed_at = self.clock()
            proposal.status = ActionStatus.EXECUTED
            self.ledger.record("EXECUTED", proposal, reason="settled by re-read")
        return self._prove(proposal, proven, session, spec, write)

    # ---------------------------------------------------------------- helpers

    def _terminal(self, proposal: ActionProposal, write) -> CommitResult:
        """What to say about a proposal that is already settled. Never a second mutation."""
        status = proposal.status
        if status in (ActionStatus.VERIFIED, ActionStatus.EXECUTED):
            return CommitResult(proposal, "already_executed", "")
        if status is ActionStatus.UNVERIFIED:
            return CommitResult(proposal, "already_executed", "")
        if status is ActionStatus.STALE:
            return CommitResult(proposal, "stale", write.spoken_stale if write else "")
        if status is ActionStatus.EXPIRED:
            return CommitResult(proposal, "expired", "That action expired. Ask again.")
        if status is ActionStatus.REVOKED:
            return CommitResult(proposal, "revoked", "")
        return CommitResult(proposal, proposal.code or "failed", "")

    def _finish(self, proposal: ActionProposal, status: ActionStatus, code: str, *, reason: str = "") -> None:
        if proposal.terminal:
            # Settled is settled. A late caller cannot turn a verified change into anything else.
            log.warning("ignored %s → %s for settled proposal %s", proposal.status.value, status.value, proposal.proposal_id)
            return
        proposal.status = status
        proposal.code = code
        proposal.reason = reason
        proposal.finished_at = self.clock()
        self.ledger.record(status.value, proposal, reason=reason or None)
        proposal.done.set()


def _payload_len(prepared: Prepared) -> int | None:
    value = prepared.summary.get("payload_len")
    return int(value) if isinstance(value, int) else None


def _short(exc: BaseException) -> str:
    return f"{type(exc).__name__}: {str(exc)[:120]}"


# ------------------------------------------------------------ the process's engine
#
# One engine per process, installed by the runtime. The dispatcher reaches it here rather
# than through the runtime so that a tool call and a tap land in the same index.

_engine: ActionEngine | None = None


def install(engine: ActionEngine) -> ActionEngine:
    global _engine
    _engine = engine
    return engine


def current() -> ActionEngine:
    global _engine
    if _engine is None:
        _engine = ActionEngine()
    return _engine


__all__ = ["ActionEngine", "CommitResult", "CODES", "Observed", "Prepared", "current", "install"]
