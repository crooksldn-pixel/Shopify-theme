"""A Gmail that answers from the golden world instead of Google.

`GmailClient` already accepts an injected service object — the class was written that way for
its own tests — so the double goes in at the googleapiclient boundary rather than replacing the
client. Every line of `GmailClient` then runs for real: the header parsing, the label handling,
`thread_state`'s internalDate arithmetic, the scope report, the error translation.

The shape imitated is googleapiclient's builder chain:

    service.users().threads().get(userId=..., id=..., format=...).execute()

so each step returns an object and only `.execute()` produces a value.

Sending, drafting and modifying raise. A fixture run may PROPOSE an email and inspect the
proposal; it may never be the reason a send looks as though it worked.
"""

from __future__ import annotations

import re
from typing import Any

from experience.fixtures import data
from experience.fixtures.data import BY_THREAD, DRAFTS, THREADS

# What the fixture credential may do. Both grants, so a scenario about "the change is offered"
# is not passing for want of a scope — the same reasoning as the fixture shop's scope list.
SCOPES = (
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.compose",
)


class FixtureWriteAttempted(AssertionError):
    """A fixture run tried to change the mailbox."""


class _Request:
    """What a googleapiclient builder call returns: something with .execute()."""

    def __init__(self, value: Any) -> None:
        self._value = value

    def execute(self, *_a: Any, **_k: Any) -> Any:
        if isinstance(self._value, Exception):
            raise self._value
        return self._value


def _query_terms(query: str) -> list[str]:
    """The bits of a Gmail query the fixture understands: quoted phrases and bare words."""
    return [t.strip('"').lower() for t in re.findall(r'"[^"]*"|\S+', query or "")]


def _thread_matches(thread, query: str) -> bool:
    terms = _query_terms(query)
    text = " ".join(
        f"{m.sender} {m.subject} {m.body}" for m in thread.messages
    ).lower()
    labels = {label for m in thread.messages for label in m.labels}
    for term in terms:
        if term in ("and", "or"):
            continue
        if term.startswith("-"):
            negated = term[1:]
            if negated.startswith("in:") or negated.startswith("label:"):
                if negated.split(":", 1)[1].upper() in labels:
                    return False
                continue
            if negated.startswith("from:"):
                if negated.split(":", 1)[1] in text:
                    return False
                continue
            if negated == "from:me":
                if "SENT" in labels and len(thread.messages) == 1:
                    return False
                continue
            if negated in text:
                return False
            continue
        if term.startswith("category:"):
            wanted = term.split(":", 1)[1]
            if wanted == "primary" and "CATEGORY_UPDATES" in labels:
                return False
            continue
        if term.startswith("in:") or term.startswith("label:"):
            wanted = term.split(":", 1)[1].upper()
            if wanted in ("INBOX", "UNREAD", "SENT") and wanted not in labels:
                return False
            continue
        if term.startswith("from:"):
            if term.split(":", 1)[1] not in text:
                return False
            continue
        if term.startswith("newer_than:") or term.startswith("older_than:"):
            # Honoured, not skipped. A fake inbox that ignores the window makes every
            # question about a period pass whatever window the code asked for, so a recipe
            # that reads "today" and then fetches a week looks correct here and is wrong on
            # the real mailbox. Gmail's form is a count and a unit: 1d, 2w, 3m, 1y.
            match = re.fullmatch(r"(newer_than|older_than):(\d+)([dwmy])", term)
            if match is None:
                continue
            scale = {"d": 1, "w": 7, "m": 30, "y": 365}[match.group(3)]
            window = int(match.group(2)) * scale
            newest = min((m.days_ago for m in thread.messages), default=0.0)
            if match.group(1) == "newer_than" and newest > window:
                return False
            if match.group(1) == "older_than" and newest <= window:
                return False
            continue
        if term.startswith("after:") or term.startswith("before:"):
            continue
        if term.startswith("subject:"):
            if term.split(":", 1)[1] not in text:
                return False
            continue
        if term not in text:
            return False
    return True


class _Threads:
    def list(self, userId: str = "me", q: str = "", maxResults: int = 20, **_k: Any) -> _Request:  # noqa: N803
        found = [t for t in THREADS if _thread_matches(t, q)]
        return _Request({
            "threads": [{"id": t.thread_id, "snippet": t.messages[-1].body[:120],
                         "historyId": "1"} for t in found[:maxResults]],
            "resultSizeEstimate": len(found),
        })

    def get(self, userId: str = "me", id: str = "", format: str = "full", **_k: Any) -> _Request:  # noqa: A002, N803
        thread = BY_THREAD.get(id)
        if thread is None:
            return _Request({"id": id, "messages": []})
        messages = [data.gmail_message_payload(m) for m in thread.messages]
        if format == "minimal":
            messages = [{"id": m["id"], "threadId": m["threadId"], "labelIds": m["labelIds"]} for m in messages]
        elif format == "metadata":
            # The real API returns only the requested headers; keeping them all is harmless
            # because every caller reads by name.
            messages = [{k: v for k, v in m.items() if k != "payload"} | {"payload": {"headers": m["payload"]["headers"]}}
                        for m in messages]
        return _Request({"id": id, "messages": messages, "historyId": "1"})

    def modify(self, **_k: Any) -> _Request:
        return _Request(FixtureWriteAttempted("a fixture run tried to modify a Gmail thread"))


class _Messages:
    def list(self, userId: str = "me", q: str = "", maxResults: int = 20, **_k: Any) -> _Request:  # noqa: N803
        out = []
        for thread in THREADS:
            if not _thread_matches(thread, q):
                continue
            for message in thread.messages:
                out.append({"id": message.message_id, "threadId": message.thread_id})
        return _Request({"messages": out[:maxResults], "resultSizeEstimate": len(out)})

    def get(self, userId: str = "me", id: str = "", format: str = "full", **_k: Any) -> _Request:  # noqa: A002, N803
        for thread in THREADS:
            for message in thread.messages:
                if message.message_id == id:
                    payload = data.gmail_message_payload(message)
                    if format == "minimal":
                        return _Request({"id": payload["id"], "threadId": payload["threadId"],
                                         "labelIds": payload["labelIds"]})
                    return _Request(payload)
        return _Request({"id": id, "labelIds": [], "payload": {"headers": []}})

    def send(self, **_k: Any) -> _Request:
        return _Request(FixtureWriteAttempted("a fixture run tried to send a Gmail message"))

    def modify(self, **_k: Any) -> _Request:
        return _Request(FixtureWriteAttempted("a fixture run tried to relabel a Gmail message"))


class _Drafts:
    def list(self, userId: str = "me", q: str = "", maxResults: int = 10, **_k: Any) -> _Request:  # noqa: N803
        return _Request({"drafts": [
            {"id": d["draft_id"], "message": {"id": d["message_id"], "threadId": d["thread_id"]}}
            for d in DRAFTS
        ][:maxResults]})

    def get(self, userId: str = "me", id: str = "", format: str = "full", **_k: Any) -> _Request:  # noqa: A002, N803
        for draft in DRAFTS:
            if draft["draft_id"] == id:
                body = draft["body"]
                import base64
                return _Request({"id": draft["draft_id"], "message": {
                    "id": draft["message_id"], "threadId": draft["thread_id"],
                    "labelIds": ["DRAFT"],
                    "payload": {"mimeType": "text/plain", "headers": [
                        {"name": "To", "value": draft["to"]},
                        {"name": "Subject", "value": draft["subject"]},
                    ], "body": {"data": base64.urlsafe_b64encode(body.encode()).decode().rstrip("=")}},
                }})
        return _Request({"id": id, "message": {}})

    def create(self, **_k: Any) -> _Request:
        return _Request(FixtureWriteAttempted("a fixture run tried to create a Gmail draft"))

    def send(self, **_k: Any) -> _Request:
        return _Request(FixtureWriteAttempted("a fixture run tried to send a Gmail draft"))

    def delete(self, **_k: Any) -> _Request:
        return _Request(FixtureWriteAttempted("a fixture run tried to delete a Gmail draft"))


class _Labels:
    def list(self, userId: str = "me", **_k: Any) -> _Request:  # noqa: N803
        return _Request({"labels": [{"id": n, "name": n} for n in ("INBOX", "UNREAD", "SENT", "DRAFT")]})


class _Users:
    def __init__(self) -> None:
        self._threads = _Threads()
        self._messages = _Messages()
        self._drafts = _Drafts()
        self._labels = _Labels()

    def threads(self) -> _Threads:
        return self._threads

    def messages(self) -> _Messages:
        return self._messages

    def drafts(self) -> _Drafts:
        return self._drafts

    def labels(self) -> _Labels:
        return self._labels

    def getProfile(self, userId: str = "me", **_k: Any) -> _Request:  # noqa: N802, N803
        return _Request({"emailAddress": data.MAILBOX, "messagesTotal": sum(len(t.messages) for t in THREADS),
                         "threadsTotal": len(THREADS), "historyId": "1"})


class FixtureGmailService:
    """The object `GmailClient.service()` hands back when a double is injected.

    `scopes` is read off this by GmailClient when a service was injected without credentials,
    which is how the fixture credential says what it may do without a token existing.
    """

    scopes = SCOPES

    def __init__(self) -> None:
        self._users = _Users()

    def users(self) -> _Users:
        return self._users


def fixture_gmail():
    """A `GmailClient` wired to the golden inbox. The client class itself is untouched."""
    from app.clients.gmail import GmailClient

    client = GmailClient()
    client._service = FixtureGmailService()
    return client
