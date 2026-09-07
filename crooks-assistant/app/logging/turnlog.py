"""Redacted per-turn JSONL logging with rotation.

Everything this application logs passes through redact() first. The rule the M13 check applies
is not "we intended not to log addresses" but "open a real log file and confirm there are none".
"""

from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path
from typing import Any

log = logging.getLogger("crooks.turnlog")

MAX_BYTES = 5_000_000
KEEP_FILES = 5

_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
# UK mobile and landline shapes, and international. Deliberately greedy: a false positive costs
# a redacted number in a log, a false negative puts a customer's phone number on disk.
_PHONE = re.compile(r"(?:(?<!\w)(?:\+\d{1,3}[\s-]?)?(?:\d[\s-]?){9,14}\d(?!\w))")
_POSTCODE = re.compile(r"\b[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}\b", re.I)
_CARD = re.compile(r"\b(?:\d[ -]?){13,19}\b")

# Keys whose values are addresses or contact details however they are spelled.
_REDACT_KEYS = {
    "address", "address1", "address2", "shippingaddress", "billingaddress", "street",
    "phone", "phonenumber", "postcode", "zip", "postalcode", "email", "emailaddress",
    "from_email", "customer_email", "body", "snippet",
}


def redact_text(text: str) -> str:
    text = _EMAIL.sub("[email]", text)
    text = _CARD.sub("[card]", text)
    text = _POSTCODE.sub("[postcode]", text)
    text = _PHONE.sub("[phone]", text)
    return text


def redact(value: Any) -> Any:
    """Walk any structure and redact both by key name and by value shape."""
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            if str(key).lower().replace("_", "") in {k.replace("_", "") for k in _REDACT_KEYS}:
                out[key] = "[redacted]" if item not in (None, "", [], {}) else item
            else:
                out[key] = redact(item)
        return out
    if isinstance(value, list):
        return [redact(v) for v in value]
    if isinstance(value, str):
        return redact_text(value)
    return value


class TurnLog:
    def __init__(self, log_dir: Path) -> None:
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.log_dir / "turns.jsonl"

    def write(self, record: dict[str, Any]) -> None:
        record = {"ts": time.time(), "iso": time.strftime("%Y-%m-%dT%H:%M:%S"), **redact(record)}
        try:
            self._rotate_if_needed()
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
        except OSError as exc:
            log.warning("could not write turn log: %s", exc)

    def _rotate_if_needed(self) -> None:
        if not self.path.exists() or self.path.stat().st_size < MAX_BYTES:
            return
        for index in range(KEEP_FILES - 1, 0, -1):
            older = self.log_dir / f"turns.jsonl.{index}"
            newer = self.log_dir / f"turns.jsonl.{index + 1}"
            if older.exists():
                older.rename(newer)
        self.path.rename(self.log_dir / "turns.jsonl.1")
