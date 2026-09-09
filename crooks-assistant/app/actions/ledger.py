"""The action audit ledger: one line per lifecycle event, appended, never rewritten.

Separate from the operational log, which rotates and is chatty. This file is the record of
what the assistant was asked to change, what it changed, and whether that was proven. It
carries identities and fingerprints, never the content: no note text, no addresses, no email,
no payloads, no tokens.
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any

from app.actions.models import ActionProposal
from app.logging.turnlog import redact

log = logging.getLogger("crooks.actions")

FILENAME = "actions.jsonl"


class ActionLedger:
    def __init__(self, log_dir: Path) -> None:
        self.path = Path(log_dir) / FILENAME
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, event: str, proposal: ActionProposal, **extra: Any) -> dict[str, Any]:
        """Append one event. Fields are copied by name from an allow-list; a new field reaches
        the ledger only when a line is added here to carry it."""
        entry = {
            "ts": round(time.time(), 3),
            "iso": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "event": event,
            "proposal_id": proposal.proposal_id,
            "operation": proposal.operation,
            "tool": proposal.tool_name,
            "risk": proposal.risk,
            "entity_kind": proposal.entity_kind,
            "entity_ref": proposal.entity_ref,
            "entity_label": proposal.entity_label,
            "session_id": proposal.session_id,
            "epoch": proposal.epoch,
            "caller": proposal.caller or None,
            "status": proposal.status.value,
            "code": proposal.code or None,
            "verified": proposal.verified,
            "args_fingerprint": proposal.fingerprint,
            "before": _fingerprint_only(proposal.before),
            "after": _fingerprint_only(proposal.after),
            "undo_of": proposal.undo_of,
        }
        for key, value in extra.items():
            if key in _EXTRA_ALLOWED:
                entry[key] = value
        # Belt and braces: nothing above is free text, but the redactor costs nothing. The
        # caller is the owner's own Tailscale login — the audit's whole point — and is kept.
        caller = entry["caller"]
        entry = redact(entry)
        entry["caller"] = caller
        self._append(entry)
        return entry

    def _append(self, entry: dict[str, Any]) -> None:
        line = json.dumps(entry, ensure_ascii=False, default=str) + "\n"
        try:
            # O_APPEND: every write lands at the end, whole, even with two writers.
            fd = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
            try:
                os.write(fd, line.encode("utf-8"))
                os.fsync(fd)
            finally:
                os.close(fd)
        except OSError as exc:
            log.error("could not write the action ledger: %s", exc)

    def read(self) -> list[dict[str, Any]]:
        """Every entry, oldest first. For inspection and tests."""
        try:
            return [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]
        except OSError:
            return []


_EXTRA_ALLOWED = frozenset({"reason", "ms", "payload_len", "detail", "deduplicated", "job", "facts"})


def _fingerprint_only(value: dict[str, Any] | None) -> dict[str, Any] | None:
    """Only the hash-and-length shape is a fingerprint; anything else is not written."""
    if not isinstance(value, dict):
        return None
    return {k: v for k, v in value.items() if k in ("sha", "len") and isinstance(v, (str, int))} or None


class NullLedger(ActionLedger):
    """For tests and tools that run without a log directory. Records in memory only."""

    def __init__(self) -> None:  # noqa: D107 — deliberately does not call super()
        self.path = Path("/dev/null")
        self.entries: list[dict[str, Any]] = []

    def _append(self, entry: dict[str, Any]) -> None:
        self.entries.append(entry)

    def read(self) -> list[dict[str, Any]]:
        return list(self.entries)
